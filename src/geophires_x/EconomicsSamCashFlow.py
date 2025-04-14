from __future__ import annotations

import csv
import json
import logging
import os
import re
import sys
import math
from functools import lru_cache
from typing import Any

from PySAM import Singleowner

import geophires_x.Model as Model
from geophires_x.GeoPHIRESUtils import json_dumpse


@lru_cache(maxsize=12)
def _calculate_sam_economics_cash_flow(model: Model, single_owner: Singleowner) -> list[list[Any]]:
    log = model.logger

    _soo = single_owner.Outputs

    profile = []
    total_duration = model.surfaceplant.plant_lifetime.value + model.surfaceplant.construction_years.value

    # Prefix with 'Year ' partially as workaround for tabulate applying float formatting to ints, possibly related
    # to https://github.com/astanin/python-tabulate/issues/18
    years = [f'Year {y}' for y in list(range(0, total_duration))]

    row_1 = [None] + years
    profile.append(row_1)

    def blank_row() -> None:
        profile.append([None] * (len(years) + 1))

    def category_row(cat_name: str) -> list[Any]:
        cr = [cat_name] + [None] * len(years)
        profile.append(cr)
        return cr

    def designator_row(designator: str):
        dsr = [designator] + [None] * len(years)
        profile.append(dsr)

    def get_data_adjust_func(row_name: str):
        def rnd(x):
            return round(x, 2)

        if row_name.endswith('($)'):

            def rnd(x):
                return round(x)

        def adj(x_):
            if isinstance(x_, str):
                return x_
            else:
                if math.isnan(x_):
                    return 'NaN'

                return rnd(x_)

        return adj

    def data_row(row_name: str, output_data: Any | None = None) -> list[Any]:
        if output_data is None:
            # TODO output_data should not be passed if present in _get_output
            output_data = _get_single_owner_output(_soo, row_name)

        if output_data is None:
            log.error(f'No output data for {row_name}')

            # TODO/WIP - skip ambiguous mapping for now
            # output_data = ['undefined'] * len(years)
            return

        adjust = get_data_adjust_func(row_name)

        dr = [row_name] + [adjust(d) for d in output_data]  # TODO revisit this to audit for precision concerns
        profile.append(dr)
        return dr

    def single_value_row(row_name: str, single_value: float | None = None) -> list[Any]:
        if single_value is None:
            # TODO single_value should not be passed if present in _get_output
            single_value = _get_single_owner_output(_soo, row_name)

        if single_value is None:
            log.error(f'No output data for {row_name}')

            # TODO/WIP - skip ambiguous mapping for now
            # single_value = 'undefined'
            return

        svr = (
            [row_name] + [get_data_adjust_func(row_name)(single_value)] + [None] * (len(years) - 1)
        )  # TODO revisit this to audit for precision concerns
        profile.append(svr)
        return svr

    with open(_get_file_path('sam_economics/sam-cash-flow-table.csv'), encoding='utf-8') as f:
        cft_reader = csv.reader(f)

        lines = []
        for _line in cft_reader:
            lines.append(_line)

        lines = lines[1:]  # exclude header row

        def is_only_commas(s: str) -> bool:
            # TODO this is a silly way to test whether entries in row are None
            return re.match(r'^,+$', s) is not None

        for line in lines:
            if is_only_commas(','.join(line)):
                blank_row()
                continue

            line_entries = line
            row_label = line_entries[0]

            # Some row labels have seemingly-erroneous extra spaces e.g.  `Reserves debt service disbursement  ($)`
            row_label = re.sub(r'\s+', ' ', row_label)

            if row_label == '':
                blank_row()
                continue

            if _is_designator_row_label(row_label):
                designator_row(row_label)
                continue

            if _is_category_row_label(row_label):
                category_row(row_label)
                continue

            if is_only_commas(','.join(line_entries[3:])):
                single_value_row(row_label)
            else:
                data_row(row_label)

    if all([it is None for it in profile[-1]]):
        profile = profile[:-1]  # trim last line if blank

    return _clean_profile(profile)


def _is_category_row_label(row_label: str) -> bool:
    return re.match(r'^([A-Z \(\)\-\:]+)$', row_label) or re.match(r'^([A-Z][A-Za-z \-]+\:)$', row_label)


def _is_designator_row_label(row_label: str) -> bool:
    return row_label == 'plus PBI if not available for debt service:' or re.match(r'^[a-z]+:$', row_label) is not None


def _clean_profile(profile: list[list[Any]]) -> list[list[Any]]:
    # Collapse consecutive blank rows
    previous_line_was_blank = False
    profile_cleaned = []
    for pl in profile:
        is_blank = all(it is None for it in pl)
        if not (is_blank and previous_line_was_blank):
            profile_cleaned.append(pl)
        previous_line_was_blank = is_blank

    return profile_cleaned


# fmt:off
_SINGLE_OWNER_OUTPUT_PROPERTIES_ADDITIONAL = {
    "Debt closing costs ($)": "cost_financing",
    'Total installed cost ($)': lambda _soo: -1.0 * _soo.cost_installed,

    # TODO: present in https://nrel-pysam.readthedocs.io/en/main/modules/CbConstructionFinancing.html#outputs-group,
    #   but unclear where it's accessible from the Singleowner module object
    # 'Total construction financing cost ($)': 'construction_financing_cost'

    # TODO: unclear what this is derived from
    # 'Other financing cost ($)'
}


# fmt:on


def _get_file_path(file_name) -> str:
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), file_name)


def _build_single_owner_output_properties():
    with open(_get_file_path('sam_economics/sam-output-properties.json'), encoding='utf-8') as f:
        sop = json.load(f)

        sop = {**sop, **_SINGLE_OWNER_OUTPUT_PROPERTIES_ADDITIONAL}

        with open(
            _get_file_path('sam_economics/Generic_400_MWe/Generic_400_MWe_singleowner.json'), encoding='utf-8'
        ) as gso:
            reserves_interest_input_value = json.load(gso)['reserves_interest']
            sop['Interest on reserves (%/year)'] = lambda _soo: reserves_interest_input_value

        return sop


_SINGLE_OWNER_OUTPUT_PROPERTIES = _build_single_owner_output_properties()


def _get_logger():
    # TODO disable debug output outside of dev environment
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.DEBUG)
    sh.setFormatter(logging.Formatter(fmt='[%(asctime)s][%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    _l = logging.getLogger(__name__)
    _l.setLevel(logging.DEBUG)
    _l.addHandler(sh)
    return _l


_log = _get_logger()


def _get_single_owner_output(soo: Any, display_name: str) -> Any:
    """ "
    :param soo: single_owner.Outputs
    :type soo: `PySAM.Singleowner.Outputs`
    """

    def ga(_p):
        # noinspection PyBroadException
        try:
            return getattr(soo, _p)
        except Exception:
            return None

    def _search_props(s: str) -> list[Any]:
        """
        Utility function to search output properties (useful in IDE debugger)
        """

        return [(p, ga(p)) for p in dir(soo) if s in p]

    # noinspection PyUnusedLocal
    def _search_prop_vals(v: Any) -> list[Any]:
        """
        Utility function to search output properties (useful in IDE debugger)
        """

        def val_match(ga_p: Any) -> bool:
            # noinspection PyBroadException
            try:
                return v == ga_p or v == abs(ga_p) or abs(v) in [abs(x) for x in ga_p]
            except Exception:
                return False

        return [(p, ga(p)) for p in dir(soo) if val_match(ga(p))]

    if display_name not in _SINGLE_OWNER_OUTPUT_PROPERTIES:
        # noinspection PyBroadException
        try:
            ld = 'SAM Cash Flow Output property'
            _log.warning(f'{ld} not found for "{display_name}"')

            def show_suggestions(search_string: str):
                if search_string is None or search_string == '':
                    _log.debug(f'No {ld} suggestions for "{display_name}" found')
                    return

                suggest = [
                    (display_name, it[0], ga(it[0]))
                    for it in _search_props(search_string)
                    if not it[0].startswith('__')
                ]

                def data_preview(sg_2):
                    if not isinstance(sg_2, list) and not isinstance(sg_2, tuple):
                        return sg_2

                    idx = min(10, len(sg_2))
                    idx = min(idx, len(sg_2))
                    preview = tuple(sg_2[:idx])
                    if idx < len(sg_2):
                        preview += ('...',)
                    return preview

                suggest_display = "\n\t".join([f"'{sg[1]}',\n\t\t{data_preview(sg[2])}" for sg in suggest])
                if len(suggest) > 0:
                    _log.debug(f'{ld} suggestions for \n\'{display_name}\': \n\t{suggest_display}')
                else:
                    _log.debug(f'No {ld} suggestions for "{display_name}" found')
                    # In IDE debugger, try:
                    # show_suggestions(display_name.lower().split(' ')[1])
                    # etc.
                return suggest

            try:
                show_suggestions(next(it for it in display_name.lower().split(' ') if it.lower() != 'total'))
            except StopIteration:
                _log.debug(f'No {ld} suggestions for "{display_name}" found')

        except Exception as e:
            _log.debug(f'Encountered exception attempting to generate suggestions for {ld} for "{display_name}": {e}"')

        return None

    prop = _SINGLE_OWNER_OUTPUT_PROPERTIES[display_name]

    if callable(prop):
        return prop(soo)

    return getattr(soo, prop)

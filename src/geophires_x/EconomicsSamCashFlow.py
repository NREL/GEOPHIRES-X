from __future__ import annotations

import csv
import logging
import os
import re
import sys
from functools import lru_cache
from typing import Any

from PySAM import Singleowner

from geophires_x import Model as Model


@lru_cache(maxsize=12)
def _calculate_sam_economics_cash_flow(model: Model, single_owner: Singleowner) -> list[list[Any]]:
    log = model.logger

    _soo = single_owner.Outputs

    profile = []
    total_duration = model.surfaceplant.plant_lifetime.value + model.surfaceplant.construction_years.value
    years = list(range(0, total_duration))
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
                return rnd(x_)

        return adj

    def data_row(row_name: str, output_data: Any | None = None) -> list[Any]:
        if output_data is None:
            # TODO output_data should not be passed if present in _get_output
            output_data = _get_single_owner_output(_soo, row_name)

        if output_data is None:
            log.error(f'No output data for {row_name}')
            output_data = ['undefined'] * len(years)  # WIP

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
            single_value = 'undefined'  # WIP

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
            return re.match(r'^,+$', s)

        for line in lines:
            if is_only_commas(','.join(line)):
                blank_row()
                continue

            line_entries = line
            row_label = line_entries[0]
            if re.match(r'^([A-Z \(\)]+)$', row_label) or re.match(r'^([A-Za-z ]+\:)$', row_label):
                category_row(row_label)
                continue

            if re.match(r'^[a-z]+:$', row_label):
                designator_row(row_label)
                continue

            if is_only_commas(','.join(line_entries[2:])):
                single_value_row(row_label)
            else:
                data_row(row_label)

    if all([it is None for it in profile[-1]]):
        profile = profile[:-1]  # trim last line if blank

    return profile


_SINGLE_OWNER_OUTPUT_PROPERTIES = {
    'Electricity to grid (kWh)': 'cf_energy_sales',
    'Electricity from grid (kWh)': 'cf_energy_purchases',
    'Electricity to grid net (kWh)': 'cf_energy_net',
    'PPA price (cents/kWh)': 'cf_ppa_price',
    'PPA revenue ($)': 'cf_energy_value',
    'Salvage value ($)': 'cf_net_salvage_value',
    'Total revenue ($)': 'cf_revenue_dispatch1',
    'O&M fixed expense ($)': 'cf_om_fixed_expense',
    'Property tax expense ($)': 'cf_property_tax_expense',
    'Total operating expenses ($)': 'cf_operating_expenses',
    'EBITDA ($)': 'cf_ebitda',
    'Debt interest payment ($)': 'cf_debt_payment_interest',
    'Cash flow from operating activities ($)': 'cf_project_operating_activities',
    'Total installed cost ($)': lambda _soo: -1.0 * _soo.cost_installed,
    'Purchase of property ($)': 'purchase_of_property',
    'Cash flow from investing activities ($)': 'cf_project_investing_activities',
    'Issuance of equity ($)': 'issuance_of_equity',
    'Size of debt ($)': 'size_of_debt',
    'Debt principal payment ($)': 'cf_debt_payment_principal',
    'Cash flow from financing activities ($)': 'cf_project_financing_activities',
    'Cash flow from operating activities ($)': 'cf_project_operating_activities',
    'Cash flow from investing activities ($)': 'cf_project_investing_activities',
    'Cash flow from financing activities ($)': 'cf_project_financing_activities',
    'Total pre-tax cash flow ($)': 'cf_pretax_cashflow',
    'Issuance of equity ($)': 'issuance_of_equity',
    'Total pre-tax cash flow ($)': 'cf_pretax_cashflow',
    'Total pre-tax returns ($)': 'cf_project_return_pretax',
    'Federal ITC total income ($)': 'cf_itc_fed',
    'Federal PTC income ($)': 'cf_ptc_fed',
    'Federal tax benefit (liability) ($)': 'cf_fedtax',
    'State ITC total income ($)': 'cf_itc_sta',
    'State PTC income ($)': 'cf_ptc_sta',
    'State tax benefit (liability) ($)': 'cf_statax',
    'Total after-tax returns ($)': 'cf_project_return_aftertax',
    'After-tax cumulative IRR (%)': 'cf_project_return_aftertax_irr',
    'After-tax cumulative NPV ($)': 'cf_project_return_aftertax_npv',
    'Annual costs ($)': 'cf_annual_costs',
    'Present value of annual costs ($)': 'npv_annual_costs',
    'Present value of annual energy nominal ($)': 'npv_energy_nom',
    'LCOE Levelized cost of energy nominal (cents/kWh)': 'lcoe_nom',
    'Present value of PPA revenue ($)': 'npv_ppa_revenue',
    'Present value of annual energy nominal ($)': 'npv_energy_nom',
    'LPPA Levelized PPA price nominal (cents/kWh)': 'lppa_nom',
    'Curtailment payment revenue ($)': 'cf_curtailment_value',
}


def _get_logger():
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

    def _search_props(s: str) -> list[Any]:
        """
        Utility function to search output properties (useful in IDE debugger)
        """

        def ga(_p):
            # noinspection PyBroadException
            try:
                return getattr(soo, _p)
            except Exception:
                return None

        return [(p, ga(p)) for p in dir(soo) if s in p]

    if display_name not in _SINGLE_OWNER_OUTPUT_PROPERTIES:
        # noinspection PyBroadException
        try:
            ld = 'SAM Cash Flow Output property'
            _log.warning(f'{ld} not found for "{display_name}"')
            suggest = [(display_name, it[0]) for it in _search_props(display_name.lower().split(' ')[0])]
            suggest = "\n\t".join([f"'{sg[0]}': '{sg[1]}'" for sg in suggest])
            if len(suggest) > 0:
                _log.debug(f'{ld} suggestions for "{display_name}":\n\t{suggest}')
            else:
                _log.debug(f'No {ld } suggestions for "{display_name}" found')
                # In IDE debugger, try:
                # _search_props(display_name.lower().split(' ')[1])
                # etc.

        except Exception as e:
            _log.debug(f'Encountered exception attempting to generate suggestions for {ld} for "{display_name}": {e}"')

        return None

    prop = _SINGLE_OWNER_OUTPUT_PROPERTIES[display_name]

    if callable(prop):
        return prop(soo)

    return getattr(soo, prop)


def _get_file_path(file_name) -> str:
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), file_name)

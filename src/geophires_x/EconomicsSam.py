from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from decimal import Decimal

import numpy as np

# noinspection PyPackageRequirements
from PySAM import CustomGeneration

# noinspection PyPackageRequirements
from PySAM import Grid

# noinspection PyPackageRequirements
from PySAM import Singleowner

# noinspection PyPackageRequirements
import PySAM.Utilityrate5 as UtilityRate

import geophires_x.Model as Model
from geophires_x.EconomicsSamCashFlow import _get_single_owner_output

_SAM_CASH_FLOW_PROFILE_KEY = 'Cash Flow'


@lru_cache(maxsize=12)
def calculate_sam_economics(model: Model) -> dict[str, dict[str, Any]]:
    custom_gen = CustomGeneration.new()
    grid = Grid.from_existing(custom_gen)
    utility_rate = UtilityRate.from_existing(custom_gen)
    single_owner = Singleowner.from_existing(custom_gen)

    project_name = 'Generic_400_MWe'
    project_dir = Path(os.path.dirname(model.economics.MyPath), 'sam_economics', project_name)
    # noinspection SpellCheckingInspection
    file_names = [f'{project_name}_{module}' for module in ['custom_generation', 'grid', 'utilityrate5', 'singleowner']]
    modules = [custom_gen, grid, utility_rate, single_owner]

    for module_file, module in zip(file_names, modules):
        with open(Path(project_dir, f'{module_file}.json'), encoding='utf-8') as file:
            data = json.load(file)
            for k, v in data.items():
                if k != 'number_inputs':
                    module.value(k, v)

    for k, v in _get_single_owner_parameters(model).items():
        single_owner.value(k, v)

    for module in modules:
        module.execute()

    cash_flow = _calculate_cash_flow(model, single_owner)

    data = [
        ('LCOE (nominal)', single_owner.Outputs.lcoe_nom, 'cents/kWh'),
        ('IRR', single_owner.Outputs.project_return_aftertax_irr, '%'),
        ('NPV', single_owner.Outputs.project_return_aftertax_npv * 1e-6, 'MUSD'),
        ('CAPEX', single_owner.Outputs.adjusted_installed_cost * 1e-6, 'MUSD'),
        # ('Gross Output', gt.Outputs.gross_output, 'MW'),
        # ('Net Output', gt.Outputs.gross_output - gt.Outputs.pump_work, 'MW')
        (_SAM_CASH_FLOW_PROFILE_KEY, cash_flow, None),
    ]

    # max_field_name_len = max(len(x[0]) for x in display_data)

    ret = {}
    for e in data:
        key = e[0]
        # field_display = e[0] + ':' + ' ' * (max_field_name_len - len(e[0]) - 1)
        # print(f'{field_display}\t{sig_figs(e[1], 5)} {e[2]}')

        as_val = e[1]
        if key != _SAM_CASH_FLOW_PROFILE_KEY:
            as_val = {'value': _sig_figs(e[1], 5), 'unit': e[2]}

        ret[key] = as_val

    return ret


def _get_single_owner_parameters(model: Model) -> dict[str, Any]:
    econ = model.economics

    ret: dict[str, Any] = {}

    itc = econ.RITCValue.value
    total_capex_musd = econ.CCap.value + itc
    ret['total_installed_cost'] = total_capex_musd * 1e6

    opex_musd = econ.Coam.value
    ret['om_fixed'] = [opex_musd * 1e6]

    # FIXME provide entire generation profile
    average_net_generation_MW = _get_average_net_generation_MW(model)
    ret['system_capacity'] = average_net_generation_MW * 1e3

    geophires_ctr_tenths = Decimal(econ.CTR.value)
    fed_ratio = 0.75
    fed_rate_tenths = geophires_ctr_tenths * (Decimal(fed_ratio))
    ret['federal_tax_rate'] = [float(fed_rate_tenths * Decimal(100))]

    # state_rate_tenths = geophires_ctr_tenths - fed_rate_tenths
    state_ratio = 0.25
    state_rate_tenths = geophires_ctr_tenths * (Decimal(state_ratio))
    ret['state_tax_rate'] = [float(state_rate_tenths * Decimal(100))]

    geophires_itc_tenths = Decimal(econ.RITC.value)
    ret['itc_fed_percent'] = [float(geophires_itc_tenths * Decimal(100))]

    geophires_ptr_tenths = Decimal(econ.PTR.value)
    ret['property_tax_rate'] = float(geophires_ptr_tenths * Decimal(100))

    ret['ppa_price_input'] = [econ.ElecStartPrice.value]

    # TODO interest rate
    # TODO debt/equity ratio

    return ret


@lru_cache(maxsize=12)
def _calculate_cash_flow(model: Model, single_owner: Singleowner) -> list[list[Any]]:
    log = model.logger

    # noinspection PyUnusedLocal
    def _search_props(s: str) -> list[Any]:
        """
        Utility function to search output properties in IDE debugger
        """

        def ga(_p):
            # noinspection PyBroadException
            try:
                return getattr(_soo, _p)
            except Exception:
                return None

        return [(p, ga(p)) for p in dir(_soo) if s in p]

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
        def a(x):
            return round(x, 2)

        if row_name.endswith('($)'):

            def a(x):
                return round(x)

        return a

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

    category_row('ENERGY')
    data_row('Electricity to grid (kWh)')
    data_row('Electricity from grid (kWh)')
    data_row('Electricity to grid net (kWh)')

    blank_row()

    category_row('REVENUE')
    data_row('PPA price (cents/kWh)')
    data_row('PPA revenue ($)')
    data_row('Salvage value ($)')
    data_row('Total revenue ($)')

    blank_row()

    # TODO Property tax net assessed value ($)

    category_row('OPERATING EXPENSES')
    data_row('O&M fixed expense ($)')
    data_row('Property tax expense ($)')
    data_row('Total operating expenses ($)')

    blank_row()

    data_row('EBITDA ($)')

    blank_row()

    category_row('OPERATING ACTIVITIES')
    data_row('EBITDA ($)')
    data_row('Debt interest payment ($)')
    data_row('Cash flow from operating activities ($)')

    blank_row()

    category_row('INVESTING ACTIVITIES')
    single_value_row('Total installed cost ($)')
    single_value_row('Purchase of property ($)')
    data_row('Cash flow from investing activities ($)')

    blank_row()

    category_row('FINANCING ACTIVITIES')
    single_value_row('Issuance of equity ($)')
    single_value_row('Size of debt ($)')
    designator_row('minus:')
    data_row('Debt principal payment ($)')
    designator_row('equals:')
    data_row('Cash flow from financing activities ($)')

    blank_row()

    category_row('PROJECT RETURNS')
    category_row('Pre-tax Cash Flow:')
    data_row('Cash flow from operating activities ($)')
    data_row('Cash flow from investing activities ($)')
    data_row('Cash flow from financing activities ($)')
    data_row('Total pre-tax cash flow ($)')

    blank_row()

    category_row('Pre-tax Returns:')
    single_value_row('Issuance of equity ($)')
    data_row('Total pre-tax cash flow ($)')
    data_row('Total pre-tax returns ($)')

    blank_row()

    category_row('After-tax Returns:')
    data_row('Total pre-tax returns ($)')
    data_row('Federal ITC total income ($)')
    data_row('Federal PTC income ($)')
    data_row('Federal tax benefit (liability) ($)')
    data_row('State ITC total income ($)')
    data_row('State PTC income ($)')
    data_row('State tax benefit (liability) ($)')
    data_row('Total after-tax returns ($)')

    blank_row()

    data_row('After-tax cumulative IRR (%)')
    data_row('After-tax cumulative NPV ($)')

    blank_row()

    category_row('AFTER-TAX LCOE AND PPA PRICE')
    data_row('Annual costs ($)')
    data_row('PPA revenue ($)')
    data_row('Electricity to grid (kWh)')

    blank_row()
    single_value_row('Present value of annual costs ($)')
    single_value_row('Present value of annual energy nominal ($)')
    single_value_row('LCOE Levelized cost of energy nominal (cents/kWh)')

    blank_row()

    single_value_row('Present value of PPA revenue ($)')
    single_value_row('Present value of annual energy nominal ($)')
    single_value_row('LPPA Levelized PPA price nominal (cents/kWh)')

    blank_row()

    category_row('PROJECT STATE INCOME TAXES')
    data_row('EBITDA ($)')

    return profile


def _get_average_net_generation_MW(model: Model) -> float:
    return np.average(model.surfaceplant.NetElectricityProduced.value)


def _sig_figs(val: float, num_sig_figs: int) -> float:
    """
    TODO move to utilities, probably
    """

    if val is None:
        return None

    if isinstance(val, list) or isinstance(val, tuple):
        return [_sig_figs(v, num_sig_figs) for v in val]

    try:
        return float('%s' % float(f'%.{num_sig_figs}g' % val))  # pylint: disable=consider-using-f-string
    except TypeError:
        # TODO warn
        return val

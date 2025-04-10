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

_CASH_FLOW_PROFILE_KEY = 'Cash Flow'


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
        ('LCOE', single_owner.Outputs.lcoe_real, 'cents/kWh'),
        ('IRR', single_owner.Outputs.project_return_aftertax_irr, '%'),
        ('NPV', single_owner.Outputs.project_return_aftertax_npv * 1e-6, 'MUSD'),
        ('CAPEX', single_owner.Outputs.adjusted_installed_cost * 1e-6, 'MUSD'),
        # ('Gross Output', gt.Outputs.gross_output, 'MW'),
        # ('Net Output', gt.Outputs.gross_output - gt.Outputs.pump_work, 'MW')
        (_CASH_FLOW_PROFILE_KEY, cash_flow, None),
    ]

    # max_field_name_len = max(len(x[0]) for x in display_data)

    ret = {}
    for e in data:
        key = e[0]
        # field_display = e[0] + ':' + ' ' * (max_field_name_len - len(e[0]) - 1)
        # print(f'{field_display}\t{sig_figs(e[1], 5)} {e[2]}')

        as_val = e[1]
        if key != _CASH_FLOW_PROFILE_KEY:
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
    years = list(range(0, total_duration + 1))
    row_1 = [None] + years
    profile.append(row_1)

    def blank_row() -> None:
        profile.append([None] * (len(years) + 1))

    def category_row(cat_name: str) -> list[Any]:
        return [cat_name] + [None] * len(years)

    def data_row(row_name: str, output_data) -> list[Any]:
        return [row_name] + [round(d, 2) for d in output_data]  # TODO revisit this to audit for precision concerns

    def single_value_row(row_name: str, single_value: float) -> list[Any]:
        svr = (
            [row_name] + [single_value] + [None] * (len(years) - 1)
        )  # TODO revisit this to audit for precision concerns
        profile.append(svr)
        return svr

    profile.append(category_row('ENERGY'))
    profile.append(data_row('Electricity to grid (kWh)', _soo.cf_energy_sales))
    profile.append(data_row('Electricity from grid (kWh)', _soo.cf_energy_purchases))
    profile.append(data_row('Electricity to grid net (kWh)', _soo.cf_energy_net))
    blank_row()

    profile.append(category_row('REVENUE'))
    profile.append(data_row('PPA price (cents/kWh)', _soo.cf_ppa_price))
    profile.append(data_row('PPA revenue ($)', _soo.cf_energy_value))
    profile.append(data_row('Salvage value ($)', _soo.cf_net_salvage_value))
    profile.append(data_row('Total revenue ($)', _soo.cf_revenue_dispatch1))

    blank_row()

    profile.append(category_row('OPERATING EXPENSES'))
    profile.append(data_row('O&M fixed expense ($)', _soo.cf_om_fixed_expense))
    profile.append(data_row('Property tax expense ($)', _soo.cf_property_tax_expense))
    profile.append(data_row('Total operating expenses ($)', _soo.cf_operating_expenses))
    blank_row()

    profile.append(data_row('EBITDA ($)', _soo.cf_ebitda))
    blank_row()

    profile.append(category_row('OPERATING ACTIVITIES'))
    profile.append(data_row('EBITDA ($)', _soo.cf_ebitda))
    profile.append(data_row('Debt interest payment ($)', _soo.cf_debt_payment_interest))
    profile.append(data_row('Cash flow from operating activities ($)', _soo.cf_project_operating_activities))

    profile.append(category_row('INVESTING ACTIVITIES'))
    single_value_row('Total installed cost ($)', -1.0 * _soo.cost_installed)
    single_value_row('Purchase of property ($)', _soo.purchase_of_property)

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

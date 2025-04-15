from __future__ import annotations

import json
import os
from functools import lru_cache
from math import isnan
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
from tabulate import tabulate

from geophires_x import Model as Model
from geophires_x.EconomicsSamCashFlow import _calculate_sam_economics_cash_flow
from geophires_x.GeoPHIRESUtils import is_float, is_int
from geophires_x.Parameter import Parameter
from geophires_x.Units import convertible_unit

_SAM_CASH_FLOW_PROFILE_KEY = 'Cash Flow'
_GEOPHIRES_TO_SAM_PRICING_MODEL_RATE_CONVERSION_CONSTANT = 0.745


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

    for k, v in _get_utility_rate_parameters(model).items():
        single_owner.value(k, v)

    for k, v in _get_single_owner_parameters(model).items():
        single_owner.value(k, v)

    for module in modules:
        module.execute()

    cash_flow = _calculate_sam_economics_cash_flow(model, single_owner)

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


def get_sam_cash_flow_profile_tabulated_output(model: Model, **tabulate_kw_args) -> str:
    """
    Note model must have already calculated economics for this to work (used in Outputs)
    """

    # fmt:off
    _tabulate_kw_args = {
        'tablefmt': 'tsv',
        'floatfmt': ',.2f',
        # 'floatfmt': ':,',
        **tabulate_kw_args
    }

    # fmt:on

    def get_entry_display(entry: Any) -> str:
        if is_float(entry):
            if not isnan(float(entry)):
                entry_display = f'{entry:,.2f}' if not is_int(entry) else f'{entry:,}'
                return entry_display
        return entry

    profile_display = model.economics.sam_economics.value[_SAM_CASH_FLOW_PROFILE_KEY].copy()
    for i in range(len(profile_display)):
        for j in range(len(profile_display[i])):
            profile_display[i][j] = get_entry_display(profile_display[i][j])

    return tabulate(profile_display, **_tabulate_kw_args)


def _get_utility_rate_parameters(model: Model) -> dict[str, Any]:
    econ = model.economics

    ret: dict[str, Any] = {}

    ret['inflation_rate'] = econ.RINFL.quantity().to(convertible_unit('%')).magnitude

    max_net_kWh_produced = np.max(model.surfaceplant.NetkWhProduced.value)
    ret['degradation'] = [
        (max_net_kWh_produced - it) / max_net_kWh_produced * 100 for it in model.surfaceplant.NetkWhProduced.value
    ]

    return ret


def _get_single_owner_parameters(model: Model) -> dict[str, Any]:
    econ = model.economics

    ret: dict[str, Any] = {}

    def pct(econ_value: Parameter) -> float:
        return econ_value.quantity().to(convertible_unit('%')).magnitude

    itc = econ.RITCValue.value
    total_capex_musd = econ.CCap.value + itc
    ret['total_installed_cost'] = total_capex_musd * 1e6
    # TODO break out indirect costs (instead of lumping all into direct cost)

    opex_musd = econ.Coam.value
    ret['om_fixed'] = [opex_musd * 1e6]
    # GEOPHIRES assumes O&M fixed costs are not affected by inflation
    ret['om_fixed_escal'] = -1.0 * pct(econ.RINFL)

    # TODO project lifetime

    # TODO construction years

    # Note generation profile is generated relative to the max in _get_utility_rate_parameters
    ret['system_capacity'] = _get_max_net_generation_MW(model) * 1e3

    # TODO utilization factor = nominal capacity factor

    geophires_ctr_tenths = Decimal(econ.CTR.value)
    fed_ratio = 0.75
    fed_rate_tenths = geophires_ctr_tenths * (Decimal(fed_ratio))
    ret['federal_tax_rate'] = [float(fed_rate_tenths * Decimal(100))]

    state_ratio = 0.25
    state_rate_tenths = geophires_ctr_tenths * (Decimal(state_ratio))
    ret['state_tax_rate'] = [float(state_rate_tenths * Decimal(100))]

    geophires_itc_tenths = Decimal(econ.RITC.value)
    ret['itc_fed_percent'] = [float(geophires_itc_tenths * Decimal(100))]

    # 'Property Tax Rate'
    geophires_ptr_tenths = Decimal(econ.PTR.value)
    ret['property_tax_rate'] = float(geophires_ptr_tenths * Decimal(100))

    ret['ppa_price_input'] = [econ.ElecStartPrice.value]
    # Approximation of GEOPHIRES rate model into SAM's percent inflation model (TODO - could probably be improved)
    ppa_escalation_rate_percent = round(
        econ.ElecEscalationRate.value
        / econ.ElecStartPrice.value
        * _GEOPHIRES_TO_SAM_PRICING_MODEL_RATE_CONVERSION_CONSTANT
        * 100.0
    )
    ret['ppa_escalation'] = ppa_escalation_rate_percent

    # Debt/equity ratio ('Fraction of Investment in Bonds' parameter)
    ret['debt_percent'] = pct(econ.FIB)

    # Interest rate
    ret['real_discount_rate'] = pct(econ.discountrate)
    ret['term_int_rate'] = pct(econ.BIR)

    # TODO 'Inflated Equity Interest Rate' (may not have equivalent in SAM...?)

    ret['ibi_oth_amount'] = (econ.OtherIncentives.quantity() + econ.TotalGrant.quantity()).to('USD').magnitude

    return ret


def _get_max_net_generation_MW(model: Model) -> float:
    return np.max(model.surfaceplant.NetElectricityProduced.value)


def _get_average_net_generation_MW(model: Model) -> float:
    return np.average(model.surfaceplant.NetElectricityProduced.value)


def _sig_figs(val: float | list | tuple, num_sig_figs: int) -> float:
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

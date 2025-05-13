from __future__ import annotations

import json
import os
import pprint
from dataclasses import dataclass, field
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
from geophires_x.EconomicsUtils import BuildPricingModel
from geophires_x.GeoPHIRESUtils import is_float, is_int
from geophires_x.OptionList import EconomicModel, EndUseOptions
from geophires_x.Parameter import Parameter, OutputParameter, floatParameter
from geophires_x.Units import convertible_unit, EnergyCostUnit, CurrencyUnit, Units, PercentUnit


@dataclass
class SamEconomics:
    sam_cash_flow_profile: list[list[Any]]

    lcoe_nominal: OutputParameter = field(
        default_factory=lambda: OutputParameter(
            UnitType=Units.ENERGYCOST,
            CurrentUnits=EnergyCostUnit.CENTSSPERKWH,
        )
    )
    capex: OutputParameter = field(
        default_factory=lambda: OutputParameter(
            UnitType=Units.CURRENCY,
            CurrentUnits=CurrencyUnit.MDOLLARS,
        )
    )
    project_npv: OutputParameter = field(
        default_factory=lambda: OutputParameter(
            UnitType=Units.CURRENCY,
            CurrentUnits=CurrencyUnit.MDOLLARS,
        )
    )
    project_irr: OutputParameter = field(
        default_factory=lambda: OutputParameter(
            UnitType=Units.PERCENT,
            CurrentUnits=PercentUnit.PERCENT,
        )
    )


def validate_read_parameters(model: Model):
    def _inv_msg(param_name: str, invalid_value: Any, supported_description: str) -> str:
        return (
            f'Invalid {param_name} ({invalid_value}) for '
            f'{EconomicModel.SAM_SINGLE_OWNER_PPA.name} economic model. '
            f'{EconomicModel.SAM_SINGLE_OWNER_PPA.name} only supports '
            f'{supported_description}.'
        )

    if model.surfaceplant.enduse_option.value != EndUseOptions.ELECTRICITY:
        raise ValueError(
            _inv_msg(
                model.surfaceplant.enduse_option.Name,
                model.surfaceplant.enduse_option.value.value,
                f'{EndUseOptions.ELECTRICITY.name} End-Use Option',
            )
        )

    if model.surfaceplant.construction_years.value != 1:
        raise ValueError(
            _inv_msg(
                model.surfaceplant.construction_years.Name,
                model.surfaceplant.construction_years.value,
                f'{model.surfaceplant.construction_years.Name}  = 1',
            )
        )

    gtr: floatParameter = model.economics.GTR
    if gtr.Provided:
        model.logger.warning(
            f'{gtr.Name} provided value ({gtr.value}) will be ignored. (SAM Economics tax rates '
            f'are determined from {model.economics.CTR.Name} and {model.economics.PTR.Name}.)'
        )

    eir: floatParameter = model.economics.EIR
    if eir.Provided:
        model.logger.warning(
            f'{eir.Name} provided value ({eir.value}) will be ignored. (SAM Economics does not support {eir.Name}.)'
        )


@lru_cache(maxsize=12)
def calculate_sam_economics(model: Model) -> SamEconomics:
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

    module_param_mappings = [
        ('Custom Generation', _get_custom_gen_parameters, custom_gen),
        ('Utility Rate', _get_utility_rate_parameters, utility_rate),
        ('Single Owner', _get_single_owner_parameters, single_owner),
    ]

    mapping_result: list[list[Any]] = [['SAM Module', 'Parameter', 'Value']]
    for mapping in module_param_mappings:
        module_name = mapping[0]
        module_params: dict[str, Any] = mapping[1](model)
        for k, v in module_params.items():
            mapping[2].value(k, v)
            mapping_result.append([module_name, k, v])

    mapping_tabulated = tabulate(mapping_result, **{'floatfmt': ',.2f'})
    mapping_msg = f'SAM Economics Parameter Mapping:\n{mapping_tabulated}'
    model.logger.info(mapping_msg)

    for module in modules:
        module.execute()

    cash_flow = _calculate_sam_economics_cash_flow(model, single_owner)

    def sf(_v: float) -> float:
        return _sig_figs(_v, 5)

    sam_economics: SamEconomics = SamEconomics(sam_cash_flow_profile=cash_flow)
    sam_economics.lcoe_nominal.value = sf(single_owner.Outputs.lcoe_nom)
    sam_economics.project_irr.value = sf(single_owner.Outputs.project_return_aftertax_irr)
    sam_economics.project_npv.value = sf(single_owner.Outputs.project_return_aftertax_npv * 1e-6)
    sam_economics.capex.value = single_owner.Outputs.adjusted_installed_cost * 1e-6

    return sam_economics


def get_sam_cash_flow_profile_tabulated_output(model: Model, **tabulate_kw_args) -> str:
    """
    Note model must have already calculated economics for this to work (used in Outputs)
    """

    # fmt:off
    _tabulate_kw_args = {
        'tablefmt': 'tsv',
        'floatfmt': ',.2f',
        **tabulate_kw_args
    }

    # fmt:on

    def get_entry_display(entry: Any) -> str:
        if is_float(entry):
            if not isnan(float(entry)):
                if not is_int(entry):
                    # skip decimals for large numbers like SAM does
                    entry_display = f'{entry:,.2f}' if entry < 1e6 else f'{entry:,.0f}'
                else:
                    entry_display = f'{entry:,}'
                return entry_display
        return entry

    profile_display = model.economics.sam_economics.sam_cash_flow_profile.copy()
    for i in range(len(profile_display)):
        for j in range(len(profile_display[i])):
            profile_display[i][j] = get_entry_display(profile_display[i][j])

    return tabulate(profile_display, **_tabulate_kw_args)


def _get_custom_gen_parameters(model: Model) -> dict[str, Any]:
    # fmt:off
    ret: dict[str, Any] = {
        # Project lifetime
        'analysis_period': model.surfaceplant.plant_lifetime.value,
        'user_capacity_factor': _pct(model.surfaceplant.utilization_factor),
    }
    # fmt:on

    return ret


def _get_utility_rate_parameters(m: Model) -> dict[str, Any]:
    econ = m.economics

    ret: dict[str, Any] = {}

    ret['inflation_rate'] = econ.RINFL.quantity().to(convertible_unit('%')).magnitude

    max_total_kWh_produced = np.max(m.surfaceplant.TotalkWhProduced.value)
    degradation_total = [
        (max_total_kWh_produced - it) / max_total_kWh_produced * 100 for it in m.surfaceplant.NetkWhProduced.value
    ]

    ret['degradation'] = degradation_total

    return ret


def _get_single_owner_parameters(model: Model) -> dict[str, Any]:
    """
    TODO:
        - Construction years
        - Break out indirect costs (instead of lumping all into direct cost):
            https://github.com/NREL/GEOPHIRES-X/issues/383
        - Inflated Equity Interest Rate: doesn't appear to have equivalent in SAM, but should probably be supported
            in some form.
    """
    econ = model.economics

    # noinspection PyDictCreation
    ret: dict[str, Any] = {}

    ret['analysis_period'] = model.surfaceplant.plant_lifetime.value

    itc = econ.RITCValue.quantity()
    total_capex = econ.CCap.quantity() + itc

    # 'Inflation Rate During Construction'
    construction_additional_cost = econ.inflrateconstruction.value * total_capex

    ret['total_installed_cost'] = (total_capex + construction_additional_cost).to('USD').magnitude

    opex_musd = econ.Coam.value
    ret['om_fixed'] = [opex_musd * 1e6]
    # GEOPHIRES assumes O&M fixed costs are not affected by inflation
    ret['om_fixed_escal'] = -1.0 * _pct(econ.RINFL)

    # Note generation profile is generated relative to the max in _get_utility_rate_parameters
    ret['system_capacity'] = _get_max_total_generation_kW(model)

    ret['federal_tax_rate'], ret['state_tax_rate'] = _get_fed_and_state_tax_rates(econ.CTR.value)

    geophires_itc_tenths = Decimal(econ.RITC.value)
    ret['itc_fed_percent'] = [float(geophires_itc_tenths * Decimal(100))]

    if econ.PTCElec.Provided:
        ret['ptc_fed_amount'] = [econ.PTCElec.quantity().to(convertible_unit('USD/kWh')).magnitude]
        ret['ptc_fed_term'] = econ.PTCDuration.quantity().to(convertible_unit('yr')).magnitude

        if econ.PTCInflationAdjusted.value:
            ret['ptc_fed_escal'] = _pct(econ.RINFL)

    # 'Property Tax Rate'
    geophires_ptr_tenths = Decimal(econ.PTR.value)
    ret['property_tax_rate'] = float(geophires_ptr_tenths * Decimal(100))

    ret['ppa_price_input'] = _ppa_pricing_model(
        model.surfaceplant.plant_lifetime.value,
        econ.ElecStartPrice.value,
        econ.ElecEndPrice.value,
        econ.ElecEscalationStart.value,
        econ.ElecEscalationRate.value,
    )

    # Debt/equity ratio ('Fraction of Investment in Bonds' parameter)
    ret['debt_percent'] = _pct(econ.FIB)

    # Interest rate
    ret['real_discount_rate'] = _pct(econ.discountrate)

    # Project lifetime
    ret['term_tenor'] = model.surfaceplant.plant_lifetime.value
    ret['term_int_rate'] = _pct(econ.BIR)

    ret['ibi_oth_amount'] = (econ.OtherIncentives.quantity() + econ.TotalGrant.quantity()).to('USD').magnitude

    return ret


def _get_fed_and_state_tax_rates(geophires_ctr_tenths: float) -> tuple[list[float]]:
    geophires_ctr_tenths = Decimal(geophires_ctr_tenths)
    max_fed_rate_tenths = Decimal(0.21)
    fed_rate_tenths = min(geophires_ctr_tenths, max_fed_rate_tenths)

    state_rate_tenths = max(0, geophires_ctr_tenths - fed_rate_tenths)

    def ret_val(val_tenths: Decimal) -> list[float]:
        return [round(float(val_tenths * Decimal(100)), 2)]

    return ret_val(fed_rate_tenths), ret_val(state_rate_tenths)


def _pct(econ_value: Parameter) -> float:
    return econ_value.quantity().to(convertible_unit('%')).magnitude


def _ppa_pricing_model(
    plant_lifetime: int, start_price: float, end_price: float, escalation_start_year: int, escalation_rate: float
) -> list:
    # See relevant comment in geophires_x.EconomicsUtils.BuildPricingModel re:
    # https://github.com/NREL/GEOPHIRES-X/issues/340?title=Price+Escalation+Start+Year+seemingly+off+by+1.
    # We use the same utility method here for the sake of consistency despite technical incorrectness.
    return BuildPricingModel(
        plant_lifetime, start_price, end_price, escalation_start_year, escalation_rate, [0] * plant_lifetime
    )


def _get_max_total_generation_kW(model: Model) -> float:
    return np.max(model.surfaceplant.ElectricityProduced.quantity().to(convertible_unit('kW')).magnitude)


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

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from functools import lru_cache
from math import isnan
from pathlib import Path
from typing import Any

from decimal import Decimal

import numpy as np
import numpy_financial as npf

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
from geophires_x.EconomicsUtils import (
    BuildPricingModel,
    wacc_output_parameter,
    nominal_discount_rate_parameter,
    after_tax_irr_parameter,
    moic_parameter,
    project_vir_parameter,
)
from geophires_x.GeoPHIRESUtils import is_float, is_int
from geophires_x.OptionList import EconomicModel, EndUseOptions
from geophires_x.Parameter import Parameter, OutputParameter, floatParameter
from geophires_x.Units import convertible_unit, EnergyCostUnit, CurrencyUnit, Units, PercentUnit


@dataclass
class SamEconomicsCalculations:
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

    after_tax_irr: OutputParameter = field(default_factory=after_tax_irr_parameter)
    nominal_discount_rate: OutputParameter = field(default_factory=nominal_discount_rate_parameter)
    wacc: OutputParameter = field(default_factory=wacc_output_parameter)
    moic: OutputParameter = field(default_factory=moic_parameter)
    project_vir: OutputParameter = field(default_factory=project_vir_parameter)


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
def calculate_sam_economics(model: Model) -> SamEconomicsCalculations:
    custom_gen = CustomGeneration.new()
    grid = Grid.from_existing(custom_gen)
    utility_rate = UtilityRate.from_existing(custom_gen)
    single_owner: Singleowner = Singleowner.from_existing(custom_gen)

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

    def sf(_v: float, num_sig_figs: int = 5) -> float:
        return _sig_figs(_v, num_sig_figs)

    sam_economics: SamEconomicsCalculations = SamEconomicsCalculations(sam_cash_flow_profile=cash_flow)
    sam_economics.lcoe_nominal.value = sf(single_owner.Outputs.lcoe_nom)
    sam_economics.after_tax_irr.value = sf(_get_after_tax_irr_pct(single_owner, cash_flow, model))

    sam_economics.project_npv.value = sf(single_owner.Outputs.project_return_aftertax_npv * 1e-6)
    sam_economics.capex.value = single_owner.Outputs.adjusted_installed_cost * 1e-6

    sam_economics.nominal_discount_rate.value, sam_economics.wacc.value = _calculate_nominal_discount_rate_and_wacc(
        model, single_owner
    )
    sam_economics.moic.value = _calculate_moic(cash_flow, model)
    sam_economics.project_vir.value = _calculate_project_vir(cash_flow, model)

    return sam_economics


def _get_after_tax_irr_pct(single_owner: Singleowner, cash_flow: list[list[Any]], model: Model) -> float:
    after_tax_irr_pct = single_owner.Outputs.project_return_aftertax_irr
    if math.isnan(after_tax_irr_pct):
        try:
            after_tax_returns_cash_flow = _cash_flow_profile_row(cash_flow, 'Total after-tax returns ($)')
            after_tax_irr_pct = npf.irr(after_tax_returns_cash_flow) * 100.0
            model.logger.info(f'After-tax IRR was NaN, calculated with numpy-financial: {after_tax_irr_pct}%')
        except Exception as e:
            model.logger.warning(f'After-tax IRR was NaN and calculation with numpy-financial failed: {e}')

    return after_tax_irr_pct


def _cash_flow_profile_row(cash_flow: list[list[Any]], row_name: str) -> list[Any]:
    return next(row for row in cash_flow if len(row) > 0 and row[0] == row_name)[1:]  # type: ignore[no-any-return]


def _calculate_nominal_discount_rate_and_wacc(model: Model, single_owner: Singleowner) -> tuple[float]:
    """
    Calculation per SAM Help -> Financial Parameters -> Commercial -> Commercial Loan Parameters -> WACC

    :return: tuple of Nominal Discount Rate (%), WACC (%)
    """

    econ = model.economics
    nominal_discount_rate_pct = ((1 + econ.discountrate.value) * (1 + econ.RINFL.value) - 1) * 100
    fed_tax_rate = max(single_owner.Outputs.cf_federal_tax_frac)
    state_tax_rate = max(single_owner.Outputs.cf_state_tax_frac)
    effective_tax_rate = (fed_tax_rate * (1 - state_tax_rate) + state_tax_rate) * 100
    debt_fraction = single_owner.Outputs.debt_fraction / 100
    wacc_pct = (
        nominal_discount_rate_pct / 100 * (1 - debt_fraction)
        + debt_fraction * econ.BIR.value * (1 - effective_tax_rate / 100)
    ) * 100

    return nominal_discount_rate_pct, wacc_pct


def _calculate_moic(cash_flow: list[list[Any]], model) -> float | None:
    try:
        total_capital_invested_USD: Decimal = Decimal(_cash_flow_profile_row(cash_flow, 'Issuance of equity ($)')[0])
        total_value_received_from_investment_USD: Decimal = sum(
            [Decimal(it) for it in _cash_flow_profile_row(cash_flow, 'Total pre-tax returns ($)')]
        )
        return float(total_value_received_from_investment_USD / total_capital_invested_USD)
    except Exception as e:
        model.logger.error(f'Encountered exception calculating MOIC: {e}')
        return None


def _calculate_project_vir(cash_flow: list[list[Any]], model) -> float | None:
    """
    VIR = PV(Future Cash Flows) / |CF_0|
    Where CF_0 is the cash flow at Year 0 (the initial investment).
    NPV = CF_0 + PV(Future Cash Flows)
    PV(Future Cash Flows) = NPV - CF_0
    """
    try:
        npv_USD = Decimal(_cash_flow_profile_row(cash_flow, 'After-tax cumulative NPV ($)')[-1])
        cf_0_USD = Decimal(_cash_flow_profile_row(cash_flow, 'Total after-tax returns ($)')[0])
        pv_of_future_cash_flows_USD = npv_USD - cf_0_USD
        vir = pv_of_future_cash_flows_USD / abs(cf_0_USD)

        return float(vir)
    except Exception as e:
        model.logger.error(f'Encountered exception calculating Project VIR: {e}')
        return None


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

    profile_display = model.economics.sam_economics_calculations.sam_cash_flow_profile.copy()
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
    """
    econ = model.economics

    # noinspection PyDictCreation
    ret: dict[str, Any] = {}

    ret['analysis_period'] = model.surfaceplant.plant_lifetime.value

    # SAM docs claim that specifying flip target year, aka "year in which you want the IRR to be achieved" influences
    # how after-tax cumulative IRR is reported (https://samrepo.nrelcloud.org/help/mtf_irr.html). This claim seems to
    # be erroneous, however, as setting this value appears to have no effect in either the SAM desktop app nor when
    # calling with PySAM. But, we set it here anyway for the sake of technical compliance.
    ret['flip_target_year'] = model.surfaceplant.plant_lifetime.value

    itc = econ.RITCValue.quantity()
    total_capex = econ.CCap.quantity() + itc
    ret['total_installed_cost'] = (total_capex * (1 + econ.inflrateconstruction.value)).to('USD').magnitude

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

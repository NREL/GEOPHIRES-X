from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from geophires_x.GeoPHIRESUtils import is_float
from scipy.interpolate.interpolate import interp1d

_TOTAL_AFTER_TAX_RETURNS_CASH_FLOW_ROW_NAME = 'Total after-tax returns ($)'
_IDC_CASH_FLOW_ROW_NAME = 'Debt interest payment ($)'


@dataclass
class PreRevenueCostsAndCashflow:
    total_installed_cost_usd: float
    construction_financing_cost_usd: float
    debt_balance_usd: float
    inflation_cost_usd: float = 0.0

    pre_revenue_cash_flow_profile: list[list[float | str]] = field(default_factory=list)

    @property
    def effective_debt_percent(self) -> float:
        return self.debt_balance_usd / self.total_installed_cost_usd * 100.0

    @property
    def total_after_tax_returns_cash_flow_usd(self):
        return self.pre_revenue_cash_flow_profile_dict[_TOTAL_AFTER_TAX_RETURNS_CASH_FLOW_ROW_NAME]

    @property
    def pre_revenue_cash_flow_profile_dict(self) -> dict[str, list[float]]:
        """Maps SAM's row names (str) to a list of pre-revenue values"""
        ret = {}

        for i in range(len(self.pre_revenue_cash_flow_profile)):
            row_name = self.pre_revenue_cash_flow_profile[i][0]
            if row_name == '':
                continue

            row_name = row_name.replace(f'{_CONSTRUCTION_LINE_ITEM_DESIGNATOR} ', '')

            row_values = self.pre_revenue_cash_flow_profile[i][1:]
            ret[row_name] = row_values

        return ret

    @property
    def interest_during_construction_usd(self) -> float:
        return sum(
            [float(it) for it in self.pre_revenue_cash_flow_profile_dict[_IDC_CASH_FLOW_ROW_NAME] if is_float(it)]
        )


def calculate_pre_revenue_costs_and_cashflow(model: 'Model') -> PreRevenueCostsAndCashflow:
    econ = model.economics
    if econ.inflrateconstruction.Provided:
        pre_revenue_inflation_rate = econ.inflrateconstruction.quantity().to('dimensionless').magnitude
    else:
        pre_revenue_inflation_rate = econ.RINFL.quantity().to('dimensionless').magnitude

    pre_revenue_bond_interest_rate_param = econ.BIR
    if econ.bond_interest_rate_during_construction.Provided:
        pre_revenue_bond_interest_rate_param = econ.bond_interest_rate_during_construction
    pre_revenue_bond_interest_rate = pre_revenue_bond_interest_rate_param.quantity().to('dimensionless').magnitude

    construction_years: int = model.surfaceplant.construction_years.value

    # Translate from negative year index input value to start-year-0-indexed calculation value
    debt_financing_start_year: int = (
        construction_years - abs(econ.bond_financing_start_year.value) if econ.bond_financing_start_year.Provided else 0
    )

    return _calculate_pre_revenue_costs_and_cashflow(
        total_overnight_capex_usd=econ.CCap.quantity().to('USD').magnitude,
        pre_revenue_years_count=construction_years,
        phased_capex_schedule=econ.construction_capex_schedule.value,
        pre_revenue_bond_interest_rate=pre_revenue_bond_interest_rate,
        inflation_rate=pre_revenue_inflation_rate,
        debt_fraction=econ.FIB.quantity().to('dimensionless').magnitude,
        debt_financing_start_year=debt_financing_start_year,
        logger=model.logger,
    )


_CONSTRUCTION_LINE_ITEM_DESIGNATOR = '[construction]'


def _calculate_pre_revenue_costs_and_cashflow(
    total_overnight_capex_usd: float,
    pre_revenue_years_count: int,
    phased_capex_schedule: list[float],
    pre_revenue_bond_interest_rate: float,
    inflation_rate: float,
    debt_fraction: float,
    debt_financing_start_year: int,
    logger: logging.Logger,
) -> PreRevenueCostsAndCashflow:
    """
    Calculates the true capitalized cost and interest during pre-revenue years (exploration/permitting/appraisal,
    construction) by simulating a year-by-year phased expenditure with inflation.

    Also builds a pre-revenue cash flow profile for constructionrevenue years.
    """

    logger.info(f"Using Phased CAPEX Schedule: {phased_capex_schedule}")

    current_debt_balance_usd = 0.0
    total_capitalized_cost_usd = 0.0
    total_interest_accrued_usd = 0.0
    total_inflation_cost_usd = 0.0

    capex_spend_vec: list[float] = []
    equity_spend_vec: list[float] = []
    debt_draw_vec: list[float] = []
    debt_balance_usd_vec: list[float] = []
    interest_accrued_vec: list[float] = []

    for year_index in range(pre_revenue_years_count):
        base_capex_this_year_usd = total_overnight_capex_usd * phased_capex_schedule[year_index]

        inflation_factor = (1.0 + inflation_rate) ** (year_index + 1)
        inflation_cost_this_year_usd = base_capex_this_year_usd * (inflation_factor - 1.0)

        capex_this_year_usd = base_capex_this_year_usd + inflation_cost_this_year_usd

        # Interest is calculated on the opening balance (from previous years' draws)
        interest_this_year_usd = current_debt_balance_usd * pre_revenue_bond_interest_rate

        debt_fraction_this_year = debt_fraction if year_index >= debt_financing_start_year else 0
        new_debt_draw_usd = capex_this_year_usd * debt_fraction_this_year

        # Equity spend is the cash portion of CAPEX not funded by new debt
        equity_spent_this_year_usd = capex_this_year_usd - new_debt_draw_usd

        capex_spend_vec.append(capex_this_year_usd)
        equity_spend_vec.append(equity_spent_this_year_usd)
        debt_draw_vec.append(new_debt_draw_usd)
        interest_accrued_vec.append(interest_this_year_usd)

        total_capitalized_cost_usd += capex_this_year_usd + interest_this_year_usd
        total_interest_accrued_usd += interest_this_year_usd
        total_inflation_cost_usd += inflation_cost_this_year_usd

        current_debt_balance_usd += new_debt_draw_usd + interest_this_year_usd
        debt_balance_usd_vec.append(current_debt_balance_usd)

    logger.info(
        f"Phased CAPEX calculation complete: "
        f"Total Installed Cost: ${total_capitalized_cost_usd:,.2f}, "
        f"Final Debt Balance: ${current_debt_balance_usd:,.2f}, "
        f"Total Capitalized Interest: ${total_interest_accrued_usd:,.2f}"
    )

    pre_revenue_cf_profile: list[list[float | str]] = []

    blank_row = [''] * len(capex_spend_vec)

    def _rnd(k_, v_: Any) -> Any:
        return round(float(v_)) if k_.endswith('($)') and is_float(v_) else v_

    def _append_row(row_name: str, row_vals: list[float | str]) -> None:
        row_name_adjusted = row_name.split('(')[0] + f'{_CONSTRUCTION_LINE_ITEM_DESIGNATOR} (' + row_name.split('(')[1]
        pre_revenue_cf_profile.append([row_name_adjusted] + [_rnd(row_name, it) for it in row_vals])

    # --- Investing Activities ---
    _append_row(f'Purchase of property ($)', [-x for x in capex_spend_vec])
    _append_row(
        f'Cash flow from investing activities ($)',
        # 'CAPEX spend ($)'
        [-x for x in capex_spend_vec],
    )

    pre_revenue_cf_profile.append(blank_row.copy())

    # --- Financing Activities ---
    _append_row(
        f'Issuance of equity ($)',
        [abs(it) for it in equity_spend_vec],
    )

    _append_row(
        # 'Debt draw ($)'
        f'Issuance of debt ($)',
        debt_draw_vec,
    )

    _append_row(
        f'Debt balance ($)'
        # 'Size of debt ($)'
        ,
        debt_balance_usd_vec,
    )

    _append_row(_IDC_CASH_FLOW_ROW_NAME, interest_accrued_vec)

    _append_row(f'Cash flow from financing activities ($)', [e + d for e, d in zip(equity_spend_vec, debt_draw_vec)])

    pre_revenue_cf_profile.append(blank_row.copy())

    # --- Returns ---
    equity_cash_flow_usd = [-x for x in equity_spend_vec]
    _append_row(f'Total pre-tax returns ($)', equity_cash_flow_usd)
    _append_row(_TOTAL_AFTER_TAX_RETURNS_CASH_FLOW_ROW_NAME, equity_cash_flow_usd)

    return PreRevenueCostsAndCashflow(
        total_installed_cost_usd=total_capitalized_cost_usd,
        construction_financing_cost_usd=total_interest_accrued_usd,
        debt_balance_usd=current_debt_balance_usd,
        inflation_cost_usd=total_inflation_cost_usd,
        # pre_revenue_cash_flow_profile_dict=pre_revenue_cf_profile_dict,
        pre_revenue_cash_flow_profile=pre_revenue_cf_profile,
    )


def adjust_phased_schedule_to_new_length(original_schedule: list[float], new_length: int) -> list[float]:
    """
    Adjusts a schedule (list of fractions) to a new length by interpolation,
    then normalizes the result to ensure it sums to 1.0.

    Args:
        original_schedule: The initial list of fractional values.
        new_length: The desired length of the new schedule.

    Returns:
        A new schedule of the desired length with its values summing to 1.0.
    """

    if new_length < 1:
        raise ValueError

    if not original_schedule:
        raise ValueError

    original_len = len(original_schedule)
    if original_len == new_length:
        return original_schedule

    if original_len == 1:
        # Interpolation is not possible with a single value; return a constant schedule
        return [1.0 / new_length] * new_length

    # Create an interpolation function based on the original schedule
    x_original = np.arange(original_len)
    y_original = np.array(original_schedule)

    # Use linear interpolation, and extrapolate if the new schedule is longer
    f = interp1d(x_original, y_original, kind='nearest', fill_value="extrapolate")

    # Create new x-points for the desired length
    x_new = np.linspace(0, original_len - 1, new_length)

    # Get the new, projected y-values
    y_new = f(x_new)

    # Normalize the new schedule so it sums to 1.0
    total = np.sum(y_new)
    if total == 0:
        # Avoid division by zero; return an equal distribution
        return [1.0 / new_length] * new_length

    normalized_schedule = (y_new / total).tolist()
    return normalized_schedule

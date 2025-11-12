from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
from scipy.interpolate.interpolate import interp1d

from geophires_x.Parameter import OutputParameter
from geophires_x.Units import Units, PercentUnit, TimeUnit, CurrencyUnit, CurrencyFrequencyUnit


def BuildPricingModel(plantlifetime: int, StartPrice: float, EndPrice: float,
                      EscalationStartYear: int, EscalationRate: float, PTCAddition: list) -> list:
    """
    BuildPricingModel builds the price model array for the project lifetime.  It is used to calculate the revenue
    stream for the project.
    :param plantlifetime: The lifetime of the project in years
    :type plantlifetime: int
    :param StartPrice: The price in the first year of the project in $/kWh
    :type StartPrice: float
    :param EndPrice: The price in the last year of the project in $/kWh
    :type EndPrice: float
    :param EscalationStartYear: The year the price escalation starts in years (not including construction years) in years
    :type EscalationStartYear: int
    :param EscalationRate: The rate of price escalation in $/kWh/year
    :type EscalationRate: float
    :param PTCAddition: The PTC addition array for the project in $/kWh
    :type PTCAddition: list
    :return: Price: The price model array for the project in $/kWh
    :rtype: list
    """
    Price = [0.0] * plantlifetime
    for i in range(0, plantlifetime, 1):
        Price[i] = StartPrice
        if i >= EscalationStartYear:
            # TODO: This is arguably an unwanted/incorrect interpretation of escalation start year, see
            # https://github.com/NREL/GEOPHIRES-X/issues/340?title=Price+Escalation+Start+Year+seemingly+off+by+1
            Price[i] = Price[i] + ((i - EscalationStartYear) * EscalationRate)
        if Price[i] > EndPrice:
            Price[i] = EndPrice
        Price[i] = Price[i] + PTCAddition[i]
    return Price


def moic_parameter() -> OutputParameter:
    return OutputParameter(
        "Project MOIC",
        ToolTipText='Project Multiple of Invested Capital. For SAM Economic Models, this is calculated as the '
                    'sum of Total pre-tax returns (total value received) '
                    'divided by Issuance of equity (total capital invested).',
        UnitType=Units.PERCENT,
        PreferredUnits=PercentUnit.TENTH,
        CurrentUnits=PercentUnit.TENTH
    )


def project_vir_parameter() -> OutputParameter:
    return OutputParameter(
        "Project Value Investment Ratio",
        display_name='Project VIR=PI=PIR',
        UnitType=Units.PERCENT,
        PreferredUnits=PercentUnit.TENTH,
        CurrentUnits=PercentUnit.TENTH
    )


def project_payback_period_parameter() -> OutputParameter:
    return OutputParameter(
        "Project Payback Period",
        UnitType=Units.TIME,
        PreferredUnits=TimeUnit.YEAR,
        CurrentUnits=TimeUnit.YEAR,
        ToolTipText='The time at which cumulative cash flow reaches zero. '
                    'For projects that never pay back, the calculated value will be "N/A". '
                    'For SAM Economic Models, total after-tax returns are used to calculate cumulative cash flow.',
    )


def after_tax_irr_parameter() -> OutputParameter:
    return OutputParameter(
        Name='After-tax IRR',
        UnitType=Units.PERCENT,
        CurrentUnits=PercentUnit.PERCENT,
        PreferredUnits=PercentUnit.PERCENT,
        ToolTipText='The After-tax IRR (internal rate of return) is the nominal discount rate that corresponds to '
                    'a net present value (NPV) of zero for PPA SAM Economic models. '
                    'See https://samrepo.nrelcloud.org/help/mtf_irr.html. If SAM calculates After-tax IRR as NaN, '
                    'numpy-financial.irr (https://numpy.org/numpy-financial/latest/irr.html) '
                    'is used to calculate the value from SAM\'s total after-tax returns.'
    )


def real_discount_rate_parameter() -> OutputParameter:
    return OutputParameter(
        Name="Real Discount Rate",
        UnitType=Units.PERCENT,
        CurrentUnits=PercentUnit.PERCENT,
        PreferredUnits=PercentUnit.PERCENT,
    )


def nominal_discount_rate_parameter() -> OutputParameter:
    return OutputParameter(
        Name="Nominal Discount Rate",
        ToolTipText="Nominal Discount Rate is displayed for SAM Economic Models. "
                    "It is calculated "
                    "per https://samrepo.nrelcloud.org/help/fin_single_owner.html?q=nominal+discount+rate: "
                    "Nominal Discount Rate = [ ( 1 + Real Discount Rate ÷ 100 ) "
                    "× ( 1 + Inflation Rate ÷ 100 ) - 1 ] × 100.",
        UnitType=Units.PERCENT,
        CurrentUnits=PercentUnit.PERCENT,
        PreferredUnits=PercentUnit.PERCENT,
    )


def wacc_output_parameter() -> OutputParameter:
    return OutputParameter(
        Name='WACC',
        ToolTipText='Weighted Average Cost of Capital displayed for SAM Economic Models. '
                    'It is calculated per https://samrepo.nrelcloud.org/help/fin_commercial.html?q=wacc: '
                    'WACC = [ Nominal Discount Rate ÷ 100 × (1 - Debt Percent ÷ 100) '
                    '+ Debt Percent ÷ 100 × Loan Rate ÷ 100 ×  (1 - Effective Tax Rate ÷ 100 ) ] × 100; '
                    'Effective Tax Rate = [ Federal Tax Rate ÷ 100 × ( 1 - State Tax Rate ÷ 100 ) '
                    '+ State Tax Rate ÷ 100 ] × 100; ',
        UnitType=Units.PERCENT,
        CurrentUnits=PercentUnit.PERCENT,
        PreferredUnits=PercentUnit.PERCENT,
    )


def inflation_cost_during_construction_output_parameter() -> OutputParameter:
    return OutputParameter(
        Name='Inflation costs during construction',
        UnitType=Units.CURRENCY,
        PreferredUnits=CurrencyUnit.MDOLLARS,
        CurrentUnits=CurrencyUnit.MDOLLARS,
        ToolTipText='The calculated amount of cost escalation due to inflation over the construction period.'
    )


def total_capex_parameter_output_parameter() -> OutputParameter:
    return OutputParameter(
        Name='Total CAPEX',
        UnitType=Units.CURRENCY,
        CurrentUnits=CurrencyUnit.MDOLLARS,
        PreferredUnits=CurrencyUnit.MDOLLARS,
        ToolTipText='The total capital expenditure (CAPEX) required to construct the plant. '
                    'This value includes all direct and indirect costs, and contingency. '
                    'For SAM Economic models, it also includes any cost escalation from inflation during construction. '
                    'It is used as the total installed cost input for SAM Economic Models.'
    )


def royalty_cost_output_parameter() -> OutputParameter:
    return OutputParameter(
            Name='Royalty Cost',
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.DOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.DOLLARSPERYEAR,
            ToolTipText='The annual costs paid to a royalty holder, calculated as a percentage of the '
                        'project\'s gross annual revenue. This is modeled as a variable operating expense.'
        )


@dataclass
class PreRevenueCostsAndCashflow:
    total_installed_cost_usd: float
    construction_financing_cost_usd: float
    debt_balance_usd: float
    inflation_cost_usd: float = 0.0
    pre_revenue_equity_cash_flow_usd: list[float] = field(default_factory=list)

    @property
    def effective_debt_percent(self) -> float:
        return self.debt_balance_usd / self.total_installed_cost_usd * 100.0


def calculate_pre_revenue_costs_and_cashflow(model:'Model') -> PreRevenueCostsAndCashflow:
    econ = model.economics
    if econ.inflrateconstruction.Provided:
        pre_revenue_inflation_rate = econ.inflrateconstruction.quantity().to('dimensionless').magnitude
    else:
        pre_revenue_inflation_rate = econ.RINFL.quantity().to('dimensionless').magnitude


    return _calculate_pre_revenue_costs_and_cashflow(
        total_overnight_capex_usd=econ.CCap.quantity().to('USD').magnitude,
        # pre_revenue_years_count=pre_revenue_years,
        pre_revenue_years_count=model.surfaceplant.construction_years.value,
        phased_capex_schedule=econ.construction_capex_schedule.value,
        pre_revenue_bond_interest_rate=econ.BIR.quantity().to('dimensionless').magnitude,
        inflation_rate=pre_revenue_inflation_rate,
        debt_fraction=econ.FIB.quantity().to('dimensionless').magnitude,
        debt_financing_start_year=econ.bond_financing_start_year.value,
        logger=model.logger,
    )


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
    """

    logger.info(f"Using Phased CAPEX Schedule: {phased_capex_schedule}")

    current_debt_balance_usd = 0.0
    total_capitalized_cost_usd = 0.0
    total_interest_accrued_usd = 0.0
    total_inflation_cost_usd = 0.0
    cash_flow_usd: list[float] = []
    equity_cash_flow_usd: list[float] = []

    for year_index in range(pre_revenue_years_count):
        # Calculate base (overnight) CAPEX for this year
        base_capex_this_year_usd = total_overnight_capex_usd * phased_capex_schedule[year_index]

        inflation_factor = (1.0 + inflation_rate) ** (year_index + 1)
        inflation_cost_this_year_usd = base_capex_this_year_usd * (inflation_factor - 1.0)

        # Total CAPEX spent this year (including inflation)
        capex_this_year_usd = base_capex_this_year_usd + inflation_cost_this_year_usd
        cash_flow_usd.append(-capex_this_year_usd)

        # Interest is calculated on the opening balance (from previous years' draws)
        interest_this_year_usd = current_debt_balance_usd * pre_revenue_bond_interest_rate

        debt_fraction_this_year = debt_fraction if year_index >= debt_financing_start_year else 0
        new_debt_draw_usd = capex_this_year_usd * debt_fraction_this_year
        equity_cash_flow_usd.append(-(capex_this_year_usd-new_debt_draw_usd))

        # Add this year's direct cost AND capitalized interest to the total project cost basis
        total_capitalized_cost_usd += capex_this_year_usd + interest_this_year_usd
        total_interest_accrued_usd += interest_this_year_usd
        total_inflation_cost_usd += inflation_cost_this_year_usd

        # Update the loan balance for *next* year's interest calculation
        # New balance = Old Balance + New Debt + Capitalized Interest
        current_debt_balance_usd += new_debt_draw_usd + interest_this_year_usd

    logger.info(
        f"Phased CAPEX calculation complete: "
        f"Total Installed Cost: ${total_capitalized_cost_usd:,.2f}, "
        f"Total Inflation Cost: ${total_inflation_cost_usd:,.2f}, "
        f"Total Capitalized Interest: ${total_interest_accrued_usd:,.2f}"
    )

    return PreRevenueCostsAndCashflow(
        total_installed_cost_usd=total_capitalized_cost_usd,
        construction_financing_cost_usd=total_interest_accrued_usd,
        debt_balance_usd=current_debt_balance_usd,
        inflation_cost_usd=total_inflation_cost_usd,
        #pre_revenue_equity_cash_flow=cash_flow_usd,
        pre_revenue_equity_cash_flow_usd=equity_cash_flow_usd,
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

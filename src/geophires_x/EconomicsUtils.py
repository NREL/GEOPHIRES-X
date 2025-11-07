from __future__ import annotations

from geophires_x.Parameter import OutputParameter
from geophires_x.Units import Units, PercentUnit, TimeUnit, CurrencyUnit, CurrencyFrequencyUnit

import numpy_financial as npf
from typing import List


def calculate_equivalent_lump_sum_capex(
    total_overnight_capex: float,
    phased_schedule_fractions: List[float],
    discount_rate: float
) -> float:
    """
    Calculates the time-zero equivalent CAPEX of a phased expenditure schedule.

    This function answers the question: "What single lump-sum payment at Year 0
    has the same present value as the multi-year phased expenditure plan?"

    It does this by calculating the Net Present Value (NPV) of the
    phased expenditure stream, discounting all future costs back to Year 0.

    Args:
        total_overnight_capex:
            The total nominal cost (e.g., 100_000_000).
        phased_schedule_fractions:
            A list of fractions (e.g., [0.1, 0.4, 0.5])
            where the index corresponds to the year of expenditure
            (index 0 = Year 0, index 1 = Year 1, etc.).
        discount_rate:
            The annual discount rate as a fraction (e.g., 0.08 for 8%).

    Returns:
        The equivalent Year 0 lump-sum capital cost (the NPV of the
        expenditure stream).
    """

    # 1. Create the nominal cash flow stream of expenditures
    #    e.g., [10_000_000, 40_000_000, 50_000_000]
    expenditure_stream = [total_overnight_capex * p for p in phased_schedule_fractions]

    # 2. Calculate the Present Value (NPV) of this stream.
    #    The numpy_financial.npv function assumes the first value in the
    #    list is at t=1, not t=0. We must handle the t=0 value manually.
    if not expenditure_stream:
        return 0.0

    # The Year 0 expenditure is already in present value
    cash_flow_t0 = expenditure_stream

    # All subsequent expenditures (Year 1 onwards) must be discounted
    cash_flow_t1_onward = expenditure_stream[1:]

    # Calculate the NPV of the future values and add the t=0 value
    present_value_of_expenditures = cash_flow_t0 + npf.npv(discount_rate, cash_flow_t1_onward)

    # 3. Return the equivalent Year 0 cost
    return present_value_of_expenditures


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

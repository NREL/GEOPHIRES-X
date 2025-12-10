from __future__ import annotations

from geophires_x.Parameter import OutputParameter
from geophires_x.Units import Units, PercentUnit, TimeUnit, CurrencyUnit, CurrencyFrequencyUnit

CONSTRUCTION_CAPEX_SCHEDULE_PARAMETER_NAME = 'Construction CAPEX Schedule'


def BuildPricingModel(
    plantlifetime: int,
    StartPrice: float,
    EndPrice: float,
    EscalationStartYear: int,
    EscalationRate: float,
    PTCAddition: list,
) -> list:
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


_SAM_EM_MOIC_RETURNS_TAX_QUALIFIER = 'pre-tax'  # TODO/WIP switch to after-tax...


def moic_parameter() -> OutputParameter:
    return OutputParameter(
        "Project MOIC",
        ToolTipText='Project Multiple of Invested Capital. For SAM Economic Models, this is calculated as the '
        f'sum of Total {_SAM_EM_MOIC_RETURNS_TAX_QUALIFIER} returns (total value received) '
        'divided by Issuance of equity (total capital invested).',
        UnitType=Units.PERCENT,
        PreferredUnits=PercentUnit.TENTH,
        CurrentUnits=PercentUnit.TENTH,
    )


def project_vir_parameter() -> OutputParameter:
    return OutputParameter(
        "Project Value Investment Ratio",
        display_name='Project VIR=PI=PIR',
        UnitType=Units.PERCENT,
        PreferredUnits=PercentUnit.TENTH,
        CurrentUnits=PercentUnit.TENTH,
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
        'is used to calculate the value from SAM\'s total after-tax returns.',
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


def overnight_capital_cost_output_parameter() -> OutputParameter:
    return OutputParameter(
        Name='Overnight Capital Cost',
        UnitType=Units.CURRENCY,
        PreferredUnits=CurrencyUnit.MDOLLARS,
        CurrentUnits=CurrencyUnit.MDOLLARS,
        ToolTipText='Overnight Capital Cost (OCC) represents the total capital cost required '
        'to construct the plant if it were built instantly ("overnight"). '
        'This value excludes time-dependent costs such as inflation and '
        'interest incurred during the construction period.',
    )


def inflation_cost_during_construction_output_parameter() -> OutputParameter:
    return OutputParameter(
        Name='Inflation costs during construction',
        UnitType=Units.CURRENCY,
        PreferredUnits=CurrencyUnit.MDOLLARS,
        CurrentUnits=CurrencyUnit.MDOLLARS,
        ToolTipText='The calculated amount of cost escalation due to inflation over the construction period.',
    )


def interest_during_construction_output_parameter() -> OutputParameter:
    return OutputParameter(
        Name='Interest during construction',
        UnitType=Units.CURRENCY,
        PreferredUnits=CurrencyUnit.MDOLLARS,
        CurrentUnits=CurrencyUnit.MDOLLARS,
        ToolTipText='Interest During Construction (IDC) is the total accumulated interest '
        'incurred on debt during the construction phase. This cost is capitalized '
        '(added to the loan principal and total installed cost) rather than paid in cash.',
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
        'It is used as the total installed cost input for SAM Economic Models.',
    )


def royalty_cost_output_parameter() -> OutputParameter:
    return OutputParameter(
        Name='Royalty Cost',
        UnitType=Units.CURRENCYFREQUENCY,
        PreferredUnits=CurrencyFrequencyUnit.DOLLARSPERYEAR,
        CurrentUnits=CurrencyFrequencyUnit.DOLLARSPERYEAR,
        ToolTipText='The annual costs paid to a royalty holder, calculated as a percentage of the '
        'project\'s gross annual revenue. This is modeled as a variable operating expense.',
    )

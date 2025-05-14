from __future__ import annotations

from geophires_x.Parameter import OutputParameter
from geophires_x.Units import Units, PercentUnit


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

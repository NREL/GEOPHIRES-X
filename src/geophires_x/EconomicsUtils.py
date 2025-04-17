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

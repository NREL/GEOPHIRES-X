import math
import sys
import os
import numpy as np
import numpy_financial as npf
import geophires_x.Model as Model
from geophires_x.OptionList import Configuration, WellDrillingCostCorrelation, EconomicModel, EndUseOptions, PlantType
from geophires_x.Parameter import intParameter, floatParameter, OutputParameter, ReadParameter, boolParameter, \
    coerce_int_params_to_enum_values
from geophires_x.Units import *


def calculate_total_drilling_lengths_m(Configuration, numnonverticalsections: int, nonvertical_length_km: float,
                                       InputDepth_km: float, OutputDepth_km: float, nprod:int, ninj:int) -> tuple:
    """
    returns the total length, vertical length, and non-vertical lengths, depending on the configuration
    :param Configuration: Configuration of the well
    :type Configuration: :class:`~geophires
    :param numnonverticalsections: number of non-vertical sections
    :type numnonverticalsections: int
    :param nonvertical_length_km: length of non-vertical sections in km
    :type nonvertical_length_km: float
    :param InputDepth_km: depth of the well in km
    :type InputDepth_km: float
    :param OutputDepth_km: depth of the output end of the well in km, if U shaped, and not horizontal
    :type OutputDepth_km: float
    :param nprod: number of production wells
    :type nprod: int
    :param ninj: number of injection wells
    :return: total length, vertical length, and horizontal lengths in meters
    :rtype: tuple
    """
    if Configuration == Configuration.ULOOP:
        # Total drilling depth of both wells and laterals in U-loop [m]
        vertical_pipe_length_m = (nprod * InputDepth_km * 1000.0) + (ninj * OutputDepth_km * 1000.0)
        nonvertical_pipe_length_m = numnonverticalsections * nonvertical_length_km * 1000.0
    elif Configuration == Configuration.COAXIAL:
        # Total drilling depth of well and lateral in co-axial case [m]
        vertical_pipe_length_m = (nprod + ninj) * InputDepth_km * 1000.0
        nonvertical_pipe_length_m = numnonverticalsections * nonvertical_length_km * 1000.0
    elif Configuration == Configuration.VERTICAL:
        # Total drilling depth of well in vertical case [m]
        vertical_pipe_length_m = (nprod + ninj) * InputDepth_km * 1000.0
        nonvertical_pipe_length_m = 0.0
    elif Configuration == Configuration.L:
        # Total drilling depth of well in L case [m]
        vertical_pipe_length_m = (nprod + ninj) * InputDepth_km * 1000.0
        nonvertical_pipe_length_m = numnonverticalsections * nonvertical_length_km * 1000.0
    else:
        raise ValueError(f'Invalid Configuration: {Configuration}')

    tot_pipe_length_m = vertical_pipe_length_m + nonvertical_pipe_length_m
    return tot_pipe_length_m, vertical_pipe_length_m, nonvertical_pipe_length_m


def calculate_cost_of_one_vertical_well(model: Model, depth_m: float, well_correlation: int,
                                        vertical_drilling_cost_per_m: float,
                                        fixed_well_cost_name: str, well_cost_adjustment_factor: float) -> float:
    """
    CalculateCostOfOneWell calculates the cost of one vertical well based on the depth of the well and the cost correlation.
    :param model: The model object
    :type model: :class:`~geophires
    :param depth_m: The depth of the well in meters
    :type depth_m: float
    :param well_correlation: The well correlation
    :type well_correlation: int
    :param vertical_drilling_cost_per_m: The vertical drilling cost per meter in $/m
    :type vertical_drilling_cost_per_m: float
    :param fixed_well_cost_name: The fixed well cost name
    :type fixed_well_cost_name: str
    :param well_cost_adjustment_factor: The well cost adjustment factor
    :type well_cost_adjustment_factor: float
    :return: cost_of_one_well: The cost of one well in MUSD
    :rtype: float
    """
    # Check if  well depth is out of standard bounds for cost correlation
    correlations_min_valid_depth_m = 500.
    correlations_max_valid_depth_m = 7000.
    cost_of_one_well = 0.0

    if depth_m < correlations_min_valid_depth_m and not well_correlation is WellDrillingCostCorrelation.SIMPLE:
        well_correlation = WellDrillingCostCorrelation.SIMPLE
        model.logger.warning(
            f'Invalid cost correlation specified ({well_correlation}) for drilling depth '
            f'<{correlations_min_valid_depth_m}m ({depth_m}m). '
            f'Falling back to simple user-specified cost '
            f'({vertical_drilling_cost_per_m} per meter)'
        )

    if depth_m > correlations_max_valid_depth_m and not well_correlation is WellDrillingCostCorrelation.SIMPLE:
        model.logger.warning(
            f'{well_correlation} may be invalid for drilling depth '
            f'>{correlations_max_valid_depth_m}m ({depth_m}m). '
            f'Consider using {WellDrillingCostCorrelation.SIMPLE} (per-meter cost) or '
            f'{fixed_well_cost_name} (fixed cost per well) instead.'
        )

    if well_correlation is WellDrillingCostCorrelation.SIMPLE:
        cost_of_one_well = vertical_drilling_cost_per_m * depth_m * 1E-6
    else:
        cost_of_one_well = well_correlation.calculate_cost_MUSD(depth_m)

    # account for adjustment factor
    cost_of_one_well = well_cost_adjustment_factor * cost_of_one_well

    return cost_of_one_well


def calculate_cost_of_non_vertical_section(model: Model, length_m: float, well_correlation: int,
                                        nonvertical_drilling_cost_per_m: float,
                                           num_nonvertical_sections: int,
                                        fixed_well_cost_name: str, NonverticalsCased: bool,
                                           well_cost_adjustment_factor: float) -> float:
    """
    calculate_cost_of_non_vertical_section calculates the cost of the non vertical section of the well.
    Assume that the cost per meter for drilling of the non-vertical section is the same as the vertical section.
    :param model: The model object
    :type model: :class:`~geophires
    :param length_m: The depth of the well in meters
    :type length_m: float
    :param well_correlation: The well cost correlation
    :type well_correlation: int
    :param nonvertical_drilling_cost_per_m: The nonvertical drilling cost per meter in $/m
    :type nonvertical_drilling_cost_per_m: float
    :param num_nonvertical_sections: The number of non vertical sections
    :type num_nonvertical_sections: int
    :param fixed_well_cost_name: The fixed well cost name
    :type fixed_well_cost_name: str
    :param NonverticalsCased: Are the nonverticals cased?
    :type NonverticalsCased: bool
    :param well_cost_adjustment_factor: The well cost adjustment factor
    :type well_cost_adjustment_factor: float
    :return: cost_of_one_well: The cost of the nonvertical section in MUSD
    :rtype: float
    """

    # if we are drilling a vertical well, the nonvertical cost is 0
    if model.wellbores.Configuration.value == Configuration.VERTICAL:
        return 0.0

    # Check if  well length is out of standard bounds for cost correlation
    length_per_section_m = length_m / num_nonvertical_sections
    correlations_min_valid_length_m = 500.
    correlations_max_valid_length_m = 7000.
    cost_of_non_vertical_section = 0.0
    cost_per_section = 0.0

    if length_per_section_m < correlations_min_valid_length_m and not well_correlation is WellDrillingCostCorrelation.SIMPLE:
        well_correlation = WellDrillingCostCorrelation.SIMPLE
        model.logger.warning(
            f'Invalid cost correlation specified ({well_correlation}) for drilling length '
            f'<{correlations_min_valid_length_m}m ({length_m}m). '
            f'Falling back to simple user-specified cost '
            f'({nonvertical_drilling_cost_per_m} per meter)'
        )

    if length_per_section_m > correlations_max_valid_length_m and not well_correlation is WellDrillingCostCorrelation.SIMPLE:
        model.logger.warning(
            f'{well_correlation} may be invalid for drilling length '
            f'>{correlations_max_valid_length_m}m ({length_m}m). '
            f'Consider using {WellDrillingCostCorrelation.SIMPLE} (per-meter cost) or '
            f'{fixed_well_cost_name} (fixed cost per well) instead.'
        )

    casing_factor = 1.0
    if not NonverticalsCased:
        # assume that casing & cementing costs 50% of drilling costs
        casing_factor = 0.5

    if model.economics.Nonvertical_drilling_cost_per_m.Provided or well_correlation is WellDrillingCostCorrelation.SIMPLE:
        cost_of_non_vertical_section = casing_factor * ((num_nonvertical_sections * nonvertical_drilling_cost_per_m * length_per_section_m)) * 1E-6
    else:
        cost_per_section = well_correlation.calculate_cost_MUSD(length_per_section_m)
        cost_of_non_vertical_section = casing_factor * num_nonvertical_sections * cost_per_section

    # account for adjustment factor
    cost_of_non_vertical_section = well_cost_adjustment_factor * cost_of_non_vertical_section

    return cost_of_non_vertical_section


def BuildPTCModel(plantlifetime: int, duration: int, ptc_price: float,
                  ptc_inflation_adjusted: bool, inflation_rate: float) -> list:
    """
    BuildPricingModel builds the price model array for the project lifetime.  It is used to calculate the revenue
    stream for the project.
    :param plantlifetime: The lifetime of the project in years
    :type plantlifetime: int
    :param duration: The duration of the PTC in years
    :type duration: int
    :param ptc_price: The PTC in $/kWh
    :type ptc_price: float
    :param ptc_inflation_adjusted: Is the PTC is inflation?
    :type ptc_inflation_adjusted: bool
    :param inflation_rate: The inflation rate in %
    :type inflation_rate: float
    :return: Price: The price model array for the PTC in $/kWh
    :rtype: list
    """
    # Build the PTC price model by setting the price to the PTCPrice for the duration of the PTC
    Price = [0.0] * plantlifetime
    for year in range(0, duration, 1):
        Price[year] = ptc_price
        if ptc_inflation_adjusted and year > 0:
            Price[year] = Price[year-1] * (1 + inflation_rate)
    return Price


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
            Price[i] = Price[i] + ((i - EscalationStartYear) * EscalationRate)
        if Price[i] > EndPrice:
            Price[i] = EndPrice
        Price[i] = Price[i] + PTCAddition[i]
    return Price


def CalculateTotalRevenue(plantlifetime: int, ConstructionYears: int, CAPEX: float, OPEX: float, AnnualRev):
    """
    CalculateRevenue calculates the revenue stream for the project.  It is used to calculate the revenue
    stream for the project.
    :param plantlifetime: The lifetime of the project in years in years (not including construction years) in years
    :type plantlifetime: int
    :param ConstructionYears: The number of years of construction for the project in years
    :type ConstructionYears: int
    :param CAPEX: The total capital cost of the project in MUSD
    :type CAPEX: float
    :param OPEX: The total annual operating cost of the project in MUSD
    :type OPEX: float
    :param AnnualRev: The annual revenue array for the project in MUSD
    :type AnnualRev: list
    :return: CashFlow: The annual cash flow for the project in MUSD and CummCashFlow: The cumulative cash flow for the
    project in MUSD
    :rtype: list
    """
    # Calculate the revenue
    ProjectCAPEXPerConstructionYear = CAPEX / ConstructionYears
    CashFlow = [0.0] * (plantlifetime + ConstructionYears)
    CummCashFlow = [0.0] * (plantlifetime + ConstructionYears)

    # Insert the cost of construction into the front of the array that will be used to calculate NPV
    # the convention is that the upfront CAPEX is negative
    for i in range(0, ConstructionYears, 1):
        CashFlow[i] = -1.0 * ProjectCAPEXPerConstructionYear
        CummCashFlow[i] = -1.0 * ProjectCAPEXPerConstructionYear

    for i in range(ConstructionYears, plantlifetime + ConstructionYears, 1):
        CashFlow[i] = (AnnualRev[i]) - OPEX

    # Calculate the cumulative revenue, skipping the first year because it is cumulative
    for i in range(1, plantlifetime + ConstructionYears, 1):
        CummCashFlow[i] = CummCashFlow[i - 1] + CashFlow[i]
    return CashFlow, CummCashFlow


def CalculateRevenue(plantlifetime: int, ConstructionYears: int, Energy, Price):
    """
    CalculateRevenue calculates the revenue stream for the project.  It is used to calculate the revenue
    stream for the project.
    # note this doesn't account for OPEX
    :param plantlifetime: The lifetime of the project in years in years (not including construction years) in years
    :type plantlifetime: int
    :param ConstructionYears: The number of years of construction for the project in years
    :type ConstructionYears: int
    :param Energy: The energy production array for the project in kWh
    :type Energy: list
    :param Price: The price model array for the project in $/kWh
    :type Price: list
    :return: CashFlow: The annual cash flow for the project in MUSD and CummCashFlow: The cumulative cash flow for the
    project in MUSD
    :rtype: list
    """
    # Calculate the revenue
    CashFlow = [0.0] * (plantlifetime + ConstructionYears)
    CummCashFlow = [0.0] * (plantlifetime + ConstructionYears)

    # Revenue/yr in MUSD
    for i in range(ConstructionYears, plantlifetime + ConstructionYears, 1):
        CashFlow[i] = ((Energy[i - ConstructionYears] * Price[i - ConstructionYears]) / 1_000_000.0)

    # Calculate the cumulative revenue, skipping the first year because it is cumulative
    for i in range(ConstructionYears, plantlifetime + ConstructionYears, 1):
        CummCashFlow[i] = CummCashFlow[i - 1] + CashFlow[i]
    return CashFlow, CummCashFlow


def CalculateCarbonRevenue(model, plant_lifetime: int, construction_years: int, price_dollar_lb,
                           grid_CO2_intensity_lb_kwh: float, natural_gas_CO2_intensity_lb_kwh: float,
                           NetkWhProduced, HeatkWhProduced):
    # Figure out how much carbon is being produced each year, and the amount of carbon that would have been
    # produced if that energy had been made using the grid average carbon production.
    # That then gives us the revenue, since we have a carbon price model
    # We can also get cumulative cash flow from it.
    # note this doesn't account for OPEX
    cash_flow_musd = [0.0] * (plant_lifetime + construction_years)
    cumm_cash_flow_musd = [0.0] * (plant_lifetime + construction_years)
    carbon_that_would_have_been_produced_annually_lbs = ([0.0] * (plant_lifetime + construction_years))
    carbon_that_would_have_been_produced_total_lbs = 0.0
    for i in range(construction_years, plant_lifetime + construction_years, 1):
        electrical_energy_kwh = 0.0
        heat_energy_kwh = 0.0
        elec_CO2_produced_lbs = 0.0
        heat_CO2_produced_lbs = 0.0

        # Carbon cashflow revenue (from both heat and elec) based net energy produced
        if model.surfaceplant.enduse_option.value == EndUseOptions.ELECTRICITY:  # This option has no heat component
            electrical_energy_kwh = NetkWhProduced[i - construction_years]
        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT:  # has heat component but no electricity
            heat_energy_kwh = HeatkWhProduced[i - construction_years]
        else:  # everything else has a component of both
            electrical_energy_kwh = NetkWhProduced[i - construction_years]
            heat_energy_kwh = HeatkWhProduced[i - construction_years]

        elec_CO2_produced_lbs = electrical_energy_kwh * grid_CO2_intensity_lb_kwh
        heat_CO2_produced_lbs = heat_energy_kwh * natural_gas_CO2_intensity_lb_kwh

        # convert lbs/year to tonnes/year
        carbon_that_would_have_been_produced_annually_lbs[i] = elec_CO2_produced_lbs + heat_CO2_produced_lbs
        carbon_that_would_have_been_produced_total_lbs = carbon_that_would_have_been_produced_total_lbs + \
                                                            carbon_that_would_have_been_produced_annually_lbs[i]

        cash_flow_musd[i] = (carbon_that_would_have_been_produced_annually_lbs[i] * price_dollar_lb[i - construction_years]) / 1_000_000.0
        if i >= construction_years:
            cumm_cash_flow_musd[i] = cumm_cash_flow_musd[i - 1] + cash_flow_musd[i]

    return cash_flow_musd, cumm_cash_flow_musd, carbon_that_would_have_been_produced_annually_lbs, carbon_that_would_have_been_produced_total_lbs


def CalculateFinancialPerformance(plantlifetime: int,
                                  FixedInternalRate: float,
                                  TotalRevenue: list,
                                  TotalCummRevenue: list,
                                  CAPEX: float,
                                  OPEX: float):
    """
    CalculateFinancialPerformance calculates the financial performance of the project.  It is used to calculate the
    financial performance of the project. It is used to calculate the revenue stream for the project.
    :param plantlifetime: The lifetime of the project in years
    :type plantlifetime: int
    :param FixedInternalRate: The fixed internal rate of return for the project in %
    :type FixedInternalRate: float
    :param TotalRevenue: The total revenue stream for the project in MUSD
    :type TotalRevenue: list
    :param TotalCummRevenue: The total cumulative revenue stream for the project in MUSD
    :type TotalCummRevenue: list
    :param CAPEX: The total capital cost of the project in MUSD
    :type CAPEX: float
    :param OPEX: The total annual operating cost of the project in MUSD
    :type OPEX: float
    :return: NPV: The net present value of the project in MUSD
    :rtype: float
    :return: IRR: The internal rate of return of the project in %
    :rtype: float
    :return: VIR: The value to investment ratio of the project in %
    :rtype: float
    :return: MOIC: The money on investment capital of the project in %
    :rtype: float
    :rtype: tuple
    """
    # Calculate financial performance values using numpy financials
    NPV = npf.npv(FixedInternalRate / 100, TotalRevenue)
    IRR = npf.irr(TotalRevenue)
    if math.isnan(IRR):
        IRR = 0.0
    else:
        IRR *= 100.  # convert from decimal to percent
    VIR = 1.0 + (NPV / CAPEX)

    # Calculate MOIC which depends on CumCashFlow
    MOIC = TotalCummRevenue[len(TotalCummRevenue) - 1] / (CAPEX + (OPEX * plantlifetime))

    return NPV, IRR, VIR, MOIC


def CalculateLCOELCOHLCOC(self, model: Model) -> tuple:
    """
    CalculateLCOELCOH calculates the levelized cost of electricity and heat for the project.
    :param model: The model object
    :type model: :class:`~geophires_x.Model.Model`
    :return: LCOE: The levelized cost of electricity and LCOH: The levelized cost of heat and LCOC: The levelized cost of cooling
    :rtype: tuple
    """
    LCOE = LCOH = LCOC = 0.0
    CCap_elec = (self.CCap.value * self.CAPEX_heat_electricity_plant_ratio.value)
    Coam_elec = (self.Coam.value * self.CAPEX_heat_electricity_plant_ratio.value)
    CCap_heat = (self.CCap.value * (1.0 - self.CAPEX_heat_electricity_plant_ratio.value))
    Coam_heat = (self.Coam.value * (1.0 - self.CAPEX_heat_electricity_plant_ratio.value))
    # Calculate LCOE/LCOH/LCOC
    if self.econmodel.value == EconomicModel.FCR:
        if model.surfaceplant.enduse_option.value == EndUseOptions.ELECTRICITY:
            LCOE = (self.FCR.value * (1 + self.inflrateconstruction.value) * self.CCap.value + self.Coam.value) / \
                   np.average(model.surfaceplant.NetkWhProduced.value) * 1E8  # cents/kWh
        elif (model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and
              model.surfaceplant.plant_type.value not in [PlantType.ABSORPTION_CHILLER, PlantType.HEAT_PUMP, PlantType.DISTRICT_HEATING]):
            LCOH = (self.FCR.value * (1 + self.inflrateconstruction.value) * self.CCap.value + self.Coam.value +
                    self.averageannualpumpingcosts.value) / np.average(
                model.surfaceplant.HeatkWhProduced.value) * 1E8  # cents/kWh
            LCOH = LCOH * 2.931  # $/Million Btu
        # co-gen
        elif model.surfaceplant.enduse_option.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT,
                                                        EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY,
                                                        EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY,
                                                        EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                        EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT,
                                                        EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]:
            LCOE = (self.FCR.value * (1 + self.inflrateconstruction.value) * CCap_elec + Coam_elec) /  np.average(model.surfaceplant.NetkWhProduced.value) * 1E8  # cents/kWh
            LCOH = (self.FCR.value * (1 + self.inflrateconstruction.value) * CCap_heat + Coam_heat + self.averageannualpumpingcosts.value) / np.average(model.surfaceplant.HeatkWhProduced.value) * 1E8  # cents/kWh
            LCOH = LCOH * 2.931  # $/Million Btu

        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value == PlantType.ABSORPTION_CHILLER:
            LCOC = (self.FCR.value * (
                    1 + self.inflrateconstruction.value) * self.CCap.value + self.Coam.value + self.averageannualpumpingcosts.value) / np.average(
                model.surfaceplant.cooling_kWh_Produced.value) * 1E8  # cents/kWh
            LCOC = LCOC * 2.931  # $/Million Btu
        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value == PlantType.HEAT_PUMP:
            LCOH = (self.FCR.value * (
                    1 + self.inflrateconstruction.value) * self.CCap.value + self.Coam.value + self.averageannualpumpingcosts.value + self.averageannualheatpumpelectricitycost.value) / np.average(
                model.surfaceplant.HeatkWhProduced.value) * 1E8  # cents/kWh
            LCOH = LCOH * 2.931  # $/Million Btu
        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
            LCOH = (self.FCR.value * (
                    1 + self.inflrateconstruction.value) * self.CCap.value + self.Coam.value + self.averageannualpumpingcosts.value + self.averageannualngcost.value) / model.surfaceplant.annual_heating_demand.value * 1E2  # cents/kWh
            LCOH = LCOH * 2.931  # $/Million Btu
    elif self.econmodel.value == EconomicModel.STANDARDIZED_LEVELIZED_COST:
        discountvector = 1. / np.power(1 + self.discountrate.value,
                                       np.linspace(0, model.surfaceplant.plant_lifetime.value - 1,
                                                   model.surfaceplant.plant_lifetime.value))
        if model.surfaceplant.enduse_option.value == EndUseOptions.ELECTRICITY:
            LCOE = ((1 + self.inflrateconstruction.value) * self.CCap.value + np.sum(
                self.Coam.value * discountvector)) / np.sum(
                model.surfaceplant.NetkWhProduced.value * discountvector) * 1E8  # cents/kWh
        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and \
            model.surfaceplant.plant_type.value not in [PlantType.ABSORPTION_CHILLER, PlantType.HEAT_PUMP, PlantType.DISTRICT_HEATING]:
            self.averageannualpumpingcosts.value = np.average(
                model.surfaceplant.PumpingkWh.value) * model.surfaceplant.electricity_cost_to_buy.value / 1E6  # M$/year
            LCOH = ((1 + self.inflrateconstruction.value) * self.CCap.value + np.sum((
                                                                                         self.Coam.value + model.surfaceplant.PumpingkWh.value * model.surfaceplant.electricity_cost_to_buy.value / 1E6) * discountvector)) / np.sum(
                model.surfaceplant.HeatkWhProduced.value * discountvector) * 1E8  # cents/kWh
            LCOH = LCOH * 2.931  # $/MMBTU

        # co-gen
        elif model.surfaceplant.enduse_option.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT,
                                                        EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY,
                                                        EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY,
                                                        EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                        EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT,
                                                        EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]:
            LCOE = ((1 + self.inflrateconstruction.value) * CCap_elec + np.sum(Coam_elec * discountvector)) / np.sum(model.surfaceplant.NetkWhProduced.value * discountvector) * 1E8  # cents/kWh
            LCOH = ((1 + self.inflrateconstruction.value) * CCap_heat +
                    np.sum((Coam_heat + model.surfaceplant.PumpingkWh.value * model.surfaceplant.electricity_cost_to_buy.value / 1E6) * discountvector)) / np.sum(model.surfaceplant.HeatkWhProduced.value * discountvector) * 1E8  # cents/kWh
            LCOH = LCOH * 2.931  # $/MMBTU

        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value == PlantType.ABSORPTION_CHILLER:
            LCOC = ((1 + self.inflrateconstruction.value) * self.CCap.value + np.sum((
                                                                                         self.Coam.value + model.surfaceplant.PumpingkWh.value * model.surfaceplant.electricity_cost_to_buy.value / 1E6) * discountvector)) / np.sum(
                model.surfaceplant.cooling_kWh_Produced.value * discountvector) * 1E8  # cents/kWh
            LCOC = LCOC * 2.931  # $/Million Btu
        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value == PlantType.HEAT_PUMP:
            LCOH = ((1 + self.inflrateconstruction.value) * self.CCap.value + np.sum(
                (self.Coam.value + model.surfaceplant.PumpingkWh.value * model.surfaceplant.electricity_cost_to_buy.value / 1E6 +
                 model.surfaceplant.heat_pump_electricity_kwh_used.value * model.surfaceplant.electricity_cost_to_buy.value / 1E6) * discountvector)) / np.sum(
                model.surfaceplant.HeatkWhProduced.value * discountvector) * 1E8  # cents/kWh
            LCOH = LCOH * 2.931  # $/Million Btu
        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
            LCOH = ((1 + self.inflrateconstruction.value) * self.CCap.value + np.sum(
                (self.Coam.value + model.surfaceplant.PumpingkWh.value * model.surfaceplant.electricity_cost_to_buy.value / 1E6 +
                 self.annualngcost.value) * discountvector)) / np.sum(
                model.surfaceplant.annual_heating_demand.value * discountvector) * 1E2  # cents/kWh
            LCOH = LCOH * 2.931  # $/Million Btu

    else:
        # must be BICYCLE
        # average return on investment (tax and inflation adjusted)
        iave = self.FIB.value * self.BIR.value * (1 - self.CTR.value) + (1 - self.FIB.value) * self.EIR.value
        # capital recovery factor
        CRF = iave / (1 - np.power(1 + iave, -model.surfaceplant.plant_lifetime.value))
        inflationvector = np.power(1 + self.RINFL.value, np.linspace(1, model.surfaceplant.plant_lifetime.value, model.surfaceplant.plant_lifetime.value))
        discountvector = 1. / np.power(1 + iave, np.linspace(1, model.surfaceplant.plant_lifetime.value, model.surfaceplant.plant_lifetime.value))
        NPVcap = np.sum((1 + self.inflrateconstruction.value) * self.CCap.value * CRF * discountvector)
        NPVfc = np.sum((1 + self.inflrateconstruction.value) * self.CCap.value * self.PTR.value * inflationvector * discountvector)
        NPVit = np.sum(self.CTR.value / (1 - self.CTR.value) * ((1 + self.inflrateconstruction.value) * self.CCap.value * CRF - self.CCap.value / model.surfaceplant.plant_lifetime.value) * discountvector)
        NPVitc = (1 + self.inflrateconstruction.value) * self.CCap.value * self.RITC.value / (1 - self.CTR.value)

        if model.surfaceplant.enduse_option.value == EndUseOptions.ELECTRICITY:
            NPVoandm = np.sum(self.Coam.value * inflationvector * discountvector)
            NPVgrt = self.GTR.value / (1 - self.GTR.value) * (NPVcap + NPVoandm + NPVfc + NPVit - NPVitc)
            LCOE = (NPVcap + NPVoandm + NPVfc + NPVit + NPVgrt - NPVitc) / np.sum(model.surfaceplant.NetkWhProduced.value * inflationvector * discountvector) * 1E8
        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value not in [PlantType.ABSORPTION_CHILLER, PlantType.HEAT_PUMP, PlantType.DISTRICT_HEATING]:
            PumpingCosts = model.surfaceplant.PumpingkWh.value * model.surfaceplant.electricity_cost_to_buy.value / 1E6
            NPVoandm = np.sum((self.Coam.value + PumpingCosts) * inflationvector * discountvector)
            NPVgrt = self.GTR.value / (1 - self.GTR.value) * (NPVcap + NPVoandm + NPVfc + NPVit - NPVitc)
            LCOH = (NPVcap + NPVoandm + NPVfc + NPVit + NPVgrt - NPVitc) / np.sum(model.surfaceplant.HeatkWhProduced.value * inflationvector * discountvector) * 1E8
            LCOH = LCOH * 2.931  # $/MMBTU
        # co-gen
        elif model.surfaceplant.enduse_option.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT,
                                                        EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY,
                                                        EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY,
                                                        EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                        EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT,
                                                        EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]:

            NPVcap_elec = np.sum((1 + self.inflrateconstruction.value) * CCap_elec * CRF * discountvector)
            NPVfc_elec = np.sum((1 + self.inflrateconstruction.value) * CCap_elec * self.PTR.value * inflationvector * discountvector)
            NPVit_elec = np.sum(self.CTR.value / (1 - self.CTR.value) * ((1 + self.inflrateconstruction.value) * CCap_elec * CRF - CCap_elec / model.surfaceplant.plant_lifetime.value) * discountvector)
            NPVitc_elec = (1 + self.inflrateconstruction.value) * CCap_elec * self.RITC.value / (1 - self.CTR.value)
            NPVoandm_elec = np.sum(Coam_elec * inflationvector * discountvector)
            NPVgrt_elec = self.GTR.value / (1 - self.GTR.value) * (NPVcap_elec + NPVoandm_elec + NPVfc_elec + NPVit_elec - NPVitc_elec)

            LCOE = ((NPVcap_elec + NPVoandm_elec + NPVfc_elec + NPVit_elec + NPVgrt_elec - NPVitc_elec) /
                    np.sum(model.surfaceplant.NetkWhProduced.value * inflationvector * discountvector) * 1E8)

            NPVcap_heat = np.sum((1 + self.inflrateconstruction.value) * CCap_heat * CRF * discountvector)
            NPVfc_heat = np.sum((1 + self.inflrateconstruction.value) * (self.CCap.value * (1.0 - self.CAPEX_heat_electricity_plant_ratio.value)) * self.PTR.value * inflationvector * discountvector)
            NPVit_heat = np.sum(self.CTR.value / (1 - self.CTR.value) * ((1 + self.inflrateconstruction.value) * CCap_heat * CRF - CCap_heat / model.surfaceplant.plant_lifetime.value) * discountvector)
            NPVitc_heat = (1 + self.inflrateconstruction.value) * CCap_heat * self.RITC.value / (1 - self.CTR.value)
            NPVoandm_heat = np.sum((self.Coam.value * (1.0 - self.CAPEX_heat_electricity_plant_ratio.value)) * inflationvector * discountvector)
            NPVgrt_heat = self.GTR.value / (1 - self.GTR.value) * (NPVcap_heat + NPVoandm_heat + NPVfc_heat + NPVit_heat - NPVitc_heat)

            LCOH = ((NPVcap_heat + NPVoandm_heat + NPVfc_heat + NPVit_heat + NPVgrt_heat - NPVitc_heat) /
                    np.sum(model.surfaceplant.HeatkWhProduced.value * inflationvector * discountvector) * 1E8)
            LCOH = LCOH * 2.931  # $/MMBTU

        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value == PlantType.ABSORPTION_CHILLER:
            PumpingCosts = model.surfaceplant.PumpingkWh.value * model.surfaceplant.electricity_cost_to_buy.value / 1E6
            NPVoandm = np.sum((self.Coam.value + PumpingCosts) * inflationvector * discountvector)
            NPVgrt = self.GTR.value / (1 - self.GTR.value) * (NPVcap + NPVoandm + NPVfc + NPVit - NPVitc)
            LCOC = (NPVcap + NPVoandm + NPVfc + NPVit + NPVgrt - NPVitc) / np.sum(
                model.surfaceplant.cooling_kWh_Produced.value * inflationvector * discountvector) * 1E8
            LCOC = LCOC * 2.931  # $/MMBTU

        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value == PlantType.HEAT_PUMP:
            PumpingCosts = model.surfaceplant.PumpingkWh.value * model.surfaceplant.electricity_cost_to_buy.value / 1E6
            HeatPumpElecCosts = model.surfaceplant.heat_pump_electricity_kwh_used.value * model.surfaceplant.electricity_cost_to_buy.value / 1E6
            NPVoandm = np.sum((self.Coam.value + PumpingCosts + HeatPumpElecCosts) * inflationvector * discountvector)
            NPVgrt = self.GTR.value / (1 - self.GTR.value) * (NPVcap + NPVoandm + NPVfc + NPVit - NPVitc)
            LCOH = (NPVcap + NPVoandm + NPVfc + NPVit + NPVgrt - NPVitc) / np.sum(
                model.surfaceplant.HeatkWhProduced.value * inflationvector * discountvector) * 1E8
            LCOH = self.LCOH.value * 2.931  # $/MMBTU

        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
            PumpingCosts = model.surfaceplant.PumpingkWh.value * model.surfaceplant.electricity_cost_to_buy.value / 1E6
            NPVoandm = np.sum(
                (self.Coam.value + PumpingCosts + self.annualngcost.value) * inflationvector * discountvector)
            NPVgrt = self.GTR.value / (1 - self.GTR.value) * (NPVcap + NPVoandm + NPVfc + NPVit - NPVitc)
            LCOH = (NPVcap + NPVoandm + NPVfc + NPVit + NPVgrt - NPVitc) / np.sum(
                model.surfaceplant.annual_heating_demand.value * inflationvector * discountvector) * 1E2
            LCOH = LCOH * 2.931  # $/MMBTU

    return LCOE, LCOH, LCOC


class Economics:
    """
     Class to support the default economic calculations in GEOPHIRES
    """

    def __init__(self, model: Model):
        """
        The __init__ function is called automatically when a class is instantiated.
        It initializes the attributes of an object, and sets default values for certain arguments that can be overridden
        by user input.
        The __init__ function is used to set up all the parameters in Economics.
        Set up all the Parameters that will be predefined by this class using the different types of parameter classes.
        Setting up includes giving it a name, a default value, The Unit Type (length, volume, temperature, etc.) and
        Unit Name of that value, sets it as required (or not), sets allowable range, the error message if that range
        is exceeded, the ToolTip Text, and the name of teh class that created it.
        This includes setting up temporary variables that will be available to all the class but noy read in by user,
        or used for Output
        This also includes all Parameters that are calculated and then published using the Printouts function.
        If you choose to subclass this master class, you can do so before or after you create your own parameters.
        If you do, you can also choose to call this method from you class, which will effectively add and set all
        these parameters to your class.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """

        model.logger.info(f'Init {__class__!s}: {sys._getframe().f_code.co_name}')

        # These dictionaries contain a list of all the parameters set in this object, stored as "Parameter" and
        # "OutputParameter" Objects.  This will allow us later to access them in a user interface and get that list,
        # along with unit type, preferred units, etc.
        self.ParameterDict = {}
        self.OutputParameterDict = {}

        # Note: setting Valid to False for any of the cost parameters forces GEOPHIRES to use it's builtin cost engine.
        # This is the default.
        self.econmodel = self.ParameterDict[self.econmodel.Name] = intParameter(
            "Economic Model",
            DefaultValue=EconomicModel.STANDARDIZED_LEVELIZED_COST,
            AllowableRange=[1, 2, 3, 4],
            Required=True,
            ErrMessage="assume default economic model (2)",
            ToolTipText="Specify the economic model to calculate the levelized cost of energy." +
                        " 1: Fixed Charge Rate Model, 2: Standard Levelized Cost Model, 3: BICYCLE Levelized Cost Model, 4: CLGS"
        )
        self.ccstimfixed = self.ParameterDict[self.ccstimfixed.Name] = floatParameter(
            "Reservoir Stimulation Capital Cost",
            DefaultValue=-1.0,
            Min=0,
            Max=100,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS,
            Provided=False,
            Valid=False,
            ToolTipText="Total reservoir stimulation capital cost"
        )
        self.ccstimadjfactor = self.ParameterDict[self.ccstimadjfactor.Name] = floatParameter(
            "Reservoir Stimulation Capital Cost Adjustment Factor",
            DefaultValue=1.0,
            Min=0,
            Max=10,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Provided=False,
            Valid=True,
            ToolTipText="Multiplier for built-in reservoir stimulation capital cost correlation"
        )
        self.ccexplfixed = self.ParameterDict[self.ccexplfixed.Name] = floatParameter(
            "Exploration Capital Cost",
            DefaultValue=-1.0,
            Min=0,
            Max=100,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS,
            Provided=False,
            Valid=False,
            ToolTipText="Total exploration capital cost"
        )
        self.ccexpladjfactor = self.ParameterDict[self.ccexpladjfactor.Name] = floatParameter(
            "Exploration Capital Cost Adjustment Factor",
            DefaultValue=1.0,
            Min=0,
            Max=10,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Provided=False,
            Valid=True,
            ToolTipText="Multiplier for built-in exploration capital cost correlation"
        )
        self.per_production_well_cost = self.ParameterDict[self.per_production_well_cost.Name] = floatParameter(
            "Well Drilling and Completion Capital Cost",
            DefaultValue=-1.0,
            Min=0,
            Max=200,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS,
            Provided=False,
            Valid=False,
            ToolTipText="Well Drilling and Completion Capital Cost"
        )
        self.per_injection_well_cost = self.ParameterDict[self.per_injection_well_cost.Name] = floatParameter(
            "Injection Well Drilling and Completion Capital Cost",
            DefaultValue=self.per_production_well_cost.value,
            Min=0,
            Max=200,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS,
            Provided=False,
            Valid=False,
            ToolTipText="Injection Well Drilling and Completion Capital Cost"
        )
        self.production_well_cost_adjustment_factor = self.ParameterDict[self.production_well_cost_adjustment_factor.Name] = floatParameter(
            "Well Drilling and Completion Capital Cost Adjustment Factor",
            DefaultValue=1.0,
            Min=0,
            Max=10,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Provided=False,
            Valid=True,
            ToolTipText="Well Drilling and Completion Capital Cost Adjustment Factor"
        )
        self.injection_well_cost_adjustment_factor = self.ParameterDict[self.injection_well_cost_adjustment_factor.Name] = floatParameter(
            "Injection Well Drilling and Completion Capital Cost Adjustment Factor",
            DefaultValue=self.production_well_cost_adjustment_factor.value,
            Min=0,
            Max=10,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Provided=False,
            Valid=True,
            ToolTipText="Injection Well Drilling and Completion Capital Cost Adjustment Factor"
        )
        self.oamwellfixed = self.ParameterDict[self.oamwellfixed.Name] = floatParameter(
            "Wellfield O&M Cost",
            DefaultValue=-1.0,
            Min=0,
            Max=100,
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            Provided=False,
            Valid=False,
            ToolTipText="Total annual wellfield O&M cost"
        )
        self.oamwelladjfactor = self.ParameterDict[self.oamwelladjfactor.Name] = floatParameter(
            "Wellfield O&M Cost Adjustment Factor",
            DefaultValue=1.0,
            Min=0,
            Max=10,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Provided=False,
            Valid=True,
            ToolTipText="Multiplier for built-in wellfield O&M cost correlation"
        )
        self.ccplantfixed = self.ParameterDict[self.ccplantfixed.Name] = floatParameter(
            "Surface Plant Capital Cost",
            DefaultValue=-1.0,
            Min=0,
            Max=1000,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS,
            Provided=False,
            Valid=False,
            ToolTipText="Total surface plant capital cost"
        )
        self.ccplantadjfactor = self.ParameterDict[self.ccplantadjfactor.Name] = floatParameter(
            "Surface Plant Capital Cost Adjustment Factor",
            DefaultValue=1.0,
            Min=0,
            Max=10,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Provided=False,
            Valid=True,
            ToolTipText="Multiplier for built-in surface plant capital cost correlation"
        )
        self.ccgathfixed = self.ParameterDict[self.ccgathfixed.Name] = floatParameter(
            "Field Gathering System Capital Cost",
            DefaultValue=-1.0,
            Min=0,
            Max=100,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS,
            Provided=False,
            Valid=False,
            ToolTipText="Total field gathering system capital cost"
        )
        self.ccgathadjfactor = self.ParameterDict[self.ccgathadjfactor.Name] = floatParameter(
            "Field Gathering System Capital Cost Adjustment Factor",
            DefaultValue=1.0,
            Min=0,
            Max=10,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Provided=False,
            Valid=True,
            ToolTipText="Multiplier for built-in field gathering system capital cost correlation"
        )
        self.oamplantfixed = self.ParameterDict[self.oamplantfixed.Name] = floatParameter(
            "Surface Plant O&M Cost",
            DefaultValue=-1.0,
            Min=0,
            Max=100,
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            Provided=False,
            Valid=False,
            ToolTipText="Total annual surface plant O&M cost"
        )
        self.oamplantadjfactor = self.ParameterDict[self.oamplantadjfactor.Name] = floatParameter(
            "Surface Plant O&M Cost Adjustment Factor",
            DefaultValue=1.0,
            Min=0,
            Max=10,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Provided=False,
            Valid=True,
            ToolTipText="Multiplier for built-in surface plant O&M cost correlation"
        )
        self.oamwaterfixed = self.ParameterDict[self.oamwaterfixed.Name] = floatParameter(
            "Water Cost",
            DefaultValue=-1.0,
            Min=0,
            Max=100,
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            Provided=False,
            Valid=False,
            ToolTipText="Total annual make-up water cost"
        )
        self.oamwateradjfactor = self.ParameterDict[self.oamwateradjfactor.Name] = floatParameter(
            "Water Cost Adjustment Factor",
            DefaultValue=1.0,
            Min=0,
            Max=10,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Provided=False,
            Valid=True,
            ToolTipText="Multiplier for built-in make-up water cost correlation"
        )
        self.totalcapcost = self.ParameterDict[self.totalcapcost.Name] = floatParameter(
            "Total Capital Cost",
            DefaultValue=-1.0,
            Min=0,
            Max=1000,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS,
            Provided=False,
            Valid=False,
            ErrMessage="calculate total capital cost using user-provided costs or" +
                       " built-in correlations for each category.",
            ToolTipText="Total initial capital cost."
        )
        self.oamtotalfixed = self.ParameterDict[self.oamtotalfixed.Name] = floatParameter(
            "Total O&M Cost",
            DefaultValue=-1.0,
            Min=0,
            Max=100,
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            Provided=False,
            Valid=False,
            ErrMessage="calculate total O&M cost using user-provided costs or built-in correlations for each category.",
            ToolTipText="Total initial O&M cost."
        )
        self.timestepsperyear = self.ParameterDict[self.timestepsperyear.Name] = intParameter(
            "Time steps per year",
            DefaultValue=4,
            AllowableRange=list(range(1, 101, 1)),
            UnitType=Units.NONE,
            Required=True,
            ErrMessage="assume default number of time steps per year (4)",
            ToolTipText="Number of internal simulation time steps per year"
        )
        self.FCR = self.ParameterDict[self.FCR.Name] = floatParameter(
            "Fixed Charge Rate",
            DefaultValue=0.1,
            Min=0.0,
            Max=1.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default fixed charge rate (0.1)",
            ToolTipText="Fixed charge rate (FCR) used in the Fixed Charge Rate Model"
        )
        self.discountrate = self.ParameterDict[self.discountrate.Name] = floatParameter(
            "Discount Rate",
            DefaultValue=0.07,
            Min=0.0,
            Max=1.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default discount rate (0.07)",
            ToolTipText="Discount rate used in the Standard Levelized Cost Model"
        )
        self.FIB = self.ParameterDict[self.FIB.Name] = floatParameter(
            "Fraction of Investment in Bonds",
            DefaultValue=0.5,
            Min=0.0,
            Max=1.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default fraction of investment in bonds (0.5)",
            ToolTipText="Fraction of geothermal project financing through bonds (see docs)"
        )
        self.BIR = self.ParameterDict[self.BIR.Name] = floatParameter(
            "Inflated Bond Interest Rate",
            DefaultValue=0.05,
            Min=0.0,
            Max=1.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default inflated bond interest rate (0.05)",
            ToolTipText="Inflated bond interest rate (see docs)"
        )
        self.EIR = self.ParameterDict[self.EIR.Name] = floatParameter(
            "Inflated Equity Interest Rate",
            DefaultValue=0.1,
            Min=0.0,
            Max=1.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default inflated equity interest rate (0.1)",
            ToolTipText="Inflated equity interest rate (see docs)"
        )
        self.RINFL = self.ParameterDict[self.RINFL.Name] = floatParameter(
            "Inflation Rate",
            DefaultValue=0.02,
            Min=0.0,
            Max=1.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default inflation rate (0.02)",
            ToolTipText="Inflation rate"
        )
        self.CTR = self.ParameterDict[self.CTR.Name] = floatParameter(
            "Combined Income Tax Rate",
            DefaultValue=0.02,
            Min=0.0,
            Max=1.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default combined income tax rate (0.3)",
            ToolTipText="Combined income tax rate (see docs)"
        )
        self.GTR = self.ParameterDict[self.GTR.Name] = floatParameter(
            "Gross Revenue Tax Rate",
            DefaultValue=0.02,
            Min=0.0,
            Max=1.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default gross revenue tax rate (0)",
            ToolTipText="Gross revenue tax rate (see docs)"
        )
        self.RITC = self.ParameterDict[self.RITC.Name] = floatParameter(
            "Investment Tax Credit Rate",
            DefaultValue=0.0,
            Min=0.0,
            Max=1.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default investment tax credit rate (0)",
            ToolTipText="Investment tax credit rate (see docs)"
        )
        self.PTR = self.ParameterDict[self.PTR.Name] = floatParameter(
            "Property Tax Rate",
            DefaultValue=0.0,
            Min=0.0,
            Max=1.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default property tax rate (0)",
            ToolTipText="Property tax rate (see docs)"
        )
        self.inflrateconstruction = self.ParameterDict[self.inflrateconstruction.Name] = floatParameter(
            "Inflation Rate During Construction",
            DefaultValue=0.0,
            Min=0.0,
            Max=1.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default inflation rate during construction (0)"
        )
        self.wellcorrelation = self.ParameterDict[self.wellcorrelation.Name] = intParameter(
            "Well Drilling Cost Correlation",
            DefaultValue=WellDrillingCostCorrelation.VERTICAL_LARGE_INT1,
            AllowableRange=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
            ValuesEnum=WellDrillingCostCorrelation,
            UnitType=Units.NONE,
            ErrMessage="assume default well drilling cost correlation (10)",
            ToolTipText="Select the built-in well drilling and completion cost correlation: " +
                        '; '.join([f'{it.int_value}: {it.value}' for it in WellDrillingCostCorrelation])
        )

        self.DoAddOnCalculations = self.ParameterDict[self.DoAddOnCalculations.Name] = boolParameter(
            "Do AddOn Calculations",
            DefaultValue=False,
            UnitType=Units.NONE,
            Required=False,
            ErrMessage="assume default: no economics calculations",
            ToolTipText="Set to true if you want the add-on economics calculations to be made"
        )
        self.DoCarbonCalculations = self.ParameterDict[self.DoCarbonCalculations.Name] = boolParameter(
            "Do Carbon Price Calculations",
            DefaultValue=False,
            UnitType=Units.NONE,
            Required=False,
            ErrMessage="assume default: no Carbon Credit calculations",
            ToolTipText="Set to true if you want the Carbon Credit economics calculations to be made"
        )
        self.DoSDACGTCalculations = self.ParameterDict[self.DoSDACGTCalculations.Name] = boolParameter(
            "Do S-DAC-GT Calculations",
            DefaultValue=False,
            UnitType=Units.NONE,
            Required=False,
            ErrMessage="assume default: no S-DAC-GT calculations",
            ToolTipText="Set to true if you want the S-DAC-GT economics calculations to be made"
        )
        self.Vertical_drilling_cost_per_m = self.ParameterDict[self.Vertical_drilling_cost_per_m.Name] = floatParameter(
            "All-in Vertical Drilling Costs",
            DefaultValue=1000.0,
            Min=0.0,
            Max=10_000.0,
            UnitType=Units.COSTPERDISTANCE,
            PreferredUnits=CostPerDistanceUnit.DOLLARSPERM,
            CurrentUnits=CostPerDistanceUnit.DOLLARSPERM,
            ErrMessage="assume default all-in cost for drill vertical well segment(s) (1000 $/m)",
            ToolTipText="Set user specified all-in cost per meter of vertical drilling," +
                        " including drilling, casing, cement, insulated insert"
        )
        self.Nonvertical_drilling_cost_per_m = self.ParameterDict[
            self.Nonvertical_drilling_cost_per_m.Name] = floatParameter(
            "All-in Nonvertical Drilling Costs",
            DefaultValue=1300.0,
            Min=0.0,
            Max=15_000.0,
            UnitType=Units.COSTPERDISTANCE,
            PreferredUnits=CostPerDistanceUnit.DOLLARSPERM,
            CurrentUnits=CostPerDistanceUnit.DOLLARSPERM,
            ErrMessage="assume default all-in cost for drill non-vertical well segment(s) (1300 $/m)",
            ToolTipText="Set user specified all-in cost per meter of non-vertical drilling, including" +
                        " drilling, casing, cement, insulated insert"
        )

        # absorption chiller
        self.chillercapex = self.ParameterDict[self.chillercapex.Name] = floatParameter(
            "Absorption Chiller Capital Cost",
            value=-1.0,
            DefaultValue=5,
            Min=0,
            Max=100,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS,
            Provided=False,
            Valid=False,
            ToolTipText="Absorption chiller capital cost"
        )
        self.chilleropex = self.ParameterDict[self.chilleropex.Name] = floatParameter(
            "Absorption Chiller O&M Cost",
            value=-1.0,
            DefaultValue=1,
            Min=0,
            Max=100,
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            Provided=False,
            Valid=False,
            ToolTipText="Absorption chiller O&M cost"
        )

        # heat pump
        self.heatpumpcapex = self.ParameterDict[self.heatpumpcapex.Name] = floatParameter(
            "Heat Pump Capital Cost",
            value=-1.0,
            DefaultValue=5,
            Min=0,
            Max=100,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS,
            Provided=False,
            Valid=False,
            ToolTipText="Heat pump capital cost"
        )

        # district heating
        self.ngprice = self.ParameterDict[self.ngprice.Name] = floatParameter(
            "Peaking Fuel Cost Rate",
            DefaultValue=0.034,
            Min=0.0,
            Max=1.0,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH,
            ErrMessage="assume default peaking fuel rate ($0.034/kWh)",
            ToolTipText="Price of peaking fuel for peaking boilers"
        )
        self.peakingboilerefficiency = self.ParameterDict[self.peakingboilerefficiency.Name] = floatParameter(
            "Peaking Boiler Efficiency",
            DefaultValue=0.85,
            Min=0,
            Max=1,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Provided=False,
            Valid=False,
            ErrMessage="assume default peaking boiler efficiency (85%)",
            ToolTipText="Peaking boiler efficiency"
        )
        self.dhpipingcostrate = self.ParameterDict[self.dhpipingcostrate.Name] = floatParameter(
            "District Heating Piping Cost Rate",
            DefaultValue=1200,
            Min=0,
            Max=10000,
            UnitType=Units.COSTPERDISTANCE,
            PreferredUnits=CostPerDistanceUnit.DOLLARSPERM,
            CurrentUnits=CostPerDistanceUnit.DOLLARSPERM,
            Provided=False,
            Valid=False,
            ErrMessage="assume default district heating piping cost rate ($1,200/m)",
            ToolTipText="District heating piping cost rate ($/m)"
        )
        self.dhtotaldistrictnetworkcost = self.ParameterDict[self.dhtotaldistrictnetworkcost.Name] = floatParameter(
            "Total District Heating Network Cost",
            DefaultValue=10,
            Min=0,
            Max=1000,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS,
            Provided=False,
            Valid=False,
            ErrMessage="assume default district heating network cost ($10M)",
            ToolTipText="Total district heating network cost ($M)"
        )
        self.dhoandmcost = self.ParameterDict[self.dhoandmcost.Name] = floatParameter(
            "District Heating O&M Cost",
            DefaultValue=1,
            Min=0,
            Max=100,
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            Provided=False, Valid=False,
            ToolTipText="Total annual district heating O&M cost ($M/year)"
        )
        self.dhpipinglength = self.ParameterDict[self.dhpipinglength.Name] = floatParameter(
            "District Heating Network Piping Length",
            DefaultValue=10.0,
            Min=0,
            Max=1000,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.KILOMETERS,
            CurrentUnits=LengthUnit.KILOMETERS,
            ErrMessage="assume default district heating network piping length (10 km)",
            ToolTipText="District heating network piping length (km)"
        )
        self.dhroadlength = self.ParameterDict[self.dhroadlength.Name] = floatParameter(
            "District Heating Road Length",
            DefaultValue=10.0,
            Min=0,
            Max=1000,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.KILOMETERS,
            CurrentUnits=LengthUnit.KILOMETERS,
            ErrMessage="assume default district heating road length (10 km)",
            ToolTipText="District heating road length (km)"
        )
        self.dhlandarea = self.ParameterDict[self.dhlandarea.Name] = floatParameter(
            "District Heating Land Area",
            DefaultValue=10.0,
            Min=0,
            Max=1000,
            UnitType=Units.AREA,
            PreferredUnits=AreaUnit.KILOMETERS2,
            CurrentUnits=AreaUnit.KILOMETERS2,
            ErrMessage="assume default district heating land area (10 km2)",
            ToolTipText="District heating land area (km2)"
        )
        self.dhpopulation = self.ParameterDict[self.dhpopulation.Name] = floatParameter(
            "District Heating Population",
            DefaultValue=200,
            Min=0,
            Max=1000000,
            UnitType=Units.NONE,
            ErrMessage="assume default population (200)",
            ToolTipText="Specify the population in the district heating network"
        )

        self.HeatStartPrice = self.ParameterDict[self.HeatStartPrice.Name] = floatParameter(
            "Starting Heat Sale Price",
            DefaultValue=0.025,
            Min=0,
            Max=100,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH
        )
        self.HeatEndPrice = self.ParameterDict[self.HeatEndPrice.Name] = floatParameter(
            "Ending Heat Sale Price",
            DefaultValue=0.025,
            Min=0,
            Max=100,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH
        )
        self.HeatEscalationStart = self.ParameterDict[self.HeatEscalationStart.Name] = intParameter(
            "Heat Escalation Start Year",
            DefaultValue=5,
            AllowableRange=list(range(0, 101, 1)),
            UnitType=Units.TIME,
            PreferredUnits=TimeUnit.YEAR,
            CurrentUnits=TimeUnit.YEAR,
            ErrMessage="assume default heat escalation delay time (5 years)",
            ToolTipText="Number of years after start of project before start of escalation"
        )
        self.HeatEscalationRate = self.ParameterDict[self.HeatEscalationRate.Name] = floatParameter(
            "Heat Escalation Rate Per Year",
            DefaultValue=0.0,
            Min=0.0,
            Max=100.0,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH,
            ErrMessage="assume no heat price escalation (0.0)",
            ToolTipText="additional cost per year of price after escalation starts"
        )
        self.ElecStartPrice = self.ParameterDict[self.ElecStartPrice.Name] = floatParameter(
            "Starting Electricity Sale Price",
            DefaultValue=0.055,
            Min=0,
            Max=100,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH
        )
        self.ElecEndPrice = self.ParameterDict[self.ElecEndPrice.Name] = floatParameter(
            "Ending Electricity Sale Price",
            DefaultValue=0.055,
            Min=0,
            Max=100,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH
        )
        self.ElecEscalationStart = self.ParameterDict[self.ElecEscalationStart.Name] = intParameter(
            "Electricity Escalation Start Year",
            DefaultValue=5,
            AllowableRange=list(range(0, 101, 1)),
            UnitType=Units.TIME,
            PreferredUnits=TimeUnit.YEAR,
            CurrentUnits=TimeUnit.YEAR,
            ErrMessage="assume default electricity escalation delay time (5 years)",
            ToolTipText="Number of years after start of project before start of escalation"
        )
        self.ElecEscalationRate = self.ParameterDict[self.ElecEscalationRate.Name] = floatParameter(
            "Electricity Escalation Rate Per Year",
            DefaultValue=0.0,
            Min=0.0,
            Max=100.0,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH,
            ErrMessage="assume no electricity price escalation (0.0)",
            ToolTipText="additional cost per year of price after escalation starts"
        )
        self.CoolingStartPrice = self.ParameterDict[self.CoolingStartPrice.Name] = floatParameter(
            "Starting Cooling Sale Price",
            DefaultValue=0.025,
            Min=0,
            Max=100,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH
        )
        self.CoolingEndPrice = self.ParameterDict[self.CoolingEndPrice.Name] = floatParameter(
            "Ending Cooling Sale Price",
            DefaultValue=0.025,
            Min=0,
            Max=100,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH
        )
        self.CoolingEscalationStart = self.ParameterDict[self.CoolingEscalationStart.Name] = intParameter(
            "Cooling Escalation Start Year",
            DefaultValue=5,
            AllowableRange=list(range(0, 101, 1)),
            UnitType=Units.TIME,
            PreferredUnits=TimeUnit.YEAR,
            CurrentUnits=TimeUnit.YEAR,
            ErrMessage="assume default cooling escalation delay time (5 years)",
            ToolTipText="Number of years after start of project before start of escalation"
        )
        self.CoolingEscalationRate = self.ParameterDict[self.CoolingEscalationRate.Name] = floatParameter(
            "Cooling Escalation Rate Per Year",
            DefaultValue=0.0,
            Min=0.0,
            Max=100.0,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH,
            ErrMessage="assume no cooling price escalation (0.0)",
            ToolTipText="additional cost per year of price after escalation starts"
        )
        self.CarbonStartPrice = self.ParameterDict[self.CarbonStartPrice.Name] = floatParameter(
            "Starting Carbon Credit Value",
            DefaultValue=0.0,
            Min=0,
            Max=1000,
            UnitType=Units.COSTPERMASS,
            PreferredUnits=CostPerMassUnit.DOLLARSPERLB,
            CurrentUnits=CostPerMassUnit.DOLLARSPERLB
        )
        self.CarbonEndPrice = self.ParameterDict[self.CarbonEndPrice.Name] = floatParameter(
            "Ending Carbon Credit Value",
            DefaultValue=0.0,
            Min=0,
            Max=1000,
            UnitType=Units.COSTPERMASS,
            PreferredUnits=CostPerMassUnit.DOLLARSPERLB,
            CurrentUnits=CostPerMassUnit.DOLLARSPERLB
        )
        self.CarbonEscalationStart = self.ParameterDict[self.CarbonEscalationStart.Name] = intParameter(
            "Carbon Escalation Start Year",
            DefaultValue=0,
            AllowableRange=list(range(0, 101, 1)),
            UnitType=Units.TIME,
            PreferredUnits=TimeUnit.YEAR,
            CurrentUnits=TimeUnit.YEAR,
            ErrMessage="assume default Carbon escalation delay time (5 years)",
            ToolTipText="Number of years after start of project before start of Carbon incentives"
            )
        self.CarbonEscalationRate = self.ParameterDict[self.CarbonEscalationRate.Name] = floatParameter(
            "Carbon Escalation Rate Per Year",
            DefaultValue=0.0,
            Min=0.0,
            Max=100.0,
            UnitType=Units.COSTPERMASS,
            PreferredUnits=CostPerMassUnit.DOLLARSPERLB,
            CurrentUnits=CostPerMassUnit.DOLLARSPERLB,
            ErrMessage="assume no Carbon credit escalation (0.0)",
            ToolTipText="additional value per year of price after escalation starts"
        )
        self.GridCO2Intensity = self.ParameterDict[self.GridCO2Intensity.Name] = floatParameter(
            "Current Grid CO2 production",
            DefaultValue=0.93916924,
            Min=0,
            Max=50000,
            UnitType=Units.CO2PRODUCTION,
            PreferredUnits=CO2ProductionUnit.LBSPERKWH,
            CurrentUnits=CO2ProductionUnit.LBSPERKWH,
            ErrMessage="assume the grid carbon intensity of Texas ERCOT by grid (0.93916924 lbs/kWh)",  #LBSPERKWH https://uh.edu/uh-energy-innovation/uh-energy/energy-research/white-papers/white-paper-files/net-zero-in-texas-electric-grid.pdf
            ToolTipText="CO2 intensity of the grid (how much CO2 is produced per kWh of electricity produced (0.93916924 lbs/kWh for Texas ERCOT))"
        )
        self.NaturalGasCO2Intensity = self.ParameterDict[self.NaturalGasCO2Intensity.Name] = floatParameter(
            "CO2 produced by Natural Gas",
            DefaultValue=0.070324961,
            Min=0,
            Max=50000,
            UnitType=Units.CO2PRODUCTION,
            PreferredUnits=CO2ProductionUnit.LBSPERKWH,
            CurrentUnits=CO2ProductionUnit.LBSPERKWH,
            ErrMessage="assume the default value CO2 production for burning natural gas (0.407855 lbs/kWh)",  #LBSPERKWH https://www.epa.gov/energy/greenhouse-gases-equivalencies-calculator-calculations-and-references
            ToolTipText="CO2 intensity of buring natural gas (how much CO2 is produced per kWh of heat produced (0.407855 lbs/kWh))"
        )

        self.AnnualLicenseEtc = self.ParameterDict[self.AnnualLicenseEtc.Name] = floatParameter(
            "Annual License Fees Etc",
            DefaultValue=0.0,
            Min=-1000.0,
            Max=1000.0,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.FlatLicenseEtc = self.ParameterDict[self.FlatLicenseEtc.Name] = floatParameter(
            "One-time Flat License Fees Etc",
            Min=-1000.0,
            Max=1000.0,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.OtherIncentives = self.ParameterDict[self.OtherIncentives.Name] = floatParameter(
            "Other Incentives",
            Min=-1000.0,
            Max=1000.0,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.TaxRelief = self.ParameterDict[self.TaxRelief.Name] = floatParameter(
            "Tax Relief Per Year",
            DefaultValue=0.0,
            Min=0.0,
            Max=100.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.PERCENT,
            CurrentUnits=PercentUnit.PERCENT,
            ErrMessage="assume no tax relief (0.0)",
            ToolTipText="Fixed percent reduction in annual tax rate"
        )
        self.TotalGrant = self.ParameterDict[self.TotalGrant.Name] = floatParameter(
            "One-time Grants Etc",
            Min=-1000.0,
            Max=1000.0,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.FixedInternalRate = self.ParameterDict[self.FixedInternalRate.Name] = floatParameter(
            "Fixed Internal Rate",
            DefaultValue=6.25,
            Min=0.0,
            Max=100.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.PERCENT,
            CurrentUnits=PercentUnit.PERCENT,
            ErrMessage="assume default for fixed internal rate (6.25%)",
            ToolTipText="Fixed Internal Rate (used in NPV calculation)"
        )
        self.CAPEX_heat_electricity_plant_ratio = self.ParameterDict[self.CAPEX_heat_electricity_plant_ratio.Name] = floatParameter(
            "CHP Electrical Plant Cost Allocation Ratio",
            DefaultValue=-1.0,
            Min=0.0,
            Max=1.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Provided=False,
            ErrMessage="assume calculation for CHP Electrical Plant Cost Allocation Ratio (cost electrical plant/total CAPEX)",
            ToolTipText="CHP Electrical Plant Cost Allocation Ratio (cost electrical plant/total CAPEX)"
        )
        self.PTCElec = self.ParameterDict[self.PTCElec.Name] = floatParameter(
            "Production Tax Credit Electricity",
            DefaultValue=0.04,
            Min=0.0,
            Max=10.0,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH,
            ErrMessage="assume default for Production Tax Credit Electricity ($0.04/kWh)",
            ToolTipText="Production tax credit for electricity in $/kWh"
        )
        self.PTCHeat = self.ParameterDict[self.PTCHeat.Name] = floatParameter(
            "Production Tax Credit Heat",
            DefaultValue=0.0,
            Min=0.0,
            Max=100.0,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERMMBTU,
            CurrentUnits=EnergyCostUnit.DOLLARSPERMMBTU,
            ErrMessage="assume default for Production Tax Credit Heat ($0.0/MMBTU)",
            ToolTipText="Production tax credit for heat in $/MMBTU"
        )
        self.PTCCooling = self.ParameterDict[self.PTCCooling.Name] = floatParameter(
            "Production Tax Credit Cooling",
            DefaultValue=0.0,
            Min=0.0,
            Max=100.0,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERMMBTU,
            CurrentUnits=EnergyCostUnit.DOLLARSPERMMBTU,
            ErrMessage="assume default for Production Tax Credit Cooling ($0.0/MMBTU)",
            ToolTipText="Production tax credit for cooling in $/MMBTU"
        )
        self.PTCDuration = self.ParameterDict[self.PTCDuration.Name] = intParameter(
            "Production Tax Credit Duration",
            DefaultValue=10,
            AllowableRange=list(range(0, 100, 1)),
            UnitType=Units.TIME,
            PreferredUnits=TimeUnit.YEAR,
            CurrentUnits=TimeUnit.YEAR,
            ErrMessage="assume default for Production Tax Credit Duration (10 years)",
            ToolTipText="Production tax credit for duration in years"
        )
        self.PTCInflationAdjusted = self.ParameterDict[self.PTCInflationAdjusted.Name] = boolParameter(
            "Production Tax Credit Inflation Adjusted",
            DefaultValue=False,
            UnitType=Units.NONE,
            Required=False,
            ErrMessage="assume default for Production Tax Credit Inflation Adjusted (False)",
            ToolTipText="Production tax credit inflation adjusted"
        )

        self.jobs_created_per_MW_electricity = self.ParameterDict[
            self.jobs_created_per_MW_electricity.Name] = floatParameter(
            "Estimated Jobs Created per MW of Electricity Produced",
            DefaultValue=2.13,
            UnitType=Units.NONE,
            Required=False,
            ToolTipText="Estimated jobs created per MW of electricity produced, per https://geothermal.org/resources/geothermal-basics"
        )

        # local variable initialization
        self.CAPEX_cost_electricity_plant = 0.0
        self.CAPEX_cost_heat_plant = 0.0
        self.OPEX_cost_electricity_plant = 0.0
        self.OPEX_cost_heat_plant = 0.0
        self.CAPEX_heat_electricity_plant_ratio.value = 0.0
        self.Claborcorrelation = 0.0
        self.Cpumps = 0.0
        self.annualelectricityincome = 0.0
        self.annualheatincome = 0.0
        self.InputFile = ""
        self.Cplantcorrelation = 0.0
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = os.path.abspath(__file__)

        # results
        self.ElecPrice = self.OutputParameterDict[self.ElecPrice.Name] = OutputParameter(
            "Electricity Sale Price Model",
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.CENTSSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH,
        )
        self.HeatPrice = self.OutputParameterDict[self.HeatPrice.Name] = OutputParameter(
            "Heat Sale Price Model",
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.CENTSSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH,
        )
        self.CoolingPrice = self.OutputParameterDict[self.CoolingPrice.Name] = OutputParameter(
            "Cooling Sale Price Model",
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.CENTSSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH,
        )
        self.CarbonPrice = self.OutputParameterDict[self.CarbonPrice.Name] = OutputParameter(
            "Carbon Price Model",
            UnitType=Units.COSTPERMASS,
            PreferredUnits=CostPerMassUnit.DOLLARSPERTONNE,
            CurrentUnits=CostPerMassUnit.DOLLARSPERTONNE
        )

        self.LCOC = self.OutputParameterDict[self.LCOC.Name] = OutputParameter(
            Name="LCOC",
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERMMBTU,
            CurrentUnits=EnergyCostUnit.DOLLARSPERMMBTU
        )

        self.LCOE = self.OutputParameterDict[self.LCOE.Name] = OutputParameter(
            Name="LCOE",
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.CENTSSPERKWH,
            CurrentUnits=EnergyCostUnit.CENTSSPERKWH
        )
        self.LCOH = self.OutputParameterDict[self.LCOH.Name] = OutputParameter(
            Name="LCOH",
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERMMBTU,
            CurrentUnits=EnergyCostUnit.DOLLARSPERMMBTU
        )  # $/MMBTU
        self.Cstim = self.OutputParameterDict[self.Cstim.Name] = OutputParameter(
            Name="O&M Surface Plant costs",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.Cexpl = self.OutputParameterDict[self.Cexpl.Name] = OutputParameter(
            Name="Exploration cost",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.Cwell = self.OutputParameterDict[self.Cwell.Name] = OutputParameter(
            Name="Wellfield cost",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.Coamwell = self.OutputParameterDict[self.Coamwell.Name] = OutputParameter(
            Name="O&M Wellfield cost",
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.Cplant = self.OutputParameterDict[self.Cplant.Name] = OutputParameter(
            Name="Surface Plant cost",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.Coamplant = self.OutputParameterDict[self.Coamplant.Name] = OutputParameter(
            Name="O&M Surface Plant costs",
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.Cgath = self.OutputParameterDict[self.Cgath.Name] = OutputParameter(
            Name="Field gathering system cost",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.Cpiping = self.OutputParameterDict[self.Cpiping.Name] = OutputParameter(
            Name="Transmission pipeline costs",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.Coamwater = self.OutputParameterDict[self.Coamwater.Name] = OutputParameter(
            Name="O&M Make-up Water costs",
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.CCap = self.OutputParameterDict[self.CCap.Name] = OutputParameter(
            Name="Total Capital Cost",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.Coam = self.OutputParameterDict[self.Coam.Name] = OutputParameter(
            Name="Total O&M Cost",
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
#        self.averageannualpumpingcosts = self.OutputParameterDict[
#            self.averageannualpumpingcosts.Name] = OutputParameter(  #typo here!??!
        self.averageannualpumpingcosts = OutputParameter(
            Name="Average Annual Pumping Costs",
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        # heat pump
        self.averageannualheatpumpelectricitycost = self.OutputParameterDict[
            self.averageannualheatpumpelectricitycost.Name] = OutputParameter(
            Name="Average Annual Heat Pump Electricity Cost",
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        # district heating
        self.peakingboilercost = self.OutputParameterDict[self.peakingboilercost.Name] = OutputParameter(
            Name="Peaking boiler cost",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.dhdistrictcost = self.OutputParameterDict[self.dhdistrictcost.Name] = OutputParameter(
            Name="District Heating System Cost",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.populationdensity = self.OutputParameterDict[self.populationdensity.Name] = OutputParameter(
            Name="District Heating System Population Density",
            UnitType=Units.POPDENSITY,
            PreferredUnits=PopDensityUnit.perkm2,
            CurrentUnits=PopDensityUnit.perkm2
        )
        self.annualngcost = self.OutputParameterDict[self.annualngcost.Name] = OutputParameter(
            Name="Annual Peaking Fuel Cost",
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.dhdistrictoandmcost = self.OutputParameterDict[self.dhdistrictoandmcost.Name] = OutputParameter(
            Name="Annual District Heating O&M Cost",
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.averageannualngcost = self.OutputParameterDict[self.averageannualngcost.Name] = OutputParameter(
            Name="Average Annual Peaking Fuel Cost",
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )

        self.ElecRevenue = self.OutputParameterDict[self.ElecRevenue.Name] = OutputParameter(
            Name="Annual Revenue from Electricity Production",
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.ElecCummRevenue = self.OutputParameterDict[self.ElecCummRevenue.Name] = OutputParameter(
            Name="Cumulative Revenue from Electricity Production",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.HeatRevenue = self.OutputParameterDict[self.HeatRevenue.Name] = OutputParameter(
            Name="Annual Revenue from Heat Production",
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.HeatCummRevenue = self.OutputParameterDict[self.HeatCummRevenue.Name] = OutputParameter(
            Name="Cumulative Revenue from Heat Production",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.CoolingRevenue = self.OutputParameterDict[self.CoolingRevenue.Name] = OutputParameter(
            Name="Annual Revenue from Cooling Production",
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.CoolingCummRevenue = self.OutputParameterDict[self.CoolingCummRevenue.Name] = OutputParameter(
            Name="Cumulative Revenue from Cooling Production",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.CarbonRevenue = self.OutputParameterDict[self.CarbonRevenue.Name] = OutputParameter(
            Name="Annual Revenue from Carbon Pricing",
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.CarbonCummCashFlow = self.OutputParameterDict[self.CarbonCummCashFlow.Name] = OutputParameter(
            Name="Cumulative Revenue from Carbon Pricing",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.CarbonThatWouldHaveBeenProducedAnnually = self.OutputParameterDict[
            self.CarbonThatWouldHaveBeenProducedAnnually.Name] = OutputParameter(
            "Annual Saved Carbon Production",
            UnitType=Units.MASS,
            PreferredUnits=MassUnit.LB,
            CurrentUnits=MassUnit.LB
        )
        self.CarbonThatWouldHaveBeenProducedTotal = self.OutputParameterDict[
            self.CarbonThatWouldHaveBeenProducedTotal.Name] = OutputParameter(
            "Total Saved Carbon Production",
            UnitType=Units.MASS,
            PreferredUnits=MassUnit.LB,
            CurrentUnits=MassUnit.LB
        )
        self.TotalRevenue = self.OutputParameterDict[self.TotalRevenue.Name] = OutputParameter(
            Name="Annual Revenue from Project",
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.TotalCummRevenue = self.OutputParameterDict[self.TotalCummRevenue.Name] = OutputParameter(
            Name="Cumulative Revenue from Project",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.ProjectNPV = self.OutputParameterDict[self.ProjectNPV.Name] = OutputParameter(
            "Project Net Present Value",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.ProjectIRR = self.OutputParameterDict[self.ProjectIRR.Name] = OutputParameter(
            "Project Internal Rate of Return",
            UnitType=Units.PERCENT,
            CurrentUnits=PercentUnit.PERCENT,
            PreferredUnits=PercentUnit.PERCENT,
        )
        self.ProjectVIR = self.OutputParameterDict[self.ProjectVIR.Name] = OutputParameter(
            "Project Value Investment Ratio",
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH
        )
        self.ProjectMOIC = self.OutputParameterDict[self.ProjectMOIC.Name] = OutputParameter(
            "Project Multiple of Invested Capital",
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH
        )
        self.ProjectPaybackPeriod = self.OutputParameterDict[self.ProjectPaybackPeriod.Name] = OutputParameter(
            "Project Payback Period",
            UnitType=Units.TIME,
            PreferredUnits=TimeUnit.YEAR,
            CurrentUnits=TimeUnit.YEAR
        )
        self.RITCValue = self.OutputParameterDict[self.RITCValue.Name] = OutputParameter(
            Name="Investment Tax Credit Value",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.cost_one_production_well = self.OutputParameterDict[self.cost_one_production_well.Name] = OutputParameter(
            Name="Cost of One Production Well",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.cost_one_injection_well = self.OutputParameterDict[self.cost_one_injection_well.Name] = OutputParameter(
            Name="Cost of One Injection Well",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.cost_nonvertical_section = self.OutputParameterDict[self.cost_nonvertical_section.Name] = OutputParameter(
            Name="Cost of the non-vertical section of a well",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.jobs_created = self.OutputParameterDict[self.jobs_created.Name] = OutputParameter(
            Name="Estimated Jobs Created",
            UnitType=Units.NONE,
        )

        model.logger.info(f'Complete {__class__!s}: {sys._getframe().f_code.co_name}')

    def read_parameters(self, model: Model) -> None:
        """
        read_parameters read and update the Economics parameters and handle the special cases
        Deal with all the parameter values that the user has provided.  They should really only provide values
        that they want to change from the default values, but they can provide a value that is already set
        because it is a default value set in __init__.  It will ignore those.
        This also deals with all the special cases that need to be taken care of after a
        value has been read in and checked.
        If you choose to subclass this master class, you can also choose to override this method (or not),
        and if you do, do it before or after you call you own version of this method.  If you do, you can also
        choose to call this method from you class, which can effectively modify all these superclass parameters
        in your class.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        model.logger.info(f'Init {__class__!s}: {sys._getframe().f_code.co_name}')

        if len(model.InputParameters) > 0:
            # loop through all the parameters that the user wishes to set, looking for parameters that match this object
            for item in self.ParameterDict.items():
                ParameterToModify = item[1]
                key = ParameterToModify.Name.strip()
                if key in model.InputParameters:
                    ParameterReadIn = model.InputParameters[key]
                    # Before we change the parameter, let's assume that the unit preferences will match
                    # - if they don't, the later code will fix this.
                    ParameterToModify.CurrentUnits = ParameterToModify.PreferredUnits
                    # this should handle all the non-special cases
                    ReadParameter(ParameterReadIn, ParameterToModify, model)

                    # handle special cases
                    if ParameterToModify.Name == "Economic Model":
                        if ParameterReadIn.sValue == '1':
                            self.econmodel.value = EconomicModel.FCR
                        elif ParameterReadIn.sValue == '2':
                            # use standard LCOE/LCOH calculation as found on wikipedia (requires an interest rate).
                            self.econmodel.value = EconomicModel.STANDARDIZED_LEVELIZED_COST
                        elif ParameterReadIn.sValue == '3':
                            # use Bicycle LCOE/LCOH model (requires several financial input parameters)
                            self.econmodel.value = EconomicModel.BICYCLE
                        else:
                            self.econmodel.value = EconomicModel.CLGS  # CLGS
                    elif ParameterToModify.Name == "Well Drilling Cost Correlation":
                        if ParameterReadIn.sValue == '1':
                            ParameterToModify.value = WellDrillingCostCorrelation.VERTICAL_SMALL
                        elif ParameterReadIn.sValue == '2':
                            ParameterToModify.value = WellDrillingCostCorrelation.DEVIATED_SMALL
                        elif ParameterReadIn.sValue == '3':
                            ParameterToModify.value = WellDrillingCostCorrelation.VERTICAL_LARGE
                        elif ParameterReadIn.sValue == '4':
                            ParameterToModify.value = WellDrillingCostCorrelation.DEVIATED_LARGE
                        elif ParameterReadIn.sValue == '5':
                            ParameterToModify.value = WellDrillingCostCorrelation.SIMPLE
                        elif ParameterReadIn.sValue == '6':
                            ParameterToModify.value = WellDrillingCostCorrelation.VERTICAL_SMALL_INT1
                        elif ParameterReadIn.sValue == '7':
                            ParameterToModify.value = WellDrillingCostCorrelation.VERTICAL_SMALL_INT2
                        elif ParameterReadIn.sValue == '8':
                            ParameterToModify.value = WellDrillingCostCorrelation.DEVIATED_SMALL_INT1
                        elif ParameterReadIn.sValue == '9':
                            ParameterToModify.value = WellDrillingCostCorrelation.DEVIATED_SMALL_INT2
                        elif ParameterReadIn.sValue == '10':
                            ParameterToModify.value = WellDrillingCostCorrelation.VERTICAL_LARGE_INT1
                        elif ParameterReadIn.sValue == '11':
                            ParameterToModify.value = WellDrillingCostCorrelation.VERTICAL_LARGE_INT2
                        elif ParameterReadIn.sValue == '12':
                            ParameterToModify.value = WellDrillingCostCorrelation.DEVIATED_LARGE_INT1
                        elif ParameterReadIn.sValue == '13':
                            ParameterToModify.value = WellDrillingCostCorrelation.DEVIATED_LARGE_INT2
                        elif ParameterReadIn.sValue == '14':
                            ParameterToModify.value = WellDrillingCostCorrelation.VERTICAL_SMALL_IDEAL
                        elif ParameterReadIn.sValue == '15':
                            ParameterToModify.value = WellDrillingCostCorrelation.DEVIATED_SMALL_IDEAL
                        elif ParameterReadIn.sValue == '16':
                            ParameterToModify.value = WellDrillingCostCorrelation.VERTICAL_LARGE_IDEAL
                        elif ParameterReadIn.sValue == '17':
                            ParameterToModify.value = WellDrillingCostCorrelation.DEVIATED_LARGE_IDEAL
                        else:
                            ParameterToModify.value = WellDrillingCostCorrelation.SIMPLE  # Assuming 'SIMPLE' is still a valid option
                    elif ParameterToModify.Name == "Reservoir Stimulation Capital Cost Adjustment Factor":
                        if self.ccstimfixed.Valid and ParameterToModify.Valid:
                            print("Warning: Provided reservoir stimulation cost adjustment factor not considered" +
                                  " because valid total reservoir stimulation cost provided.")
                            model.logger.warning(
                                "Provided reservoir stimulation cost adjustment factor not considered" +
                                " because valid total reservoir stimulation cost provided.")
                        elif not self.ccstimfixed.Provided and not ParameterToModify.Provided:
                            ParameterToModify.value = 1.0
                            print("Warning: No valid reservoir stimulation total cost or adjustment factor provided." +
                                  " GEOPHIRES will assume default built-in reservoir stimulation cost correlation with" +
                                  " adjustment factor = 1.")
                            model.logger.warning("No valid reservoir stimulation total cost or adjustment factor" +
                                                 " provided. GEOPHIRES will assume default built-in reservoir stimulation cost correlation" +
                                                 " with adjustment factor = 1.")
                        elif self.ccstimfixed.Provided and not self.ccstimfixed.Valid:
                            print("Warning: Provided reservoir stimulation cost outside of range 0-100. GEOPHIRES" +
                                  " will assume default built-in reservoir stimulation cost correlation with" +
                                  " adjustment factor = 1.")
                            model.logger.warning(
                                "Provided reservoir stimulation cost outside of range 0-100. GEOPHIRES" +
                                " will assume default built-in reservoir stimulation cost correlation with" +
                                " adjustment factor = 1.")
                            ParameterToModify.value = 1.0
                        elif not self.ccstimfixed.Provided and ParameterToModify.Provided and not ParameterToModify.Valid:
                            print("Warning: Provided reservoir stimulation cost adjustment factor outside of" +
                                  " range 0-10. GEOPHIRES will assume default reservoir stimulation cost correlation with" +
                                  " adjustment factor = 1.")
                            model.logger.warning("Provided reservoir stimulation cost adjustment factor outside of" +
                                                 " range 0-10. GEOPHIRES will assume default reservoir stimulation cost correlation with" +
                                                 " adjustment factor = 1.")
                            ParameterToModify.value = 1.0
                    elif ParameterToModify.Name == "Exploration Capital Cost Adjustment Factor":
                        if self.totalcapcost.Valid:
                            if self.ccexplfixed.Provided:
                                print("Warning: Provided exploration cost not considered because valid" +
                                      " total capital cost provided.")
                                model.logger.warning("Warning: Provided exploration cost not considered" +
                                                     " because valid total capital cost provided.")
                            if ParameterToModify.Provided:
                                print("Warning: Provided exploration cost adjustment factor not considered because" +
                                      " valid total capital cost provided.")
                                model.logger.warning("Warning: Provided exploration cost not considered because valid" +
                                                     " total capital cost provided.")
                        else:
                            if self.ccexplfixed.Valid and ParameterToModify.Valid:
                                print("Warning: Provided exploration cost adjustment factor not considered" +
                                      " because valid total exploration cost provided.")
                                model.logger.warning("Provided exploration cost adjustment factor not" +
                                                     " considered because valid total exploration cost provided.")
                            elif not self.ccexplfixed.Provided and not ParameterToModify.Provided:
                                ParameterToModify.value = 1.0
                                print("Warning: No valid exploration total cost or adjustment factor provided." +
                                      " GEOPHIRES will assume default built-in exploration cost correlation with" +
                                      " adjustment factor = 1.")
                                model.logger.warning("No valid exploration total cost or adjustment factor provided." +
                                                     " GEOPHIRES will assume default built-in exploration cost correlation with" +
                                                     " adjustment factor = 1.")
                            elif self.ccexplfixed.Provided and not self.ccexplfixed.Valid:
                                print("Warning: Provided exploration cost outside of range 0-100. GEOPHIRES" +
                                      " will assume default built-in exploration cost correlation with adjustment factor = 1.")
                                model.logger.warning("Provided exploration cost outside of range 0-100. GEOPHIRES" +
                                                     " will assume default built-in exploration cost correlation with adjustment factor = 1.")
                                ParameterToModify.value = 1.0
                            elif not self.ccexplfixed.Provided and ParameterToModify.Provided and not ParameterToModify.Valid:
                                print("Warning: Provided exploration cost adjustment factor outside of range 0-10." +
                                      " GEOPHIRES will assume default exploration cost correlation with adjustment factor = 1.")
                                model.logger.warning("Provided exploration cost adjustment factor outside of" +
                                                     " range 0-10. GEOPHIRES will assume default exploration cost correlation with" +
                                                     " adjustment factor = 1.")
                                ParameterToModify.value = 1.0
                    elif ParameterToModify.Name == "Well Drilling and Completion Capital Cost Adjustment Factor":
                        if self.per_production_well_cost.Valid and ParameterToModify.Valid:
                            print("Warning: Provided well drilling and completion cost adjustment factor not" +
                                  " considered because valid total well drilling and completion cost provided.")
                            model.logger.warning("Provided well drilling and completion cost adjustment factor not" +
                                                 " considered because valid total well drilling and completion cost provided.")
                        elif not self.per_production_well_cost.Provided and not self.production_well_cost_adjustment_factor.Provided:
                            ParameterToModify.value = 1.0
                            print("Warning: No valid well drilling and completion total cost or adjustment" +
                                  " factor provided. GEOPHIRES will assume default built-in well drilling and" +
                                  " completion cost correlation with adjustment factor = 1.")
                            model.logger.warning(
                                "No valid well drilling and completion total cost or adjustment factor" +
                                " provided. GEOPHIRES will assume default built-in well drilling and completion cost" +
                                " correlation with adjustment factor = 1.")
                        elif self.per_production_well_cost.Provided and not self.per_production_well_cost.Valid:
                            print("Warning: Provided well drilling and completion cost outside of range 0-1000." +
                                  " GEOPHIRES will assume default built-in well drilling and completion cost correlation" +
                                  " with adjustment factor = 1.")
                            model.logger.warning("Provided well drilling and completion cost outside of range 0-1000." +
                                                 " GEOPHIRES will assume default built-in well drilling and completion cost correlation with" +
                                                 " adjustment factor = 1.")
                            self.production_well_cost_adjustment_factor.value = 1.0
                        elif not self.per_production_well_cost.Provided and self.production_well_cost_adjustment_factor.Provided and not self.production_well_cost_adjustment_factor.Valid:
                            print("Warning: Provided well drilling and completion cost adjustment factor outside" +
                                  " of range 0-10. GEOPHIRES will assume default built-in well drilling and completion" +
                                  " cost correlation with adjustment factor = 1.")
                            model.logger.warning(
                                "Provided well drilling and completion cost adjustment factor outside" +
                                " of range 0-10. GEOPHIRES will assume default built-in well drilling and completion" +
                                " cost correlation with adjustment factor = 1.")
                            self.production_well_cost_adjustment_factor.value = 1.0
                    elif ParameterToModify.Name == "Wellfield O&M Cost Adjustment Factor":
                        if self.oamtotalfixed.Valid:
                            if self.oamwellfixed.Provided:
                                print("Warning: Provided total wellfield O&M cost not considered because" +
                                      " valid total annual O&M cost provided.")
                                model.logger.warning("Provided total wellfield O&M cost not considered because" +
                                                     " valid total annual O&M cost provided.")
                            if ParameterToModify.Provided:
                                print("Warning: Provided wellfield O&M cost adjustment factor not considered because" +
                                      " valid total annual O&M cost provided.")
                                model.logger.warning("Provided wellfield O&M cost adjustment factor not considered" +
                                                     " because valid total annual O&M cost provided.")
                        else:
                            if self.oamwellfixed.Valid and ParameterToModify.Valid:
                                print("Warning: Provided wellfield O&M cost adjustment factor not considered" +
                                      " because valid total wellfield O&M cost provided.")
                                model.logger.warning("Provided wellfield O&M cost adjustment factor not considered" +
                                                     " because valid total wellfield O&M cost provided.")
                            elif not self.oamwellfixed.Provided and not ParameterToModify.Provided:
                                ParameterToModify.value = 1.0
                                print("Warning: No valid total wellfield O&M cost or adjustment factor provided." +
                                      " GEOPHIRES will assume default built-in wellfield O&M cost correlation with" +
                                      " adjustment factor = 1.")
                                model.logger.warning("No valid total wellfield O&M cost or adjustment factor" +
                                                     " provided. GEOPHIRES will assume default built-in wellfield O&M cost correlation" +
                                                     " with adjustment factor = 1.")
                            elif self.oamwellfixed.Provided and not self.oamwellfixed.Valid:
                                print("Warning: Provided total wellfield O&M cost outside of range 0-100." +
                                      " GEOPHIRES will assume default built-in wellfield O&M cost correlation with" +
                                      " adjustment factor = 1.")
                                model.logger.warning("Provided total wellfield O&M cost outside of range 0-100." +
                                                     " GEOPHIRES will assume default built-in wellfield O&M cost correlation with" +
                                                     " adjustment factor = 1.")
                                ParameterToModify.value = 1.0
                            elif not self.oamwellfixed.Provided and self.oamwelladjfactor.Provided and not self.oamwelladjfactor.Valid:
                                print("Warning: Provided wellfield O&M cost adjustment factor outside of range 0-10." +
                                      " GEOPHIRES will assume default wellfield O&M cost correlation with adjustment factor = 1.")
                                model.logger.warning("Provided wellfield O&M cost adjustment factor outside of" +
                                                     " range 0-10. GEOPHIRES will assume default wellfield O&M cost correlation with" +
                                                     " adjustment factor = 1.")
                                ParameterToModify.value = 1.0
                    elif ParameterToModify.Name == "Surface Plant Capital Cost Adjustment Factor":
                        if self.totalcapcost.Valid:
                            if self.ccplantfixed.Provided:
                                print("Warning: Provided surface plant cost not considered because valid" +
                                      " total capital cost provided.")
                                model.logger.warning("Provided surface plant cost not considered because valid" +
                                                     " total capital cost provided.")
                            if ParameterToModify.Provided:
                                print("Warning: Provided surface plant cost adjustment factor not considered" +
                                      " because valid total capital cost provided.")
                                model.logger.warning("Provided surface plant cost adjustment factor not considered" +
                                                     " because valid total capital cost provided.")
                        else:
                            if self.ccplantfixed.Valid and ParameterToModify.Valid:
                                print("Warning: Provided surface plant cost adjustment factor not considered because" +
                                      " valid total surface plant cost provided.")
                                model.logger.warning("Provided surface plant cost adjustment factor not considered" +
                                                     " because valid total surface plant cost provided.")
                            elif not self.ccplantfixed.Provided and not ParameterToModify.Provided:
                                ParameterToModify.value = 1.0
                                print("Warning: No valid surface plant total cost or adjustment factor provided." +
                                      " GEOPHIRES will assume default built-in surface plant cost correlation with" +
                                      " adjustment factor = 1.")
                                model.logger.warning("No valid surface plant total cost or adjustment factor" +
                                                     " provided. GEOPHIRES will assume default built-in surface plant cost correlation" +
                                                     " with adjustment factor = 1.")
                            elif self.ccplantfixed.Provided and not self.ccplantfixed.Valid:
                                print("Warning: Provided surface plant cost outside of range 0-1000." +
                                      " GEOPHIRES will assume default built-in surface plant cost correlation with" +
                                      " adjustment factor = 1.")
                                model.logger.warning("Provided surface plant cost outside of range 0-1000." +
                                                     " GEOPHIRES will assume default built-in surface plant cost correlation with" +
                                                     " adjustment factor = 1.")
                                ParameterToModify.value = 1.0
                            elif not self.ccplantfixed.Provided and self.ccplantadjfactor.Provided and not self.ccplantadjfactor.Valid:
                                print("Warning: Provided surface plant cost adjustment factor outside of range 0-10." +
                                      " GEOPHIRES will assume default surface plant cost correlation with" +
                                      " adjustment factor = 1.")
                                model.logger.warning("Provided surface plant cost adjustment factor outside of" +
                                                     " range 0-10. GEOPHIRES will assume default surface plant cost correlation with" +
                                                     " adjustment factor = 1.")
                                ParameterToModify.value = 1.0
                    elif ParameterToModify.Name == "Field Gathering System Capital Cost Adjustment Factor":
                        if self.totalcapcost.Valid:
                            if self.ccgathfixed.Provided:
                                print("Warning: Provided field gathering system cost not considered because valid" +
                                      " total capital cost provided.")
                                model.logger.warning(
                                    "Provided field gathering system cost not considered because valid" +
                                    " total capital cost provided.")
                            if ParameterToModify.Provided:
                                print("Warning: Provided field gathering system cost adjustment factor not" +
                                      " considered because valid total capital cost provided.")
                                model.logger.warning("Provided field gathering system cost adjustment factor not" +
                                                     " considered because valid total capital cost provided.")
                        else:
                            if self.ccgathfixed.Valid and ParameterToModify.Valid:
                                print("Warning: Provided field gathering system cost adjustment factor not" +
                                      " considered because valid total field gathering system cost provided.")
                                model.logger.warning("Provided field gathering system cost adjustment factor not" +
                                                     " considered because valid total field gathering system cost provided.")
                            elif not self.ccgathfixed.Provided and not ParameterToModify.Provided:
                                ParameterToModify.value = 1.0
                                print("Warning: No valid field gathering system total cost or adjustment factor" +
                                      " provided. GEOPHIRES will assume default built-in field gathering system cost" +
                                      " correlation with adjustment factor = 1.")
                                model.logger.warning("No valid field gathering system total cost or adjustment factor" +
                                                     " provided. GEOPHIRES will assume default built-in field gathering system cost" +
                                                     " correlation with adjustment factor = 1.")
                            elif self.ccgathfixed.Provided and not self.ccgathfixed.Valid:
                                print("Warning: Provided field gathering system cost outside of range 0-100." +
                                      " GEOPHIRES will assume default built-in field gathering system cost correlation" +
                                      " with adjustment factor = 1.")
                                model.logger.warning("Provided field gathering system cost outside of range 0-100." +
                                                     " GEOPHIRES will assume default built-in field gathering system cost correlation with" +
                                                     " adjustment factor = 1.")
                                ParameterToModify.value = 1.0
                            elif not self.ccgathfixed.Provided and ParameterToModify.Provided and not ParameterToModify.Valid:
                                print("Warning: Provided field gathering system cost adjustment factor" +
                                      " outside of range 0-10. GEOPHIRES will assume default field gathering system" +
                                      " cost correlation with adjustment factor = 1.")
                                model.logger.warning("Provided field gathering system cost adjustment factor" +
                                                     " outside of range 0-10. GEOPHIRES will assume default field gathering system cost" +
                                                     " correlation with adjustment factor = 1.")
                                ParameterToModify.value = 1.0
                    elif ParameterToModify.Name == "Water Cost Adjustment Factor":
                        if self.oamtotalfixed.Valid:
                            if self.oamwaterfixed.Provided:
                                print("Warning: Provided total water cost not considered because valid" +
                                      " total annual O&M cost provided.")
                                model.logger.warning("Provided total water cost not considered because valid" +
                                                     " total annual O&M cost provided.")
                            if ParameterToModify.Provided:
                                print("Warning: Provided water cost adjustment factor not considered because" +
                                      " valid total annual O&M cost provided.")
                                model.logger.warning("Provided water cost adjustment factor not considered because" +
                                                     " valid total annual O&M cost provided.")
                        else:
                            if self.oamwaterfixed.Valid and ParameterToModify.Valid:
                                print("Warning: Provided water cost adjustment factor not considered because" +
                                      " valid total water cost provided.")
                                model.logger.warning("Provided water cost adjustment factor not considered because" +
                                                     " valid total water cost provided.")
                            elif not self.oamwaterfixed.Provided and not ParameterToModify.Provided:
                                ParameterToModify.value = 1.0
                                print("Warning: No valid total water cost or adjustment factor provided." +
                                      " GEOPHIRES will assume default built-in water cost correlation with" +
                                      " adjustment factor = 1.")
                                model.logger.warning("No valid total water cost or adjustment factor provided." +
                                                     " GEOPHIRES will assume default built-in water cost correlation with" +
                                                     " adjustment factor = 1.")
                            elif self.oamwaterfixed.Provided and not self.oamwaterfixed.Valid:
                                print("Warning: Provided total water cost outside of range 0-100. GEOPHIRES" +
                                      " will assume default built-in water cost correlation with adjustment factor = 1.")
                                model.logger.warning("Provided total water cost outside of range 0-100. GEOPHIRES" +
                                                     " will assume default built-in water cost correlation with adjustment factor = 1.")
                                ParameterToModify.value = 1.0
                            elif not self.oamwaterfixed.Provided and ParameterToModify.Provided and not ParameterToModify.Valid:
                                print("Warning: Provided water cost adjustment factor outside of range 0-10." +
                                      " GEOPHIRES will assume default water cost correlation with adjustment factor = 1.")
                                model.logger.warning("Provided water cost adjustment factor outside of range 0-10." +
                                                     " GEOPHIRES will assume default water cost correlation with adjustment factor = 1.")
                                ParameterToModify.value = 1.0
                    elif ParameterToModify.Name == "Surface Plant O&M Cost Adjustment Factor":
                        if self.oamtotalfixed.Valid:
                            if self.oamplantfixed.Provided:
                                print("Warning: Provided total surface plant O&M cost not considered because" +
                                      " valid total annual O&M cost provided.")
                                model.logger.warning("Provided total surface plant O&M cost not considered because" +
                                                     " valid total annual O&M cost provided.")
                            if ParameterToModify.Provided:
                                print("Warning: Provided surface plant O&M cost adjustment factor not considered" +
                                      " because valid total annual O&M cost provided.")
                                model.logger.warning(
                                    "Provided surface plant O&M cost adjustment factor not considered" +
                                    " because valid total annual O&M cost provided.")
                        else:
                            if self.oamplantfixed.Valid and ParameterToModify.Valid:
                                print("Warning: Provided surface plant O&M cost adjustment factor not considered" +
                                      " because valid total surface plant O&M cost provided.")
                                model.logger.warning(
                                    "Provided surface plant O&M cost adjustment factor not considered" +
                                    " because valid total surface plant O&M cost provided.")
                            elif not self.oamplantfixed.Provided and not ParameterToModify.Provided:
                                ParameterToModify.value = 1.0
                                print("Warning: No valid surface plant O&M cost or adjustment factor provided." +
                                      " GEOPHIRES will assume default built-in surface plant O&M cost correlation with" +
                                      " adjustment factor = 1.")
                                model.logger.warning("No valid surface plant O&M cost or adjustment factor provided." +
                                                     " GEOPHIRES will assume default built-in surface plant O&M cost correlation with" +
                                                     " adjustment factor = 1.")
                            elif self.oamplantfixed.Provided and not self.oamplantfixed.Valid:
                                print("Warning: Provided surface plant O&M cost outside of range 0-100." +
                                      " GEOPHIRES will assume default built-in surface plant O&M cost correlation with" +
                                      " adjustment factor = 1.")
                                model.logger.warning("Provided surface plant O&M cost outside of range 0-100." +
                                                     " GEOPHIRES will assume default built-in surface plant O&M cost correlation with" +
                                                     " adjustment factor = 1.")
                                ParameterToModify.value = 1.0
                            elif not self.oamplantfixed.Provided and ParameterToModify.Provided and not ParameterToModify.Valid:
                                print("Warning: Provided surface plant O&M cost adjustment factor outside of" +
                                      " range 0-10. GEOPHIRES will assume default surface plant O&M cost correlation with" +
                                      " adjustment factor = 1.")
                                model.logger.warning("Provided surface plant O&M cost adjustment factor outside of" +
                                                     " range 0-10. GEOPHIRES will assume default surface plant O&M cost correlation with" +
                                                     " adjustment factor = 1.")
                                ParameterToModify.value = 1.0
        else:
            model.logger.info("No parameters read because no content provided")

        # we can determine on-the-fly if Addons, CCUS, or S-DAC-GT are being used in the user input file
        for key in model.InputParameters.keys():
            if key.startswith("AddOn"):
                self.DoAddOnCalculations.value = True
                break
        for key in model.InputParameters.keys():
            if key.startswith("S-DAC-GT"):
                self.DoSDACGTCalculations.value = True
                break

        coerce_int_params_to_enum_values(self.ParameterDict)

        model.logger.info(f'complete {__class__!s}: {sys._getframe().f_code.co_name}')

    def Calculate(self, model: Model) -> None:
        """
        The Calculate function is where all the calculations are done.
        This function can be called multiple times, and will only recalculate what has changed each time it is called.
        This is where all the calculations are made using all the values that have been set.
        If you subclass this class, you can choose to run these calculations before (or after) your calculations,
        but that assumes you have set all the values that are required for these calculations
        If you choose to subclass this master class, you can also choose to override this method (or not),
        and if you do, do it before or after you call you own version of this method.  If you do,
        you can also choose to call this method from you class, which can effectively run the calculations
        of the superclass, making all thr values available to your methods. but you had
        better have set all the parameters!
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing, but it does make calculations and set values in the model
        """
        model.logger.info(f'Init {__class__!s}: {sys._getframe().f_code.co_name}')

        # capital costs
        # well costs (using GeoVision drilling correlations). These are calculated whether totalcapcostvalid = 1
        # start with the cost of one well
        # C1well is well drilling and completion cost in M$/well
        if self.per_production_well_cost.Valid:
            self.cost_one_production_well.value = self.per_production_well_cost.value
            if not self.per_injection_well_cost.Provided:
                self.cost_one_injection_well.value = self.per_production_well_cost.value
            else:
                self.cost_one_injection_well.value = self.per_injection_well_cost.value
            self.Cwell.value = ((self.cost_one_production_well.value * model.wellbores.nprod.value) +
                                (self.cost_one_injection_well.value * model.wellbores.ninj.value))
        else:
            if hasattr(model.wellbores, 'numnonverticalsections') and model.wellbores.numnonverticalsections.Provided:
                self.cost_nonvertical_section.value = 0.0
                if not model.wellbores.IsAGS.value:
                    input_vert_depth_km = model.reserv.depth.quantity().to('km').magnitude
                    output_vert_depth_km = 0.0
                else:
                    input_vert_depth_km = model.reserv.InputDepth.quantity().to('km').magnitude
                    output_vert_depth_km = model.reserv.OutputDepth.quantity().to('km').magnitude
                model.wellbores.injection_reservoir_depth.value = input_vert_depth_km

                tot_m, tot_vert_m, tot_horiz_m = calculate_total_drilling_lengths_m(model.wellbores.Configuration.value,
                                                                      model.wellbores.numnonverticalsections.value,
                                                                      model.wellbores.Nonvertical_length.value / 1000.0,
                                                                      input_vert_depth_km,
                                                                      output_vert_depth_km,
                                                                      model.wellbores.nprod.value,
                                                                      model.wellbores.ninj.value)

            else:
                tot_m = tot_vert_m = model.reserv.depth.quantity().to('km').magnitude
                tot_horiz_m = 0.0
                if not model.wellbores.injection_reservoir_depth.Provided:
                    model.wellbores.injection_reservoir_depth.value = model.reserv.depth.quantity().to('km').magnitude
                else:
                    model.wellbores.injection_reservoir_depth.value = model.wellbores.injection_reservoir_depth.quantity().to('km').magnitude

            self.cost_one_production_well.value = calculate_cost_of_one_vertical_well(model, model.reserv.depth.quantity().to('m').magnitude,
                                                                                      self.wellcorrelation.value,
                                                                                      self.Vertical_drilling_cost_per_m.value,
                                                                                      self.per_production_well_cost.Name,
                                                                                      self.production_well_cost_adjustment_factor.value)
            if model.wellbores.ninj.value == 0:
                self.cost_one_injection_well.value = -1.0
            else:
                self.cost_one_injection_well.value = calculate_cost_of_one_vertical_well(model,
                                                                                         model.wellbores.injection_reservoir_depth.value * 1000.0,
                                                                                         self.wellcorrelation.value,
                                                                                         self.Vertical_drilling_cost_per_m.value,
                                                                                         self.per_injection_well_cost.Name,
                                                                                         self.injection_well_cost_adjustment_factor.value)

            if hasattr(model.wellbores, 'numnonverticalsections') and model.wellbores.numnonverticalsections.Provided:
                self.cost_nonvertical_section.value = calculate_cost_of_non_vertical_section(model, tot_horiz_m,
                                            self.wellcorrelation.value,
                                            self.Nonvertical_drilling_cost_per_m.value,
                                            model.wellbores.numnonverticalsections.value,
                                            self.per_injection_well_cost.Name,
                                            model.wellbores.NonverticalsCased.value,
                                            self.production_well_cost_adjustment_factor.value)
            else:
                self.cost_nonvertical_section.value = 0.0
            # cost of the well field
            # 1.05 for 5% indirect costs
            self.Cwell.value = 1.05 * ((self.cost_one_production_well.value * model.wellbores.nprod.value) +
                                          (self.cost_one_injection_well.value * model.wellbores.ninj.value) +
                                          self.cost_nonvertical_section.value)

        # reservoir stimulation costs (M$/injection well). These are calculated whether totalcapcost.Valid = 1
        if self.ccstimfixed.Valid:
            self.Cstim.value = self.ccstimfixed.value
        else:
            self.Cstim.value = 1.05 * 1.15 * self.ccstimadjfactor.value * model.wellbores.ninj.value * 1.25  # 1.15 for 15% contingency and 1.05 for 5% indirect costs

        # field gathering system costs (M$)
        if self.ccgathfixed.Valid:
            self.Cgath.value = self.ccgathfixed.value
        else:
            self.Cgath.value = self.ccgathadjfactor.value * 50 - 6 * np.max(
                model.surfaceplant.HeatExtracted.value) * 1000.  # (GEOPHIRES v1 correlation)
            if model.wellbores.impedancemodelused.value:
                pumphp = np.max(model.wellbores.PumpingPower.value) * 1341
                numberofpumps = np.ceil(pumphp / 2000)  # pump can be maximum 2,000 hp
                if numberofpumps == 0:
                    self.Cpumps = 0.0
                else:
                    pumphpcorrected = pumphp / numberofpumps
                    self.Cpumps = numberofpumps * 1.5 * (
                            (1750 * pumphpcorrected ** 0.7) * 3 * pumphpcorrected ** (-0.11))
            else:
                if model.wellbores.productionwellpumping.value:
                    prodpumphp = np.max(model.wellbores.PumpingPowerProd.value) / model.wellbores.nprod.value * 1341
                    Cpumpsprod = model.wellbores.nprod.value * 1.5 * (1750 * prodpumphp ** 0.7 + 5750 *
                                                                      prodpumphp ** 0.2 + 10000 + np.max(
                            model.wellbores.pumpdepth.value) * 50 * 3.281)  # see page 46 in user's manual assuming rental of rig for 1 day.
                else:
                    Cpumpsprod = 0

                injpumphp = np.max(model.wellbores.PumpingPowerInj.value) * 1341
                numberofinjpumps = np.ceil(injpumphp / 2000)  # pump can be maximum 2,000 hp
                if numberofinjpumps == 0:
                    Cpumpsinj = 0
                else:
                    injpumphpcorrected = injpumphp / numberofinjpumps
                    Cpumpsinj = numberofinjpumps * 1.5 * (
                            1750 * injpumphpcorrected ** 0.7) * 3 * injpumphpcorrected ** (-0.11)
                self.Cpumps = Cpumpsinj + Cpumpsprod

        # Based on GETEM 2016 #1.15 for 15% contingency and 1.12 for 12% indirect costs
        self.Cgath.value = 1.15 * self.ccgathadjfactor.value * 1.12 * (
                (model.wellbores.nprod.value + model.wellbores.ninj.value) * 750 * 500. + self.Cpumps) / 1E6

        # plant costs
        if (model.surfaceplant.enduse_option.value == EndUseOptions.HEAT
            and model.surfaceplant.plant_type.value not in [PlantType.ABSORPTION_CHILLER, PlantType.HEAT_PUMP, PlantType.DISTRICT_HEATING]):  # direct-use
            if self.ccplantfixed.Valid:
                self.Cplant.value = self.ccplantfixed.value
            else:
                self.Cplant.value = 1.12 * 1.15 * self.ccplantadjfactor.value * 250E-6 * np.max(
                    model.surfaceplant.HeatExtracted.value) * 1000.  # 1.15 for 15% contingency and 1.12 for 12% indirect costs

        # absorption chiller
        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value == PlantType.ABSORPTION_CHILLER:  # absorption chiller
            if self.ccplantfixed.Valid:
                self.Cplant.value = self.ccplantfixed.value
            else:
                # this is for the direct-use part all the way up to the absorption chiller
                self.Cplant.value = 1.12 * 1.15 * self.ccplantadjfactor.value * 250E-6 * np.max(
                    model.surfaceplant.HeatExtracted.value) * 1000.  # 1.15 for 15% contingency and 1.12 for 12% indirect costs
                if self.chillercapex.value == -1:  # no value provided by user, use built-in correlation ($2500/ton)
                    self.chillercapex.value = 1.12 * 1.15 * np.max(
                        model.surfaceplant.cooling_produced.value) * 1000 / 3.517 * 2500 / 1e6  # $2,500/ton of cooling. 1.15 for 15% contingency and 1.12 for 12% indirect costs

                # now add chiller cost to surface plant cost
                self.Cplant.value += self.chillercapex.value

        # heat pump
        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value == PlantType.HEAT_PUMP:
            if self.ccplantfixed.Valid:
                self.Cplant.value = self.ccplantfixed.value
            else:
                # this is for the direct-use part all the way up to the heat pump
                self.Cplant.value = 1.12 * 1.15 * self.ccplantadjfactor.value * 250E-6 * np.max(
                    model.surfaceplant.HeatExtracted.value) * 1000.  # 1.15 for 15% contingency and 1.12 for 12% indirect costs
                if self.heatpumpcapex.value == -1:  # no value provided by user, use built-in correlation ($150/kWth)
                    self.heatpumpcapex.value = 1.12 * 1.15 * np.max(
                        model.surfaceplant.HeatProduced.value) * 1000 * 150 / 1e6  # $150/kW. 1.15 for 15% contingency and 1.12 for 12% indirect costs

                # now add heat pump cost to surface plant cost
                self.Cplant.value += self.heatpumpcapex.value

        # district heating
        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
            if self.ccplantfixed.Valid:
                self.Cplant.value = self.ccplantfixed.value
            else:
                self.Cplant.value = 1.12 * 1.15 * self.ccplantadjfactor.value * 250E-6 * np.max(
                    model.surfaceplant.HeatExtracted.value) * 1000.  # 1.15 for 15% contingency and 1.12 for 12% indirect costs
                self.peakingboilercost.value = 65 * model.surfaceplant.max_peaking_boiler_demand.value / 1000  # add 65$/KW for peaking boiler
                self.Cplant.value += self.peakingboilercost.value  # add peaking boiler cost to surface plant cost


        else:  # all other options have power plant
            if model.surfaceplant.plant_type.value == PlantType.SUB_CRITICAL_ORC:
                MaxProducedTemperature = np.max(model.surfaceplant.TenteringPP.value)
                if MaxProducedTemperature < 150.:
                    C3 = -1.458333E-3
                    C2 = 7.6875E-1
                    C1 = -1.347917E2
                    C0 = 1.0075E4
                    CCAPP1 = C3 * MaxProducedTemperature ** 3 + C2 * MaxProducedTemperature ** 2 + C1 * MaxProducedTemperature + C0
                else:
                    CCAPP1 = 2231 - 2 * (MaxProducedTemperature - 150.)
                x = np.max(model.surfaceplant.ElectricityProduced.value)
                y = np.max(model.surfaceplant.ElectricityProduced.value)
                if y == 0.0:
                    y = 15.0
                z = math.pow(y / 15., -0.06)
                self.Cplantcorrelation = CCAPP1 * z * x * 1000. / 1E6

            elif model.surfaceplant.plant_type.value == PlantType.SUPER_CRITICAL_ORC:
                MaxProducedTemperature = np.max(model.surfaceplant.TenteringPP.value)
                if MaxProducedTemperature < 150.:
                    C3 = -1.458333E-3
                    C2 = 7.6875E-1
                    C1 = -1.347917E2
                    C0 = 1.0075E4
                    CCAPP1 = C3 * MaxProducedTemperature ** 3 + C2 * MaxProducedTemperature ** 2 + C1 * MaxProducedTemperature + C0
                else:
                    CCAPP1 = 2231 - 2 * (MaxProducedTemperature - 150.)
                # factor 1.1 to make supercritical 10% more expansive than subcritical
                self.Cplantcorrelation = 1.1 * CCAPP1 * math.pow(
                    np.max(model.surfaceplant.ElectricityProduced.value) / 15., -0.06) * np.max(
                    model.surfaceplant.ElectricityProduced.value) * 1000. / 1E6

            elif model.surfaceplant.plant_type.value == PlantType.SINGLE_FLASH:
                if np.max(model.surfaceplant.ElectricityProduced.value) < 10.:
                    C2 = 4.8472E-2
                    C1 = -35.2186
                    C0 = 8.4474E3
                    D2 = 4.0604E-2
                    D1 = -29.3817
                    D0 = 6.9911E3
                    PLL = 5.
                    PRL = 10.
                elif np.max(model.surfaceplant.ElectricityProduced.value) < 25.:
                    C2 = 4.0604E-2
                    C1 = -29.3817
                    C0 = 6.9911E3
                    D2 = 3.2773E-2
                    D1 = -23.5519
                    D0 = 5.5263E3
                    PLL = 10.
                    PRL = 25.
                elif np.max(model.surfaceplant.ElectricityProduced.value) < 50.:
                    C2 = 3.2773E-2
                    C1 = -23.5519
                    C0 = 5.5263E3
                    D2 = 3.4716E-2
                    D1 = -23.8139
                    D0 = 5.1787E3
                    PLL = 25.
                    PRL = 50.
                elif np.max(model.surfaceplant.ElectricityProduced.value) < 75.:
                    C2 = 3.4716E-2
                    C1 = -23.8139
                    C0 = 5.1787E3
                    D2 = 3.5271E-2
                    D1 = -24.3962
                    D0 = 5.1972E3
                    PLL = 50.
                    PRL = 75.
                else:
                    C2 = 3.5271E-2
                    C1 = -24.3962
                    C0 = 5.1972E3
                    D2 = 3.3908E-2
                    D1 = -23.4890
                    D0 = 5.0238E3
                    PLL = 75.
                    PRL = 100.
                maxProdTemp = np.max(model.surfaceplant.TenteringPP.value)
                CCAPPLL = C2 * maxProdTemp ** 2 + C1 * maxProdTemp + C0
                CCAPPRL = D2 * maxProdTemp ** 2 + D1 * maxProdTemp + D0
                b = math.log(CCAPPRL / CCAPPLL) / math.log(PRL / PLL)
                a = CCAPPRL / PRL ** b
                # factor 0.75 to make double flash 25% more expansive than single flash
                self.Cplantcorrelation = (0.8 * a * math.pow(np.max(model.surfaceplant.ElectricityProduced.value), b) *
                                          np.max(model.surfaceplant.ElectricityProduced.value) * 1000. / 1E6)

            elif model.surfaceplant.plant_type.value == PlantType.DOUBLE_FLASH:
                if np.max(model.surfaceplant.ElectricityProduced.value) < 10.:
                    C2 = 4.8472E-2
                    C1 = -35.2186
                    C0 = 8.4474E3
                    D2 = 4.0604E-2
                    D1 = -29.3817
                    D0 = 6.9911E3
                    PLL = 5.
                    PRL = 10.
                elif np.max(model.surfaceplant.ElectricityProduced.value) < 25.:
                    C2 = 4.0604E-2
                    C1 = -29.3817
                    C0 = 6.9911E3
                    D2 = 3.2773E-2
                    D1 = -23.5519
                    D0 = 5.5263E3
                    PLL = 10.
                    PRL = 25.
                elif np.max(model.surfaceplant.ElectricityProduced.value) < 50.:
                    C2 = 3.2773E-2
                    C1 = -23.5519
                    C0 = 5.5263E3
                    D2 = 3.4716E-2
                    D1 = -23.8139
                    D0 = 5.1787E3
                    PLL = 25.
                    PRL = 50.
                elif np.max(model.surfaceplant.ElectricityProduced.value) < 75.:
                    C2 = 3.4716E-2
                    C1 = -23.8139
                    C0 = 5.1787E3
                    D2 = 3.5271E-2
                    D1 = -24.3962
                    D0 = 5.1972E3
                    PLL = 50.
                    PRL = 75.
                else:
                    C2 = 3.5271E-2
                    C1 = -24.3962
                    C0 = 5.1972E3
                    D2 = 3.3908E-2
                    D1 = -23.4890
                    D0 = 5.0238E3
                    PLL = 75.
                    PRL = 100.
                maxProdTemp = np.max(model.surfaceplant.TenteringPP.value)
                CCAPPLL = C2 * maxProdTemp ** 2 + C1 * maxProdTemp + C0
                CCAPPRL = D2 * maxProdTemp ** 2 + D1 * maxProdTemp + D0
                b = math.log(CCAPPRL / CCAPPLL) / math.log(PRL / PLL)
                a = CCAPPRL / PRL ** b
                self.Cplantcorrelation = (a * math.pow(np.max(model.surfaceplant.ElectricityProduced.value), b) *
                                          np.max(model.surfaceplant.ElectricityProduced.value) * 1000. / 1E6)

            if self.ccplantfixed.Valid:
                self.Cplant.value = self.ccplantfixed.value
                self.CAPEX_cost_electricity_plant = self.Cplant.value * self.CAPEX_heat_electricity_plant_ratio.value
                self.CAPEX_cost_heat_plant = self.Cplant.value * (1.0 - self.CAPEX_heat_electricity_plant_ratio.value)
            else:
                # 1.02 to convert cost from 2012 to 2016 #factor 1.15 for 15% contingency and 1.12 for 12% indirect costs. factor 1.10 to convert from 2016 to 2022
                self.Cplant.value = 1.12 * 1.15 * self.ccplantadjfactor.value * self.Cplantcorrelation * 1.02 * 1.10
                self.CAPEX_cost_electricity_plant = self.Cplant.value

        # add direct-use plant cost of co-gen system to Cplant (only of no total Cplant was provided)
        if not self.ccplantfixed.Valid:  # 1.15 below for contingency and 1.12 for indirect costs
            if model.surfaceplant.enduse_option.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY,
                                                          EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT]:  # enduse_option = 3: cogen topping cycle
                self.CAPEX_cost_heat_plant = 1.12 * 1.15 * self.ccplantadjfactor.value * 250E-6 * np.max(
                    model.surfaceplant.HeatProduced.value / model.surfaceplant.enduse_efficiency_factor.value) * 1000.
            elif model.surfaceplant.enduse_option.value in [EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                            EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY]:  # enduse_option = 4: cogen bottoming cycle
                self.CAPEX_cost_heat_plant = 1.12 * 1.15 * self.ccplantadjfactor.value * 250E-6 * np.max(
                    model.surfaceplant.HeatProduced.value / model.surfaceplant.enduse_efficiency_factor.value) * 1000.
            elif model.surfaceplant.enduse_option.value in [EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY,
                                                            EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT]:  # cogen parallel cycle
                self.CAPEX_cost_heat_plant = 1.12 * 1.15 * self.ccplantadjfactor.value * 250E-6 * np.max(
                    model.surfaceplant.HeatProduced.value / model.surfaceplant.enduse_efficiency_factor.value) * 1000.

            self.Cplant.value = self.Cplant.value + self.CAPEX_cost_heat_plant
            if not self.CAPEX_heat_electricity_plant_ratio.Provided:
                self.CAPEX_heat_electricity_plant_ratio.value = self.CAPEX_cost_electricity_plant/self.Cplant.value

        if not self.totalcapcost.Valid:
            # exploration costs (same as in Geophires v1.2) (M$)
            if self.ccexplfixed.Valid:
                self.Cexpl.value = self.ccexplfixed.value
            else:
                self.Cexpl.value = 1.15 * self.ccexpladjfactor.value * 1.12 * (
                    1. + self.cost_one_production_well.value * 0.6)  # 1.15 for 15% contingency and 1.12 for 12% indirect costs

            # Surface Piping Length Costs (M$) #assumed $750k/km
            self.Cpiping.value = 750 / 1000 * model.surfaceplant.piping_length.value

            # district heating network costs
            if model.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:  # district heat
                if self.dhtotaldistrictnetworkcost.Provided:
                    self.dhdistrictcost.value = self.dhtotaldistrictnetworkcost.value
                elif self.dhpipinglength.Provided:
                    self.dhdistrictcost.value = self.dhpipinglength.value * self.dhpipingcostrate.value / 1000  # M$
                elif self.dhroadlength.Provided:  # check if road length is provided to calculate cost
                    self.dhdistrictcost.value = self.dhroadlength.value * 0.75 * self.dhpipingcostrate.value / 1000  # M$ (assuming 75% of road length is used for district network piping)
                else:  # calculate district network cost based on population density
                    if self.dhlandarea.Provided == False:
                        model.logger.warning("District heating network cost calculated based on default district area")
                    if self.dhpopulation.Provided:
                        self.populationdensity.value = self.dhpopulation.value / self.dhlandarea.value
                    elif model.surfaceplant.dh_number_of_housing_units.Provided:
                        self.populationdensity.value = model.surfaceplant.dh_number_of_housing_units.value * 2.6 / self.dhlandarea.value  # estimate population based on 2.6 number of people per household
                    else:
                        model.logger.warning(
                            "District heating network cost calculated based on default number of people in district")
                        self.populationdensity.value = self.dhpopulation.value / self.dhlandarea.value

                    if self.populationdensity.value > 1000:
                        self.dhpipinglength.value = 7.5 * self.dhlandarea.value  # using constant 7.5km of pipe per km^2 when population density is >1500
                    else:
                        self.dhpipinglength.value = max(
                            self.populationdensity.value / 1000 * 7.5 * self.dhlandarea.value,
                            self.dhlandarea.value)  # scale the piping length based on population density, but with a minimum of 1 km of piping per km^2 of area
                    self.dhdistrictcost.value = self.dhpipingcostrate.value * self.dhpipinglength.value / 1000

            else:
                self.dhdistrictcost.value = 0

            self.CCap.value = self.Cexpl.value + self.Cwell.value + self.Cstim.value + self.Cgath.value + self.Cplant.value + self.Cpiping.value + self.dhdistrictcost.value
        else:
            self.CCap.value = self.totalcapcost.value

        # update the capitol costs, assuming the entire ITC is used to reduce the capitol costs
        if self.RITC.Provided:
            self.RITCValue.value = self.RITC.value * self.CCap.value
            self.CCap.value = self.CCap.value - self.RITCValue.value

        # Add in the FlatLicenseEtc, OtherIncentives, & TotalGrant
        self.CCap.value = self.CCap.value + self.FlatLicenseEtc.value - self.OtherIncentives.value - self.TotalGrant.value

        # O&M costs
        # calculate first O&M costs independent of whether oamtotalfixed is provided or not
        # additional electricity cost for heat pump as end-use
        if model.surfaceplant.plant_type.value == PlantType.HEAT_PUMP:  # heat pump:
            self.averageannualheatpumpelectricitycost.value = np.average(
                model.surfaceplant.heat_pump_electricity_kwh_used.value) * model.surfaceplant.electricity_cost_to_buy.value / 1E6  # M$/year

        # district heating peaking fuel annual cost
        if model.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:  # district heating
            self.annualngcost.value = model.surfaceplant.annual_ng_demand.value * self.ngprice.value / 1000 / self.peakingboilerefficiency.value  # array with annual O&M cost for peaking fuel
            self.averageannualngcost.value = np.average(self.annualngcost.value)

        # calculate average annual pumping costs in case no electricity is provided
        if model.surfaceplant.plant_type.value in [PlantType.INDUSTRIAL, PlantType.ABSORPTION_CHILLER, PlantType.HEAT_PUMP, PlantType.DISTRICT_HEATING]:
            self.averageannualpumpingcosts.value = np.average(model.surfaceplant.PumpingkWh.value) * model.surfaceplant.electricity_cost_to_buy.value / 1E6  # M$/year

        if not self.oamtotalfixed.Valid:
            # labor cost
            if model.surfaceplant.enduse_option.value == EndUseOptions.ELECTRICITY:  # electricity
                if np.max(model.surfaceplant.ElectricityProduced.value) < 2.5:
                    self.Claborcorrelation = 236. / 1E3  # M$/year
                else:
                    self.Claborcorrelation = (589. * math.log(
                        np.max(model.surfaceplant.ElectricityProduced.value)) - 304.) / 1E3  # M$/year
            else:
                if np.max(model.surfaceplant.HeatExtracted.value) < 2.5 * 5.:
                    self.Claborcorrelation = 236. / 1E3  # M$/year
                else:
                    self.Claborcorrelation = (589. * math.log(
                        np.max(model.surfaceplant.HeatExtracted.value) / 5.) - 304.) / 1E3  # M$/year
                # * 1.1 to convert from 2012 to 2016$ with BLS employment cost index (for utilities in March)
            self.Claborcorrelation = self.Claborcorrelation * 1.1

            # plant O&M cost
            if self.oamplantfixed.Valid:
                self.Coamplant.value = self.oamplantfixed.value
            else:
                self.Coamplant.value = self.oamplantadjfactor.value * (
                        1.5 / 100. * self.Cplant.value + 0.75 * self.Claborcorrelation)

            # wellfield O&M cost
            if self.oamwellfixed.Valid:
                self.Coamwell.value = self.oamwellfixed.value
            else:
                self.Coamwell.value = self.oamwelladjfactor.value * (
                        1. / 100. * (self.Cwell.value + self.Cgath.value) + 0.25 * self.Claborcorrelation)

            # water O&M cost
            if self.oamwaterfixed.Valid:
                self.Coamwater.value = self.oamwaterfixed.value
            else:
                # here is assumed 1 l per kg maybe correct with real temp. (M$/year) 925$/ML = 3.5$/1,000 gallon
                self.Coamwater.value = self.oamwateradjfactor.value * (model.wellbores.nprod.value *
                                                                       model.wellbores.prodwellflowrate.value *
                                                                       model.reserv.waterloss.value * model.surfaceplant.utilization_factor.value *
                                                                       365. * 24. * 3600. / 1E6 * 925. / 1E6)

            # additional O&M cost for absorption chiller if used
            if model.surfaceplant.plant_type.value == PlantType.ABSORPTION_CHILLER:  # absorption chiller:
                if self.chilleropex.value == -1:
                    self.chilleropex.value = self.chillercapex.value * 2 / 100  # assumed annual O&M for chiller is 2% of investment cost

                # correct plant O&M cost as otherwise chiller opex would be counted double (subtract chiller capex from plant cost when calculating Coandmplant)
                if self.oamplantfixed.Valid == False:
                    self.Coamplant.value = self.oamplantadjfactor.value * (
                        1.5 / 100. * (self.Cplant.value - self.chillercapex.value) + 0.75 * self.Claborcorrelation)

            else:
                self.chilleropex.value = 0

            # district heating O&M cost
            if model.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:  # district heating
                self.annualngcost.value = model.surfaceplant.annual_ng_demand.value * self.ngprice.value / 1000  # array with annual O&M cost for peaking fuel

                if self.dhoandmcost.Provided:
                    self.dhdistrictoandmcost.value = self.dhoandmcost.value  # M$/yr
                else:
                    self.dhdistrictoandmcost.value = 0.01 * self.dhdistrictcost.value + 0.02 * sum(
                        model.surfaceplant.daily_heating_demand.value) * model.surfaceplant.electricity_cost_to_buy.value / 1000  # [M$/year] we assume annual district OPEX equals 1% of district CAPEX and 2% of total heat demand for pumping costs

            else:
                self.dhdistrictoandmcost.value = 0

            self.Coam.value = self.Coamwell.value + self.Coamplant.value + self.Coamwater.value + self.chilleropex.value + self.dhdistrictoandmcost.value  # total O&M cost (M$/year)

        else:
            self.Coam.value = self.oamtotalfixed.value  # total O&M cost (M$/year)

        if model.wellbores.redrill.value > 0:
            # account for well redrilling
            self.Coam.value = self.Coam.value + \
                              (self.Cwell.value + self.Cstim.value) * model.wellbores.redrill.value / model.surfaceplant.plant_lifetime.value

        # Add in the AnnualLicenseEtc and TaxRelief
        self.Coam.value = self.Coam.value + self.AnnualLicenseEtc.value - self.TaxRelief.value

        # partition the OPEX for CHP plants based on the CAPEX ratio
        self.OPEX_cost_electricity_plant = self.Coam.value * self.CAPEX_heat_electricity_plant_ratio.value
        self.OPEX_cost_heat_plant = self.Coam.value * (1.0 - self.CAPEX_heat_electricity_plant_ratio.value)

        # The Reservoir depth measure was arbitrarily changed to meters despite being defined in the docs as kilometers.
        # For display consistency sake, we need to convert it back
        if model.reserv.depth.value > 500:
            model.reserv.depth.value = model.reserv.depth.value / 1000.0
            model.reserv.depth.CurrentUnits = LengthUnit.KILOMETERS

        # build the PTC price models
        self.PTCElecPrice = [0.0] * model.surfaceplant.plant_lifetime.value
        self.PTCHeatPrice = [0.0] * model.surfaceplant.plant_lifetime.value
        self.PTCCoolingPrice = [0.0] * model.surfaceplant.plant_lifetime.value
        self.PTCCarbonPrice = [0.0] * model.surfaceplant.plant_lifetime.value
        if self.PTCElec.Provided:
            self.PTCElecPrice = BuildPTCModel(model.surfaceplant.plant_lifetime.value,
                                              self.PTCDuration.value, self.PTCElec.value, self.PTCInflationAdjusted.value,
                                              self.RINFL.value)
        if self.PTCHeat.Provided:
            self.PTCHeatPrice = BuildPTCModel(model.surfaceplant.plant_lifetime.value,
                                              self.PTCDuration.value, self.PTCHeat.value, self.PTCInflationAdjusted.value,
                                              self.RINFL.value)
        if self.PTCCooling.Provided:
            self.PTCCoolingPrice = BuildPTCModel(model.surfaceplant.plant_lifetime.value,
                                              self.PTCDuration.value,self.PTCCooling.value, self.PTCInflationAdjusted.value,
                                              self.RINFL.value)

        # build the price models
        self.ElecPrice.value = BuildPricingModel(model.surfaceplant.plant_lifetime.value,
                                                 self.ElecStartPrice.value, self.ElecEndPrice.value,
                                                 self.ElecEscalationStart.value, self.ElecEscalationRate.value,
                                                 self.PTCElecPrice)
        self.HeatPrice.value = BuildPricingModel(model.surfaceplant.plant_lifetime.value,
                                                 self.HeatStartPrice.value, self.HeatEndPrice.value,
                                                 self.HeatEscalationStart.value, self.HeatEscalationRate.value,
                                                 self.PTCHeatPrice)
        self.CoolingPrice.value = BuildPricingModel(model.surfaceplant.plant_lifetime.value,
                                                 self.CoolingStartPrice.value, self.CoolingEndPrice.value,
                                                 self.CoolingEscalationStart.value, self.CoolingEscalationRate.value,
                                                 self.PTCCoolingPrice)
        self.CarbonPrice.value = BuildPricingModel(model.surfaceplant.plant_lifetime.value,
                                                 self.CarbonStartPrice.value, self.CarbonEndPrice.value,
                                                 self.CarbonEscalationStart.value, self.CarbonEscalationRate.value,
                                                 self.PTCCarbonPrice)

        # do the additional economic calculations first, if needed, so the summaries below work.
        if self.DoAddOnCalculations.value:
            model.addeconomics.Calculate(model)
        if self.DoSDACGTCalculations.value:
            model.sdacgteconomics.Calculate(model)

        # Calculate cashflow and cumulative cash flow
        total_duration = model.surfaceplant.plant_lifetime.value + model.surfaceplant.construction_years.value
        self.ElecRevenue.value = [0.0] * total_duration
        self.ElecCummRevenue.value = [0.0] * total_duration
        self.HeatRevenue.value = [0.0] * total_duration
        self.HeatCummRevenue.value = [0.0] * total_duration
        self.CoolingRevenue.value = [0.0] * total_duration
        self.CoolingCummRevenue.value = [0.0] * total_duration
        self.CarbonRevenue.value = [0.0] * total_duration
        self.CarbonCummCashFlow.value = [0.0] * total_duration
        self.TotalRevenue.value = [0.0] * total_duration
        self.TotalCummRevenue.value = [0.0] * total_duration
        self.CarbonThatWouldHaveBeenProducedTotal.value = 0.0

        # Based on the style of the project, calculate the revenue & cumulative revenue
        if model.surfaceplant.enduse_option.value == EndUseOptions.ELECTRICITY:
            self.ElecRevenue.value, self.ElecCummRevenue.value = CalculateRevenue(
                model.surfaceplant.plant_lifetime.value, model.surfaceplant.construction_years.value,
                model.surfaceplant.NetkWhProduced.value, self.ElecPrice.value)
            self.TotalRevenue.value = self.ElecRevenue.value
            #self.TotalCummRevenue.value = self.ElecCummRevenue.value
        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value not in [PlantType.ABSORPTION_CHILLER]:
            self.HeatRevenue.value, self.HeatCummRevenue.value = CalculateRevenue(
                model.surfaceplant.plant_lifetime.value, model.surfaceplant.construction_years.value,
                model.surfaceplant.HeatkWhProduced.value, self.HeatPrice.value)
            self.TotalRevenue.value = self.HeatRevenue.value
            #self.TotalCummRevenue.value = self.HeatCummRevenue.value
        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value in [PlantType.ABSORPTION_CHILLER]:
            self.CoolingRevenue.value, self.CoolingCummRevenue.value = CalculateRevenue(
                model.surfaceplant.plant_lifetime.value, model.surfaceplant.construction_years.value,
                model.surfaceplant.cooling_kWh_Produced.value, self.CoolingPrice.value)
            self.TotalRevenue.value = self.CoolingRevenue.value
            #self.TotalCummRevenue.value = self.CoolingCummRevenue.value
        elif model.surfaceplant.enduse_option.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT,
                                                        EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY,
                                                        EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY,
                                                        EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                        EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT,
                                                        EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]:  # co-gen
            # else:
            self.ElecRevenue.value, self.ElecCummRevenue.value = CalculateRevenue(
                model.surfaceplant.plant_lifetime.value, model.surfaceplant.construction_years.value,
                model.surfaceplant.NetkWhProduced.value, self.ElecPrice.value)
            self.HeatRevenue.value, self.HeatCummRevenue.value = CalculateRevenue(
                model.surfaceplant.plant_lifetime.value, model.surfaceplant.construction_years.value,
                model.surfaceplant.HeatkWhProduced.value, self.HeatPrice.value)

            for i in range(0, model.surfaceplant.plant_lifetime.value + model.surfaceplant.construction_years.value, 1):
                self.TotalRevenue.value[i] = self.ElecRevenue.value[i] + self.HeatRevenue.value[i]
                #if i > 0:
                #    self.TotalCummRevenue.value[i] = self.TotalCummRevenue.value[i - 1] + self.TotalRevenue.value[i]

        if self.DoCarbonCalculations.value:
            self.CarbonRevenue.value, self.CarbonCummCashFlow.value, self.CarbonThatWouldHaveBeenProducedAnnually.value, \
             self.CarbonThatWouldHaveBeenProducedTotal.value = CalculateCarbonRevenue(model,
                  model.surfaceplant.plant_lifetime.value, model.surfaceplant.construction_years.value,
                  self.CarbonPrice.value, self.GridCO2Intensity.value, self.NaturalGasCO2Intensity.value,
                  model.surfaceplant.NetkWhProduced.value, model.surfaceplant.HeatkWhProduced.value)
            for i in range(model.surfaceplant.construction_years.value, model.surfaceplant.plant_lifetime.value + model.surfaceplant.construction_years.value, 1):
                self.TotalRevenue.value[i] = self.TotalRevenue.value[i] + self.CarbonRevenue.value[i]
                #self.TotalCummRevenue.value[i] = self.TotalCummRevenue.value[i] + self.CarbonCummCashFlow.value[i]

        # for the sake of display, insert zeros at the beginning of the pricing arrays
        for i in range(0, model.surfaceplant.construction_years.value, 1):
            self.ElecPrice.value.insert(0, 0.0)
            self.HeatPrice.value.insert(0, 0.0)
            self.CoolingPrice.value.insert(0, 0.0)
            self.CarbonPrice.value.insert(0, 0.0)

        # Insert the cost of construction into the front of the array that will be used to calculate NPV
        # the convention is that the upfront CAPEX is negative
        # This is the same for all projects
        ProjectCAPEXPerConstructionYear = self.CCap.value / model.surfaceplant.construction_years.value
        for i in range(0, model.surfaceplant.construction_years.value, 1):
            self.TotalRevenue.value[i] = -1.0 * ProjectCAPEXPerConstructionYear
            self.TotalCummRevenue.value[i] = -1.0 * ProjectCAPEXPerConstructionYear
#        self.TotalRevenue.value, self.TotalCummRevenue.value = CalculateTotalRevenue(
#            model.surfaceplant.plant_lifetime.value, model.surfaceplant.construction_years.value, self.CCap.value,
#                self.Coam.value, self.TotalRevenue.value, self.TotalCummRevenue.value)

        # Do a one-time calculation that accounts for OPEX - no OPEX in the first year.
        for i in range(model.surfaceplant.construction_years.value,
                       model.surfaceplant.plant_lifetime.value + model.surfaceplant.construction_years.value, 1):
            self.TotalRevenue.value[i] = self.TotalRevenue.value[i] - self.Coam.value

        # Now do a one-time calculation that calculates the cumulative cash flow after everything else has been accounted for
        for i in range(1, model.surfaceplant.plant_lifetime.value + model.surfaceplant.construction_years.value, 1):
            self.TotalCummRevenue.value[i] = self.TotalCummRevenue.value[i-1] + self.TotalRevenue.value[i]

        # Calculate more financial values using numpy financials
        self.ProjectNPV.value, self.ProjectIRR.value, self.ProjectVIR.value, self.ProjectMOIC.value = \
            CalculateFinancialPerformance(model.surfaceplant.plant_lifetime.value, self.FixedInternalRate.value,
                                          self.TotalRevenue.value, self.TotalCummRevenue.value, self.CCap.value,
                                          self.Coam.value)

        # Calculate the project payback period
        self.ProjectPaybackPeriod.value = 0.0   # start by assuming the project never pays back
        for i in range(0, len(self.TotalCummRevenue.value), 1):
                # find out when the cumm cashflow goes from negative to positive
                if self.TotalCummRevenue.value[i] > 0 >= self.TotalCummRevenue.value[i - 1]:
                    # we just crossed the threshold into positive project cummcashflow, so we can calculate payback period
                    dFullDiff = self.TotalCummRevenue.value[i] + math.fabs(self.TotalCummRevenue.value[(i - 1)])
                    dPerc = math.fabs(self.TotalCummRevenue.value[(i - 1)]) / dFullDiff
                    self.ProjectPaybackPeriod.value = i + dPerc


        # Calculate LCOE/LCOH
        self.LCOE.value, self.LCOH.value, self.LCOC.value = CalculateLCOELCOHLCOC(self, model)

        # https://github.com/NREL/GEOPHIRES-X/issues/232
        self.jobs_created.value = round(
            np.average(model.surfaceplant.ElectricityProduced.quantity().to(
                'MW').magnitude * self.jobs_created_per_MW_electricity.value))

        model.logger.info(f'complete {__class__!s}: {sys._getframe().f_code.co_name}')

    def __str__(self):
        return "Economics"

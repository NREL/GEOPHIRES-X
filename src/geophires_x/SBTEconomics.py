import sys, math
import numpy as np
import geophires_x.Model as Model
from .Economics import Economics, calculate_cost_of_one_vertical_well, BuildPTCModel, CalculateRevenue, CalculateFinancialPerformance, CalculateLCOELCOHLCOC
from .EconomicsUtils import BuildPricingModel
from .OptionList import Configuration, WellDrillingCostCorrelation, PlantType
from geophires_x.Parameter import floatParameter
from geophires_x.Units import *
from geophires_x.OptionList import WorkingFluid, EndUseOptions, EconomicModel


def calculate_cost_of_lateral_section(model: Model, length_m: float, well_correlation: int,
                                      lateral_drilling_cost_per_m: float,
                                      num_lateral_sections: int,
                                      fixed_well_cost_name: str, NonverticalsCased: bool,
                                      well_cost_adjustment_factor: float) -> float:
    """
    calculate_cost_of_lateral_section calculates the cost of the lateral section of the well.
    Assume that the cost per meter for drilling of the lateral section is the same as the vertical section,
    except the casing cost is half, if it is uncased.
    :param model: The model object
    :type model: :class:`~geophires
    :param length_m: The depth of the well in meters
    :type length_m: float
    :param well_correlation: The well cost correlation
    :type well_correlation: int
    :param lateral_drilling_cost_per_m: The lateral drilling cost per meter in $/m
    :type lateral_drilling_cost_per_m: float
    :param num_lateral_sections: The number of lateral sections
    :type num_lateral_sections: int
    :param fixed_well_cost_name: The fixed well cost name
    :type fixed_well_cost_name: str
    :param NonverticalsCased: Are the laterals cased?
    :type NonverticalsCased: bool
    :param well_cost_adjustment_factor: The well cost adjustment factor
    :type well_cost_adjustment_factor: float
    :return: cost_of_one_well: The cost of the lateral section in MUSD
    :rtype: float
    """

    # if we are drilling a vertical well, the lateral cost is 0
    if model.wellbores.Configuration.value == Configuration.VERTICAL:
        return 0.0

    # Check if  well length is out of standard bounds for cost correlation
    length_per_section_m = length_m / num_lateral_sections
    correlations_min_valid_length_m = 500.
    correlations_max_valid_length_m = 8000.
    cost_of_lateral_section = 0.0
    cost_per_section = 0.0
    if length_per_section_m < correlations_min_valid_length_m and not well_correlation is WellDrillingCostCorrelation.SIMPLE:
        well_correlation = WellDrillingCostCorrelation.SIMPLE
        model.logger.warning(
            f'Invalid cost correlation specified ({well_correlation}) for per lateral section drilling length '
            f'<{correlations_min_valid_length_m}m ({length_per_section_m}m). '
            f'Falling back to simple user-specified cost '
            f'({lateral_drilling_cost_per_m} per meter)'
        )

    if length_per_section_m > correlations_max_valid_length_m and not well_correlation is WellDrillingCostCorrelation.SIMPLE:
        model.logger.warning(
            f'{well_correlation} may be invalid for per lateral section rilling length '
            f'>{correlations_max_valid_length_m}m ({length_per_section_m}m). '
            f'Consider using {WellDrillingCostCorrelation.SIMPLE} (per-meter cost) or '
            f'{fixed_well_cost_name} (fixed cost per well) instead.'
        )

    casing_factor = 1.0
    if not NonverticalsCased:
        # assume that casing & cementing costs 50% of drilling costs
        casing_factor = 0.5
    if model.economics.Nonvertical_drilling_cost_per_m.Provided or well_correlation is WellDrillingCostCorrelation.SIMPLE:
        cost_of_lateral_section = casing_factor * ((num_lateral_sections * lateral_drilling_cost_per_m * length_per_section_m)) * 1E-6
    else:
        cost_per_section = well_correlation.calculate_cost_MUSD(length_per_section_m)
        cost_of_lateral_section = casing_factor * num_lateral_sections * cost_per_section

    # account for adjustment factor
    cost_of_lateral_section = well_cost_adjustment_factor * cost_of_lateral_section
    return cost_of_lateral_section


class SBTEconomics(Economics):
    """
    SBTEconomics Child class of Economics; it is the same, but has advanced SBT closed-loop functionality
    """

    def __init__(self, model: Model):
        """
        The __init__ function is the constructor for a class.  It is called whenever an instance of the class is created.
        The __init__ function can take arguments, but self is always the first one. Self refers to the instance of the
        object that has already been created, and it's used to access variables that belong to that object
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: Model
        :return: Nothing, and is used to initialize the class
        """
        model.logger.info(f'Init {__class__!s}: {sys._getframe().f_code.co_name}')

        # Initialize the superclass first to gain access to those variables
        super().__init__(model)
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = os.path.abspath(__file__)
        #self.Electricity_rate = None
        #self.Discount_rate = None
        #self.error = 0
        #self.AverageOPEX_Plant = 0
        #self.OPEX_Plant = 0
        #self.TotalCAPEX = 0
        #self.CAPEX_Surface_Plant = 0
        #self.CAPEX_Drilling = 0

        # Set up all the Parameters that will be predefined by this class using the different types of parameter classes.
        # Setting up includes giving it a name, a default value, The Unit Type (length, volume, temperature, etc.)
        # and Unit Name of that value, sets it as required (or not), sets allowable range,
        # the error message if that range is exceeded, the ToolTip Text, and the name of the class that created it.
        # This includes setting up temporary variables that will be available to all the class but noy read in by user,
        # or used for Output
        # This also includes all Parameters that are calculated and then published using the Printouts function.
        # If you choose to subclass this master class, you can do so before or after you create your own parameters.
        # If you do, you can also choose to call this method from you class, which will effectively add
        # and set all these parameters to your class.
        # NB: inputs we already have ("already have it") need to be set at ReadParameter time so values
        # are set at the last possible time

        """
        self.O_and_M_cost_plant = self.ParameterDict[self.O_and_M_cost_plant.Name] = floatParameter(
            "Operation & Maintenance Cost of Surface Plant",
            DefaultValue=0.015,
            Min=0.0,
            Max=0.2,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Required=True,
            ErrMessage="assume default Operation & Maintenance cost of surface plant expressed as fraction of total surface plant capital cost (0.015)"
        )
        self.Direct_use_heat_cost_per_kWth = self.ParameterDict[
            self.Direct_use_heat_cost_per_kWth.Name] = floatParameter(
            "Capital Cost for Surface Plant for Direct-use System",
            DefaultValue=100.0,
            Min=0.0,
            Max=10000.0,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKW,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKW,
            Required=False,
            ErrMessage="assume default Capital cost for surface plant for direct-use system (100 $/kWth)"
        )
        self.Power_plant_cost_per_kWe = self.ParameterDict[self.Power_plant_cost_per_kWe.Name] = floatParameter(
            "Capital Cost for Power Plant for Electricity Generation",
            DefaultValue=3000.0,
            Min=0.0,
            Max=10000.0,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKW,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKW,
            Required=True,
            ErrMessage="assume default Power plant capital cost per kWe (3000 USD/kWe)"
        )

        # results are stored here and in the parent ProducedTemperature array

"""
        model.logger.info(f'complete {__class__!s}: {sys._getframe().f_code.co_name}')

    def __str__(self):
        return 'SBTEconomics'

    def read_parameters(self, model: Model) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary and stores them in the parameters.
        It also handles special cases that need to be handled after a value has been read in and checked.
        If you choose to subclass this master class, you can also choose to override this method (or not), and if you do
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        model.logger.info(f'Init {__class__!s}: {sys._getframe().f_code.co_name}')
        super().read_parameters(model)  # read the default parameters
        # if we call super, we don't need to deal with setting the parameters here,
        # just deal with the special cases for the variables in this class
        # because the call to the super.readparameters will set all the variables,
        # including the ones that are specific to this class

        # inputs we already have - needs to be set at ReadParameter time so values set at the latest possible time
   #     self.Discount_rate = model.economics.discountrate.value  # same units are GEOPHIRES
   #     self.Electricity_rate = model.surfaceplant.electricity_cost_to_buy.value  # same units are GEOPHIRES

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

        #if hasattr(model.wellbores, 'numnonverticalsections') and model.wellbores.numnonverticalsections.Provided:
            #self.cost_lateral_section.value = 0.0

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
            # calculate the cost of one vertical production well
            self.cost_one_production_well.value = (
                self._wellfield_indirect_cost_factor
                * calculate_cost_of_one_vertical_well(model,
                                                      model.wellbores.vertical_section_length.value,
                                                      self.wellcorrelation.value,
                                                      self.Vertical_drilling_cost_per_m.value,
                                                      self.per_production_well_cost.Name,
                                                      self.production_well_cost_adjustment_factor.value)
            )

            # If there is no injector well, then we assume we are doing a coaxial closed-loop.
            if model.wellbores.ninj.value == 0:
                self.cost_one_injection_well.value = 0.0
            else:
                # Now calculate the cost of one vertical injection well
                # assume the cost of the injector and producer is the same
                self.cost_one_injection_well.value = self.cost_one_production_well.value

            if hasattr(model.wellbores, 'numnonverticalsections') and model.wellbores.numnonverticalsections.Provided:
                # now calculate the costs if we have a lateral section
                self.cost_lateral_section.value = (
                    self._wellfield_indirect_cost_factor
                    * calculate_cost_of_lateral_section(model,
                                                        model.wellbores.tot_lateral_m.value,
                                                        self.wellcorrelation.value,
                                                        self.Nonvertical_drilling_cost_per_m.value,
                                                        model.wellbores.numnonverticalsections.value,
                                                        self.per_injection_well_cost.Name,
                                                        model.wellbores.NonverticalsCased.value,
                                                        self.production_well_cost_adjustment_factor.value)
                )

                # If it is an EavorLoop, we need to calculate the cost of the section of the well from
                # the bottom of the vertical to the junction with the laterals.
                # This section is not vertical, but it is cased, so we will estimate the cost
                # of this section as if it were a vertical section.
                if model.wellbores.Configuration.value == Configuration.EAVORLOOP:
                    self.cost_to_junction_section.value = (
                        self._wellfield_indirect_cost_factor
                        * calculate_cost_of_one_vertical_well(model,
                                                              model.wellbores.tot_to_junction_m.value,
                                                              self.wellcorrelation.value,
                                                              self.Vertical_drilling_cost_per_m.value,
                                                              self.per_injection_well_cost.Name,
                                                              self.injection_well_cost_adjustment_factor.value)
                    )
            else:
                self.cost_lateral_section.value = 0.0
                self.cost_to_junction_section.value = 0.0

            # cost of the well field
            self.Cwell.value = ((self.cost_one_production_well.value * model.wellbores.nprod.value) +
                                (self.cost_one_injection_well.value * model.wellbores.ninj.value) +
                                self.cost_lateral_section.value + self.cost_to_junction_section.value)

        self.Cstim.value = self.calculate_stimulation_costs(model).to(self.Cstim.CurrentUnits).magnitude

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

        # Based on GETEM 2016 #1.15 for 15% contingency
        self.Cgath.value = 1.15 * self.ccgathadjfactor.value * self._indirect_cost_factor * (
                (model.wellbores.nprod.value + model.wellbores.ninj.value) * 750 * 500. + self.Cpumps) / 1E6

        # plant costs
        if (model.surfaceplant.enduse_option.value == EndUseOptions.HEAT
            and model.surfaceplant.plant_type.value not in [PlantType.ABSORPTION_CHILLER, PlantType.HEAT_PUMP, PlantType.DISTRICT_HEATING]):  # direct-use
            if self.ccplantfixed.Valid:
                self.Cplant.value = self.ccplantfixed.value
            else:
                self.Cplant.value = self._indirect_cost_factor * 1.15 * self.ccplantadjfactor.value * 250E-6 * np.max(
                    model.surfaceplant.HeatExtracted.value) * 1000.  # 1.15 for 15% contingency

        # absorption chiller
        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value == PlantType.ABSORPTION_CHILLER:  # absorption chiller
            if self.ccplantfixed.Valid:
                self.Cplant.value = self.ccplantfixed.value
            else:
                # this is for the direct-use part all the way up to the absorption chiller
                self.Cplant.value = self._indirect_cost_factor * 1.15 * self.ccplantadjfactor.value * 250E-6 * np.max(
                    model.surfaceplant.HeatExtracted.value) * 1000.  # 1.15 for 15% contingency
                if self.chillercapex.value == -1:  # no value provided by user, use built-in correlation ($2500/ton)
                    self.chillercapex.value = self._indirect_cost_factor * 1.15 * np.max(
                        model.surfaceplant.cooling_produced.value) * 1000 / 3.517 * 2500 / 1e6  # $2,500/ton of cooling. 1.15 for 15% contingency

                # now add chiller cost to surface plant cost
                self.Cplant.value += self.chillercapex.value

        # heat pump
        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value == PlantType.HEAT_PUMP:
            if self.ccplantfixed.Valid:
                self.Cplant.value = self.ccplantfixed.value
            else:
                # this is for the direct-use part all the way up to the heat pump
                self.Cplant.value = self._indirect_cost_factor * 1.15 * self.ccplantadjfactor.value * 250E-6 * np.max(
                    model.surfaceplant.HeatExtracted.value) * 1000.  # 1.15 for 15% contingency
                if self.heatpumpcapex.value == -1:  # no value provided by user, use built-in correlation ($150/kWth)
                    self.heatpumpcapex.value = self._indirect_cost_factor * 1.15 * np.max(
                        model.surfaceplant.HeatProduced.value) * 1000 * 150 / 1e6  # $150/kW. 1.15 for 15% contingency

                # now add heat pump cost to surface plant cost
                self.Cplant.value += self.heatpumpcapex.value

        # district heating
        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
            if self.ccplantfixed.Valid:
                self.Cplant.value = self.ccplantfixed.value
            else:
                self.Cplant.value = self._indirect_cost_factor * 1.15 * self.ccplantadjfactor.value * 250E-6 * np.max(
                    model.surfaceplant.HeatExtracted.value) * 1000.  # 1.15 for 15% contingency

                # FIXME use self.peaking_boiler_cost_per_kW instead of hardcoded 65
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
                # 1.02 to convert cost from 2012 to 2016 #factor 1.15 for 15% contingency and factor 1.10 to convert from 2016 to 2022
                self.Cplant.value = self._indirect_cost_factor * 1.15 * self.ccplantadjfactor.value * self.Cplantcorrelation * 1.02 * 1.10
                self.CAPEX_cost_electricity_plant = self.Cplant.value

        # add direct-use plant cost of co-gen system to Cplant (only of no total Cplant was provided)
        if not self.ccplantfixed.Valid:  # 1.15 below for contingency
            if model.surfaceplant.enduse_option.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY,
                                                          EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT]:  # enduse_option = 3: cogen topping cycle
                self.CAPEX_cost_heat_plant = self._indirect_cost_factor * 1.15 * self.ccplantadjfactor.value * 250E-6 * np.max(
                    model.surfaceplant.HeatProduced.value / model.surfaceplant.enduse_efficiency_factor.value) * 1000.
            elif model.surfaceplant.enduse_option.value in [EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                            EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY]:  # enduse_option = 4: cogen bottoming cycle
                self.CAPEX_cost_heat_plant = self._indirect_cost_factor * 1.15 * self.ccplantadjfactor.value * 250E-6 * np.max(
                    model.surfaceplant.HeatProduced.value / model.surfaceplant.enduse_efficiency_factor.value) * 1000.
            elif model.surfaceplant.enduse_option.value in [EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY,
                                                            EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT]:  # cogen parallel cycle
                self.CAPEX_cost_heat_plant = self._indirect_cost_factor * 1.15 * self.ccplantadjfactor.value * 250E-6 * np.max(
                    model.surfaceplant.HeatProduced.value / model.surfaceplant.enduse_efficiency_factor.value) * 1000.

            self.Cplant.value = self.Cplant.value + self.CAPEX_cost_heat_plant
            if not self.CAPEX_heat_electricity_plant_ratio.Provided:
                self.CAPEX_heat_electricity_plant_ratio.value = self.CAPEX_cost_electricity_plant/self.Cplant.value

        if not self.totalcapcost.Valid:
            # exploration costs (same as in Geophires v1.2) (M$)
            if self.ccexplfixed.Valid:
                self.Cexpl.value = self.ccexplfixed.value
            else:
                self.Cexpl.value = 1.15 * self.ccexpladjfactor.value * self._indirect_cost_factor * (
                    1. + self.cost_one_production_well.value * 0.6)  # 1.15 for 15% contingency

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
                # TODO parameterize
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
                                                           self.PTCDuration.value, self.PTCCooling.value, self.PTCInflationAdjusted.value,
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
            self.TotalRevenue.value = self.ElecRevenue.value.copy()
            #self.TotalCummRevenue.value = self.ElecCummRevenue.value
        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value not in [PlantType.ABSORPTION_CHILLER]:
            self.HeatRevenue.value, self.HeatCummRevenue.value = CalculateRevenue(
                model.surfaceplant.plant_lifetime.value, model.surfaceplant.construction_years.value,
                model.surfaceplant.HeatkWhProduced.value, self.HeatPrice.value)
            self.TotalRevenue.value = self.HeatRevenue.value.copy()
            #self.TotalCummRevenue.value = self.HeatCummRevenue.value
        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value in [PlantType.ABSORPTION_CHILLER]:
            self.CoolingRevenue.value, self.CoolingCummRevenue.value = CalculateRevenue(
                model.surfaceplant.plant_lifetime.value, model.surfaceplant.construction_years.value,
                model.surfaceplant.cooling_kWh_Produced.value, self.CoolingPrice.value)
            self.TotalRevenue.value = self.CoolingRevenue.value.copy()
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

        self._calculate_derived_outputs(model)
        model.logger.info(f'complete {__class__!s}: {sys._getframe().f_code.co_name}')


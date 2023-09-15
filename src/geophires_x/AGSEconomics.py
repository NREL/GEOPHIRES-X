import sys
import os
import numpy as np
import geophires_x.AdvModel as AdvModel
import geophires_x.Economics as Economics
import geophires_x.AdvGeoPHIRESUtils as AdvGeoPHIRESUtils
from .Parameter import floatParameter
from .Units import *
from .OptionList import WorkingFluid, EndUseOptions, EconomicModel


class AGSEconomics(Economics.Economics):
    """
    AGSEconomics Child class of Economics; it is the same, but has advanced AGS closed-loop functionality
    """

    def __init__(self, model: AdvModel):
        """
        The __init__ function is the constructor for a class.  It is called whenever an instance of the class is created.
        The __init__ function can take arguments, but self is always the first one. Self refers to the instance of the
        object that has already been created, and it's used to access variables that belong to that object.&quot;

        :param self: Reference the class object itself
        :param model: The container class of the application, giving access to everything else, including the logger

        :return: Nothing, and is used to initialize the class
        :doc-author: Malcolm Ross
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        # Initialize the superclass first to gain access to those variables
        super().__init__(model)
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = os.path.abspath(__file__)
        self.Electricity_rate = None
        self.Discount_rate = None
        self.error = 0
        self.AverageOPEX_Plant = 0
        self.OPEX_Plant = 0
        self.TotalCAPEX = 0
        self.CAPEX_Surface_Plant = 0
        self.CAPEX_Drilling = 0

        # Set up all the Parameters that will be predefined by this class using the different types of parameter classes.
        # Setting up includes giving it a name, a default value, The Unit Type (length, volume, temperature, etc.) and Unit Name of that value,
        # sets it as required (or not), sets allowable range, the error message if that range is exceeded, the ToolTip Text,
        # and the name of teh class that created it.
        # This includes setting up temporary variables that will be available to all the class but noy read in by user,
        # or used for Output
        # This also includes all Parameters that are calculated and then published using the Printouts function.
        # If you choose to subclass this master class, you can do so before or after you create your own parameters.
        # If you do, you can also choose to call this method from you class, which will effectively add and set all these parameters to your class.
        # NB: inputs we already have ("already have it") need to be set at ReadParameter time so values are set at the last possible time

        self.O_and_M_cost_plant = self.ParameterDict[self.O_and_M_cost_plant.Name] = floatParameter(
            "Operation & Maintenance Cost of Surface Plant",
            value=0.015,
            DefaultValue=0.015,
            Min=0.0,
            Max=0.2,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Required=True,
            ErrMessage="assume default Operation & Maintenance cost of surface plant expressed as fraction of total surface plant capital cost (0.015)"
        )
        self.Direct_use_heat_cost_per_kWth = self.ParameterDict[self.Direct_use_heat_cost_per_kWth.Name] = floatParameter(
            "Capital Cost for Surface Plant for Direct-use System",
            value=100.0,
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
            "Capital Cost for Power Plant for Electricity Generation", value=3000.0,
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

        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def __str__(self):
        return "AGSEconomics"

    def read_parameters(self, model: AdvModel) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary and stores them in the parameters.
        It also handles special cases that need to be handled after a value has been read in and checked.
        If you choose to subclass this master class, you can also choose to override this method (or not), and if you do

        :param self: Access variables that belong to a class
        :param model: The container class of the application, giving access to everything else, including the logger

        :return: None
        :doc-author: Malcolm Ross
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)
        super().read_parameters(model)  # read the default parameters
        # if we call super, we don't need to deal with setting the parameters here, just deal with the special cases for the variables in this class
        # because the call to the super.readparameters will set all the variables, including the ones that are specific to this class

        # inputs we already have - needs to be set at ReadParameter time so values set at the latest possible time
        self.Discount_rate = model.economics.discountrate.value  # same units are GEOPHIRES
        self.Electricity_rate = model.surfaceplant.elecprice.value  # same units are GEOPHIRES

        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def verify(self, model: AdvModel) -> int:
        """
        The validate function checks that all values provided are within the range expected by AGS modeling system.
        These values in within a smaller range than the value ranges available to GEOPHIRES-X

        :param self: Access variables that belong to a class
        :param model: The container class of the application, giving access to everything else, including the logger

        :return: 0 if all OK, 1 if error.
        :doc-author: Koenraad Beckers
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        # Verify inputs are within allowable bounds
        self.error = 0
        if self.O_and_M_cost_plant.value < 0 or self.O_and_M_cost_plant.value > 0.2:
            print(
                "Error: CLGS model database imposes additional range restrictions: Operation & maintenance cost of \
                surface plant (expressed as fraction of total surface plant capital cost) must be between 0 and 0.2. \
                Simulation terminated.")
            model.logger.fatal(
                "Error: CLGS model database imposes additional range restrictions: Operation & maintenance cost of \
                surface plant (expressed as fraction of total surface plant capital cost) must be between 0 and 0.2. \
                Simulation terminated.")
            self.error = 1
        if self.Discount_rate < 0 or self.Discount_rate > 0.2:
            print(
                "Error: CLGS model database imposes additional range restrictions: Discount rate must be between \
                0 and 0.2. Simulation terminated.")
            model.logger.fatal(
                "Error: CLGS model database imposes additional range restrictions: Discount rate must be between \
                0 and 0.2. Simulation terminated.")
            self.error = 1
        if self.Direct_use_heat_cost_per_kWth.value < 0 or self.Direct_use_heat_cost_per_kWth.value > 10_000:
            print(
                "Error: CLGS model database imposes additional range restrictions: Capital cost for direct-use \
                surface plant must be between 0 and 10,000 $/kWth. Simulation terminated.")
            model.logger.fatal(
                "Error: CLGS model database imposes additional range restrictions: Capital cost for direct-use \
                surface plant must be between 0 and 10,000 $/kWth. Simulation terminated.")
            self.error = 1
        if self.Electricity_rate < 0 or self.Electricity_rate > 0.5:
            print(
                "Error: CLGS model database imposes additional range restrictions: Electricity rate in direct-use \
                for pumping power must be between 0 and 0.5 $/kWh. Simulation terminated.")
            model.logger.fatal(
                "Error: CLGS model database imposes additional range restrictions: Electricity rate in direct-use \
                for pumping power must be between 0 and 0.5 $/kWh. Simulation terminated.")
            self.error = 1
        if self.Power_plant_cost_per_kWe.value < 0 or self.Power_plant_cost_per_kWe.value > 10_000:
            print(
                "Error: CLGS model database imposes additional range restrictions: Power plant capital cost must be \
                between 0 and 10,000 $/kWe. Simulation terminated.")
            model.logger.fatal(
                "Error: CLGS model database imposes additional range restrictions: Power plant capital cost must be \
                between 0 and 10,000 $/kWe. Simulation terminated.")
            self.error = 1
        if model.surfaceplant.End_use not in (EndUseOptions.HEAT, EndUseOptions.ELECTRICITY):
            print(
                "Error: CLGS model database imposes additional range restrictions: Economic Calculations can only be \
                made only for electricity or heat, not a combination.")
            model.logger.fatal(
                "Error: CLGS model database imposes additional range restrictions:  Economic Calculations can only be \
                made only for electricity or heat, not a combination.")
            self.error = 1

        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)
        return self.error

    def Calculate(self, model: AdvModel) -> None:
        """
        The calculate function verifies, initializes, and calculate the values for the AGS model

        :param self: Access variables that belong to a class
        :param model: The container class of the application, giving access to everything else, including the logger

        :return: None
        :doc-author: Koenraad Beckers
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        if self.econmodel.value != EconomicModel.CLGS:  # do a classical econ calculation
            super().Calculate(model)
        else:  # use the CLGS-Style economic calculations
            err = self.verify(model)
            if err > 0:
                print("Error: GEOPHIRES failed to Failed to validate CLGS input value.  Exiting....")
                sys.exit()
            # Calculate CAPEX
            tot, vert, horiz = model.wellbores.calculatedrillinglengths(model)
            vertical_CAPEX_Drilling = vert * self.Vertical_drilling_cost_per_m.value / 1e6  # Drilling capital cost [M$]
            horizontal_CAPEX_Drilling = horiz * self.Nonvertical_drilling_cost_per_m.value / 1e6  # Drilling capital cost [M$]
            self.CAPEX_Drilling = vertical_CAPEX_Drilling + horizontal_CAPEX_Drilling
            if model.surfaceplant.End_use == EndUseOptions.HEAT:
                self.CAPEX_Surface_Plant = np.max(
                    model.surfaceplant.Instantaneous_heat_production) * self.Direct_use_heat_cost_per_kWth.value / 1e6  # [M$]
            elif model.surfaceplant.End_use == EndUseOptions.ELECTRICITY:
                if model.wellbores.Fluid.value == WorkingFluid.WATER:
                    self.CAPEX_Surface_Plant = np.max(
                        model.surfaceplant.Instantaneous_electricity_production_method_1) * self.Power_plant_cost_per_kWe.value / 1e6  # [M$]
                else:
                    self.CAPEX_Surface_Plant = np.max(
                        model.surfaceplant.Instantaneous_electricity_production_method_4) * self.Power_plant_cost_per_kWe.value / 1e6  # [M$]

            self.TotalCAPEX = self.CAPEX_Drilling + self.CAPEX_Surface_Plant  # Total system capital cost (only includes drilling and surface plant cost) [M$]

            # Calculate OPEX
            if model.surfaceplant.End_use == EndUseOptions.HEAT:
                self.OPEX_Plant = self.O_and_M_cost_plant.value * self.CAPEX_Surface_Plant + model.surfaceplant.Annual_pumping_power * self.Electricity_rate / 1e6  # Annual plant O&M cost [M$/year]
            elif model.surfaceplant.End_use == EndUseOptions.ELECTRICITY:
                self.OPEX_Plant = self.O_and_M_cost_plant.value * self.CAPEX_Surface_Plant  # Annual plant O&M cost [M$/year]

            self.AverageOPEX_Plant = np.average(self.OPEX_Plant)

            # Calculate LCO(H)(E)
            Discount_vector = 1. / np.power(1 + self.Discount_rate, np.linspace(0, model.surfaceplant.Lifetime - 1,
                                                                                model.surfaceplant.Lifetime))
            if model.surfaceplant.End_use == EndUseOptions.HEAT:
                self.LCOH.CurrentUnits = EnergyCostUnit.DOLLARSPERMWH
                self.LCOH.value = (self.TotalCAPEX + np.sum(self.OPEX_Plant * Discount_vector)) * 1e6 / np.sum(
                    model.surfaceplant.Annual_heat_production / 1e3 * Discount_vector)  # $/MWh
                if self.LCOH.value < 0:
                    self.LCOH.value = 9999
                    model.surfaceplant.error_codes = np.append(model.surfaceplant.error_codes, 5000)
            elif model.surfaceplant.End_use == EndUseOptions.ELECTRICITY:
                self.LCOE.CurrentUnits = EnergyCostUnit.DOLLARSPERMWH
                if model.surfaceplant.Average_electricity_production == 0:
                    self.LCOE.value = 9999
                    model.surfaceplant.error_codes = np.append(model.surfaceplant.error_codes, 6000)
                else:
                    self.LCOE.value = (self.TotalCAPEX + np.sum(self.OPEX_Plant * Discount_vector)) * 1e6 / np.sum((
                                                                                                                           model.surfaceplant.Annual_electricity_production - model.surfaceplant.Annual_pumping_power) / 1e3 * Discount_vector)  # $/MWh
                if self.LCOE.value < 0:
                    self.LCOE.value = 9999
                    model.surfaceplant.error_codes = np.append(model.surfaceplant.error_codes, 7000)

            # handle errors
            if len(model.surfaceplant.error_codes) > 0:
                model.logger.fatal(
                    "failed with the following error codes: " + str(model.surfaceplant.error_codes[0:]) + " in " + str(
                        __class__) + " " + os.path.abspath(__file__))
                print("Error: failed with the following error codes" + str(
                    model.surfaceplant.error_codes[0:]) + " in " + str(__class__) + " " + os.path.abspath(
                    __file__) + ".  Exiting....")
                sys.exit()

            # copy values to GEOPHIRES Equivalents
            self.CCap.value = self.TotalCAPEX
            self.CCap.CurrentUnits = CurrencyUnit.MDOLLARS
            self.Cwell.value = self.CAPEX_Drilling
            self.Cplant.CurrentUnits = CurrencyUnit.MDOLLARS
            self.Cplant.value = self.CAPEX_Surface_Plant
            self.Cplant.CurrentUnits = CurrencyUnit.MDOLLARS
            self.Coam.value = self.AverageOPEX_Plant * 1000
            self.Coam.CurrentUnits = CurrencyFrequencyUnit.KDOLLARSPERYEAR

        # store the calculation result and associated object parameters in the database
        resultkey = AdvGeoPHIRESUtils.store_result(model, self)
        if resultkey.startswith("ERROR"):
            model.logger.warn("Failed To Store " + str(__class__) + " " + os.path.abspath(__file__))
        else:
            pass

        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def __str__(self):
        return "AGSEconomics"

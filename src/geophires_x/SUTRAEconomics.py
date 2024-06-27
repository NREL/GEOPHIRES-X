import sys
import os
import numpy as np
import geophires_x.Model as Model
import geophires_x.Economics as Economics
from geophires_x.OptionList import WellDrillingCostCorrelation, EconomicModel
from geophires_x.Parameter import intParameter, floatParameter, OutputParameter, ReadParameter, boolParameter
from geophires_x.Units import *


class SUTRAEconomics(Economics.Economics):
    """
    Class to support the default economic calculations in GEOPHIRES
    """

    def __init__(self, model: Model):
        """
        The __init__ function is called automatically when a class is instantiated.
        It initializes the attributes of an object, and sets default values for certain arguments that can be overridden
        by user input.
        The __init__ function is used to set up all the parameters in Economics.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        model.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')
        super().__init__(model)

        # Set up all the Parameters that will be predefined by this class using the different types of parameter classes.
        # Setting up includes giving it a name, a default value, The Unit Type (length, volume, temperature, etc.) and
        # Unit Name of that value, sets it as required (or not), sets allowable range, the error message if that range
        # is exceeded, the ToolTip Text, and the name of teh class that created it.
        # This includes setting up temporary variables that will be available to all the class but noy read in by user,
        # or used for Output
        # This also includes all Parameters that are calculated and then published using the Printouts function.
        # If you choose to subclass this master class, you can do so before or after you create your own parameters.
        # If you do, you can also choose to call this method from you class, which will effectively add and set all
        # these parameters to your class.

        # These dictionaries contain a list of all the parameters set in this object, stored as "Parameter" and
        # "OutputParameter" Objects.  This will allow us later to access them in a user interface and get that list,
        # along with unit type, preferred units, etc.
        self.ParameterDict = {}
        self.OutputParameterDict = {}

        # Note: setting Valid to False for any of the cost parameters forces GEOPHIRES to use it's builtin cost engine.
        # This is the default.
        self.econmodel = self.ParameterDict[self.econmodel.Name] = intParameter(
            "Economic Model",
            value=EconomicModel.STANDARDIZED_LEVELIZED_COST,
            DefaultValue=EconomicModel.STANDARDIZED_LEVELIZED_COST,
            AllowableRange=[1, 2, 3],
            Required=True,
            ErrMessage="assume default economic model (2)",
            ToolTipText="Specify the economic model to calculate the levelized cost of energy."
            + " 1: Fixed Charge Rate Model, 2: Standard Levelized Cost Model, 3: BICYCLE Levelized Cost Model, 4: CLGS",
        )

        self.ccwellfixed = self.ParameterDict[self.ccwellfixed.Name] = floatParameter(
            "Well Drilling and Completion Capital Cost",
            value=-1.0,
            DefaultValue=-1.0,
            Min=0,
            Max=200,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS,
            Provided=False,
            Valid=False,
            ToolTipText="Well Drilling and Completion Capital Cost",
        )
        self.ccwelladjfactor = self.ParameterDict[self.ccwelladjfactor.Name] = floatParameter(
            "Well Drilling and Completion Capital Cost Adjustment Factor",
            value=1.0,
            DefaultValue=1.0,
            Min=0,
            Max=10,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Provided=False,
            Valid=True,
            ToolTipText="Well Drilling and Completion Capital Cost Adjustment Factor",
        )

        self.ccplantfixed = self.ParameterDict[self.ccplantfixed.Name] = floatParameter(
            "Surface Plant Capital Cost",
            value=-1.0,
            DefaultValue=-1.0,
            Min=0,
            Max=1000,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS,
            Provided=False,
            Valid=False,
            ToolTipText="Total surface plant capital cost",
        )
        self.ccplantadjfactor = self.ParameterDict[self.ccplantadjfactor.Name] = floatParameter(
            "Surface Plant Capital Cost Adjustment Factor",
            value=1.0,
            DefaultValue=1.0,
            Min=0,
            Max=10,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Provided=False,
            Valid=True,
            ToolTipText="Multiplier for built-in surface plant capital cost correlation",
        )

        self.discountrate = self.ParameterDict[self.discountrate.Name] = floatParameter(
            "Discount Rate",
            value=0.07,
            DefaultValue=0.07,
            Min=0.0,
            Max=1.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.PERCENT,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default discount rate (0.07)",
            ToolTipText="Discount rate used in the Standard Levelized Cost Model",
        )

        self.inflrateconstruction = self.ParameterDict[self.inflrateconstruction.Name] = floatParameter(
            "Inflation Rate During Construction",
            value=0.0,
            DefaultValue=0.0,
            Min=0.0,
            Max=1.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.PERCENT,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default inflation rate during construction (0)",
        )
        self.wellcorrelation = self.ParameterDict[self.wellcorrelation.Name] = intParameter(
            "Well Drilling Cost Correlation",
            DefaultValue=WellDrillingCostCorrelation.VERTICAL_LARGE_INT1.int_value,
            AllowableRange=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
            ValuesEnum=WellDrillingCostCorrelation,
            UnitType=Units.NONE,
            ErrMessage="assume default well drilling cost correlation (10)",
            ToolTipText="Select the built-in well drilling and completion cost correlation: " +
                        '; '.join([f'{it.int_value}: {it.value}' for it in WellDrillingCostCorrelation])
        )

        self.timestepsperyear = self.ParameterDict[self.timestepsperyear.Name] = intParameter(
            "Time steps per year",
            value=4,
            DefaultValue=4,
            AllowableRange=list(range(1, 101, 1)),
            UnitType=Units.NONE,
            Required=True,
            ErrMessage="assume default number of time steps per year (4)",
            ToolTipText="Number of internal simulation time steps per year",
        )

        self.DoAddOnCalculations = self.ParameterDict[self.DoAddOnCalculations.Name] = boolParameter(
            "Do AddOn Calculations",
            value=False,
            DefaultValue=False,
            UnitType=Units.NONE,
            Required=False,
            ErrMessage="assume default: no economics calculations",
            ToolTipText="Set to true if you want the add-on economics calculations to be made",
        )
        self.DoCCUSCalculations = self.ParameterDict[self.DoCCUSCalculations.Name] = boolParameter(
            "Do CCUS Calculations",
            value=False,
            DefaultValue=False,
            UnitType=Units.NONE,
            Required=False,
            ErrMessage="assume default: no CCUS calculations",
            ToolTipText="Set to true if you want the CCUS economics calculations to be made",
        )
        self.DoSDACGTCalculations = self.ParameterDict[self.DoSDACGTCalculations.Name] = boolParameter(
            "Do S-DAC-GT Calculations",
            value=False,
            DefaultValue=False,
            UnitType=Units.NONE,
            Required=False,
            ErrMessage="assume default: no S-DAC-GT calculations",
            ToolTipText="Set to true if you want the S-DAC-GT economics calculations to be made",
        )

        # heat pump
        self.heatpumpcapex = self.ParameterDict[self.heatpumpcapex.Name] = floatParameter(
            "Heat Pump Capital Cost",
            value=-1.0,
            Min=0,
            Max=100,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS,
            Provided=False,
            Valid=False,
            ToolTipText="Heat pump capital cost",
        )

        self.ngprice = self.ParameterDict[self.ngprice.Name] = floatParameter(
            "Peaking Fuel Cost Rate",
            value=0.034,
            Min=0.0,
            Max=1.0,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH,
            ErrMessage="assume default peaking fuel rate ($0.034/kWh)",
            ToolTipText="Price of peaking fuel for peaking boilers",
        )
        self.peakingboilerefficiency = self.ParameterDict[self.peakingboilerefficiency.Name] = floatParameter(
            "Peaking Boiler Efficiency",
            value=0.85,
            Min=0,
            Max=1,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Provided=False,
            Valid=False,
            ErrMessage="assume default peaking boiler efficiency (85%)",
            ToolTipText="Peaking boiler efficiency",
        )

        self.LCOH = self.OutputParameterDict[self.LCOH.Name] = OutputParameter(
            "Heat Sale Price Model",
            value=[0.025],
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.CENTSSPERKWH,
            CurrentUnits=EnergyCostUnit.CENTSSPERKWH,
        )

        # local variable initialization
        self.Cpumps = 0.0
        self.InputFile = ""
        self.C1well = 0.0
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = os.path.abspath(__file__)

        # results
        self.Cwell = self.OutputParameterDict[self.Cwell.Name] = OutputParameter(
            Name="Wellfield cost",
            value=-999.9,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS,
        )

        self.CCap = self.OutputParameterDict[self.CCap.Name] = OutputParameter(
            Name="Total Capital Cost",
            value=-999.9,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS,
        )
        self.Coam = self.OutputParameterDict[self.Coam.Name] = OutputParameter(
            Name="Total O&M Cost",
            value=-999.9,
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.KDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.KDOLLARSPERYEAR,
        )
        self.annualpumpingcosts = self.OutputParameterDict[self.annualpumpingcosts.Name] = OutputParameter(
            Name="Annual Pumping Costs",
            value=-0.0,
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.KDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.KDOLLARSPERYEAR,
        )

        # heat pump
        self.averageannualheatpumpelectricitycost = self.OutputParameterDict[
            self.averageannualheatpumpelectricitycost.Name
        ] = OutputParameter(
            Name="Average Annual Heat Pump Electricity Cost",
            value=0.0,
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
        )

        self.peakingboilercost = self.OutputParameterDict[self.peakingboilercost.Name] = OutputParameter(
            Name="Peaking boiler cost",
            value=0,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS,
        )

        self.annualngcost = self.OutputParameterDict[self.annualngcost.Name] = OutputParameter(
            Name="Annual Peaking Fuel Cost",
            value=0,
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.KDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.KDOLLARSPERYEAR,
        )

        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def read_parameters(self, model: Model) -> None:
        """
        read_parameters read and update the Economics parameters and handle the special cases that need to be taken care of after a
        value has been read in and checked. This is called from the main Model class. It is not called from the __init__
        function because the user may not want to read in the parameters from the input file, but may want to set them
        in the user interface.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing, but it does make calculations and set values in the model
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        # Deal with all the parameter values that the user has provided.  They should really only provide values
        # that they want to change from the default values, but they can provide a value that is already set
        # because it is a default value set in __init__.  It will ignore those.
        # This also deals with all the special cases that need to be taken care of after a
        # value has been read in and checked.
        # If you choose to subclass this master class, you can also choose to override this method (or not),
        # and if you do, do it before or after you call you own version of this method.  If you do, you can also
        # choose to call this method from you class, which can effectively modify all these superclass parameters
        # in your class.

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
        else:
            model.logger.info("No parameters read because no content provided")

        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def Calculate(self, model: Model) -> None:
        """
        The Calculate function is where all the calculations are done.
        This function can be called multiple times, and will only recalculate what has changed each time it is called.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing, but it does make calculations and set values in the model
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        # This is where all the calculations are made using all the values that have been set.
        # If you subclass this class, you can choose to run these calculations before (or after) your calculations,
        # but that assumes you have set all the values that are required for these calculations
        # If you choose to subclass this master class, you can also choose to override this method (or not),
        # and if you do, do it before or after you call you own version of this method.  If you do,
        # you can also choose to call this method from you class, which can effectively run the calculations
        # of the superclass, making all thr values available to your methods. but you had
        # better have set all the parameters!

        # CAPEX
        # Drilling

        self.C1well = 0
        if self.ccwellfixed.Valid:
            self.C1well = self.ccwellfixed.value
            self.Cwell.value = self.C1well * (model.wellbores.nprod.value + model.wellbores.ninj.value)
        else:
            if model.reserv.depth.value > 7000.0 or model.reserv.depth.value < 500:
                print('Warning: simple user-specified cost per meter used for drilling depth < 500 or > 7000 m')
                model.logger.warning(
                    'Warning: simple user-specified cost per meter used for drilling depth < 500 or > 7000 m'
                )

            self.C1well = self.wellcorrelation.value.calculate_cost_MUSD(model.reserv.depth.value)

            self.C1well = self.C1well * self.ccwelladjfactor.value
            self.Cwell.value = self.C1well * (model.wellbores.nprod.value + model.wellbores.ninj.value)

        # Boiler
        self.peakingboilercost.value = (
            65 * model.surfaceplant.max_peaking_boiler_demand.value / self.peakingboilerefficiency.value / 1000
        )  # add 65$/KW for peaking boiler

        # Circulation Pump
        pumphp = np.max(model.wellbores.PumpingPower.value) * 1.341
        numberofpumps = np.ceil(pumphp / 2000)  # pump can be maximum 2,000 hp
        if numberofpumps == 0:
            self.Cpumps = 0.0
        else:
            pumphpcorrected = pumphp / numberofpumps
            self.Cpumps = numberofpumps * 1.5 * ((1750 * pumphpcorrected**0.7) * 3 * pumphpcorrected ** (-0.11)) / 1e6

        # Total CAPEX ($M)
        self.CCap.value = self.Cwell.value + self.peakingboilercost.value + self.Cpumps

        # OPEX
        # Pumping
        self.annualpumpingcosts.value = (
            model.surfaceplant.PumpingkWh.value * model.surfaceplant.electricity_cost_to_buy.value / 1e3
        )

        # Natural Gas
        self.annualngcost.value = (
            model.surfaceplant.AnnualAuxiliaryHeatProduced.value
            * self.ngprice.value
            / self.peakingboilerefficiency.value
            * 1e3
        )

        # Price for the heat injected currently not considered

        # Total O&M cost ($K/year)
        self.Coam.value = self.annualpumpingcosts.value + self.annualngcost.value

        # LCOH
        discountvector = 1.0 / np.power(
            1 + self.discountrate.value,
            np.linspace(0, model.surfaceplant.plant_lifetime.value - 1, model.surfaceplant.plant_lifetime.value),
        )
        self.LCOH.value = (
            ((1 + self.inflrateconstruction.value) * self.CCap.value + np.sum(self.Coam.value * discountvector))
            / np.sum(model.surfaceplant.AnnualTotalHeatProduced.value * 1e6 * discountvector)
            * 1e8
        )  # cents/kWh

        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def __str__(self):
        return "Economics"

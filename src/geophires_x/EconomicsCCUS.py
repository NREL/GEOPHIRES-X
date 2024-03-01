import sys
import os
import math
import numpy_financial as npf
from geophires_x.Economics import BuildPricingModel, Economics
from geophires_x.OptionList import EndUseOptions
from geophires_x.Parameter import intParameter, floatParameter, OutputParameter
from geophires_x.Units import *


class EconomicsCCUS(Economics):
    def __init__(self, model):
        """
        The __init__ function is called automatically when a class is instantiated.
        It initializes the attributes of an object, and sets default values for certain arguments
        that can be overridden by user input.
        The __init__ function is used to set up all the parameters in the CCUS Economics.
        Set up all the Parameters that will be predefined by this class using the different types of parameter classes.
        Setting up includes giving it a name, a default value, The Unit Type (length, volume, temperature, etc.) and
        Unit Name of that value, sets it as required (or not), sets allowable range, the error message if that range
        is exceeded, the ToolTip Text, and the name of teh class that created it.
        This includes setting up temporary variables that will be available to all the class but noy read in by user,
        or used for Output
        This also includes all Parameters that are calculated and then published using the Printouts function.
        If you choose to subclass this master class, you can do so before or after you create your own parameters.
        If you do, you can also choose to call this method from you class, which will effectively add and set
        all these parameters to your class.
        set up the parameters using the Parameter Constructors (intParameter, floatParameter, strParameter, etc.);
        initialize with their name, default value, and valid range (if int or float).  Optionally, you can specify:
        Required (is it required to run? default value = False), ErrMessage (what GEOPHIRES will report if the
        value provided is invalid, "assume default value (see manual)"), ToolTipText (when there is a GUI,
        this is the text that the user will see, "This is ToolTip Text"),
        UnitType (the type of units associated with this parameter (length, temperature, density, etc), Units.NONE),
        CurrentUnits (what the units are for this parameter (meters, celcius, gm/cc, etc., Units:NONE),
        and PreferredUnits (usually equal to CurrentUnits, but these are the units that the calculations assume
        when running, Units.NONE
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)
        super().__init__(model)  # initialize the parent parameters and variables
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = os.path.abspath(__file__)

        self.FixedInternalRate = self.ParameterDict[self.FixedInternalRate.Name] = floatParameter(
            "Fixed Internal Rate",
            value=6.25,
            DefaultValue=6.25,
            Min=0.0,
            Max=100.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.PERCENT,
            CurrentUnits=PercentUnit.PERCENT,
            ErrMessage="assume default for fixed internal rate (6.25%)",
            ToolTipText="Fixed Internal Rate (used in NPV calculation)"
        )
        self.ConstructionYears = self.ParameterDict[self.ConstructionYears.Name] = intParameter(
            "Construction Years",
            value=1,
            DefaultValue=1,
            AllowableRange=list(range(1, 15, 1)),
            UnitType=Units.NONE,
            ErrMessage="assume default number of years in construction (1)",
            ToolTipText="Number of years spent in construction (assumes whole years, no fractions)"
        )
        self.CCUSEndPrice = self.ParameterDict[self.CCUSEndPrice.Name] = floatParameter(
            "Ending CCUS Credit Value",
            value=0.0,
            DefaultValue=0.0,
            Min=0,
            Max=1000,
            UnitType=Units.COSTPERMASS,
            PreferredUnits=CostPerMassUnit.DOLLARSPERLB,
            CurrentUnits=CostPerMassUnit.DOLLARSPERLB
        )
        self.CCUSEscalationStart = self.ParameterDict[self.CCUSEscalationStart.Name] = intParameter(
            "CCUS Escalation Start Year",
            value=0,
            DefaultValue=0,
            AllowableRange=list(range(0, 101, 1)),
            UnitType=Units.TIME,
            PreferredUnits=TimeUnit.YEAR,
            CurrentUnits=TimeUnit.YEAR,
            ErrMessage="assume default CCUS escalation delay time (5 years)",
            ToolTipText="Number of years after start of project before start of CCUS incentives"
            )
        self.CCUSEscalationRate = self.ParameterDict[self.CCUSEscalationRate.Name] = floatParameter(
            "CCUS Escalation Rate Per Year",
            value=0.0,
            DefaultValue=0.0,
            Min=0.0,
            Max=100.0,
            UnitType=Units.COSTPERMASS,
            PreferredUnits=CostPerMassUnit.DOLLARSPERMT,
            CurrentUnits=CostPerMassUnit.DOLLARSPERMT,
            ErrMessage="assume no CCUS credit escalation (0.0)",
            ToolTipText="additional value per year of price after escalation starts"
        )
        self.CCUSStartPrice = self.ParameterDict[self.CCUSStartPrice.Name] = floatParameter(
            "Starting CCUS Credit Value",
            value=0.0,
            DefaultValue=0.0,
            Min=0,
            Max=1000,
            UnitType=Units.COSTPERMASS,
            PreferredUnits=CostPerMassUnit.DOLLARSPERMT,
            CurrentUnits=CostPerMassUnit.DOLLARSPERMT
        )
        self.CCUSGridCO2 = self.ParameterDict[self.CCUSGridCO2.Name] = floatParameter(
            "Current Grid CO2 production",
            value=0.0,
            DefaultValue=0.0,
            Min=0,
            Max=50000,
            UnitType=Units.CO2PRODUCTION,
            PreferredUnits=CO2ProductionUnit.LBSPERKWH,
            CurrentUnits=CO2ProductionUnit.LBSPERKWH
        )
        self.HeatStartPrice = self.ParameterDict[self.HeatStartPrice.Name] = floatParameter(
            "Starting Heat Sale Price",
            value=0.025,
            DefaultValue=0.025,
            Min=0,
            Max=100,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH
        )
        self.HeatEndPrice = self.ParameterDict[self.HeatEndPrice.Name] = floatParameter(
            "Ending Heat Sale Price",
            value=0.025,
            DefaultValue=0.025,
            Min=0,
            Max=100,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH
        )
        self.HeatEscalationStart = self.ParameterDict[self.HeatEscalationStart.Name] = intParameter(
            "Heat Escalation Start Year",
            value=5,
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
            value=0.0,
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
            value=0.055,
            DefaultValue=0.055,
            Min=0,
            Max=100,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH
        )
        self.ElecEndPrice = self.ParameterDict[self.ElecEndPrice.Name] = floatParameter(
            "Ending Electricity Sale Price",
            value=0.055,
            DefaultValue=0.055,
            Min=0,
            Max=100,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH
        )
        self.ElecEscalationStart = self.ParameterDict[self.ElecEscalationStart.Name] = intParameter(
            "Electricity Escalation Start Year",
            value=5,
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
            value=0.0,
            DefaultValue=0.0,
            Min=0.0,
            Max=100.0,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH,
            ErrMessage="assume no electricity price escalation (0.0)",
            ToolTipText="additional cost per year of price after escalation starts"
        )

        # local variables that need initialization

        # results
        self.ProjectNPV = self.OutputParameterDict[self.ProjectNPV.Name] = OutputParameter(
            "Project Net Present Value",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.ProjectIRR = self.OutputParameterDict[self.ProjectIRR.Name] = OutputParameter(
            "Project Internal Rate of Return",
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.PERCENT,
            CurrentUnits=PercentUnit.PERCENT
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
        self.ProjectCashFlow = self.OutputParameterDict[self.ProjectCashFlow.Name] = OutputParameter(
            "Annual Project Cash Flow",
            value=[0.0],
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.ProjectCummCashFlow = self.OutputParameterDict[self.ProjectCummCashFlow.Name] = OutputParameter(
            "Cumulative Project Cash Flow",
            value=[0.0],
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.CCUSPrice = self.OutputParameterDict[self.CCUSPrice.Name] = OutputParameter(
            "CCUS Incentive Model",
            value=[0.0],
            UnitType=Units.COSTPERMASS,
            PreferredUnits=CostPerMassUnit.DOLLARSPERLB,
            CurrentUnits=CostPerMassUnit.DOLLARSPERLB
        )
        self.CCUSRevenue = self.OutputParameterDict[self.CCUSRevenue.Name] = OutputParameter(
            "Annual Revenue Generated from CCUS",
            value=[0.0],
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.CCUSCashFlow = self.OutputParameterDict[self.CCUSCashFlow.Name] = OutputParameter(
            "Annual Cash Flow",
            value=[0.0],
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.CCUSCummCashFlow = self.OutputParameterDict[self.CCUSCummCashFlow.Name] = OutputParameter(
            "Cumulative Cash Flow",
            value=[0.0],
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.CarbonThatWouldHaveBeenProducedAnnually = self.OutputParameterDict[
            self.CarbonThatWouldHaveBeenProducedAnnually.Name] = OutputParameter(
            "Annual Saved Carbon Production",
            value=[0.0],
            UnitType=Units.MASS,
            PreferredUnits=MassUnit.LB,
            CurrentUnits=MassUnit.LB
        )
        self.CarbonThatWouldHaveBeenProducedTotal = self.OutputParameterDict[
            self.CarbonThatWouldHaveBeenProducedTotal.Name] = OutputParameter(
            "Annual Saved Carbon Production",
            UnitType=Units.MASS,
            PreferredUnits=MassUnit.LB,
            CurrentUnits=MassUnit.LB
        )
        self.CCUSOnElecPrice = self.OutputParameterDict[self.CCUSOnElecPrice.Name] = OutputParameter(
            "CCUS Electricity Sale Price Model",
            value=[0.055],
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.CENTSSPERKWH,
            CurrentUnits=EnergyCostUnit.CENTSSPERKWH
        )
        self.CCUSOnHeatPrice = self.OutputParameterDict[self.CCUSOnHeatPrice.Name] = OutputParameter(
            "CCUS Heat Sale Price Model",
            value=[0.025],
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.CENTSSPERKWH,
            CurrentUnits=EnergyCostUnit.CENTSSPERKWH
        )

        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def read_parameters(self, model) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary and stores them in the parameters.
        It also handles special cases that need to be handled after a value has been read in and checked.
        If you choose to subclass this master class, you can also choose to override this method (or not), and if you do
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)
        super().read_parameters(model)  # read the parameters for the parent.
        # if we call super, we don't need to deal with setting the parameters here, just deal with the special cases
        # for the variables in this class
        # because the call to the super.readparameters will set all the variables, including the ones that are specific
        # to this class

        # Deal with all the parameter values that the user has provided that relate to this extension.
        # super.read_parameter will have already dealt with all the regular values, but anything unusual may not
        # be dealt with, so check.
        # In this case, all the values are array values, and weren't correctly dealt with,
        # so below is where we process them.

        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def Calculate(self, model) -> None:
        """
        The Calculate function is where all the calculations are done.
        This function can be called multiple times, and will only recalculate what has changed each time it is called.
        This is where all the calculations are made using all the values that have been set.
        If you subclass this class, you can choose to run these calculations before (or after) your calculations,
        but that assumes you have set all the values that are required for these calculations
        If you choose to subclass this master class, you can also choose to override this method (or not),
        and if you do, do it before or after you call you own version of this method.  If you do, you can also choose
        to call this method from you class, which can effectively run the calculations of the superclass, making all
        thr values available to your methods. but you had better have set all the parameters!
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing, but it does make calculations and set values in the model
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        self.CCUSRevenue.value = [0.0] * model.surfaceplant.plant_lifetime.value
        self.CCUSCashFlow.value = [0.0] * model.surfaceplant.plant_lifetime.value
        self.CCUSCummCashFlow.value = [0.0] * model.surfaceplant.plant_lifetime.value
        self.CarbonThatWouldHaveBeenProducedAnnually.value = [0.0] * model.surfaceplant.plant_lifetime.value
        self.CarbonThatWouldHaveBeenProducedTotal.value = 0.0
        ProjectCapCostPerYear = model.economics.CCap.value / self.ConstructionYears.value

        # Calculate carbon price models
        self.CCUSPrice.value = BuildPricingModel(model.surfaceplant.plant_lifetime.value, self.CCUSEscalationStart.value,
                                                 self.CCUSStartPrice.value, self.CCUSEndPrice.value,
                                                 self.CCUSEscalationStart.value, self.CCUSEscalationRate.value)
        self.CCUSOnElecPrice.value = BuildPricingModel(model.surfaceplant.plant_lifetime.value, 0,
                                                       self.ElecStartPrice.value, self.ElecEndPrice.value,
                                                       self.ElecEscalationStart.value, self.ElecEscalationRate.value)
        self.CCUSOnHeatPrice.value = BuildPricingModel(model.surfaceplant.plant_lifetime.value, 0,
                                                       self.HeatStartPrice.value, self.HeatEndPrice.value,
                                                       self.HeatEscalationStart.value, self.HeatEscalationRate.value)

        # Figure out how much energy is being produced each year, and the amount of carbon that would have been
        # produced if that energy had been made using the grid average carbon production.
        # That then gives us the revenue, since we have a carbon price model
        # We can also get annual cash flow from it.
        self.ProjectCashFlow.value = [0.0] * model.surfaceplant.plant_lifetime.value
        self.ProjectCummCashFlow.value = [0.0] * model.surfaceplant.plant_lifetime.value
        for i in range(0, model.surfaceplant.plant_lifetime.value, 1):
            dElectricalEnergy = 0.0
            ProjectElectricalEnergy = 0.0
            dHeatEnergy = 0.0
            ProjectHeatEnergy = 0.0
            dBothEnergy = 0.0
            if model.surfaceplant.enduse_option.value == EndUseOptions.ELECTRICITY:  # This option has no heat component
                ProjectElectricalEnergy = model.surfaceplant.NetkWhProduced.value[i]
                dElectricalEnergy = model.surfaceplant.NetkWhProduced.value[i]
            elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT:  # has heat component but no electricity
                ProjectHeatEnergy = model.surfaceplant.HeatkWhProduced.value[i]
                dHeatEnergy = model.surfaceplant.HeatkWhProduced.value[i]
            else:  # everything else has a component of both
                ProjectElectricalEnergy = model.surfaceplant.NetkWhProduced.value[i]
                ProjectHeatEnergy = model.surfaceplant.HeatkWhProduced.value[i]
                dElectricalEnergy = model.surfaceplant.NetkWhProduced.value[i]
                dHeatEnergy = model.surfaceplant.HeatkWhProduced.value[i]

            dBothEnergy = dElectricalEnergy + dHeatEnergy
            self.CarbonThatWouldHaveBeenProducedAnnually.value[i] = dBothEnergy * self.CCUSGridCO2.value
            self.CarbonThatWouldHaveBeenProducedTotal.value = self.CarbonThatWouldHaveBeenProducedTotal.value + \
                                                              self.CarbonThatWouldHaveBeenProducedAnnually.value[i]
            self.CCUSRevenue.value[i] = (self.CarbonThatWouldHaveBeenProducedAnnually.value[i] * self.CCUSPrice.value[
                i]) / 1_000_000.0  # CCUS (from both heat and elec) based on total, not net energy; in $M
            self.CCUSCashFlow.value[i] = self.CCUSRevenue.value[i]
            self.ProjectCashFlow.value[i] = (self.CCUSRevenue.value[i] + (((ProjectElectricalEnergy *
                                            self.CCUSOnElecPrice.value[i]) +
                                            (ProjectHeatEnergy * self.CCUSOnHeatPrice.value[i])) / 1_000_000.0) -
                                             model.economics.Coam.value)  # MUSD

        # Calculate the Carbon credit cumulative cash flows
        i = 0
        for val in self.CCUSCashFlow.value:
            if i == 0:
                self.CCUSCummCashFlow.value[0] = val
            else:
                self.CCUSCummCashFlow.value[i] = self.CCUSCummCashFlow.value[i - 1] + val
            i = i + 1

        # now insert the cost of construction into the front of the array that will be used to calculate NPV = the convention is that the upfront CAPEX is negative
        self.ProjectCummCashFlow.value = [0.0] * model.surfaceplant.plant_lifetime.value
        for i in range(0, self.ConstructionYears.value, 1):
            self.ProjectCashFlow.value.insert(0, -1.0 * ProjectCapCostPerYear)
            self.ProjectCummCashFlow.value.insert(0, -1.0 * ProjectCapCostPerYear)

        # Calculate the Project cumulative cash flows and payback period
        i = 0
        for val in self.ProjectCashFlow.value:
            if i == 0:
                self.ProjectCummCashFlow.value[0] = val
            else:
                self.ProjectCummCashFlow.value[i] = self.ProjectCummCashFlow.value[i - 1] + val
            i = i + 1

        # Calculate more financial values using numpy financials
        self.ProjectNPV.value = npf.npv(self.FixedInternalRate.value / 100, self.ProjectCashFlow.value)
        self.ProjectIRR.value = npf.irr(self.ProjectCashFlow.value)
        if math.isnan(self.ProjectIRR.value):
            self.ProjectIRR.value = 0.0
        self.ProjectVIR.value = 1.0 + (self.ProjectNPV.value / model.economics.CCap.value)

        # Calculate MOIC which depends on CumCashFlow
        self.ProjectMOIC.value = self.ProjectCummCashFlow.value[len(self.ProjectCummCashFlow.value) - 1] / (
                model.economics.CCap.value + (model.economics.Coam.value * model.surfaceplant.plant_lifetime.value))

        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def __str__(self):
        return "EconomicsCCUS"

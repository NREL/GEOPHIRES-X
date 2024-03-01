import math
import sys
import os
import numpy as np
import numpy_financial as npf
import geophires_x.Economics as Economics
import geophires_x.Model as Model
from geophires_x.OptionList import EndUseOptions
from geophires_x.Parameter import listParameter, OutputParameter
from geophires_x.Units import *


class EconomicsAddOns(Economics.Economics):
    def __init__(self, model: Model):
        """
        The __init__ function is called automatically when a class is instantiated.
        It initializes the attributes of an object, and sets default values for certain arguments that can be
        overridden by user input.
        The __init__ function is used to set up all the parameters in Economics AddOns.
        Set up all the Parameters that will be predefined by this class using the different types of parameter classes.
        Setting up includes giving it a name, a default value, The Unit Type (length, volume, temperature, etc.)
        and Unit Name of that value, sets it as required (or not), sets allowable range, the error message if
        that range is exceeded, the ToolTip Text, and the name of the class that created it.
        This includes setting up temporary variables that will be available to all the class but noy read in by user,
        or used for Output
        This also includes all Parameters that are calculated and then published using the Printouts function.
        If you choose to subclass this master class, you can do so before or after you create your own parameters.
        If you do, you can also choose to call this method from you class, which will effectively add and
        set all these parameters to your class.
        set up the parameters using the Parameter Constructors (intParameter, floatParameter, strParameter, etc.);
        initialize with their name, default value, and valid range (if int or float).  Optionally, you can specify:
        Required (is it required to run? default value = False), ErrMessage (what GEOPHIRES will report if the value
        provided is invalid, "assume default value (see manual)"), ToolTipText (when there is a GIU, this is the
        text that the user will see, "This is ToolTip Text"), UnitType (the type of units associated with this
        parameter (length, temperature, density, etc), Units.NONE), CurrentUnits (what the units are for this
        parameter (meters, Celsius, gm/cc, etc., Units:NONE), and PreferredUnits (usually equal to CurrentUnits,
        but these are the units that the calculations assume when running, Units.NONE
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """

        model.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')
        super().__init__(model)  # initialize the parent parameters and variables
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = os.path.abspath(__file__)

        self.AddOnNickname = self.ParameterDict[self.AddOnNickname.Name] = listParameter(
            "AddOn Nickname",
            UnitType=Units.NONE,
            Min=0.0,
            Max=1000.0
        )
        self.AddOnCAPEX = self.ParameterDict[self.AddOnCAPEX.Name] = listParameter(
            "AddOn CAPEX",
            Min=0.0,
            Max=1000.0,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.AddOnOPEXPerYear = self.ParameterDict[self.AddOnOPEXPerYear.Name] = listParameter(
            "AddOn OPEX",
            Min=0.0,
            Max=1000.0,
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.AddOnElecGainedPerYear = self.ParameterDict[self.AddOnElecGainedPerYear.Name] = listParameter(
            "AddOn Electricity Gained",
            Min=0.0,
            Max=1000.0,
            UnitType=Units.ENERGYFREQUENCY,
            PreferredUnits=EnergyFrequencyUnit.KWPERYEAR,
            CurrentUnits=EnergyFrequencyUnit.KWPERYEAR
        )
        self.AddOnHeatGainedPerYear = self.ParameterDict[self.AddOnHeatGainedPerYear.Name] = listParameter(
            "AddOn Heat Gained",
            Min=0.0,
            Max=1000.0,
            UnitType=Units.ENERGYFREQUENCY,
            PreferredUnits=EnergyFrequencyUnit.KWPERYEAR,
            CurrentUnits=EnergyFrequencyUnit.KWPERYEAR
        )
        self.AddOnProfitGainedPerYear = self.ParameterDict[self.AddOnProfitGainedPerYear.Name] = listParameter(
            "AddOn Profit Gained",
            Min=0.0,
            Max=1000.0,
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )

        # local variables that need initialization
        # results
        self.AddOnCAPEXTotal = self.OutputParameterDict[self.AddOnCAPEXTotal.Name] = OutputParameter(
            "AddOn CAPEX Total",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.AddOnOPEXTotalPerYear = self.OutputParameterDict[self.AddOnOPEXTotalPerYear.Name] = OutputParameter(
            "AddOn OPEX Total Per Year",
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.AddOnElecGainedTotalPerYear = self.OutputParameterDict[
            self.AddOnElecGainedTotalPerYear.Name] = OutputParameter(
            "AddOn Electricity Gained Total Per Year",
            UnitType=Units.ENERGYFREQUENCY,
            PreferredUnits=EnergyFrequencyUnit.KWPERYEAR,
            CurrentUnits=EnergyFrequencyUnit.KWPERYEAR
        )
        self.AddOnHeatGainedTotalPerYear = self.OutputParameterDict[
            self.AddOnHeatGainedTotalPerYear.Name] = OutputParameter(
            "AddOn Heat Gained Total Per Year",
            UnitType=Units.ENERGYFREQUENCY,
            PreferredUnits=EnergyFrequencyUnit.KWPERYEAR,
            CurrentUnits=EnergyFrequencyUnit.KWPERYEAR
        )
        self.AddOnProfitGainedTotalPerYear = self.OutputParameterDict[
            self.AddOnProfitGainedTotalPerYear.Name] = OutputParameter(
            "AddOn Profit Gained Total Per Year",
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.AddOnPaybackPeriod = self.OutputParameterDict[self.AddOnPaybackPeriod.Name] = OutputParameter(
            "AddOn Payback Period",
            UnitType=Units.TIME,
            PreferredUnits=TimeUnit.YEAR,
            CurrentUnits=TimeUnit.YEAR
        )
        self.AdjustedProjectCAPEX = self.OutputParameterDict[self.AdjustedProjectCAPEX.Name] = OutputParameter(
            "Adjusted CAPEX",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.AdjustedProjectOPEX = self.OutputParameterDict[self.AdjustedProjectOPEX.Name] = OutputParameter(
            "Adjusted OPEX",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.AddOnCashFlow = self.OutputParameterDict[self.AddOnCashFlow.Name] = OutputParameter(
            "Annual AddOn Cash Flow",
            value=[0.0],
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.AddOnCummCashFlow = self.OutputParameterDict[self.AddOnCummCashFlow.Name] = OutputParameter(
            "Cumulative AddOn Cash Flow",
            value=[0.0],
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
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
        self.AddOnElecRevenue = self.OutputParameterDict[self.AddOnElecRevenue.Name] = OutputParameter(
            "Annual Revenue Generated from Electricity Sales",
            value=[0.0],
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.AddOnHeatRevenue = self.OutputParameterDict[self.AddOnHeatRevenue.Name] = OutputParameter(
            "Annual Revenue Generated from Heat Sales",
            value=[0.0],
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.AddOnRevenue = self.OutputParameterDict[self.AddOnRevenue.Name] = OutputParameter(
            "Annual Revenue Generated from AddOns",
            value=[0.0],
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )

        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def read_parameters(self, model: Model) -> None:
        """
        The read_parameters function is called by the model to read in all the parameters that are used for this
        extension.  The user can create as many or as few parameters
        as needed.  Each parameter is created by a call to the InputParameter class, which is defined below, and then
        stored in a dictionary with a name assigned to
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        model.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')
        super().read_parameters(model)  # read the parameters for the parent.

        # Deal with all the parameter values that the user has provided that relate to this extension.
        # super.read_parameter will have already dealt with all the regular values, but anything unusual
        # may not be dealt with, so check.
        # In this case, all the values are array values, and weren't correctly dealt with, so below is where
        # we process them.  The problem is that they have a position number i.e., "AddOnCAPEX 1, AddOnCAPEX 2"
        # appended to them, while the
        # Parameter name is just "AddOnCAPEX" and the position indicates where in the array the user wants it stored.
        # So we need to look for the 5 arrays and position values and insert them into the arrays.

        # this does not deal with units if the user wants to do any conversions...
        # In this case, the read_parameters function didn't deal with the arrays of values we wanted,
        # so we will craft that here.
        for key in model.InputParameters.keys():
            if key.startswith("AddOn Nickname"):
                val = str(model.InputParameters[key].sValue)
                self.AddOnNickname.value.append(val)  # this assumes they put the values in the file in consecutive fashion
            if key.startswith("AddOn CAPEX"):
                val = float(model.InputParameters[key].sValue)
                self.AddOnCAPEX.value.append(val)  # this assumes they put the values in the file in consecutive fashion
            if key.startswith("AddOn OPEX"):
                val = float(model.InputParameters[key].sValue)
                self.AddOnOPEXPerYear.value.append(val)  # this assumes they put the values in the file in consecutive fashion
            if key.startswith("AddOn Electricity Gained"):
                val = float(model.InputParameters[key].sValue)
                self.AddOnElecGainedPerYear.value.append(val)  # this assumes they put the values in the file in consecutive fashion
            if key.startswith("AddOn Heat Gained"):
                val = float(model.InputParameters[key].sValue)
                self.AddOnHeatGainedPerYear.value.append(val)  # this assumes they put the values in the file in consecutive fashion
            if key.startswith("AddOn Profit Gained"):
                val = float(model.InputParameters[key].sValue)
                self.AddOnProfitGainedPerYear.value.append(val)  # this assumes they put the values in the file in consecutive fashion
        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def Calculate(self, model: Model) -> None:
        """
        The Calculate function is where all the calculations are done.
        This function can be called multiple times, and will only recalculate what has changed each time it is called.
        This is where all the calculations are made using all the values that have been set.
        If you subclass this class, you can choose to run these calculations before (or after) your calculations,
        but that assumes you have set all the values that are required for these calculations
        If you choose to subclass this master class, you can also choose to override this method (or not),
        and if you do, do it before or after you call you own version of this method.
        If you do, you can also choose to call this method from you class, which can effectively run the
        calculations of the superclass, making all thr values available to your methods.
        but you had better have set all the parameters!
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing, but it does make calculations and set values in the model
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        # sum all the AddOn values together, so we can treat all AddOns together. If an AddOn slot is not used,
        # it has zeros for the values, so this won't create problems
        if len(self.AddOnCAPEX.value) > 0:
            self.AddOnCAPEXTotal.value = np.sum(self.AddOnCAPEX.value)
        if len(self.AddOnOPEXPerYear.value) > 0:
            self.AddOnOPEXTotalPerYear.value = np.sum(self.AddOnOPEXPerYear.value)
        if len(self.AddOnElecGainedPerYear.value) > 0:
            self.AddOnElecGainedTotalPerYear.value = np.sum(self.AddOnElecGainedPerYear.value)
        if len(self.AddOnHeatGainedPerYear.value) > 0:
            self.AddOnHeatGainedTotalPerYear.value = np.sum(self.AddOnHeatGainedPerYear.value)
        if len(self.AddOnProfitGainedPerYear.value) > 0:
            self.AddOnProfitGainedTotalPerYear.value = np.sum(self.AddOnProfitGainedPerYear.value)

        # The amount of electricity and/or heat have for the project already been calculated in SurfacePlant,
        # so we need to update them here so when they get used in the final economic calculation (below),
        # the new values reflect the addition of the AddOns
        for i in range(0, model.surfaceplant.plant_lifetime.value):
            if model.surfaceplant.enduse_option.value != EndUseOptions.HEAT:  # all these end-use options have an electricity generation component
                model.surfaceplant.TotalkWhProduced.value[i] = model.surfaceplant.TotalkWhProduced.value[i] + self.AddOnElecGainedTotalPerYear.value
                model.surfaceplant.NetkWhProduced.value[i] = model.surfaceplant.NetkWhProduced.value[i] + self.AddOnElecGainedTotalPerYear.value
                if model.surfaceplant.enduse_option.value != EndUseOptions.ELECTRICITY:
                    model.surfaceplant.HeatkWhProduced.value[i] = model.surfaceplant.HeatkWhProduced.value[i] + self.AddOnHeatGainedTotalPerYear.value
            else:
                # all the end-use option of direct-use only components have a heat generation component
                model.surfaceplant.HeatkWhProduced.value[i] = model.surfaceplant.HeatkWhProduced.value[i] + self.AddOnHeatGainedTotalPerYear.value

        # Calculate the adjusted OPEX and CAPEX
        self.AdjustedProjectCAPEX.value = model.economics.CCap.value + self.AddOnCAPEXTotal.value
        self.AdjustedProjectOPEX.value = model.economics.Coam.value + self.AddOnOPEXTotalPerYear.value
        AddOnCapCostPerYear = self.AddOnCAPEXTotal.value / model.surfaceplant.construction_years.value
        ProjectCapCostPerYear = self.AdjustedProjectCAPEX.value / model.surfaceplant.construction_years.value

        # (re)Calculate the revenues
        self.AddOnElecRevenue.value = [0.0] * model.surfaceplant.plant_lifetime.value
        self.AddOnHeatRevenue.value = [0.0] * model.surfaceplant.plant_lifetime.value
        self.AddOnRevenue.value = [0.0] * model.surfaceplant.plant_lifetime.value
        self.AddOnCashFlow.value = [0.0] * model.surfaceplant.plant_lifetime.value
        self.ProjectCashFlow.value = [0.0] * model.surfaceplant.plant_lifetime.value
        for i in range(0, model.surfaceplant.plant_lifetime.value, 1):
            ProjectElectricalEnergy = 0.0
            ProjectHeatEnergy = 0.0
            AddOnElectricalEnergy = 0.0
            AddOnHeatEnergy = 0.0
            if model.surfaceplant.enduse_option.value == EndUseOptions.ELECTRICITY:  # This option has no heat component
                ProjectElectricalEnergy = model.surfaceplant.NetkWhProduced.value[i]
                AddOnElectricalEnergy = self.AddOnElecGainedTotalPerYear.value
            elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT:  # has heat component but no electricity
                ProjectHeatEnergy = model.surfaceplant.HeatkWhProduced.value[i]
                AddOnHeatEnergy = self.AddOnHeatGainedTotalPerYear.value
            else:  # everything else has a component of both
                ProjectElectricalEnergy = model.surfaceplant.NetkWhProduced.value[i]
                ProjectHeatEnergy = model.surfaceplant.HeatkWhProduced.value[i]
                AddOnElectricalEnergy = self.AddOnElecGainedTotalPerYear.value
                AddOnHeatEnergy = self.AddOnHeatGainedTotalPerYear.value

            self.AddOnElecRevenue.value[i] = (AddOnElectricalEnergy * model.economics.ElecPrice.value[
                i]) / 1_000_000.0  # Electricity revenue in MUSD
            self.AddOnHeatRevenue.value[i] = (AddOnHeatEnergy * model.economics.HeatPrice.value[
                i]) / 1_000_000.0  # Heat revenue in MUSD
            self.AddOnRevenue.value[i] = self.AddOnElecRevenue.value[i] + self.AddOnHeatRevenue.value[
                i] + self.AddOnProfitGainedTotalPerYear.value - self.AddOnOPEXTotalPerYear.value
            self.AddOnCashFlow.value[i] = self.AddOnRevenue.value[i]
            self.ProjectCashFlow.value[i] = self.AddOnRevenue.value[i] + (((ProjectElectricalEnergy *
                                            model.economics.ElecPrice.value[i]) + (ProjectHeatEnergy *
                                            model.economics.HeatPrice.value[i])) / 1_000_000.0) - model.economics.Coam.value  # MUSD

        # now insert the cost of construction into the front of the array that will be used to calculate
        # NPV = the convention is that the upfront CAPEX is negative
        for i in range(0, model.surfaceplant.construction_years.value, 1):
            self.AddOnCashFlow.value.insert(0, -1.0 * AddOnCapCostPerYear)
            self.ProjectCashFlow.value.insert(0, -1.0 * ProjectCapCostPerYear)

        # Now calculate a new "NPV", "IRR", "VIR", "Payback Period", and "MOIC"
        # Calculate more financial values using numpy financials
        self.ProjectNPV.value = npf.npv(self.FixedInternalRate.value / 100, self.ProjectCashFlow.value)
        self.ProjectIRR.value = npf.irr(self.ProjectCashFlow.value)
        if math.isnan(self.ProjectIRR.value):
            self.ProjectIRR.value = 0.0
        self.ProjectVIR.value = 1.0 + (self.ProjectNPV.value / self.AdjustedProjectCAPEX.value)

        # calculate Cummcashflows and payback period
        self.ProjectCummCashFlow.value = [0.0] * len(self.ProjectCashFlow.value)
        i = 0
        for val in self.ProjectCashFlow.value:
            if i == 0:
                self.ProjectCummCashFlow.value[i] = val
            else:
                self.ProjectCummCashFlow.value[i] = self.ProjectCummCashFlow.value[i - 1] + val
            i = i + 1
        i = 0
        self.AddOnCummCashFlow.value = [0.0] * len(self.AddOnCashFlow.value)
        for val in self.AddOnCashFlow.value:
            if i == 0:
                self.AddOnCummCashFlow.value[0] = val
            else:
                self.AddOnCummCashFlow.value[i] = self.AddOnCummCashFlow.value[i - 1] + val
                if self.AddOnCummCashFlow.value[i] > 0 >= self.AddOnCummCashFlow.value[
                    i - 1]:  # we just crossed the threshold into positive project cummcashflow, so we can calculate payback period
                    dFullDiff = self.AddOnCummCashFlow.value[i] + math.fabs(self.AddOnCummCashFlow.value[(i - 1)])
                    dPerc = math.fabs(self.AddOnCummCashFlow.value[(i - 1)]) / dFullDiff
                    self.AddOnPaybackPeriod.value = i + dPerc
            i = i + 1

        # Calculate MOIC which depends on CumCashFlow
        self.ProjectMOIC.value = self.ProjectCummCashFlow.value[len(self.ProjectCummCashFlow.value) - 1] / (
                self.AdjustedProjectCAPEX.value + (
                    self.AdjustedProjectOPEX.value * model.surfaceplant.plant_lifetime.value))

        # recalculate LCOE/LCOH
        self.LCOE.value, self.LCOH.value, LCOC = Economics.CalculateLCOELCOHLCOC(self, model)

        model.logger.info(f'complete {str(__class__)}: {sys._getframe().f_code.co_name}')

    def __str__(self):
        return "EconomicsAddOns"

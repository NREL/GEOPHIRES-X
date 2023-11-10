import sys
import os
import Model
from OptionList import WellDrillingCostCorrelation
from Parameter import intParameter, floatParameter, OutputParameter, ReadParameter
from Units import *


class CLEconomics:
    """
     Class to support the closed-loop economic calculations in GEOPHIRES
    """

    def __init__(self, model: Model):
        """
        The __init__ function is called automatically when a class is instantiated.
        It initializes the attributes of an object, and sets default values for certain arguments that can be overridden by user input.
        The __init__ function is used to set up all the parameters in closed loop Economics.
        Sets up all the Parameters that will be predefined by this class using the different types of parameter classes.
        Setting up includes giving it a name, a default value, The Unit Type (length, volume, temperature, etc.)
        and Unit Name of that value, sets it as required (or not), sets allowable range, the error message if that
        range is exceeded, the ToolTip Text, and the name of teh class that created it.
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
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        # These dictionaries contains a list of all the parameters set in this object, stored as "Parameter"
        # and "OutputParameter" Objects.  This will alow us later to access them in a user interface and get that list,
        # along with unit type, preferred units, etc.
        self.ParameterDict = {}
        self.OutputParameterDict = {}

        self.horizontalccwellfixed = self.ParameterDict[self.horizontalccwellfixed.Name] = floatParameter(
            "Horizontal Well Drilling and Completion Capital Cost",
            value=-1.0,
            DefaultValue=-1.0,
            Min=0,
            Max=200,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS,
            Provided=False,
            Valid=False,
            ToolTipText="Horizontal Well Drilling and Completion Capital Cost (per horizontal section)"
        )
        self.horizontalccwelladjfactor = self.ParameterDict[self.horizontalccwelladjfactor.Name] = floatParameter(
            "Horizontal Well Drilling and Completion Capital Cost Adjustment Factor",
            value=1.0,
            DefaultValue=1.0,
            Min=0,
            Max=10,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Provided=False,
            Valid=True,
            ToolTipText="Horizontal Well Drilling and Completion Capital Cost Adjustment Factor"
        )
        self.horizontalwellcorrelation = self.ParameterDict[self.horizontalwellcorrelation.Name] = intParameter(
            "Horizontal Well Drilling Cost Correlation",
            value=WellDrillingCostCorrelation.VERTICAL_SMALL,
            DefaultValue=WellDrillingCostCorrelation.VERTICAL_SMALL,
            AllowableRange=[1, 2, 3, 4, 5],
            UnitType=Units.NONE,
            ErrMessage="assume default horizontal well drilling cost correlation (1)",
            ToolTipText="Select the built-in horizontal well drilling and completion cost correlation. 1: \
            vertical open-hole, small diameter; 2: deviated liner, small diameter; 3: vertical open-hole, \
            large diameter; 4: deviated liner, large diameter; 5: Simple - user specified cost per meter"
        )
        self.Vertical_drilling_cost_per_m = self.ParameterDict[self.Vertical_drilling_cost_per_m.Name] = floatParameter(
            "All-in Vertical Drilling Costs",
            value=1000.0,
            DefaultValue=1000.0,
            Min=0.0,
            Max=10_000.0,
            UnitType=Units.COSTPERDISTANCE,
            PreferredUnits=CostPerDistanceUnit.DOLLARSPERM,
            CurrentUnits=CostPerDistanceUnit.DOLLARSPERM,
            ErrMessage="assume default all-in cost for drill vertical well segment(s) (1000 $/m)",
            ToolTipText="Set user specified all-in cost per meter of vertical drilling, including \
            drilling, casing, cement, insulated insert"
        )
        self.Nonvertical_drilling_cost_per_m = self.ParameterDict[
            self.Nonvertical_drilling_cost_per_m.Name] = floatParameter(
            "All-in Nonvertical Drilling Costs",
            value=1300.0,
            DefaultValue=1300.0,
            Min=0.0,
            Max=15_000.0,
            UnitType=Units.COSTPERDISTANCE,
            PreferredUnits=CostPerDistanceUnit.DOLLARSPERM,
            CurrentUnits=CostPerDistanceUnit.DOLLARSPERM,
            ErrMessage="assume default all-in cost for drill non-vertical well segment(s) (1300 $/m)",
            ToolTipText="Set user specified all-in cost per meter of non-vertical drilling, including \
            drilling, casing, cement, insulated insert"
        )

        # local variable initialization
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = os.path.abspath(__file__)
        self.LCOE = None
        self.LCOH = None

        # results
        self.C1well = self.OutputParameterDict[self.C1well.Name] = OutputParameter(
            Name="Cost of One Horizontal",
            value=-999.9,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.CHorizwell = self.OutputParameterDict[self.CHorizwell.Name] = OutputParameter(
            Name="Cost of All Horizontals",
            value=-999.9,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )

        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def read_parameters(self, model: Model) -> None:
        """
        read_parameters read and update the Economics parameters and handle the special cases
        Deals with all the parameter values that the user has provided.  They should really only provide values
        that they want to change from the default values, but they can provide a value that is already set because
        it is a default value set in __init__.  It will ignore those.
        This also deals with all the special cases that need to be talen care of after a vlaue has been
        read in and checked.
        If you choose to subclass this master class, you can also choose to override this method (or not),
        and if you do, do it before or after you call you own version of this method.  If you do, you can
        also choose to call this method from you class, which can effectively modify all these superclass
        parameters in your class.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        if len(model.InputParameters) > 0:
            # loop through all the parameters that the user wishes to set, looking for parameters that match this object
            for item in self.ParameterDict.items():
                ParameterToModify = item[1]
                key = ParameterToModify.Name.strip()
                if key in model.InputParameters:
                    ParameterReadIn = model.InputParameters[key]
                    # Before we change the parameter, let's assume that the unit preferences will match -
                    # if they don't, the later code will fix this.
                    ParameterToModify.CurrentUnits = ParameterToModify.PreferredUnits
                    ReadParameter(ParameterReadIn, ParameterToModify, model)  # this should handle the non-special cases

                    # handle special cases
                    if ParameterToModify.Name == "Horizontal Well Drilling Cost Correlation":
                        if ParameterReadIn.sValue == '1':
                            ParameterToModify.value = WellDrillingCostCorrelation.VERTICAL_SMALL
                        elif ParameterReadIn.sValue == '2':
                            ParameterToModify.value = WellDrillingCostCorrelation.DEVIATED_SMALL
                        elif ParameterReadIn.sValue == '3':
                            ParameterToModify.value = WellDrillingCostCorrelation.VERTICAL_LARGE
                        elif ParameterReadIn.sValue == '4':
                            ParameterToModify.value = WellDrillingCostCorrelation.DEVIATED_LARGE
                        else:
                            ParameterToModify.value = WellDrillingCostCorrelation.SIMPLE
                    elif ParameterToModify.Name == "Horizontal Well Drilling and Completion Capital Cost Adjustment Factor":
                        if self.horizontalccwellfixed.Valid and ParameterToModify.Valid:
                            print("Warning: Provided horizontal well drilling and completion cost adjustment \
                            factor not considered because valid total horizontal well drilling and completion cost provided.")
                            model.logger.warning("Provided horizontal well drilling and completion cost adjustment \
                            factor not considered because valid total horizontal well drilling and completion cost provided.")
                        elif not self.horizontalccwellfixed.Provided and not self.horizontalccwelladjfactor.Provided:
                            ParameterToModify.value = 1.0
                            print("Warning: No valid horizontal well drilling and completion total cost or \
                            adjustment factor provided. GEOPHIRES will assume default built-in horizontal well drilling\
                             and completion cost correlation with adjustment factor = 1.")
                            model.logger.warning("No valid horizontal well drilling and completion total cost or \
                            adjustment factor provided. GEOPHIRES will assume default built-in horizontal well drilling\
                             and completion cost correlation with adjustment factor = 1.")
                        elif self.horizontalccwellfixed.Provided and not self.horizontalccwellfixed.Valid:
                            print("Warning: Provided horizontal well drilling and completion cost outside of \
                            range 0-1000. GEOPHIRES will assume default built-in horizontal well drilling and \
                            completion cost correlation with adjustment factor = 1.")
                            model.logger.warning("Provided horizontal well drilling and completion cost outside of \
                            range 0-1000. GEOPHIRES will assume default built-in horizontal well horizontal drilling and\
                             completion cost correlation with adjustment factor = 1.")
                            self.horizontalccwelladjfactor.value = 1.0
                        elif not self.horizontalccwellfixed.Provided and self.horizontalccwelladjfactor.Provided and not self.horizontalccwelladjfactor.Valid:
                            print("Warning: Provided horizontal well drilling and completion cost \
                            adjustment factor outside of range 0-10. GEOPHIRES will assume default built-in \
                            horizontal well drilling and completion cost correlation with adjustment factor = 1.")
                            model.logger.warning("Provided horizontal well drilling and completion cost \
                            adjustment factor outside of range 0-10. GEOPHIRES will assume default built-in \
                            well drilling and completion cost correlation with adjustment factor = 1.")
                            self.ccwelladjfactor.value = 1.0
        else:
            model.logger.info("No parameters read because no content provided")
        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def Calculate(self, model: Model) -> None:
        """
        The Calculate function is where all the calculations are done.
        This function can be called multiple times, and will only recalculate what has changed each time it is called.
        This is where all the calculations are made using all the values that have been set.
        If you subclass this class, you can choose to run these calculations before (or after) your calculations,
        but that assumes you have set all the values that are required for these calculations
        If you choose to subclass this master class, you can also choose to override this method (or not),
        and if you do, do it before or after you call you own version of this method.  If you do, you can also
        choose to call this method from you class, which can effectively run the calculations of the superclass,
        making all the values available to your methods. but you had better have set all the parameters!
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing, but it does make calculations and set values in the model
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        # -------------
        # capital costs
        # -------------
        # horizontal well costs. These are calculated whether or not totalcapcostvalid = 1
        if self.horizontalccwellfixed.Valid:  # increment the cost of wells by the cost of the horizontal sections give by user
            self.C1well.value = self.horizontalccwellfixed.value
            self.CHorizwell.value = 1.05 * self.C1well.value * model.clwellbores.numhorizontalsections.value  # 1.05 for 5% indirect cost
            model.economics.Cwell.value = model.economics.Cwell.value + self.CHorizwell.value
        else:
            # well drilling and completion cost in M$/well
            if self.horizontalwellcorrelation.value == WellDrillingCostCorrelation.VERTICAL_SMALL:
                self.C1well.value = (
                                            0.3021 * model.clwellbores.l_pipe.value ** 2 + 584.9112 * model.clwellbores.l_pipe.value + 751368.) * 1E-6
            elif self.horizontalwellcorrelation.value == WellDrillingCostCorrelation.DEVIATED_SMALL:
                self.C1well.value = (
                                            0.2898 * model.clwellbores.l_pipe.value ** 2 + 822.1507 * model.clwellbores.l_pipe.value + 680563.) * 1E-6
            elif self.horizontalwellcorrelation.value == WellDrillingCostCorrelation.VERTICAL_LARGE:
                self.C1well.value = (
                                            0.2818 * model.clwellbores.l_pipe.value ** 2 + 1275.5213 * model.clwellbores.l_pipe.value + 632315.) * 1E-6
            elif self.horizontalwellcorrelation.value == WellDrillingCostCorrelation.DEVIATED_LARGE:
                self.C1well.value = (
                                            0.2553 * model.clwellbores.l_pipe.value ** 2 + 1716.7157 * model.clwellbores.l_pipe.value + 500867.) * 1E-6
            else:
                # MIR MIR MIR
                pass
            if model.clwellbores.HorizontalsCased.value:
                # assumes that cost of casing & cement is 50% of the cost of a well.
                self.C1well.value = self.horizontalccwelladjfactor.value * self.C1well.value * 0.5
            else:
                self.C1well.value = self.horizontalccwelladjfactor.value * self.C1well.value

            self.CHorizwell.value = 1.05 * self.C1well.value * model.clwellbores.numhorizontalsections.value  # 1.05 for 5% indirect costs

            model.economics.Cwell.value = model.economics.Cwell.value + self.CHorizwell.value  # total cost os cost of verticals please cost of horizontal field

        # adjust the CAPEX for the cost of the horizontals
        if not model.economics.totalcapcost.Valid:
            model.economics.CCap.value = model.economics.CCap.value + model.economics.Cwell.value
            # ReCalculate LCOE/LCOH
            self.LCOE.value, self.LCOH.value = model.economics.CalculateLCOELCOH(model)

        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def __str__(self):
        return "CLEconomics"

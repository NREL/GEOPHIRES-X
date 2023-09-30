import math
import sys
import os
import numpy as np
import numpy_financial as npf
import geophires_x.Model as Model
from .OptionList import Configuration, WellDrillingCostCorrelation, EconomicModel, EndUseOptions, PowerPlantType
from .Parameter import intParameter, floatParameter, OutputParameter, ReadParameter, boolParameter
from .Units import *


def BuildPricingModel(plantlifetime: int, StartYear: int, StartPrice: float, EndPrice: float,
                      EscalationStart: int, EscalationRate: float):
    # build the price model array
    Price = [StartPrice] * plantlifetime
    if StartPrice == EndPrice:
        return Price
    for i in range(StartYear, plantlifetime, 1):
        if i >= EscalationStart:
            Price[i] = Price[i] + ((i - EscalationStart) * EscalationRate)
        if Price[i] > EndPrice:
            Price[i] = EndPrice
    return Price


def CalculateRevenue(plantlifetime: int, ConstructionYears: int, CAPEX: float, OPEX: float, Energy, Price):
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
        CashFlow[i] = ((Energy[i - ConstructionYears] * Price[
            i - ConstructionYears]) / 1_000_000.0) - OPEX  # Revenue/yr in MUSD

    # Calculate the cumulative revenue, skipping the first year because it is cumulative
    for i in range(1, plantlifetime + ConstructionYears, 1):
        CummCashFlow[i] = CummCashFlow[i - 1] + CashFlow[i]
    return CashFlow, CummCashFlow


def CalculateFinancialPerformance(plantlifetime: int, FixedInternalRate: float, TotalRevenue, TotalCummRevenue,
                                  CAPEX: float, OPEX: float):
    # Calculate financial performance values using numpy financials
    NPV = npf.npv(FixedInternalRate / 100, TotalRevenue)
    IRR = npf.irr(TotalRevenue)
    if math.isnan(IRR):
        IRR = 0.0
    VIR = 1.0 + (NPV / CAPEX)

    # Calculate MOIC which depends on CumCashFlow
    MOIC = TotalCummRevenue[len(TotalCummRevenue) - 1] / (CAPEX + (OPEX * plantlifetime))

    return NPV, IRR, VIR, MOIC


def CalculateLCOELCOH(self, model: Model) -> tuple:
    LCOE = LCOH = 0.0

    # Calculate LCOE/LCOH
    if self.econmodel.value == EconomicModel.FCR:
        if model.surfaceplant.enduseoption.value == EndUseOptions.ELECTRICITY:
            LCOE = (self.FCR.value*(1+self.inflrateconstruction.value)*self.CCap.value + self.Coam.value) / \
                   np.average(model.surfaceplant.NetkWhProduced.value)*1E8  # cents/kWh
        elif model.surfaceplant.enduseoption.value == EndUseOptions.HEAT:
            self.averageannualpumpingcosts.value = np.average(model.surfaceplant.PumpingkWh.value) * \
                                                   model.surfaceplant.elecprice.value/1E6  # M$/year
            LCOH = (self.FCR.value*(1+self.inflrateconstruction.value)*self.CCap.value + self.Coam.value +
                    self.averageannualpumpingcosts.value)/np.average(model.surfaceplant.HeatkWhProduced.value)*1E8  # cents/kWh
            LCOH = LCOH * 2.931  # $/Million Btu
        elif model.surfaceplant.enduseoption.value not in [EndUseOptions.ELECTRICITY, EndUseOptions.HEAT]:  # cogeneration
            # heat sales is additional income revenue stream
            if model.surfaceplant.enduseoption.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT,
                                                         EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                         EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT]:
                averageannualheatincome = np.average(self.HeatkWhProduced.value)*self.heatprice.value/1E6  # M$/year ASSUMING heatprice IS IN $/KWH FOR HEAT SALES
                LCOE = (self.FCR.value*(1+self.inflrateconstruction.value)*self.CCap.value + self.Coam.value - averageannualheatincome)/np.average(model.surfaceplant.NetkWhProduced.value)*1E8  # cents/kWh
            elif model.surfaceplant.enduseoption.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICTY,
                                                           EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICTY,
                                                           EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICTY]:  # electricity sales is additional income revenue stream
                averageannualelectricityincome = np.average(model.surfaceplant.NetkWhProduced.value)*model.surfaceplant.elecprice.value/1E6  # M$/year
                LCOH = (self.CCap.value + self.Coam.value - averageannualelectricityincome)/np.average(model.surfaceplant.HeatkWhProduced.value)*1E8  # cents/kWh
                LCOH = LCOH * 2.931  # $/MMBTU
    elif self.econmodel.value == EconomicModel.STANDARDIZED_LEVELIZED_COST:
        discountvector = 1./np.power(1+self.discountrate.value, np.linspace(0, model.surfaceplant.plantlifetime.value-1, model.surfaceplant.plantlifetime.value))
        if model.surfaceplant.enduseoption.value == EndUseOptions.ELECTRICITY:
            LCOE = ((1+self.inflrateconstruction.value)*self.CCap.value + np.sum(self.Coam.value*discountvector))/np.sum(model.surfaceplant.NetkWhProduced.value*discountvector)*1E8  # cents/kWh
        elif model.surfaceplant.enduseoption.value == EndUseOptions.HEAT:
            self.averageannualpumpingcosts.value = np.average(model.surfaceplant.PumpingkWh.value)*model.surfaceplant.elecprice.value/1E6  # M$/year
            LCOH = ((1+self.inflrateconstruction.value)*self.CCap.value + np.sum((self.Coam.value+model.surfaceplant.PumpingkWh.value*model.surfaceplant.elecprice.value/1E6)*discountvector))/np.sum(model.surfaceplant.HeatkWhProduced.value*discountvector)*1E8  # cents/kWh
            LCOH = LCOH * 2.931  # $/MMBTU
        elif model.surfaceplant.enduseoption.value not in [EndUseOptions.ELECTRICITY, EndUseOptions.HEAT]:
            if model.surfaceplant.enduseoption.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT,
                                                         EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                         EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT]:  # heat sales is additional income revenue stream
                annualheatincome = model.surfaceplant.HeatkWhProduced.value*model.surfaceplant.heatprice.value/1E6  # M$/year ASSUMING heatprice IS IN $/KWH FOR HEAT SALES
                LCOE = ((1+self.inflrateconstruction.value)*self.CCap.value + np.sum((self.Coam.value-annualheatincome)*discountvector))/np.sum(model.surfaceplant.NetkWhProduced.value*discountvector)*1E8  # cents/kWh
            elif model.surfaceplant.enduseoption.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICTY,
                                                           EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICTY,
                                                           EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICTY]:  # electricity sales is additional income revenue stream
                annualelectricityincome = model.surfaceplant.NetkWhProduced.value*self.elecprice.value/1E6  # M$/year
                LCOH = ((1+self.inflrateconstruction.value)*self.CCap.value + np.sum((self.Coam.value-annualelectricityincome)*discountvector))/np.sum(model.surfaceplant.HeatkWhProduced.value*discountvector)*1E8  # cents/kWh
                LCOH = LCOH*2.931  # $/MMBTU
    elif self.econmodel.value == EconomicModel.BICYCLE:
        iave = self.FIB.value*self.BIR.value*(1-self.CTR.value) + (1-self.FIB.value)*self.EIR.value  # average return on investment (tax and inflation adjusted)
        CRF = iave/(1-np.power(1+iave, -model.surfaceplant.plantlifetime.value))  # capital recovery factor
        inflationvector = np.power(1+self.RINFL.value, np.linspace(1, model.surfaceplant.plantlifetime.value, model.surfaceplant.plantlifetime.value))
        discountvector = 1./np.power(1+iave, np.linspace(1, model.surfaceplant.plantlifetime.value, model.surfaceplant.plantlifetime.value))
        NPVcap = np.sum((1+self.inflrateconstruction.value)*self.CCap.value*CRF*discountvector)
        NPVfc = np.sum((1+self.inflrateconstruction.value)*self.CCap.value*self.PTR.value*inflationvector*discountvector)
        NPVit = np.sum(self.CTR.value/(1-self.CTR.value)*((1+self.inflrateconstruction.value)*self.CCap.value*CRF-self.CCap.value/model.surfaceplant.plantlifetime.value)*discountvector)
        NPVitc = (1+self.inflrateconstruction.value)*self.CCap.value*self.RITC.value/(1-self.CTR.value)
        if model.surfaceplant.enduseoption.value == EndUseOptions.ELECTRICITY:
            NPVoandm = np.sum(self.Coam.value*inflationvector*discountvector)
            NPVgrt = self.GTR.value/(1-self.GTR.value)*(NPVcap + NPVoandm + NPVfc + NPVit - NPVitc)
            LCOE = (NPVcap + NPVoandm + NPVfc + NPVit + NPVgrt - NPVitc)/np.sum(model.surfaceplant.NetkWhProduced.value*inflationvector*discountvector)*1E8
        elif model.surfaceplant.enduseoption.value == EndUseOptions.HEAT:
            PumpingCosts = model.surfaceplant.PumpingkWh.value*model.surfaceplant.elecprice.value/1E6
            self.averageannualpumpingcosts.value = np.average(model.surfaceplant.PumpingkWh.value)*model.surfaceplant.elecprice.value/1E6  # M$/year
            NPVoandm = np.sum((self.Coam.value+PumpingCosts)*inflationvector*discountvector)
            NPVgrt = self.GTR.value/(1-self.GTR.value)*(NPVcap + NPVoandm + NPVfc + NPVit - NPVitc)
            LCOH = (NPVcap + NPVoandm + NPVfc + NPVit + NPVgrt - NPVitc)/np.sum(model.surfaceplant.HeatkWhProduced.value*inflationvector*discountvector)*1E8
            LCOH = LCOH*2.931  # $/MMBTU
        elif model.surfaceplant.enduseoption.value not in [EndUseOptions.ELECTRICITY, EndUseOptions.HEAT]:
            if model.surfaceplant.enduseoption.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT,
                                                         EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                         EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT]:  # heat sales is additional income revenue stream
                annualheatincome = model.surfaceplant.HeatkWhProduced.value*model.surfaceplant.heatprice.value/1E6  # M$/year ASSUMING ELECPRICE IS IN $/KWH FOR HEAT SALES
                NPVoandm = np.sum(self.Coam.value*inflationvector*discountvector)
                NPVgrt = self.GTR.value/(1-self.GTR.value)*(NPVcap + NPVoandm + NPVfc + NPVit - NPVitc)
                LCOE = (NPVcap + NPVoandm + NPVfc + NPVit + NPVgrt - NPVitc - np.sum(annualheatincome*inflationvector*discountvector))/np.sum(model.surfaceplant.NetkWhProduced.value*inflationvector*discountvector)*1E8
            elif model.surfaceplant.enduseoption.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICTY,
                                                            EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICTY,
                                                            EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICTY]:  # electricity sales is additional income revenue stream
                annualelectricityincome = model.surfaceplant.NetkWhProduced.value*model.surfaceplant.elecprice.value/1E6  # M$/year
                NPVoandm = np.sum(self.Coam.value*inflationvector*discountvector)
                NPVgrt = self.GTR.value/(1-self.GTR.value)*(NPVcap + NPVoandm + NPVfc + NPVit - NPVitc)
                LCOH = (NPVcap + NPVoandm + NPVfc + NPVit + NPVgrt - NPVitc - np.sum(annualelectricityincome*inflationvector*discountvector))/np.sum(model.surfaceplant.HeatkWhProduced.value*inflationvector*discountvector)*1E8
                LCOH = self.LCOELCOHCombined.value*2.931  # $/MMBTU
    return LCOE, LCOH


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

        :param self: Store data that will be used by the class
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: None
        :doc-author: Malcolm Ross
        """

        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

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
            AllowableRange=[1, 2, 3, 4],
            Required=True,
            ErrMessage="assume default economic model (2)",
            ToolTipText="Specify the economic model to calculate the levelized cost of energy." +
            " 1: Fixed Charge Rate Model, 2: Standard Levelized Cost Model, 3: BICYCLE Levelized Cost Model, 4: CLGS"
        )
        self.ccstimfixed = self.ParameterDict[self.ccstimfixed.Name] = floatParameter(
            "Reservoir Stimulation Capital Cost",
            value=-1.0,
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
            value=1.0,
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
            value=-1.0,
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
            value=1.0,
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
            ToolTipText="Well Drilling and Completion Capital Cost"
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
            ToolTipText="Well Drilling and Completion Capital Cost Adjustment Factor"
        )
        self.oamwellfixed = self.ParameterDict[self.oamwellfixed.Name] = floatParameter(
            "Wellfield O&M Cost",
            value=-1.0,
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
            value=1.0,
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
            value=-1.0,
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
            value=1.0,
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
            value=-1.0,
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
            value=1.0,
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
            value=-1.0,
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
            value=1.0,
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
            value=-1.0,
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
            value=1.0,
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
            value=-1.0,
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
            value=-1.0,
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
            value=4,
            DefaultValue=4,
            AllowableRange=list(range(1, 101, 1)),
            UnitType=Units.NONE,
            Required=True,
            ErrMessage="assume default number of time steps per year (4)",
            ToolTipText="Number of internal simulation time steps per year"
        )
        self.FCR = self.ParameterDict[self.FCR.Name] = floatParameter(
            "Fixed Charge Rate",
            value=0.1,
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
            value=0.07,
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
            value=0.5,
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
            value=0.05,
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
            value=0.1,
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
            value=0.02,
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
            value=0.02,
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
            value=0.02,
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
            value=0.0,
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
            value=0.0,
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
            value=0.0,
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
            value=WellDrillingCostCorrelation.VERTICAL_SMALL,
            DefaultValue=WellDrillingCostCorrelation.VERTICAL_SMALL,
            AllowableRange=[1, 2, 3, 4, 5],
            UnitType=Units.NONE,
            ErrMessage="assume default well drilling cost correlation (1)",
            ToolTipText="Select the built-in horizontal well drilling and completion cost correlation." +
            " 1: vertical open-hole, small diameter; 2: deviated liner, small diameter;" +
            " 3: vertical open-hole, large diameter; 4: deviated liner, large diameter;" +
            " 5: Simple - user specified cost per meter"
        )
        self.DoAddOnCalculations = self.ParameterDict[self.DoAddOnCalculations.Name] = boolParameter(
            "Do AddOn Calculations",
            value=False,
            DefaultValue=False,
            UnitType=Units.NONE,
            Required=False,
            ErrMessage="assume default: no economics calculations",
            ToolTipText="Set to true if you want the add-on economics calculations to be made"
        )
        self.DoCCUSCalculations = self.ParameterDict[self.DoCCUSCalculations.Name] = boolParameter(
            "Do CCUS Calculations",
            value=False,
            DefaultValue=False,
            UnitType=Units.NONE,
            Required=False,
            ErrMessage="assume default: no CCUS calculations",
            ToolTipText="Set to true if you want the CCUS economics calculations to be made"
        )
        self.DoSDACGTCalculations = self.ParameterDict[self.DoSDACGTCalculations.Name] = boolParameter(
            "Do S-DAC-GT Calculations",
            value=False,
            DefaultValue=False,
            UnitType=Units.NONE,
            Required=False,
            ErrMessage="assume default: no S-DAC-GT calculations",
            ToolTipText="Set to true if you want the S-DAC-GT economics calculations to be made"
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
            ToolTipText="Set user specified all-in cost per meter of vertical drilling," +
            " including drilling, casing, cement, insulated insert"
        )
        self.Nonvertical_drilling_cost_per_m = self.ParameterDict[self.Nonvertical_drilling_cost_per_m.Name] = floatParameter(
            "All-in Nonvertical Drilling Costs",
            value=1300.0,
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
        self.ElecPrice = self.OutputParameterDict[self.ElecPrice.Name] = OutputParameter(
            "Electricity Sale Price Model",
            value=[0.055],
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.CENTSSPERKWH,
            CurrentUnits=EnergyCostUnit.CENTSSPERKWH
        )
        self.HeatPrice = self.OutputParameterDict[self.HeatPrice.Name] = OutputParameter(
            "Heat Sale Price Model",
            value=[0.025],
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.CENTSSPERKWH,
            CurrentUnits=EnergyCostUnit.CENTSSPERKWH
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

        self.AnnualLicenseEtc = self.ParameterDict[self.AnnualLicenseEtc.Name] = floatParameter(
            "Annual License Fees Etc",
            value=0.0,
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
            value=0.0,
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

    # local variable initialization
        self.Claborcorrelation = 0.0
        self.Cpumps = 0.0
        self.annualelectricityincome = 0.0
        self.annualheatincome = 0.0
        self.InputFile = ""
        self.Cplantcorrelation = 0.0
        self.C1well = 0.0
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = os.path.abspath(__file__)

        # results
        self.LCOE = self.OutputParameterDict[self.LCOE.Name] = OutputParameter(
            Name="LCOE",
            value=0.0,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.CENTSSPERKWH,
            CurrentUnits=EnergyCostUnit.CENTSSPERKWH
        )
        self.LCOH = self.OutputParameterDict[self.LCOH.Name] = OutputParameter(
            Name="LCOH",
            value=0.0,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERMMBTU,
            CurrentUnits=EnergyCostUnit.DOLLARSPERMMBTU
        )    # $/MMBTU
        self.Cstim = self.OutputParameterDict[self.Cstim.Name] = OutputParameter(
            Name="O&M Surface Plant costs",
            value=-999.9,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.Cexpl = self.OutputParameterDict[self.Cexpl.Name] = OutputParameter(
            Name="Exploration cost",
            value=-999.9,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.Cwell = self.OutputParameterDict[self.Cwell.Name] = OutputParameter(
            Name="Wellfield cost",
            value=-999.9,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.Coamwell = self.OutputParameterDict[self.Coamwell.Name] = OutputParameter(
            Name="O&M Wellfield cost",
            value=-999.9,
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.Cplant = self.OutputParameterDict[self.Cplant.Name] = OutputParameter(
            Name="Surface Plant cost",
            value=-999.9,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.Coamplant = self.OutputParameterDict[self.Coamplant.Name] = OutputParameter(
            Name="O&M Surface Plant costs",
            value=-999.9,
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.Cgath = self.OutputParameterDict[self.Cgath.Name] = OutputParameter(
            Name="Field gathering system cost",
            value=-999.9,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.Cpiping = self.OutputParameterDict[self.Cpiping.Name] = OutputParameter(
            Name="Transmission pipeline costs",
            value=-999.9,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.Coamwater = self.OutputParameterDict[self.Coamwater.Name] = OutputParameter(
            Name="O&M Make-up Water costs",
            value=-999.9,
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.CCap = self.OutputParameterDict[self.CCap.Name] = OutputParameter(
            Name="Total Capital Cost",
            value=-999.9,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.Coam = self.OutputParameterDict[self.Coam.Name] = OutputParameter(
            Name="Total O&M Cost",
            value=-999.9,
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.averageannualpumpingcosts = self.OutputParameterDict[self.averageannualpumpingcosts.Name] = OutputParameter(
            Name="Average Annual Pumping Costs",
            value=-0.0,
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )

        self.ElecRevenue = self.OutputParameterDict[self.ElecRevenue.Name] = OutputParameter(
            Name="Annual Revenue from Electricity Production",
            value=[0.0],
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.ElecCummRevenue = self.OutputParameterDict[self.ElecCummRevenue.Name] = OutputParameter(
            Name="Cumulative Revenue from Electricity Production",
            value=[0.0],
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.HeatRevenue = self.OutputParameterDict[self.HeatRevenue.Name] = OutputParameter(
            Name="Annual Revenue from Heat Production",
            value=[0.0],
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.HeatCummRevenue = self.OutputParameterDict[self.HeatCummRevenue.Name] = OutputParameter(
            Name="Cumulative Revenue from Electricity Production",
            value=[0.0],
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.TotalRevenue = self.OutputParameterDict[self.TotalRevenue.Name] = OutputParameter(
            Name="Annual Revenue from Project",
            value=[0.0],
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.MDOLLARSPERYEAR
        )
        self.TotalCummRevenue = self.OutputParameterDict[self.TotalCummRevenue.Name] = OutputParameter(
            Name="Cumulative Revenue from Project",
            value=[0.0],
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.ProjectNPV = self.OutputParameterDict[self.ProjectNPV.Name] = OutputParameter(
            "Project Net Present Value",
            value=0.0,
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.MDOLLARS,
            CurrentUnits=CurrencyUnit.MDOLLARS
        )
        self.ProjectIRR = self.OutputParameterDict[self.ProjectIRR.Name] = OutputParameter(
            "Project Internal Rate of Return",
            value=0.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.PERCENT,
            CurrentUnits=PercentUnit.PERCENT
        )
        self.ProjectVIR = self.OutputParameterDict[self.ProjectVIR.Name] = OutputParameter(
            "Project Value Investment Ratio",
            value=0.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH
        )
        self.ProjectMOIC = self.OutputParameterDict[self.ProjectMOIC.Name] = OutputParameter(
            "Project Multiple of Invested Capital",
            value=0.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH
        )

        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def read_parameters(self, model: Model) -> None:
        """
        read_parameters read and update the Economics parameters and handle the special cases

        Args:
            model (Model): The container class of the application, giving access to everything else, including the logger
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
                            self.wellcorrelation.value = WellDrillingCostCorrelation.DEVIATED_SMALL
                        elif ParameterReadIn.sValue == '3':
                            self.wellcorrelation.value = WellDrillingCostCorrelation.VERTICAL_LARGE
                        elif ParameterReadIn.sValue == '4':
                            self.wellcorrelation.value = WellDrillingCostCorrelation.DEVIATED_LARGE
                        else:
                            self.wellcorrelation.value = WellDrillingCostCorrelation.SIMPLE
                    elif ParameterToModify.Name == "Reservoir Stimulation Capital Cost Adjustment Factor":
                        if self.ccstimfixed.Valid and ParameterToModify.Valid:
                            print("Warning: Provided reservoir stimulation cost adjustment factor not considered" +
                            " because valid total reservoir stimulation cost provided.")
                            model.logger.warning("Provided reservoir stimulation cost adjustment factor not considered" +
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
                            model.logger.warning("Provided reservoir stimulation cost outside of range 0-100. GEOPHIRES" +
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
                        if self.ccwellfixed.Valid and ParameterToModify.Valid:
                            print("Warning: Provided well drilling and completion cost adjustment factor not" +
                            " considered because valid total well drilling and completion cost provided.")
                            model.logger.warning("Provided well drilling and completion cost adjustment factor not" +
                            " considered because valid total well drilling and completion cost provided.")
                        elif not self.ccwellfixed.Provided and not self.ccwelladjfactor.Provided:
                            ParameterToModify.value = 1.0
                            print("Warning: No valid well drilling and completion total cost or adjustment" +
                            " factor provided. GEOPHIRES will assume default built-in well drilling and" +
                            " completion cost correlation with adjustment factor = 1.")
                            model.logger.warning("No valid well drilling and completion total cost or adjustment factor" +
                            " provided. GEOPHIRES will assume default built-in well drilling and completion cost" +
                            " correlation with adjustment factor = 1.")
                        elif self.ccwellfixed.Provided and not self.ccwellfixed.Valid:
                            print("Warning: Provided well drilling and completion cost outside of range 0-1000." +
                            " GEOPHIRES will assume default built-in well drilling and completion cost correlation" +
                            " with adjustment factor = 1.")
                            model.logger.warning("Provided well drilling and completion cost outside of range 0-1000." +
                            " GEOPHIRES will assume default built-in well drilling and completion cost correlation with" +
                            " adjustment factor = 1.")
                            self.ccwelladjfactor.value = 1.0
                        elif not self.ccwellfixed.Provided and self.ccwelladjfactor.Provided and not self.ccwelladjfactor.Valid:
                            print("Warning: Provided well drilling and completion cost adjustment factor outside" +
                            " of range 0-10. GEOPHIRES will assume default built-in well drilling and completion" +
                            " cost correlation with adjustment factor = 1.")
                            model.logger.warning("Provided well drilling and completion cost adjustment factor outside" +
                            " of range 0-10. GEOPHIRES will assume default built-in well drilling and completion" +
                            " cost correlation with adjustment factor = 1.")
                            self.ccwelladjfactor.value = 1.0
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
                                model.logger.warning("Provided field gathering system cost not considered because valid" +
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
                                model.logger.warning("Provided surface plant O&M cost adjustment factor not considered" +
                                " because valid total annual O&M cost provided.")
                        else:
                            if self.oamplantfixed.Valid and ParameterToModify.Valid:
                                print("Warning: Provided surface plant O&M cost adjustment factor not considered" +
                                " because valid total surface plant O&M cost provided.")
                                model.logger.warning("Provided surface plant O&M cost adjustment factor not considered" +
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
            if key.startswith("CCUS"):
                self.DoCCUSCalculations.value = True
                break
        for key in model.InputParameters.keys():
            if key.startswith("S-DAC-GT"):
                self.DoSDACGTCalculations.value = True
                break

        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def Calculate(self, model: Model) -> None:
        """
        The Calculate function is where all the calculations are done.
        This function can be called multiple times, and will only recalculate what has changed each time it is called.
        :param self: Access variables that belongs to the class
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: Nothing, but it does make calculations and set values in the model
        :doc-author: Malcolm Ross
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

        # capital costs
        # well costs (using GeoVision drilling correlations). These are calculated whether totalcapcostvalid = 1
        # start with the cost of one well
        if self.ccwellfixed.Valid:
            self.C1well = self.ccwellfixed.value
            self.Cwell.value = self.C1well*(model.wellbores.nprod.value+model.wellbores.ninj.value)
        else:
            # if depth is > 7000 m, we don't have a correlation for it, so we must use the SIMPLE logic
            checkdepth = model.reserv.depth.value
            if model.reserv.depth.CurrentUnits != LengthUnit.METERS:
                checkdepth = checkdepth*1000.0
            if (checkdepth > 7000.0 or checkdepth < 500) and not self.wellcorrelation.value == WellDrillingCostCorrelation.SIMPLE:
                print("Warning: simple user-specified cost per meter used for drilling depth < 500 or > 7000 m")
                model.logger.warning("Warning: simple user-specified cost per meter used for drilling depth < 500 or > 7000 m")
                self.wellcorrelation.value = WellDrillingCostCorrelation.SIMPLE
            if self.wellcorrelation.value == WellDrillingCostCorrelation.SIMPLE:  # use SIMPLE approach
                if hasattr(model.wellbores, 'Configuration'):
                    if model.wellbores.Configuration.value == Configuration.ULOOP:
                        if hasattr(model.reserv, 'InputDepth'):  # must be using simple cylindrical model, which has an Input and Output Depth
                            self.C1well = ((self.Vertical_drilling_cost_per_m.value *
                                            (model.reserv.InputDepth.value*1000.0)) +
                                           (self.Vertical_drilling_cost_per_m.value * (model.reserv.OutputDepth.value*1000.0)) +
                                           (self.Nonvertical_drilling_cost_per_m.value * model.wellbores.Nonvertical_length.value))*1E-6
                        else:
                            if hasattr(model.wellbores, 'Nonvertical_length'):
                                self.C1well = ((2 * self.Vertical_drilling_cost_per_m.value *
                                                (model.reserv.depth.value*1000.0)) +
                                               (self.Nonvertical_drilling_cost_per_m.value * model.wellbores.Nonvertical_length.value))*1E-6
                            else:
                                self.C1well = (2 * self.Vertical_drilling_cost_per_m.value * (model.reserv.depth.value * 1000.0)) * 1E-6
                    else:  # Coaxial
                        self.C1well = ((self.Vertical_drilling_cost_per_m.value * (model.reserv.depth.value*1000.0)) +
                                       (self.Nonvertical_drilling_cost_per_m.value * model.wellbores.Nonvertical_length.value))*1E-6

            elif self.wellcorrelation.value == WellDrillingCostCorrelation.VERTICAL_SMALL:
                self.C1well = (0.3021*checkdepth**2 + 584.9112*checkdepth + 751368.)*1E-6  # well drilling and completion cost in M$/well
            elif self.wellcorrelation.value == WellDrillingCostCorrelation.DEVIATED_SMALL:
                self.C1well = (0.2898*checkdepth**2 + 822.1507*checkdepth + 680563.)*1E-6
            elif self.wellcorrelation.value == WellDrillingCostCorrelation.VERTICAL_LARGE:
                self.C1well = (0.2818*checkdepth**2 + 1275.5213*checkdepth + 632315.)*1E-6
            elif self.wellcorrelation.value == WellDrillingCostCorrelation.DEVIATED_LARGE:
                self.C1well = (0.2553*checkdepth**2 + 1716.7157*checkdepth + 500867.)*1E-6

            # account for adjustment factor
            self.C1well = self.ccwelladjfactor.value*self.C1well

            # cost of the well field
            self.Cwell.value = 1.05*self.C1well*(model.wellbores.nprod.value+model.wellbores.ninj.value)  # 1.05 for 5% indirect costs

        # reservoir stimulation costs (M$/injection well). These are calculated whether totalcapcost.Valid = 1
        if self.ccstimfixed.Valid:
            self.Cstim.value = self.ccstimfixed.value
        else:
            self.Cstim.value = 1.05*1.15*self.ccstimadjfactor.value*model.wellbores.ninj.value*1.25  # 1.15 for 15% contingency and 1.05 for 5% indirect costs

        # field gathering system costs (M$)
        if self.ccgathfixed.Valid:
            self.Cgath.value = self.ccgathfixed.value
        else:
            self.Cgath.value = self.ccgathadjfactor.value*50-6*np.max(model.surfaceplant.HeatExtracted.value)*1000.  # (GEOPHIRES v1 correlation)
            if model.wellbores.impedancemodelused.value:
                pumphp = np.max(model.wellbores.PumpingPower.value)*1341
                numberofpumps = np.ceil(pumphp/2000)  # pump can be maximum 2,000 hp
                if numberofpumps == 0:
                    self.Cpumps = 0.0
                else:
                    pumphpcorrected = pumphp/numberofpumps
                    self.Cpumps = numberofpumps*1.5*((1750 * pumphpcorrected ** 0.7) * 3 * pumphpcorrected ** (-0.11))
            else:
                if model.wellbores.productionwellpumping.value:
                    prodpumphp = np.max(model.wellbores.PumpingPowerProd.value)/model.wellbores.nprod.value*1341
                    Cpumpsprod = model.wellbores.nprod.value*1.5*(1750 * prodpumphp ** 0.7 + 5750 *
                                prodpumphp ** 0.2 + 10000 + np.max(model.wellbores.pumpdepth.value) * 50 * 3.281)  # see page 46 in user's manual assuming rental of rig for 1 day.
                else:
                    Cpumpsprod = 0

                injpumphp = np.max(model.wellbores.PumpingPowerInj.value)*1341
                numberofinjpumps = np.ceil(injpumphp/2000)  # pump can be maximum 2,000 hp
                if numberofinjpumps == 0:
                    Cpumpsinj = 0
                else:
                    injpumphpcorrected = injpumphp/numberofinjpumps
                    Cpumpsinj = numberofinjpumps * 1.5 * (1750 * injpumphpcorrected ** 0.7) * 3 * injpumphpcorrected ** (-0.11)
                self.Cpumps = Cpumpsinj + Cpumpsprod

        # Based on GETEM 2016 #1.15 for 15% contingency and 1.12 for 12% indirect costs
        self.Cgath.value = 1.15*self.ccgathadjfactor.value*1.12*((model.wellbores.nprod.value+model.wellbores.ninj.value)*750*500. + self.Cpumps)/1E6

        # plant costs
        if model.surfaceplant.enduseoption.value == EndUseOptions.HEAT:  # direct-use
            if self.ccplantfixed.Valid:
                self.Cplant.value = self.ccplantfixed.value
            else:
                self.Cplant.value = 1.12*1.15*self.ccplantadjfactor.value*250E-6*np.max(model.surfaceplant.HeatExtracted.value)*1000.  # 1.15 for 15% contingency and 1.12 for 12% indirect costs
        else:  # all other options have power plant
            if model.surfaceplant.pptype.value == PowerPlantType.SUB_CRITICAL_ORC:
                MaxProducedTemperature = np.max(model.surfaceplant.TenteringPP.value)
                if MaxProducedTemperature < 150.:
                    C3 = -1.458333E-3
                    C2 = 7.6875E-1
                    C1 = -1.347917E2
                    C0 = 1.0075E4
                    CCAPP1 = C3*MaxProducedTemperature**3 + C2*MaxProducedTemperature**2 + C1*MaxProducedTemperature + C0
                else:
                    CCAPP1 = 2231 - 2*(MaxProducedTemperature-150.)
                x = np.max(model.surfaceplant.ElectricityProduced.value)
                y = np.max(model.surfaceplant.ElectricityProduced.value)
                if y == 0.0:
                    y = 15.0
                z = math.pow(y/15., -0.06)
                self.Cplantcorrelation = CCAPP1*z*x*1000./1E6

            elif model.surfaceplant.pptype.value == PowerPlantType.SUPER_CRITICAL_ORC:
                MaxProducedTemperature = np.max(model.surfaceplant.TenteringPP.value)
                if MaxProducedTemperature < 150.:
                    C3 = -1.458333E-3
                    C2 = 7.6875E-1
                    C1 = -1.347917E2
                    C0 = 1.0075E4
                    CCAPP1 = C3*MaxProducedTemperature**3 + C2*MaxProducedTemperature**2 + C1*MaxProducedTemperature + C0
                else:
                    CCAPP1 = 2231 - 2*(MaxProducedTemperature-150.)
                # factor 1.1 to make supercritical 10% more expansive than subcritical
                self.Cplantcorrelation = 1.1*CCAPP1*math.pow(np.max(model.surfaceplant.ElectricityProduced.value)/15., -0.06)*np.max(model.surfaceplant.ElectricityProduced.value)*1000./1E6

            elif model.surfaceplant.pptype.value == PowerPlantType.SINGLE_FLASH:
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
                CCAPPLL = C2*maxProdTemp**2 + C1*maxProdTemp + C0
                CCAPPRL = D2*maxProdTemp**2 + D1*maxProdTemp + D0
                b = math.log(CCAPPRL/CCAPPLL)/math.log(PRL/PLL)
                a = CCAPPRL/PRL**b
                # factor 0.75 to make double flash 25% more expansive than single flash
                self.Cplantcorrelation = (0.8*a*math.pow(np.max(model.surfaceplant.ElectricityProduced.value), b) *
                                          np.max(model.surfaceplant.ElectricityProduced.value)*1000./1E6)

            elif model.surfaceplant.pptype.value == PowerPlantType.DOUBLE_FLASH:
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
                CCAPPLL = C2*maxProdTemp**2 + C1*maxProdTemp + C0
                CCAPPRL = D2*maxProdTemp**2 + D1*maxProdTemp + D0
                b = math.log(CCAPPRL/CCAPPLL)/math.log(PRL/PLL)
                a = CCAPPRL/PRL**b
                self.Cplantcorrelation = (a*math.pow(np.max(model.surfaceplant.ElectricityProduced.value), b) *
                                          np.max(model.surfaceplant.ElectricityProduced.value)*1000./1E6)

            if self.ccplantfixed.Valid:
                self.Cplant.value = self.ccplantfixed.value
            else:
                # 1.02 to convert cost from 2012 to 2016 #factor 1.15 for 15% contingency and 1.12 for 12% indirect costs.
                self.Cplant.value = 1.12*1.15*self.ccplantadjfactor.value*self.Cplantcorrelation*1.02

        # add direct-use plant cost of co-gen system to Cplant (only of no total Cplant was provided)
        if not self.ccplantfixed.Valid:  # 1.15 below for contingency and 1.12 for indirect costs
            if model.surfaceplant.enduseoption.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICTY,
                                                         EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT]:  # enduseoption = 3: cogen topping cycle
                self.Cplant.value = self.Cplant.value + 1.12*1.15*self.ccplantadjfactor.value*250E-6*np.max(model.surfaceplant.HeatProduced.value/model.surfaceplant.enduseefficiencyfactor.value)*1000.
            elif model.surfaceplant.enduseoption.value in [EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                           EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICTY]:  # enduseoption = 4: cogen bottoming cycle
                self.Cplant = self.Cplant.value + 1.12*1.15*self.ccplantadjfactor.value*250E-6*np.max(model.surfaceplant.HeatProduced.value/model.surfaceplant.enduseefficiencyfactor.value)*1000.
            elif model.surfaceplant.enduseoption.value in [EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICTY,
                                                           EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT]:  # cogen parallel cycle
                self.Cplant.value = self.Cplant.value + 1.12*1.15*self.ccplantadjfactor.value*250E-6*np.max(model.surfaceplant.HeatProduced.value/model.surfaceplant.enduseefficiencyfactor.value)*1000.

        if not self.totalcapcost.Valid:
            # exploration costs (same as in Geophires v1.2) (M$)
            if self.ccexplfixed.Valid:
                self.Cexpl.value = self.ccexplfixed.value
            else:
                self.Cexpl.value = 1.15*self.ccexpladjfactor.value*1.12*(1. + self.C1well*0.6)  # 1.15 for 15% contingency and 1.12 for 12% indirect costs

            # Surface Piping Length Costs (M$) #assumed $750k/km
            self.Cpiping.value = 750/1000*model.surfaceplant.pipinglength.value

            self.CCap.value = self.Cexpl.value + self.Cwell.value + self.Cstim.value + self.Cgath.value + self.Cplant.value + self.Cpiping.value
        else:
            self.CCap.value = self.totalcapcost.value

        # O&M costs
        if not self.oamtotalfixed.Valid:
            # labor cost
            if model.surfaceplant.enduseoption.value == EndUseOptions.ELECTRICITY:  # electricity
                if np.max(model.surfaceplant.ElectricityProduced.value) < 2.5:
                    self.Claborcorrelation = 236./1E3  # M$/year
                else:
                    self.Claborcorrelation = (589.*math.log(np.max(model.surfaceplant.ElectricityProduced.value))-304.)/1E3  # M$/year
            else:
                if np.max(model.surfaceplant.HeatExtracted.value) < 2.5*5.:
                    self.Claborcorrelation = 236./1E3  # M$/year
                else:
                    self.Claborcorrelation = (589.*math.log(np.max(model.surfaceplant.HeatExtracted.value)/5.)-304.)/1E3  # M$/year
                # * 1.1 to convert from 2012 to 2016$ with BLS employment cost index (for utilities in March)
            self.Claborcorrelation = self.Claborcorrelation*1.1

            # plant O&M cost
            if self.oamplantfixed.Valid:
                self.Coamplant.value = self.oamplantfixed.value
            else:
                self.Coamplant.value = self.oamplantadjfactor.value*(1.5/100.*self.Cplant.value + 0.75*self.Claborcorrelation)

            # wellfield O&M cost
            if self.oamwellfixed.Valid:
                self.Coamwell.value = self.oamwellfixed.value
            else:
                self.Coamwell.value = self.oamwelladjfactor.value*(1./100.*(self.Cwell.value + self.Cgath.value) + 0.25*self.Claborcorrelation)

            # water O&M cost
            if self.oamwaterfixed.Valid:
                self.Coamwater.value = self.oamwaterfixed.value
            else:
                # here is assumed 1 l per kg maybe correct with real temp. (M$/year) 925$/ML = 3.5$/1,000 gallon
                self.Coamwater.value = self.oamwateradjfactor.value*(model.wellbores.nprod.value *
                                                                     model.wellbores.prodwellflowrate.value *
                                                                     model.reserv.waterloss.value*model.surfaceplant.utilfactor.value *
                                                                     365.*24.*3600./1E6*925./1E6)

            self.Coam.value = self.Coamwell.value + self.Coamplant.value + self.Coamwater.value  # total O&M cost (M$/year)

        else:
            self.Coam.value = self.oamtotalfixed.value  # total O&M cost (M$/year)

        if model.wellbores.redrill.value > 0:
            # account for well redrilling
            model.Coam.value = model.Coam.value + \
                (self.Cwell.value + model.reserv.Cstim.value) * model.wellbores.redrill.value / model.surfaceplant.plantlifetime.value

        # The Reservoir depth measure was arbitrarily changed to meters despite being defined in the docs as kilometers.
        # For display consistency sake, we need to convert it back
        if model.reserv.depth.value > 500:
            model.reserv.depth.value = model.reserv.depth.value/1000.0
            model.reserv.depth.CurrentUnits = LengthUnit.KILOMETERS

        # build the price models
        self.ElecPrice.value = BuildPricingModel(model.surfaceplant.plantlifetime.value, 0,
                                                      self.ElecStartPrice.value, self.ElecEndPrice.value,
                                                      self.ElecEscalationStart.value, self.ElecEscalationRate.value)
        self.HeatPrice.value = BuildPricingModel(model.surfaceplant.plantlifetime.value, 0,
                                                      self.HeatStartPrice.value, self.HeatEndPrice.value,
                                                      self.HeatEscalationStart.value, self.HeatEscalationRate.value)

        # Add in the FlatLicenseEtc, OtherIncentives, TotalGrant, AnnualLicenseEtc, and TaxRelief
        self.CCap.value = self.CCap.value + self.FlatLicenseEtc.value - self.OtherIncentives.value - self.TotalGrant.value
        self.Coam.value = self.Coam.value + self.AnnualLicenseEtc.value - self.TaxRelief.value

        # Calculate cashflow and cumulative cash flow
        if model.surfaceplant.enduseoption.value == EndUseOptions.ELECTRICITY:
            self.ElecRevenue.value, self.ElecCummRevenue.value = CalculateRevenue(
                model.surfaceplant.plantlifetime.value, model.surfaceplant.ConstructionYears.value, self.CCap.value,
                self.Coam.value, model.surfaceplant.NetkWhProduced.value, self.ElecPrice.value)
            self.TotalRevenue.value = self.ElecRevenue.value
            self.TotalCummRevenue.value = self.ElecCummRevenue.value
        elif model.surfaceplant.enduseoption.value == EndUseOptions.HEAT:
            self.HeatRevenue.value, self.HeatCummRevenue.value = CalculateRevenue(
               model.surfaceplant.plantlifetime.value, model.surfaceplant.ConstructionYears.value, self.CCap.value,
               self.Coam.value, model.surfaceplant.HeatkWhProduced.value, self.HeatPrice.value)
            self.TotalRevenue.value = self.HeatRevenue.value
            self.TotalCummRevenue.value = self.HeatCummRevenue.value
        else:
            self.ElecRevenue.value, self.ElecCummRevenue.self = CalculateRevenue(
               model.surfaceplant.plantlifetime.value, model.surfaceplant.ConstructionYears.value, self.CCap.value,
               self.Coam.value, model.surfaceplant.NetkWhProduced.value, self.ElecPrice.value)
           # note that CAPEX & OPEX are 0.0 because we only want them counted once, and it will be accounted
           # for in the previous line
            self.HeatRevenue.value, self.HeatCummRevenue.self = CalculateRevenue(
               model.surfaceplant.plantlifetime.value, model.surfaceplant.ConstructionYears.value, 0.0, 0.0,
               model.surfaceplant.HeatkWhProduced.value, self.HeatPrice.value)
            self.TotalRevenue.value = [0.0] * (model.surfaceplant.plantlifetime.value+model.surfaceplant.ConstructionYears.value)
            self.TotalCummRevenue.value = [0.0] * (model.surfaceplant.plantlifetime.value+model.surfaceplant.ConstructionYears.value)
            for i in range(0, model.surfaceplant.plantlifetime.value+model.surfaceplant.ConstructionYears.value, 1):
                self.TotalRevenue.value[i] = self.ElecRevenue.value[i] + self.HeatRevenue.value[i]
                self.TotalCummRevenue.value[i] = self.TotalRevenue.value[i]
                if i > 0:
                    self.TotalCummRevenue.value[i] = self.TotalCummRevenue.value[i-1] + self.TotalRevenue.value[i]

        # Calculate more financial values using numpy financials
        self.ProjectNPV.value, self.ProjectIRR.value, self.ProjectVIR.value, self.ProjectMOIC.value = \
            CalculateFinancialPerformance(model.surfaceplant.plantlifetime.value, self.FixedInternalRate.value,
                                               self.TotalRevenue.value, self.TotalCummRevenue.value, self.CCap.value,
                                               self.Coam.value)

        # Calculate LCOE/LCOH
        self.LCOE.value, self.LCOH.value = CalculateLCOELCOH(self, model)

        model.logger.info("complete "+ str(__class__) + ": " + sys._getframe().f_code.co_name)

    def __str__(self):
        return "Economics"

import sys
import os
import numpy as np
from geophires_x.Parameter import floatParameter, OutputParameter, ReadParameter
from geophires_x.Units import *
from geophires_x.OptionList import EndUseOptions
import geophires_x.Model as Model
import geophires_x.Economics as Economics


class EconomicsS_DAC_GT(Economics.Economics):
    """
    Solid Sorbent Direct Air Capture Using Geothermal Energy Resources (S-DAC-GT)
    Model For Region Specific Economic Analysis
    SPE-215735-MS
    Conference: Session: 02 - Technology Systems and Strategy for the Energy Transition
    August 2023
    Paper Authors: Timur Kuru, Keivan Khaleghi, and Silviu Livescu
    University of Texas at Austin, United States
    Primary coder: Timur Kuru
    Integration with GEOPHIRES: Malcolm I Ross
    Prepared 6/13/2023
    """

    def __init__(self, model: Model):
        """
        The __init__ function is the constructor for a class.  It is called whenever an instance of the class is created.
        The __init__ function can take arguments, but self is always the first one. Self refers to the instance of the
        object that has already been created and it's used to access variables that belong to that object.
        Set up all the Parameters that will be predefined by this class using the different types of parameter classes.
        Setting up includes giving it a name, a default value, The Unit Type (length, volume, temperature, etc) and
        Unit Name of that value, sets it as required (or not), sets allowable range, the error message if that range is
        exceeded, the ToolTip Text, and the name of teh class that created it.
        This includes setting up temporary variables that will be available to all the class but noy read in by user,
        or used for Output
        This also includes all Parameters that are calculated and then published using the Printouts function.
        If you choose to subclass this master class, you can do so before or after you create your own parameters.
        If you do, you can also choose to call this method from you class, which will effectively add and set
        all these parameters to your class.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing, and is used to initialize the class
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        # These dictionaries contains a list of all the parameters set in this object, stored as "Parameter" and
        # OutputParameter Objects.  This will allow us later to access them in a user interface and get that list,
        # along with unit type, preferred units, etc.
        self.ParameterDict = {}
        self.OutputParameterDict = {}
        self.wacc = self.ParameterDict[self.wacc.Name] = floatParameter(
            "WACC",
            value=10.0,
            DefaultValue=10.0,
            Min=0.1,
            Max=30.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.PERCENT,
            CurrentUnits=PercentUnit.PERCENT,
            ErrMessage="assume default Weighted Average Cost of Capital (10%)",
            ToolTipText="Weighted Average Cost of Capital (percent)"
        )
        self.CAPEX = self.ParameterDict[self.CAPEX.Name] = floatParameter(
            "S-DAC-GT CAPEX",
            value=1379.0,
            DefaultValue=1379.0,
            Min=100.0,
            Max=5000.0,
            UnitType=Units.COSTPERMASS,
            PreferredUnits=CostPerMassUnit.DOLLARSPERTONNE,
            CurrentUnits=CostPerMassUnit.DOLLARSPERTONNE,
            ErrMessage="assume default CAPEX (1379 USD per tonne CO2 capacity)",
            ToolTipText="CAPEX (USD per tonne CO2 capacity)"
        )
        self.OPEX = self.ParameterDict[self.OPEX.Name] = floatParameter(
            "S-DAC-GT OPEX",
            value=56.0,
            DefaultValue=56.0,
            Min=10.0,
            Max=500.0,
            UnitType=Units.COSTPERMASS,
            PreferredUnits=CostPerMassUnit.DOLLARSPERTONNE,
            CurrentUnits=CostPerMassUnit.DOLLARSPERTONNE,
            ErrMessage="assume default OPEX (56 USD per tonne CO2)",
            ToolTipText="OPEX (USD per tonne CO2)"
        )
        self.elec = self.ParameterDict[self.elec.Name] = floatParameter(
            "S-DAC-GT Electrical Energy",
            value=916.0,
            DefaultValue=916.0,
            Min=100.0, Max=5000.0,
            UnitType=Units.ENERGYPERCO2,
            PreferredUnits=EnergyPerCO2Unit.KWHEPERTONNE,
            CurrentUnits=EnergyPerCO2Unit.KWHEPERTONNE,
            ErrMessage="assume default Electrical Energy (916 kWh_e per tonne CO2)",
            ToolTipText="Electrical Energy (kWh_e per tonne CO2)"
        )
        self.therm = self.ParameterDict[self.therm.Name] = floatParameter(
            "S-DAC-GT Thermal Energy",
            value=1447.0,
            DefaultValue=1447.0,
            Min=100.0,
            Max=5000.0,
            UnitType=Units.ENERGYPERCO2,
            PreferredUnits=EnergyPerCO2Unit.KWTHPERTONNE,
            CurrentUnits=EnergyPerCO2Unit.KWTHPERTONNE,
            ErrMessage="assume default Thermal Energy (1447 kW_th per tonne CO2)",
            ToolTipText="Thermal Energy (kW_th per tonne CO2)"
        )
        self.NG_price = self.ParameterDict[self.NG_price.Name] = floatParameter(
            "S-DAC-GT Natural Gas Price",
            value=5.0,
            DefaultValue=5.0,
            Min=0.5,
            Max=500.0,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERMCF,
            CurrentUnits=EnergyCostUnit.DOLLARSPERMCF,
            ErrMessage="assume default Natural Gas Price (5 USD per MCF)",
            ToolTipText="Natural Gas Price (USD per MCF)"
        )
        self.power_co2intensity = self.ParameterDict[self.power_co2intensity.Name] = floatParameter(
            "S-DAC-GT CO2 Intensity of Electricity",
            value=0.4,
            DefaultValue=0.4,
            Min=0.0,
            Max=1.0,
            UnitType=Units.CO2PRODUCTION,
            PreferredUnits=CO2ProductionUnit.TONNEPERMWH,
            CurrentUnits=CO2ProductionUnit.TONNEPERMWH,
            ErrMessage="assume default CO2 Intensity of Electricity (0.4 tonne CO2 emitted per MWh)",
            ToolTipText="CO2 Intensity of Electricity (tonne CO2 emitted per MWh)"
        )
        self.NG_co2intensity = self.ParameterDict[self.NG_co2intensity.Name] = floatParameter(
            "S-DAC-GT CO2 Intensity of Natural Gas",
            value=0.194965384,
            DefaultValue=0.194965384,
            Min=0.0,
            Max=1.0,
            UnitType=Units.CO2PRODUCTION,
            PreferredUnits=CO2ProductionUnit.TONNEPERMWH,
            CurrentUnits=CO2ProductionUnit.TONNEPERMWH,
            ErrMessage="assume default Natural Gas Intensity of Electricity (0.194965384 tonne CO2 emitted per MWh)",
            ToolTipText="CO2 Intensity of Natural Gas (tonne CO2 emitted per MWh)"
        )
        self.NG_EnergyDensity = self.ParameterDict[self.NG_EnergyDensity.Name] = floatParameter(
            "S-DAC-GT Natural Gas Energy Density",
            value=282.6142719,
            DefaultValue=282.6142719,
            Min=0.0,
            Max=1000.0,
            UnitType=Units.ENERGYDENSITY,
            PreferredUnits=EnergyDensityUnit.KWHPERMCF,
            CurrentUnits=EnergyDensityUnit.KWHPERMCF,
            ErrMessage="assume default Natural Gas Energy Density (282.6142719 kWh per MCF)",
            ToolTipText="Natural Gas Energy Density (kWh per MCF)"
        )
        self.CAPEX_mult = self.ParameterDict[self.CAPEX_mult.Name] = floatParameter(
            "S-DAC-GT CAPEX Multiplier",
            value=1.0,
            DefaultValue=1.0,
            Min=0.5,
            Max=3.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default CAPEX Multiplier (1.0)",
            ToolTipText="CAPEX Multiplier"
        )
        self.OPEX_mult = self.ParameterDict[self.OPEX_mult.Name] = floatParameter(
            "S-DAC-GT OPEX Multiplier",
            value=1.0,
            DefaultValue=1.0,
            Min=0.5,
            Max=3.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default OPEX Multiplier (1.0)",
            ToolTipText="OPEX Multiplier"
        )
        self.therm_index = self.ParameterDict[self.therm_index.Name] = floatParameter(
            "S-DAC-GT Thermal Energy Multiplier",
            value=1.0,
            DefaultValue=1.0,
            Min=0.5,
            Max=1.8,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default S-DAC Thermal Energy Multiplier (1.0)",
            ToolTipText="S-DAC Thermal Energy Multiplier [usually due to avg humidity/temperature]"
        )
        self.transport = self.ParameterDict[self.transport.Name] = floatParameter(
            "S-DAC-GT CO2 Transportation Cost",
            value=10.0,
            DefaultValue=10.0,
            Min=1.0,
            Max=50.0,
            UnitType=Units.COSTPERMASS,
            PreferredUnits=CostPerMassUnit.DOLLARSPERTONNE,
            CurrentUnits=CostPerMassUnit.DOLLARSPERTONNE,
            ErrMessage="assume default CO2 Transportation Cost (10 USD per tonne CO2)",
            ToolTipText="CO2 Transportation Cost (USD per tonne CO2)"
        )
        self.storage = self.ParameterDict[self.storage.Name] = floatParameter(
            "S-DAC-GT CO2 Storage Cost",
            value=10.0,
            DefaultValue=10.0,
            Min=5.0,
            Max=50.0,
            UnitType=Units.COSTPERMASS,
            PreferredUnits=CostPerMassUnit.DOLLARSPERTONNE,
            CurrentUnits=CostPerMassUnit.DOLLARSPERTONNE,
            ErrMessage="assume default CO2 Storage Cost (10 USD per tonne CO2)",
            ToolTipText="CO2 Storage Cost (USD per tonne CO2)"
        )
        self.EnergySplit = self.ParameterDict[self.EnergySplit.Name] = floatParameter(
            "S-DAC-GT CO2 Percent Energy Devoted To Process",
            value=0.5,
            DefaultValue=0.5,
            Min=0.0,
            Max=1.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default Percent Energy Devoted To Process (50%)",
            ToolTipText="Percent Energy Devoted To Process (%)"
        )

        # local variable initiation
        # Capital Recovery Rate or Fixed Charge Factor - set initially for definitions
        self.CRF = 0.1175

        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = os.path.abspath(__file__)

        # Results - used by other objects or printed in output downstream
        self.LCOD_elec = self.OutputParameterDict[self.LCOD_elec.Name] = OutputParameter(
            "Total LCOD 100% electric",
            UnitType=Units.COSTPERMASS,
            PreferredUnits=CostPerMassUnit.DOLLARSPERTONNE,
            CurrentUnits=CostPerMassUnit.DOLLARSPERTONNE
        )
        self.LCOD_ng = self.OutputParameterDict[self.LCOD_ng.Name] = OutputParameter(
            Name="Total LCOD natural gas",
            UnitType=Units.COSTPERMASS,
            PreferredUnits=CostPerMassUnit.DOLLARSPERTONNE,
            CurrentUnits=CostPerMassUnit.DOLLARSPERTONNE
        )
        self.LCOD_geo = self.OutputParameterDict[self.LCOD_geo.Name] = OutputParameter(
            Name="Total LCOD S-DAC-GT",
            UnitType=Units.COSTPERMASS,
            PreferredUnits=CostPerMassUnit.DOLLARSPERTONNE,
            CurrentUnits=CostPerMassUnit.DOLLARSPERTONNE
        )
        self.CO2total_elec = self.OutputParameterDict[self.CO2total_elec.Name] = OutputParameter(
            Name="Total CO2 Intensity 100% electric",
            UnitType=Units.CO2PRODUCTION,
            PreferredUnits=CO2ProductionUnit.TONNEPERMWH,
            CurrentUnits=CO2ProductionUnit.TONNEPERMWH
        )
        self.CO2total_ng = self.OutputParameterDict[self.CO2total_ng.Name] = OutputParameter(
            Name="Total CO2 Intensity natural gas",
            UnitType=Units.CO2PRODUCTION,
            PreferredUnits=CO2ProductionUnit.TONNEPERMWH,
            CurrentUnits=CO2ProductionUnit.TONNEPERMWH
        )
        self.CO2total_geo = self.OutputParameterDict[self.CO2total_geo.Name] = OutputParameter(
            Name="Total CO2 Intensity S-DAC-GT",
            UnitType=Units.CO2PRODUCTION,
            PreferredUnits=CO2ProductionUnit.TONNEPERMWH,
            CurrentUnits=CO2ProductionUnit.TONNEPERMWH
        )
        self.LCOH = self.OutputParameterDict[self.LCOH.Name] = OutputParameter(
            Name="LCOH",
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH
        )
        self.kWh_e_per_kWh_th = self.OutputParameterDict[self.kWh_e_per_kWh_th.Name] = OutputParameter(
            Name="Energy Use Ratio heat vs electricity",
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH
        )
        self.tot_heat_energy_consumed_per_tonne = self.OutputParameterDict[
            self.tot_heat_energy_consumed_per_tonne.Name] = OutputParameter(
            Name="Total Heat Energy Used to extract carbon",
            UnitType=Units.ENERGYPERCO2,
            PreferredUnits=EnergyPerCO2Unit.KWTHPERTONNE,
            CurrentUnits=EnergyPerCO2Unit.KWTHPERTONNE
        )
        self.tot_cost_per_tonne = self.OutputParameterDict[self.tot_cost_per_tonne.Name] = OutputParameter(
            Name="Total Cost per Tonne of CO2 Captured",
            UnitType=Units.COSTPERMASS,
            PreferredUnits=CostPerMassUnit.DOLLARSPERTONNE,
            CurrentUnits=CostPerMassUnit.DOLLARSPERTONNE
        )
        self.percent_thermal_energy_going_to_heat = self.OutputParameterDict[
            self.percent_thermal_energy_going_to_heat.Name] = OutputParameter(
            Name="Percent of Total Energy Used as heat in processs",
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH
        )
        self.S_DAC_GTAnnualCost = self.OutputParameterDict[self.S_DAC_GTAnnualCost.Name] = OutputParameter(
            Name="Total Cost per Year",
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.DOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.DOLLARSPERYEAR
        )
        self.S_DAC_GTCummCashFlow = self.OutputParameterDict[self.S_DAC_GTCummCashFlow.Name] = OutputParameter(
            Name="Running Total Cost",
            UnitType=Units.CURRENCY,
            PreferredUnits=CurrencyUnit.DOLLARS,
            CurrentUnits=CurrencyUnit.DOLLARS
        )
        self.CarbonExtractedAnnually = self.OutputParameterDict[self.CarbonExtractedAnnually.Name] = OutputParameter(
            Name="Tonnes per Year CO2 extracted",
            UnitType=Units.MASSPERTIME,
            PreferredUnits=MassPerTimeUnit.TONNEPERYEAR,
            CurrentUnits=MassPerTimeUnit.TONNEPERYEAR
        )
        self.S_DAC_GTCummCarbonExtracted = self.OutputParameterDict[
            self.S_DAC_GTCummCarbonExtracted.Name] = OutputParameter(
            Name="Running Carbon Capture",
            UnitType=Units.MASS,
            PreferredUnits=MassUnit.TONNE,
            CurrentUnits=MassUnit.TONNE
        )
        self.CarbonExtractedTotal = self.OutputParameterDict[self.CarbonExtractedTotal.Name] = OutputParameter(
            Name="Total Tonnes of CO2 extracted",
            UnitType=Units.MASS,
            PreferredUnits=MassUnit.TONNE,
            CurrentUnits=MassUnit.TONNE
        )
        self.CummCostPerTonne = self.OutputParameterDict[self.CummCostPerTonne.Name] = OutputParameter(
            Name="Running cost per Tonne of capture",
            UnitType=Units.COSTPERMASS,
            PreferredUnits=CostPerMassUnit.DOLLARSPERTONNE,
            CurrentUnits=CostPerMassUnit.DOLLARSPERTONNE
        )

        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def __str__(self):
        return "EconomicsS_DAC_GT"

    def read_parameters(self, model: Model) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary and stores them in the parameters.
        It also handles special cases that need to be handled after a value has been read in and checked.
        If you choose to subclass this master class, you can also choose to override this method (or not), and if you do
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        # Deal with all the parameter values that the user has provided.  They should really only provide values
        # that they want to change from the default values, but they can provide a value that is already set because it
        # is a default value set in __init__.  It will ignore those.
        # This also deals with all the special cases that need to be taken care of after a vlaue has been read in and checked.
        # If you choose to subclass this master class, you can also choose to override this method (or not),
        # and if you do, do it before or after you call you own version of this method.  If you do, you can also
        # choose to call this method from you class, which can effectively modify all these superclass parameters in your class.

        if len(model.InputParameters) > 0:
            # loop thru all the parameters that the user wishes to set, looking for parameters that match this object
            for item in self.ParameterDict.items():
                ParameterToModify = item[1]
                key = ParameterToModify.Name.strip()
                if key in model.InputParameters:
                    ParameterReadIn = model.InputParameters[key]
                    # Before we change the paremater, let's assume that the unit preferences will match -
                    # if they don't, the later code will fix this.
                    ParameterToModify.CurrentUnits = ParameterToModify.PreferredUnits
                    # this should handle all the non-special cases
                    ReadParameter(ParameterReadIn, ParameterToModify, model)

                    # handle special cases
                    # none in this case so far
        else:
            model.logger.info("No parameters read becuase no content provided")
        model.logger.info("read parameters complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def calculate_CRF(self, wacc: float, num_years: float) -> float:
        """
        Calculate the Capital Recovery Factor (CRF) or Fixed Charge Factor (FCF)
        :param wacc: Weighted Average Cost of Capital (percent) - default 10% or 0.1 in this model
        :type wacc: float
        :param num_years: Number of years of project duration - default 20 years in this model (2022-2042)
         - 20 years is the minimum for this model to work properly - if you change it, you will need to change the
            default values for CAPEX and OPEX to match the new duration - see the paper for more details on this model and
            the assumptions made in it - the paper is available at https://www.onepetro.org/conference-paper/SPE-215735-MS -
            the paper is also available in the docs folder of this project
        :type num_years: float
        :return: CRF
        :rtype: float
        """

        # Default set to 11.75%, or calculated value for project duration of 20 years with WACC of 10%
        wacc = wacc / 100.0
        CRF = (wacc * (1 + wacc) ** num_years) / ((1 + wacc) ** num_years - 1)
        return CRF

    def range_check(self) -> tuple:
        """
        Check that all the values are within the allowable range
        :return: tuple of (True/False, Error Message)
        :rtype: tuple
        """
        wacc_min = 0.1
        wacc_max = 30
        CAPEX_min = 100
        CAPEX_max = 5000
        OPEX_min = 10
        OPEX_max = 500
        elec_min = 100
        elec_max = 5000
        therm_min = 100
        therm_max = 5000
        NG_price_min = 0.5
        NG_price_max = 100
        power_co2intensity_min = 0
        power_co2intensity_max = 1
        CAPEX_mult_min = 0.5
        CAPEX_mult_max = 3
        OPEX_mult_min = 0.5
        OPEX_mult_max = 3
        therm_index_min = 0.5
        therm_index_max = 1.8
        transport_min = 1
        transport_max = 50
        storage_min = 5
        storage_max = 50

        if not (wacc_min <= self.wacc.value <= wacc_max):
            error_message = "S-DAC-GT ERROR: WACC should be between {}% and {}%".format(wacc_min, wacc_max)
            return True, error_message

        if not (CAPEX_min <= self.CAPEX.value <= CAPEX_max):
            error_message = "S-DAC-GT ERROR: CAPEX should be between {} and {}".format(CAPEX_min, CAPEX_max)
            return True, error_message

        if not (OPEX_min <= self.OPEX.value <= OPEX_max):
            error_message = "S-DAC-GT ERROR: OPEX should be between {} and {}".format(OPEX_min, OPEX_max)
            return True, error_message

        if not (elec_min <= self.elec.value <= elec_max):
            error_message = "S-DAC-GT ERROR: Electrical Energy should be between {} and {}".format(elec_min, elec_max)
            return True, error_message

        if not (therm_min <= self.therm.value <= therm_max):
            error_message = "S-DAC-GT ERROR: Thermal Energy should be between {} and {}".format(therm_min, therm_max)
            return True, error_message

        if not (NG_price_min <= self.NG_price.value <= NG_price_max):
            error_message = "S-DAC-GT ERROR: Natural Gas Price should be between {} and {}".format(NG_price_min,
                                                                                                   NG_price_max)
            return True, error_message

        if not (power_co2intensity_min <= self.power_co2intensity.value <= power_co2intensity_max):
            error_message = "S-DAC-GT ERROR: CO2 Intensity of Electricity should be between {} and {}".format(
                power_co2intensity_min, power_co2intensity_max)
            return True, error_message

        if not (CAPEX_mult_min <= self.CAPEX_mult.value <= CAPEX_mult_max):
            error_message = "S-DAC-GT ERROR: CAPEX Multiplier should be between {} and {}".format(CAPEX_mult_min,
                                                                                                  CAPEX_mult_max)
            return True, error_message

        if not (OPEX_mult_min <= self.OPEX_mult.value <= OPEX_mult_max):
            error_message = "S-DAC-GT ERROR: OPEX Multiplier should be between {} and {}".format(OPEX_mult_min,
                                                                                                 OPEX_mult_max)
            return True, error_message

        if not (therm_index_min <= self.therm_index.value <= therm_index_max):
            error_message = "S-DAC-GT ERROR: S-DAC Thermal Energy Multiplier should be between {} and {}".format(
                therm_index_min, therm_index_max)
            return True, error_message

        if not (transport_min <= self.transport.value <= transport_max):
            error_message = "S-DAC-GT ERROR: CO2 Transportation Cost should be between {} and {}".format(transport_min,
                                                                                                         transport_max)
            return True, error_message

        if not (storage_min <= self.storage.value <= storage_max):
            error_message = "S-DAC-GT ERROR: CO2 Storage Cost should be between {} and {}".format(storage_min,
                                                                                                  storage_max)
            return True, error_message

        return False, ""

    def geo_therm_cost(self, power_cost: float, CAPEX_mult: float, OPEX_mult: float, depth: float,
                       Production_temp: float, Injection_temp: float, Flow_rate: float) -> tuple:
        """
        Calculate Levelized cost of heat and ratio of electric power to heat power
        LCOH calculated in USD
        Power ratio calculated as kWh_e / kWh_th --> used for calculating CO2 footprint of geothermal energy
        inputs are cost of electricity, regional capex and opex multipliers,
        depth of geothermal reservoir, Average Production Temperature, Injection Temperature, and Flow Rate
        recoded by Malcolm Ross when integrated with GEOPHIRES - GEOPHIRES has more information,
        so fewer assumptions are made
        :param power_cost: Cost of electricity in USD per kWh - default 0.05 USD per kWh in this model (5 cents per kWh) - this is the default value for the US in 2022
        :type power_cost: float
        :param CAPEX_mult: Regional CAPEX multiplier - default 1.0 in this model - this is the default value for the US in 2022
        :type CAPEX_mult: float
        :param OPEX_mult: Regional OPEX multiplier - default 1.0 in this model - this is the default value for the US in 2022
        :type OPEX_mult: float
        :param depth: Depth of geothermal reservoir in feet - default 4101 feet in this model - this is the default value for the US in 2022
        :type depth: float
        :param Production_temp: Average Production Temperature in Celsius - default 150 degrees C in this model - this is the default value for the US in 2022
        :type Production_temp: float
        :param Injection_temp: Injection Temperature in Celsius - default 50 degrees C in this model - this is the default value for the US in 2022
        :type Injection_temp: float
        :param Flow_rate: Flow Rate in kg/s - default 50 kg/s in this model - this is the default value for the US in 2022
        :type Flow_rate: float
        :return: tuple of (LCOH, kWh_e_per_kWh_th) - LCOH in USD per kWh_therm, kWh_e_per_kWh_th is ratio of kWh_e to kWh_th (kWh_e / kWh_th)
        :rtype: tuple
        """
        # Update NREL 2016 model for 2022
        # Inflation 2017 thru 2022 1H
        Inflation = 1.189
        # 2016 - Sep 2022 - EIA drilling prod report
        Drilling_efficiency_factor = 1.61
        # Thermal capacity of water
        H2O_thermal_capacity = 0.001163  # kWh/kg C
        # Plant capacity factor
        Capacity_factor = 0.9

        # NREL 2016 Model for new well adjusted for inflation
        NREL_depth = 4101  # feet
        NREL_CAPEX = 3712500 * Inflation  # USD, excludes drilling
        NREL_CAPEX_drill = 2112500 * Inflation  # USD
        NREL_drill_per_foot = NREL_CAPEX_drill / NREL_depth  # USD/foot
        NREL_pumping = 1980215  # kWh
        NREL_pump_per_foot = NREL_pumping / NREL_depth  # kWh/foot
        NREL_inhibitor = 50000 * Inflation  # USD
        NREL_labor = 100000 * Inflation  # USD
        NREL_reinjection = 127130 * Inflation  # USD

        # Normalize for region
        CAPEX = NREL_CAPEX * CAPEX_mult
        CAPEX_drill = depth * NREL_drill_per_foot / Drilling_efficiency_factor
        pump_kwh = depth * NREL_pump_per_foot
        pump_cost = pump_kwh * power_cost
        inhibitor = NREL_inhibitor * OPEX_mult
        labor = NREL_labor * OPEX_mult
        reinjection = NREL_reinjection / NREL_depth * depth * OPEX_mult

        # total costs
        CAPEX_total = CAPEX + CAPEX_drill
        OPEX_total = pump_cost + inhibitor + labor + reinjection

        # total thermal energy generation
        Thermal_capacity = (Production_temp - Injection_temp) * Flow_rate * H2O_thermal_capacity * 60 * 60  # kW
        Annual_op_hrs = 365 * 24 * Capacity_factor  # hours
        Therm_total = Thermal_capacity * Annual_op_hrs  # kWh

        # Levelized cost of heat (LCOH)
        LCOH = (CAPEX_total * self.CRF + OPEX_total) / Therm_total  # $/kWh_therm

        kWh_e_per_kWh_th = pump_kwh / Therm_total

        return LCOH, kWh_e_per_kWh_th

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
        # and if you do, do it before or after you call you own version of this method.
        # If you do, you can also choose to call this method from you class, which can effectively
        # run the calculations of the superclass, making all thr values available to your methods.
        # but you had better have set all the parameters!

        # Ensure parameters are within range.  If not, exit function without completing calculation or generating charts
        err_state, err_message = self.range_check()
        if err_state:
            model.logger.fatal(err_message + "  Exiting....")
            print(err_message + "  Exiting....")
            sys.exit()

        # Calculate initial CRF value based on default inputs
        self.CRF = self.calculate_CRF(self.wacc.value, model.surfaceplant.plant_lifetime.value)

        # don't change a parameters value directly - it throw off the rehydration
        CAPEX = self.CAPEX.value * self.CRF
        CAPEX = CAPEX * self.CAPEX_mult.value
        self.OPEX.value = self.OPEX.value * self.OPEX_mult.value
        self.therm.value = self.therm.value * self.therm_index.value
        power_totalcost = self.elec.value * model.surfaceplant.electricity_cost_to_buy.value
        elec_heat_totalcost = self.therm.value * model.surfaceplant.electricity_cost_to_buy.value

        # Convert from $/McF to $/kWh_th, but don't change any parameters value directly - it will throw off the rehydration
        NG_price = self.NG_price.value / self.NG_EnergyDensity.value
        NG_totalcost = self.therm.value * NG_price
        self.LCOH.value, self.kWh_e_per_kWh_th.value = self.geo_therm_cost(model.surfaceplant.electricity_cost_to_buy.value,
                                                                           self.CAPEX_mult.value, self.OPEX_mult.value,
                                                                           model.reserv.depth.value * 3280.84,
                                                                           np.average(model.wellbores.ProducedTemperature.value),
                                                                           model.wellbores.Tinj.value,
                                                                           model.wellbores.nprod.value * model.wellbores.prodwellflowrate.value)
        geothermal_totalcost = self.LCOH.value * self.therm.value
        co2_power = self.elec.value / 1000 * self.power_co2intensity.value
        co2_elec_heat = self.therm.value / 1000 * self.power_co2intensity.value
        co2_ng = self.therm.value / 1000 * self.NG_co2intensity.value
        co2_geothermal = self.therm.value * self.kWh_e_per_kWh_th.value / 1000 * self.power_co2intensity.value

        self.LCOD_elec.value = CAPEX + self.OPEX.value + power_totalcost + elec_heat_totalcost + self.storage.value + self.transport.value
        self.LCOD_ng.value = CAPEX + self.OPEX.value + power_totalcost + NG_totalcost + self.storage.value + self.transport.value
        self.LCOD_geo.value = CAPEX + self.OPEX.value + power_totalcost + geothermal_totalcost + self.storage.value + self.transport.value

        self.CO2total_elec.value = co2_power + co2_elec_heat
        self.CO2total_ng.value = co2_power + co2_ng
        self.CO2total_geo.value = co2_power + co2_geothermal

        # calculate the net impact of S-DAC-GT on the annual production of the model
        avg_first_law_eff = np.average(model.surfaceplant.FirstLawEfficiency.value)
        self.tot_heat_energy_consumed_per_tonne.value = (self.elec.value / avg_first_law_eff) + self.therm.value  # kWh_th/tonne
        self.tot_cost_per_tonne.value = CAPEX + self.OPEX.value + self.storage.value + self.transport.value  # USD/tonne
        self.percent_thermal_energy_going_to_heat.value = self.therm.value / self.tot_heat_energy_consumed_per_tonne.value

        self.S_DAC_GTAnnualCost.value = [0.0] * model.surfaceplant.plant_lifetime.value
        self.S_DAC_GTCummCashFlow.value = [0.0] * model.surfaceplant.plant_lifetime.value
        self.CarbonExtractedAnnually.value = [0.0] * model.surfaceplant.plant_lifetime.value
        self.S_DAC_GTCummCarbonExtracted.value = [0.0] * model.surfaceplant.plant_lifetime.value
        self.CummCostPerTonne.value = [0.0] * model.surfaceplant.plant_lifetime.value
        self.CarbonExtractedTotal.value = 0.0

        # Figure out how much energy is being produced each year, and the amount of carbon that
        # would have been produced if that energy had been made using the grid average carbon production.
        # That then gives us the revenue, since we have a carbon price model
        # We can also get annual cash flow from it.
        for i in range(0, model.surfaceplant.plant_lifetime.value, 1):
            self.CarbonExtractedAnnually.value[i] = (self.EnergySplit.value * model.surfaceplant.HeatkWhExtracted.value[i]) / self.tot_heat_energy_consumed_per_tonne.value
            if i == 0:
                self.S_DAC_GTCummCarbonExtracted.value[i] = self.CarbonExtractedAnnually.value[i]
            else:
                self.S_DAC_GTCummCarbonExtracted.value[i] = self.S_DAC_GTCummCarbonExtracted.value[i - 1] + self.CarbonExtractedAnnually.value[i]
            self.CarbonExtractedTotal.value = self.CarbonExtractedTotal.value + self.CarbonExtractedAnnually.value[i]
            self.S_DAC_GTAnnualCost.value[i] = self.CarbonExtractedAnnually.value[i] * self.tot_cost_per_tonne.value
            if i == 0:
                self.S_DAC_GTCummCashFlow.value[i] = self.S_DAC_GTAnnualCost.value[i]
            else:
                self.S_DAC_GTCummCashFlow.value[i] = self.S_DAC_GTCummCashFlow.value[i - 1] + self.S_DAC_GTAnnualCost.value[i]
            self.CummCostPerTonne.value[i] = self.S_DAC_GTCummCashFlow.value[i] / self.S_DAC_GTCummCarbonExtracted.value[i]

        # We need to update the heat and electricity generated because we have consumed
        # some (all) of it to do the capture, so when they get used in the final economic calculation (below),
        # the new values reflect the impact of S-DAC-GT
        for i in range(0, model.surfaceplant.plant_lifetime.value):
            if model.surfaceplant.enduse_option.value != EndUseOptions.HEAT:
                # all these end-use options have an electricity generation component
                model.surfaceplant.TotalkWhProduced.value[i] = model.surfaceplant.TotalkWhProduced.value[i] - (
                    self.CarbonExtractedAnnually.value[i] * self.elec.value)
                model.surfaceplant.NetkWhProduced.value[i] = model.surfaceplant.NetkWhProduced.value[i] - (
                    self.CarbonExtractedAnnually.value[i] * self.elec.value)
                if model.surfaceplant.enduse_option.value != EndUseOptions.ELECTRICITY:
                    model.surfaceplant.HeatkWhProduced.value[i] = model.surfaceplant.HeatkWhProduced.value[i] - (
                        self.CarbonExtractedAnnually.value[i] * self.therm.value)
            else:
                # all the end-use option of direct-use only component
                model.surfaceplant.HeatkWhProduced.value[i] = (model.surfaceplant.HeatkWhProduced.value[i] -
                                                               (self.CarbonExtractedAnnually.value[i] * self.therm.value))

        # Build a revenue generation model for the carbon capture, assuming the capture is being sequestered and that
        # there is some sort of credit involved for doing that sequestering
        # note that there may already be values in the CarbonRevenue array, so we need to
        # add to them, not just set them. If there isn't values, there, the array will be filed with zeros, so adding won't be a problem
        #total_duration = model.surfaceplant.plant_lifetime.value
        #for i in range(0, total_duration, 1):
        #    model.sdacgteconomics.CarbonRevenue.value[i] = (model.sdacgteconomics.CarbonRevenue.value[i] +
        #                                              (self.CarbonExtractedAnnually.value[i] * model.economics.CarbonPrice.value[i]))
#            if i > 0:
#                model.economics.CarbonCummCashFlow.value[i] = model.economics.CarbonCummCashFlow.value[i - 1] + model.economics.CarbonRevenue.value[i]
        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

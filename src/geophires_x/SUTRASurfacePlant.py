import sys
import os
import numpy as np
from .OptionList import EndUseOptions, PowerPlantType
from .Parameter import floatParameter, intParameter, strParameter, OutputParameter, ReadParameter
from .Units import *
import geophires_x.Model as Model
import pandas as pd
from matplotlib import pyplot as plt

class SUTRASurfacePlant:
    def __init__(self, model: Model):
        """
        The __init__ function is called automatically when a class is instantiated.
        It initializes the attributes of an object, and sets default values for certain arguments that can be overridden
         by user input.
        The __init__ function is used to set up all the parameters in the Surfaceplant.
        :param self: Store data that will be used by the class
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: None
        :doc-author: Malcolm Ross
        """

        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)
        self.Tinj = 0.0

        # Set up all the Parameters that will be predefined by this class using the different types of parameter classes.
        # Setting up includes giving it a name, a default value, The Unit Type (length, volume, temperature, etc.) and
        # Unit Name of that value, sets it as required (or not), sets allowable range, the error message if that range
        # is exceeded, the ToolTip Text, and the name of teh class that created it.
        # This includes setting up temporary variables that will be available to all the class but noy read in by user,
        # or used for Output
        # This also includes all Parameters that are calculated and then published using the Printouts function.

        # These dictionaries contain a list of all the parameters set in this object, stored as "Parameter" and
        # "OutputParameter" Objects.  This will allow us later to access them in a user interface and get that list,
        # along with unit type, preferred units, etc.
        self.ParameterDict = {}
        self.OutputParameterDict = {}

        self.enduseoption = self.ParameterDict[self.enduseoption.Name] = intParameter(
            "End-Use Option",
            value=EndUseOptions.ELECTRICITY,
            AllowableRange=[1, 2, 31, 32, 41, 42, 51, 52, 6, 7, 8, 9],
            UnitType=Units.NONE,
            ErrMessage="assume default end-use option (1: electricity only)",
            ToolTipText="Select the end-use application of the geofluid heat (see docs for details)"
        )

        self.pumpeff = self.ParameterDict[self.pumpeff.Name] = floatParameter(
            "Circulation Pump Efficiency",
            value=0.75,
            DefaultValue=0.75,
            Min=0.1,
            Max=1.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Required=True,
            ErrMessage="assume default circulation pump efficiency (0.75)",
            ToolTipText="Specify the overall efficiency of the injection and production well pumps"
        )

        self.enduseefficiencyfactor = self.ParameterDict[self.enduseefficiencyfactor.Name] = floatParameter(
            "End-Use Efficiency Factor",
            value=0.9,
            DefaultValue=0.9,
            Min=0.1,
            Max=1.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default end-use efficiency factor (0.9)",
            ToolTipText="Constant thermal efficiency of the direct-use application"
        )

        self.Tenv = self.ParameterDict[self.Tenv.Name] = floatParameter(
            "Ambient Temperature",
            value=15.0,
            DefaultValue=15.0,
            Min=-50,
            Max=50,
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS,
            ErrMessage="assume default ambient temperature (15 deg.C)",
            ToolTipText="Ambient (or dead-state) temperature used for calculating power plant utilization efficiency"
        )
        self.plantlifetime = self.ParameterDict[self.plantlifetime.Name] = intParameter(
            "Plant Lifetime",
            value=30,
            DefaultValue=30,
            AllowableRange=list(range(1, 101, 1)),
            UnitType=Units.TIME,
            PreferredUnits=TimeUnit.YEAR,
            CurrentUnits=TimeUnit.YEAR,
            Required=True,
            ErrMessage="assume default plant lifetime (30 years)",
            ToolTipText="System lifetime"
        )

        self.elecprice = self.ParameterDict[self.elecprice.Name] = floatParameter(
            "Electricity Rate",
            value=0.07,
            DefaultValue=0.07,
            Min=0.0,
            Max=1.0,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH,
            ErrMessage="assume default electricity rate ($0.07/kWh)",
            ToolTipText="Price of electricity to calculate pumping costs in direct-use heat only mode or revenue" +
            " from electricity sales in CHP mode."
        )

        # local variable initialization
        self.setinjectionpressurefixed = False
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = os.path.abspath(__file__)

        #heat pump
        self.heatpumpcop = self.ParameterDict[self.heatpumpcop.Name] = floatParameter(
            "Heat Pump COP",
            value = 5,
            Min=1,
            Max = 10,
            UnitType = Units.PERCENT,
            PreferredUnits = PercentUnit.TENTH,
            CurrentUnits = PercentUnit.TENTH,
            ErrMessage="assume default heat pump COP (5)",
            ToolTipText="Specify the coefficient of performance (COP) of the heat pump"
        )

        # Results - used by other objects or printed in output downstream
        self.SUTRATimeStep = self.OutputParameterDict[self.SUTRATimeStep.Name] = OutputParameter(
            Name="Time Step used in SUTRA",
            value=[0.0],
            UnitType=Units.TIME,
            PreferredUnits=TimeUnit.HOUR,
            CurrentUnits=TimeUnit.HOUR
        )

        self.HeatInjected = self.OutputParameterDict[self.HeatInjected.Name] = OutputParameter(
            Name="Heat Injected",
            value=[0.0],
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )
        self.HeatProduced = self.OutputParameterDict[self.HeatProduced.Name] = OutputParameter(
            Name="Heat Produced",
            value=[0.0],
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )

        self.AuxiliaryHeatProduced = self.OutputParameterDict[self.AuxiliaryHeatProduced.Name] = OutputParameter(
            Name="Auxiliary Heat Produced",
            value=[0.0],
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )

        self.TotalHeatProduced = self.OutputParameterDict[self.TotalHeatProduced.Name] = OutputParameter(
            Name="Total Heat Produced",
            value=[0.0],
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )

        self.AnnualHeatInjected = self.OutputParameterDict[self.AnnualHeatInjected.Name] = OutputParameter(
            Name="Annual Heat Injected",
            value=[0.0],
            UnitType=Units.ENERGYFREQUENCY,
            PreferredUnits=EnergyFrequencyUnit.GWhPERYEAR,
            CurrentUnits=EnergyFrequencyUnit.GWhPERYEAR
        )

        self.AnnualHeatProduced = self.OutputParameterDict[self.AnnualHeatProduced.Name] = OutputParameter(
            Name="Annual Heat Produced",
            value=[0.0],
            UnitType=Units.ENERGYFREQUENCY,
            PreferredUnits=EnergyFrequencyUnit.GWhPERYEAR,
            CurrentUnits=EnergyFrequencyUnit.GWhPERYEAR
        )

        self.AnnualAuxiliaryHeatProduced = self.OutputParameterDict[self.AnnualAuxiliaryHeatProduced.Name] = OutputParameter(
            Name="Annual Auxiliary Heat Produced",
            value=[0.0],
            UnitType=Units.ENERGYFREQUENCY,
            PreferredUnits=EnergyFrequencyUnit.GWhPERYEAR,
            CurrentUnits=EnergyFrequencyUnit.GWhPERYEAR
        )

        self.AnnualTotalHeatProduced = self.OutputParameterDict[self.AnnualTotalHeatProduced.Name] = OutputParameter(
            Name="Annual Total Heat Produced",
            value=[0.0],
            UnitType=Units.ENERGYFREQUENCY,
            PreferredUnits=EnergyFrequencyUnit.GWhPERYEAR,
            CurrentUnits=EnergyFrequencyUnit.GWhPERYEAR
        )

        self.PumpingkWh = self.OutputParameterDict[self.PumpingkWh.Name] = OutputParameter(
            Name="Annual Pumping Electricity Required",
            value=[],
            UnitType=Units.ENERGYFREQUENCY,
            PreferredUnits=EnergyFrequencyUnit.KWhPERYEAR,
            CurrentUnits=EnergyFrequencyUnit.KWhPERYEAR
        )

        self.maxpeakingboilerdemand = self.OutputParameterDict[self.maxpeakingboilerdemand.Name] = OutputParameter(
            Name = "Maximum Peaking Boiler Natural Gas Demand",
            value=[0.0],
            UnitType = Units.POWER,
            PreferredUnits = PowerUnit.MW,
            CurrentUnits = PowerUnit.MW
        )

        #heat pump (potentially used in the future)
        self.HeatPumpElectricityUsed = self.OutputParameterDict[self.HeatPumpElectricityUsed.Name] = OutputParameter(
            Name = "Heat Pump Electricity Consumed",
            value=[0.0],
            UnitType = Units.POWER,
            PreferredUnits = PowerUnit.MW,
            CurrentUnits = PowerUnit.MW
        )
        self.HeatPumpElectricitykWhUsed = self.OutputParameterDict[self.HeatPumpElectricitykWhUsed.Name] = OutputParameter(
            Name = "Annual Heat Pump Electricity Consumption",
            value=[0.0],
            UnitType = Units.ENERGYFREQUENCY,
            PreferredUnits = EnergyFrequencyUnit.KWhPERYEAR,
            CurrentUnits = EnergyFrequencyUnit.KWhPERYEAR
        )

        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def __str__(self):
        return "SurfacePlant"

    def read_parameters(self, model:Model) -> None:
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

        # Deal with all the parameter values that the user has provided.  They should really only provide values that
        # they want to change from the default values, but they can provide a value that is already set because it is a
        # default value set in __init__.  It will ignore those.
        # This also deals with all the special cases that need to be taken care of after a value has been
        # read in and checked.
        # If you choose to subclass this master class, you can also choose to override this method (or not),
        # and if you do, do it before or after you call you own version of this method.
        # If you do, you can also choose to call this method from you class, which can effectively modify all
        # these superclass parameters in your class.

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
                    # this should handle all the non-special cases
                    ReadParameter(ParameterReadIn, ParameterToModify, model)

                    # handle special cases
                    if ParameterToModify.Name == "End-Use Option":
                        if ParameterReadIn.sValue == str(1):
                            ParameterToModify.value = EndUseOptions.ELECTRICITY
                        elif ParameterReadIn.sValue == str(2):
                            ParameterToModify.value = EndUseOptions.HEAT
                        elif ParameterReadIn.sValue == str(31):
                            ParameterToModify.value = EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT
                        elif ParameterReadIn.sValue == str(32):
                            ParameterToModify.value = EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICTY
                        elif ParameterReadIn.sValue == str(41):
                            ParameterToModify.value = EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT
                        elif ParameterReadIn.sValue == str(42):
                            ParameterToModify.value = EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICTY
                        elif ParameterReadIn.sValue == str(51):
                            ParameterToModify.value = EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT
                        elif ParameterReadIn.sValue == str(52):
                            ParameterToModify.value = EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICTY
                        elif ParameterReadIn.sValue == str(6):
                            ParameterToModify.value = EndUseOptions.ABSORPTION_CHILLER
                        elif ParameterReadIn.sValue == str(7):
                            ParameterToModify.value = EndUseOptions.HEAT_PUMP
                        elif ParameterReadIn.sValue == str(8):
                            ParameterToModify.value = EndUseOptions.DISTRICT_HEATING
                        elif ParameterReadIn.sValue == str(9):
                            ParameterToModify.value = EndUseOptions.RTES

        else:
            model.logger.info("No parameters read because no content provided")
        model.logger.info("complete "+ str(__class__) + ": " + sys._getframe().f_code.co_name)

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
        # and if you do, do it before or after you call you own version of this method.  If you do, you can also choose
        # to call this method from you class, which can effectively run the calculations of the superclass, making all
        # the values available to your methods. but you had better have set all the parameters!


        # calculate and instantaneous heat injected, geothermal heat supplied, auxiliary heating required and total heat produced
        TimeVector = np.append(model.reserv.TimeProfile.value[0:-1:2],model.reserv.TimeProfile.value[-1])
        self.SUTRATimeStep.value = TimeVector[-1]/len(TimeVector)
        TargetHeat = np.append(model.reserv.TargetHeat.value[0:-1:2],model.reserv.TargetHeat.value[-1])
        SimulatedHeat = np.append(model.reserv.SimulatedHeat.value[0:-1:2],model.reserv.SimulatedHeat.value[-1])
        AuxiliaryHeat = TargetHeat-SimulatedHeat
        AuxiliaryHeat[AuxiliaryHeat<0] = 0 #set negative values to 0
        SimulatedHeatInjected = np.copy(SimulatedHeat)
        SimulatedHeatInjected[SimulatedHeatInjected>0] = 0
        SimulatedHeatProduced = np.copy(SimulatedHeat)
        SimulatedHeatProduced[SimulatedHeatProduced < 0] = 0
        self.HeatInjected.value = SimulatedHeatInjected/(self.SUTRATimeStep.value)/1e3
        self.HeatProduced.value = SimulatedHeatProduced/(self.SUTRATimeStep.value)/1e3
        self.AuxiliaryHeatProduced.value = AuxiliaryHeat/(self.SUTRATimeStep.value)/1e3
        self.TotalHeatProduced.value = SimulatedHeatProduced/(self.SUTRATimeStep.value)/1e3 + AuxiliaryHeat/(self.SUTRATimeStep.value)/1e3

        # calculate annual heat injected, geothermal heat supplied, total heat supplied, backup heating required and pumping electricity
        self.AnnualHeatInjected.value = np.zeros(round(TimeVector[-1]/8766))
        self.AnnualHeatProduced.value = np.zeros(round(TimeVector[-1] / 8766))
        self.AnnualAuxiliaryHeatProduced.value = np.zeros(round(TimeVector[-1] / 8766))
        self.AnnualTotalHeatProduced.value = np.zeros(round(TimeVector[-1] / 8766))
        self.PumpingkWh.value = np.zeros(round(TimeVector[-1] / 8766))
        for i in range(round(TimeVector[-1]/8766)):
            self.AnnualHeatInjected.value[i] = sum(self.HeatInjected.value[0+i*730:(i+1)*730])*self.SUTRATimeStep.value/1000
            self.AnnualHeatProduced.value[i] = sum(self.HeatProduced.value[0+i*730:(i+1)*730])*self.SUTRATimeStep.value/1000
            self.AnnualAuxiliaryHeatProduced.value[i] = sum(self.AuxiliaryHeatProduced.value[0+i*730:(i+1)*730])*self.SUTRATimeStep.value/1000
            self.AnnualTotalHeatProduced.value[i] = sum(self.TotalHeatProduced.value[0+i*730:(i+1)*730])*self.SUTRATimeStep.value/1000
            self.PumpingkWh.value[i] = sum(model.wellbores.PumpingPower.value[0+i*730:(i+1)*730])*self.SUTRATimeStep.value*1000

        #calculate maximum auxilary boiler demand
        self.maxpeakingboilerdemand.value = max(self.AnnualAuxiliaryHeatProduced.value)

        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)


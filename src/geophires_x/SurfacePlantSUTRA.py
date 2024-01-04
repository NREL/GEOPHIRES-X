from pathlib import Path
import numpy as np
from .Parameter import OutputParameter
from .SurfacePlant import SurfacePlant
from .Units import *
import geophires_x.Model as Model


class surface_plant_sutra(SurfacePlant):
    def __init__(self, model: Model):
        """
        The __init__ function is called automatically when a class is instantiated.
        It initializes the attributes of an object, and sets default values for certain arguments that can be overridden
         by user input.
        The __init__ function is used to set up all the parameters in the Surfaceplant.
        Set up all the Parameters that will be predefined by this class using the different types of parameter classes.
        Setting up includes giving it a name, a default value, The Unit Type (length, volume, temperature, etc.) and
        Unit Name of that value, sets it as required (or not), sets allowable range, the error message if that range
        is exceeded, the ToolTip Text, and the name of teh class that created it.
        This includes setting up temporary variables that will be available to all the class but noy read in by user,
        or used for Output
        This also includes all Parameters that are calculated and then published using the Printouts function.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """

        model.logger.info(f"Init {self.__class__.__name__}: {self.__init__.__name__}")

        # These dictionaries contain a list of all the parameters set in this object, stored as "Parameter" and
        # "OutputParameter" Objects.  This will allow us later to access them in a user interface and get that list,
        # along with unit type, preferred units, etc.
        super().__init__(model)  # Initialize all the parameters in the superclass

        # local variable initialization
        sclass = self.__class__.__name__
        self.MyClass = sclass
        self.MyPath = Path(__file__).resolve()

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

        model.logger.info(f"Complete {self.__class__.__name__}: {self.__init__.__name__}")

    def __str__(self):
        return "SurfacePlantSUTRA"

    def read_parameters(self, model:Model) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary and stores them in the parameters.
        It also handles special cases that need to be handled after a value has been read in and checked.
        If you choose to subclass this master class, you can also choose to override this method (or not), and if you do
        Deal with all the parameter values that the user has provided.  They should really only provide values that
        they want to change from the default values, but they can provide a value that is already set because it is a
        default value set in __init__.  It will ignore those.
        This also deals with all the special cases that need to be taken care of after a value has been
        read in and checked.
        If you choose to subclass this master class, you can also choose to override this method (or not),
        and if you do, do it before or after you call you own version of this method.
        If you do, you can also choose to call this method from you class, which can effectively modify all
        these superclass parameters in your class.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        model.logger.info(f"Init {self.__class__.__name__}: {self.__init__.__name__}")
        super().read_parameters(model)  # Read in all the parameters from the superclass
        model.logger.info(f"complete {self.__class__.__name__}: {self.__init__.__name__}")

    def Calculate(self, model: Model) -> None:
        """
        The Calculate function is where all the calculations are done.
        This function can be called multiple times, and will only recalculate what has changed each time it is called.
        This is where all the calculations are made using all the values that have been set.
        If you subclass this class, you can choose to run these calculations before (or after) your calculations,
        but that assumes you have set all the values that are required for these calculations
        If you choose to subclass this master class, you can also choose to override this method (or not),
        and if you do, do it before or after you call you own version of this method.  If you do, you can also choose
        to call this method from you class, which can effectively run the calculations of the superclass, making all
        the values available to your methods. but you had better have set all the parameters!
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing, but it does make calculations and set values in the model
        """
        model.logger.info(f"Init {self.__class__.__name__}: {self.__init__.__name__}")

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
            self.PumpingkWh.value[i] = sum(model.wellbores.PumpingPower.value[0+i*730:(i+1)*730])*self.SUTRATimeStep.value

        # calculate maximum auxiliary boiler demand
        self.maxpeakingboilerdemand.value = max(self.AnnualAuxiliaryHeatProduced.value)

        model.logger.info(f"complete {self.__class__.__name__}: {self.__init__.__name__}")


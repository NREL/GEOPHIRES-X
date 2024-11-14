import inspect
from pathlib import Path
import numpy as np
from geophires_x.Parameter import floatParameter, OutputParameter
from geophires_x.SurfacePlant import SurfacePlant
from geophires_x.Units import *
import geophires_x.Model as Model


class SurfacePlantHeatPump(SurfacePlant):
    def __init__(self, model: Model):
        """
        The __init__ function is called automatically when a class is instantiated.
        It initializes the attributes of an object, and sets default values for certain arguments that can be overridden
         by user input.
        The __init__ function is used to set up all the parameters in the Surfaceplant.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """

        model.logger.info("Init " + str(__class__) + ": " + inspect.currentframe().f_code.co_name)
        super().__init__(model)  # Initialize all the parameters in the superclass

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

        # local variable initialization
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = Path(__file__).resolve()

        self.heat_pump_cop = self.ParameterDict[self.heat_pump_cop.Name] = floatParameter(
            "Heat Pump COP",
            DefaultValue=5,
            Min=1,
            Max=10,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default heat pump COP (5)",
            ToolTipText="Specify the coefficient of performance (COP) of the heat pump"
        )

        # Results - used by other objects or printed in output downstream
        self.heat_pump_electricity_used = self.OutputParameterDict[self.heat_pump_electricity_used.Name] = OutputParameter(
            Name="Heat Pump Electricity Consumed",
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )
        self.heat_pump_electricity_kwh_used = self.OutputParameterDict[self.heat_pump_electricity_kwh_used.Name] = OutputParameter(
            Name = "Annual Heat Pump Electricity Consumption",
            UnitType=Units.ENERGYFREQUENCY,
            PreferredUnits=EnergyFrequencyUnit.KWhPERYEAR,
            CurrentUnits=EnergyFrequencyUnit.KWhPERYEAR
        )

        model.logger.info("Complete " + str(__class__) + ": " + inspect.currentframe().f_code.co_name)

    def __str__(self):
        return "SurfacePlantHeatPump"

    def read_parameters(self, model:Model) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary and stores them in the parameters.
        It also handles special cases that need to be handled after a value has been read in and checked.
        If you choose to subclass this master class, you can also choose to override this method (or not), and if you do
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: None
        """
        model.logger.info("Init " + str(__class__) + ": " + inspect.currentframe().f_code.co_name)
        super().read_parameters(model)  # Read in all the parameters from the superclass

        # Since there are no parameters unique to this class, we don't need to read any in here.

        model.logger.info("complete "+ str(__class__) + ": " + inspect.currentframe().f_code.co_name)

    def Calculate(self, model: Model) -> None:
        """
        The Calculate function is where all the calculations are done.
        This function can be called multiple times, and will only recalculate what has changed each time it is called.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing, but it does make calculations and set values in the model
        """
        model.logger.info("Init " + str(__class__) + ": " + inspect.currentframe().f_code.co_name)

        # This is where all the calculations are made using all the values that have been set.
        # If you subclass this class, you can choose to run these calculations before (or after) your calculations,
        # but that assumes you have set all the values that are required for these calculations
        # If you choose to subclass this master class, you can also choose to override this method (or not),
        # and if you do, do it before or after you call you own version of this method.  If you do, you can also choose
        # to call this method from you class, which can effectively run the calculations of the superclass, making all
        # the values available to your methods. but you had better have set all the parameters!

        self.HeatExtracted.value = model.wellbores.nprod.value * model.wellbores.prodwellflowrate.value * model.reserv.cpwater.value * (
                model.wellbores.ProducedTemperature.value - model.wellbores.Tinj.value) / 1E6  # heat extracted from geofluid [MWth]

        self.HeatProduced.value = (self.HeatExtracted.value * self.heat_pump_cop.value / (self.heat_pump_cop.value - 1) *
                                   self.enduse_efficiency_factor.value)  # [MWth]
        self.heat_pump_electricity_used.value = self.HeatExtracted.value / (self.heat_pump_cop.value - 1)

        # Calculate annual electricity/heat production
        # all end-use options have "heat extracted from reservoir" and pumping kWs
        self.HeatkWhExtracted.value = np.zeros(self.plant_lifetime.value)
        self.PumpingkWh.value = np.zeros(self.plant_lifetime.value)

        for i in range(0, self.plant_lifetime.value):
            self.HeatkWhExtracted.value[i] = np.trapz(self.HeatExtracted.value[(0 + i * model.economics.timestepsperyear.value):((i + 1) * model.economics.timestepsperyear.value) + 1],dx=1. / model.economics.timestepsperyear.value * 365. * 24.) * 1000. * self.utilization_factor.value
            self.PumpingkWh.value[i] = np.trapz(model.wellbores.PumpingPower.value[(0 + i * model.economics.timestepsperyear.value):((i + 1) * model.economics.timestepsperyear.value) + 1],dx=1. / model.economics.timestepsperyear.value * 365. * 24.) * 1000. * self.utilization_factor.value

        self.HeatkWhProduced.value = np.zeros(self.plant_lifetime.value)
        for i in range(0, self.plant_lifetime.value):
            self.HeatkWhProduced.value[i] = np.trapz(self.HeatProduced.value[(0+i*model.economics.timestepsperyear.value):((i+1)*model.economics.timestepsperyear.value)+1],dx = 1./model.economics.timestepsperyear.value*365.*24.)*1000.*self.utilization_factor.value

        self.heat_pump_electricity_kwh_used.value = np.zeros(self.plant_lifetime.value)
        for i in range(0, self.plant_lifetime.value):
            self.heat_pump_electricity_kwh_used.value[i] = np.trapz(self.heat_pump_electricity_used.value[(0 + i * model.economics.timestepsperyear.value):((i + 1) * model.economics.timestepsperyear.value) + 1], dx =1. / model.economics.timestepsperyear.value * 365. * 24.) * 1000. * self.utilization_factor.value

        # calculate reservoir heat content
        self.RemainingReservoirHeatContent.value = SurfacePlant.remaining_reservoir_heat_content(
            self, model.reserv.InitialReservoirHeatContent.value, self.HeatkWhExtracted.value)

        model.logger.info("complete " + str(__class__) + ": " + inspect.currentframe().f_code.co_name)

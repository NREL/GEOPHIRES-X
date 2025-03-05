import numpy as np
from .Parameter import floatParameter, OutputParameter
from .SurfacePlant import SurfacePlant
from .Units import *
import geophires_x.Model as Model


class SurfacePlantAbsorptionChiller(SurfacePlant):
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

        model.logger.info(f"Init {self.__class__.__name__}: {__name__}")
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

        self.setinjectionpressurefixed = False
        self.MyClass = self.__class__.__name__
        self.MyPath = __file__

        # Input parameters absorption chiller
        self.absorption_chiller_cop = self.ParameterDict[self.absorption_chiller_cop.Name] = floatParameter(
            "Absorption Chiller COP",
            value=0.7,
            Min=0.1,
            Max=1.5,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH, CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default absorption chiller COP (0.7)",
            ToolTipText="Specify the coefficient of performance (COP) of the absorption chiller"
        )

        # Output Parameters
        self.cooling_produced = self.OutputParameterDict[self.cooling_produced.Name] = OutputParameter(
            Name="Cooling Produced",
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )
        self.cooling_kWh_Produced = self.OutputParameterDict[self.cooling_kWh_Produced.Name] = OutputParameter(
            Name="Annual Cooling Produced",
            UnitType=Units.ENERGYFREQUENCY,
            PreferredUnits=EnergyFrequencyUnit.KWhPERYEAR,
            CurrentUnits=EnergyFrequencyUnit.KWhPERYEAR
        )

        model.logger.info(f"Complete {self.__class__.__name__}: {__name__}")

    def __str__(self):
        return "SurfacePlantAbsorptionChiller"

    def read_parameters(self, model: Model) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary and stores them in the parameters.
        It also handles special cases that need to be handled after a value has been read in and checked.
        If you choose to subclass this master class, you can also choose to override this method (or not), and if you do
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: None
        """
        model.logger.info(f"Init {self.__class__.__name__}: {__name__}")
        super().read_parameters(model)  # Read in all the parameters from the superclass

        # Since there are no parameters that require unique adjustments in this class, we don't need to do anything.

        model.logger.info(f"complete {self.__class__.__name__}: {__name__}")

    def Calculate(self, model: Model) -> None:
        """
        The Calculate function is where all the calculations are done.
        This function can be called multiple times, and will only recalculate what has changed each time it is called.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing, but it does make calculations and set values in the model
        """
        model.logger.info(f"Init {self.__class__.__name__}: {__name__}")

        # This is where all the calculations are made using all the values that have been set.
        # If you subclass this class, you can choose to run these calculations before (or after) your calculations,
        # but that assumes you have set all the values that are required for these calculations
        # If you choose to subclass this master class, you can also choose to override this method (or not),
        # and if you do, do it before or after you call you own version of this method.  If you do, you can also choose
        # to call this method from you class, which can effectively run the calculations of the superclass, making all
        # the values available to your methods. but you had better have set all the parameters!

        # calculate produced electricity/direct-use heat
        # absorption chiller: we don't consider end-use efficiency factor here.
        # All extracted heat will go to absorption chiller and there is the end-use efficiency factor. [MWth]
        self.HeatExtracted.value = model.wellbores.nprod.value * model.wellbores.prodwellflowrate.value * model.reserv.cpwater.value * (
            model.wellbores.ProducedTemperature.value - model.wellbores.Tinj.value) / 1E6  # heat extracted from geofluid [MWth]
        self.HeatProduced.value = self.HeatExtracted.value

        self.cooling_produced.value = self.HeatProduced.value * self.absorption_chiller_cop.value * self.enduse_efficiency_factor.value  # MW

        # Calculate annual electricity/heat production
        # all end-use options have "heat extracted from reservoir" and pumping kWs
        self.HeatkWhExtracted.value = np.zeros(self.plant_lifetime.value)
        self.PumpingkWh.value = np.zeros(self.plant_lifetime.value)

        for i in range(0, self.plant_lifetime.value):
            # FIXME TODO WIP adjust dx for slice size
            self.HeatkWhExtracted.value[i] = np.trapz(self.HeatExtracted.value[
                                            (0 + i * model.economics.timestepsperyear.value):((
                                            i + 1) * model.economics.timestepsperyear.value) + 1],
                                            dx=1. / model.economics.timestepsperyear.value * 365. * 24.) * 1000. * self.utilization_factor.value
            self.PumpingkWh.value[i] = np.trapz(model.wellbores.PumpingPower.value[
                                                (0 + i * model.economics.timestepsperyear.value):((
                                                i + 1) * model.economics.timestepsperyear.value) + 1],
                                                dx=1. / model.economics.timestepsperyear.value * 365. * 24.) * 1000. * self.utilization_factor.value

        self.HeatkWhProduced.value = np.zeros(self.plant_lifetime.value)
        for i in range(0, self.plant_lifetime.value):
            # FIXME TODO WIP adjust dx for slice size
            self.HeatkWhProduced.value[i] = np.trapz(self.HeatProduced.value[
                                                     (0 + i * model.economics.timestepsperyear.value):((
                                                    i + 1) * model.economics.timestepsperyear.value) + 1],
                                                     dx=1. / model.economics.timestepsperyear.value * 365. * 24.) * 1000. * self.utilization_factor.value

        self.cooling_kWh_Produced.value = np.zeros(self.plant_lifetime.value)
        for i in range(0, self.plant_lifetime.value):
            # FIXME TODO WIP adjust dx for slice size
            self.cooling_kWh_Produced.value[i] = np.trapz(self.cooling_produced.value[
                                                        (0 + i * model.economics.timestepsperyear.value):((
                                                        i + 1) * model.economics.timestepsperyear.value) + 1],
                                                          dx=1. / model.economics.timestepsperyear.value * 365. * 24.) * 1000. * self.utilization_factor.value

        # calculate reservoir heat content
        self.RemainingReservoirHeatContent.value = SurfacePlant.remaining_reservoir_heat_content(
            self, model.reserv.InitialReservoirHeatContent.value, self.HeatkWhExtracted.value)

        self._calculate_derived_outputs(model)
        model.logger.info(f"complete {self.__class__.__name__}: {__name__}")

import sys
from pathlib import Path
import numpy as np
from geophires_x.OptionList import EndUseOptions
from geophires_x.SurfacePlant import SurfacePlant
import geophires_x.Model as Model

class surface_plant_single_flash(SurfacePlant):
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

        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)
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
        sclass = self.__class__.__name__
        self.MyClass = sclass
        self.MyPath = Path(__file__).resolve()
        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def __str__(self):
        return "SurfacePlantSingleFlash"

    def read_parameters(self, model:Model) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary and stores them in the parameters.
        It also handles special cases that need to be handled after a value has been read in and checked.
        If you choose to subclass this master class, you can also choose to override this method (or not), and if you do
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: None
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)
        super().read_parameters(model)  # Initialize all the parameters in the superclass
        model.logger.info("complete "+ str(__class__) + ": " + sys._getframe().f_code.co_name)

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
        # and if you do, do it before or after you call you own version of this method.  If you do, you can also choose
        # to call this method from you class, which can effectively run the calculations of the superclass, making all
        # the values available to your methods. but you had better have set all the parameters!

        # calculate power plant entering temperature
        self.TenteringPP.value = SurfacePlant.power_plant_entering_temperature(self, self.enduse_option.value,
                                model.reserv.timevector.value, self.T_chp_bottom.value, model.wellbores.ProducedTemperature.value)

        # Availability water
        self.Availability.value = SurfacePlant.availability_water(self, self.ambient_temperature.value, self.TenteringPP.value, self.ambient_temperature.value)

        # Single flash-specific values.
        if self.ambient_temperature.value < 15.:
            C21 = -4.27318E-7
            C11 = 8.65629E-4
            C01 = 1.78931E-1
            D21 = -5.85412E-7
            D11 = 9.68352E-4
            D01 = 1.58056E-1
            C22 = -1.11519E-3
            C12 = 7.79126E-1
            C02 = -10.2242
            D22 = -1.10232E-3
            D12 = 7.83893E-1
            D02 = -5.17039
        else:
            C21 = -5.85412E-7
            C11 = 9.68352E-4
            C01 = 1.58056E-1
            D21 = -7.78996E-7
            D11 = 1.09230E-3
            D01 = 1.33708E-1
            C22 = -1.10232E-3
            C12 = 7.83893E-1
            C02 = -5.17039
            D22 = -1.08914E-3
            D12 = 7.88562E-1
            D02 = -1.89707E-1

        model.wellbores.Tinj.value, ReinjTemp, etau = SurfacePlant.reinjection_temperature(self, model,
                                                    self.ambient_temperature.value, self.TenteringPP.value, model.wellbores.Tinj.value,
                                                    C01, C11, C21, D01, D11, D21, C02, C12, C22, D02, D12, D22)

        # calculate electricity & heat production
        self.ElectricityProduced.value, self.HeatExtracted.value, self.HeatProduced.value, HeatExtractedTowardsElectricity = \
        SurfacePlant.electricity_heat_production(self, self.enduse_option.value, self.Availability.value, etau,
                                                model.wellbores.nprod.value, model.wellbores.prodwellflowrate.value,
                                                model.reserv.cpwater.value, model.wellbores.ProducedTemperature.value,
                                                model.wellbores.Tinj.value, ReinjTemp, self.T_chp_bottom.value,
                                                 self.enduse_efficiency_factor.value, self.chp_fraction.value)

        # subtract pumping power for net electricity and  calculate first law efficiency
        self.NetElectricityProduced.value = self.ElectricityProduced.value - model.wellbores.PumpingPower.value
        self.FirstLawEfficiency.value = self.NetElectricityProduced.value/HeatExtractedTowardsElectricity

        # Calculate annual electricity, pum;ping, and heat production
        self.HeatkWhExtracted.value, self.PumpingkWh.value, self.TotalkWhProduced.value, self.NetkWhProduced.value, self.HeatkWhProduced.value = \
        SurfacePlant.annual_electricity_pumping_power(self, self.plant_lifetime.value, self.enduse_option.value,
                                self.HeatExtracted.value, model.economics.timestepsperyear.value, self.utilization_factor.value,
                                model.wellbores.PumpingPower.value, self.ElectricityProduced.value,
                                self.NetElectricityProduced.value, self.HeatProduced.value)

        # calculate reservoir heat content
        self.RemainingReservoirHeatContent.value = SurfacePlant.remaining_reservoir_heat_content(
            self, model.reserv.InitialReservoirHeatContent.value, self.HeatkWhExtracted.value)

        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

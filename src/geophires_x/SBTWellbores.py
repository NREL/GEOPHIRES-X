import math
import sys
import numpy as np
from pint.facets.plain import PlainQuantity

from geophires_x.WellBores import (WellBores, RameyCalc, WellPressureDrop, \
    ProdPressureDropsAndPumpingPowerUsingImpedenceModel, ProdPressureDropAndPumpingPowerUsingIndexes)
from geophires_x.Economics import calculate_total_drilling_lengths_m
from .Parameter import floatParameter, intParameter, boolParameter, OutputParameter, ReadParameter
from geophires_x.GeoPHIRESUtils import vapor_pressure_water_kPa, quantity, static_pressure_MPa, \
    heat_capacity_water_J_per_kg_per_K
from geophires_x.GeoPHIRESUtils import density_water_kg_per_m3
from geophires_x.GeoPHIRESUtils import viscosity_water_Pa_sec
from .Units import *
import geophires_x.Model as Model
from .OptionList import ReservoirModel, Configuration, WorkingFluid


class SBTWellbores(WellBores):
    """
    SBTWellbores Child class of AGSWellBores; it is the same, but has advanced SBT closed-loop functionality
    """

    def __init__(self, model: Model):
        """
        The __init__ function is the constructor for a class. It is called whenever an instance of the class is created.
        The __init__ function can take arguments, but self is always the first one. Self refers to the instance of the
        object that has already been created, and it's used to access variables that belong to that object.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing, and is used to initialize the class
        """
        model.logger.info(f'Init {__class__!s}: {sys._getframe().f_code.co_name}')

        # Initialize the superclass first to gain access to those variables
        super().__init__(model)
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = os.path.abspath(__file__)
        self.Tini = 0.0

        # Set up the Parameters that will be predefined by this class using the different types of parameter classes.
        # Setting up includes giving it a name, a default value, The Unit Type (length, volume, temperature, etc.) and
        # Unit Name of that value, sets it as required (or not), sets allowable range, the error message if that range
        # is exceeded, the ToolTip Text, and the name of teh class that created it.
        # This includes setting up temporary variables that will be available to all the class but noy read in by user,
        # or used for Output
        # This also includes all Parameters that are calculated and then published using the Printouts function.
        # If you choose to subclass this master class, you can do so before or after you create your own parameters.
        # If you do, you can also choose to call this method from you class, which will effectively add and set all
        # these parameters to your class.
        # NB: inputs we already have ("already have it") need to be set at ReadParameter time so values are set at the
        # last possible time

        self.vertical_section_length = self.ParameterDict[self.vertical_section_length.Name] = floatParameter(
            'Vertical Section Length',
            DefaultValue=2000.0,
            Min=0.01,
            Max=10000.0,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.METERS,
            CurrentUnits=LengthUnit.METERS,
            ErrMessage='assume default for Vertical Section Length (2000.0 meters)',
            ToolTipText='length/depth to the bottom of the vertical wellbores'
        )
        self.vertical_wellbore_spacing = self.ParameterDict[self.vertical_wellbore_spacing.Name] = floatParameter(
            'Vertical Wellbore Spacing',
            DefaultValue=100.0,
            Min=0.01,
            Max=10000.0,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.METERS,
            CurrentUnits=LengthUnit.METERS,
            ErrMessage='assume default for Vertical Wellbore Spacing (100.0 meters)',
            ToolTipText='Horizontal distance between vertical wellbores'
        )
        self.lateral_spacing = self.ParameterDict[self.lateral_spacing.Name] = floatParameter(
            'Lateral Spacing',
            DefaultValue=100.0,
            Min=0.01,
            Max=10000.0,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.METERS,
            CurrentUnits=LengthUnit.METERS,
            ErrMessage='assume default for Lateral Spacing (100.0 meters)',
            ToolTipText='Horizontal distance between laterals'
        )
        self.lateral_inclination_angle = self.ParameterDict[self.lateral_inclination_angle.Name] = floatParameter(
            'Lateral Inclination Angle',
            DefaultValue=20.0,
            Min=0.0,
            Max=89.999999,
            UnitType=Units.ANGLE,
            PreferredUnits=AngleUnit.DEGREES,
            CurrentUnits=AngleUnit.DEGREES,
            ErrMessage='assume default for Lateral Inclination Angle (20.0 degrees)',
            ToolTipText='Inclination of the lateral section, where 0 degrees would mean vertical while 90 degrees is pure horizontal'
        )
        self.element_length = self.ParameterDict[self.element_length.Name] = floatParameter(
            'Discretization Length',
            DefaultValue=250.0,
            Min=0.01,
            Max=10000.0,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.METERS,
            CurrentUnits=LengthUnit.METERS,
            ErrMessage='assume default for Discretization Length (250.0 meters)',
            ToolTipText='distance between sample point along length of model'
        )
        self.junction_depth = self.ParameterDict[self.junction_depth.Name] = floatParameter(
            'Junction Depth',
            DefaultValue=4000.0,
            Min=1000,
            Max=15000.0,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.METERS,
            CurrentUnits=LengthUnit.METERS,
            ErrMessage='assume default for Junction Depth (4000.0 meters)',
            ToolTipText='vertical depth where the different laterals branch out (where the multilateral section starts, second deepest depth of model)'
        )
        self.lateral_endpoint_depth = self.ParameterDict[self.lateral_endpoint_depth.Name] = floatParameter(
            'Lateral Endpoint Depth',
            DefaultValue=7000.0,
            Min=1000,
            Max=15000.0,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.METERS,
            CurrentUnits=LengthUnit.METERS,
            ErrMessage='assume default for Lateral Endpoint Depth (7000.0 meters)',
            ToolTipText='vertical depth where the lateral section ends (tip of the multilateral section, deepest depth of model)'
        )

        model.logger.info(f'complete {__class__!s}: {sys._getframe().f_code.co_name}')

    def __str__(self):
        return 'SBTWellbores'

    def read_parameters(self, model: Model) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary and stores them in the parameters.
        It also handles special cases that need to be handled after a value has been read in and checked.
        If you choose to subclass this master class, you can also choose to override this method (or not), and if you do
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        model.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')
        super().read_parameters(model)  # read the default parameters
        # if we call super, we don't need to deal with setting the parameters here, just deal with the special cases
        # for the variables in this class because the call to the super.readparameters will set all the variables,
        # including the ones that are specific to this class

        if len(model.InputParameters) > 0:
            # loop through all the parameters that the user wishes to set, looking for parameters that match this object
            for item in self.ParameterDict.items():
                ParameterToModify = item[1]
                key = ParameterToModify.Name.strip()
                if key in model.InputParameters:
                    ParameterReadIn = model.InputParameters[key]
                    # just handle special cases for this class - the call to super set all the values,
                    # including the value unique to this class
        else:
            model.logger.info("No parameters read because no content provided")

        model.logger.info(f'complete {str(__class__)}: {sys._getframe().f_code.co_name}')

    def Calculate(self, model: Model) -> None:
        """
        The calculate function verifies, initializes, and extracts the values from the AGS model
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        model.logger.info(f'Init {__class__!s}: {sys._getframe().f_code.co_name}')
        self.Tini = np.max(model.reserv.Tresoutput.value)  # initial temperature of the reservoir
        self.ProducedTemperature.value = np.array(model.reserv.Tresoutput.value)

        # Calculate the drilled lengths
        self.tot_vert_m.value = self.vertical_section_length.quantity().to('km').magnitude
        input_vert_depth_km = self.vertical_section_length.quantity().to('km').magnitude
        output_vert_depth_km = self.lateral_endpoint_depth.quantity().to('km').magnitude
        junction_depth_km = self.junction_depth.quantity().to('km').magnitude
        angle_rad = ((90.0 * np.pi) / 180) - self.lateral_inclination_angle.quantity().to('radians').magnitude

        # Use the parents class implementation of calculate_total_drilling_lengths_m
        self.total_drilled_length.value, self.tot_vert_m.value, self.tot_lateral_m.value, self.tot_to_junction_m.value = \
            calculate_total_drilling_lengths_m(self.Configuration.value,
                                               self.numnonverticalsections.value,
                                               self.Nonvertical_length.value / 1000.0,
                                               input_vert_depth_km,
                                               output_vert_depth_km,
                                               self.nprod.value,
                                               self.ninj.value,
                                               junction_depth_km,
                                               angle_rad)
        self.total_drilled_length.value = self.total_drilled_length.value / 1000.0  # convert to km

        # Now use the parent's calculation to calculate the upgoing and downgoing pressure drops and pumping power
        self.PumpingPower.value = [0.0] * len(self.ProducedTemperature.value)  # initialize the array
        if self.productionwellpumping.value:
            self.rhowaterinj = density_water_kg_per_m3(
                model.reserv.Tsurf.value,
                pressure=model.reserv.hydrostatic_pressure()
            ) * np.linspace(1, 1,
                            len(self.ProducedTemperature.value))

            self.rhowaterprod = density_water_kg_per_m3(
                model.reserv.Trock.value,
                pressure=model.reserv.hydrostatic_pressure()
            ) * np.linspace(1, 1, len(self.ProducedTemperature.value))

            self.DPProdWell.value, f3, vprod, self.rhowaterprod = WellPressureDrop(model,
                                                                                   self.ProducedTemperature.value,
                                                                                   self.prodwellflowrate.value,
                                                                                   self.prodwelldiam.value,
                                                                                   self.impedancemodelused.value,
                                                                                   self.vertical_section_length.value)
            if self.impedancemodelused.value:  # assumed everything stays liquid throughout
                self.DPOverall.value, UpgoingPumpingPower, self.DPProdWell.value, self.DPReserv.value, self.DPBouyancy.value = \
                    ProdPressureDropsAndPumpingPowerUsingImpedenceModel(
                        f3, vprod,
                        self.rhowaterprod, self.rhowaterinj, self.rhowaterprod,
                        self.vertical_section_length.value, self.prodwellflowrate.value,
                        self.prodwelldiam.value, self.impedance.value,
                        self.nprod.value, model.reserv.waterloss.value, model.surfaceplant.pump_efficiency.value)
                self.DPOverall.value, DowngoingPumpingPower, self.DPProdWell.value, self.DPReserv.value, self.DPBouyancy.value = \
                    ProdPressureDropsAndPumpingPowerUsingImpedenceModel(
                        f3, vprod,
                        self.rhowaterinj, self.rhowaterprod, self.rhowaterprod,
                        self.vertical_section_length.value, self.prodwellflowrate.value,
                        self.injwelldiam.value, self.impedance.value,
                        self.ninj.value, model.reserv.waterloss.value, model.surfaceplant.pump_efficiency.value, 90.0, False)
                self.DPOverall.value, NonverticalPumpingPower, self.DPProdWell.value, self.DPReserv.value, self.DPBouyancy.value = \
                    ProdPressureDropsAndPumpingPowerUsingImpedenceModel(
                        f3, vprod,
                        self.rhowaterinj, self.rhowaterprod, self.rhowaterprod,
                        self.vertical_section_length.value, self.prodwellflowrate.value,
                        self.injwelldiam.value, self.impedance.value,
                        self.ninj.value, model.reserv.waterloss.value, model.surfaceplant.pump_efficiency.value,
                        self.lateral_inclination_angle.value, False)

            else:  # PI is used for both the verticals
                UpgoingPumpingPower, self.PumpingPowerProd.value, self.DPProdWell.value, self.Pprodwellhead.value = \
                    ProdPressureDropAndPumpingPowerUsingIndexes(
                        model, self.productionwellpumping.value,
                        self.usebuiltinppwellheadcorrelation,
                        model.reserv.Trock.value, self.vertical_section_length.value,
                        self.ppwellhead.value, self.PI.value,
                        self.prodwellflowrate.value, f3, vprod,
                        self.prodwelldiam.value, self.nprod.value, model.surfaceplant.pump_efficiency.value,
                        self.rhowaterprod)

                DowngoingPumpingPower, ppp2, dppw, ppwh = ProdPressureDropAndPumpingPowerUsingIndexes(
                    model, self.productionwellpumping.value,
                    self.usebuiltinppwellheadcorrelation,
                    model.reserv.Trock.value, self.vertical_section_length.value,
                    self.ppwellhead.value, self.PI.value,
                    self.prodwellflowrate.value, f3, vprod,
                    self.injwelldiam.value, self.nprod.value, model.surfaceplant.pump_efficiency.value,
                    self.rhowaterinj)

            # Calculate Nonvertical Pressure Drop
            # TODO assume no pressure drop in the non-vertical section for now
            #NonverticalPumpingPower = [0.0] * len(DowngoingPumpingPower)  # initialize the array
            #self.NonverticalPressureDrop.value = [0.0] * len(DowngoingPumpingPower)  # initialize the array
            #NonverticalPumpingPower = [0.0] * len(DowngoingPumpingPower)  # initialize the array

            # recalculate the pumping power by looking at the difference between the upgoing and downgoing and the nonvertical
            self.PumpingPower.value = np.array(DowngoingPumpingPower) + np.array(NonverticalPumpingPower) + np.array(UpgoingPumpingPower)
            self.PumpingPower.value = [max(x, 0.) for x in self.PumpingPower.value]  # cannot be negative, so set to 0

        # calculate water values based on initial temperature, Need this for surface plant output calculation
        rho_water = density_water_kg_per_m3(np.average(self.ProducedTemperature.value), model.reserv.lithostatic_pressure())
        model.reserv.cpwater.value = heat_capacity_water_J_per_kg_per_K(np.average(self.ProducedTemperature.value), model.reserv.hydrostatic_pressure(),)

        # set pumping power to zero for all times, assuming that the thermosphere wil always
        # make pumping of working fluid unnecessary
        self.PumpingPower.value = [0.0] * (len(self.DPOverall.value))
        self.PumpingPower.value = self.DPOverall.value * self.prodwellflowrate.value / rho_water / model.surfaceplant.pump_efficiency.value / 1E3
        # in GEOPHIRES v1.2, negative pumping power values become zero
        # (b/c we are not generating electricity) = thermosiphon is happening!
        self.PumpingPower.value = [max(x, 0.) for x in self.PumpingPower.value]

        model.logger.info(f'complete {str(__class__)}: {sys._getframe().f_code.co_name}')

    def CalculateNonverticalPressureDrop(self, model, value, time_max, al):
        pass


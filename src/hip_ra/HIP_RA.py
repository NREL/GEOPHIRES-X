from __future__ import annotations

import logging
import logging.config
import math
import os
import sys
import traceback

from geophires_x.GeoPHIRESUtils import DensityWater
from geophires_x.GeoPHIRESUtils import EnthalpyH20_func
from geophires_x.GeoPHIRESUtils import EntropyH20_func
from geophires_x.GeoPHIRESUtils import HeatCapacityWater
from geophires_x.GeoPHIRESUtils import RecoverableHeat
from geophires_x.GeoPHIRESUtils import UtilEff_func
from geophires_x.GeoPHIRESUtils import celsius_to_kelvin
from geophires_x.GeoPHIRESUtils import read_input_file
from geophires_x.Parameter import ConvertOutputUnits
from geophires_x.Parameter import ConvertUnitsBack
from geophires_x.Parameter import LookupUnits
from geophires_x.Parameter import OutputParameter
from geophires_x.Parameter import ParameterEntry
from geophires_x.Parameter import ReadParameter
from geophires_x.Parameter import floatParameter
from geophires_x.Parameter import intParameter
from geophires_x.Units import AreaUnit
from geophires_x.Units import DensityUnit
from geophires_x.Units import EnthalpyUnit
from geophires_x.Units import HeatCapacityUnit
from geophires_x.Units import HeatPerUnitAreaUnit
from geophires_x.Units import HeatUnit
from geophires_x.Units import LengthUnit
from geophires_x.Units import MassUnit
from geophires_x.Units import PercentUnit
from geophires_x.Units import PowerPerUnitAreaUnit
from geophires_x.Units import PowerUnit
from geophires_x.Units import TemperatureUnit
from geophires_x.Units import TimeUnit
from geophires_x.Units import Units
from geophires_x.Units import VolumeUnit

"""
Heat in Place calculation: Muffler, P., and Raffaele Cataldi.
"Methods for regional assessment of geothermal resources."
Geothermics 7.2-4 (1978): 53-89.
and: Garg, S.K. and J. Combs. 2011.  A Reexamination of the USGS Volumetric "Heat in Place" Method.
Stanford University, 36th Workshop on Geothermal Reservoir Engineering; SGP-TR-191, 5 pp.
build date: September 2023
Created on Monday Nov 28 08:54 2022

@author: Malcolm Ross V1
"""


def rock_enthalpy_func(mass, specific_heat_capacity_kj, delta_temperature_k):
    """
    Calculate the enthalpy change for a rock.

    Parameters:
    - mass: Mass of the rock (in kg)
    - specific_heat_capacity_kj: Specific heat capacity of the rock material (in kJ/(kg·K))
    - delta_temperature_celsius: Change in temperature (in degrees Celsius)

    Returns:
    - Enthalpy change (in kJ/kg)
    """
    #    enthalpy_change = mass * specific_heat_capacity_kj * delta_temperature_celsius
    enthalpy_change = (specific_heat_capacity_kj * delta_temperature_k) / mass
    return enthalpy_change


def rock_entropy_func():
    """
    Calculate the information entropy of a rock based on its composition.

    Parameters:
    - composition: A dictionary representing the composition of the rock,
                   where keys are mineral names and values are their abundances.

    Returns:
    - entropy: The information entropy of the rock.
    """
    composition = {'quartz': 30, 'feldspar': 40, 'mica': 20, 'amphibole': 10}
    total_abundance = sum(composition.values())

    # Calculate the probability of each mineral in the rock
    probabilities = [abundance / total_abundance for abundance in composition.values()]

    # Calculate the entropy using the Shannon entropy formula
    entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)

    return entropy


class HIP_RA:
    """
    HIP_RA is the container class of the HIP_RA application, giving access to everything else, including the logger
    """

    def __init__(self, enable_hip_ra_logging_config=True):
        """
        The __init__ function is called automatically every time the class is being used to create a new object.
        The self parameter is a Python convention. It must be included in each function definition and points to the
        current instance of the class (the object that is being created).
        :param self: Reference the class instance itself
        :return: Nothing
        :doc-author: Malcolm Ross
        """
        # get logging started
        self.logger = logging.getLogger('root')

        if enable_hip_ra_logging_config:
            logging.config.fileConfig('logging.conf')
            self.logger.setLevel(logging.INFO)

        self.logger.info(f'Init {__class__.__name__!s}: {__name__}')

        # Initiate the elements of the Model
        # Set up all the Parameters that will be predefined by this class using the different types of parameter
        # classes.  Setting up includes giving it a name, a default value, The Unit Type (length, volume,
        # temperature, etc.) and Unit Name of that value, sets it as required (or not), sets allowable range,
        # the error message if that range is exceeded, the ToolTip Text, and the name of teh class that created it.
        # This includes setting up temporary variables that will be available to all the class but noy read in by user,
        # or used for Output
        # This also includes all Parameters that are calculated and then published using the Printouts function.

        # These dictionaries contain a list of all the parameters set in this object, stored as "Parameter" and
        # "OutputParameter" Objects.  This will allow us later to access them in a user interface and get that list,
        # along with unit type, preferred units, etc.
        self.ParameterDict = {}
        self.OutputParameterDict: dict[str, OutputParameter] = {}
        self.InputParameters: dict[str, ParameterEntry] = {}  # input parameters the user wants to change

        # inputs
        self.reservoir_temperature = self.ParameterDict[self.reservoir_temperature.Name] = floatParameter(
            'Reservoir Temperature',
            value=150.0,
            Min=50,
            Max=1000,
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS,
            Required=True,
            ErrMessage='assume default reservoir temperature (150 deg-C)',
            ToolTipText='Reservoir Temperature [150 dec-C]',
        )
        self.rejection_temperature = self.ParameterDict[self.rejection_temperature.Name] = floatParameter(
            'Rejection Temperature',
            value=25.0,
            Min=0.1,
            Max=200,
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS,
            Required=True,
            ErrMessage='assume default rejection temperature (25 deg-C)',
            ToolTipText='Rejection Temperature [25 dec-C]',
        )
        self.reservoir_porosity = self.ParameterDict[self.reservoir_porosity.Name] = floatParameter(
            'Reservoir Porosity',
            value=18.0,
            Min=0.0,
            Max=100.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.PERCENT,
            CurrentUnits=PercentUnit.PERCENT,
            Required=True,
            ErrMessage='assume default reservoir porosity (18%)',
            ToolTipText='Reservoir Porosity [18%]',
        )
        self.reservoir_area = self.ParameterDict[self.reservoir_area.Name] = floatParameter(
            'Reservoir Area',
            value=81.0,
            Min=0.0,
            Max=10000.0,
            UnitType=Units.AREA,
            PreferredUnits=AreaUnit.KILOMETERS2,
            CurrentUnits=AreaUnit.KILOMETERS2,
            Required=True,
            ErrMessage='assume default reservoir area (81 km2)',
            ToolTipText='Reservoir Area [81 km2]',
        )
        self.reservoir_thickness = self.ParameterDict[self.reservoir_thickness.Name] = floatParameter(
            'Reservoir Thickness',
            value=0.286,
            Min=0.0,
            Max=10000.0,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.KILOMETERS,
            CurrentUnits=LengthUnit.KILOMETERS,
            Required=True,
            ErrMessage='assume default reservoir thickness (0.286 km2)',
            ToolTipText='Reservoir Thickness [0.286 km]',
        )
        self.reservoir_life_cycle = self.ParameterDict[self.reservoir_life_cycle.Name] = intParameter(
            'Reservoir Life Cycle',
            value=30,
            UnitType=Units.TIME,
            PreferredUnits=TimeUnit.YEAR,
            CurrentUnits=TimeUnit.YEAR,
            AllowableRange=list(range(1, 101, 1)),
            Required=True,
            ErrMessage='assume default Reservoir Life Cycle (25 years)',
            ToolTipText='Reservoir Life Cycle [30 years]',
        )

        # user-changeable semi-constants
        self.rock_heat_capacity = self.ParameterDict[self.rock_heat_capacity.Name] = floatParameter(
            'Reservoir Rock Heat Capacity',
            value=2.84e12,
            Min=0.0,
            Max=1e14,
            UnitType=Units.HEAT_CAPACITY,
            PreferredUnits=HeatCapacityUnit.KJPERKM3C,
            CurrentUnits=HeatCapacityUnit.KJPERKM3C,
            Required=True,
            ErrMessage='assume default Reservoir Heat Capacity (2.84E+12 kJ/km3C)',
            ToolTipText='Reservoir Heat Capacity [2.84E+12 kJ/km3C]',
        )
        self.fluid_heat_capacity = self.ParameterDict[self.fluid_heat_capacity.Name] = floatParameter(
            'Reservoir Fluid Heat Capacity',
            value=-1.0,
            Min=3.0,
            Max=10.0,
            UnitType=Units.HEAT_CAPACITY,
            PreferredUnits=HeatCapacityUnit.kJPERKGC,
            CurrentUnits=HeatCapacityUnit.kJPERKGC,
            Required=True,
            ErrMessage='calculate a value based on the water temperature',
            ToolTipText='Heat Capacity Of Water [4.18 kJ/kgC]',
        )
        self.fluid_density = self.ParameterDict[self.fluid_density.Name] = floatParameter(
            'Density Of Reservoir Fluid',
            value=-1.0,
            Min=1.000e11,
            Max=1.000e13,
            UnitType=Units.DENSITY,
            PreferredUnits=DensityUnit.KGPERKILOMETERS3,
            CurrentUnits=DensityUnit.KGPERKILOMETERS3,
            Required=True,
            ErrMessage='calculate a value based on the water temperature',
            ToolTipText='Density Of Water [1.0E+12 kg/km3]',
        )
        self.rock_density = self.ParameterDict[self.rock_density.Name] = floatParameter(
            'Density Of Reservoir Rock',
            value=2.55e12,
            Min=1.000e11,
            Max=1.000e13,
            UnitType=Units.DENSITY,
            PreferredUnits=DensityUnit.KGPERKILOMETERS3,
            CurrentUnits=DensityUnit.KGPERKILOMETERS3,
            Required=True,
            ErrMessage='assume default Density Of Rock (2.55E+12 kg/km3)',
            ToolTipText='Density Of Rock [2.55E+12 kg/km3]',
        )
        self.rock_recoverable_heat = self.ParameterDict[self.rock_recoverable_heat.Name] = floatParameter(
            'Rock Recoverable Heat',
            value=-1.0,
            Min=0.0,
            Max=1.000,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Required=False,
            ErrMessage='assume 0.66 for high-T reservoirs (>150C), 0.43 for low-T reservoirs \
            (>90, Garg and Combs (2011)',
            ToolTipText='percent of heat that is recoverable from the rock in the reservoir 0.66 for high-T reservoirs,\
             0.43 for low-T reservoirs (Garg and Combs (2011)',
        )
        self.fluid_recoverable_heat = self.ParameterDict[self.fluid_recoverable_heat.Name] = floatParameter(
            'Fluid Recoverable Heat',
            value=-1.0,
            Min=0.00,
            Max=1.000,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Required=False,
            ErrMessage='assume 0.66 for high-T reservoirs (>150C), 0.43 for low-T reservoirs \
            (>90, Garg and Combs (2011)',
            ToolTipText='percent of heat that is recoverable from the fluid in the reservoir 0.66 for high-T reservoirs,\
             0.43 for low-T reservoirs (Garg and Combs (2011)',
        )
        self.recoverable_fluid = self.ParameterDict[self.recoverable_fluid.Name] = floatParameter(
            'Recoverable Fluid Volume',
            value=0.5,
            Min=0.00,
            Max=1.000,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Required=False,
            ErrMessage='assume 0.5 (50%) of fluid from the reservoir is recoverable',
            ToolTipText='percent of fluid that is recoverable from the reservoir (0.5 = 50%)',
        )
        self.recoverable_rock_heat = self.ParameterDict[self.recoverable_rock_heat.Name] = floatParameter(
            'Recoverable Heat from Rock',
            value=0.75,
            Min=0.00,
            Max=1.000,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Required=False,
            ErrMessage='assume 0.75 (75%) of fluid from the reservoir is recoverable',
            ToolTipText='percent of fluid that is recoverable from the reservoir (0.75 = 75%)',
        )

        # Output parameters
        self.reservoir_volume = self.OutputParameterDict[self.reservoir_volume.Name] = OutputParameter(
            Name='Reservoir Volume (reservoir)',
            UnitType=Units.VOLUME,
            PreferredUnits=VolumeUnit.KILOMETERS3,
            CurrentUnits=VolumeUnit.KILOMETERS3,
        )
        self.volume_rock = self.OutputParameterDict[self.volume_rock.Name] = OutputParameter(
            Name='Reservoir Volume (rock)',
            UnitType=Units.VOLUME,
            PreferredUnits=VolumeUnit.KILOMETERS3,
            CurrentUnits=VolumeUnit.KILOMETERS3,
        )
        self.volume_fluid = self.OutputParameterDict[self.volume_fluid.Name] = OutputParameter(
            Name='Reservoir Volume (fluid)',
            UnitType=Units.VOLUME,
            PreferredUnits=VolumeUnit.KILOMETERS3,
            CurrentUnits=VolumeUnit.KILOMETERS3,
        )
        self.reservoir_stored_heat = self.OutputParameterDict[self.reservoir_stored_heat.Name] = OutputParameter(
            Name='Stored Heat (reservoir)',
            UnitType=Units.HEAT,
            PreferredUnits=HeatUnit.KJ,
            CurrentUnits=HeatUnit.KJ,
        )
        self.stored_heat_rock = self.OutputParameterDict[self.stored_heat_rock.Name] = OutputParameter(
            Name='Stored Heat (rock)',
            UnitType=Units.HEAT,
            PreferredUnits=HeatUnit.KJ,
            CurrentUnits=HeatUnit.KJ,
        )
        self.stored_heat_fluid = self.OutputParameterDict[self.stored_heat_fluid.Name] = OutputParameter(
            Name='Stored Heat (fluid)',
            UnitType=Units.HEAT,
            PreferredUnits=HeatUnit.KJ,
            CurrentUnits=HeatUnit.KJ,
        )
        self.reservoir_mass = self.OutputParameterDict[self.reservoir_mass.Name] = OutputParameter(
            Name='Mass of Reservoir (total)',
            UnitType=Units.MASS,
            PreferredUnits=MassUnit.KILOGRAM,
            CurrentUnits=MassUnit.KILOGRAM,
        )
        self.mass_rock = self.OutputParameterDict[self.mass_rock.Name] = OutputParameter(
            Name='Mass of Reservoir (rock)',
            UnitType=Units.MASS,
            PreferredUnits=MassUnit.KILOGRAM,
            CurrentUnits=MassUnit.KILOGRAM,
        )
        self.mass_fluid = self.OutputParameterDict[self.mass_fluid.Name] = OutputParameter(
            Name='Mass of Reservoir (fluid)',
            UnitType=Units.MASS,
            PreferredUnits=MassUnit.KILOGRAM,
            CurrentUnits=MassUnit.KILOGRAM,
        )
        self.reservoir_enthalpy = self.OutputParameterDict[self.reservoir_enthalpy.Name] = OutputParameter(
            Name='Enthalpy (reservoir)',
            UnitType=Units.ENTHALPY,
            PreferredUnits=EnthalpyUnit.KJPERKG,
            CurrentUnits=EnthalpyUnit.KJPERKG,
        )
        self.enthalpy_rock = self.OutputParameterDict[self.enthalpy_rock.Name] = OutputParameter(
            Name='Enthalpy (rock)',
            UnitType=Units.ENTHALPY,
            PreferredUnits=EnthalpyUnit.KJPERKG,
            CurrentUnits=EnthalpyUnit.KJPERKG,
        )
        self.enthalpy_fluid = self.OutputParameterDict[self.enthalpy_fluid.Name] = OutputParameter(
            Name='Enthalpy (fluid)',
            UnitType=Units.ENTHALPY,
            PreferredUnits=EnthalpyUnit.KJPERKG,
            CurrentUnits=EnthalpyUnit.KJPERKG,
        )
        self.wellhead_heat = self.OutputParameterDict[self.wellhead_heat.Name] = OutputParameter(
            Name='Wellhead Heat (reservoir)',
            UnitType=Units.HEAT,
            PreferredUnits=HeatUnit.KJ,
            CurrentUnits=HeatUnit.KJ,
        )
        self.wellhead_heat_recovery_rock = self.OutputParameterDict[
            self.wellhead_heat_recovery_rock.Name
        ] = OutputParameter(
            Name='Wellhead Heat (rock)',
            UnitType=Units.HEAT,
            PreferredUnits=HeatUnit.KJ,
            CurrentUnits=HeatUnit.KJ,
        )
        self.wellhead_heat_recovery_fluid = self.OutputParameterDict[
            self.wellhead_heat_recovery_fluid.Name
        ] = OutputParameter(
            Name='Wellhead Heat (fluid)',
            UnitType=Units.HEAT,
            PreferredUnits=HeatUnit.KJ,
            CurrentUnits=HeatUnit.KJ,
        )
        self.reservoir_recovery_factor = self.OutputParameterDict[
            self.reservoir_recovery_factor.Name
        ] = OutputParameter(
            Name='Recovery Factor (reservoir)',
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.PERCENT,
            CurrentUnits=PercentUnit.PERCENT,
        )
        self.recovery_factor_rock = self.OutputParameterDict[self.recovery_factor_rock.Name] = OutputParameter(
            Name='Recovery Factor (rock)',
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.PERCENT,
            CurrentUnits=PercentUnit.PERCENT,
        )
        self.recovery_factor_fluid = self.OutputParameterDict[self.recovery_factor_fluid.Name] = OutputParameter(
            Name='Recovery Factor (fluid)',
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.PERCENT,
            CurrentUnits=PercentUnit.PERCENT,
        )
        self.reservoir_available_heat = self.OutputParameterDict[self.reservoir_available_heat.Name] = OutputParameter(
            Name='Available Heat (reservoir)',
            UnitType=Units.HEAT,
            PreferredUnits=HeatUnit.KJ,
            CurrentUnits=HeatUnit.KJ,
        )
        self.available_heat_rock = self.OutputParameterDict[self.available_heat_rock.Name] = OutputParameter(
            Name='Available Heat (rock)',
            UnitType=Units.HEAT,
            PreferredUnits=HeatUnit.KJ,
            CurrentUnits=HeatUnit.KJ,
        )
        self.available_heat_fluid = self.OutputParameterDict[self.available_heat_fluid.Name] = OutputParameter(
            Name='Available Heat (fluid)',
            UnitType=Units.HEAT,
            PreferredUnits=HeatUnit.KJ,
            CurrentUnits=HeatUnit.KJ,
        )
        self.reservoir_producible_heat = self.OutputParameterDict[
            self.reservoir_producible_heat.Name
        ] = OutputParameter(
            Name='Producible Heat (reservoir)',
            UnitType=Units.HEAT,
            PreferredUnits=HeatUnit.KJ,
            CurrentUnits=HeatUnit.KJ,
        )
        self.producible_heat_rock = self.OutputParameterDict[self.producible_heat_rock.Name] = OutputParameter(
            Name='Producible Heat (rock)',
            UnitType=Units.HEAT,
            PreferredUnits=HeatUnit.KJ,
            CurrentUnits=HeatUnit.KJ,
        )
        self.producible_heat_fluid = self.OutputParameterDict[self.producible_heat_fluid.Name] = OutputParameter(
            Name='Producible Heat (fluid)',
            UnitType=Units.HEAT,
            PreferredUnits=HeatUnit.KJ,
            CurrentUnits=HeatUnit.KJ,
        )
        self.reservoir_producible_electricity = self.OutputParameterDict[
            self.reservoir_producible_electricity.Name
        ] = OutputParameter(
            Name='Producible Electricity (reservoir)',
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW,
        )
        self.producible_electricity_rock = self.OutputParameterDict[
            self.producible_electricity_rock.Name
        ] = OutputParameter(
            Name='Producible Electricity (rock)',
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW,
        )
        self.producible_electricity_fluid = self.OutputParameterDict[
            self.producible_electricity_fluid.Name
        ] = OutputParameter(
            Name='Producible Electricity (fluid)',
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW,
        )
        self.producible_heat_per_unit_area = self.OutputParameterDict[
            self.producible_heat_per_unit_area.Name
        ] = OutputParameter(
            Name='Producible Heat/Unit Area (reservoir)',
            UnitType=Units.HEATPERUNITAREA,
            PreferredUnits=HeatPerUnitAreaUnit.KJPERSQKM,
            CurrentUnits=HeatPerUnitAreaUnit.KJPERSQKM,
        )
        self.heat_per_unit_area_rock = self.OutputParameterDict[self.heat_per_unit_area_rock.Name] = OutputParameter(
            Name='Producible Heat/Unit Area (rock)',
            UnitType=Units.HEATPERUNITAREA,
            PreferredUnits=HeatPerUnitAreaUnit.KJPERSQKM,
            CurrentUnits=HeatPerUnitAreaUnit.KJPERSQKM,
        )
        self.heat_per_unit_area_fluid = self.OutputParameterDict[self.heat_per_unit_area_fluid.Name] = OutputParameter(
            Name='Producible Heat/Unit Area (fluid)',
            UnitType=Units.HEATPERUNITAREA,
            PreferredUnits=HeatPerUnitAreaUnit.KJPERSQKM,
            CurrentUnits=HeatPerUnitAreaUnit.KJPERSQKM,
        )
        self.producible_electricity_per_unit_area = self.OutputParameterDict[
            self.producible_electricity_per_unit_area.Name
        ] = OutputParameter(
            Name='Producible Electricity/Unit Area (reservoir)',
            UnitType=Units.POWERPERUNITAREA,
            PreferredUnits=PowerPerUnitAreaUnit.MWPERSQKM,
            CurrentUnits=PowerPerUnitAreaUnit.MWPERSQKM,
        )
        self.electricity_per_unit_area_rock = self.OutputParameterDict[
            self.electricity_per_unit_area_rock.Name
        ] = OutputParameter(
            Name='Producible Electricity/Unit Area (rock)',
            UnitType=Units.POWERPERUNITAREA,
            PreferredUnits=PowerPerUnitAreaUnit.MWPERSQKM,
            CurrentUnits=PowerPerUnitAreaUnit.MWPERSQKM,
        )
        self.electricity_per_unit_area_fluid = self.OutputParameterDict[
            self.electricity_per_unit_area_fluid.Name
        ] = OutputParameter(
            Name='Producible Electricity/Unit Area (fluid)',
            UnitType=Units.POWERPERUNITAREA,
            PreferredUnits=PowerPerUnitAreaUnit.MWPERSQKM,
            CurrentUnits=PowerPerUnitAreaUnit.MWPERSQKM,
        )

        self.logger.info(f'Complete {__class__.__name__!s}: {__name__}')

    def read_parameters(self) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary created by reading the user-provided file
        and updates the parameter values for this object.

        The function reads in all the parameters that relate to this object, including those that are inherited
        from other objects. It then updates any of these parameter values that have been changed by the user.
        It also handles any special cases.
        :param self: Reference the class instance (such as it is) from within the class
        :return: None
        :doc-author: Malcolm Ross
        """
        self.logger.info(f'Init {__class__.__name__!s}: {__name__}')

        # This should give us a dictionary with all the parameters the user wants to set.  Should be only those value
        # that they want to change from the default.
        # we do this as soon as possible because what we instantiate may depend on settings in this file

        read_input_file(self.InputParameters, logger=self.logger)

        # Deal with all the parameter values that the user has provided.  They should really only provide values
        # that they want to change from the default values, but they can provide a value that is already set because
        # it is a default value set in __init__.  It will ignore those.
        # This also deals with all the special cases that need to be taken care of after
        # a value has been read in and checked.
        # If you choose to subclass this master class, you can also choose to override this method (or not),
        # and if you do, do it before or after you call you own version of this method.  If you do, you can
        # also choose to call this method from you class, which can effectively modify all these superclass parameters
        # in your class.

        if len(self.InputParameters) > 0:
            # loop through all the parameters that the user wishes to set, looking for parameters that match this object
            for item in self.ParameterDict.items():
                ParameterToModify = item[1]
                key = ParameterToModify.Name.strip()
                if key in self.InputParameters:
                    ParameterReadIn = self.InputParameters[key]
                    # Before we change the parameter, let's assume that the unit preferences will match -
                    # if they don't, the later code will fix this.
                    ParameterToModify.CurrentUnits = ParameterToModify.PreferredUnits
                    ReadParameter(
                        ParameterReadIn, ParameterToModify, self
                    )  # this should handle all the non-special cases
        else:
            self.logger.info('No parameters read because no content provided')

        # loop through all the parameters that the user wishes to set, looking for parameters that contain
        # the prefix "Units:" - that means we want to set a special case for converting this output parameter
        # to new units
        for key in self.InputParameters.keys():
            if key.startswith('Units:'):
                self.OutputParameterDict[key.replace('Units:', '')].CurrentUnits = LookupUnits(
                    self.InputParameters[key].sValue
                )[0]
                self.OutputParameterDict[key.replace('Units:', '')].UnitsMatch = False

        self.logger.info(f'complete {__class__.__name__!s}: {__name__}')

    def Calculate(self):
        """
        The Calculate function is where all the calculations are made.  This is handled on a class-by-class basis.
        The Calculate function does not return anything, but it does store the results for later use by other functions.
        :param self: Access the class variables
        :return: None
        :doc-author: Malcolm Ross
        """
        self.logger.info(f'Init {__class__!s}: {__class__.__name__!s}: {__name__}')

        try:
            # calculate the volume of rock and fluid in the reservoir
            # note that we can't recover all the fluid from the reservoir, so we multiply times the recoverable fluid factor
            self.reservoir_volume.value = self.reservoir_area.value * self.reservoir_thickness.value
            self.volume_rock.value = self.reservoir_volume.value * (1.0 - (self.reservoir_porosity.value / 100.0))
            self.volume_fluid.value = (
                self.reservoir_volume.value * (self.reservoir_porosity.value / 100.0) * self.recoverable_fluid.value
            )

            # calculate the mass of the rock and the fluid in the reservoir
            if self.fluid_density.value < self.fluid_density.Min:
                self.fluid_density.value = (
                    DensityWater(self.reservoir_temperature.value) * 1_000_000_000.0
                )  # converted to kj/km3
            self.mass_rock.value = self.volume_rock.value * self.rock_density.value
            self.mass_fluid.value = self.volume_fluid.value * self.fluid_density.value
            self.reservoir_mass.value = self.mass_rock.value + self.mass_fluid.value

            # do all the simple calculations and look-ups only once
            if self.fluid_heat_capacity.value < self.fluid_heat_capacity.Min:
                self.fluid_heat_capacity.value = (
                    HeatCapacityWater(self.reservoir_temperature.value) / 1000.0
                )  # converted to kJ/kg-K
            rejection_temperature_k = celsius_to_kelvin(self.rejection_temperature.value)
            reservoir_temperature_k = celsius_to_kelvin(self.reservoir_temperature.value)
            # delta_temperature = self.reservoir_temperature.value - self.rejection_temperature.value
            delta_temperature_k = reservoir_temperature_k - rejection_temperature_k
            # rejection_entropy = EntropyH20_func(self.rejection_temperature.value)
            # rejection_enthalpy = EnthalpyH20_func(self.rejection_temperature.value)
            fluid_net_enthalpy = EnthalpyH20_func(delta_temperature_k)
            fluid_net_entropy = EntropyH20_func(delta_temperature_k)
            rock_net_enthalpy = rock_enthalpy_func(
                self.mass_rock.value, self.rock_heat_capacity.value, delta_temperature_k
            )
            rock_net_entropy = rock_entropy_func()

            # calculate the stored heat of the rock and the fluid in the reservoir (in kJ)
            # note that the rock stored heat is a function of the volume, so we multiple times the volume of the rock (in km3)
            # and the fluid stored heat is a function of the mass of the fluid, so we multiply times the mass of the fluid (in kg)
            # Also note that we can't recover all the heat from the rock, so we multiply times the recoverable rock heat factor
            self.stored_heat_rock.value = self.volume_rock.value * self.rock_heat_capacity.value * delta_temperature_k
            self.stored_heat_rock.value = self.stored_heat_rock.value * self.recoverable_rock_heat.value
            self.stored_heat_fluid.value = self.mass_fluid.value * self.fluid_heat_capacity.value * delta_temperature_k
            self.reservoir_stored_heat.value = self.stored_heat_rock.value + self.stored_heat_fluid.value

            # calculate the maximum energy out per unit of mass (in kJ/kg)
            #            self.enthalpy_rock.value = fluid_net_enthalpy - (delta_temperature_k * rock_net_entropy)
            self.enthalpy_rock.value = rock_net_enthalpy - (delta_temperature_k * rock_net_entropy)
            self.enthalpy_fluid.value = fluid_net_enthalpy - (delta_temperature_k * fluid_net_entropy)
            # self.enthalpy_rock.value = self.stored_heat_rock.value/self.mass_rock.value
            # self.enthalpy_fluid.value = self.stored_heat_fluid.value/self.mass_fluid.value
            self.reservoir_enthalpy.value = self.enthalpy_rock.value + self.enthalpy_fluid.value

            # calculate the heat recovery at the wellhead (in kJ)
            # this assume negligible heat loss as the heat is transferred to the surface (i.e., no heat loss in the well)
            # self.wellhead_heat_recovery_rock.value = self.mass_rock.value * rock_net_enthalpy
            # self.wellhead_heat_recovery_fluid.value = self.mass_fluid.value * fluid_net_enthalpy
            # rockx = self.mass_rock.value * self.enthalpy_rock.value
            # fluidx = self.mass_fluid.value * self.enthalpy_fluid.value
            self.wellhead_heat_recovery_rock.value = self.stored_heat_rock.value
            self.wellhead_heat_recovery_fluid.value = self.stored_heat_fluid.value
            self.wellhead_heat.value = self.wellhead_heat_recovery_rock.value + self.wellhead_heat_recovery_fluid.value

            # calculate the Recoverable heat: if the user supplied -1 as the Recoverable Heat, they want us to calculate it.
            if self.rock_recoverable_heat.value < self.rock_recoverable_heat.Min:
                self.rock_recoverable_heat.value = RecoverableHeat(self.reservoir_temperature.value)
            if self.fluid_recoverable_heat.value < self.fluid_recoverable_heat.Min:
                self.fluid_recoverable_heat.value = RecoverableHeat(self.reservoir_temperature.value)

            # calculate the available heat
            self.available_heat_rock.value = (
                self.mass_rock.value * self.enthalpy_rock.value * self.rock_recoverable_heat.value
            )
            self.available_heat_fluid.value = (
                self.mass_fluid.value * self.enthalpy_fluid.value * self.fluid_recoverable_heat.value
            )
            self.reservoir_available_heat.value = self.available_heat_rock.value + self.available_heat_fluid.value

            # calculate the producible heat given the utilization efficiency of producing electricity at that temperature
            # This uses a function from Garg and Coombs that assumes ORC for low temperature and flash for high temperature
            utilization_effectiveness = UtilEff_func(self.reservoir_temperature.value)
            self.producible_heat_rock.value = self.available_heat_rock.value * utilization_effectiveness
            self.producible_heat_fluid.value = self.available_heat_fluid.value * utilization_effectiveness
            self.reservoir_producible_heat.value = self.producible_heat_rock.value + self.producible_heat_fluid.value

            # calculate the recovery factor
            self.recovery_factor_rock.value = self.producible_heat_rock.value / self.stored_heat_rock.value
            self.recovery_factor_fluid.value = self.producible_heat_fluid.value / self.stored_heat_fluid.value
            self.reservoir_recovery_factor.value = (
                self.reservoir_producible_heat.value / self.reservoir_stored_heat.value
            )

            # calculate the producible heat per unit area
            self.heat_per_unit_area_rock.value = self.producible_heat_rock.value / self.reservoir_area.value
            self.heat_per_unit_area_fluid.value = self.producible_heat_fluid.value / self.reservoir_area.value
            self.producible_heat_per_unit_area.value = self.reservoir_producible_heat.value / self.reservoir_area.value

            # calculate the producible electricity by converting Kilojoules of heat to MWe of electricity
            # kJ_to_Mwe = 3.156e+7 #seconds in a year
            # self.We.value = (self.WE.value / 3_600_000) / 8_760  # convert Kilojoules of heat to MWe of electricity
            self.producible_electricity_rock.value = (self.producible_heat_rock.value / 3_600_000) / 8_760
            self.producible_electricity_fluid.value = (self.producible_heat_fluid.value / 3_600_000) / 8_760
            #            self.producible_electricity_fluid.value = self.producible_heat_fluid.value / kJ_to_Mwe
            self.reservoir_producible_electricity.value = (
                self.producible_electricity_rock.value + self.producible_electricity_fluid.value
            )

            # calculate the producible electricity by converting Kilojoules of heat to MWh of electricity
            #            kJ_to_Mwhe = 2.7778E-7
            #            self.producible_electricity_rock.value = self.producible_heat_rock.value * kJ_to_Mwhe
            #            self.producible_electricity_fluid.value = self.producible_heat_fluid.value * kJ_to_Mwhe
            #            self.reservoir_producible_electricity.value = self.producible_electricity_rock.value + self.producible_electricity_fluid.value
            # self.reservoir_producible_electricity.value = (self.reservoir_producible_heat.value / 3_600_000) / 8_760  # convert Kilojoules of heat to MWe of electricity

            # calculate the producible electricity per unit area
            self.electricity_per_unit_area_rock.value = (
                self.producible_electricity_rock.value / self.reservoir_area.value
            )
            self.electricity_per_unit_area_fluid.value = (
                self.producible_electricity_fluid.value / self.reservoir_area.value
            )
            self.producible_electricity_per_unit_area.value = (
                self.reservoir_producible_electricity.value / self.reservoir_area.value
            )

            self.logger.info(f'Complete {__class__!s}: {__class__.__name__!s}: {__name__}')
        except Exception as e:
            self.logger.error(f'Error occurred during calculations: {e!s}')
            traceback.print_exc()

    def PrintOutputs(self):
        """
        PrintOutputs writes the standard outputs to the output file.
        """
        self.logger.info(f'Init {__class__.__name__!s}: {__name__}')

        # Deal with converting Units back to PreferredUnits, if required.
        # before we write the outputs, we go through all the parameters for all the objects and set the values back
        # to the units that the user entered the data in
        # reservoir_producible_electricity do this because the value may be displayed in the output, and we want the user to recognize their value,
        # not some converted value
        for key in self.ParameterDict:
            param = self.ParameterDict[key]
            if not param.UnitsMatch:
                ConvertUnitsBack(param, self)

        # now we need to loop through all the output parameters to update their units to whatever
        # units the user has specified.
        # i.reservoir_enthalpy., they may have specified that all LENGTH results must be in feet, so we need to convert those from
        # whatever LENGTH unit they are to feet.
        # same for all the other classes of units (TEMPERATURE, DENSITY, etc).
        for key in self.OutputParameterDict:
            if not self.OutputParameterDict[key].UnitsMatch:
                ConvertOutputUnits(self.OutputParameterDict[key], self.OutputParameterDict[key].CurrentUnits, self)

        # ---------------------------------------
        # write results to output file and screen
        # ---------------------------------------
        try:
            outputfile = 'HIP.out' if len(sys.argv) <= 2 else sys.argv[2]

            def render_default(p: floatParameter | OutputParameter) -> str:
                return f'{p.value:10.2f} {p.CurrentUnits.value}'

            def render_scientific(p: floatParameter | OutputParameter) -> str:
                return f'{p.value:10.2e} {p.CurrentUnits.value}'

            summary_of_results = {}

            for param, render in [
                (self.reservoir_temperature, render_default),
                (self.reservoir_volume, render_default),
                (self.volume_rock, render_default),
                (self.volume_fluid, render_default),
                (self.reservoir_stored_heat, render_scientific),
                (self.stored_heat_rock, render_scientific),
                (self.stored_heat_fluid, render_scientific),
                (self.reservoir_mass, render_scientific),
                (self.mass_rock, render_scientific),
                (self.mass_fluid, render_scientific),
                (self.reservoir_enthalpy, render_default),
                (self.enthalpy_rock, render_default),
                (self.enthalpy_fluid, render_default),
                (self.wellhead_heat, render_scientific),
                (self.wellhead_heat_recovery_rock, render_scientific),
                (self.wellhead_heat_recovery_fluid, render_scientific),
                (
                    self.reservoir_recovery_factor,
                    lambda rg: f'{(100 * rg.value):10.2f} {self.reservoir_recovery_factor.CurrentUnits.value}',
                ),
                (
                    self.recovery_factor_rock,
                    lambda rg: f'{(100 * rg.value):10.2f} {self.recovery_factor_rock.CurrentUnits.value}',
                ),
                (
                    self.recovery_factor_fluid,
                    lambda rg: f'{(100 * rg.value):10.2f} {self.recovery_factor_fluid.CurrentUnits.value}',
                ),
                (self.reservoir_available_heat, render_scientific),
                (self.available_heat_rock, render_scientific),
                (self.available_heat_fluid, render_scientific),
                (self.reservoir_producible_heat, render_scientific),
                (self.producible_heat_rock, render_scientific),
                (self.producible_heat_fluid, render_scientific),
                (self.producible_heat_per_unit_area, render_scientific),
                (self.heat_per_unit_area_rock, render_scientific),
                (self.heat_per_unit_area_fluid, render_scientific),
                (self.reservoir_producible_electricity, render_default),
                (self.producible_electricity_rock, render_default),
                (self.producible_electricity_fluid, render_default),
                (self.producible_electricity_per_unit_area, render_default),
                (self.electricity_per_unit_area_rock, render_default),
                (self.electricity_per_unit_area_fluid, render_default),
            ]:
                summary_of_results[param.Name] = render(param)

            case_data = {'SUMMARY OF RESULTS': summary_of_results}

            with open(outputfile, 'w', encoding='UTF-8') as f:
                nl = '\n'

                f.write(f'                               *********************{nl}')
                f.write(f'                               ***HIP CASE REPORT***{nl}')
                f.write(f'                               *********************{nl}')
                f.write(nl)
                f.write(f'                           ***SUMMARY OF RESULTS***{nl}')
                f.write(nl)

                for k, v in case_data['SUMMARY OF RESULTS'].items():
                    # align space between value and units to same column
                    kv_spaces = max(1, (24 - (len(v.split(' ')[0]) + len(k)))) * ' '

                    f.write(f'      {k}:{kv_spaces}{v}{nl}')

        except FileNotFoundError as ex:
            print(str(ex))
            traceback_str = traceback.format_exc()
            msg = f'Error: HIP_RA Failed to write the output file. Exiting....\n{traceback_str}'
            print(msg)
            self.logger.critical(str(ex))
            self.logger.critical(msg)
            raise

        except PermissionError as ex:
            print(str(ex))
            traceback_str = traceback.format_exc()
            msg = f'Error: HIP_RA Failed to write the output file. Exiting....\n{traceback_str}'
            print(msg)
            self.logger.critical(str(ex))
            self.logger.critical(msg)
            raise

        except Exception as ex:
            print(str(ex))
            traceback_str = traceback.format_exc()
            msg = f'Error: HIP_RA Failed to write the output file. Exiting....\n{traceback_str}'
            print(msg)
            self.logger.critical(str(ex))
            self.logger.critical(msg)
            raise

        # copy the output file to the screen
        with open(outputfile, encoding='UTF-8') as f:
            content = f.readlines()  # store all output in one long list

            # Now write each line to the screen
            for line in content:
                sys.stdout.write(line)

    def __str__(self):
        return 'HIP_RA'


def main(enable_geophires_logging_config=True):
    # set the starting directory to be the directory that this file is in
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # set up logging.
    if enable_geophires_logging_config:
        logging.config.fileConfig('logging.conf')
    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger('root')

    logger.info('Initializing the application')

    # initiate the HIP-RA parameters, setting them to their default values
    model = HIP_RA(enable_hip_ra_logging_config=enable_geophires_logging_config)

    # read the parameters that apply to the model
    model.read_parameters()

    try:
        # Calculate the entire model
        model.Calculate()
    except Exception as e:
        logger.error(f'Error occurred during model calculation: {e!s}')

    try:
        # write the outputs
        model.PrintOutputs()
    except Exception as e:
        logger.error(f'Error occurred during output printing: {e!s}')

    logger.info('Application execution completed')


if __name__ == '__main__':
    main()

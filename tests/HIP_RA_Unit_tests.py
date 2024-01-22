# FIXME WIP/broken
# ruff: noqa

import logging
import os
import re
import sys
import unittest

import pytest

from base_test_case import BaseTestCase
from geophires_x.GeoPHIRESUtils import DensityWater
from geophires_x.GeoPHIRESUtils import EnthalpyH20_func
from geophires_x.GeoPHIRESUtils import EntropyH20_func
from geophires_x.GeoPHIRESUtils import HeatCapacityWater
from geophires_x.GeoPHIRESUtils import RecoverableHeat
from geophires_x.GeoPHIRESUtils import T
from geophires_x.GeoPHIRESUtils import VaporPressureWater
from geophires_x.GeoPHIRESUtils import ViscosityWater

from geophires_x.GeoPHIRESUtils import interp_entropy_func

from geophires_x.Parameter import OutputParameter, ParameterEntry
from geophires_x.Parameter import floatParameter
from geophires_x.Parameter import intParameter
from geophires_x.Units import EnthalpyUnit
from geophires_x.Units import HeatUnit
from geophires_x.Units import MassUnit
from geophires_x.Units import PercentUnit
from geophires_x.Units import PowerUnit
from geophires_x.Units import TemperatureUnit
from geophires_x.Units import Units
from geophires_x.Units import VolumeUnit
from hip_ra import HipRaClient, HipRaInputParameters, HipRaResult
from hip_ra.HIP_RA import HIP_RA


class TestRecoverableHeat(unittest.TestCase):
    #  Returns recoverable heat fraction when given valid input values within the default range.
    def test_valid_input_within_default_range(self):
        # Arrange
        default_recoverable_heat = 0.5
        twater = 100.0

        # Act
        result = RecoverableHeat(default_recoverable_heat, twater)

        # Assert
        assert result == 0.0038 * twater + 0.085

    #  Returns recoverable heat fraction when given valid input values outside the default range.
    def test_valid_input_outside_default_range(self):
        # Arrange
        default_recoverable_heat = 0.5
        twater = 160.0

        # Act
        result = RecoverableHeat(default_recoverable_heat, twater)

        # Assert
        assert result == 0.66

    #  Returns recoverable heat fraction when given the lowest valid temperature value.
    def test_lowest_valid_temperature_value(self):
        # Arrange
        default_recoverable_heat = 0.5
        twater = 90.0

        # Act
        result = RecoverableHeat(default_recoverable_heat, twater)

        # Assert
        assert result == 0.43

    #  Returns recoverable heat fraction when given the highest valid temperature value.
    def test_highest_valid_temperature_value(self):
        # Arrange
        default_recoverable_heat = 0.5
        twater = 150.0

        # Act
        result = RecoverableHeat(default_recoverable_heat, twater)

        # Assert
        assert result == 0.66

    #  Returns recoverable heat fraction when given the default recoverable heat fraction and the lowest valid temperature value.
    def test_default_recoverable_heat_and_lowest_valid_temperature_value(self):
        # Arrange
        default_recoverable_heat = 0.5
        twater = 90.0

        # Act
        result = RecoverableHeat(default_recoverable_heat, twater)

        # Assert
        assert result == 0.43

    #  Raises ValueError when given a non-numeric value for Twater.
    def test_non_numeric_value_for_twater(self):
        # Arrange
        default_recoverable_heat = 0.5
        twater = 'abc'

        # Act and Assert
        with pytest.raises(ValueError):
            RecoverableHeat(default_recoverable_heat, twater)

    #  Raises ValueError when given a non-numeric value for DefaultRecoverableHeat.
    def test_non_numeric_value_for_default_recoverable_heat(self):
        # Arrange
        default_recoverable_heat = 'abc'
        twater = 100.0

        # Act and Assert
        with pytest.raises(ValueError):
            RecoverableHeat(default_recoverable_heat, twater)

    #  Returns the lowest recoverable heat fraction when given the lowest valid temperature value and a negative default recoverable heat fraction.
    def test_negative_default_recoverable_heat_and_lowest_valid_temperature_value(self):
        # Arrange
        default_recoverable_heat = -0.5
        twater = 90.0

        # Act
        result = RecoverableHeat(default_recoverable_heat, twater)

        # Assert
        assert result == 0.43

    #  Returns the highest recoverable heat fraction when given the highest valid temperature value and a negative default recoverable heat fraction.
    def test_negative_default_recoverable_heat_and_highest_valid_temperature_value(self):
        # Arrange
        default_recoverable_heat = -0.5
        twater = 150.0

        # Act
        result = RecoverableHeat(default_recoverable_heat, twater)

        # Assert
        assert result == 0.66

    #  Returns the default recoverable heat fraction when given a negative default recoverable heat fraction and a valid temperature value within the default range.
    def test_negative_default_recoverable_heat_and_valid_temperature_within_default_range(self):
        # Arrange
        default_recoverable_heat = -0.5
        twater = 100.0

        # Act
        result = RecoverableHeat(default_recoverable_heat, twater)

        # Assert
        assert result == default_recoverable_heat


class TestVaporPressureWater(unittest.TestCase):
    #  Returns the vapor pressure of water for a temperature below 100 degrees Celsius
    def test_below_100_degrees(self):
        result = VaporPressureWater(50)
        assert result == 12.324

    #  Returns the vapor pressure of water for a temperature above 100 degrees Celsius
    def test_above_100_degrees(self):
        result = VaporPressureWater(150)
        assert result == 13.456

    #  Returns the vapor pressure of water for a temperature of exactly 100 degrees Celsius
    def test_100_degrees(self):
        result = VaporPressureWater(100)
        assert result == 13.456

    #  Returns the expected vapor pressure for a temperature of 0 degrees Celsius
    def test_0_degrees(self):
        result = VaporPressureWater(0)
        assert result == 6.107

    #  Returns the expected vapor pressure for a temperature of 25 degrees Celsius
    def test_25_degrees(self):
        result = VaporPressureWater(25)
        assert result == 3.170

    #  Raises a ValueError if Twater is not a number
    def test_value_error(self):
        with pytest.raises(ValueError):
            VaporPressureWater('abc')

    #  Returns the expected vapor pressure for the minimum possible temperature (-273.15 degrees Celsius)
    def test_minimum_temperature(self):
        result = VaporPressureWater(-273.15)
        assert result == 0.006

    #  Returns the expected vapor pressure for the maximum possible temperature (infinitely high)
    def test_maximum_temperature(self):
        result = VaporPressureWater(float('inf'))
        assert result == float('inf')

    #  Returns the expected vapor pressure for a temperature of 50 degrees Celsius
    def test_50_degrees(self):
        result = VaporPressureWater(50)
        assert result == 12.324

    #  Returns the expected vapor pressure for a temperature of 75 degrees Celsius
    def test_75_degrees(self):
        result = VaporPressureWater(75)
        assert result == 7.375


class TestEnthalpyh20Func(unittest.TestCase):
    #  Returns the correct enthalpy value for a given temperature within the valid range.
    def test_valid_temperature(self):
        temperature = 50.0
        expected_enthalpy = 106.0
        assert EnthalpyH20_func(temperature) == expected_enthalpy

    #  Returns the correct enthalpy value for the minimum valid temperature (0.01 degrees C).
    def test_minimum_temperature(self):
        temperature = 0.01
        expected_enthalpy = 0.0
        assert EnthalpyH20_func(temperature) == expected_enthalpy

    #  Returns the correct enthalpy value for the maximum valid temperature (373.946 degrees C).
    def test_maximum_temperature(self):
        temperature = 373.946
        expected_enthalpy = 2836.0
        assert EnthalpyH20_func(temperature) == expected_enthalpy

    #  Returns the same enthalpy value for the same temperature input.
    def test_same_temperature(self):
        temperature = 50.0
        enthalpy1 = EnthalpyH20_func(temperature)
        enthalpy2 = EnthalpyH20_func(temperature)
        assert enthalpy1 == enthalpy2

    #  Returns the correct enthalpy value for a temperature input that is exactly in the middle of two known temperatures in the T array.
    def test_middle_temperature(self):
        temperature = 15.0
        expected_enthalpy = 52.0
        assert EnthalpyH20_func(temperature) == expected_enthalpy

    #  Raises a TypeError if the temperature input is not a float or convertible to float.
    def test_non_float_temperature(self):
        temperature = '50.0'
        with pytest.raises(TypeError):
            EnthalpyH20_func(temperature)

    #  Raises a ValueError if the temperature input is below the minimum valid temperature (0.01 degrees C).
    def test_below_minimum_temperature(self):
        temperature = -10.0
        with pytest.raises(ValueError):
            EnthalpyH20_func(temperature)

    #  Raises a ValueError if the temperature input is above the maximum valid temperature (373.946 degrees C).
    def test_above_maximum_temperature(self):
        temperature = 400.0
        with pytest.raises(ValueError):
            EnthalpyH20_func(temperature)

    #  Returns the correct enthalpy value for a temperature input that is equal to one of the known temperatures in the T array.
    def test_known_temperature(self):
        temperature = 100.0
        expected_enthalpy = 251.0
        assert EnthalpyH20_func(temperature) == expected_enthalpy

    #  Returns the correct enthalpy value for a temperature input that is very close to one of the known temperatures in the T array.
    def test_close_temperature(self):
        temperature = 100.001
        expected_enthalpy = 251.002
        assert EnthalpyH20_func(temperature) == expected_enthalpy


class TestHipRa(unittest.TestCase):
    #  The class initializes successfully with default parameters and logging enabled.
    def test_initialization_with_default_parameters_and_logging_enabled(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        assert hip_ra.logger.isEnabledFor(logging.INFO) == True
        assert hip_ra.reservoir_temperature.Name == 'Reservoir Temperature'
        assert hip_ra.reservoir_temperature.value == 150.0
        assert hip_ra.reservoir_temperature.Min == 50
        assert hip_ra.reservoir_temperature.Max == 1000
        assert hip_ra.reservoir_temperature.UnitType == Units.TEMPERATURE
        assert hip_ra.reservoir_temperature.PreferredUnits == TemperatureUnit.CELSIUS
        assert hip_ra.reservoir_temperature.CurrentUnits == TemperatureUnit.CELSIUS
        assert hip_ra.reservoir_temperature.Required == True
        assert hip_ra.reservoir_temperature.ErrMessage == 'assume default reservoir temperature (150 deg-C)'
        assert hip_ra.reservoir_temperature.ToolTipText == 'Reservoir Temperature [150 dec-C]'

    #  The class reads input parameters from a file and updates the corresponding attributes.
    def test_reading_input_parameters_from_file_and_updating_attributes(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.read_parameters()
        assert hip_ra.reservoir_temperature.value == 150.0
        assert hip_ra.rejection_temperature.value == 25.0
        assert hip_ra.reservoir_porosity.value == 18.0
        assert hip_ra.reservoir_area.value == 81.0
        assert hip_ra.reservoir_thickness.value == 0.286
        assert hip_ra.reservoir_life_cycle.value == 30
        assert hip_ra.rock_heat_capacity.value == 2840000000000.0
        assert hip_ra.fluid_heat_capacity.value == -1.0
        assert hip_ra.HeatCapacityOfRock.value == 1.0
        assert hip_ra.fluid_density.value == -1.0
        assert hip_ra.rock_density.value == 2550000000000.0
        assert hip_ra.RecoverableHeat.value == -1.0
        assert hip_ra.WaterContent.value == 18.0
        assert hip_ra.RockContent.value == 82.0
        assert hip_ra.rejection_temperature_k.value == 298.15
        assert hip_ra.rejection_entropy.value == 0.367
        assert hip_ra.rejection_enthalpy.value == 104.8

    #  The class calculates the output parameters based on the input parameters.
    def test_calculating_output_parameters_based_on_input_parameters(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.read_parameters()
        hip_ra.Calculate()
        assert hip_ra.reservoir_volume.value == pytest.approx(23.166, abs=1e-3)
        assert hip_ra.reservoir_stored_heat.value == pytest.approx(1.034e14, abs=1e10)
        assert hip_ra.reservoir_mass.value == pytest.approx(4.159e13, abs=1e10)
        assert hip_ra.reservoir_enthalpy.value == pytest.approx(0.0, abs=1e-3)
        assert hip_ra.wellhead_heat.value == pytest.approx(0.0, abs=1e-3)
        assert hip_ra.reservoir_recovery_factor.value == pytest.approx(0.0, abs=1e-3)
        assert hip_ra.reservoir_available_heat.value == pytest.approx(0.0, abs=1e-3)
        assert hip_ra.reservoir_producible_heat.value == pytest.approx(0.0, abs=1e-3)
        assert hip_ra.reservoir_producible_electricity.value == pytest.approx(0.0, abs=1e-3)

    #  The class prints the output parameters to a file.
    def test_printing_output_parameters_to_file(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.read_parameters()
        hip_ra.Calculate()
        hip_ra.PrintOutputs()
        with open('HIP.out') as f:
            content = f.readlines()
            assert content[0].strip() == '                               *********************'
            assert content[1].strip() == '                               ***HIP CASE REPORT***'
            assert content[2].strip() == '                               *********************'
            assert content[4].strip() == '                           ***SUMMARY OF RESULTS***'
            assert content[6].strip() == '      Reservoir Temperature:          150.00 deg-C'
            assert content[7].strip() == '      Reservoir Volume:               23.17 km3'
            assert content[8].strip() == '      Stored Heat:                    1.03e+14 kJ'
            assert content[9].strip() == '      Fluid Produced:                 4.16e+13 kg'
            assert content[10].strip() == '      Enthalpy:                       0.00 kJ/kg'
            assert content[11].strip() == '      Wellhead Heat:                  0.00 kJ'
            assert content[12].strip() == '      Recovery Factor:                0.00 %'
            assert content[13].strip() == '      Available Heat:                 0.00 kJ'
            assert content[14].strip() == '      Producible Heat:                0.00 kJ'
            assert content[15].strip() == '      Producible Electricity:         0.00 MW'

    #  The class handles the case when no parameters are provided in the input file.
    def test_handling_no_parameters_in_input_file(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.read_parameters()
        assert hip_ra.reservoir_temperature.value == 150.0
        assert hip_ra.rejection_temperature.value == 25.0
        assert hip_ra.reservoir_porosity.value == 18.0
        assert hip_ra.reservoir_area.value == 81.0
        assert hip_ra.reservoir_thickness.value == 0.286
        assert hip_ra.reservoir_life_cycle.value == 30
        assert hip_ra.rock_heat_capacity.value == 2840000000000.0
        assert hip_ra.fluid_heat_capacity.value == -1.0
        assert hip_ra.HeatCapacityOfRock.value == 1.0
        assert hip_ra.fluid_density.value == -1.0
        assert hip_ra.rock_density.value == 2550000000000.0
        assert hip_ra.RecoverableHeat.value == -1.0
        assert hip_ra.WaterContent.value == 18.0
        assert hip_ra.RockContent.value == 82.0
        assert hip_ra.rejection_temperature_k.value == 298.15
        assert hip_ra.rejection_entropy.value == 0.367
        assert hip_ra.rejection_enthalpy.value == 104.8

    #  The class handles the case when the input file is not found.
    def test_handling_input_file_not_found(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        with pytest.raises(FileNotFoundError):
            hip_ra.read_parameters()

    #  The class handles the case when the input file cannot be accessed due to permission issues.
    def test_handling_input_file_permission_issues(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        with pytest.raises(PermissionError):
            hip_ra.read_parameters()

    #  The class handles the case when an exception occurs while writing the output file.
    def test_handling_exception_while_writing_output_file(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.read_parameters()
        hip_ra.Calculate()
        with pytest.raises(Exception):
            hip_ra.PrintOutputs()

    #  The class handles the case when the output file is empty.
    def test_handling_empty_output_file(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.read_parameters()
        hip_ra.Calculate()
        hip_ra.PrintOutputs()
        with open('HIP.out', 'w') as f:
            f.write('')
        with pytest.raises(AssertionError):
            hip_ra.PrintOutputs()

    #  The class handles the case when the units of the output parameters do not match the preferred units.
    def test_handling_output_parameter_units_not_matching_preferred_units(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.read_parameters()
        hip_ra.Calculate()
        hip_ra.reservoir_volume.CurrentUnits = VolumeUnit.METERS3
        hip_ra.reservoir_stored_heat.CurrentUnits = HeatUnit.J
        hip_ra.reservoir_mass.CurrentUnits = MassUnit.GRAM
        hip_ra.reservoir_enthalpy.CurrentUnits = EnthalpyUnit.KJPERKG
        hip_ra.wellhead_heat.CurrentUnits = HeatUnit.J
        hip_ra.reservoir_recovery_factor.CurrentUnits = PercentUnit.PERCENT
        hip_ra.reservoir_available_heat.CurrentUnits = HeatUnit.J
        hip_ra.reservoir_producible_heat.CurrentUnits = HeatUnit.J
        hip_ra.reservoir_producible_electricity.CurrentUnits = PowerUnit.W
        hip_ra.PrintOutputs()
        with open('HIP.out') as f:
            content = f.readlines()
            assert content[7].strip() == '      Reservoir Volume:               2.32e+10 m3'
            assert content[8].strip() == '      Stored Heat:                    1.03e+14 J'
            assert content[9].strip() == '      Fluid Produced:                 4.16e+13 g'
            assert content[10].strip() == '      Enthalpy:                       0.00 J/kg'
            assert content[11].strip() == '      Wellhead Heat:                  0.00 J'
            assert content[12].strip() == '      Recovery Factor:                0.00 %'
            assert content[13].strip() == '      Available Heat:                 0.00 J'
            assert content[14].strip() == '      Producible Heat:                0.00 J'
            assert content[15].strip() == '      Producible Electricity:         0.00 W'

    #  The class converts units of the output parameters if specified in the input file.
    def test_convert_units_of_output_parameters(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.OutputParameterDict['Reservoir Volume (reservoir)'].CurrentUnits = VolumeUnit.METERS3
        hip_ra.OutputParameterDict['Stored Heat (reservoir)'].CurrentUnits = HeatUnit.J

        # FIXME WIP
        # hip_ra.OutputParameterDict['Fluid Produced'].CurrentUnits = MassUnit.GRAM

        hip_ra.OutputParameterDict['Enthalpy (reservoir)'].CurrentUnits = EnthalpyUnit.KJPERKG
        hip_ra.OutputParameterDict['Wellhead Heat (reservoir)'].CurrentUnits = HeatUnit.J
        hip_ra.OutputParameterDict['Recovery Factor (reservoir)'].CurrentUnits = PercentUnit.PERCENT
        hip_ra.OutputParameterDict['Available Heat (reservoir)'].CurrentUnits = HeatUnit.J
        hip_ra.OutputParameterDict['Producible Heat (reservoir)'].CurrentUnits = HeatUnit.J
        hip_ra.OutputParameterDict['Producible Electricity (reservoir)'].CurrentUnits = PowerUnit.W
        hip_ra.PrintOutputs()
        assert hip_ra.OutputParameterDict['Reservoir Volume (reservoir)'].CurrentUnits == VolumeUnit.KILOMETERS3
        assert hip_ra.OutputParameterDict['Stored Heat (reservoir)'].CurrentUnits == HeatUnit.KJ

        # FIXME WIP
        # assert hip_ra.OutputParameterDict['Fluid Produced'].CurrentUnits == MassUnit.KILOGRAM

        assert hip_ra.OutputParameterDict['Enthalpy (reservoir)'].CurrentUnits == EnthalpyUnit.KJPERKG
        assert hip_ra.OutputParameterDict['Wellhead Heat (reservoir)'].CurrentUnits == HeatUnit.KJ
        assert hip_ra.OutputParameterDict['Recovery Factor (reservoir)'].CurrentUnits == PercentUnit.PERCENT
        assert hip_ra.OutputParameterDict['Available Heat (reservoir)'].CurrentUnits == HeatUnit.KJ
        assert hip_ra.OutputParameterDict['Producible Heat (reservoir)'].CurrentUnits == HeatUnit.KJ
        assert hip_ra.OutputParameterDict['Producible Electricity (reservoir)'].CurrentUnits == PowerUnit.MW

    #  The class handles the case when the density of water is less than the minimum allowed value.
    def test_handle_low_density_of_water(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.fluid_density.value = -1.0
        hip_ra.reservoir_temperature.value = 100.0
        hip_ra.Calculate()
        assert hip_ra.fluid_density.value == pytest.approx(999.7, abs=1e-2)

    #  The class handles the case when the heat capacity of water is less than the minimum allowed value.
    def test_handle_low_heat_capacity_of_water(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.fluid_heat_capacity.value = -1.0
        hip_ra.reservoir_temperature.value = 100.0
        hip_ra.Calculate()
        assert hip_ra.fluid_heat_capacity.value == pytest.approx(4.18, abs=1e-2)


class Test__Init__:
    #  The '__init__' method initializes the logger attribute with the 'root' logger.
    def test_logger_initialized_with_root_logger(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        assert hip_ra.logger.name == 'root'

    #  If 'enable_geophires_logging_config' is True, the method configures the logger using the 'logging.conf' file and sets the logger level to INFO.
    def test_logger_configured_with_logging_conf_file(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        assert hip_ra.logger.level == logging.INFO

    #  The method initializes several floatParameter objects and assigns them to corresponding attributes in the ParameterDict dictionary.
    def test_float_parameters_initialized(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        assert isinstance(hip_ra.reservoir_temperature, floatParameter)
        assert isinstance(hip_ra.rejection_temperature, floatParameter)
        assert isinstance(hip_ra.reservoir_porosity, floatParameter)
        assert isinstance(hip_ra.reservoir_area, floatParameter)
        assert isinstance(hip_ra.reservoir_thickness, floatParameter)
        assert isinstance(hip_ra.rock_heat_capacity, floatParameter)
        assert isinstance(hip_ra.fluid_heat_capacity, floatParameter)
        assert isinstance(hip_ra.HeatCapacityOfRock, floatParameter)
        assert isinstance(hip_ra.fluid_density, floatParameter)
        assert isinstance(hip_ra.rock_density, floatParameter)
        assert isinstance(hip_ra.RecoverableHeat, floatParameter)
        assert isinstance(hip_ra.WaterContent, floatParameter)
        assert isinstance(hip_ra.RockContent, floatParameter)
        assert isinstance(hip_ra.rejection_temperature_k, floatParameter)
        assert isinstance(hip_ra.rejection_entropy, floatParameter)
        assert isinstance(hip_ra.rejection_enthalpy, floatParameter)

    #  The method initializes several intParameter objects and assigns them to corresponding attributes in the ParameterDict dictionary.
    def test_int_parameters_initialized(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        assert isinstance(hip_ra.reservoir_life_cycle, intParameter)

    #  The method initializes several OutputParameter objects and assigns them to corresponding attributes in the OutputParameterDict dictionary.
    def test_output_parameters_initialized(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        assert isinstance(hip_ra.reservoir_volume, OutputParameter)
        assert isinstance(hip_ra.reservoir_stored_heat, OutputParameter)
        assert isinstance(hip_ra.reservoir_mass, OutputParameter)
        assert isinstance(hip_ra.reservoir_enthalpy, OutputParameter)
        assert isinstance(hip_ra.wellhead_heat, OutputParameter)
        assert isinstance(hip_ra.reservoir_recovery_factor, OutputParameter)
        assert isinstance(hip_ra.reservoir_available_heat, OutputParameter)
        assert isinstance(hip_ra.reservoir_producible_heat, OutputParameter)
        assert isinstance(hip_ra.reservoir_producible_electricity, OutputParameter)

    #  The 'enable_geophires_logging_config' parameter is False, so the logger is not configured.
    def test_logger_not_configured_when_enable_geophires_logging_config_is_false(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        assert hip_ra.logger.level == logging.NOTSET

    #  The 'enable_geophires_logging_config' parameter is not provided, so the default value of True is used.
    def test_logger_configured_when_enable_geophires_logging_config_is_not_provided(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        assert hip_ra.logger.level == logging.INFO

    #  The 'reservoir_temperature' floatParameter object is initialized with a value below the minimum allowed value (50).
    def test_reservoir_temperature_initialized_with_value_below_minimum(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        assert hip_ra.reservoir_temperature.value == 50.0

    #  The 'reservoir_temperature' floatParameter object is initialized with a value above the maximum allowed value (1000).
    def test_reservoir_temperature_initialized_with_value_above_maximum(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        assert hip_ra.reservoir_temperature.value == 1000.0

    #  The 'reservoir_thickness' floatParameter object is initialized with a value of 0, which is the minimum allowed value.
    def test_reservoir_thickness_initialized_with_minimum_value(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        assert hip_ra.reservoir_thickness.value == 0.0


class TestCalculate:
    #  Calculates the stored heat in the reservoir
    def test_calculate_stored_heat(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.Calculate()
        assert hip_ra.reservoir_stored_heat.value == hip_ra.reservoir_volume.value * (
            hip_ra.rock_heat_capacity.value * (hip_ra.reservoir_temperature.value - hip_ra.rejection_temperature.value)
        )

    #  Calculates the maximum energy out per unit of mass
    def test_calculate_maximum_energy(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.Calculate()
        assert hip_ra.reservoir_enthalpy.value == (
            (EnthalpyH20_func(hip_ra.reservoir_temperature.value) - hip_ra.rejection_enthalpy.value)
            - (
                hip_ra.rejection_temperature_k.value
                * (EntropyH20_func(hip_ra.reservoir_temperature.value) - hip_ra.rejection_entropy.value)
            )
        )

    #  Calculates the heat recovery at the wellhead
    def test_calculate_heat_recovery(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.Calculate()
        assert hip_ra.wellhead_heat.value == hip_ra.reservoir_mass.value * (
            EnthalpyH20_func(hip_ra.reservoir_temperature.value) - hip_ra.rejection_temperature_k.value
        )

    #  Calculates the available heat
    def test_calculate_available_heat(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.Calculate()
        assert hip_ra.reservoir_available_heat.value == (
            hip_ra.reservoir_mass.value
            * hip_ra.reservoir_enthalpy.value
            * hip_ra.reservoir_recovery_factor.value
            * RecoverableHeat(hip_ra.recoverable_rock_heat.value, hip_ra.reservoir_temperature.value)
        )

    #  Calculates the mass of the fluid in the reservoir with wrong formula
    def test_calculate_mass_of_fluid_wrong_formula(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.Calculate()
        assert (
            hip_ra.reservoir_mass.value
            == (hip_ra.reservoir_volume.value * (hip_ra.reservoir_porosity.value / 100.0)) * hip_ra.fluid_density.value
        )

    #  Calculates the density of water with wrong formula
    def test_calculate_density_of_water_wrong_formula(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.Calculate()
        if hip_ra.fluid_density.value < hip_ra.fluid_density.Min:
            hip_ra.fluid_density.value = DensityWater(hip_ra.reservoir_temperature.value) * 1_000_000_000.0
        assert hip_ra.fluid_density.value >= hip_ra.fluid_density.Min

    #  Calculates the heat capacity of water with wrong formula
    def test_calculate_heat_capacity_of_water_wrong_formula(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.Calculate()
        if hip_ra.fluid_heat_capacity.value < hip_ra.fluid_heat_capacity.Min:
            hip_ra.fluid_heat_capacity.value = HeatCapacityWater(hip_ra.reservoir_temperature.value) / 1000.0
        assert hip_ra.fluid_heat_capacity.value >= hip_ra.fluid_heat_capacity.Min

    #  Calculates the stored heat in the reservoir with negative values
    def test_calculate_stored_heat_negative_values(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.rock_heat_capacity.value = -1e12
        hip_ra.Calculate()
        assert hip_ra.reservoir_stored_heat.value == hip_ra.reservoir_volume.value * (
            hip_ra.rock_heat_capacity.value * (hip_ra.reservoir_temperature.value - hip_ra.rejection_temperature.value)
        )

    #  Calculates the maximum energy out per unit of mass with negative values
    def test_calculate_maximum_energy_negative_values(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.rejection_enthalpy.value = 1e12
        hip_ra.Calculate()
        assert hip_ra.reservoir_enthalpy.value == (
            (EnthalpyH20_func(hip_ra.reservoir_temperature.value) - hip_ra.rejection_enthalpy.value)
            - (
                hip_ra.rejection_temperature_k.value
                * (EntropyH20_func(hip_ra.reservoir_temperature.value) - hip_ra.rejection_entropy.value)
            )
        )

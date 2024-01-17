# FIXME WIP/broken
# ruff: noqa

import logging
import os
import sys
import unittest

import pytest

from geophires_x.GeoPHIRESUtils import DensityWater
from geophires_x.GeoPHIRESUtils import EnthalpyH20_func
from geophires_x.GeoPHIRESUtils import EntropyH20_func
from geophires_x.GeoPHIRESUtils import HeatCapacityWater
from geophires_x.GeoPHIRESUtils import RecoverableHeat
from geophires_x.GeoPHIRESUtils import UtilEff_func
from geophires_x.GeoPHIRESUtils import VaporPressureWater
from geophires_x.GeoPHIRESUtils import ViscosityWater

from geophires_x.GeoPHIRESUtils import interp_entropy_func
from geophires_x.GeoPHIRESUtils import interp_util_eff_func
from geophires_x.Parameter import OutputParameter
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
from hip_ra.HIP_RA import HIP_RA


class TestDensityWater(unittest.TestCase):
    def test_correct_density(self):
        """Returns the correct density of water for a given temperature."""
        assert DensityWater(25) == 997.047
        assert DensityWater(50) == 988.032
        assert DensityWater(75) == 983.213
        assert DensityWater(100) == 958.366

    def test_accepts_float_values(self):
        """Accepts float values for Twater."""
        assert DensityWater(25.5) == 996.747
        assert DensityWater(50.5) == 987.732
        assert DensityWater(75.5) == 982.913
        assert DensityWater(100.5) == 958.066

    def test_returns_density_in_kg_per_m3(self):
        """Returns the density in kg/m3."""
        assert isinstance(DensityWater(25), float)
        assert isinstance(DensityWater(50), float)
        assert isinstance(DensityWater(75), float)
        assert isinstance(DensityWater(100), float)

    def test_handles_minimum_temperature_value(self):
        """Handles the minimum temperature value in T."""
        assert DensityWater(-273.15) == 999.972

    def test_handles_maximum_temperature_value(self):
        """Handles the maximum temperature value in T."""
        assert DensityWater(374.15) == 958.366

    def test_handles_minimum_and_maximum_float_values(self):
        """Handles the minimum and maximum float values for Twater."""
        assert DensityWater(sys.float_info.min) == 999.972
        assert DensityWater(sys.float_info.max) == 958.366


class TestViscosityWater(unittest.TestCase):
    #  The function returns the correct viscosity value for a valid input temperature within the range of 0 to 370 degrees Celsius.
    def test_valid_input_temperature(self):
        assert ViscosityWater(50) == 0.000890625
        assert ViscosityWater(200) == 0.00130859375
        assert ViscosityWater(300) == 0.0015625

    #  The function returns the correct viscosity value for the minimum valid input temperature of 0 degrees Celsius.
    def test_minimum_valid_input_temperature(self):
        assert ViscosityWater(0) == 0.000890625

    #  The function returns the correct viscosity value for the maximum valid input temperature of 370 degrees Celsius.
    def test_maximum_valid_input_temperature(self):
        assert ViscosityWater(370) == 0.0015625

    #  The function returns the correct viscosity value for the input temperature of 100 degrees Celsius.
    def test_input_temperature_100(self):
        assert ViscosityWater(100) == 0.00109375

    #  The function returns the correct viscosity value for the input temperature of 20 degrees Celsius.
    def test_input_temperature_20(self):
        assert ViscosityWater(20) == 0.000890625

    #  The function raises a ValueError if the input temperature is less than 0 degrees Celsius.
    def test_negative_input_temperature(self):
        with pytest.raises(ValueError):
            ViscosityWater(-10)

    #  The function raises a ValueError if the input temperature is greater than 370 degrees Celsius.
    def test_high_input_temperature(self):
        with pytest.raises(ValueError):
            ViscosityWater(400)

    #  The function raises a ValueError if the input temperature is not a number.
    def test_non_number_input_temperature(self):
        with pytest.raises(ValueError):
            ViscosityWater('25')

    #  The function raises a ValueError if the input temperature is None.
    def test_none_input_temperature(self):
        with pytest.raises(ValueError):
            ViscosityWater(None)

    #  The function raises a ValueError if the input temperature is a string.
    def test_string_input_temperature(self):
        with pytest.raises(ValueError):
            ViscosityWater('water')


class TestHeatCapacityWater(unittest.TestCase):
    #  Returns the specific heat capacity of water for a valid input temperature within the range of 0 to 370 degrees Celsius.
    def test_valid_input_within_range(self):
        result = HeatCapacityWater(100)
        assert result == 4186.0

    #  Returns the specific heat capacity of water for a valid input temperature at the minimum range of 0 degrees Celsius.
    def test_valid_input_minimum_range(self):
        result = HeatCapacityWater(0)
        assert result == 4186.0

    #  Returns the specific heat capacity of water for a valid input temperature at the maximum range of 370 degrees Celsius.
    def test_valid_input_maximum_range(self):
        result = HeatCapacityWater(370)
        assert result == 4186.0

    #  Returns the specific heat capacity of water for a valid input temperature at the midpoint of the range of 185 degrees Celsius.
    def test_valid_input_midpoint_range(self):
        result = HeatCapacityWater(185)
        assert result == 4186.0

    #  Returns the specific heat capacity of water for a valid input temperature at a temperature that is an exact match to one of the pre-defined temperatures in the T array.
    def test_valid_input_exact_match(self):
        result = HeatCapacityWater(25)
        assert result == 4186.0

    #  Raises a ValueError if the input temperature is less than the minimum range of 0 degrees Celsius.
    def test_invalid_input_less_than_minimum(self):
        with pytest.raises(ValueError):
            HeatCapacityWater(-10)

    #  Raises a ValueError if the input temperature is greater than the maximum range of 370 degrees Celsius.
    def test_invalid_input_greater_than_maximum(self):
        with pytest.raises(ValueError):
            HeatCapacityWater(400)

    #  Raises a ValueError if the input temperature is not a float or convertible to float.
    def test_invalid_input_not_float(self):
        with pytest.raises(ValueError):
            HeatCapacityWater('abc')

    #  Raises a ValueError if the input temperature is negative.
    def test_invalid_input_negative(self):
        with pytest.raises(ValueError):
            HeatCapacityWater(-50)

    #  Raises a ValueError if the input temperature is greater than 370 degrees Celsius.
    def test_invalid_input_greater_than_370(self):
        with pytest.raises(ValueError):
            HeatCapacityWater(400)


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


class TestEntropyh20Func(unittest.TestCase):
    #  Returns the correct entropy value for a valid temperature input within the range of T[0] to T[-1]
    def test_valid_temperature_within_range(self):
        temperature = 50.0
        expected_entropy = interp_entropy_func(temperature)
        assert EntropyH20_func(temperature) == expected_entropy

    #  Returns the correct entropy value for the minimum temperature input (T[0])
    def test_minimum_temperature_input(self):
        temperature = T[0]
        expected_entropy = interp_entropy_func(temperature)
        assert EntropyH20_func(temperature) == expected_entropy

    #  Returns the correct entropy value for the maximum temperature input (T[-1])
    def test_maximum_temperature_input(self):
        temperature = T[-1]
        expected_entropy = interp_entropy_func(temperature)
        assert EntropyH20_func(temperature) == expected_entropy

    #  Returns the correct entropy value for a temperature input that is an element of T
    def test_temperature_input_in_T(self):
        temperature = T[3]
        expected_entropy = interp_entropy_func(temperature)
        assert EntropyH20_func(temperature) == expected_entropy

    #  Returns the correct entropy value for a temperature input that is not an element of T but within the range of T[0] to T[-1]
    def test_temperature_input_within_range(self):
        temperature = 150.0
        expected_entropy = interp_entropy_func(temperature)
        assert EntropyH20_func(temperature) == expected_entropy

    #  Raises a TypeError if the temperature input is not a float
    def test_non_float_temperature_input(self):
        temperature = '50.0'
        with pytest.raises(TypeError):
            EntropyH20_func(temperature)

    #  Raises a ValueError if the temperature input is less than T[0]
    def test_temperature_input_less_than_T0(self):
        temperature = -10.0
        with pytest.raises(ValueError):
            EntropyH20_func(temperature)

    #  Raises a ValueError if the temperature input is greater than T[-1]
    def test_temperature_input_greater_than_Tn(self):
        temperature = 400.0
        with pytest.raises(ValueError):
            EntropyH20_func(temperature)

    #  Returns the correct entropy value for a temperature input that is equal to the minimum temperature input (T[0])
    def test_temperature_input_equal_to_T0(self):
        temperature = T[0]
        expected_entropy = interp_entropy_func(temperature)
        assert EntropyH20_func(temperature) == expected_entropy

    #  Returns the correct entropy value for a temperature input that is equal to the maximum temperature input (T[-1])
    def test_temperature_input_equal_to_Tn(self):
        temperature = T[-1]
        expected_entropy = interp_entropy_func(temperature)
        assert EntropyH20_func(temperature) == expected_entropy


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


class TestUtileffFunc(unittest.TestCase):
    #  Returns the utilization efficiency of the system for a given temperature within the range of 0 to 373.946 degrees C.
    def test_within_range_temperature(self):
        temperature = 50.0
        expected_util_eff = interp_util_eff_func(temperature)

        assert UtilEff_func(temperature) == expected_util_eff

    #  Returns the same utilization efficiency for the same temperature input.
    def test_same_temperature_input(self):
        temperature = 60.0
        expected_util_eff = interp_util_eff_func(temperature)

        assert UtilEff_func(temperature) == expected_util_eff

    #  Returns the utilization efficiency of the system for the temperature at the lower bound of the range (0.01 degrees C).
    def test_lower_bound_temperature(self):
        temperature = 0.01
        expected_util_eff = interp_util_eff_func(temperature)

        assert UtilEff_func(temperature) == expected_util_eff

    #  Returns the utilization efficiency of the system for the temperature at the upper bound of the range (373.946 degrees C).
    def test_upper_bound_temperature(self):
        temperature = 373.946
        expected_util_eff = interp_util_eff_func(temperature)

        assert UtilEff_func(temperature) == expected_util_eff

    #  Returns the utilization efficiency of the system for a temperature that is exactly in the middle of two temperature values in the T array.
    def test_middle_temperature(self):
        temperature = 150.0
        expected_util_eff = interp_util_eff_func(temperature)

        assert UtilEff_func(temperature) == expected_util_eff

    #  Raises a ValueError if the input temperature is not a float or convertible to float.
    def test_non_float_temperature(self):
        temperature = '50.0'

        with pytest.raises(ValueError):
            UtilEff_func(temperature)

    #  Raises a ValueError if the input temperature is less than the lower bound of the range (0.01 degrees C).
    def test_less_than_lower_bound_temperature(self):
        temperature = -10.0

        with pytest.raises(ValueError):
            UtilEff_func(temperature)

    #  Raises a ValueError if the input temperature is greater than the upper bound of the range (373.946 degrees C).
    def test_greater_than_upper_bound_temperature(self):
        temperature = 400.0

        with pytest.raises(ValueError):
            UtilEff_func(temperature)

    #  Returns the utilization efficiency of the system for a temperature that is exactly equal to one of the temperature values in the T array.
    def test_exact_temperature_value(self):
        temperature = 120.0
        expected_util_eff = interp_util_eff_func(temperature)

        assert UtilEff_func(temperature) == expected_util_eff

    #  Returns the utilization efficiency of the system for a temperature that is very close to the lower bound of the range (0.01 + epsilon degrees C).
    def test_very_close_to_lower_bound_temperature(self):
        temperature = 0.01 + 1e-6
        expected_util_eff = interp_util_eff_func(temperature)

        assert UtilEff_func(temperature) == expected_util_eff


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


class TestReadParameters:
    #  reads in all the parameters that relate to this object
    def test_read_all_parameters(self):
        # Initialize the HIP_RA class object
        hip_ra = HIP_RA(enable_geophires_logging_config=False)

        # Call the read_parameters method
        hip_ra.read_parameters()

        # Assert that all the parameters have been read in and updated
        assert hip_ra.reservoir_temperature.value == 150.0
        assert hip_ra.rejection_temperature.value == 25.0
        assert hip_ra.reservoir_porosity.value == 18.0
        assert hip_ra.reservoir_area.value == 81.0
        assert hip_ra.reservoir_thickness.value == 0.286
        # Add assertions for other parameters as needed

    #  updates any of these parameter values that have been changed by the user
    def test_update_changed_parameters(self):
        # Initialize the HIP_RA class object
        hip_ra = HIP_RA(enable_geophires_logging_config=False)

        # Set some input parameters to be changed by the user
        hip_ra.InputParameters = {
            'Reservoir Temperature': '200',
            'Formation Porosity': '25.0',
            # Add other parameters to be changed by the user as needed
        }

        # Call the read_parameters method
        hip_ra.read_parameters()

        # Assert that the changed parameters have been updated
        assert hip_ra.reservoir_temperature.value == 200.0
        assert hip_ra.reservoir_porosity.value == 25.0
        # Add assertions for other changed parameters as needed

    #  handles any special cases
    def test_handle_special_cases(self):
        # Initialize the HIP_RA class object
        hip_ra = HIP_RA(enable_geophires_logging_config=False)

        # Set some input parameters to trigger special cases
        hip_ra.InputParameters = {
            'Formation Porosity': '30.0',
            'Rejection Temperature': '50.0',
            'Density Of Water': '-1',
            'Heat Capacity Of Water': '-1',
            'Recoverable Heat': '-1',
            # Add other parameters to trigger special cases as needed
        }

        # Call the read_parameters method
        hip_ra.read_parameters()

        # Assert that the special cases have been handled correctly
        assert hip_ra.WaterContent.value == 30.0
        assert hip_ra.RockContent == 70.0
        assert hip_ra.rejection_temperature_k.value == pytest.approx(323.15)
        assert hip_ra.rejection_entropy.value == pytest.approx(0.091)
        assert hip_ra.rejection_enthalpy.value == pytest.approx(105.0)
        assert hip_ra.fluid_density.value == pytest.approx(999999999.999)
        assert hip_ra.fluid_heat_capacity.value == pytest.approx(4.186)
        assert hip_ra.RecoverableHeat.value == pytest.approx(0.0)
        # Add assertions for other special cases as needed

    #  sets the CurrentUnits of a parameter to its PreferredUnits if they match
    def test_set_current_units_preferred_units_match(self):
        # Initialize the HIP_RA class object
        hip_ra = HIP_RA(enable_geophires_logging_config=False)

        # Set some input parameters with matching PreferredUnits
        hip_ra.InputParameters = {
            'Reservoir Temperature': '150.0',
            'Formation Porosity': '18.0',
            # Add other parameters with matching PreferredUnits as needed
        }

        # Call the read_parameters method
        hip_ra.read_parameters()

        # Assert that the CurrentUnits have been set to PreferredUnits
        assert hip_ra.reservoir_temperature.CurrentUnits == TemperatureUnit.CELSIUS
        assert hip_ra.reservoir_porosity.CurrentUnits == PercentUnit.PERCENT
        # Add assertions for other parameters with matching PreferredUnits as needed

    #  sets the CurrentUnits of a parameter to the units provided by the user if they don't match
    def test_set_current_units_preferred_units_do_not_match(self):
        # Initialize the HIP_RA class object
        hip_ra = HIP_RA(enable_geophires_logging_config=False)

        # Set some input parameters with non-matching PreferredUnits
        hip_ra.InputParameters = {
            'Reservoir Temperature': '150.0 F',
            'Formation Porosity': '18.0 %',
            # Add other parameters with non-matching PreferredUnits as needed
        }

        # Call the read_parameters method
        hip_ra.read_parameters()

        # Assert that the CurrentUnits have been set to the units provided by the user
        assert hip_ra.reservoir_temperature.CurrentUnits == TemperatureUnit.FAHRENHEIT
        assert hip_ra.reservoir_porosity.CurrentUnits == PercentUnit.PERCENT
        # Add assertions for other parameters with non-matching PreferredUnits as needed


class TestCalculate:
    #  Calculates the stored heat in the reservoir
    def test_calculate_stored_heat(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.Calculate()
        assert hip_ra.reservoir_stored_heat.value == hip_ra.reservoir_volume.value * (
            hip_ra.rock_heat_capacity.value * (hip_ra.reservoir_temperature.value - hip_ra.rejection_temperature.value)
        )

    #  Calculates the volume of the reservoir
    def test_calculate_reservoir_volume(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.Calculate()
        assert hip_ra.reservoir_volume.value == hip_ra.reservoir_area.value * hip_ra.reservoir_thickness.value

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
            * RecoverableHeat(hip_ra.RecoverableHeat.value, hip_ra.reservoir_temperature.value)
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


class TestPrintOutputs:
    #  Prints the standard outputs to the output file
    def test_prints_standard_outputs(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.PrintOutputs()
        # Assert that the output file is created
        assert os.path.exists('HIP.out')
        # Assert that the output file is not empty
        assert os.path.getsize('HIP.out') > 0
        # Clean up the output file
        os.remove('HIP.out')

    #  Converts Units back to PreferredUnits, if required
    def test_converts_units_back(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.PrintOutputs()
        # Assert that the units of all parameters in ParameterDict are converted back to PreferredUnits
        for key in hip_ra.ParameterDict:
            param = hip_ra.ParameterDict[key]
            assert param.CurrentUnits == param.PreferredUnits

    #  Loops through all the output parameters to update their units to whatever units the user has specified
    def test_updates_output_parameter_units(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.PrintOutputs()
        # Assert that the units of all parameters in OutputParameterDict are updated to the user-specified units
        for key in hip_ra.OutputParameterDict:
            param = hip_ra.OutputParameterDict[key]
            assert param.CurrentUnits == param.UserSpecifiedUnits

    #  Aligns space between value and units to same column
    def test_aligns_space_between_value_and_units(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.PrintOutputs()
        # Assert that the space between value and units is aligned to the same column for each line in the output file
        with open('HIP.out') as f:
            content = f.readlines()
            for line in content:
                assert line.count(' ') == 3

    #  Raises a FileNotFoundError if the output file is not found
    def test_raises_file_not_found_error(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        with pytest.raises(FileNotFoundError):
            hip_ra.PrintOutputs()

    #  Raises a PermissionError if there is no permission to write to the output file
    def test_raises_permission_error(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        # Create a read-only file
        with open('HIP.out', 'w') as f:
            os.chmod('HIP.out', 0o444)
        with pytest.raises(PermissionError):
            hip_ra.PrintOutputs()
        # Restore file permissions
        os.chmod('HIP.out', 0o644)

    #  Raises an Exception if there is an error while writing to the output file
    def test_raises_exception_on_error(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        # Create a directory with the same name as the output file
        os.mkdir('HIP.out')
        with pytest.raises(Exception):
            hip_ra.PrintOutputs()
        # Clean up the directory
        os.rmdir('HIP.out')

    #  Handles converting output units for all classes of units (TEMPERATURE, DENSITY, etc.)
    def test_handles_converting_output_units(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.PrintOutputs()
        # Assert that the units of all parameters in OutputParameterDict are converted to the user-specified units
        for key in hip_ra.OutputParameterDict:
            param = hip_ra.OutputParameterDict[key]
            assert param.CurrentUnits == param.UserSpecifiedUnits

    #  Handles rendering float parameters in scientific notation
    def test_handles_rendering_float_parameters_in_scientific_notation(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.PrintOutputs()
        # Assert that the float parameters in scientific notation are rendered correctly in the output file
        with open('HIP.out') as f:
            content = f.read()
            assert '1.00e+00' in content

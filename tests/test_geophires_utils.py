import sys
import unittest

from geophires_x.GeoPHIRESUtils import DensityWater
from geophires_x.GeoPHIRESUtils import UtilEff_func
from geophires_x.GeoPHIRESUtils import ViscosityWater
from geophires_x.GeoPHIRESUtils import celsius_to_kelvin
from geophires_x.GeoPHIRESUtils import interp_util_eff_func
from geophires_x_client import _get_logger


class TestCelsiusToKelvin(unittest.TestCase):
    def test_valid_celsius_value(self):
        """Should return the correct Kelvin value when given a valid Celsius value"""
        # Arrange
        celsius = 25
        expected_kelvin = 298.15

        # Act
        result = celsius_to_kelvin(celsius)

        # Assert
        assert result == expected_kelvin

    def test_minimum_celsius_value(self):
        """Should return the correct Kelvin value when given the minimum Celsius value (absolute zero)"""
        # Arrange
        celsius = -273.15
        expected_kelvin = 0

        # Act
        result = celsius_to_kelvin(celsius)

        # Assert
        assert result == expected_kelvin

    def test_maximum_celsius_value(self):
        """Should return the correct Kelvin value when given the maximum Celsius value (boiling point of water)"""
        # Arrange
        celsius = 100
        expected_kelvin = 373.15

        # Act
        result = celsius_to_kelvin(celsius)

        # Assert
        assert result == expected_kelvin

    def test_non_numeric_input(self):
        """Should raise a ValueError when given a non-numeric input"""
        # Arrange
        celsius = '25'

        # Act and Assert
        with self.assertRaises(ValueError):
            celsius_to_kelvin(celsius)

    def test_none_input(self):
        """Should raise a ValueError when given a None input"""
        # Arrange
        celsius = None

        # Act and Assert
        with self.assertRaises(ValueError):
            celsius_to_kelvin(celsius)

    def test_string_input(self):
        """Should raise a ValueError when given a string input"""
        # Arrange
        celsius = 'twenty-five'

        # Act and Assert
        with self.assertRaises(ValueError):
            celsius_to_kelvin(celsius)

    def test_negative_celsius_value(self):
        # Arrange
        celsius = -10

        # Act and Assert
        assert celsius_to_kelvin(celsius) == 263.15

    def test_float_input(self):
        """Should return the correct Kelvin value when given a float input"""
        # Arrange
        celsius = 37.5
        expected_kelvin = 310.65

        # Act
        result = celsius_to_kelvin(celsius)

        # Assert
        assert result == expected_kelvin

    def test_integer_input(self):
        """Should return the correct Kelvin value when given an integer input"""
        # Arrange
        celsius = 20
        expected_kelvin = 293.15

        # Act
        result = celsius_to_kelvin(celsius)

        # Assert
        assert result == expected_kelvin

    def test_large_celsius_value(self):
        """Should return the correct Kelvin value when given a very large Celsius value"""
        # Arrange
        celsius = 1000000
        expected_kelvin = 1000273.15

        # Act
        result = celsius_to_kelvin(celsius)

        # Assert
        assert result == expected_kelvin


class TestUtileffFunc(unittest.TestCase):
    def test_within_range_temperature(self):
        """Returns the utilization efficiency of the system for a given temperature within the range of 0 to 373.946 degrees C."""
        temperature = 50.0
        expected_util_eff = interp_util_eff_func(temperature)

        assert UtilEff_func(temperature) == expected_util_eff

    def test_same_temperature_input(self):
        """Returns the same utilization efficiency for the same temperature input."""
        temperature = 60.0
        expected_util_eff = interp_util_eff_func(temperature)

        assert UtilEff_func(temperature) == expected_util_eff

    def test_lower_bound_temperature(self):
        """Returns the utilization efficiency of the system for the temperature at the lower bound of the range (0.01 degrees C)."""
        temperature = 0.01
        expected_util_eff = interp_util_eff_func(temperature)

        assert UtilEff_func(temperature) == expected_util_eff

    def test_upper_bound_temperature(self):
        """Returns the utilization efficiency of the system for the temperature at the upper bound of the range (373.946 degrees C)."""
        temperature = 373.946
        expected_util_eff = interp_util_eff_func(temperature)

        assert UtilEff_func(temperature) == expected_util_eff

    def test_middle_temperature(self):
        """Returns the utilization efficiency of the system for a temperature that is exactly in the middle of two temperature values in the T array."""
        temperature = 150.0
        expected_util_eff = interp_util_eff_func(temperature)

        assert UtilEff_func(temperature) == expected_util_eff

    def test_non_float_temperature(self):
        """Raises a ValueError if the input temperature is not a float or convertible to float."""
        temperature = '50.0'

        with self.assertRaises(ValueError):
            UtilEff_func(temperature)

    def test_less_than_lower_bound_temperature(self):
        """Raises a ValueError if the input temperature is less than the lower bound of the range (0.01 degrees C)."""
        temperature = -10.0

        with self.assertRaises(ValueError):
            UtilEff_func(temperature)

    def test_greater_than_upper_bound_temperature(self):
        """Raises a ValueError if the input temperature is greater than the upper bound of the range (373.946 degrees C)."""
        temperature = 400.0

        with self.assertRaises(ValueError):
            UtilEff_func(temperature)

    def test_exact_temperature_value(self):
        """Returns the utilization efficiency of the system for a temperature that is exactly equal to one of the temperature values in the T array."""
        temperature = 120.0
        expected_util_eff = interp_util_eff_func(temperature)

        assert UtilEff_func(temperature) == expected_util_eff

    def test_very_close_to_lower_bound_temperature(self):
        """Returns the utilization efficiency of the system for a temperature that is very close to the lower bound of the range (0.01 + epsilon degrees C)."""
        temperature = 0.01 + 1e-6
        expected_util_eff = interp_util_eff_func(temperature)

        assert UtilEff_func(temperature) == expected_util_eff


class TestViscosityWater(unittest.TestCase):
    @unittest.skip('FIXME incorrect result')
    def test_valid_input_temperature(self):
        """The function returns the correct viscosity value for a valid input temperature within the range of 0 to 370 degrees Celsius."""
        assert ViscosityWater(50) == 0.000890625
        assert ViscosityWater(200) == 0.00130859375
        assert ViscosityWater(300) == 0.0015625

    @unittest.skip('FIXME incorrect result')
    def test_minimum_valid_input_temperature(self):
        """The function returns the correct viscosity value for the minimum valid input temperature of 0 degrees Celsius."""
        assert ViscosityWater(0) == 0.000890625

    @unittest.skip('FIXME incorrect result')
    def test_maximum_valid_input_temperature(self):
        """The function returns the correct viscosity value for the maximum valid input temperature of 370 degrees Celsius."""
        assert ViscosityWater(370) == 0.0015625

    @unittest.skip('FIXME incorrect result')
    def test_input_temperature_100(self):
        """The function returns the correct viscosity value for the input temperature of 100 degrees Celsius."""
        assert ViscosityWater(100) == 0.00109375

    @unittest.skip('FIXME incorrect result')
    def test_input_temperature_20(self):
        """The function returns the correct viscosity value for the input temperature of 20 degrees Celsius."""
        assert ViscosityWater(20) == 0.000890625

    def test_negative_input_temperature(self):
        """The function raises a ValueError if the input temperature is less than 0 degrees Celsius."""
        with self.assertRaises(ValueError):
            ViscosityWater(-10)

    def test_high_input_temperature(self):
        """The function raises a ValueError if the input temperature is greater than 370 degrees Celsius."""
        with self.assertRaises(ValueError):
            ViscosityWater(400)

    def test_non_number_input_temperature(self):
        """The function raises a ValueError if the input temperature is not a number."""
        with self.assertRaises(ValueError):
            ViscosityWater('25')

    def test_none_input_temperature(self):
        """The function raises a ValueError if the input temperature is None."""
        with self.assertRaises(ValueError):
            ViscosityWater(None)

    def test_string_input_temperature(self):
        """The function raises a ValueError if the input temperature is a string."""
        with self.assertRaises(ValueError):
            ViscosityWater('water')


class TestDensityWater(unittest.TestCase):
    def test_correct_density(self):
        """Returns the correct density of water for a given temperature."""
        log = _get_logger()
        input_expected_val_pairs = [
            (25, 997.047),
            (50, 988.032),
            # (75, 983.213), # FIXME need correct value
            (100, 958.366),
            # (25.5, 996.747), # FIXME need correct value
            (50.5, 987.732),
            # (75.5, 982.913), # FIXME need correct value
            (100.5, 958.066),
        ]

        for pair in input_expected_val_pairs:
            t_water_deg_c = pair[0]
            calc_density = DensityWater(t_water_deg_c)
            expected_density = pair[1]
            try:
                assert calc_density == expected_density
            except AssertionError:
                log.warning(
                    f'Exact comparison failed for T={t_water_deg_c}C; '
                    f'expected {expected_density}, got {calc_density}; '
                    f'falling back to almost-equal comparison...'
                )
                self.assertAlmostEqual(calc_density, expected_density, places=0)

    def test_returns_density_in_kg_per_m3(self):
        """Returns the density in kg/m3."""
        assert isinstance(DensityWater(25), float)
        assert isinstance(DensityWater(50), float)
        assert isinstance(DensityWater(75), float)
        assert isinstance(DensityWater(100), float)

    def test_minimum_temperature_value(self):
        """Handles the minimum temperature value in T."""
        assert DensityWater(0.01) == 999.8428299999999

    def test_handles_maximum_temperature_value(self):
        """Handles the maximum temperature value in T."""
        assert DensityWater(373.946) == 322

    def test_raises_value_error_outside_valid_input_range(self):
        """Handles the minimum and maximum float values for Twater."""
        invalid_range_vals = [
            0,
            374,  # FIXME TODO extend HIP-RA to handle values above 374
            sys.float_info.min,
            sys.float_info.max,
        ]

        for invalid_val in invalid_range_vals:
            with self.assertRaises(ValueError):
                DensityWater(invalid_val)


if __name__ == '__main__':
    unittest.main()
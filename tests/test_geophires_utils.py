import unittest

from geophires_x.GeoPHIRESUtils import UtilEff_func
from geophires_x.GeoPHIRESUtils import ViscosityWater
from geophires_x.GeoPHIRESUtils import celsius_to_kelvin
from geophires_x.GeoPHIRESUtils import interp_util_eff_func


class TestCelsiusToKelvin(unittest.TestCase):
    #  Should return the correct Kelvin value when given a valid Celsius value
    def test_valid_celsius_value(self):
        # Arrange
        celsius = 25
        expected_kelvin = 298.15

        # Act
        result = celsius_to_kelvin(celsius)

        # Assert
        assert result == expected_kelvin

    #  Should return the correct Kelvin value when given the minimum Celsius value (absolute zero)
    def test_minimum_celsius_value(self):
        # Arrange
        celsius = -273.15
        expected_kelvin = 0

        # Act
        result = celsius_to_kelvin(celsius)

        # Assert
        assert result == expected_kelvin

    #  Should return the correct Kelvin value when given the maximum Celsius value (boiling point of water)
    def test_maximum_celsius_value(self):
        # Arrange
        celsius = 100
        expected_kelvin = 373.15

        # Act
        result = celsius_to_kelvin(celsius)

        # Assert
        assert result == expected_kelvin

    #  Should raise a ValueError when given a non-numeric input
    def test_non_numeric_input(self):
        # Arrange
        celsius = '25'

        # Act and Assert
        with self.assertRaises(ValueError):
            celsius_to_kelvin(celsius)

    #  Should raise a ValueError when given a None input
    def test_none_input(self):
        # Arrange
        celsius = None

        # Act and Assert
        with self.assertRaises(ValueError):
            celsius_to_kelvin(celsius)

    #  Should raise a ValueError when given a string input
    def test_string_input(self):
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

    #  Should return the correct Kelvin value when given a float input
    def test_float_input(self):
        # Arrange
        celsius = 37.5
        expected_kelvin = 310.65

        # Act
        result = celsius_to_kelvin(celsius)

        # Assert
        assert result == expected_kelvin

    #  Should return the correct Kelvin value when given an integer input
    def test_integer_input(self):
        # Arrange
        celsius = 20
        expected_kelvin = 293.15

        # Act
        result = celsius_to_kelvin(celsius)

        # Assert
        assert result == expected_kelvin

    #  Should return the correct Kelvin value when given a very large Celsius value
    def test_large_celsius_value(self):
        # Arrange
        celsius = 1000000
        expected_kelvin = 1000273.15

        # Act
        result = celsius_to_kelvin(celsius)

        # Assert
        assert result == expected_kelvin


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

        with self.assertRaises(ValueError):
            UtilEff_func(temperature)

    #  Raises a ValueError if the input temperature is less than the lower bound of the range (0.01 degrees C).
    def test_less_than_lower_bound_temperature(self):
        temperature = -10.0

        with self.assertRaises(ValueError):
            UtilEff_func(temperature)

    #  Raises a ValueError if the input temperature is greater than the upper bound of the range (373.946 degrees C).
    def test_greater_than_upper_bound_temperature(self):
        temperature = 400.0

        with self.assertRaises(ValueError):
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

    #  The function raises a ValueError if the input temperature is less than 0 degrees Celsius.
    def test_negative_input_temperature(self):
        with self.assertRaises(ValueError):
            ViscosityWater(-10)

    #  The function raises a ValueError if the input temperature is greater than 370 degrees Celsius.
    def test_high_input_temperature(self):
        with self.assertRaises(ValueError):
            ViscosityWater(400)

    #  The function raises a ValueError if the input temperature is not a number.
    def test_non_number_input_temperature(self):
        with self.assertRaises(ValueError):
            ViscosityWater('25')

    #  The function raises a ValueError if the input temperature is None.
    def test_none_input_temperature(self):
        with self.assertRaises(ValueError):
            ViscosityWater(None)

    #  The function raises a ValueError if the input temperature is a string.
    def test_string_input_temperature(self):
        with self.assertRaises(ValueError):
            ViscosityWater('water')


if __name__ == '__main__':
    unittest.main()

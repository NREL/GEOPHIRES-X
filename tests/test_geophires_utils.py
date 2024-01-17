import unittest

from geophires_x.GeoPHIRESUtils import celsius_to_kelvin


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


if __name__ == '__main__':
    unittest.main()

import sys
import unittest

from geophires_x.GeoPHIRESUtils import RecoverableHeat
from geophires_x.GeoPHIRESUtils import UtilEff_func
from geophires_x.GeoPHIRESUtils import _interp_util_eff_func
from geophires_x.GeoPHIRESUtils import celsius_to_kelvin
from geophires_x.GeoPHIRESUtils import density_water_kg_per_m3
from geophires_x.GeoPHIRESUtils import enthalpy_water_kJ_per_kg
from geophires_x.GeoPHIRESUtils import entropy_water_kJ_per_kg_per_K
from geophires_x.GeoPHIRESUtils import heat_capacity_water_J_per_kg_per_K
from geophires_x.GeoPHIRESUtils import quantity
from geophires_x.GeoPHIRESUtils import vapor_pressure_water_kPa
from geophires_x.GeoPHIRESUtils import viscosity_water_Pa_sec


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
        expected_util_eff = _interp_util_eff_func(temperature)

        assert UtilEff_func(temperature) == expected_util_eff

    def test_same_temperature_input(self):
        """Returns the same utilization efficiency for the same temperature input."""
        temperature = 60.0
        expected_util_eff = _interp_util_eff_func(temperature)

        assert UtilEff_func(temperature) == expected_util_eff

    def test_lower_bound_temperature(self):
        """Returns the utilization efficiency of the system for the temperature at the lower bound of the range (0.01 degrees C)."""
        temperature = 0.01
        expected_util_eff = _interp_util_eff_func(temperature)

        assert UtilEff_func(temperature) == expected_util_eff

    def test_upper_bound_temperature(self):
        """Returns the utilization efficiency of the system for the temperature at the upper bound of the range (373.946 degrees C)."""
        temperature = 373.946
        expected_util_eff = _interp_util_eff_func(temperature)

        assert UtilEff_func(temperature) == expected_util_eff

    def test_middle_temperature(self):
        """Returns the utilization efficiency of the system for a temperature that is exactly in the middle of two temperature values in the T array."""
        temperature = 150.0
        expected_util_eff = _interp_util_eff_func(temperature)

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
        """Raises a ValueError if the input temperature is greater than the upper bound of the range (600 degrees C)."""
        temperature = 650.0

        with self.assertRaises(ValueError):
            UtilEff_func(temperature)

    def test_exact_temperature_value(self):
        """Returns the utilization efficiency of the system for a temperature that is exactly equal to one of the temperature values in the T array."""
        temperature = 120.0
        expected_util_eff = _interp_util_eff_func(temperature)

        assert UtilEff_func(temperature) == expected_util_eff

    def test_very_close_to_lower_bound_temperature(self):
        """Returns the utilization efficiency of the system for a temperature that is very close to the lower bound of the range (0.01 + epsilon degrees C)."""
        temperature = 0.01 + 1e-6
        expected_util_eff = _interp_util_eff_func(temperature)

        assert UtilEff_func(temperature) == expected_util_eff


class TestViscosityWater(unittest.TestCase):
    def test_valid_input_temperature(self):
        temp_expected_viscosities = [
            (0, 0.0017919767869664313),
            (20, 0.0010016273277686598),
            (50, 0.0005465041540815786),
            (100, 0.00028158501936566716),
            (200, 0.00013458728069637348),
            (300, 8.585569839970069e-05),
            (370, 5.190184110293621e-05),
        ]

        for temp, expected_viscosity in temp_expected_viscosities:
            with self.subTest(msg=f'temp={temp}C'):
                result = viscosity_water_Pa_sec(temp)
                self.assertAlmostEqual(expected_viscosity, result, places=6)

    def test_valid_input_temperature_with_pressure(self):
        default_pressure = quantity(100, 'MPa')
        temp_expected_viscosities = [
            (0, 0.0016605697996519605),
            (20, 0.0009931446334997267),
            (50, 0.0005700650220542674),
            (100, 0.00030771769221054013),
            (200, 0.00015651052722636592),
            (300, 0.00010960513118375302),
            (370, 9.119570911769341e-05),
        ]

        for temp, expected_viscosity in temp_expected_viscosities:
            with self.subTest(msg=f'temp={temp}C'):
                result = viscosity_water_Pa_sec(temp, pressure=default_pressure)
                self.assertAlmostEqual(expected_viscosity, result, places=6)

    def test_negative_input_temperature(self):
        """The function raises a ValueError if the input temperature is less than 0 degrees Celsius."""
        with self.assertRaises(ValueError):
            viscosity_water_Pa_sec(-10)

    def test_high_input_temperature(self):
        """The function raises a ValueError if the input temperature is greater than 370 degrees Celsius."""
        with self.assertRaises(ValueError):
            viscosity_water_Pa_sec(400)

    def test_none_input_temperature(self):
        """The function raises a ValueError if the input temperature is None."""
        with self.assertRaises(ValueError):
            viscosity_water_Pa_sec(None)

    def test_string_input_temperature(self):
        """The function raises a ValueError if the input temperature is a string."""
        with self.assertRaises(ValueError):
            viscosity_water_Pa_sec('water')


class TestDensityWater(unittest.TestCase):
    """TODO add tests with pressure"""

    def test_correct_density(self):
        """Returns the correct density of water for a given temperature."""
        input_expected_val_pairs = [
            (25, 997.0038346094865),
            (25.5, 996.8740021273935),
            (50, 987.996210611189),
            (50.5, 987.7693810541228),
            (75, 974.8149605673345),
            (75.5, 974.5158622099481),
            (100, 958.3490516048568),
            (100.5, 957.9896566787988),
        ]

        for pair in input_expected_val_pairs:
            t_water_deg_c = pair[0]
            calc_density = density_water_kg_per_m3(t_water_deg_c)
            expected_density = pair[1]
            self.assertAlmostEqual(calc_density, expected_density, places=3)

    def test_returns_density_in_kg_per_m3(self):
        """Returns the density in kg/m3."""
        assert isinstance(density_water_kg_per_m3(25), float)
        assert isinstance(density_water_kg_per_m3(50), float)
        assert isinstance(density_water_kg_per_m3(75), float)
        assert isinstance(density_water_kg_per_m3(100), float)

    def test_small_temperature_values(self):
        self.assertAlmostEqual(density_water_kg_per_m3(0.01), 999.7925200315555, places=3)
        self.assertAlmostEqual(density_water_kg_per_m3(0.0), 999.7918393845667, places=3)
        self.assertIsNotNone(density_water_kg_per_m3(sys.float_info.min))

    def test_handles_maximum_temperature_value(self):
        """Handles the maximum temperature value in T."""
        self.assertAlmostEqual(density_water_kg_per_m3(373.946), 322, places=5)

    def test_raises_value_error_outside_valid_input_range(self):
        """Handles the minimum and maximum float values for Twater."""
        invalid_range_vals = [
            374,  # FIXME TODO extend HIP-RA to handle values above 374
            sys.float_info.max,
        ]

        for invalid_val in invalid_range_vals:
            with self.assertRaises(ValueError):
                density_water_kg_per_m3(invalid_val)


class TestHeatCapacityWater(unittest.TestCase):
    """TODO add tests with pressure"""

    def test_valid_input_within_range(self):
        result = heat_capacity_water_J_per_kg_per_K(100)
        self.assertAlmostEqual(4215.673616815784, result, places=3)

    def test_valid_input_minimum_range(self):
        result = heat_capacity_water_J_per_kg_per_K(0.01)
        self.assertAlmostEqual(4219.911516371655, result, places=3)

    def test_valid_input_maximum_range(self):
        result = heat_capacity_water_J_per_kg_per_K(370)
        self.assertAlmostEqual(45155.17556557058, result, places=3)

    def test_valid_input_midpoint_range(self):
        result = heat_capacity_water_J_per_kg_per_K(185)
        self.assertAlmostEqual(4425.481049192385, result, places=3)

    def test_valid_input_exact_match(self):
        result = heat_capacity_water_J_per_kg_per_K(25)
        self.assertAlmostEqual(4181.599569862515, result, places=3)

    def test_invalid_input_less_than_minimum(self):
        with self.assertRaises(ValueError):
            heat_capacity_water_J_per_kg_per_K(-10)

    def test_invalid_input_not_number(self):
        with self.assertRaises(ValueError):
            heat_capacity_water_J_per_kg_per_K('abc')

    def test_invalid_input_negative(self):
        with self.assertRaises(ValueError):
            heat_capacity_water_J_per_kg_per_K(-50)

    def test_invalid_input_greater_than_500(self):
        with self.assertRaises(ValueError):
            heat_capacity_water_J_per_kg_per_K(501)


class TestEntropyWater(unittest.TestCase):
    def test_valid_temperature_within_range(self):
        """Returns the correct entropy value for a valid temperature input within the range of T[0] to T[-1]"""

        temperature = 50.0
        expected_entropy = 0.7038086259330144
        result_entropy = entropy_water_kJ_per_kg_per_K(temperature)
        self.assertAlmostEqual(expected_entropy, result_entropy, places=3)

    def test_minimum_temperature_input(self):
        """Returns the correct entropy value for the minimum temperature input (T[0])"""

        temperature = 0.01
        expected_entropy = -1.4592809254309467e-13
        result_entropy = entropy_water_kJ_per_kg_per_K(temperature)
        self.assertAlmostEqual(expected_entropy, result_entropy, places=3)

    def test_h20_critical_point_temperature_input(self):
        """Returns the correct entropy value for the maximum temperature input (T[-1])"""

        temperature = 373.946
        expected_entropy = 4.406961892363361
        result_entropy = entropy_water_kJ_per_kg_per_K(temperature)
        self.assertAlmostEqual(expected_entropy, result_entropy, places=3)

    def test_temperature_input_25C(self):
        """Returns the correct entropy value for a temperature input that is an element of T"""

        temperature = 25.0
        expected_entropy = 0.36722496627639006
        result_entropy = entropy_water_kJ_per_kg_per_K(temperature)
        self.assertAlmostEqual(expected_entropy, result_entropy, places=3)

    def test_temperature_input_150C(self):
        """
        Returns the correct entropy value for a temperature input that is not an element of T but within the range of
        T[0] to T[-1]
        """

        temperature = 150.0
        expected_entropy = 1.8418018983902633
        result_entropy = entropy_water_kJ_per_kg_per_K(temperature)
        self.assertAlmostEqual(expected_entropy, result_entropy, places=3)

    def test_temperature_input_minus10C(self):
        """Raises a ValueError if the temperature input is less than T[0]"""

        temperature = -10.0
        with self.assertRaises(ValueError):
            entropy_water_kJ_per_kg_per_K(temperature)

    def test_temperature_input_greater_than_Tn(self):
        """Raises a ValueError if the temperature input is greater than T[-1]"""

        temperature = 400.0
        with self.assertRaises(ValueError):
            entropy_water_kJ_per_kg_per_K(temperature)


class TestRecoverableHeat(unittest.TestCase):
    def test_valid_input_within_default_range(self):
        """Returns recoverable heat fraction when given valid input values within the default range."""

        twater = 100.0

        result = RecoverableHeat(twater)

        assert result == 0.0038 * twater + 0.085

    def test_valid_input_outside_default_range(self):
        """Returns recoverable heat fraction when given valid input values outside the default range."""

        assert RecoverableHeat(160.0) == 0.66

    def test_lowest_valid_temperature_value(self):
        """Returns recoverable heat fraction when given the lowest valid temperature value."""
        assert RecoverableHeat(90.0) == 0.43

    def test_highest_valid_temperature_value(self):
        """Returns recoverable heat fraction when given the highest valid temperature value."""

        assert RecoverableHeat(150.0) == 0.66

    def test_non_numeric_value_for_twater(self):
        """Raises ValueError when given a non-numeric value for Twater."""

        with self.assertRaises(ValueError):
            RecoverableHeat('abc')


class TestVaporPressureWater(unittest.TestCase):
    def test_below_100_degrees(self):
        result = vapor_pressure_water_kPa(42)
        self.assertAlmostEqual(result, 8.209563332516748, places=3)

    def test_above_100_degrees(self):
        result = vapor_pressure_water_kPa(150)
        self.assertAlmostEqual(result, 476.16453796900316, places=3)

    def test_100_degrees(self):
        result = vapor_pressure_water_kPa(100)
        self.assertAlmostEqual(result, 101.41797792131013, places=3)

    def test_0_degrees(self):
        result = vapor_pressure_water_kPa(0)
        self.assertAlmostEqual(result, 0.6112126774443449, places=3)

    def test_25_degrees(self):
        result = vapor_pressure_water_kPa(25)
        self.assertAlmostEqual(result, 3.1697468549523626, places=3)

    def test_value_error(self):
        with self.assertRaises(ValueError):
            vapor_pressure_water_kPa('abc')

    def test_minimum_temperature(self):
        with self.assertRaises(ValueError):
            vapor_pressure_water_kPa(-273.15)

    def test_maximum_temperature(self):
        with self.assertRaises(ValueError):
            vapor_pressure_water_kPa(float('inf'))

    def test_50_degrees(self):
        result = vapor_pressure_water_kPa(50)
        self.assertAlmostEqual(result, 12.351945857074021, places=3)

    def test_75_degrees(self):
        result = vapor_pressure_water_kPa(75)
        self.assertAlmostEqual(result, 38.59536268655676, places=3)


class TestEnthalpyWater(unittest.TestCase):
    def test_valid_temperature(self):
        temperature = 50.0
        result = enthalpy_water_kJ_per_kg(temperature)
        self.assertAlmostEqual(result, 209.34176132671735, places=3)

    def test_minimum_temperature(self):
        temperature = 0.01
        result = enthalpy_water_kJ_per_kg(temperature)
        self.assertAlmostEqual(result, 0.0006117830490730841, places=5)

    def test_maximum_temperature(self):
        temperature = 373.946
        result = enthalpy_water_kJ_per_kg(temperature)
        self.assertAlmostEqual(result, 2084.256255907945, places=3)

    def test_same_temperature(self):
        temperature = 50.0
        enthalpy1 = enthalpy_water_kJ_per_kg(temperature)
        enthalpy2 = enthalpy_water_kJ_per_kg(temperature)
        assert enthalpy1 == enthalpy2

    def test_middle_temperature(self):
        temperature = 15.0
        result = enthalpy_water_kJ_per_kg(temperature)
        self.assertAlmostEqual(result, 62.98145105731618, places=3)

    def test_non_float_temperature(self):
        temperature = 'abc123'
        with self.assertRaises(TypeError):
            enthalpy_water_kJ_per_kg(temperature)

    def test_below_minimum_temperature(self):
        temperature = -10.0
        with self.assertRaises(ValueError):
            enthalpy_water_kJ_per_kg(temperature)

    def test_above_maximum_temperature(self):
        temperature = 400.0
        with self.assertRaises(ValueError):
            enthalpy_water_kJ_per_kg(temperature)

    def test_known_temperature(self):
        temperature = 100.0
        result = enthalpy_water_kJ_per_kg(temperature)
        self.assertAlmostEqual(result, 419.1661628928869, places=3)

    def test_close_temperature(self):
        temperature = 100.001
        result = enthalpy_water_kJ_per_kg(temperature)
        self.assertAlmostEqual(result, 419.1703812859442, places=3)


if __name__ == '__main__':
    unittest.main()

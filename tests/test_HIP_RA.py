import os
import re
import unittest
from pathlib import Path

from geophires_x.Parameter import OutputParameter
from hip_ra import HipRaClient
from hip_ra import HipRaInputParameters
from hip_ra import HipRaResult
from hip_ra.HIP_RA import HIP_RA
from tests.base_test_case import BaseTestCase


# noinspection PyTypeChecker
class HIP_RATestCase(BaseTestCase):
    def test_HIP_RA_examples(self):
        example_files = self._list_test_files_dir(test_files_dir='examples')

        client = HipRaClient()

        def get_output_file_for_example(example_file: Path):
            return self._get_test_file_path(Path(example_file).with_suffix('.out'))

        for example_file_path in example_files:
            if example_file_path.startswith('HIPexample') and '.out' not in example_file_path:
                with self.subTest(msg=example_file_path):
                    input_file_path = self._get_test_file_path(Path('examples', example_file_path))
                    result = client.get_hip_ra_result(HipRaInputParameters(input_file_path))

                    assert result is not None
                    expected_result_output_file_path = get_output_file_for_example(input_file_path)

                    expected_result = HipRaResult(expected_result_output_file_path)
                    self.assertDictEqual(result.result, expected_result.result)

                    self.assertFileContentsEqual(expected_result_output_file_path, result.output_file_path)

    def test_result_parsing_1(self):
        result = HipRaResult(self._get_test_file_path('hip-result_example-1.out'))
        self.assertIsNotNone(result.result)
        self.assertDictEqual(
            result.result,
            {
                'Reservoir Temperature': {'value': 250.0, 'unit': 'degC'},
                'Reservoir Volume': {'value': 13.75, 'unit': 'km**3'},
                'Stored Heat': {'value': 7420000000000000.0, 'unit': 'kJ'},
                'Fluid Produced': {'value': 1100000000000.0, 'unit': 'kilogram'},
                'Enthalpy': {'value': 181.43, 'unit': 'kJ/kg'},
                'Wellhead Heat': {'value': 827000000000000.0, 'unit': 'kJ'},
                'Recovery Factor': {'value': 11.15, 'unit': '%'},
                'Available Heat': {'value': 14700000000000.0, 'unit': 'kJ'},
                'Producible Heat': {'value': 5860000000000.0, 'unit': 'kJ'},
                'Producible Electricity': {'value': 185.85, 'unit': 'MW'},
            },
        )

    def test_result_parsing_2(self):
        result = HipRaResult(self._get_test_file_path('hip-result_example-2.out'))
        self.assertIsNotNone(result.result)
        self.assertDictEqual(
            result.result,
            {
                'Reservoir Temperature': {'value': 250.00, 'unit': 'degC'},
                'Reservoir Volume (reservoir)': {'value': 13.75, 'unit': 'km**3'},
                'Reservoir Volume (rock)': {'value': 12.38, 'unit': 'km**3'},
                'Reservoir Volume (fluid)': {'value': 0.69, 'unit': 'km**3'},
                'Stored Heat (reservoir)': {'value': 5.52e15, 'unit': 'kJ'},
                'Stored Heat (rock)': {'value': 5.01e15, 'unit': 'kJ'},
                'Stored Heat (fluid)': {'value': 5.09e14, 'unit': 'kJ'},
                'Mass of Reservoir (total)': {'value': 3.21e13, 'unit': 'kilogram'},
                'Mass of Reservoir (rock)': {'value': 3.16e13, 'unit': 'kilogram'},
                'Mass of Reservoir (fluid)': {'value': 5.49e11, 'unit': 'kilogram'},
                'Enthalpy (reservoir)': {'value': 49.31, 'unit': 'kJ/kg'},
                'Enthalpy (rock)': {'value': -333.72, 'unit': 'kJ/kg'},
                'Enthalpy (fluid)': {'value': 383.04, 'unit': 'kJ/kg'},
                'Wellhead Heat (reservoir)': {'value': 5.52e15, 'unit': 'kJ'},
                'Wellhead Heat (rock)': {'value': 5.01e15, 'unit': 'kJ'},
                'Wellhead Heat (fluid)': {'value': 5.09e14, 'unit': 'kJ'},
                'Recovery Factor (reservoir)': {'value': -49.39, 'unit': '%'},
                'Recovery Factor (rock)': {'value': -55.51, 'unit': '%'},
                'Recovery Factor (fluid)': {'value': 10.91, 'unit': '%'},
                'Available Heat (reservoir)': {'value': -6.81e15, 'unit': 'kJ'},
                'Available Heat (rock)': {'value': -6.95e15, 'unit': 'kJ'},
                'Available Heat (fluid)': {'value': 1.39e14, 'unit': 'kJ'},
                'Producible Heat (reservoir)': {'value': -2.72e15, 'unit': 'kJ'},
                'Producible Heat (rock)': {'value': -2.78e15, 'unit': 'kJ'},
                'Producible Heat (fluid)': {'value': 5.55e13, 'unit': 'kJ'},
                'Producible Heat/Unit Area (reservoir)': {'value': -4.95e13, 'unit': 'KJ/km**2'},
                'Producible Heat/Unit Area (rock)': {'value': -5.05e13, 'unit': 'KJ/km**2'},
                'Producible Heat/Unit Area (fluid)': {'value': 1.01e12, 'unit': 'KJ/km**2'},
                'Producible Electricity (reservoir)': {'value': -86399.37, 'unit': 'MW'},
                'Producible Electricity (rock)': {'value': -88159.67, 'unit': 'MW'},
                'Producible Electricity (fluid)': {'value': 1760.30, 'unit': 'MW'},
                'Producible Electricity/Unit Area (reservoir)': {'value': -1570.90, 'unit': 'MW/km**2'},
                'Producible Electricity/Unit Area (rock)': {'value': -1602.90, 'unit': 'MW/km**2'},
                'Producible Electricity/Unit Area (fluid)': {'value': 32.01, 'unit': 'MW/km**2'},
            },
        )

    def test_calculate_reservoir_volume(self):
        """Calculates the volume of the reservoir"""
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.Calculate()
        assert hip_ra.reservoir_volume.value == hip_ra.reservoir_area.value * hip_ra.reservoir_thickness.value

    def test_standard_outputs(self):
        """Prints the standard outputs to the output file"""
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.PrintOutputs()

        # Assert that the output file is created
        # ruff: noqa: PTH110
        assert os.path.exists('HIP.out')

        # Assert that the output file is not empty
        # ruff: noqa: PTH202
        assert os.path.getsize('HIP.out') > 0

        # Clean up the output file
        # ruff: noqa: PTH107
        os.remove('HIP.out')

    def test_converts_units_back(self):
        """Converts Units back to PreferredUnits, if required"""
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.PrintOutputs()
        # Assert that the units of all parameters in ParameterDict are converted back to PreferredUnits

        for key in hip_ra.ParameterDict:
            param = hip_ra.ParameterDict[key]
            assert param.CurrentUnits == param.PreferredUnits

    def test_updates_output_parameter_units(self):
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.PrintOutputs()
        # Assert that the units of all parameters in OutputParameterDict are updated to the user-specified units
        for key in hip_ra.OutputParameterDict:
            param: OutputParameter = hip_ra.OutputParameterDict[key]
            assert param.CurrentUnits == param.PreferredUnits

    @unittest.skip('FIXME WIP')
    def test_aligns_space_between_value_and_units(self):
        """
        Assert that the space between value and units is aligned to the same column for each line in the output file
        """

        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.PrintOutputs()

        with open('HIP.out') as f:
            content = f.readlines()
            for line in content:
                assert line.count(' ') == 3

    def test_raises_permission_error(self):
        """Raises a PermissionError if there is no permission to write to the output file"""
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        # Create a read-only file
        Path.chmod('HIP.out', 0o444)
        with self.assertRaises(PermissionError):
            hip_ra.PrintOutputs()
        # Restore file permissions
        Path.chmod('HIP.out', 0o644)

    def test_handles_converting_output_units(self):
        """Handles converting output units for all classes of units (TEMPERATURE, DENSITY, etc.)"""
        hip_ra = HIP_RA(enable_geophires_logging_config=False)
        hip_ra.PrintOutputs()
        # Assert that the units of all parameters in OutputParameterDict are converted to the user-specified units
        for key in hip_ra.OutputParameterDict:
            param = hip_ra.OutputParameterDict[key]
            assert param.CurrentUnits == param.PreferredUnits

    def test_handles_rendering_float_parameters_in_scientific_notation(self):
        """
        Assert that the float parameters in scientific notation are rendered correctly in the output file
        """
        client = HipRaClient()
        result: HipRaResult = client.get_hip_ra_result(
            HipRaInputParameters(self._get_test_file_path('examples/HIPexample1.txt'))
        )
        with open(result.output_file_path) as f:
            content = f.read()
            assert len(re.compile(r'[0-9]e\+[0-9]+\s').findall(content)) > 0

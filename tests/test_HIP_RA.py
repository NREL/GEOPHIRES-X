import os
from pathlib import Path

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
                    self.assertFileContentsEqual(get_output_file_for_example(input_file_path), result.output_file_path)

    def test_result_parsing(self):
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

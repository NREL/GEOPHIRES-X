import tempfile
import uuid
from pathlib import Path
from typing import Optional

from geophires_x.OptionList import PlantType
from geophires_x_client import GeophiresXClient
from geophires_x_client import GeophiresXResult
from geophires_x_client import _get_logger
from geophires_x_client.geophires_input_parameters import EndUseOption
from geophires_x_client.geophires_input_parameters import GeophiresInputParameters
from tests.base_test_case import BaseTestCase


# noinspection PyTypeChecker
class GeophiresXTestCase(BaseTestCase):
    def test_geophires_x_end_use_direct_use_heat(self):
        client = GeophiresXClient()
        result = client.get_geophires_result(
            GeophiresInputParameters(
                {
                    'Print Output to Console': 0,
                    'End-Use Option': EndUseOption.DIRECT_USE_HEAT.value,
                    'Reservoir Model': 1,
                    'Time steps per year': 1,
                    'Reservoir Depth': 3,
                    'Gradient 1': 50,
                    'Maximum Temperature': 250,
                }
            )
        )

        assert result is not None
        self.assertIsNotNone(result)
        self.assertEqual(result.result['metadata']['End-Use Option'], 'DIRECT_USE_HEAT')
        self.assertEqual(result.result['RESERVOIR PARAMETERS']['Reservoir Model'], 'Multiple Parallel Fractures Model')
        self.assertEqual(result.result['RESERVOIR PARAMETERS']['Fracture model'], 'Circular fracture with known area')
        self.assertEqual(
            result.result['RESERVOIR SIMULATION RESULTS']['Production Wellbore Heat Transmission Model'], 'Ramey Model'
        )
        self.assertEqual(result.result['ECONOMIC PARAMETERS']['Economic Model'], 'Standard Levelized Cost')

        result_same_input = client.get_geophires_result(
            GeophiresInputParameters(
                {
                    'Print Output to Console': 0,
                    'End-Use Option': EndUseOption.DIRECT_USE_HEAT.value,
                    'Reservoir Model': 1,
                    'Time steps per year': 1,
                    'Reservoir Depth': 3,
                    'Gradient 1': 50,
                    'Maximum Temperature': 250,
                }
            )
        )

        del result.result['metadata']
        del result_same_input.result['metadata']
        self.assertDictEqual(result.result, result_same_input.result)

        # See TODO in geophires_x_client.geophires_input_parameters.GeophiresInputParameters.__hash__ - if/when hashes
        # of equivalent sets of parameters are made equal, the commented assertion below will test that caching is
        # working as expected.
        # assert result == result_same_input

    def test_geophires_x_end_use_electricity(self):
        client = GeophiresXClient()
        result = client.get_geophires_result(
            GeophiresInputParameters(
                {
                    'Print Output to Console': 0,
                    'End-Use Option': EndUseOption.ELECTRICITY.value,
                    'Reservoir Model': 1,
                    'Time steps per year': 1,
                    'Reservoir Depth': 3,
                    'Gradient 1': 50,
                    'Maximum Temperature': 300,
                }
            )
        )

        assert result is not None
        assert result.result['metadata']['End-Use Option'] == 'ELECTRICITY'

    def test_reservoir_model_2(self):
        client = GeophiresXClient()
        result = client.get_geophires_result(
            GeophiresInputParameters(
                {
                    'Print Output to Console': 0,
                    'Time steps per year': 6,
                    'Reservoir Model': 2,
                    'Reservoir Depth': 5,
                    'Gradient 1': 35,
                    'Maximum Temperature': 250,
                    'Number of Production Wells': 2,
                    'Number of Injection Wells': 2,
                    'Production Well Diameter': 5.5,
                    'Injection Well Diameter': 5.5,
                    'Ramey Production Wellbore Model': 1,
                    'Injection Wellbore Temperature Gain': 0,
                    'Production Flow Rate per Well': 30,
                    'Fracture Shape': 4,
                    'Fracture Height': 100,
                    'Fracture Width': 100,
                    'Reservoir Volume Option': 3,
                    'Number of Fractures': 10,
                    'Fracture Separation': 40,
                    'Reservoir Volume': 125000000,
                    'Productivity Index': 10,
                    'Injectivity Index': 10,
                    'Injection Temperature': 50,
                    'Reservoir Heat Capacity': 774,
                    'Reservoir Density': 2600,
                    'Reservoir Thermal Conductivity': 3,
                    'Reservoir Porosity': 0.04,
                    'Water Loss Fraction': 0.02,
                    'Maximum Drawdown': 1,
                    'End-Use Option': 1,
                    'Power Plant Type': 2,
                    'Circulation Pump Efficiency': 0.8,
                    'Utilization Factor': 0.9,
                    'Surface Temperature': 20,
                    'Ambient Temperature': 20,
                    'Plant Lifetime': 35,
                    'Economic Model': 3,
                    'Fraction of Investment in Bonds': 0.75,
                    'Inflated Bond Interest Rate': 0.05,
                    'Inflated Equity Interest Rate': 0.1,
                    'Inflation Rate': 0.02,
                    'Combined Income Tax Rate': 0.3,
                    'Gross Revenue Tax Rate': 0,
                    'Investment Tax Credit Rate': 0.3,
                    'Property Tax Rate': 0,
                    'Inflation Rate During Construction': 0.05,
                    'Well Drilling and Completion Capital Cost Adjustment Factor': 1,
                    'Well Drilling Cost Correlation': 1,
                    'Reservoir Stimulation Capital Cost Adjustment Factor': 1,
                    'Surface Plant Capital Cost Adjustment Factor': 1,
                    'Field Gathering System Capital Cost Adjustment Factor': 1,
                    'Exploration Capital Cost Adjustment Factor': 1,
                    'Wellfield O&M Cost Adjustment Factor': 1,
                    'Surface Plant O&M Cost Adjustment Factor': 1,
                    'Water Cost Adjustment Factor': 1,
                }
            )
        )

        assert result is not None

    def test_geophires_examples(self):
        log = _get_logger()
        client = GeophiresXClient()

        def get_output_file_for_example(example_file: str):
            return self._get_test_file_path(Path('examples', f'{example_file.split(".txt")[0]}.out'))

        example_files = list(
            filter(
                lambda example_file_path: example_file_path.startswith(
                    ('example', 'Beckers_et_al', 'SUTRA', 'Wanju', 'Fervo')
                )
                and '.out' not in example_file_path,
                self._list_test_files_dir(test_files_dir='examples'),
            )
        )

        assert len(example_files) > 0  # test integrity check - no files means something is misconfigured
        for example_file_path in example_files:
            with self.subTest(msg=example_file_path):
                print(f'Running example test {example_file_path}')
                input_params = GeophiresInputParameters(
                    from_file_path=self._get_test_file_path(Path('examples', example_file_path))
                )
                geophires_result: GeophiresXResult = client.get_geophires_result(input_params)
                del geophires_result.result['metadata']

                expected_result: GeophiresXResult = GeophiresXResult(get_output_file_for_example(example_file_path))
                del expected_result.result['metadata']

                try:
                    self.assertDictEqual(
                        expected_result.result, geophires_result.result, msg=f'Example test: {example_file_path}'
                    )
                except AssertionError as ae:
                    # Float deviation is observed across processor architecture in some test cases - see example
                    # https://github.com/softwareengineerprogrammer/python-geophires-x-nrel/actions/runs/6475850654/job/17588523571
                    # Adding additional test cases that require this fallback should be avoided if possible.
                    cases_to_allow_almost_equal = [
                        'Beckers_et_al_2023_Tabulated_Database_Coaxial_water_heat.txt',
                        'Wanju_Yuan_Closed-Loop_Geothermal_Energy_Recovery.txt',
                    ]
                    allow_almost_equal = example_file_path in cases_to_allow_almost_equal
                    if allow_almost_equal:
                        log.warning(
                            f"Results aren't exactly equal in {example_file_path}, falling back to almostEqual..."
                        )
                        self.assertDictAlmostEqual(
                            expected_result.result,
                            geophires_result.result,
                            places=1,
                            msg=f'Example test: {example_file_path}',
                        )
                    else:
                        msg = 'Results are not approximately equal within any percentage <100'
                        percent_diff = self._get_unequal_dicts_approximate_percent_difference(
                            expected_result.result, geophires_result.result
                        )

                        if percent_diff is not None:
                            msg = (
                                f'Results are approximately equal within {percent_diff}%. '
                                f'(Run `regenerate-example-result.sh {example_file_path.split(".")[0]}` '
                                f'from tests/ if this difference is expected due to calculation updates)'
                            )

                        raise AssertionError(msg) from ae

    def _get_unequal_dicts_approximate_percent_difference(self, d1: dict, d2: dict) -> Optional[float]:
        for i in range(99):
            try:
                self.assertDictAlmostEqual(d1, d2, percent=i)
                return i
            except AssertionError:
                pass

        return None

    def test_clgs_depth_greater_than_5km(self):
        """
        TODO update test to check result when https://github.com/NREL/GEOPHIRES-X/issues/125 is addressed
          (currently just verifies that input results in RuntimeError rather than previous behavior of sys.exit())
        """

        input_content = """Is AGS, True
Closed-loop Configuration, 1
End-Use Option, 1
Heat Transfer Fluid, 2
Number of Production Wells, 1
Number of Injection Wells, 0
All-in Vertical Drilling Costs, 1000.0
All-in Nonvertical Drilling Costs, 1000.0
Production Flow Rate per Well, 40
Cylindrical Reservoir Input Depth, 5001.0 meter
Gradient 1, 60.0
Total Nonvertical Length, 9000
Production Well Diameter, 8.5
Injection Temperature, 60.0
Plant Lifetime, 40
Ambient Temperature, 20
Electricity Rate, 0.10
Circulation Pump Efficiency, 0.8
CO2 Turbine Outlet Pressure, 200
Economic Model, 4
Reservoir Stimulation Capital Cost, 0
Exploration Capital Cost, 0
Print Output to Console, 1"""
        input_file = Path(tempfile.gettempdir(), f'{uuid.uuid4()!s}.txt')
        with open(input_file, 'w') as f:
            f.write(input_content)

        with self.assertRaises(RuntimeError):
            client = GeophiresXClient()
            client.get_geophires_result(GeophiresInputParameters(from_file_path=input_file))

    def test_runtime_error_with_error_code(self):
        client = GeophiresXClient()

        with self.assertRaises(RuntimeError) as re:
            # Note that error-code-5500.txt is expected to fail with error code 5500 as of the time of the writing
            # of this test. If this expectation is voided by future code updates (possibly such as addressing
            # https://github.com/NREL/python-geophires-x/issues/13), then error-code-5500.txt should be updated with
            # different input that is still expected to result in error code 5500.
            input_params = GeophiresInputParameters(
                from_file_path=self._get_test_file_path(Path('error-code-5500.txt'))
            )
            client.get_geophires_result(input_params)

        self.assertEqual(
            str(re.exception), 'GEOPHIRES encountered an exception: failed with the following error codes: [5500.]'
        )

    def test_parameter_value_outside_of_allowable_range_error(self):
        client = GeophiresXClient()

        with self.assertRaises(RuntimeError) as re:
            input_params = GeophiresInputParameters(
                {
                    'Print Output to Console': 0,
                    'End-Use Option': EndUseOption.DIRECT_USE_HEAT.value,
                    'Reservoir Model': 1,
                    'Time steps per year': 1,
                    'Reservoir Depth': 3000,
                    'Gradient 1': 50,
                    'Maximum Temperature': 250,
                }
            )

            client.get_geophires_result(input_params)

        self.assertTrue(
            'GEOPHIRES encountered an exception: Error: Parameter given (3000.0) for Reservoir Depth outside of valid range.'
            in str(re.exception)
        )

    def test_RTES_name(self):
        self.assertEqual(PlantType.RTES.value, 'Reservoir Thermal Energy Storage')

    def test_input_unit_conversion(self):
        client = GeophiresXClient()

        result_meters_input = client.get_geophires_result(
            GeophiresInputParameters(
                from_file_path=self._get_test_file_path(
                    Path('geophires_x_tests/cylindrical_reservoir_input_depth_meters.txt')
                )
            )
        )
        del result_meters_input.result['metadata']

        result_kilometers_input = client.get_geophires_result(
            GeophiresInputParameters(
                from_file_path=self._get_test_file_path(
                    Path('geophires_x_tests/cylindrical_reservoir_input_depth_kilometers.txt')
                )
            )
        )
        del result_kilometers_input.result['metadata']

        self.assertDictEqual(result_kilometers_input.result, result_meters_input.result)

    def test_fcr_sensitivity(self):
        def input_for_fcr(fcr: float) -> GeophiresInputParameters:
            return GeophiresInputParameters(
                from_file_path=self._get_test_file_path('examples/example1.txt'), params={'Fixed Charge Rate': fcr}
            )

        def get_fcr_lcoe(fcr: float) -> float:
            return (
                GeophiresXClient()
                .get_geophires_result(input_for_fcr(fcr))
                .result['SUMMARY OF RESULTS']['Electricity breakeven price']['value']
            )

        self.assertAlmostEqual(9.61, get_fcr_lcoe(0.05), places=1)
        self.assertAlmostEqual(3.33, get_fcr_lcoe(0.0001), places=1)
        self.assertAlmostEqual(104.27, get_fcr_lcoe(0.8), places=1)

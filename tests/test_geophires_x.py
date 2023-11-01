from pathlib import Path

from geophires_x.OptionList import EndUseOptions

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
        assert result.result['metadata']['End-Use Option'] == 'DIRECT_USE_HEAT'

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

        assert result == result_same_input

        # TODO assert that result was retrieved from cache instead of recomputed (somehow)

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
        example_files = self._list_test_files_dir(test_files_dir='examples')

        def get_output_file_for_example(example_file: str):
            return self._get_test_file_path(Path('examples', f'{example_file.split(".txt")[0]}.out'))

        for example_file_path in example_files:
            if (example_file_path.startswith(('example', 'Beckers_et_al'))) and '.out' not in example_file_path:
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
                            geophires_result.result, expected_result.result, msg=f'Example test: {example_file_path}'
                        )
                    except AssertionError as ae:
                        # Float deviation is observed across processor architecture in some test cases - see example
                        # https://github.com/softwareengineerprogrammer/python-geophires-x-nrel/actions/runs/6475850654/job/17588523571
                        # Adding additional test cases that require this fallback should be avoided if possible.
                        cases_to_allow_almost_equal = [
                            'Beckers_et_al_2023_Tabulated_Database_Coaxial_water_heat.txt',
                        ]
                        if example_file_path in cases_to_allow_almost_equal:
                            log.warning(
                                f"Results aren't exactly equal in {example_file_path}, falling back to almostEqual"
                            )
                            self.assertDictAlmostEqual(
                                geophires_result.result,
                                expected_result.result,
                                places=2,
                                msg=f'Example test: {example_file_path}',
                            )
                        else:
                            raise ae

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

    def test_RTES_name(self):
        self.assertEqual(EndUseOptions.RTES.value, 'Reservoir Thermal Energy Storage')

import os.path
import unittest
from pathlib import Path

from geophires_x_client import GeophiresXClient
from geophires_x_client import GeophiresXResult
from geophires_x_client import _get_logger
from geophires_x_client.geophires_input_parameters import EndUseOption
from geophires_x_client.geophires_input_parameters import GeophiresInputParameters


# noinspection PyTypeChecker
class GeophiresXTestCase(unittest.TestCase):
    maxDiff = None

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

    def test_geophires_x_result_1(self):
        test_result_path = self._get_test_file_path('geophires-result_example-1.out')

        result = GeophiresXResult(test_result_path)

        assert result is not None

        expected_price = 7.06

        assert result.direct_use_heat_breakeven_price_USD_per_MMBTU == expected_price
        assert result.result['SUMMARY OF RESULTS']['Direct-Use heat breakeven price']['value'] == expected_price
        assert result.result['SUMMARY OF RESULTS']['Direct-Use heat breakeven price']['unit'] == 'USD/MMBTU'

    def test_geophires_x_result_2(self):
        test_result_path = self._get_test_file_path('geophires-result_example-2.out')
        result = GeophiresXResult(test_result_path)

        assert result is not None
        assert result.direct_use_heat_breakeven_price_USD_per_MMBTU is None
        assert result.result['SUMMARY OF RESULTS']['Average Net Electricity Production']['value'] == 5.39

    def test_geophires_x_result_4(self):
        test_result_path = self._get_test_file_path('geophires-result_example-4.out')
        result = GeophiresXResult(test_result_path)

        assert result is not None
        assert result.result['SUMMARY OF RESULTS']['Annual District Heating Demand']['value'] == 242.90
        assert result.result['SUMMARY OF RESULTS']['Annual District Heating Demand']['unit'] == 'GWh/year'

        assert result.result['OPERATING AND MAINTENANCE COSTS (M$/yr)']['Annual District Heating O&M Cost']['value'] == 0.39
        assert result.result['OPERATING AND MAINTENANCE COSTS (M$/yr)']['Annual District Heating O&M Cost']['unit'] == 'MUSD/yr'

        assert result.result['OPERATING AND MAINTENANCE COSTS (M$/yr)']['Average Annual Peaking Fuel Cost']['value'] == 3.01
        assert result.result['OPERATING AND MAINTENANCE COSTS (M$/yr)']['Average Annual Peaking Fuel Cost']['unit'] == 'MUSD/yr'

    def test_geophires_x_result_generation_profiles(self):
        test_result_path = self._get_test_file_path('geophires-result_example-3.out')
        result = GeophiresXResult(test_result_path)

        assert result.power_generation_profile is not None
        assert len(result.power_generation_profile) == 36
        assert result.power_generation_profile[0] == [
            'YEAR',
            'THERMAL DRAWDOWN',
            'GEOFLUID TEMPERATURE (deg C)',
            'PUMP POWER (MW)',
            'NET POWER (MW)',
            'NET HEAT (MW)',
            'FIRST LAW EFFICIENCY (%)',
        ]
        assert result.power_generation_profile[1] == [0, 1.0, 225.24, 0.1791, 20.597, 11.6711, 16.5771]
        assert result.power_generation_profile[19] == [18, 0.9877, 222.47, 0.1791, 20.0002, 11.3001, 16.3717]
        assert result.power_generation_profile[35] == [34, 0.9248, 208.31, 0.1791, 17.1102, 9.2569, 15.3214]

        assert result.heat_electricity_extraction_generation_profile is not None
        assert len(result.heat_electricity_extraction_generation_profile) == 36
        assert result.heat_electricity_extraction_generation_profile[0] == [
            'YEAR',
            'HEAT PROVIDED (GWh/year)',
            'ELECTRICITY PROVIDED (GWh/year)',
            'HEAT EXTRACTED (GWh/year)',
            'RESERVOIR HEAT CONTENT (10^15 J)',
            'PERCENTAGE OF TOTAL HEAT MINED (%)',
        ]
        assert result.heat_electricity_extraction_generation_profile[1] == [1, 93.2, 164.4, 1090.2, 80.03, 4.67]
        assert result.heat_electricity_extraction_generation_profile[-1] == [35, 72.5, 134.2, 958.47, -48.48, 157.75]

    def test_geophires_examples(self):
        client = GeophiresXClient()
        example_files = self._list_test_files_dir(test_files_dir='examples')
        _get_logger()

        def get_output_file_for_example(example_file: str):
            return self._get_test_file_path(Path('examples', f'{example_file.split(".txt")[0]}V3_output.txt'))

        for example_file_path in example_files:
            if (
                (example_file_path.startswith(('example', 'Beckers_et_al')))
                # FIXME temporarily disabled unit tests (debugging GitHub Actions WIP)
                and not example_file_path.startswith(
                    ('Beckers_et_al_2023_Tabulated_Database_Uloop_sCO2_heat', 'Beckers_et_al_2023_Tabulated_Database_Coaxial_water_heat')
                )
                and '_output' not in example_file_path
            ):
                with self.subTest(msg=example_file_path):
                    print(f'Running example test {example_file_path}')
                    input_params = GeophiresInputParameters(from_file_path=self._get_test_file_path(Path('examples', example_file_path)))
                    geophires_result: GeophiresXResult = client.get_geophires_result(input_params)
                    del geophires_result.result['metadata']

                    expected_result: GeophiresXResult = GeophiresXResult(get_output_file_for_example(example_file_path))
                    del expected_result.result['metadata']

                    self.assertDictEqual(geophires_result.result, expected_result.result)

    def test_input_hashing(self):
        input1 = GeophiresInputParameters(
            {'End-Use Option': EndUseOption.DIRECT_USE_HEAT.value, 'Gradient 1': 50, 'Maximum Temperature': 250}
        )

        input2 = GeophiresInputParameters(
            {'Maximum Temperature': 250, 'End-Use Option': EndUseOption.DIRECT_USE_HEAT.value, 'Gradient 1': 50}
        )

        assert hash(input1) == hash(input2)

        input3 = GeophiresInputParameters(
            {'Maximum Temperature': 420, 'End-Use Option': EndUseOption.DIRECT_USE_HEAT.value, 'Gradient 1': 69}
        )

        assert hash(input1) != hash(input3)

    def _get_test_file_path(self, test_file_name):
        return os.path.join(os.path.abspath(os.path.dirname(__file__)), test_file_name)

    def _get_test_file_content(self, test_file_name):
        with open(self._get_test_file_path(test_file_name)) as f:
            return f.readlines()

    def _list_test_files_dir(self, test_files_dir: str):
        return os.listdir(self._get_test_file_path(test_files_dir))

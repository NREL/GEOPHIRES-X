import tempfile
import uuid
from pathlib import Path

from geophires_x_client import GeophiresXClient
from geophires_x_client import GeophiresXResult
from geophires_x_client.geophires_input_parameters import EndUseOption
from geophires_x_client.geophires_input_parameters import GeophiresInputParameters
from tests.base_test_case import BaseTestCase


# noinspection PyTypeChecker
class GeophiresXClientTestCase(BaseTestCase):
    """
    Note that these are tests of the geophires_x_client package only and not of the core geophires_x package.
    If a test calls geophires_x_client.GeophiresXClient.get_geophires_result then it belongs in
    test_geophires_x.GeophiresXTestCase.
    """

    def test_geophires_x_result_1(self):
        test_result_path = self._get_test_file_path('geophires-result_example-1.out')

        result = GeophiresXResult(test_result_path)

        assert result is not None

        expected_price = 7.06

        assert result.direct_use_heat_breakeven_price_USD_per_MMBTU == expected_price
        assert result.result['SUMMARY OF RESULTS']['Direct-Use heat breakeven price']['value'] == expected_price
        assert result.result['SUMMARY OF RESULTS']['Direct-Use heat breakeven price']['unit'] == 'USD/MMBTU'
        assert result.result['SUMMARY OF RESULTS']['End-Use Option']['value'] == 'Direct-Use Heat'

    def test_geophires_x_result_2(self):
        test_result_path = self._get_test_file_path('geophires-result_example-2.out')
        result = GeophiresXResult(test_result_path)

        assert result is not None
        assert result.direct_use_heat_breakeven_price_USD_per_MMBTU is None
        assert result.result['SUMMARY OF RESULTS']['Average Net Electricity Production']['value'] == 5.39
        assert result.result['ENGINEERING PARAMETERS']['Power plant type']['value'] == 'Supercritical ORC'
        assert result.result['SUMMARY OF RESULTS']['End-Use Option']['value'] == 'Electricity'

    def test_geophires_x_result_3(self):
        test_result_path = self._get_test_file_path('geophires-result_example-3.out')
        result = GeophiresXResult(test_result_path)
        assert (
            result.result['SUMMARY OF RESULTS']['End-Use Option']['value']
            == 'Cogeneration Topping Cycle, Heat sales considered as extra income'
        )

    def test_geophires_x_result_4(self):
        test_result_path = self._get_test_file_path('geophires-result_example-4.out')
        result = GeophiresXResult(test_result_path)

        assert result is not None
        assert result.result['SUMMARY OF RESULTS']['Annual District Heating Demand']['value'] == 242.90
        assert result.result['SUMMARY OF RESULTS']['Annual District Heating Demand']['unit'] == 'GWh/year'

        assert (
            result.result['OPERATING AND MAINTENANCE COSTS (M$/yr)']['Annual District Heating O&M Cost']['value']
            == 0.39
        )
        assert (
            result.result['OPERATING AND MAINTENANCE COSTS (M$/yr)']['Annual District Heating O&M Cost']['unit']
            == 'MUSD/yr'
        )

        assert (
            result.result['OPERATING AND MAINTENANCE COSTS (M$/yr)']['Average Annual Peaking Fuel Cost']['value']
            == 3.01
        )
        assert (
            result.result['OPERATING AND MAINTENANCE COSTS (M$/yr)']['Average Annual Peaking Fuel Cost']['unit']
            == 'MUSD/yr'
        )

    def test_example_multiple_gradients_result(self):
        test_result_path = self._get_test_file_path('examples/example_multiple_gradients.out')
        result = GeophiresXResult(test_result_path)

        categories = ['SUMMARY OF RESULTS', 'RESOURCE CHARACTERISTICS']
        for category in categories:
            assert result.result[category]['Segment 1   Geothermal gradient']['value'] == 0.0500
            assert result.result[category]['Segment 1   Geothermal gradient']['unit'] == 'degC/m'
            assert result.result[category]['Segment 1   Thickness']['value'] == 1000
            assert result.result[category]['Segment 1   Thickness']['unit'] == 'meter'

            assert result.result[category]['Segment 2   Geothermal gradient']['value'] == 0.0400
            assert result.result[category]['Segment 2   Geothermal gradient']['unit'] == 'degC/m'
            assert result.result[category]['Segment 2   Thickness']['value'] == 1000
            assert result.result[category]['Segment 2   Thickness']['unit'] == 'meter'

            assert result.result[category]['Segment 3   Geothermal gradient']['value'] == 0.0300
            assert result.result[category]['Segment 3   Geothermal gradient']['unit'] == 'degC/m'
            assert result.result[category]['Segment 3   Thickness']['value'] == 1000
            assert result.result[category]['Segment 3   Thickness']['unit'] == 'meter'

            assert result.result[category]['Segment 4   Geothermal gradient']['value'] == 0.0500
            assert result.result[category]['Segment 4   Geothermal gradient']['unit'] == 'degC/m'

    def test_example_absorption_chiller_result(self):
        test_result_path = self._get_test_file_path('examples/example11_AC.out')
        result = GeophiresXResult(test_result_path).result

        assert result['CAPITAL COSTS (M$)']['of which Absorption Chiller Cost']['value'] == 3.74
        assert result['CAPITAL COSTS (M$)']['of which Absorption Chiller Cost']['unit'] == 'MUSD'

    def test_geophires_x_result_generation_profiles(self):
        test_result_path = self._get_test_file_path('geophires-result_example-3.out')
        result = GeophiresXResult(test_result_path)

        assert result.power_generation_profile is not None
        assert len(result.power_generation_profile) == 36
        self.assertListEqual(
            result.power_generation_profile[0],
            [
                'YEAR',
                'THERMAL DRAWDOWN',
                'GEOFLUID TEMPERATURE (deg C)',
                'PUMP POWER (MW)',
                'NET POWER (MW)',
                'NET HEAT (MW)',
                'FIRST LAW EFFICIENCY (%)',
            ],
        )
        self.assertListEqual(result.power_generation_profile[1], [0, 1.0, 225.24, 0.1791, 20.597, 11.6711, 16.5771])
        self.assertListEqual(
            result.power_generation_profile[19], [18, 0.9877, 222.47, 0.1791, 20.0002, 11.3001, 16.3717]
        )
        self.assertListEqual(
            result.power_generation_profile[35], [34, 0.9248, 208.31, 0.1791, 17.1102, 9.2569, 15.3214]
        )

        assert result.heat_electricity_extraction_generation_profile is not None
        assert len(result.heat_electricity_extraction_generation_profile) == 36
        self.assertListEqual(
            result.heat_electricity_extraction_generation_profile[0],
            [
                'YEAR',
                'HEAT PROVIDED (GWh/year)',
                'ELECTRICITY PROVIDED (GWh/year)',
                'HEAT EXTRACTED (GWh/year)',
                'RESERVOIR HEAT CONTENT (10^15 J)',
                'PERCENTAGE OF TOTAL HEAT MINED (%)',
            ],
        )
        self.assertListEqual(
            result.heat_electricity_extraction_generation_profile[1], [1, 93.2, 164.4, 1090.2, 80.03, 4.67]
        )
        self.assertListEqual(
            result.heat_electricity_extraction_generation_profile[-1], [35, 72.5, 134.2, 958.47, -48.48, 157.75]
        )

    def test_ags_clgs_result_generation_profiles(self):
        test_result_path = self._get_test_file_path('geophires-result_example-5.out')
        result = GeophiresXResult(test_result_path)

        assert result.power_generation_profile is not None
        assert len(result.power_generation_profile) == 41
        self.assertListEqual(
            result.power_generation_profile[0],
            [
                'YEAR',
                'THERMAL DRAWDOWN',
                'GEOFLUID TEMPERATURE (degC)',
                'PUMP POWER (MW)',
                'NET POWER (MW)',
                'FIRST LAW EFFICIENCY (%)',
            ],
        )
        self.assertListEqual(result.power_generation_profile[1], [1, 1.0000, 108.39, 0.0000, 0.2930, 9.5729])
        self.assertListEqual(result.power_generation_profile[-1], [40, 0.8649, 96.86, 0.0000, 0.2070, 6.7646])

        assert result.heat_electricity_extraction_generation_profile is not None
        assert len(result.heat_electricity_extraction_generation_profile) == 41
        self.assertListEqual(
            result.heat_electricity_extraction_generation_profile[0],
            [
                'YEAR',
                'ELECTRICITY PROVIDED (GWh/year)',
                'HEAT EXTRACTED (GWh/year)',
                'RESERVOIR HEAT CONTENT (10^15 J)',
                'PERCENTAGE OF TOTAL HEAT MINED (%)',
            ],
        )
        self.assertListEqual(result.heat_electricity_extraction_generation_profile[1], [1, 2.6, 30.1, 3.68, 2.86])
        self.assertListEqual(result.heat_electricity_extraction_generation_profile[-1], [40, 1.8, 22.7, 0.32, 91.57])

    def test_extended_economic_profile(self):
        test_result_path = self._get_test_file_path('examples/example1_addons.out')
        result = GeophiresXResult(test_result_path)
        eep = result.result['EXTENDED ECONOMIC PROFILE']

        self.assertListEqual(
            [
                [
                    'Year Since Start',
                    'Electricity Price (cents/kWh)',
                    'Electricity Revenue (MUSD/yr)',
                    'Heat Price (cents/kWh)',
                    'Heat Revenue (MUSD/yr)',
                    'Add-on Revenue (MUSD/yr)',
                    'Annual AddOn Cash Flow (MUSD/yr)',
                    'Cumm. AddOn Cash Flow (MUSD)',
                    'Annual Project Cash Flow (MUSD/yr)',
                    'Cumm. Project Cash Flow (MUSD)',
                ],
                [1, 0.09, 0.0023, 0.012, 0.0, 1.14, -70.0, -70.0, -101.07, -101.07],
                [2, 0.09, 0.0023, 0.012, 0.0, 1.14, 1.14, -68.86, 5.71, -95.36],
                [3, 0.09, 0.0023, 0.012, 0.0, 1.14, 1.14, -67.72, 5.75, -89.61],
                [4, 0.09, 0.0023, 0.012, 0.0, 1.14, 1.14, -66.59, 5.77, -83.84],
                [5, 0.09, 0.0023, 0.012, 0.0, 1.14, 1.14, -65.45, 5.77, -78.07],
                [6, 0.09, 0.0023, 0.012, 0.0, 1.14, 1.14, -64.31, 5.78, -72.29],
                [7, 0.102, 0.0026, 0.012, 0.0, 1.14, 1.14, -63.17, 5.78, -66.51],
                [8, 0.114, 0.003, 0.012, 0.0, 1.14, 1.14, -62.03, 6.3, -60.21],
                [9, 0.126, 0.0033, 0.022, 0.0, 1.14, 1.14, -60.89, 6.81, -53.4],
                [10, 0.138, 0.0036, 0.032, 0.0, 1.14, 1.14, -59.75, 7.33, -46.07],
                [11, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -58.61, 7.84, -38.23],
                [12, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -57.47, 8.36, -29.87],
                [13, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -56.33, 8.36, -21.51],
                [14, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -55.19, 8.36, -13.14],
                [15, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -54.05, 8.37, -4.78],
                [16, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -52.91, 8.37, 3.59],
                [17, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -51.77, 8.37, 11.96],
                [18, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -50.63, 8.37, 20.33],
                [19, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -49.49, 8.37, 28.71],
                [20, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -48.35, 8.37, 37.08],
                [21, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -47.21, 8.38, 45.46],
                [22, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -46.07, 8.38, 53.83],
                [23, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -44.93, 8.38, 62.21],
                [24, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -43.8, 8.38, 70.59],
                [25, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -42.66, 8.38, 78.97],
                [26, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -41.52, 8.38, 87.36],
                [27, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -40.38, 8.38, 95.74],
                [28, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -39.24, 8.38, 104.12],
                [29, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -38.1, 8.39, 112.51],
                [30, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -36.96, 8.39, 120.9],
            ],
            eep,
        )

    def test_ccus_profile(self):
        test_result_path = self._get_test_file_path('examples/example1_addons.out')
        result = GeophiresXResult(test_result_path)

        self.assertListEqual(
            [
                [
                    'Year Since Start',
                    'Carbon Avoided (pound)',
                    'CCUS Price (USD/lb)',
                    'CCUS Revenue (MUSD/yr)',
                    'CCUS Annual Cash Flow (MUSD/yr)',
                    'CCUS Cumm. Cash Flow (MUSD)',
                    'Project Annual Cash Flow (MUSD/yr)',
                    'Project Cumm. Cash Flow (MUSD)',
                ],
                [1, None, None, None, None, None, -31.07, -31.07],
                [2, 34242902.215, 0.015, 0.51, 0.51, 0.51, 5.09, -25.98],
                [3, 34603285.382, 0.015, 0.52, 0.52, 1.03, 5.13, -20.85],
                [4, 34725268.317, 0.015, 0.52, 0.52, 1.55, 5.15, -15.7],
                [5, 34797511.21, 0.015, 0.52, 0.52, 2.08, 5.16, -10.55],
                [6, 34848151.206, 0.015, 0.52, 0.52, 2.6, 5.16, -5.38],
                [7, 34886783.934, 0.015, 0.52, 0.52, 3.12, 5.17, -0.21],
                [8, 34917819.177, 0.025, 0.87, 0.87, 3.99, 6.03, 5.82],
                [9, 34943638.596, 0.035, 1.22, 1.22, 5.22, 6.9, 12.71],
                [10, 34965669.213, 0.045, 1.57, 1.57, 6.79, 7.76, 20.48],
                [11, 34984830.866, 0.055, 1.92, 1.92, 8.72, 8.63, 29.1],
                [12, 35001749.647, 0.065, 2.28, 2.28, 10.99, 9.49, 38.6],
                [13, 35016870.098, 0.075, 2.63, 2.63, 13.62, 9.85, 48.44],
                [14, 35030518.704, 0.085, 2.98, 2.98, 16.59, 10.2, 58.65],
                [15, 35042941.962, 0.095, 3.33, 3.33, 19.92, 10.55, 69.2],
                [16, 35054330.314, 0.1, 3.51, 3.51, 23.43, 10.73, 79.93],
                [17, 35064833.772, 0.1, 3.51, 3.51, 26.94, 10.74, 90.67],
                [18, 35074572.443, 0.1, 3.51, 3.51, 30.44, 10.74, 101.41],
                [19, 35083643.806, 0.1, 3.51, 3.51, 33.95, 10.74, 112.15],
                [20, 35092127.828, 0.1, 3.51, 3.51, 37.46, 10.74, 122.9],
                [21, 35100090.618, 0.1, 3.51, 3.51, 40.97, 10.75, 133.64],
                [22, 35107587.061, 0.1, 3.51, 3.51, 44.48, 10.75, 144.39],
                [23, 35114662.718, 0.1, 3.51, 3.51, 47.99, 10.75, 155.14],
                [24, 35121355.214, 0.1, 3.51, 3.51, 51.5, 10.75, 165.89],
                [25, 35127695.24, 0.1, 3.51, 3.51, 55.02, 10.75, 176.65],
                [26, 35133707.294, 0.1, 3.51, 3.51, 58.53, 10.76, 187.4],
                [27, 35139410.222, 0.1, 3.51, 3.51, 62.04, 10.76, 198.16],
                [28, 35144817.62, 0.1, 3.51, 3.51, 65.56, 10.76, 208.92],
                [29, 35149938.146, 0.1, 3.51, 3.51, 69.07, 10.76, 219.68],
                [30, 35154775.749, 0.1, 3.52, 3.52, 72.59, 10.76, 230.44],
                [31, 29302677.11, 0.1, 2.93, 2.93, 75.52, 9.11, 239.55],
            ],
            result.result['CCUS PROFILE'],
        )

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

    def test_input_with_non_default_units(self):
        client = GeophiresXClient()
        result_default_units = client.get_geophires_result(
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
        ).result
        del result_default_units['metadata']

        result_non_default_units = client.get_geophires_result(
            GeophiresInputParameters(
                {
                    'Print Output to Console': 0,
                    'End-Use Option': EndUseOption.DIRECT_USE_HEAT.value,
                    'Reservoir Model': 1,
                    'Time steps per year': 1,
                    'Reservoir Depth': '3000 meter',
                    'Gradient 1': 50,
                    'Maximum Temperature': 250,
                }
            )
        ).result
        del result_non_default_units['metadata']

        self.assertDictEqual(result_default_units, result_non_default_units)

    def test_csv(self):
        def assert_csv_equal(case_report_file_path, expected_csv_file_path):
            test_result_path = self._get_test_file_path(case_report_file_path)
            result = GeophiresXResult(test_result_path)

            as_csv = result.as_csv()
            self.assertIsNotNone(as_csv)

            result_file = Path(tempfile.gettempdir(), f'test_csv-result_{uuid.uuid1()!s}.csv')
            with open(result_file, 'w', newline='', encoding='utf-8') as rf:
                rf.write(as_csv)
                self.assertFileContentsEqual(self._get_test_file_path(expected_csv_file_path), result_file)

        for case in [
            ('geophires-result_example-3.out', 'geophires-result_example-3.csv'),
            ('examples/example1_addons.out', 'example1_addons.csv'),
        ]:
            with self.subTest(msg=case[0]):
                assert_csv_equal(case[0], case[1])

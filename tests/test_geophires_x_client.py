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
        """
        TODO make this less tedious to update when expected result values are updated
            (https://github.com/NREL/GEOPHIRES-X/issues/107)
        """

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
                [1, 0.09, 0.0023, 0.012, 0.0, 1.14, -70.0, -70.0, -101.06, -101.06],
                [2, 0.09, 0.0023, 0.012, 0.0, 1.14, 1.14, -68.86, 5.68, -95.38],
                [3, 0.09, 0.0023, 0.012, 0.0, 1.14, 1.14, -67.72, 5.72, -89.65],
                [4, 0.09, 0.0023, 0.012, 0.0, 1.14, 1.14, -66.59, 5.74, -83.91],
                [5, 0.09, 0.0023, 0.012, 0.0, 1.14, 1.14, -65.45, 5.75, -78.17],
                [6, 0.09, 0.0023, 0.012, 0.0, 1.14, 1.14, -64.31, 5.75, -72.42],
                [7, 0.102, 0.0026, 0.012, 0.0, 1.14, 1.14, -63.17, 5.76, -66.66],
                [8, 0.114, 0.003, 0.012, 0.0, 1.14, 1.14, -62.03, 6.27, -60.39],
                [9, 0.126, 0.0033, 0.022, 0.0, 1.14, 1.14, -60.89, 6.78, -53.61],
                [10, 0.138, 0.0036, 0.032, 0.0, 1.14, 1.14, -59.75, 7.29, -46.32],
                [11, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -58.61, 7.8, -38.52],
                [12, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -57.47, 8.31, -30.21],
                [13, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -56.33, 8.32, -21.89],
                [14, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -55.19, 8.32, -13.57],
                [15, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -54.05, 8.32, -5.25],
                [16, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -52.91, 8.32, 3.08],
                [17, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -51.77, 8.33, 11.4],
                [18, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -50.63, 8.33, 19.73],
                [19, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -49.49, 8.33, 28.06],
                [20, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -48.35, 8.33, 36.39],
                [21, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -47.21, 8.33, 44.72],
                [22, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -46.07, 8.33, 53.06],
                [23, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -44.93, 8.34, 61.39],
                [24, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -43.8, 8.34, 69.73],
                [25, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -42.66, 8.34, 78.07],
                [26, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -41.52, 8.34, 86.41],
                [27, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -40.38, 8.34, 94.75],
                [28, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -39.24, 8.34, 103.09],
                [29, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -38.1, 8.34, 111.43],
                [30, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -36.96, 8.34, 119.77],
            ],
            eep,
        )

    def test_ccus_profile(self):
        """
        TODO make this less tedious to update when expected result values are updated
            (https://github.com/NREL/GEOPHIRES-X/issues/107)
        """

        test_result_path = self._get_test_file_path('examples/example1_addons.out')
        result = GeophiresXResult(test_result_path)
        ccus_profile = result.result['CCUS PROFILE']

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
                [1, None, None, None, None, None, -31.06, -31.06],
                [2, 33969152.766, 0.015, 0.51, 0.51, 0.51, 5.05, -26.01],
                [3, 34341162.882, 0.015, 0.52, 0.52, 1.02, 5.1, -20.91],
                [4, 34467117.964, 0.015, 0.52, 0.52, 1.54, 5.12, -15.79],
                [5, 34541720.779, 0.015, 0.52, 0.52, 2.06, 5.13, -10.66],
                [6, 34594018.221, 0.015, 0.52, 0.52, 2.58, 5.13, -5.53],
                [7, 34633917.159, 0.015, 0.52, 0.52, 3.1, 5.14, -0.39],
                [8, 34665970.699, 0.025, 0.87, 0.87, 3.96, 6.0, 5.6],
                [9, 34692638.021, 0.035, 1.21, 1.21, 5.18, 6.85, 12.46],
                [10, 34715392.651, 0.045, 1.56, 1.56, 6.74, 7.71, 20.17],
                [11, 34735184.429, 0.055, 1.91, 1.91, 8.65, 8.57, 28.75],
                [12, 34752659.886, 0.065, 2.26, 2.26, 10.91, 9.43, 38.18],
                [13, 34768278.088, 0.075, 2.61, 2.61, 13.52, 9.78, 47.96],
                [14, 34782376.191, 0.085, 2.96, 2.96, 16.47, 10.14, 58.1],
                [15, 34795208.759, 0.095, 3.31, 3.31, 19.78, 10.49, 68.59],
                [16, 34806972.481, 0.1, 3.48, 3.48, 23.26, 10.66, 79.25],
                [17, 34817822.318, 0.1, 3.48, 3.48, 26.74, 10.67, 89.92],
                [18, 34827882.405, 0.1, 3.48, 3.48, 30.23, 10.67, 100.59],
                [19, 34837253.604, 0.1, 3.48, 3.48, 33.71, 10.67, 111.26],
                [20, 34846018.858, 0.1, 3.48, 3.48, 37.19, 10.68, 121.94],
                [21, 34854247.043, 0.1, 3.49, 3.49, 40.68, 10.68, 132.62],
                [22, 34861995.782, 0.1, 3.49, 3.49, 44.17, 10.68, 143.3],
                [23, 34869313.518, 0.1, 3.49, 3.49, 47.65, 10.68, 153.98],
                [24, 34876241.046, 0.1, 3.49, 3.49, 51.14, 10.68, 164.66],
                [25, 34882812.647, 0.1, 3.49, 3.49, 54.63, 10.69, 175.35],
                [26, 34889056.938, 0.1, 3.49, 3.49, 58.12, 10.69, 186.04],
                [27, 34894997.5, 0.1, 3.49, 3.49, 61.61, 10.69, 196.73],
                [28, 34900653.351, 0.1, 3.49, 3.49, 65.1, 10.69, 207.42],
                [29, 34906039.293, 0.1, 3.49, 3.49, 68.59, 10.69, 218.11],
                [30, 34911166.179, 0.1, 3.49, 3.49, 72.08, 10.69, 228.81],
                [31, 29099912.619, 0.1, 2.91, 2.91, 74.99, 9.05, 237.86],
            ],
            ccus_profile,
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
        """
        TODO make this less tedious to update when expected result values are updated
            (https://github.com/NREL/GEOPHIRES-X/issues/107)
        """

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

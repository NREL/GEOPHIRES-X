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
        TODO make this less tedious to update when expected result values change
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
                [1, 0.09, 0.0023, 0.012, 0.0, 1.14, -70.0, -70.0, -102.63, -102.63],
                [2, 0.09, 0.0023, 0.012, 0.0, 1.14, 1.14, -68.86, 2.72, -99.91],
                [3, 0.09, 0.0023, 0.012, 0.0, 1.14, 1.14, -67.72, 2.76, -97.15],
                [4, 0.09, 0.0023, 0.012, 0.0, 1.14, 1.14, -66.59, 2.77, -94.38],
                [5, 0.09, 0.0023, 0.012, 0.0, 1.14, 1.14, -65.45, 2.78, -91.6],
                [6, 0.09, 0.0023, 0.012, 0.0, 1.14, 1.14, -64.31, 2.79, -88.81],
                [7, 0.102, 0.0026, 0.012, 0.0, 1.14, 1.14, -63.17, 2.79, -86.02],
                [8, 0.114, 0.003, 0.012, 0.0, 1.14, 1.14, -62.03, 2.91, -83.11],
                [9, 0.126, 0.0033, 0.022, 0.0, 1.14, 1.14, -60.89, 3.03, -80.08],
                [10, 0.138, 0.0036, 0.032, 0.0, 1.14, 1.14, -59.75, 3.15, -76.94],
                [11, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -58.61, 3.26, -73.68],
                [12, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -57.47, 3.38, -70.29],
                [13, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -56.33, 3.39, -66.91],
                [14, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -55.19, 3.39, -63.52],
                [15, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -54.05, 3.39, -60.13],
                [16, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -52.91, 3.39, -56.74],
                [17, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -51.77, 3.39, -53.34],
                [18, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -50.63, 3.4, -49.95],
                [19, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -49.49, 3.4, -46.55],
                [20, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -48.35, 3.4, -43.15],
                [21, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -47.21, 3.4, -39.75],
                [22, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -46.07, 3.4, -36.35],
                [23, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -44.93, 3.4, -32.95],
                [24, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -43.8, 3.4, -29.54],
                [25, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -42.66, 3.41, -26.14],
                [26, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -41.52, 3.41, -22.73],
                [27, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -40.38, 3.41, -19.32],
                [28, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -39.24, 3.41, -15.91],
                [29, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -38.1, 3.41, -12.5],
                [30, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -36.96, 3.41, -9.09],
            ],
            eep,
        )

    def test_ccus_profile(self):
        """
        TODO make this less tedious to update when expected result values change
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
                [1, None, None, None, None, None, -32.63, -32.63],
                [2, 7101870.358, 0.015, 0.11, 0.11, 0.11, 1.69, -30.95],
                [3, 7470391.043, 0.015, 0.11, 0.11, 0.22, 1.73, -29.21],
                [4, 7595168.229, 0.015, 0.11, 0.11, 0.33, 1.75, -27.46],
                [5, 7669074.1, 0.015, 0.12, 0.12, 0.45, 1.76, -25.71],
                [6, 7720883.286, 0.015, 0.12, 0.12, 0.56, 1.76, -23.94],
                [7, 7760409.892, 0.015, 0.12, 0.12, 0.68, 1.77, -22.17],
                [8, 7792164.418, 0.025, 0.19, 0.19, 0.87, 1.97, -20.21],
                [9, 7818583.043, 0.035, 0.27, 0.27, 1.15, 2.16, -18.04],
                [10, 7841125.517, 0.045, 0.35, 0.35, 1.5, 2.36, -15.69],
                [11, 7860732.801, 0.055, 0.43, 0.43, 1.93, 2.56, -13.13],
                [12, 7878045.387, 0.065, 0.51, 0.51, 2.45, 2.75, -10.37],
                [13, 7893518.049, 0.075, 0.59, 0.59, 3.04, 2.84, -7.54],
                [14, 7907484.797, 0.085, 0.67, 0.67, 3.71, 2.92, -4.62],
                [15, 7920197.818, 0.095, 0.75, 0.75, 4.46, 3.0, -1.61],
                [16, 7931851.962, 0.1, 0.79, 0.79, 5.26, 3.05, 1.43],
                [17, 7942600.746, 0.1, 0.79, 0.79, 6.05, 3.05, 4.48],
                [18, 7952567.147, 0.1, 0.8, 0.8, 6.84, 3.05, 7.53],
                [19, 7961851.088, 0.1, 0.8, 0.8, 7.64, 3.05, 10.58],
                [20, 7970534.743, 0.1, 0.8, 0.8, 8.44, 3.06, 13.64],
                [21, 7978686.355, 0.1, 0.8, 0.8, 9.24, 3.06, 16.7],
                [22, 7986363.027, 0.1, 0.8, 0.8, 10.03, 3.06, 19.76],
                [23, 7993612.777, 0.1, 0.8, 0.8, 10.83, 3.06, 22.82],
                [24, 8000476.061, 0.1, 0.8, 0.8, 11.63, 3.06, 25.89],
                [25, 8006986.902, 0.1, 0.8, 0.8, 12.43, 3.07, 28.95],
                [26, 8013173.735, 0.1, 0.8, 0.8, 13.24, 3.07, 32.02],
                [27, 8019060.033, 0.1, 0.8, 0.8, 14.04, 3.07, 35.09],
                [28, 8024664.782, 0.1, 0.8, 0.8, 14.84, 3.07, 38.16],
                [29, 8030002.83, 0.1, 0.8, 0.8, 15.64, 3.07, 41.24],
                [30, 8035085.158, 0.1, 0.8, 0.8, 16.45, 3.07, 44.31],
                [31, 6703146.945, 0.1, 0.67, 0.67, 17.12, 2.7, 47.01],
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
        TODO make this less tedious to update when expected result values change
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

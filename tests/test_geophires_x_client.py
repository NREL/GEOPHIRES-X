import tempfile
import unittest
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

        assert 'GEOPHIRES Version' in result.result['Simulation Metadata']
        assert '3.' in result.result['Simulation Metadata']['GEOPHIRES Version']['value']

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

    def test_direct_use_heat_property(self):
        test_result_path = self._get_test_file_path('examples/example12_DH.out')
        result = GeophiresXResult(test_result_path)

        with open(test_result_path) as f:
            self.assertIn('Direct-Use heat breakeven price (LCOH)', f.read())

        # Don't care about the value in this test - just that it's being read with the (LCOH)-suffixed name
        self.assertIsNotNone(result.direct_use_heat_breakeven_price_USD_per_MMBTU)

    def test_surface_application_field(self):
        for example_file, surface_application in [
            ('examples/example10_HP.out', 'Heat Pump'),
            ('examples/example11_AC.out', 'Absorption Chiller'),
            ('examples/example12_DH.out', 'District Heating'),
        ]:
            with self.subTest(msg=example_file):
                test_result_path = self._get_test_file_path(example_file)
                result = GeophiresXResult(test_result_path)

                assert result.result['SUMMARY OF RESULTS']['Surface Application']['value'] == surface_application

    def test_example_multiple_gradients_result(self):
        test_result_path = self._get_test_file_path('examples/example_multiple_gradients.out')
        result = GeophiresXResult(test_result_path)

        categories = ['SUMMARY OF RESULTS', 'RESOURCE CHARACTERISTICS']
        for category in categories:
            assert result.result[category]['Segment 1   Geothermal gradient']['value'] == 50
            assert result.result[category]['Segment 1   Geothermal gradient']['unit'] == 'degC/km'
            assert result.result[category]['Segment 1   Thickness']['value'] == 1
            assert result.result[category]['Segment 1   Thickness']['unit'] == 'kilometer'

            assert result.result[category]['Segment 2   Geothermal gradient']['value'] == 40
            assert result.result[category]['Segment 2   Geothermal gradient']['unit'] == 'degC/km'
            assert result.result[category]['Segment 2   Thickness']['value'] == 1
            assert result.result[category]['Segment 2   Thickness']['unit'] == 'kilometer'

            assert result.result[category]['Segment 3   Geothermal gradient']['value'] == 30
            assert result.result[category]['Segment 3   Geothermal gradient']['unit'] == 'degC/km'
            assert result.result[category]['Segment 3   Thickness']['value'] == 1
            assert result.result[category]['Segment 3   Thickness']['unit'] == 'kilometer'

            assert result.result[category]['Segment 4   Geothermal gradient']['value'] == 50
            assert result.result[category]['Segment 4   Geothermal gradient']['unit'] == 'degC/km'

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
                [1, 0.0, 0.0023, 0.0, 0.0, 1.14, -70.0, -70.0, -101.07, -101.07],
                [2, 0.09, 0.0023, 0.012, 0.0, 1.14, 1.14, -68.86, 5.7, -95.37],
                [3, 0.09, 0.0023, 0.012, 0.0, 1.14, 1.14, -67.72, 5.74, -89.63],
                [4, 0.09, 0.0023, 0.012, 0.0, 1.14, 1.14, -66.59, 5.75, -83.88],
                [5, 0.09, 0.0023, 0.012, 0.0, 1.14, 1.14, -65.45, 5.76, -78.12],
                [6, 0.09, 0.0023, 0.012, 0.0, 1.14, 1.14, -64.31, 5.77, -72.35],
                [7, 0.09, 0.0026, 0.012, 0.0, 1.14, 1.14, -63.17, 5.77, -66.58],
                [8, 0.102, 0.003, 0.012, 0.0, 1.14, 1.14, -62.03, 6.28, -60.29],
                [9, 0.114, 0.0033, 0.012, 0.0, 1.14, 1.14, -60.89, 6.8, -53.5],
                [10, 0.126, 0.0036, 0.022, 0.0, 1.14, 1.14, -59.75, 7.31, -46.19],
                [11, 0.138, 0.0039, 0.032, 0.0, 1.14, 1.14, -58.61, 7.82, -38.36],
                [12, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -57.47, 8.34, -30.02],
                [13, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -56.33, 8.34, -21.68],
                [14, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -55.19, 8.34, -13.34],
                [15, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -54.05, 8.35, -4.99],
                [16, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -52.91, 8.35, 3.36],
                [17, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -51.77, 8.35, 11.71],
                [18, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -50.63, 8.35, 20.06],
                [19, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -49.49, 8.35, 28.41],
                [20, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -48.35, 8.36, 36.77],
                [21, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -47.21, 8.36, 45.12],
                [22, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -46.07, 8.36, 53.48],
                [23, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -44.93, 8.36, 61.84],
                [24, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -43.8, 8.36, 70.2],
                [25, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -42.66, 8.36, 78.56],
                [26, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -41.52, 8.36, 86.92],
                [27, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -40.38, 8.36, 95.29],
                [28, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -39.24, 8.36, 103.65],
                [29, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -38.1, 8.37, 112.02],
                [30, 0.15, 0.0039, 0.036, 0.0, 1.14, 1.14, -36.96, 8.37, 120.39],
            ],
            eep,
        )

    def test_revenue_and_cashflow_profile(self):
        example_result_path = self._get_test_file_path('examples/example1_addons.out')
        example_result = GeophiresXResult(example_result_path)
        example_profile = example_result.result['REVENUE & CASHFLOW PROFILE']
        self.assertIsNotNone(example_profile)

        profile_headers = [
            'Year Since Start',
            'Electricity Price (cents/kWh)',
            'Electricity Ann. Rev. (MUSD/yr)',
            'Electricity Cumm. Rev. (MUSD)',
            'Heat Price (cents/kWh)',
            'Heat Ann. Rev. (MUSD/yr)',
            'Heat Cumm. Rev. (MUSD)',
            'Cooling Price (cents/kWh)',
            'Cooling Ann. Rev. (MUSD/yr)',
            'Cooling Cumm. Rev. (MUSD)',
            'Carbon Price (USD/tonne)',
            'Carbon Ann. Rev. (MUSD/yr)',
            'Carbon Cumm. Rev. (MUSD)',
            'Project OPEX (MUSD/yr)',
            'Project Net Rev. (MUSD/yr)',
            'Project Net Cashflow (MUSD)',
        ]

        self.assertListEqual(profile_headers, example_profile[0])

        rcf_path = self._get_test_file_path('result_with_revenue_and_cashflow_profile.out')
        rcf_result = GeophiresXResult(rcf_path)
        rcf_profile = rcf_result.result['REVENUE & CASHFLOW PROFILE']
        self.assertIsNotNone(rcf_profile)

        self.assertListEqual(
            [
                profile_headers,
                [1, 0.09, -32.63, 0.0, 0.01, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -32.63, -32.63],
                [2, 0.09, 1.58, 0.78, 0.01, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 1.58, -31.05],
                [3, 0.09, 1.62, 1.6, 0.01, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 1.62, -29.43],
                [4, 0.09, 1.63, 2.43, 0.01, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 1.63, -27.8],
                [5, 0.09, 1.64, 3.27, 0.01, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 1.64, -26.15],
                [6, 0.09, 1.65, 4.12, 0.01, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 1.65, -24.5],
                [7, 0.1, 1.65, 4.97, 0.01, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 1.65, -22.85],
                [8, 0.11, 1.77, 5.94, 0.01, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 1.77, -21.08],
                [9, 0.13, 1.89, 7.03, 0.02, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 1.89, -19.19],
                [10, 0.14, 2.01, 8.24, 0.03, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 2.01, -17.19],
                [11, 0.15, 2.12, 9.56, 0.04, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 2.12, -15.06],
                [12, 0.15, 2.24, 11.0, 0.04, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 2.24, -12.82],
                [13, 0.15, 2.25, 12.44, 0.04, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 2.25, -10.57],
                [14, 0.15, 2.25, 13.89, 0.04, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 2.25, -8.33],
                [15, 0.15, 2.25, 15.34, 0.04, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 2.25, -6.08],
                [16, 0.15, 2.25, 16.79, 0.04, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 2.25, -3.82],
                [17, 0.15, 2.25, 18.24, 0.04, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 2.25, -1.57],
                [18, 0.15, 2.26, 19.7, 0.04, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 2.26, 0.69],
                [19, 0.15, 2.26, 21.15, 0.04, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 2.26, 2.94],
                [20, 0.15, 2.26, 22.61, 0.04, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 2.26, 5.2],
                [21, 0.15, 2.26, 24.07, 0.04, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 2.26, 7.46],
                [22, 0.15, 2.26, 25.53, 0.04, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 2.26, 9.73],
                [23, 0.15, 2.26, 26.99, 0.04, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 2.26, 11.99],
                [24, 0.15, 2.26, 28.46, 0.04, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 2.26, 14.25],
                [25, 0.15, 2.27, 29.92, 0.04, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 2.27, 16.52],
                [26, 0.15, 2.27, 31.39, 0.04, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 2.27, 18.79],
                [27, 0.15, 2.27, 32.85, 0.04, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 2.27, 21.06],
                [28, 0.15, 2.27, 34.32, 0.04, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 2.27, 23.32],
                [29, 0.15, 2.27, 35.79, 0.04, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 2.27, 25.59],
                [30, 0.15, 2.27, 37.26, 0.04, 0.0, 0.0, 0.03, 0.0, 0.0, 0.0, 0.0, 0.0, -0.8, 2.27, 27.87],
            ],
            rcf_profile,
        )

    def test_ccus_profile(self):
        test_result_path = self._get_test_file_path('result_with_ccus_profile.out')
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

    @unittest.skip(
        'Not currently relevant - '
        'see TODO in geophires_x_client.geophires_input_parameters.GeophiresInputParameters.__hash__'
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

        Current easiest method to update:
         1. set breakpoint on line after `as_csv = result.as_csv()`
         2. debug test, hit break point
         3. copy-paste value of `as_csv` to example1_addons.csv
        """

        def assertFileContentsEqual(expected_file_path, actual_file_path, tol=0.01):
            with open(expected_file_path, encoding='utf-8') as ef:
                expected_lines = ef.readlines()
            with open(actual_file_path, encoding='utf-8') as af:
                actual_lines = af.readlines()

            self.assertEqual(len(expected_lines), len(actual_lines), 'The number of lines in the files do not match.')

            for line_index, (expected_line, actual_line) in enumerate(zip(expected_lines, actual_lines), start=1):
                expected_parts = expected_line.strip().split(',')
                actual_parts = actual_line.strip().split(',')
                self.assertEqual(
                    len(expected_parts),
                    len(actual_parts),
                    f'The number of columns in line {line_index} does not match.',
                )
                for col_index, (expected, actual) in enumerate(zip(expected_parts, actual_parts), start=1):
                    try:
                        expected_float = float(expected)
                        actual_float = float(actual)
                        self.assertTrue(
                            abs(expected_float - actual_float) < tol,
                            f'Float values differ at line {line_index}, column {col_index}: {expected} != {actual}',
                        )
                    except ValueError:
                        self.assertEqual(
                            expected,
                            actual,
                            f'String values differ at line {line_index}, column {col_index}: {expected} != {actual}',
                        )

        def assert_csv_equal(case_report_file_path, expected_csv_file_path):
            test_result_path = self._get_test_file_path(case_report_file_path)
            result = GeophiresXResult(test_result_path)
            as_csv = result.as_csv()
            self.assertIsNotNone(as_csv)

            result_file = Path(tempfile.gettempdir(), f'test_csv-result_{uuid.uuid1()!s}.csv')
            with open(result_file, 'w', newline='', encoding='utf-8') as rf:
                rf.write(as_csv)
            assertFileContentsEqual(self._get_test_file_path(expected_csv_file_path), result_file)

        for case in [
            ('examples/example1_addons.out', 'example1_addons.csv'),
            ('geophires-result_example-3.out', 'geophires-result_example-3.csv'),
        ]:
            with self.subTest(msg=case[0]):
                assert_csv_equal(case[0], case[1])

    def test_parse_chp_percent_cost_allocation(self):
        result = GeophiresXResult(self._get_test_file_path('examples/example3.out'))
        self.assertEqual(
            result.result['ECONOMIC PARAMETERS']['CHP: Percent cost allocation for electrical plant']['value'], 93.48
        )

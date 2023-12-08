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

    def test_geophires_x_result_2(self):
        test_result_path = self._get_test_file_path('geophires-result_example-2.out')
        result = GeophiresXResult(test_result_path)

        assert result is not None
        assert result.direct_use_heat_breakeven_price_USD_per_MMBTU is None
        assert result.result['SUMMARY OF RESULTS']['Average Net Electricity Production']['value'] == 5.39
        assert result.result['ENGINEERING PARAMETERS']['Power plant type']['value'] == 'Supercritical ORC'

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
            eep,
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
                ['1', '0.090', '0.0023', '0.012', '0.0000', '1.14', '-70.00', '-70.00', '-101.08', '-101.08'],
                ['2', '0.090', '0.0023', '0.012', '0.0000', '1.14', '1.14', '-68.86', '5.70', '-95.39'],
                ['3', '0.090', '0.0023', '0.012', '0.0000', '1.14', '1.14', '-67.72', '5.74', '-89.65'],
                ['4', '0.090', '0.0023', '0.012', '0.0000', '1.14', '1.14', '-66.59', '5.75', '-83.90'],
                ['5', '0.090', '0.0023', '0.012', '0.0000', '1.14', '1.14', '-65.45', '5.76', '-78.14'],
                ['6', '0.090', '0.0023', '0.012', '0.0000', '1.14', '1.14', '-64.31', '5.76', '-72.37'],
                ['7', '0.102', '0.0026', '0.012', '0.0000', '1.14', '1.14', '-63.17', '5.77', '-66.61'],
                ['8', '0.114', '0.0030', '0.012', '0.0000', '1.14', '1.14', '-62.03', '6.28', '-60.32'],
                ['9', '0.126', '0.0033', '0.022', '0.0000', '1.14', '1.14', '-60.89', '6.79', '-53.53'],
                ['10', '0.138', '0.0036', '0.032', '0.0000', '1.14', '1.14', '-59.75', '7.31', '-46.22'],
                ['11', '0.150', '0.0039', '0.036', '0.0000', '1.14', '1.14', '-58.61', '7.82', '-38.40'],
                ['12', '0.150', '0.0039', '0.036', '0.0000', '1.14', '1.14', '-57.47', '8.33', '-30.07'],
                ['13', '0.150', '0.0039', '0.036', '0.0000', '1.14', '1.14', '-56.33', '8.34', '-21.73'],
                ['14', '0.150', '0.0039', '0.036', '0.0000', '1.14', '1.14', '-55.19', '8.34', '-13.39'],
                ['15', '0.150', '0.0039', '0.036', '0.0000', '1.14', '1.14', '-54.05', '8.34', '-5.05'],
                ['16', '0.150', '0.0039', '0.036', '0.0000', '1.14', '1.14', '-52.91', '8.34', '3.30'],
                ['17', '0.150', '0.0039', '0.036', '0.0000', '1.14', '1.14', '-51.77', '8.35', '11.64'],
                ['18', '0.150', '0.0039', '0.036', '0.0000', '1.14', '1.14', '-50.63', '8.35', '19.99'],
                ['19', '0.150', '0.0039', '0.036', '0.0000', '1.14', '1.14', '-49.49', '8.35', '28.34'],
                ['20', '0.150', '0.0039', '0.036', '0.0000', '1.14', '1.14', '-48.35', '8.35', '36.69'],
                ['21', '0.150', '0.0039', '0.036', '0.0000', '1.14', '1.14', '-47.21', '8.35', '45.04'],
                ['22', '0.150', '0.0039', '0.036', '0.0000', '1.14', '1.14', '-46.07', '8.35', '53.40'],
                ['23', '0.150', '0.0039', '0.036', '0.0000', '1.14', '1.14', '-44.93', '8.36', '61.75'],
                ['24', '0.150', '0.0039', '0.036', '0.0000', '1.14', '1.14', '-43.80', '8.36', '70.11'],
                ['25', '0.150', '0.0039', '0.036', '0.0000', '1.14', '1.14', '-42.66', '8.36', '78.46'],
                ['26', '0.150', '0.0039', '0.036', '0.0000', '1.14', '1.14', '-41.52', '8.36', '86.82'],
                ['27', '0.150', '0.0039', '0.036', '0.0000', '1.14', '1.14', '-40.38', '8.36', '95.18'],
                ['28', '0.150', '0.0039', '0.036', '0.0000', '1.14', '1.14', '-39.24', '8.36', '103.54'],
                ['29', '0.150', '0.0039', '0.036', '0.0000', '1.14', '1.14', '-38.10', '8.36', '111.90'],
                ['30', '0.150', '0.0039', '0.036', '0.0000', '1.14', '1.14', '-36.96', '8.36', '120.27'],
            ],
        )

    def test_ccus_profile(self):
        test_result_path = self._get_test_file_path('examples/example1_addons.out')
        result = GeophiresXResult(test_result_path)

        self.assertListEqual(
            result.result['CCUS PROFILE'],
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
                ['1', '', '', '', '', '', '-31.08', '-31.08'],
                ['2', '34111730.026', '0.015', '0.51', '0.51', '0.51', '5.07', '-26.01'],
                ['3', '34472696.061', '0.015', '0.52', '0.52', '1.03', '5.12', '-20.90'],
                ['4', '34594857.936', '0.015', '0.52', '0.52', '1.55', '5.13', '-15.76'],
                ['5', '34667203.032', '0.015', '0.52', '0.52', '2.07', '5.14', '-10.62'],
                ['6', '34717913.040', '0.015', '0.52', '0.52', '2.59', '5.15', '-5.48'],
                ['7', '34756598.286', '0.015', '0.52', '0.52', '3.11', '5.15', '-0.33'],
                ['8', '34787675.160', '0.025', '0.87', '0.87', '3.98', '6.01', '5.69'],
                ['9', '34813528.834', '0.035', '1.22', '1.22', '5.20', '6.87', '12.56'],
                ['10', '34835588.409', '0.045', '1.57', '1.57', '6.77', '7.74', '20.30'],
                ['11', '34854775.046', '0.055', '1.92', '1.92', '8.68', '8.60', '28.89'],
                ['12', '34871715.729', '0.065', '2.27', '2.27', '10.95', '9.46', '38.36'],
                ['13', '34886855.631', '0.075', '2.62', '2.62', '13.57', '9.81', '48.17'],
                ['14', '34900521.692', '0.085', '2.97', '2.97', '16.53', '10.17', '58.34'],
                ['15', '34912960.757', '0.095', '3.32', '3.32', '19.85', '10.52', '68.85'],
                ['16', '34924363.532', '0.100', '3.49', '3.49', '23.34', '10.70', '79.55'],
                ['17', '34934880.239', '0.100', '3.49', '3.49', '26.83', '10.70', '90.25'],
                ['18', '34944631.163', '0.100', '3.49', '3.49', '30.33', '10.70', '100.95'],
                ['19', '34953713.933', '0.100', '3.50', '3.50', '33.82', '10.70', '111.66'],
                ['20', '34962208.662', '0.100', '3.50', '3.50', '37.32', '10.71', '122.36'],
                ['21', '34970181.608', '0.100', '3.50', '3.50', '40.82', '10.71', '133.07'],
                ['22', '34977687.818', '0.100', '3.50', '3.50', '44.32', '10.71', '143.79'],
                ['23', '34984773.045', '0.100', '3.50', '3.50', '47.81', '10.71', '154.50'],
                ['24', '34991475.140', '0.100', '3.50', '3.50', '51.31', '10.72', '165.21'],
                ['25', '34997825.066', '0.100', '3.50', '3.50', '54.81', '10.72', '175.93'],
                ['26', '35003847.644', '0.100', '3.50', '3.50', '58.31', '10.72', '186.65'],
                ['27', '35009562.099', '0.100', '3.50', '3.50', '61.81', '10.72', '197.37'],
                ['28', '35014982.470', '0.100', '3.50', '3.50', '65.32', '10.72', '208.09'],
                ['29', '35020117.916', '0.100', '3.50', '3.50', '68.82', '10.72', '218.82'],
                ['30', '35024972.957', '0.100', '3.50', '3.50', '72.32', '10.72', '229.54'],
                ['31', '35029547.662', '0.100', '3.50', '3.50', '75.82', '10.73', '240.27'],
            ],
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
                self.assertFileContentsEqual(result_file, self._get_test_file_path(expected_csv_file_path))

        for case in [
            ('geophires-result_example-3.out', 'geophires-result_example-3.csv'),
            ('examples/example1_addons.out', 'example1_addons.csv'),
        ]:
            with self.subTest(msg=case[0]):
                assert_csv_equal(case[0], case[1])

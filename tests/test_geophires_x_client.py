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
        test_result_path = self._get_test_file_path('geophires-result_example-3.out')
        result = GeophiresXResult(test_result_path)

        as_csv = result.as_csv()
        self.assertIsNotNone(as_csv)

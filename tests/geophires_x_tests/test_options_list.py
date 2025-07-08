from typing import ClassVar

from base_test_case import BaseTestCase
from geophires_x.OptionList import EndUseOptions
from geophires_x.OptionList import PlantType
from geophires_x.OptionList import ReservoirModel
from geophires_x.OptionList import WellDrillingCostCorrelation


class EndUseOptionsTestCase(BaseTestCase):
    def test_get_end_use_option_from_input_string(self):
        self.assertEqual(EndUseOptions.from_input_string('1'), EndUseOptions.ELECTRICITY)

        with self.assertRaises(ValueError):
            EndUseOptions.from_input_string('2034982309')

    def test_get_end_use_option_from_int_val(self):
        self.assertEqual(EndUseOptions.from_int(1), EndUseOptions.ELECTRICITY)

    def test_cast_from_name_string(self):
        self.assertIs(EndUseOptions('Electricity'), EndUseOptions.ELECTRICITY)
        self.assertIs(EndUseOptions('Direct-Use Heat'), EndUseOptions.HEAT)

    def test_equality(self):
        self.assertFalse(EndUseOptions.HEAT == EndUseOptions.ELECTRICITY)
        self.assertTrue(EndUseOptions.HEAT == EndUseOptions.HEAT)
        self.assertTrue(EndUseOptions.HEAT != EndUseOptions.ELECTRICITY)
        self.assertTrue(EndUseOptions.ELECTRICITY != EndUseOptions.HEAT)
        self.assertFalse(EndUseOptions.HEAT is None)
        self.assertTrue(EndUseOptions.HEAT is EndUseOptions.HEAT)
        self.assertFalse(EndUseOptions.HEAT is EndUseOptions.ELECTRICITY)
        self.assertTrue(EndUseOptions.HEAT is not EndUseOptions.ELECTRICITY)

        self.assertEqual(str(EndUseOptions.HEAT), 'EndUseOptions.HEAT')
        self.assertEqual(str(EndUseOptions.ELECTRICITY), 'EndUseOptions.ELECTRICITY')


class WellDrillingCostCorrelationTestCase(BaseTestCase):

    def test_equality(self):
        self.assertFalse(WellDrillingCostCorrelation.VERTICAL_SMALL == WellDrillingCostCorrelation.DEVIATED_SMALL)
        self.assertTrue(WellDrillingCostCorrelation.VERTICAL_SMALL == WellDrillingCostCorrelation.VERTICAL_SMALL)

    COST_CORRELATION_TEST_CASES: ClassVar[list] = [
        (WellDrillingCostCorrelation.VERTICAL_SMALL, 3500, 5.1),
        (WellDrillingCostCorrelation.VERTICAL_SMALL, 6500, 13.9),
        (WellDrillingCostCorrelation.VERTICAL_SMALL, 7000, 15.9),
        (WellDrillingCostCorrelation.VERTICAL_LARGE, 6500, 17.2),
        (WellDrillingCostCorrelation.DEVIATED_SMALL, 6500, 14.9),
        (WellDrillingCostCorrelation.DEVIATED_LARGE, 6500, 18.3),
    ]

    def test_drilling_cost_curve_correlations(self):
        """
        Check calibration with NREL 2025 Cost Curve Update.
        Values in COST_CORRELATION_TEST_CASES derived from graphs on p. 8 of
        https://pangea.stanford.edu/ERE/db/GeoConf/papers/SGW/2025/Akindipe.pdf?t=1740084555
        """

        for test_case in WellDrillingCostCorrelationTestCase.COST_CORRELATION_TEST_CASES:
            correlation: WellDrillingCostCorrelation = test_case[0]
            depth_m = test_case[1]
            expected_cost_musd = test_case[2]
            with self.subTest(msg=str(f'{correlation.name}, {depth_m}m')):
                self.assertAlmostEqual(expected_cost_musd, correlation.calculate_cost_MUSD(depth_m), delta=0.1)


class PlantTypeTestCase(BaseTestCase):
    def test_equality(self):
        self.assertFalse(PlantType.SUB_CRITICAL_ORC == PlantType.SUPER_CRITICAL_ORC)
        self.assertTrue(WellDrillingCostCorrelation.VERTICAL_SMALL == WellDrillingCostCorrelation.VERTICAL_SMALL)


class ReservoirModelTestCase(BaseTestCase):
    def test_display_name(self):
        self.assertEqual(
            'Multiple Parallel Fractures Model (Gringarten)', ReservoirModel.MULTIPLE_PARALLEL_FRACTURES.display_name
        )

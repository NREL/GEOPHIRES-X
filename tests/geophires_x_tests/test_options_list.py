from base_test_case import BaseTestCase
from geophires_x.OptionList import EndUseOptions
from geophires_x.OptionList import PlantType
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

    def test_baseline_curve_costs(self):
        # Sanity-check calibration with NREL 2025 Cost Curve Update
        # https://pangea.stanford.edu/ERE/db/GeoConf/papers/SGW/2025/Akindipe.pdf?t=1740084555

        self.assertAlmostEqual(5.1, WellDrillingCostCorrelation.VERTICAL_SMALL.calculate_cost_MUSD(3500), delta=0.1)
        self.assertAlmostEqual(13.9, WellDrillingCostCorrelation.VERTICAL_SMALL.calculate_cost_MUSD(6500), delta=0.1)
        self.assertAlmostEqual(15.9, WellDrillingCostCorrelation.VERTICAL_SMALL.calculate_cost_MUSD(7000), delta=0.1)

        self.assertAlmostEqual(17.2, WellDrillingCostCorrelation.VERTICAL_LARGE.calculate_cost_MUSD(6500), delta=0.1)

        self.assertAlmostEqual(14.9, WellDrillingCostCorrelation.DEVIATED_SMALL.calculate_cost_MUSD(6500), delta=0.1)

        self.assertAlmostEqual(18.3, WellDrillingCostCorrelation.DEVIATED_LARGE.calculate_cost_MUSD(6500), delta=0.1)


class PlantTypeTestCase(BaseTestCase):
    def test_equality(self):
        self.assertFalse(PlantType.SUB_CRITICAL_ORC == PlantType.SUPER_CRITICAL_ORC)
        self.assertTrue(WellDrillingCostCorrelation.VERTICAL_SMALL == WellDrillingCostCorrelation.VERTICAL_SMALL)

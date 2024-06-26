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
        self.assertFalse(EndUseOptions.HEAT is None)
        self.assertTrue(EndUseOptions.HEAT is EndUseOptions.HEAT)
        # self.assertTrue(EndUseOptions.HEAT == 'HEAT')
        # self.assertFalse(EndUseOptions.HEAT == 'Electricity')


class WellDrillingCostCorrelationTestCase(BaseTestCase):
    def test_equality(self):
        self.assertFalse(WellDrillingCostCorrelation.VERTICAL_SMALL == WellDrillingCostCorrelation.DEVIATED_SMALL)
        self.assertTrue(WellDrillingCostCorrelation.VERTICAL_SMALL == WellDrillingCostCorrelation.VERTICAL_SMALL)


class PlantTypeTestCase(BaseTestCase):
    def test_equality(self):
        self.assertFalse(PlantType.SUB_CRITICAL_ORC == PlantType.SUPER_CRITICAL_ORC)
        self.assertTrue(WellDrillingCostCorrelation.VERTICAL_SMALL == WellDrillingCostCorrelation.VERTICAL_SMALL)

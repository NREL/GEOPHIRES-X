from base_test_case import BaseTestCase
from geophires_x.Units import CurrencyFrequencyUnit


class UnitsTestCase(BaseTestCase):

    def test_get_currency_frequency_unit_currency_unit_str(self):
        self.assertEqual('USD', CurrencyFrequencyUnit.DOLLARSPERYEAR.get_currency_unit_str())

from geophires_x_client import GeophiresXResult
from tests.base_test_case import BaseTestCase


class GeophiresXResultTestCase(BaseTestCase):

    def test_get_sam_cash_flow_row_name_unit_split(self) -> None:
        cases = [
            ('Electricity to grid (kWh)', ['Electricity to grid', 'kWh']),
            ('Federal tax benefit (liability) ($)', ['Federal tax benefit (liability)', '$']),
            ('Underwater baskets', ['Underwater baskets', '']),
        ]

        for case in cases:
            with self.subTest(msg=case[0]):
                actual = GeophiresXResult._get_sam_cash_flow_row_name_unit_split(case[0])
                self.assertListEqual(actual, case[1])

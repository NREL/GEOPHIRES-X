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

    def test_reservoir_volume_calculation_note(self):
        r: GeophiresXResult = GeophiresXResult(self._get_test_file_path('../examples/example2.out'))
        field_name = 'Reservoir volume calculation note'
        self.assertIn(field_name, r.result['RESERVOIR PARAMETERS'])
        self.assertEqual(
            r.result['RESERVOIR PARAMETERS'][field_name],
            'Number of fractures calculated with reservoir volume and fracture separation as input',
        )

from __future__ import annotations


from base_test_case import BaseTestCase

# ruff: noqa: I001  # Successful module initialization is dependent on this specific import order.

# noinspection PyProtectedMember

# noinspection PyProtectedMember
from geophires_x_client import GeophiresInputParameters
from geophires_x_client import GeophiresXClient
from geophires_x_client import GeophiresXResult


class WellBoresTestCase(BaseTestCase):

    def test_number_of_doublets(self):
        def _get_result(_params) -> GeophiresXResult:
            params = GeophiresInputParameters(
                {
                    'Reservoir Depth': 5,
                    'Gradient 1': 74,
                    'Power Plant Type': 2,
                    'Maximum Temperature': 600,
                }
                | _params
            )
            return GeophiresXClient().get_geophires_result(params)

        def _prod_inj_lcoe(_r: GeophiresXResult) -> tuple[int, int]:
            return (
                _r.result['ENGINEERING PARAMETERS']['Number of Production Wells']['value'],
                _r.result['ENGINEERING PARAMETERS']['Number of Injection Wells']['value'],
                _r.result['SUMMARY OF RESULTS']['Electricity breakeven price']['value'],
                _r.result['SUMMARY OF RESULTS']['Electricity breakeven price']['value'],
                _r.result['SURFACE EQUIPMENT SIMULATION RESULTS']['Average Net Electricity Generation']['value'],
            )

        r_prod_inj: GeophiresXResult = _get_result(
            {
                'Number of Production Wells': 10,
                'Number of Injection Wells': 10,
            }
        )

        r_doublets: GeophiresXResult = _get_result(
            {
                'Number of Doublets': 10,
            }
        )

        self.assertEqual(_prod_inj_lcoe(r_doublets), _prod_inj_lcoe(r_prod_inj))

    def test_number_of_doublets_validation(self):
        def _get_result(_params) -> GeophiresXResult:
            params = GeophiresInputParameters(
                {
                    'Reservoir Depth': 5,
                    'Gradient 1': 74,
                    'Power Plant Type': 2,
                    'Maximum Temperature': 600,
                }
                | _params
            )
            return GeophiresXClient().get_geophires_result(params)

        with self.assertRaises(RuntimeError):
            _get_result(
                {
                    'Number of Production Wells': 10,
                    'Number of Injection Wells': 10,
                    'Number of Doublets': 10,
                }
            )

        with self.assertRaises(RuntimeError):
            _get_result(
                {
                    'Number of Production Wells': 10,
                    'Number of Doublets': 10,
                }
            )

        with self.assertRaises(RuntimeError):
            _get_result(
                {
                    'Number of Injection Wells': 10,
                    'Number of Doublets': 10,
                }
            )

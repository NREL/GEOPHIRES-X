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
        r_prod_inj: GeophiresXResult = self._get_result(
            {
                'Number of Production Wells': 10,
                'Number of Injection Wells': 10,
            }
        )

        r_doublets: GeophiresXResult = self._get_result(
            {
                'Number of Doublets': 10,
            }
        )

        self.assertEqual(self._prod_inj_lcoe_production(r_doublets), self._prod_inj_lcoe_production(r_prod_inj))

    def test_number_of_doublets_validation(self):
        with self.assertRaises(RuntimeError):
            self._get_result(
                {
                    'Number of Production Wells': 10,
                    'Number of Injection Wells': 10,
                    'Number of Doublets': 10,
                }
            )

        with self.assertRaises(RuntimeError):
            self._get_result(
                {
                    'Number of Production Wells': 10,
                    'Number of Doublets': 10,
                }
            )

        with self.assertRaises(RuntimeError):
            self._get_result(
                {
                    'Number of Injection Wells': 10,
                    'Number of Doublets': 10,
                }
            )

    def test_number_of_doublets_non_integer(self):
        """
        Non-integer values are relevant for MC simulations, since distributions produce floats, and we want
        Number of Doublets to be compatible with MC.
        """

        prod_inj_lcoe = self._prod_inj_lcoe_production(
            self._get_result(
                {
                    'Number of Doublets': 40.7381,
                }
            )
        )

        self.assertEqual(prod_inj_lcoe[0], 40)
        self.assertEqual(prod_inj_lcoe[1], 40)

        prod_inj_lcoe_2 = self._prod_inj_lcoe_production(
            self._get_result(
                {
                    'Number of Doublets': 199.2,
                }
            )
        )

        self.assertEqual(prod_inj_lcoe_2[0], 199)
        self.assertEqual(prod_inj_lcoe_2[1], 199)

    # noinspection PyMethodMayBeStatic
    def _get_result(self, _params) -> GeophiresXResult:
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

    # noinspection PyMethodMayBeStatic
    def _prod_inj_lcoe_production(self, _r: GeophiresXResult) -> tuple[int, int, float, float]:
        return (
            _r.result['ENGINEERING PARAMETERS']['Number of Production Wells']['value'],
            _r.result['ENGINEERING PARAMETERS']['Number of Injection Wells']['value'],
            _r.result['SUMMARY OF RESULTS']['Electricity breakeven price']['value'],
            _r.result['SURFACE EQUIPMENT SIMULATION RESULTS']['Average Net Electricity Generation']['value'],
        )

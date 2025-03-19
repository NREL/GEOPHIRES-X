import os
import sys
from pathlib import Path

import numpy_financial as npf

# ruff: noqa: I001  # Successful module initialization is dependent on this specific import order.
from geophires_x.Model import Model
from geophires_x.Economics import CalculateFinancialPerformance
from tests.base_test_case import BaseTestCase


class EconomicsTestCase(BaseTestCase):
    @staticmethod
    def cumm_revenue(total_revenue):
        cumm_revenue = [total_revenue[0]] * len(total_revenue)
        cumm_revenue[1] = total_revenue[1]
        for i in range(2, len(total_revenue)):
            cumm_revenue[i] = cumm_revenue[i - 1] + total_revenue[i]
        return cumm_revenue

    def test_irr(self):
        """
        Test cases adapted from https://numpy.org/numpy-financial/latest/irr.html
        """

        def calc_irr(total_revenue):
            NPV, IRR, VIR, MOIC = CalculateFinancialPerformance(
                30, 5, total_revenue, EconomicsTestCase.cumm_revenue(total_revenue), 1000, 10
            )

            return IRR

        self.assertAlmostEqual(28.095, calc_irr([-100, 39, 59, 55, 20]), places=3)
        self.assertAlmostEqual(-9.55, calc_irr([-100, 0, 0, 74]), places=2)
        self.assertAlmostEqual(-8.33, calc_irr([-100, 100, 0, -7]), places=2)
        self.assertAlmostEqual(6.21, calc_irr([-100, 100, 0, 7]), places=2)
        self.assertAlmostEqual(8.86, calc_irr([-5, 10.5, 1, -8, 1]), places=2)

    def test_npv(self):
        """
        Includes sanity checks that numpy-financial.npv used by CalculateFinancialPerformance
        matches reference calculations
        """

        rate = 0.12

        def calc_npv(total_revenue, discount_initial_year_cashflow=False):
            NPV, IRR, VIR, MOIC = CalculateFinancialPerformance(
                len(total_revenue) + 1,
                rate * 100,
                total_revenue,
                EconomicsTestCase.cumm_revenue(total_revenue),
                total_revenue[0],
                10,
                discount_initial_year_cashflow=discount_initial_year_cashflow,
            )

            return NPV

        # https://www.nrel.gov/docs/legosti/old/5173.pdf, p. 41
        cashflow_series = [-10000, 7274, 6558, 6223, 6087, 6259]

        npf_npv = npf.npv(rate, cashflow_series)
        self.assertEqual(13572, round(npf_npv))

        geophires_npv = calc_npv(cashflow_series)
        self.assertEqual(13572, round(geophires_npv))

        # https://support.microsoft.com/en-us/office/npv-function-8672cb67-2576-4d07-b67b-ac28acf2a568
        rate = 0.1
        cashflow_series = [-10000, 3000, 4200, 6800]
        excel_npv = npf.npv(rate, [0, *cashflow_series])
        self.assertEqual(1188.44, round(excel_npv, 2))

        geophires_npv = calc_npv(cashflow_series, discount_initial_year_cashflow=True)
        self.assertEqual(1188.44, round(geophires_npv, 2))

    def test_well_drilling_cost_correlation_tooltiptext(self):
        ec = self._new_model().economics
        self.assertEqual(
            ec.wellcorrelation.ToolTipText,
            'Select the built-in well drilling and completion cost correlation: '
            + '1: vertical small diameter, baseline (2025 cost curve); '
            + '2: deviated small diameter, baseline (2025 cost curve); '
            + '3: vertical large diameter, baseline (2025 cost curve); '
            + '4: deviated large diameter, baseline (2025 cost curve); '
            + '5: Simple; '
            + '6: vertical small diameter, intermediate1; '
            + '7: vertical small diameter, intermediate2; '
            + '8: deviated small diameter, intermediate1; '
            + '9: deviated small diameter, intermediate2; '
            + '10: vertical large diameter, intermediate1; '
            + '11: vertical large diameter, intermediate2; '
            + '12: deviated large diameter, intermediate1; '
            + '13: deviated large diameter, intermediate2; '
            + '14: vertical open-hole, small diameter, ideal; '
            + '15: deviated liner, small diameter, ideal; '
            + '16: vertical open-hole, large diameter, ideal; '
            + '17: deviated liner, large diameter, ideal',
        )

    def _new_model(self) -> Model:
        stash_cwd = Path.cwd()
        stash_sys_argv = sys.argv

        sys.argv = ['']

        m = Model(enable_geophires_logging_config=False)

        sys.argv = stash_sys_argv
        os.chdir(stash_cwd)

        return m

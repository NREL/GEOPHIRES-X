from base_test_case import BaseTestCase
from geophires_x.Economics import CalculateFinancialPerformance


class ReservoirTestCase(BaseTestCase):
    def test_irr(self):
        """
        Test cases adapted from https://numpy.org/numpy-financial/latest/irr.html
        """

        def cumm_revenue(total_revenue):
            cumm_revenue = [total_revenue[0]] * len(total_revenue)
            cumm_revenue[1] = total_revenue[1]
            for i in range(2, len(total_revenue)):
                cumm_revenue[i] = cumm_revenue[i - 1] + total_revenue[i]
            return cumm_revenue

        def calc_irr(total_revenue):
            NPV, IRR, VIR, MOIC = CalculateFinancialPerformance(
                30, 5, total_revenue, cumm_revenue(total_revenue), 1000, 10
            )

            return IRR

        self.assertAlmostEqual(28.095, calc_irr([-100, 39, 59, 55, 20]), places=3)
        self.assertAlmostEqual(-9.55, calc_irr([-100, 0, 0, 74]), places=2)
        self.assertAlmostEqual(-8.33, calc_irr([-100, 100, 0, -7]), places=2)
        self.assertAlmostEqual(6.21, calc_irr([-100, 100, 0, 7]), places=2)
        self.assertAlmostEqual(8.86, calc_irr([-5, 10.5, 1, -8, 1]), places=2)

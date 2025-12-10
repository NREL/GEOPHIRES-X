from __future__ import annotations

from base_test_case import BaseTestCase

# noinspection PyProtectedMember
from geophires_x.EconomicsSamCashFlow import _get_logger
from geophires_x.EconomicsSamPreRevenue import PreRevenueCostsAndCashflow

# noinspection PyProtectedMember
from geophires_x.EconomicsSamPreRevenue import _calculate_pre_revenue_costs_and_cashflow
from geophires_x.EconomicsSamPreRevenue import adjust_phased_schedule_to_new_length


class EconomicsSamPreRevenueTestCase(BaseTestCase):

    def test_adjust_phased_schedule_to_new_length(self) -> None:
        def asrt(original_schedule: list[float], new_length: int, expected_schedule: list[float]) -> None:
            adjusted_schedule = adjust_phased_schedule_to_new_length(original_schedule, new_length)
            self.assertListAlmostEqual(expected_schedule, adjusted_schedule, percent=3)

        # fmt:off
        asrt(
            [1.],
            2,
            [0.5, 0.5]
        )

        asrt(
            [0.5, 0.5],
            4,
            [0.25, 0.25, 0.25, 0.25]
        )

        asrt(
            [0.25, 0.25, 0.25, 0.25],
            2,
            [0.5, 0.5],
        )

        asrt(
            [0.5, 0.25, 0.25],
            6,
            [0.25] * 2 + [0.1278] * 4
        )
        # fmt:on

    def test_calculate_pre_revenue_costs_and_cashflow(self) -> None:
        _log = _get_logger()
        pre_rev: PreRevenueCostsAndCashflow = _calculate_pre_revenue_costs_and_cashflow(
            100_000_000, 3, [0.25, 0.25, 0.5], 0.1, 0.05, 0.5, 1, _log
        )

        def _get_row(row_name: str) -> list[float]:
            cf_line_item = next(row for row in pre_rev.pre_revenue_cash_flow_profile if row[0] == row_name)[1:]

            # Ensure dict property consistency
            self.assertListEqual(
                cf_line_item, pre_rev.pre_revenue_cash_flow_profile_dict[row_name.replace('[construction] ', '')]
            )

            return cf_line_item

        self.assertListEqual([-25e6, -25e6, -50e6], _get_row('Overnight capital expenditure [construction] ($)'))

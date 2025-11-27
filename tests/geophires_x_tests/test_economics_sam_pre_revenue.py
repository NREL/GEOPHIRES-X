from __future__ import annotations

from base_test_case import BaseTestCase
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
            [0.25] * 2 + [0.1278]*4
        )
        # fmt:on

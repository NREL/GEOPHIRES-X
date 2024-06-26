import unittest

from tests.base_test_case import BaseTestCase


class TestBaseTestCase(BaseTestCase):
    def test_assertAlmostEqualWithinPercentage(self):
        self.assertAlmostEqualWithinPercentage(100, 100, percent=5)
        self.assertAlmostEqualWithinPercentage(100, 95, percent=5)
        self.assertAlmostEqualWithinPercentage(100, 105, percent=5)
        self.assertAlmostEqualWithinPercentage(-100, -95, percent=5)
        self.assertAlmostEqualWithinPercentage(-100, -105, percent=5)

        with self.assertRaises(AssertionError):
            self.assertAlmostEqualWithinPercentage(100, 0, percent=5)
            self.assertAlmostEqualWithinPercentage(100, 94.5, percent=5)
            self.assertAlmostEqualWithinPercentage(100, 105.5, percent=5)

        self.assertListAlmostEqual([1, 2, 3], [1.1, 2.2, 3.3], percent=10.5)

        with self.assertRaises(AssertionError):
            self.assertListAlmostEqual([1, 2, 3], [1.1, 2.2, 3.3], percent=5)


if __name__ == '__main__':
    unittest.main()

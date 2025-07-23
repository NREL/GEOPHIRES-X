import os
import platform
import sys
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

        with self.assertRaises(AssertionError):
            self.assertAlmostEqualWithinPercentage(100, 94.5, percent=5)

        with self.assertRaises(AssertionError):
            self.assertAlmostEqualWithinPercentage(100, 105.5, percent=5)

        self.assertListAlmostEqual([1, 2, 3], [1.1, 2.2, 3.3], percent=10.5)

        with self.assertRaises(AssertionError):
            self.assertListAlmostEqual([1, 2, 3], [1.1, 2.2, 3.3], percent=5)

    def test_assertAlmostEqualWithinPercentage_bad_arguments(self):
        with self.assertRaises(ValueError) as msg_type_error:
            self.assertAlmostEqualWithinPercentage(100, 100, 10)

            self.assertIn(str(msg_type_error), '(you may have meant to pass percent=10)')

        with self.assertLogs(level='INFO') as logs:
            with self.assertRaises(AssertionError):
                self.assertAlmostEqualWithinPercentage([1, 2, 3], [1.1, 2.2, 3.3], percent=10.5)

            try:
                self.assertHasLogRecordWithMessage(
                    logs,
                    'Got 2 lists, you probably meant to call:\n\t'
                    'self.assertListAlmostEqual([1, 2, 3], [1.1, 2.2, 3.3], msg=None, percent=10.5)',
                )
            except AssertionError as ae:
                if (
                    'CI' in os.environ
                    and (platform.system() in ['Darwin', 'Linux'])
                    and (sys.version_info.major, sys.version_info.minor) == (3, 11)
                ):
                    # Intermittent failures observed in GitHub Actions py311 macos and ubuntu beginning on 2025-07-23.
                    # Examples:
                    # - https://github.com/softwareengineerprogrammer/GEOPHIRES/actions/runs/16476574734/job/46579711905
                    # - https://github.com/softwareengineerprogrammer/GEOPHIRES/actions/runs/16477002832/job/46581220253
                    # TODO to investigate and resolve
                    self.skipTest(f'Skipping test due to platform-specific intermittent failure: {ae!s}')
                else:
                    raise ae


if __name__ == '__main__':
    unittest.main()

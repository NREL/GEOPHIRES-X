from __future__ import annotations

import inspect
import numbers
import os.path
import unittest

# noinspection PyProtectedMember
from geophires_x_client import _get_logger


class BaseTestCase(unittest.TestCase):
    maxDiff = None

    def _get_test_file_path(self, test_file_name) -> str:
        return os.path.join(os.path.abspath(os.path.dirname(inspect.getfile(self.__class__))), test_file_name)

    def _get_test_file_content(self, test_file_name, **open_kw_args) -> str:
        with open(self._get_test_file_path(test_file_name), **open_kw_args) as f:
            return f.readlines()

    def _list_test_files_dir(self, test_files_dir: str):
        return os.listdir(self._get_test_file_path(test_files_dir))  # noqa: PTH208

    def assertAlmostEqualWithinPercentage(self, expected, actual, msg: str | None = None, percent=5):
        if msg is not None and not isinstance(msg, str):
            raise ValueError(f'msg must be a string (you may have meant to pass percent={msg})')

        if isinstance(expected, numbers.Real):
            self.assertAlmostEqual(expected, actual, msg=msg, delta=abs(percent / 100.0 * expected))
        else:
            if isinstance(expected, list) and isinstance(actual, list):
                suggest = f'self.assertListAlmostEqual({expected}, {actual}, msg={msg}, percent={percent})'
                suggest = f'Got 2 lists, you probably meant to call:\n\t{suggest}'
                log = _get_logger(__name__)
                log.warning(suggest)

            self.assertEqual(expected, actual, msg)

    def assertDictAlmostEqual(self, expected, actual, msg=None, places=7, percent=None):
        """
        https://stackoverflow.com/a/53081544/21380804
        """

        if percent is not None:
            places = None

        # check if both inputs are dicts
        self.assertIsInstance(expected, dict, 'First argument is not a dictionary')
        self.assertIsInstance(actual, dict, 'Second argument is not a dictionary')

        # check if both inputs have the same keys
        self.assertEqual(expected.keys(), actual.keys())

        # check each key
        for key, value in expected.items():
            if isinstance(value, dict):
                self.assertDictAlmostEqual(expected[key], actual[key], msg=msg, places=places, percent=percent)
            elif isinstance(value, list):
                self.assertListAlmostEqual(expected[key], actual[key], msg=msg, places=places, percent=percent)
            else:
                if places is not None:
                    self.assertAlmostEqual(expected[key], actual[key], places=places, msg=msg)
                else:
                    self.assertAlmostEqualWithinPercentage(expected[key], actual[key], percent=percent, msg=msg)

    def assertListAlmostEqual(self, expected, actual, msg=None, places=7, percent=None):
        if percent is not None:
            places = None

        # check if both inputs are dicts
        self.assertIsInstance(expected, list, 'First argument is not a list')
        self.assertIsInstance(actual, list, 'Second argument is not a list')

        # check if both inputs have the same keys
        self.assertEqual(len(expected), len(actual))

        # check each key
        for i in range(len(expected)):
            v1 = expected[i]
            v2 = actual[i]
            if isinstance(v1, dict):
                self.assertDictAlmostEqual(v1, v2, msg=msg, places=places, percent=percent)
            elif isinstance(v1, list):
                self.assertListAlmostEqual(v1, v2, msg=msg, places=places, percent=percent)
            else:
                if places is not None:
                    self.assertAlmostEqual(v1, v2, places=places, msg=msg)
                else:
                    self.assertAlmostEqualWithinPercentage(v1, v2, percent=percent, msg=msg)

    def assertFileContentsEqual(self, expected, actual):
        with open(
            expected, newline=None
        ) as f1_o:  # newline=None enables universal line endings which is required by Windows
            with open(actual, newline=None) as f2_o:
                f1_lines = f1_o.readlines()
                f2_lines = f2_o.readlines()
                self.assertListEqual(f1_lines, f2_lines, msg=f'{expected}, {actual}')

    # noinspection PyPep8Naming,PyMethodMayBeStatic
    def assertHasLogRecordWithMessage(self, logs_, message):
        assert message in [record.message for record in logs_.records]

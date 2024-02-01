import inspect
import os.path
import unittest


class BaseTestCase(unittest.TestCase):
    maxDiff = None

    def _get_test_file_path(self, test_file_name) -> str:
        return os.path.join(os.path.abspath(os.path.dirname(inspect.getfile(self.__class__))), test_file_name)

    def _get_test_file_content(self, test_file_name):
        with open(self._get_test_file_path(test_file_name)) as f:
            return f.readlines()

    def _list_test_files_dir(self, test_files_dir: str):
        return os.listdir(self._get_test_file_path(test_files_dir))

    def assertDictAlmostEqual(self, expected, actual, msg=None, places=7):
        """
        https://stackoverflow.com/a/53081544/21380804
        """

        # check if both inputs are dicts
        self.assertIsInstance(expected, dict, 'First argument is not a dictionary')
        self.assertIsInstance(actual, dict, 'Second argument is not a dictionary')

        # check if both inputs have the same keys
        self.assertEqual(expected.keys(), actual.keys())

        # check each key
        for key, value in expected.items():
            if isinstance(value, dict):
                self.assertDictAlmostEqual(expected[key], actual[key], msg=msg, places=places)
            elif isinstance(value, list):
                self.assertListAlmostEqual(expected[key], actual[key], msg=msg, places=places)
            else:
                self.assertAlmostEqual(expected[key], actual[key], places=places, msg=msg)

    def assertListAlmostEqual(self, expected, actual, msg=None, places=7):
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
                self.assertDictAlmostEqual(v1, v2, msg=msg, places=places)
            elif isinstance(v1, list):
                self.assertListAlmostEqual(v1, v2, msg=msg, places=places)
            else:
                self.assertAlmostEqual(v1, v2, places=places, msg=msg)

    def assertFileContentsEqual(self, expected, actual):
        with open(
            expected, newline=None
        ) as f1_o:  # newline=None enables universal line endings which is required by Windows
            with open(actual, newline=None) as f2_o:
                f1_lines = f1_o.readlines()
                f2_lines = f2_o.readlines()
                self.assertListEqual(f1_lines, f2_lines, msg=f'{expected}, {actual}')

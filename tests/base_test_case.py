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

    def assertDictAlmostEqual(self, d1, d2, msg=None, places=7):
        """
        https://stackoverflow.com/a/53081544/21380804
        """

        # check if both inputs are dicts
        self.assertIsInstance(d1, dict, 'First argument is not a dictionary')
        self.assertIsInstance(d2, dict, 'Second argument is not a dictionary')

        # check if both inputs have the same keys
        self.assertEqual(d1.keys(), d2.keys())

        # check each key
        for key, value in d1.items():
            if isinstance(value, dict):
                self.assertDictAlmostEqual(d1[key], d2[key], msg=msg, places=places)
            elif isinstance(value, list):
                self.assertListAlmostEqual(d1[key], d2[key], msg=msg, places=places)
            else:
                self.assertAlmostEqual(d1[key], d2[key], places=places, msg=msg)

    def assertListAlmostEqual(self, l1, l2, msg=None, places=7):
        # check if both inputs are dicts
        self.assertIsInstance(l1, list, 'First argument is not a list')
        self.assertIsInstance(l2, list, 'Second argument is not a list')

        # check if both inputs have the same keys
        self.assertEqual(len(l1), len(l2))

        # check each key
        for i in range(len(l1)):
            v1 = l1[i]
            v2 = l2[i]
            if isinstance(v1, dict):
                self.assertDictAlmostEqual(v1, v2, msg=msg, places=places)
            elif isinstance(v1, list):
                self.assertListAlmostEqual(v1, v2, msg=msg, places=places)
            else:
                self.assertAlmostEqual(v1, v2, places=places, msg=msg)

    def assertFileContentsEqual(self, f1, f2):
        with open(f1, newline=None) as f1_o:  # newline=None enables universal line endings which is required by Windows
            with open(f2, newline=None) as f2_o:
                f1_lines = f1_o.readlines()
                f2_lines = f2_o.readlines()
                self.assertListEqual(f1_lines, f2_lines, msg=f'{f1}, {f2}')

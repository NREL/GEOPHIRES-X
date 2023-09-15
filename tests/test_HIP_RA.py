import os.path
import unittest
import sys
from pathlib import Path
from geophires_x import HIP_RA

from geophires_x_client import GeophiresXClient
from geophires_x_client import GeophiresXResult
from geophires_x_client.geophires_input_parameters import EndUseOption
from geophires_x_client.geophires_input_parameters import GeophiresInputParameters


# noinspection PyTypeChecker
class HIP_RATestCase(unittest.TestCase):
    maxDiff = None

    def test_HIP_RA_examples(self):
        client = GeophiresXClient()
        example_files = self._list_test_files_dir(test_files_dir='examples')

        def get_output_file_for_example(example_file: str):
            return self._get_test_file_path(Path('examples', f'{example_file.split(".txt")[0].capitalize()}V3_output.txt'))

        for example_file_path in example_files:
            if example_file_path.startswith('HIPexample') and '_output' not in example_file_path:
                with self.subTest(msg=example_file_path):
                    input_file_path = self._get_test_file_path(Path('examples', example_file_path))
                    sys.argv = ['', input_file_path]
                    HIP_RA.main()

    def _get_test_file_path(self, test_file_name):
        return os.path.join(os.path.abspath(os.path.dirname(__file__)), test_file_name)

    def _get_test_file_content(self, test_file_name):
        with open(self._get_test_file_path(test_file_name)) as f:
            return f.readlines()

    def _list_test_files_dir(self, test_files_dir: str):
        return os.listdir(self._get_test_file_path(test_files_dir))

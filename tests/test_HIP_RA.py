import sys
from pathlib import Path

from base_test_case import BaseTestCase
from geophires_x import HIP_RA


# noinspection PyTypeChecker
class HIP_RATestCase(BaseTestCase):
    def test_HIP_RA_examples(self):
        example_files = self._list_test_files_dir(test_files_dir='examples')

        def get_output_file_for_example(example_file: str):
            return self._get_test_file_path(
                Path('examples', f'{example_file.split(".txt")[0].capitalize()}V3_output.txt')
            )

        for example_file_path in example_files:
            if example_file_path.startswith('HIPexample') and '_output' not in example_file_path:
                with self.subTest(msg=example_file_path):
                    input_file_path = self._get_test_file_path(Path('examples', example_file_path))
                    sys.argv = ['', input_file_path]
                    HIP_RA.main()

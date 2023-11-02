from pathlib import Path

from hip_ra import HipRaClient
from hip_ra import HipRaInputParameters
from tests.base_test_case import BaseTestCase


# noinspection PyTypeChecker
class HIP_RATestCase(BaseTestCase):
    def test_HIP_RA_examples(self):
        example_files = self._list_test_files_dir(test_files_dir='examples')

        client = HipRaClient()

        def get_output_file_for_example(example_file: Path):
            return self._get_test_file_path(Path(example_file).with_suffix('.out'))

        for example_file_path in example_files:
            if example_file_path.startswith('HIPexample') and '.out' not in example_file_path:
                with self.subTest(msg=example_file_path):
                    input_file_path = self._get_test_file_path(Path('examples', example_file_path))
                    result = client.get_hip_ra_result(HipRaInputParameters(input_file_path))

                    assert result is not None
                    self.assertFileContentsEqual(get_output_file_for_example(input_file_path), result.output_file_path)

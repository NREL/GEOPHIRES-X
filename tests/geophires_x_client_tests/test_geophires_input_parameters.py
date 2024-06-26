import tempfile
import uuid
from pathlib import Path

from geophires_x_client import GeophiresInputParameters
from geophires_x_client import GeophiresXClient
from tests.base_test_case import BaseTestCase


class GeophiresInputParametersTestCase(BaseTestCase):

    def test_id(self):
        input_1 = GeophiresInputParameters(from_file_path=self._get_test_file_path('client_test_input_1.txt'))
        input_2 = GeophiresInputParameters(from_file_path=self._get_test_file_path('client_test_input_2.txt'))
        self.assertIsNot(input_1._id, input_2._id)

    def test_init_with_input_file(self):
        file_path = self._get_test_file_path('client_test_input_1.txt')
        input_params = GeophiresInputParameters(from_file_path=file_path)
        self.assertEqual(file_path, input_params.as_file_path())

    def test_init_with_params(self):
        dummy_input_path = Path(tempfile.gettempdir(), f'geophires-dummy-input-params_{uuid.uuid4()!s}.txt')
        with open(dummy_input_path, 'w', encoding='UTF-8') as f:
            f.write('Foo, Bar\nBaz, Qux\n')

        input_from_file = GeophiresInputParameters(from_file_path=dummy_input_path)
        input_from_params = GeophiresInputParameters(params={'Foo': 'Bar', 'Baz': 'Qux'})
        self.assertFileContentsEqual(input_from_file.as_file_path(), input_from_params.as_file_path())

    def test_init_with_input_file_and_parameters(self):
        dummy_input_content = 'Foo, Bar\nBaz, Qux\n'
        dummy_input_path = Path(tempfile.gettempdir(), f'geophires-dummy-input-params_{uuid.uuid4()!s}.txt')
        with open(dummy_input_path, 'w', encoding='UTF-8') as f:
            f.write(dummy_input_content)

        input_params = GeophiresInputParameters(from_file_path=dummy_input_path, params={'Baz': 'Quux', 'Quuz': 2})

        # New combined input file is created when params are provided
        self.assertIsNot(dummy_input_path.absolute(), input_params.as_file_path().absolute())

        with open(dummy_input_path, encoding='UTF-8') as f:
            # Ensure original input file is not modified
            self.assertEqual(dummy_input_content, f.read())

        with open(input_params.as_file_path(), encoding='UTF-8') as f:
            self.assertEqual('Foo, Bar\nBaz, Qux\nBaz, Quux\nQuuz, 2\n', f.read())

    def test_input_file_comments(self):
        result = GeophiresXClient().get_geophires_result(
            GeophiresInputParameters(from_file_path=self._get_test_file_path('input_comments.txt'))
        )
        self.assertIsNotNone(result)

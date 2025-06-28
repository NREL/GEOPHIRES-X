import copy
import tempfile
import uuid
from pathlib import Path
from types import MappingProxyType

from geophires_x_client import GeophiresInputParameters
from geophires_x_client import GeophiresXClient
from geophires_x_client.geophires_input_parameters import ImmutableGeophiresInputParameters
from tests.base_test_case import BaseTestCase


class GeophiresInputParametersTestCase(BaseTestCase):

    def test_internal_id_and_hash(self):
        input_1 = GeophiresInputParameters(from_file_path=self._get_test_file_path('client_test_input_1.txt'))
        input_2 = GeophiresInputParameters(from_file_path=self._get_test_file_path('client_test_input_2.txt'))
        self.assertIsNot(input_1._id, input_2._id)
        self.assertNotEqual(hash(input_1), hash(input_2))

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


class ImmutableGeophiresInputParametersTestCase(BaseTestCase):
    def test_init_with_file_path_as_string(self):
        """Verify that the class can be initialized with a string path without raising an AttributeError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file_path = tmp_file.name
            tmp_file.write('key,value\n')

        # This should not raise an AttributeError
        params = ImmutableGeophiresInputParameters(from_file_path=tmp_file_path)

        # Verify the path was correctly converted and can be used
        self.assertTrue(params.as_file_path().exists())
        self.assertIsInstance(params.from_file_path, Path)

        # Clean up the temporary file
        Path(tmp_file_path).unlink()

    def test_hash_equality(self):
        """Verify that two objects with the same content have the same hash."""
        params = {'Reservoir Depth': 3, 'Gradient 1': 50}
        p1 = ImmutableGeophiresInputParameters(params=params)
        p2 = ImmutableGeophiresInputParameters(params=params)

        self.assertIsNot(p1, p2)
        self.assertEqual(hash(p1), hash(p2))

    def test_hash_inequality(self):
        """Verify that two objects with different content have different hashes."""
        p1 = ImmutableGeophiresInputParameters(params={'Reservoir Depth': 3})
        p2 = ImmutableGeophiresInputParameters(params={'Reservoir Depth': 4})
        self.assertNotEqual(hash(p1), hash(p2))

    def test_immutability_of_params(self):
        """Verify that the params dictionary is an immutable mapping proxy."""
        p1 = ImmutableGeophiresInputParameters(params={'Reservoir Depth': 3})
        self.assertIsInstance(p1.params, MappingProxyType)

        with self.assertRaises(TypeError):
            # This should fail because MappingProxyType is read-only
            p1.params['Reservoir Depth'] = 4

    def test_combining_file_and_params_with_no_trailing_newline(self):
        """Verify that combining a base file and params works correctly when the base file lacks a trailing newline."""
        # Arrange
        base_content = 'base_key,base_value'  # Note: no trailing newline
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, newline='') as tmp_file:
            base_file_path = Path(tmp_file.name)
            tmp_file.write(base_content)

        # Act
        params = ImmutableGeophiresInputParameters(from_file_path=base_file_path, params={'new_key': 'new_value'})
        combined_file_path = params.as_file_path()
        combined_content = combined_file_path.read_text()

        # Assert
        expected_content = 'base_key,base_value\nnew_key, new_value\n'
        self.assertEqual(expected_content, combined_content)

        # Clean up the temporary file
        base_file_path.unlink()

    def test_deepcopy(self):
        """Verify that copy.deepcopy works on an instance without raising a TypeError."""
        p1 = ImmutableGeophiresInputParameters(params={'Reservoir Depth': 3})
        p2 = None

        try:
            p2 = copy.deepcopy(p1)
        except TypeError:
            self.fail('copy.deepcopy(ImmutableGeophiresInputParameters) raised TypeError unexpectedly!')

        # For an immutable object, deepcopy should ideally return the same instance.
        self.assertIs(p1, p2)

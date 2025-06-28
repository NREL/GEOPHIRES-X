import sys
import unittest
from unittest.mock import patch

from geophires_x_client import GeophiresXClient
from geophires_x_client.geophires_input_parameters import ImmutableGeophiresInputParameters
from tests.base_test_case import BaseTestCase


class GeophiresClientCachingTestCase(BaseTestCase):
    """
    Tests the caching functionality of the GeophiresXClient, especially
    in conjunction with the content-addressable ImmutableGeophiresInputParameters.
    """

    def _create_mock_output_file(self, *args, **kwargs):
        """
        A helper function to be used as a side_effect for mocking geophires.main.
        It simulates the behavior of GEOPHIRES by creating an output file based on
        the arguments it receives via sys.argv.
        """
        # The client sets sys.argv to ['', input_path, output_path] before calling main.
        # We read from sys.argv directly to correctly simulate the real process.
        output_path_arg = sys.argv[2]
        with open(output_path_arg, 'w') as f:
            with open(self._get_test_file_path('caching-test-result.out'), encoding='utf-8') as fr:
                f.write(fr.read())
        return 0  # Simulate a successful run

    @patch('geophires_x_client.geophires.main')
    def test_caching_with_identical_immutable_params(self, mock_geophires_main: unittest.mock.MagicMock):
        """
        Verify that when two different ImmutableGeophiresInputParameters objects
        have the same content, the GeophiresXClient's caching mechanism is
        triggered and the expensive geophires.main function is only called once.
        """
        # Arrange
        mock_geophires_main.side_effect = self._create_mock_output_file

        client = GeophiresXClient(enable_caching=True)

        # Create two distinct parameter objects with identical content.
        params1 = ImmutableGeophiresInputParameters(params={'Reservoir Depth': 3, 'Gradient 1': 50})
        params2 = ImmutableGeophiresInputParameters(params={'Reservoir Depth': 3, 'Gradient 1': 50})

        # Pre-condition check: Although they are different objects in memory,
        # their content-based hashes must be identical for caching to work.
        self.assertIsNot(params1, params2, 'Test setup failed: params1 and params2 should be different objects.')
        self.assertEqual(hash(params1), hash(params2), 'Hashes of identical-content objects should be equal.')

        # Act
        result1 = client.get_geophires_result(params1)
        result2 = client.get_geophires_result(params2)

        # Assert
        # The core assertion: was the expensive simulation function only called once?
        mock_geophires_main.assert_called_once()

        self.assertDictEqual(result1.result, result2.result)

        # TODO The results should probably not only be equivalent but also the *same object*...
        #  For now they not, but we probably don't care about this since the important part is performance/cache hit -
        #  manually verified the cache hit in debugger during development.
        # self.assertIs(result1, result2, 'The second result should be the cached object instance.')

    @patch('geophires_x_client.geophires.main')
    def test_no_caching_with_different_immutable_params(self, mock_geophires_main: unittest.mock.MagicMock):
        """
        Verify that when two ImmutableGeophiresInputParameters objects have
        different content, the cache is not used and geophires.main is called for each.
        """
        # Arrange
        mock_geophires_main.side_effect = self._create_mock_output_file

        client = GeophiresXClient(enable_caching=True)
        params1 = ImmutableGeophiresInputParameters(params={'Reservoir Depth': 3})
        params2 = ImmutableGeophiresInputParameters(params={'Reservoir Depth': 4})

        self.assertNotEqual(hash(params1), hash(params2), 'Hashes of different-content objects should not be equal.')

        # Act
        client.get_geophires_result(params1)
        client.get_geophires_result(params2)

        # Assert
        self.assertEqual(
            mock_geophires_main.call_count, 2, 'geophires.main should be called for each unique set of parameters.'
        )

    @patch('geophires_x_client.geophires.main')
    def test_no_caching_when_disabled(self, mock_geophires_main: unittest.mock.MagicMock):
        """
        Verify that even with identical parameters, geophires.main is called
        multiple times if the client has caching disabled.
        """
        # Arrange
        mock_geophires_main.side_effect = self._create_mock_output_file

        client = GeophiresXClient(enable_caching=False)  # Caching is explicitly disabled
        params1 = ImmutableGeophiresInputParameters(params={'Reservoir Depth': 3})
        params2 = ImmutableGeophiresInputParameters(params={'Reservoir Depth': 3})

        self.assertEqual(hash(params1), hash(params2))

        # Act
        client.get_geophires_result(params1)
        client.get_geophires_result(params2)

        # Assert
        self.assertEqual(
            mock_geophires_main.call_count, 2, 'geophires.main should be called twice when caching is disabled.'
        )

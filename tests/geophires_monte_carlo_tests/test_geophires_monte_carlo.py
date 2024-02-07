import os
import unittest
from pathlib import Path

from geophires_monte_carlo import GeophiresMonteCarloClient
from geophires_monte_carlo import MonteCarloRequest
from geophires_monte_carlo import MonteCarloResult
from geophires_monte_carlo import SimulationProgram


class GeophiresMonteCarloTestCase(unittest.TestCase):
    def test_geophires_monte_carlo(self):
        client = GeophiresMonteCarloClient()

        def get_path(arg_file):
            return Path(Path(os.path.abspath(__file__)).parent, arg_file).absolute()

        result: MonteCarloResult = client.get_monte_carlo_result(
            MonteCarloRequest(
                SimulationProgram.GEOPHIRES, get_path('example1.txt'), get_path('MC_GEOPHIRES_Settings_file.txt')
            )
        )
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()

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
            test_dir: Path = Path(os.path.abspath(__file__)).parent
            return Path(test_dir, arg_file).absolute()

        result: MonteCarloResult = client.get_monte_carlo_result(
            MonteCarloRequest(
                SimulationProgram.GEOPHIRES,
                get_path('example1.txt'),
                get_path('MC_GEOPHIRES_Settings_file.txt'),
            )
        )
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.output_file_path)

        with open(result.output_file_path) as f:
            result_content = '\n'.join(f.readlines())
            self.assertIn('Electricity', result_content)


if __name__ == '__main__':
    unittest.main()

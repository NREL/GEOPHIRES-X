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

        result: MonteCarloResult = client.get_monte_carlo_result(
            MonteCarloRequest(
                SimulationProgram.GEOPHIRES,
                self._get_arg_file_path('GEOPHIRES-example1.txt'),
                self._get_arg_file_path('MC_GEOPHIRES_Settings_file.txt'),
            )
        )
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.output_file_path)

        with open(result.output_file_path) as f:
            result_content = '\n'.join(f.readlines())
            self.assertIn('Electricity', result_content)

    @unittest.skip(reason='FIXME: MC HIP result parsing is broken')
    def test_hip_ra_monte_carlo(self):
        client = GeophiresMonteCarloClient()

        result: MonteCarloResult = client.get_monte_carlo_result(
            MonteCarloRequest(
                SimulationProgram.HIP_RA,
                self._get_arg_file_path('HIP-example1.txt'),
                self._get_arg_file_path('MC_HIP_Settings_file.txt'),
            )
        )
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.output_file_path)

        with open(result.output_file_path) as f:
            result_content = '\n'.join(f.readlines())
            self.assertIn('Electricity', result_content)

    def _get_arg_file_path(self, arg_file):
        test_dir: Path = Path(os.path.abspath(__file__)).parent
        return Path(test_dir, arg_file).absolute()


if __name__ == '__main__':
    unittest.main()

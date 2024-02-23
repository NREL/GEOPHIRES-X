import json
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
            result_content = f.read()
            self.assertIn(
                'Average Net Electricity Production, Average Production Temperature, Average Annual Total Electricity Generation, Gradient 1, Reservoir Temperature, Utilization Factor, Ambient Temperature',
                result_content,
            )
            # TODO test actual results/content

        with open(result.json_output_file_path) as f:
            json_content = f.read()
            self.assertIsNotNone(json_content)
            result_json_obj = json.loads(json_content)
            self.assertIsNotNone(result_json_obj)
            for output in [
                'Average Annual Total Electricity Generation',
                'Average Production Temperature',
                'Average Net Electricity Production',
            ]:
                self.assertIn(output, result_json_obj)
                for stat in ['average', 'maximum', 'mean', 'median', 'minimum', 'standard deviation']:
                    self.assertIn(stat, result_json_obj[output])
                    self.assertIs(type(result_json_obj[output][stat]), float)

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

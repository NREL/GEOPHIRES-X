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

        input_file_path: Path = self._get_arg_file_path('GEOPHIRES-example1.txt')
        mc_settings_file_path: Path = self._get_arg_file_path('MC_GEOPHIRES_Settings_file.txt')
        result: MonteCarloResult = client.get_monte_carlo_result(
            MonteCarloRequest(
                SimulationProgram.GEOPHIRES,
                input_file_path,
                mc_settings_file_path,
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

        self.assertIn('input', result.result)
        with open(input_file_path) as f:
            self.assertEqual(f.read(), result.result['input']['input_file_content'])

        with open(mc_settings_file_path) as mcf:
            self.assertEqual(mcf.read(), result.result['input']['monte_carlo_settings_file_content'])

        self.assertIn('output', result.result)

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

            self.assertDictEqual(result_json_obj, result.result['output'])

    def test_monte_carlo_result_ordering(self):
        client = GeophiresMonteCarloClient()

        input_file_path: Path = self._get_arg_file_path('GEOPHIRES-example_SHR-2.txt')
        mc_settings_file_path: Path = self._get_arg_file_path('MC_GEOPHIRES_Settings_file-2.txt')
        result: MonteCarloResult = client.get_monte_carlo_result(
            MonteCarloRequest(
                SimulationProgram.GEOPHIRES,
                input_file_path,
                mc_settings_file_path,
            )
        )
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.output_file_path)

        with open(result.json_output_file_path) as f:
            json_content = f.read()
            self.assertIsNotNone(json_content)
            result_json_obj = json.loads(json_content)
            self.assertIsNotNone(result_json_obj)
            for output in [
                'Electricity breakeven price',
                'Average Net Electricity Production',
                'Project NPV',
                'Total capital costs',
                'Average Production Temperature',
                'Reservoir hydrostatic pressure',
            ]:
                self.assertIn(output, result_json_obj)
                for stat in ['average', 'maximum', 'mean', 'median', 'minimum', 'standard deviation']:
                    self.assertIn(stat, result_json_obj[output])
                    self.assertIs(type(result_json_obj[output][stat]), float)

            avg_prod_tmp = result_json_obj['Average Production Temperature']['average']

            # Note that the results aren't deterministic and this temp range isn't *strictly* guaranteed to hold...
            # However in practice it probably should; if it doesn't - i.e. tests randomly fail here more than once in
            # a super-blue moon - then the values here can be adjusted to be inclusive of some reasonable range.
            # The key point is that this test is asserting is that the value is something that is in the ballpark of a
            # plausible temperature value, and hopefully not mixed up with some other output (as was occurring prior to
            # https://github.com/NREL/GEOPHIRES-X/issues/132 being addressed)
            self.assertGreater(avg_prod_tmp, 280)
            self.assertLess(avg_prod_tmp, 420)

            self.assertGreater(result_json_obj['Reservoir hydrostatic pressure']['average'], 60000)
            self.assertLess(result_json_obj['Total capital costs']['average'], 1000)

            self.assertDictEqual(result_json_obj, result.result['output'])

    def test_hip_ra_monte_carlo(self):
        client = GeophiresMonteCarloClient()

        result: MonteCarloResult = client.get_monte_carlo_result(
            MonteCarloRequest(
                SimulationProgram.HIP_RA,
                self._get_arg_file_path('HIP-example1.txt'),
                self._get_arg_file_path('MC_HIP_Settings_file.txt'),
                self._get_arg_file_path('MC_HIP_Result.txt'),
            )
        )
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.output_file_path)

        with open(result.output_file_path) as f:
            result_content = '\n'.join(f.readlines())
            self.assertIn('Electricity', result_content)

        with open(result.json_output_file_path) as f:
            json_result = json.loads(f.read())
            self.assertIn('Producible Electricity', json_result)
            self.assertLess(json_result['Producible Electricity']['median'], 1000)
            self.assertGreater(json_result['Producible Electricity']['median'], 20)

    def _get_arg_file_path(self, arg_file):
        test_dir: Path = Path(os.path.abspath(__file__)).parent
        return Path(test_dir, arg_file).absolute()


if __name__ == '__main__':
    unittest.main()

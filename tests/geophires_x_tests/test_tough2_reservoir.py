from pathlib import Path

from tests.base_test_case import BaseTestCase

# Ruff disabled because imports are order-dependent
# ruff: noqa: I001
from geophires_x.Model import Model
from geophires_x.Parameter import ParameterEntry


# ruff: noqa: I001
from geophires_x.TOUGH2Reservoir import TOUGH2Reservoir
from geophires_x.OptionList import ReservoirModel
from geophires_x_client import GeophiresInputParameters

import sys
import os


class Tough2ReservoirTestCase(BaseTestCase):
    def _new_model_with_tough2_reservoir(self, input_file=None) -> Model:
        stash_cwd = Path.cwd()
        stash_sys_argv = sys.argv

        sys.argv = ['']

        if input_file is not None:
            sys.argv.append(input_file)

        m = Model(enable_geophires_logging_config=False)
        m.InputParameters['Reservoir Model'] = ParameterEntry(
            Name='Reservoir Model', sValue=str(ReservoirModel.TOUGH2_SIMULATOR.int_value)
        )
        m.reserv = TOUGH2Reservoir(m)

        if input_file is not None:
            m.read_parameters()

        sys.argv = stash_sys_argv
        os.chdir(stash_cwd)

        return m

    def test_read_inputs(self):
        base_params = GeophiresInputParameters(
            from_file_path=self._get_test_file_path('../examples/example1.txt'),
            params={
                'Reservoir Model': ReservoirModel.TOUGH2_SIMULATOR.int_value,
            },
        )
        model = self._new_model_with_tough2_reservoir(input_file=base_params.as_file_path())
        self.assertEqual(model.reserv.tough2_executable_path.value, 'xt2_eos1.exe')

        params_custom_exe = GeophiresInputParameters(
            from_file_path=self._get_test_file_path('../examples/example1.txt'),
            params={
                'Reservoir Model': ReservoirModel.TOUGH2_SIMULATOR.int_value,
                'TOUGH2 Executable Path': 'C:\\Users\\my-geophires-project\\tough3-eos1.exe',
            },
        )
        model = self._new_model_with_tough2_reservoir(input_file=params_custom_exe.as_file_path())
        reservoir: TOUGH2Reservoir = model.reserv
        self.assertEqual(reservoir.tough2_executable_path.value, 'C:\\Users\\my-geophires-project\\tough3-eos1.exe')

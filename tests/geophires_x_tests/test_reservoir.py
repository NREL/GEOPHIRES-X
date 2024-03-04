import os
import sys
from pathlib import Path

from pint.facets.plain import PlainQuantity

from base_test_case import BaseTestCase
from geophires_x.GeoPHIRESUtils import static_pressure_MPa
from geophires_x.Model import Model
from geophires_x.Reservoir import Reservoir


class ReservoirTestCase(BaseTestCase):
    def test_lithostatic_pressure(self):
        p = static_pressure_MPa(2700, 3000)
        self.assertEqual(79.433865, p)

    def test_reservoir_lithostatic_pressure(self):
        reservoir = Reservoir(self._new_model())
        p: PlainQuantity = reservoir.lithostatic_pressure()

        # Assumes Reservoir default values of rho=2700, depth=3km
        self.assertAlmostEqual(79.433865, p.magnitude, places=3)
        self.assertEqual('megapascal', p.units)

    def _new_model(self, input_file=None) -> Model:
        stash_cwd = Path.cwd()
        stash_sys_argv = sys.argv

        sys.argv = ['']

        if input_file is not None:
            sys.argv.append(input_file)

        m = Model(enable_geophires_logging_config=False)

        if input_file is not None:
            m.read_parameters()

        sys.argv = stash_sys_argv
        os.chdir(stash_cwd)

        return m

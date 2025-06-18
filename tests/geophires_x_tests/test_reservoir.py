import os
import sys
from pathlib import Path

from pint.facets.plain import PlainQuantity

from geophires_x.GeoPHIRESUtils import static_pressure_MPa
from geophires_x.Model import Model
from geophires_x.Reservoir import Reservoir
from geophires_x_client import GeophiresInputParameters
from geophires_x_client import GeophiresXClient
from geophires_x_client import GeophiresXResult
from tests.base_test_case import BaseTestCase


class ReservoirTestCase(BaseTestCase):
    def test_lithostatic_pressure(self):
        p = static_pressure_MPa(2700, 3000)
        self.assertEqual(79.433865, p)

    def test_reservoir_lithostatic_pressure(self):
        reservoir = Reservoir(self._new_model())

        # Assumes Reservoir default values of rho=2700, depth=3km
        assert reservoir.rhorock.quantity() == PlainQuantity(2700.0, 'kilogram / meter ** 3')
        assert reservoir.depth.quantity() == PlainQuantity(3000, 'm')

        p: PlainQuantity = reservoir.lithostatic_pressure()

        self.assertAlmostEqual(79.433865, p.magnitude, places=3)
        self.assertEqual('megapascal', p.units)

    # noinspection PyMethodMayBeStatic
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

    def test_number_of_fractures(self):
        def _get_result(num_fractures: int) -> GeophiresXResult:
            return GeophiresXClient().get_geophires_result(
                GeophiresInputParameters(
                    from_file_path=self._get_test_file_path('generic-egs-case.txt'),
                    params={
                        'Number of Fractures': num_fractures,
                    },
                )
            )

        r = _get_result(10_000)
        self.assertEqual(10_000, r.result['RESERVOIR PARAMETERS']['Number of fractures']['value'])

        max_fracs = 99_999
        self.assertEqual(
            max_fracs, _get_result(max_fracs).result['RESERVOIR PARAMETERS']['Number of fractures']['value']
        )

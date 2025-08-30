from __future__ import annotations

import copy
import os
import sys
from pathlib import Path
from typing import Any

from pint.facets.plain import PlainQuantity

from geophires_x.GeoPHIRESUtils import static_pressure_MPa
from geophires_x.Model import Model
from geophires_x.Reservoir import Reservoir
from geophires_x_client import GeophiresInputParameters
from geophires_x_client import GeophiresXClient
from geophires_x_client import GeophiresXResult
from geophires_x_client import ImmutableGeophiresInputParameters
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

    def test_gringarten_stehfest_precision(self):
        def _log(msg) -> None:
            print(f'[DEBUG][test_gringarten_stehfest_precision] {msg}')

        def _get_result(gringarten_stehfest_precision: int) -> GeophiresXResult:
            return GeophiresXClient(enable_caching=False).get_geophires_result(
                ImmutableGeophiresInputParameters(
                    from_file_path=self._get_test_file_path('generic-egs-case.txt'),
                    params={'Gringarten-Stehfest Precision': gringarten_stehfest_precision},
                )
            )

        _ = _get_result(15)  # warm up any caching
        result_15 = _get_result(15)
        result_8 = _get_result(8)

        def calc_time(r: GeophiresXResult) -> float:
            return r.result['Simulation Metadata']['Calculation Time']['value']

        calc_time_15_sec = calc_time(result_15)
        calc_time_8_sec = calc_time(result_8)

        _log(f'calc_time_15_sec={calc_time_15_sec}, calc_time_8_sec={calc_time_8_sec}')

        self.assertLess(calc_time_8_sec, calc_time_15_sec)

        speedup_pct = ((calc_time_15_sec - calc_time_8_sec) / calc_time_15_sec) * 100
        _log(f'Speedup: {speedup_pct:.2f}%')

        def no_metadata(r: GeophiresXResult) -> dict[str, Any]:
            ret = copy.deepcopy(r.result)
            del ret['Simulation Metadata']
            del ret['metadata']
            return ret

        result_12_nm = no_metadata(_get_result(12))
        result_15_nm = no_metadata(result_15)
        try:
            self.assertDictAlmostEqual(result_15_nm, result_12_nm, percent=1)
        except AssertionError as ae:
            try:
                self.assertDictEqual(result_15_nm, result_12_nm)
            except AssertionError as ae_with_dict_diff:
                raise ae from ae_with_dict_diff

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
                        'Reservoir Volume Option': '1, -- FRAC_NUM_SEP',
                        'Fracture Shape': '3, -- Square',
                        'Fracture Height': 165,
                        'Number of Fractures': num_fractures,
                    },
                )
            )

        def _fractures_lcoe_net(r: GeophiresXResult) -> tuple[int, float, float]:
            return (
                r.result['RESERVOIR PARAMETERS']['Number of fractures']['value'],
                r.result['SUMMARY OF RESULTS']['Electricity breakeven price']['value'],
                r.result['SUMMARY OF RESULTS']['Average Net Electricity Production']['value'],
            )

        fractures, lcoe, net_production = _fractures_lcoe_net(_get_result(10_000))

        self.assertEqual(10_000, fractures)

        self.assertGreater(lcoe, 0)
        self.assertLess(lcoe, 400)

        self.assertGreater(net_production, 0)
        self.assertLess(net_production, 500)

        max_fractures = 99_999
        fractures, lcoe, net_production = _fractures_lcoe_net(_get_result(max_fractures))

        self.assertEqual(max_fractures, fractures)

        self.assertGreater(lcoe, 0)
        self.assertLess(lcoe, 400)

        self.assertGreater(net_production, 0)
        self.assertLess(net_production, 500)

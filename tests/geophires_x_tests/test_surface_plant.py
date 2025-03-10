import os
import sys
from pathlib import Path

import numpy as np

from geophires_x.Model import Model
from tests.base_test_case import BaseTestCase


class SurfacePlantTestCase(BaseTestCase):

    def test_integrate_time_series_slice_1_time_step_per_year(self):
        self._workaround_module_initialization_order_dependency()
        from geophires_x.SurfacePlant import SurfacePlant

        time_steps_per_year = 1
        utilization_factor = 0.9

        def _integrate_slice(series: np.ndarray, _i: int) -> np.float64:
            return SurfacePlant.integrate_time_series_slice(series, _i, time_steps_per_year, utilization_factor)

        plant_lifetime = 20
        ElectricityProduced = [
            456.1403991563267,
            456.1403991563267,
            456.9435504549861,
            457.36358815671883,
            457.6422257879382,
            457.8482065397373,
            458.01033644148254,
            458.1433031993208,
            458.2555647922617,
            458.35241646970593,
            458.4373827710431,
            458.51292228292505,
            458.58081486894883,
            458.6423884476247,
            458.69865878571187,
            458.7504193786508,
            458.7983013143066,
            458.84281435825204,
            458.8843758887934,
            458.9233317382275,
        ]

        NetElectricityProduced = [
            402.39393233698496,
            402.39393233698496,
            403.2023017770401,
            403.6250678276089,
            403.9055150923539,
            404.11283347253067,
            404.2760161602529,
            404.40984628330665,
            404.52283676542146,
            404.6203172528295,
            404.70583517837395,
            404.78186509759365,
            404.8501984341015,
            404.9121717307827,
            404.9688073512418,
            405.020903944086,
            405.0690966955198,
            405.11389868149865,
            405.15572999069246,
            405.19493870111074,
        ]

        TotalkWhProduced = np.zeros(plant_lifetime)
        NetkWhProduced = np.zeros(plant_lifetime)
        for i in range(plant_lifetime):
            TotalkWhProduced[i] = _integrate_slice(ElectricityProduced, i)
            NetkWhProduced[i] = _integrate_slice(NetElectricityProduced, i)

        self.assertAlmostEqual(3194711457.45603, NetkWhProduced[-1], places=3)
        self.assertAlmostEqual(TotalkWhProduced[-2], TotalkWhProduced[-1], delta=308_000)

    def _workaround_module_initialization_order_dependency(self) -> Model:
        stash_cwd = Path.cwd()
        stash_sys_argv = sys.argv

        sys.argv = ['']

        m = Model(enable_geophires_logging_config=False)

        sys.argv = stash_sys_argv
        os.chdir(stash_cwd)

        return m

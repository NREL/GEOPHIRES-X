import os
import sys
from pathlib import Path

from base_test_case import BaseTestCase

# ruff: noqa: I001  # Successful module initialization is dependent on this specific import order.
from geophires_x.Model import Model

from geophires_x.EconomicsSam import calculate_sam_economics, _sig_figs, _CASH_FLOW_PROFILE_KEY
from geophires_x_client import GeophiresInputParameters
from geophires_x_client import GeophiresXClient
from geophires_x_client import GeophiresXResult


class EconomicsSamTestCase(BaseTestCase):

    def _egs_test_file_path(self) -> str:
        return self._get_test_file_path('generic-egs-case-2.txt')

    def _get_result(self, _params) -> GeophiresXResult:
        return GeophiresXClient().get_geophires_result(
            GeophiresInputParameters(
                from_file_path=self._egs_test_file_path(),
                params={'Economic Model': 5, **_params},
            )
        )

    def test_economic_model_single_owner_ppa_sam(self):
        def _lcoe(r: GeophiresXResult) -> float:
            return r.result['SUMMARY OF RESULTS']['Electricity breakeven price']['value']

        def _npv(r: GeophiresXResult) -> float:
            return r.result['ECONOMIC PARAMETERS']['Project NPV']['value']

        base_result = self._get_result({})
        base_lcoe = _lcoe(base_result)
        self.assertGreater(base_lcoe, 6)

        npvs = [_npv(self._get_result({'Starting Electricity Sale Price': x / 100.0})) for x in range(1, 20, 4)]
        for i in range(len(npvs) - 1):
            self.assertLess(npvs[i], npvs[i + 1])

    def test_cashflow(self):
        m: Model = EconomicsSamTestCase._new_model(Path(self._egs_test_file_path()))
        m.read_parameters()
        m.Calculate()

        sam_econ = calculate_sam_economics(m)
        cash_flow = sam_econ[_CASH_FLOW_PROFILE_KEY]
        self.assertIsNotNone(cash_flow)
        self.assertEqual(23, len(cash_flow[0]))

        def get_row(name: str) -> list[float]:
            return next(r for r in cash_flow if r[0] == name)[1:]

        self.assertListEqual(get_row('PPA revenue ($)'), get_row('Total revenue ($)'))

        tic = get_row('Total installed cost ($)')[0]
        self.assertLess(tic, 0)
        self.assertAlmostEqual(get_row('Cash flow from investing activities ($)')[0], tic, places=2)

        self.assertAlmostEqual(get_row('Cash flow from financing activities ($)')[0], -1.0 * tic, places=2)

    def test_only_electricity_end_use_supported(self):
        with self.assertRaises(RuntimeError):
            self._get_result({'End-Use Option': 2})

    def test_sig_figs(self):
        self.assertListEqual(_sig_figs([1.14, 2.24], 2), [1.1, 2.2])
        self.assertListEqual(_sig_figs((1.14, 2.24), 2), [1.1, 2.2])

    @staticmethod
    def _new_model(input_file: Path) -> Model:
        stash_cwd = Path.cwd()
        stash_sys_argv = sys.argv

        sys.argv = ['']

        m = Model(enable_geophires_logging_config=False, input_file=input_file)

        sys.argv = stash_sys_argv
        os.chdir(stash_cwd)

        return m

from base_test_case import BaseTestCase
from geophires_x_client import GeophiresInputParameters
from geophires_x_client import GeophiresXClient
from geophires_x_client import GeophiresXResult


class EconomicsSamTestCase(BaseTestCase):

    def _get_result(self, _params) -> GeophiresXResult:
        return GeophiresXClient().get_geophires_result(
            GeophiresInputParameters(
                from_file_path=self._get_test_file_path('generic-egs-case.txt'),
                # from_file_path=self._get_test_file_path('../examples/Fervo_Project_Cape-3.txt'), # FIXME TEMP
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

    def test_only_electricity_end_use_supported(self):
        with self.assertRaises(RuntimeError):
            self._get_result({'End-Use Option': 2})

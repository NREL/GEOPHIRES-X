from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import numpy as np

from base_test_case import BaseTestCase

# ruff: noqa: I001  # Successful module initialization is dependent on this specific import order.
from geophires_x.Model import Model

# noinspection PyProtectedMember
from geophires_x.EconomicsSam import (
    calculate_sam_economics,
    _sig_figs,
    _SAM_CASH_FLOW_PROFILE_KEY,
    _GEOPHIRES_TO_SAM_PRICING_MODEL_RATE_CONVERSION_CONSTANT,
    get_sam_cash_flow_profile_tabulated_output,
)

# noinspection PyProtectedMember
from geophires_x.EconomicsSamCashFlow import _clean_profile, _is_category_row_label, _is_designator_row_label
from geophires_x_client import GeophiresInputParameters
from geophires_x_client import GeophiresXClient
from geophires_x_client import GeophiresXResult


class EconomicsSamTestCase(BaseTestCase):

    def _egs_test_file_path(self) -> str:
        return self._get_test_file_path('generic-egs-case-2_sam-single-owner-ppa.txt')

    def _get_result(self, _params, file_path=None) -> GeophiresXResult:
        if file_path is None:
            file_path = self._egs_test_file_path()

        return GeophiresXClient().get_geophires_result(
            GeophiresInputParameters(
                from_file_path=file_path,
                params={'Economic Model': 5, **_params},
            )
        )

    def test_economic_model_single_owner_ppa_sam(self):
        def _lcoe(r: GeophiresXResult) -> float:
            return r.result['SUMMARY OF RESULTS']['Electricity breakeven price']['value']

        base_result = self._get_result({})
        base_lcoe = _lcoe(base_result)
        self.assertGreater(base_lcoe, 7)

        ir = base_result.result['ECONOMIC PARAMETERS']['Interest Rate']
        self.assertEqual(ir['value'], 7.0)
        self.assertEqual(ir['unit'], '%')

    def test_drawdown(self):
        r = self._get_result(
            {'Plant Lifetime': 20, 'End-Use Option': 1}, file_path=self._get_test_file_path('../examples/example13.txt')
        )

        cash_flow = r.result['SAM CASH FLOW PROFILE']

        def get_row(name: str) -> list[float]:
            return EconomicsSamTestCase._get_cash_flow_row(cash_flow, name)

        elec_net_kWh = get_row('Electricity to grid net (kWh)')
        self.assertLess(elec_net_kWh[15], elec_net_kWh[14])
        self.assertGreater(elec_net_kWh[16], elec_net_kWh[15])
        self.assertLess(elec_net_kWh[20], elec_net_kWh[16])

    def test_plant_lifetime(self):
        r = self._get_result({'Plant Lifetime': 30})

        cash_flow = r.result['SAM CASH FLOW PROFILE']

        def get_row(name: str) -> list[float]:
            return EconomicsSamTestCase._get_cash_flow_row(cash_flow, name)

        self.assertEqual(32, len(cash_flow[0]))
        self.assertEqual('Year 30', cash_flow[0][-1])
        self.assertEqual(31, len(get_row('Electricity to grid net (kWh)')))

    def test_npv(self):
        def _npv(r: GeophiresXResult) -> float:
            return r.result['ECONOMIC PARAMETERS']['Project NPV']['value']

        inflation = 0.02
        rate_params = [
            {
                'Starting Electricity Sale Price': x / 100.0,
                # Escalation rate must remain constant percent
                'Electricity Escalation Rate Per Year': x
                * inflation
                / 100.0
                / _GEOPHIRES_TO_SAM_PRICING_MODEL_RATE_CONVERSION_CONSTANT,
            }
            for x in range(1, 20, 4)
        ]
        npvs = [_npv(self._get_result(rp)) for rp in rate_params]
        for i in range(len(npvs) - 1):
            self.assertLess(npvs[i], npvs[i + 1])

    def test_electricity_generation_profile(self):
        r = self._get_result({})
        lifetime = r.result['ECONOMIC PARAMETERS']['Project lifetime']['value']

        cash_flow = r.result['SAM CASH FLOW PROFILE']

        def get_row(name: str) -> list[float]:
            return EconomicsSamTestCase._get_cash_flow_row(cash_flow, name)

        geophires_avg_net_gen_GWh = r.result['SURFACE EQUIPMENT SIMULATION RESULTS'][
            'Average Annual Net Electricity Generation'
        ]['value']

        sam_gen_profile = get_row('Electricity to grid net (kWh)')

        # Discrepancy is probably due to windowing and/or rounding effects
        #   (TODO to investigate further when time permits)
        allowed_delta_percent = 15
        self.assertAlmostEqualWithinPercentage(
            geophires_avg_net_gen_GWh,
            np.average(sam_gen_profile) * 1e-6,
            allowed_delta_percent,
        )

        elec_idx = r.result['HEAT AND/OR ELECTRICITY EXTRACTION AND GENERATION PROFILE'][0].index(
            'ELECTRICITY PROVIDED (GWh/year)'
        )
        for i in range(lifetime):
            geophires_elec = r.result['HEAT AND/OR ELECTRICITY EXTRACTION AND GENERATION PROFILE'][1:][i][elec_idx]
            sam_elec = sam_gen_profile[i + 1] * 1e-6
            self.assertAlmostEqual(geophires_elec, sam_elec, places=0)

    def test_cash_flow(self):
        m: Model = EconomicsSamTestCase._new_model(Path(self._egs_test_file_path()))

        sam_econ = calculate_sam_economics(m)
        cash_flow = sam_econ[_SAM_CASH_FLOW_PROFILE_KEY]
        self.assertIsNotNone(cash_flow)

        print(
            get_sam_cash_flow_profile_tabulated_output(
                m,
                # cash_flow,
                # tablefmt='pretty',
                # tablefmt='psql',
                # tablefmt='simple_grid',
                # tablefmt='fancy_grid',
                # headers='keys'
            )
        )

        self.assertEqual(22, len(cash_flow[0]))

        def get_row(name: str) -> list[float]:
            return EconomicsSamTestCase._get_cash_flow_row(cash_flow, name)

        def get_single_value(name: str) -> list[float]:
            return EconomicsSamTestCase._get_cash_flow_row(cash_flow, name)[0]

        self.assertListEqual(get_row('PPA revenue ($)')[:-1], get_row('Total revenue ($)')[:-1])

        tic = get_single_value('Total installed cost ($)')
        self.assertLess(tic, 0)
        self.assertAlmostEqual(get_single_value('Cash flow from investing activities ($)'), tic, places=2)

        self.assertAlmostEqual(get_single_value('Cash flow from financing activities ($)'), -1.0 * tic, places=2)

        self.assertAlmostEqual(
            m.economics.LCOE.value, get_single_value('LCOE Levelized cost of energy nominal (cents/kWh)'), places=2
        )

    @staticmethod
    def _get_cash_flow_row(cash_flow, name):

        return next(
            [GeophiresXResult._get_sam_cash_flow_profile_entry_display_to_entry_val(ed) for ed in r]
            for r in cash_flow
            if r[0] == name
        )[1:]

    def test_only_electricity_end_use_supported(self):
        with self.assertRaises(RuntimeError) as e:
            self._get_result({'End-Use Option': 2})

        self.assertIn('Invalid End-Use Option (Direct-Use Heat)', str(e.exception))

    def test_only_1_construction_year_supported(self):
        with self.assertRaises(RuntimeError) as e:
            self._get_result({'Construction Years': 2})

        self.assertIn('Invalid Construction Years (2)', str(e.exception))
        self.assertIn('SAM_SINGLE_OWNER_PPA only supports Construction Years  = 1.', str(e.exception))

    def test_property_tax_rate(self):
        pt_rate = 0.01
        m: Model = EconomicsSamTestCase._new_model(
            self._egs_test_file_path(), additional_params={'Property Tax Rate': pt_rate}
        )

        sam_econ = calculate_sam_economics(m)
        cash_flow = sam_econ[_SAM_CASH_FLOW_PROFILE_KEY]

        def get_row(name: str):
            return EconomicsSamTestCase._get_cash_flow_row(cash_flow, name)

        ptv_row = get_row('Property tax net assessed value ($)')
        pte_row = get_row('Property tax expense ($)')
        self.assertIsNotNone(pte_row)
        self.assertAlmostEqual(ptv_row[1] * pt_rate, pte_row[1], places=0)  # Assumes 100% property tax basis

    def test_incentives(self):
        def assert_incentives(params, expected_ibi_usd):
            m: Model = EconomicsSamTestCase._new_model(self._egs_test_file_path(), additional_params=params)

            sam_econ = calculate_sam_economics(m)
            cash_flow = sam_econ[_SAM_CASH_FLOW_PROFILE_KEY]

            def get_row(name: str):
                return EconomicsSamTestCase._get_cash_flow_row(cash_flow, name)

            other_ibi = get_row('Other IBI income ($)')[0]
            total_ibi = get_row('Total IBI income ($)')[0]
            self.assertEqual(expected_ibi_usd, other_ibi)
            self.assertEqual(other_ibi, total_ibi)

        assert_incentives({'One-time Grants Etc': 1}, 1_000_000)
        assert_incentives({'Other Incentives': 2.5}, 2_500_000)

        assert_incentives({'One-time Grants Etc': 100, 'Other Incentives': 0.1}, 100_100_000)

    def test_clean_profile(self):
        profile = [
            ['foo', 1, 2, 3],
            [None] * 4,
            ['bar', 4, 5, 6],
            [None] * 4,
            [None] * 4,
            ['baz', 7, 8, 9],
        ]

        clean = _clean_profile(profile)

        self.assertListEqual(
            clean,
            [
                ['foo', 1, 2, 3],
                [None] * 4,
                ['bar', 4, 5, 6],
                [None] * 4,
                ['baz', 7, 8, 9],
            ],
        )

    def test_is_category_row_label(self):
        self.assertTrue(_is_category_row_label('OPERATING ACTIVITIES'))
        self.assertFalse(_is_category_row_label('plus PBI if not available for debt service:'))

    def test_is_designator_row_label(self):
        self.assertTrue(_is_designator_row_label('plus PBI if not available for debt service:'))

    def test_sig_figs(self):
        self.assertListEqual(_sig_figs([1.14, 2.24], 2), [1.1, 2.2])
        self.assertListEqual(_sig_figs((1.14, 2.24), 2), [1.1, 2.2])

    @staticmethod
    def _new_model(input_file: Path, additional_params: dict[str, Any] | None = None, read_and_calculate=True) -> Model:
        if additional_params is not None:
            params = GeophiresInputParameters(from_file_path=input_file, params=additional_params)
            input_file = params.as_file_path()

        stash_cwd = Path.cwd()
        stash_sys_argv = sys.argv

        sys.argv = ['']

        m = Model(enable_geophires_logging_config=False, input_file=input_file)

        sys.argv = stash_sys_argv
        os.chdir(stash_cwd)

        if read_and_calculate:
            m.read_parameters()
            m.Calculate()

        return m

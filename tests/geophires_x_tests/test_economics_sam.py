from __future__ import annotations

import math
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import numpy_financial as npf

from base_test_case import BaseTestCase

# ruff: noqa: I001  # Successful module initialization is dependent on this specific import order.
from geophires_x.Model import Model

# noinspection PyProtectedMember
from geophires_x.EconomicsSam import (
    calculate_sam_economics,
    get_sam_cash_flow_profile_tabulated_output,
    _ppa_pricing_model,
    _get_fed_and_state_tax_rates,
)
from geophires_x.GeoPHIRESUtils import sig_figs

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
        self.assertIsNone(ir)

        rdr = base_result.result['ECONOMIC PARAMETERS']['Real Discount Rate']
        self.assertEqual(rdr['value'], 7.0)
        self.assertEqual(rdr['unit'], '%')

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

        _pricing_conversion_constant = 0.745
        inflation = 0.02
        rate_params = [
            {
                'Starting Electricity Sale Price': x / 100.0,
                # Escalation rate must remain constant percent
                'Electricity Escalation Rate Per Year': x * inflation / 100.0 / _pricing_conversion_constant,
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

        # Discrepancy is probably due to windowing and/or rounding effects,
        #  may merit further investigation when time permits.
        allowed_delta_percent = 5
        self.assertAlmostEqualWithinPercentage(
            geophires_avg_net_gen_GWh,
            np.average(sam_gen_profile) * 1e-6,
            percent=allowed_delta_percent,
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
        cash_flow = sam_econ.sam_cash_flow_profile
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

        def r_0(r):
            if r is not None and len(r) > 0:
                return r[0]

            return None

        return next(
            [GeophiresXResult._get_sam_cash_flow_profile_entry_display_to_entry_val(ed) for ed in r]
            for r in cash_flow
            if r_0(r) == name
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

    def test_ppa_pricing_model(self):
        self.assertListEqual(
            [
                0.15,
                0.15,
                0.154053223,
                0.15810644599999998,
                0.162159669,
                0.166212892,
                0.170266115,
                0.174319338,
                0.17837256099999999,
                0.18242578399999998,
                0.186479007,
                0.19053223,
                0.194585453,
                0.198638676,
                0.202691899,
                0.206745122,
                0.210798345,
                0.214851568,
                0.218904791,
                0.22295801399999998,
            ],
            _ppa_pricing_model(20, 0.15, 1.00, 1, 0.004053223),
        )

    def test_property_tax_rate(self):
        pt_rate = 0.01
        m: Model = EconomicsSamTestCase._new_model(
            self._egs_test_file_path(), additional_params={'Property Tax Rate': pt_rate}
        )

        sam_econ = calculate_sam_economics(m)
        cash_flow = sam_econ.sam_cash_flow_profile

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
            cash_flow = sam_econ.sam_cash_flow_profile

            def get_row(name: str):
                return EconomicsSamTestCase._get_cash_flow_row(cash_flow, name)

            other_ibi = get_row('Other IBI income ($)')[0]
            total_ibi = get_row('Total IBI income ($)')[0]
            self.assertEqual(expected_ibi_usd, other_ibi)
            self.assertEqual(other_ibi, total_ibi)

        assert_incentives({'One-time Grants Etc': 1}, 1_000_000)
        assert_incentives({'Other Incentives': 2.5}, 2_500_000)

        assert_incentives({'One-time Grants Etc': 100, 'Other Incentives': 0.1}, 100_100_000)

    def test_inflation_rate_during_construction(self):
        infl_rate = 0.05
        r_no_infl = self._get_result({'Inflation Rate During Construction': 0})
        r_infl = self._get_result({'Inflation Rate During Construction': infl_rate})

        cash_flow_no_infl = r_no_infl.result['SAM CASH FLOW PROFILE']
        cash_flow_infl = r_infl.result['SAM CASH FLOW PROFILE']

        tic = 'Total installed cost ($)'
        tic_no_infl = EconomicsSamTestCase._get_cash_flow_row(cash_flow_no_infl, tic)[0]
        tic_infl = EconomicsSamTestCase._get_cash_flow_row(cash_flow_infl, tic)[0]

        self.assertAlmostEqual(tic_no_infl * (1 + infl_rate), tic_infl, places=0)

    def test_ptc(self):
        def assert_ptc(params, expected_ptc_usd_per_kWh):
            m: Model = EconomicsSamTestCase._new_model(self._egs_test_file_path(), additional_params=params)

            sam_econ = calculate_sam_economics(m)
            cash_flow = sam_econ.sam_cash_flow_profile

            def get_row(name: str):
                return EconomicsSamTestCase._get_cash_flow_row(cash_flow, name)

            ptc_vals = get_row('Federal PTC income ($)')
            self.assertListAlmostEqual(expected_ptc_usd_per_kWh, ptc_vals, percent=1)

        assert_ptc({}, [0] * 21)

        base_expected = [
            0,
            126447893,
            127031474,
            127215192,
            127324226,
            127400735,
            127459143,
            127506088,
            127545160,
            127578508,
            127607522,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ]

        assert_ptc({'Production Tax Credit Electricity': 0.04}, base_expected)

        inflation_rate = 0.03

        # Ideally this would be calculated from first principles here in the test (approximately: base_expected *
        # an inflation vector with correct offset for PTC escalation year = 2), but this is fine for now.
        inflation_expected = [
            0,
            126447893,
            130207261,
            133575951,
            140056649,
            143325827,
            146578015,
            153007306,
            156242820,
            162662598,
            165889779,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ]

        assert_ptc(
            {
                'Production Tax Credit Electricity': 0.04,
                'Production Tax Credit Inflation Adjusted': True,
                'Inflation Rate': inflation_rate,
            },
            inflation_expected,
        )

        shortened_term_duration_yr = 9
        shortened_term_expected = base_expected.copy()
        shortened_term_expected[shortened_term_duration_yr + 1] = 0
        assert_ptc(
            {'Production Tax Credit Electricity': 0.04, 'Production Tax Credit Duration': 9}, shortened_term_expected
        )

    def test_capacity_factor(self):
        r_90 = self._get_result({'Utilization Factor': 0.9})
        cash_flow_90 = r_90.result['SAM CASH FLOW PROFILE']

        r_20 = self._get_result({'Utilization Factor': 0.2})
        cash_flow_20 = r_20.result['SAM CASH FLOW PROFILE']

        etg = 'Electricity to grid (kWh)'

        etg_90 = EconomicsSamTestCase._get_cash_flow_row(cash_flow_90, etg)
        etg_20 = EconomicsSamTestCase._get_cash_flow_row(cash_flow_20, etg)

        etg_20_expected = [(etg_90_entry / 0.9) * 0.2 for etg_90_entry in etg_90]

        self.assertListAlmostEqual(etg_20_expected, etg_20, percent=1)

    def test_unsupported_econ_params_ignored_with_warning(self):
        is_github_actions = 'CI' in os.environ or 'TOXPYTHON' in os.environ
        try:
            with self.assertLogs(level='INFO') as logs:
                gtr_provided_result = self._get_result({'Gross Revenue Tax Rate': 0.5})

                self.assertHasLogRecordWithMessage(
                    logs,
                    'Gross Revenue Tax Rate provided value (0.5) will be ignored. '
                    '(SAM Economics tax rates are determined from Combined Income Tax Rate and Property Tax Rate.)',
                )
        except AssertionError as ae:
            if is_github_actions:
                # TODO to investigate and fix
                self.skipTest('Skipping due to intermittent failure on GitHub Actions')
            else:
                raise ae

        def _npv(r: GeophiresXResult) -> float:
            return r.result['ECONOMIC PARAMETERS']['Project NPV']['value']

        default_result = self._get_result({})

        self.assertEqual(_npv(default_result), _npv(gtr_provided_result))  # Check GTR is ignored in calculations

        try:
            with self.assertLogs(level='INFO') as logs:
                eir_provided_result = self._get_result({'Inflated Equity Interest Rate': 0.25})

                self.assertHasLogRecordWithMessage(
                    logs,
                    'Inflated Equity Interest Rate provided value (0.25) will be ignored. '
                    '(SAM Economics does not support Inflated Equity Interest Rate.)',
                )
        except AssertionError as ae:
            if is_github_actions:
                # TODO to investigate and fix
                self.skipTest('Skipping due to intermittent failure on GitHub Actions')
            else:
                raise ae

        self.assertEqual(_npv(default_result), _npv(eir_provided_result))  # Check EIR is ignored in calculations

    def test_carbon_calculations(self):
        r = self._get_result(
            {
                'Do Carbon Price Calculations': True,
                'Starting Carbon Credit Value': 0.015,
                'Ending Carbon Credit Value': 0.1,
                'Carbon Escalation Start Year': 5,
                'Carbon Escalation Rate Per Year': 0.01,
                'Units:Total Saved Carbon Production': 'kilotonne',
            }
        )

        ace = r.result['SUMMARY OF RESULTS']['Total Avoided Carbon Emissions']
        self.assertEqual('kilotonne', ace['unit'])
        self.assertAlmostEqualWithinPercentage(27159, ace['value'], percent=20)

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
        self.assertListEqual(sig_figs([1.14, 2.24], 2), [1.1, 2.2])
        self.assertListEqual(sig_figs((1.14, 2.24), 2), [1.1, 2.2])

    def test_get_fed_and_state_tax_rates(self):
        self.assertEqual(([21], [7]), _get_fed_and_state_tax_rates(0.28))
        self.assertEqual(([21], [0]), _get_fed_and_state_tax_rates(0.21))
        self.assertEqual(([21], [9]), _get_fed_and_state_tax_rates(0.3))
        self.assertEqual(([10], [0]), _get_fed_and_state_tax_rates(0.1))

    def test_nan_after_tax_irr(self):
        """
        Verify that After-tax IRRs that would have been calculated as NaN by SAM are instead calculated with
        numpy-financial.irr
        """

        def _irr(_r: GeophiresXResult) -> float:
            return _r.result['ECONOMIC PARAMETERS']['After-tax IRR']['value']

        rate_params = {
            'Electricity Escalation Rate Per Year': 0.00348993288590604,
            'Starting Electricity Sale Price': 0.13,
        }
        r: GeophiresXResult = self._get_result(rate_params)
        after_tax_irr_cash_flow_entries = EconomicsSamTestCase._get_cash_flow_row(
            r.result['SAM CASH FLOW PROFILE'], 'After-tax cumulative IRR (%)'
        )
        sam_after_tax_irr_calc = float(after_tax_irr_cash_flow_entries[-1])

        # Test case condition - we expect SAM to have calculated NaN here. If this assertion fails, adjust params passed
        # to _get_result such that final year of After-tax cumulative IRR is NaN.
        assert math.isnan(sam_after_tax_irr_calc)

        after_tax_cash_flow = EconomicsSamTestCase._get_cash_flow_row(
            r.result['SAM CASH FLOW PROFILE'], 'Total after-tax returns ($)'
        )
        npf_irr = npf.irr(after_tax_cash_flow) * 100.0

        r_irr = _irr(r)
        self.assertFalse(math.isnan(r_irr))
        self.assertAlmostEqual(npf_irr, r_irr, places=2)

    def test_nan_project_payback_period(self):
        def _payback_period(_r: GeophiresXResult) -> float:
            return _r.result['ECONOMIC PARAMETERS']['Project Payback Period']['value']

        never_pays_back_params = {
            'Starting Electricity Sale Price': 0.00001,
            'Ending Electricity Sale Price': 0.00002,
        }
        r: GeophiresXResult = self._get_result(never_pays_back_params)
        self.assertIsNone(_payback_period(r))

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

from __future__ import annotations

import csv
import logging
import os
import re
import sys
import math
from functools import lru_cache
from typing import Any

from PySAM import Singleowner

import geophires_x.Model as Model


@lru_cache(maxsize=12)
def _calculate_sam_economics_cash_flow(model: Model, single_owner: Singleowner) -> list[list[Any]]:
    log = model.logger

    _soo = single_owner.Outputs

    profile = []
    total_duration = model.surfaceplant.plant_lifetime.value + model.surfaceplant.construction_years.value

    # Prefix with 'Year ' partially as workaround for tabulate applying float formatting to ints, possibly related
    # to https://github.com/astanin/python-tabulate/issues/18
    years = [f'Year {y}' for y in list(range(0, total_duration))]

    row_1 = [None] + years
    profile.append(row_1)

    def blank_row() -> None:
        profile.append([None] * (len(years) + 1))

    def category_row(cat_name: str) -> list[Any]:
        cr = [cat_name] + [None] * len(years)
        profile.append(cr)
        return cr

    def designator_row(designator: str):
        dsr = [designator] + [None] * len(years)
        profile.append(dsr)

    def get_data_adjust_func(row_name: str):
        def rnd(x):
            return round(x, 2)

        if row_name.endswith('($)'):

            def rnd(x):
                return round(x)

        def adj(x_):
            if isinstance(x_, str):
                return x_
            else:
                if math.isnan(x_):
                    return 'NaN'

                return rnd(x_)

        return adj

    def data_row(row_name: str, output_data: Any | None = None) -> list[Any]:
        if output_data is None:
            # TODO output_data should not be passed if present in _get_output
            output_data = _get_single_owner_output(_soo, row_name)

        if output_data is None:
            log.error(f'No output data for {row_name}')

            # TODO/WIP - skip ambiguous mapping for now
            # output_data = ['undefined'] * len(years)
            return

        adjust = get_data_adjust_func(row_name)

        dr = [row_name] + [adjust(d) for d in output_data]  # TODO revisit this to audit for precision concerns
        profile.append(dr)
        return dr

    def single_value_row(row_name: str, single_value: float | None = None) -> list[Any]:
        if single_value is None:
            # TODO single_value should not be passed if present in _get_output
            single_value = _get_single_owner_output(_soo, row_name)

        if single_value is None:
            log.error(f'No output data for {row_name}')

            # TODO/WIP - skip ambiguous mapping for now
            # single_value = 'undefined'
            return

        svr = (
            [row_name] + [get_data_adjust_func(row_name)(single_value)] + [None] * (len(years) - 1)
        )  # TODO revisit this to audit for precision concerns
        profile.append(svr)
        return svr

    with open(_get_file_path('sam_economics/sam-cash-flow-table.csv'), encoding='utf-8') as f:
        cft_reader = csv.reader(f)

        lines = []
        for _line in cft_reader:
            lines.append(_line)

        lines = lines[1:]  # exclude header row

        def is_only_commas(s: str) -> bool:
            # TODO this is a silly way to test whether entries in row are None
            return re.match(r'^,+$', s) is not None

        for line in lines:
            if is_only_commas(','.join(line)):
                blank_row()
                continue

            line_entries = line
            row_label = line_entries[0]

            # Some row labels have seemingly-erroneous extra spaces e.g.  `Reserves debt service disbursement  ($)`
            row_label = re.sub(r'\s+', ' ', row_label)

            if row_label == '':
                blank_row()
                continue

            if _is_designator_row_label(row_label):
                # designator_row(row_label)
                # TODO/WIP - skip designator rows because they may be incorrect until all output properties have been
                # mapped.
                continue

            if _is_category_row_label(row_label):
                category_row(row_label)
                continue

            if is_only_commas(','.join(line_entries[3:])):
                single_value_row(row_label)
            else:
                data_row(row_label)

    if all([it is None for it in profile[-1]]):
        profile = profile[:-1]  # trim last line if blank

    return _clean_profile(profile)


def _is_category_row_label(row_label: str) -> bool:
    return re.match(r'^([A-Z \(\)\-\:]+)$', row_label) or re.match(r'^([A-Z][A-Za-z \-]+\:)$', row_label)


def _is_designator_row_label(row_label: str) -> bool:
    return row_label == 'plus PBI if not available for debt service:' or re.match(r'^[a-z]+:$', row_label) is not None


def _clean_profile(profile: list[list[Any]]) -> list[list[Any]]:
    # Collapse consecutive blank rows
    previous_line_was_blank = False
    profile_cleaned = []
    for pl in profile:
        is_blank = all(it is None for it in pl)
        if not (is_blank and previous_line_was_blank):
            profile_cleaned.append(pl)
        previous_line_was_blank = is_blank

    return profile_cleaned


_SINGLE_OWNER_OUTPUT_PROPERTIES = {
    'Electricity to grid (kWh)': 'cf_energy_sales',
    'Electricity from grid (kWh)': 'cf_energy_purchases',
    'Electricity to grid net (kWh)': 'cf_energy_net',
    'PPA price (cents/kWh)': 'cf_ppa_price',
    'PPA revenue ($)': 'cf_energy_value',
    'Salvage value ($)': 'cf_net_salvage_value',
    'Total revenue ($)': 'cf_revenue_dispatch1',
    'O&M fixed expense ($)': 'cf_om_fixed_expense',
    'Property tax expense ($)': 'cf_property_tax_expense',
    'Total operating expenses ($)': 'cf_operating_expenses',
    'EBITDA ($)': 'cf_ebitda',
    'Debt interest payment ($)': 'cf_debt_payment_interest',
    'Cash flow from operating activities ($)': 'cf_project_operating_activities',
    'Total installed cost ($)': lambda _soo: -1.0 * _soo.cost_installed,
    'Purchase of property ($)': 'purchase_of_property',
    'Cash flow from investing activities ($)': 'cf_project_investing_activities',
    'Issuance of equity ($)': 'issuance_of_equity',
    'Size of debt ($)': 'size_of_debt',
    'Debt principal payment ($)': 'cf_debt_payment_principal',
    'Cash flow from financing activities ($)': 'cf_project_financing_activities',
    'Cash flow from operating activities ($)': 'cf_project_operating_activities',
    'Cash flow from investing activities ($)': 'cf_project_investing_activities',
    'Cash flow from financing activities ($)': 'cf_project_financing_activities',
    'Total pre-tax cash flow ($)': 'cf_pretax_cashflow',
    'Issuance of equity ($)': 'issuance_of_equity',
    'Total pre-tax cash flow ($)': 'cf_pretax_cashflow',
    'Total pre-tax returns ($)': 'cf_project_return_pretax',
    'Federal ITC total income ($)': 'cf_itc_fed',
    'Federal PTC income ($)': 'cf_ptc_fed',
    'Federal tax benefit (liability) ($)': 'cf_fedtax',
    'State ITC total income ($)': 'cf_itc_sta',
    'State PTC income ($)': 'cf_ptc_sta',
    'State tax benefit (liability) ($)': 'cf_statax',
    'Total after-tax returns ($)': 'cf_project_return_aftertax',
    'After-tax cumulative IRR (%)': 'cf_project_return_aftertax_irr',
    'After-tax cumulative NPV ($)': 'cf_project_return_aftertax_npv',
    'Annual costs ($)': 'cf_annual_costs',
    'Present value of annual costs ($)': 'npv_annual_costs',
    'Present value of annual energy nominal ($)': 'npv_energy_nom',
    'LCOE Levelized cost of energy nominal (cents/kWh)': 'lcoe_nom',
    'Present value of PPA revenue ($)': 'npv_ppa_revenue',
    'Present value of annual energy nominal ($)': 'npv_energy_nom',
    'LPPA Levelized PPA price nominal (cents/kWh)': 'lppa_nom',
    'Curtailment payment revenue ($)': 'cf_curtailment_value',
    'Capacity payment revenue ($)': 'cf_capacity_payment',
    'Property tax net assessed value ($)': 'cf_property_tax_assessed_value',
    'O&M production-based expense ($)': 'cf_om_production_expense',
    'O&M capacity-based expense ($)': 'cf_om_capacity_expense',
    'Fuel expense ($)': 'cf_om_fuel_expense',
    'Electricity purchase ($)': 'cf_energy_purchases',
    'Insurance expense ($)': 'cf_insurance_expense',
    'Interest earned on reserves ($)': 'cf_reserve_interest',
    'Debt up-front fee ($)': 'cost_debt_upfront',
    'Debt closing costs ($)': 'cost_financing',
    'Debt balance ($)': 'cf_debt_balance',
    'Debt total payment ($)': 'cf_debt_payment_total',
    'Federal income tax rate (frac)': 'cf_federal_tax_frac',
    'Cash available for debt service (CAFDS) ($)': 'cf_cash_for_ds',
    'DSCR (pre-tax)': 'cf_pretax_dscr',
    'Net capital cost ($)': 'adjusted_installed_cost',
    'Federal taxable CBI income ($)': 'cbi_fedtax_total',
    'State taxable CBI income ($)': 'cbi_statax_total',
    'Total CBI income ($)': 'cbi_total',
    'Federal CBI income ($)': 'cbi_total_fed',
    'Other CBI income ($)': 'cbi_total_oth',
    'State CBI income ($)': 'cbi_total_sta',
    'Utility CBI income ($)': 'cbi_total_uti',
    'After-tax cash flow ($)': 'cf_after_tax_cash_flow',
    'After-tax annual costs ($)': 'cf_after_tax_net_equity_cost_flow',
    'Annual storage costs ($)': 'cf_annual_cost_lcos',
    'Annual storage discharge (kWh)': 'cf_annual_discharge_lcos',
    'Battery replacement cost ($)': 'cf_battery_replacement_cost',
    'Battery replacement cost schedule ($)': 'cf_battery_replacement_cost_schedule',
    'Annual cost to charge from grid ($)': 'cf_charging_cost_grid',
    'Annual cost to charge from grid (monthly) ($)': 'cf_charging_cost_grid_month',
    'Annual cost to charge from system ($)': 'cf_charging_cost_pv',
    'Cumulative simple payback with expenses ($)': 'cf_cumulative_payback_with_expenses',
    'Cumulative simple payback without expenses ($)': 'cf_cumulative_payback_without_expenses',
    'Interest payment ($)': 'cf_debt_payment_interest',
    'Principal payment ($)': 'cf_debt_payment_principal',
    'Total P&I debt payment ($)': 'cf_debt_payment_total',
    'Deductible expenses ($)': 'cf_deductible_expenses',
    'Discounted costs ($)': 'cf_discounted_costs',
    'Cumulative discounted payback ($)': 'cf_discounted_cumulative_payback',
    'Discounted payback ($)': 'cf_discounted_payback',
    'Discounted savings ($)': 'cf_discounted_savings',
    'Effective income tax rate (frac)': 'cf_effective_tax_frac',
    'Electricity net generation (kWh)': 'cf_energy_net',
    'Electricity from grid to system (kWh)': 'cf_energy_purchases',
    'Electricity generation (kWh)': 'cf_energy_sales',
    'Value of electricity savings ($)': 'cf_energy_value',
    'Electricity generated without the battery or curtailment (kWh)': 'cf_energy_without_battery',
    'Federal depreciation schedule (%)': 'cf_fed_depr_sched',
    'Federal depreciation ($)': 'cf_fed_depreciation',
    'Federal incentive income less deductions ($)': 'cf_fed_incentive_income_less_deductions',
    'Federal tax savings ($)': 'cf_fed_tax_savings',
    'Federal taxable incentive income ($)': 'cf_fed_taxable_incentive_income',
    'Federal taxable income less deductions ($)': 'cf_fed_taxable_income_less_deductions',
    'Fuel cell replacement cost ($)': 'cf_fuelcell_replacement_cost',
    'Fuel cell replacement cost schedule ($/kW)': 'cf_fuelcell_replacement_cost_schedule',
    'Federal ITC amount income ($)': 'cf_itc_fed_amount',
    'Federal ITC percent income ($)': 'cf_itc_fed_percent_amount',
    'State ITC amount income ($)': 'cf_itc_sta_amount',
    'State ITC percent income ($)': 'cf_itc_sta_percent_amount',
    'Total ITC income ($)': 'cf_itc_total',
    'Land lease expense ($)': 'cf_land_lease_expense',
    'Number of periods in cash flow': 'cf_length',
    'Net salvage value ($)': 'cf_net_salvage_value',
    'NTE Not to exceed (cents/kWh)': 'cf_nte',
    'Annual cost for battery capacity based maintenance ($)': 'cf_om_batt_capacity_expense',
    'Annual fixed cost for battery maintenance ($)': 'cf_om_batt_fixed_expense',
    'O&M battery capacity-based expense ($)': 'cf_om_capacity1_expense',
    'O&M fuel cell capacity-based expense ($)': 'cf_om_capacity2_expense',
    'O&M battery fixed expense ($)': 'cf_om_fixed1_expense',
    'O&M fuel cell fixed expense ($)': 'cf_om_fixed2_expense',
    'Feedstock biomass expense ($)': 'cf_om_opt_fuel_1_expense',
    'Feedstock coal expense ($)': 'cf_om_opt_fuel_2_expense',
    'O&M battery production-based expense ($)': 'cf_om_production1_expense',
    'O&M fuel cell production-based expense ($)': 'cf_om_production2_expense',
    'Total operating expense ($)': 'cf_operating_expenses',
    'Parasitic load costs ($)': 'cf_parasitic_cost',
    'Simple payback with expenses ($)': 'cf_payback_with_expenses',
    'Simple payback without expenses ($)': 'cf_payback_without_expenses',
    'Federal taxable PBI income ($)': 'cf_pbi_fedtax_total',
    'State taxable PBI income ($)': 'cf_pbi_statax_total',
    'Total PBI income ($)': 'cf_pbi_total',
    'Federal PBI income ($)': 'cf_pbi_total_fed',
    'Other PBI income ($)': 'cf_pbi_total_oth',
    'State PBI income ($)': 'cf_pbi_total_sta',
    'Utility PBI income ($)': 'cf_pbi_total_uti',
    'Annual battery salvage value costs ($)': 'cf_salvage_cost_lcos',
    'Total tax savings (federal and state) ($)': 'cf_sta_and_fed_tax_savings',
    'State depreciation schedule (%)': 'cf_sta_depr_sched',
    'State depreciation ($)': 'cf_sta_depreciation',
    'State incentive income less deductions ($)': 'cf_sta_incentive_income_less_deductions',
    'State tax savings ($)': 'cf_sta_tax_savings',
    'State taxable incentive income ($)': 'cf_sta_taxable_incentive_income',
    'State taxable income less deductions ($)': 'cf_sta_taxable_income_less_deductions',
    'State income tax rate (frac)': 'cf_state_tax_frac',
    'Value of thermal savings ($)': 'cf_thermal_value',
    'Utility escalation rate': 'cf_util_escal_rate',
    'Real estate value added ($)': 'cf_value_added',
    'Discounted payback period (years)': 'discounted_payback',
    'Effective tax rate (%)': 'effective_tax_rate',
    'Equity ($)': 'first_cost',
    'Federal taxable IBI income ($)': 'ibi_fedtax_total',
    'State taxable IBI income ($)': 'ibi_statax_total',
    'Total IBI income ($)': 'ibi_total',
    'Federal IBI income ($)': 'ibi_total_fed',
    'Other IBI income ($)': 'ibi_total_oth',
    'State IBI income ($)': 'ibi_total_sta',
    'Utility IBI income ($)': 'ibi_total_uti',
    'IRR Internal rate of return ($)': 'irr',
    'Total ITC income ($)': 'itc_total',
    'Federal ITC income ($)': 'itc_total_fed',
    'State ITC income ($)': 'itc_total_sta',
    'LCOE Levelized cost of energy real (cents/kWh)': 'lcoe_real',
    'Levelized federal PTC nominal (cents/kWh)': 'lcoptc_fed_nom',
    'Levelized federal PTC real (cents/kWh)': 'lcoptc_fed_real',
    'Levelized state PTC nominal (cents/kWh)': 'lcoptc_sta_nom',
    'Levelized state PTC real (cents/kWh)': 'lcoptc_sta_real',
    'LCOS Levelized cost of storage nominal (cents/kWh)': 'lcos_nom',
    'LCOS Levelized cost of storage real (cents/kWh)': 'lcos_real',
    'NTE Not to exceed nominal (cents/kWh)': 'lnte_nom',
    'NTE Not to exceed real (cents/kWh)': 'lnte_real',
    'Debt ($)': 'loan_amount',
    'Nominal discount rate (%)': 'nominal_discount_rate',
    'NPV Net present value ($)': 'npv',
    'Present value of annual storage costs ($)': 'npv_annual_costs_lcos',
    'Present value of annual stored energy (nominal) (kWh)': 'npv_energy_lcos_nom',
    'Present value of annual stored energy (real) (kWh)': 'npv_energy_lcos_real',
    'Payback period (years)': 'payback',
    'Present value of fuel expenses ($)': 'present_value_fuel',
    'Present value of insurance and property tax ($)': 'present_value_insandproptax',
    'Present value of O&M expenses ($)': 'present_value_oandm',
    'Present value of non-fuel O&M expenses ($)': 'present_value_oandm_nonfuel',
    'WACC Weighted average cost of capital': 'wacc',
    'NTE Not to exceed Year 1 (cents/kWh)': 'year1_nte',
    'Initial cost less cash incentives ($)': 'adjusted_installed_cost',  # Singleowner
    'IRR at end of analysis period (%)': 'analysis_period_irr',  # Singleowner
    'Reserves debt service disbursement ($)': 'cf_disbursement_debtservice',  # Singleowner
    'Reserves major equipment 1 disbursement ($)': 'cf_disbursement_equip1',  # Singleowner
    'Reserves major equipment 2 disbursement ($)': 'cf_disbursement_equip2',  # Singleowner
    'Reserves major equipment 3 disbursement ($)': 'cf_disbursement_equip3',  # Singleowner
    'Reserves working capital disbursement ($)': 'cf_disbursement_om',  # Singleowner
    'Reserves receivables disbursement ($)': 'cf_disbursement_receivables',  # Singleowner
    'Electricity curtailed (kWh)': 'cf_energy_curtailed',  # Singleowner
    'Energy produced by year in April (kWh)': 'cf_energy_sales_apr',  # Singleowner
    'Energy produced by year in August (kWh)': 'cf_energy_sales_aug',  # Singleowner
    'Energy produced by year in December (kWh)': 'cf_energy_sales_dec',  # Singleowner
    'Energy produced by year in TOD period 1 (kWh)': 'cf_energy_sales_dispatch1',  # Singleowner
    'Energy produced by year in TOD period 2 (kWh)': 'cf_energy_sales_dispatch2',  # Singleowner
    'Energy produced by year in TOD period 3 (kWh)': 'cf_energy_sales_dispatch3',  # Singleowner
    'Energy produced by year in TOD period 4 (kWh)': 'cf_energy_sales_dispatch4',  # Singleowner
    'Energy produced by year in TOD period 5 (kWh)': 'cf_energy_sales_dispatch5',  # Singleowner
    'Energy produced by year in TOD period 6 (kWh)': 'cf_energy_sales_dispatch6',  # Singleowner
    'Energy produced by year in TOD period 7 (kWh)': 'cf_energy_sales_dispatch7',  # Singleowner
    'Energy produced by year in TOD period 8 (kWh)': 'cf_energy_sales_dispatch8',  # Singleowner
    'Energy produced by year in TOD period 9 (kWh)': 'cf_energy_sales_dispatch9',  # Singleowner
    'Energy produced by year in February (kWh)': 'cf_energy_sales_feb',  # Singleowner
    'Energy produced by year in January (kWh)': 'cf_energy_sales_jan',  # Singleowner
    'Energy produced by year in July (kWh)': 'cf_energy_sales_jul',  # Singleowner
    'Energy produced by year in June (kWh)': 'cf_energy_sales_jun',  # Singleowner
    'Energy produced by year in March (kWh)': 'cf_energy_sales_mar',  # Singleowner
    'Energy produced by year in May (kWh)': 'cf_energy_sales_may',  # Singleowner
    'Energy produced in Year 1 by month for TOD period 1 (kWh)': 'cf_energy_sales_monthly_firstyear_TOD1',
    # Singleowner
    'Energy produced in Year 1 by month for TOD period 2 (kWh)': 'cf_energy_sales_monthly_firstyear_TOD2',
    # Singleowner
    'Energy produced in Year 1 by month for TOD period 3 (kWh)': 'cf_energy_sales_monthly_firstyear_TOD3',
    # Singleowner
    'Energy produced in Year 1 by month for TOD period 4 (kWh)': 'cf_energy_sales_monthly_firstyear_TOD4',
    # Singleowner
    'Energy produced in Year 1 by month for TOD period 5 (kWh)': 'cf_energy_sales_monthly_firstyear_TOD5',
    # Singleowner
    'Energy produced in Year 1 by month for TOD period 6 (kWh)': 'cf_energy_sales_monthly_firstyear_TOD6',
    # Singleowner
    'Energy produced in Year 1 by month for TOD period 7 (kWh)': 'cf_energy_sales_monthly_firstyear_TOD7',
    # Singleowner
    'Energy produced in Year 1 by month for TOD period 8 (kWh)': 'cf_energy_sales_monthly_firstyear_TOD8',
    # Singleowner
    'Energy produced in Year 1 by month for TOD period 9 (kWh)': 'cf_energy_sales_monthly_firstyear_TOD9',
    # Singleowner
    'Energy produced by year in November (kWh)': 'cf_energy_sales_nov',  # Singleowner
    'Energy produced by year in October (kWh)': 'cf_energy_sales_oct',  # Singleowner
    'Energy produced by year in September (kWh)': 'cf_energy_sales_sep',  # Singleowner
    'Electricity generated without storage (kWh)': 'cf_energy_without_battery',  # Singleowner
    'Federal depreciation from custom ($)': 'cf_feddepr_custom',  # Singleowner
    'Federal depreciation from 15-yr MACRS ($)': 'cf_feddepr_macrs_15',  # Singleowner
    'Federal depreciation from 5-yr MACRS ($)': 'cf_feddepr_macrs_5',  # Singleowner
    'Federal depreciation from major equipment 1 ($)': 'cf_feddepr_me1',  # Singleowner
    'Federal depreciation from major equipment 2 ($)': 'cf_feddepr_me2',  # Singleowner
    'Federal depreciation from major equipment 3 ($)': 'cf_feddepr_me3',  # Singleowner
    'Federal depreciation from 15-yr straight line ($)': 'cf_feddepr_sl_15',  # Singleowner
    'Federal depreciation from 20-yr straight line ($)': 'cf_feddepr_sl_20',  # Singleowner
    'Federal depreciation from 39-yr straight line ($)': 'cf_feddepr_sl_39',  # Singleowner
    'Federal depreciation from 5-yr straight line ($)': 'cf_feddepr_sl_5',  # Singleowner
    'Total federal tax depreciation ($)': 'cf_feddepr_total',  # Singleowner
    'Federal taxable income without incentives ($)': 'cf_fedtax_income_prior_incentives',  # Singleowner
    'Federal taxable income ($)': 'cf_fedtax_income_with_incentives',  # Singleowner
    'Federal taxable incentives ($)': 'cf_fedtax_taxable_incentives',  # Singleowner
    'Reserves debt service funding ($)': 'cf_funding_debtservice',  # Singleowner
    'Reserves major equipment 1 funding ($)': 'cf_funding_equip1',  # Singleowner
    'Reserves major equipment 2 funding ($)': 'cf_funding_equip2',  # Singleowner
    'Reserves major equipment 3 funding ($)': 'cf_funding_equip3',  # Singleowner
    'Reserves working capital funding ($)': 'cf_funding_om',  # Singleowner
    'Reserves receivables funding ($)': 'cf_funding_receivables',  # Singleowner
    'Number of periods in cashflow': 'cf_length',  # Singleowner
    'Reserve (increase)/decrease debt service ($)': 'cf_project_dsra',  # Singleowner
    'Reserve capital spending major equipment 1 ($)': 'cf_project_me1cs',  # Singleowner
    'Reserve (increase)/decrease major equipment 1 ($)': 'cf_project_me1ra',  # Singleowner
    'Reserve capital spending major equipment 2 ($)': 'cf_project_me2cs',  # Singleowner
    'Reserve (increase)/decrease major equipment 2 ($)': 'cf_project_me2ra',  # Singleowner
    'Reserve capital spending major equipment 3 ($)': 'cf_project_me3cs',  # Singleowner
    'Reserve (increase)/decrease major equipment 3 ($)': 'cf_project_me3ra',  # Singleowner
    'Reserve capital spending major equipment total ($)': 'cf_project_mecs',  # Singleowner
    'Reserve (increase)/decrease total reserve account ($)': 'cf_project_ra',  # Singleowner
    'Reserve (increase)/decrease receivables ($)': 'cf_project_receivablesra',  # Singleowner
    'Total after-tax cash returns ($)': 'cf_project_return_aftertax_cash',  # Singleowner
    'After-tax project maximum IRR (%)': 'cf_project_return_aftertax_max_irr',  # Singleowner
    'Pre-tax cumulative IRR (%)': 'cf_project_return_pretax_irr',  # Singleowner
    'Pre-tax cumulative NPV ($)': 'cf_project_return_pretax_npv',  # Singleowner
    'Reserve (increase)/decrease working capital ($)': 'cf_project_wcra',  # Singleowner
    'Present value of CAFDS ($)': 'cf_pv_cash_for_ds',  # Singleowner
    'Present value interest factor for CAFDS': 'cf_pv_interest_factor',  # Singleowner
    'Recapitalization operating expense ($)': 'cf_recapitalization',  # Singleowner
    'Reserves debt service balance ($)': 'cf_reserve_debtservice',  # Singleowner
    'Reserves major equipment 1 balance ($)': 'cf_reserve_equip1',  # Singleowner
    'Reserves major equipment 2 balance ($)': 'cf_reserve_equip2',  # Singleowner
    'Reserves major equipment 3 balance ($)': 'cf_reserve_equip3',  # Singleowner
    'Reserves working capital balance ($)': 'cf_reserve_om',  # Singleowner
    'Reserves receivables balance ($)': 'cf_reserve_receivables',  # Singleowner
    'Reserves total reserves balance ($)': 'cf_reserve_total',  # Singleowner
    'PPA revenue by year for April ($)': 'cf_revenue_apr',  # Singleowner
    'PPA revenue by year for August ($)': 'cf_revenue_aug',  # Singleowner
    'PPA revenue by year for December ($)': 'cf_revenue_dec',  # Singleowner
    'PPA revenue by year for TOD period 1 ($)': 'cf_revenue_dispatch1',  # Singleowner
    'PPA revenue by year for TOD period 2 ($)': 'cf_revenue_dispatch2',  # Singleowner
    'PPA revenue by year for TOD period 3 ($)': 'cf_revenue_dispatch3',  # Singleowner
    'PPA revenue by year for TOD period 4 ($)': 'cf_revenue_dispatch4',  # Singleowner
    'PPA revenue by year for TOD period 5 ($)': 'cf_revenue_dispatch5',  # Singleowner
    'PPA revenue by year for TOD period 6 ($)': 'cf_revenue_dispatch6',  # Singleowner
    'PPA revenue by year for TOD period 7 ($)': 'cf_revenue_dispatch7',  # Singleowner
    'PPA revenue by year for TOD period 8 ($)': 'cf_revenue_dispatch8',  # Singleowner
    'PPA revenue by year for TOD period 9 ($)': 'cf_revenue_dispatch9',  # Singleowner
    'PPA revenue by year for February ($)': 'cf_revenue_feb',  # Singleowner
    'PPA revenue by year for January ($)': 'cf_revenue_jan',  # Singleowner
    'PPA revenue by year for July ($)': 'cf_revenue_jul',  # Singleowner
    'PPA revenue by year for June ($)': 'cf_revenue_jun',  # Singleowner
    'PPA revenue by year for March ($)': 'cf_revenue_mar',  # Singleowner
    'PPA revenue by year for May ($)': 'cf_revenue_may',  # Singleowner
    'PPA revenue in Year 1 by month for TOD period 1 ($)': 'cf_revenue_monthly_firstyear_TOD1',  # Singleowner
    'PPA revenue in Year 1 by month for TOD period 2 ($)': 'cf_revenue_monthly_firstyear_TOD2',  # Singleowner
    'PPA revenue in Year 1 by month for TOD period 3 ($)': 'cf_revenue_monthly_firstyear_TOD3',  # Singleowner
    'PPA revenue in Year 1 by month for TOD period 4 ($)': 'cf_revenue_monthly_firstyear_TOD4',  # Singleowner
    'PPA revenue in Year 1 by month for TOD period 5 ($)': 'cf_revenue_monthly_firstyear_TOD5',  # Singleowner
    'PPA revenue in Year 1 by month for TOD period 6 ($)': 'cf_revenue_monthly_firstyear_TOD6',  # Singleowner
    'PPA revenue in Year 1 by month for TOD period 7 ($)': 'cf_revenue_monthly_firstyear_TOD7',  # Singleowner
    'PPA revenue in Year 1 by month for TOD period 8 ($)': 'cf_revenue_monthly_firstyear_TOD8',  # Singleowner
    'PPA revenue in Year 1 by month for TOD period 9 ($)': 'cf_revenue_monthly_firstyear_TOD9',  # Singleowner
    'PPA revenue by year for November ($)': 'cf_revenue_nov',  # Singleowner
    'PPA revenue by year for October ($)': 'cf_revenue_oct',  # Singleowner
    'PPA revenue by year for September ($)': 'cf_revenue_sep',  # Singleowner
    'State depreciation from custom ($)': 'cf_stadepr_custom',  # Singleowner
    'State depreciation from 15-yr MACRS ($)': 'cf_stadepr_macrs_15',  # Singleowner
    'State depreciation from 5-yr MACRS ($)': 'cf_stadepr_macrs_5',  # Singleowner
    'State depreciation from major equipment 1 ($)': 'cf_stadepr_me1',  # Singleowner
    'State depreciation from major equipment 2 ($)': 'cf_stadepr_me2',  # Singleowner
    'State depreciation from major equipment 3 ($)': 'cf_stadepr_me3',  # Singleowner
    'State depreciation from 15-yr straight line ($)': 'cf_stadepr_sl_15',  # Singleowner
    'State depreciation from 20-yr straight line ($)': 'cf_stadepr_sl_20',  # Singleowner
    'State depreciation from 39-yr straight line ($)': 'cf_stadepr_sl_39',  # Singleowner
    'State depreciation from 5-yr straight line ($)': 'cf_stadepr_sl_5',  # Singleowner
    'Total state tax depreciation ($)': 'cf_stadepr_total',  # Singleowner
    'State taxable income without incentives ($)': 'cf_statax_income_prior_incentives',  # Singleowner
    'State taxable income ($)': 'cf_statax_income_with_incentives',  # Singleowner
    'State taxable incentives ($)': 'cf_statax_taxable_incentives',  # Singleowner
    'Thermal revenue ($)': 'cf_thermal_value',  # Singleowner
    'Total financing cost ($)': 'cost_financing',  # Singleowner
    'Net capital cost per watt ($/W)': 'cost_installedperwatt',  # Singleowner
    'Debt percent (%)': 'debt_fraction',  # Singleowner
    'Custom straight line depreciation federal and state allocation ($)': 'depr_alloc_custom',  # Singleowner
    '15-yr MACRS depreciation federal and state allocation ($)': 'depr_alloc_macrs_15',  # Singleowner
    '5-yr MACRS depreciation federal and state allocation ($)': 'depr_alloc_macrs_5',  # Singleowner
    'Non-depreciable federal and state allocation ($)': 'depr_alloc_none',  # Singleowner
    'Non-depreciable federal and state allocation (%)': 'depr_alloc_none_percent',  # Singleowner
    '15-yr straight line depreciation federal and state allocation ($)': 'depr_alloc_sl_15',  # Singleowner
    '20-yr straight line depreciation federal and state allocation ($)': 'depr_alloc_sl_20',  # Singleowner
    '39-yr straight line depreciation federal and state allocation ($)': 'depr_alloc_sl_39',  # Singleowner
    '5-yr straight line depreciation federal and state allocation ($)': 'depr_alloc_sl_5',  # Singleowner
    'Total depreciation federal and state allocation ($)': 'depr_alloc_total',  # Singleowner
    'Custom straight line federal depreciation basis after ITC reduction ($)': 'depr_fedbas_after_itc_custom',
    # Singleowner
    '15-yr MACRS federal depreciation basis after ITC reduction ($)': 'depr_fedbas_after_itc_macrs_15',  # Singleowner
    '5-yr MACRS federal depreciation basis after ITC reduction ($)': 'depr_fedbas_after_itc_macrs_5',  # Singleowner
    '15-yr straight line federal depreciation basis after ITC reduction ($)': 'depr_fedbas_after_itc_sl_15',
    # Singleowner
    '20-yr straight line federal depreciation basis after ITC reduction ($)': 'depr_fedbas_after_itc_sl_20',
    # Singleowner
    '39-yr straight line federal depreciation basis after ITC reduction ($)': 'depr_fedbas_after_itc_sl_39',
    # Singleowner
    '5-yr straight line federal depreciation basis after ITC reduction ($)': 'depr_fedbas_after_itc_sl_5',
    # Singleowner
    'Total federal depreciation basis after ITC reduction ($)': 'depr_fedbas_after_itc_total',  # Singleowner
    'Custom straight line federal CBI reduction ($)': 'depr_fedbas_cbi_reduc_custom',  # Singleowner
    '15-yr MACRS federal CBI reduction ($)': 'depr_fedbas_cbi_reduc_macrs_15',  # Singleowner
    '5-yr MACRS federal CBI reduction ($)': 'depr_fedbas_cbi_reduc_macrs_5',  # Singleowner
    '15-yr straight line federal CBI reduction ($)': 'depr_fedbas_cbi_reduc_sl_15',  # Singleowner
    '20-yr straight line federal CBI reduction ($)': 'depr_fedbas_cbi_reduc_sl_20',  # Singleowner
    '39-yr straight line federal CBI reduction ($)': 'depr_fedbas_cbi_reduc_sl_39',  # Singleowner
    '5-yr straight line federal CBI reduction ($)': 'depr_fedbas_cbi_reduc_sl_5',  # Singleowner
    'Total federal CBI reduction ($)': 'depr_fedbas_cbi_reduc_total',  # Singleowner
    'Custom straight line federal depreciation basis ($)': 'depr_fedbas_custom',  # Singleowner
    'Custom straight line federal first year bonus depreciation ($)': 'depr_fedbas_first_year_bonus_custom',
    # Singleowner
    '15-yr MACRS federal first year bonus depreciation ($)': 'depr_fedbas_first_year_bonus_macrs_15',  # Singleowner
    '5-yr MACRS federal first year bonus depreciation ($)': 'depr_fedbas_first_year_bonus_macrs_5',  # Singleowner
    '15-yr straight line federal first year bonus depreciation ($)': 'depr_fedbas_first_year_bonus_sl_15',
    # Singleowner
    '20-yr straight line federal first year bonus depreciation ($)': 'depr_fedbas_first_year_bonus_sl_20',
    # Singleowner
    '39-yr straight line federal first year bonus depreciation ($)': 'depr_fedbas_first_year_bonus_sl_39',
    # Singleowner
    '5-yr straight line federal first year bonus depreciation ($)': 'depr_fedbas_first_year_bonus_sl_5',  # Singleowner
    'Total federal first year bonus depreciation ($)': 'depr_fedbas_first_year_bonus_total',  # Singleowner
    'Custom straight line depreciation ITC basis from federal fixed amount ($)': 'depr_fedbas_fixed_amount_custom',
    # Singleowner
    '15-yr MACRS depreciation ITC basis from federal fixed amount ($)': 'depr_fedbas_fixed_amount_macrs_15',
    # Singleowner
    '5-yr MACRS depreciation ITC basis from federal fixed amount ($)': 'depr_fedbas_fixed_amount_macrs_5',
    # Singleowner
    '15-yr straight line depreciation ITC basis from federal fixed amount ($)': 'depr_fedbas_fixed_amount_sl_15',
    # Singleowner
    '20-yr straight line depreciation ITC basis from federal fixed amount ($)': 'depr_fedbas_fixed_amount_sl_20',
    # Singleowner
    '39-yr straight line depreciation ITC basis from federal fixed amount ($)': 'depr_fedbas_fixed_amount_sl_39',
    # Singleowner
    '5-yr straight line depreciation ITC basis from federal fixed amount ($)': 'depr_fedbas_fixed_amount_sl_5',
    # Singleowner
    'Total depreciation ITC basis from federal fixed amount ($)': 'depr_fedbas_fixed_amount_total',  # Singleowner
    'Custom straight line federal IBI reduction ($)': 'depr_fedbas_ibi_reduc_custom',  # Singleowner
    '15-yr MACRS federal IBI reduction ($)': 'depr_fedbas_ibi_reduc_macrs_15',  # Singleowner
    '5-yr MACRS federal IBI reduction ($)': 'depr_fedbas_ibi_reduc_macrs_5',  # Singleowner
    '15-yr straight line federal IBI reduction ($)': 'depr_fedbas_ibi_reduc_sl_15',  # Singleowner
    '20-yr straight line federal IBI reduction ($)': 'depr_fedbas_ibi_reduc_sl_20',  # Singleowner
    '39-yr straight line federal IBI reduction ($)': 'depr_fedbas_ibi_reduc_sl_39',  # Singleowner
    '5-yr straight line federal IBI reduction ($)': 'depr_fedbas_ibi_reduc_sl_5',  # Singleowner
    'Total federal IBI reduction ($)': 'depr_fedbas_ibi_reduc_total',  # Singleowner
    'Custom straight line federal basis federal ITC reduction ($)': 'depr_fedbas_itc_fed_reduction_custom',
    # Singleowner
    '15-yr MACRS federal basis federal ITC reduction ($)': 'depr_fedbas_itc_fed_reduction_macrs_15',  # Singleowner
    '5-yr MACRS federal basis federal ITC reduction ($)': 'depr_fedbas_itc_fed_reduction_macrs_5',  # Singleowner
    '15-yr straight line federal basis federal ITC reduction ($)': 'depr_fedbas_itc_fed_reduction_sl_15',  # Singleowner
    '20-yr straight line federal basis federal ITC reduction ($)': 'depr_fedbas_itc_fed_reduction_sl_20',  # Singleowner
    '39-yr straight line federal basis federal ITC reduction ($)': 'depr_fedbas_itc_fed_reduction_sl_39',  # Singleowner
    '5-yr straight line federal basis federal ITC reduction ($)': 'depr_fedbas_itc_fed_reduction_sl_5',  # Singleowner
    'Total federal basis federal ITC reduction ($)': 'depr_fedbas_itc_fed_reduction_total',  # Singleowner
    'Custom straight line federal basis state ITC reduction ($)': 'depr_fedbas_itc_sta_reduction_custom',  # Singleowner
    '15-yr MACRS federal basis state ITC reduction ($)': 'depr_fedbas_itc_sta_reduction_macrs_15',  # Singleowner
    '5-yr MACRS federal basis state ITC reduction ($)': 'depr_fedbas_itc_sta_reduction_macrs_5',  # Singleowner
    '15-yr straight line federal basis state ITC reduction ($)': 'depr_fedbas_itc_sta_reduction_sl_15',  # Singleowner
    '20-yr straight line federal basis state ITC reduction ($)': 'depr_fedbas_itc_sta_reduction_sl_20',  # Singleowner
    '39-yr straight line federal basis state ITC reduction ($)': 'depr_fedbas_itc_sta_reduction_sl_39',  # Singleowner
    '5-yr straight line federal basis state ITC reduction ($)': 'depr_fedbas_itc_sta_reduction_sl_5',  # Singleowner
    'Total federal basis state ITC reduction ($)': 'depr_fedbas_itc_sta_reduction_total',  # Singleowner
    '15-yr MACRS federal depreciation basis ($)': 'depr_fedbas_macrs_15',  # Singleowner
    '5-yr MACRS federal depreciation basis ($)': 'depr_fedbas_macrs_5',  # Singleowner
    'Custom straight line depreciation ITC basis from federal percentage ($)': 'depr_fedbas_percent_amount_custom',
    # Singleowner
    '15-yr MACRS depreciation ITC basis from federal percentage ($)': 'depr_fedbas_percent_amount_macrs_15',
    # Singleowner
    '5-yr MACRS depreciation ITC basis from federal percentage ($)': 'depr_fedbas_percent_amount_macrs_5',
    # Singleowner
    '15-yr straight line depreciation ITC basis from federal percentage ($)': 'depr_fedbas_percent_amount_sl_15',
    # Singleowner
    '20-yr straight line depreciation ITC basis from federal percentage ($)': 'depr_fedbas_percent_amount_sl_20',
    # Singleowner
    '39-yr straight line depreciation ITC basis from federal percentage ($)': 'depr_fedbas_percent_amount_sl_39',
    # Singleowner
    '5-yr straight line depreciation ITC basis from federal percentage ($)': 'depr_fedbas_percent_amount_sl_5',
    # Singleowner
    'Total depreciation ITC basis from federal percentage ($)': 'depr_fedbas_percent_amount_total',  # Singleowner
    'Custom straight line federal percent of total depreciable basis (%)': 'depr_fedbas_percent_custom',  # Singleowner
    '15-yr MACRS federal percent of total depreciable basis (%)': 'depr_fedbas_percent_macrs_15',  # Singleowner
    '5-yr MACRS federal percent of total depreciable basis (%)': 'depr_fedbas_percent_macrs_5',  # Singleowner
    'Custom straight line federal percent of qualifying costs (%)': 'depr_fedbas_percent_qual_custom',  # Singleowner
    '15-yr MACRS federal percent of qualifying costs (%)': 'depr_fedbas_percent_qual_macrs_15',  # Singleowner
    '5-yr MACRS federal percent of qualifying costs (%)': 'depr_fedbas_percent_qual_macrs_5',  # Singleowner
    '15-yr straight line federal percent of qualifying costs (%)': 'depr_fedbas_percent_qual_sl_15',  # Singleowner
    '20-yr straight line federal percent of qualifying costs (%)': 'depr_fedbas_percent_qual_sl_20',  # Singleowner
    '39-yr straight line federal percent of qualifying costs (%)': 'depr_fedbas_percent_qual_sl_39',  # Singleowner
    '5-yr straight line federal percent of qualifying costs (%)': 'depr_fedbas_percent_qual_sl_5',  # Singleowner
    'Total federal percent of qualifying costs (%)': 'depr_fedbas_percent_qual_total',  # Singleowner
    '15-yr straight line federal percent of total depreciable basis (%)': 'depr_fedbas_percent_sl_15',  # Singleowner
    '20-yr straight line federal percent of total depreciable basis (%)': 'depr_fedbas_percent_sl_20',  # Singleowner
    '39-yr straight line federal percent of total depreciable basis (%)': 'depr_fedbas_percent_sl_39',  # Singleowner
    '5-yr straight line federal percent of total depreciable basis (%)': 'depr_fedbas_percent_sl_5',  # Singleowner
    'Total federal percent of total depreciable basis (%)': 'depr_fedbas_percent_total',  # Singleowner
    'Custom straight line federal depreciation basis prior ITC reduction ($)': 'depr_fedbas_prior_itc_custom',
    # Singleowner
    '15-yr MACRS federal depreciation basis prior ITC reduction ($)': 'depr_fedbas_prior_itc_macrs_15',  # Singleowner
    '5-yr MACRS federal depreciation basis prior ITC reduction ($)': 'depr_fedbas_prior_itc_macrs_5',  # Singleowner
    '15-yr straight line federal depreciation basis prior ITC reduction ($)': 'depr_fedbas_prior_itc_sl_15',
    # Singleowner
    '20-yr straight line federal depreciation basis prior ITC reduction ($)': 'depr_fedbas_prior_itc_sl_20',
    # Singleowner
    '39-yr straight line federal depreciation basis prior ITC reduction ($)': 'depr_fedbas_prior_itc_sl_39',
    # Singleowner
    '5-yr straight line federal depreciation basis prior ITC reduction ($)': 'depr_fedbas_prior_itc_sl_5',
    # Singleowner
    'Total federal depreciation basis prior ITC reduction ($)': 'depr_fedbas_prior_itc_total',  # Singleowner
    '15-yr straight line federal depreciation basis ($)': 'depr_fedbas_sl_15',  # Singleowner
    '20-yr straight line federal depreciation basis ($)': 'depr_fedbas_sl_20',  # Singleowner
    '39-yr straight line federal depreciation basis ($)': 'depr_fedbas_sl_39',  # Singleowner
    '5-yr straight line federal depreciation basis ($)': 'depr_fedbas_sl_5',  # Singleowner
    'Total federal depreciation basis ($)': 'depr_fedbas_total',  # Singleowner
    'Custom straight line state depreciation basis after ITC reduction ($)': 'depr_stabas_after_itc_custom',
    # Singleowner
    '15-yr MACRS state depreciation basis after ITC reduction ($)': 'depr_stabas_after_itc_macrs_15',  # Singleowner
    '5-yr MACRS state depreciation basis after ITC reduction ($)': 'depr_stabas_after_itc_macrs_5',  # Singleowner
    '15-yr straight line state depreciation basis after ITC reduction ($)': 'depr_stabas_after_itc_sl_15',
    # Singleowner
    '20-yr straight line state depreciation basis after ITC reduction ($)': 'depr_stabas_after_itc_sl_20',
    # Singleowner
    '39-yr straight line state depreciation basis after ITC reduction ($)': 'depr_stabas_after_itc_sl_39',
    # Singleowner
    '5-yr straight line state depreciation basis after ITC reduction ($)': 'depr_stabas_after_itc_sl_5',  # Singleowner
    'Total state depreciation basis after ITC reduction ($)': 'depr_stabas_after_itc_total',  # Singleowner
    'Custom straight line state CBI reduction ($)': 'depr_stabas_cbi_reduc_custom',  # Singleowner
    '15-yr MACRS state CBI reduction ($)': 'depr_stabas_cbi_reduc_macrs_15',  # Singleowner
    '5-yr MACRS state CBI reduction ($)': 'depr_stabas_cbi_reduc_macrs_5',  # Singleowner
    '15-yr straight line state CBI reduction ($)': 'depr_stabas_cbi_reduc_sl_15',  # Singleowner
    '20-yr straight line state CBI reduction ($)': 'depr_stabas_cbi_reduc_sl_20',  # Singleowner
    '39-yr straight line state CBI reduction ($)': 'depr_stabas_cbi_reduc_sl_39',  # Singleowner
    '5-yr straight line state CBI reduction ($)': 'depr_stabas_cbi_reduc_sl_5',  # Singleowner
    'Total state CBI reduction ($)': 'depr_stabas_cbi_reduc_total',  # Singleowner
    'Custom straight line state depreciation basis ($)': 'depr_stabas_custom',  # Singleowner
    'Custom straight line state first year bonus depreciation ($)': 'depr_stabas_first_year_bonus_custom',
    # Singleowner
    '15-yr MACRS state first year bonus depreciation ($)': 'depr_stabas_first_year_bonus_macrs_15',  # Singleowner
    '5-yr MACRS state first year bonus depreciation ($)': 'depr_stabas_first_year_bonus_macrs_5',  # Singleowner
    '15-yr straight line state first year bonus depreciation ($)': 'depr_stabas_first_year_bonus_sl_15',  # Singleowner
    '20-yr straight line state first year bonus depreciation ($)': 'depr_stabas_first_year_bonus_sl_20',  # Singleowner
    '39-yr straight line state first year bonus depreciation ($)': 'depr_stabas_first_year_bonus_sl_39',  # Singleowner
    '5-yr straight line state first year bonus depreciation ($)': 'depr_stabas_first_year_bonus_sl_5',  # Singleowner
    'Total state first year bonus depreciation ($)': 'depr_stabas_first_year_bonus_total',  # Singleowner
    'Custom straight line depreciation ITC basis from state fixed amount ($)': 'depr_stabas_fixed_amount_custom',
    # Singleowner
    '15-yr MACRS depreciation ITC basis from state fixed amount ($)': 'depr_stabas_fixed_amount_macrs_15',
    # Singleowner
    '5-yr MACRS depreciation ITC basis from state fixed amount ($)': 'depr_stabas_fixed_amount_macrs_5',  # Singleowner
    '15-yr straight line depreciation ITC basis from state fixed amount ($)': 'depr_stabas_fixed_amount_sl_15',
    # Singleowner
    '20-yr straight line depreciation ITC basis from state fixed amount ($)': 'depr_stabas_fixed_amount_sl_20',
    # Singleowner
    '39-yr straight line depreciation ITC basis from state fixed amount ($)': 'depr_stabas_fixed_amount_sl_39',
    # Singleowner
    '5-yr straight line depreciation ITC basis from state fixed amount ($)': 'depr_stabas_fixed_amount_sl_5',
    # Singleowner
    'Total depreciation ITC basis from state fixed amount ($)': 'depr_stabas_fixed_amount_total',  # Singleowner
    'Custom straight line state IBI reduction ($)': 'depr_stabas_ibi_reduc_custom',  # Singleowner
    '15-yr MACRS state IBI reduction ($)': 'depr_stabas_ibi_reduc_macrs_15',  # Singleowner
    '5-yr MACRS state IBI reduction ($)': 'depr_stabas_ibi_reduc_macrs_5',  # Singleowner
    '15-yr straight line state IBI reduction ($)': 'depr_stabas_ibi_reduc_sl_15',  # Singleowner
    '20-yr straight line state IBI reduction ($)': 'depr_stabas_ibi_reduc_sl_20',  # Singleowner
    '39-yr straight line state IBI reduction ($)': 'depr_stabas_ibi_reduc_sl_39',  # Singleowner
    '5-yr straight line state IBI reduction ($)': 'depr_stabas_ibi_reduc_sl_5',  # Singleowner
    'Total state IBI reduction ($)': 'depr_stabas_ibi_reduc_total',  # Singleowner
    'Custom straight line state basis federal ITC reduction ($)': 'depr_stabas_itc_fed_reduction_custom',  # Singleowner
    '15-yr MACRS state basis federal ITC reduction ($)': 'depr_stabas_itc_fed_reduction_macrs_15',  # Singleowner
    '5-yr MACRS state basis federal ITC reduction ($)': 'depr_stabas_itc_fed_reduction_macrs_5',  # Singleowner
    '15-yr straight line state basis federal ITC reduction ($)': 'depr_stabas_itc_fed_reduction_sl_15',  # Singleowner
    '20-yr straight line state basis federal ITC reduction ($)': 'depr_stabas_itc_fed_reduction_sl_20',  # Singleowner
    '39-yr straight line state basis federal ITC reduction ($)': 'depr_stabas_itc_fed_reduction_sl_39',  # Singleowner
    '5-yr straight line state basis federal ITC reduction ($)': 'depr_stabas_itc_fed_reduction_sl_5',  # Singleowner
    'Total state basis federal ITC reduction ($)': 'depr_stabas_itc_fed_reduction_total',  # Singleowner
    'Custom straight line state basis state ITC reduction ($)': 'depr_stabas_itc_sta_reduction_custom',  # Singleowner
    '15-yr MACRS state basis state ITC reduction ($)': 'depr_stabas_itc_sta_reduction_macrs_15',  # Singleowner
    '5-yr MACRS state basis state ITC reduction ($)': 'depr_stabas_itc_sta_reduction_macrs_5',  # Singleowner
    '15-yr straight line state basis state ITC reduction ($)': 'depr_stabas_itc_sta_reduction_sl_15',  # Singleowner
    '20-yr straight line state basis state ITC reduction ($)': 'depr_stabas_itc_sta_reduction_sl_20',  # Singleowner
    '39-yr straight line state basis state ITC reduction ($)': 'depr_stabas_itc_sta_reduction_sl_39',  # Singleowner
    '5-yr straight line state basis state ITC reduction ($)': 'depr_stabas_itc_sta_reduction_sl_5',  # Singleowner
    'Total state basis state ITC reduction ($)': 'depr_stabas_itc_sta_reduction_total',  # Singleowner
    '15-yr MACRS state depreciation basis ($)': 'depr_stabas_macrs_15',  # Singleowner
    '5-yr MACRS state depreciation basis ($)': 'depr_stabas_macrs_5',  # Singleowner
    'Custom straight line depreciation ITC basis from state percentage ($)': 'depr_stabas_percent_amount_custom',
    # Singleowner
    '15-yr MACRS depreciation ITC basis from state percentage ($)': 'depr_stabas_percent_amount_macrs_15',
    # Singleowner
    '5-yr MACRS depreciation ITC basis from state percentage ($)': 'depr_stabas_percent_amount_macrs_5',  # Singleowner
    '15-yr straight line depreciation ITC basis from state percentage ($)': 'depr_stabas_percent_amount_sl_15',
    # Singleowner
    '20-yr straight line depreciation ITC basis from state percentage ($)': 'depr_stabas_percent_amount_sl_20',
    # Singleowner
    '39-yr straight line depreciation ITC basis from state percentage ($)': 'depr_stabas_percent_amount_sl_39',
    # Singleowner
    '5-yr straight line depreciation ITC basis from state percentage ($)': 'depr_stabas_percent_amount_sl_5',
    # Singleowner
    'Total depreciation ITC basis from state percentage ($)': 'depr_stabas_percent_amount_total',  # Singleowner
    'Custom straight line state percent of total depreciable basis (%)': 'depr_stabas_percent_custom',  # Singleowner
    '15-yr MACRS state percent of total depreciable basis (%)': 'depr_stabas_percent_macrs_15',  # Singleowner
    '5-yr MACRS state percent of total depreciable basis (%)': 'depr_stabas_percent_macrs_5',  # Singleowner
    'Custom straight line state percent of qualifying costs (%)': 'depr_stabas_percent_qual_custom',  # Singleowner
    '15-yr MACRS state percent of qualifying costs (%)': 'depr_stabas_percent_qual_macrs_15',  # Singleowner
    '5-yr MACRS state percent of qualifying costs (%)': 'depr_stabas_percent_qual_macrs_5',  # Singleowner
    '15-yr straight line state percent of qualifying costs (%)': 'depr_stabas_percent_qual_sl_15',  # Singleowner
    '20-yr straight line state percent of qualifying costs (%)': 'depr_stabas_percent_qual_sl_20',  # Singleowner
    '39-yr straight line state percent of qualifying costs (%)': 'depr_stabas_percent_qual_sl_39',  # Singleowner
    '5-yr straight line state percent of qualifying costs (%)': 'depr_stabas_percent_qual_sl_5',  # Singleowner
    'Total state percent of qualifying costs (%)': 'depr_stabas_percent_qual_total',  # Singleowner
    '15-yr straight line state percent of total depreciable basis (%)': 'depr_stabas_percent_sl_15',  # Singleowner
    '20-yr straight line state percent of total depreciable basis (%)': 'depr_stabas_percent_sl_20',  # Singleowner
    '39-yr straight line state percent of total depreciable basis (%)': 'depr_stabas_percent_sl_39',  # Singleowner
    '5-yr straight line state percent of total depreciable basis (%)': 'depr_stabas_percent_sl_5',  # Singleowner
    'Total state percent of total depreciable basis (%)': 'depr_stabas_percent_total',  # Singleowner
    'Custom straight line state depreciation basis prior ITC reduction ($)': 'depr_stabas_prior_itc_custom',
    # Singleowner
    '15-yr MACRS state depreciation basis prior ITC reduction ($)': 'depr_stabas_prior_itc_macrs_15',  # Singleowner
    '5-yr MACRS state depreciation basis prior ITC reduction ($)': 'depr_stabas_prior_itc_macrs_5',  # Singleowner
    '15-yr straight line state depreciation basis prior ITC reduction ($)': 'depr_stabas_prior_itc_sl_15',
    # Singleowner
    '20-yr straight line state depreciation basis prior ITC reduction ($)': 'depr_stabas_prior_itc_sl_20',
    # Singleowner
    '39-yr straight line state depreciation basis prior ITC reduction ($)': 'depr_stabas_prior_itc_sl_39',
    # Singleowner
    '5-yr straight line state depreciation basis prior ITC reduction ($)': 'depr_stabas_prior_itc_sl_5',  # Singleowner
    'Total state depreciation basis prior ITC reduction ($)': 'depr_stabas_prior_itc_total',  # Singleowner
    '15-yr straight line state depreciation basis ($)': 'depr_stabas_sl_15',  # Singleowner
    '20-yr straight line state depreciation basis ($)': 'depr_stabas_sl_20',  # Singleowner
    '39-yr straight line state depreciation basis ($)': 'depr_stabas_sl_39',  # Singleowner
    '5-yr straight line state depreciation basis ($)': 'depr_stabas_sl_5',  # Singleowner
    'Total state depreciation basis ($)': 'depr_stabas_total',  # Singleowner
    'Energy produced in Year 1 TOD period 1 (kWh)': 'firstyear_energy_dispatch1',  # Singleowner
    'Energy produced in Year 1 TOD period 2 (kWh)': 'firstyear_energy_dispatch2',  # Singleowner
    'Energy produced in Year 1 TOD period 3 (kWh)': 'firstyear_energy_dispatch3',  # Singleowner
    'Energy produced in Year 1 TOD period 4 (kWh)': 'firstyear_energy_dispatch4',  # Singleowner
    'Energy produced in Year 1 TOD period 5 (kWh)': 'firstyear_energy_dispatch5',  # Singleowner
    'Energy produced in Year 1 TOD period 6 (kWh)': 'firstyear_energy_dispatch6',  # Singleowner
    'Energy produced in Year 1 TOD period 7 (kWh)': 'firstyear_energy_dispatch7',  # Singleowner
    'Energy produced in Year 1 TOD period 8 (kWh)': 'firstyear_energy_dispatch8',  # Singleowner
    'Energy produced in Year 1 TOD period 9 (kWh)': 'firstyear_energy_dispatch9',  # Singleowner
    'Power price in Year 1 TOD period 1 (cents/kWh)': 'firstyear_energy_price1',  # Singleowner
    'Power price in Year 1 TOD period 2 (cents/kWh)': 'firstyear_energy_price2',  # Singleowner
    'Power price in Year 1 TOD period 3 (cents/kWh)': 'firstyear_energy_price3',  # Singleowner
    'Power price in Year 1 TOD period 4 (cents/kWh)': 'firstyear_energy_price4',  # Singleowner
    'Power price in Year 1 TOD period 5 (cents/kWh)': 'firstyear_energy_price5',  # Singleowner
    'Power price in Year 1 TOD period 6 (cents/kWh)': 'firstyear_energy_price6',  # Singleowner
    'Power price in Year 1 TOD period 7 (cents/kWh)': 'firstyear_energy_price7',  # Singleowner
    'Power price in Year 1 TOD period 8 (cents/kWh)': 'firstyear_energy_price8',  # Singleowner
    'Power price in Year 1 TOD period 9 (cents/kWh)': 'firstyear_energy_price9',  # Singleowner
    'PPA revenue in Year 1 TOD period 1 ($)': 'firstyear_revenue_dispatch1',  # Singleowner
    'PPA revenue in Year 1 TOD period 2 ($)': 'firstyear_revenue_dispatch2',  # Singleowner
    'PPA revenue in Year 1 TOD period 3 ($)': 'firstyear_revenue_dispatch3',  # Singleowner
    'PPA revenue in Year 1 TOD period 4 ($)': 'firstyear_revenue_dispatch4',  # Singleowner
    'PPA revenue in Year 1 TOD period 5 ($)': 'firstyear_revenue_dispatch5',  # Singleowner
    'PPA revenue in Year 1 TOD period 6 ($)': 'firstyear_revenue_dispatch6',  # Singleowner
    'PPA revenue in Year 1 TOD period 7 ($)': 'firstyear_revenue_dispatch7',  # Singleowner
    'PPA revenue in Year 1 TOD period 8 ($)': 'firstyear_revenue_dispatch8',  # Singleowner
    'PPA revenue in Year 1 TOD period 9 ($)': 'firstyear_revenue_dispatch9',  # Singleowner
    'IRR in target year (%)': 'flip_actual_irr',  # Singleowner
    'Year target IRR was achieved (year)': 'flip_actual_year',  # Singleowner
    'IRR target (%)': 'flip_target_irr',  # Singleowner
    'Target year to meet IRR': 'flip_target_year',  # Singleowner
    'Custom straight line depreciation ITC basis disallowance from federal fixed amount ($)': 'itc_disallow_fed_fixed_custom',
    # Singleowner
    '15-yr MACRS depreciation ITC basis disallowance from federal fixed amount ($)': 'itc_disallow_fed_fixed_macrs_15',
    # Singleowner
    '5-yr MACRS depreciation ITC basis disallowance from federal fixed amount ($)': 'itc_disallow_fed_fixed_macrs_5',
    # Singleowner
    '15-yr straight line depreciation ITC basis disallowance from federal fixed amount ($)': 'itc_disallow_fed_fixed_sl_15',
    # Singleowner
    '20-yr straight line depreciation ITC basis disallowance from federal fixed amount ($)': 'itc_disallow_fed_fixed_sl_20',
    # Singleowner
    '39-yr straight line depreciation ITC basis disallowance from federal fixed amount ($)': 'itc_disallow_fed_fixed_sl_39',
    # Singleowner
    '5-yr straight line depreciation ITC basis disallowance from federal fixed amount ($)': 'itc_disallow_fed_fixed_sl_5',
    # Singleowner
    'Total depreciation ITC basis disallowance from federal fixed amount ($)': 'itc_disallow_fed_fixed_total',
    # Singleowner
    'Custom straight line depreciation ITC basis disallowance from federal percentage ($)': 'itc_disallow_fed_percent_custom',
    # Singleowner
    '15-yr MACRS depreciation ITC basis disallowance from federal percentage ($)': 'itc_disallow_fed_percent_macrs_15',
    # Singleowner
    '5-yr MACRS depreciation ITC basis disallowance from federal percentage ($)': 'itc_disallow_fed_percent_macrs_5',
    # Singleowner
    '15-yr straight line depreciation ITC basis disallowance from federal percentage ($)': 'itc_disallow_fed_percent_sl_15',
    # Singleowner
    '20-yr straight line depreciation ITC basis disallowance from federal percentage ($)': 'itc_disallow_fed_percent_sl_20',
    # Singleowner
    '39-yr straight line depreciation ITC basis disallowance from federal percentage ($)': 'itc_disallow_fed_percent_sl_39',
    # Singleowner
    '5-yr straight line depreciation ITC basis disallowance from federal percentage ($)': 'itc_disallow_fed_percent_sl_5',
    # Singleowner
    'Total depreciation ITC basis disallowance from federal percentage ($)': 'itc_disallow_fed_percent_total',
    # Singleowner
    'Custom straight line depreciation ITC basis disallowance from state fixed amount ($)': 'itc_disallow_sta_fixed_custom',
    # Singleowner
    '15-yr MACRS depreciation ITC basis disallowance from state fixed amount ($)': 'itc_disallow_sta_fixed_macrs_15',
    # Singleowner
    '5-yr MACRS depreciation ITC basis disallowance from state fixed amount ($)': 'itc_disallow_sta_fixed_macrs_5',
    # Singleowner
    '15-yr straight line depreciation ITC basis disallowance from state fixed amount ($)': 'itc_disallow_sta_fixed_sl_15',
    # Singleowner
    '20-yr straight line depreciation ITC basis disallowance from state fixed amount ($)': 'itc_disallow_sta_fixed_sl_20',
    # Singleowner
    '39-yr straight line depreciation ITC basis disallowance from state fixed amount ($)': 'itc_disallow_sta_fixed_sl_39',
    # Singleowner
    '5-yr straight line depreciation ITC basis disallowance from state fixed amount ($)': 'itc_disallow_sta_fixed_sl_5',
    # Singleowner
    'Total depreciation ITC basis disallowance from state fixed amount ($)': 'itc_disallow_sta_fixed_total',
    # Singleowner
    'Custom straight line depreciation ITC basis disallowance from state percentage ($)': 'itc_disallow_sta_percent_custom',
    # Singleowner
    '15-yr MACRS depreciation ITC basis disallowance from state percentage ($)': 'itc_disallow_sta_percent_macrs_15',
    # Singleowner
    '5-yr MACRS depreciation ITC basis disallowance from state percentage ($)': 'itc_disallow_sta_percent_macrs_5',
    # Singleowner
    '15-yr straight line depreciation ITC basis disallowance from state percentage ($)': 'itc_disallow_sta_percent_sl_15',
    # Singleowner
    '20-yr straight line depreciation ITC basis disallowance from state percentage ($)': 'itc_disallow_sta_percent_sl_20',
    # Singleowner
    '39-yr straight line depreciation ITC basis disallowance from state percentage ($)': 'itc_disallow_sta_percent_sl_39',
    # Singleowner
    '5-yr straight line depreciation ITC basis disallowance from state percentage ($)': 'itc_disallow_sta_percent_sl_5',
    # Singleowner
    'Total depreciation ITC basis disallowance from state percentage ($)': 'itc_disallow_sta_percent_total',
    # Singleowner
    'Federal ITC fixed total ($)': 'itc_fed_fixed_total',  # Singleowner
    'Federal ITC percent total ($)': 'itc_fed_percent_total',  # Singleowner
    'Custom straight line depreciation federal ITC adj qualifying costs ($)': 'itc_fed_qual_custom',  # Singleowner
    '15-yr MACRS depreciation federal ITC adj qualifying costs ($)': 'itc_fed_qual_macrs_15',  # Singleowner
    '5-yr MACRS depreciation federal ITC adj qualifying costs ($)': 'itc_fed_qual_macrs_5',  # Singleowner
    '15-yr straight line depreciation federal ITC adj qualifying costs ($)': 'itc_fed_qual_sl_15',  # Singleowner
    '20-yr straight line depreciation federal ITC adj qualifying costs ($)': 'itc_fed_qual_sl_20',  # Singleowner
    '39-yr straight line depreciation federal ITC adj qualifying costs ($)': 'itc_fed_qual_sl_39',  # Singleowner
    '5-yr straight line depreciation federal ITC adj qualifying costs ($)': 'itc_fed_qual_sl_5',  # Singleowner
    'Total federal ITC adj qualifying costs ($)': 'itc_fed_qual_total',  # Singleowner
    'State ITC fixed total ($)': 'itc_sta_fixed_total',  # Singleowner
    'State ITC percent total ($)': 'itc_sta_percent_total',  # Singleowner
    'Custom straight line depreciation state ITC adj qualifying costs ($)': 'itc_sta_qual_custom',  # Singleowner
    '15-yr MACRS depreciation state ITC adj qualifying costs ($)': 'itc_sta_qual_macrs_15',  # Singleowner
    '5-yr MACRS depreciation state ITC adj qualifying costs ($)': 'itc_sta_qual_macrs_5',  # Singleowner
    '15-yr straight line depreciation state ITC adj qualifying costs ($)': 'itc_sta_qual_sl_15',  # Singleowner
    '20-yr straight line depreciation state ITC adj qualifying costs ($)': 'itc_sta_qual_sl_20',  # Singleowner
    '39-yr straight line depreciation state ITC adj qualifying costs ($)': 'itc_sta_qual_sl_39',  # Singleowner
    '5-yr straight line depreciation state ITC adj qualifying costs ($)': 'itc_sta_qual_sl_5',  # Singleowner
    'Total state ITC adj qualifying costs ($)': 'itc_sta_qual_total',  # Singleowner
    'LPPA Levelized PPA price real (cents/kWh)': 'lppa_real',  # Singleowner
    'Minimum DSCR': 'min_dscr',  # Singleowner
    'Present value of capacity payment revenue ($)': 'npv_capacity_revenue',  # Singleowner
    'Present value of curtailment payment revenue ($)': 'npv_curtailment_revenue',  # Singleowner
    'Present value of annual energy nominal (kWh)': 'npv_energy_nom',  # Singleowner
    'Present value of annual energy real (kWh)': 'npv_energy_real',  # Singleowner
    'Present value of federal PBI income ($)': 'npv_fed_pbi_income',  # Singleowner
    'Present value of other PBI income ($)': 'npv_oth_pbi_income',  # Singleowner
    'Present value of salvage value ($)': 'npv_salvage_value',  # Singleowner
    'Present value of state PBI income ($)': 'npv_sta_pbi_income',  # Singleowner
    'Present value of thermal value ($)': 'npv_thermal_value',  # Singleowner
    'Present value of utility PBI income ($)': 'npv_uti_pbi_income',  # Singleowner
    'PPA price in Year 1 (cents/kWh)': 'ppa',  # Singleowner
    'PPA price escalation (%/year)': 'ppa_escalation',  # Singleowner
    'TOD factors': 'ppa_multipliers',  # Singleowner
    'PPA price in first year (cents/kWh)': 'ppa_price',  # Singleowner
    'Depreciable basis prior to allocation ($)': 'pre_depr_alloc_basis',  # Singleowner
    'ITC basis prior to qualification ($)': 'pre_itc_qual_basis',  # Singleowner
    'Present value of fuel O&M ($)': 'present_value_fuel',  # Singleowner
    'Present value of insurance and prop tax ($)': 'present_value_insandproptax',  # Singleowner
    'Present value of O&M ($)': 'present_value_oandm',  # Singleowner
    'Present value of non-fuel O&M ($)': 'present_value_oandm_nonfuel',  # Singleowner
    'IRR Internal rate of return (%)': 'project_return_aftertax_irr',  # Singleowner
    'Assessed value of property for tax purposes ($)': 'prop_tax_assessed_value',  # Singleowner
    'Present value of CAFDS ($)': 'pv_cafds',  # Singleowner
    'Electricity to grid (kW)': 'revenue_gen',  # Singleowner
    'Net pre-tax cash salvage value ($)': 'salvage_value',  # Singleowner
    'WACC Weighted average cost of capital ($)': 'wacc',  # Singleowner
}


def _get_logger():
    # TODO disable debug output outside of dev environment
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.DEBUG)
    sh.setFormatter(logging.Formatter(fmt='[%(asctime)s][%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    _l = logging.getLogger(__name__)
    _l.setLevel(logging.DEBUG)
    _l.addHandler(sh)
    return _l


_log = _get_logger()


def _get_single_owner_output(soo: Any, display_name: str) -> Any:
    """ "
    :param soo: single_owner.Outputs
    :type soo: `PySAM.Singleowner.Outputs`
    """

    def ga(_p):
        # noinspection PyBroadException
        try:
            return getattr(soo, _p)
        except Exception:
            return None

    def _search_props(s: str) -> list[Any]:
        """
        Utility function to search output properties (useful in IDE debugger)
        """

        return [(p, ga(p)) for p in dir(soo) if s in p]

    # noinspection PyUnusedLocal
    def _search_prop_vals(v: Any) -> list[Any]:
        """
        Utility function to search output properties (useful in IDE debugger)
        """

        def val_match(ga_p: Any) -> bool:
            # noinspection PyBroadException
            try:
                return v == ga_p or v == abs(ga_p) or abs(v) in [abs(x) for x in ga_p]
            except Exception:
                return False

        return [(p, ga(p)) for p in dir(soo) if val_match(ga(p))]

    if display_name not in _SINGLE_OWNER_OUTPUT_PROPERTIES:
        # noinspection PyBroadException
        try:
            ld = 'SAM Cash Flow Output property'
            _log.warning(f'{ld} not found for "{display_name}"')

            def show_suggestions(search_string: str):
                if search_string is None or search_string == '':
                    _log.debug(f'No {ld} suggestions for "{display_name}" found')
                    return

                suggest = [
                    (display_name, it[0], ga(it[0]))
                    for it in _search_props(search_string)
                    if not it[0].startswith('__')
                ]

                def data_preview(sg_2):
                    if not isinstance(sg_2, list) and not isinstance(sg_2, tuple):
                        return sg_2

                    idx = min(10, len(sg_2))
                    idx = min(idx, len(sg_2))
                    preview = tuple(sg_2[:idx])
                    if idx < len(sg_2):
                        preview += ('...',)
                    return preview

                suggest_display = "\n\t".join([f"'{sg[1]}',\n\t\t{data_preview(sg[2])}" for sg in suggest])
                if len(suggest) > 0:
                    _log.debug(f'{ld} suggestions for \n\'{display_name}\': \n\t{suggest_display}')
                else:
                    _log.debug(f'No {ld} suggestions for "{display_name}" found')
                    # In IDE debugger, try:
                    # show_suggestions(display_name.lower().split(' ')[1])
                    # etc.
                return suggest

            try:
                show_suggestions(next(it for it in display_name.lower().split(' ') if it.lower() != 'total'))
            except StopIteration:
                _log.debug(f'No {ld} suggestions for "{display_name}" found')

        except Exception as e:
            _log.debug(f'Encountered exception attempting to generate suggestions for {ld} for "{display_name}": {e}"')

        return None

    prop = _SINGLE_OWNER_OUTPUT_PROPERTIES[display_name]

    if callable(prop):
        return prop(soo)

    return getattr(soo, prop)


def _get_file_path(file_name) -> str:
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), file_name)


def _generate_mapping_from_module_doc(module_name: str = 'Cashloan'):
    with open(_get_file_path(f'sam_economics/{module_name}.html.txt'), encoding='utf-8') as f:
        # lines = f.readlines()

        txt = f.read()
        # lines = txt.split('PySAM.Cashloan.Cashloan.Outputs')[1].split('\n')
        txt = txt.split(f'PySAM.{module_name}.{module_name}.Outputs')[1].split('Outputs_vals =')[2]
        lines = txt.split('\n')[2:]

        _log.debug(f'Found {len(lines)} lines {module_name} in module doc')
        for i in range(0, len(lines), 8):
            prop = lines[i].strip()[:-1]
            if prop == '':
                continue
            display_name = lines[i + 2].strip().replace('[', '(').replace(']', ')')
            # _log.debug(f'Property: {prop}')
            if display_name not in _SINGLE_OWNER_OUTPUT_PROPERTIES:
                print(f"\t'{display_name}': '{prop}',  # {module_name}")


if __name__ == '__main__':
    _generate_mapping_from_module_doc('Cashloan')
    _generate_mapping_from_module_doc('Singleowner')

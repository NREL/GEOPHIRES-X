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
            if re.match(r'^[a-z]+:$', row_label):
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


def generate_mapping_from_cashloan_module_doc():

    with open(_get_file_path('sam_economics/cashloan.html.txt'), encoding='utf-8') as f:
        # lines = f.readlines()

        txt = f.read()
        # lines = txt.split('PySAM.Cashloan.Cashloan.Outputs')[1].split('\n')
        txt = txt.split('PySAM.Cashloan.Cashloan.Outputs')[1].split('Outputs_vals =')[2]
        lines = txt.split('\n')[2:]

        _log.debug(f'Found {len(lines)} lines cashloan in module doc')
        for i in range(0, len(lines), 8):
            prop = lines[i].strip()[:-1]
            if prop == '':
                continue
            display_name = lines[i + 2].strip().replace('[', '(').replace(']', ')')
            # _log.debug(f'Property: {prop}')
            if display_name not in _SINGLE_OWNER_OUTPUT_PROPERTIES:
                print(f"\t'{display_name}': '{prop}',")


if __name__ == '__main__':
    generate_mapping_from_cashloan_module_doc()

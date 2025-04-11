from typing import Any

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
}


def _get_single_owner_output(soo: Any, display_name: str) -> Any:
    """"
    TODO/WIP move to EconomicsSam.py

    :param soo: single_owner.Outputs
    :type soo: `PySAM.Singleowner.Outputs`
    """

    if display_name not in _SINGLE_OWNER_OUTPUT_PROPERTIES:
        return None

    # prop = getattr(soo, prop_map[display_name])
    prop = _SINGLE_OWNER_OUTPUT_PROPERTIES[display_name]

    if callable(prop):
        return prop(soo)

    return getattr(soo, prop)

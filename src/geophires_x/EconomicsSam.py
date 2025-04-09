from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from decimal import Decimal

import numpy as np
# noinspection PyPackageRequirements
from PySAM import CustomGeneration

# noinspection PyPackageRequirements
from PySAM import Grid

# noinspection PyPackageRequirements
from PySAM import Singleowner

# noinspection PyPackageRequirements
import PySAM.Utilityrate5 as UtilityRate

import geophires_x.Model as Model


def calculate_sam_economics(
        model: Model
) -> dict[str, dict[str, Any]]:
    custom_gen = CustomGeneration.new()
    grid = Grid.from_existing(custom_gen)
    utility_rate = UtilityRate.from_existing(custom_gen)
    single_owner = Singleowner.from_existing(custom_gen)

    project_name = 'Generic_400_MWe'
    project_dir = Path(os.path.dirname(model.economics.MyPath), 'sam_economics', project_name)
    # noinspection SpellCheckingInspection
    file_names = [f'{project_name}_{module}' for module in ['custom_generation', 'grid', 'utilityrate5', 'singleowner']]
    modules = [custom_gen, grid, utility_rate, single_owner]

    for module_file, module in zip(file_names, modules):
        with open(Path(project_dir, f'{module_file}.json'), encoding='utf-8') as file:
            data = json.load(file)
            for k, v in data.items():
                if k != 'number_inputs':
                    module.value(k, v)

    for k, v in _get_single_owner_parameters(model).items():
        single_owner.value(k, v)

    for module in modules:
        module.execute()

    display_data = [
        ('LCOE', single_owner.Outputs.lcoe_real, 'cents/kWh'),
        ('IRR', single_owner.Outputs.project_return_aftertax_irr, '%'),
        ('NPV', single_owner.Outputs.project_return_aftertax_npv * 1e-6, 'MUSD'),
        ('CAPEX', single_owner.Outputs.adjusted_installed_cost * 1e-6, 'MUSD'),
        # ('Gross Output', gt.Outputs.gross_output, 'MW'),
        # ('Net Output', gt.Outputs.gross_output - gt.Outputs.pump_work, 'MW')
    ]

    max_field_name_len = max(len(x[0]) for x in display_data)

    ret = {}
    for e in display_data:
        field_display = e[0] + ':' + ' ' * (max_field_name_len - len(e[0]) - 1)
        # print(f'{field_display}\t{sig_figs(e[1], 5)} {e[2]}')
        ret[e[0]] = {'value': _sig_figs(e[1], 5), 'unit': e[2]}

    return ret


def _get_single_owner_parameters(model: Model) -> dict[str, Any]:
    econ = model.economics

    ret: dict[str, Any] = {}

    itc = econ.CCap.value * econ.RITC.value
    total_capex_musd = (
            econ.CCap.value - itc
    )
    ret['total_installed_cost'] = total_capex_musd * 1e6

    opex_musd = econ.Coam.value
    ret['om_fixed'] = [opex_musd * 1e6]

    average_net_generation_MW = _get_average_net_generation_MW(model)
    ret['system_capacity'] = average_net_generation_MW * 1e3

    geophires_ctr_tenths = Decimal(econ.CTR.value)
    fed_rate_tenths = geophires_ctr_tenths * (Decimal(0.7))
    state_rate_tenths = geophires_ctr_tenths - fed_rate_tenths
    ret['federal_tax_rate'] = [float(fed_rate_tenths * Decimal(100))]
    ret['state_tax_rate'] = [float(state_rate_tenths * Decimal(100))]

    geophires_itc_tenths = Decimal(econ.RITC.value)
    ret['itc_fed_percent'] = [float(geophires_itc_tenths * Decimal(100))]

    geophires_ptr_tenths = Decimal(econ.PTR.value)
    ret['property_tax_rate'] = float(geophires_ptr_tenths * Decimal(100))

    ret['ppa_price_input'] = [econ.ElecStartPrice.value]

    return ret


def _get_average_net_generation_MW(model: Model) -> float:
    return np.average(model.surfaceplant.NetElectricityProduced.value)


def _sig_figs(val: float, num_sig_figs: int) -> float:
    if val is None:
        return None

    return float('%s' % float(f'%.{num_sig_figs}g' % val))  # pylint: disable=consider-using-f-string

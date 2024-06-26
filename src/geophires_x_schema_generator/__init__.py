import json
import os
import sys
from pathlib import Path
from typing import Tuple, Any

# Ruff disabled because imports are order-dependent
# ruff: noqa: I001
from geophires_x.Model import Model

from geophires_x.SFReservoir import SFReservoir
from geophires_x.LHSReservoir import LHSReservoir
from geophires_x.MPFReservoir import MPFReservoir
from geophires_x.AGSEconomics import AGSEconomics
from geophires_x.AGSWellBores import AGSWellBores
from geophires_x.CylindricalReservoir import CylindricalReservoir
from geophires_x.EconomicsAddOns import EconomicsAddOns
from geophires_x.EconomicsCCUS import EconomicsCCUS
from geophires_x.GeoPHIRESUtils import json_dumpse
from geophires_x.Parameter import Parameter
from geophires_x.SurfacePlantAGS import SurfacePlantAGS
from geophires_x.SurfacePlantSUTRA import SurfacePlantSUTRA
from geophires_x.SUTRAEconomics import SUTRAEconomics
from geophires_x.SUTRAReservoir import SUTRAReservoir
from geophires_x.SUTRAWellBores import SUTRAWellBores
from geophires_x.TDPReservoir import TDPReservoir


class GeophiresXSchemaGenerator:
    def __init__(self):
        pass

    def _get_dummy_model(self):
        stash_cwd = Path.cwd()
        stash_sys_argv = sys.argv
        sys.argv = ['']
        try:
            dummy_model = Model(enable_geophires_logging_config=False)
            return dummy_model
        finally:
            sys.argv = stash_sys_argv
            os.chdir(stash_cwd)

    def get_parameters_json(self) -> Tuple[str, str]:
        dummy_model = self._get_dummy_model()

        def with_category(param_dict: dict, category: str):
            def _with_cat(p: Parameter, cat: str):
                p.parameter_category = cat
                return p

            return {k: _with_cat(v, category) for k, v in param_dict.items()}

        parameter_sources = [
            (dummy_model.reserv, 'Reservoir'),
            (TDPReservoir(dummy_model), 'Reservoir'),
            (LHSReservoir(dummy_model), 'Reservoir'),
            (MPFReservoir(dummy_model), 'Reservoir'),
            (SFReservoir(dummy_model), 'Reservoir'),
            (CylindricalReservoir(dummy_model), 'Reservoir'),
            (SUTRAReservoir(dummy_model), 'Reservoir'),
            (dummy_model.wellbores, 'Well Bores'),
            (AGSWellBores(dummy_model), 'Well Bores'),
            (SUTRAWellBores(dummy_model), 'Well Bores'),
            (dummy_model.surfaceplant, 'Surface Plant'),
            (SurfacePlantAGS(dummy_model), 'Surface Plant'),
            (SurfacePlantSUTRA(dummy_model), 'Surface Plant'),
            (dummy_model.economics, 'Economics'),
            (AGSEconomics(dummy_model), 'Economics'),
            (SUTRAEconomics(dummy_model), 'Economics'),
            (EconomicsCCUS(dummy_model), 'Economics'),
            (EconomicsAddOns(dummy_model), 'Economics'),
        ]

        output_params = {}
        input_params = {}
        for param_source in parameter_sources:
            input_params.update(with_category(param_source[0].ParameterDict, param_source[1]))
            output_params.update(with_category(param_source[0].OutputParameterDict, param_source[1]))

        return json_dumpse(input_params), json_dumpse(output_params)

    def generate_json_schema(self) -> dict:
        input_params_json, output_params_json = self.get_parameters_json()
        input_params = json.loads(input_params_json)

        properties = {}
        required = []

        for param_name in input_params:
            param = input_params[param_name]

            units_val = param['CurrentUnits'] if isinstance(param['CurrentUnits'], str) else None
            min_val, max_val = _get_min_and_max(param, default_val=None)
            properties[param_name] = {
                'description': param['ToolTipText'],
                'type': param['json_parameter_type'],
                'units': units_val,
                'category': param['parameter_category'],
                'default': param['DefaultValue'],
                'minimum': min_val,
                'maximum': max_val,
            }

            if param['Required']:
                required.append(param_name)

            if param['ValuesEnum']:
                properties[param_name]['enum_values'] = param['ValuesEnum']

        schema = {
            'definitions': {},
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'type': 'object',
            'title': 'GEOPHIRES Schema',
            'required': required,
            'properties': properties,
        }

        return schema

    def generate_parameters_reference_rst(self) -> str:
        input_params_json, output_params_json = self.get_parameters_json()
        input_params: dict = json.loads(input_params_json)

        input_params_by_category: dict = {}
        for input_param_name, input_param in input_params.items():
            category: str = input_param['parameter_category']
            if category not in input_params_by_category:
                input_params_by_category[category] = {}  # []

            input_params_by_category[category][input_param_name] = input_param

        def get_input_params_table(category_params, category_name) -> str:
            input_rst = f"""
{category_name}
{'-' * len(category_name)}
    .. list-table:: {category_name} Parameters
       :header-rows: 1

       * - Name
         - Description
         - Preferred Units
         - Default Value Type
         - Default Value
         - Min
         - Max"""

            for param_name in category_params:
                param = input_params[param_name]

                # if param['Required']:
                #     TODO designate required params

                min_val, max_val = _get_min_and_max(param)

                input_rst += f"""\n       * - {param['Name']}
         - {_get_key(param, 'ToolTipText')}
         - {_get_key(param, 'PreferredUnits')}
         - {_get_key(param, 'json_parameter_type')}
         - {_get_key(param, 'DefaultValue')}
         - {min_val}
         - {max_val}"""

            return input_rst

        input_rst = ''
        for category, category_params in input_params_by_category.items():
            input_rst += get_input_params_table(category_params, category)

        output_rst = self.get_output_params_table_rst(output_params_json)

        rst = f"""Parameters
==========

.. contents::

Input Parameters
################
{input_rst}

Output Parameters
#################
{output_rst}
"""

        return rst

    def get_output_params_table_rst(self, output_params_json) -> str:
        output_params = json.loads(output_params_json)

        output_rst = """
    .. list-table:: Output Parameters
       :header-rows: 1

       * - Name
         - Preferred Units
         - Default Value Type"""

        for param_name in output_params:
            param = output_params[param_name]

            def get_key(k):
                if k in param and str(param[k]) != '':  # noqa
                    return param[k]  # noqa
                else:
                    return ''

            output_rst += f"""\n       * - {param['Name']}
         - {get_key('PreferredUnits')}
         - {get_key('json_parameter_type')}"""

        return output_rst


def _get_key(param: dict, k: str, default_val='') -> Any:
    if k in param and str(param[k]) != '':
        return param[k]
    else:
        return default_val


def _get_min_and_max(param: dict, default_val='') -> Tuple:
    min_val = _get_key(param, 'Min', default_val=default_val)
    max_val = _get_key(param, 'Max', default_val=default_val)

    if 'AllowableRange' in param:
        # TODO warn if min/max are defined and at odds with allowable range
        min_val = min(param['AllowableRange'])
        max_val = max(param['AllowableRange'])

    return (min_val, max_val)

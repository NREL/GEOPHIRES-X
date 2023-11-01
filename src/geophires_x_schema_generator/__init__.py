import json

from geophires_x.Model import Model


class GeophiresXSchemaGenerator:
    def __init__(self):
        pass

    def generate_json_schema(self) -> dict:
        input_params_json, output_params_json = Model(enable_geophires_logging_config=False).get_parameters_json()
        input_params = json.loads(input_params_json)

        properties = {}
        required = []

        for param_name in input_params:
            param = input_params[param_name]

            units_val = param['CurrentUnits'] if isinstance(param['CurrentUnits'], str) else None
            properties[param_name] = {
                'description': param['ToolTipText'],
                'type': param['json_parameter_type'],
                'units': units_val,
                'category': param['parameter_category'],
            }

            if param['Required']:
                required.append(param_name)

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
        input_params_json, output_params_json = Model(enable_geophires_logging_config=False).get_parameters_json()
        input_params = json.loads(input_params_json)

        def get_input_params_table(category_params, category_name='Input Parameters') -> str:
            input_rst = f"""
    .. list-table:: {category_name}
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

                def get_key(k):
                    if k in param and str(param[k]) != '':  # noqa
                        return param[k]  # noqa
                    else:
                        return ''

                min_val = get_key('Min')
                max_val = get_key('Max')

                if 'AllowableRange' in param:
                    # TODO warn if min/max are defined and at odds with allowable range
                    min_val = min(param['AllowableRange'])
                    max_val = max(param['AllowableRange'])

                    # TODO include full AllowableRange in reference (or fully describe if possible using min/max/increment)

                input_rst += f"""\n       * - {param['Name']}
         - {get_key('ToolTipText')}
         - {get_key('PreferredUnits')}
         - {get_key('json_parameter_type')}
         - {get_key('DefaultValue')}
         - {min_val}
         - {max_val}"""

            return input_rst

        input_rst = get_input_params_table(input_params, 'Input Parameters')
        output_rst = self.get_output_params_table_rst(output_params_json)

        rst = f"""Parameters
==========

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
import argparse
import json
from pathlib import Path

from geophires_x.Model import Model


def generate_schema() -> dict:
    params = json.loads(Model(enable_geophires_logging_config=False).get_parameters_json())

    properties = {}
    required = []
    rst = """Parameters
==========
    .. list-table:: Input Parameters
       :widths: 25 50 10 10 10 10 25
       :header-rows: 1

       * - Name
         - Description
         - Preferred Units
         - Default Value Type
         - Default Value
         - Min
         - Max"""

    for param_name in params:
        param = params[param_name]

        units_val = param['CurrentUnits'] if isinstance(param['CurrentUnits'], str) else None
        properties[param_name] = {
            'description': param['ToolTipText'],
            'type': param['json_parameter_type'],
            'units': units_val,
            'category': param['parameter_category'],
        }

        if param['Required']:
            required.append(param_name)

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

        rst += f"""\n       * - {param['Name']}
         - {get_key('ToolTipText')}
         - {get_key('PreferredUnits')}
         - {get_key('json_parameter_type')}
         - {get_key('DefaultValue')}
         - {min_val}
         - {max_val}"""

    schema = {
        'definitions': {},
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'type': 'object',
        'title': 'GEOPHIRES Schema',
        'required': required,
        'properties': properties,
    }

    return schema, rst


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-in-src', required=False, choices=[True, False], default=True)
    parser.add_argument('--build-path', required=False)
    args = parser.parse_args()
    build_in_src = args.build_in_src

    build_dir = Path(Path(__file__).parent)
    if not args.build_in_src:
        build_dir = Path(Path(__file__).parent.parent.parent, 'build')

    if args.build_path:
        build_dir = Path(args.build_path)

    build_dir.mkdir(exist_ok=True)

    build_path = Path(build_dir, 'geophires-request.json')

    schema_json, rst = generate_schema()

    with open(build_path, 'w') as f:
        f.write(json.dumps(schema_json, indent=2))
        print(f'Wrote schema file to {build_path}.')

    build_path_rst = Path(build_dir, 'parameters.rst')
    with open(build_path_rst, 'w') as f:
        f.write(rst)

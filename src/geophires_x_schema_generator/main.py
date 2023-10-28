import argparse
import json
from pathlib import Path

from geophires_x.Model import Model


def get_json_schema() -> dict:
    params = json.loads(Model(enable_geophires_logging_config=False).get_parameters_json())

    properties = {}
    required = []

    for param_name in params:
        param = params[param_name]

        properties[param_name] = {
            'description': param['ToolTipText'],
            'type': param['json_parameter_type'],
            'units': param['CurrentUnits'] if isinstance(param['CurrentUnits'], str) else None,
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-in-src', required=False, choices=[True, False], default=True)
    args = parser.parse_args()
    build_in_src = args.build_in_src

    build_dir = Path(Path(__file__).parent)
    if not args.build_in_src:
        build_dir = Path(Path(__file__).parent.parent.parent, 'build')

    build_dir.mkdir(exist_ok=True)

    build_path = Path(build_dir, 'geophires-request.json')
    with open(build_path, 'w') as f:
        f.write(json.dumps(get_json_schema(), indent=2))

    print(f'Wrote schema file to {build_path}.')

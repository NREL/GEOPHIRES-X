from __future__ import annotations

import argparse
import json
from pathlib import Path

from geophires_x_schema_generator import GeophiresXSchemaGenerator
from geophires_x_schema_generator import HipRaXSchemaGenerator


def generate_schemas(build_in_src: bool, build_path: str | Path) -> None:
    build_dir = Path(Path(__file__).parent)
    if not build_in_src:
        build_dir = Path(Path(__file__).parent.parent.parent, 'build')

    if build_path:
        build_dir = Path(build_path)

    build_dir.mkdir(exist_ok=True)

    def build(json_file_name_prefix: str, generator: GeophiresXSchemaGenerator, rst_file_name: str):
        request_schema_json, result_schema_json = generator.generate_json_schema()

        request_build_path = Path(build_dir, f'{json_file_name_prefix}request.json')
        with open(request_build_path, 'w', encoding='utf-8') as f:

            print(json.dumps(request_schema_json, indent=2), file=f)
            # using print([...], file=f) instead of f.write avoids need for pre-commit end of file fix

            print(f'Wrote request JSON schema file to {request_build_path}.')

        if result_schema_json is not None:
            result_build_path = Path(build_dir, f'{json_file_name_prefix}result.json')
            with open(result_build_path, 'w', encoding='utf-8') as f:
                print(json.dumps(result_schema_json, indent=2), file=f)
                print(f'Wrote result JSON schema file to {result_build_path}.')

        rst = generator.generate_parameters_reference_rst()

        build_path_rst = Path(build_dir, rst_file_name)
        with open(build_path_rst, 'w') as f:
            f.write(rst)
            print(f'Wrote RST file to {build_path_rst}.')

    build('geophires-', GeophiresXSchemaGenerator(), 'parameters.rst')
    build('hip-ra-x-', HipRaXSchemaGenerator(), 'hip_ra_x_parameters.rst')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-in-src', required=False, choices=[True, False], default=True)
    parser.add_argument('--build-path', required=False)
    args = parser.parse_args()
    build_in_src_ = args.build_in_src
    build_path_ = args.build_path if args.build_path else None
    generate_schemas(build_in_src_, build_path_)

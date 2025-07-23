from __future__ import annotations

import json
import tempfile
from pathlib import Path

from base_test_case import BaseTestCase
from geophires_x_schema_generator.main import generate_schemas


class GeneratedSchemasTestCase(BaseTestCase):

    def test_generated_schemas_up_to_date(self) -> None:
        try:
            build_dir: Path = Path(tempfile.gettempdir())
            generate_schemas(False, build_dir)

            def assert_schema(schema_file_name: str) -> None:
                with open(Path(build_dir, schema_file_name), encoding='utf-8') as f:
                    generated_geophires_request_schema = json.loads(f.read())

                src_geophires_request_path = Path(
                    self._get_test_file_path(f'../../src/geophires_x_schema_generator/{schema_file_name}')
                )
                with open(src_geophires_request_path, encoding='utf-8') as f:
                    src_geophires_request_schema = json.loads(f.read())

                self.assertDictEqual(generated_geophires_request_schema, src_geophires_request_schema)

            assert_schema('geophires-request.json')
            assert_schema('geophires-result.json')
            assert_schema('hip-ra-x-request.json')
        except AssertionError as ae:
            raise AssertionError(
                'Generated schemas in source are not up-to-date. '
                'Run src/geophires_x_schema_generator/main.py to update them.'
            ) from ae

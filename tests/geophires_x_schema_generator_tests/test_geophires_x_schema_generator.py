import json
import unittest

from geophires_x_schema_generator import GeophiresXSchemaGenerator
from tests.base_test_case import BaseTestCase


class GeophiresXSchemaGeneratorTestCase(BaseTestCase):
    def test_parameters_rst(self):
        g = GeophiresXSchemaGenerator()
        rst = g.generate_parameters_reference_rst()
        self.assertIsNotNone(rst)  # TODO sanity checks on content

    def test_outputs_rst(self):
        g = GeophiresXSchemaGenerator()
        _, output_params_json = g.get_parameters_json()
        rst = g.get_output_params_table_rst(output_params_json)

        self.assertIn(
            """ECONOMIC PARAMETERS
-------------------
    .. list-table:: ECONOMIC PARAMETERS Outputs
       :header-rows: 1

       * - Name
         - Description
         - Preferred Units
         - Default Value Type
       * - Economic Model
""",
            rst,
        )

        self.assertIn(
            """       * - Project IRR
         - Project Internal Rate of Return
         - %
         - number
""",
            rst,
        )

    def test_get_json_schema(self):
        g = GeophiresXSchemaGenerator()
        req_schema, result_schema = g.generate_json_schema()
        self.assertIsNotNone(req_schema)  # TODO sanity checks on content
        self.assertIsNotNone(result_schema)  # TODO sanity checks on content

        print(f'Generated result schema: {json.dumps(result_schema, indent=2)}')

        def get_result_prop(cat: str, name: str) -> dict:
            return result_schema['properties'][cat]['properties'][name]

        self.assertIn(
            'multiple of invested capital',
            get_result_prop('ECONOMIC PARAMETERS', 'Project MOIC')['description'].lower(),
        )

        self.assertIn(
            'Wellfield cost. ', get_result_prop('CAPITAL COSTS (M$)', 'Drilling and completion costs')['description']
        )


if __name__ == '__main__':
    unittest.main()

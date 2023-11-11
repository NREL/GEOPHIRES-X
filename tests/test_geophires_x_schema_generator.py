import unittest

from geophires_x_schema_generator import GeophiresXSchemaGenerator
from tests.base_test_case import BaseTestCase


class GeophiresXSchemaGeneratorTestCase(BaseTestCase):
    def test_parameters_rst(self):
        g = GeophiresXSchemaGenerator()
        rst = g.generate_parameters_reference_rst()
        self.assertIsNotNone(rst)  # TODO sanity checks on content


if __name__ == '__main__':
    unittest.main()

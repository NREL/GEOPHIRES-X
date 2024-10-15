import os
import sys
import tempfile
from pathlib import Path

from geophires_x.Model import Model
from geophires_x_client import GeophiresInputParameters
from geophires_x_client import GeophiresXClient
from tests.base_test_case import BaseTestCase


class OutputsTestCase(BaseTestCase):

    def test_html_output_file(self):
        html_path = Path(tempfile.gettempdir(), 'example12_DH.html').absolute()
        GeophiresXClient().get_geophires_result(
            GeophiresInputParameters(
                from_file_path=self._get_test_file_path('../examples/example12_DH.txt'),
                params={'HTML Output File': str(html_path)},
            )
        )
        self.assertTrue(html_path.exists())
        with open(html_path, encoding='UTF-8') as f:
            html_content = f.read()
            self.assertIn('***CASE REPORT***', html_content)
            # TODO expand test to assert more about output HTML

    def test_relative_output_file_path(self):
        input_file = GeophiresInputParameters({'HTML Output File': 'foo.html'}).as_file_path()
        m = self._new_model(input_file=input_file, original_cwd=Path('/tmp/'))  # noqa: S108
        html_filepath = Path(m.outputs.html_output_file.value)
        self.assertTrue(html_filepath.is_absolute())
        self.assertEqual(str(html_filepath).replace('D:', ''), str(Path('/tmp/foo.html')))  # noqa: S108

    def test_absolute_output_file_path(self):
        input_file = GeophiresInputParameters(
            {'HTML Output File': '/home/user/my-geophires-project/foo.html'}
        ).as_file_path()
        m = self._new_model(input_file=input_file, original_cwd=Path('/tmp/'))  # noqa: S108
        html_filepath = Path(m.outputs.html_output_file.value)
        self.assertTrue(html_filepath.is_absolute())
        self.assertEqual(str(html_filepath).replace('D:', ''), str(Path('/home/user/my-geophires-project/foo.html')))

    def _new_model(self, input_file=None, original_cwd=None) -> Model:
        stash_cwd = Path.cwd()
        stash_sys_argv = sys.argv

        sys.argv = ['']

        if input_file is not None:
            sys.argv.append(input_file)

        m = Model(enable_geophires_logging_config=False)

        if input_file is not None:
            m.read_parameters(default_output_path=original_cwd)

        sys.argv = stash_sys_argv
        os.chdir(stash_cwd)

        return m

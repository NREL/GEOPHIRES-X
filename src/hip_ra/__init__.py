import os
import re
import sys
import tempfile
import uuid
from pathlib import Path

from geophires_x_client.common import _get_logger
from hip_ra import HIP_RA


class HipRaInputParameters:
    def __init__(self, from_file_path: str):
        self._input_file_path = Path(from_file_path)
        self._output_file_path = Path(
            tempfile.gettempdir(), f'hip-ra-result_{self._input_file_path.stem}_{uuid.uuid1()!s}.out'
        )

    def as_file_path(self) -> Path:
        return self._input_file_path

    @property
    def output_file_path(self) -> Path:
        return self._output_file_path


class HipRaResult:
    def __init__(self, output_file_path):
        self.output_file_path = output_file_path
        self.result = self._parse_fields()

    def _parse_fields(self):
        with open(self.output_file_path) as f:
            text = f.read()
            pattern = re.compile(r'(.+?):\s+([0-9eE.+-]+)\s*(.+)+?')

            matches = re.findall(pattern, text)

            result = {
                key.strip(): {'value': float(value), 'unit': unit.strip()}
                if unit
                else {'value': float(value), 'unit': None}
                for key, value, unit in matches
            }

            return result


class HipRaClient:
    def __init__(self, enable_caching=True, logger_name='root'):
        self._logger = _get_logger(logger_name=logger_name)

    def get_hip_ra_result(self, input_params: HipRaInputParameters) -> HipRaResult:
        stash_cwd = Path.cwd()
        stash_sys_argv = sys.argv

        sys.argv = ['', input_params.as_file_path(), input_params.output_file_path]
        try:
            HIP_RA.main(enable_hip_ra_logging_config=False)
        except Exception as e:
            raise RuntimeError(f'HIP-RA encountered an exception: {e!s}') from e
        except SystemExit:
            raise RuntimeError('HIP-RA exited without giving a reason') from None
        finally:
            # Undo HIP-RA internal global settings changes
            sys.argv = stash_sys_argv
            os.chdir(stash_cwd)

        self._logger.info(f'HIP-RA output file: {input_params.output_file_path}')

        return HipRaResult(input_params.output_file_path)

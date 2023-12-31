import os
import sys
import tempfile
import uuid
from pathlib import Path

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


class HipRaClient:
    def __init__(self, enable_caching=True, logger_name='root'):
        # self._logger = _get_logger(logger_name=logger_name)
        pass

    def get_hip_ra_result(self, input_params: HipRaInputParameters) -> HipRaResult:
        stash_cwd = Path.cwd()
        stash_sys_argv = sys.argv

        sys.argv = ['', input_params.as_file_path(), input_params.output_file_path]
        try:
            HIP_RA.main(enable_geophires_logging_config=False)
        except Exception as e:
            raise RuntimeError(f'HIP_RA encountered an exception: {e!s}') from e
        except SystemExit:
            raise RuntimeError('HIP_RA exited without giving a reason') from None

        # Undo Geophires internal global settings changes
        sys.argv = stash_sys_argv
        os.chdir(stash_cwd)

        # self._logger.info(f'GEOPHIRES-X output file: {input_params.get_output_file_path()}')

        return HipRaResult(input_params.output_file_path)

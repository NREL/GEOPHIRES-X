import os
import sys
from pathlib import Path

from geophires_x_client.common import _get_logger
from hip_ra import HipRaInputParameters
from hip_ra import HipRaResult
from hip_ra_x import hip_ra_x


class HipRaXClient:
    def __init__(self, enable_caching=True, logger_name='root'):
        self._logger = _get_logger(logger_name=logger_name)

    def get_hip_ra_result(self, input_params: HipRaInputParameters) -> HipRaResult:
        stash_cwd = Path.cwd()
        stash_sys_argv = sys.argv

        sys.argv = ['', input_params.as_file_path(), input_params.output_file_path]
        try:
            hip_ra_x.main(enable_hip_ra_logging_config=False)
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

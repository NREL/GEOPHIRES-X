import json
import os
import sys
import threading
from pathlib import Path

# noinspection PyPep8Naming
from geophires_x import GEOPHIRESv3 as geophires

from .common import _get_logger
from .geophires_input_parameters import EndUseOption
from .geophires_input_parameters import GeophiresInputParameters
from .geophires_x_result import GeophiresXResult


class GeophiresXClient:
    def __init__(self, enable_caching=True, logger_name=None):
        if logger_name is None:
            logger_name = __name__

        self._logger = _get_logger(logger_name=logger_name)
        self._enable_caching = enable_caching
        self._cache = {}
        self._lock = threading.Lock()

    def get_geophires_result(self, input_params: GeophiresInputParameters) -> GeophiresXResult:
        """
        Calculates a GEOPHIRES result in a thread-safe manner.

        This method ensures thread safety by using a lock to serialize access,
        preventing race conditions on the cache and corruption of global state
        (sys.argv, os.cwd) that GEOPHIRES modifies.
        """
        with self._lock:
            cache_key = hash(input_params)
            if self._enable_caching and cache_key in self._cache:
                return self._cache[cache_key]

            stash_cwd = Path.cwd()
            stash_sys_argv = sys.argv

            sys.argv = ['', input_params.as_file_path(), input_params.get_output_file_path()]
            try:
                geophires.main(enable_geophires_logging_config=False)
            except Exception as e:
                raise RuntimeError(f'GEOPHIRES encountered an exception: {e!s}') from e
            except SystemExit:
                raise RuntimeError('GEOPHIRES exited without giving a reason') from None
            finally:
                # Ensure global state is restored even if geophires.main() fails
                sys.argv = stash_sys_argv
                os.chdir(stash_cwd)

            self._logger.info(f'GEOPHIRES-X output file: {input_params.get_output_file_path()}')

            result = GeophiresXResult(input_params.get_output_file_path())
            if self._enable_caching:
                self._cache[cache_key] = result

            return result


if __name__ == '__main__':
    client = GeophiresXClient()
    log = _get_logger()

    # noinspection PyTypeChecker
    params = GeophiresInputParameters(
        {
            'Print Output to Console': 0,
            'End-Use Option': EndUseOption.DIRECT_USE_HEAT.value,
            'Reservoir Model': 1,
            'Time steps per year': 1,
            'Reservoir Depth': 3,
            'Gradient 1': 50,
            'Maximum Temperature': 250,
        }
    )

    result_ = client.get_geophires_result(params)
    log.info(f'Breakeven price: ${result_.direct_use_heat_breakeven_price_USD_per_MMBTU}/MMBTU')
    log.info(json.dumps(result_.result, indent=2))

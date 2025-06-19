import json
import os
import sys
from multiprocessing import Manager
from pathlib import Path

# noinspection PyPep8Naming
from geophires_x import GEOPHIRESv3 as geophires

from .common import _get_logger
from .geophires_input_parameters import EndUseOption
from .geophires_input_parameters import GeophiresInputParameters
from .geophires_x_result import GeophiresXResult


class GeophiresXClient:
    # Use a multiprocessing Manager to create a cache and lock that are
    # shared across all processes spawned by a ProcessPoolExecutor.
    _manager = Manager()
    _cache = _manager.dict()
    _lock = _manager.Lock()

    def __init__(self, enable_caching=True, logger_name=None):
        if logger_name is None:
            logger_name = __name__

        self._logger = _get_logger(logger_name=logger_name)
        self.enable_caching = enable_caching

    def get_geophires_result(self, input_params: GeophiresInputParameters) -> GeophiresXResult:
        if not self.enable_caching:
            return self._run_geophires(input_params)

        cache_key = hash(input_params)
        with self.__class__._lock:
            # Use a lock to ensure the check-and-set operation is atomic.
            if cache_key in self.__class__._cache:
                # Cache hit
                return self.__class__._cache[cache_key]

            # If not in cache, we will run the simulation, still under the lock,
            # to prevent a race condition with other processes.
            # Cache miss
            result = self._run_geophires(input_params)
            self.__class__._cache[cache_key] = result
            return result

    def _run_geophires(self, input_params: GeophiresInputParameters) -> GeophiresXResult:
        """Helper method to encapsulate the actual GEOPHIRES execution."""
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
            # Ensure we always restore the original state
            sys.argv = stash_sys_argv
            os.chdir(stash_cwd)

        self._logger.info(f'GEOPHIRES-X output file: {input_params.get_output_file_path()}')
        return GeophiresXResult(input_params.get_output_file_path())


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

import json
import os
import sys
import threading
from multiprocessing import Manager
from pathlib import Path

from geophires_x import GEOPHIRESv3 as geophires

from .common import _get_logger
from .geophires_input_parameters import EndUseOption
from .geophires_input_parameters import GeophiresInputParameters
from .geophires_x_result import GeophiresXResult


class GeophiresXClient:
    # --- Class-level shared resources ---
    # These will be initialized lazily and shared across all instances and processes.
    _manager = None
    _cache = None
    _lock = None  # This will be a process-safe RLock from the manager.

    # A standard threading lock to make the one-time initialization thread-safe.
    _init_lock = threading.Lock()

    def __init__(self, enable_caching=True, logger_name=None):
        if logger_name is None:
            logger_name = __name__

        self._logger = _get_logger(logger_name=logger_name)
        self._enable_caching = enable_caching

        # Lazy-initialize shared resources if they haven't been already.
        # This approach is safe to call from multiple threads/processes.
        if GeophiresXClient._manager is None:
            self._initialize_shared_resources()

    @classmethod
    def _initialize_shared_resources(cls):
        """
        Initializes the multiprocessing Manager and shared resources (cache, lock)
        in a thread-safe and process-safe manner.
        """
        # Use a thread-safe lock to ensure this block only ever runs once
        # across all threads in the main process.
        with cls._init_lock:
            # The double-check locking pattern ensures we don't try to
            # re-initialize if another thread finished while we were waiting.
            if cls._manager is None:
                cls._manager = Manager()
                cls._cache = cls._manager.dict()
                cls._lock = cls._manager.RLock()  # The Manager now creates the lock.

    def get_geophires_result(self, input_params: GeophiresInputParameters) -> GeophiresXResult:
        """
        Calculates a GEOPHIRES result in a thread-safe and process-safe manner.
        """
        # Use the process-safe lock from the manager to make the check-then-act
        # operation on the cache fully atomic across multiple processes.
        with GeophiresXClient._lock:
            cache_key = hash(input_params)
            if self._enable_caching and cache_key in GeophiresXClient._cache:
                return GeophiresXClient._cache[cache_key]

            # --- This section is now guaranteed to run only once per unique input ---
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
    # This block remains for direct testing of the script.
    client = GeophiresXClient()
    log = _get_logger()

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

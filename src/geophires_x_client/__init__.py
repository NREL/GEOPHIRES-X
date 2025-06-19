import json
import os
import sys

# --- MULTIPROCESSING CHANGES ---
from multiprocessing import Manager
from multiprocessing import RLock
from pathlib import Path

from geophires_x import GEOPHIRESv3 as geophires

from .common import _get_logger
from .geophires_input_parameters import EndUseOption
from .geophires_input_parameters import GeophiresInputParameters
from .geophires_x_result import GeophiresXResult


class GeophiresXClient:
    # --- LAZY-LOADED, PROCESS-SAFE SINGLETONS ---
    # Define class-level placeholders. These will be shared across all instances.
    _manager = None
    _cache = None
    _lock = RLock()  # Use a process-safe re-entrant lock

    def __init__(self, enable_caching=True, logger_name=None):
        if logger_name is None:
            logger_name = __name__

        self._logger = _get_logger(logger_name=logger_name)
        self._enable_caching = enable_caching

        # This method will safely initialize the shared manager and cache
        # only when the first client instance is created.
        self._initialize_shared_resources()

    @classmethod
    def _initialize_shared_resources(cls):
        """
        Initializes the multiprocessing Manager and shared cache dictionary.
        This method is designed to be called safely by multiple processes,
        ensuring the manager is only started once.
        """
        with cls._lock:
            if cls._manager is None:
                # This code is now protected. It won't run on module import.
                # It runs only when the first GeophiresXClient is instantiated.
                cls._manager = Manager()
                cls._cache = cls._manager.dict()

    def get_geophires_result(self, input_params: GeophiresInputParameters) -> GeophiresXResult:
        # Use the class-level lock to protect access to the shared cache
        # and the non-reentrant GEOPHIRES core.
        with GeophiresXClient._lock:
            cache_key = hash(input_params)
            if self._enable_caching and cache_key in GeophiresXClient._cache:
                return GeophiresXClient._cache[cache_key]

            # ... (The rest of your logic remains the same)
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
                sys.argv = stash_sys_argv
                os.chdir(stash_cwd)

            self._logger.info(f'GEOPHIRES-X output file: {input_params.get_output_file_path()}')

            result = GeophiresXResult(input_params.get_output_file_path())
            if self._enable_caching:
                GeophiresXClient._cache[cache_key] = result

            return result


if __name__ == '__main__':
    # This block is safe, as it's protected from being run on import.
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

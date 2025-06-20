import atexit
import os
import sys
import threading
from multiprocessing import Manager
from pathlib import Path

# noinspection PyPep8Naming
from geophires_x import GEOPHIRESv3 as geophires

from .common import _get_logger
from .geophires_input_parameters import GeophiresInputParameters
from .geophires_input_parameters import ImmutableGeophiresInputParameters
from .geophires_x_result import GeophiresXResult


class GeophiresXClient:
    """
    A thread-safe and process-safe client for running GEOPHIRES simulations.
    It automatically manages a background process via atexit and provides an
    explicit shutdown() method for advanced use cases like testing.
    """

    # --- Class-level shared resources ---
    _manager = None
    _cache = None
    _lock = None

    _init_lock = threading.Lock()
    """A standard threading lock to make the one-time initialization thread-safe."""

    def __init__(self, enable_caching=True, logger_name=None):
        if logger_name is None:
            logger_name = __name__

        self._logger = _get_logger(logger_name=logger_name)
        self._enable_caching = enable_caching

        # Lazy-initialize shared resources if they haven't been already.
        if enable_caching and GeophiresXClient._manager is None:
            self._initialize_shared_resources()

    @classmethod
    def _initialize_shared_resources(cls):
        """
        Initializes the multiprocessing Manager and shared resources in a
        thread-safe manner. It also registers the shutdown hook to ensure
        automatic cleanup on application exit.
        """
        with cls._init_lock:
            if cls._manager is None:
                cls._manager = Manager()
                cls._cache = cls._manager.dict()
                cls._lock = cls._manager.RLock()
                # Register the shutdown method to be called automatically on exit.
                atexit.register(cls.shutdown)

    @classmethod
    def shutdown(cls):
        """
        Explicitly shuts down the background manager process and de-registers
        the atexit hook to prevent errors if called multiple times.
        This is useful for test suites or applications that need to precisely
        control the resource lifecycle.
        """
        with cls._init_lock:
            if cls._manager is not None:
                cls._manager.shutdown()
                # De-register the hook to avoid trying to shut down twice.
                atexit.unregister(cls.shutdown)
                cls._manager = None
                cls._cache = None
                cls._lock = None

    def get_geophires_result(self, input_params: GeophiresInputParameters) -> GeophiresXResult:
        """
        Calculates a GEOPHIRES result, using a cross-process cache to avoid
        re-computing results for the same inputs. Caching is only effective
        when providing an instance of ImmutableGeophiresInputParameters.
        """
        is_immutable = isinstance(input_params, ImmutableGeophiresInputParameters)

        if not (self._enable_caching and is_immutable):
            return self._run_simulation(input_params)

        cache_key = hash(input_params)

        with GeophiresXClient._lock:
            if cache_key in GeophiresXClient._cache:
                return GeophiresXClient._cache[cache_key]

            result = self._run_simulation(input_params)
            GeophiresXClient._cache[cache_key] = result
            return result

    def _run_simulation(self, input_params: GeophiresInputParameters) -> GeophiresXResult:
        """Helper method to encapsulate the actual GEOPHIRES run."""
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
        return result

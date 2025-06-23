import atexit
import sys
import threading
from multiprocessing import Manager
from multiprocessing import current_process

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

    def __init__(self, enable_caching=False, logger_name=None):
        if logger_name is None:
            logger_name = __name__

        self._logger = _get_logger(logger_name=logger_name)
        self._enable_caching = enable_caching

        if enable_caching and GeophiresXClient._manager is None:
            # Lazy-initialize shared resources if they haven't been already.
            self._initialize_shared_resources()

    @classmethod
    def _initialize_shared_resources(cls):
        """
        Initializes the multiprocessing Manager and shared resources in a
        thread-safe and now process-safe manner. It also registers the
        shutdown hook to ensure automatic cleanup on application exit.
        """
        # Ensure that only the top-level user process can create the manager.
        # A spawned child process, which re-imports this script, will have a different name
        # (e.g., 'Spawn-1') and will skip this entire block, preventing a recursive crash.
        if current_process().name == 'MainProcess':
            with cls._init_lock:
                if cls._manager is None:
                    cls._logger = _get_logger(__name__)  # Add a logger for this class method
                    cls._logger.debug('MainProcess is creating the shared multiprocessing manager...')
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
                cls._logger = _get_logger(__name__)
                cls._logger.debug('Shutting down the shared multiprocessing manager...')
                cls._manager.shutdown()
                # De-register the hook to avoid trying to shut down twice.
                try:
                    atexit.unregister(cls.shutdown)
                except Exception as e:
                    # Fails in some environments (e.g. pytest), but is not critical
                    cls._logger.debug(
                        f'Encountered exception shutting down the shared multiprocessing manager (OK): ' f'{e!s}'
                    )
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

        if not (self._enable_caching and is_immutable and GeophiresXClient._manager is not None):
            return self._run_simulation(input_params)

        cache_key = hash(input_params)

        with GeophiresXClient._lock:
            if cache_key in GeophiresXClient._cache:
                # self._logger.debug(f'Cache hit for inputs: {input_params}')
                return GeophiresXClient._cache[cache_key]

            # Cache miss
            result = self._run_simulation(input_params)
            GeophiresXClient._cache[cache_key] = result
            return result

    def _run_simulation(self, input_params: GeophiresInputParameters) -> GeophiresXResult:
        """Helper method to encapsulate the actual GEOPHIRES run."""
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

        self._logger.info(f'GEOPHIRES-X output file: {input_params.get_output_file_path()}')
        result = GeophiresXResult(input_params.get_output_file_path())
        return result

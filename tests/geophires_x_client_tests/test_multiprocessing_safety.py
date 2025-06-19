import logging
import multiprocessing
import sys
import time
import unittest
from logging.handlers import QueueHandler
from queue import Empty

from geophires_x_client import EndUseOption

# Important: We must be able to import the client
from geophires_x_client import GeophiresXClient
from geophires_x_client.geophires_input_parameters import ImmutableGeophiresInputParameters


# This is the function that each worker process will execute.
# It must be a top-level function to be picklable by multiprocessing.
def run_client_in_process(params_dict: dict, log_queue: multiprocessing.Queue, result_queue: multiprocessing.Queue):
    """
    Instantiates a client and runs a calculation, reporting results
    and logs back to the main process via queues.
    """
    # Configure logging for this worker process to send messages to the shared queue.
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [QueueHandler(log_queue)]

    try:
        client = GeophiresXClient(enable_caching=True)
        params = ImmutableGeophiresInputParameters(params_dict)

        # This now calls the REAL geophires.main via the client.
        result = client.get_geophires_result(params)

        # Put the primitive result into the queue to avoid serialization issues.
        result_queue.put(result.direct_use_heat_breakeven_price_USD_per_MMBTU)
    except Exception as e:
        # Report any exceptions back to the main process.
        result_queue.put(e)


class TestMultiprocessingSafety(unittest.TestCase):
    # Class-level attributes to manage shared resources across test runs.
    _ctx = None
    _client_for_setup = None

    @classmethod
    def setUpClass(cls):
        """
        Set up the multiprocessing context and start the shared Manager
        process ONCE before any tests in this class run.
        """
        if sys.platform == 'win32':
            # Skip all tests in this class if not on a fork-supporting OS.
            raise unittest.SkipTest("The 'fork' multiprocessing context is not available on Windows.")

        cls._ctx = multiprocessing.get_context('fork')
        # Instantiating the client here creates the shared _manager and _cache
        # that all child processes forked from this test will inherit.
        cls._client_for_setup = GeophiresXClient()

    @classmethod
    def tearDownClass(cls):
        """
        Shut down the shared Manager process ONCE after all tests in this
        class have finished. This is the key to preventing hanging processes.
        """
        if cls._client_for_setup and hasattr(cls._client_for_setup, '_manager'):
            if cls._client_for_setup._manager is not None:
                cls._client_for_setup._manager.shutdown()

    def setUp(self):
        """Set up a shared set of parameters for each test."""
        # This setup runs before each individual test method.
        self.params_dict = {
            'Print Output to Console': 0,
            'End-Use Option': EndUseOption.DIRECT_USE_HEAT.value,
            'Reservoir Model': 1,
            'Time steps per year': 1,
            # Use nanoseconds to ensure each test run gets a unique cache key (Use a different value per run)
            'Reservoir Depth': 4 + time.time_ns() / 1e19,
            'Gradient 1': 50,
            'Maximum Temperature': 550,
        }

    def test_client_runs_real_geophires_and_caches_across_processes(self):
        """
        Tests that GeophiresXClient can run the real geophires.main in multiple
        processes and that the cache is shared between them.
        """
        log_queue = self._ctx.Queue()
        result_queue = self._ctx.Queue()
        num_processes = 8
        # Timeout should be long enough for at least one successful run.
        process_timeout_seconds = 5

        processes = [
            self._ctx.Process(target=run_client_in_process, args=(self.params_dict, log_queue, result_queue))
            for _ in range(num_processes)
        ]

        for p in processes:
            p.start()

        # --- Robust Result Collection ---
        results = []
        for i in range(num_processes):
            try:
                result = result_queue.get(timeout=process_timeout_seconds)
                results.append(result)
            except Empty:
                # Terminate running processes before failing to avoid hanging the suite
                for p_cleanup in processes:
                    if p_cleanup.is_alive():
                        p_cleanup.terminate()
                self.fail(f'Test timed out waiting for result #{i + 1}. A worker process likely crashed or is stuck.')

        # --- Process Cleanup ---
        # With the robust tearDownClass, a simple join is sufficient here.
        for p in processes:
            p.join(timeout=process_timeout_seconds)

        # --- Assertions ---
        # 1. Check that no process returned an exception.
        for r in results:
            self.assertNotIsInstance(r, Exception, f'A process failed with an exception: {r}')

        # 2. Check that all processes got a valid, non-None result.
        for r in results:
            self.assertIsNotNone(r)
            self.assertIsInstance(r, float)

        # 3. CRITICAL: Assert that the expensive GEOPHIRES calculation was only run ONCE.
        #    This assertion is expected to fail until the caching bug in the client is fixed.
        log_records = []
        while not log_queue.empty():
            log_records.append(log_queue.get().getMessage())

        cache_indicator_log = 'GEOPHIRES-X output file:'
        successful_runs = sum(1 for record in log_records if cache_indicator_log in record)

        self.assertEqual(
            1,
            successful_runs,
            f'FAIL: GEOPHIRES was run {successful_runs} times instead of once, indicating the cross-process cache failed.',
        )

        print(f'\nDetected {successful_runs} non-cached GEOPHIRES run(s) for {num_processes} requests.')


if __name__ == '__main__':
    unittest.main()

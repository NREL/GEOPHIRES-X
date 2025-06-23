import logging
import multiprocessing
import sys
import time
import unittest
from logging.handlers import QueueHandler
from queue import Empty

# Important: We must be able to import the client and all parameter classes
from geophires_x_client import GeophiresXClient
from geophires_x_client.geophires_input_parameters import EndUseOption
from geophires_x_client.geophires_input_parameters import ImmutableGeophiresInputParameters


def run_client_in_process(params_dict: dict, log_queue: multiprocessing.Queue, result_queue: multiprocessing.Queue):
    """
    This is the function that each worker process will execute.
    It must be a top-level function to be picklable by multiprocessing.
    """
    # Configure logging for this worker process to send messages to the shared queue.
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [QueueHandler(log_queue)]

    try:
        # The client will use the Manager that was injected by the test's main process.
        client = GeophiresXClient(enable_caching=True)
        params = ImmutableGeophiresInputParameters(params_dict)
        result = client.get_geophires_result(params)
        result_queue.put(result.direct_use_heat_breakeven_price_USD_per_MMBTU)
    except Exception as e:
        result_queue.put(e)


class TestMultiprocessingSafety(unittest.TestCase):
    def setUp(self):
        """Set up a unique set of parameters for each test."""
        self.params_dict = {
            'Print Output to Console': 0,
            'End-Use Option': EndUseOption.DIRECT_USE_HEAT.value,
            'Reservoir Model': 1,
            'Time steps per year': 1,
            'Reservoir Depth': 4 + time.time_ns() / 1e19,
            'Gradient 1': 50,
            'Maximum Temperature': 550,
        }

    def test_client_runs_real_geophires_and_caches_across_processes(self):
        """
        Tests that GeophiresXClient can run the real geophires.main in multiple
        processes and that the cache is shared between them. This test is now
        fully self-contained to prevent resource conflicts with the test runner.
        """
        if sys.platform == 'win32':
            self.skipTest("The 'fork' multiprocessing context is not available on Windows.")

        ctx = multiprocessing.get_context('fork')
        # Use the Manager as a context manager. This is the key to ensuring
        # all resources it creates (queues, etc.) are properly shut down
        # at the end of the block, preventing deadlocks.
        with ctx.Manager() as manager:
            # For this test to work, we MUST inject the test-specific manager
            # into the client's class-level singleton attributes.
            GeophiresXClient._manager = manager
            GeophiresXClient._cache = manager.dict()
            GeophiresXClient._lock = manager.RLock()

            log_queue = manager.Queue()
            result_queue = manager.Queue()

            num_processes = 4
            process_timeout_seconds = 15

            processes = [
                ctx.Process(target=run_client_in_process, args=(self.params_dict, log_queue, result_queue))
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
                    for p_cleanup in processes:
                        if p_cleanup.is_alive():
                            p_cleanup.terminate()
                    self.fail(
                        f'Test timed out waiting for result #{i + 1}. A worker process likely crashed or is stuck.'
                    )

            # --- Process Cleanup ---
            for p in processes:
                p.join(timeout=process_timeout_seconds)
                if p.is_alive():
                    p.terminate()
                    self.fail(f'Process {p.pid} failed to terminate cleanly.')

            # --- Assertions ---
            for r in results:
                self.assertNotIsInstance(r, Exception, f'A process failed with an exception: {r}')
                self.assertIsNotNone(r)
                self.assertIsInstance(r, float)

            log_records = []
            while not log_queue.empty():
                log_records.append(log_queue.get().getMessage())

            cache_indicator_log = 'GEOPHIRES-X output file:'
            successful_runs = sum(1 for record in log_records if cache_indicator_log in record)

            self.assertEqual(
                successful_runs,
                1,
                f'FAIL: GEOPHIRES was run {successful_runs} times instead of once, indicating the cache failed.',
            )

            print(
                f'\nTest passed: Detected {successful_runs} non-cached GEOPHIRES run(s) for {num_processes} requests.'
            )

        # CRITICAL: Reset the client's singleton state after the test to not interfere with other tests.
        GeophiresXClient._manager = None
        GeophiresXClient._cache = None
        GeophiresXClient._lock = None


if __name__ == '__main__':
    unittest.main()

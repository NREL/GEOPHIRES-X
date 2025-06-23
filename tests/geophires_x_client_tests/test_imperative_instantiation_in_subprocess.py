# ruff: noqa: S603

import subprocess
import sys
import tempfile
from pathlib import Path

from base_test_case import BaseTestCase


class GeophiresClientImperativeInstantiationTestCase(BaseTestCase):

    # noinspection PyMethodMayBeStatic
    def test_imperative_instantiation_in_subprocess(self):
        """
        Verifies that GeophiresXClient can be instantiated at the global scope
        in a script without causing a multiprocessing-related RuntimeError.

        This test directly simulates the failure condition by writing and executing
        a separate Python script as a subprocess. This ensures that the fix
        (checking for 'MainProcess') is working correctly on systems that use
        the 'spawn' start method for multiprocessing (like macOS and Windows).
        """
        project_root = Path(__file__).parent.parent.resolve()

        script_content = f"""
import sys
# We must add the project root to the path for the import to work.
sys.path.insert(0, r'{project_root}')

from geophires_x_client import GeophiresXClient

print("Attempting to instantiate GeophiresXClient at the global scope...")

# This is the line that would have previously crashed with a RuntimeError.
client = GeophiresXClient()

print("Instantiation successful.")

# It is critical to shut down the client to release the manager process,
# otherwise it can linger and interfere with other tests in the suite.
GeophiresXClient.shutdown()

print("Shutdown successful.")

# A final message to confirm the script completed without errors.
print("SUCCESS")
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            test_script_path = Path(tmpdir) / 'run_client_test.py'
            test_script_path.write_text(script_content)

            # fmt:off
            result = subprocess.run(
                [sys.executable, str(test_script_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            # fmt:on

        assert result.returncode == 0, (
            f'Subprocess failed with exit code {result.returncode}. This indicates a crash.\\n'
            f'--- STDOUT ---\\n{result.stdout}\\n'
            f'--- STDERR ---\\n{result.stderr}'
        )

        assert 'SUCCESS' in result.stdout, (
            "Subprocess completed but did not print the final 'SUCCESS' message.\\n" f"--- STDOUT ---\\n{result.stdout}"
        )

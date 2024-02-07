import os
import sys
from enum import Enum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

from geophires_monte_carlo import MC_GeoPHIRES3
from geophires_monte_carlo.common import _get_logger


class SimulationProgram(str, Enum):
    GEOPHIRES = 'GEOPHIRES', 'geophires_x/GEOPHIRESv3.py'
    HIP_RA = 'HIP-RA', 'hip_ra/HIP_RA.py'

    def __new__(cls, *args, **kwds):
        obj = str.__new__(cls)
        obj._value_ = args[0]
        return obj

    # ignore the first param since it's already set by __new__
    def __init__(self, _: str, code_file_path: str):
        self._code_file_path: Path = Path(Path(os.path.abspath(__file__)).parent.parent, code_file_path)

    # this makes sure that the description is read-only
    @property
    def code_file_path(self) -> Path:
        return self._code_file_path


class MonteCarloRequest:
    def __init__(
        self,
        simulation_program: SimulationProgram,
        input_file: Path,
        monte_carlo_settings_file: Path,
        output_file: Optional[Path] = None,
    ):
        self._simulation_program: SimulationProgram = simulation_program

        if not input_file.is_absolute():
            raise ValueError(f'Input file path ({input_file}) must be absolute')
        self.input_file = input_file

        if not monte_carlo_settings_file.is_absolute():
            raise ValueError(f'Monte Carlo settings file path ({monte_carlo_settings_file}) must be absolute')
        self.monte_carlo_settings_file = monte_carlo_settings_file

        if output_file is not None:
            self.output_file: Path = output_file
        else:
            self._temp_output_dir: TemporaryDirectory = TemporaryDirectory(prefix='geophires_monte_carlo-')
            self.output_file: Path = Path(self._temp_output_dir.name, 'MC_GEOPHIRES_Result.txt').absolute()

        if not self.output_file.is_absolute():
            raise ValueError(f'Output file path ({output_file}) must be absolute')

    @property
    def code_file_path(self) -> Path:
        return self._simulation_program.code_file_path

    def __del__(self):
        if hasattr(self, '_temp_output_dir'):
            self._temp_output_dir.cleanup()


class MonteCarloResult:
    def __init__(self, request: MonteCarloRequest):
        self._request: MonteCarloRequest = request

    @property
    def output_file_path(self) -> Path:
        return self._request.output_file

    # TODO expose properties in result


class GeophiresMonteCarloClient:
    def __init__(self):
        self._logger = _get_logger()

    def get_monte_carlo_result(self, request: MonteCarloRequest) -> MonteCarloResult:
        stash_cwd = Path.cwd()
        stash_sys_argv = sys.argv

        sys.argv = ['', str(request.code_file_path), str(request.input_file), str(request.monte_carlo_settings_file)]
        if request.output_file is not None:
            sys.argv.append(str(request.output_file))

        try:
            MC_GeoPHIRES3.main()
        except Exception as e:
            raise RuntimeError(f'Monte Carlo encountered an exception: {e!s}') from e
        except SystemExit:
            raise RuntimeError('Monte Carlo exited without giving a reason') from None
        finally:
            # Undo MC internal global settings changes
            sys.argv = stash_sys_argv
            os.chdir(stash_cwd)

        return MonteCarloResult(request)

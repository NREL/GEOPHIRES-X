import os
import sys
from pathlib import Path

from geophires_monte_carlo import MC_GeoPHIRES3
from geophires_monte_carlo import common

if __name__ == '__main__':
    log = common._get_logger()
    stash_cwd = Path.cwd()

    try:
        command_line_args = []
        for i in range(len(sys.argv[1:])):
            arg = sys.argv[i + 1]
            if Path(arg).exists():
                arg = str(Path(arg).absolute())
                log.info(f'Converted arg to absolute path: {arg}')

            command_line_args.append(arg)

        MC_GeoPHIRES3.main(command_line_args=command_line_args)
    except Exception as e:
        raise RuntimeError(f'Monte Carlo encountered an exception: {e!s}') from e
    except SystemExit:
        raise RuntimeError('Monte Carlo exited without giving a reason') from None
    finally:
        # Undo MC internal global settings changes
        os.chdir(stash_cwd)

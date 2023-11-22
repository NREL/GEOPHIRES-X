from geophires_x import GEOPHIRESv3 as geophires
from pathlib import Path
import sys
import os

stash_cwd = Path.cwd()
stash_sys_argv = sys.argv

if len(sys.argv) >= 2:
    sys.argv[1] = Path(sys.argv[1]).absolute()

if len(sys.argv) >= 3:
    sys.argv[2] = Path(sys.argv[2]).absolute()

try:
    geophires.main()
finally:
    # Undo Geophires internal global settings changes
    sys.argv = stash_sys_argv
    os.chdir(stash_cwd)



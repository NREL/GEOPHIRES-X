import argparse

from geophires_x import GEOPHIRESv3 as geophires
from pathlib import Path
import sys
import os

parser = argparse.ArgumentParser(description='GEOPHIRES-X CLI')
parser.add_argument('input-file', nargs=1, help='Input file path')
parser.add_argument('output-file', nargs='?', help='Output file path')
parsed_args = {k: v for k, v in vars(parser.parse_args()).items() if v is not None}

stash_cwd = Path.cwd()
stash_sys_argv = sys.argv

if 'input-file' in parsed_args:
    sys.argv[1] = Path(parsed_args['input-file'][0]).absolute()

if 'output-file' in parsed_args:
    sys.argv[2] = Path(parsed_args['output-file'][0]).absolute()
else:
    if len(sys.argv) < 3:
        sys.argv.append('')

    sys.argv[2] = Path(stash_cwd, 'HDR.out').absolute()

rc = 1
try:
    geophires.main()
    rc = 0
finally:
    # Undo internal global settings changes
    sys.argv = stash_sys_argv
    os.chdir(stash_cwd)

sys.exit(rc)

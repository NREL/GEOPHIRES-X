#!/bin/zsh


# Use this script to regenerate example results in cases where changes in GEOPHIRES
# calculations alter the example test output. Example:
# ./tests/regenerate-example-result.sh SUTRAExample1
# See https://github.com/NREL/GEOPHIRES-X/issues/107


cd "$(dirname "$0")"
python -mgeophires_x examples/$1.txt examples/$1.out
rm examples/$1.json

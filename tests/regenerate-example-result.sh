#!/bin/zsh


# Use this script to regenerate example results in cases where changes in GEOPHIRES
# calculations alter the example test output. Example:
# ./tests/regenerate-example-result.sh SUTRAExample1
# See https://github.com/NREL/GEOPHIRES-X/issues/107

# Note: make sure your virtualenv is activated before running or this script will fail
# or generate incorrect results.

cd "$(dirname "$0")"
python -mgeophires_x examples/$1.txt examples/$1.out
rm examples/$1.json

if [[ $1 == "example1_addons" ]]
then
    echo "Updating CSV..."
    python regenerate_example_result_csv.py
fi

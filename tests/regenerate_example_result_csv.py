import argparse
import os

from geophires_x_client import GeophiresXResult


def _get_file_path(file_name: str) -> str:
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), str(file_name))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Regenerate a CSV result file from a GEOPHIRES-X example .out file.')
    parser.add_argument(
        'example_name',
        type=str,
        nargs='?',  # Makes the argument optional
        default='example1_addons',
        help='The base name of the example file (e.g., "example1_addons"). Defaults to "example1_addons".',
    )
    args = parser.parse_args()

    example_name = args.example_name
    example_relative_path = f'{"examples/" if example_name.startswith("example") else ""}{example_name}.out'

    with open(_get_file_path(f'{example_name}.csv'), 'w', encoding='utf-8') as csvfile:
        csvfile.write(GeophiresXResult(_get_file_path(example_relative_path)).as_csv())

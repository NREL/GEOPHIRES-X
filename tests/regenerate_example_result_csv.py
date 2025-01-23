import os

from geophires_x_client import GeophiresXResult


def _get_file_path(file_name: str) -> str:
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), str(file_name))


if __name__ == '__main__':
    with open(_get_file_path('example1_addons.csv'), 'w', encoding='utf-8') as csvfile:
        csvfile.write(GeophiresXResult(_get_file_path('examples/example1_addons.out')).as_csv())

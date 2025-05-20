import os

# noinspection PyProtectedMember
from geophires_x.EconomicsSamCashFlow import _SINGLE_OWNER_OUTPUT_PROPERTIES


def _get_file_path(file_name) -> str:
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), file_name)


def _generate_mapping_from_module_doc(module_name: str = 'Cashloan'):
    with open(_get_file_path(f'{module_name}.html.txt'), encoding='utf-8') as f:
        # lines = f.readlines()

        txt = f.read()
        # lines = txt.split('PySAM.Cashloan.Cashloan.Outputs')[1].split('\n')
        txt = txt.split(f'PySAM.{module_name}.{module_name}.Outputs')[1].split('Outputs_vals =')[2]
        lines = txt.split('\n')[2:]

        # _log.debug(f'Found {len(lines)} lines {module_name} in module doc')
        for i in range(0, len(lines), 8):
            prop = lines[i].strip()[:-1]
            if prop == '':
                continue
            display_name = lines[i + 2].strip().replace('[', '(').replace(']', ')')
            # _log.debug(f'Property: {prop}')
            if display_name not in _SINGLE_OWNER_OUTPUT_PROPERTIES:
                print(f"\t'{display_name}': '{prop}',  # {module_name}")


if __name__ == '__main__':
    # sop = _SINGLE_OWNER_OUTPUT_PROPERTIES.copy()
    # # del sop['Total installed cost ($)']
    # print(json_dumpse(sop))

    _generate_mapping_from_module_doc('Cashloan')
    _generate_mapping_from_module_doc('Singleowner')

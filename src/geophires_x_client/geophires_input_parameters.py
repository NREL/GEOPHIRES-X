import tempfile
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Optional


class EndUseOption(Enum):
    ELECTRICITY = 1
    DIRECT_USE_HEAT = 2
    COGEN_TOPPING_CYCLE = 3
    COGEN_BOTTOMING_CYCLE = 4
    COGEN_SPLIT_OF_MASS_FLOW_RATE = 5


class PowerPlantType(Enum):
    SUBCRITICAL_ORC = 1
    SUPERCRITICAL_ORC = 2
    SINGLE_FLASH = 3
    DOUBLE_FLASH = 4


class GeophiresInputParameters:
    def __init__(self, params: Optional[MappingProxyType] = None, from_file_path: Optional[Path] = None):
        assert (params is None) ^ (from_file_path is None), 'Only one of params or from_file_path may be provided'

        if params is not None:
            self._params = dict(params)
            self._id = abs(hash(frozenset(self._params.items())))
            # TODO validate params - i.e. that all names are accepted by simulation, values don't exceed max allowed,
            #  etc.

            tmp_file_path = Path(tempfile.gettempdir(), f'geophires-input-params_{self._id}.txt')
            f = Path.open(tmp_file_path, 'w')

            f.writelines([','.join([str(p) for p in param_item]) + '\n' for param_item in self._params.items()])
            f.close()
            self._file_path = tmp_file_path

        if from_file_path is not None:
            self._file_path = from_file_path
            self._id = hash(from_file_path)

    def as_file_path(self):
        return self._file_path

    def get_output_file_path(self):
        return Path(tempfile.gettempdir(), f'geophires-result_{self._id}.out')

    def __hash__(self):
        return self._id

import tempfile
import uuid
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Optional


class EndUseOption(Enum):
    """
    TODO consolidate with geophires_x.OptionList.EndUseOptions
    """

    ELECTRICITY = 1
    DIRECT_USE_HEAT = 2
    COGEN_TOPPING_CYCLE = 3
    COGEN_BOTTOMING_CYCLE = 4
    COGEN_SPLIT_OF_MASS_FLOW_RATE = 5
    COGENERATION_TOPPING_EXTRA_HEAT = 31
    COGENERATION_TOPPING_EXTRA_ELECTRICTY = 32
    COGENERATION_BOTTOMING_EXTRA_ELECTRICTY = 41
    COGENERATION_BOTTOMING_EXTRA_HEAT = 42
    COGENERATION_PARALLEL_EXTRA_HEAT = 51
    COGENERATION_PARALLEL_EXTRA_ELECTRICTY = 52
    ABSORPTION_CHILLER = 6
    HEAT_PUMP = 7
    DISTRICT_HEATING = 8


class PowerPlantType(Enum):
    SUBCRITICAL_ORC = 1
    SUPERCRITICAL_ORC = 2
    SINGLE_FLASH = 3
    DOUBLE_FLASH = 4


class GeophiresInputParameters:

    def __init__(self, params: Optional[MappingProxyType] = None, from_file_path: Optional[Path] = None):
        """
        Note that params will override any duplicate entries in from_file_path
        """

        assert (params is not None) or (from_file_path is not None), 'One of params or from_file_path must be provided'

        if params is not None:
            self._params = dict(params)
            self._file_path = Path(tempfile.gettempdir(), f'geophires-input-params_{uuid.uuid4()!s}.txt')

            if from_file_path is not None:
                with open(from_file_path, encoding='UTF-8') as base_file:
                    with open(self._file_path, 'a', encoding='UTF-8') as f:
                        f.writelines(base_file.readlines())
        else:
            self._file_path = from_file_path

        if params is not None:
            # TODO validate params - i.e. that all names are accepted by simulation, values don't exceed max allowed,
            #  etc.

            with open(self._file_path, 'a', encoding='UTF-8') as f:
                f.writelines([', '.join([str(p) for p in param_item]) + '\n' for param_item in self._params.items()])

        self._id = hash(self._file_path)

    def as_file_path(self):
        return self._file_path

    def get_output_file_path(self):
        return Path(tempfile.gettempdir(), f'geophires-result_{self._id}.out')

    def as_text(self):
        with open(self.as_file_path(), encoding='UTF-8') as f:
            return f.read()

    def __hash__(self):
        """TODO make hashes for equivalent parameters equal"""
        return self._id

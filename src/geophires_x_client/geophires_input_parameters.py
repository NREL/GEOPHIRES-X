import tempfile
import uuid
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any
from typing import Mapping
from typing import Optional
from typing import Union


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
                # Note: This has a potential race condition if the file doesn't exist at the time of 'a',
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
        """
        Note hashes for equivalent parameters may not be equal.
        Use ImmutableGeophiresInputParameters instead.
        """

        return self._id


@dataclass(frozen=True)
class ImmutableGeophiresInputParameters(GeophiresInputParameters):
    """
    An immutable, self-contained, and content-hashable set of GEOPHIRES
    input parameters.

    This class is hashable based on its logical content, making it safe for
    caching. It generates its file representation on-demand and is designed
    for use cases where parameter sets must be treated as immutable values.
    """

    params: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    from_file_path: Union[Path, None] = None

    # A unique ID for this instance, used for file I/O but not for hashing or equality.
    _instance_id: uuid.UUID = field(default_factory=uuid.uuid4, init=False, repr=False, compare=False)

    def __post_init__(self):
        """Ensures that the parameters dictionary is immutable."""
        if not isinstance(self.params, MappingProxyType):
            # object.__setattr__ is required to modify a field in a frozen dataclass
            object.__setattr__(self, 'params', MappingProxyType(self.params))

    def __hash__(self) -> int:
        """
        Computes a hash based on the content of the parameters.
        If a base file is used, its content is read and hashed to ensure
        the hash reflects a true snapshot of all inputs.
        """

        param_hash = hash(frozenset(self.params.items()))

        if self.from_file_path is not None and self.from_file_path.exists():
            file_content_hash = hash(self.from_file_path.read_bytes())
        else:
            file_content_hash = hash(self.from_file_path)

        return hash((param_hash, file_content_hash))

    def as_file_path(self) -> Path:
        """
        Creates a temporary file representation of the parameters on demand.
        The resulting file path is cached for efficiency.
        """

        # Return the cached path if the file has already been generated for this instance.
        if hasattr(self, '_cached_file_path'):
            return self._cached_file_path

        file_path = Path(tempfile.gettempdir(), f'geophires-input-params_{self._instance_id!s}.txt')

        with open(file_path, 'w', encoding='UTF-8') as f:
            if self.from_file_path is not None:
                with open(self.from_file_path, encoding='UTF-8') as base_file:
                    f.write(base_file.read())

            if self.params:
                # Ensure there is a newline between the base file content and appended params.
                if self.from_file_path is not None and f.tell() > 0:
                    f.seek(f.tell() - 1)
                    if f.read(1) != '\n':
                        f.write('\n')
                f.writelines([f'{key}, {value}\n' for key, value in self.params.items()])

        # Cache the path on the instance after creation.
        object.__setattr__(self, '_cached_file_path', file_path)
        return file_path

    def get_output_file_path(self) -> Path:
        """Returns a unique path for the GEOPHIRES output file."""
        return Path(tempfile.gettempdir(), f'geophires-result_{self._instance_id!s}.out')

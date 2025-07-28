import dataclasses

from geophires_x.GeoPHIRESUtils import UpgradeSymbologyOfUnits


@dataclasses.dataclass
class OutputTableItem:
    parameter: str = ''
    value: str = ''
    units: str = ''

    def __init__(self, parameter: str, value: str = '', units: str = ''):
        self.parameter = parameter
        self.value = value
        self.units = units
        if self.units:
            self.units = UpgradeSymbologyOfUnits(self.units)

# copyright, 2023, Malcolm I Ross
from enum import Enum


class EndUseOptions(str, Enum):
    ELECTRICITY = "Electricity"  # 1
    HEAT = "Direct-Use Heat"  # 2
    COGENERATION_TOPPING_EXTRA_HEAT = "Cogeneration Topping Cycle, Heat sales considered as extra income"  # 31
    COGENERATION_TOPPING_EXTRA_ELECTRICITY = "Cogeneration Topping Cycle, Electricity sales considered as extra income"  # 32
    COGENERATION_BOTTOMING_EXTRA_HEAT = "Cogeneration Bottoming Cycle, Heat sales considered as extra income"  # 41
    COGENERATION_BOTTOMING_EXTRA_ELECTRICITY = "Cogeneration Bottoming Cycle, Electricity sales considered as extra income"  # 42
    COGENERATION_PARALLEL_EXTRA_HEAT = "Cogeneration Parallel Cycle, Heat sales considered as extra income"  # 51
    COGENERATION_PARALLEL_EXTRA_ELECTRICITY = "Cogeneration Parallel Cycle, Electricity sales considered as extra income"  # 52


class PlantType(str, Enum):
    SUB_CRITICAL_ORC = "Subcritical ORC" # 1
    SUPER_CRITICAL_ORC = "Supercritical ORC" # 2
    SINGLE_FLASH = "Single-Flash" # 3
    DOUBLE_FLASH = "Double-Flash" # 4
    ABSORPTION_CHILLER = "Absorption Chiller"  # 5
    HEAT_PUMP = "Heat Pump"  # 6
    DISTRICT_HEATING = "District Heating"  # 7
    RTES = "Reservoir Thermal Energy Storage"  # 8
    INDUSTRIAL = "Industrial"  # 9


class EconomicModel(str, Enum):
    CLGS = "Simple (CLGS)"
    FCR = "Fixed Charge Rate (FCR)"
    STANDARDIZED_LEVELIZED_COST = "Standard Levelized Cost"
    BICYCLE = "BICYCLE"


class ReservoirModel(str, Enum):
    CYLINDRICAL = "Simple cylindrical"
    MULTIPLE_PARALLEL_FRACTURES = "Multiple Parallel Fractures"
    LINEAR_HEAT_SWEEP = "1-D Linear Heat Sweep"
    SINGLE_FRACTURE = "Single Fracture m/A Thermal Drawdown"
    ANNUAL_PERCENTAGE = "Annual Percentage Thermal Drawdown"
    USER_PROVIDED_PROFILE = "User-Provided Temperature Profile"
    TOUGH2_SIMULATOR = "TOUGH2 Simulator"
    SUTRA = "SUTRA"


class ReservoirVolume(str, Enum):
    FRAC_NUM_SEP = "Specify number of fractures and fracture separation"
    RES_VOL_FRAC_SEP = "Specify reservoir volume and fracture separation"
    RES_VOL_FRAC_NUM = "Specify reservoir volume and number of fractures"
    RES_VOL_ONLY = "Specify reservoir volume only"


class WellDrillingCostCorrelation(str, Enum):
    """Note: order must be retained since input is read as an int"""

    VERTICAL_SMALL = "vertical small diameter, baseline"
    DEVIATED_SMALL = "deviated small diameter, baseline"
    VERTICAL_LARGE = "vertical large diameter, baseline"
    DEVIATED_LARGE = "deviated large diameter, baseline"

    SIMPLE = "Simple"

    VERTICAL_SMALL_INT1 = "vertical small diameter, intermediate1"
    VERTICAL_SMALL_INT2 = "vertical small diameter, intermediate2"
    DEVIATED_SMALL_INT1 = "deviated small diameter, intermediate1"
    DEVIATED_SMALL_INT2 = "deviated small diameter, intermediate2"
    VERTICAL_LARGE_INT1 = "vertical large diameter, intermediate1"
    VERTICAL_LARGE_INT2 = "vertical large diameter, intermediate2"
    DEVIATED_LARGE_INT1 = "deviated large diameter, intermediate1"
    DEVIATED_LARGE_INT2 = "deviated large diameter, intermediate2"
    VERTICAL_SMALL_IDEAL = "vertical open-hole, small diameter, ideal"
    DEVIATED_SMALL_IDEAL = "deviated liner, small diameter, ideal"
    VERTICAL_LARGE_IDEAL = "vertical open-hole, large diameter, ideal"
    DEVIATED_LARGE_IDEAL = "deviated liner, large diameter, ideal"



class FractureShape(str, Enum):
    CIRCULAR_AREA = "Circular fracture with known area"
    CIRCULAR_DIAMETER = "Circular fracture with known diameter"
    SQUARE = "Square"
    RECTANGULAR = "Rectangular"


class WorkingFluid(str, Enum):
    WATER = "water"
    SCO2 = "sCO2"


class Configuration(str, Enum):
    ULOOP = "utube"
    COAXIAL = "coaxial"

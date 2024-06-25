# copyright, 2023, Malcolm I Ross
from enum import Enum


class GeophiresInputEnum(str, Enum):
    """
    Input enums have a name, integer input value, and string value
    """

    def __new__(cls, *args, **kwds):
        obj = str.__new__(cls)
        obj._value_ = args[1]
        return obj

    def __init__(self, int_value: int, _: str):
        self.int_value = int_value

    def __eq__(self, other):
        return str(self) == str(other)


class EndUseOptions(GeophiresInputEnum):
    ELECTRICITY = 1, "Electricity"
    HEAT = 2, "Direct-Use Heat"
    COGENERATION_TOPPING_EXTRA_HEAT = 31, "Cogeneration Topping Cycle, Heat sales considered as extra income"
    COGENERATION_TOPPING_EXTRA_ELECTRICITY = 32, "Cogeneration Topping Cycle, Electricity sales considered as extra income"
    COGENERATION_BOTTOMING_EXTRA_HEAT = 41, "Cogeneration Bottoming Cycle, Heat sales considered as extra income"
    COGENERATION_BOTTOMING_EXTRA_ELECTRICITY = 42, "Cogeneration Bottoming Cycle, Electricity sales considered as extra income"
    COGENERATION_PARALLEL_EXTRA_HEAT = 51, "Cogeneration Parallel Cycle, Heat sales considered as extra income"
    COGENERATION_PARALLEL_EXTRA_ELECTRICITY = 52, "Cogeneration Parallel Cycle, Electricity sales considered as extra income"

    @staticmethod
    def get_end_use_option_from_input_string(input_string:str):
        """
        :rtype: EndUseOptions
        """

        for option in EndUseOptions:
            if input_string == str(option.int_value):
                return option

        raise ValueError(f'Unknown End-Use Option input value: {input_string}')


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


class ReservoirModel(GeophiresInputEnum):
    CYLINDRICAL = 0, "Simple cylindrical"
    MULTIPLE_PARALLEL_FRACTURES = 1, "Multiple Parallel Fractures"
    LINEAR_HEAT_SWEEP = 2, "1-D Linear Heat Sweep"
    SINGLE_FRACTURE = 3, "Single Fracture m/A Thermal Drawdown"
    ANNUAL_PERCENTAGE = 4, "Annual Percentage Thermal Drawdown"
    USER_PROVIDED_PROFILE = 5, "User-Provided Temperature Profile"
    TOUGH2_SIMULATOR = 6, "TOUGH2 Simulator"
    SUTRA = 7, "SUTRA"

    @staticmethod
    def get_reservoir_model_from_input_string(input_string:str):
        """
        :rtype: ReservoirModel
        """

        for model in ReservoirModel:
            if input_string == str(model.int_value):
                return model

        raise ValueError(f'Unknown Reservoir Model input value: {input_string}')


class ReservoirVolume(str, Enum):
    FRAC_NUM_SEP = "Specify number of fractures and fracture separation"
    RES_VOL_FRAC_SEP = "Specify reservoir volume and fracture separation"
    RES_VOL_FRAC_NUM = "Specify reservoir volume and number of fractures"
    RES_VOL_ONLY = "Specify reservoir volume only"


class WellDrillingCostCorrelation(GeophiresInputEnum):
    """Note: order must be retained since input is read as an int; first int arg is duplicative of order"""

    VERTICAL_SMALL = 1, "vertical small diameter, baseline", 0.30212, 584.91124, 751368.47270
    DEVIATED_SMALL = 2, "deviated small diameter, baseline", 0.28977, 882.15067, 680562.50150
    VERTICAL_LARGE = 3, "vertical large diameter, baseline", 0.28180, 1275.52130, 632315.12640
    DEVIATED_LARGE = 4, "deviated large diameter, baseline", 0.25528, 1716.71568, 500866.89110

    SIMPLE = 5, "Simple", 0, 1846*1E6, 0 # Based on Fervo Project Cape cost per meter (~$1846/m)

    VERTICAL_SMALL_INT1 = 6, "vertical small diameter, intermediate1", 0.13710, 129.61033, 1205587.57100
    VERTICAL_SMALL_INT2 = 7, "vertical small diameter, intermediate2", 0.00804, 455.60507, 921007.68680
    DEVIATED_SMALL_INT1 = 8, "deviated small diameter, intermediate1", 0.15340, 120.31700, 1431801.54400
    DEVIATED_SMALL_INT2 = 9, "deviated small diameter, intermediate2", 0.00854, 506.08357, 1057330.39000
    VERTICAL_LARGE_INT1 = 10, "vertical large diameter, intermediate1", 0.18927, 293.45174, 1326526.31300
    VERTICAL_LARGE_INT2 = 11, "vertical large diameter, intermediate2", 0.00315, 782.69676, 983620.25270
    DEVIATED_LARGE_INT1 = 12, "deviated large diameter, intermediate1", 0.19950, 296.13011, 1697867.70900
    DEVIATED_LARGE_INT2 = 13, "deviated large diameter, intermediate2", 0.00380, 838.90249, 1181947.04400
    VERTICAL_SMALL_IDEAL = 14, "vertical open-hole, small diameter, ideal", 0.00252, 439.44503, 590611.90110
    DEVIATED_SMALL_IDEAL = 15, "deviated liner, small diameter, ideal", 0.00719, 455.85233, 753377.73080
    VERTICAL_LARGE_IDEAL = 16, "vertical open-hole, large diameter, ideal", -0.00240, 752.93946, 524337.65380
    DEVIATED_LARGE_IDEAL = 17, "deviated liner, large diameter, ideal", 0.00376, 762.52696, 765103.07690

    def calculate_cost_MUSD(self, meters) -> float:
        return (self._c2 * meters ** 2 + self._c1 * meters + self._c0) * 1E-6

    def __init__(self, int_value: int, _: str, c2: float, c1: float, c0: float):
        self._c2 = c2
        self._c1 = c1
        self._c0 = c0
        super().__init__(int_value, _)

    def calculate_cost_MUSD(self, meters) -> float:
        return (self._c2 * meters ** 2 + self._c1 * meters + self._c0) * 1E-6


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
    VERTICAL = "vertical"
    L = "L"

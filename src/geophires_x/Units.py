# copyright, 2023, Malcolm I Ross
from enum import IntEnum, Enum, auto


class Units(IntEnum):
    """All possible systems of measure"""
    NONE = auto()
    CHOICE = auto()
    LENGTH = auto()
    AREA = auto()
    VOLUME = auto()
    MASS = auto()
    DENSITY = auto()
    TEMPERATURE = auto()
    PRESSURE = auto()
    TIME = auto()
    FLOWRATE = auto()
    TEMP_GRADIENT = auto()
    DRAWDOWN = auto()
    IMPEDANCE = auto()
    PRODUCTIVITY_INDEX = auto()
    INJECTIVITY_INDEX = auto()
    HEAT = auto()
    HEAT_CAPACITY = auto()
    ENTROPY = auto()
    ENTHALPY = auto()
    THERMAL_CONDUCTIVITY = auto()
    POROSITY = auto()
    PERMEABILITY = auto()
    CURRENCY = auto()
    CURRENCYFREQUENCY = auto()
    ENERGYCOST = auto()
    ENERGYDENSITY = auto()
    COSTPERMASS = auto()
    MASSPERTIME = auto()
    COSTPERDISTANCE = auto()
    PERCENT = auto()
    ENERGY = auto()
    POWER = auto()
    ENERGYFREQUENCY = auto()
    AVAILABILITY = auto()
    CO2PRODUCTION = auto()
    ENERGYPERCO2 = auto()
    POPDENSITY = auto()
    HEATPERUNITAREA = auto()
    POWERPERUNITAREA = auto()
    HEATPERUNITVOLUME = auto()
    POWERPERUNITVOLUME = auto()


class TemperatureUnit(str, Enum):
    """Temperature Units"""
    CELSIUS = "degC"
    FAHRENHEIT = "degF"
    KELVIN = "degK"


class TemperatureGradientUnit(str, Enum):
    """Temperature Gradient Units"""
    DEGREESCPERKM = "degC/km"
    DEGREESFPERMILE = "degF/mi"
    DEGREESCPERM = "degC/m"


class PercentUnit(str, Enum):
    """Percent Units"""
    PERCENT = "%"
    TENTH = ""


class LengthUnit(str, Enum):
    """Length Units"""
    METERS = "meter"
    CENTIMETERS = "centimeter"
    KILOMETERS = "kilometer"
    FEET = "ft"
    INCHES = "in"
    MILES = "mile"


class AreaUnit(str, Enum):
    """Area Units"""
    METERS2 = "m**2"
    CENTIMETERS2 = "cm**2"
    KILOMETERS2 = "km**2"
    FEET2 = "ft**2"
    INCHES2 = "in**2"
    MILES2 = "mi**2"


class VolumeUnit(str, Enum):
    """Volume Units"""
    METERS3 = "m**3"
    CENTIMETERS3 = "cm**3"
    KILOMETERS3 = "km**3"
    FEET3 = "ft**3"
    INCHES3 = "in**3"
    MILES3 = "mi**3"


class DensityUnit(str, Enum):
    """Density Units"""
    KGPERMETERS3 = "kg/m**3"
    GRPERCENTIMETERS3 = "gr/cm**3"
    KGPERKILOMETERS3 = "kg/km**3"
    LBSPERFEET3 = "lbs/ft**3"
    OZPERINCHES3 = "oz/in**3"
    LBSPERMILES3 = "lbs/mi**3"


class EnergyUnit(str, Enum):
    """Energy (electricity or heat) Units"""
    WH = "Wh"
    KWH = "kWh"
    MWH = "MWh"
    GWH = "GWh"


class PowerUnit(str, Enum):
    """Power (electrcity or heat) Units"""
    W = "W"
    KW = "kW"
    MW = "MW"
    GW = "GW"


class EnergyFrequencyUnit(str, Enum):
    """Energy per interval Units"""
    WPERYEAR = "W/yr"
    KWPERYEAR = "kW/yr"
    MWPERYEAR = "MW/yr"
    GWPERYEAR = "GW/yr"
    KWhPERYEAR = "kWh/yr"
    MWhPERHOUR = "MWh/hr"
    MWhPERDAY = "MWh/day"
    MWhPERYEAR = "MWh/year"
    GWhPERYEAR = "GWh/year"

class CurrencyUnit(str, Enum):
    """Currency Units"""
    MDOLLARS = "MUSD"
    KDOLLARS = "KUSD"
    DOLLARS = "USD"
    MEUR = "MEUR"
    KEUR = "KEUR"
    EUR = "EUR"
    MMXN = "MMXN"
    KMXN = "KMXN"
    MXN = "MXN"


class CurrencyFrequencyUnit(str, Enum):
    MDOLLARSPERYEAR = "MUSD/yr"
    KDOLLARSPERYEAR = "KUSD/yr"
    DOLLARSPERYEAR = "USD/yr"
    MEURPERYEAR = "MEUR/yr"
    KEURPERYEAR = "KEUR/yr"
    EURPERYEAR = "EUR/yr"
    MMXNPERYEAR = "MXN/yr"
    KMXNPERYEAR = "KMXN/yr"
    MXNPERYEAR = "MXN/yr"


class EnergyCostUnit(str, Enum):
    DOLLARSPERKWH = "USD/kWh"
    DOLLARSPERMWH = "USD/MWh"
    CENTSSPERKWH = "cents/kWh"
    DOLLARSPERKW = "USD/kW"
    CENTSSPERKW = "cents/kW"
    DOLLARSPERMMBTU = "USD/MMBTU"
    DOLLARSPERMCF = "USD/MCF"


class EnergyDensityUnit(str, Enum):
    KWHPERMCF = "kWh/MCF"


class MassPerTimeUnit(str, Enum):
    TONNEPERYEAR = "tonne/yr"


class CostPerMassUnit(str, Enum):
    CENTSSPERMT = "cents/mt"
    DOLLARSPERMT = "USD/mt"
    DOLLARSPERTONNE = "USD/tonne"
    CENTSSPERLB = "cents/lb"
    DOLLARSPERLB = "USD/lb"


class CostPerDistanceUnit(str, Enum):
    DOLLARSPERM = "USD/m"


class PressureUnit(str, Enum):
    """Pressure Units"""
    MPASCAL = "mPa"
    KPASCAL = "kPa"
    PASCAL = "Pa"
    BAR = "bar"
    KBAR = "kbar"


class AvailabilityUnit(str, Enum):
    """Availability Units"""
    MWPERKGPERSEC = "MW/(kg/s)"


class DrawdownUnit(str, Enum):
    """Drawdown Units"""
    KGPERSECPERSQMETER = "kg/s/m**2"
    PERYEAR = "1/year"


class HeatUnit(str, Enum):
    """Heat Units"""
    J = "J"
    KJ = "kJ"


class HeatCapacityUnit(str, Enum):
    """Heat Capacity Units"""
    JPERKGPERK = "J/kg/kelvin"
    KJPERKM3C = "kJ/km**3C"
    kJPERKGC = "kJ/kgC"


class EntropyUnit(str, Enum):
    """Entropy Units"""
    KJPERKGK = "kJ/kgK"


class EnthalpyUnit(str, Enum):
    """Enthalpy Units"""
    KJPERKG = "kJ/kg"


class ThermalConductivityUnit(str, Enum):
    """Thermal Conductivity Units"""
    WPERMPERK = "watt/m/kelvin"


class TimeUnit(str, Enum):
    """Time Units"""
    MSECOND = "msec"
    SECOND = "sec"
    MINUTE = "min"
    HOUR = "hr"
    DAY = "day"
    WEEK = "week"
    YEAR = "yr"


class FlowRateUnit(str, Enum):
    """Flow Rate Units"""
    KGPERSEC = "kg/sec"


class ImpedanceUnit(str, Enum):
    """Impedance Units"""
    GPASPERM3 = "GPa.s/m**3"


class ProductivityIndexUnit(str, Enum):
    """Productivity IndexUnits"""
    KGPERSECPERBAR = "kg/sec/bar"


class InjectivityIndexUnit(str, Enum):
    """Injectivity IndexUnits"""
    KGPERSECPERBAR = "kg/sec/bar"


class PorosityUnit(str, Enum):
    """Porosity Units"""
    PERCENT = "%"


class PermeabilityUnit(str, Enum):
    """Permeability Units"""
    SQUAREMETERS = "m**2"


class CO2ProductionUnit(str, Enum):
    """CO2 Production Units"""
    LBSPERKWH = "lbs/kWh"
    KPERKWH = "k/kWh"
    TONNEPERMWH = "t/MWh"


class EnergyPerCO2Unit(str, Enum):
    """Energy cost per tonne of CO2 extracted Units"""
    KWHEPERTONNE = "kWh/t"
    KWTHPERTONNE = "kW/t"


class MassUnit(str, Enum):
    """Mass Units"""
    GRAM = "gram"
    KILOGRAM = "kilogram"
    TONNE = "tonne"
    TON = "ton"
    LB = "pound"
    OZ = "ounce"


class PopDensityUnit(str,Enum):
    """Population Density Units"""
    perkm2 = "Population per square km"


class HeatPerUnitAreaUnit(str,Enum):
    """Population Density Units"""
    KJPERSQKM = "kJ/km**2"


class PowerPerUnitAreaUnit(str,Enum):
    """Population Density Units"""
    MWPERSQKM = "MW/km**2"


class HeatPerUnitVolumeUnit(str,Enum):
    """Population Density Units"""
    KJPERCUBICKM = "kJ/km**3"


class PowerPerUnitVolumeUnit(str,Enum):
    """Population Density Units"""
    MWPERCUBICKM = "MW/km**3"

from __future__ import annotations
from os.path import exists
import dataclasses
import json
import numbers
from functools import lru_cache

from scipy.interpolate import interp1d
import numpy as np

from geophires_x.Parameter import *

from iapws.iapws97 import IAPWS97

_T = np.array(
    [
        0.01,
        10.0,
        20.0,
        25.0,
        30.0,
        40.0,
        50.0,
        60.0,
        70.0,
        80.0,
        90.0,
        100.0,
        110.0,
        120.0,
        140.0,
        160.0,
        180.0,
        200.0,
        220.0,
        240.0,
        260.0,
        280.0,
        300.0,
        320.0,
        340.0,
        360.0,
        373.946,
    ]
)


# from https://www.engineeringtoolbox.com/water-properties-d_1508.html
_UtilEff = np.array(
    [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0057,
        0.0337,
        0.0617,
        0.0897,
        0.1177,
        0.13,
        0.16,
        0.19,
        0.22,
        0.26,
        0.29,
        0.32,
        0.35,
        0.38,
        0.40,
        0.4,
        0.4,
        0.4,
        0.4,
        0.4,
        0.4,
        0.4,
        0.4,
    ]
)

_interp_util_eff_func = interp1d(_T, _UtilEff)


@lru_cache(maxsize=None)
def DensityWater(Twater_degC: float) -> float:
    """
    Calculate the density of water as a function of temperature.

    Args:
        Twater_degC: The temperature of water in degrees C.
    Returns:
        The density of water in kg/m³.
    Raises:
        ValueError: If Twater is not a float or convertible to float.
    """
    if not np.can_cast(Twater_degC, float):
        raise ValueError(f'Twater ({Twater_degC}) must be a float or convertible to float.')

    try:
        return IAPWS97(T=celsius_to_kelvin(Twater_degC), x=0).rho
    except NotImplementedError as nie:
        raise ValueError(f'Input temperature {Twater_degC} is out of range or otherwise not implemented') from nie


@lru_cache(maxsize=None)
def celsius_to_kelvin(celsius: float) -> float:
    """
    Convert temperature from Celsius to Kelvin.

    Args:
        celsius: Temperature in degrees Celsius.
    Returns:
        Temperature in Kelvin.
    Raises:
        ValueError: If celsius is not a float or convertible to float.
    """
    if not isinstance(celsius, (int, float)):
        raise ValueError("Invalid input for celsius. celsius must be a number.")

    CELSIUS_TO_KELVIN_CONSTANT = 273.15
    return celsius + CELSIUS_TO_KELVIN_CONSTANT


@lru_cache(maxsize=None)
def ViscosityWater(Twater_degC: float) -> float:
    """
    The ViscosityWater function is used to calculate the dynamic viscosity of water as a function of temperature.
    Args:
        Twater_degC: the temperature of water in degrees C
    Returns:
        Viscosity of water in Pa·s (Ns/m2)
    Raises:
        ValueError: If Twater_degC is not a float or convertible to float.
    """

    try:
        return IAPWS97(T=celsius_to_kelvin(Twater_degC), x=0).mu
    except NotImplementedError as nie:
        raise ValueError(f'Input temperature {Twater_degC} is out of range or otherwise not implemented') from nie


@lru_cache(maxsize=None)
def HeatCapacityWater(Twater_degC: float) -> float:
    """
    Calculate the isobaric specific heat capacity (c_p) of water as a function of temperature.

    Args:
        Twater_degC: The temperature of water in degrees C.
    Returns:
        The isobaric specific heat capacity of water as a function of temperature in J/kg-K.
    Raises:
        ValueError: If Twater_degC is not a float or convertible to float.
    """
    if not isinstance(Twater_degC, numbers.Real) or Twater_degC < 0 or Twater_degC > 500:
        raise ValueError(
            f'Invalid input for Twater_degC.'
            f'Twater_degC must be a non-negative number and must be within the range of 0 to 500 degrees Celsius.'
            f'The input value was: {Twater_degC}'
        )

    try:
        return IAPWS97(T=celsius_to_kelvin(Twater_degC), x=0).cp * 1e3
    except NotImplementedError as nie:
        raise ValueError(f'Input temperature {Twater_degC} is out of range or otherwise not implemented') from nie


@lru_cache(maxsize=None)
def RecoverableHeat(Twater_degC: float) -> float:
    """
    the RecoverableHeat function is used to calculate the recoverable heat fraction as a function of temperature

    Args:
        Twater_degC: the temperature of water in degrees C
    Returns:
        the recoverable heat fraction as a function of temperature
    Raises:
        ValueError: If Twater is not a float or convertible to float.
        ValueError: If DefaultRecoverableHeat is not a float or convertible to float.
    """
    LOW_TEMP_THRESHOLD = 90.0
    HIGH_TEMP_THRESHOLD = 150.0
    LOW_TEMP_RECOVERABLE_HEAT = 0.43
    HIGH_TEMP_RECOVERABLE_HEAT = 0.66

    if not isinstance(Twater_degC, (int, float)):
        raise ValueError(f'Twater_degC {Twater_degC} must be a number')

    if Twater_degC <= LOW_TEMP_THRESHOLD:
        recoverable_heat = LOW_TEMP_RECOVERABLE_HEAT
    elif Twater_degC >= HIGH_TEMP_THRESHOLD:
        recoverable_heat = HIGH_TEMP_RECOVERABLE_HEAT
    else:
        recoverable_heat = 0.0038 * Twater_degC + 0.085

    return recoverable_heat


@lru_cache(maxsize=None)
def VaporPressureWater(Twater_degC: float) -> float:
    """
    The VaporPressureWater function is used to calculate the vapor pressure of water as a function of temperature.

    Args:
        Twater_degC: the temperature of water in degrees C
    Returns:
        The vapor pressure of water as a function of temperature in kPa
    Raises:
        ValueError: If Twater_degC is not a float or convertible to float.
        ValueError: If Twater_degC is below 0.
    """

    if not isinstance(Twater_degC, (int, float)):
        raise ValueError(f'Twater_degC ({Twater_degC}) must be a number')
    if Twater_degC < 0:
        raise ValueError(f'Twater_degC ({Twater_degC}) must be greater than or equal to 0')

    try:
        return IAPWS97(T=celsius_to_kelvin(Twater_degC), x=0).P * 1e3
    except NotImplementedError as nie:
        raise ValueError(f'Input temperature {Twater_degC} is out of range or otherwise not implemented') from nie


@lru_cache(maxsize=None)
def EntropyH20_func(temperature_degC: float) -> float:
    """
    the EntropyH20_func function is used to calculate the entropy of water as a function of temperature
    TODO switch to IAPWS instead of custom interpolation

    Args:
        temperature_degC: the temperature of water in degrees C
    Returns:
        the entropy of water as a function of temperature in kJ/kg-K
    Raises:

    """
    try:
        temperature_degC = float(temperature_degC)
    except ValueError:
        raise TypeError(f'Input temperature ({temperature_degC}) must be a float')

    try:
        return IAPWS97(T=celsius_to_kelvin(temperature_degC), x=0).s
    except NotImplementedError as nie:
        raise ValueError(f'Input temperature {temperature_degC} is out of range or otherwise not implemented') from nie


@lru_cache(maxsize=None)
def EnthalpyH20_func(temperature_degC: float) -> float:
    """
    the EnthalpyH20_func function is used to calculate the enthalpy of water as a function of temperature

    Args:
        temperature_degC: the temperature of water in degrees C (float)
    Returns:
        the enthalpy of water as a function of temperature in kJ/kg
    Raises:
        TypeError: If temperature is not a float or convertible to float.
        ValueError: If temperature is not within the range of 0 to 373.946 degrees C.
    """
    try:
        temperature_degC = float(temperature_degC)
    except ValueError:
        raise TypeError(f'Input temperature ({temperature_degC}) must be a float')

    try:
        return IAPWS97(T=celsius_to_kelvin(temperature_degC), x=0).h
    except NotImplementedError as nie:
        raise ValueError(f'Input temperature {temperature_degC} is out of range or otherwise not implemented') from nie


@lru_cache(maxsize=None)
def UtilEff_func(temperature_degC: float) -> float:
    """
    the UtilEff_func function is used to calculate the utilization efficiency of the system as a function of temperature
    Args:
        temperature_degC: the temperature of water in degrees C
    Returns:
         the utilization efficiency of the system as a function of temperature
    Raises:
        ValueError: If x is not a float or convertible to float.
        ValueError: If x is not within the range of 0 to 373.946 degrees C.
    """

    if not isinstance(temperature_degC, (int, float)):
        raise ValueError(f'Input temperature ({temperature_degC}) must be a number')

    if temperature_degC < _T[0] or temperature_degC > _T[-1]:
        raise ValueError(f'Temperature ({temperature_degC}) must be within the range of {_T[0]} to {_T[-1]} degrees C.')

    util_eff = _interp_util_eff_func(temperature_degC)
    return util_eff


def read_input_file(return_dict_1, logger=None):
    """
    Read input file and return a dictionary of parameters
    :param return_dict_1: dictionary of parameters
    :param logger: logger object
    :return: dictionary of parameters
    :rtype: dict
    """

    logger.info(f'Init {__name__}')

    # Specify path of input file - it will always be the first command line argument.
    # If it doesn't exist, simply run the default model without any inputs

    # read input data (except input from optional filenames)
    if len(sys.argv) > 1:
        f_name = sys.argv[1]
        content = []
        if exists(f_name):
            logger.info(f'Found filename: {f_name}. Proceeding with run using input parameters from that file')
            with open(f_name, encoding='UTF-8') as f:
                # store all input in one long string that will be passed to all objects
                # so they can parse out their specific parameters (and ignore the rest)
                content = f.readlines()
        else:
            raise FileNotFoundError(f'Unable to read input file: File {f_name} not found')

        # successful read of data into list.  Now make a dictionary with all the parameter entries.
        # Index will be the unique name of the parameter.
        # The value will be a "ParameterEntry" structure, with name, value (optionally with units), optional comment
        for line in content:
            if line.startswith('#'):
                # skip any line that starts with "#" - # will be the comment parameter
                continue

            # now deal with the comma delimited parameters
            # split on a comma - that should give us major divisions,
            # Could be:
            # 1) Desc and Val (2 elements),
            # 2) Desc and Val with Unit (2 elements, Unit split from Val by space),
            # 3) Desc, Val, and comment (3 elements),
            # 4) Desc, Val with Unit, Comment (3 elements, Unit split from Val by space)
            # If there are more than 3 commas, we are going to assume it is parseable,
            # and that the commas are in the comment
            elements = line.split(',')

            if len(elements) < 2:
                # not enough commas, so must not be data to parse
                continue

                # we have good data, so make initial assumptions
            description = elements[0].strip()
            s_val = elements[1].strip()
            comment = ""  # cases 1 & 2 - no comment
            if len(elements) == 3:  # cases 3 & 4
                comment = elements[2].strip()

            if len(elements) > 3:
                # too many commas, so assume they are in comments
                for i in range(2, len(elements), 1):
                    comment = comment + elements[i]

            # done with parsing, now create the object and add to the dictionary
            p_entry = ParameterEntry(description, s_val, comment)
            return_dict_1[description] = p_entry  # make the dictionary element

    else:
        logger.warning(
            'No input parameter file specified on the command line. \
        Proceeding with default parameter run... '
        )

    logger.info(f'Complete {__name__}: {sys._getframe().f_code.co_name}')


class _EnhancedJSONEncoder(json.JSONEncoder):
    """
    Enhanced JSON encoder that can handle dataclasses
    :param json.JSONEncoder: JSON encoder
    :return: JSON encoder
    :rtype: json.JSONEncoder
    """

    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def json_dumpse(obj) -> str:
    return json.dumps(obj, cls=_EnhancedJSONEncoder)

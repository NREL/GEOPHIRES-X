# copyright, 2023, Malcolm I Ross
import os.path
import sys
from array import array
from typing import List
from dataclasses import dataclass, field
from enum import IntEnum
from forex_python.converter import CurrencyRates, CurrencyCodes
import pint
from .Units import *

ureg = pint.UnitRegistry()
ureg.load_definitions(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'GEOPHIRES3_newunits.txt'))


@dataclass
class ParameterEntry:
    """A dataclass that contains the three fields that are being read from the user-provided file

    Attributes:
        Name (str): The official name of the parameter that the user wants to set
        sValue (str): The value that the user wants it to be set to, as a string.
        Comment (str): The optional comment that the user provided with that parameter in the text file
    """
    Name: str
    sValue: str
    Comment: str


@dataclass
class OutputParameter:
    """A dataclass that is the holder values that are provided to the user as output
     but are calculated internally by GEOPHIRES

    Attributes:
        Name (str): The official name of that output
        value: (any): the value of this parameter - can be int, float, text, bool, list, etc...
        ToolTipText (str): Text to place in a ToolTip in a UI
        UnitType (IntEnum): The class of units that parameter falls in (i.e., "length", "time", "area"...)
        PreferredUnits (Enum): The units as required by GEOPHIRES (or your algorithms)
        CurrentUnits (Enum): The units that the parameter is provided in (usually the same PreferredUnits)
        UnitsMatch (boolean): Internal flag set when units are different
    """
    Name: str = ""
    value: int = 0
    ToolTipText: str = "This is ToolTip Text"
    UnitType: IntEnum = Units.NONE
    PreferredUnits: Enum = Units.NONE
    # set to PreferredUnits by default assuming that the current units are the preferred units -
    # they will only change if the read function reads a different unit associated with a parameter
    CurrentUnits: Enum = PreferredUnits
    UnitsMatch: bool = True


@dataclass
class Parameter:
    """
     A dataclass that is the holder values that are provided (optionally) by the user.  These are all the inout values
     to the model.  They all must have a default value that is reasonable and will
     provide a reasonable result if not changed.

    Attributes:
        Name (str): The official name of that output
        Required (bool, False): Is this parameter required to be set?  See user manual.
        Provided (bool, False): Has this value been provided by the user?
        Valid (bool, True): has this value been successfully validated?
        ErrMessage (str): the error message that the user sees if the va;ue they provide does not pass validation -
              by default, it is: "assuming default value (see manual)"
        InputComment (str): The optional comment that the user provided with that parameter in the text file
        ToolTipText (str): Text to place in a ToolTip in a UI
        UnitType (IntEnum): The class of units that parameter falls in (i.e., "length", "time", "area"...)
        PreferredUnits (Enum): The units as required by GEOPHIRES (or your algorithms)
        CurrentUnits (Enum): The units that the parameter is provided in (usually the same PreferredUnits)
        UnitsMatch (boolean): Internal flag set when units are different
    """
    Name: str = ""
    Required: bool = False
    Provided: bool = False
    Valid: bool = True
    ErrMessage: str = "assume default value (see manual)"
    InputComment: str = ""
    ToolTipText: str = Name
    UnitType: IntEnum = Units.NONE
    PreferredUnits: Enum = Units.NONE

    # set to PreferredUnits assuming that the current units are the preferred units
    # - they will only change if the read function reads a different unit associated with a parameter
    CurrentUnits: Enum = PreferredUnits
    UnitsMatch: bool = True
    parameter_category: str = None


@dataclass
class boolParameter(Parameter):
    """
    boolParameter: a dataclass that stores the values for a Boolean value.  Includes the default value and the
    validation values (if appropriate).  Child of Parameter, so it gets all the Attributes of that class.

    Attributes:
        value (bool): The value of that parameter
        DefaultValue (bool, True):  The default value of that parameter
    """
    value: bool = True
    DefaultValue: bool = value
    json_parameter_type: str = 'boolean'


@dataclass
class intParameter(Parameter):
    """
    intParameter: a dataclass that stores the values for a Integer value.  Includes the default value and the
    validation values (if appropriate).  Child of Parameter, so it gets all the Attributes of that class.

    Attributes:
        value (int): The value of that parameter
        DefaultValue (int, 0):  The default value of that parameter
        AllowableRange (list): A list of the valid values
    """
    value: int = 0
    DefaultValue: int = value
    AllowableRange: List[int] = field(default_factory=list)
    json_parameter_type: str = 'integer'


@dataclass
class floatParameter(Parameter):
    """
    floatParameter: a dataclass that stores the values for a Float value.  Includes the default value and the
    validation values (if appropriate).  Child of Parameter, so it gets all the Attributes of that class.

    Attributes:
        value (float): The value of that parameter
        DefaultValue (float, 0.0):  The default value of that parameter
        Min (float, -1.8e308): minimum valid value - not that it is set to a very small value,
                which means that any value is valid by default
        Min (float, 1.8e308): maximum valid value - not that it is set to a very large value,
                which means that any value is valid by default
    """
    value: float = 0.0
    DefaultValue: float = value
    Min: float = -1.8e30
    Max: float = 1.8e30
    json_parameter_type: str = 'number'


@dataclass
class strParameter(Parameter):
    """
    strParameter: a dataclass that stores the values for a String value.  Includes the default value and the
    validation values (if appropriate).  Child of Parameter, so it gets all the Attributes of that class.

    Attributes:
        value (str): The value of that parameter
        DefaultValue (str, ""):  The default value of that parameter
    """
    value: str = ""
    DefaultValue: str = value
    json_parameter_type: str = 'string'


@dataclass
class listParameter(Parameter):
    """
    listParameter: a dataclass that stores the values for a List of values.  Includes the default value and the
    validation values (if appropriate).  Child of Parameter, so it gets all the Attributes of that class.

    Attributes:
        value (list): The value of that parameter
        DefaultValue (list, []):  The default value of that parameter
        Min (float, -1.8e308): minimum valid value of each value in the list - not that it is set to a very small value,
              which means that any value is valid by default
        Min (float, 1.8e308): maximum valid value of each va;ue in the list - not that it is set to a very large value,
            which means that any value is valid by default
    """
    value: List[float] = field(default_factory=list)
    DefaultValue: List[float] = field(default_factory=list)
    Min: float = -1.8e308
    Max: float = 1.8e308
    json_parameter_type: str = 'array'


def ReadParameter(ParameterReadIn: ParameterEntry, ParamToModify, model):
    """
    ReadParameter: A method to take a single ParameterEntry object and use it to update the associated Parameter.
    Does validation as well as Unit and Currency conversion

    Args:
        ParameterReadIn (ParameterEntry): The value the user wants to change
        ParamToModify (Parameter): The Parameter that will be modified (assuming it passes validation and conversion)
        model (Model):  The container class of the application, giving access to everything else, including the logger

    Returns:
        None

    Yields:
        None
    """
    model.logger.info("Init " + str(__name__) + ": " + sys._getframe().f_code.co_name + " for " + ParamToModify.Name)
    # these Parameter Types don't have units so don't do anything fancy, and ignore it if the user has supplied units
    if isinstance(ParamToModify, boolParameter) or isinstance(ParamToModify, strParameter):
        if isinstance(ParamToModify, boolParameter):
            if 'false' in ParameterReadIn.sValue.lower():
                ParamToModify.value = False
            elif 'true' in ParameterReadIn.sValue.lower():
                ParamToModify.value = True
            else:
                ParamToModify.value = bool(ParameterReadIn.sValue)
        else:
            ParamToModify.value = ParameterReadIn.sValue
        ParamToModify.Provided = True  # set provided to true because we are using a user provide value now
        ParamToModify.Valid = True  # set Valid to true because it passed the validation tests
        model.logger.info("Complete " + str(__name__) + ": " + sys._getframe().f_code.co_name)
        return

    # deal with the case where the value has a unit involved - that will be indicated by a space in it
    if ParameterReadIn.sValue.__contains__(" "):
        new_str = ConvertUnits(ParamToModify, ParameterReadIn.sValue, model)
        if len(new_str) > 0: ParameterReadIn.sValue = new_str
    else:
        # The value came in without any units, so it must be using the default PreferredUnits
        ParamToModify.CurrentUnits = ParamToModify.PreferredUnits
        ParamToModify.UnitsMatch = True

    if isinstance(ParamToModify, intParameter):
        New_val = int(float(ParameterReadIn.sValue))
        # Warning - the value read in is the same as the default value, making it superfluous - add a warning and suggestion
        if New_val == ParamToModify.DefaultValue:
            if len(ParamToModify.ErrMessage) > 0:
                print("Warning: Parameter given (" + str(New_val) + ") for " + ParamToModify.Name + " is being set by \
                the input file to a value that is the same as the default. No change was made to that value. \
                Recommendation: remove the " + ParamToModify.Name + " from the input file unless you wish to \
                change it from the default value of (" + str(ParamToModify.DefaultValue) + ")")
                model.logger.warning("Parameter given (" + str(New_val) + ") for " + ParamToModify.Name + " is being \
                set by the input file to a value that is the same as the default. No change was made to that value. \
                Recommendation: remove the " + ParamToModify.Name + " from the input file unless you wish to \
                change it from the default value of (" + str(ParamToModify.DefaultValue) + ")")
            model.logger.info("Complete " + str(__name__) + ": " + sys._getframe().f_code.co_name)
            return

        # We have nothing to change - user provide value that was the same as the existing value (likely, the default value)
        if New_val == ParamToModify.value:
            return
        # user provided value is out of range, so announce it, leave set to whatever it was set to (default value)
        if not (New_val in ParamToModify.AllowableRange):
            if len(ParamToModify.ErrMessage) > 0:
                print("Error: Parameter given (" + str(New_val) + ") for " + ParamToModify.Name +
                      " outside of valid range. GEOPHIRES will " + ParamToModify.ErrMessage)
                model.logger.fatal("Error: Parameter given (" + str(New_val) + ") for " + ParamToModify.Name +
                                   " outside of valid range. GEOPHIRES will " + ParamToModify.ErrMessage)
            model.logger.info("Complete " + str(__name__) + ": " + sys._getframe().f_code.co_name)
            sys.exit()
        else:  # All is good
            ParamToModify.value = New_val  # set the new value
            ParamToModify.Provided = True  # set provided to true because we are using a user provide value now
            ParamToModify.Valid = True  # set Valid to true because it passed the validation tests
    elif isinstance(ParamToModify, floatParameter):
        New_val = float(ParameterReadIn.sValue)
        # Warning - the value read in is the same as the default value, making it superfluous - add a warning and suggestion
        if New_val == ParamToModify.DefaultValue:
            if len(ParamToModify.ErrMessage) > 0:
                print("Warning: Parameter given (" + str(New_val) + ") for " + ParamToModify.Name +
                      " is being set by the input file to a value that is the same as the default. No change was \
                      made to that value. Recommendation: remove the " + ParamToModify.Name + " from the input file \
                      unless you wish to change it from the default value of (" + str(ParamToModify.DefaultValue) + ")")
                model.logger.warning("Parameter given (" + str(New_val) + ") for " + ParamToModify.Name +
                                     " is being set by the input file to a value that is the same as the default. No change was \
                      made to that value. Recommendation: remove the " + ParamToModify.Name + " from the input file \
                      unless you wish to change it from the default value of (" + str(ParamToModify.DefaultValue) + ")")
            model.logger.info("Complete " + str(__name__) + ": " + sys._getframe().f_code.co_name)
        if New_val == ParamToModify.value:
            # We have nothing to change - user provide value that was the same as the existing value (likely, the default value)
            model.logger.info("Complete " + str(__name__) + ": " + sys._getframe().f_code.co_name)
            return
        # user provided value is out of range, so announce it, leave set to whatever it was set to (default value)
        if (New_val < float(ParamToModify.Min)) or (New_val > float(ParamToModify.Max)):
            if len(ParamToModify.ErrMessage) > 0:
                print("Error: Parameter given (" + str(New_val) + ") for " + ParamToModify.Name +
                      " outside of valid range. GEOPHIRES will " + ParamToModify.ErrMessage)
                model.logger.fatal("Error: Parameter given (" + str(New_val) + ") for " + ParamToModify.Name +
                                   " outside of valid range. GEOPHIRES will " + ParamToModify.ErrMessage)
            model.logger.info("Complete " + str(__name__) + ": " + sys._getframe().f_code.co_name)
            sys.exit()
        else:  # All is good
            ParamToModify.value = New_val  # set the new value
            ParamToModify.Provided = True  # set provided to true because we are using a user provide value now
            ParamToModify.Valid = True  # set Valid to true because it passed the validation tests
    elif isinstance(ParamToModify, listParameter):
        New_val = float(ParameterReadIn.sValue)
        if (New_val < float(ParamToModify.Min)) or (New_val > float(ParamToModify.Max)):
            # user provided value is out of range, so announce it, leave set to whatever it was set to (default value)
            if len(ParamToModify.ErrMessage) > 0:
                print("Warning: Parameter given (" + str(New_val) + ") for " + ParamToModify.Name +
                      " outside of valid range. GEOPHIRES will " + ParamToModify.ErrMessage)
                model.logger.warning("Parameter given (" + str(New_val) + ") for " + ParamToModify.Name +
                                     " outside of valid range. GEOPHIRES will " + ParamToModify.ErrMessage)
            model.logger.info("Complete " + str(__name__) + ": " + sys._getframe().f_code.co_name)
            return
        # All is good.  With a list, we have to use the last character of the Description to get the position.
        # I.e., "Gradient 1" should yield a position = 0 ("1" - 1)
        else:
            parts = ParameterReadIn.Name.split(' ')
            position = int(parts[1]) - 1
            if position >= len(ParamToModify.value):
                ParamToModify.value.append(New_val)  # we are adding to the list, so use append
            else:  # we are replacing a value, so pop the value we want to replace, then insert a new one
                ParamToModify.value.pop(position)
                ParamToModify.value.insert(position, New_val)
    elif isinstance(ParamToModify, boolParameter):
        if ParameterReadIn.sValue == "0":
            New_val = False
        if ParameterReadIn.sValue == "false" or ParameterReadIn.sValue == "False" or ParameterReadIn.sValue == "FALSE":
            New_val = False
        else:
            New_val = True
        if New_val == ParamToModify.value:
            model.logger.info("Complete " + str(__name__) + ": " + sys._getframe().f_code.co_name)
            # We have nothing to change - user provide value that was the same as the existing value (likely, the default value)
            return
        ParamToModify.value = New_val  # set the new value
        ParamToModify.Provided = True  # set provided to true because we are using a user provide value now
        ParamToModify.Valid = True  # set Valid to true because it passed the validation tests
    elif isinstance(ParamToModify, strParameter):
        New_val = str(ParameterReadIn.sValue)
        if New_val == ParamToModify.value:
            # We have nothing to change - user provide value that was the same as the existing value (likely, the default value)
            return
        ParamToModify.value = New_val  # set the new value
        ParamToModify.Provided = True  # set provided to true because we are using a user provide value now
        ParamToModify.Valid = True  # set Valid to true because it passed the validation tests

    model.logger.info("Complete " + str(__name__) + ": " + sys._getframe().f_code.co_name)


def ConvertUnits(ParamToModify, strUnit: str, model) -> str:
    """
    ConvertUnits gets called if a unit version is needed: either currency or standard units like F to C or m to ft
    Args:
        ParamToModify (Parameter): The Parameter that will be modified (assuming it passes validation and conversion)
        strUnit (str): A string containing the value to be converted along with the units it is current in.
        The units to convert to are set by the PreferredUnits of ParamToModify
        model (Model):  The container class of the application, giving access to everything else, including the logger
    Returns:
        str: The new value as a string (without the units, because they are already held in PreferredUnits of ParamToModify)
    """
    model.logger.info("Init " + str(__name__) + ": " + sys._getframe().f_code.co_name + " for " + ParamToModify.Name)

    # deal with the currency case
    if ParamToModify.UnitType in [Units.CURRENCY, Units.CURRENCYFREQUENCY, Units.COSTPERMASS, Units.ENERGYCOST]:
        prefType = ParamToModify.PreferredUnits.value
        parts = strUnit.split(' ')
        val = parts[0].strip()
        currType = parts[1].strip()
        # user has provided a currency that is the currency expected, so just strip off the currency
        if prefType == currType:
            strUnit = str(val)
            ParamToModify.UnitsMatch = True
            ParamToModify.CurrentUnits = currType
            return strUnit

        # First we need to deal the possibility that there is a suffix on the units (like /yr, kwh, or /tonne)
        # that will make it not be recognized by the currency conversion engine.
        # generally, we will just strip the suffix off of a copy of the string that represents the units,
        # then allow the conversion to happen. For now, we ignore the suffix.
        # this has the consequence that we don't do any conversion based on that suffix, so units like EUR/MMBTU
        # will trigger a conversion to USD/MMBTU, where MMBY+TU doesn't get converted to KW (or whatever)
        currSuff = prefSuff = ""
        elements = currType.split("/")
        if len(elements) > 1:
            currType = elements[0]  # strip off the suffix, but save it
            currSuff = "/" + elements[1]
        elements = prefType.split("/")
        if len(elements) > 1:
            prefType = elements[0]  # strip off the suffix, but save it
            prefSuff = "/" + elements[1]

        # Let's try to deal with first the simple conversion where the required units have a prefix like M (m) or K (k)
        # that means "million" or "thousand", like MUSD (or KUSD), and the user provided USD (or KUSD) or KEUR, MEUR
        # we have to deal with the case that the M, m, K, or k are NOT prefixes, but rather are a part of the currency name.
        cc = CurrencyCodes()
        currFactor = prefFactor = 1.0
        currPrefix = prefPrefix = False
        Factor = 1.0
        prefShort = prefType
        currShort = currType
        # if either of these returns a symbol, then we must have prefixes we need to deal with
        symbol = cc.get_symbol(prefType[1:])
        symbol2 = cc.get_symbol(currType[1:])
        if symbol is not None:
            prefPrefix = True
        if symbol2 is not None:
            currPrefix = True
        if prefPrefix and prefType[0] in ['M', 'm']:
            prefFactor = prefFactor * 1_000_000.0
        elif prefPrefix and prefType[0] in ['K', 'k']:
            prefFactor = prefFactor * 1000.0
        if currPrefix and currType[0] in ['M', 'm']:
            currFactor = currFactor / 1_000_000.0
        elif currPrefix and currType[0] in ['K', 'k']:
            currFactor = currFactor / 1000.0
        Factor = currFactor * prefFactor
        if prefPrefix:
            prefShort = prefType[1:]
        if currPrefix:
            currShort = currType[1:]
        # this is true, then we just have a conversion between KUSD and USD, MUSD to KUSD, MUER to EUR, etc,
        # so just do the simple factor conversion
        if prefShort == currShort:
            val = float(val) * Factor
            strUnit = str(val)
            ParamToModify.UnitsMatch = True
            ParamToModify.CurrentUnits = currType
            return strUnit

        # if we come here, we have a currency conversion to do (USD->EUR, etc).
        try:
            cr = CurrencyRates()
            conv_rate = cr.get_rate(currShort, prefShort)
        except BaseException as ex:
            print(str(ex))
            print("Error: GEOPHIRES failed to convert your currency for " + ParamToModify.Name +
                  " to something it understands. You gave " + strUnit + " - Are these currency units defined for \
                  forex-python?  or perhaps the currency server is down?  Please change your units to " +
                  ParamToModify.PreferredUnits.value + "to continue. Cannot continue unless you do.  Exiting.")
            model.logger.critical(str(ex))
            model.logger.critical("Error: GEOPHIRES failed to convert your currency for " + ParamToModify.Name +
                  " to something it understands. You gave " + strUnit + " - Are these currency units defined for \
                  forex-python?  or perhaps the currency server is down?  Please change your units to " +
                  ParamToModify.PreferredUnits.value + "to continue. Cannot continue unless you do.  Exiting.")
            sys.exit()
        New_val = (conv_rate * float(val)) * Factor
        strUnit = str(New_val)
        ParamToModify.UnitsMatch = False
        ParamToModify.CurrentUnits = parts[1]

        if len(prefSuff) > 0: prefType = prefType + prefSuff  # set it back the way it was
        if len(currSuff) > 0: currType = currType + currSuff
        parts = strUnit.split(' ')
        strUnit = parts[0]
        return strUnit

    else:  # must be something other than boolean, string, or currency
        if isinstance(strUnit, pint.Quantity):
            val = ParamToModify.value
            currType = str(strUnit)
        else:
            parts = strUnit.split(' ')
            val = parts[0].strip()
            currType = parts[1].strip()
        # check to see if the units provided (CurrentUnits) are the same as the preferred units.
        # In that case, we don't need to do anything.
        try:
            # Make a Pint Quantity out of the old value: the amount of the unit doesn't matter,
            # just the units, so I set the amount to 0
            Old_valQ = ureg.Quantity(0.000, str(ParamToModify.CurrentUnits.value))
            New_valQ = ureg.Quantity(float(val), currType)  # Make a Pint Quantity out of the new value
        except BaseException as ex:
            print(str(ex))
            print("Error: GEOPHIRES failed to initialize your units for " + ParamToModify.Name +
                  " to something it understands. You gave " + strUnit + " - Are the units defined for Pint library, \
                  or have you defined them in the user defined units file (GEOPHIRES3_newunits)?  Cannot continue.  \
                  Exiting.")
            model.logger.critical(str(ex))
            model.logger.critical("Error: GEOPHIRES failed to initialize your units for " + ParamToModify.Name +
                  " to something it understands. You gave " + strUnit + " - Are the units defined for Pint library, \
                  or have you defined them in the user defined units file (GEOPHIRES3_newunits)?  Cannot continue.  \
                  Exiting.")
            sys.exit()

        if Old_valQ.units != New_valQ.units:  # do the transformation only if the units don't match
            ParamToModify.CurrentUnits = LookupUnits(currType)[0]
            try:
                # ParamToModify.PreferredUnits.value)    #update The quantity to the preferred units,
                # so we don't have to change the underlying calculations.  This assumes that PInt recognizes our unit.
                # If we have a new unit, we have to add it to the Pint configuration text file
                New_valQ.ito(Old_valQ)
            except BaseException as ex:
                print(str(ex))
                print("Error: GEOPHIRES failed to convert your units for " + ParamToModify.Name +
                      " to something it understands. You gave " + strUnit + " - Are the units defined for Pint library, \
                      or have you defined them in the user defined units file (GEOPHIRES3_newunits)?  Cannot continue. \
                      Exiting.")
                model.logger.critical(str(ex))
                model.logger.critical("Error: GEOPHIRES failed to convert your units for " + ParamToModify.Name +
                      " to something it understands. You gave " + strUnit + " - Are the units defined for Pint library, \
                      or have you defined them in the user defined units file (GEOPHIRES3_newunits)?  Cannot continue. \
                      Exiting.")
                sys.exit()

            # set sValue to the value based on the new units - don't add units to it - it should just be a raw number
            strUnit = str(New_valQ.magnitude)
            ParamToModify.UnitsMatch = False
        else:
            # if we come here, we must have a unit declared, but the unit must be the same as the preferred unit,
            # so we need to just get rid of the extra text after the space
            parts = strUnit.split(' ')
            strUnit = parts[0]

    model.logger.info("Complete " + str(__name__) + ": " + sys._getframe().f_code.co_name)
    return strUnit


def ConvertUnitsBack(ParamToModify, model):
    """
    CovertUnitsBack: Converts units back to what the user specified they as.  It does this so that the user can see them
    in the report as the units they specified.  We know that because CurrentUnits contains the desired units
    Args:
        ParamToModify (Parameter): The Parameter that will be modified.
        model (Model):  The container class of the application, giving access to everything else, including the logger
    """
    model.logger.info("Init " + str(__name__) + ": " + sys._getframe().f_code.co_name + " for " + ParamToModify.Name)

    # deal with the currency case
    if ParamToModify.UnitType in [Units.CURRENCY, Units.CURRENCYFREQUENCY, Units.COSTPERMASS, Units.ENERGYCOST]:
        prefType = ParamToModify.PreferredUnits.value
        currType = ParamToModify.CurrentUnits

        # First we need to deal the possibility that there is a suffix on the units (like /yr, kwh, or /tonne)
        # that will make it not be recognized by the currency conversion engine.
        # generally, we will just strip the suffux off of a copy of the string that represents the units, then allow
        # the conversion to happen. For now, we ignore the suffix.
        # this has the consequence that we don't do any conversion based on that suffix, so units like EUR/MMBTU
        # will trigger a conversion to USD/MMBTU, where MMBY+TU dosesn't get converted to KW (or whatever)
        currSuff = prefSuff = ""
        elements = currType.split("/")
        if len(elements) > 1:
            currType = elements[0]  # strip off the suffix, but save it
            currSuff = "/" + elements[1]
        elements = prefType.split("/")
        if len(elements) > 1:
            prefType = elements[0]  # strip off the suffix, but save it
            prefSuff = "/" + elements[1]

        # Let's try to deal with first the simple conversion where the required units have a prefix like M (m) or K (k)
        # that means "million" or "thousand", like MUSD (or KUSD), and the user provided USD (or KUSD) or KEUR, MEUR
        # we have to deal with the case that the M, m, K, or k are NOT prefixes,
        # but rather are a part of the currency name.
        cc = CurrencyCodes()
        currFactor = prefFactor = 1.0
        currPrefix = prefPrefix = False
        Factor = 1.0
        prefShort = prefType
        currShort = currType
        symbol = cc.get_symbol(prefType[1:])  # if either of these returns a symbol, then we must have prefixes we need to deal with
        symbol2 = cc.get_symbol(currType[1:])
        if symbol is not None:
            prefPrefix = True
        if symbol2 is not None:
            currPrefix = True
        if prefPrefix and prefType[0] in ['M', 'm']:
            prefFactor = prefFactor * 1_000_000.0
        elif prefPrefix and prefType[0] in ['K', 'k']:
            prefFactor = prefFactor * 1000.0
        if currPrefix and currType[0] in ['M', 'm']:
            currFactor = currFactor / 1_000_000.0
        elif currPrefix and currType[0] in ['K', 'k']:
            currFactor = currFactor / 1000.0
        Factor = currFactor * prefFactor
        if prefPrefix:
            prefShort = prefType[1:]
        if currPrefix:
            currShort = currType[1:]
        if prefShort == currShort:
            # this is true, then we just have a conversion between KUSD and USD, MUSD to KUSD, MUER to EUR, etc.,
            # so just do the simple factor conversion
            ParamToModify.value = ParamToModify.value * Factor
            ParamToModify.UnitsMatch = True
            ParamToModify.CurrentUnits = currType
            return

        # Now lets deal with the case where the units still don't match, so we have a real currency conversion,
        # like USD to EUR
        # start the currency conversion process
        cc = CurrencyCodes()
        try:
            cr = CurrencyRates()
            conv_rate = cr.get_rate(currType, prefType)
        except BaseException as ex:
            print(str(ex))
            print("Error: GEOPHIRES failed to convert your currency for " + ParamToModify.Name +
                  " to something it understands. You gave " + currType + " - Are these currency units defined for \
                  forex-python?  or perhaps the currency server is down?  Please change your units to " +
                  ParamToModify.PreferredUnits.value + "to contine. Cannot continue unless you do.  Exiting.")
            model.logger.critical(str(ex))
            model.logger.critical("Error: GEOPHIRES failed to convert your currency for " + ParamToModify.Name +
                  " to something it understands. You gave " + currType + " - Are these currency units defined for \
                  forex-python?  or perhaps the currency server is down?  Please change your units to " +
                  ParamToModify.PreferredUnits.value + "to continue. Cannot continue unless you do.  Exiting.")
            sys.exit()
        ParamToModify.value = (conv_rate * float(ParamToModify.value)) / prefFactor
        ParamToModify.UnitsMatch = False
        model.logger.info("Complete " + str(__name__) + ": " + sys._getframe().f_code.co_name)
        return

    else:  # must be something other than currency
        if isinstance(ParamToModify.CurrentUnits, pint.Quantity):
            val = ParamToModify.CurrentUnits.magnitude
            currType = str(ParamToModify.CurrentUnits.units)
        else:
            if " " in ParamToModify.CurrentUnits.value:
                parts = ParamToModify.CurrentUnits.value.split(' ')
                val = parts[0].strip()
                currType = parts[1].strip()
            else:
                val = ParamToModify.value
                currType = ParamToModify.CurrentUnits.value

        try:
            if isinstance(ParamToModify.PreferredUnits, pint.Quantity):
                prefQ = ParamToModify.PreferredUnits
            else:
                # Make a Pint Quantity out of the old value
                prefQ = ureg.Quantity(float(val), str(ParamToModify.PreferredUnits.value))
            if isinstance(ParamToModify.CurrentUnits, pint.Quantity):
                currQ = ParamToModify.CurrentUnits
            else:
                currQ = ureg.Quantity(float(val), currType)  # Make a Pint Quantity out of the new value
        except BaseException as ex:
            print(str(ex))
            print("Error: GEOPHIRES failed to initialize your units for " + ParamToModify.Name +
                  " to something it understands. You gave " + currType + " - Are the units defined for Pint library, \
                  or have you defined them in the user defined units file (GEOPHIRES3_newunits)?  Cannot continue. \
                  Exiting.")
            model.logger.critical(str(ex))
            model.logger.critical("Error: GEOPHIRES failed to initialize your units for " + ParamToModify.Name +
                  " to something it understands. You gave " + currType + " - Are the units defined for Pint library, \
                  or have you defined them in the user defined units file (GEOPHIRES3_newunits)?  Cannot continue. \
                  Exiting.")
            sys.exit()
        try:
            # update The quantity back to the current units (the units that we started with) units
            # so the display will be in the right units
            currQ = prefQ.to(currQ)
        except BaseException as ex:
            print(str(ex))
            print("Error: GEOPHIRES failed to convert your units for " + ParamToModify.Name +
                  " to something it understands. You gave " + currType + " - Are the units defined for Pint library, \
                  or have you defined them in the user defined units file (GEOPHIRES3_newunits)?  Cannot continue. \
                  Exiting.")
            model.logger.critical(str(ex))
            model.logger.critical("Error: GEOPHIRES failed to convert your units for " + ParamToModify.Name +
                  " to something it understands. You gave " + currType + " - Are the units defined for Pint library, \
                  or have you defined them in the user defined units file (GEOPHIRES3_newunits)?  Cannot continue. \
                  Exiting.")
            sys.exit()

        # rest the value
        ParamToModify.value = currQ.magnitude
    model.logger.info("Complete " + str(__name__) + ": " + sys._getframe().f_code.co_name)


def LookupUnits(sUnitText: str):
    """
    LookupUnits Given a unit class and a text string, this will return the value from the Enumneration if it is there
    (or return nothing if it is not)
    Args:
        sUnitText (str): The units desired to be checked (e.g., "ft", "degF")
    Returns:
        Enum: The Enumerated value and the Unit class Enumeration
    """
    # look through all unit types and names for a match with my units
    for uType in Units:
        MyEnum = None
        if uType == Units.LENGTH:
            MyEnum = LengthUnit
        elif uType == Units.AREA:
            MyEnum = AreaUnit
        elif uType == Units.VOLUME:
            MyEnum = VolumeUnit
        elif uType == Units.MASS:
            MyEnum = MassUnit
        elif uType == Units.DENSITY:
            MyEnum = DensityUnit
        elif uType == Units.TEMPERATURE:
            MyEnum = TemperatureUnit
        elif uType == Units.PRESSURE:
            MyEnum = PressureUnit
        elif uType == Units.TIME:
            MyEnum = TimeUnit
        elif uType == Units.FLOWRATE:
            MyEnum = FlowRateUnit
        elif uType == Units.TEMP_GRADIENT:
            MyEnum = TemperatureGradientUnit
        elif uType == Units.DRAWDOWN:
            MyEnum = DrawdownUnit
        elif uType == Units.IMPEDANCE:
            MyEnum = ImpedanceUnit
        elif uType == Units.PRODUCTIVITY_INDEX:
            MyEnum = ProductivityIndexUnit
        elif uType == Units.INJECTIVITY_INDEX:
            MyEnum = InjectivityIndexUnit
        elif uType == Units.HEAT_CAPACITY:
            MyEnum = HeatCapacityUnit
        elif uType == Units.THERMAL_CONDUCTIVITY:
            MyEnum = ThermalConductivityUnit
        elif uType == Units.CURRENCY:
            MyEnum = CurrencyUnit
        elif uType == Units.CURRENCYFREQUENCY:
            MyEnum = CurrencyFrequencyUnit
        elif uType == Units.PERCENT:
            MyEnum = PercentUnit
        elif uType == Units.ENERGY:
            MyEnum = EnergyUnit
        elif uType == Units.ENERGYCOST:
            MyEnum = EnergyCostUnit
        elif uType == Units.ENERGYFREQUENCY:
            MyEnum = EnergyFrequencyUnit
        elif uType == Units.COSTPERMASS:
            MyEnum = CostPerMassUnit
        elif uType == Units.AVAILABILITY:
            MyEnum = AvailabilityUnit
        elif uType == Units.ENTROPY:
            MyEnum = EntropyUnit
        elif uType == Units.ENTHALPY:
            MyEnum = EnthalpyUnit
        elif uType == Units.POROSITY:
            MyEnum = PorosityUnit
        elif uType == Units.PERMEABILITY:
            MyEnum = PermeabilityUnit
        elif uType == Units.ENERGYDENSITY:
            MyEnum = EnergyDensityUnit
        elif uType == Units.MASSPERTIME:
            MyEnum = MassPerTimeUnit
        elif uType == Units.COSTPERDISTANCE:
            MyEnum = CostPerDistanceUnit
        elif uType == Units.POWER:
            MyEnum = PowerUnit
        elif uType == Units.CO2PRODUCTION:
            MyEnum = CO2ProductionUnit
        elif uType == Units.ENERGYPERCO2:
            MyEnum = EnergyPerCO2Unit

        if MyEnum is not None:
            for item in MyEnum:
                if item.value == sUnitText:
                    return item, uType
    return None, None


def ConvertOutputUnits(oparam: OutputParameter, newUnit: Units, model):
    """
    ConvertOutputUnits Given an output parameter, convert the value(s) from what they contain
    (as calculated by GEOPHIRES) to what the user specified as what they want for outputs.  Conversion happens inline.
    Args:
        oparam (OutputParameter): The parameter you want to be converted (value or list of values).
               Because Parameters know the PreferredUnits and CurrentUnits, this routine knows what to do.
        newUnit (Units): The new units you want to convert value to
        model (Model):  The container class of the application, giving access to everything else, including the logger

    Returns:
        None
    """
    if isinstance(oparam.value, str):
        return  # strings have no units
    elif isinstance(oparam.value, bool):
        return  # booleans have no units
    DefUnit, UnitSystem = LookupUnits(newUnit.value)

    if UnitSystem not in [Units.CURRENCY, Units.CURRENCYFREQUENCY, Units.COSTPERMASS, Units.ENERGYCOST]:
        if isinstance(oparam.value, float) or isinstance(oparam.value, int):
            # this is a simple unit conversion- could be just units (meters->feet) or simple currency ($->EUR)
            # or compound Currency (MUSD-EUR)
            try:
                fromQ = ureg.Quantity(oparam.value,
                                      str(oparam.PreferredUnits.value))  # Make a Pint Quantity out of the value
                toQ = ureg.Quantity(0, str(newUnit.value))  # Make a Pint Quantity out of the new value
            except BaseException as ex:
                print(str(ex))
                print("Warning: GEOPHIRES failed to initialize your units for " + oparam.Name +
                      " to something it understands. You gave " + newUnit.value + " - Are the units defined for Pint \
                      library, or have you defined them in the user defined units file (GEOPHIRES3_newunits)? \
                      Continuing without output conversion.")
                model.logger.warning(str(ex))
                model.logger.warning("Warning: GEOPHIRES failed to initialize your units for " + oparam.Name +
                      " to something it understands. You gave " + newUnit.value + " - Are the units defined for Pint \
                      library, or have you defined them in the user defined units file (GEOPHIRES3_newunits)? \
                      Continuing without output conversion.")
                return
            try:
                toQ = fromQ.to(toQ)  # update The quantity to the units that the user wanted
            except BaseException as ex:
                print(str(ex))
                print("Warning: GEOPHIRES failed to convert your units for " + oparam.Name +
                      " to something it understands. You gave " + newUnit.value + " - Are the units defined for Pint \
                      library, or have you defined them in the user defined units file (GEOPHIRES3_newunits)?\
                      Continuing without output conversion.")
                model.logger.warning(str(ex))
                model.logger.warning("Warning: GEOPHIRES failed to convert your units for " + oparam.Name +
                      " to something it understands. You gave " + newUnit.value + " - Are the units defined for Pint \
                      library, or have you defined them in the user defined units file (GEOPHIRES3_newunits)? \
                      Continuing without output conversion.")
                return
            # reset the value and current units
            oparam.value = toQ.magnitude
            oparam.CurrentUnits = newUnit

        elif isinstance(oparam.value, array):  # handle the array case
            i = 0
            for arrayval in oparam.value:
                try:
                    fromQ = ureg.Quantity(oparam.value[i], str(oparam.PreferredUnits.value))  # Make a Pint Quantity out of the from value
                    toQ = ureg.Quantity(0, str(newUnit.value))  # Make a Pint Quantity out of the new value
                except BaseException as ex:
                    print(str(ex))
                    print("Warning: GEOPHIRES failed to initialize your units for " + oparam.Name +
                          " to something it understands. You gave " + str(newUnit.value) + " -Are the units defined for\
                           Pint library, or have you defined them in the user defined units file (GEOPHIRES3_newunits)?\
                            Continuing without output conversion.")
                    model.logger.warning(str(ex))
                    model.logger.warning("Warning: GEOPHIRES failed to initialize your units for " + oparam.Name +
                            " to something it understands. You gave " + str(newUnit.value) + " - Are the units defined \
                            for Pint library, or have you defined them in the user defined units file (GEOPHIRES3_newunits)? \
                            Continuing without output conversion.")
                    return
                try:
                    toQ = fromQ.to(toQ)  # update The quantity to the units that the user wanted
                except BaseException as ex:
                    print(str(ex))
                    print("Warning: GEOPHIRES failed to convert your units for " + oparam.Name +
                          " to something it understands. You gave " + str(newUnit.value) +
                          " - Are the units defined for Pint library, or have you defined them in the user defined \
                          units file (GEOPHIRES3_newunits)?    continuing without output conversion.")
                    model.logger.warning(str(ex))
                    model.logger.warning("Warning: GEOPHIRES failed to convert your units for " + oparam.Name +
                          " to something it understands. You gave " + str(newUnit.value) +
                          " - Are the units defined for Pint library, or have you defined them in the user defined \
                          units file (GEOPHIRES3_newunits)?   continuing without output conversion.")
                    return

                # reset the value and current units
                oparam.value[i] = toQ.magnitude
                oparam.CurrentUnits = newUnit
                i = i + 1

    else:  # must be a currency thing.
        prefType = oparam.PreferredUnits.value
        currType = newUnit.value

        # First we need to deal the possibility that there is a suffix on the units (like /yr, kwh, or /tonne)
        # that will make it not be recognized by the currency conversion engine.
        # generally, we will just strip the suffix off of a copy of the string that represents the units, then
        # allow the conversion to happen. For now, we ignore the suffix.
        # this has the consequence that we don't do any conversion based on that suffix, so units like EUR/MMBTU
        # will trigger a conversion to USD/MMBTU, where MMBY+TU dosesn't get converted to KW (or whatever)
        currSuff = prefSuff = ""
        elements = currType.split("/")
        if len(elements) > 1:
            currType = elements[0]  # strip off the suffix, but save it
            currSuff = "/" + elements[1]
        elements = prefType.split("/")
        if len(elements) > 1:
            prefType = elements[0]  # strip off the suffix, but save it
            prefSuff = "/" + elements[1]

        # Let's try to deal with first the simple conversion where the required units have a prefix like M (m) or K (k)
        # that means "million" or "thousand", like MUSD (or KUSD), and the user provided USD (or KUSD) or KEUR, MEUR
        # we have to deal with the case that the M, m, K, or k are NOT prefixes, but rather
        # are a part of the currency name.
        cc = CurrencyCodes()
        currFactor = prefFactor = 1.0
        currPrefix = prefPrefix = False
        Factor = 1.0
        prefShort = prefType
        currShort = currType
        symbol = cc.get_symbol(prefType[1:])  # if either of these returns a symbol, then we must have prefixes we need to deal with
        symbol2 = cc.get_symbol(currType[1:])
        if symbol is not None:
            prefPrefix = True
        if symbol2 is not None:
            currPrefix = True
        if prefPrefix and prefType[0] in ['M', 'm']:
            prefFactor = prefFactor * 1_000_000.0
        elif prefPrefix and prefType[0] in ['K', 'k']:
            prefFactor = prefFactor * 1000.0
        if currPrefix and currType[0] in ['M', 'm']:
            currFactor = currFactor / 1_000_000.0
        elif currPrefix and currType[0] in ['K', 'k']:
            currFactor = currFactor / 1000.0
        Factor = currFactor * prefFactor
        if prefPrefix:
            prefShort = prefType[1:]
        if currPrefix:
            currShort = currType[1:]
        if prefShort == currShort:
            # this is true, then we just have a conversion between KUSD and USD, MUSD to KUSD, MUER to EUR, etc.,
            # so just do the simple factor conversion and exit
            oparam.value = oparam.value * Factor
            oparam.CurrentUnits = DefUnit
            oparam.UnitsMatch = False
            return

        # start the currency conversion process
        # if we have a symbol for a currency type, then the type is known to the library.
        # If we don't try some tricks to make it into something it does do recognize
        symbol = cc.get_symbol(currShort)
        if symbol is None:
            print("Error: GEOPHIRES failed to convert your currency for " + oparam.Name +
                  " to something it understands. You gave " + currType + " - Are these currency units defined for \
                  forex-python?  or perhaps the currency server is down?  Please change your units to " +
                  oparam.PreferredUnits.value + "to continue. Cannot continue unless you do.  Exiting.")
            model.logger.critical("Error: GEOPHIRES failed to convert your currency for " + oparam.Name +
                  " to something it understands. You gave " + currType + " - Are these currency units defined for \
                  forex-python?  or perhaps the currency server is down?  Please change your units to " +
                  oparam.PreferredUnits.value + "to continue. Cannot continue unless you do.  Exiting.")
            sys.exit()

        symbol = cc.get_symbol(prefShort)
        # if we have a symbol for a currency type, then the type is known to the library.  If we don't
        # try some tricks to make it into something it does do recognize
        if symbol is None:
            print("Error: GEOPHIRES failed to convert your currency for " + oparam.Name +
                  " to something it understands. You gave " + prefType + " - Are these currency units defined for \
                  forex-python?  or perhaps the currency server is down?  Please change your units to " +
                  oparam.PreferredUnits.value + "to continue. Cannot continue unless you do.  Exiting.")
            model.logger.critical("Error: GEOPHIRES failed to convert your currency for " + oparam.Name +
                  " to something it understands. You gave " + prefType + " - Are these currency units defined for \
                  forex-python?  or perhaps the currency server is down?  Please change your units to " +
                  oparam.PreferredUnits.value + "to continue. Cannot continue unless you do.  Exiting.")
            sys.exit()
        try:
            cr = CurrencyRates()
            conv_rate = cr.get_rate(prefShort, currShort)
        except BaseException as ex:
            print(str(ex))
            print("Error: GEOPHIRES failed to convert your currency for " + oparam.Name +
                  " to something it understands. You gave " + currType + " - Are these currency units defined for \
                  forex-python?  or perhaps the currency server is down?  Please change your units to " +
                  oparam.PreferredUnits.value + "to continue. Cannot continue unless you do.  Exiting.")
            model.logger.critical(str(ex))
            model.logger.critical("Error: GEOPHIRES failed to convert your currency for " + oparam.Name +
                  " to something it understands. You gave " + currType + " - Are these currency units defined for \
                  forex-python?  or perhaps the currency server is down?  Please change your units to " +
                  oparam.PreferredUnits.value + "to continue. Cannot continue unless you do.  Exiting.")
            sys.exit()
        oparam.value = (Factor * conv_rate * float(oparam.value))
        oparam.CurrentUnits = DefUnit
        oparam.UnitsMatch = False
        model.logger.info("Complete " + str(__name__) + ": " + sys._getframe().f_code.co_name)

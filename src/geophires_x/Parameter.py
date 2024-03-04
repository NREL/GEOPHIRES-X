# copyright, 2023, Malcolm I Ross
import copy
import os.path
import sys
from array import array
from typing import List, Optional, Any
from dataclasses import dataclass, field
from enum import IntEnum
from forex_python.converter import CurrencyRates, CurrencyCodes
import pint

from abc import ABC

from pint.facets.plain import PlainQuantity

from geophires_x.Units import *

ureg = pint.get_application_registry()
ureg.load_definitions(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'GEOPHIRES3_newunits.txt'))


class HasQuantity(ABC):

    def quantity(self) -> PlainQuantity:
        """
        :rtype: pint.registry.Quantity - note type annotation uses PlainQuantity due to issues with python 3.8 failing
            to import the Quantity TypeAlias
        """
        return ureg.Quantity(self.value, str(self.CurrentUnits.value))


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
    Comment: Optional[str] = None


@dataclass
class OutputParameter(HasQuantity):
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
class Parameter(HasQuantity):
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

    def __post_init__(self):
        if self.value is None:
            self.value:bool = self.DefaultValue

    value: bool = None
    DefaultValue: bool = value
    json_parameter_type: str = 'boolean'


@dataclass
class intParameter(Parameter):
    """
    intParameter: a dataclass that stores the values for an Integer value.  Includes the default value and the
    validation values (if appropriate).  Child of Parameter, so it gets all the Attributes of that class.

    Attributes:
        value (int): The value of that parameter
        DefaultValue (int, 0):  The default value of that parameter
        AllowableRange (list): A list of the valid values
    """

    def __post_init__(self):
        if self.value is None:
            self.value:int = self.DefaultValue

    value: int = None
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

    def __post_init__(self):
        if self.value is None:
            self.value = self.DefaultValue

    value: float = None

    DefaultValue: float = 0.0
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
    def __post_init__(self):
        if self.value is None:
            self.value:str = self.DefaultValue

    value: str = None
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

    def __post_init__(self):
        if self.value is None:
            self.value:str = self.DefaultValue

    value: List[float] = None
    DefaultValue: List[float] = field(default_factory=list)
    Min: float = -1.8e308
    Max: float = 1.8e308
    json_parameter_type: str = 'array'


def ReadParameter(ParameterReadIn: ParameterEntry, ParamToModify, model):
    """
    ReadParameter: A method to take a single ParameterEntry object and use it to update the associated Parameter.
    Does validation as well as Unit and Currency conversion
    :param ParameterEntry: The value the user wants to change and the value they want to change it to (as a string)
     and  any comment they provided with it (as a string) - all in one object (ParameterEntry) that is passed in
      to this method as a parameter itself (ParameterReadIn) - see ParameterEntry class for details on the fields in it
    :type ParameterEntry: :class:`~geophires_x.Parameter.ParameterEntry`
    :param ParamToModify: The Parameter that will be modified (assuming it passes validation and conversion) - this is
      the object that will be modified by this method - see Parameter class for details on the fields in it
    :type ParamToModify: :class:`~geophires_x.Parameter.Parameter`
    :param model: The container class of the application, giving access to everything else, including the logger
    :type model: :class:`~geophires_x.Model.Model`
    :return: None
    """
    model.logger.info(f'Init {str(__name__)}: {sys._getframe().f_code.co_name} for {ParamToModify.Name}')

    # these Parameter Types don't have units so don't do anything fancy, and ignore it if the user has supplied units
    if isinstance(ParamToModify, boolParameter) or isinstance(ParamToModify, strParameter):
        if isinstance(ParamToModify, boolParameter):
            if ParameterReadIn.sValue in ['0', 'false', 'False', 'f', 'F', 'no', 'No', 'n', 'N']:
                ParamToModify.value = False
            elif ParameterReadIn.sValue in ['1', 'true', 'True', 't', 'T', 'yes', 'Yes', 'y', 'Y']:
                ParamToModify.value = True
            else:
                ParamToModify.value = bool(ParameterReadIn.sValue)
        else:
            ParamToModify.value = ParameterReadIn.sValue
        ParamToModify.Provided = True  # set provided to true because we are using a user provide value now
        ParamToModify.Valid = True  # set Valid to true because it passed the validation tests
        model.logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')
        return

    # deal with the case where the value has a unit involved - that will be indicated by a space in it
    if ' ' in ParameterReadIn.sValue:
        new_str = ConvertUnits(ParamToModify, ParameterReadIn.sValue, model)
        if len(new_str) > 0:
            ParameterReadIn.sValue = new_str
    else:
        # The value came in without any units, so it must be using the default PreferredUnits
        ParamToModify.CurrentUnits = ParamToModify.PreferredUnits
        ParamToModify.UnitsMatch = True

    def default_parameter_value_message(new_val: Any, param_to_modify_name: str, default_value: Any) -> str:
        return (
            f'Parameter given ({str(New_val)}) for {ParamToModify.Name} is the same as the default value. '
            f'Consider removing {ParamToModify.Name} from the input file unless you wish '
            f'to change it from the default value of ({str(ParamToModify.DefaultValue)})'
        )

    if isinstance(ParamToModify, intParameter):
        New_val = int(float(ParameterReadIn.sValue))

        if New_val == ParamToModify.DefaultValue:
            if len(ParamToModify.ErrMessage) > 0:
                msg = default_parameter_value_message(New_val, ParamToModify.Name, ParamToModify.DefaultValue)
                model.logger.info(msg)

            model.logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')
            return

        if New_val == ParamToModify.value:
            # We have nothing to change - user provide value that was the same as the
            # existing value (likely, the default value)
            return

        if not (New_val in ParamToModify.AllowableRange):
            # user provided value is out of range, so announce it, leave set to whatever it was set to (default value)
            err_msg = f"Error: Parameter given ({New_val}) for {ParamToModify.Name} outside of valid range."
            print(err_msg)
            model.logger.fatal(err_msg)
            model.logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')
            raise ValueError(err_msg)
        else:
            # All is good
            ParamToModify.value = New_val  # set the new value
            ParamToModify.Provided = True  # set provided to true because we are using a user provide value now
            ParamToModify.Valid = True  # set Valid to true because it passed the validation tests
    elif isinstance(ParamToModify, floatParameter):
        New_val = float(ParameterReadIn.sValue)

        if New_val == ParamToModify.DefaultValue:
            # Warning - the value read in is the same as the default value, making it superfluous
            # - add a warning and suggestion

            ParamToModify.Provided = True
            if len(ParamToModify.ErrMessage) > 0:
                msg = default_parameter_value_message(New_val, ParamToModify.Name, ParamToModify.DefaultValue)
                model.logger.info(msg)

            model.logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')
        if New_val == ParamToModify.value:
            # We have nothing to change - user provided value that was the same as the
            # existing value (likely, the default value)
            model.logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')
            return

        if (New_val < float(ParamToModify.Min)) or (New_val > float(ParamToModify.Max)):
            # user provided value is out of range, so announce it, leave set to whatever it was set to (default value)
            err_msg = f'Error: Parameter given ({New_val}) for {ParamToModify.Name} outside of valid range.'
            print(err_msg)
            model.logger.fatal(err_msg)
            model.logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')
            raise ValueError(err_msg)
        else:
            # All is good
            ParamToModify.value = New_val  # set the new value
            ParamToModify.Provided = True  # set provided to true because we are using a user provide value now
            ParamToModify.Valid = True  # set Valid to true because it passed the validation tests
    elif isinstance(ParamToModify, listParameter):
        New_val = float(ParameterReadIn.sValue)
        if (New_val < float(ParamToModify.Min)) or (New_val > float(ParamToModify.Max)):
            # user provided value is out of range, so announce it, leave set to whatever it was set to (default value)
            if len(ParamToModify.ErrMessage) > 0:
                msg = (
                    f'Parameter given ({str(New_val)}) for {ParamToModify.Name} outside of valid range.'
                    f'GEOPHIRES will {ParamToModify.ErrMessage}'
                )
                print(f'Warning: {msg}')
                model.logger.warning(msg)
            model.logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')
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
            model.logger.info(f'Complete {str(__name__)}": {sys._getframe().f_code.co_name}')
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

    model.logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')


def ConvertUnits(ParamToModify, strUnit: str, model) -> str:
    """
    ConvertUnits gets called if a unit version is needed: either currency or standard units like F to C or m to ft
    :param ParamToModify: The Parameter that will be modified (assuming it passes validation and conversion) - this is
        the object that will be modified by this method - see Parameter class for details on the fields in it
    :type ParamToModify: :class:`~geophires_x.Parameter.Parameter`
    :param strUnit: A string containing the value to be converted along with the units it is currently in.
        The units to convert to are set by the PreferredUnits of ParamToModify
    :type strUnit: str
    :param model: The container class of the application, giving access to everything else, including the logger
    :type model: :class:`~geophires_x.Model.Model`
    :return: The new value as a string (without the units, because they are already held in PreferredUnits of ParamToModify)
    :rtype: str
    """
    model.logger.info(f'Init {str(__name__)}: {sys._getframe().f_code.co_name} for {ParamToModify.Name}')

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
        # that means a "million" or a "thousand", like MUSD (or KUSD), and the user provided USD (or KUSD) or KEUR, MEUR
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

        if prefShort == currShort:
            # this is true, then we just have a conversion between KUSD and USD, MUSD to KUSD, MUER to EUR, etc.,
            # so just do the simple factor conversion

            val = float(val) * Factor
            strUnit = str(val)
            ParamToModify.UnitsMatch = True
            ParamToModify.CurrentUnits = currType
            return strUnit

        try:
            # if we come here, we have a currency conversion to do (USD->EUR, etc.).
            cr = CurrencyRates()
            conv_rate = cr.get_rate(currShort, prefShort)
        except BaseException as ex:
            print(str(ex))
            msg = (
                f'Error: GEOPHIRES failed to convert your currency for {ParamToModify.Name} to something it '
                f'understands. You gave {strUnit} - Are these currency units defined for forex-python? or perhaps the '
                f'currency server is down?  Please change your units to {ParamToModify.PreferredUnits.value} to '
                f'continue. Cannot continue unless you do.  Exiting.'
            )
            print(msg)
            model.logger.critical(str(ex))
            model.logger.critical(msg)

            raise RuntimeError(msg)

        New_val = (conv_rate * float(val)) * Factor
        strUnit = str(New_val)
        ParamToModify.UnitsMatch = False
        ParamToModify.CurrentUnits = parts[1]

        if len(prefSuff) > 0:
            prefType = prefType + prefSuff  # set it back the way it was
        if len(currSuff) > 0:
            currType = currType + currSuff
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
            msg = (
                f'Error: GEOPHIRES failed to initialize your units for {ParamToModify.Name} '
                f'to something it understands. '
                f'You gave {strUnit} - Are the units defined for Pint library, or have you defined them in the '
                f'user-defined units file (GEOPHIRES3_newunits)?  Cannot continue. Exiting.'
            )
            print(msg)
            model.logger.critical(str(ex))
            model.logger.critical(msg)

            raise RuntimeError(msg)

        if Old_valQ.units != New_valQ.units:  # do the transformation only if the units don't match
            ParamToModify.CurrentUnits = LookupUnits(currType)[0]
            try:
                # update the quantity to the preferred units,
                # so we don't have to change the underlying calculations.  This assumes that Pint recognizes our unit.
                # If we have a new unit, we have to add it to the Pint configuration text file
                New_valQ.ito(Old_valQ)
            except BaseException as ex:
                print(str(ex))
                msg = (
                    f'Error: GEOPHIRES failed to convert your units for {ParamToModify.Name} '
                    f'to something it understands. You gave {strUnit} - Are the units defined for Pint library, '
                    f'or have you defined them in the user defined units file (GEOPHIRES3_newunits)? '
                    f'Cannot continue. Exiting.'
                )
                print(msg)
                model.logger.critical(str(ex))
                model.logger.critical(msg)

                raise RuntimeError(msg)

            # set sValue to the value based on the new units - don't add units to it - it should just be a raw number
            strUnit = str(New_valQ.magnitude)

            new_val_units_lookup = LookupUnits(str(New_valQ.units))
            if new_val_units_lookup is not None and new_val_units_lookup[0] is not None:
                ParamToModify.CurrentUnits = new_val_units_lookup[0]

            ParamToModify.UnitsMatch = False
        else:
            # if we come here, we must have a unit declared, but the unit must be the same as the preferred unit,
            # so we need to just get rid of the extra text after the space
            parts = strUnit.split(' ')
            strUnit = parts[0]

    model.logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')
    return strUnit


def ConvertUnitsBack(ParamToModify: Parameter, model):
    """
    CovertUnitsBack: Converts units back to what the user specified they as.  It does this so that the user can see them
    in the report as the units they specified. We know that because CurrentUnits contains the desired units
    :param param: The Parameter that will be modified (assuming it passes validation and conversion) - this is
        the object that will be modified by this method - see Parameter class for details on the fields in it
    :type param: :class:`~geophires_x.Parameter.Parameter`
    :param model: The container class of the application, giving access to everything else, including the logger
    :type model: :class:`~geophires_x.Model.Model`
    :return: None
    """
    model.logger.info(f'Init {str(__name__)}: {sys._getframe().f_code.co_name} for {ParamToModify.Name}')
    param_modified: Parameter = parameter_with_units_converted_back_to_preferred_units(ParamToModify, model)
    ParamToModify.value = param_modified.value
    ParamToModify.CurrentUnits = param_modified.CurrentUnits
    ParamToModify.UnitType = param_modified.UnitsMatch
    model.logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')


def parameter_with_units_converted_back_to_preferred_units(param: Parameter, model) -> Parameter:
    param_with_units_converted_back = copy.deepcopy(param)

    # deal with the currency case
    if param.UnitType in [Units.CURRENCY, Units.CURRENCYFREQUENCY, Units.COSTPERMASS, Units.ENERGYCOST]:
        prefType = param.PreferredUnits.value
        currType = param.CurrentUnits

        # First we need to deal the possibility that there is a suffix on the units (like /yr, kwh, or /tonne)
        # that will make it not be recognized by the currency conversion engine.
        # generally, we will just strip the suffix off of a copy of the string that represents the units, then allow
        # the conversion to happen. For now, we ignore the suffix.
        # this has the consequence that we don't do any conversion based on that suffix, so units like EUR/MMBTU
        # will trigger a conversion to USD/MMBTU, where MMBY+TU doesn't get converted to KW (or whatever)
        currSuff = prefSuff = ""
        elements = str(currType).split("/")
        if len(elements) > 1:
            currType = elements[0]  # strip off the suffix, but save it
            currSuff = "/" + elements[1]
        elements = prefType.split("/")
        if len(elements) > 1:
            prefType = elements[0]  # strip off the suffix, but save it
            prefSuff = "/" + elements[1]

        # Let's try to deal with first the simple conversion where the required units have a prefix like M (m) or K (k)
        # that means a "million" or a "thousand", like MUSD (or KUSD), and the user provided USD (or KUSD) or KEUR, MEUR
        # we have to deal with the case that the M, m, K, or k are NOT prefixes,
        # but rather are a part of the currency name.
        cc = CurrencyCodes()
        currFactor = prefFactor = 1.0
        currPrefix = prefPrefix = False
        Factor = 1.0
        prefShort = prefType
        currShort = currType
        symbol = cc.get_symbol(
            prefType[1:]
        )  # if either of these returns a symbol, then we must have prefixes we need to deal with
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
            param_with_units_converted_back.value = param.value * Factor
            param_with_units_converted_back.UnitsMatch = True
            param_with_units_converted_back.CurrentUnits = currType
            return param_with_units_converted_back

        # Now lets deal with the case where the units still don't match, so we have a real currency conversion,
        # like USD to EUR
        # start the currency conversion process
        cc = CurrencyCodes()
        try:
            cr = CurrencyRates()
            conv_rate = cr.get_rate(currType, prefType)
        except BaseException as ex:
            print(str(ex))
            msg = (
                f'Error: GEOPHIRES failed to convert your currency for {param.Name} to something it understands.'
                f'You gave {currType} - Are these currency units defined for forex-python? '
                f'or perhaps the currency server is down?  Please change your units to {param.PreferredUnits.value}'
                f'to continue. Cannot continue unless you do.  Exiting.'
            )
            print(msg)
            model.logger.critical(str(ex))
            model.logger.critical(msg)

            raise RuntimeError(msg, ex)

        param_with_units_converted_back.value = (conv_rate * float(param.value)) / prefFactor
        param_with_units_converted_back.UnitsMatch = False
        return param_with_units_converted_back

    else:
        # must be something other than currency
        if isinstance(param.CurrentUnits, pint.Quantity):
            val = param.CurrentUnits.value
            currType = str(param.CurrentUnits.value)
        else:
            if ' ' in param.CurrentUnits.value:
                parts = param.CurrentUnits.value.split(' ')
                val = parts[0].strip()
                currType = parts[1].strip()
            else:
                val = param.value
                currType = param.CurrentUnits.value

        try:
            if isinstance(param.PreferredUnits, pint.Quantity):
                prefQ = param.PreferredUnits
            else:
                # Make a Pint Quantity out of the old value
                prefQ = param.PreferredUnits
            if isinstance(param.CurrentUnits, pint.Quantity):
                currQ = param.CurrentUnits
            else:
                currQ = ureg.Quantity(float(val), currType)  # Make a Pint Quantity out of the new value
        except BaseException as ex:
            print(str(ex))
            msg = (
                f'Error: GEOPHIRES failed to initialize your units for {param.Name} to something it understands. '
                f'You gave {currType} - Are the units defined for Pint library, '
                f'or have you defined them in the user defined units file (GEOPHIRES3_newunits)? '
                f'Cannot continue. Exiting.'
            )
            print(msg)
            model.logger.critical(str(ex))
            model.logger.critical(msg)

            raise RuntimeError(msg)
        try:
            # update The quantity back to the current units (the units that we started with) units
            # so the display will be in the right units
            currQ = currQ.to(prefQ)
        except BaseException as ex:
            print(str(ex))
            msg = (
                f'Error: GEOPHIRES failed to convert your units for {param.Name} to something it understands. '
                f'You gave {currType}  - Are the units defined for Pint library, '
                f' or have you defined them in the user defined units file (GEOPHIRES3_newunits)? '
                f'Cannot continue. Exiting.'
            )
            print(msg)
            model.logger.critical(str(ex))
            model.logger.critical(msg)

            raise RuntimeError(msg)

        # reset the values
        if param.value != currQ.magnitude:
            param_with_units_converted_back.value = currQ.magnitude
            param_with_units_converted_back.CurrentUnits = param.PreferredUnits

    return param_with_units_converted_back


def LookupUnits(sUnitText: str):
    """
    LookupUnits Given a unit class and a text string, this will return the value from the Enumeration if it is there
    (or return nothing if it is not)
    :param sUnitText: The text string to look for in the Enumeration of units (like "m" or "feet") - this is the text
        that the user provides in the input file or the GUI to specify the units they want to use for a parameter or
        output value (like "m" or "feet")
    :type sUnitText: str (text)
    :return: The Enumerated value and the Unit class Enumeration
    :rtype: tuple
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
    :param oparam: The parameter you want to be converted (value or list of values).  Because Parameters know the
        PreferredUnits and CurrentUnits, this routine knows what to do. It will convert the value(s) in the parameter
        to the new units, and then reset the CurrentUnits to the new units. This is done so that the user can see the units
        they specified in the output report. The value(s) in the parameter are converted back to the original units after
        the report is generated. This is done so that the calculations are done in the units that GEOPHIRES expects. If
        the user wants to see the output in different units, they can specify that in the input file or the GUI.
    :type oparam: :class:`~geophires_x.Parameter.Parameter`
    :param newUnit: The new units you want to convert value to (like "m" or "feet") - this is the text that the user
        provides in the input file or the GUI to specify the units they want to use for a parameter or output value
        (like "m" or "feet")
    :type newUnit: str (text)
    :param model: The container class of the application, giving access to everything else, including the logger
    :type model: :class:`~geophires_x.Model.Model`
    :return: None
    """
    if isinstance(oparam.value, str):
        return  # strings have no units
    elif isinstance(oparam.value, bool):
        return  # booleans have no units
    DefUnit, UnitSystem = LookupUnits(str(newUnit.value))

    if UnitSystem not in [Units.CURRENCY, Units.CURRENCYFREQUENCY, Units.COSTPERMASS, Units.ENERGYCOST]:
        if isinstance(oparam.value, float) or isinstance(oparam.value, int):
            # this is a simple unit conversion: it could be just units (meters->feet) or simple currency ($->EUR)
            # or compound Currency (MUSD-EUR)
            try:
                fromQ = ureg.Quantity(
                    oparam.value, str(oparam.PreferredUnits.value)
                )  # Make a Pint Quantity out of the value
                toQ = ureg.Quantity(0, str(newUnit.value))  # Make a Pint Quantity out of the new value
            except BaseException as ex:
                print(str(ex))
                msg = (
                    "Warning: GEOPHIRES failed to initialize your units for "
                    + oparam.Name
                    + " to something it understands. You gave "
                    + str(newUnit.value)
                    + " - Are the units defined for Pint"
                    + " library, or have you defined them in the user defined units file (GEOPHIRES3_newunits)?"
                    + " Continuing without output conversion."
                )
                print(msg)
                model.logger.warning(str(ex))
                model.logger.warning(msg)
                return
            try:
                toQ = fromQ.to(toQ)  # update The quantity to the units that the user wanted
            except BaseException as ex:
                print(str(ex))
                msg = (
                    "Warning: GEOPHIRES failed to convert your units for "
                    + oparam.Name
                    + " to something it understands. You gave "
                    + str(newUnit.value)
                    + " - Are the units defined for Pint"
                    + " library, or have you defined them in the user defined units file (GEOPHIRES3_newunits)?"
                    + " Continuing without output conversion."
                )
                print(msg)
                model.logger.warning(str(ex))
                model.logger.warning(msg)
                return
            # reset the value and current units
            oparam.value = toQ.magnitude
            oparam.CurrentUnits = newUnit

        elif isinstance(oparam.value, array):  # handle the array case
            i = 0
            for arrayval in oparam.value:
                try:
                    fromQ = ureg.Quantity(
                        oparam.value[i], str(oparam.PreferredUnits.value)
                    )  # Make a Pint Quantity out of from the value
                    toQ = ureg.Quantity(0, str(newUnit.value))  # Make a Pint Quantity out of the new value
                except BaseException as ex:
                    print(str(ex))
                    msg = (
                        "Warning: GEOPHIRES failed to initialize your units for "
                        + oparam.Name
                        + " to something it understands. You gave "
                        + str(newUnit.value)
                        + " -Are the units defined for"
                        + " Pint library, or have you defined them in the user defined units file (GEOPHIRES3_newunits)?"
                        + " Continuing without output conversion."
                    )
                    print(msg)
                    model.logger.warning(str(ex))
                    model.logger.warning(msg)
                    return
                try:
                    toQ = fromQ.to(toQ)  # update The quantity to the units that the user wanted
                except BaseException as ex:
                    print(str(ex))
                    msg = (
                        "Warning: GEOPHIRES failed to convert your units for "
                        + oparam.Name
                        + " to something it understands. You gave "
                        + str(newUnit.value)
                        + " - Are the units defined for Pint library, or have you defined them in the user defined"
                        + " units file (GEOPHIRES3_newunits)?    continuing without output conversion."
                    )
                    print(msg)
                    model.logger.warning(str(ex))
                    model.logger.warning(msg)
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
        # will trigger a conversion to USD/MMBTU, where MMBY+TU doesn't get converted to KW (or whatever)
        currSuff = prefSuff = ""
        elements = str(currType).split("/")
        if len(elements) > 1:
            currType = elements[0]  # strip off the suffix, but save it
            currSuff = "/" + elements[1]
        elements = prefType.split("/")
        if len(elements) > 1:
            prefType = elements[0]  # strip off the suffix, but save it
            prefSuff = "/" + elements[1]

        # Let's try to deal with first the simple conversion where the required units have a prefix like M (m) or K (k)
        # that means a "million" or a "thousand", like MUSD (or KUSD), and the user provided USD (or KUSD) or KEUR, MEUR
        # we have to deal with the case that the M, m, K, or k are NOT prefixes, but rather
        # are a part of the currency name.
        cc = CurrencyCodes()
        currFactor = prefFactor = 1.0
        currPrefix = prefPrefix = False
        Factor = 1.0
        prefShort = prefType
        currShort = currType
        symbol = cc.get_symbol(
            prefType[1:]
        )  # if either of these returns a symbol, then we must have prefixes we need to deal with
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
            msg = (
                f'Error: GEOPHIRES failed to convert your currency for {oparam.Name} to something it understands. '
                f'You gave {currType}  - Are these currency units defined for forex-python? '
                f' or perhaps the currency server is down?  Please change your units to {oparam.PreferredUnits.value}'
                f'to continue. Cannot continue unless you do.  Exiting.'
            )
            print(msg)
            model.logger.critical(msg)

            raise RuntimeError(msg)

        symbol = cc.get_symbol(prefShort)
        # if we have a symbol for a currency type, then the type is known to the library.  If we don't
        # try some tricks to make it into something it does do recognize
        if symbol is None:
            msg = (
                f'Error: GEOPHIRES failed to convert your currency for {oparam.Name} to something it understands. '
                f'You gave {prefType}  - Are these currency units defined for forex-python? '
                f' or perhaps the currency server is down?  Please change your units to {oparam.PreferredUnits.value}'
                f'to continue. Cannot continue unless you do.  Exiting.'
            )

            print(msg)
            model.logger.critical(msg)

            raise RuntimeError(msg)
        try:
            cr = CurrencyRates()
            conv_rate = cr.get_rate(prefShort, currShort)
        except BaseException as ex:
            print(str(ex))

            msg = (
                f'Error: GEOPHIRES failed to convert your currency for {oparam.Name} to something it understands. '
                f'You gave {currType} - Are these currency units defined for forex-python?'
                f'or perhaps the currency server is down? '
                f'Please change your units to {oparam.PreferredUnits.value} to continue.'
                f'Cannot continue unless you do.  Exiting.'
            )

            print(msg)

            model.logger.critical(str(ex))
            model.logger.critical(msg)

            raise RuntimeError(msg)

        oparam.value = Factor * conv_rate * float(oparam.value)
        oparam.CurrentUnits = DefUnit
        oparam.UnitsMatch = False
        model.logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')

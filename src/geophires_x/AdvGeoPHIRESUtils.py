# copyright, 2023, Malcolm I Ross
import sys
import os
from os.path import exists
import hashlib
import numpy as np
from pprint import pprint
from datetime import datetime
import json
import jsons
from mysql.connector import connect, Error
from .Parameter import Parameter, intParameter, boolParameter, floatParameter, strParameter, listParameter, OutputParameter
from enum import Enum
from .OptionList import ReservoirModel, FractureShape, ReservoirVolume, EndUseOptions, PowerPlantType, EconomicModel, WellDrillingCostCorrelation, WorkingFluid, Configuration

from cryptography.fernet import Fernet
import zlib


UseDatabase = False


def encrypt(message: bytes, key: bytes) -> bytes:
    return Fernet(key).encrypt(message)


def decrypt(token: bytes, key: bytes) -> bytes:
    return Fernet(key).decrypt(token)


def write_key():
    key = Fernet.generate_key()  # Generates the key
    with open("key.key", "wb") as key_file:  # Opens the file the key is to be written to
        key_file.write(key)  # Writes the key


def load_key():
    return open("key.key", "rb").read()  # Opens the file, reads and returns the key stored in the file


def DumpObjectAsJson(obj) -> str:
    """
    The DumpObjectAsJson function accepts a Python object and returns a JSON string representation of that object.
    The function is useful for debugging purposes, as it allows you to dump an object's contents to the console in
    a human-readable format.

    :param obj: Pass in the object that you want to convert into a json string
    :return: A string of the object in json format
    :doc-author: Malcolm Ross
    """
    jsons.suppress_warnings(True)
    return jsons.dumps(obj, indent=4, sort_keys=True, supress_warnings=True)


def read_JSONinput_file(fname: str, model) -> dict:
    """
    The read_JSONinput_file function reads a JSON input file and returns a dictionary of parameters.
    The function is called by the run_model function to read in the JSON input file.
    :param fname:str: Pass the name of the json file that contains the input parameters
    :param model: The container class of the application, giving access to everything else, including the logger
    :return: A dictionary of parameter entry objects
    :doc-author: Malcolm Ross
    """
    model.logger.info("Init " + str(__name__))
    ReturnDict1 = {}
    # read input data
    try:
        if exists(fname):
            model.logger.info("Found filename: " + fname + " Proceeding with run using JSON input parameters from that file")
            with open(fname, encoding='UTF-8') as f:
                if fname.upper().endswith('.JSON'):
                    dJson = json.load(f)
        else:
            model.logger.warn("File: " + fname + "  not found - proceeding with default parameter run...")
            return {}

    except BaseException as ex:
        print(ex)
        model.logger.error(
            "Error " + str(ex) + "using JSON filename:" + fname + " proceeding with default parameter run...")
        return {}

    if fname.upper().endswith('.JSON'):
        for item in dJson.items():
            PEntry = Parameter.ParameterEntry(item[0], str(item[1]['Value']), item[1]['Comment'])
            # make the dictionary element with the key set to lowercase without spaces.
            # This should help the algorithm br more forgiving about finding things in the dictionary
            ReturnDict1[item[0]] = PEntry

    model.logger.info("Complete " + str(__name__) + ": " + sys._getframe().f_code.co_name)
    return ReturnDict1


def PopulateStructureFromDict(obj, dd: dict) -> any:
    """
    The PopulateStructureFromDict function rehydrates the object based on values in the JSON-based dictionary -
    # copy the original values for the object for those that don't change,
    # and use the dictionary values for the ones that might have changed
    # we need to iterate through all the entries looking for a match to the one we are looking for,
    # setting dd to the right dictionary once we find it
    :param obj: The object that needs to be rehydrated
    :param dd: is a dictionary of dictionaries containing the values to use in the rehydration
    :return: A parameter entry object or None if error
    :doc-author: Malcolm Ross
    """
    #
    for key in dd:
        valdict = dd[key]
        if not isinstance(valdict, dict):
            continue  # skip it if it is a not a dict
        if "value" not in valdict:
            continue  # skip is there is a "value" entry - if there isn't, it must not be valid
        if "Name" not in valdict:
            continue  # skip is there is a "Name" entry - if there isn't, it must not be valid
        if valdict["Name"] == obj.Name:
            ddx = valdict
            break

    try:
        if isinstance(obj, OutputParameter):
            if isinstance(obj.value, float):
                if '[' in str(ddx["value"]):
                    obj.value = list(ddx["value"])  # if it has "[" it must be a list
                else:
                    obj.value = float(ddx["value"])
            elif isinstance(obj.value, int):
                obj.value = int(ddx["value"])
            elif isinstance(obj.value, bool):
                obj.value = bool(ddx["value"])
            elif isinstance(obj.value, str):
                obj.value = str(ddx["value"])
            elif isinstance(obj.value, list):
                obj.value = np.array(list(ddx["value"]))
            else:
                obj.value = ddx["value"]
            return OutputParameter(obj.Name, value=obj.value, UnitType=obj.UnitType,
                                   PreferredUnits=obj.PreferredUnits, CurrentUnits=obj.CurrentUnits,
                                   UnitsMatch=obj.UnitsMatch)
        else:
            if "Provided" in ddx:
                obj.Provided = bool(ddx["Provided"])
            if "Valid" in ddx:
                obj.Valid = bool(ddx["Valid"])
            # ignore all the other parameters because that can't won't be changed by users.
            # The only failure here is when the CurrentUnits change...

            # different value types makes it a bit complicated
            if isinstance(obj, floatParameter):
                if not isinstance(ddx["value"], list):
                    obj.value = float(ddx["value"])
                else:
                    obj.value = list(ddx["value"])
                return floatParameter(obj.Name, value=obj.value, Required=obj.Required,
                                      Provided=obj.Provided, Valid=obj.Valid, ErrMessage=obj.ErrMessage,
                                      InputComment=obj.InputComment, ToolTipText=obj.ToolTipText,
                                      UnitType=obj.UnitType, PreferredUnits=obj.PreferredUnits,
                                      CurrentUnits=obj.CurrentUnits, UnitsMatch=obj.UnitsMatch,
                                      DefaultValue=obj.DefaultValue, Min=obj.Min, Max=obj.Max)
            elif isinstance(obj, intParameter):  # int is complicated because it can be an int or an enum
                if isinstance(obj.value,
                              Enum):  # Enums are even more complicated but only exist for input parameters
                    if isinstance(obj.value, ReservoirModel):
                        obj.value = ReservoirModel[obj.value.name]
                    elif isinstance(obj.value, ReservoirVolume):
                        obj.value = ReservoirVolume[obj.value.name]
                    elif isinstance(obj.value, FractureShape):
                        obj.value = FractureShape[obj.value.name]
                    elif isinstance(obj.value, EndUseOptions):
                        obj.value = EndUseOptions[obj.value.name]
                    elif isinstance(obj.value, PowerPlantType):
                        obj.value = PowerPlantType[obj.value.name]
                    elif isinstance(obj.value, EconomicModel):
                        obj.value = EconomicModel[obj.value.name]
                    elif isinstance(obj.value, WellDrillingCostCorrelation):
                        obj.value = WellDrillingCostCorrelation[obj.value.name]
                    elif isinstance(obj.value, WorkingFluid):
                        obj.value = WorkingFluid[obj.value.name]
                    elif isinstance(obj.value, Configuration):
                        obj.value = Configuration[obj.value.name]
                else:
                    obj.value = int(ddx["value"])
                return intParameter(obj.Name, value=obj.value, Required=obj.Required,
                                    Provided=obj.Provided, Valid=obj.Valid, ErrMessage=obj.ErrMessage,
                                    InputComment=obj.InputComment, ToolTipText=obj.ToolTipText,
                                    UnitType=obj.UnitType, PreferredUnits=obj.PreferredUnits,
                                    CurrentUnits=obj.CurrentUnits, UnitsMatch=obj.UnitsMatch,
                                    DefaultValue=obj.DefaultValue, AllowableRange=obj.AllowableRange)
            elif isinstance(obj, boolParameter):
                obj.value = bool(ddx["value"])
                return boolParameter(obj.Name, value=obj.value, Required=obj.Required,
                                     Provided=obj.Provided, Valid=obj.Valid, ErrMessage=obj.ErrMessage,
                                     InputComment=obj.InputComment, ToolTipText=obj.ToolTipText,
                                     UnitType=obj.UnitType, PreferredUnits=obj.PreferredUnits,
                                     CurrentUnits=obj.CurrentUnits, UnitsMatch=obj.UnitsMatch,
                                     DefaultValue=obj.DefaultValue)
            elif isinstance(obj, strParameter):
                obj.value = str(ddx["value"])
                return strParameter(obj.Name, value=obj.value, Required=obj.Required,
                                    Provided=obj.Provided, Valid=obj.Valid, ErrMessage=obj.ErrMessage,
                                    InputComment=obj.InputComment, ToolTipText=obj.ToolTipText,
                                    UnitType=obj.UnitType, PreferredUnits=obj.PreferredUnits,
                                    CurrentUnits=obj.CurrentUnits, UnitsMatch=obj.UnitsMatch,
                                    DefaultValue=obj.DefaultValue)
            elif isinstance(obj, listParameter):
                obj.value = list(ddx["value"])
                return listParameter(obj.Name, value=obj.value, Required=obj.Required,
                                     Provided=obj.Provided, Valid=obj.Valid, ErrMessage=obj.ErrMessage,
                                     InputComment=obj.InputComment, ToolTipText=obj.ToolTipText,
                                     UnitType=obj.UnitType, PreferredUnits=obj.PreferredUnits,
                                     CurrentUnits=obj.CurrentUnits, UnitsMatch=obj.UnitsMatch,
                                     DefaultValue=obj.DefaultValue, Min=obj.Min, Max=obj.Max)
            else:
                obj.value = ddx["value"]
                return strParameter(obj.Name, value=obj.value, Required=obj.Required,
                                    Provided=obj.Provided, Valid=obj.Valid, ErrMessage=obj.ErrMessage,
                                    InputComment=obj.InputComment, ToolTipText=obj.ToolTipText,
                                    UnitType=obj.UnitType, PreferredUnits=obj.PreferredUnits,
                                    CurrentUnits=obj.CurrentUnits, UnitsMatch=obj.UnitsMatch,
                                    DefaultValue=obj.DefaultValue)
    except Error as ex:
        print(ex)
        return None


def CalculateHash(code_path: str, obj) -> str:
    """
    The CalculateHash function converts the input parameters and code to JSON and hashes it
    :param code_path:str: Pass the path of the python source code file that contains the code that processes the input parameters
    :param obj: the object that contains the input parameters
    :return: A string of the one-way hash of those two inputs
    :doc-author: Malcolm Ross
    """

    OutputAsJSON = DumpObjectAsJson(obj.ParameterDict)
    KeyAsHash = hashlib.blake2b(OutputAsJSON.encode())
    with open(code_path, 'r', encoding='UTF-8') as f:
        code = f.read()
    KeyAsHash.update(bytes(code, 'utf-8'))
    KeyAsHash = KeyAsHash.hexdigest()
    return KeyAsHash


def RestoreValuesFromDict(model, dd: dict, obj) -> bool:
    """
    The RestoreValuesFromDict function populates the object with the previously calculated results
    stored in a dictionary that was returned from the database
    :param model: The container class of the application, giving access to everything else, including the logger
    :param dd: The sdictionary that contains the parameters that we want to restore
    :param obj the object to which the parameters will be restored
    :return: bool, True is successful, False if not
    :doc-author: Malcolm Ross
    """
    # populate the object with the previously calculated results
    # stored in a dictionary that was returned from the database
    sclass = str(obj.__class__)
    try:
        if "Reservoir" in sclass:  # Try to rehydrate the Reservoir object
            for key in model.reserv.ParameterDict:
                model.reserv.ParameterDict[key] = PopulateStructureFromDict(model.reserv.ParameterDict[key], dd)
            for key in model.reserv.OutputParameterDict:
                model.reserv.OutputParameterDict[key] = PopulateStructureFromDict(model.reserv.OutputParameterDict[key], dd)

        elif "WellBores" in sclass:  # Try to rehydrate the WellBores object
            for key in model.wellbores.ParameterDict:
                model.wellbores.ParameterDict[key] = PopulateStructureFromDict(model.wellbores.ParameterDict[key], dd)
            for key in model.wellbores.OutputParameterDict:
                model.wellbores.OutputParameterDict[key] = PopulateStructureFromDict(model.wellbores.OutputParameterDict[key], dd)

        elif "SurfacePlant" in sclass:  # Try to rehydrate the SurfacePlant object
            for key in model.surfaceplant.ParameterDict:
                model.surfaceplant.ParameterDict[key] = PopulateStructureFromDict(model.surfaceplant.ParameterDict[key], dd)
            for key in model.surfaceplant.OutputParameterDict:
                model.surfaceplant.OutputParameterDict[key] = PopulateStructureFromDict(model.surfaceplant.OutputParameterDict[key], dd)

        elif "<class 'Economics.Economics'>" in sclass:
            for key in model.economics.ParameterDict:
                model.economics.ParameterDict[key] = PopulateStructureFromDict(model.economics.ParameterDict[key], dd)
            for key in model.economics.OutputParameterDict:
                model.economics.OutputParameterDict[key] = PopulateStructureFromDict(model.economics.OutputParameterDict[key], dd)

        elif "EconomicsAddOns" in sclass:
            for key in model.addeconomics.ParameterDict:
                model.addeconomics.ParameterDict[key] = PopulateStructureFromDict(model.addeconomics.ParameterDict[key], dd)
            for key in model.addeconomics.OutputParameterDict:
                model.addeconomics.OutputParameterDict[key] = PopulateStructureFromDict(model.addeconomics.OutputParameterDict[key], dd)

        elif "EconomicsCCUS" in sclass:
            for key in model.ccuseconomics.ParameterDict:
                model.ccuseconomics.ParameterDict[key] = PopulateStructureFromDict(model.ccuseconomics.ParameterDict[key], dd)
            for key in model.ccuseconomics.OutputParameterDict:
                model.ccuseconomics.OutputParameterDict[key] = PopulateStructureFromDict(model.ccuseconomics.OutputParameterDict[key], dd)

        elif "EconomicsS_DAC_GT" in sclass:
            for key in model.sdacgteconomics.ParameterDict:
                model.sdacgteconomics.ParameterDict[key] = PopulateStructureFromDict(model.sdacgteconomics.ParameterDict[key], dd)
            for key in model.sdacgteconomics.OutputParameterDict:
                model.sdacgteconomics.OutputParameterDict[key] = PopulateStructureFromDict(model.sdacgteconomics.OutputParameterDict[key], dd)

        return True
    except Error as ex:
        print(ex)
        model.logger.error("Error " + str(ex) + " Restoring the values from the database to the object. Proceeding as if we didn't find the object in the database.")
        return False
    return False


def RunStoredProcedure(store_procedure_name: str, parameters: list) -> list:
    """
    The RunStoredProcedure runs a stored procedure in the database
    :param store_procedure_name:str: The name of the stored procedure
    :param parameters: The parameters that need to passed to the stored procedure
    :return: A list of results from the stored procedure
    :doc-author: Malcolm Ross
    """
    if not UseDatabase:
        return []
    res = details = warnings = obj = None
    with connect(host="localhost", user="malcolm", password=".Carnot.", database="geophiresx") as connection:
        try:
            obj = connection.cursor()
            res = obj.callproc(store_procedure_name, parameters)
            connection.commit()
            for result in obj.stored_results():
                details = result.fetchall()
                warnings = result.fetchwarnings()
            obj.close()
            connection.close()
        except connection.Error as err:
            print("Something went wrong: {}".format(err))
            return []
    return details


def ReadParameterFromJson(dJson: dict, ParameterDict: dict):
    """
    The ReadParameterFromJson function reads a JSON string and updates the parameters of this class accordingly.
    :param dJson:dict: Pass the dictionary that is derived from encoding a json string to the function
    :param ParameterDict:dict: The parameter dict
    :return: The value of the parameter that is passed in
    :doc-author: Malcolm Ross
    """
    for item in dJson.items():
        if item[0] in ParameterDict:
            if isinstance(ParameterDict[item[0]], Parameter.floatParameter):
                val = float(item[1]['Value'])
            if isinstance(ParameterDict[item[0]], Parameter.intParameter):
                val = int(float(item[1]['Value']))
            if isinstance(ParameterDict[item[0]], Parameter.boolParameter):
                val = bool(item[1]['Value'])
            if isinstance(ParameterDict[item[0]], Parameter.strParameter):
                val = str(item[1]['Value'])
            ParameterDict[item[0]].value = val


def CheckForExistingResult(model, obj) -> str:
    """
    The CheckForExistingResult function checks the database for an existing result. If so, return the key value.
    the obj contains the path to the code and the parameters to be hashed to create the key
    :param model: The container class of the application, giving access to everything else, including the logger
    :param obj: Return the dictionary of parameters to the main function
    :return: the key value to use to look up the result in the database, or empty string if not using database, or error message
    :doc-author: Malcolm Ross
    """
    if not UseDatabase:
        return ""
    model.logger.info("Init " + str(__name__))
    # convert the input parameters abd code to JSON and hash it
    KeyAsHash = CalculateHash(obj.MyPath, obj)

    # Now search the database for something that already has that hash.
    try:
        with connect(host="localhost", user="malcolm", password=".Carnot.", database="geophiresx") as connection:
            SQLCommand = ("SELECT value FROM geophiresx.objects where uniquekey = \'" + KeyAsHash + "\'")
            with connection.cursor() as cursor:
                cursor.execute(SQLCommand)
                row = cursor.fetchone()
                if row is not None:  # we have a key, let's use it to populate the object then return the hash
                    dd = returnDictByKey(model, KeyAsHash)
                    # try to restore the object -
                    # if it fails, make it seem like there was no object so the calculation will run again
                    if not RestoreValuesFromDict(model, dd, obj):
                        return ""
                    model.logger.info("Restored " + obj.MyClass + " using hash =" + KeyAsHash)
                    print("Restored " + obj.MyClass + " using hash =" + KeyAsHash)
                else:
                    model.logger.info("Could not restore " + obj.MyClass + " using hash =" + KeyAsHash)
                    print("Could not restore " + obj.MyClass + " using hash =" + KeyAsHash)
                    KeyAsHash = ""  # if it is not found, return empty string
    except Error as ex:
        print(ex)
        model.logger.error("Error " + str(ex) + "Checking the database for result. Proceeding as if we didn't find one.")
        return "ERROR: " + str(ex)

    # model.logger.info("Complete "+ str(__name__) + ": " + sys._getframe().f_code.co_name)
    return KeyAsHash


def store_result(model, obj) -> str:
    """
    The store_result function stores a result in the database
    :param model: The container class of the application, giving access to everything else, including the logger
    :param obj: Return the dictionary of parameters to the main function
    :return: returns the database key for the value it just stored (which is a has of the code+input data)
               or error string, if error
    :doc-author: Malcolm Ross
    """
    if not UseDatabase:
        return ""
    model.logger.info("Init " + str(__name__))

    # handle encryption stuff
    key = ""
    if exists("key.key"):
        key = load_key()  # Loads the key and stores it in a variable
    else:
        write_key()  # Writes the key to the key file
        key = load_key()  # Loads the key and stores it in a variable
    f = Fernet(key)

    # convert the input parameters abd code to JSON and hash it
    KeyAsHash = CalculateHash(obj.MyPath, obj)

    # Now we have the unique key based on the inputs and the code.
    # We now need get the object we want to store in a form we can store it
    OutputAsJSON = DumpObjectAsJson(obj)
    ValueToStore = str(OutputAsJSON)

    encrypted_message = f.encrypt(ValueToStore.encode())
    compressed_message = zlib.compress(encrypted_message, -1)

    # set the other values we will store
    now = datetime.now()  # current date and time
    sdate_time = str(now.strftime("%Y%m%d%H%M%S%f"))
    user = str(os.getlogin())

    # now try to write those as a record in the database
    try:
        with connect(host="localhost", user="malcolm", password=".Carnot.", database="geophiresx") as connection:
            SQLCommand = "INSERT INTO geophiresx.objects(uniquekey,class, name, datetime, value, ze_value) VALUES(%s,%s,%s,%s,%s, %s)"
            with connection.cursor() as cursor:
                cursor.execute(SQLCommand,
                               (KeyAsHash, obj.MyClass, user, sdate_time, ValueToStore, compressed_message))
                connection.commit()
                model.logger.info("Stored " + obj.MyClass + " under hash =" + KeyAsHash)
                print("Stored " + obj.MyClass + " under hash =" + KeyAsHash)
    except Error as ex:
        print(ex)
        model.logger.error(
            "Error " + str(ex) + "writing into the database with the result. Proceeding as if we did.")
        return "ERROR: " + str(ex)

    model.logger.info("Complete " + str(__name__) + ": " + sys._getframe().f_code.co_name)
    return KeyAsHash


def returnDictByKey(model, skey: str) -> dict:
    """
    The returnDictByKey function returns values from the database based on a search key
    The function is called by the run_model function to read in the JSON input file.
    :param model: The container class of the application, giving access to everything else, including the logger
    :param skey: the unique value for which to search in the database for.
    :return:the object as a dictionary, or an empty dictionary, if error or if not using database
    :doc-author: Malcolm Ross
    """
    if not UseDatabase:
        return {}

    model.logger.info("Init " + str(__name__))
    # now try to read the record in the database
    try:
        with connect(host="localhost", user="malcolm", password=".Carnot.", database="geophiresx") as connection:
            SQLCommand = ("SELECT value FROM geophiresx.objects where uniquekey = \'" + skey + "\'")
            with connection.cursor() as cursor:
                cursor.execute(SQLCommand)
                row = cursor.fetchone()
                if row is not None:
                    dd = json.loads(row[0])
                    return dd  # if it is found, return the key
                else:
                    return {}  # if it is not found, return none
    except Error as ex:
        print(ex)
        model.logger.error(
            "Error " + str(ex) + " getting the database for result. Proceeding as if we didn't find one.")
        return {}


def SmartCalculate(model, obj):
    """
    The SmartCalculate function call the Calculate method on an object,
    but only if a record doesn't exist in the database that was calculated already.
    If it has to calculate something, it stores the calculation result in the database with the right key
    :param model: The container class of the application, giving access to everything else, including the logger
    :param obj: The object that contains the Calculate Method we will run unless the database contains the has we are looking for
    :doc-author: Malcolm Ross
    """
    obj.Calculate(model)  # run calculation because there was nothing in the database

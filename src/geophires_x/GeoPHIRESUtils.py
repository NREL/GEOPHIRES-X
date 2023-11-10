import sys
from geophires_x.Parameter import ParameterEntry
from os.path import exists
import dataclasses
import json


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
        try:
            if exists(f_name):
                content = []
                logger.info(
                    f'Found filename: {f_name}. Proceeding with run using input parameters from that file')
                with open(f_name, encoding='UTF-8') as f:
                    # store all input in one long string that will be passed to all objects
                    # so they can parse out their specific parameters (and ignore the rest)
                    content = f.readlines()
            else:
                logger.warn(f'File: {f_name} not found - proceeding with default parameter run...')
                return

        except BaseException as ex:
            print(ex)
            logger.error(f'Error {ex} using filename {f_name} proceeding with default parameter run...')
            return

        # successful read of data into list.  Now make a dictionary with all the parameter entries.
        # Index will be the unique name of the parameter.
        # The value will be a "ParameterEntry" structure, with name, value (optionally with units), optional comment
        for line in content:
            if line.startswith("#"):
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
        logger.warn("No input parameter file specified on the command line. Proceeding with default parameter run... ")

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

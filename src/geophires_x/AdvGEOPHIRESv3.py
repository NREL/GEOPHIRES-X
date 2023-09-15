#! python
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  6 10:34:04 2017

@author: kbeckers V1 and V2; Malcolm Ross V3
# copyright, 2023, Malcolm I Ross
"""

# GEOPHIRES v3.0 Advanced for GUI interfacing
# build date: May 2022
# github address: https://github.com/malcolm-dsider/GEOPHIRES-X

import os
import sys
from datetime import datetime
import logging
import logging.config
from .AdvModel import AdvModel
import jsons
from deepdiff import DeepDiff
from pprint import pprint
import numpy as np


def main():
    # set up logging.
    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger('root')
    logger.info("Init " + str(__name__))

    # set the starting directory to be the directory that this file is in
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # initiate the entire model
    model = AdvModel()

    # read the parameters that apply to the model
    model.read_parameters()

    # Calculate the entire model
    model.Calculate()

    # write the outputs, if requested
    model.outputs.PrintOutputs(model)

    # if the user has asked for it, copy the output file to the screen
    if model.outputs.printoutput:
        outputfile = "HDR.out"
        if len(sys.argv) > 2: outputfile = sys.argv[2]
        with open(outputfile, 'r', encoding='UTF-8') as f:
            content = f.readlines()  # store all output in one long list

            # Now write each line to the screen
            for line in content:
                sys.stdout.write(line)

    # analysis
    # start by making a second model and comparing them
    # model1 = AdvModel()
    # model1.read_parameters()
    # model1.reserv.gradient.value[0] = 0.08 #change the gradient between the models
    # model1.Calculate()
    # dd=DeepDiff(model, model1, significant_digits=0).pretty()
    # with open('output.txt', 'wt') as out: pprint(dd, stream=out)

    # Do a sensitvity analysis.  Try ambient temperature from 15-30 in 1 degree steps, monitoring electrcity produced.
    # TrackingValue1 = {}
    # model1 = AdvModel()
    # model1.read_parameters()
    # for model1.surfaceplant.Tenv.value in range(0,30,1):
    #    model1.Calculate()
    #    TrackingValue1[model1.surfaceplant.Tenv.value] = np.average(model1.surfaceplant.NetElectricityProduced.value)
    # pprint(TrackingValue1)
    # with open('Sensitivty.txt', 'wt') as out: pprint(TrackingValue1, stream=out)

    # try dumping the whole model to json.  Dumping the whole thing fails, so just dump the important parts.
    # ToDump = {model.reserv, model.wellbores, model.surfaceplant, model.ccuseconomics, model.addeconomics}
    # dJson = {}
    # Json1 = {}
    # for obj in ToDump:
    #     dJson1 = jsons.dump(obj, indent=4, sort_keys = True, supress_warnings=True, strip_microseconds = True, strip_nulls = True, strip_privates = True, strip_properties = True, use_enum_name = True)
    #    dJson.update(dJson1)

    # convert dict to string
    # strJson = str(dJson)
    # makesure that string 100% conforms to JSON spec
    #    strJson = strJson.replace("\'", "\"")
    #    strJson = strJson.replace("True", "\"True\"")
    #    strJson = strJson.replace("False", "\"False\"")

    # now wtite it as a date-time stamped file
    #    now = datetime.now() # current date and time
    #    date_time = now.strftime("%Y%m%d%H%M%S")
    #    with open(date_time+'.json','w', encoding='UTF-8') as f:
    #        f.write(str(strJson))

    logger.info("Complete " + str(__name__) + ": " + sys._getframe().f_code.co_name)


if __name__ == "__main__":
    main()

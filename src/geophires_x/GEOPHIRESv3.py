#! python
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  6 10:34:04 2017

@author: kbeckers V1 and V2; Malcolm Ross V3
"""

# GEOPHIRES v3.0
# build date: May 2022
# github address: https://github.com/malcolm-dsider/GEOPHIRES-X

import logging
import logging.config
import os
import sys
import geophires_x.Model as Model
import geophires_x.OptionList as OptionList

def main(enable_geophires_logging_config=True):
    # set the starting directory to be the directory that this file is in
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    if enable_geophires_logging_config:
        # set up logging.
        logging.config.fileConfig('logging.conf')

    logger = logging.getLogger('root')
    logger.info("Init " + str(__name__))

    # initiate the entire model
    model = Model.Model(enable_geophires_logging_config=enable_geophires_logging_config)

    # read the parameters that apply to the model
    model.read_parameters()

    # Calculate the entire model
    model.Calculate()

    # write the outputs, if requested
    model.outputs.PrintOutputs(model)

    # write the outputs as JSON
    import jsons, json
    jsons.suppress_warnings(True)
    JSONresrv = jsons.dumps(model.reserv.OutputParameterDict, indent=4, sort_keys=True, supress_warnings=True)
    JSONwells = jsons.dumps(model.wellbores.OutputParameterDict, indent=4, sort_keys=True, supress_warnings=True)
    JSONsurfaceplant = jsons.dumps(model.surfaceplant.OutputParameterDict, indent=4, sort_keys=True, supress_warnings=True)
    JSONEconomics = jsons.dumps(model.economics.OutputParameterDict, indent=4, sort_keys=True, supress_warnings=True)
    jsonMerged = {**json.loads(JSONresrv), **json.loads(JSONwells), **json.loads(JSONEconomics), **json.loads(JSONsurfaceplant)}
    if model.economics.DoAddOnCalculations.value:
        JSONAddons = jsons.dumps(model.addeconomics.OutputParameterDict, indent=4, sort_keys=True, supress_warnings=True)
        jsonMerged = {**jsonMerged, **json.loads(JSONAddons)}
    if model.economics.DoCCUSCalculations.value:
        JSONCCUS = jsons.dumps(model.ccuseconomics.OutputParameterDict, indent=4, sort_keys=True, supress_warnings=True)
        jsonMerged = {**jsonMerged, **json.loads(JSONCCUS)}
    if model.economics.DoSDACGTCalculations.value:
        JSONSDACGT = jsons.dumps(model.sdacgteconomics.OutputParameterDict, indent=4, sort_keys=True, supress_warnings=True)
        jsonMerged = {**jsonMerged, **json.loads(JSONSDACGT)}

    JSONoutputfile = "HDR.json"
    if len(sys.argv) > 2:
        JSONoutputfile = str(sys.argv[2])
        segs = JSONoutputfile.split('.')
        JSONoutputfile = segs[0] + '.json'
    with open(JSONoutputfile, 'w', encoding='UTF-8') as f:
        f.write(json.dumps(jsonMerged))

    # if the user has asked for it, copy the output file to the screen
    if model.outputs.printoutput:
        outputfile = "HDR.out"
        if len(sys.argv) > 2:
            outputfile = sys.argv[2]
        with open(outputfile, 'r', encoding='UTF-8') as f:
            content = f.readlines()    # store all output in one long list

            # Now write each line to the screen
            for line in content:
                sys.stdout.write(line)

    #make district heating plot
    if model.surfaceplant.enduseoption.value == OptionList.EndUseOptions.DISTRICT_HEATING:
        model.outputs.MakeDistrictHeatingPlot(model)

    logger.info("Complete "+ str(__name__) + ": " + sys._getframe().f_code.co_name)


if __name__ == "__main__":
    main()

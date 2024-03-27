#! python
# -*- coding: utf-8 -*-

import logging
import logging.config
import os
import sys
import geophires_x.Model as Model
import geophires_x.OptionList as OptionList


def main(enable_geophires_logging_config=True):
    """
    This is the main function for the GEOPHIRESv3 model.  It is called when the user runs the model from the command
    line.  It is also called by the GUI when the user clicks the "Run Model" button.
    :param enable_geophires_logging_config: If True, the logging.conf file will be used to configure logging.  If False,
    logging will be configured in the Model class.
    :return: None
    """
    # set the starting directory to be the directory that this file is in
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    if enable_geophires_logging_config:
        # set up logging.
        logging.config.fileConfig('logging.conf')

    logger = logging.getLogger('root')
    logger.info(f'Init {str(__name__)}')

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
    json_resrv = jsons.dumps(model.reserv.OutputParameterDict, indent=4, sort_keys=True, supress_warnings=True)
    json_wells = jsons.dumps(model.wellbores.OutputParameterDict, indent=4, sort_keys=True, supress_warnings=True)
    json_surfaceplant = jsons.dumps(model.surfaceplant.OutputParameterDict, indent=4, sort_keys=True,
                                    supress_warnings=True)
    json_economics = jsons.dumps(model.economics.OutputParameterDict, indent=4, sort_keys=True, supress_warnings=True)
    json_merged = {**json.loads(json_resrv), **json.loads(json_wells), **json.loads(json_economics),
                   **json.loads(json_surfaceplant)}
    if model.economics.DoAddOnCalculations.value:
        json_addons = jsons.dumps(model.addeconomics.OutputParameterDict, indent=4, sort_keys=True,
                                  supress_warnings=True)
        json_merged = {**json_merged, **json.loads(json_addons)}
    if model.economics.DoSDACGTCalculations.value:
        json_sdacgt = jsons.dumps(model.sdacgteconomics.OutputParameterDict, indent=4, sort_keys=True,
                                  supress_warnings=True)
        json_merged = {**json_merged, **json.loads(json_sdacgt)}

    json_outputfile = 'HDR.json'
    if len(sys.argv) > 2:
        json_outputfile = str(sys.argv[2])
        segs = json_outputfile.split('.')
        json_outputfile = segs[0] + '.json'
    with open(json_outputfile, 'w', encoding='UTF-8') as f:
        f.write(json.dumps(json_merged))

    # if the user has asked for it, copy the output file to the screen
    if model.outputs.printoutput:
        outputfile = 'HDR.out'
        if len(sys.argv) > 2:
            outputfile = sys.argv[2]

        with open(outputfile, 'r', encoding='UTF-8') as f:
            sys.stdout.write('\n')
            content = f.readlines()  # store all output in one long list

            # Now write each line to the screen
            for line in content:
                sys.stdout.write(line)

    logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')


if __name__ == '__main__':
    main()

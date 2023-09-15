#! python
# -*- coding: utf-8 -*-
"""
Framework for running Monte Carlo simulations using GEOPHIRES v3.0 & HIP-RA 1.0
build date: September 2023

Created on Wed November  16 10:43:04 2017

@author: Malcolm Ross V3
"""


import os
import sys
import time
import logging
import logging.config
import numpy as np
import argparse
import uuid
import shutil
import subprocess
import multiprocessing


def CheckAndReplaceMean(input_value, args) -> list:
    """
    CheckAndReplaceMean - check to see if the user has requested that a value be replaced by a mean value by specifying
    a value as "#"
    Args:
        input_value: the value to check
        args: the list of arguments passed in from the command line

    Returns: a list of values that have been checked and replaced if necessary
    """
    i = 0
    for inputx in input_value:
        if "#" in inputx:
            # found one we have to process.
            VariName = input_value[0]
            # find it in the Input_file
            with open(args.Input_file) as f:
                ss = f.readlines()
            for s in ss:
                if str(s).startswith(VariName):
                    s2 = s.split(",")
                    input_value[i] = s2[1]
                    break
            break
        i = i + 1
    return input_value

def WorkPackage(Job_ID, Inputs, Outputs, args, Outputfile, working_dir, PythonPath: str):
    tmpoutputfile = tmpfilename = ""
#get random values for each of the INPUTS based on the distributions and boundary values
    rando = 0.0
    s = ""
    for input_value in Inputs:
        if input_value[1].strip().startswith('normal'):
            rando = np.random.normal(float(input_value[2]), float(input_value[3]))
            s = s + input_value[0] + ", " + str(rando) + os.linesep
        elif input_value[1].strip().startswith('uniform'):
            rando = np.random.uniform(float(input_value[2]), float(input_value[3]))
            s = s + input_value[0] + ", " + str(rando) + os.linesep
        elif input_value[1].strip().startswith('triangular'):
            rando = np.random.triangular(float(input_value[2]), float(input_value[3]), float(input_value[4]))
            s = s + input_value[0] + ", " + str(rando) + os.linesep
        if input_value[1].strip().startswith('lognormal'):
            rando = np.random.lognormal(float(input_value[2]), float(input_value[3]))
            s = s + input_value[0] + ", " + str(rando) + os.linesep
        if input_value[1].strip().startswith('binomial'):
            rando = np.random.binomial(float(input_value[2]), float(input_value[3]))
            s = s + input_value[0] + ", " + str(rando) + os.linesep

    # make up a temporary file name that will be shared among files for this iteration
    tmpfilename = working_dir + str(uuid.uuid4()) + ".txt"
    tmpoutputfile = tmpfilename.replace(".txt", "_result.txt")

    # copy the contents of the Input_file into a new input file
    shutil.copyfile(args.Input_file, tmpfilename)

    # append those values to the new input file in the format "variable name, new_random_value".
    # This will cause GeoPHIRES/HIP-RA to replace the value in the file with this random value in the calculation
    with open(tmpfilename, "a") as f:
        f.write(s)

#start GeoPHIRES/HIP-RA with that input file. Capture the output into a filename that is the same as the input file but has the suffix "_result.txt".
    sprocess = subprocess.Popen([PythonPath, args.Code_File, tmpfilename, tmpoutputfile], stdout=subprocess.DEVNULL)
    sprocess.wait()

    # look thru "_result.txt" file for the OUTPUT variables that the user asked for.
    # For each of them, write them as a column in results file
    s1 = ""
    s2 = {}
    result_s = ""
    localOutputs = Outputs

    # make sure a key file exists. If not, exit
    if not os.path.exists(tmpoutputfile):
        print("Timed out waiting for: " + tmpoutputfile)
        logger.warning("Timed out waiting for: " + tmpoutputfile)
        exit(-33)

    with open(tmpoutputfile, "r") as f:
        s1=f.readline()
        i=0
        while s1:
            for out in localOutputs:
                if out in s1:
                    localOutputs.remove(out)
                    s2 = s.split(":")
                    s2 = s2[1].strip()
                    s2 = s2.split(" ")
                    s2 = s2[0]
                    result_s = result_s + s2 + ", "
                    i = i + 1
                    if i < (len(Outputs) - 1):
                        # go back to the beginning of the file in case the outputs that the user specified are not
                        # in the order that they appear in the file.
                        f.seek(0)
                    break
            s1 = f.readline()

    # delete  temporary files
    os.remove(tmpfilename)
    os.remove(tmpoutputfile)

    # write out the results
    result_s = result_s.strip(" ")  # get rid of last space
    result_s = result_s.strip(",")  # et rid of last comma
    result_s = result_s + os.linesep
    with open(Outputfile, "a") as f:
        f.write(result_s)


def main(enable_geophires_logging_config=True):
    # set the starting directory to be the directory that this file is in
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    # set up logging.
    if enable_geophires_logging_config:
        # set up logging.
        logging.config.fileConfig('logging.conf')
    logger = logging.getLogger('root')
    logger.info("Init " + str(__name__))
    # keep track of execution time
    tic = time.time()

    # set the starting directory to be the directory that this file is in
    working_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(working_dir)
    working_dir = working_dir + os.sep

    # from the command line, read what we need to know:
    #    0) Code_File: Python code to run
    #    1) Input_file: The base model for the calculations
    #    2) MC_Settings_file: The settings file for the MC run:
    #         a) the input variables to change (spelling and case are IMPORTANT), their distribition functions
    #         (choices = normal, uniform, triangular, lognormal, binomial - see numpy.random for documenation),
    #         and the inputs for that distribution function (Comma seperated; If the mean is set to "#",
    #         then value from the Input_file as the mode/mean). In the form:
    #                INPUT, Maximum Temperature, normal, mean, std_dev
    #                INPUT, Utilization Factor,uniform, min, max
    #                INPUT, Ambient Temperature,triangular, left, mode, right
    #         b) the output variable(s) to track (spelling and case are IMPORTANT), in the form
    #         [NOTE: THIS LIST SHOULD BE IN THE ORDER THEY APPEAR IN THE OUTPUT FILE]:
    #                OUTPUT, Average Net Electricity Production
    #                OUTPUT, Electricity breakeven price
    #         c) the number of iterations, in the form:
    #                ITERATIONS, 1000
    #         d) the name of the output file (it will contain one column for each of the output variables to track),
    #         in the form:
    #                MC_OUTPUT_FILE, "D:\Work\GEOPHIRES3-master\MC_Result.txt"
    #         d) the path to the python executable, it it is not already linked to "python", in the form:
    #                PYTHON_PATH, /user/local/bin/python3

    # get the values off the command line
    parser = argparse.ArgumentParser()
    parser.add_argument("Code_File", help="Code_File")
    parser.add_argument("Input_file", help="Input file")
    parser.add_argument("MC_Settings_file", help="MC Settings file")
    args = parser.parse_args()

    # Set up a unique Job_ID
    Job_ID = str(uuid.uuid4())

    # make a list of the INPUTS, distribution functions, and the inputs for that distribution function.
    # Make a list of the OUTPUTs
    # Find the iteration value
    # Find the Output_file
    with open(args.MC_Settings_file, encoding='UTF-8') as f:
        flist = f.readlines()

    Inputs = []
    Outputs = []
    Iterations = 0
    Outputfile = ""
    PythonPath = "python"
    for line in flist:
        clean = line.strip()
        pair = clean.split(",")
        pair[1] = pair[1].strip()
        if pair[0].startswith("INPUT"):
            Inputs.append(pair[1:])
        elif pair[0].startswith("OUTPUT"):
            Outputs.append(pair[1])
        elif pair[0].startswith("ITERATIONS"):
            Iterations = int(pair[1])
        elif pair[0].startswith("MC_OUTPUT_FILE"):
            Outputfile = pair[1]
        elif pair[0].startswith("PYTHON_PATH"):
            PythonPath = pair[1]

    # check to see if there is a "#" in an input, if so, use the results file to replace it with the value
    for input_value in Inputs:
        input_value = CheckAndReplaceMean(input_value, args)

    # create the file output_file. Put headers in it for each of the INPUT and OUTPUT variables
    # - these form the column headings when importing into Excel
    # - we include the INPUT and OUTPUT variables in the output file so that we can track the results and tell which
    # combination of variables produced the interesting values (like lowest or highest, or mean)
    # start by creating the string we will write as header
    s = ""
    for input in Inputs:
        s = s + input[0] + ", "
    for output in Outputs:
        s = s + output + ", "
    s = "".join(s.rsplit(" ", 1))  # get rid of last space
    s = "".join(s.rsplit(",", 1))  # get rid of last comma
    s = s + os.linesep
    with open(Outputfile, "w") as f:
        f.write(s)

    # loop through the specified number of iterations
    procs = []
    print("Starting Iteration:", end='')
    for i in range(1, Iterations + 1):
        print(str(i), end=',')
        proc = multiprocessing.Process(target=WorkPackage, args=(Job_ID, Inputs, Outputs, args, Outputfile, working_dir, PythonPath))
        procs.append(proc)
        proc.start()

    # complete the processes
    for proc in procs:
        proc.join()

    print (os.linesep + "Done with calculations! Summarizing..." + os.linesep)
    logger.info("Done with calculations! Summarizing...")

    # read the results into an array
    actual_records_count = Iterations
    with open(Outputfile, "r") as f:
        s = f.readline()  # skip the first line
        all_results = f.readlines()

    result_count = 0
    Results = []
    for line in all_results:
        result_count = result_count + 1
        if "-9999.0" not in line and len(s) > 1:
            line = line.strip()
            if len(line) > 3:
                Results.append([float(y) for y in line.split(",")])
            else:
                logger.warn("space found in line " + str(result_count))
        else:
            logger.warn("-9999.0 or space found in line " + str(result_count))

    actual_records_count = len(Results)

    # Compute the stats along the specified axes.
    mins = np.nanmin(Results, 0)
    maxs = np.nanmax(Results, 0)
    medians = np.nanmedian(Results, 0)
    averages = np.average(Results, 0)
    means = np.nanmean(Results, 0)
    std = np.nanstd(Results, 0)
    var = np.nanvar(Results, 0)

    # write them out
    with open(Outputfile, "a") as f:
        i=0
        if Iterations != actual_records_count:
            f.write(os.linesep + os.linesep + str(actual_records_count) + " iterations finished successfully and were used to calculate the statistics" + os.linesep + os.linesep)
        for output in Outputs:
            f.write (output + ":" + os.linesep)
            f.write (f"     minimum: {mins[i]:,.2f}" + os.linesep)
            f.write (f"     maximum: {maxs[i]:,.2f}" + os.linesep)
            f.write (f"     median: {medians[i]:,.2f}" + os.linesep)
            f.write (f"     average: {averages[i]:,.2f}" + os.linesep)
            f.write (f"     mean: {means[i]:,.2f}" + os.linesep)
            f.write (f"     standard deviation: {std[i]:,.2f}" + os.linesep)
            f.write (f"     variance: {var[i]:,.2f}" + os.linesep)
            i = i + 1

    print (" Calculation Time: "+"{0:10.3f}".format((time.time()-tic)) + " sec" + os.linesep)
    logger.info(" Calculation Time: "+"{0:10.3f}".format((time.time()-tic)) + " sec" + os.linesep)
    print (" Calculation Time per iteration: "+"{0:10.3f}".format(((time.time()-tic))/actual_records_count) +" sec" + os.linesep)
    logger.info(" Calculation Time per iteration: "+"{0:10.3f}".format(((time.time()-tic))/actual_records_count) +" sec" + os.linesep)
    if Iterations != actual_records_count:
        print(os.linesep + os.linesep + "NOTE:" + str(actual_records_count) +
              " iterations finished successfully and were used to calculate the statistics." + os.linesep + os.linesep)
        logger.warning(os.linesep + os.linesep + "NOTE:" + str(actual_records_count) +
              " iterations finished successfully and were used to calculate the statistics." + os.linesep + os.linesep)

    logger.info("Complete " + str(__name__) + ": " + sys._getframe().f_code.co_name)


if __name__ == "__main__":
    # set up logging.
    logger = logging.getLogger('root')
    logger.info("Init " + str(__name__))


    main()

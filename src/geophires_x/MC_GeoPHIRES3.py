#! python
# -*- coding: utf-8 -*-
"""
Framework for running Monte Carlo simulations using GEOPHIRES v3.0 & HIP-RA 1.0
build date: September 2023
Created on Wed November  16 10:43:04 2017
@author: Malcolm Ross V3
@author: softwareengineerprogrammer
"""

import os
import sys
import time
import logging
import logging.config
from pathlib import Path

import numpy as np
import argparse
import uuid
import shutil
import concurrent.futures
import subprocess
import matplotlib.pyplot as plt
import pandas as pd
import tempfile


def CheckAndReplaceMean(input_value, args) -> list:
    """
    CheckAndReplaceMean - check to see if the user has requested that a value be replaced by a mean value by specifying
    a value as "#"
    :param input_value: the value to check
    :type input_value: list
    :param args: the list of arguments passed in from the command line
    :type args: list
    :return: the input_value, with the mean value replaced if necessary
    :rtype: list
    """
    i = 0
    for inputx in input_value:
        if '#' in inputx:
            # found one we have to process.
            VariName = input_value[0]
            # find it in the Input_file
            with open(args.Input_file) as f:
                ss = f.readlines()
            for s in ss:
                if str(s).startswith(VariName):
                    s2 = s.split(',')
                    input_value[i] = s2[1]
                    break
            break
        i = i + 1
    return input_value


def WorkPackage(pass_list):
    """
    WorkPackage - this is the function that is called by the executor. It does the work of running the simulation
    :param pass_list: the list of arguments passed in from the command line
    :type pass_list: list
    :return: None
    """
    Inputs = pass_list[0]
    Outputs = pass_list[1]
    args = pass_list[2]
    Outputfile = pass_list[3]
    working_dir = pass_list[4]
    PythonPath = pass_list[5]

    tmpoutputfile = tmpfilename = ''

    # get random values for each of the INPUTS based on the distributions and boundary values
    rando = 0.0
    s = ''
    print('#', end='')  # TODO Use tdqm library to show progress bar on screen: https://github.com/tqdm/tqdm
    for input_value in Inputs:
        if input_value[1].strip().startswith('normal'):
            rando = np.random.normal(float(input_value[2]), float(input_value[3]))
            s += input_value[0] + ", " + str(rando) + "\n"
        elif input_value[1].strip().startswith('uniform'):
            rando = np.random.uniform(float(input_value[2]), float(input_value[3]))
            s += input_value[0] + ", " + str(rando) + "\n"
        elif input_value[1].strip().startswith('triangular'):
            rando = np.random.triangular(float(input_value[2]), float(input_value[3]), float(input_value[4]))
            s += input_value[0] + ", " + str(rando) + "\n"
        if input_value[1].strip().startswith('lognormal'):
            rando = np.random.lognormal(float(input_value[2]), float(input_value[3]))
            s += input_value[0] + ", " + str(rando) + "\n"
        if input_value[1].strip().startswith('binomial'):
            rando = np.random.binomial(int(input_value[2]), float(input_value[3]))
            s += input_value[0] + ", " + str(rando) + "\n"

    # make up a temporary file name that will be shared among files for this iteration
    tmpfilename = str(Path(tempfile.gettempdir(), f'{str(uuid.uuid4())}.txt'))
    tmpoutputfile = tmpfilename.replace('.txt', '_result.txt')

    # copy the contents of the Input_file into a new input file
    shutil.copyfile(args.Input_file, tmpfilename)

    # append those values to the new input file in the format "variable name, new_random_value".
    # This will cause GeoPHIRES/HIP-RA to replace the value in the file with this random value in the calculation
    # if it exists in that file already, or it will set it to the value as if it was a new value set by the user.
    with open(tmpfilename, 'a') as f:
        f.write(s)

    # start the passed in program name (usually GEOPHIRES or HIP-RA) with the supplied input file.
    # Capture the output into a filename that is the same as the input file but has the suffix "_result.txt".
    sprocess = subprocess.Popen([PythonPath, args.Code_File, tmpfilename, tmpoutputfile], stdout=subprocess.DEVNULL)
    sprocess.wait()

    # look group "_result.txt" file for the OUTPUT variables that the user asked for.
    # For each of them, write them as a column in results file
    s1 = ''
    s2 = {}
    result_s = ''
    localOutputs = Outputs

    # make sure a key file exists. If not, exit
    if not os.path.exists(tmpoutputfile):
        print(f'Timed out waiting for: {tmpoutputfile}')
        # logger.warning(f'Timed out waiting for: {tmpoutputfile}')
        exit(-33)

    with open(tmpoutputfile, 'r') as f:
        s1 = f.readline()
        i = 0
        while s1:  # read until the end of the file
            for out in localOutputs:  # check for each requested output
                if out in s1:  # If true, we found the output value that the user requested, so process it
                    localOutputs.remove(out)  # as an optimization, drop the output from the list once we have found it
                    s2 = s1.split(':')  # colon marks the split between the title and the data
                    s2 = s2[1].strip()  # remove leading and trailing spaces
                    s2 = s2.split(
                        ' ')  # split on space because there is a unit string after the value we are looking for
                    s2 = s2[0].strip()  # we finally have the result we were looking for
                    result_s += s2 + ", "
                    i += 1
                    if i < (len(Outputs) - 1):
                        # go back to the beginning of the file in case the outputs that the user specified are not
                        # in the order that they appear in the file.
                        f.seek(0)
                    break
            s1 = f.readline()

        # append the input values to the output values so the optimal input values are easy to find,
        # the form "inputVar:Rando;nextInputVar:Rando..."
        result_s += '(' + s.replace("\n", ";", -1).replace(", ", ":", -1) + ')'

    # delete temporary files
    os.remove(tmpfilename)
    os.remove(tmpoutputfile)

    # write out the results
    result_s = result_s.strip(' ')  # get rid of last space
    result_s = result_s.strip(',')  # get rid of last comma
    result_s += '\n'

    with open(Outputfile, 'a') as f:
        f.write(result_s)


def main(enable_geophires_logging_config=True):
    """
    main - this is the main function that is called when the program is run
    It gets most of its key values from the command line:
       0) Code_File: Python code to run
       1) Input_file: The base model for the calculations
       2) MC_Settings_file: The settings file for the MC run:
            a) the input variables to change (spelling and case are IMPORTANT), their distribution functions
            (choices = normal, uniform, triangular, lognormal, binomial - see numpy.random for documentation),
            and the inputs for that distribution function (Comma separated; If the mean is set to "#",
            then value from the Input_file as the mode/mean). In the form:
                   INPUT, Maximum Temperature, normal, mean, std_dev
                   INPUT, Utilization Factor,uniform, min, max
                   INPUT, Ambient Temperature,triangular, left, mode, right
            b) the output variable(s) to track (spelling and case are IMPORTANT), in the form
            [NOTE: THIS LIST SHOULD BE IN THE ORDER THEY APPEAR IN THE OUTPUT FILE]:
                   OUTPUT, Average Net Electricity Production
                   OUTPUT, Electricity breakeven price
            c) the number of iterations, in the form:
                   ITERATIONS, 1000
            d) the name of the output file (it will contain one column for each of the output variables to track),
            in the form:
                   MC_OUTPUT_FILE, "D:\Work\GEOPHIRES3-master\MC_Result.txt"
            d) the path to the python executable, it it is not already linked to "python", in the form:
                   PYTHON_PATH, /user/local/bin/python3
    :param enable_geophires_logging_config: if True, use the logging.conf file to configure logging
    :type enable_geophires_logging_config: bool
    :return: None
    """
    # set the starting directory to be the directory that this file is in
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    # set up logging.
    if enable_geophires_logging_config:
        # set up logging.
        logging.config.fileConfig('logging.conf')
    logger = logging.getLogger('root')
    logger.info(f'Init {str(__name__)}')
    # keep track of execution time
    tic = time.time()

    # set the starting directory to be the directory that this file is in
    working_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(working_dir)
    working_dir = working_dir + os.sep

    # get the values off the command line
    parser = argparse.ArgumentParser()
    parser.add_argument('Code_File', help='Code_File')
    parser.add_argument('Input_file', help='Input file')
    parser.add_argument('MC_Settings_file', help='MC Settings file')
    args = parser.parse_args()

    # make a list of the INPUTS, distribution functions, and the inputs for that distribution function.
    # Make a list of the OUTPUTs
    # Find the iteration value
    # Find the Output_file
    with open(args.MC_Settings_file, encoding='UTF-8') as f:
        flist = f.readlines()

    Inputs = []
    Outputs = []
    Iterations = 0
    Outputfile = ''
    PythonPath = 'python'
    for line in flist:
        clean = line.strip()
        pair = clean.split(',')
        pair[1] = pair[1].strip()
        if pair[0].startswith('INPUT'):
            Inputs.append(pair[1:])
        elif pair[0].startswith('OUTPUT'):
            Outputs.append(pair[1])
        elif pair[0].startswith('ITERATIONS'):
            Iterations = int(pair[1])
        elif pair[0].startswith('MC_OUTPUT_FILE'):
            Outputfile = pair[1]
        elif pair[0].startswith('PYTHON_PATH'):
            PythonPath = pair[1]

    # check to see if there is a "#" in an input, if so, use the results file to replace it with the value
    for input_value in Inputs:
        input_value = CheckAndReplaceMean(input_value, args)

    # create the file output_file. Put headers in it for each of the INPUT and OUTPUT variables
    # - these form the column headings when importing into Excel
    # - we include the INPUT and OUTPUT variables in the output file so that we can track the results and tell which
    # combination of variables produced the interesting values (like lowest or highest, or mean)
    # start by creating the string we will write as header
    s = ''
    for output in Outputs:
        s += output + ', '
    for input in Inputs:
        s += input[0] + ', '
    s = ''.join(s.rsplit(' ', 1))  # get rid of last space
    s = ''.join(s.rsplit(',', 1))  # get rid of last comma
    s += '\n'

    # write the header so it is easy to import and analyze in Excel
    with open(Outputfile, 'w') as f:
        f.write(s)

    # build the args list
    pass_list = [Inputs, Outputs, args, Outputfile, working_dir, PythonPath]  # this list never changes

    args = []
    for i in range(0, Iterations):
        args.append(pass_list)  # we need to make Iterations number of copies of this list fr the map
    args = tuple(args)  # convert to a tuple

    # Now run the executor with the map - that will run it Iterations number of times
    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(WorkPackage, args)

    print('\nDone with calculations! Summarizing...\n')
    logger.info('Done with calculations! Summarizing...')

    # read the results into an array
    with open(Outputfile, 'r') as f:
        s = f.readline()  # skip the first line
        all_results = f.readlines()

    result_count = 0
    Results = []
    for line in all_results:
        result_count = result_count + 1
        if '-9999.0' not in line and len(s) > 1:
            line = line.strip()
            if len(line) > 3:
                line, sep, tail = line.partition(', (')  # strip off the Input Variable Values
                Results.append([float(y) for y in line.split(',')])
        else:
            logger.warning(f'-9999.0 or space found in line {str(result_count)}')

    actual_records_count = len(Results)

    # Load the results into a pandas dataframe
    results_pd = pd.read_csv(Outputfile)
    df = pd.DataFrame(results_pd)

    # Compute the stats along the specified axes.
    mins = np.nanmin(Results, 0)
    maxs = np.nanmax(Results, 0)
    medians = np.nanmedian(Results, 0)
    averages = np.average(Results, 0)
    means = np.nanmean(Results, 0)
    std = np.nanstd(Results, 0)

    print(" Calculation Time: " + "{0:10.3f}".format((time.time() - tic)) + " sec\n")
    logger.info(" Calculation Time: " + "{0:10.3f}".format((time.time() - tic)) + " sec\n")
    print(" Calculation Time per iteration: " + "{0:10.3f}".format(
        ((time.time() - tic)) / actual_records_count) + " sec\n")
    logger.info(" Calculation Time per iteration: " + "{0:10.3f}".format(
        ((time.time() - tic)) / actual_records_count) + " sec\n")
    if Iterations != actual_records_count:
        print("\n\nNOTE:" + str(
            actual_records_count) + " iterations finished successfully and were used to calculate the statistics.\n\n")
        logger.warning("\n\nNOTE:" + str(
            actual_records_count) + " iterations finished successfully and were used to calculate the statistics.\n\n")

    # write them out
    annotations = ""
    with open(Outputfile, "a") as f:
        i = 0
        if Iterations != actual_records_count:
            f.write(f'\n\n{str(actual_records_count)} iterations finished successfully and were used to calculate the '
                    f'statistics\n\n')
        for output in Outputs:
            f.write(f'{output}:\n')
            f.write(f'     minimum: {mins[i]:,.2f}\n')
            annotations += f'     minimum: {mins[i]:,.2f}\n'
            f.write(f'     maximum: {maxs[i]:,.2f}\n')
            annotations += f'     maximum: {maxs[i]:,.2f}\n'
            f.write(f'     median: {medians[i]:,.2f}\n')
            annotations += f"     median: {medians[i]:,.2f}\n"
            f.write(f'     average: {averages[i]:,.2f}\n')
            annotations += f'     average: {averages[i]:,.2f}\n'
            f.write(f'     mean: {means[i]:,.2f}\n')
            annotations += f'     mean: {means[i]:,.2f}\n'
            f.write(f'     standard deviation: {std[i]:,.2f}\n')
            annotations += f'     standard deviation: {std[i]:,.2f}\n'

            plt.figure(figsize=(8, 6))
            ax = plt.subplot()
            ax.set_title(output)
            ax.set_xlabel('Output units')
            ax.set_ylabel('Probability')

            plt.figtext(0.11, 0.74, annotations, fontsize=8)
            ret = plt.hist(df[df.columns[i]].tolist(), bins=50, density=True)
            f.write('bin values (as percentage): ' + str(ret[0]) + '\n')
            f.write('bin edges: ' + str(ret[1]) + '\n')
            fname = df.columns[i].strip().replace('/', '-')
            plt.savefig(Path(Path(Outputfile).parent, f'{fname}.png'))
            i += 1
            annotations = ''

    logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')


if __name__ == '__main__':
    # set up logging.
    logger = logging.getLogger('root')
    logger.info(f'Init {str(__name__)}')

    main()

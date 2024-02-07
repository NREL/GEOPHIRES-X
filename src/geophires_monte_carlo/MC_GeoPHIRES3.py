#! python
"""
Framework for running Monte Carlo simulations using GEOPHIRES v3.0 & HIP-RA 1.0
build date: September 2023
Created on Wed November  16 10:43:04 2017
@author: Malcolm Ross V3
@author: softwareengineerprogrammer
"""

import argparse
import concurrent.futures
import logging
import logging.config
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def check_and_replace_mean(input_value, args) -> list:
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
    for input_x in input_value:
        if '#' in input_x:
            # found one we have to process.
            vari_name = input_value[0]
            # find it in the Input_file
            with open(args.Input_file) as f:
                ss = f.readlines()
            for s in ss:
                if str(s).startswith(vari_name):
                    s2 = s.split(',')
                    input_value[i] = s2[1]
                    break
            break
        i += 1

    return input_value


def work_package(pass_list: list):
    """
    Function that is called by the executor. It does the work of running the simulation.
    :param pass_list: the list of arguments passed in from the command line
    """

    print('#', end='')  # TODO Use tdqm library to show progress bar on screen: https://github.com/tqdm/tqdm

    inputs = pass_list[0]
    outputs = pass_list[1]
    args = pass_list[2]
    outputfile = pass_list[3]
    working_dir = pass_list[4]  # noqa: F841
    python_path = pass_list[5]

    input_file_entries = ''

    for input_value in inputs:
        # get random values for each of the INPUTS based on the distributions and boundary values
        if input_value[1].strip().startswith('normal'):
            rando = np.random.normal(float(input_value[2]), float(input_value[3]))
            input_file_entries += input_value[0] + ', ' + str(rando) + '\n'
        elif input_value[1].strip().startswith('uniform'):
            rando = np.random.uniform(float(input_value[2]), float(input_value[3]))
            input_file_entries += input_value[0] + ', ' + str(rando) + '\n'
        elif input_value[1].strip().startswith('triangular'):
            rando = np.random.triangular(float(input_value[2]), float(input_value[3]), float(input_value[4]))
            input_file_entries += input_value[0] + ', ' + str(rando) + '\n'
        if input_value[1].strip().startswith('lognormal'):
            rando = np.random.lognormal(float(input_value[2]), float(input_value[3]))
            input_file_entries += input_value[0] + ', ' + str(rando) + '\n'
        if input_value[1].strip().startswith('binomial'):
            rando = np.random.binomial(int(input_value[2]), float(input_value[3]))
            input_file_entries += input_value[0] + ', ' + str(rando) + '\n'

    # make up a temporary file name that will be shared among files for this iteration
    tmp_filename = str(Path(tempfile.gettempdir(), f'{uuid.uuid4()!s}.txt'))
    tmp_output_file = tmp_filename.replace('.txt', '_result.txt')

    # copy the contents of the Input_file into a new input file
    shutil.copyfile(args.Input_file, tmp_filename)

    # append those values to the new input file in the format "variable name, new_random_value".
    # This will cause GeoPHIRES/HIP-RA to replace the value in the file with this random value in the calculation
    # if it exists in that file already, or it will set it to the value as if it was a new value set by the user.
    with open(tmp_filename, 'a') as f:
        f.write(input_file_entries)

    # start the passed in program name (usually GEOPHIRES or HIP-RA) with the supplied input file.
    # Capture the output into a filename that is the same as the input file but has the suffix "_result.txt".
    # ruff: noqa: S603 # FIXME re-enable QA and address
    sprocess = subprocess.Popen([python_path, args.Code_File, tmp_filename, tmp_output_file], stdout=subprocess.DEVNULL)
    sprocess.wait()

    # look group "_result.txt" file for the OUTPUT variables that the user asked for.
    # For each of them, write them as a column in results file
    s1 = ''
    s2 = {}
    result_s = ''
    local_outputs = outputs

    # make sure a key file exists. If not, exit
    if not Path(tmp_output_file).exists():
        print(f'Timed out waiting for: {tmp_output_file}')
        # logger.warning(f'Timed out waiting for: {tmp_output_file}')
        exit(-33)

    with open(tmp_output_file) as f:
        s1 = f.readline()
        i = 0
        while s1:  # read until the end of the file
            for out in local_outputs:  # check for each requested output
                if out in s1:  # If true, we found the output value that the user requested, so process it
                    local_outputs.remove(out)  # as an optimization, drop the output from the list once we have found it
                    s2 = s1.split(':')  # colon marks the split between the title and the data
                    s2 = s2[1].strip()  # remove leading and trailing spaces
                    s2 = s2.split(
                        ' '
                    )  # split on space because there is a unit string after the value we are looking for
                    s2 = s2[0].strip()  # we finally have the result we were looking for
                    result_s += s2 + ', '
                    i += 1
                    if i < (len(outputs) - 1):
                        # go back to the beginning of the file in case the outputs that the user specified are not
                        # in the order that they appear in the file.
                        f.seek(0)
                    break

            s1 = f.readline()

        # append the input values to the output values so the optimal input values are easy to find,
        # the form "inputVar:Rando;nextInputVar:Rando..."
        result_s += '(' + input_file_entries.replace('\n', ';', -1).replace(', ', ':', -1) + ')'

    # delete temporary files
    Path.unlink(tmp_filename)
    Path.unlink(tmp_output_file)

    # write out the results
    result_s = result_s.strip(' ').strip(',')  # get rid of last space and comma
    result_s += '\n'

    with open(outputfile, 'a') as f:
        f.write(result_s)


def main(enable_geophires_monte_carlo_logging_config=True):
    r"""
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
    :param enable_geophires_monte_carlo_logging_config: if True, use the logging.conf file to configure logging
    :type enable_geophires_monte_carlo_logging_config: bool
    """

    # set the starting directory to be the directory that this file is in
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    if enable_geophires_monte_carlo_logging_config:
        # set up logging.
        logging.config.fileConfig('logging.conf')

    logger = logging.getLogger('root')
    logger.info(f'Init {__name__!s}')
    # keep track of execution time
    tic = time.time()

    # set the starting directory to be the directory that this file is in
    working_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(working_dir)
    working_dir = working_dir + os.sep

    # get the values off the command line
    parser = argparse.ArgumentParser()
    parser.add_argument('Code_File', help='Code File')
    parser.add_argument('Input_file', help='Input file')
    parser.add_argument('MC_Settings_file', help='MC Settings file')
    parser.add_argument('MC_OUTPUT_FILE', help='Output file', nargs='?')
    args = parser.parse_args()

    # make a list of the INPUTS, distribution functions, and the inputs for that distribution function.
    # Make a list of the OUTPUTs
    # Find the iteration value
    # Find the Output_file
    with open(args.MC_Settings_file, encoding='UTF-8') as f:
        flist = f.readlines()

    inputs = []
    outputs = []
    iterations = 0
    output_file = args.MC_OUTPUT_FILE if 'MC_OUTPUT_FILE' in args and args.MC_OUTPUT_FILE is not None else ''
    python_path = 'python'
    for line in flist:
        clean = line.strip()
        pair = clean.split(',')
        pair[1] = pair[1].strip()
        if pair[0].startswith('INPUT'):
            inputs.append(pair[1:])
        elif pair[0].startswith('OUTPUT'):
            outputs.append(pair[1])
        elif pair[0].startswith('ITERATIONS'):
            iterations = int(pair[1])
        elif pair[0].startswith('MC_OUTPUT_FILE'):
            output_file = pair[1]
        elif pair[0].startswith('PYTHON_PATH'):
            python_path = pair[1]

    # check to see if there is a "#" in an input, if so, use the results file to replace it with the value
    for input_value in inputs:
        # FIXME assign via index instead of reference
        input_value = check_and_replace_mean(input_value, args)

    # create the file output_file. Put headers in it for each of the INPUT and OUTPUT variables
    # - these form the column headings when importing into Excel
    # - we include the INPUT and OUTPUT variables in the output file so that we can track the results and tell which
    # combination of variables produced the interesting values (like lowest or highest, or mean)
    # start by creating the string we will write as header
    s = ''

    for output in outputs:
        s += output + ', '

    for input in inputs:
        s += input[0] + ', '

    s = ''.join(s.rsplit(' ', 1))  # get rid of last space
    s = ''.join(s.rsplit(',', 1))  # get rid of last comma
    s += '\n'

    # write the header so it is easy to import and analyze in Excel
    with open(output_file, 'w') as f:
        f.write(s)

    # build the args list
    pass_list = [inputs, outputs, args, output_file, working_dir, python_path]  # this list never changes

    args = []
    for _ in range(iterations):
        args.append(pass_list)  # we need to make Iterations number of copies of this list fr the map
    args = tuple(args)  # convert to a tuple

    # Now run the executor with the map - that will run it Iterations number of times
    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(work_package, args)

    print('\nDone with calculations! Summarizing...\n')
    logger.info('Done with calculations! Summarizing...')

    # read the results into an array
    with open(output_file) as f:
        s = f.readline()  # skip the first line
        all_results = f.readlines()

    result_count = 0
    results = []
    for line in all_results:
        result_count = result_count + 1
        if '-9999.0' not in line and len(s) > 1:
            line = line.strip()
            if len(line) > 3:
                line, sep, tail = line.partition(', (')  # strip off the Input Variable Values
                results.append([float(y) for y in line.split(',')])
        else:
            logger.warning(f'-9999.0 or space found in line {result_count!s}')

    actual_records_count = len(results)

    # Load the results into a pandas dataframe
    results_pd = pd.read_csv(output_file)
    df = pd.DataFrame(results_pd)

    # Compute the stats along the specified axes.
    mins = np.nanmin(results, 0)
    maxs = np.nanmax(results, 0)
    medians = np.nanmedian(results, 0)
    averages = np.average(results, 0)
    means = np.nanmean(results, 0)
    std = np.nanstd(results, 0)

    print(f' Calculation Time: {time.time() - tic:10.3f} sec\n')
    logger.info(f' Calculation Time: {time.time() - tic:10.3f} sec\n')
    print(f' Calculation Time per iteration: {(time.time() - tic) / actual_records_count:10.3f} sec\n')
    logger.info(f' Calculation Time per iteration: {(time.time() - tic) / actual_records_count:10.3f} sec\n')
    if iterations != actual_records_count:
        print(
            '\n\nNOTE:'
            + str(actual_records_count)
            + ' iterations finished successfully and were used to calculate the statistics.\n\n'
        )
        logger.warning(
            '\n\nNOTE:'
            + str(actual_records_count)
            + ' iterations finished successfully and were used to calculate the statistics.\n\n'
        )

    # write them out
    annotations = ''
    with open(output_file, 'a') as f:
        i = 0
        if iterations != actual_records_count:
            f.write(
                f'\n\n{actual_records_count!s} iterations finished successfully and were used to calculate the '
                f'statistics\n\n'
            )
        for output in outputs:
            f.write(f'{output}:\n')
            f.write(f'     minimum: {mins[i]:,.2f}\n')
            annotations += f'     minimum: {mins[i]:,.2f}\n'
            f.write(f'     maximum: {maxs[i]:,.2f}\n')
            annotations += f'     maximum: {maxs[i]:,.2f}\n'
            f.write(f'     median: {medians[i]:,.2f}\n')
            annotations += f'     median: {medians[i]:,.2f}\n'
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
            plt.savefig(Path(Path(output_file).parent, f'{fname}.png'))
            i += 1
            annotations = ''

    logger.info(f'Complete {__name__!s}: {sys._getframe().f_code.co_name}')


if __name__ == '__main__':
    # set up logging.
    logger = logging.getLogger('root')
    logger.info(f'Init {__name__!s}')

    main()

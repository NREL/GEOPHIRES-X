#! python
# -*- coding: utf-8 -*-
"""
Created on Wed November  16 10:43:04 2017

@author: Malcolm Ross V3
"""

# Framework for running Monte Carlo simulations uding GEOPHIRES v3.0 & HIP-RA 1.0
# build date: November 2022
# github address: https://github.com/malcolm-dsider/GEOPHIRES-X

import os
import sys
import logging
import logging.config
import argparse
import uuid
import shutil
import subprocess
import multiprocessing


def convert_string_to_number(test_string):
    # Initialize a translation table to remove non-numeric characters
    translation_table = str.maketrans('', '',
                                      'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-/:;<=>?@[\\]^_`{|}~')
    translation_table[176] = None  # add and entry for the degree symbol
    # Use str.translate() with the translation table to remove non-numeric characters
    numeric_string = test_string.translate(translation_table)
    return (float(numeric_string))

def main():
    # set up logging.
    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger('root')
    logger.info("Init " + str(__name__))

    # set the starting directory to be the directory that this file is in
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # from the command line, read what we need to know:
    #    0) Code_File: Python code to run (this file)
    #    1) Input_file: The input parameter file that controls the executon of this program
    #    2) Input_file contains the following lines (the group of following lines can be repeasted as many times as you want for different input parameter files):
    #       GEOPHIRES-X_Validation_Tool output file, with the results of the analysis, e.g., "D:\Work\GEOPHIRES3-master\Results\GEOPHIRES-X_Output_Validation_Tool_output.txt"
    #       GEOPHIRES-X input control file, with the parameters the user wishes to change, e.g., D:\Work\GEOPHIRES3-master\Examples\example1.txt
    #       GEOPHIRES-X output result file, with results from running the above input control file, e.g., D:\Work\GEOPHIRES3-master\Example1V3_output.txt
    #       Precomputed results file that we will be comparing against, e.g., D:\Work\GEOPHIRES3-master\Results\Example1V3.txt
    #       List of output files that you want used to compare and validate. List can be as long as you want, terminated with a blank line.
    #            This string in the search string that must appear in BOTH OUTPUT FILES IN EXACTLY THE SAME FORMAT, case, spelling, etc. or you must specify the equivilent string in the precomputed file
    #                  adding a "|" and then the equivilent string in the precomputed file. The tool will look for this string(s) in both files, then extract the associated value (after the colon or =) and compare.
    #                  If it is the same, do nothing. If it is not, report it.
    #            For values in a table, the search string is the name of the table, followed by a comma, then the number of lines to skip to get to the value you want to validate, then a comma,
    #                 then the column number that contains the value you want to compare.
    #       e.g.,
    #       Average Net Electricity Production
    #       Electricity breakeven price|LCOE
    #       Average Production Temperature
    #       Average Production Well Pump Pressure Drop
    #       Total capital costs|Total Capital Costs
    #       Total operating and maintenance costs
    #       Average Total Electricity Generation
    #       POWER GENERATION PROFILE, 34, 6
    #       HEAT AND/OR ELECTRICITY EXTRACTION AND GENERATION PROFILE, 34, 5
    #
    # NOTE: new option: if you append % and a number to the search string, the comparison will be made based on "percent difference" rather than absolute, and the percent difference will be the number after the %, so
    #     Average Net Electricity Production%10
    #         Will do the percent difference calculation and flag it as different if the difference is >10%

    # get the values off the command line
    parser = argparse.ArgumentParser()
    parser.add_argument("Input_file", help="Input_file")
    args = parser.parse_args()

    # Open the input_file and read the first few lines
    with open(args.Input_file, mode="r", encoding='UTF-8') as f1:
        python_code_to_run = f1.readline().strip()
        output_file = f1.readline().strip()
        # open the output file into which we will write results
        with open(output_file, mode="w", encoding='UTF-8') as f2:

            # This is where we start the loop of however many GEOPHIRES-X runs
            while True:
                input_control_file = f1.readline().strip()
                if not input_control_file: break  # we have reached the end of the job
                output_result_file = f1.readline().strip()
                if not output_result_file: break  # we have reached the end of the job

                # run GEOPHIRES-X so we can get an output file to validate
                sprocess = subprocess.Popen(["python", python_code_to_run, input_control_file,
                                             output_result_file])  # allow stdout to be printed to screen:  , stdout=subprocess.DEVNULL)
                sprocess.wait()

                # we should now have a result in output_result_file so we can open it and the Precomputed_results_file
                Precomputed_results_file = f1.readline().strip()
                f2.write("\nComparing: " + output_result_file + " to " + Precomputed_results_file + "\n")

                # now read all the search strings into a list. Terminate when ths string length is 0
                search_strings = []
                while True:
                    line = f1.readline().strip()
                    if len(line) == 0: break
                    search_strings.append(line)

                # Read the all the lines in the output and precomputed files into lists
                with open(output_result_file, mode="r", encoding='UTF-8') as f3:
                    output_lines = f3.readlines()
                with open(Precomputed_results_file, mode="r") as f4:
                    precomputed_lines = f4.readlines()

                # now we have everything we need in lists, for each search string, search the outputs and precomputed results
                for search_string in search_strings:
                    pair = search_string.split(",")  # If pair has a ",", it must be a table search
                    pair3 = search_string.split(
                        "|")  # If pair has a "|", it must have 2 different spellings for search string
                    if len(pair3) > 1:
                        search_string = pair3[0]
                        pc_search_string = pair3[1]
                    else:
                        pc_search_string = search_string

                    percent_difference_calc = False

                    # If len(pair) is 1, we have a simple entry
                    if len(pair) == 1:
                        if "%" in search_string:  # must be doing a percent difference calculation
                            percent_difference_calc = True
                            p = search_string.strip().split("%")
                            search_string = p[0]
                            percent_difference = float(str(p[1]).strip())

                        # loop thru the output_result_file, looking for the search string
                        for output_line in output_lines:
                            result_value = precompute_value = None
                            if search_string in output_line:
                                pair = output_line.split(":")
                                if len(pair) == 1: pair = output_line.split(
                                    "=")  # If there isn't a ":" in search string, then we have an old-style outfile file, which uses "="
                                result_value = convert_string_to_number(pair[1])
                                # pair[1].strip()
                                # result_value = result_value.split(" ") #split on " " in case there are units
                                # result_value = float(result_value[0])
                                break
                        for precomputed_line in precomputed_lines:
                            if pc_search_string in precomputed_line:
                                pair = precomputed_line.split(":")
                                if len(pair) == 1: pair = precomputed_line.split(
                                    "=")  # If there isn't a ":" in search string, then we have an old-style outfile file, which uses "="
                                precomputed_value = convert_string_to_number(pair[1])
                                # pair[1].strip()
                                # precomputed_value = precomputed_value.split(" ")
                                # precomputed_value = float(precomputed_value[0])
                                break

                        # if either is None, we didn't find a pair to compare
                        if result_value is not None and precomputed_value is not None:
                            # if we come here, then we have found values we need to compare
                            if not percent_difference_calc:
                                if result_value != precomputed_value:
                                    f2.write("for " + search_string + ", values DO NOT MATCH! result value = " + str(
                                        result_value) + "; precomputed value = " + str(precomputed_value) + "\n")
                                else:
                                    pass  # don't report anything if they match
                            else:
                                pd = 100.0 * (result_value - precomputed_value) / (
                                        (result_value + precomputed_value) / 2.0)
                                if pd > percent_difference:
                                    f2.write("for " + search_string + ", values EXCEED A PERCENT DIFFERENCE OF " + str(
                                        percent_difference) + "%! result value = " + str(
                                        result_value) + "; precomputed value = " + str(precomputed_value) + "\n")
                                else:
                                    pass  # don't report anything if they match
                        else:
                            if result_value is None: f2.write(
                                search_string + " not found in: " + output_result_file + "\n")
                            if precompute_value is None: f2.write(
                                pc_search_string + " not found in: " + Precomputed_results_file + "\n")

                    # if len(pair) is 3, then we have a entry that wants to compare values from a table
                    elif len(pair) == 3:
                        pc_search_string = search_string = pair[0]
                        pair3 = search_string.split(
                            "|")  # If pair has a "|", it must have 2 different spellings for search string
                        if len(pair3) > 1:
                            search_string = pair3[0]
                            pc_search_string = pair3[1]
                        rows_to_skip = int(pair[1].strip())
                        column_to_access = int(pair[2].strip()) - 1
                        if "%" in search_string:  # must be doing a percent difference calculation
                            percent_difference_calc = True
                            p = search_string.strip().split("%")
                            search_string = p[0]
                            percent_difference = float(str(p[1]).strip())

                        # loop thru the output_result_file, looking for the search string
                        row = -1
                        for output_line in output_lines:
                            result_value = precompute_value = None
                            row = row + 1
                            if search_string in output_line:
                                row_str = output_lines[row + rows_to_skip]  # skip to the correct row
                                row_str = row_str.replace("  ", " ")
                                row_str = row_str.replace("  ", " ")
                                row_str = row_str.replace("  ", " ")
                                row_str = row_str.replace("  ", " ")
                                row_str = row_str.replace("  ", " ")
                                columns = row_str.strip().split(" ")
                                result_value = columns[column_to_access].strip()
                                result_value = result_value.split(" ")  # split on " " in case there are units
                                result_value = float(result_value[0])
                                break
                        row = -1
                        for precomputed_line in precomputed_lines:
                            row = row + 1
                            if pc_search_string in precomputed_line:
                                row_str = precomputed_lines[row + rows_to_skip]  # skip to the correct row
                                row_str = row_str.replace("  ", " ")
                                row_str = row_str.replace("  ", " ")
                                row_str = row_str.replace("  ", " ")
                                row_str = row_str.replace("  ", " ")
                                row_str = row_str.replace("  ", " ")
                                columns = row_str.strip().split(" ")
                                precomputed_value = columns[column_to_access].strip()
                                precomputed_value = precomputed_value.split(" ")  # split on " " in case there are units
                                precomputed_value = float(precomputed_value[0])
                                break

                        # if either is None, we didn't find a pair to compare
                        if result_value is not None and precomputed_value is not None:
                            # if we come here, then we have found values we need to compare
                            if not percent_difference_calc:
                                if result_value != precomputed_value:
                                    f2.write("for " + search_string + ", values DO NOT MATCH! result value = " + str(
                                        result_value) + "; precomputed value = " + str(precomputed_value) + "\n")
                                else:
                                    pass  # don't report anything if they match
                            else:
                                pd = 100.0 * (result_value - precomputed_value) / (
                                        (result_value + precomputed_value) / 2.0)
                                if pd > percent_difference:
                                    f2.write("for " + search_string + ", values EXCEED A PERCENT DIFFERENCE OF " + str(
                                        percent_difference) + "%! result value = " + str(
                                        result_value) + "; precomputed value = " + str(precomputed_value) + "\n")
                                else:
                                    pass  # don't report anything if they match
                        else:
                            if result_value is None: f2.write(
                                search_string + " not found in: " + output_result_file + "\n")
                            if precompute_value is None: f2.write(
                                pc_search_string + " not found in: " + Precomputed_results_file + "\n")

    # write the result to the screen
    with open(output_file, 'r', encoding='UTF-8') as f:
        content = f.readlines()  # store all output in one long list
    # Now write each line to the screen
    for line in content: sys.stdout.write(line)

    logger.info("Complete " + str(__name__) + ": " + sys._getframe().f_code.co_name)


if __name__ == "__main__":
    # set up logging.
    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger('root')
    logger.info("Init " + str(__name__))

    main()

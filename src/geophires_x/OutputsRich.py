import dataclasses
import string
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import rich
from matplotlib import pyplot as plt
from rich.console import Console
from rich.table import Table

from geophires_x.GeoPHIRESUtils import UpgradeSymbologyOfUnits, render_default, InsertImagesIntoHTML
from geophires_x.OptionList import EndUseOptions, PlantType
from geophires_x.Parameter import intParameter

NL = '\n'
validFilenameChars = "-_.() %s%s" % (string.ascii_letters, string.digits)


@dataclasses.dataclass
class OutputTableItem:
    parameter: str = ''
    value: str = ''
    units: str = ''

    def __init__(self, parameter: str, value: str = '', units: str = ''):
        self.parameter = parameter
        self.value = value
        self.units = units
        if self.units:
            self.units = UpgradeSymbologyOfUnits(self.units)


def removeDisallowedFilenameChars(filename):
    """
     This function removes disallowed filename characters
     :param filename: the filename
     :type filename: str
     :return: the cleaned filename
     :rtype: str
     """
    cleanedFilename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore')
    return ''.join(chr(c) for c in cleanedFilename if chr(c) in validFilenameChars)


def ShortenArrayToAnnual(array_to_shorten: pd.array, new_length:int, time_steps_per_year: int) -> pd.array:
    """
    This function shortens the array to the number of years in the model
    :param array_to_shorten: the array to shorten
    :type array_to_shorten: pd.array
    :param new_length: the new length
    :type new_length: int
    :param time_steps_per_year: the number of time steps per year
    :type time_steps_per_year: int
    :return: the new array
    :rtype: pd.array
    """
    if len(array_to_shorten) == new_length:
        return array_to_shorten

    new_array = np.zeros(new_length)

    j = 0
    for i in range(0, len(array_to_shorten), time_steps_per_year):
        new_array[j] = array_to_shorten[i]
        j = j + 1

    return new_array


def Write_Simple_Text_Table(title: str, items: list, f) -> None:
    """
    This function writes out the simple tables as text
    :param title: the title of the table
    :type title: str
    :param items: the list of items to be written out
    :type items: list
    :param f: the file object
    :type f: file
    """
    f.write(f'{NL}')
    f.write(f'                           ***{title}***{NL}')
    f.write(f'{NL}')
    for item in items:
        f.write(f'      {item.parameter:<45}: {item.value:^10} {item.units}{NL}')


def Write_Complex_Text_table(title: str, df_table: pd.DataFrame, time_steps_per_year: int, f) -> None:
    """
    This function writes out the complex tables as text
    :param title: the title of the table
    :type title: str
    :param df_table: the dataframe to be written out
    :type df_table: pd.DataFrame
    :param time_steps_per_year: the number of time steps per year
    :type time_steps_per_year: int
    :param f: the file object
    :type f: file
    """
    f.write(f'{NL}')
    f.write(f'                            ***************************************************************{NL}')
    f.write(f'                            *{title:^58}*{NL}')
    f.write(f'                            ***************************************************************{NL}')
    column_fmt = []
    for col in df_table.columns:
        if col != 'index':
            pair = col.split('|')
            column_name = pair[0]
            column_fmt.append(pair[1])
            f.write(f'  {UpgradeSymbologyOfUnits(column_name):^29}   ')

    f.write(f'{NL}')
    for index, row in df_table.iterrows():
        # only print the number of rows implied by time_steps_per_year
        if int(index) % time_steps_per_year == 0:
            for i in range(1, len(row)):
                f.write(f'{render_default((df_table.at[index, row.index[i]]) / time_steps_per_year, "", column_fmt[i - 1]):^33} ')
            f.write(f'{NL}')


def Write_Text_Output(output_path: str, simulation_metadata: list, summary: list, economic_parameters: list,
                      engineering_parameters: list, resource_characteristics: list, reservoir_parameters: list,
                      reservoir_stimulation_results: list, CAPEX: list, OPEX: list, surface_equipment_results: list,
                      sdac_results: list, addon_results: list, hce: pd.DataFrame, ahce: pd.DataFrame,
                      cashflow: pd.DataFrame, sdac_df: pd.DataFrame, addon_df: pd.DataFrame) -> None:
    """
    This function writes out the text output
    :param output_path: the path to the output file
    :type output_path: str
    :param simulation_metadata: the simulation metadata
    :type simulation_metadata: list
    :param summary: the summary of results
    :type summary: list
    :param economic_parameters: the economic parameters
    :type economic_parameters: list
    :param engineering_parameters: the engineering parameters
    :type engineering_parameters: list
    :param resource_characteristics: the resource characteristics
    :type resource_characteristics: list
    :param reservoir_parameters: the reservoir parameters
    :type reservoir_parameters: list
    :param reservoir_stimulation_results: the reservoir stimulation results
    :type reservoir_stimulation_results: list
    :param CAPEX: the capital costs
    :type CAPEX: list
    :param OPEX: the operating and maintenance costs
    :type OPEX: list
    :param surface_equipment_results: the surface equipment simulation results
    :type surface_equipment_results: list
    :param sdac_results: the sdac results
    :type sdac_results: list
    :param hce: the heating, cooling and/or electricity production profile
    :type hce: pd.DataFrame
    :param cashflow: the revenue & cashflow profile
    :type cashflow: pd.DataFrame
    :param sdac_df: the sdac dataframe
    :type sdac_df: pd.DataFrame
    :return: None
    """
    with open(output_path, 'w', encoding='UTF-8') as f:
        f.write(f'                               *****************{NL}')
        f.write(f'                               ***CASE REPORT***{NL}')
        f.write(f'                               *****************{NL}')
        f.write(f'{NL}')

        # write out the simulation metadata
        f.write(f'Simulation Metadata{NL}')
        f.write(f'----------------------{NL}')
        for item in simulation_metadata:
            f.write(f'{item.parameter}: {item.value} {item.units}{NL}')

        # write the simple text tables
        Write_Simple_Text_Table('SUMMARY OF RESULTS', summary, f)
        Write_Simple_Text_Table('ECONOMIC PARAMETERS', economic_parameters, f)
        Write_Simple_Text_Table('ENGINEERING PARAMETERS', engineering_parameters, f)
        Write_Simple_Text_Table('RESOURCE CHARACTERISTICS', resource_characteristics, f)
        Write_Simple_Text_Table('RESERVOIR PARAMETERS', reservoir_parameters, f)
        Write_Simple_Text_Table('RESERVOIR STIMULATION RESULTS', reservoir_stimulation_results, f)
        Write_Simple_Text_Table('CAPITAL COSTS', CAPEX, f)
        Write_Simple_Text_Table('OPERATING AND MAINTENANCE COSTS', OPEX, f)
        Write_Simple_Text_Table('SURFACE EQUIPMENT SIMULATION RESULTS', surface_equipment_results, f)
        if len(addon_results) > 0:
            Write_Simple_Text_Table('ADD-ON ECONOMICS', addon_results, f)
        if len(sdac_results) > 0:
            Write_Simple_Text_Table('S_DAC_GT ECONOMICS', sdac_results, f)

        # write the complex text tables
        Write_Complex_Text_table('HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE', hce, 1, f)
        Write_Complex_Text_table('ANNUAL HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE', ahce, 1, f)
        Write_Complex_Text_table('REVENUE & CASHFLOW PROFILE', cashflow, 1, f)
        if len(addon_df) > 0:
            Write_Complex_Text_table('ADD-ON PROFILE', addon_df, 1, f)
        if len(sdac_df) > 0:
            Write_Complex_Text_table('S_DAC_GT PROFILE', sdac_df, 1, f)


def Write_Simple_HTML_Table(title: str, items: list, console: rich.console) -> None:
    """
    This function writes out the simple tables as HTML. The console object is used to write out the HTML.
    :param title: the title of the table
    :type title: str
    :param items: the list of items to be written out
    :type items: list
    :param console: the console object
    :type console: rich.Console
    """
    table = Table(title=title)
    table.add_column('Parameter', style='bold', no_wrap=True, justify='center')
    table.add_column('Value', style='bold', no_wrap=True, justify='center')
    table.add_column('Units', style='bold', no_wrap=True, justify='center')
    for item in items:
        table.add_row(str(item.parameter), str(item.value), str(item.units))
    console.print(table)


def Write_Complex_HTML_Table(title: str, df_table: pd.DataFrame, time_steps_per_year: int, console: rich.console)-> None:
    """
    This function writes out the complex tables
    :param title: the title of the table
    :type title: str
    :param df_table: the dataframe to be written out
    :type df_table: pd.DataFrame
    :param time_steps_per_year: the number of time steps per year
    :type time_steps_per_year: int
    :param console: the console object
    :type console: rich.Console
    """
    table = Table(title=title)
    column_fmt = []
    for col in df_table.columns:
        if col != 'index':
            pair = col.split('|')
            column_name=pair[0]
            column_fmt.append(pair[1])
            table.add_column(UpgradeSymbologyOfUnits(column_name), style='bold', no_wrap=True, justify='center')
    for index, row in df_table.iterrows():
        # only print the number of rows implied by time_steps_per_year
        if time_steps_per_year == 0 or int(index) % time_steps_per_year == 0:
            table.add_row(*[render_default((df_table.at[index, row.index[i]]) / time_steps_per_year, '', column_fmt[i - 1]) for i in range(1, len(row))])
    console.print(table)


def Write_HTML_Output(html_path: str, simulation_metadata: list, summary: list, economic_parameters: list,
                      engineering_parameters: list, resource_characteristics: list, reservoir_parameters: list,
                      reservoir_stimulation_results: list, CAPEX: list, OPEX: list, surface_equipment_results: list,
                      sdac_results: list, addon_results: list, hce: pd.DataFrame, ahce: pd.DataFrame,
                      cashflow: pd.DataFrame, pumping_power_profiles: pd.DataFrame,
                      sdac_df: pd.DataFrame, addon_df: pd.DataFrame) -> None:
    """
    This function writes out the HTML output
    :param html_path: the path to the HTML output file
    :type html_path: str
    :param simulation_metadata: the simulation metadata
    :type simulation_metadata: list
    :param summary: the summary of results
    :type summary: list
    :param economic_parameters: the economic parameters
    :type economic_parameters: list
    :param engineering_parameters: the engineering parameters
    :type engineering_parameters: list
    :param resource_characteristics: the resource characteristics
    :type resource_characteristics: list
    :param reservoir_parameters: the reservoir parameters
    :type reservoir_parameters: list
    :param reservoir_stimulation_results: the reservoir stimulation results
    :type reservoir_stimulation_results: list
    :param CAPEX: the capital costs
    :type CAPEX: list
    :param OPEX: the operating and maintenance costs
    :type OPEX: list
    :param surface_equipment_results: the surface equipment simulation results
    :type surface_equipment_results: list
    :param sdac_results: the sdac results
    :type sdac_results: list
    :param addon_results: the addon results
    :type addon_results: list
    :param hce: the heating, cooling and/or electricity production profile
    :type hce: pd.DataFrame
    :param ahce: the annual heating, cooling and/or electricity production profile
    :type ahce: pd.DataFrame
    :param cashflow: the revenue & cashflow profile
    :type cashflow: pd.DataFrame
    :param pumping_power_profiles: the pumping power profiles
    :type pd.DataFrame
    :param sdac_df: the sdac dataframe
    :type sdac_df: pd.DataFrame
    :param addon_df: the addon dataframe

    """

    console = Console(style='bold black on white', force_terminal=True, record=True, width=500)

    # write out the simulation metadata
    console.print('*****************')
    console.print('***CASE REPORT***')
    console.print('*****************')
    console.print('Simulation Metadata')
    console.print('----------------------')

    for item in simulation_metadata:
        console.print(f'{str(item.parameter)}: {str(item.value)} {str(item.units)}')

    # write out the simple tables
    Write_Simple_HTML_Table('SUMMARY OF RESULTS', summary, console)
    Write_Simple_HTML_Table('ECONOMIC PARAMETERS', economic_parameters, console)
    Write_Simple_HTML_Table('ENGINEERING PARAMETERS', engineering_parameters, console)
    Write_Simple_HTML_Table('RESOURCE CHARACTERISTICS', resource_characteristics, console)
    Write_Simple_HTML_Table('RESERVOIR PARAMETERS', reservoir_parameters, console)
    Write_Simple_HTML_Table('RESERVOIR STIMULATION RESULTS', reservoir_stimulation_results, console)
    Write_Simple_HTML_Table('CAPITAL COSTS', CAPEX, console)
    Write_Simple_HTML_Table('OPERATING AND MAINTENANCE COSTS', OPEX, console)
    Write_Simple_HTML_Table('SURFACE EQUIPMENT SIMULATION RESULTS', surface_equipment_results, console)
    if len(addon_results) > 0:
        Write_Simple_HTML_Table('ADD-ON ECONOMICS', addon_results, console)
    if len(sdac_results) > 0:
        Write_Simple_HTML_Table('S_DAC_GT ECONOMICS', sdac_results, console)

    # write out the complex tables
    Write_Complex_HTML_Table('HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE', hce, 1, console)
    Write_Complex_HTML_Table('ANNUAL HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE', ahce, 1, console)
    Write_Complex_HTML_Table('REVENUE & CASHFLOW PROFILE', cashflow, 1, console)
    if len(pumping_power_profiles) > 0:
        Write_Complex_HTML_Table('PUMPING POWER PROFILES', pumping_power_profiles, 1, console)
    if len(addon_df) > 0:
        Write_Complex_HTML_Table('ADD-ON PROFILE', addon_df, 1, console)
    if len(sdac_df) > 0:
        Write_Complex_HTML_Table('S_DAC_GT PROFILE', sdac_df, 1, console)

    # Save it all as HTML.
    console.save_html(html_path)


def Plot_Twin_Graph(title: str, html_path: str, x: pd.array, y1: pd.array, y2: pd.array,
                    x_label: str, y1_label: str, y2_label:str) -> None:
    """
    This function plots the twin graph
    :param title: the title of the graph
    :type title: str
    :param html_path: the path to the HTML output file
    :type html_path: str
    :param x: the x values
    :type x: pd.array
    :param y1: the y1 values
    :type y1: pd.array
    :param y2: the y2 values
    :type y2: pd.array
    :param x_label: the x label
    :type x_label: str
    :param y1_label: the y1 label
    :type y1_label: str
    :param y2_label: the y2 label
    :type y2_label: str
    """
    COLOR_TEMPERATURE = "#69b3a2"
    COLOR_PRICE = "#3399e6"

    fig, ax1 = plt.subplots(figsize=(40, 4))

    ax1.plot(x, y1, label=UpgradeSymbologyOfUnits(y1_label), color=COLOR_PRICE, lw=3)
    ax1.set_xlabel(UpgradeSymbologyOfUnits(x_label), color = COLOR_PRICE, fontsize=14)
    ax1.set_ylabel(UpgradeSymbologyOfUnits(y1_label), color=COLOR_PRICE, fontsize=14)
    ax1.tick_params(axis="y", labelcolor=COLOR_PRICE)
    ax1.set_xlim(x.min(), x.max())
    ax1.legend(loc='lower left')

    ax2 = ax1.twinx()
    ax2.plot(x, y2, label=UpgradeSymbologyOfUnits(y2_label), color=COLOR_TEMPERATURE, lw=4)
    ax2.set_ylabel(UpgradeSymbologyOfUnits(y2_label), color=COLOR_TEMPERATURE, fontsize=14)
    ax2.tick_params(axis="y", labelcolor=COLOR_TEMPERATURE)
    ax2.legend(loc='best')

    fig.suptitle(title, fontsize=20)

    full_names: set = set()
    short_names: set = set()
    title = removeDisallowedFilenameChars(title.replace(' ', '_'))
    save_path = Path(Path(html_path).parent, f'{title}.png')
    plt.savefig(save_path)
    short_names.add(title)
    full_names.add(save_path)

    InsertImagesIntoHTML(html_path, short_names, full_names)


def Plot_Single_Graph(title: str, html_path: str, x: pd.array, y: pd.array, x_label: str, y_label: str) -> None:
    """
    This function plots the single graph
    :param title: the title of the graph
    :type title: str
    :param html_path: the path to the HTML output file
    :type html_path: str
    :param x: the x values
    :type x: pd.array
    :param y: the y values
    :type y: pd.array
    :param x_label: the x label
    :type x_label: str
    :param y_label: the y label
    :type y_label: str
    """
    COLOR_PRICE = "#3399e6"

#    plt.plot(x, y, color=COLOR_PRICE)
    fig, ax = plt.subplots(figsize=(40, 4))
    ax.plot(x, y, label=UpgradeSymbologyOfUnits(y_label), color=COLOR_PRICE)
    ax.set_xlabel(UpgradeSymbologyOfUnits(x_label), color = COLOR_PRICE, fontsize=14)
    ax.set_ylabel(UpgradeSymbologyOfUnits(y_label), color=COLOR_PRICE, fontsize=14)
    ax.tick_params(axis="y", labelcolor=COLOR_PRICE)
    ax.set_xlim(x.min(), x.max())
    ax.legend(loc='best')
    #plt.ylim(y.min(), y.max())
    #plt.gca().legend((UpgradeSymbologyOfUnits(x_label), UpgradeSymbologyOfUnits(y_label)), loc='best')
    fig.suptitle(title, fontsize=20)

    full_names: set = set()
    short_names: set = set()
    title = removeDisallowedFilenameChars(title.replace(' ', '_'))
    save_path = Path(Path(html_path).parent, f'{title}.png')
    plt.savefig(save_path)
    short_names.add(title)
    full_names.add(save_path)

    InsertImagesIntoHTML(html_path, short_names, full_names)


def Plot_Tables_Into_HTML(enduse_option: intParameter, plant_type: intParameter, html_path: str,
                          hce: pd.DataFrame, ahce: pd.DataFrame, cashflow: pd.DataFrame, pumping_power_profiles: pd.DataFrame,
                          sdac_df: pd.DataFrame, addon_df: pd.DataFrame) -> None:
    """
    This function plots the tables into the HTML
    :param enduse_option: the end use option
    :type enduse_option: intParameter
    :param html_path: the path to the HTML output file
    :type html_path: str
    :param plant_type: the plant type
    :type plant_type: intParameter
    :param hce: the heating, cooling and/or electricity production profile
    :type hce: pd.DataFrame
    :param ahce: the annual heating, cooling and/or electricity production profile
    :type ahce: pd.DataFrame
    :param cashflow: the revenue & cashflow profile
    :type cashflow: pd.DataFrame
    :param pumping_power_profiles: The pumping power profiles
    :type pd.DataFrame
    :param sdac_df: the sdac dataframe
    :type sdac_df: pd.DataFrame
    :param addon_df: the addon dataframe
    :type addon_df: pd.DataFrame
    """

    # HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILES
    # Plot the three that appear for all end uses
    Plot_Single_Graph('HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILES: Thermal Drawdown',
                      html_path, hce.values[0:, 1], hce.values[0:, 2], hce.columns[1].split('|')[0], hce.columns[2].split('|')[0])
    Plot_Single_Graph('HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILES: Geofluid Temperature',
                      html_path, hce.values[0:, 1], hce.values[0:, 3], hce.columns[1].split('|')[0], hce.columns[3].split('|')[0])
    Plot_Single_Graph('HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILES: Pump Power',
                      html_path, hce.values[0:, 1], hce.values[0:, 4], hce.columns[1].split('|')[0], hce.columns[4].split('|')[0])
    if enduse_option.value == EndUseOptions.ELECTRICITY:
        # only electricity
        Plot_Single_Graph('HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILES: First Law Efficiency',
                        html_path, hce.values[0:, 1], hce.values[0:, 6], hce.columns[1].split('|')[0], hce.columns[6].split('|')[0])
        Plot_Single_Graph('HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILES: Net Power',
                        html_path, hce.values[0:, 1], hce.values[0:, 5], hce.columns[1].split('|')[0], hce.columns[5].split('|')[0])
    elif enduse_option.value == EndUseOptions.HEAT and plant_type.value not in [PlantType.HEAT_PUMP, PlantType.DISTRICT_HEATING, PlantType.ABSORPTION_CHILLER]:
        # only direct-use
        Plot_Single_Graph('HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILES: Net Heat',
                        html_path, hce.values[0:, 1], hce.values[0:, 5], hce.columns[1].split('|')[0], hce.columns[5].split('|')[0])
    elif enduse_option.value == EndUseOptions.HEAT and plant_type.value == PlantType.HEAT_PUMP:
        # heat pump
        Plot_Twin_Graph('HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILES: Net Heat & Heat Pump Electricity Use',
                        html_path, hce.values[0:, 1], hce.values[0:, 5], hce.values[0:, 6],
                        hce.columns[1].split('|')[0], hce.columns[5].split('|')[0], hce.columns[6].split('|')[0])
    elif enduse_option.value == EndUseOptions.HEAT and plant_type.value == PlantType.DISTRICT_HEATING:
        # district heating
        Plot_Single_Graph('HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILES: Geothermal Heat Output',
                        html_path, hce.values[0:, 1], hce.values[0:, 5], hce.columns[1].split('|')[0], hce.columns[5].split('|')[0])
    elif enduse_option.value == EndUseOptions.HEAT and plant_type.value == PlantType.ABSORPTION_CHILLER:
        # absorption chiller
        Plot_Twin_Graph('HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILES: Net Heat & Net Cooling',
                        html_path, hce.values[0:, 1], hce.values[0:, 5], hce.values[0:, 6],
                        hce.columns[1].split('|')[0], hce.columns[5].split('|')[0], hce.columns[6].split('|')[0])
    elif enduse_option.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT, EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY,
                                EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]:
        # co-gen
        Plot_Twin_Graph('HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILES: Net Power & Net Heat',
                        html_path, hce.values[0:, 1], hce.values[0:, 5], hce.values[0:, 6],
                        hce.columns[1].split('|')[0], hce.columns[5].split('|')[0], hce.columns[6].split('|')[0])
        Plot_Single_Graph('HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILES: First Law Efficiency',
                        html_path, hce.values[0:, 1], hce.values[0:, 7], hce.columns[1].split('|')[0], hce.columns[7].split('|')[0])

    # ANNUAL HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE
    # plot the common graphs
    Plot_Twin_Graph('ANNUAL HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE: Heat Extracted & Reservoir Heat Content',
                    html_path, ahce.values[0:, 1], ahce.values[0:, 3], ahce.values[0:, 4],
                    ahce.columns[1].split('|')[0], ahce.columns[3].split('|')[0], ahce.columns[4].split('|')[0])
    if plant_type.value in [PlantType.DISTRICT_HEATING]:
        # columns are in a different place for district heating
        Plot_Single_Graph('ANNUAL HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE: Percentage of Total Heat Mined',
                          html_path, ahce.values[0:, 1], ahce.values[0:, 6], ahce.columns[1].split('|')[0], ahce.columns[6].split('|')[0])
    else:
        Plot_Single_Graph('ANNUAL HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE: Percentage of Total Heat Mined',
                          html_path, ahce.values[0:, 1], ahce.values[0:, 5], ahce.columns[1].split('|')[0], ahce.columns[5].split('|')[0])

    if enduse_option.value == EndUseOptions.ELECTRICITY:
        # only electricity
        Plot_Single_Graph('ANNUAL HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE: Electricity Provided',
                          html_path, ahce.values[0:, 1], ahce.values[0:, 2], ahce.columns[1].split('|')[0], ahce.columns[2].split('|')[0])
    elif plant_type.value == PlantType.ABSORPTION_CHILLER:
        # absorption chiller
        Plot_Single_Graph('ANNUAL HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE: Cooling Provided',
                          html_path, ahce.values[0:, 1], ahce.values[0:, 2], ahce.columns[1].split('|')[0], ahce.columns[2].split('|')[0])
    elif plant_type.value in [PlantType.DISTRICT_HEATING]:
        # district-heating
        Plot_Twin_Graph('ANNUAL HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE: Geothermal Heating Provided & Peaking Boiler Heating Provided',
                        html_path, ahce.values[0:, 1], ahce.values[0:, 2], ahce.values[0:, 3],
                        ahce.columns[1].split('|')[0], ahce.columns[2].split('|')[0], ahce.columns[3].split('|')[0])
    elif plant_type.value == PlantType.HEAT_PUMP:
        # heat pump
        Plot_Single_Graph('ANNUAL HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE: Heating Provided',
                          html_path, ahce.values[0:, 1], ahce.values[0:, 2], ahce.columns[1].split('|')[0], ahce.columns[2].split('|')[0])
        Plot_Single_Graph('ANNUAL HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE: Heat Pump Electricity Use',
                          html_path, ahce.values[0:, 1], ahce.values[0:, 4], ahce.columns[1].split('|')[0], ahce.columns[4].split('|')[0])
    elif enduse_option.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT, EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY,
                                                    EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                    EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]:
        # co-gen
        Plot_Twin_Graph('ANNUAL HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE: Heat Provided & Electricity Provided',
                        html_path, ahce.values[0:, 1], ahce.values[0:, 2], ahce.values[0:, 3],
                        ahce.columns[1].split('|')[0], ahce.columns[2].split('|')[0], ahce.columns[3].split('|')[0])
    elif enduse_option.value == EndUseOptions.HEAT:
        # only direct-use
        Plot_Single_Graph('ANNUAL HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE: Heat Provided',
                          html_path, ahce.values[0:, 1], ahce.values[0:, 2], ahce.columns[1].split('|')[0], ahce.columns[2].split('|')[0])

    # Cashflow Graphs
    Plot_Twin_Graph('REVENUE & CASHFLOW PROFILE: Electricity: Price & Cumulative Revenue',
                    html_path, cashflow.values[0:, 1], cashflow.values[0:, 2], cashflow.values[0:, 4],
                    cashflow.columns[1].split('|')[0], cashflow.columns[2].split('|')[0], cashflow.columns[4].split('|')[0])
    Plot_Twin_Graph('REVENUE & CASHFLOW PROFILE: Heat: Price & Cumulative Revenue',
                    html_path, cashflow.values[0:, 1], cashflow.values[0:, 5], cashflow.values[0:, 7],
                    cashflow.columns[1].split('|')[0], cashflow.columns[5].split('|')[0], cashflow.columns[7].split('|')[0])
    Plot_Twin_Graph('REVENUE & CASHFLOW PROFILE: Cooling: Price & Cumulative Revenue',
                    html_path, cashflow.values[0:, 1], cashflow.values[0:, 8], cashflow.values[0:, 10],
                    cashflow.columns[1].split('|')[0], cashflow.columns[8].split('|')[0], cashflow.columns[10].split('|')[0])
    Plot_Twin_Graph('REVENUE & CASHFLOW PROFILE: Carbon: Price & Cumulative Revenue',
                    html_path, cashflow.values[0:, 1], cashflow.values[0:, 11], cashflow.values[0:, 13],
                    cashflow.columns[1].split('|')[0], cashflow.columns[11].split('|')[0], cashflow.columns[13].split('|')[0])
    Plot_Twin_Graph('REVENUE & CASHFLOW PROFILE: Project: Net Revenue and cashflow',
                    html_path, cashflow.values[0:, 1], cashflow.values[0:, 15], cashflow.values[0:, 16],
                    cashflow.columns[1].split('|')[0], cashflow.columns[15].split('|')[0], cashflow.columns[16].split('|')[0])

    # Pumping Power Profiles Graphs
    if len(pumping_power_profiles) > 0:
        Plot_Twin_Graph('PUMPING POWER PROFILES: Production Pumping Power & Injection Pumping Power', html_path,
                        pumping_power_profiles.values[0:, 1], pumping_power_profiles.values[0:, 2], pumping_power_profiles.values[0:, 3],
                        pumping_power_profiles.columns[1].split('|')[0], pumping_power_profiles.columns[2].split('|')[0], pumping_power_profiles.columns[3].split('|')[0])
        Plot_Single_Graph('PUMPING POWER PROFILES: Pumping Power', html_path,
                            pumping_power_profiles.values[0:, 1], pumping_power_profiles.values[0:, 4], pumping_power_profiles.columns[1].split('|')[0],
                            pumping_power_profiles.columns[4].split('|')[0])

    if len (addon_df) > 0:
        Plot_Twin_Graph('ADD-ON PROFILE: Electricity Annual Price vs. Revenue',
                        html_path, addon_df.values[0:, 1], addon_df.values[0:, 2], addon_df.values[0:, 3],
                        addon_df.columns[1].split('|')[0], addon_df.columns[2].split('|')[0], addon_df.columns[3].split('|')[0])
        Plot_Twin_Graph('ADD-ON PROFILE: Heat Annual Price vs. Revenue',
                        html_path, addon_df.values[0:, 1], addon_df.values[0:, 4], addon_df.values[0:, 5],
                        addon_df.columns[1].split('|')[0], addon_df.columns[4].split('|')[0], addon_df.columns[5].split('|')[0])
        Plot_Twin_Graph('ADD-ON PROFILE: Add-On Net Revenue & Annual Cashflow',
                        html_path, addon_df.values[0:, 1], addon_df.values[0:, 6], addon_df.values[0:, 7],
                        addon_df.columns[1].split('|')[0], addon_df.columns[6].split('|')[0], addon_df.columns[7].split('|')[0])
        Plot_Single_Graph('ADD-ON PROFILE: Add-On Cumulative Cashflow',
                        html_path, addon_df.values[0:, 1], addon_df.values[0:, 8],  addon_df.columns[1].split('|')[0],
                          addon_df.columns[8].split('|')[0])
        Plot_Twin_Graph('ADD-ON PROFILE: Project Cashflow vs. Cumulative Cashflow',
                        html_path, addon_df.values[0:, 1], addon_df.values[0:, 9], addon_df.values[0:, 10],
                        addon_df.columns[1].split('|')[0], addon_df.columns[9].split('|')[0], addon_df.columns[10].split('|')[0])
    if len(sdac_df) > 0:
        Plot_Twin_Graph('S_DAC_GT PROFILE: Annual vs Cumulative Carbon Captured',
                        html_path, sdac_df.values[0:, 1], sdac_df.values[0:, 2], sdac_df.values[0:, 3],
                        sdac_df.columns[1].split('|')[0], sdac_df.columns[2].split('|')[0], sdac_df.columns[3].split('|')[0])
        Plot_Twin_Graph('S_DAC_GT PROFILE: Annual Cost vs Cumulative Cost',
                        html_path, sdac_df.values[0:, 1], sdac_df.values[0:, 4], sdac_df.values[0:, 5],
                        sdac_df.columns[1].split('|')[0], sdac_df.columns[4].split('|')[0], sdac_df.columns[5].split('|')[0])
        Plot_Single_Graph('S_DAC_GT PROFILE: Cumulative Capture Cost per Tonne',
                        html_path, sdac_df.values[0:, 1], sdac_df.values[0:, 6], sdac_df.columns[1].split('|')[0],
                          sdac_df.columns[6].split('|')[0])


def MakeDistrictHeatingPlot(html_path: str, dh_geothermal_heating: pd.array, daily_heating_demand: pd.array) -> None:
    """"
    Make a plot of the district heating system
    :param html_path: the path to the HTML output file
    :type html_path: str
    :param dh_geothermal_heating: the geothermal heating
    :type dh_geothermal_heating: pd.array
    :param daily_heating_demand: the daily heating demand
    :type daily_heating_demand: pd.array
    """
    plt.close('all')
    year_day = np.arange(1, 366, 1)  # make an array of days for plot x-axis
    plt.plot(year_day, daily_heating_demand, label='District Heating Demand')
    plt.fill_between(year_day, 0, dh_geothermal_heating[0:365] * 24, color='g', alpha=0.5,
                     label='Geothermal Heat Supply')
    plt.fill_between(year_day, dh_geothermal_heating[0:365] * 24,
                     daily_heating_demand, color='r', alpha=0.5,
                     label='Natural Gas Heat Supply')
    plt.xlabel('Ordinal Day')
    plt.ylabel('Heating Demand/Supply [MWh/day]')
    plt.ylim([0, max(daily_heating_demand) * 1.05])
    plt.legend()
    plt.title('Geothermal district heating system with peaking boilers')
    full_names: set = set()
    short_names: set = set()
    title = removeDisallowedFilenameChars('Geothermal district heating system with peaking boilers'.replace(' ', '_'))
    save_path = Path(Path(html_path).parent, f'{title}.png')
    plt.savefig(save_path)
    short_names.add(title)
    full_names.add(save_path)

    InsertImagesIntoHTML(html_path, short_names, full_names)

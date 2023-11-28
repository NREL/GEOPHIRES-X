from pathlib import Path

import pandas as pd

from geophires_x_client import GeophiresXClient
from geophires_x_client.geophires_input_parameters import GeophiresInputParameters


def process_file(file_path):
    client = GeophiresXClient()
    result = client.get_geophires_result(GeophiresInputParameters(from_file_path=file_path))

    all_results = result.result

    # Extracting specific values from all_results
    depth_m = (
        all_results.get('ENGINEERING PARAMETERS', {})
        .get('Well depth (or total length, if not vertical)', {})
        .get('value', None)
    )
    number_of_prod_wells = (
        all_results.get('ENGINEERING PARAMETERS', {}).get('Number of Production Wells', {}).get('value', None)
    )
    number_of_inj_wells = (
        all_results.get('ENGINEERING PARAMETERS', {}).get('Number of Injection Wells', {}).get('value', None)
    )
    max_reservoir_temp = (
        all_results.get('RESOURCE CHARACTERISTICS', {}).get('Maximum reservoir temperature', {}).get('value', None)
    )

    # CAPITAL COSTS
    wellfield_cost = (
        all_results.get('CAPITAL COSTS (M$)', {}).get('Drilling and completion costs', {}).get('value', None)
    )
    surface_plant_cost = (
        all_results.get('CAPITAL COSTS (M$)', {}).get('Surface power plant costs', {}).get('value', None)
    )
    exploration_cost = all_results.get('CAPITAL COSTS (M$)', {}).get('Exploration costs', {}).get('value', None)
    gathering_cost = (
        all_results.get('CAPITAL COSTS (M$)', {}).get('Field gathering system costs', {}).get('value', None)
    )

    # OPERATING AND MAINTENANCE COSTS
    wellfield_OM_cost = (
        all_results.get('OPERATING AND MAINTENANCE COSTS (M$/yr)', {})
        .get('Wellfield maintenance costs', {})
        .get('value', None)
    )
    surface_plant_OM_cost = (
        all_results.get('OPERATING AND MAINTENANCE COSTS (M$/yr)', {})
        .get('Power plant maintenance costs', {})
        .get('value', None)
    )
    water_OM_cost = (
        all_results.get('OPERATING AND MAINTENANCE COSTS (M$/yr)', {}).get('Water costs', {}).get('value', None)
    )

    # SURFACE EQUIPMENT SIMULATION RESULTS
    avg_total_heat_gen = (
        all_results.get('SURFACE EQUIPMENT SIMULATION RESULTS', {})
        .get('Average Total Electricity Generation', {})
        .get('value', None)
    )
    avg_total_electricity_gen = (
        all_results.get('SURFACE EQUIPMENT SIMULATION RESULTS', {})
        .get('Average Total Electricity Generation', {})
        .get('value', None)
    )

    # ECONOMIC PARAMETERS RESULTS
    lifetime = all_results.get('ECONOMIC PARAMETERS', {}).get('Project lifetime', {}).get('value', None)

    # Constructing the dictionary for DataFrame row
    data_row = {
        'Depth (m)': depth_m,
        'Number of Prod Wells': number_of_prod_wells,
        'Number of Inj Wells': number_of_inj_wells,
        'Maximum Reservoir Temperature (deg.C)': max_reservoir_temp,
        'Wellfield Cost ($M)': wellfield_cost,
        'Surface Plant Cost ($M)': surface_plant_cost,
        'Exploration Cost ($M)': exploration_cost,
        'Field Gathering System Cost ($M)': gathering_cost,
        'Wellfield O&M Cost ($M/year)': wellfield_OM_cost,
        'Surface Plant O&M Cost ($M/year)': surface_plant_OM_cost,
        'Make-Up Water O&M Cost ($M/year)': water_OM_cost,
        'Average Reservoir Heat Extraction (MWth)': avg_total_heat_gen,
        'Average Total Electricity Generation (MWe)': avg_total_electricity_gen,
        'Lifetime': lifetime,
    }

    return data_row


plant = 'CHP'
# Specify the folder containing .txt files
folder_path = Path('/Users/bpulluta/python-geophires-x/Engage-Testing/chp_test')

# Find all .txt files in the folder
file_paths = list(folder_path.glob('*.txt'))

# List to store dictionaries of results from each file
df_results = []

# Process each file and append the results to df_results
for file_path in file_paths:
    data_row = process_file(file_path)
    df_results.append(data_row)

df_final = pd.DataFrame(
    df_results,
    columns=[
        'Depth (m)',
        'Number of Prod Wells',
        'Number of Inj Wells',
        'Maximum Reservoir Temperature (deg.C)',
        'Wellfield Cost ($M)',
        'Surface Plant Cost ($M)',
        'Exploration Cost ($M)',
        'Field Gathering System Cost ($M)',
        'Wellfield O&M Cost ($M/year)',
        'Surface Plant O&M Cost ($M/year)',
        'Make-Up Water O&M Cost ($M/year)',
        'Average Reservoir Heat Extraction (MWth)',
        'Average Total Electricity Generation (MWe)',
        'Lifetime',
    ],
)

# Sorting and saving to Excel
df_final = df_final.sort_values(
    by=['Depth (m)', 'Number of Prod Wells', 'Number of Inj Wells'], ascending=[True, True, True]
)
df_final.to_csv('Engage-Testing/results.csv')

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from scipy.optimize import curve_fit

from geophires_x_client import GeophiresXClient
from geophires_x_client.geophires_input_parameters import GeophiresInputParameters


class EngageAnalysis:
    def __init__(self, plant):
        self.client = GeophiresXClient()
        self.df_results = []
        self.parameter_list = []
        self.plant = plant
        self.results_cache = {}  # Cache for storing results

    def process_multiple(self, input_params):
        # Generate a unique key for the input parameters (e.g., a string representation)
        param_key = str(input_params)

        # Check if results for these parameters are already in the cache
        if param_key in self.results_cache:
            return self.results_cache[param_key]

        # def process_multiple(self, input_params):
        result = self.client.get_geophires_result(GeophiresInputParameters(input_params))
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

        # RESERVOIR SIMULATION RESULTS
        avg_reservoir_extraction = (
            all_results.get('RESERVOIR SIMULATION RESULTS', {})
            .get('Average Reservoir Heat Extraction', {})
            .get('value', None)
        )

        # SURFACE EQUIPMENT SIMULATION RESULTS
        avg_total_heat_gen = (
            all_results.get('SURFACE EQUIPMENT SIMULATION RESULTS', {})
            .get('Average Net Heat Production', {})
            .get('value', None)
        )

        avg_total_electricity_gen = (
            all_results.get('SURFACE EQUIPMENT SIMULATION RESULTS', {})
            .get('Average Net Electricity Generation', {})
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
            'Average Reservoir Heat Extraction (MWth)': avg_reservoir_extraction,
            'Average Total Heat Generation (MWth)': avg_total_heat_gen,
            'Average Total Electricity Generation (MWe)': avg_total_electricity_gen,
            'Lifetime': lifetime,
        }

        # Save the processed data in the cache
        self.results_cache[param_key] = data_row

        return data_row

    def run_iterations(self):
        for params in self.parameter_list:
            data_row = self.process_multiple(params)
            self.df_results.append(data_row)

    def prepare_parameters(self, new_params_list):
        self.parameter_list = new_params_list

    def get_final_dataframe(self):
        return pd.DataFrame(
            self.df_results,
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
                'Average Total Heat Generation (MWth)',
                'Average Total Electricity Generation (MWe)',
                'Lifetime',
            ],
        )


def generate_parameters(base_params):
    parameter_list = []
    for depth in np.arange(2.5, 5.0, 0.1):
        for wells_prod in range(1, 7):
            for wells_inj in range(1, 7):
                if wells_inj < wells_prod:
                    continue

                # Create a copy of the base parameters and update specific values
                params = base_params.copy()
                params.update(
                    {
                        'Reservoir Depth': depth,
                        'Number of Production Wells': wells_prod,
                        'Number of Injection Wells': wells_inj,
                    }
                )
                parameter_list.append(params)
    return parameter_list


# Function to fit a linear model
def fit_linear_model(x, y):
    # Define the objective function for the linear model: y = ax + b
    def objective(x, a, b):
        return a * x + b

    # Use curve fitting to find the optimal values of a and b that minimize
    # the difference between the predicted y values and the actual y values
    popt, _ = curve_fit(objective, x, y)
    a, b = popt  # a is the slope, b is the y-intercept

    # Generate x values for the line of best fit: use the minimum and maximum x values
    x_line = np.asarray([np.min(x), np.max(x)])

    # Calculate the residuals (difference between actual y values and predicted y values)
    # This is used to adjust the y-intercept for the lower bound line
    b_values = y - np.multiply(a, x)

    # Calculate the 5th percentile of the residuals to determine the lower bound
    lower_b = np.percentile(b_values, 5)

    # Calculate the y values for the lower bound line using the adjusted y-intercept
    lower_line = objective(x_line, a, lower_b)

    # Create a label for the plot with the equation of the lower bound line
    label = f'y={a:.4f}x+{lower_b:.4f}'

    return a, lower_b, x_line, lower_line, label


# Function to create and customize scatter plots
def create_scatter_plot(x, y, x_line, lower_line, label, title, xlabel, ylabel, color_map, unique_vals, df):
    plt.figure()
    for i, val in enumerate(unique_vals):
        mask = df['Number of Prod Wells'] == val
        plt.scatter(x[mask], y[mask], color=color_map(i / len(unique_vals)), label=val, s=4)
    plt.plot(x_line, lower_line, '--', color='red', label=label)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend(handles=[plt.plot([], [], color='red', ls='--', label=label)[0]])


# Function to save plots to a PDF
def save_image(filename, fig_nums):
    p = PdfPages(filename)
    figs = [plt.figure(n) for n in fig_nums]
    for fig in figs:
        fig.savefig(p, format='pdf')
    p.close()


base_params = {
    'Reservoir Model': 3,
    'Drawdown Parameter': 0.00002,
    'Number of Segments': 1,
    'Gradient 1': 70,
    'Maximum Temperature': 400,
    'Production Well Diameter': 8.5,
    'Injection Well Diameter': 8.5,
    'Ramey Production Wellbore Model': 0,
    'Production Wellbore Temperature Drop': 5,
    'Injection Wellbore Temperature Gain': 3,
    'Production Flow Rate per Well': 70,
    'Reservoir Volume Option': 1,
    'Fracture Shape': 1,
    'Fracture Area': 200000,
    'Number of Fractures': 12,
    'Fracture Separation': 80,
    'Injectivity Index': 5,
    'Injection Temperature': 70,
    'Maximum Drawdown': 1,
    'Reservoir Heat Capacity': 1000,
    'Reservoir Density': 3000,
    'Reservoir Thermal Conductivity': 3,
    'Water Loss Fraction': 0.02,
    'End-Use Option': 31,
    'Power Plant Type': 4,
    'Circulation Pump Efficiency': 0.80,
    'Utilization Factor': 0.9,
    'End-Use Efficiency Factor': 0.9,
    'Surface Temperature': 15,
    'Ambient Temperature': 15,
    'Plant Lifetime': 35,
    'Economic Model': 2,
    'Fraction of Investment in Bonds': 0.5,
    'Inflated Bond Interest Rate': 0.05,
    'Inflated Equity Interest Rate': 0.08,
    'Inflation Rate': 0.02,
    'Combined Income Tax Rate': 0.3,
    'Gross Revenue Tax Rate': 0,
    'Investment Tax Credit Rate': 0,
    'Property Tax Rate': 0,
    'Inflation Rate During Construction': 0.05,
    'Well Drilling and Completion Capital Cost Adjustment Factor': 1,
    'Well Drilling Cost Correlation': 3,
    'Reservoir Stimulation Capital Cost Adjustment Factor': 1,
    'Surface Plant Capital Cost Adjustment Factor': 1,
    'Field Gathering System Capital Cost Adjustment Factor': 1,
    'Exploration Capital Cost Adjustment Factor': 1,
    'Wellfield O&M Cost Adjustment Factor': 1,
    'Surface Plant O&M Cost Adjustment Factor': 1,
    'Water Cost Adjustment Factor': 1,
    'Heat Rate': 0.02,
    'Print Output to Console': 0,
    'Time steps per year': 10,
}

plant = 'CHP'

engage_analysis = EngageAnalysis(plant)

# Generate parameters based on the base parameters
generated_params = generate_parameters(base_params)
engage_analysis.prepare_parameters(generated_params)

# Run iterations and process the data
engage_analysis.run_iterations()

df_final = engage_analysis.get_final_dataframe()

# Sorting and saving to Excel
df_final = df_final.sort_values(
    by=['Depth (m)', 'Number of Prod Wells', 'Number of Inj Wells'], ascending=[True, True, True]
)
df_final.to_csv('Engage-Testing/results.csv')

# Prepare data for plots
cmap = plt.get_cmap('OrRd')
unique_prod_wells = df_final['Number of Prod Wells'].unique()

# Prepare arrays for scatter plot and linear model
thermal_capacity = np.array(df_final['Average Reservoir Heat Extraction (MWth)'])
electric_capacity = np.array(df_final['Average Total Electricity Generation (MWe)'])
subsurface_cost = np.array(df_final['Wellfield Cost ($M)']) + np.array(df_final['Field Gathering System Cost ($M)'])
surface_cost = np.array(df_final['Surface Plant Cost ($M)'])
subsurface_o_m_cost = np.array(df_final['Wellfield O&M Cost ($M/year)']) + np.array(
    df_final['Make-Up Water O&M Cost ($M/year)']
)
surface_o_m_cost = np.array(df_final['Surface Plant O&M Cost ($M/year)'])

# Fit linear models and prepare for scatter plots
a1, b1, x1_line, lower_b1_line, label_b1 = fit_linear_model(thermal_capacity, subsurface_cost)
a2, b2, x2_line, lower_b2_line, label_b2 = fit_linear_model(electric_capacity, surface_cost)
a3, b3, x3_line, lower_b3_line, label_b3 = fit_linear_model(thermal_capacity, subsurface_o_m_cost)
a4, b4, x4_line, lower_b4_line, label_b4 = fit_linear_model(electric_capacity, surface_o_m_cost)

# Create scatter plots
create_scatter_plot(
    thermal_capacity,
    subsurface_cost,
    x1_line,
    lower_b1_line,
    label_b1,
    f'{plant} subsurface cost-to-thermal capacity relation',
    'Avg. Thermal capacity (MWth)',
    'Subsurface Total Cost ($M)',
    cmap,
    unique_prod_wells,
    df_final,
)

create_scatter_plot(
    electric_capacity,
    surface_cost,
    x2_line,
    lower_b2_line,
    label_b2,
    f'{plant} surface cost-to-electric capacity relation',
    'Avg. Electric capacity (MWe)',
    'Surface Total Cost ($M)',
    cmap,
    unique_prod_wells,
    df_final,
)

create_scatter_plot(
    thermal_capacity,
    subsurface_o_m_cost,
    x3_line,
    lower_b3_line,
    label_b3,
    f'{plant} subsurface O&M cost-to-thermal capacity relation',
    'Avg. Thermal capacity (MWth)',
    'Subsurface Total O&M Cost ($M)',
    cmap,
    unique_prod_wells,
    df_final,
)

create_scatter_plot(
    electric_capacity,
    surface_o_m_cost,
    x4_line,
    lower_b4_line,
    label_b4,
    f'{plant} surface O&M cost-to-electric capacity relation',
    'Avg. Electric capacity (MWe)',
    'Surface O&M Total Cost ($M)',
    cmap,
    unique_prod_wells,
    df_final,
)

# Save all plots to a PDF
fig_nums = plt.get_fignums()

save_image('Engage-Testing/results.pdf', fig_nums)

#!/usr/bin/env python
# coding: utf-8

# ### Solid Sorbent Direct Air Capture Using Geothermal Energy Resources
# # (S-DAC-GT)
# # Model For Region Specific Economic Analysis
# 
# ### SPE-215735-MS
# 
# ### Conference: Session: 02 - Technology Systems and Strategy for the Energy Transition
# ### August 2023
# 
# #### Paper Authors: Timur Kuru, Keivan Khaleghi, and Silviu Livescu
# #### University of Texas at Austin, United States
# 
# #### Primary coder: Timur Kuru
# 
# #### Prepared 6/13/2023

# In[ ]:


# Imports and constants
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
import tkinter.font as tkfont
import tkinter.messagebox as tkmb

# from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Global parameter - Capital Recovery Rate or Fixed Charge Factor - set initially for definitions
CRF = 0.1175


# In[ ]:


# Function definitions

# CRF calculator. Also Fixed Charge Factor - FCF
# Default set to 11.75%, or calculated value for project duration of 20 years with WACC of 10%
def calculate_CRF(*args):
    bold_font = tkfont.Font(weight="bold", size=10)
    try:
        wacc = float(wacc_entry.get())/100
        num_years = float(num_years_entry.get())
        
        # Validate the range for WACC
        if not (wacc_min/100 <= wacc <= wacc_max/100):
            raise ValueError("WACC should be between {:.1f}% and {:.0f}%".format(wacc_min, wacc_max))
        
        # Validate the range for Number of years
        if not (num_years_min <= num_years <= num_years_max):
            raise ValueError("Number of years should be between {:.0f} and {:0f}".format(num_years_min, num_years_max))
        
        CRF = (wacc*(1+wacc)**num_years)/((1+wacc)**num_years-1)
        CRF_label.config(text="Calculated Fixed Charge Factor (FCF):    {:.2f}%".format(CRF*100), font=bold_font, fg="black")
    except ValueError as e:
        CRF_label.config(text=str(e), fg="red")

# Command to close main parameter input window
# Other "close window" commands are defined within child-window functions
def close_window():
    popup_window.destroy()


# In[ ]:


# Function definitions

# Parameter range check
# Used prior to LCOD and CO2 Intensity calculation for results chart and sensitivity chart generation
# Produces an error window if a parameter is out of range, and returns True if parameter is outside of range
def range_check():
    wacc = float(wacc_entry.get())/100
    num_years = float(num_years_entry.get())
    CAPEX = float(CAPEX_entry.get())
    OPEX = float(OPEX_entry.get())
    elec = float(elec_entry.get())
    therm = float(therm_entry.get())
    NG_price = float(NG_price_entry.get())
    power_cost = float(power_cost_entry.get())
    power_co2intensity = float(power_co2intensity_entry.get())
    CAPEX_mult = float(CAPEX_mult_entry.get())
    OPEX_mult = float(OPEX_mult_entry.get())
    therm_index = float(therm_index_entry.get())
    depth = float(depth_entry.get())
    temp_drawdown = float(temp_drawdown_entry.get())
    transport = float(transport_entry.get())
    storage = float(storage_entry.get())
    
    if not (wacc_min/100 <= wacc <= wacc_max/100):
        error_message = "ERROR: WACC should be between {}% and {}%".format(wacc_min, wacc_max)
        tkmb.showerror ("Range Error", error_message, parent=popup_window)
        return(True)

    if not (num_years_min <= num_years <= num_years_max):
        error_message = "ERROR: Number of years should be between {:.0f} and {:.0f}".format(num_years_min, num_years_max)
        tkmb.showerror ("Range Error", error_message, parent=popup_window)
        return(True)
    
    if not (CAPEX_min <= CAPEX <= CAPEX_max):
        error_message = "ERROR: CAPEX should be between {} and {}".format(CAPEX_min, CAPEX_max)
        tkmb.showerror ("Range Error", error_message, parent=popup_window)
        return(True)
    
    if not (OPEX_min <= OPEX <= OPEX_max):
        error_message = "ERROR: OPEX should be between {} and {}".format(OPEX_min, OPEX_max)
        tkmb.showerror ("Range Error", error_message, parent=popup_window)
        return(True)
    
    if not (elec_min <= elec <= elec_max):
        error_message = "ERROR: Electrical Energy should be between {} and {}".format(elec_min, elec_max)
        tkmb.showerror ("Range Error", error_message, parent=popup_window)
        return(True)
    
    if not (therm_min <= therm <= therm_max):
        error_message = "ERROR: Thermal Energy should be between {} and {}".format(therm_min, therm_max)
        tkmb.showerror ("Range Error", error_message, parent=popup_window)
        return(True)
    
    if not (NG_price_min <= NG_price <= NG_price_max):
        error_message = "ERROR: Natural Gas Price should be between {} and {}".format(NG_price_min, NG_price_max)
        tkmb.showerror ("Range Error", error_message, parent=popup_window)
        return(True)
    
    if not (power_cost_min <= power_cost <= power_cost_max):
        error_message = "ERROR: Electricity Price should be between {} and {}".format(power_cost_min, power_cost_max)
        tkmb.showerror ("Range Error", error_message, parent=popup_window)
        return(True)
    
    if not (power_co2intensity_min <= power_co2intensity <= power_co2intensity_max):
        error_message = "ERROR: CO2 Intensity of Electricity should be between {} and {}".format(power_co2intensity_min, power_co2intensity_max)
        tkmb.showerror ("Range Error", error_message, parent=popup_window)
        return(True)
    
    if not (CAPEX_mult_min <= CAPEX_mult <= CAPEX_mult_max):
        error_message = "ERROR: CAPEX Multiplier should be between {} and {}".format(CAPEX_mult_min, CAPEX_mult_max)
        tkmb.showerror ("Range Error", error_message, parent=popup_window)
        return(True)
    
    if not (OPEX_mult_min <= OPEX_mult <= OPEX_mult_max):
        error_message = "ERROR: OPEX Multiplier should be between {} and {}".format(OPEX_mult_min, OPEX_mult_max)
        tkmb.showerror ("Range Error", error_message, parent=popup_window)
        return(True)
    
    if not (therm_index_min <= therm_index <= therm_index_max):
        error_message = "ERROR: S-DAC Thermal Energy Multiplier should be between {} and {}".format(therm_index_min, therm_index_max)
        tkmb.showerror ("Range Error", error_message, parent=popup_window)
        return(True)
    
    if not (depth_min <= depth <= depth_max):
        error_message = "ERROR: Geothermal Reservoir Depth should be between {} and {}".format(depth_min, depth_max)
        tkmb.showerror ("Range Error", error_message, parent=popup_window)
        return(True)

    if not (temp_drawdown_min <= temp_drawdown <= temp_drawdown_max):
        error_message = "ERROR: Geothermal Reservoir Temperature Drawdown should be between {} and {}".format(temp_drawdown_min, temp_drawdown_max)
        tkmb.showerror ("Range Error", error_message, parent=popup_window)
        return(True)

    if not (transport_min <= transport <= transport_max):
        error_message = "ERROR: CO2 Transportation Cost should be between {} and {}".format(transport_min, transport_max)
        tkmb.showerror ("Range Error", error_message, parent=popup_window)
        return(True)
    
    if not (storage_min <= storage <= storage_max):
        error_message = "ERROR: CO2 Storage Cost should be between {} and {}".format(storage_min, storage_max)
        tkmb.showerror ("Range Error", error_message, parent=popup_window)
        return(True)
    
    return(False)
    


# In[ ]:


# Function definitions

# Calculate Levelized cost of heat and ratio of electric power to heat power
# LCOH calculated in USD
# Power ratio calculated as kWh_e / kWh_th --> used for calculating CO2 footprint of geothermal energy
# inputs are cost of electricity, regional capex and opex multipliers, 
# depth of geothermal reservoir (assumed to be 120degC), and long-term thermal drawdown of thermal drawdown
def geo_therm_cost(power_cost, CAPEX_mult, OPEX_mult, depth, temp_drawdown):
    # Update NREL 2016 model for 2022
    # Inflation 2017 thru 2022 1H
    Inflation = 1.189
    # 2016 - Sep 2022 - EIA drilling prod report
    Drilling_efficiency_factor = 1.61
    # Thermal capacity of water
    H2O_thermal_capacity =  0.001163 # kWh/kg C
    # Plant capacity factor
    Capacity_factor = 0.9

    # NREL 2016 Model for new well adjusted for inflation
    NREL_depth = 4101                                    # feet
    NREL_CAPEX = 3712500 * Inflation                     # USD, excludes drilling
    NREL_CAPEX_drill =  2112500 * Inflation              # USD
    NREL_drill_per_foot = NREL_CAPEX_drill/NREL_depth    # USD/foot
    NREL_pumping =  1980215                              # kWh
    NREL_pump_per_foot = NREL_pumping/NREL_depth         # kWh/foot
    NREL_inhibitor =  50000 * Inflation                  # USD
    NREL_labor = 100000 * Inflation                      # USD
    NREL_reinjection =  127130 * Inflation               # USD

    # Normalize for region
    CAPEX = NREL_CAPEX * CAPEX_mult 
    CAPEX_drill = depth * NREL_drill_per_foot / Drilling_efficiency_factor
    pump_kwh = depth * NREL_pump_per_foot
    pump_cost = pump_kwh * power_cost
    inhibitor = NREL_inhibitor * OPEX_mult
    labor = NREL_labor * OPEX_mult
    reinjection = NREL_reinjection / NREL_depth * depth * OPEX_mult
    
    # total costs
    CAPEX_total = CAPEX + CAPEX_drill
    OPEX_total = pump_cost + inhibitor + labor + reinjection

    # total thermal energy generation
    Production_temp = 120 - temp_drawdown        # degC     
    Injection_temp = 80                          # degC 
    Flow_rate = 89                        # L/s
    Thermal_capacity = (Production_temp-Injection_temp)*Flow_rate*H2O_thermal_capacity*60*60   # kW
    Annual_op_hrs = 365*24*Capacity_factor         # hours
    Therm_total = Thermal_capacity * Annual_op_hrs # kWh
    
    # Levelized cost of heat (LCOH)
    LCOH = (CAPEX_total*CRF + OPEX_total)/Therm_total # $/kWh_therm
    
    kWh_e_per_kWh_th = pump_kwh / Therm_total
    
    return (LCOH, kWh_e_per_kWh_th)


# In[ ]:


#Function definitions

# Function to create results bar chart child window
# Calculates and charts levelized cost of DAC (LCOD) and CO2 intensity based on economic, DAC technical, 
# and region specific parameters obtained from main parameter input window 
# LDAC is in USD, CO2 intensity is defined as units of CO2 emitted for each unit of DAC 
# Outputs 2 bart charts showing 3 DAC systems using different sources for thermal heat: baseline 100% electric,
# natural gas, and geothermal
def create_bar_charts():
    CAPEX = float(CAPEX_entry.get())
    OPEX = float(OPEX_entry.get())
    elec = float(elec_entry.get())
    therm = float(therm_entry.get())
    NG_price = float(NG_price_entry.get())
    power_cost = float(power_cost_entry.get())
    power_co2intensity = float(power_co2intensity_entry.get())
    CAPEX_mult = float(CAPEX_mult_entry.get())
    OPEX_mult = float(OPEX_mult_entry.get())
    therm_index = float(therm_index_entry.get())
    depth = float(depth_entry.get())
    temp_drawdown = float(temp_drawdown_entry.get())
    transport = float(transport_entry.get())
    storage = float(storage_entry.get())
    
    # Ensure parameters are within range.  If not, exit function without completing calculation or generating charts
    if (range_check()):
        return()
    
    ng_co2intensity = 0.194965384    # tonne/MWh_th
    
    CAPEX = CAPEX * CRF
    CAPEX = CAPEX * CAPEX_mult
    OPEX = OPEX * OPEX_mult
    therm = therm * therm_index
    power_totalcost = elec * power_cost
    elec_heat_totalcost = therm * power_cost
    NG_price = NG_price / 282.614    # Convert from $/McF to $/kWh_th
    NG_totalcost = therm * NG_price
    (LCOH, kWh_e_per_kWh_th) = geo_therm_cost(power_cost, CAPEX_mult, OPEX_mult, depth, temp_drawdown)
    geothermal_totalcost = LCOH*therm
    co2_power = elec/1000*power_co2intensity
    co2_elec_heat = therm/1000*power_co2intensity
    co2_ng = therm/1000*ng_co2intensity
    co2_geothermal = therm*kWh_e_per_kWh_th/1000*power_co2intensity
    
    LCOD_elec = CAPEX+OPEX+power_totalcost+elec_heat_totalcost+storage+transport
    LCOD_ng = CAPEX+OPEX+power_totalcost+NG_totalcost+storage+transport
    LCOD_geo = CAPEX+OPEX+power_totalcost+geothermal_totalcost+storage+transport
    
    CO2total_elec = co2_power + co2_elec_heat
    CO2total_ng = co2_power + co2_ng
    CO2total_geo = co2_power + co2_geothermal
    
    # Temporary print lines for debugging
    #print("Total LCOD 100% electric: ", LCOD_elec)
    #print("Total LCOD natural gas: ", LCOD_ng)
    #print("Total LCOD S-DAC-GT: ", LCOD_geo)
    #print("Total CO2 Intensity 100% electric: ", CO2total_elec)
    #print("Total CO2 Intensity natural gas: ", CO2total_ng)
    #print("Total CO2 Intensity S-DAC-GT: ", CO2total_geo)
        
    # Create data for the bar charts
    x = ['100% electric', 'Natural Gas', 'S-DAC-GT']
    y_LCOD = [LCOD_elec,LCOD_ng,LCOD_geo]
    y_CO2 = [CO2total_elec,CO2total_ng,CO2total_geo]
    
    colors = [(31/255, 119/255, 180/255), (214/255, 39/255, 40/255), (44/255, 160/255, 44/255)]   
    
    figure, (plt1, plt2) = plt.subplots(1,2,figsize=(10, 5))
    LCOD_bars = plt1.bar(x, y_LCOD,color=colors, edgecolor='black')
    plt1.set_ylabel('USD'); 
    plt1.set_title('Levelized Cost of DAC (LCOD)')   
    
    # Add labels for plt1
    for bar in LCOD_bars:
        yval = bar.get_height()
        plt1.text(bar.get_x() + bar.get_width()/2, yval, int(yval), va='bottom', ha='center') 
        
    CO2_bars = plt2.bar(x, y_CO2,color=colors, edgecolor='black')
    plt2.set_ylabel('Units CO2 Emissions per Unit DAC'); 
    plt2.set_title('S-DAC CO2 Intensity')
    
    # Add labels for plt2
    for bar in CO2_bars:
        yval = bar.get_height()
        plt2.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 1), va='bottom', ha='center') 
    
    chart_window = tk.Toplevel(popup_window)
    chart_window.title('Results Charts')
    chart_window.geometry('800x400')
    
    canvas = FigureCanvasTkAgg(figure, master=chart_window)
    canvas.draw()
    canvas.get_tk_widget().pack()
    
    # close window command - closes only bar chart child window
    def close_chart_window():
        chart_window.destroy()
        
    close_button = tk.Button(chart_window, text="Close", command=close_chart_window)
    close_button.pack(pady=10)
    
    plt.close(figure)


# In[ ]:


#Function definitions

# Function to create sensitivity chart child window
# Calculates and charts sensititivity of LCOD and CO2 intensity for only geothermal DAC system to all input parameters
# "Sensitivity delta" allows user to set increase/decrease of each parameter.  Default is +/- 25%
def sensitivity_analysis():
    
    # Ensure parameters are within range.  If not, exit function without completing calculation or generating charts
    if (range_check()):
        return()
    
    global canvas
    canvas = None  # Start with no canvas
    
    bold_font = tkfont.Font(weight="bold", size=10)
    italic_font = tkfont.Font(slant="italic", size=10)
        
    sensitivity_window = tk.Toplevel(popup_window)
    sensitivity_window.title('S-DAC-GT Sensitivity')
    sensitivity_window.geometry('1000x800')
    
    delta_min = 0
    delta_max = 100
    default_delta = 25
    
    sensitivity_frame = tk.Frame(sensitivity_window)
    sensitivity_frame.pack(side=tk.TOP, fill=tk.X)
    
    empty_label = tk.Label(sensitivity_frame, text="")
    empty_label.grid(row=0, column=0, columnspan=2, padx=125, pady=5)
    delta_label = tk.Label(sensitivity_frame, text="Sensitivity Delta:", font=bold_font)
    delta_label.grid(row=0, column=5, padx=10, pady=5, sticky=tk.W)
    delta_entry = tk.Entry(sensitivity_frame, width=10, justify=tk.RIGHT)
    delta_entry.insert(tk.END, default_delta)
    delta_entry.grid(row=0, column=6, padx=10, pady=5)
    delta_unit_label = tk.Label(sensitivity_frame, text="%", font=bold_font)
    delta_unit_label.grid(row=0, column=7, padx=0, pady=5, sticky=tk.W)
    delta_range_label = tk.Label(sensitivity_frame, text="(Range: {:.0f} - {:.0f})".format(delta_min, delta_max), font=bold_font)
    delta_range_label.grid(row=0, column=8, padx=10, pady=5, sticky=tk.W)
    note_label = tk.Label(sensitivity_frame, text="Note: Sensitivity calculation is constrained by min/max of allowable parameter range.", font=italic_font)
    note_label.grid(row=1, column=5, columnspan=5, padx=10, pady=5, sticky=tk.W)
    
    def update_sensitivity():
        delta = float(delta_entry.get()) / 100
            
        CAPEX = float(CAPEX_entry.get())                               # vars[0]
        OPEX = float(OPEX_entry.get())                                 # vars[1]
        elec = float(elec_entry.get())                                 # vars[2]
        therm = float(therm_entry.get())                               # vars[3]
        NG_price = float(NG_price_entry.get())                         # vars[4]
        power_cost = float(power_cost_entry.get())                     # vars[5]
        power_co2intensity = float(power_co2intensity_entry.get())     # vars[6]
        CAPEX_mult = float(CAPEX_mult_entry.get())                     # vars[7]
        OPEX_mult = float(OPEX_mult_entry.get())                       # vars[8]
        therm_index = float(therm_index_entry.get())                   # vars[9]
        depth = float(depth_entry.get())                               # vars[10]
        temp_drawdown = float(temp_drawdown_entry.get())               # vars[11]
        transport = float(transport_entry.get())                       # vars[12]
        storage = float(storage_entry.get())                           # vars[13]

    
        vars_initial = [CAPEX,OPEX,elec,therm,NG_price,
                        power_cost,power_co2intensity,CAPEX_mult,
                        OPEX_mult,therm_index,depth,temp_drawdown,
                        transport,storage]

        # Used to ensure sensitivity does not exceed parameter range
        vars_minmax = [[CAPEX_min,CAPEX_max],
                       [OPEX_min,OPEX_max],
                       [elec_min,elec_max],
                       [therm_min,therm_max],
                       [NG_price_min,NG_price_max],
                       [power_cost_min,power_cost_max],
                       [power_co2intensity_min,power_co2intensity_max],
                       [CAPEX_mult_min,CAPEX_mult_max],
                       [OPEX_mult_min,OPEX_mult_max],
                       [therm_index_min,therm_index_max],
                       [depth_min,depth_max],
                       [temp_drawdown_min,temp_drawdown_max],
                       [transport_min,transport_max],
                       [storage_min,storage_max]]
        
        ng_co2intensity = 0.194965384    # tonne/MWh_th
    
        # Calculate base values
        CAPEX = CAPEX * CRF
        CAPEX = CAPEX * CAPEX_mult
        OPEX = OPEX * OPEX_mult
        therm = therm * therm_index
        power_totalcost = elec * power_cost
        elec_heat_totalcost = therm * power_cost
        NG_price = NG_price / 282.614    # Convert from $/McF to $/kWh_th
        NG_totalcost = therm * NG_price
        (LCOH, kWh_e_per_kWh_th) = geo_therm_cost(power_cost, CAPEX_mult, OPEX_mult, depth, temp_drawdown)
        geothermal_totalcost = LCOH*therm
        co2_power = elec/1000*power_co2intensity
        co2_elec_heat = therm/1000*power_co2intensity
        co2_ng = therm/1000*ng_co2intensity
        co2_geothermal = therm*kWh_e_per_kWh_th/1000*power_co2intensity

        LCOD_elec_base = CAPEX+OPEX+power_totalcost+elec_heat_totalcost+storage+transport
        LCOD_ng_base = CAPEX+OPEX+power_totalcost+NG_totalcost+storage+transport
        LCOD_geo_base = CAPEX+OPEX+power_totalcost+geothermal_totalcost+storage+transport

        CO2total_elec_base = co2_power + co2_elec_heat
        CO2total_ng_base = co2_power + co2_ng
        CO2total_geo_base = co2_power + co2_geothermal

        vars = vars_initial[:]        
        
        LCOD_sensitivity_increase = []
        LCOD_sensitivity_decrease = []

        CO2_sensitivity_increase = []
        CO2_sensitivity_decrease = []
    
        for i, var in enumerate(vars):
            
            #ensure that the sensitivity parameter does not exceed the min/max of parameter range
            var_min, var_max = vars_minmax[i]
            
            # Calculate sensitivity for increase
            vars[i] = var*(1+delta)
            
            vars[i] = min(vars[i],var_max)
        
            vars[0] = vars[0] * CRF
            vars[0] = vars[0] * vars[7]
            vars[1] = vars[1] * vars[8]
            vars[3] = vars[3] * vars[9]
            power_totalcost = vars[2] * vars[5]
            elec_heat_totalcost = vars[3] * vars[5]
            vars[4] = vars[4] / 282.614    # Convert from $/McF to $/kWh_th
            NG_totalcost = vars[3] * vars[4]
            (LCOH, kWh_e_per_kWh_th) = geo_therm_cost(vars[5], vars[7], vars[8], vars[10], vars[11])
            geothermal_totalcost = LCOH*vars[3]
            co2_power = vars[2]/1000*vars[6]
            co2_elec_heat = vars[3]/1000*vars[6]
            co2_ng = vars[3]/1000*ng_co2intensity
            co2_geothermal = vars[3]*kWh_e_per_kWh_th/1000*vars[6]
    
            LCOD_elec = vars[0]+vars[1]+power_totalcost+elec_heat_totalcost+vars[13]+vars[12]
            LCOD_ng = vars[0]+vars[1]+power_totalcost+NG_totalcost+vars[13]+vars[12]
            LCOD_geo = vars[0]+vars[1]+power_totalcost+geothermal_totalcost+vars[13]+vars[12]
    
            CO2total_elec = co2_power + co2_elec_heat
            CO2total_ng = co2_power + co2_ng
            CO2total_geo = co2_power + co2_geothermal

            LCOD_increase = LCOD_geo - LCOD_geo_base
            CO2_increase = CO2total_geo - CO2total_geo_base
        
            # reset vars
            vars = vars_initial[:]
        
            # Calculate sensitivity for decrease
            vars[i] = var*(1-delta)
            
            vars[i] = max(vars[i],var_min)
        
            vars[0] = vars[0] * CRF
            vars[0] = vars[0] * vars[7]
            vars[1] = vars[1] * vars[8]
            vars[3] = vars[3] * vars[9]
            power_totalcost = vars[2] * vars[5]
            elec_heat_totalcost = vars[3] * vars[5]
            vars[4] = vars[4] / 282.614    # Convert from $/McF to $/kWh_th
            NG_totalcost = vars[3] * vars[4]
            (LCOH, kWh_e_per_kWh_th) = geo_therm_cost(vars[5], vars[7], vars[8], vars[10], vars[11])
            geothermal_totalcost = LCOH*vars[3]
            co2_power = vars[2]/1000*vars[6]
            co2_elec_heat = vars[3]/1000*vars[6]
            co2_ng = vars[3]/1000*ng_co2intensity
            co2_geothermal = vars[3]*kWh_e_per_kWh_th/1000*vars[6]
    
            LCOD_elec = vars[0]+vars[1]+power_totalcost+elec_heat_totalcost+vars[13]+vars[12]
            LCOD_ng = vars[0]+vars[1]+power_totalcost+NG_totalcost+vars[13]+vars[12]
            LCOD_geo = vars[0]+vars[1]+power_totalcost+geothermal_totalcost+vars[13]+vars[12]
    
            CO2total_elec = co2_power + co2_elec_heat
            CO2total_ng = co2_power + co2_ng
            CO2total_geo = co2_power + co2_geothermal

            LCOD_decrease = LCOD_geo - LCOD_geo_base
            CO2_decrease = CO2total_geo - CO2total_geo_base
           
            LCOD_sensitivity_increase.append(LCOD_increase)
            LCOD_sensitivity_decrease.append(LCOD_decrease)
    
            CO2_sensitivity_increase.append(CO2_increase)
            CO2_sensitivity_decrease.append(CO2_decrease)
        
            # reset vars
            vars = vars_initial[:]
        
        global canvas
        if canvas is not None:
            canvas.get_tk_widget().pack_forget()  # Remove the old canvas from the layout
        
        # Generate parameter labels
        parameters = ["CAPEX","OPEX","Electrical Energy","Thermal Energy","Natural Gas Price",
                      "Electric Power Cost","CO2 Intensity of Electricity","CAPEX Multiplier",
                      "OPEX Multiplier","S-DAC Thermal Energy Multiplier","Geothermal Reservoir Depth",
                      "Reservoir Temperature Drawdown","CO2 Transportation","CO2 Storage"]
        
        pos = np.arange(len(parameters))
            
        figure, (plt1, plt2) = plt.subplots(1,2,figsize=(10, 10))
        figure.subplots_adjust(left=0.25, bottom=0.1, right=0.9, top=0.9, wspace=0.2, hspace=0)
    
        plt1.barh(pos, LCOD_sensitivity_increase, align='center', color='#cc4b37', label='Increase',edgecolor='black')
        plt1.barh(pos, LCOD_sensitivity_decrease, align='center', color='#66b447', label='Decrease',edgecolor='black')
    
        plt2.barh(pos, CO2_sensitivity_increase, align='center', color='#cc4b37', label='Increase',edgecolor='black')
        plt2.barh(pos, CO2_sensitivity_decrease, align='center', color='#66b447', label='Decrease',edgecolor='black')
    
        plt1.set_xlabel('Change in USD'); 
        plt1.set_title('Levelized Cost of DAC Sensitivity')   
    
        plt2.set_xlabel('Change in CO2 emissions per unit DAC'); 
        plt2.set_title('CO2 Intensity Sensitivity')
    
        plt1.set_yticks(pos)
        plt1.set_yticklabels(parameters)
        plt1.legend()
        plt1.grid(axis='x')
    
        plt2.legend()
        plt2.grid(axis='x')
        plt2.yaxis.set_ticks([])
         
        canvas = FigureCanvasTkAgg(figure, master=sensitivity_window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
                    
        plt.close(figure)
    
    calculate_button = tk.Button(sensitivity_frame, text="Calculate", font=bold_font, command=update_sensitivity)
    calculate_button.grid(row=0, column=9, padx=10, pady=5) 

    # close window command - closes only sensitivity chart child window
    def close_sensitivity_window():
        sensitivity_window.destroy()
        
    close_button = tk.Button(sensitivity_window, text="Close", command=close_sensitivity_window)
    close_button.pack(side=tk.BOTTOM, pady=10)


    return ()
 


# In[ ]:


# Launch parent/main interactive window for parameter input  
popup_window = tk.Tk()
bold_underline_font = tkfont.Font(family="Helvetica", size=10, weight="bold", underline=True)
popup_window.title("S-DAC Cost and CO2 Intensity Parameters");


# In[ ]:


# Parameter input window:
# Cost of Capital section
# Customizable range values
wacc_min = 0.1
wacc_max = 30
num_years_min = 1
num_years_max = 100

grid_row = 0

# Create a title label
title_label = tk.Label(popup_window, text="Economic Parameters", font=("Helvetica", 14, "bold"))
title_label.grid(row=grid_row, column=0, columnspan=3, padx=10, pady=10, sticky=tk.W)

# Create a Range column label
title_label = tk.Label(popup_window, text="Range", font=bold_underline_font)
title_label.grid(row=grid_row, column=3, columnspan=3, padx=10, pady=10, sticky=tk.W)

# Create labels for the inputs and range
wacc_label = tk.Label(popup_window, text="WACC")
wacc_label.grid(row=grid_row+1, column=0, padx=10, pady=5, sticky=tk.W)
wacc_range_label = tk.Label(popup_window, text="({:.1f} - {:.0f})".format(wacc_min, wacc_max))
wacc_range_label.grid(row=grid_row+1, column=3, padx=10, pady=5, sticky=tk.W)

num_years_label = tk.Label(popup_window, text="Number of Years (N)")
num_years_label.grid(row=grid_row+2, column=0, padx=10, pady=5, sticky=tk.W)
num_years_range_label = tk.Label(popup_window, text="({} - {})".format(num_years_min, num_years_max))
num_years_range_label.grid(row=grid_row+2, column=3, padx=10, pady=5, sticky=tk.W)

# Create entry boxes for the inputs
default_wacc = 10
default_num_years = 20

wacc_entry = tk.Entry(popup_window, width=10, justify=tk.RIGHT)
wacc_entry.insert(tk.END, default_wacc)
wacc_entry.grid(row=grid_row+1, column=1, padx=10, pady=5)

wacc_unit_label = tk.Label(popup_window, text="%")
wacc_unit_label.grid(row=grid_row+1, column=2, padx=0, pady=5, sticky=tk.W)

num_years_entry = tk.Entry(popup_window, width=10, justify=tk.RIGHT)
num_years_entry.insert(tk.END, default_num_years)
num_years_entry.grid(row=grid_row+2, column=1, padx=10, pady=5)

num_years_unit_label = tk.Label(popup_window, text="years")
num_years_unit_label.grid(row=grid_row+2, column=2, padx=0, pady=5, sticky=tk.W)

# Create a label to display the output
CRF_label = tk.Label(popup_window, text="FRF: ")
CRF_label.grid(row=grid_row+3, column=0, columnspan=2, padx=10, pady=5, sticky=tk.W)

# Set the output label to update continuously
wacc_entry.bind("<KeyRelease>", calculate_CRF)
num_years_entry.bind("<KeyRelease>", calculate_CRF)

calculate_CRF()  # Calculate initial CRF value based on default inputs


# In[ ]:


# Parameter input window:
# DAC inputs section
# Customizable range values
CAPEX_min = 100
CAPEX_max = 5000
OPEX_min = 10
OPEX_max = 500
elec_min = 100
elec_max = 5000
therm_min = 100
therm_max = 5000

grid_row = 5

# Create a title label
title_label = tk.Label(popup_window, text="DAC Technical Cost and Energy Parameters", font=("Helvetica", 14, "bold"))
title_label.grid(row=grid_row, column=0, columnspan=3, padx=10, pady=10, sticky=tk.W)

# Create labels for the inputs and range
CAPEX_label = tk.Label(popup_window, text="CAPEX")
CAPEX_label.grid(row=grid_row+1, column=0, padx=10, pady=5, sticky=tk.W)
CAPEX_range_label = tk.Label(popup_window, text="({:.0f} - {:.0f})".format(CAPEX_min, CAPEX_max))
CAPEX_range_label.grid(row=grid_row+1, column=3, padx=10, pady=5, sticky=tk.W)

OPEX_label = tk.Label(popup_window, text="OPEX")
OPEX_label.grid(row=grid_row+2, column=0, padx=10, pady=5, sticky=tk.W)
OPEX_range_label = tk.Label(popup_window, text="({:.0f} - {:.0f})".format(OPEX_min, OPEX_max))
OPEX_range_label.grid(row=grid_row+2, column=3, padx=10, pady=5, sticky=tk.W)

elec_label = tk.Label(popup_window, text="Electrical Energy")
elec_label.grid(row=grid_row+3, column=0, padx=10, pady=5, sticky=tk.W)
elec_range_label = tk.Label(popup_window, text="({:.0f} - {:.0f})".format(elec_min, elec_max))
elec_range_label.grid(row=grid_row+3, column=3, padx=10, pady=5, sticky=tk.W)

therm_label = tk.Label(popup_window, text="Thermal Energy")
therm_label.grid(row=grid_row+4, column=0, padx=10, pady=5, sticky=tk.W)
therm_range_label = tk.Label(popup_window, text="({:.0f} - {:.0f})".format(therm_min, therm_max))
therm_range_label.grid(row=grid_row+4, column=3, padx=10, pady=5, sticky=tk.W)

# Create entry boxes for the inputs
default_CAPEX = 1379
default_OPEX = 56
default_elec = 916
default_therm = 1447

CAPEX_entry = tk.Entry(popup_window, width=10, justify=tk.RIGHT)
CAPEX_entry.insert(tk.END, default_CAPEX)
CAPEX_entry.grid(row=grid_row+1, column=1, padx=10, pady=5)

CAPEX_unit_label = tk.Label(popup_window, text="USD per tonne CO2 capacity")
CAPEX_unit_label.grid(row=grid_row+1, column=2, padx=0, pady=5, sticky=tk.W)

OPEX_entry = tk.Entry(popup_window, width=10, justify=tk.RIGHT)
OPEX_entry.insert(tk.END, default_OPEX)
OPEX_entry.grid(row=grid_row+2, column=1, padx=10, pady=5)

OPEX_unit_label = tk.Label(popup_window, text="USD per tonne CO2")
OPEX_unit_label.grid(row=grid_row+2, column=2, padx=0, pady=5, sticky=tk.W)

elec_entry = tk.Entry(popup_window, width=10, justify=tk.RIGHT)
elec_entry.insert(tk.END, default_elec)
elec_entry.grid(row=grid_row+3, column=1, padx=10, pady=5)

elec_unit_label = tk.Label(popup_window, text="kWh_e per tonne CO2")
elec_unit_label.grid(row=grid_row+3, column=2, padx=0, pady=5, sticky=tk.W)

therm_entry = tk.Entry(popup_window, width=10, justify=tk.RIGHT)
therm_entry.insert(tk.END, default_therm)
therm_entry.grid(row=grid_row+4, column=1, padx=10, pady=5)

therm_unit_label = tk.Label(popup_window, text="kW_th per tonne CO2")
therm_unit_label.grid(row=grid_row+4, column=2, padx=0, pady=5, sticky=tk.W)


# In[ ]:


# Parameter input window:
# Regional factors section - Part 1
# Customizable range values

# NG_price - natural gas $/Mcf
# power_cost - electric power $/kWh
# power_co2intnesity - CO2 emissions per MWh
# CAPEX_mult = NG_price multiplier
# OPEX_mult - power_cost multiplier

NG_co2intensity = 0.194965384 # tonne CO2 per kWh_CAPEX_multal
NG_kWh_per_Mcf = 282.6142719


NG_price_min = 0.5
NG_price_max = 100
power_cost_min = 0.01
power_cost_max = 1
power_co2intensity_min = 0
power_co2intensity_max = 1
CAPEX_mult_min = 0.5
CAPEX_mult_max = 3
OPEX_mult_min = 0.5
OPEX_mult_max = 3

grid_row = 10

# Create a title label
title_label = tk.Label(popup_window, text="Regional Parameters", font=("Helvetica", 14, "bold"))
title_label.grid(row=grid_row, column=0, columnspan=3, padx=10, pady=10, sticky=tk.W)

# Create labels for the inputs and range
NG_price_label = tk.Label(popup_window, text="Natural Gas Price")
NG_price_label.grid(row=grid_row+1, column=0, padx=10, pady=5, sticky=tk.W)
NG_price_range_label = tk.Label(popup_window, text="({:.2f} - {:.2f})".format(NG_price_min, NG_price_max))
NG_price_range_label.grid(row=grid_row+1, column=3, padx=10, pady=5, sticky=tk.W)

power_cost_label = tk.Label(popup_window, text="Electricity Price")
power_cost_label.grid(row=grid_row+2, column=0, padx=10, pady=5, sticky=tk.W)
power_cost_range_label = tk.Label(popup_window, text="({:.2f} - {:.2f})".format(power_cost_min, power_cost_max))
power_cost_range_label.grid(row=grid_row+2, column=3, padx=10, pady=5, sticky=tk.W)

power_co2intensity_label = tk.Label(popup_window, text="CO2 Intensity of Electricity")
power_co2intensity_label.grid(row=grid_row+3, column=0, padx=10, pady=5, sticky=tk.W)
power_co2intensity_range_label = tk.Label(popup_window, text="({:.2f} - {:.2f})".format(power_co2intensity_min, power_co2intensity_max))
power_co2intensity_range_label.grid(row=grid_row+3, column=3, padx=10, pady=5, sticky=tk.W)

CAPEX_mult_label = tk.Label(popup_window, text="CAPEX Multiplier")
CAPEX_mult_label.grid(row=grid_row+4, column=0, padx=10, pady=5, sticky=tk.W)
CAPEX_mult_range_label = tk.Label(popup_window, text="({:.1f} - {:.1f})".format(CAPEX_mult_min, CAPEX_mult_max))
CAPEX_mult_range_label.grid(row=grid_row+4, column=3, padx=10, pady=5, sticky=tk.W)

OPEX_mult_label = tk.Label(popup_window, text="OPEX Multiplier")
OPEX_mult_label.grid(row=grid_row+5, column=0, padx=10, pady=5, sticky=tk.W)
OPEX_mult_range_label = tk.Label(popup_window, text="({:.1f} - {:.1f})".format(OPEX_mult_min, OPEX_mult_max))
OPEX_mult_range_label.grid(row=grid_row+5, column=3, padx=10, pady=5, sticky=tk.W)

# Create entry boxes for the inputs
default_NG_price = 5
default_power_cost = 0.15
default_power_co2intensity = 0.40
default_CAPEX_mult = 1.0
default_OPEX_mult = 1.0

NG_price_entry = tk.Entry(popup_window, width=10, justify=tk.RIGHT)
NG_price_entry.insert(tk.END, default_NG_price)
NG_price_entry.grid(row=grid_row+1, column=1, padx=10, pady=5)

NG_price_unit_label = tk.Label(popup_window, text="USD per McF")
NG_price_unit_label.grid(row=grid_row+1, column=2, padx=0, pady=5, sticky=tk.W)

power_cost_entry = tk.Entry(popup_window, width=10, justify=tk.RIGHT)
power_cost_entry.insert(tk.END, default_power_cost)
power_cost_entry.grid(row=grid_row+2, column=1, padx=10, pady=5)

power_cost_unit_label = tk.Label(popup_window, text="USD per kWh")
power_cost_unit_label.grid(row=grid_row+2, column=2, padx=0, pady=5, sticky=tk.W)

power_co2intensity_entry = tk.Entry(popup_window, width=10, justify=tk.RIGHT)
power_co2intensity_entry.insert(tk.END, default_power_co2intensity)
power_co2intensity_entry.grid(row=grid_row+3, column=1, padx=10, pady=5)

power_co2intensity_unit_label = tk.Label(popup_window, text="tonne CO2 emitted per MWh")
power_co2intensity_unit_label.grid(row=grid_row+3, column=2, padx=0, pady=5, sticky=tk.W)

CAPEX_mult_entry = tk.Entry(popup_window, width=10, justify=tk.RIGHT)
CAPEX_mult_entry.insert(tk.END, default_CAPEX_mult)
CAPEX_mult_entry.grid(row=grid_row+4, column=1, padx=10, pady=5)

CAPEX_mult_unit_label = tk.Label(popup_window, text="")
CAPEX_mult_unit_label.grid(row=grid_row+4, column=2, padx=0, pady=5, sticky=tk.W)

OPEX_mult_entry = tk.Entry(popup_window, width=10, justify=tk.RIGHT)
OPEX_mult_entry.insert(tk.END, default_OPEX_mult)
OPEX_mult_entry.grid(row=grid_row+5, column=1, padx=10, pady=5)

OPEX_mult_unit_label = tk.Label(popup_window, text="")
OPEX_mult_unit_label.grid(row=grid_row+5, column=2, padx=0, pady=5, sticky=tk.W)


# In[ ]:


# Parameter input window:
# Regional factors section - Part 2
# Customizable range values

# therm_index - Thermal energy multiplier due to avg humidity/temperature
# depth - depth of 120 degC formation
# temp_drawdown - steady state temperature drawdown over goetransport_indexal reservoir in degC
# transport - $ per tonne for 
# storage - $ per tonne for geological storage

therm_index_min = 0.5
therm_index_max = 1.8
depth_min = 3000
depth_max = 20000
temp_drawdown_min = 0
temp_drawdown_max = 39
transport_min = 1
transport_max = 50
storage_min = 5
storage_max = 50

grid_row = 15

# Create labels for the inputs and range
therm_index_label = tk.Label(popup_window, text="S-DAC Thermal Energy Multiplier")
therm_index_label.grid(row=grid_row+1, column=0, padx=10, pady=5, sticky=tk.W)
therm_index_range_label = tk.Label(popup_window, text="({:.1f} - {:.1f})".format(therm_index_min, therm_index_max))
therm_index_range_label.grid(row=grid_row+1, column=3, padx=10, pady=5, sticky=tk.W)

depth_label = tk.Label(popup_window, text="Geothermal Reservoir Depth")
depth_label.grid(row=grid_row+2, column=0, padx=10, pady=5, sticky=tk.W)
depth_range_label = tk.Label(popup_window, text="({:.0f} - {:.0f})".format(depth_min, depth_max))
depth_range_label.grid(row=grid_row+2, column=3, padx=10, pady=5, sticky=tk.W)

temp_drawdown_label = tk.Label(popup_window, text="Geothermal Reservoir Temperature Drawdown")
temp_drawdown_label.grid(row=grid_row+3, column=0, padx=10, pady=5, sticky=tk.W)
temp_drawdown_range_label = tk.Label(popup_window, text="({:.0f} - {:.0f})".format(temp_drawdown_min, temp_drawdown_max))
temp_drawdown_range_label.grid(row=grid_row+3, column=3, padx=10, pady=5, sticky=tk.W)

transport_label = tk.Label(popup_window, text="CO2 Transportation Cost")
transport_label.grid(row=grid_row+4, column=0, padx=10, pady=5, sticky=tk.W)
transport_range_label = tk.Label(popup_window, text="({:.0f} - {:.0f})".format(transport_min, transport_max))
transport_range_label.grid(row=grid_row+4, column=3, padx=10, pady=5, sticky=tk.W)

storage_label = tk.Label(popup_window, text="CO2 Storage Cost")
storage_label.grid(row=grid_row+5, column=0, padx=10, pady=5, sticky=tk.W)
storage_range_label = tk.Label(popup_window, text="({:.0f} - {:.0f})".format(storage_min, storage_max))
storage_range_label.grid(row=grid_row+5, column=3, padx=10, pady=5, sticky=tk.W)

# Create entry boxes for the inputs
default_therm_index = 1.0
default_depth = 10000
default_temp_drawdown = 10
default_transport = 10
default_storage = 10

therm_index_entry = tk.Entry(popup_window, width=10, justify=tk.RIGHT)
therm_index_entry.insert(tk.END, default_therm_index)
therm_index_entry.grid(row=grid_row+1, column=1, padx=10, pady=5)

therm_index_unit_label = tk.Label(popup_window, text="")
therm_index_unit_label.grid(row=grid_row+1, column=2, padx=0, pady=5, sticky=tk.W)

depth_entry = tk.Entry(popup_window, width=10, justify=tk.RIGHT)
depth_entry.insert(tk.END, default_depth)
depth_entry.grid(row=grid_row+2, column=1, padx=10, pady=5)

depth_unit_label = tk.Label(popup_window, text="ft")
depth_unit_label.grid(row=grid_row+2, column=2, padx=0, pady=5, sticky=tk.W)

temp_drawdown_entry = tk.Entry(popup_window, width=10, justify=tk.RIGHT)
temp_drawdown_entry.insert(tk.END, default_temp_drawdown)
temp_drawdown_entry.grid(row=grid_row+3, column=1, padx=10, pady=5)

temp_drawdown_unit_label = tk.Label(popup_window, text="degC")
temp_drawdown_unit_label.grid(row=grid_row+3, column=2, padx=0, pady=5, sticky=tk.W)

transport_entry = tk.Entry(popup_window, width=10, justify=tk.RIGHT)
transport_entry.insert(tk.END, default_transport)
transport_entry.grid(row=grid_row+4, column=1, padx=10, pady=5)

transport_unit_label = tk.Label(popup_window, text="USD per tonne CO2")
transport_unit_label.grid(row=grid_row+4, column=2, padx=0, pady=5, sticky=tk.W)

storage_entry = tk.Entry(popup_window, width=10, justify=tk.RIGHT)
storage_entry.insert(tk.END, default_storage)
storage_entry.grid(row=grid_row+5, column=1, padx=10, pady=5)

storage_unit_label = tk.Label(popup_window, text="USD per tonne CO2")
storage_unit_label.grid(row=grid_row+5, column=2, padx=0, pady=5, sticky=tk.W)


# In[ ]:


# Display three control buttons at bottom
# First launches bar-shart child window
# Second launches sensitivity chart child window
# Third closes main window and terminates program
grid_row = 21

display_button = tk.Button(popup_window, text="Display Chart", command=create_bar_charts)
display_button.grid(row=grid_row, column=0, columnspan=1, padx=10, pady=10)

display_button = tk.Button(popup_window, text="Calculate S-DAC-GT Sensitivity", command=sensitivity_analysis)
display_button.grid(row=grid_row, column=1, columnspan=1, padx=10, pady=10)

close_button = tk.Button(popup_window, text="Close", command=close_window)
close_button.grid(row=grid_row, column=2, columnspan=1, padx=10, pady=10)

popup_window.mainloop()


# In[ ]:




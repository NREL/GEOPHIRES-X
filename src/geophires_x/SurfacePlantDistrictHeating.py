import os
import numpy as np
import pandas as pd
from geophires_x.OptionList import PlantType
from geophires_x.Parameter import floatParameter, intParameter, strParameter, OutputParameter
from geophires_x.SurfacePlant import SurfacePlant
from geophires_x.Units import *
import geophires_x.Model as Model


class SurfacePlantDistrictHeating(SurfacePlant):
    def __init__(self, model: Model):
        """
        The __init__ function is called automatically when a class is instantiated.
        It initializes the attributes of an object, and sets default values for certain arguments that can be overridden
         by user input.
        The __init__ function is used to set up all the parameters in the Surfaceplant.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """

        model.logger.info(f"Init {self.__class__.__name__}: {__name__}")
        super().__init__(model)  # this calls the __init__ function of the superclass, which is SurfacePlant

        # Set up all the Parameters that will be predefined by this class using the different types of parameter classes.
        # Setting up includes giving it a name, a default value, The Unit Type (length, volume, temperature, etc.) and
        # Unit Name of that value, sets it as required (or not), sets allowable range, the error message if that range
        # is exceeded, the ToolTip Text, and the name of teh class that created it.
        # This includes setting up temporary variables that will be available to all the class but noy read in by user,
        # or used for Output
        # This also includes all Parameters that are calculated and then published using the Printouts function.

        # These dictionaries contain a list of all the parameters set in this object, stored as "Parameter" and
        # "OutputParameter" Objects.  This will allow us later to access them in a user interface and get that list,
        # along with unit type, preferred units, etc.

        # local variable initialization
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = os.path.abspath(__file__)

        self.dh_demand_option = self.ParameterDict[self.dh_demand_option.Name] = intParameter(
            "District Heating Demand Option",
            value=1,
            AllowableRange=[1, 2],
            UnitType=Units.NONE,
            ErrMessage="assume default district heating demand option (1: known heat demand profile)",
            ToolTipText="Select the method to provide the district heating demand to GEOPHIRES"
        )
        self.dh_demand_filename = self.ParameterDict[self.dh_demand_filename.Name] = strParameter(
            "District Heating Demand File Name",
            value='HeatDemand.csv',
            UnitType=Units.NONE,
            ErrMessage="assume default district heating demand filename (HeatDemand.csv)",
            ToolTipText="Provide district heating demand in csv file in MW or MWh per day (if district heating demand option is set to 1)"
        )
        self.dh_demand_time_resolution = self.ParameterDict[self.dh_demand_time_resolution.Name] = intParameter(
            "District Heating Demand Data Time Resolution",
            value=1,
            AllowableRange=[1, 2],
            UnitType=Units.NONE,
            ErrMessage="assume default district heating data time resolution (1: hourly data)",
            ToolTipText="Provide time interval for thermal demand data: 1 = hourly (data provided as MW = MWh' 2 = daily (data provided as MWh/day) (if district heating demand option is set to 1)"
        )
        self.dh_demand_data_column_number = self.ParameterDict[self.dh_demand_data_column_number.Name] = intParameter(
            "District Heating Demand Data Column Number",
            value=2,
            AllowableRange=list(range(1, 101, 1)),
            UnitType=Units.NONE,
            ErrMessage="assume default district heating demand data column number (2)",
            ToolTipText="Select the column number of the hourly or daily data in the district heating demand csv file (if district heating demand option is set to 1)"
        )
        self.dh_temperature_filename = self.ParameterDict[self.dh_temperature_filename.Name] = strParameter(
            "Temperature File Name",
            value='Temperature.csv',
            UnitType=Units.NONE,
            ErrMessage="assume default temperature filename (Temperature.csv)",
            ToolTipText="Provide filename of temperature file with hourly temperature to calculate district heating demand (if district heating demand option is set to 2)"
        )
        self.dh_temperature_data_column_number = self.ParameterDict[
            self.dh_temperature_data_column_number.Name] = intParameter(
            "Temperature Data Column Number",
            value=2,
            AllowableRange=list(range(1, 101, 1)),
            UnitType=Units.NONE,
            ErrMessage="assume default temperature data column number (2)",
            ToolTipText="Select the column number of the hourly temperature data in the temperature csv file (if district heating demand option is set to 2)"
        )
        self.dh_number_of_housing_units = self.ParameterDict[self.dh_number_of_housing_units.Name] = intParameter(
            "Number of Housing Units",
            value=100,
            AllowableRange=list(range(0, 1000000, 1)),
            UnitType=Units.NONE,
            ErrMessage="assume default number of housing units (100)",
            ToolTipText="Specify the number of housing units to calculate district heating demand (if district heating demand option is set to 2)"
        )
        self.dh_constant_anchor_demand = self.ParameterDict[self.dh_constant_anchor_demand.Name] = floatParameter(
            "Constant Anchor Demand",
            value=0.0,
            Min=0.0,
            Max=100.0,
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW,
            ErrMessage="assume default constant anchor demand (10 MWth)",
            ToolTipText="Specify the constant anchor demand to calculate the district heating demand (if district heating demand option is set to 2)"
        )
        self.dh_us_census_division = self.ParameterDict[self.dh_us_census_division.Name] = intParameter(
            "US Census Division",
            value=1,
            AllowableRange=[1, 2, 3, 4, 5, 6, 7, 8, 9],
            UnitType=Units.NONE,
            ErrMessage="assume default U.S. census division (1)",
            ToolTipText="Select the U.S. census division to calculate district heating demand (if district heating demand option is set to 2)"
            )

        # Results - used by other objects or printed in output downstream
        self.hourly_heating_demand = self.OutputParameterDict[self.hourly_heating_demand.Name] = OutputParameter(
            Name="Hourly Heating Demand",
            UnitType=Units.ENERGYFREQUENCY,
            PreferredUnits=EnergyFrequencyUnit.MWhPERHOUR,
            CurrentUnits=EnergyFrequencyUnit.MWhPERHOUR
        )
        self.daily_heating_demand = self.OutputParameterDict[self.daily_heating_demand.Name] = OutputParameter(
            Name="Daily Heating Demand",
            UnitType=Units.ENERGYFREQUENCY,
            PreferredUnits=EnergyFrequencyUnit.MWhPERDAY,
            CurrentUnits=EnergyFrequencyUnit.MWhPERDAY
        )
        self.annual_heating_demand = self.OutputParameterDict[self.annual_heating_demand.Name] = OutputParameter(
            Name="Annual Heating Demand",
            UnitType=Units.ENERGYFREQUENCY,
            PreferredUnits=EnergyFrequencyUnit.GWhPERYEAR,
            CurrentUnits=EnergyFrequencyUnit.GWhPERYEAR
        )
        self.util_factor_array = self.OutputParameterDict[self.util_factor_array.Name] = OutputParameter(
            Name="Utilisation Factor Array",
            UnitType=Units.NONE
        )
        self.annual_ng_demand = self.OutputParameterDict[self.annual_ng_demand.Name] = OutputParameter(
            Name="Annual Peaking Boiler Natural Gas Demand",
            UnitType=Units.ENERGYFREQUENCY,
            PreferredUnits=EnergyFrequencyUnit.MWhPERYEAR,
            CurrentUnits=EnergyFrequencyUnit.MWhPERYEAR
        )
        self.max_peaking_boiler_demand = self.OutputParameterDict[
            self.max_peaking_boiler_demand.Name] = OutputParameter(
            Name="Maximum Peaking Boiler Natural Gas Demand",
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )
        self.dh_geothermal_heating = self.OutputParameterDict[self.dh_geothermal_heating.Name] = OutputParameter(
            Name="Instantaneous Geothermal Heating Over Lifetime",
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )
        self.dh_natural_gas_heating = self.OutputParameterDict[self.dh_natural_gas_heating.Name] = OutputParameter(
            Name="Instantaneous Natural Gas Heating Over Lifetime",
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )
        model.logger.info(f"Complete {self.__class__.__name__}: {__name__}")

    def __str__(self):
        return "SurfacePlantDistrictHeating"

    def read_parameters(self, model: Model) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary and stores them in the parameters.
        It also handles special cases that need to be handled after a value has been read in and checked.
        If you choose to subclass this master class, you can also choose to override this method (or not), and if you do
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: None
        """
        model.logger.info(f"Init {self.__class__.__name__}: {__name__}")
        super().read_parameters(model)  # this calls the read_parameters function of the superclass, which is SurfacePlant
        # Since there are no parameters that require unique adjustments in this class, we don't need to do anything.
        model.logger.info(f"Complete {self.__class__.__name__}: {__name__}")

    def Calculate(self, model: Model) -> None:
        """
        The Calculate function is where all the calculations are done.
        This function can be called multiple times, and will only recalculate what has changed each time it is called.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing, but it does make calculations and set values in the model
        """
        model.logger.info(f"Init {self.__class__.__name__}: {__name__}")

        # This is where all the calculations are made using all the values that have been set.
        # If you subclass this class, you can choose to run these calculations before (or after) your calculations,
        # but that assumes you have set all the values that are required for these calculations
        # If you choose to subclass this master class, you can also choose to override this method (or not),
        # and if you do, do it before or after you call you own version of this method.  If you do, you can also choose
        # to call this method from you class, which can effectively run the calculations of the superclass, making all
        # the values available to your methods. but you had better have set all the parameters!

        # useful direct-use heat provided to district heating network [MWth]
        # heat extracted from geofluid [MWth]
        self.HeatExtracted.value = model.wellbores.nprod.value * model.wellbores.prodwellflowrate.value * model.reserv.cpwater.value * (
            model.wellbores.ProducedTemperature.value - model.wellbores.Tinj.value) / 1E6
        self.HeatProduced.value = self.HeatExtracted.value * self.enduse_efficiency_factor.value

        [self.util_factor_array.value, self.utilization_factor.value, self.annual_ng_demand.value,
         self.max_peaking_boiler_demand.value, self.dh_geothermal_heating.value,
         self.dh_natural_gas_heating.value] = self.calc_util_factor(self.HeatProduced.value, model.economics.timestepsperyear.value)
        self.annual_heating_demand.value = np.sum(self.daily_heating_demand.value) / 1000  # GWh/year

        # Calculate annual electricity/heat production
        # all end-use options have "heat extracted from reservoir" and pumping kWs
        self.HeatkWhExtracted.value = np.zeros(self.plant_lifetime.value)
        self.PumpingkWh.value = np.zeros(self.plant_lifetime.value)

        for i in range(0, self.plant_lifetime.value):
            if self.plant_type.value == PlantType.DISTRICT_HEATING:  # for district heating, we have a util_factor_array
                self.HeatkWhExtracted.value[i] = np.trapz(self.HeatExtracted.value[
                                                          (0 + i * model.economics.timestepsperyear.value):((
                                                           i + 1) * model.economics.timestepsperyear.value) + 1],
                                                          dx=1. / model.economics.timestepsperyear.value * 365. * 24.) * 1000. * \
                                                 self.util_factor_array.value[i]
                self.PumpingkWh.value[i] = np.trapz(model.wellbores.PumpingPower.value[
                                                    (0 + i * model.economics.timestepsperyear.value):((
                                                    i + 1) * model.economics.timestepsperyear.value) + 1],
                                                    dx=1. / model.economics.timestepsperyear.value * 365. * 24.) * 1000. * \
                                           self.util_factor_array.value[i]
            else:
                self.HeatkWhExtracted.value[i] = np.trapz(self.HeatExtracted.value[
                                                          (0 + i * model.economics.timestepsperyear.value):((
                                                          i + 1) * model.economics.timestepsperyear.value) + 1],
                                                          dx=1. / model.economics.timestepsperyear.value * 365. * 24.) * 1000. * self.utilization_factor.value
                self.PumpingkWh.value[i] = np.trapz(model.wellbores.PumpingPower.value[
                                                    (0 + i * model.economics.timestepsperyear.value):((
                                                    i + 1) * model.economics.timestepsperyear.value) + 1],
                                                    dx=1. / model.economics.timestepsperyear.value * 365. * 24.) * 1000. * self.utilization_factor.value

        self.HeatkWhProduced.value = np.zeros(self.plant_lifetime.value)
        for i in range(0, self.plant_lifetime.value):
            self.HeatkWhProduced.value[i] = np.trapz(self.HeatProduced.value[
                                                     (0 + i * model.economics.timestepsperyear.value):((
                                                     i + 1) * model.economics.timestepsperyear.value) + 1],
                                                     dx=1. / model.economics.timestepsperyear.value * 365. * 24.) * 1000. * \
                                                     self.util_factor_array.value[i]

        # calculate reservoir heat content
        self.RemainingReservoirHeatContent.value = SurfacePlant.remaining_reservoir_heat_content(
            self, model.reserv.InitialReservoirHeatContent.value, self.HeatkWhExtracted.value)

        model.logger.info(f"Complete {self.__class__.__name__}: {__name__}")

    # district heating routines below
    def CalculateDHDemand(self, model: Model) -> None:
        """
        Calculate the direct Heat demand of the district heating system based on the number of housing units and the census division
        :param model: the model
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        # calculate heating demand for a district heating system
        model.logger.info(f"Init {self.__class__.__name__}: {__name__}")

        if self.dh_demand_option.value == 1:  # user provides district heating demand using csv file
            # obtain daily heating demand from csv file
            self.daily_heating_demand.value = self.read_daily_demand(self.dh_demand_filename.value,
                                                                     self.dh_demand_data_column_number.value,
                                                                     self.dh_demand_time_resolution.value)
            if self.dh_demand_time_resolution.value == 1:
                # if time interval is 1 hour, also store hourly heating demand
                self.hourly_heating_demand.value = self.read_csv(self.dh_demand_filename.value,
                                                                 self.dh_demand_data_column_number.value)

        elif self.dh_demand_option.value == 2:  # calculate thermal demand from TMY and HDD
            self.daily_heating_demand.value = self.calculate_dh_demand(self.dh_number_of_housing_units.value,
                                                                       self.dh_us_census_division.value,
                                                                       self.dh_constant_anchor_demand.value,
                                                                       self.dh_temperature_filename.value,
                                                                       self.dh_temperature_data_column_number.value)

    def read_daily_demand(self, demand_file_name, demand_data_column, time_interval) -> np.array:
        """
        Read the daily demand data column from the csv file and return the daily demand in MWh/day
        :param demand_file_name: the name of the csv file
        :type demand_file_name: str
        :param demand_data_column: the column number of the demand data
        :type demand_data_column: int
        :param time_interval: the time interval of the demand data;
            1: hourly data, units in MW or MWh (both are treated equivalent)
            2: daily data, units in MWh
        :type time_interval: int
        :return: numpy array of daily demand in MWh/day
        :rtype: numpy array
        """
        demand = np.empty(0)  # create an empty np array for daily demand
        if time_interval == 1:  # hourly data
            hourly_demand = self.read_csv(demand_file_name, demand_data_column)
            year_hour = 0
            for day in range(0, 365):  # iterate through each day of the year
                D_sum = 0
                for hour in range(0, 24):  # iterate through hours of each day
                    D_sum += hourly_demand[year_hour]
                    year_hour += 1
                demand = np.append(demand, D_sum)
        elif time_interval == 2:  # directly read in the daily values
            np.demand = self.read_csv(demand_file_name, demand_data_column)
        return demand

    def read_csv(self, file_name, data_column) -> np.array:  # data_column starts from 1
        # Extract data from CSV file
        Data = pd.read_csv(file_name)  # Read csv data using pandas to dataframe
        data_column -= 1  # change index to start at 0 instead of 1
        data_array = Data.iloc[:, data_column].to_numpy()  # Extract data and convert to numpy array [s]
        return data_array

    def calculate_dh_demand(self, households, census_division, constant_demand, temp_file_name, temp_data_column) -> np.array:
        """
        :param households: Number of households in the district heating system
        :type households: int
        :param census_division: 1-9, see manual or descriptions below for options
        :type: census_division: int
        :param constant_demand : constant known demand in MW (do not include residential water heating)
        :type constant_demand : float
        :param temp_file_name : name of the hourly temperature profile CSV file to read
        :type temp_file_name : string
        :param temp_data_column : column number of temperature data, starting from 1
        :type temp_data_column : int
        :return: numpy array of hourly and daily thermal demand
        :rtype: numpy array
        """
        # read in hourly temperature data
        hourly_temperature = self.read_csv(temp_file_name, temp_data_column)

        # obtain HDD : 1 x 365 numpy array
    # Heating degree days for each day of the year as calculated in calc_HDD
        daily_HDD = self.calc_HDD(hourly_temperature)

        # space and water heating demand intensity values by census division
        # default is New England
        heat_intensity = 2.773  # KWh/household/HDD
        water_intensity = 13.56  # KWh/household/day
        if census_division == 2:  # middle atlantic
            heat_intensity = 2.727
            water_intensity = 13.97
        elif census_division == 3:  # east north central
            heat_intensity = 2.650
            water_intensity = 14.24
        elif census_division == 4:  # west north central
            heat_intensity = 2.266
            water_intensity = 13.19
        elif census_division == 5:  # south atlantic
            heat_intensity = 2.583
            water_intensity = 10.35
        elif census_division == 6:  # east south central
            heat_intensity = 2.033
            water_intensity = 11.01
        elif census_division == 7:  # west south central
            heat_intensity = 2.872
            water_intensity = 10.35
        elif census_division == 8:  # mountain
            heat_intensity = 2.027
            water_intensity = 13.14
        elif census_division == 9:  # pacific
            heat_intensity = 1.845
            water_intensity = 12.41

        demand = np.empty(0) # create an empty np array for daily demand
        for day in daily_HDD:
            # MWh/day
            demand = np.append(demand, households * (heat_intensity * day + water_intensity) / 1000 + constant_demand * 24)

        return demand

    def calc_HDD(self, hourly_temp) -> np.array:
        """
        calculate heating-degree-days (HDD) per day from a one-year hourly temperature file, deg. C only
        :param hourly_temp: 8760 hourly temperature data in deg. C
        :type hourly_temp: numpy array
        :return: numpy array of heating degree days
        :rtype: numpy array
        """
        T_mean = np.zeros(8760)  # create an empty np array for daily mean temp
        HDD = np.empty(0) # create an empty np array for heating degree days
        year_hour = 0  # counting variable for dataset (hours from 1 to 8760)
        for day in range(0, 365):  # iterate through each day of the year
            T_sum = 0  # temporary summing variable for degrees in a day
            for hour in range(0, 24):  # loop over the hours of a single day
                T_sum += hourly_temp[year_hour]  # sum the temperatures within a single day
                year_hour += 1  # advance the indexing variable
            T_mean[day] = T_sum / 24  # calculate the mean temp for the day
            if T_mean[day] < 18.3:  # check whether heating was required for day
                HDD = np.append(HDD, 18.3 - T_mean[day])  # calculate HDD if heating was required
            else:
                HDD = np.append(HDD, 0)  # record a 0 if no heating was required

        return HDD

    def calc_util_factor(self, heat_produced, time_steps_per_year):
        util_factor_array = np.zeros(self.plant_lifetime.value)  # [-]
        annual_ng_demand = np.zeros(self.plant_lifetime.value)  # MWh per year
        instantaneous_peaking_boiler_demand = np.zeros(self.plant_lifetime.value * 365)
        actual_geothermal_used = np.zeros(self.plant_lifetime.value * 365)
        current_heat_output_stored = np.zeros(self.plant_lifetime.value * 365)

        for i in range(0, self.plant_lifetime.value):
            for j in range(0, 365):
                # compare thermal demand with supply
                current_index = i * 365 + j
                current_time = i + j / 365
                xp = np.arange(0, self.plant_lifetime.value + 0.01, 1 / time_steps_per_year)
                fp = heat_produced
                xp = xp[:len(fp)]
                current_heat_output = np.interp(current_time, xp, fp)
#                current_heat_output = np.interp(current_time, np.arange(0, self.plant_lifetime.value + 0.01, 1 / time_steps_per_year), heat_produced)
                current_heat_output_stored[current_index] = current_heat_output
                if self.daily_heating_demand.value[j] / 24 > current_heat_output:
                    actual_geothermal_used[current_index] = current_heat_output
                    instantaneous_peaking_boiler_demand[current_index] = self.daily_heating_demand.value[j] / 24 - current_heat_output
                else:
                    actual_geothermal_used[current_index] = self.daily_heating_demand.value[j] / 24
            annual_ng_demand[i] = np.sum(instantaneous_peaking_boiler_demand[i * 365:(i + 1) * 365]) * 24  # MWh/year
            util_factor_array[i] = np.sum(actual_geothermal_used[i * 365:(i + 1) * 365]) / np.sum(current_heat_output_stored[i * 365:(i + 1) * 365])

        util_factor = np.sum(actual_geothermal_used) / np.sum(current_heat_output_stored)
        if np.max(instantaneous_peaking_boiler_demand) > 0:
            # max instantaneous peaking boiler demand in MW
            # assuming it must meet peak demand day running for 20 hours in that day
            max_peaking_boiler_demand = np.max(instantaneous_peaking_boiler_demand) / 20 * 24
        else:
            max_peaking_boiler_demand = 0

        return [util_factor_array, util_factor, annual_ng_demand, max_peaking_boiler_demand, actual_geothermal_used, instantaneous_peaking_boiler_demand]

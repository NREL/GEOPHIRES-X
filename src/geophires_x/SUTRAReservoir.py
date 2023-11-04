import sys
from .Parameter import strParameter, OutputParameter
from .Units import *
import geophires_x.Model as Model
from .Reservoir import Reservoir
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np


class SUTRAReservoir(Reservoir):
    """
    This class reads in the output of a simulation with SUTRA.
    """
    def __init__(self, model: Model):
        """
        The __init__ function is called automatically when a class is instantiated.
        It initializes the attributes of an object, and sets default values for certain arguments that can be overridden
        by user input.
        :param self: Store data that will be used by the class
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: None
        :doc-author: Malcolm Ross
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)
        super().__init__(model)   # initialize the parent parameters and variables
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>","")

        # Set up all the Parameters that will be predefined by this class using the different types of parameter classes.
        # Setting up includes giving it a name, a default value, The Unit Type (length, volume, temperature, etc.) and
        # Unit Name of that value, sets it as required (or not), sets allowable range, the error message if that range
        # is exceeded, the ToolTip Text, and the name of teh class that created it.
        # This includes setting up temporary variables that will be available to all the class but noy read in by user,
        # or used for Output
        # This also includes all Parameters that are calculated and then published using the Printouts function.
        # If you choose to subclass this master class, you can do so before or after you create your own parameters.
        # If you do, you can also choose to call this method from you class, which will effectively add and set all
        # these parameters to your class.
        # specific to this class:

        self.sutraannualheatfilename = self.ParameterDict[self.sutraannualheatfilename.Name] = strParameter(
            "SUTRA Annual Heat File Name",
            value='annual_heat.csv',
            UnitType=Units.NONE,
            ErrMessage="assume default SUTRA annual heat output file name (annual_heat.csv)",
            ToolTipText="SUTRA file with heat stored, heat supplied and efficiency for each year"
        )

        self.sutraheatbudgetfilename = self.ParameterDict[self.sutraheatbudgetfilename.Name] = strParameter(
            "SUTRA Heat Budget File Name",
            value='heat_budget.csv',
            UnitType=Units.NONE,
            ErrMessage="assume default SUTRA heat budget output file name (heat_budget.csv)",
            ToolTipText="SUTRA file with target heat and simulated heat for each SUTRA time step over lifetime"
        )

        self.sutrabalanceandstoragewelloutputfilename = self.ParameterDict[self.sutrabalanceandstoragewelloutputfilename.Name] = strParameter(
            "SUTRA Balance and Storage Well Output File Name",
            value='annual_heat.csv',
            UnitType=Units.NONE,
            ErrMessage="assume default SUTRA balance and storage well output file name (balance_and_storage_well_output.csv)",
            ToolTipText="SUTRA file with well flow rate and temperature for each SUTRA time step over lifetime"
        )

        self.AnnualHeatStored = self.OutputParameterDict[self.AnnualHeatStored.Name] = OutputParameter(
            Name="SUTRA Annual Heat Stored",
            value=[],
            UnitType=Units.ENERGY,
            PreferredUnits=EnergyUnit.GWH,
            CurrentUnits=EnergyUnit.GWH
        )

        self.AnnualHeatSupplied = self.OutputParameterDict[self.AnnualHeatSupplied.Name] = OutputParameter(
            Name="SUTRA Annual Heat Supplied",
            value=[],
            UnitType=Units.ENERGY,
            PreferredUnits=EnergyUnit.GWH,
            CurrentUnits=EnergyUnit.GWH
        )

        self.AnnualRTESEfficiency = self.OutputParameterDict[self.AnnualRTESEfficiency.Name] = OutputParameter(
            Name="SUTRA Annual Round-Trip Heat Efficiency",
            value=[],
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.PERCENT,
            CurrentUnits=PercentUnit.PERCENT
        )

        self.TimeProfile = self.OutputParameterDict[self.TimeProfile.Name] = OutputParameter(
            Name="SUTRA Target Heat Profile",
            value=[],
            UnitType=Units.TIME,
            PreferredUnits=TimeUnit.HOUR,
            CurrentUnits=TimeUnit.HOUR
        )

        self.TargetHeat = self.OutputParameterDict[self.TargetHeat.Name] = OutputParameter(
            Name="SUTRA Target Heat Profile",
            value=[],
            UnitType=Units.ENERGY,
            PreferredUnits=EnergyUnit.KWH,
            CurrentUnits=EnergyUnit.KWH
        )

        self.SimulatedHeat = self.OutputParameterDict[self.SimulatedHeat.Name] = OutputParameter(
            Name="SUTRA Simulated Heat Profile",
            value=[],
            UnitType=Units.ENERGY,
            PreferredUnits=EnergyUnit.KWH,
            CurrentUnits=EnergyUnit.KWH
        )

        self.StorageWellFlowRate = self.OutputParameterDict[self.StorageWellFlowRate.Name] = OutputParameter(
            Name="SUTRA Storage Well Flow Rate Profile",
            value=[],
            UnitType=Units.FLOWRATE,
            PreferredUnits=FlowRateUnit.KGPERSEC,
            CurrentUnits=FlowRateUnit.KGPERSEC
        )

        self.BalanceWellFlowRate = self.OutputParameterDict[self.BalanceWellFlowRate.Name] = OutputParameter(
            Name="SUTRA Balance Well Flow Rate Profile",
            value=[],
            UnitType=Units.FLOWRATE,
            PreferredUnits=FlowRateUnit.KGPERSEC,
            CurrentUnits=FlowRateUnit.KGPERSEC
        )

        self.StorageWellTemperature = self.OutputParameterDict[self.StorageWellTemperature.Name] = OutputParameter(
            Name="SUTRA Storage Well Temperature Profile",
            value=[],
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS
        )

        self.BalanceWellTemperature = self.OutputParameterDict[self.BalanceWellTemperature.Name] = OutputParameter(
            Name="SUTRA Balance Well Temperature Profile",
            value=[],
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS
        )

        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def __str__(self):
        return "UPPReservoir"

    def read_parameters(self, model:Model) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary created by reading the user-provided file
        and updates the parameter values for this object.

        The function reads in all the parameters that relate to this object, including those that are inherited from
        other objects. It then updates any of these parameter values that have been changed by the user.
        It also handles any special cases.
        :param self: Reference the class instance (such as it is) from within the class
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: None
        :doc-author: Malcolm Ross
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)
        super().read_parameters(model)    # read the parameters for the parent.
        # if we call super, we don't need to deal with setting the parameters here, just deal with the special cases
        # for the variables in this class
        # because the call to the super.readparameters will set all the variables, including the ones that are specific
        # to this class

        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def Calculate(self, model: Model):
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)
        super().Calculate(model)    # run calculations for the parent.

        # Read in SUTRA simulation output
        try:
            data = pd.read_csv(self.sutraannualheatfilename.value)
            self.AnnualHeatStored.value = data[['Heat Stored (J)']].to_numpy()/3.6e12
            self.AnnualHeatSupplied.value = data[['Heat Supplied (J)']].to_numpy()/3.6e12
            self.AnnualRTESEfficiency.value = data[['Efficiency (%)']].to_numpy()

            data = pd.read_csv(self.sutraheatbudgetfilename.value)
            self.TimeProfile.value = data[['Time (hrs)']].to_numpy()
            self.TargetHeat.value = data[['Target Heat (J)']].to_numpy()/3.6e6
            self.SimulatedHeat.value = data[['Simulated Heat (J)']].to_numpy()/3.6e6

            data = pd.read_csv(self.sutrabalanceandstoragewelloutputfilename.value)
            self.StorageWellFlowRate.value = data[['Storage Well Q(kg/s)']].to_numpy()
            self.BalanceWellFlowRate.value = data[['Balance Well Q(kg/s)']].to_numpy()
            self.StorageWellTemperature.value = data[['Storage Well T(C)']].to_numpy()
            self.BalanceWellTemperature.value = data[['Balance Well T(C)']].to_numpy()
        except:
            model.logger.critical('Error: GEOPHIRES could not read SUTRA output results and will abort simulation')
            print('Error: GEOPHIRES could not read SUTRA output results and will abort simulation')
            sys.exit()

        # clean up SUTRA simulation output and store in GEOPHIRES reservoir arrays
        model.reserv.timevector.value = self.TimeProfile.value[0:-1:2,0]
        model.reserv.Tresoutput.value = self.StorageWellTemperature.value[0:-1:2,0]


        #create plots of imported SUTRA data

        plt.close('all')
        plt.figure(1)
        year = np.arange(1, 31, 1)  # make an array of days for plot x-axis
        plt.plot(year, abs(self.AnnualHeatStored.value[:,0]), label='Annual Heat Stored')
        plt.plot(year, abs(self.AnnualHeatSupplied.value[:, 0]), label='Annual Heat Supplied')
        plt.xlabel('Year')
        plt.ylabel('Annual Heat Balance [GWh/year]')
        #plt.ylim([0, max(model.surfaceplant.dailyheatingdemand.value) * 1.05])
        plt.legend()
        plt.title('SUTRA Heat Balance')
        plt.show(block=False)

        plt.figure(2)
        plt.plot(self.TimeProfile.value[0:-1:2,0], self.TargetHeat.value[0:-1:2,0], label='Target Heat')
        plt.plot(self.TimeProfile.value[0:-1:2,0], self.SimulatedHeat.value[0:-1:2,0], label='Simulated Heat')
        plt.xlabel('Hour')
        plt.ylabel('Heat Exchange [kWh]')
        #plt.ylim([0, max(model.surfaceplant.dailyheatingdemand.value) * 1.05])
        plt.legend()
        plt.title('SUTRA Target and Simulated Heat')
        plt.show(block=False)

        plt.figure(3)
        plt.plot(self.TimeProfile.value[0:-1:2,0], self.StorageWellFlowRate.value[0:-1:2,0], label='Storage Well Flow Rate')
        plt.plot(self.TimeProfile.value[0:-1:2,0], self.BalanceWellFlowRate.value[0:-1:2,0], label='Balance Well Flow Rate')
        plt.xlabel('Hour')
        plt.ylabel('Flow Rate [kg/s]')
        #plt.ylim([0, max(model.surfaceplant.dailyheatingdemand.value) * 1.05])
        plt.legend()
        plt.title('SUTRA Well Flow Rates')
        plt.show(block=False)

        plt.figure(4)
        plt.plot(self.TimeProfile.value[0:-1:2, 0], self.StorageWellTemperature.value[0:-1:2, 0], label='Storage Well Temperature')
        plt.plot(self.TimeProfile.value[0:-1:2, 0], self.BalanceWellTemperature.value[0:-1:2, 0], label='Balance Well Temperature')
        plt.xlabel('Hour')
        plt.ylabel('Temperature [C]')
        # plt.ylim([0, max(model.surfaceplant.dailyheatingdemand.value) * 1.05])
        plt.legend()
        plt.title('SUTRA Well Temperatures')
        plt.show(block=False)

        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

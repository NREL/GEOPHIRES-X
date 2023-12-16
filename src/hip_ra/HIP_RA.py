from __future__ import annotations
import traceback
import logging
import logging.config
import os

from geophires_x.GeoPHIRESUtils import read_input_file, EntropyH20_func, EnthalpyH20_func, DensityWater, \
    HeatCapacityWater, RecoverableHeat, UtilEff_func
from geophires_x.Parameter import *
from geophires_x.Units import *
from geophires_x.Parameter import LookupUnits, ReadParameter
"""
Heat in Place calculation: Muffler, P., and Raffaele Cataldi.
"Methods for regional assessment of geothermal resources."
Geothermics 7.2-4 (1978): 53-89.
and: Garg, S.K. and J. Combs. 2011.  A Reexamination of the USGS Volumetric "Heat in Place" Method.
Stanford University, 36th Workshop on Geothermal Reservoir Engineering; SGP-TR-191, 5 pp.
build date: September 2023
Created on Monday Nov 28 08:54 2022

@author: Malcolm Ross V1
"""


class HIP_RA:
    """
    HIP_RA is the container class of the HIP_RA application, giving access to everything else, including the logger
    """

    def __init__(self, enable_geophires_logging_config=True):
        """
        The __init__ function is called automatically every time the class is being used to create a new object.
        The self parameter is a Python convention. It must be included in each function definition and points to the
        current instance of the class (the object that is being created).
        :param self: Reference the class instance itself
        :return: Nothing
        :doc-author: Malcolm Ross
        """
        # get logging started
        self.logger = logging.getLogger('root')

        if enable_geophires_logging_config:
            logging.config.fileConfig('logging.conf')
            self.logger.setLevel(logging.INFO)

        self.logger.info(f'Init {__class__.__name__!s}: {__name__}')

        # Initiate the elements of the Model
        # Set up all the Parameters that will be predefined by this class using the different types of parameter
        # classes.  Setting up includes giving it a name, a default value, The Unit Type (length, volume,
        # temperature, etc.) and Unit Name of that value, sets it as required (or not), sets allowable range,
        # the error message if that range is exceeded, the ToolTip Text, and the name of teh class that created it.
        # This includes setting up temporary variables that will be available to all the class but noy read in by user,
        # or used for Output
        # This also includes all Parameters that are calculated and then published using the Printouts function.

        # These dictionaries contain a list of all the parameters set in this object, stored as "Parameter" and
        # "OutputParameter" Objects.  This will allow us later to access them in a user interface and get that list,
        # along with unit type, preferred units, etc.
        self.ParameterDict = {}
        self.OutputParameterDict = {}  # declare some dictionaries
        self.InputParameters = {}  # dictionary to hold all the input parameter the user wants to change

        # inputs
        self.ReservoirTemperature = self.ParameterDict[self.ReservoirTemperature.Name] = floatParameter(
            'Reservoir Temperature',
            value=150.0,
            Min=50,
            Max=1000,
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS,
            Required=True,
            ErrMessage='assume default reservoir temperature (150 deg-C)',
            ToolTipText='Reservoir Temperature [150 dec-C]',
        )
        self.RejectionTemperature = self.ParameterDict[self.RejectionTemperature.Name] = floatParameter(
            'Rejection Temperature',
            value=25.0,
            Min=0.1,
            Max=200,
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS,
            Required=True,
            ErrMessage='assume default rejection temperature (25 deg-C)',
            ToolTipText='Rejection Temperature [25 dec-C]',
        )
        self.FormationPorosity = self.ParameterDict[self.FormationPorosity.Name] = floatParameter(
            'Formation Porosity',
            value=18.0,
            Min=0.0,
            Max=100.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.PERCENT,
            CurrentUnits=PercentUnit.PERCENT,
            Required=True,
            ErrMessage='assume default formation porosity (18%)',
            ToolTipText='Formation Porosity [18%]',
        )
        self.ReservoirArea = self.ParameterDict[self.ReservoirArea.Name] = floatParameter(
            'Reservoir Area',
            value=81.0,
            Min=0.0,
            Max=10000.0,
            UnitType=Units.AREA,
            PreferredUnits=AreaUnit.KILOMETERS2,
            CurrentUnits=AreaUnit.KILOMETERS2,
            Required=True,
            ErrMessage='assume default reservoir area (81 km2)',
            ToolTipText='Reservoir Area [81 km2]',
        )
        self.ReservoirThickness = self.ParameterDict[self.ReservoirThickness.Name] = floatParameter(
            'Reservoir Thickness',
            value=0.286,
            Min=0.0,
            Max=10000.0,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.KILOMETERS,
            CurrentUnits=LengthUnit.KILOMETERS,
            Required=True,
            ErrMessage='assume default reservoir thickness (0.286 km2)',
            ToolTipText='Reservoir Thickness [0.286 km]',
        )
        self.ReservoirLifeCycle = self.ParameterDict[self.ReservoirLifeCycle.Name] = intParameter(
            'Reservoir Life Cycle',
            value=30,
            UnitType=Units.TIME,
            PreferredUnits=TimeUnit.YEAR,
            CurrentUnits=TimeUnit.YEAR,
            AllowableRange=list(range(1, 101, 1)),
            Required=True,
            ErrMessage='assume default Reservoir Life Cycle (25 years)',
            ToolTipText='Reservoir Life Cycle [30 years]',
        )

        # user-changeable semi-constants
        self.ReservoirHeatCapacity = self.ParameterDict[self.ReservoirHeatCapacity.Name] = floatParameter(
            'Reservoir Heat Capacity',
            value=2.84e12,
            Min=0.0,
            Max=1e14,
            UnitType=Units.HEAT_CAPACITY,
            PreferredUnits=HeatCapacityUnit.KJPERKM3C,
            CurrentUnits=HeatCapacityUnit.KJPERKM3C,
            Required=True,
            ErrMessage='assume default Reservoir Heat Capacity (2.84E+12 kJ/km3C)',
            ToolTipText='Reservoir Heat Capacity [2.84E+12 kJ/km3C]',
        )
        self.HeatCapacityOfWater = self.ParameterDict[self.HeatCapacityOfWater.Name] = floatParameter(
            'Heat Capacity Of Water',
            value=-1.0,
            Min=3.0,
            Max=10.0,
            UnitType=Units.HEAT_CAPACITY,
            PreferredUnits=HeatCapacityUnit.kJPERKGC,
            CurrentUnits=HeatCapacityUnit.kJPERKGC,
            Required=True,
            ErrMessage='calculate a value based on the water temperature',
            ToolTipText='Heat Capacity Of Water [4.18 kJ/kgC]',
        )
        self.DensityOfWater = self.ParameterDict[self.DensityOfWater.Name] = floatParameter(
            'Density Of Water',
            value=-1.0,
            Min=1.000e11,
            Max=1.000e13,
            UnitType=Units.DENSITY,
            PreferredUnits=DensityUnit.KGPERKILOMETERS3,
            CurrentUnits=DensityUnit.KGPERKILOMETERS3,
            Required=True,
            ErrMessage='calculate a value based on the water temperature',
            ToolTipText='Heat Density Of Water [1.0E+12 kg/km3]',
        )
        self.DensityOfRock = self.ParameterDict[self.DensityOfRock.Name] = floatParameter(
            'Density Of Rock',
            value=2.55e12,
            Min=1.000e11,
            Max=1.000e13,
            UnitType=Units.DENSITY,
            PreferredUnits=DensityUnit.KGPERKILOMETERS3,
            CurrentUnits=DensityUnit.KGPERKILOMETERS3,
            Required=True,
            ErrMessage='assume default Density Of Rock (2.55E+12 kg/km3)',
            ToolTipText='Heat Density Of Rock [2.55E+12 kg/km3]',
        )
        self.RecoverableHeat = self.ParameterDict[self.RecoverableHeat.Name] = floatParameter(
            'Recoverable Heat',
            value=-1.0,
            Min=0.001,
            Max=1.000,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Required=False,
            ErrMessage='assume 0.66 for high-T reservoirs (>150C), 0.43 for low-T reservoirs \
            (>90, Garg and Combs (2011)',
            ToolTipText='percent of heat that is recoverable from the rock in the reservoir 0.66 for high-T reservoirs,\
             0.43 for low-T reservoirs (Garg and Combs (2011)',
        )

        # internal
        self.WaterContent = self.ParameterDict[self.WaterContent.Name] = floatParameter(
            'Water Content',
            value=18.0,
            Min=0.0,
            Max=100.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.PERCENT,
            CurrentUnits=PercentUnit.PERCENT,
            Required=True,
            ErrMessage='assume default water content (18%)',
            ToolTipText='Water Content',
        )
        self.RockContent = self.ParameterDict[self.RockContent.Name] = floatParameter(
            'Rock Content',
            value=82.0,
            Min=0.0,
            Max=100.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.PERCENT,
            CurrentUnits=PercentUnit.PERCENT,
            Required=True,
            ErrMessage='assume default rock content (82%)',
            ToolTipText='Rock Content',
        )
        self.RejectionTemperatureK = self.ParameterDict[self.RejectionTemperatureK.Name] = floatParameter(
            'Rejection Temperature in K',
            value=298.15,
            Min=0.1,
            Max=1000.0,
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.KELVIN,
            CurrentUnits=TemperatureUnit.KELVIN,
            Required=True,
            ErrMessage='assume default rejection temperature in K (298.15 deg-K)',
            ToolTipText='Rejection Temperature in K [298.15 deg-K]',
        )
        self.RejectionEntropy = self.ParameterDict[self.RejectionEntropy.Name] = floatParameter(
            'Rejection Entropy',
            value=0.3670,
            Min=0.0001,
            Max=100.0,
            UnitType=Units.ENTROPY,
            PreferredUnits=EntropyUnit.KJPERKGK,
            CurrentUnits=EntropyUnit.KJPERKGK,
            Required=True,
            ErrMessage='assume default Rejection Entropy (0.3670 kJ/kgK @25 deg-C)',
            ToolTipText='Rejection Entropy [0.3670 kJ/kgK @25 deg-C]',
        )
        self.RejectionEnthalpy = self.ParameterDict[self.RejectionEnthalpy.Name] = floatParameter(
            'Rejection Enthalpy',
            value=104.8,
            Min=0.0001,
            Max=1000.0,
            UnitType=Units.ENTHALPY,
            PreferredUnits=EnthalpyUnit.KJPERKG,
            CurrentUnits=EnthalpyUnit.KJPERKG,
            Required=True,
            ErrMessage='assume default Rejection Enthalpy (104.8 kJ/kg @25 deg-C)',
            ToolTipText='Rejection Enthalpy [104.8 kJ/kg @25 deg-C]',
        )

        # Outputs
        self.V = self.OutputParameterDict[self.V.Name] = OutputParameter(
            Name='Reservoir Volume',
            UnitType=Units.VOLUME,
            PreferredUnits=VolumeUnit.KILOMETERS3,
            CurrentUnits=VolumeUnit.KILOMETERS3,
        )
        self.qR = self.OutputParameterDict[self.qR.Name] = OutputParameter(
            Name='Stored Heat',
            UnitType=Units.HEAT,
            PreferredUnits=HeatUnit.KJ,
            CurrentUnits=HeatUnit.KJ
        )
        self.mWH = self.OutputParameterDict[self.mWH.Name] = OutputParameter(
            Name='Fluid Produced',
            UnitType=Units.MASS,
            PreferredUnits=MassUnit.KILOGRAM,
            CurrentUnits=MassUnit.KILOGRAM
        )
        self.e = self.OutputParameterDict[self.e.Name] = OutputParameter(
            Name='Enthalpy',
            UnitType=Units.ENTHALPY,
            PreferredUnits=EnthalpyUnit.KJPERKG,
            CurrentUnits=EnthalpyUnit.KJPERKG,
        )
        self.qWH = self.OutputParameterDict[self.qWH.Name] = OutputParameter(
            Name='Wellhead Heat',
            UnitType=Units.HEAT,
            PreferredUnits=HeatUnit.KJ,
            CurrentUnits=HeatUnit.KJ
        )
        self.Rg = self.OutputParameterDict[self.Rg.Name] = OutputParameter(
            Name='Recovery Factor',
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.PERCENT,
            CurrentUnits=PercentUnit.PERCENT,
        )
        self.WA = self.OutputParameterDict[self.WA.Name] = OutputParameter(
            Name='Available Heat',
            UnitType=Units.HEAT,
            PreferredUnits=HeatUnit.KJ,
            CurrentUnits=HeatUnit.KJ
        )
        self.WE = self.OutputParameterDict[self.WE.Name] = OutputParameter(
            Name='Producible Heat',
            UnitType=Units.HEAT,
            PreferredUnits=HeatUnit.KJ,
            CurrentUnits=HeatUnit.KJ
        )
        self.We = self.OutputParameterDict[self.We.Name] = OutputParameter(
            Name='Producible Electricity',
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )

        self.logger.info(f'Complete {__class__.__name__!s}: {__name__}')

    def read_parameters(self) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary created by reading the user-provided file
        and updates the parameter values for this object.

        The function reads in all the parameters that relate to this object, including those that are inherited
        from other objects. It then updates any of these parameter values that have been changed by the user.
        It also handles any special cases.
        :param self: Reference the class instance (such as it is) from within the class
        :return: None
        :doc-author: Malcolm Ross
        """
        self.logger.info(f'Init {__class__.__name__!s}: {__name__}')

        # This should give us a dictionary with all the parameters the user wants to set.  Should be only those value
        # that they want to change from the default.
        # we do this as soon as possible because what we instantiate may depend on settings in this file

        read_input_file(self.InputParameters, logger=self.logger)

        # Deal with all the parameter values that the user has provided.  They should really only provide values
        # that they want to change from the default values, but they can provide a value that is already set because
        # it is a default value set in __init__.  It will ignore those.
        # This also deals with all the special cases that need to be taken care of after
        # a value has been read in and checked.
        # If you choose to subclass this master class, you can also choose to override this method (or not),
        # and if you do, do it before or after you call you own version of this method.  If you do, you can
        # also choose to call this method from you class, which can effectively modify all these superclass parameters
        # in your class.

        if len(self.InputParameters) > 0:
            # loop through all the parameters that the user wishes to set, looking for parameters that match this object
            for item in self.ParameterDict.items():
                ParameterToModify = item[1]
                key = ParameterToModify.Name.strip()
                if key in self.InputParameters:
                    ParameterReadIn = self.InputParameters[key]
                    # Before we change the parameter, let's assume that the unit preferences will match -
                    # if they don't, the later code will fix this.
                    ParameterToModify.CurrentUnits = ParameterToModify.PreferredUnits
                    ReadParameter(ParameterReadIn, ParameterToModify, self)  # this should handle all the non-special cases

                    # handle special cases
                    if ParameterToModify.Name == 'Formation Porosity':
                        self.WaterContent.value = ParameterToModify.value
                        self.RockContent = 100.0 - ParameterToModify.value

                    elif ParameterToModify.Name == 'Rejection Temperature':
                        self.RejectionTemperatureK.value = 273.15 + ParameterToModify.value
                        self.RejectionEntropy.value = EntropyH20_func(ParameterToModify.value)
                        self.RejectionEnthalpy.value = EnthalpyH20_func(ParameterToModify.value)

                    elif ParameterToModify.Name == 'Density Of Water':
                        value = float(ParameterReadIn.sValue)
                        if value < 0:  # if the user supplied -1 as the density, they want us to calculate it.
                            ParameterToModify.value = DensityWater(self.ReservoirTemperature.value) * 1_000_000_000.0
                            self.DensityOfWater.value = ParameterToModify.value

                    elif ParameterToModify.Name == 'Heat Capacity Of Water':
                        value = float(ParameterReadIn.sValue)
                        if value < 0:  # if the user supplied -1 as the capacity, they want us to calculate it.
                            ParameterToModify.value = HeatCapacityWater(self.ReservoirTemperature.value) / 1000.0
                            self.HeatCapacityOfWater.value = ParameterToModify.value

                    elif ParameterToModify.Name == 'Recoverable Heat':
                        value = float(ParameterReadIn.sValue)
                        if value < 0:  # if the user supplied -1 as the Recoverable Heat, they want us to calculate it.
                            ParameterToModify.value = RecoverableHeat(self.RecoverableHeat.value, self.ReservoirTemperature.value)
                            self.RecoverableHeat.value = ParameterToModify.value
        else:
            self.logger.info('No parameters read because no content provided')

        # loop through all the parameters that the user wishes to set, looking for parameters that contain
        # the prefix "Units:" - that means we want to set a special case for converting this output parameter
        # to new units
        for key in self.InputParameters.keys():
            if key.startswith('Units:'):
                self.OutputParameterDict[key.replace('Units:', '')].CurrentUnits = LookupUnits(self.InputParameters[key].sValue)[0]
                self.OutputParameterDict[key.replace('Units:', '')].UnitsMatch = False

        self.logger.info(f'complete {__class__.__name__!s}: {__name__}')

    def Calculate(self):
        """
        The Calculate function is where all the calculations are made.  This is handled on a class-by-class basis.
        The Calculate function does not return anything, but it does store the results for later use by other functions.
        :param self: Access the class variables
        :return: None
        :doc-author: Malcolm Ross
        """
        self.logger.info(f'Init {__class__!s}: {__class__.__name__!s}: {__name__}')

        try:
            # This is where all the calculations are made using all the values that have been set.
            # first, make sure that density and heat capacity of water are set
            if self.DensityOfWater.value < self.DensityOfWater.Min:
                self.DensityOfWater.value = DensityWater(self.ReservoirTemperature.value) * 1_000_000_000.0
            if self.HeatCapacityOfWater.value < self.HeatCapacityOfWater.Min:
                self.HeatCapacityOfWater.value = HeatCapacityWater(self.ReservoirTemperature.value) / 1000.0

            # now do the volume calculation
            self.V.value = self.ReservoirArea.value * self.ReservoirThickness.value

            # calculate the stored heat in the reservoir
            self.qR.value = self.V.value * ( self.ReservoirHeatCapacity.value * (self.ReservoirTemperature.value - self.RejectionTemperature.value))

            # calculate the mass of the fluid in the reservoir
            # TODO: this is wrong, it should be the mass of the producible fluid, not the total mass of all the fluid in the reservoir
            self.mWH.value = (self.V.value * (self.FormationPorosity.value / 100.0)) * self.DensityOfWater.value

            # calculate the maximum energy out per unit of mass (equation 7 of Garg & Combs (2011))
            self.e.value = ((EnthalpyH20_func(self.ReservoirTemperature.value) - self.RejectionEnthalpy.value)
                            - (self.RejectionTemperatureK.value
                            * (EntropyH20_func(self.ReservoirTemperature.value) - self.RejectionEntropy.value)))

            # calculate the heat recovery at the wellhead
            self.qWH.value = self.mWH.value * (EnthalpyH20_func(self.ReservoirTemperature.value) - self.RejectionTemperatureK.value)

            # calculate the recovery factor
            self.Rg.value = self.qWH.value / self.qR.value

            # calculate the available heat
            self.WA.value = (self.mWH.value * self.e.value * self.Rg.value * RecoverableHeat(self.RecoverableHeat.value, self.ReservoirTemperature.value))

            # calculate the producible heat given the utilization efficiency
            self.WE.value = self.WA.value * UtilEff_func(self.ReservoirTemperature.value)

            # calculate the producible electricity
            self.We.value = (self.WE.value / 3_600_000) / 8_760  # convert Kilojoules of heat to MWe of electricity

            self.logger.info(f'Complete {__class__!s}: {__class__.__name__!s}: {__name__}')
        except Exception as e:
            self.logger.error(f'Error occurred during calculations: {str(e)}')
            traceback.print_exc()

    def PrintOutputs(self):
        """
        PrintOutputs writes the standard outputs to the output file.
        """
        self.logger.info(f'Init {__class__.__name__!s}: {__name__}')

        # Deal with converting Units back to PreferredUnits, if required.
        # before we write the outputs, we go through all the parameters for all the objects and set the values back
        # to the units that the user entered the data in
        # We do this because the value may be displayed in the output, and we want the user to recognize their value,
        # not some converted value
        for key in self.ParameterDict:
            param = self.ParameterDict[key]
            if not param.UnitsMatch:
                ConvertUnitsBack(param, self)

        # now we need to loop through all the output parameters to update their units to whatever
        # units the user has specified.
        # i.e., they may have specified that all LENGTH results must be in feet, so we need to convert those from
        # whatever LENGTH unit they are to feet.
        # same for all the other classes of units (TEMPERATURE, DENSITY, etc).
        for key in self.OutputParameterDict:
            if not self.OutputParameterDict[key].UnitsMatch:
                ConvertOutputUnits(self.OutputParameterDict[key], self.OutputParameterDict[key].CurrentUnits, self)

        # ---------------------------------------
        # write results to output file and screen
        # ---------------------------------------
        try:
            outputfile = 'HIP.out' if len(sys.argv) <= 2 else sys.argv[2]

            def render_default(p: floatParameter | OutputParameter) -> str:
                return f'{p.value:10.2f} {p.CurrentUnits.value}'

            def render_scientific(p: floatParameter | OutputParameter) -> str:
                return f'{p.value:10.2e} {p.CurrentUnits.value}'

            summary_of_results = {}

            for param, render in [
                (self.ReservoirTemperature, render_default),
                (self.V, render_default),
                (self.qR, render_scientific),
                (self.mWH, render_scientific),
                (self.e, render_default),
                (self.qWH, render_scientific),
                (self.Rg, lambda rg: f'{(100 * rg.value):10.2f} {rg.CurrentUnits.value}'),
                (self.WA, render_scientific),
                (self.WE, render_scientific),
                (self.We, render_default),]:
                summary_of_results[param.Name] = render(param)

            case_data = {'SUMMARY OF RESULTS': summary_of_results}

            with open(outputfile, 'w', encoding='UTF-8') as f:
                nl = '\n'

                f.write(f'                               *********************{nl}')
                f.write(f'                               ***HIP CASE REPORT***{nl}')
                f.write(f'                               *********************{nl}')
                f.write(nl)
                f.write(f'                           ***SUMMARY OF RESULTS***{nl}')
                f.write(nl)

                for k, v in case_data['SUMMARY OF RESULTS'].items():
                    # align space between value and units to same column
                    kv_spaces = max(1, (24 - (len(v.split(' ')[0]) + len(k)))) * ' '

                    f.write(f'      {k}:{kv_spaces}{v}{nl}')

        except FileNotFoundError as ex:
            print(str(ex))
            traceback_str = traceback.format_exc()
            msg = f'Error: HIP_RA Failed to write the output file. Exiting....\n{traceback_str}'
            print(msg)
            self.logger.critical(str(ex))
            self.logger.critical(msg)
            raise

        except PermissionError as ex:
            print(str(ex))
            traceback_str = traceback.format_exc()
            msg = f'Error: HIP_RA Failed to write the output file. Exiting....\n{traceback_str}'
            print(msg)
            self.logger.critical(str(ex))
            self.logger.critical(msg)
            raise

        except Exception as ex:
            print(str(ex))
            traceback_str = traceback.format_exc()
            msg = f'Error: HIP_RA Failed to write the output file. Exiting....\n{traceback_str}'
            print(msg)
            self.logger.critical(str(ex))
            self.logger.critical(msg)
            raise

        # copy the output file to the screen
        with open(outputfile, encoding='UTF-8') as f:
            content = f.readlines()  # store all output in one long list

            # Now write each line to the screen
            for line in content:
                sys.stdout.write(line)

    def __str__(self):
        return 'HIP_RA'


def main(enable_geophires_logging_config=True):
    # set the starting directory to be the directory that this file is in
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # set up logging.
    if enable_geophires_logging_config:
        logging.config.fileConfig('logging.conf')
    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger('root')

    logger.info('Initializing the application')

    # initiate the HIP-RA parameters, setting them to their default values
    model = HIP_RA(enable_geophires_logging_config=enable_geophires_logging_config)

    # read the parameters that apply to the model
    model.read_parameters()

    try:
        # Calculate the entire model
        model.Calculate()
    except Exception as e:
        logger.error(f'Error occurred during model calculation: {str(e)}')

    try:
        # write the outputs
        model.PrintOutputs()
    except Exception as e:
        logger.error(f'Error occurred during output printing: {str(e)}')

    logger.info('Application execution completed')


if __name__ == '__main__':
    main()

import sys
import logging
import time
import logging.config

from geophires_x.GeoPHIRESUtils import read_input_file
from geophires_x.WellBores import WellBores
from geophires_x.SurfacePlant import SurfacePlant
from geophires_x.SurfacePlantDirectUseHeat import surface_plant_direct_use_heat
from geophires_x.SurfacePlantSubcriticalORC import surface_plant_subcritical_orc
from geophires_x.SurfacePlantSupercriticalORC import surface_plant_supercritical_orc
from geophires_x.SurfacePlantSingleFlash import surface_plant_single_flash
from geophires_x.SurfacePlantDoubleFlash import surface_plant_double_flash
from geophires_x.SurfacePlantAbsorptionChiller import surface_plant_absorption_chiller
from geophires_x.SurfacePlantDistrictHeating import surface_plant_district_heating
from geophires_x.SurfacePlantHeatPump import surface_plant_heat_pump
from geophires_x.SurfacePlantSUTRA import surface_plant_sutra
from geophires_x.Economics import Economics
from geophires_x.Outputs import Outputs
from geophires_x.OptionList import EndUseOptions, PlantType


class Model(object):
    """
    Model is the container class of the application, giving access to everything else, including the logger
    """

    def __init__(self, enable_geophires_logging_config=True):
        """
        The __init__ function is called automatically every time the class is being used to create a new object.
        :return: Nothing
        """

        # get logging started
        self.logger = logging.getLogger('root')

        if enable_geophires_logging_config:
            logging.config.fileConfig('logging.conf')
            self.logger.setLevel(logging.INFO)

        self.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')

        # keep track of execution time
        self.tic = time.time()

        # dictionary to hold all the input parameter the user wants to change
        # This should give us a dictionary with all the parameters the user wants to set.
        # Should be only those value that they want to change from the default.
        # we do this as soon as possible because what we instantiate may depend on settings in this file
        self.InputParameters = {}

        read_input_file(self.InputParameters, logger=self.logger)

        self.ccuseconomics = None
        self.ccusoutputs = None
        self.sdacgtoutputs = None
        self.sdacgteconomics = None
        self.addoutputs = None
        self.addeconomics = None

        # Initiate the elements of the Model
        # this is where you can change what class get initiated - the superclass, or one of the subclasses
        self.logger.info("Initiate the elements of the Model")
        # we need to decide which reservoir to instantiate based on the user input (InputParameters),
        # which we just read above for the first time
        # Default is Thermal drawdown percentage model (GETEM)
        from .TDPReservoir import TDPReservoir as TDPReservoir
        self.reserv = TDPReservoir(self)
        if 'Reservoir Model' in self.InputParameters:
            if self.InputParameters['Reservoir Model'].sValue == '0':
                from geophires_x.CylindricalReservoir import CylindricalReservoir as CylindricalReservoir
                self.reserv = CylindricalReservoir(self)  # Simple Cylindrical Reservoir
            elif self.InputParameters['Reservoir Model'].sValue == '1':
                from geophires_x.MPFReservoir import MPFReservoir as MPFReservoir
                self.reserv = MPFReservoir(self)  # Multiple parallel fractures model (LANL)
            elif self.InputParameters['Reservoir Model'].sValue == '2':
                from geophires_x.LHSReservoir import LHSReservoir as LHSReservoir
                self.reserv = LHSReservoir(self)  # Multiple parallel fractures model (LANL)
            elif self.InputParameters['Reservoir Model'].sValue == '3':
                from geophires_x.SFReservoir import SFReservoir as SFReservoir
                self.reserv = SFReservoir(self)  # Drawdown parameter model (Tester)
            elif self.InputParameters['Reservoir Model'].sValue == '5':
                from geophires_x.UPPReservoir import UPPReservoir as UPPReservoir
                self.reserv = UPPReservoir(self)  # Generic user-provided temperature profile
            elif self.InputParameters['Reservoir Model'].sValue == '6':
                from geophires_x.TOUGH2Reservoir import TOUGH2Reservoir as TOUGH2Reservoir
                self.reserv = TOUGH2Reservoir(self)  # Tough2 is called
            elif self.InputParameters['Reservoir Model'].sValue == '7':
                from geophires_x.SUTRAReservoir import SUTRAReservoir as SUTRAReservoir
                self.reserv = SUTRAReservoir(self)  # SUTRA output is read

        # initialize the default objects
        self.wellbores = WellBores(self)
        self.surfaceplant = SurfacePlant(self)
        self.economics = Economics(self)
        self.outputs = Outputs(self)

        if 'Reservoir Model' in self.InputParameters:
            if self.InputParameters['Reservoir Model'].sValue == '7':
                # if we use SUTRA output for simulating reservoir thermal energy storage, we use a special wellbore object that can handle SUTRA data
                del self.wellbores
                from geophires_x.SUTRAWellBores import SUTRAWellBores as SUTRAWellBores
                self.wellbores = SUTRAWellBores(self)
                del self.surfaceplant
                from geophires_x.SurfacePlantSUTRA import SUTRASurfacePlant as SUTRASurfacePlant
                self.surfaceplant = SUTRASurfacePlant(self)
                del self.economics
                from geophires_x.SUTRAEconomics import SUTRAEconomics as SUTRAEconomics
                self.economics = SUTRAEconomics(self)
                del self.outputs
                from geophires_x.SUTRAOutputs import SUTRAOutputs as SUTRAOutputs
                self.outputs = SUTRAOutputs(self)

        if 'Is AGS' in self.InputParameters:
            if self.InputParameters['Is AGS'].sValue == 'True':
                self.logger.info("Setup the AGS elements of the Model and instantiate new attributes as needed")
                # If we are doing AGS, we need to replace the various objects we with versions of the objects
                # that have AGS functionality.
                # that means importing them, initializing them, then reading their parameters
                # use the simple cylindrical reservoir for all AGS systems.
                from geophires_x.CylindricalReservoir import CylindricalReservoir as CylindricalReservoir
                del self.reserv  # delete the original object so we can replace it
                self.reserv = CylindricalReservoir(self)
                del self.wellbores
                from geophires_x.AGSWellBores import AGSWellBores as AGSWellBores
                self.wellbores = AGSWellBores(self)
                del self.surfaceplant
                from geophires_x.AGSSurfacePlant import AGSSurfacePlant as AGSSurfacePlant
                self.surfaceplant = AGSSurfacePlant(self)
                del self.economics
                from geophires_x.AGSEconomics import AGSEconomics as AGSEconomics
                self.economics = AGSEconomics(self)
                from geophires_x.AGSOutputs import AGSOutputs as AGSOutputs
                del self.outputs
                self.outputs = AGSOutputs(self)

        # if we find out we have an add-ons, we need to instantiate it, then read for the parameters
        if 'AddOn Nickname 1' in self.InputParameters:
            self.logger.info("Initiate the Add-on elements")
            from geophires_x.EconomicsAddOns import EconomicsAddOns  # do this only is user wants add-ons
            self.addeconomics = EconomicsAddOns(self)
            from geophires_x.OutputsAddOns import OutputsAddOns
            self.addoutputs = OutputsAddOns(self)

        # if we find out we have a ccus, we need to instantiate it, then read for the parameters
        if 'Ending CCUS Credit Value' in self.InputParameters:
            self.logger.info("Initiate the CCUS elements")
            from geophires_x.EconomicsCCUS import EconomicsCCUS  # do this only is user wants CCUS
            self.ccuseconomics = EconomicsCCUS(self)
            from geophires_x.OutputsCCUS import OutputsCCUS
            self.ccusoutputs = OutputsCCUS(self)

        # if we find out we have an S-DAC-GT calculation, we need to instantiate it
        if 'S-DAC-GT' in self.InputParameters:
            if self.InputParameters['S-DAC-GT'].sValue == 'On':
                self.logger.info("Initiate the S-DAC-GT elements")
                from geophires_x.EconomicsS_DAC_GT import EconomicsS_DAC_GT  # do this only is user wants S-DAC-GT
                self.sdacgteconomics = EconomicsS_DAC_GT(self)
                from geophires_x.OutputsS_DAC_GT import OutputsS_DAC_GT
                self.sdacgtoutputs = OutputsS_DAC_GT(self)

        self.logger.info(f'Complete {str(__class__)}: {sys._getframe().f_code.co_name}')

    def __str__(self):
        return "Model"

    def read_parameters(self) -> None:
        """
        The read_parameters function reads the parameters from the input file and stores them in a dictionary.
        :return: None
        """
        self.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')

        # Deal with all the parameter values that the user has provided.  This is handled on a class-by-class basis.
        self.logger.info("Read parameters for the elements of the Model and instantiate new attributes as needed")
        self.reserv.read_parameters(self)
        self.wellbores.read_parameters(self)
        self.surfaceplant.read_parameters(self)
        self.economics.read_parameters(self)
        self.outputs.read_parameters(self)

        # if we find out we have an add-ons, read the parameters
        if self.economics.DoAddOnCalculations.value:
            self.addeconomics.read_parameters(self)
            self.addoutputs.read_parameters(self)
        # if we find out we have a ccus, read for the parameters
        if self.economics.DoCCUSCalculations.value:
            self.ccuseconomics.read_parameters(self)
            self.ccusoutputs.read_parameters(self)
        # if we find out we have an S-DAC-GT calculation, read for the parameters
        if self.economics.DoSDACGTCalculations.value:
            self.sdacgteconomics.read_parameters(self)
            self.sdacgtoutputs.read_parameters(self)

        # Once we are done reading and processing parameters, we reset the objects to more specific objects based on user choices

        if self.surfaceplant.enduse_option.value not in [EndUseOptions.HEAT]:
            # if we are doing power generation, we need to instantiate the surface plant object based on the user input
            if self.surfaceplant.plant_type.value == PlantType.SUB_CRITICAL_ORC:
                self.surfaceplant = surface_plant_subcritical_orc(self)
            elif self.surfaceplant.plant_type.value == PlantType.SUPER_CRITICAL_ORC:
                self.surfaceplant = surface_plant_supercritical_orc(self)
            elif self.surfaceplant.plant_type.value == PlantType.SINGLE_FLASH:
                self.surfaceplant = surface_plant_single_flash(self)
            else: # default is double flash
                self.surfaceplant = surface_plant_double_flash(self)

            # re-read the parameters for the newly instantiated surface plant
            self.surfaceplant.read_parameters(self)

            # assume that if they are doing CHP of some kind, we have two surface plants we need to account for,
            # and that the second surface plant is industrial heat only
            if self.surfaceplant.enduse_option.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT,
                                                          EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY,
                                                          EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                          EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY,
                                                          EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT,
                                                          EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]:
                self.surfaceplant2 = surface_plant_direct_use_heat(self)
                self.surfaceplant2.read_parameters(self)    #read the parameters for the second surface plant
        else:   #direct use heat only style physical plant
            if self.surfaceplant.plant_type.value == PlantType.ABSORPTION_CHILLER:
                self.surfaceplant = surface_plant_absorption_chiller(self)
            elif self.surfaceplant.plant_type.value == PlantType.HEAT_PUMP:
                self.surfaceplant = surface_plant_heat_pump(self)
            elif self.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
                self.surfaceplant = surface_plant_district_heating(self)
            elif self.surfaceplant.plant_type.value == PlantType.RTES:
                self.surfaceplant = surface_plant_sutra(self)
            else:
                self.surfaceplant = surface_plant_direct_use_heat(self)

        # re-read the parameters for the newly instantiated surface plant
        self.surfaceplant.read_parameters(self)

        # if end-use option is 8 (district heating), some calculations are required prior to the reservoir and wellbore simulations
        if self.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
            self.surfaceplant.CalculateDHDemand(self)  # calculate district heating demand

        self.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def Calculate(self):
        """
        The Calculate function is where all the calculations are made.  This is handled on a class-by-class basis.
        The Calculate function does not return anything, but it does store the results in self.reserv, self.wellbores
         and self.surfaceplant for later use by other functions.
        :return: None
        """
        self.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')
        # calculate the results
        self.logger.info("Run calculations for the elements of the Model")

        # This is where all the calculations are made using all the values that have been set.
        # This is handled on a class-by-class basis

        self.reserv.Calculate(self)  # model the reservoir
        self.wellbores.Calculate(self)  # model the wellbores
        self.surfaceplant.Calculate(self)  # model the surfaceplant

        # if we are doing cogeneration, we need to calculate the values for second surface plant
        if self.surfaceplant.enduse_option.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT,
                                                      EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY,
                                                      EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                      EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY,
                                                      EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT,
                                                      EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]:
            self.surfaceplant2.Calculate(self)

        # in case of district heating, the surface plant module may have updated the utilization factor,
        # and therefore we need to recalculate the modules reservoir, wellbore and surface plant.
        # 1 iteration should be sufficient.
        if self.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
            self.reserv.Calculate(self)  # model the reservoir
            self.wellbores.Calculate(self)  # model the wellbores
            self.surfaceplant.Calculate(self)  # model the surfaceplant

        self.economics.Calculate(self)  # model the economics

        # do the additional economic calculations if needed
        if self.economics.DoAddOnCalculations.value:
            self.addeconomics.Calculate(self)
        if self.economics.DoCCUSCalculations.value:
            self.ccuseconomics.Calculate(self)
        if self.economics.DoSDACGTCalculations.value:
            self.sdacgteconomics.Calculate(self)

        self.logger.info(f'complete {str(__class__)}: {sys._getframe().f_code.co_name}')

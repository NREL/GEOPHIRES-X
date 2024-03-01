from pathlib import Path
import logging
import time
import logging.config

from geophires_x.EconomicsS_DAC_GT import EconomicsS_DAC_GT
from geophires_x.GeoPHIRESUtils import read_input_file
from geophires_x.OutputsAddOns import OutputsAddOns
from geophires_x.OutputsS_DAC_GT import OutputsS_DAC_GT
from geophires_x.TDPReservoir import TDPReservoir
from geophires_x.WellBores import WellBores
from geophires_x.SurfacePlant import SurfacePlant
from geophires_x.SurfacePlantIndustrialHeat import SurfacePlantIndustrialHeat
from geophires_x.SurfacePlantSubcriticalORC import SurfacePlantSubcriticalOrc
from geophires_x.SurfacePlantSupercriticalORC import SurfacePlantSupercriticalOrc
from geophires_x.SurfacePlantSingleFlash import SurfacePlantSingleFlash
from geophires_x.SurfacePlantDoubleFlash import SurfacePlantDoubleFlash
from geophires_x.SurfacePlantAbsorptionChiller import SurfacePlantAbsorptionChiller
from geophires_x.SurfacePlantDistrictHeating import SurfacePlantDistrictHeating
from geophires_x.SurfacePlantHeatPump import SurfacePlantHeatPump
from geophires_x.Economics import Economics
from geophires_x.Outputs import Outputs
from geophires_x.OptionList import EndUseOptions, PlantType
from geophires_x.CylindricalReservoir import CylindricalReservoir
from geophires_x.MPFReservoir import MPFReservoir
from geophires_x.LHSReservoir import LHSReservoir
from geophires_x.SFReservoir import SFReservoir
from geophires_x.UPPReservoir import UPPReservoir
from geophires_x.TOUGH2Reservoir import TOUGH2Reservoir
from geophires_x.SUTRAReservoir import SUTRAReservoir
from geophires_x.SUTRAWellBores import SUTRAWellBores
from geophires_x.SurfacePlantSUTRA import SurfacePlantSUTRA
from geophires_x.SUTRAEconomics import SUTRAEconomics
from geophires_x.SUTRAOutputs import SUTRAOutputs
from geophires_x.AGSWellBores import AGSWellBores
from geophires_x.SurfacePlantAGS import SurfacePlantAGS
from geophires_x.AGSEconomics import AGSEconomics
from geophires_x.AGSOutputs import AGSOutputs
from geophires_x.EconomicsAddOns import EconomicsAddOns


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
            logging.config.fileConfig(Path(Path(__file__).parent,'logging.conf'))
            self.logger.setLevel(logging.INFO)

        self.logger.info(f'Init {__class__}: {__name__}')

        # keep track of execution time
        self.tic = time.time()

        # dictionary to hold all the input parameter the user wants to change
        # This should give us a dictionary with all the parameters the user wants to set.
        # Should be only those value that they want to change from the default.
        # we do this as soon as possible because what we instantiate may depend on settings in this file
        self.InputParameters = {}

        read_input_file(self.InputParameters, logger=self.logger)

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
        self.reserv: TDPReservoir = TDPReservoir(self)
        if 'Reservoir Model' in self.InputParameters:
            if self.InputParameters['Reservoir Model'].sValue == '0':
                self.reserv: CylindricalReservoir = CylindricalReservoir(self)  # Simple Cylindrical Reservoir
            elif self.InputParameters['Reservoir Model'].sValue == '1':
                self.reserv: MPFReservoir = MPFReservoir(self)  # Multiple parallel fractures model (LANL)
            elif self.InputParameters['Reservoir Model'].sValue == '2':
                self.reserv: LHSReservoir = LHSReservoir(self)  # Multiple parallel fractures model (LANL)
            elif self.InputParameters['Reservoir Model'].sValue == '3':
                self.reserv: SFReservoir = SFReservoir(self)  # Drawdown parameter model (Tester)
            elif self.InputParameters['Reservoir Model'].sValue == '5':
                self.reserv: UPPReservoir = UPPReservoir(self)  # Generic user-provided temperature profile
            elif self.InputParameters['Reservoir Model'].sValue == '6':
                self.reserv: TOUGH2Reservoir = TOUGH2Reservoir(self)  # Tough2 is called
            elif self.InputParameters['Reservoir Model'].sValue == '7':
                self.reserv: SUTRAReservoir = SUTRAReservoir(self)  # SUTRA output is created

        # initialize the default objects
        self.wellbores: WellBores = WellBores(self)
        self.surfaceplant: SurfacePlant = SurfacePlant(self)
        self.economics: Economics = Economics(self)
        self.outputs: Outputs = Outputs(self)

        if 'Reservoir Model' in self.InputParameters:
            if self.InputParameters['Reservoir Model'].sValue == '7':
                # if we use SUTRA output for simulating reservoir thermal energy storage, we use a special wellbore object that can handle SUTRA data
                self.wellbores: WellBores = SUTRAWellBores(self)
                self.surfaceplant: SurfacePlantSUTRA = SurfacePlantSUTRA(self)
                self.economics: SUTRAEconomics = SUTRAEconomics(self)
                self.outputs: SUTRAOutputs = SUTRAOutputs(self)

        if 'Is AGS' in self.InputParameters:
            if self.InputParameters['Is AGS'].sValue in ['True', 'true', 'TRUE', 'T', '1']:
                self.logger.info("Setup the AGS elements of the Model and instantiate new attributes as needed")
                # If we are doing AGS, we need to replace the various objects we with versions of the objects
                # that have AGS functionality.
                # that means importing them, initializing them, then reading their parameters
                # use the simple cylindrical reservoir for all AGS systems.
                self.reserv: CylindricalReservoir = CylindricalReservoir(self)
                self.wellbores: WellBores = AGSWellBores(self)
                self.surfaceplant: SurfacePlantAGS = SurfacePlantAGS(self)
                self.economics: AGSEconomics = AGSEconomics(self)
                self.outputs: AGSOutputs = AGSOutputs(self)
                self.wellbores.IsAGS.value = True

        # if we find out we have an add-ons, we need to instantiate it, then read for the parameters
        if 'AddOn Nickname 1' in self.InputParameters:
            self.logger.info("Initiate the Add-on elements")
            self.addeconomics: EconomicsAddOns = EconomicsAddOns(self)
            self.addoutputs: OutputsAddOns = OutputsAddOns(self)

        # if we find out we have an S-DAC-GT calculation, we need to instantiate it
        if 'Do S-DAC-GT Calculations' in self.InputParameters:
            if self.InputParameters['Do S-DAC-GT Calculations'].sValue in ['On', 'on', 'ON', 'True', 'true', 'TRUE', 'T', 't', '1']:
                self.logger.info("Initiate the S-DAC-GT elements")
                self.sdacgteconomics: EconomicsS_DAC_GT = EconomicsS_DAC_GT(self)
                self.sdacgtoutputs: OutputsS_DAC_GT = OutputsS_DAC_GT(self)

        self.logger.info(f'Complete {__class__}: {__name__}')

    def __str__(self):
        return "Model"

    def read_parameters(self) -> None:
        """
        The read_parameters function reads the parameters from the input file and stores them in a dictionary.
        :return: None
        """
        self.logger.info(f'Init {__class__}: {__name__}')

        # Deal with all the parameter values that the user has provided.  This is handled on a class-by-class basis.
        self.logger.info("Read parameters for the elements of the Model and instantiate new attributes as needed")
        self.reserv.read_parameters(self)
        self.wellbores.read_parameters(self)
        self.surfaceplant.read_parameters(self)
        self.economics.read_parameters(self)
        self.outputs.read_parameters(self)

        # having read in the parameters, we now need to set up the objects that are specific to the user's choices
        # if we find out we have an add-ons, read the parameters
        if self.economics.DoAddOnCalculations.value:
            self.addeconomics.read_parameters(self)
            self.addoutputs.read_parameters(self)
        # if we find out we have an S-DAC-GT calculation, read for the parameters
        if self.economics.DoSDACGTCalculations.value:
            self.sdacgteconomics.read_parameters(self)
            self.sdacgtoutputs.read_parameters(self)

        # Once we are done reading and processing parameters,
        # we reset the objects to more specific objects based on user choices
        # Handle the special case where the user defines it as AGS, but sets the temperature too high or the laterals > 1
        # in that case, we revert to the classical version of the surfaceplant
        if self.wellbores.IsAGS.value and self.wellbores.Tini < 375.0 and self.wellbores.numnonverticalsections.value == 1:
            self.surfaceplant = SurfacePlantAGS(self)
        elif self.surfaceplant.enduse_option.value not in [EndUseOptions.HEAT]:
            # if we are any doing power generation (only power, or CHP),
            # we need to instantiate the surface plant object based on the user input
            if self.surfaceplant.plant_type.value == PlantType.SUB_CRITICAL_ORC:
                self.surfaceplant = SurfacePlantSubcriticalOrc(self)
            elif self.surfaceplant.plant_type.value == PlantType.SUPER_CRITICAL_ORC:
                self.surfaceplant = SurfacePlantSupercriticalOrc(self)
            elif self.surfaceplant.plant_type.value == PlantType.SINGLE_FLASH:
                self.surfaceplant = SurfacePlantSingleFlash(self)
            else: # default is double flash
                self.surfaceplant = SurfacePlantDoubleFlash(self)

        else:   # direct use heat only style physical plant
            if self.surfaceplant.plant_type.value == PlantType.ABSORPTION_CHILLER:
                self.surfaceplant = SurfacePlantAbsorptionChiller(self)
            elif self.surfaceplant.plant_type.value == PlantType.HEAT_PUMP:
                self.surfaceplant = SurfacePlantHeatPump(self)
            elif self.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
                self.surfaceplant = SurfacePlantDistrictHeating(self)
            elif self.surfaceplant.plant_type.value == PlantType.RTES:
                self.surfaceplant = SurfacePlantSUTRA(self)
            else:
                self.surfaceplant = SurfacePlantIndustrialHeat(self)

        # re-read the parameters for the newly instantiated surface plant
        self.surfaceplant.read_parameters(self)

        # if end-use option is 8 (district heating), some calculations are required prior to the reservoir and wellbore simulations
        if self.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
            self.surfaceplant.CalculateDHDemand(self)  # calculate district heating demand

        self.logger.info(f'complete {str(__class__)}: {__name__}')

    def Calculate(self):
        """
        The Calculate function is where all the calculations are made.  This is handled on a class-by-class basis.
        The Calculate function does not return anything, but it does store the results in self.reserv, self.wellbores
         and self.surfaceplant for later use by other functions.
        :return: None
        """
        self.logger.info(f'Init {__class__}: {__name__}')
        # calculate the results
        self.logger.info("Run calculations for the elements of the Model")

        # This is where all the calculations are made using all the values that have been set.
        # This is handled on a class-by-class basis

        self.reserv.Calculate(self)  # model the reservoir
        self.wellbores.Calculate(self)  # model the wellbores
        self.surfaceplant.Calculate(self)  # model the surfaceplant

        # in case of district heating, the surface plant module may have updated the utilization factor,
        # and therefore we need to recalculate the modules reservoir, wellbore and surface plant.
        # 1 iteration should be sufficient.
        if self.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
            self.reserv.Calculate(self)  # model the reservoir
            self.wellbores.Calculate(self)  # model the wellbores
            self.surfaceplant.Calculate(self)  # model the surfaceplant

        self.economics.Calculate(self)  # model the economics

        self.logger.info(f'complete {__class__}: {__name__}')

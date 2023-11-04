import sys
import logging
import time
import logging.config
from typing import Tuple

from geophires_x.OptionList import EndUseOptions
from geophires_x.Parameter import Parameter
from geophires_x.GeoPHIRESUtils import read_input_file
from geophires_x.WellBores import WellBores
from geophires_x.SurfacePlant import SurfacePlant
from geophires_x.Economics import Economics
from geophires_x.Outputs import Outputs


class Model(object):
    """
    Model is the container class of the application, giving access to everything else, including the logger
    """

    def __init__(self, enable_geophires_logging_config=True):
        """
        The __init__ function is called automatically every time the class is being used to create a new object.

        The self parameter is a Python convention. It must be included in each function definition
        and points to the current instance of the class (the object that is being created).

        :param self: Reference the class instance itself
        :return: Nothing
        :doc-author: Malcolm Ross
        """

        # get logging started
        self.logger = logging.getLogger('root')

        if enable_geophires_logging_config:
            logging.config.fileConfig('logging.conf')
            self.logger.setLevel(logging.INFO)

        self.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')

        # keep track of execution time
        self.tic = time.time()

        # declare some dictionaries
        self.InputParameters = {}  # dictionary to hold all the input parameter the user wants to change

        # This should give us a dictionary with all the parameters the user wants to set.
        # Should be only those value that they want to change from the default.
        # we do this as soon as possible because what we instantiate may depend on settings in this file
        read_input_file(self.InputParameters, logger=self.logger)

        self.ccuseconomics = None
        self.ccusoutputs = None
        self.sdacgtoutputs = None
        self.sdacgteconomics = None
        self.addoutputs = None
        self.addeconomics = None

        # these are database operation we aren't doing yet
        # model_elements = self.RunStoredProcedure("model_elements", [1])
        # model_connections = self.RunStoredProcedure("model_connections", [1])
        # self.RunStoredProcedure("delete_model", [14])
        # self.RunStoredProcedure("add_new_model", ["dummy", "new", 999])

        # Initiate the elements of the Model
        # this is where you can change what class get initiated - the superclass, or one of the subclasses
        self.logger.info("Initiate the elements of the Model")
        # we need to decide which reservoir to instantiate based on the user input (InputParameters),
        # which we just read above for the first time
        from .TDPReservoir import TDPReservoir as TDPReservoir
        self.reserv = TDPReservoir(self)  # Default is Thermal drawdown percentage model (GETEM)
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

        if self.InputParameters['End-Use Option'].sValue == '9' and self.InputParameters['Reservoir Model'].sValue == '7':
            #if we use SUTRA output for simulating reservoir thermal energy storage, we use a special wellbore object that can handle SUTRA data
            del self.wellbores
            from geophires_x.SUTRAWellBores import SUTRAWellBores as SUTRAWellBores
            self.wellbores = SUTRAWellBores(self)

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

        :param self: Access the variables and other functions of the class
        :return: None
        :doc-author: Malcolm Ross
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

        self.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def Calculate(self):
        """
        The Calculate function is where all the calculations are made.  This is handled on a class-by-class basis.

        The Calculate function does not return anything, but it does store the results in self.reserv, self.wellbores
         and self.surfaceplant for later use by other functions.

        :param self: Access the class variables
        :return: None
        :doc-author: Malcolm Ross
        """
        self.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')
        # calculate the results
        self.logger.info("Run calculations for the elements of the Model")

        # This is where all the calculations are made using all the values that have been set.
        # This is handled on a class-by-class basis
        # We choose not to call calculate of the parent, but rather let the child handle the
        # call to the parent if it is needed

        # if end-use option is 8 (district heating), some calculations are required prior to the reservoir and wellbore simulations
        if self.surfaceplant.enduseoption.value == EndUseOptions.DISTRICT_HEATING:
            self.surfaceplant.CalculateDHDemand(self)  # calculate district heating demand

        self.reserv.Calculate(self)  # model the reservoir
        self.wellbores.Calculate(self)  # model the wellbores
        self.surfaceplant.Calculate(self)  # model the surfaceplant

        # in case of district heating, the surface plant module may have updated the utilization factor,
        # and therefore we need to recalculate the modules reservoir, wellbore and surface plant.
        # 1 iteration should be sufficient.
        if self.surfaceplant.enduseoption.value == EndUseOptions.DISTRICT_HEATING:
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

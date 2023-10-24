import sys
import geophires_x.Model as Model
import geophires_x.AdvGeoPHIRESUtils as AdvGeoPHIRESUtils


class AdvModel(Model, AdvGeoPHIRESUtils):
    """
    AdvModel is the container class of the advanced elements of the application,
    giving access to everything optional, including the logger
    """

    def __init__(self):
        """
        The __init__ function is called automatically every time the class is being used to create
        a new object.
        The self parameter is a Python convention. It must be included in each function
        definition and points to the current instance of the class (the object that is being created).
        :param self: Reference the class instance itself
        :return: Nothing
        :doc-author: Malcolm Ross
        """
        super().__init__()  # initialize the parent parameters and variables

        self.ccuseconomics = None
        self.ccusoutputs = None
        self.sdacgtoutputs = None
        self.sdacgteconomics = None
        self.addoutputs = None
        self.addeconomics = None
        model_elements = self.RunStoredProcedure("model_elements", [1])
        model_connections = self.RunStoredProcedure("model_connections", [1])
        self.RunStoredProcedure("delete_model", [14])
        self.RunStoredProcedure("add_new_model", ["dummy", "new", 999])

        # We don't initiate the optional elements here because we don't know if the user wants to use
        # them or not - we won't know that until we read the parameters (in the next step)

        self.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def read_parameters(self) -> None:
        """
        The read_parameters function reads the parameters from the input file and stores them
        in a dictionary.
        :param self: Access the variables and other functions of the class
        :return: None
        :doc-author: Malcolm Ross
        """
        self.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)
        super().read_parameters()  # read the parent parameters and variables

        # Deal with all the parameter values that the user has provided.  This is handled on a class-by-class basis.
        self.logger.info("Read parameters for the newer elements of the Model and instantiate new attributes as needed")

        if self.wellbores.IsAGS.value:
            # If we are doing AGS, we need to replace the various objects we with versions of the objects
            # that have AGS functionality.
            # that means importing them, initializing them, then reading their parameters
            self.logger.info("Initiate the AGS elements")
            from geophires_x import CylindricalReservoir
            del self.reserv  # delete the original object so we can replace it
            self.reserv = CylindricalReservoir.CylindricalReservoir(self)
            import AGSWellBores
            del self.wellbores
            self.wellbores = AGSWellBores.AGSWellBores(self)
            import AGSSurfacePlant
            del self.surfaceplant
            self.surfaceplant = AGSSurfacePlant.AGSSurfacePlant(self)
            import AGSEconomics
            del self.economics
            self.economics = AGSEconomics.AGSEconomics(self)
            del self.outputs
            import AGSOutputs
            self.outputs = AGSOutputs.AGSOutputs(self)

            self.logger.info("Read the parameters for the AGS elements")
            self.reserv.read_parameters(self)
            self.wellbores.read_parameters(self)
            self.surfaceplant.read_parameters(self)
            self.economics.read_parameters(self)
            self.outputs.read_parameters(self)

        # if we find out we have an add-ons, we need to instantiate it, then read for the parameters
        if self.economics.DoAddOnCalculations.value:
            self.logger.info("Initiate the Add-on elements")
            import EconomicsAddOns  # do this only is user wants add-ons
            self.addeconomics = EconomicsAddOns.EconomicsAddOns(self)
            import OutputsAddOns
            self.addeconomics.read_parameters(self)
            self.addoutputs = OutputsAddOns.OutputsAddOns(self)
            self.addoutputs.read_parameters(self)
            # if we find out we have a ccus, we need to instantiate it, then read for the parameters
        if self.economics.DoCCUSCalculations.value:
            self.logger.info("Initiate the CCUS elements")
            import EconomicsCCUS  # do this only is user wants CCUS
            self.ccuseconomics = EconomicsCCUS.EconomicsCCUS(self)
            self.ccuseconomics.read_parameters(self)
            import OutputsCCUS
            self.ccusoutputs = OutputsCCUS.OutputsCCUS(self)
            self.ccusoutputs.read_parameters(self)
            # if we find out we have an S-DAC-GT calculation, we need to instantiate it,
            # then read for the parameters
        if self.economics.DoSDACGTCalculations.value:
            self.logger.info("Initiate the S-DAC-GT elements")
            import EconomicsS_DAC_GT  # do this only is user wants S-DAC-GT
            self.sdacgteconomics = EconomicsS_DAC_GT.EconomicsS_DAC_GT(self)
            self.sdacgteconomics.read_parameters(self)
            import OutputsS_DAC_GT
            self.sdacgtoutputs = OutputsS_DAC_GT.OutputsS_DAC_GT(self)
            self.sdacgtoutputs.read_parameters(self)

        self.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def Calculate(self):
        """
        The Calculate function is where all the calculations are made.  This is handled on a
        class-by-class basis.
        The Calculate function does not return anything, but it does store the results in
        self.reserv, self.wellbores, self.surfaceplant, and self.economics (and their children)
        for later use by other functions.
        :param self: Access the class variables
        :return: None
        :doc-author: Malcolm Ross
        """
        self.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        # This is where all the calculations are made using all the values that have been set.
        # This is handled on a class-by-class basis
        # We choose not to call calculate of the parent, but rather let the child handle the
        # call to the parent if it is needed.

        # Reservoir
        self.SmartCalculate(self, self.reserv)

        # WellBores
        self.SmartCalculate(self, self.wellbores)

        # SurfacePlant
        self.SmartCalculate(self, self.surfaceplant)

        # Economics
        self.SmartCalculate(self, self.economics)

        if self.economics.DoAddOnCalculations.value:
            self.SmartCalculate(self, self.addeconomics)
        if self.economics.DoCCUSCalculations.value:
            self.SmartCalculate(self, self.ccuseconomics)
        if self.economics.DoSDACGTCalculations.value:
            self.SmartCalculate(self, self.sdacgteconomics)

        self.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def __str__(self):
        return "AdvModel"

import sys
from .Parameter import strParameter
from .Units import *
import geophires_x.Model as Model
from .Reservoir import Reservoir


class UPPReservoir(Reservoir):
    """
    This class models the User Provided Profile Reservoir.
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

        self.filenamereservoiroutput = self.ParameterDict[self.filenamereservoiroutput.Name] = strParameter(
            "Reservoir Output File Name",
            value='ReservoirOutput.txt',
            UnitType=Units.NONE,
            ErrMessage="assume default reservoir output file name (ReservoirOutput.txt)",
            ToolTipText="File name of reservoir output in case reservoir model 5 is selected"
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

        model.reserv.Tresoutput.value[0] = model.reserv.Trock.value
        try:
            with open(model.reserv.filenamereservoiroutput.value, encoding='UTF-8') as f:
                contentprodtemp = f.readlines()
        except:
            model.logger.critical('Error: GEOPHIRES could not read reservoir output file ('
                                  + model.reserv.filenamereservoiroutput.value+') and will abort simulation.')
            print('Error: GEOPHIRES could not read reservoir output file ('
                  + model.reserv.filenamereservoiroutput.value+') and will abort simulation.')
            sys.exit()
        numlines = len(contentprodtemp)
        if numlines != model.surfaceplant.plantlifetime.value*model.economics.timestepsperyear.value+1:
            model.logging.critical('Error: Reservoir output file ('
                                   + model.reserv.filenamereservoiroutput.value +
                                   ') does not have required ' +
                                   str(model.surfaceplant.plantlifetime.value*model.economics.timestepsperyear.value+1) +
                                   ' lines. GEOPHIRES will abort simulation.')
            print('Error: Reservoir output file (' +
                  model.reserv.filenamereservoiroutput.value+') does not have required ' +
                  str(model.surfaceplant.plantlifetime.value*model.economics.timestepsperyear.value+1) +
                  ' lines. GEOPHIRES will abort simulation.')
            sys.exit()
        for i in range(0, numlines-1):
            model.reserv.Tresoutput.value[i] = float(contentprodtemp[i].split(',')[1].strip('\n'))

        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

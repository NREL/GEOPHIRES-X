# copyright, 2023, Malcolm I Ross
import sys
import os
import geophires_x.AdvModel as Model
from .Reservoir import Reservoir as Reservoir


class AdvReservoir(Reservoir):
    """
    AdvReservoir Child class of Reservoir; it is the same, but has advanced functionality
    """

    def __init__(self, model: Model):
        """
        The __init__ function is called automatically every time the class is instantiated.
        This function sets up all the parameters that will be used by this class, and also creates
        temporary variables that are available to all classes but not read in by user or used for Output.

        :param self: Reference the object instance to itself
        :param model (AdvModel): The container class of the application, giving access to
        everything else, including the logger
        :return: None
        :doc-author: Malcolm Ross
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        # Initialize the superclass first
        super().__init__(model)
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = os.path.abspath(__file__)

        # These dictionaries contain a list of all the parameters set in this object, stored as
        # "Parameter" and OutputParameter Objects.
        # This will allow us later to access them in a user interface and get that list, along with
        # unit type, preferred units, etc.
        # They already contain the values of the parent because the parent was
        # initialized (line above).  You can add your own items here.
        #        self.ParameterDict = model.reserv.ParameterDict
        #        self.OutputParameterDict = model.reserv.OutputParameterDict

        # Set up all the Parameters that will be predefined by this class using the different types of
        # parameter classes.
        # Setting up includes giving it a name, a default value, The Unit Type (length, volume,
        # temperature, etc.) and Unit Name of that value,
        # sets it as required (or not), sets allowable range, the error message if that range
        # is exceeded, the ToolTip Text, and the name of teh class that created it.
        # This includes setting up temporary variables that will be available to all the class
        # but noy read in by user, or used for Output
        # This also includes all Parameters that are calculated and then published using the
        # Printouts function.
        # If you choose to subclass this master class, you can do so before or after you
        # create your own parameters.
        # If you do, you can also choose to call this method from you class, which will
        # effectively add and set all these parameters to your class.

        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def read_parameters(self, model: Model) -> None:
        """
        The read_parameters function is called by the model to read in all the parameters that have
        been set for this object.
        It loops through all the parameters that have been set for this object, looking for ones
        that match those of this class.
         If it finds a match, it reads in and sets those values.

        :param self: Access variables that belong to the class
        :param model: The container class of the application, giving access to everything else,
        including the logger
        :return: Nothing
        :doc-author: Malcolm Ross
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)
        super().read_parameters(model)  # read the parameters for the parent.
        # if we call super, we don't need to deal with setting the parameters here, just deal with
        # the special cases for the variables in this class
        # because the call to the super.readparameters will set all the variables, including
        # the ones that are specific to this class
        # handle special cases for the parameters you added

        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def Calculate(self, model: Model) -> None:
        """
        The Calculate function is the main function that runs all the calculations for this child.

        :param self: Reference the class itself
        :param model: The container class of the application, giving access to everything else,
         including the logger
        :return: None
        :doc-author: Malcolm Ross
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)
        super().Calculate(model)  # run super calculation
        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def __str__(self):
        return "ImpermeableReservoir"

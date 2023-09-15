import sys
import math
from .Parameter import floatParameter
from .Units import *
import geophires_x.Model as Model
from .Reservoir import Reservoir


class SFReservoir(Reservoir):
    """
    This class models the Single Fracture Reservoir.
    """
    def __init__(self, model:Model):
        """
        The __init__ function is called automatically when a class is instantiated.
        It initializes the attributes of an object, and sets default values for certain arguments that can be
        overridden by user input.
        :param self: Store data that will be used by the class
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: None
        :doc-author: Malcolm Ross
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)
        super().__init__(model)   # initialize the parent parameters and variables
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")

        # Set up all the Parameters that will be predefined by this class using the different types of parameter classes.
        # Setting up includes giving it a name, a default value, The Unit Type (length, volume, temperature, etc)
        # and Unit Name of that value, sets it as required (or not), sets allowable range, the error message if that
        # range is exceeded, the ToolTip Text, and the name of teh class that created it.
        # This includes setting up temporary variables that will be available to all the class but noy read in by user,
        # or used for Output
        # This also includes all Parameters that are calculated and then published using the Printouts function.
        # If you choose to subclass this master class, you can do so before or after you create your own parameters.
        # If you do, you can also choose to call this method from you class, which will effectively add
        # and set all these parameters to your class.
        self.drawdp = self.ParameterDict[self.drawdp.Name] = floatParameter(
            "Drawdown Parameter",
            value=0.005,
            DefaultValue=0.005,
            Min=0,
            Max=0.2,
            UnitType=Units.DRAWDOWN,
            PreferredUnits=DrawdownUnit.PERYEAR,
            CurrentUnits=DrawdownUnit.PERYEAR,
            ErrMessage="assume default drawdown parameter",
            ToolTipText="specify the thermal drawdown for reservoir model 3 and 4"
        )

        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def __str__(self):
        return "LHSReservoir"

    def read_parameters(self, model: Model) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary created by reading the user-provided file
         nd updates the parameter values for this object.
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
        # if we call super, we don't need to deal with setting the parameters here,
        # just deal with the special cases for the variables in this class
        # because the call to the super.readparameters will set all the variables,
        # including the ones that are specific to this class
        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def Calculate(self, model:Model):
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)
        super().Calculate(model)    # run calculation for the parent.

        model.reserv.Tresoutput.value[0] = model.reserv.Trock.value
        for i in range(1, len(model.reserv.timevector.value)):
            model.reserv.Tresoutput.value[i] = math.erf(1. / model.reserv.drawdp.value / model.reserv.cpwater.value *
                                                        math.sqrt(model.reserv.krock.value*model.reserv.rhorock.value *
                                                        model.reserv.cprock.value/model.reserv.timevector.value[i] /
                                                        (365. * 24. * 3600.))) *\
                                                        (model.reserv.Trock.value - model.wellbores.Tinj.value) +\
                                                        model.wellbores.Tinj.value

        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

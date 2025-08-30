import sys

from mpmath import mp, MPContext, exp, sqrt, tanh
import numpy as np

import geophires_x.Model as Model
from .Parameter import intParameter
from .Reservoir import Reservoir
from .Units import Units


class MPFReservoir(Reservoir):
    """
    This class models the Multiple Parallel Fractures Reservoir. It is a subclass of the Reservoir class.
    It inherits all the methods and attributes of that class, and can override them as necessary.
    It also has its own methods and attributes that are unique to this class.
    """

    # noinspection PyUnresolvedReferences,PyProtectedMember
    def __init__(self, model: Model):
        """
        The __init__ function is called automatically when a class is instantiated.
        It initializes the attributes of an object, and sets default values for certain arguments
        that can be overridden by user input.
        Set up all the Parameters that will be predefined by this class using the different types of parameter classes.
        Setting up includes giving it a name, a default value, The Unit Type (length, volume, temperature, etc)
        and Unit Name of that value, sets it as required (or not), sets allowable range,
        the error message if that range is exceeded, the ToolTip Text, and the name of teh class that created it.
        This includes setting up temporary variables that will be available to all the class but noy read in by user,
        or used for Output
        This also includes all Parameters that are calculated and then published using the Printouts function.
        If you choose to subclass this master class, you can do so before or after you create your own parameters.
        If you do, you can also choose to call this method from you class,
        which will effectively add and set all these parameters to your class.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        model.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')

        super().__init__(model)  # initialize the parent parameters and variables
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")

        max_allowed_precision = 15
        self.gringarten_stehfest_precision = self.ParameterDict[self.gringarten_stehfest_precision.Name] = intParameter(
            'Gringarten-Stehfest Precision',
            DefaultValue=15,
            AllowableRange=list(range(8, max_allowed_precision + 1)),
            UnitType=Units.NONE,
            Required=False,
            ToolTipText='Sets the numerical precision (decimal places) for the Stehfest '
                        'algorithm used for the inverse Laplace transform.'
        )


        model.logger.info(f'Complete {str(__class__)}: {sys._getframe().f_code.co_name}')

    def __str__(self):
        return "MPFReservoir"

    # noinspection PyUnresolvedReferences,PyProtectedMember
    def read_parameters(self, model: Model) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary created by reading the user-provided file
        and updates the parameter values for this object.
        The function reads in all parameters that relate to this object, including those that are inherited from other
        objects. It then updates any of these parameter values that have been changed by the user.
        It also handles any special cases.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        model.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')
        # if we call super, we don't need to deal with setting the parameters here,
        # just deal with the special cases for the variables in this class
        # because the call to the super.readparameters will set all the variables,
        # including the ones that are specific to this class
        super().read_parameters(model)  # read the parameters for the parent.

        model.logger.info(f'Complete {str(__class__)}: {sys._getframe().f_code.co_name}')

    # noinspection SpellCheckingInspection,PyUnresolvedReferences,PyProtectedMember
    def Calculate(self, model: Model):
        """
        The Calculate function calculates the values of all the parameters that are calculated by this object.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        model.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')
        super().Calculate(model)  # run calculate for the parent.

        # convert flowrate to volumetric rate
        q = model.wellbores.nprod.value * model.wellbores.prodwellflowrate.value / model.reserv.rhowater.value  # m^3/s

        # specify Laplace-space function
        fp = lambda s: (1. / s) * exp(-sqrt(s) * tanh((model.reserv.rhowater.value * model.reserv.cpwater.value * (
                q / model.reserv.fracnumbcalc.value / model.reserv.fracwidthcalc.value) * (
                                                               model.reserv.fracsepcalc.value / 2.) / (
                                                               2. * model.reserv.krock.value * model.reserv.fracheightcalc.value)) * sqrt(s)))

        # calculate non-dimensional time
        td = ((model.reserv.rhowater.value * model.reserv.cpwater.value) ** 2 / (4 * model.reserv.krock.value * model.reserv.rhorock.value * model.reserv.cprock.value) *
              (q / float(model.reserv.fracnumbcalc.value) / model.reserv.fracwidthcalc.value / model.reserv.fracheightcalc.value) ** 2 *
              model.reserv.timevector.value * 365. * 24. * 3600)

        # calculate non-dimensional temperature array
        Twnd = []
        try:
            dps = mp.dps
            if self.gringarten_stehfest_precision.Provided:
                dps = self.gringarten_stehfest_precision.value

            for t in range(1, len(model.reserv.timevector.value)):
                # Twnd = Twnd + [float(invertlaplace(fp, td[t], method='stehfest'))]
                Twnd = Twnd + [float(_thread_safe_invertlaplace_stehfest(fp, td[t], dps))]

        except Exception as e_:
            msg = (f'Error: GEOPHIRES could not execute numerical inverse laplace calculation for reservoir model 1 '
                   f'({self.gringarten_stehfest_precision.Name} = {dps}). '
                   'Simulation will abort.')
            print(msg)
            raise RuntimeError(msg) from e_

        Twnd = np.asarray(Twnd)

        # calculate dimensional temperature, add initial rock temperature to beginning of array
        model.reserv.Tresoutput.value = model.reserv.Trock.value - (Twnd * (model.reserv.Trock.value - model.wellbores.Tinj.value))
        model.reserv.Tresoutput.value = np.append([model.reserv.Trock.value], model.reserv.Tresoutput.value)

        model.logger.info(f'Complete {str(__class__)}: {sys._getframe().f_code.co_name}')


# noinspection SpellCheckingInspection
def _thread_safe_invertlaplace_stehfest(fp, t, dps):
    """
    Calculates the inverse Laplace transform at a specific precision
    without modifying the global mpmath context.

    Args:
        fp: The Laplace-space function.
        t: The time at which to evaluate the inverse transform.
        dps: The desired decimal places of precision for this calculation.

    Returns:
        The result of the inverse Laplace transform.
    """
    # Create a local, temporary context object.
    local_ctx = MPContext()

    # Set the desired precision *only* on this local context.
    local_ctx.dps = dps

    # Call invertlaplace from the local_ctx object. It will use its own
    # precision when instantiating the stehfest method internally.
    return local_ctx.invertlaplace(fp, t, method='stehfest')

import sys
import os
import math
from functools import lru_cache
import numpy as np
import geophires_x.Model as Model
from .Parameter import floatParameter, OutputParameter
from .Units import *
from .Reservoir import *


class CylindricalReservoir(Reservoir):
    """
    The CylindricalReservoir class is a subclass of the Reservoir class in a straightforward conduction-only model.

    It inherits from the primary Reservoir model but offers new parameters and calculations.

    .. list-table:: Input Parameters
       :widths: 25 50 10 10 10 10 25
       :header-rows: 1

       * - Name
         - Description
         - Default Value Type
         - Default Value
         - Min
         - Max
         - Preferred Units
       * - Cylindrical Reservoir Input Depth
         - Depth of the inflow end of a cylindrical reservoir.
         - float
         - 3.0
         - 0.1
         - 15
         - LengthUnit.KILOMETERS
       * - Cylindrical Reservoir Output Depth
         - Depth of the outflow end of a cylindrical reservoir
         - float
         - Input Depth
         - 0.1
         - 15
         - LengthUnit.KILOMETERS
       * - Reservoir Length
         - Length of cylindrical reservoir
         - float
         - 4.0
         - 0.1
         - 10.0
         - LengthUnit.KILOMETERS
       * - Cylindrical Reservoir Radius of Effect
         - The radius of effect - the distance into the rock from the center of the cylinder that will be perturbed by at least 1 C
         - float
         - 30.0
         - 0
         - 1000.0
         - LengthUnit.METERS
       * - Cylindrical Reservoir Radius of Effect Factor
         - The radius of effect reduction factor accounts for the fact that we cannot extract 100% of the heat in the cylinder.
         - float
         - 1.0
         - 0.0
         - 10.0
         - PercentUnit.TENTH

    .. list-table:: Output Parameters
       :widths: 25 20 20
       :header-rows: 1

       * - Name
         - Default Value Type
         - Preferred Units
       * - Cylindrical Reservoir Surface Area
         - float
         - METERS2
       * - Average Gradient
         - float
         - dEGC/KM
       * - Time Vector
         - float array
         - YEAR
       * - Reservoir Temperature History
         - float array
         - CELSIUS


    :doc-author: Malcolm Ross
    """
    def __init__(self, model:Model):
        """
        The __init__ function is called automatically when a class is instantiated.
        It initializes the attributes of an object, and sets default values for certain arguments that can be
         overridden by user input.
        The __init__ function is used to set up all the parameters in the Reservoir.

        :param self: Store data that will be used by the class
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: None
        :doc-author: Malcolm Ross
        """
        model.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')
        super().__init__(model)   # initialize the parent parameters and variables

        # Set up all the Parameters that will be predefined by this class using the different types of parameter classes.
        # Setting up includes giving it a name, a default value, The Unit Type (length, volume, temperature, etc)
        # and Unit Name of that value, sets it as required (or not), sets allowable range, the error message
        # if that range is exceeded, the ToolTip Text, and the name of teh class that created it.
        # This includes setting up temporary variables that will be available to all the class but noy read in by user,
        # or used for Output
        # This also includes all Parameters that are calculated and then published using the Printouts function.
        # If you choose to subclass this master class, you can do so before or after you create your own parameters.
        # If you do, you can also choose to call this method from you class, which will effectively add and set all
        # these parameters to your class.

        self.InputDepth = self.ParameterDict[self.InputDepth.Name] = floatParameter(
            "Cylindrical Reservoir Input Depth",
            value=3.0,
            DefaultValue=3.0,
            Min=0.1,
            Max=15,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.KILOMETERS,
            CurrentUnits=LengthUnit.KILOMETERS,
            Required=True,
            ErrMessage="assume default cylindrical reservoir depth (3 km)",
            ToolTipText="Depth of the inflow end of a cylindrical reservoir"
        )

        self.OutputDepth = self.ParameterDict[self.OutputDepth.Name] = floatParameter(
            "Cylindrical Reservoir Output Depth",
            value=self.InputDepth.value,
            DefaultValue=self.InputDepth.value,
            Min=0.1,
            Max=15,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.KILOMETERS,
            CurrentUnits=LengthUnit.KILOMETERS,
            Required=True,
            ErrMessage="assume default cyclindrical reservoir input depth (3 km)",
            ToolTipText="Depth of the outflow end of a cyclindrical reservoir"
        )
        self.Length = self.ParameterDict[self.Length.Name] = floatParameter(
            "Cylindrical Reservoir Length",
            value=4.0,
            DefaultValue=4.0,
            Min=0.1,
            Max=10.0,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.KILOMETERS,
            CurrentUnits=LengthUnit.KILOMETERS,
            Required=True,
            ErrMessage="assume default cylindrical reservoir length (4 km)",
            ToolTipText="Length of cylindrical reservoir"
        )
        self.RadiusOfEffect = self.ParameterDict[self.RadiusOfEffect.Name] = floatParameter(
            "Cylindrical Reservoir Radius of Effect",
            value=30.0,
            DefaultValue=30.0,
            Min=0,
            Max=1000.0,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.METERS,
            CurrentUnits=LengthUnit.METERS,
            ErrMessage="assume default cylindrical reservoir radius of effect (30 m)",
            ToolTipText="The radius of effect - the distance into the rock from the center of the cylinder that will" +
                        " be perturbed by at least 1 C"
        )
        self.RadiusOfEffectFactor = self.ParameterDict[self.RadiusOfEffectFactor.Name] = floatParameter(
            "Cylindrical Reservoir Radius of Effect Factor",
            value=1.0,
            DefaultValue=1.0,
            Min=0.0, Max=10.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default cyclindrical reservoir radius of effect reduction factor (0.1)",
            ToolTipText="The radius of effect reduction factor - to account for the fact that we cannot extract 100%" +
                        " of the heat in the cylinder."
        )

        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = os.path.abspath(__file__)
        # internal values required for calculations
        self.depth = self.ParameterDict[self.depth.Name] = floatParameter(
            "Drilled length",
            value=0.0,
            DefaultValue=0.0,
            Min=0.0,
            Max=150,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.KILOMETERS,
            CurrentUnits=LengthUnit.KILOMETERS,
            Required=True,
            ErrMessage="assume default cyclindrical reservoir depth (3 km)",
            ToolTipText="Depth of the inflow end of a cyclindrical reservoir"
        )
        self.waterloss = self.ParameterDict[self.waterloss.Name] = floatParameter(
            "Water Loss Fraction",
            value=0.0,
            DefaultValue=0.0,
            Min=0.0, Max=0.99,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default water loss fraction (0)",
            ToolTipText="Fraction of water lost in the reservoir defined as (total geofluid lost)/(total geofluid produced).")

        # Results - used by other objects or printed in output downstream
        self.SurfaceArea = self.OutputParameterDict[self.SurfaceArea.Name] = OutputParameter(
            "Cylindrical Reservoir Surface Area",
            UnitType=Units.AREA,
            PreferredUnits=AreaUnit.METERS2,
            CurrentUnits=AreaUnit.METERS2
        )
        self.averagegradient = self.OutputParameterDict[self.averagegradient.Name] = OutputParameter(
            "averagegradient",
            UnitType=Units.NONE
        )
        self.timevector = self.OutputParameterDict[self.timevector.Name] = OutputParameter(
            "Time Vector",
            value=[],
            UnitType=Units.NONE
        )
        self.Tresoutput = self.OutputParameterDict[self.Tresoutput.Name] = OutputParameter(
            "Reservoir Temperature History",
            value=[],
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS
        )

        model.logger.info(f'Complete {str(__class__)}: {sys._getframe().f_code.co_name}')

    def __str__(self):
        return "CylindricalReservoir"

    def read_parameters(self, model: Model) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary created by reading the user-provided
         file and updates the parameter values for this object.

        The function reads in all the parameters that relate to this object, including those that are inherited
        from other objects. It then updates any of these parameter values that have been changed by the user.
        It also handles any special cases.

        :param self: Reference the class instance (such as it is) from within the class
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: None
        :doc-author: Malcolm Ross
        """
        model.logger.info(f"Init {str(__class__)}: {sys._getframe().f_code.co_name}")
        super().read_parameters(model)
        # if we call super, we don't need to deal with setting the parameters here, just deal with the special cases
        # for the variables in this class
        # because the call to the super.readparameters will set all the variables, including the ones that are
        # specific to this class

        # Deal with all the parameter values that the user has provided.  They should really only provide values
        # that they want to change from the default values, but they can provide a value that is already set because
        # it is a default value set in __init__.  It will ignore those.
        # This also deals with all the special cases that need to be taken care of after a value has been
        # read in and checked.
        # If you choose to subclass this master class, you can also choose to override this method (or not),
        # and if you do, do it before or after you call you own version of this method.  If you do, you can also
        # choose to call this method from you class, which can effectively modify all these
        # superclass parameters in your class.

        if len(model.InputParameters) > 0:
            # loop through all the parameters that the user wishes to set, looking for parameters that match this object
            for item in self.ParameterDict.items():
                ParameterToModify = item[1]
                key = ParameterToModify.Name.strip()
                if key in model.InputParameters:
                    # just handle special cases for this class - the call to super set all thr values,
                    # including the value unique to this class
                    # if input depth is set and not output, assume output is the same as input
                    if ParameterToModify.Name == "Cylindrical Reservoir Input Depth":
                        if "Cylindrical Reservoir Output Depth" not in model.InputParameters:
                            self.OutputDepth.value = self.InputDepth.value
        else:
            model.logger.info("No parameters read because no content provided")
            model.logger.info(f"complete {str(__class__)}: {sys._getframe().f_code.co_name}")

    @lru_cache(maxsize=1024)
    def Calculate(self, model:Model) -> None:
        """
        The Calculate function is where all the calculations are done.

        This function can be called multiple times, and will only recalculate what has changed each time it is called.

        :param self: Access variables that belongs to the class
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: Nothing, but it does make calculations and set values in the model
        :doc-author: Malcolm Ross
        """
        model.logger.info(f"Init {str(__class__)}: {sys._getframe().f_code.co_name}")

        # This is where all the calculations are made using all the values that have been set.
        # If you subclass this class, you can choose to run these calculations before (or after) your calculations,
        # but that assumes you have set all the values that are required for these calculations
        # If you choose to subclass this master class, you can also choose to override this method (or not),
        # and if you do, do it before or after you call you own version of this method.
        # If you do, you can also choose to call this method from you class, which can effectively
        # run the calculations of the superclass, making all the values available to your methods. but you had
        # better have set all the parameters!

        # specify time-stepping vectors
        self.timevector.value = np.linspace(0, model.surfaceplant.plantlifetime.value,
                                            model.economics.timestepsperyear.value*model.surfaceplant.plantlifetime.value)
        self.averagegradient.value = self.gradient.value[0]

        self.Trock.value = self.Tsurf.value + (self.gradient.value[0] * (self.InputDepth.value * 1000.0))
        # initialize with the Initial reservoir temperature
        self.Tresoutput.value = np.array(len(self.timevector.value) * [self.Trock.value])
        # depth in this case is actually the total length of the drilled assembly
        self.depth.value = self.InputDepth.value/1000.0 + self.OutputDepth.value + self.Length.value
        # Total volume of all laterals but hollow cylinder - doesn't include drilled-out area, units = m3
        self.resvolcalc.value = model.wellbores.numnonverticalsections.value * math.pi * (self.Length.value * 1000.0) *\
                                ((pow(self.RadiusOfEffect.value, 2)) - pow(model.wellbores.prodwelldiam.value, 2))
        self.SurfaceArea.value = (2.0 * math.pi * self.RadiusOfEffect.value * (self.Length.value * 1000.0)) +\
                                 (2.0 * math.pi * pow(self.RadiusOfEffect.value, 2))    # m3
        self.InitialReservoirHeatContent.value = (self.RadiusOfEffectFactor.value *
                                                  self.resvolcalc.value*self.rhorock.value*self.cprock.value*
                                                  (self.Trock.value-model.wellbores.Tinj.value))/1E15 # 10^15 J
        self.cpwater.value = heatcapacitywater(model.wellbores.Tinj.value*0.5 +
                                               (self.Trock.value*0.9+model.wellbores.Tinj.value*0.1)*0.5)
        self.rhowater.value = densitywater(model.wellbores.Tinj.value*0.5 +
                                                        (self.Trock.value*0.9+model.wellbores.Tinj.value*0.1)*0.5)

        model.logger.info(f"complete {str(__class__)}: {sys._getframe().f_code.co_name}")

import sys
import os
import math
from functools import lru_cache
import numpy as np
from mpmath import *
from .OptionList import ReservoirModel, FractureShape, ReservoirVolume
from .Parameter import intParameter, floatParameter, strParameter, listParameter, OutputParameter, ReadParameter
from .Units import *
import geophires_x.Model as Model


# user-defined functions
def densitywater(Twater) -> float:
    T = Twater + 273.15
    # water density correlation as used in Geophires v1.2 [kg/m3]
    rhowater = (.7983223 + (1.50896E-3 - 2.9104E-6 * T) * T) * 1E3
    return rhowater


def viscositywater(Twater) -> float:
    # accurate to within 2.5% from 0 to 370 degrees C [Ns/m2]
    muwater = 2.414E-5 * np.power(10, 247.8 / (Twater + 273.15 - 140))
    return muwater


def heatcapacitywater(Twater) -> float:
    # J/kg/K (based on TARB in Geophires v1.2)
    Twater = (Twater + 273.15) / 1000
    A = -203.6060
    B = 1523.290
    C = -3196.413
    D = 2474.455
    E = 3.855326
    # water specific heat capacity in J/kg-K
    cpwater = (A + B * Twater + C * Twater ** 2 + D * Twater ** 3 + E / (Twater ** 2)) / 18.02 * 1000
    return cpwater


class Reservoir:
    """
    This class is the parent class for modeling the Reservoir.
    """

    def __init__(self, model: Model):
        """
        The __init__ function is called automatically when a class is instantiated.
        It initializes the attributes of an object, and sets default values for certain arguments that can be overridden by user input.
        The __init__ function is used to set up all the parameters in the Reservoir.

        :param self: Store data that will be used by the class
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: None
        :doc-author: Malcolm Ross
        """
        model.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')

        # Set up all the Parameters that will be predefined by this class using the different types of parameter classes
        # Setting up includes giving it a name, a default value, The Unit Type (length, volume, temperature, etc) and
        # Unit Name of that value, sets it as required (or not), sets allowable range, the error message if that range
        # is exceeded, the ToolTip Text, and the name of the class that created it.
        # This includes setting up temporary variables that will be available to all the class but noy read in by user,
        # or used for Output
        # This also includes all Parameters that are calculated and then published using the Printouts function.
        # If you choose to subclass this master class, you can do so before or after you create your own parameters.
        # If you do, you can also choose to call this method from you class, which will effectively add and set all
        # these parameters to your class.

        # These dictionaries contain a list of all the parameters set in this object, stored as "Parameter" and
        # OutputParameter Objects.  This will allow us later to access them in a user interface and get that list,
        # along with unit type, preferred units, etc.
        self.ParameterDict = {}
        self.OutputParameterDict = {}

        self.resoption = self.ParameterDict[self.resoption.Name] = intParameter(
            "Reservoir Model",
            value=ReservoirModel.ANNUAL_PERCENTAGE,
            DefaultValue=ReservoirModel.ANNUAL_PERCENTAGE,
            AllowableRange=[0, 1, 2, 3, 4, 5, 6],
            Required=True,
            ErrMessage="run default reservoir model (Thermal Drawdown Percentage Model)",
            ToolTipText="1: Multiple parallel fractures model, 2: 1D linear heat sweep model,  \
            3: m/a single fracture drawdown model, 4: Linear thermal drawdown model, \
            5: Generic user-provided temperature profile, 6: TOUGH2"
        )

        self.depth = self.ParameterDict[self.depth.Name] = floatParameter(
            "Reservoir Depth",
            value=3.0,
            DefaultValue=3.0,
            Min=0.1,
            Max=15,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.KILOMETERS,
            CurrentUnits=LengthUnit.KILOMETERS,
            Required=True,
            ErrMessage="assume default reservoir depth (3 km)",
            ToolTipText="Depth of the reservoir"
        )

        self.Tmax = self.ParameterDict[self.Tmax.Name] = floatParameter(
            "Maximum Temperature",
            value=400.0,
            DefaultValue=400.0,
            Min=50,
            Max=400,
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS,
            Required=True,
            ErrMessage="assume default maximum temperature (400 deg.C)",
            ToolTipText="Maximum allowable reservoir temperature (e.g. due to drill bit or logging tools constraints). \
            GEOPHIRES will cap the drilling depth to stay below this maximum temperature."
        )

        self.numseg = self.ParameterDict[self.numseg.Name] = intParameter(
            "Number of Segments",
            value=1,
            DefaultValue=1,
            AllowableRange=[1, 2, 3, 4],
            UnitType=Units.NONE,
            Required=True,
            ErrMessage="assume default number of segments (1)",
            ToolTipText="Number of rock segments from surface to reservoir depth with specific geothermal gradient"
        )

        self.gradient = self.ParameterDict[self.gradient.Name] = floatParameter(
            "Gradients",
            value=[0.05, 0.0, 0.0, 0.0],
            DefaultValue=[0.05, 0.0, 0.0, 0.0],
            Min=0.0,
            Max=500.0,
            UnitType=Units.TEMP_GRADIENT,
            PreferredUnits=TemperatureGradientUnit.DEGREESCPERKM,
            CurrentUnits=TemperatureGradientUnit.DEGREESCPERKM,
            Required=True,
            ErrMessage="assume default geothermal gradients 1 (50, 0, 0, 0 deg.C/km)",
            ToolTipText="Geothermal gradients"
        )

        self.gradient1 = self.ParameterDict[self.gradient1.Name] = floatParameter(
            "Gradient 1",
            value=0.05,
            DefaultValue=0.05,
            Min=0.0,
            Max=500.0,
            UnitType=Units.TEMP_GRADIENT,
            PreferredUnits=TemperatureGradientUnit.DEGREESCPERKM,
            CurrentUnits=TemperatureGradientUnit.DEGREESCPERKM,
            Required=True,
            ErrMessage="assume default geothermal gradient 1 (50 deg.C/km)",
            ToolTipText="Geothermal gradient 1 in rock segment 1"
        )

        self.gradient2 = self.ParameterDict[self.gradient2.Name] = floatParameter(
            "Gradient 2",
            value=0.0,
            DefaultValue=0.0,
            Min=0.0,
            Max=500.0,
            UnitType=Units.TEMP_GRADIENT,
            PreferredUnits=TemperatureGradientUnit.DEGREESCPERKM,
            CurrentUnits=TemperatureGradientUnit.DEGREESCPERKM,
            Required=True,
            ErrMessage="assume default geothermal gradient 2 (0 deg.C/km)",
            ToolTipText="Geothermal gradient 2 in rock segment 2"
        )

        self.gradient3 = self.ParameterDict[self.gradient3.Name] = floatParameter(
            "Gradient 3",
            value=0.0,
            DefaultValue=0.0,
            Min=0.0,
            Max=500.0,
            UnitType=Units.TEMP_GRADIENT,
            PreferredUnits=TemperatureGradientUnit.DEGREESCPERKM,
            CurrentUnits=TemperatureGradientUnit.DEGREESCPERKM,
            Required=True,
            ErrMessage="assume default geothermal gradient 3 (0 deg.C/km)",
            ToolTipText="Geothermal gradient 3 in rock segment 3"
        )

        self.gradient4 = self.ParameterDict[self.gradient4.Name] = floatParameter(
            "Gradient 4",
            value=0.0,
            DefaultValue=0.0,
            Min=0.0,
            Max=500.0,
            UnitType=Units.TEMP_GRADIENT,
            PreferredUnits=TemperatureGradientUnit.DEGREESCPERKM,
            CurrentUnits=TemperatureGradientUnit.DEGREESCPERKM,
            Required=True,
            ErrMessage="assume default geothermal gradient 4 (0 deg.C/km)",
            ToolTipText="Geothermal gradient 4 in rock segment 4"
        )

        self.layerthickness = self.ParameterDict[self.layerthickness.Name] = listParameter(
            "Thicknesses",
            value=[100_000.0, 0.01, 0.01,
                   0.01, 0.01],
            DefaultValue=[100_000.0,
                          0.01, 0.01,
                          0.01, 0.01],
            Min=0.01,
            Max=100.0,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.KILOMETERS,
            CurrentUnits=LengthUnit.KILOMETERS,
            ErrMessage="assume default layer thicknesses (100,000, 0, 0, 0 km)",
            ToolTipText="Thicknesses of rock segments"
        )

        self.layerthickness1 = self.ParameterDict[self.layerthickness1.Name] = floatParameter(
            "Thickness 1",
            value=2.0,
            DefaultValue=2.0,
            Min=0.01,
            Max=100.0,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.KILOMETERS,
            CurrentUnits=LengthUnit.KILOMETERS,
            ErrMessage="assume default layer thickness 1 (2 km)",
            ToolTipText="Thickness of rock segment 1"
        )

        self.layerthickness2 = self.ParameterDict[self.layerthickness2.Name] = floatParameter(
            "Thickness 2",
            value=0.01,
            DefaultValue=0.01,
            Min=0.01,
            Max=100.0,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.KILOMETERS,
            CurrentUnits=LengthUnit.KILOMETERS,
            ErrMessage="assume default layer thickness 2 (0 km)",
            ToolTipText="Thickness of rock segment 2"
        )

        self.layerthickness3 = self.ParameterDict[self.layerthickness3.Name] = floatParameter(
            "Thickness 3",
            value=0.01,
            DefaultValue=0.01,
            Min=0.01,
            Max=100.0,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.KILOMETERS,
            CurrentUnits=LengthUnit.KILOMETERS,
            ErrMessage="assume default layer thickness 3 (0 km)",
            ToolTipText="Thickness of rock segment 3"
        )

        self.layerthickness4 = self.ParameterDict[self.layerthickness4.Name] = floatParameter(
            "Thickness 4",
            value=0.01,
            DefaultValue=0.01,
            Min=0.01,
            Max=100.0,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.KILOMETERS,
            CurrentUnits=LengthUnit.KILOMETERS,
            ErrMessage="assume default layer thickness 4 (0 km)",
            ToolTipText="Thickness of rock segment 4"
        )

        self.resvoloption = self.ParameterDict[self.resvoloption.Name] = intParameter(
            "Reservoir Volume Option",
            value=ReservoirVolume.RES_VOL_FRAC_NUM,
            DefaultValue=ReservoirVolume.RES_VOL_FRAC_NUM,
            AllowableRange=[1, 2, 3, 4],
            Required=True,
            UnitType=Units.NONE,
            ErrMessage="assume default reservoir volume option",
            ToolTipText="Specifies how the reservoir volume, and fracture distribution (for reservoir models 1 and 2) \
            are calculated. The reservoir volume is used by GEOPHIRES to estimate the stored heat in place. The \
            fracture distribution is needed as input for the EGS fracture-based reservoir models 1 and 2: \
            Specify number of fractures and fracture separation, 2: Specify reservoir volume and fracture separation, \
            3: Specify reservoir volume and number of fractures, 4: Specify reservoir volume only \
            (sufficient for reservoir models 3, 4, 5 and 6)"
        )

        self.fracshape = self.ParameterDict[self.fracshape.Name] = intParameter(
            "Fracture Shape",
            value=FractureShape.CIRCULAR_AREA,
            DefaultValue=FractureShape.CIRCULAR_AREA,
            AllowableRange=[1, 2, 3, 4],
            UnitType=Units.NONE,
            ErrMessage="assume default fracture shape (1)",
            ToolTipText="Specifies the shape of the (identical) fractures in a fracture-based reservoir: \
            1: Circular fracture with known area, 2: Circular fracture with known diameter, \
            3: Square fracture, 4: Rectangular fracture"
        )

        self.fracarea = self.ParameterDict[self.fracarea.Name] = floatParameter(
            "Fracture Area",
            value=250_000.0,
            DefaultValue=250_000.0,
            Min=1,
            Max=1E8,
            UnitType=Units.AREA,
            PreferredUnits=AreaUnit.METERS2,
            CurrentUnits=AreaUnit.METERS2,
            ErrMessage="assume default fracture shape (1)",
            ToolTipText="Effective heat transfer area per fracture"
        )

        self.fracheight = self.ParameterDict[self.fracheight.Name] = floatParameter(
            "Fracture Height",
            value=500.0,
            DefaultValue=500.0,
            Min=1,
            Max=10000,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.METERS,
            CurrentUnits=LengthUnit.METERS,
            ErrMessage="assume default fracture height (500 m)",
            ToolTipText="Diameter (if fracture shape = 2) or height (if fracture shape = 3 or 4) of each fracture"
        )

        self.fracwidth = self.ParameterDict[self.fracwidth.Name] = floatParameter(
            "Fracture Width",
            value=500.0,
            DefaultValue=500.0,
            Min=1,
            Max=10000,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.METERS,
            CurrentUnits=LengthUnit.METERS,
            ErrMessage="assume default fracture width (500 m)",
            ToolTipText="Width of each fracture"
        )

        self.fracnumb = self.ParameterDict[self.fracnumb.Name] = intParameter(
            "Number of Fractures",
            value=10,
            DefaultValue=10,
            AllowableRange=list(range(1, 21, 1)),
            UnitType=Units.NONE,
            ErrMessage="assume default number of fractures (10)",
            ToolTipText="Number of identical parallel fractures in EGS fracture-based reservoir model."
        )

        self.fracsep = self.ParameterDict[self.fracsep.Name] = floatParameter(
            "Fracture Separation",
            value=50.0,
            DefaultValue=50.0,
            Min=1,
            Max=1E4,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.METERS,
            CurrentUnits=LengthUnit.METERS,
            ErrMessage="assume default fracture separation (50 m)",
            ToolTipText="Separation of identical parallel fractures with uniform spatial distribution \
            in EGS fracture-based reservoir"
        )

        self.resvol = self.ParameterDict[self.resvol.Name] = floatParameter(
            "Reservoir Volume",
            value=125_000_000.0,
            DefaultValue=125_000_000.0,
            Min=10,
            Max=1E12,
            UnitType=Units.VOLUME,
            PreferredUnits=VolumeUnit.METERS3,
            CurrentUnits=VolumeUnit.METERS3,
            ErrMessage="assume default reservoir volume (1.25E8 m3)",
            ToolTipText="Geothermal reservoir volume"
        )

        self.waterloss = self.ParameterDict[self.waterloss.Name] = floatParameter(
            "Water Loss Fraction",
            value=0.0,
            DefaultValue=0.0,
            Min=0.0,
            Max=0.99,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default water loss fraction (0)",
            ToolTipText="Fraction of water lost in the reservoir defined as (total geofluid lost)/(total geofluid produced)."
        )

        self.cprock = self.ParameterDict[self.cprock.Name] = floatParameter(
            "Reservoir Heat Capacity",
            value=1000.0,
            DefaultValue=1000.0,
            Min=100,
            Max=10000,
            UnitType=Units.HEAT_CAPACITY,
            PreferredUnits=HeatCapacityUnit.JPERKGPERK,
            CurrentUnits=HeatCapacityUnit.JPERKGPERK,
            Required=True,
            ErrMessage=" assume default reservoir heat capacity (1000 J/kg/K)",
            ToolTipText="Constant and uniform reservoir rock heat capacity"
        )

        self.rhorock = self.ParameterDict[self.rhorock.Name] = floatParameter(
            "Reservoir Density",
            value=2700.0,
            DefaultValue=2700.0,
            Min=100,
            Max=10000,
            UnitType=Units.DENSITY,
            PreferredUnits=DensityUnit.KGPERMETERS3,
            CurrentUnits=DensityUnit.KGPERMETERS3,
            Required=True,
            ErrMessage="assume default reservoir density (2700 kg/m^3)",
            ToolTipText="Constant and uniform reservoir rock density"
        )

        self.krock = self.ParameterDict[self.krock.Name] = floatParameter(
            "Reservoir Thermal Conductivity",
            value=3.0,
            DefaultValue=3.0,
            Min=0.01,
            Max=100,
            UnitType=Units.THERMAL_CONDUCTIVITY,
            PreferredUnits=ThermalConductivityUnit.WPERMPERK,
            CurrentUnits=ThermalConductivityUnit.WPERMPERK,
            ErrMessage="assume default reservoir thermal conductivity (3 W/m/K)",
            ToolTipText="Constant and uniform reservoir rock thermal conductivity"
        )

        self.permrock = self.ParameterDict[self.permrock.Name] = floatParameter(
            "Reservoir Permeability",
            value=1E-13,
            DefaultValue=1E-13,
            Min=1E-20,
            Max=1E-5,
            UnitType=Units.PERMEABILITY,
            PreferredUnits=AreaUnit.METERS2,
            CurrentUnits=AreaUnit.METERS2,
            ErrMessage="assume default reservoir permeability (1E-13 m^2)",
            ToolTipText="Constant and uniform reservoir permeability"
        )

        self.porrock = self.ParameterDict[self.porrock.Name] = floatParameter(
            "Reservoir Porosity",
            value=0.04,
            DefaultValue=0.04,
            Min=0.001,
            Max=0.99,
            UnitType=Units.POROSITY,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default reservoir porosity (0.04)",
            ToolTipText="Constant and uniform reservoir porosity"
        )

        self.Tsurf = self.ParameterDict[self.Tsurf.Name] = floatParameter(
            "Surface Temperature",
            value=15.0,
            DefaultValue=15.0,
            Min=-50,
            Max=50,
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS,
            Required=True,
            ErrMessage="assume default surface temperature (15 deg.C)",
            ToolTipText="Surface temperature used for calculating bottom-hole temperature \
            (with geothermal gradient and reservoir depth)"
        )

        self.usebuiltintough2model = False
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = os.path.abspath(__file__)

        # Results - used by other objects or printed in output downstream - note the first 6 values are copies of the
        # input values.  They are required because it is a bad practice to change input values after the user
        # has assigned them.  Instead, we make new parameters that are copies of the input parameters, but then
        # modify these values - we only use and display the calculated values. This is OK because the calculated value
        # starts a a copy of the input value and only changes if needed.
        self.fracsepcalc = self.OutputParameterDict[self.fracsepcalc.Name] = OutputParameter(
            "Calculated Fracture Separation",
            value=self.fracsep.value,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.METERS,
            CurrentUnits=LengthUnit.METERS
        )

        self.fracnumbcalc = self.OutputParameterDict[self.fracnumbcalc.Name] = OutputParameter(
            "Calculated Number of Fractures",
            value=self.fracnumb.value,
            UnitType=Units.NONE
        )

        self.fracwidthcalc = self.OutputParameterDict[self.fracwidthcalc.Name] = OutputParameter(
            "Calculated Fracture Width",
            value=self.fracwidth.value,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.METERS,
            CurrentUnits=LengthUnit.METERS
        )

        self.fracheightcalc = self.OutputParameterDict[self.fracheightcalc.Name] = OutputParameter(
            "Calculated Fracture Height",
            value=self.fracheight.value,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.METERS,
            CurrentUnits=LengthUnit.METERS
        )

        self.fracareacalc = self.OutputParameterDict[self.fracareacalc.Name] = OutputParameter(
            "Calculated Fracture Area",
            value=self.fracarea.value,
            UnitType=Units.AREA,
            PreferredUnits=AreaUnit.METERS2,
            CurrentUnits=AreaUnit.METERS2
        )

        self.resvolcalc = self.OutputParameterDict[self.resvolcalc.Name] = floatParameter(
            "Calculated Reservoir Volume",
            value=self.resvol.value,
            UnitType=Units.VOLUME,
            PreferredUnits=VolumeUnit.METERS3,
            CurrentUnits=VolumeUnit.METERS3
        )

        self.cpwater = self.OutputParameterDict[self.cpwater.Name] = floatParameter(
            "cpwater",
            value=0.0,
            UnitType=Units.NONE
        )

        self.rhowater = self.OutputParameterDict[self.rhowater.Name] = floatParameter(
            "rhowater",
            value=0.0,
            UnitType=Units.NONE
        )

        self.averagegradient = self.OutputParameterDict[self.averagegradient.Name] = floatParameter(
            "averagegradient",
            value=0.0,
            UnitType=Units.NONE
        )

        self.Trock = self.OutputParameterDict[self.Trock.Name] = OutputParameter(
            Name="Bottom-hole temperature",
            value=-999.9,
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS
        )

        self.InitialReservoirHeatContent = self.OutputParameterDict[
            self.InitialReservoirHeatContent.Name] = OutputParameter(
            Name="Initial Reservoir Heat Content",
            value=-999.9,
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )

        self.timevector = self.OutputParameterDict[self.timevector.Name] = OutputParameter(
            Name="Time Vector",
            value=[],
            UnitType=Units.NONE
        )

        self.Tresoutput = self.OutputParameterDict[self.Tresoutput.Name] = OutputParameter(
            Name="Reservoir Temperature History",
            value=[],
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS
        )

        model.logger.info(f'Complete {str(__class__)}: {sys._getframe().f_code.co_name}')

    def __str__(self):
        return "Reservoir"

    def read_parameters(self, model: Model) -> None:
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

        # Deal with all the parameter values that the user has provided.  They should really only provide values
        # that they want to change from the default values, but they can provide a value that is already set
        # because it is a default value set in __init__.  It will ignore those.
        # This also deals with all the special cases that need to be taken care of
        # after a value has been read in and checked.
        # If you choose to subclass this master class, you can also choose to override this method (or not),
        # and if you do, do it before or after you call you own version of this method.  If you do, you can
        # also choose to call this method from you class, which can effectively modify all these
        # superclass parameters in your class.

        if len(model.InputParameters) > 0:
            # loop through all the parameters that the user wishes to set, looking for parameters that match this object
            for item in self.ParameterDict.items():
                ParameterToModify = item[1]
                key = ParameterToModify.Name.strip()
                if key in model.InputParameters:
                    ParameterReadIn = model.InputParameters[key]
                    # Before we change the parameter, let's assume that the unit preferences will match -
                    # if they don't, the later code will fix this.
                    ParameterToModify.CurrentUnits = ParameterToModify.PreferredUnits
                    ReadParameter(ParameterReadIn, ParameterToModify, model)  # this handles all non-special cases

                    # handle special cases
                    if ParameterToModify.Name == "Reservoir Model":
                        if ParameterReadIn.sValue == '1':
                            # Multiple parallel fractures model (LANL)
                            ParameterToModify.value = ReservoirModel.MULTIPLE_PARALLEL_FRACTURES
                        elif ParameterReadIn.sValue == '2':
                            # Volumetric block model (1D linear heat sweep model (Stanford))
                            ParameterToModify.value = ReservoirModel.LINEAR_HEAT_SWEEP
                        elif ParameterReadIn.sValue == '3':
                            # Drawdown parameter model (Tester)
                            ParameterToModify.value = ReservoirModel.SINGLE_FRACTURE
                        elif ParameterReadIn.sValue == '4':
                            # Thermal drawdown percentage model (GETEM)
                            ParameterToModify.value = ReservoirModel.ANNUAL_PERCENTAGE
                        elif ParameterReadIn.sValue == '5':
                            # Generic user-provided temperature profile
                            ParameterToModify.value = ReservoirModel.USER_PROVIDED_PROFILE
                        else:
                            # TOUGH2 is called
                            ParameterToModify.value = ReservoirModel.TOUGH2_SIMULATOR

                    elif ParameterToModify.Name == "Reservoir Depth":
                        ParameterToModify.value = ParameterToModify.value * 1000
                        ParameterToModify.CurrentUnits = LengthUnit.METERS
                        ParameterToModify.UnitsMatch = False

                    elif ParameterToModify.Name == "Reservoir Volume Option":
                        if ParameterReadIn.sValue == '1':
                            ParameterToModify.value = ReservoirVolume.FRAC_NUM_SEP
                        elif ParameterReadIn.sValue == '2':
                            ParameterToModify.value = ReservoirVolume.RES_VOL_FRAC_SEP
                        elif ParameterReadIn.sValue == '3':
                            ParameterToModify.value = ReservoirVolume.RES_VOL_FRAC_NUM
                        else:
                            ParameterToModify.value = ReservoirVolume.RES_VOL_ONLY

                        if ParameterToModify.value == ReservoirVolume.RES_VOL_ONLY and ParameterToModify.value in [
                            ReservoirModel.MULTIPLE_PARALLEL_FRACTURES, ReservoirModel.LINEAR_HEAT_SWEEP]:
                            ParameterToModify.value = ReservoirVolume.RES_VOL_FRAC_NUM
                            print("Warning: If user-selected reservoir model is 1 or 2, then user-selected \
                            reservoir volume option cannot be 4 but should be 1, 2, or 3. GEOPHIRES will assume \
                            reservoir volume option 3.")
                            model.logger.warning("If user-selected reservoir model is 1 or 2, then user-selected \
                            reservoir volume option cannot be 4 but should be 1, 2, or 3. GEOPHIRES will assume \
                            reservoir volume option 3.")

                    elif ParameterToModify.Name == "Fracture Shape":
                        if ParameterReadIn.sValue == '1':
                            # fracshape = 1  Circular fracture with known area
                            ParameterToModify.value = FractureShape.CIRCULAR_AREA
                        elif ParameterReadIn.sValue == '2':
                            # fracshape = 2  Circular fracture with known diameter
                            ParameterToModify.value = FractureShape.CIRCULAR_DIAMETER
                        elif ParameterReadIn.sValue == '3':
                            # fracshape = 3  Square fracture
                            ParameterToModify.value = FractureShape.SQUARE
                        else:
                            # fracshape = 4  Rectangular fracture
                            ParameterToModify.value = FractureShape.RECTANGULAR

                    elif ParameterToModify.Name.startswith("Gradient"):
                        parts = ParameterReadIn.Name.split(' ')
                        position = int(parts[1]) - 1
                        model.reserv.gradient.value[position] = ParameterToModify.value
                        if model.reserv.gradient.value[position] > 1.0:
                            model.reserv.gradient.value[position] = model.reserv.gradient.value[
                                                                        position] / 1000.0  # convert C/m
                            model.reserv.gradient.CurrentUnits = TemperatureGradientUnit.DEGREESCPERM
                        if model.reserv.gradient.value[position] < 1e-6:
                            # convert 0 C/m gradients to very small number, avoids divide by zero errors later
                            model.reserv.gradient.value[position] = 1e-6

                    elif ParameterToModify.Name.startswith("Thickness"):
                        parts = ParameterReadIn.Name.split(' ')
                        position = int(parts[1]) - 1
                        model.reserv.layerthickness.value[position] = ParameterToModify.value
                        if model.reserv.layerthickness.value[position] < 100.0:
                            model.reserv.layerthickness.value[position] = model.reserv.layerthickness.value[
                                                                              position] * 1000.0  # convert m
                            model.reserv.layerthickness.CurrentUnits = LengthUnit.METERS
                        # set thickness of bottom segment to large number to override lower, unused segments
                        model.reserv.layerthickness.value[position + 1] = 100_000.0

                    elif ParameterToModify.Name.startswith("Fracture Separation"):
                        self.fracsepcalc.value = self.fracsep.value
                    elif ParameterToModify.Name.startswith("Number of Fractures"):
                        self.fracnumbcalc.value = self.fracnumb.value
                    elif ParameterToModify.Name.startswith("Fracture Width"):
                        self.fracwidthcalc.value = self.fracwidth.value
                    elif ParameterToModify.Name.startswith("Fracture Height"):
                        self.fracheightcalc.value = self.fracheight.value
                    elif ParameterToModify.Name.startswith("Fracture Area"):
                        self.fracareacalc.value = self.fracarea.value
                    elif ParameterToModify.Name.startswith("Reservoir Volume"):
                        self.resvolcalc.value = self.resvol.value
        else:
            model.logger.info("No parameters read because no content provided")

        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    @lru_cache(maxsize=1024)
    def Calculate(self, model: Model) -> None:
        """
        The Calculate function is where all the calculations are done.
        This function can be called multiple times, and will only recalculate what has changed each time it is called.

        :param self: Access variables that belongs to the class
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: Nothing, but it does make calculations and set values in the model
        :doc-author: Malcolm Ross
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        # This is where all the calculations are made using all the values that have been set.
        # If you subclass this class, you can choose to run these calculations before (or after) your calculations,
        # but that assumes you have set all the values that are required for these calculations
        # If you choose to subclass this master class, you can also choose to override this method (or not),
        # and if you do, do it before or after you call you own version of this method.  If you do, you can also
        # choose to call this method from you class, which can effectively run the calculations of the superclass,
        # making all thr values available to your methods. but you had n better set all the parameters!

        # calculate fracture geometry
        if self.fracshape.value == FractureShape.CIRCULAR_AREA:
            self.fracheightcalc.value = math.sqrt(4 / math.pi * self.fracareacalc.value)
            self.fracwidthcalc.value = self.fracheightcalc.value
        elif self.fracshape.value == FractureShape.CIRCULAR_DIAMETER:
            self.fracwidthcalc.value = self.fracheightcalc.value
            self.fracareacalc.value = math.pi / 4 * self.fracheightcalc.value * self.fracheightcalc.value
        elif self.fracshape.value == FractureShape.SQUARE:
            self.fracwidthcalc.value = self.fracheightcalc.value
            self.fracareacalc.value = self.fracheightcalc.value * self.fracwidthcalc.value
        elif self.fracshape.value == FractureShape.RECTANGULAR:
            self.fracareacalc.value = self.fracheightcalc.value * self.fracwidthcalc.value

        # calculate reservoir geometry:
        if self.resvoloption.value == ReservoirVolume.FRAC_NUM_SEP:
            self.resvolcalc.value = (self.fracnumbcalc.value - 1) * self.fracareacalc.value * self.fracsepcalc.value
        elif self.resvoloption.value == ReservoirVolume.RES_VOL_FRAC_SEP:
            self.fracnumbcalc.value = self.resvolcalc.value / self.fracareacalc.value / self.fracsepcalc.value + 1
        elif self.resvoloption.value == ReservoirVolume.RES_VOL_FRAC_NUM:
            self.fracsepcalc.value = self.resvol.value / self.fracareacalc.value / (self.fracnumbcalc.value - 1)

        # some additional preprocessing calculations
        # calculate maximum well depth (m)
        intersecttemperature = [1000., 1000., 1000., 1000.]
        if self.numseg.value == 1:
            maxdepth = (self.Tmax.value - self.Tsurf.value) / self.gradient.value[0]
        else:
            maxdepth = 0
            intersecttemperature[0] = self.Tsurf.value + self.gradient.value[0] * self.layerthickness.value[0]
            for i in range(1, self.numseg.value - 1):
                intersecttemperature[i] = intersecttemperature[i - 1] + self.gradient.value[i] * \
                                          self.layerthickness.value[i]
            layerindex = next(loc for loc, val in enumerate(intersecttemperature) if val > self.Tmax.value)
            if layerindex > 0:
                for i in range(0, layerindex):
                    maxdepth = maxdepth + self.layerthickness.value[i]
                maxdepth = maxdepth + (self.Tmax.value - intersecttemperature[layerindex - 1]) / self.gradient.value[
                    layerindex]
            else:
                maxdepth = (self.Tmax.value - self.Tsurf.value) / self.gradient.value[0]

        if self.depth.value > maxdepth:
            self.depth.value = maxdepth

        # calculate initial reservoir temperature
        intersecttemperature = [self.Tsurf.value] + intersecttemperature
        totaldepth = np.append(np.array([0.0]), np.cumsum(self.layerthickness.value))
        temperatureindex = max(loc for loc, val in enumerate(self.depth.value > totaldepth) if val)

#        temperatureindex = max(loc for loc, val in enumerate(self.depth.value > totaldepth) if val is True)
        self.Trock.value = intersecttemperature[temperatureindex] + self.gradient.value[temperatureindex] * \
                           (self.depth.value - totaldepth[temperatureindex])

        # calculate average geothermal gradient
        if self.numseg.value == 1:
            self.averagegradient.value = self.gradient.value[0]
        else:
            self.averagegradient.value = (self.Trock.value - self.Tsurf.value) / self.depth.value

        # specify time-stepping vectors
        self.timevector.value = np.linspace(0, model.surfaceplant.plantlifetime.value,
                                        model.economics.timestepsperyear.value * model.surfaceplant.plantlifetime.value)
        self.Tresoutput.value = np.zeros(len(self.timevector.value))

        # calculate reservoir water properties
        self.cpwater.value = heatcapacitywater(
            model.wellbores.Tinj.value * 0.5 + (self.Trock.value * 0.9 + model.wellbores.Tinj.value * 0.1) * 0.5)
        self.rhowater.value = densitywater(
            model.wellbores.Tinj.value * 0.5 + (self.Trock.value * 0.9 + model.wellbores.Tinj.value * 0.1) * 0.5)

        # temperature gain in injection wells
        model.wellbores.Tinj.value = model.wellbores.Tinj.value + model.wellbores.tempgaininj.value

        # calculate reservoir heat content
        self.InitialReservoirHeatContent.value = self.resvolcalc.value * self.rhorock.value * self.cprock.value * (
            self.Trock.value - model.wellbores.Tinj.value) / 1E15  # 10^15 J

        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

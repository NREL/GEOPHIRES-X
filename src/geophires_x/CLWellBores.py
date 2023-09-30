import math
import sys
import os
import numpy as np
from scipy.interpolate import interpn, interp1d
import geophires_x.Model as Model
from geophires_x.WellBores import *
from .Parameter import floatParameter, intParameter, boolParameter, OutputParameter
from .Units import *

esp2 = 10.0e-10


# ######################################point source/sink solution functions#########################################
def thetaY(self, yt, ye, alpha, t):
    y = 0
    y1 = 0
    i = 0
    while abs(1.0 / math.sqrt(math.pi * alpha * t) * math.exp(
        -(yt + 2 * i * ye) * (yt + 2 * i * ye) / 4.0 / alpha / t)) > esp2:
        i += 1
    k = -1
    while abs(1.0 / math.sqrt(math.pi * alpha * t) * math.exp(
        -(yt + 2 * k * ye) * (yt + 2 * k * ye) / 4.0 / alpha / t)) > esp2:
        k -= 1
    for j in range(i, -1, -1):
        y += 1.0 / math.sqrt(math.pi * alpha * t) * math.exp(-(yt + 2 * j * ye) * (yt + 2 * j * ye) / 4.0 / alpha / t)
    for w in range(k, 0):
        y1 += 1.0 / math.sqrt(math.pi * alpha * t) * math.exp(-(yt + 2 * w * ye) * (yt + 2 * w * ye) / 4.0 / alpha / t)
    return y + y1


def thetaZ(self, zt, ze, alpha, t):
    y = 0
    y1 = 0
    i = 0
    while abs(1.0 / math.sqrt(math.pi * alpha * t) * math.exp(
        -(zt + 2 * i * ze) * (zt + 2 * i * ze) / 4.0 / alpha / t)) > esp2:
        i += 1
    k = -1
    while abs(1.0 / math.sqrt(math.pi * alpha * t) * math.exp(
        -(zt + 2 * k * ze) * (zt + 2 * k * ze) / 4.0 / alpha / t)) > esp2:
        k -= 1
    for j in range(i, -1, -1):
        y += 1.0 / math.sqrt(math.pi * alpha * t) * math.exp(-(zt + 2 * j * ze) * (zt + 2 * j * ze) / 4.0 / alpha / t)
    for w in range(k, 0):
        y1 += 1.0 / math.sqrt(math.pi * alpha * t) * math.exp(-(zt + 2 * w * ze) * (zt + 2 * w * ze) / 4.0 / alpha / t)
    return y + y1


def pointsource(self, yy, zz, yt, zt, ye, ze, alpha, sp, t):
    z = 1.0 / self.rhorock / self.cprock / 4.0 * (self.thetaY(yt - yy, ye, alpha, t) +
                                                  self.thetaY(yt + yy, ye, alpha, t)) * \
        (self.thetaZ(zt - zz, ze, alpha, t) + self.thetaZ(zt + zz, ze, alpha, t)) * math.exp(-sp * t)
    return z


# #############Chebyshev approximation for numerical Laplace transformation integration from 1e-8 to 1e30###########
def Chebyshev(self, a, b, n, yy, zz, yt, zt, ye, ze, alpha, sp, func):
    bma = 0.5 * (b - a)
    bpa = 0.5 * (b + a)
    f = [func(yy, zz, yt, zt, ye, ze, alpha, sp, math.cos(math.pi * (k + 0.5) / n) * bma + bpa) for k in range(n)]
    fac = 2.0 / n
    c = [fac * np.sum([f[k] * math.cos(math.pi * j * (k + 0.5) / n)
                       for k in range(n)]) for j in range(n)]
    con = 0.25 * (b - a)
    fac2 = 1.0
    cint = np.zeros(513)
    summ = 0.0
    for j in range(1, n - 1):
        cint[j] = con * (c[j - 1] - c[j + 1]) / j
        summ += fac2 * cint[j]
        fac2 = -fac2
        cint[n - 1] = con * c[n - 2] / (n - 1)
        summ += fac2 * cint[n - 1]
        cint[0] = 2.0 * summ
    d = 0.0
    dd = 0.0
    y = (2.0 * b - a - b) * (1.0 / (b - a))
    y2 = 2.0 * y
    for j in range(n - 1, 0, -1):
        sv = d
        d = y2 * d - dd + cint[j]
        dd = sv
    return y * d - dd + 0.5 * cint[0]  # Last step is different


def chebeve_pointsource(self, yy, zz, yt, zt, ye, ze, alpha, sp):
    m = 32
    t_1 = 1.0e-8
    n = int(math.log10(1.0e4 / 1.0e-8) + 1)
    # t_2 = t_1 * 10 ** n
    a = t_1
    temp = 0.0
    for i in range(1, n + 1):
        b = a * 10.0
        temp = temp + self.Chebyshev(a, b, m, yy, zz, yt, zt, ye, ze, alpha, sp, self.pointsource)
        a = b
    return temp + (1 / sp * (math.exp(-sp * 1.0e5) - math.exp(-sp * 1.0e30))) / (ye * ze) / self.rhorock / self.cprock


# ###########################Duhamerl convolution method for closed-loop system######################################
def laplace_solution(self, sp, model):
    Toutletl = 0.0
    ss = 1.0 / sp / self.chebeve_pointsource(self.y_well, self.z_well, self.y_well, self.z_well - 0.078,
                                             self.y_boundary, self.z_boundary, self.alpha_rock, sp)

    Toutletl = (self.Tini - self.Tinj.value) / sp * np.exp(
        -sp * ss / self.q_circulation / 24.0 / model.reserv.densitywater(self.Tini) / model.reserv.heatcapacitywater(
            self.Tini) * self.l_pipe.value - sp / self.velocity * self.l_pipe.value)
    return Toutletl


# ###############################Numerical Laplace transformation algorithm#########################
def inverselaplace(self, NL, MM, model):
    V = np.zeros(50)
    Gi = np.zeros(50)
    H = np.zeros(25)
    DLN2 = 0.6931471805599453
    FI = 0.0
    SN = 0.0
    Az = 0.0
    Z = 0.0

    if NL != MM:
        Gi[1] = 1.0
        NH = NL // 2
        SN = 2.0 * (NH % 2) - 1.0

        for i in range(1, NL + 1):
            Gi[i + 1] = Gi[i] * i

        H[1] = 2.0 / Gi[NH]
        for i in range(1, NH + 1):
            FI = i
            H[i] = math.pow(FI, NH) * Gi[2 * i + 1] / Gi[NH - i + 1] / Gi[i + 1] / Gi[i]

        for i in range(1, NL + 1):
            V[i] = 0.0
            KBG = (i + 1) // 2
            temp = NH if i >= NH else i
            KND = temp
            for k in range(KBG, KND + 1):
                V[i] = V[i] + H[k] / Gi[i - k + 1] / Gi[2 * k - i + 1]
            V[i] = SN * V[i]
            SN = -SN
        MM = NL

    FI = 0.0
    Az = DLN2 / self.time_operation.value
    Toutlet = 0.0
    for k in range(1, NL + 1):
        Z = Az * k
        Toutletl = self.laplace_solution(Z, model)
        Toutlet += Toutletl * V[k]
    Toutlet = self.Tini - Az * Toutlet
    return Toutlet


class CLWellBores(WellBores):
    """
    CLWellBores Child class of WellBores; it is the same, but has advanced closed-loop functionality
    """

    def __init__(self, model: Model) -> None:
        """
        The __init__ function is called automatically every time the class is instantiated.
        This function sets up all the parameters that will be used by this class, and also creates temporary variables
        that are available to all classes but not read in by user or used for Output.
        :param self: Reference the object instance to itself
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: None
        :doc-author: Malcolm Ross
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        # Initialize the superclass first to make those variables available
        super().__init__(model)
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = os.path.abspath(__file__)

        self.area = 0.0
        self.q_circulation = 0.0
        self.velocity = 0.0
        self.x_boundary = self.y_boundary = self.z_boundary = self.x_well = self.y_well = self.z_well = 0.0
        self.al = 0.0
        self.time_max = 0.0
        self.rhorock = 0.0
        self.cprock = 0.0
        self.alpha_rock = 0.0
        self.Tini = 0.0
        self.alpha_fluid = 0.0

        # Set up all the Parameters that will be predefined by this class using the different types of
        # parameter classes.  Setting up includes giving it a name, a default value, The Unit Type
        # (length, volume, temperature, etc) and Unit Name of that value, sets it as required (or not),
        # sets allowable range, the error message if that range is exceeded, the ToolTip Text,
        # and the name of teh class that created it.
        # This includes setting up temporary variables that will be available to all the class but noy read in by user,
        # or used for Output
        # This also includes all Parameters that are calculated and then published using the Printouts function.
        # If you choose to subclass this master class, you can do so before or after you create your own parameters.
        # If you do, you can also choose to call this method from you class, which will effectively add and
        # set all these parameters to your class.
        # set up the parameters using the Parameter Constructors (intParameter, floatParameter, strParameter, etc);
        # initialize with their name, default value, and valid range (if int or float).  Optionally, you can specify:
        # Required (is it required to run? default value = False),
        # ErrMessage (what GEOPHIRES will report if the value provided is invalid, "assume default value (see manual)"),
        # ToolTipText (when there is a GIU, this is the text that the user will see, "This is ToolTip Text"),
        # UnitType (the type of units associated with this parameter (length, temperature, density, etc), Units.NONE),
        # CurrentUnits (what the units are for this parameter (meters, celsius, gm/cc, etc, Units:NONE),
        # and PreferredUnits (usually equal to CurrentUnits,
        # but these are the units that the calculations assume when running, Units.NONE
        self.WaterThermalConductivity = self.ParameterDict[self.WaterThermalConductivity.Name] = floatParameter(
            "Water Thermal Conductivity",
            value=0.6,
            DefaultValue=0.6,
            Min=0.0,
            Max=100.0,
            UnitType=Units.THERMAL_CONDUCTIVITY,
            PreferredUnits=ThermalConductivityUnit.WPERMPERK,
            CurrentUnits=ThermalConductivityUnit.WPERMPERK,
            ErrMessage="assume default for water thermal conductivity (0.6 W/m/K)",
            ToolTipText="Water Thermal Conductivity"
        )
        self.l_pipe = self.ParameterDict[self.l_pipe.Name] = floatParameter(
            "Horizontal Wellbore Length",
            value=5000.0,
            DefaultValue=5000.0,
            Min=0.01,
            Max=100_000.0,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.METERS,
            CurrentUnits=LengthUnit.METERS,
            ErrMessage="assume default for Horizontal Wellbore Length (5000.0 m)",
            ToolTipText="Horizontal Wellbore Length"
        )
        self.diameter = self.ParameterDict[self.diameter.Name] = floatParameter(
            "Horizontal Wellbore Diameter",
            value=0.156,
            DefaultValue=0.156,
            Min=0.01,
            Max=100.0,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.METERS,
            CurrentUnits=LengthUnit.METERS,
            ErrMessage="assume default for Horizontal Wellbore Diameter (5000.0 m)",
            ToolTipText="Horizontal Wellbore Diameter"
        )
        self.numhorizontalsections = self.ParameterDict[self.numhorizontalsections.Name] = intParameter(
            "Number of Horizontal Wellbore Sections",
            value=1,
            DefaultValue=1,
            AllowableRange=list(range(0, 101, 1)),
            UnitType=Units.NONE,
            ErrMessage="assume default for Number of Horizontal Wellbore Sections (1)",
            ToolTipText="Number of Horizontal Wellbore Sections"
        )
        self.time_operation = self.ParameterDict[self.time_operation.Name] = floatParameter(
            "Closed Loop Calculation Start Year",
            value=0.01,
            DefaultValue=0.01,
            Min=0.01,
            Max=100.0,
            UnitType=Units.TIME,
            PreferredUnits=TimeUnit.YEAR,
            CurrentUnits=TimeUnit.YEAR,
            ErrMessage="assume default for Closed Loop Calculation Start Year (0.01)",
            ToolTipText="Closed Loop Calculation Start Year"
        )
        self.HorizontalsCased = self.ParameterDict[self.HorizontalsCased.Name] = boolParameter(
            "Horizontals Cased",
            value=False,
            DefaultValue=False,
            Required=False,
            Provided=False,
            Valid=True,
            ErrMessage="assume default value (False)"
        )

        # results are stored here and in the parent ProducedTemperature array
        self.HorizontalProducedTemperature = self.OutputParameterDict[self.ProducedTemperature.Name] = OutputParameter(
            Name="Horizontal Produced Temperature",
            value=[0.0],
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS
        )
        self.HorizontalProducedTemperature.value = [
                                                       0.0] * model.surfaceplant.plantlifetime.value  # initialize the array
        self.HorizontalPressureDrop = self.OutputParameterDict[self.HorizontalPressureDrop.Name] = OutputParameter(
            Name="Horizontal Pressure Drop",
            value=[0.0],
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL
        )
        self.HorizontalPressureDrop.value = [0.0] * model.surfaceplant.plantlifetime.value  # initialize the array
        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def read_parameters(self, model: Model) -> None:
        """
        The read_parameters function is called by the model to read in all the parameters that have been set
        for this object.  It loops through all the parameters that have been set for this object, looking for ones
         that match those of this class.  If it finds a match, it reads in and sets those values.
        :param self: Access variables that belong to the class
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: Nothing
        :doc-author: Malcolm Ross
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)
        super().read_parameters(model)  # read the parameters for the parent.
        # if we call super, we don't need to deal with setting the parameters here,
        # just deal with the special cases for the variables in this class
        # because the call to the super.readparameters will set all the variables,
        # including the ones that are specific to this class

        # handle special cases for the parameters you added
        if self.diameter.value > 2.0:
            self.diameter.value = self.diameter.value * 0.0254
        self.area = math.pi * (self.diameter.value * 0.5) * (self.diameter.value * 0.5)
        # need to convert prodwellflowrate in l/sec to m3/hour and then split the flow equally across all the sections
        self.q_circulation = (self.prodwellflowrate.value / 3.6) / self.numhorizontalsections.value
        self.velocity = self.q_circulation / self.area * 24.0
        # Wanju says it ts OK to make these numbers large - "we consider it is an infinite system"
        self.x_boundary = self.y_boundary = self.z_boundary = 2.0e15
        self.y_well = 0.5 * self.y_boundary  # Horizontal wellbore in the center
        self.z_well = 0.5 * self.z_boundary  # Horizontal wellbore in the center
        self.al = 365.0 / 4.0 * model.economics.timestepsperyear.value
        self.time_max = model.surfaceplant.plantlifetime.value * 365.0
        self.rhorock = model.reserv.rhorock.value
        self.cprock = model.reserv.cprock.value
        self.alpha_rock = model.reserv.krock.value / model.reserv.rhorock.value / model.reserv.cprock.value * 24.0 * 3600.0
        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def Calculate(self, model: Model) -> None:
        """
        The Calculate function is the main function that runs all the calculations for this child.
        :param self: Reference the class itself
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: None
        :doc-author: Malcolm Ross
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        super().Calculate(model)  # run calculation because there was nothing in the database
        # initialize the temperature to be the initial temperature of the reservoir
        self.Tini = model.reserv.Tresoutput.value[0]

        while self.time_operation.value <= self.time_max:
            # MIR figure out how to calculate year ands extract Tini from reserv Tresoutput array
            year = math.trunc(self.time_operation.value / self.al)
            self.HorizontalProducedTemperature.value[year] = inverselaplace(16, 0, model)
            # update alpha_fluid value based on next temperature of reservoir
            self.alpha_fluid = self.WaterThermalConductivity.value / model.reserv.densitywater(
                self.HorizontalProducedTemperature.value[year]) / model.reserv.heatcapacitywater(
                self.HorizontalProducedTemperature.value[year]) * 24.0 * 3600.0
            self.time_operation.value += self.al

        # ------------------------------------------
        # recalculate pressure drops and pumping power
        # ------------------------------------------
        # horizontal wellbore fluid conditions based on current temperature
        rhowater = model.reserv.densitywater(self.HorizontalProducedTemperature.value[year])
        muwater = model.reserv.viscositywater(self.HorizontalProducedTemperature.value[year])
        vhoriz = self.q_circulation / rhowater / (math.pi / 4. * self.diameter.value ** 2)

        # Calculate reynolds number to decide if laminar or turbulent flow.
        Rewaterhoriz = 4. * self.q_circulation / (muwater * math.pi * self.diameter.value)
        if Rewaterhoriz < 2300.0:
            friction = 64. / Rewaterhoriz  # laminar
        else:
            if self.HorizontalsCased:
                relroughness = 1E-4 / self.diameter.value
            else:
                # note the higher relative roughness for uncased horizontal bores
                relroughness = 0.02 / self.diameter.value
            # 6 iterations to converge
            friction = 1. / np.power(-2 * np.log10(relroughness / 3.7 + 5.74 / np.power(Rewaterhoriz, 0.9)), 2.)
            friction = 1. / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewaterhoriz / np.sqrt(friction))), 2.)
            friction = 1. / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewaterhoriz / np.sqrt(friction))), 2.)
            friction = 1. / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewaterhoriz / np.sqrt(friction))), 2.)
            friction = 1. / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewaterhoriz / np.sqrt(friction))), 2.)
            friction = 1. / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewaterhoriz / np.sqrt(friction))), 2.)

            # assume everything stays liquid throughout
            # horizontal section pressure drop [kPa] per lateral section
            # assume no buoyancy effect because laterals are horizontal, or if they are not,
            # they return to the same place, so there is no buoyancy effect
            self.HorizontalPressureDrop.value[year] = friction * (rhowater * vhoriz ** 2 / 2) * (
                self.l_pipe.value / self.diameter.value) / 1E3  # /1E3 to convert from Pa to kPa

        # overall pressure drop  = previous pressure drop (as calculated from the verticals) +
        # horizontal section pressure drop
        # interpolation is required because HorizontalPressureDrop is sampled yearly, and
        # DPOverall is sampled more frequently
        f = interp1d(np.arange(0, len(self.HorizontalPressureDrop.value)), self.HorizontalPressureDrop.value, fill_value="extrapolate")
        self.HorizontalPressureDrop.value = f(np.arange(0, len(self.DPOverall.value), 1))
        model.wellbores.DPOverall.value = model.wellbores.DPOverall.value + self.HorizontalPressureDrop.value

        # recalculate pumping power [MWe] (approximate)
        model.wellbores.PumpingPower.value = model.wellbores.DPOverall.value * self.q_circulation / rhowater / model.surfaceplant.pumpeff.value / 1E3

        # in GEOPHIRES v1.2, negative pumping power values become zero
        # (b/c we are not generating electricity) = thermosiphon is happening!
        model.wellbores.PumpingPower.value = [0. if x < 0. else x for x in self.PumpingPower.value]

        # done with calculations. Now overlay the HorizontalProducedTemperature onto WellBores.ProducedTemperatures
        # - interpolation is required because HorizontalProducedTemperature is sampled yearly,
        # and ProducedTemperature is sampled more frequently
        f = interp1d(np.arange(0, len(self.HorizontalProducedTemperature.value)), self.HorizontalProducedTemperature.value, fill_value="extrapolate")
        model.wellbores.ProducedTemperature.value = f(np.arange(0, len(self.HorizontalProducedTemperature.value),
                                                                1.0 / model.economics.timestepsperyear.value))

        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def __str__(self):
        return "CLWellBores"

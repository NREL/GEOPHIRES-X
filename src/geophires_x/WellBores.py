import sys
import os
import math
import numpy as np
from .Parameter import floatParameter, intParameter, boolParameter, OutputParameter, ReadParameter
from .Reservoir import densitywater, viscositywater
from .Units import *
import geophires_x.Model as Model
from .OptionList import ReservoirModel


# user-defined functions
def vaporpressurewater(Twater: float) -> float:
    """
    calculate the vapor pressure of water based on the temperature of the water
        :param Twater: temperature of the water
        :return: vapor pressure of the water
        :doc-author: Malcolm Ross
    """
    if Twater < 100:
        A = 8.07131
        B = 1730.63
        C = 233.426
    else:
        A = 8.14019
        B = 1810.94
        C = 244.485
    vp = 133.322 * (10 ** (A - B / (C + Twater))) / 1000  # water vapor pressure in kPa using Antione Equation
    return vp


def RameyCalc(krock: float, rhorock: float, cprock: float, welldiam: float, tv, utilfactor: float, flowrate: float,
              cpwater: float, Trock: float, Tresoutput: float, averagegradient: float, depth: float) -> float:
    """
    Calculate teh temperature drop along the length of a well
    this code is only valid so far for 1 gradient and deviation = 0
    For multiple gradients, use Ramey's model for every layer
    assume outside diameter of casing is 10% larger than inside diameter of production pipe (=prodwelldiam)
    assume borehole thermal resistance is negligible to rock thermal resistance
        :param depth:
        :param averagegradient:
        :param Tresoutput:
        :param Trock:
        :param flowrate:
        :param utilfactor:
        :param tv:
        :param welldiam:
        :param cprock:
        :param rhorock:
        :param krock:
        :param cpwater:
        :return: temperature drop
        :doc-author: Malcolm Ross
    """
    alen = len(tv)
    alpharock = krock / (rhorock * cprock)
    framey = np.zeros(alen)
    framey[1:] = -np.log(
        1.1 * (welldiam / 2.0) / np.sqrt(4. * alpharock * tv[1:] * 365.0 * 24.0 * 3600.0 * utilfactor)) - 0.29
    framey[0] = framey[1]  # fource the first value to be the same as the second to get away from near surface effects
    rameyA = flowrate * cpwater * framey / 2 / math.pi / krock
    TempDrop = -((Trock - Tresoutput) - averagegradient * (depth - rameyA) + (
        Tresoutput - averagegradient * rameyA - Trock) * np.exp(-depth / rameyA))

    return TempDrop


def WellPressureDrop(model: Model, Taverage: float, wellflowrate: float, welldiam: float,
                     impedancemodelused: bool, depth: float) -> tuple:
    """
    calculate the pressure drop over the length of the well due to friction or impedance
        :param model:
        :param depth:
        :param impedancemodelused:
        :param welldiam:
        :param wellflowrate:
        :param Taverage:
        :return: tuple of DPWell, f3, v, rhowater
        :doc-author: Malcolm Ross
    """
    # start by calculating wellbore fluid conditions [kPa], noting that most temperature drop happens
    # in upper section (because surrounding rock temperature is lowest in upper section)
    rhowater = densitywater(Taverage)  # replace with correlation based on Tprodaverage
    muwater = viscositywater(Taverage)  # replace with correlation based on Tprodaverage
    v = wellflowrate / rhowater / (math.pi / 4. * welldiam ** 2)
    Rewater = 4.0 * wellflowrate / (muwater * math.pi * welldiam)  # laminar or turbulent flow?
    Rewateraverage = np.average(Rewater)
    if Rewateraverage < 2300.0:
        f3 = 64. / Rewater
    else:
        relroughness = 1E-4 / welldiam
        # 6 iterations to converge
        f3 = 1. / np.power(-2 * np.log10(relroughness / 3.7 + 5.74 / np.power(Rewater, 0.9)), 2.)
        f3 = 1. / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewater / np.sqrt(f3))), 2.)
        f3 = 1. / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewater / np.sqrt(f3))), 2.)
        f3 = 1. / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewater / np.sqrt(f3))), 2.)
        f3 = 1. / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewater / np.sqrt(f3))), 2.)
        f3 = 1. / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewater / np.sqrt(f3))), 2.)

    if impedancemodelused:
        # assumed everything stays liquid throughout; /1E3 to convert from Pa to kPa
        DPWell = f3 * (rhowater * v ** 2 / 2.) * (depth / welldiam) / 1E3
    else:
        DPWell = []  # it will be calculated elsewhere

    return DPWell, f3, v, rhowater


def InjectionWellPressureDrop(model: Model, Taverage: float, wellflowrate: float, welldiam: float,
                              impedancemodelused: bool, depth: float, nprod: int, ninj: int, waterloss: float) -> tuple:
    """
    calculate the injection well pressure drop over the length of the well due to friction or impedance
        :param self:
        :param model:
        :param depth:
        :param impedancemodelused:
        :param welldiam:
        :param wellflowrate:
        :param Taverage:
        :param waterloss:
        :param ninj:
        :param nprod:
        :return: tuple of DPWell, f1, v, rhowater
        :doc-author: Malcolm Ross
    """
    # start by calculating wellbore fluid conditions [kPa], noting that most temperature drop happens in
    # upper section (because surrounding rock temperature is lowest in upper section)
    rhowater = densitywater(Taverage) * np.linspace(1, 1, len(model.wellbores.ProducedTemperature.value))
    # replace with correlation based on Tinjaverage
    muwater = viscositywater(Taverage) * np.linspace(1, 1, len(model.wellbores.ProducedTemperature.value))
    v = nprod / ninj * wellflowrate * (1.0 + waterloss) / rhowater / (math.pi / 4. * welldiam ** 2)
    Rewater = 4. * nprod / ninj * wellflowrate * (1.0 + waterloss) / (
        muwater * math.pi * welldiam)  # laminar or turbulent flow?
    Rewateraverage = np.average(Rewater)
    if Rewateraverage < 2300.:  # laminar flow
        f1 = 64. / Rewater
    else:  # turbulent flow
        relroughness = 1E-4 / welldiam
        # 6 iterations to converge
        f1 = 1. / np.power(-2 * np.log10(relroughness / 3.7 + 5.74 / np.power(Rewater, 0.9)), 2.)
        f1 = 1. / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewater / np.sqrt(f1))), 2.)
        f1 = 1. / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewater / np.sqrt(f1))), 2.)
        f1 = 1. / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewater / np.sqrt(f1))), 2.)
        f1 = 1. / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewater / np.sqrt(f1))), 2.)
        f1 = 1. / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewater / np.sqrt(f1))), 2.)

    if impedancemodelused:
        # assumed everything stays liquid throughout, calculate well pressure drop [kPa]; /1E3 to convert from Pa to kPa
        DPWell = f1 * (rhowater * v ** 2 / 2) * (depth / welldiam) / 1E3
    else:
        DPWell = []  # it will be calculated elsewhere

    return DPWell, f1, v, rhowater


def ProdPressureDropsAndPumpingPowerUsingImpedenceModel(f3: float, vprod: float, rhowaterinj: float,
                                                        rhowaterprod: float, rhowaterreservoir: float, depth: float,
                                                        wellflowrate: float, prodwelldiam: float,
                                                        impedance: float, nprod: int, waterloss: float,
                                                        pumpeff: float) -> tuple:
    """
    Calculate Pressure Drops and Pumping Power needed for the production well using the Impedance Model
        :param depth:
        :param wellflowrate:
        :param waterloss:
        :param nprod:
        :param pumpeff:
        :param impedance:
        :param prodwelldiam:
        :param rhowaterreservoir:
        :param rhowaterprod:
        :param rhowaterinj:
        :param vprod:
        :param f3:
        :return: tuple of DPOverall, PumpingPower, DPProdWell, DPReserv, DPBouyancy
        :doc-author: Malcolm Ross
    """
    # production well pressure drops [kPa]
    DPProdWell = f3 * (rhowaterprod * vprod ** 2 / 2.) * (depth / prodwelldiam) / 1E3  # /1E3 to convert from Pa to kPa

    # reservoir pressure drop [kPa]
    DPReserv = impedance * nprod * wellflowrate * 1000. / rhowaterreservoir

    # buoyancy pressure drop [kPa]
    DPBouyancy = (rhowaterprod - rhowaterinj) * depth * 9.81 / 1E3  # /1E3 to convert from Pa to kPa

    # overall pressure drop
    DPOverall = DPReserv + DPProdWell + DPBouyancy

    # calculate pumping power [MWe] (approximate)
    PumpingPower = ([0.0] * len(vprod))
    PumpingPower = DPOverall * nprod * wellflowrate * (1 + waterloss) / rhowaterinj / pumpeff / 1E3

    # in GEOPHIRES v1.2, negative pumping power values become zero (b/c we are not generating electricity)
    PumpingPower = [0. if x < 0. else x for x in PumpingPower]

    return DPOverall, PumpingPower, DPProdWell, DPReserv, DPBouyancy


def InjPressureDropsAndPumpingPowerUsingImpedenceModel(f1: float, vinj: float, rhowaterinj: float, depth: float,
                                                       wellflowrate: float, injwelldiam: float, ninj: int,
                                                       waterloss: float, pumpeff: float, DPOverall) -> tuple:
    """
    Calculate Injection well Pressure Drops and Pumping Power needed for the injection well using the Impedance Model
        :param depth:
        :param wellflowrate:
        :param waterloss:
        :param rhowaterinj:
        :param DPOverall:
        :param pumpeff:
        :param ninj:
        :param injwelldiam:
        :param vinj:
        :param f1:
        :return: tuple of newDPOverall, PumpingPower, DPInjWell
        :doc-author: Malcolm Ross
    """
    # Calculate Pressure Drops and Pumping Power needed for the injection well using the Impedance Model
    # injection well pressure drops [kPa]
    DPInjWell = f1 * (rhowaterinj * vinj ** 2 / 2) * (depth / injwelldiam) / 1E3  # /1E3 to convert from Pa to kPa

    # overall pressure drop
    newDPOverall = DPOverall + DPInjWell

    # calculate pumping power [MWe] (approximate)
    PumpingPower = newDPOverall * ninj * wellflowrate * (1 + waterloss) / rhowaterinj / pumpeff / 1E3

    # in GEOPHIRES v1.2, negative pumping power values become zero (b/c we are not generating electricity)
    PumpingPower = [0. if x < 0. else x for x in PumpingPower]

    return newDPOverall, PumpingPower, DPInjWell


def ProdPressureDropAndPumpingPowerUsingIndexes(model: Model, usebuiltinhydrostaticpressurecorrelation: bool,
                                                productionwellpumping: bool, usebuiltinppwellheadcorrelation: bool,
                                                Trock: float, Tsurf: float, depth: float, gradient: float,
                                                ppwellhead: float, PI: float, wellflowrate: float, f3: float,
                                                vprod: float, prodwelldiam: float, nprod: int, pumpeff: float,
                                                rhowaterprod: float) -> tuple:
    """
    Calculate Pressure Drops and Pumping Power needed for the production well using indexes
        :param depth:
        :param wellflowrate:
        :param pumpeff:
        :param rhowaterprod:
        :param nprod:
        :param prodwelldiam:
        :param vprod:
        :param f3:
        :param PI:
        :param ppwellhead:
        :param gradient:
        :param Tsurf:
        :param Trock:
        :param usebuiltinppwellheadcorrelation:
        :param productionwellpumping:
        :param usebuiltinhydrostaticpressurecorrelation:
        :param model:
        :return: tuple of PumpingPower, PumpingPowerProd, DPProdWell, Pprodwellhead
        :doc-author: Malcolm Ross
    """
    # initialize PumpingPower value in case it doesn't get set.
    PumpingPower = PumpingPowerProd = DPProdWell = Pprodwellhead = ([0.0] * len(vprod))

    # reservoir hydrostatic pressure [kPa]
    if usebuiltinhydrostaticpressurecorrelation:
        CP = 4.64E-7
        CT = 9E-4 / (30.796 * Trock ** (-0.552))
        Phydrostaticcalc = 0 + 1. / CP * (math.exp(densitywater(Tsurf) * 9.81 * CP / 1000 * (depth - CT / 2 * gradient * depth ** 2)) - 1)

    if productionwellpumping:
        # [kPa] = 50 psi. Excess pressure covers non-condensable gas pressure and net positive suction head for the pump
        Pexcess = 344.7
        # [kPa] is minimum production pump inlet pressure and minimum wellhead pressure
        Pminimum = vaporpressurewater(Trock) + Pexcess
        if usebuiltinppwellheadcorrelation:
            Pprodwellhead = Pminimum  # production wellhead pressure [kPa]
        else:
            Pprodwellhead = ppwellhead
            if Pprodwellhead < Pminimum:
                Pprodwellhead = Pminimum
                print("Warning: provided production wellhead pressure under minimum pressure. \
                GEOPHIRES will assume minimum wellhead pressure")
                model.logger.warning("Provided production wellhead pressure under minimum pressure. \
                GEOPHIRES will assume minimum wellhead pressure")

        PIkPa = PI / 100.0  # convert PI from kg/s/bar to kg/s/kPa

        # calculate pumping depth
        pumpdepth = depth + (Pminimum - Phydrostaticcalc + wellflowrate / PIkPa) / (
            f3 * (rhowaterprod * vprod ** 2 / 2.) * (1 / prodwelldiam) / 1E3 + rhowaterprod * 9.81 / 1E3)
        pumpdepthfinal = np.max(pumpdepth)
        if pumpdepthfinal < 0.0:
            pumpdepthfinal = 0.0
            print("Warning: GEOPHIRES calculates negative production well pumping depth. \
            No production well pumps will be assumed")
            model.logger.warning(
                "GEOPHIRES calculates negative production well pumping depth. \
                No production well pumps will be assumed")
        elif pumpdepthfinal > 600.0:
            print("Warning: GEOPHIRES calculates production pump depth to be deeper than 600 m. \
            Verify reservoir pressure, production well flow rate and production well dimensions")
            model.logger.warning("GEOPHIRES calculates production pump depth to be deeper than 600 m. \
            Verify reservoir pressure, production well flow rate and production well dimensions")

        # calculate production well pumping pressure [kPa]
        DPProdWell = Pprodwellhead - (Phydrostaticcalc - wellflowrate / PIkPa - rhowaterprod * 9.81 * depth / 1E3 - f3 *
                                      (rhowaterprod * vprod ** 2 / 2.) * (depth / prodwelldiam) / 1E3)
        # [MWe] total pumping power for production wells
        PumpingPowerProd = DPProdWell * nprod * wellflowrate / rhowaterprod / pumpeff / 1E3
        PumpingPowerProd = np.array([0. if x < 0. else x for x in PumpingPowerProd])

    # total pumping power
    if productionwellpumping:
        PumpingPower = PumpingPowerProd

    # negative pumping power values become zero (b/c we are not generating electricity)
    PumpingPower = [0. if x < 0. else x for x in PumpingPower]

    return PumpingPower, PumpingPowerProd, DPProdWell, Pprodwellhead


def InjPressureDropAndPumpingPowerUsingIndexes(model: Model, usebuiltinhydrostaticpressurecorrelation: bool,
                                               productionwellpumping: bool, usebuiltinppwellheadcorrelation: bool,
                                               usebuiltinoutletplantcorrelation: bool, Trock: float, Tsurf: float,
                                               depth: float, gradient: float, ppwellhead: float, II: float,
                                               wellflowrate: float, f1: float, vinj: float, injwelldiam: float,
                                               nprod: int, ninj: int, waterloss: float, pumpeff: float,
                                               rhowaterinj: float, Pplantoutlet: float, PumpingPowerProd) -> tuple:
    """
     Calculate PressureDrops and Pumping Power needed for the injection well using indexes
        :param depth:
        :param wellflowrate:
        :param pumpeff:
        :param nprod:
        :param ppwellhead:
        :param gradient:
        :param Tsurf:
        :param Trock:
        :param usebuiltinppwellheadcorrelation:
        :param productionwellpumping:
        :param usebuiltinhydrostaticpressurecorrelation:
        :param model:
        :param Pplantoutlet:
        :param rhowaterinj:
        :param waterloss:
        :param ninj:
        :param injwelldiam:
        :param vinj:
        :param f1:
        :param usebuiltinoutletplantcorrelation:
        :param PumpingPowerProd:
        :param II:
        :return: tuple of PumpingPower, PumpingPowerInj, DPInjWell, Pplantoutlet, Pprodwellhead
        :doc-author: Malcolm Ross
    """
    PumpingPowerInj = DPInjWell = Pprodwellhead = [0.0]  # initialize value in case it doesn't get set.

    # reservoir hydrostatic pressure [kPa]
    if usebuiltinhydrostaticpressurecorrelation:
        CP = 4.64E-7
        CT = 9E-4 / (30.796 * Trock ** (-0.552))
        Phydrostaticcalc = 0 + 1. / CP * (math.exp(densitywater(Tsurf) * 9.81 * CP / 1000 * (depth - CT / 2 * gradient * depth ** 2)) - 1)

    if productionwellpumping:
        # [kPa] = 50 psi. Excess pressure covers non-condensable gas pressure and net positive suction head for the pump
        Pexcess = 344.7
        # [kPa] is minimum production pump inlet pressure and minimum wellhead pressure
        Pminimum = vaporpressurewater(Trock) + Pexcess
        if usebuiltinppwellheadcorrelation:
            Pprodwellhead = Pminimum  # production wellhead pressure [kPa]
        else:
            Pprodwellhead = ppwellhead
            if Pprodwellhead < Pminimum:
                Pprodwellhead = Pminimum
                print("Warning: provided production wellhead pressure under minimum pressure. \
                GEOPHIRES will assume minimum wellhead pressure")
                model.logger.warning("Provided production wellhead pressure under minimum pressure. \
                GEOPHIRES will assume minimum wellhead pressure")

    IIkPa = II / 100.0  # convert II from kg/s/bar to kg/s/kPa

    # necessary injection wellhead pressure [kPa]
    Pinjwellhead = Phydrostaticcalc + wellflowrate * (
        1 + waterloss) * nprod / ninj / IIkPa - rhowaterinj * 9.81 * depth / 1E3 + f1 * (
                       rhowaterinj * vinj ** 2 / 2) * (depth / injwelldiam) / 1E3

    # plant outlet pressure [kPa]
    if usebuiltinoutletplantcorrelation:
        DPSurfaceplant = 68.95  # [kPa] assumes 10 psi pressure drop in surface equipment
        Pplantoutlet = Pprodwellhead - DPSurfaceplant

    # injection pump pressure [kPa]
    DPInjWell = Pinjwellhead - Pplantoutlet
    # [MWe] total pumping power for injection wells
    PumpingPowerInj = DPInjWell * nprod * wellflowrate * (1 + waterloss) / rhowaterinj / pumpeff / 1E3
    PumpingPowerInj = np.array([0. if x < 0. else x for x in PumpingPowerInj])

    # total pumping power
    if productionwellpumping:
        PumpingPower = PumpingPowerInj + PumpingPowerProd
    else:
        PumpingPower = PumpingPowerInj

    # negative pumping power values become zero (b/c we are not generating electricity)
    PumpingPower = [0. if x < 0. else x for x in PumpingPower]

    return PumpingPower, PumpingPowerInj, DPInjWell, Pplantoutlet, Pprodwellhead


class WellBores:
    def __init__(self, model: Model):
        """
        The __init__ function is the constructor for a class.  It is called whenever an instance of the class is created.
        The __init__ function can take arguments, but self is always the first one. Self refers to the instance of the
         object that has already been created, and it's used to access variables that belong to that object.

        :param self: Reference the class object itself
        :param model: The container class of the application, giving access to everything else, including the logger

        :return: Nothing, and is used to initialize the class
        :doc-author: Malcolm Ross
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)
        self.rhowaterprod = self.rhowaterinj = 0.0

        # Set up all the Parameters that will be predefined by this class using the different types of parameter classes.
        # Setting up includes giving it a name, a default value, The Unit Type (length, volume, temperature, etc.)
        # and Unit Name of that value, sets it as required (or not), sets allowable range, the error message
        # if that range is exceeded, the ToolTip Text, and the name of teh class that created it.
        # This includes setting up temporary variables that will be available to all the class but noy read in by user,
        # or used for Output
        # This also includes all Parameters that are calculated and then published using the Printouts function.
        # If you choose to subclass this master class, you can do so before or after you create your own parameters.
        # If you do, you can also choose to call this method from you class, which will effectively add and set all
        # these parameters to your class.

        # These dictionaries contain a list of all the parameters set in this object, stored as "Parameter" and
        # OutputParameter Objects.  This will alow us later to access them in a user interface and get that list,
        # along with unit type, preferred units, etc.
        self.ParameterDict = {}
        self.OutputParameterDict = {}

        self.nprod = self.ParameterDict[self.nprod.Name] = intParameter(
            "Number of Production Wells",
            value=2,
            DefaultValue=2,
            AllowableRange=list(range(1, 201, 1)),
            UnitType=Units.NONE,
            Required=True,
            ErrMessage="assume default number of production wells (2)",
            ToolTipText="Number of (identical) production wells"
        )
        self.ninj = self.ParameterDict[self.ninj.Name] = intParameter(
            "Number of Injection Wells",
            value=2,
            DefaultValue=2,
            AllowableRange=list(range(0, 201, 1)),
            UnitType=Units.NONE,
            Required=True,
            ErrMessage="assume default number of injection wells (2)",
            ToolTipText="Number of (identical) injection wells"
        )
        self.prodwelldiam = self.ParameterDict[self.prodwelldiam.Name] = floatParameter(
            "Production Well Diameter",
            value=8.0,
            DefaultValue=8.0,
            Min=1.,
            Max=30.,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.INCHES,
            CurrentUnits=LengthUnit.INCHES,
            Required=True,
            ErrMessage="assume default production well diameter (8 inch)",
            ToolTipText="Inner diameter of production wellbore (assumed constant along the wellbore) to calculate \
            frictional pressure drop and wellbore heat transmission with Rameys model"
        )
        self.injwelldiam = self.ParameterDict[self.injwelldiam.Name] = floatParameter(
            "Injection Well Diameter",
            value=8.0,
            DefaultValue=8.0,
            Min=1.,
            Max=30.,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.INCHES,
            CurrentUnits=LengthUnit.INCHES,
            Required=True,
            ErrMessage="assume default injection well diameter (8 inch)",
            ToolTipText="Inner diameter of production wellbore (assumed constant along the wellbore) to calculate \
            frictional pressure drop and wellbore heat transmission with Rameys model"
        )
        self.rameyoptionprod = self.ParameterDict[self.rameyoptionprod.Name] = boolParameter(
            "Ramey Production Wellbore Model",
            value=True,
            DefaultValue=True,
            UnitType=Units.NONE,
            Required=True,
            ErrMessage="assume default production wellbore model (Ramey model active)",
            ToolTipText="Select whether to use Rameys model to estimate the geofluid temperature drop in the \
            production wells"
        )
        self.tempdropprod = self.ParameterDict[self.tempdropprod.Name] = floatParameter(
            "Production Wellbore Temperature Drop",
            value=5.0,
            DefaultValue=5.0,
            Min=-5.,
            Max=50.,
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS,
            ErrMessage="assume default production wellbore temperature drop (5 deg.C)",
            ToolTipText="Specify constant production well geofluid temperature drop in case Rameys model is disabled."
        )
        self.tempgaininj = self.ParameterDict[self.tempgaininj.Name] = floatParameter(
            "Injection Wellbore Temperature Gain",
            value=0.0,
            DefaultValue=0.0,
            Min=-5.,
            Max=50.,
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS,
            ErrMessage="assume default injection wellbore temperature gain (0 deg.C)",
            ToolTipText="Specify constant injection well geofluid temperature gain."
        )
        self.prodwellflowrate = self.ParameterDict[self.prodwellflowrate.Name] = floatParameter(
            "Production Flow Rate per Well",
            value=50.0,
            DefaultValue=50.0,
            Min=1.,
            Max=500.,
            UnitType=Units.FLOWRATE,
            PreferredUnits=FlowRateUnit.KGPERSEC,
            CurrentUnits=FlowRateUnit.KGPERSEC,
            ErrMessage="assume default flow rate per production well (50 kg/s)",
            ToolTipText="Geofluid flow rate per production well."
        )
        self.impedance = self.ParameterDict[self.impedance.Name] = floatParameter(
            "Reservoir Impedance",
            value=1000.0,
            DefaultValue=1000.0,
            Min=1E-4,
            Max=1E4,
            UnitType=Units.IMPEDANCE,
            PreferredUnits=ImpedanceUnit.GPASPERM3,
            CurrentUnits=ImpedanceUnit.GPASPERM3,
            ErrMessage="assume default reservoir impedance (0.1 GPa*s/m^3)",
            ToolTipText="Reservoir resistance to flow per well-pair. For EGS-type reservoirs when the injection well \
            is in hydraulic communication with the production well, this parameter specifies the overall pressure drop \
            in the reservoir between injection well and production well (see docs)"
        )
        self.wellsep = self.ParameterDict[self.wellsep.Name] = floatParameter(
            "Well Separation",
            value=1000.0,
            DefaultValue=1000.0,
            Min=10.,
            Max=10000.,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.METERS,
            CurrentUnits=LengthUnit.INCHES,
            ErrMessage="assume default well separation (1000 m)",
            ToolTipText="Well separation for built-in TOUGH2 doublet reservoir model"
        )
        self.Tinj = self.ParameterDict[self.Tinj.Name] = floatParameter(
            "Injection Temperature",
            value=70.0,
            DefaultValue=70.0,
            Min=0.,
            Max=200.,
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS,
            Required=True,
            ErrMessage="assume default injection temperature (70 deg.C)",
            ToolTipText="Constant geofluid injection temperature at injection wellhead."
        )
        self.Phydrostatic = self.ParameterDict[self.Phydrostatic.Name] = floatParameter(
            "Reservoir Hydrostatic Pressure",
            value=1E2,
            DefaultValue=1E2,
            Min=1E2,
            Max=1E5,
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL,
            ErrMessage="calculate reservoir hydrostatic pressure using built-in correlation",
            ToolTipText="Reservoir hydrostatic far-field pressure.  Default value is calculated with built-in modified \
            Xie-Bloomfield-Shook equation (DOE, 2016)."
        )
        self.ppwellhead = self.ParameterDict[self.ppwellhead.Name] = floatParameter(
            "Production Wellhead Pressure",
            value=101.3200 + 344.7,
            DefaultValue=101.3200 + 344.7,
            Min=0.0,
            Max=1E4,
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL,
            ErrMessage="using Water vapor pressure (101.3200; at 100 C) + 344.7 kPa (50 psi).",
            ToolTipText="Constant production wellhead pressure; Required if specifying productivity index"
        )
        self.II = self.ParameterDict[self.II.Name] = floatParameter(
            "Injectivity Index",
            value=10.0,
            DefaultValue=10.0,
            Min=1E-2,
            Max=1E4,
            UnitType=Units.INJECTIVITY_INDEX,
            PreferredUnits=InjectivityIndexUnit.KGPERSECPERBAR,
            CurrentUnits=InjectivityIndexUnit.KGPERSECPERBAR,
            ErrMessage="assume default injectivity index (10 kg/s/bar)",
            ToolTipText="Injectivity index defined as ratio of injection well flow rate over injection well outflow \
            pressure drop (flowing bottom hole pressure - hydrostatic reservoir pressure)."
        )
        self.PI = self.ParameterDict[self.PI.Name] = floatParameter(
            "Productivity Index",
            value=10.0,
            DefaultValue=10.0,
            Min=1E-2,
            Max=1E4,
            UnitType=Units.PRODUCTIVITY_INDEX,
            PreferredUnits=ProductivityIndexUnit.KGPERSECPERBAR,
            CurrentUnits=ProductivityIndexUnit.KGPERSECPERBAR,
            ErrMessage="assume default productivity index (10 kg/s/bar)",
            ToolTipText="Productivity index defined as ratio of production well flow rate over production well inflow \
            pressure drop (see docs)"
        )
        self.maxdrawdown = self.ParameterDict[self.maxdrawdown.Name] = floatParameter(
            "Maximum Drawdown",
            value=1.0,
            DefaultValue=1.0,
            Min=0.0,
            Max=1.000001,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default maximum drawdown (1)",
            ToolTipText="Maximum allowable thermal drawdown before redrilling of all wells into new reservoir \
            (most applicable to EGS-type reservoirs with heat farming strategies). E.g. a value of 0.2 means that \
            all wells are redrilled after the production temperature (at the wellhead) has dropped by 20% of \
            its initial temperature"
        )
        self.IsAGS = self.ParameterDict[self.IsAGS.Name] = boolParameter(
            "Is AGS",
            value=False,
            DefaultValue=False,
            UnitType=Units.NONE,
            Required=False,
            ErrMessage="assume default is not AGS",
            ToolTipText="Set to true if the model is for an Advanced Geothermal System (AGS)"
        )

        # local variable initiation
        self.Pinjwellhead = 0.0
        self.usebuiltinhydrostaticpressurecorrelation = True
        self.usebuiltinppwellheadcorrelation = True
        self.Pminimum = 0.0
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = os.path.abspath(__file__)

        # Results - used by other objects or printed in output downstream
        self.Phydrostaticcalc = self.OutputParameterDict[self.Phydrostaticcalc.Name] = floatParameter(
            Name="Calculated Reservoir Hydrostatic Pressure",
            value=self.Phydrostatic.value,
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL
        )
        self.redrill = self.OutputParameterDict[self.redrill.Name] = OutputParameter(
            Name="redrill",
            value=0,
            UnitType=Units.NONE
        )
        self.PumpingPowerProd = self.OutputParameterDict[self.PumpingPowerProd.Name] = OutputParameter(
            Name="PumpingPowerProd",
            value=[0.0],
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )
        self.PumpingPowerInj = self.OutputParameterDict[self.PumpingPowerInj.Name] = OutputParameter(
            Name="PumpingPowerInj",
            value=[0.0],
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )
        self.pumpdepth = self.OutputParameterDict[self.pumpdepth.Name] = OutputParameter(
            Name="pumpdepth",
            value=[0.0],
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.METERS,
            CurrentUnits=LengthUnit.METERS
        )
        self.impedancemodelallowed = self.OutputParameterDict[self.impedancemodelallowed.Name] = OutputParameter(
            Name="impedancemodelallowed",
            value=True,
            UnitType=Units.NONE
        )
        self.productionwellpumping = self.OutputParameterDict[self.productionwellpumping.Name] = OutputParameter(
            Name="productionwellpumping",
            value=True,
            UnitType=Units.NONE
        )
        self.impedancemodelused = self.OutputParameterDict[self.impedancemodelused.Name] = OutputParameter(
            Name="impedancemodelused",
            value=False,
            UnitType=Units.NONE
        )
        self.ProdTempDrop = self.OutputParameterDict[self.ProdTempDrop.Name] = OutputParameter(
            Name="Production Well Temperature Drop",
            value=[0.0],
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS
        )
        self.DPOverall = self.OutputParameterDict[self.DPOverall.Name] = OutputParameter(
            Name="Total Pressure Drop",
            value=[0.0],
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL
        )
        self.DPInjWell = self.OutputParameterDict[self.DPInjWell.Name] = OutputParameter(
            Name="Injection Well Pressure Drop",
            value=[0.0],
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL
        )
        self.DPReserv = self.OutputParameterDict[self.DPReserv.Name] = OutputParameter(
            Name="Reservoir Pressure Drop",
            value=[0.0],
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL
        )
        self.DPProdWell = self.OutputParameterDict[self.DPProdWell.Name] = OutputParameter(
            Name="Production Well Pump Pressure Drop",
            value=[0.0],
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL
        )
        self.DPBouyancy = self.OutputParameterDict[self.DPBouyancy.Name] = OutputParameter(
            Name="Bouyancy Pressure Drop",
            value=[0.0],
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL
        )
        self.ProducedTemperature = self.OutputParameterDict[self.ProducedTemperature.Name] = OutputParameter(
            Name="Produced Temperature",
            value=[0.0],
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS
        )
        self.PumpingPower = self.OutputParameterDict[self.PumpingPower.Name] = OutputParameter(
            Name="Pumping Power",
            value=[0.0],
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )
        self.Pprodwellhead = self.OutputParameterDict[self.Pprodwellhead.Name] = OutputParameter(
            Name="Production wellhead pressure",
            value=-999.0,
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL
        )

        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def __str__(self):
        return "WellBores"

    def read_parameters(self, model: Model) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary and stores them in the parameters.
          It also handles special cases that need to be handled after a value has been read in and checked.
            If you choose to subclass this master class, you can also choose to override this method (or not).
        :param self: Access variables that belong to a class
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: None
        :doc-author: Malcolm Ross
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        # Deal with all the parameter values that the user has provided.  They should really only provide values that
        # they want to change from the default values, but they can provide a value that is already set because it is a
        # default value set in __init__.  It will ignore those.
        # This also deals with all the special cases that need to be taken care of after a value has been
        # read in and checked.
        # If you choose to subclass this master class, you can also choose to override this method (or not),
        # and if you do, do it before or after you call you own version of this method.  If you do, you can also choose
        # to call this method from you class, which can modify all these superclass parameters in your class.

        if len(model.InputParameters) > 0:
            # loop through all the parameters that the user wishes to set, looking for parameters that match this object
            for item in self.ParameterDict.items():
                ParameterToModify = item[1]
                key = ParameterToModify.Name.strip()
                if key in model.InputParameters:
                    ParameterReadIn = model.InputParameters[key]
                    # Before we change the parameter, let's assume that the unit preferences will match
                    # - if they don't, the later code will fix this.
                    ParameterToModify.CurrentUnits = ParameterToModify.PreferredUnits
                    ReadParameter(ParameterReadIn, ParameterToModify, model)  # this should handle all non-special cases

                    # handle special cases
                    # impedance: impedance per well pair (input as GPa*s/m^3 and converted to KPa/kg/s
                    # (assuming 1000 for density; density will be corrected for later))
                    if ParameterToModify.Name == "Reservoir Impedance":
                        # shift it by a constant to make the units right, per line 619 of GEOPHIRES 2
                        self.impedance.value = self.impedance.value * (1E6 / 1E3)
                        self.impedancemodelused.value = True
                        if self.impedance.Provided is False:
                            self.impedancemodelused.value = False
                    elif ParameterToModify.Name == "Reservoir Hydrostatic Pressure":
                        if ParameterToModify.value == -1:
                            self.usebuiltinhydrostaticpressurecorrelation = True
                        else:
                            self.usebuiltinhydrostaticpressurecorrelation = False
                    elif ParameterToModify.Name == "Production Wellhead Pressure":
                        if ParameterToModify.value == -1.0:
                            self.usebuiltinppwellheadcorrelation = True
                        else:
                            self.usebuiltinppwellheadcorrelation = False
        else:
            model.logger.info("No parameters read because no content provided")
        model.logger.info("read parameters complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

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
        # making all thr values available to your methods. but you had better have set all the parameters!

        # special case: production and injection well diameters are input as inches and call calculations
        # assume meters! Check and change if needed, assuming anything > 2 must be talking about inches
        if self.injwelldiam.value > 2.0:
            self.injwelldiam.value = self.injwelldiam.value * 0.0254
            self.injwelldiam.CurrentUnits = LengthUnit.METERS
            self.injwelldiam.UnitsMatch = False
        if self.prodwelldiam.value > 2.0:
            self.prodwelldiam.value = self.prodwelldiam.value * 0.0254
            self.prodwelldiam.CurrentUnits = LengthUnit.METERS
            self.prodwelldiam.UnitsMatch = False

        # calculate wellbore temperature drop
        self.ProdTempDrop.value = self.tempdropprod.value  # if not Ramey, hard code a user-supplied temperature drop.
        if self.rameyoptionprod.value:
            if hasattr(model.reserv, "InputDepth"):
                d = model.reserv.InputDepth.value
            else:
                d = model.reserv.depth.value
            self.ProdTempDrop.value = RameyCalc(model.reserv.krock.value,
                                                model.reserv.rhorock.value,
                                                model.reserv.cprock.value,
                                                self.prodwelldiam.value, model.reserv.timevector.value,
                                                model.surfaceplant.utilfactor.value, self.prodwellflowrate.value,
                                                model.reserv.cpwater.value, model.reserv.Trock.value,
                                                model.reserv.Tresoutput.value, model.reserv.averagegradient.value,
                                                d)

        self.ProducedTemperature.value = model.reserv.Tresoutput.value - self.ProdTempDrop.value

        # redrilling
        # only applies to the built-in analytical reservoir models
        if model.reserv.resoption.value in \
            [ReservoirModel.MULTIPLE_PARALLEL_FRACTURES, ReservoirModel.LINEAR_HEAT_SWEEP,
             ReservoirModel.SINGLE_FRACTURE, ReservoirModel.ANNUAL_PERCENTAGE]:
            indexfirstmaxdrawdown = np.argmax(self.ProducedTemperature.value < (1 - model.wellbores.maxdrawdown.value) *
                                              self.ProducedTemperature.value[0])
            if indexfirstmaxdrawdown > 0:  # redrilling necessary
                self.redrill.value = int(np.floor(len(self.ProducedTemperature.value) / indexfirstmaxdrawdown))
                ProducedTemperatureRepeatead = np.tile(self.ProducedTemperature.value[0:indexfirstmaxdrawdown],
                                                       self.redrill.value + 1)
                self.ProducedTemperature.value = ProducedTemperatureRepeatead[0:len(self.ProducedTemperature.value)]

        # calculate pressure drops and pumping power
        self.DPProdWell.value, f3, vprod, self.rhowaterprod = WellPressureDrop(
            model, model.reserv.Tresoutput.value - self.ProdTempDrop.value / 4.0, self.prodwellflowrate.value,
            self.prodwelldiam.value, self.impedancemodelused.value, model.reserv.depth.value)
        self.DPInjWell.value, f1, vinj, self.rhowaterinj = InjectionWellPressureDrop(
            model, self.Tinj.value, self.prodwellflowrate.value, self.injwelldiam.value, self.impedancemodelused.value,
            model.reserv.depth.value, self.nprod.value, self.ninj.value, model.reserv.waterloss.value)

        if self.impedancemodelused.value:  # assumed everything stays liquid throughout, based on TARB in Geophires v1.2
            rhowaterreservoir = densitywater(0.1 * self.Tinj.value + 0.9 * model.reserv.Tresoutput.value)
            self.DPOverall.value, self.PumpingPower.value, self.DPProdWell.value, self.DPReserv.value, self.DPBouyancy.value = \
                ProdPressureDropsAndPumpingPowerUsingImpedenceModel(f3, vprod, self.rhowaterinj, self.rhowaterprod,
                                                                    model.reserv.rhowater.value,
                                                                    model.reserv.depth.value,
                                                                    self.prodwellflowrate.value,
                                                                    self.prodwelldiam.value,
                                                                    self.impedance.value, self.nprod.value,
                                                                    model.reserv.waterloss.value,
                                                                    model.surfaceplant.pumpeff.value)
            self.DPOverall.value, self.PumpingPower.value, self.DPInjWell.value = \
                InjPressureDropsAndPumpingPowerUsingImpedenceModel(f1, vinj, self.rhowaterinj, model.reserv.depth.value,
                                                                   self.prodwellflowrate.value, self.injwelldiam.value,
                                                                   self.ninj.value, model.reserv.waterloss.value,
                                                                   model.surfaceplant.pumpeff.value,
                                                                   self.DPOverall.value)

        else:  # PI and II are used
            self.PumpingPower.value, self.PumpingPowerProd.value, self.DPProdWell.value, self.Pprodwellhead.value = \
                ProdPressureDropAndPumpingPowerUsingIndexes(model, self.usebuiltinhydrostaticpressurecorrelation,
                                                            self.productionwellpumping.value,
                                                            self.usebuiltinppwellheadcorrelation,
                                                            model.reserv.Trock.value,
                                                            model.reserv.Tsurf.value, model.reserv.depth.value,
                                                            model.reserv.averagegradient.value, self.ppwellhead.value,
                                                            self.PI.value, self.prodwellflowrate.value, f3, vprod,
                                                            self.prodwelldiam.value, self.nprod.value,
                                                            model.surfaceplant.pumpeff.value, self.rhowaterprod)
            self.PumpingPower.value, self.PumpingPowerInj.value, self.DPInjWell.value, model.surfaceplant.Pplantoutlet.value, self.Pprodwellhead.value = \
                InjPressureDropAndPumpingPowerUsingIndexes(model, self.usebuiltinhydrostaticpressurecorrelation,
                                                           self.productionwellpumping.value,
                                                           self.usebuiltinppwellheadcorrelation,
                                                           model.surfaceplant.usebuiltinoutletplantcorrelation.value,
                                                           model.reserv.Trock.value, model.reserv.Tsurf.value,
                                                           model.reserv.depth.value,
                                                           model.reserv.averagegradient.value,
                                                           self.ppwellhead.value, self.II.value,
                                                           self.prodwellflowrate.value, f1, vinj,
                                                           self.injwelldiam.value, self.nprod.value,
                                                           self.ninj.value, model.reserv.waterloss.value,
                                                           model.surfaceplant.pumpeff.value, self.rhowaterinj,
                                                           model.surfaceplant.Pplantoutlet.value,
                                                           self.PumpingPowerProd.value)

        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

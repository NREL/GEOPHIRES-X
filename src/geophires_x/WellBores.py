import math
import numpy as np
from pint.facets.plain import PlainQuantity

from .Parameter import floatParameter, intParameter, boolParameter, OutputParameter, ReadParameter
from geophires_x.GeoPHIRESUtils import vapor_pressure_water_kPa, quantity, static_pressure_MPa
from geophires_x.GeoPHIRESUtils import density_water_kg_per_m3
from geophires_x.GeoPHIRESUtils import viscosity_water_Pa_sec
from .Units import *
import geophires_x.Model as Model
from .OptionList import ReservoirModel


def RameyCalc(krock: float, rhorock: float, cprock: float, welldiam: float, tv, utilfactor: float, flowrate: float,
              cpwater: float, Trock: float, Tresoutput: float, averagegradient: float, depth: float) -> float:
    """
    Calculate the temperature drop along the length of a well
    this code is only valid so far for 1 gradient and deviation = 0
    For multiple gradients, use Ramey's model for every layer
    assume outside diameter of casing is 10% larger than inside diameter of production pipe (=prodwelldiam)
    assume borehole thermal resistance is negligible to rock thermal resistance
        :param depth:  depth of the well [m]
        :type: float
        :param averagegradient: average geothermal gradient [C/km]
        :type: float
        :param Tresoutput: reservoir output temperature [C]
        :type: float
        :param Trock: rock temperature [C]
        :type: float
        :param flowrate: flow rate [kg/s]
        :type: float
        :param utilfactor: utilization factor (fraction of time the well is producing) [-]
        :type: float
        :param tv: time vector [years]
        :type: float
        :param welldiam: well diameter [m]
        :type: float
        :param cprock: rock heat capacity [J/kg/C]
        :type: float
        :param rhorock: rock density [kg/m3]
        :type: float
        :param krock: rock thermal conductivity [W/m/C]
        :type: float
        :param cpwater: water heat capacity [J/kg/C]
        :type: float
        :return: temperature drop along the length of the well [C]
        :rtype: float
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
    calculate the pressure drop over the length of the well due to friction or impedance for the production well and
    the injection well (if applicable) using the Impedance Model or the friction model (if applicable) and the well
    flow rate and diameter and the average temperature of the fluid in the well (which is the average of the reservoir
    temperature and the injection temperature) and the depth of the well and the impedance of the reservoir (if
    applicable) and the number of production wells and the number of injection wells and the water loss (if applicable)
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :param Taverage: average temperature of the fluid in the well [C]
        :type Taverage: float
        :param wellflowrate: flow rate of the fluid in the well [kg/s]
        :type wellflowrate: float
        :param welldiam: diameter of the well [m]
        :type welldiam: float
        :param impedancemodelused: whether or not the impedance model is used (True or False) [-]
        :type impedancemodelused: bool
        :param depth: depth of the well [m]
        :type depth: float
        :return: tuple of DPWell, f3, v, rhowater
        :rtype: tuple
    """
    # start by calculating wellbore fluid conditions [kPa], noting that most temperature drop happens
    # in upper section (because surrounding rock temperature is lowest in upper section)

    rhowater = np.array([
        density_water_kg_per_m3(
            t,
            pressure=model.reserv.lithostatic_pressure(),
        )
        for t in Taverage
    ])  # replace with correlation based on Tprodaverage

    muwater = np.array([
        viscosity_water_Pa_sec(
            t,
            pressure=model.reserv.lithostatic_pressure(),
        )
        for t in Taverage
    ])  # replace with correlation based on Tprodaverage

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
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :param Taverage: average temperature of the fluid in the well [C]
        :type Taverage: float
        :param wellflowrate: flow rate of the fluid in the well [kg/s]
        :type wellflowrate: float
        :param welldiam: diameter of the well [m]
        :type welldiam: float
        :param impedancemodelused: whether or not the impedance model is used (True or False) [-]
        :type impedancemodelused: bool
        :param depth: depth of the well [m]
        :type depth: float
        :param nprod: number of production wells [-]
        :type nprod: int
        :param ninj: number of injection wells [-]
        :type ninj: int
        :param waterloss: water loss [-]
        :type waterloss: float
        :return: tuple of DPWell, f1, v, rhowater
        :rtype: tuple
    """
    # start by calculating wellbore fluid conditions [kPa], noting that most temperature drop happens in
    # upper section (because surrounding rock temperature is lowest in upper section)
    rhowater = (density_water_kg_per_m3(Taverage, pressure=model.reserv.lithostatic_pressure())
                * np.linspace(1, 1, len(model.wellbores.ProducedTemperature.value)))

    # replace with correlation based on Tinjaverage
    muwater = viscosity_water_Pa_sec(Taverage, pressure=model.reserv.lithostatic_pressure()) * np.linspace(1, 1, len(model.wellbores.ProducedTemperature.value))
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
        :param f3: friction factor [-]
        :type f3: float
        :param vprod: velocity of the fluid in the production well [m/s]
        :type vprod: float
        :param rhowaterinj: density of the water in the injection well [kg/m3]
        :type rhowaterinj: float
        :param rhowaterreservoir: density of the water in the reservoir [kg/m3]
        :type rhowaterreservoir: float
        :param rhowaterprod: density of the water in the production well [kg/m3]
        :type rhowaterprod: float
        :param depth: depth of the well [m]
        :type depth: float
        :param wellflowrate: flow rate of the fluid in the well [kg/s]
        :type wellflowrate: float
        :param prodwelldiam: diameter of the well [m]
        :type prodwelldiam: float
        :param impedance: impedance of the reservoir [kg/s/kPa]
        :type impedance: float
        :param nprod: number of production wells [-]
        :type nprod: int
        :param waterloss: water loss [-]
        :type waterloss: float
        :param pumpeff: pump efficiency [-]
        :type pumpeff: float
        :return: tuple of DPOverall, PumpingPower, DPProdWell, DPReserv, DPBouyancy
        :rtype: tuple
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
        :param f1: friction factor [-]
        :type f1: float
        :param vinj: velocity of the fluid in the injection well [m/s]
        :type vinj: float
        :param rhowaterinj: density of the water in the injection well [kg/m3]
        :type rhowaterinj: float
        :param depth: depth of the well [m]
        :type depth: float
        :param wellflowrate: flow rate of the fluid in the well [kg/s]
        :type wellflowrate: float
        :param injwelldiam: diameter of the well [m]
        :type injwelldiam: float
        :param ninj: number of injection wells [-]
        :type ninj: int
        :param waterloss: water loss [-]
        :type waterloss: float
        :param pumpeff: pump efficiency [-]
        :type pumpeff: float
        :param DPOverall: overall pressure drop [kPa]
        :type DPOverall: float
        :return: tuple of newDPOverall, PumpingPower, DPInjWell [kPa]
        :rtype: tuple
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

def get_hydrostatic_pressure_kPa(
        Trock_degC: float,
        Tsurf_degC: float,
        depth_m: float,
        gradient_C_per_km: float,
        lithostatic_pressure: PlainQuantity) -> float:
    """
    Correlation cited as being from Xie, Bloomfield, and Shook in
    https://workingincaes.inl.gov/SiteAssets/CAES%20Files/FORGE/inl_ext-16-38751%20GETEM%20User%20Manual%20Final.pdf
    """
    CP = 4.64E-7
    CT = 9E-4 / (30.796 * Trock_degC ** (-0.552))
    return 0 + 1. / CP * (math.exp(
        density_water_kg_per_m3(Tsurf_degC, pressure=lithostatic_pressure) * 9.81 * CP / 1000 * (
            depth_m - CT / 2 * gradient_C_per_km * depth_m ** 2)) - 1)


def ProdPressureDropAndPumpingPowerUsingIndexes(
        model: Model,
        productionwellpumping: bool,
        usebuiltinppwellheadcorrelation: bool,
        Trock_degC: float,
        depth_m: float,
        ppwellhead_kPa: float,
        PI_kg_per_sec_per_bar: float,
        wellflowrate_kg_per_sec: float,
        f3: float,
        vprod_m: float,
        prodwelldiam_m: float,
        nprod: int,
        pumpeff: float,
        rhowaterprod_kg_per_m3: float) -> tuple:
    """
    Calculate Pressure Drops and Pumping Power needed for the production well using indexes
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :param usebuiltinhydrostaticpressurecorrelation: whether or not to use the built-in hydrostatic pressure correlation (True or False) [-]
        :type usebuiltinhydrostaticpressurecorrelation: bool
        :param productionwellpumping: whether or not the production well is pumping (True or False) [-]
        :type productionwellpumping: bool
        :param usebuiltinppwellheadcorrelation: whether or not to use the built-in wellhead pressure correlation (True or False) [-]
        :type usebuiltinppwellheadcorrelation: bool
        :param Trock_degC: rock temperature [C]
        :type Trock_degC: float
        :param Tsurf_degC: surface temperature [C]
        :type Tsurf_degC: float
        :param depth_m: depth of the well [m]
        :type depth_m: float
        :param gradient_C_per_km: geothermal gradient [C/km]
        :param ppwellhead_kPa: production wellhead pressure [kPa]
        :type ppwellhead_kPa: float
        :param PI_kg_per_sec_per_bar: productivity index [kg/s/bar]
        :type PI_kg_per_sec_per_bar: float
        :param wellflowrate_kg_per_sec: flow rate of the fluid in the well [kg/s]
        :type wellflowrate_kg_per_sec: float
        :param f3: friction factor [-]
        :type f3: float
        :param vprod_m: velocity of the fluid in the production well [m/s]
        :type vprod_m: float
        :param prodwelldiam_m: diameter of the well [m]
        :type prodwelldiam_m: float
        :param nprod: number of production wells [-]
        :type nprod: int
        :param pumpeff: pump efficiency [-]
        :type pumpeff: float
        :param rhowaterprod_kg_per_m3: density of the water in the production well [kg/m3]
        :type rhowaterprod_kg_per_m3: float
        :return: tuple of PumpingPower, PumpingPowerProd, DPProdWell, Pprodwellhead [kPa]
        :rtype: tuple
    """
    # initialize PumpingPower value in case it doesn't get set.
    PumpingPower = PumpingPowerProd = DPProdWell = Pprodwellhead = ([0.0] * len(vprod_m))

    # reservoir hydrostatic pressure
    Phydrostaticcalc_kPa = model.wellbores.Phydrostaticcalc.quantity().to('kPa').magnitude

    if productionwellpumping:
        # Excess pressure covers non-condensable gas pressure and net positive suction head for the pump
        Pexcess_kPa = 344.7  # = 50 psi

        # Minimum production pump inlet pressure and minimum wellhead pressure
        Pminimum_kPa = vapor_pressure_water_kPa(
            Trock_degC,
            pressure=quantity(Phydrostaticcalc_kPa, 'kPa'),
        ) + Pexcess_kPa

        if usebuiltinppwellheadcorrelation:
            Pprodwellhead = Pminimum_kPa  # production wellhead pressure [kPa]
        else:
            Pprodwellhead = ppwellhead_kPa
            if Pprodwellhead < Pminimum_kPa:
                Pprodwellhead = Pminimum_kPa
                msg = (f'Provided production wellhead pressure ({Pprodwellhead}kPa) '
                       f'under minimum pressure ({Pminimum_kPa}kPa). '
                       f'GEOPHIRES will assume minimum wellhead pressure')

                print(f'Warning: {msg}')
                model.logger.warning(msg)

        PI_kPa = PI_kg_per_sec_per_bar / 100.0  # convert PI from kg/s/bar to kg/s/kPa

        # calculate pumping depth
        pumpdepth_m = depth_m + (Pminimum_kPa - Phydrostaticcalc_kPa + wellflowrate_kg_per_sec / PI_kPa) / (
            f3 * (rhowaterprod_kg_per_m3 * vprod_m ** 2 / 2.) * (
            1 / prodwelldiam_m) / 1E3 + rhowaterprod_kg_per_m3 * 9.81 / 1E3)
        pumpdepthfinal_m = np.max(pumpdepth_m)
        if pumpdepthfinal_m < 0.0:
            pumpdepthfinal_m = 0.0
            msg = (f'GEOPHIRES calculates negative production well pumping depth. ({pumpdepthfinal_m:.2f}m)'
                   f'No production well pumps will be assumed')
            print(f'Warning: {msg}')
            model.logger.warning(msg)
        elif pumpdepthfinal_m > 600.0:
            msg = (f'GEOPHIRES calculates production pump depth to be deeper than 600m ({pumpdepthfinal_m:.2f}m). '
                   f'Verify reservoir pressure, production well flow rate and production well dimensions')
            print(f'Warning: {msg}')
            model.logger.warning(msg)

        # calculate production well pumping pressure [kPa]
        DPProdWell = Pprodwellhead - (
            Phydrostaticcalc_kPa - wellflowrate_kg_per_sec / PI_kPa - rhowaterprod_kg_per_m3 * 9.81 * depth_m / 1E3 - f3 *
            (rhowaterprod_kg_per_m3 * vprod_m ** 2 / 2.) * (depth_m / prodwelldiam_m) / 1E3)
        # [MWe] total pumping power for production wells
        PumpingPowerProd = DPProdWell * nprod * wellflowrate_kg_per_sec / rhowaterprod_kg_per_m3 / pumpeff / 1E3
        PumpingPowerProd = np.array([0. if x < 0. else x for x in PumpingPowerProd])

    # total pumping power
    if productionwellpumping:
        PumpingPower = PumpingPowerProd

    # negative pumping power values become zero (b/c we are not generating electricity)
    PumpingPower = [0. if x < 0. else x for x in PumpingPower]

    return PumpingPower, PumpingPowerProd, DPProdWell, Pprodwellhead


def InjPressureDropAndPumpingPowerUsingIndexes(
        model: Model,
        productionwellpumping: bool,
        usebuiltinppwellheadcorrelation: bool,
        usebuiltinoutletplantcorrelation: bool,
        Trock_degC: float,
        depth_m: float,
        ppwellhead: float,
        II: float,
        wellflowrate: float,
        f1: float,
        vinj: float,
        injwelldiam: float,
        nprod: int,
        ninj: int,
        waterloss: float,
        pumpeff: float,
        rhowaterinj: float,
        Pplantoutlet: float,
        PumpingPowerProd) -> tuple:
    """
     Calculate PressureDrops and Pumping Power needed for the injection well using indexes
        :param depth_m: depth of the well [m]
        :type depth_m: float
        :param wellflowrate: flow rate of the fluid in the well [kg/s]
        :type wellflowrate: float
        :param pumpeff: pump efficiency [-]
        :type pumpeff: float
        :param nprod: number of production wells [-]
        :type nprod: int
        :param ppwellhead: production wellhead pressure [kPa]
        :type ppwellhead: float
        :param gradient_C_per_km: geothermal gradient [C/km]
        :type gradient_C_per_km: float
        :param Tsurf: surface temperature [C]
        :type Tsurf: float
        :param Trock_degC: rock temperature [C]
        :type Trock_degC: float
        :param usebuiltinppwellheadcorrelation: whether or not to use the built-in wellhead pressure correlation (True or False) [-]
        :type usebuiltinppwellheadcorrelation: bool
        :param productionwellpumping: whether or not the production well is pumping (True or False) [-]
        :type productionwellpumping: bool
        :param usebuiltinhydrostaticpressurecorrelation:
        :type usebuiltinhydrostaticpressurecorrelation: bool
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :param Pplantoutlet: plant outlet pressure [kPa]
        :type Pplantoutlet: float
        :param rhowaterinj: density of the water in the injection well [kg/m3]
        :type rhowaterinj: float
        :param waterloss: water loss [-]
        :type waterloss: float
        :param ninj: number of injection wells [-]
        :type ninj: int
        :param injwelldiam: diameter of the well [m]
        :type injwelldiam: float
        :param vinj: velocity of the fluid in the injection well [m/s]
        :type vinj: float
        :param f1: friction factor [-]
        :type f1: float
        :param usebuiltinoutletplantcorrelation: whether or not to use the built-in outlet plant pressure correlation (True or False) [-]
        :type usebuiltinoutletplantcorrelation: bool
        :param PumpingPowerProd: pumping power for production wells [MWe]
        :type PumpingPowerProd: float
        :param II: injectivity index [kg/s/bar]
        :type II: float
        :return: tuple of PumpingPower, PumpingPowerInj, DPInjWell, plant_outlet_pressure, Pprodwellhead [kPa]
        :rtype: tuple
    """
    PumpingPowerInj = DPInjWell = Pprodwellhead = [0.0]  # initialize value in case it doesn't get set.

    # reservoir hydrostatic pressure
    Phydrostaticcalc_kPa = model.wellbores.Phydrostaticcalc.quantity().to('kPa').magnitude

    if productionwellpumping:
        # Excess pressure covers non-condensable gas pressure and net positive suction head for the pump
        Pexcess_kPa = 344.7 # = 50 psi

        # Minimum production pump inlet pressure and minimum wellhead pressure
        Pminimum_kPa = vapor_pressure_water_kPa(
            Trock_degC,
            pressure=quantity(Phydrostaticcalc_kPa, 'kPa'),
        ) + Pexcess_kPa

        if usebuiltinppwellheadcorrelation:
            Pprodwellhead = Pminimum_kPa  # production wellhead pressure [kPa]
        else:
            Pprodwellhead = ppwellhead
            if Pprodwellhead < Pminimum_kPa:
                Pprodwellhead = Pminimum_kPa
                msg = (f'Provided production wellhead pressure ({Pprodwellhead}) under minimum pressure ({Pminimum_kPa}). '
                       f'GEOPHIRES will assume minimum wellhead pressure')
                print(f'Warning: {msg}')
                model.logger.warning(msg)

    IIkPa = II / 100.0  # convert II from kg/s/bar to kg/s/kPa

    # necessary injection wellhead pressure [kPa]
    Pinjwellhead = Phydrostaticcalc_kPa + wellflowrate * (
        1 + waterloss) * nprod / ninj / IIkPa - rhowaterinj * 9.81 * depth_m / 1E3 + f1 * (
                       rhowaterinj * vinj ** 2 / 2) * (depth_m / injwelldiam) / 1E3

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
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing, and is used to initialize the class
        """
        model.logger.info(f'Init {self.__class__.__name__}: {__name__}')
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
        # OutputParameter Objects.  This will allow us later to access them in a user interface and get that list,
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
            DefaultValue=29430, # Calculated from example1
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
        sclass = self.__class__.__name__
        self.MyClass = sclass
        self.MyPath = __file__

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
            UnitType=Units.NONE
        )
        self.PumpingPowerProd = self.OutputParameterDict[self.PumpingPowerProd.Name] = OutputParameter(
            Name="PumpingPowerProd",
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )
        self.PumpingPowerInj = self.OutputParameterDict[self.PumpingPowerInj.Name] = OutputParameter(
            Name="PumpingPowerInj",
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )
        self.pumpdepth = self.OutputParameterDict[self.pumpdepth.Name] = OutputParameter(
            Name="pumpdepth",
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.METERS,
            CurrentUnits=LengthUnit.METERS
        )
        self.impedancemodelallowed = self.OutputParameterDict[self.impedancemodelallowed.Name] = OutputParameter(
            Name="impedancemodelallowed",
            UnitType=Units.NONE
        )
        self.productionwellpumping = self.OutputParameterDict[self.productionwellpumping.Name] = OutputParameter(
            Name="productionwellpumping",
            value=True,
            UnitType=Units.NONE
        )
        self.impedancemodelused = self.OutputParameterDict[self.impedancemodelused.Name] = OutputParameter(
            Name="impedancemodelused",
            UnitType=Units.NONE
        )
        self.ProdTempDrop = self.OutputParameterDict[self.ProdTempDrop.Name] = OutputParameter(
            Name="Production Well Temperature Drop",
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS
        )
        self.DPOverall = self.OutputParameterDict[self.DPOverall.Name] = OutputParameter(
            Name="Total Pressure Drop",
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL
        )
        self.DPInjWell = self.OutputParameterDict[self.DPInjWell.Name] = OutputParameter(
            Name="Injection Well Pressure Drop",
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL
        )
        self.DPReserv = self.OutputParameterDict[self.DPReserv.Name] = OutputParameter(
            Name="Reservoir Pressure Drop",
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL
        )
        self.DPProdWell = self.OutputParameterDict[self.DPProdWell.Name] = OutputParameter(
            Name="Production Well Pump Pressure Drop",
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL
        )
        self.DPBouyancy = self.OutputParameterDict[self.DPBouyancy.Name] = OutputParameter(
            Name="Bouyancy Pressure Drop",
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL
        )
        self.ProducedTemperature = self.OutputParameterDict[self.ProducedTemperature.Name] = OutputParameter(
            Name="Produced Temperature",
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS
        )
        self.PumpingPower = self.OutputParameterDict[self.PumpingPower.Name] = OutputParameter(
            Name="Pumping Power",
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )
        self.Pprodwellhead = self.OutputParameterDict[self.Pprodwellhead.Name] = OutputParameter(
            Name="Production wellhead pressure",
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL
        )

    def __str__(self):
        return "WellBores"

    def read_parameters(self, model: Model) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary and stores them in the parameters.
        It also handles special cases that need to be handled after a value has been read in and checked.
        If you choose to subclass this master class, you can also choose to override this method (or not).
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        model.logger.info(f'Init {self.__class__.__name__}: {__name__}')

        # Deal with all the parameter values that the user has provided. They should really only provide values that
        # they want to change from the default values, but they can provide a value that is already set because it is a
        # default value set in __init__. It will ignore those.
        # This also deals with all the special cases that need to be taken care of after a value has been
        # read in and checked.
        # If you choose to subclass this master class, you can also choose to override this method (or not),
        # and if you do, do it before or after you call you own version of this method. If you do, you can also choose
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
                    # IsAGS is false by default - if it equal 1, then it is true
                    if ParameterToModify.Name == "Ramey Production Wellbore Model":
                        if ParameterReadIn.sValue == '0':
                            ParameterToModify.value = False
                    # Ramey Production Wellbore Model is true by default - if it equal 0, then it is false
                    elif ParameterToModify.Name == "Is AGS":
                        if ParameterReadIn.sValue == '1':
                            ParameterToModify.value = True
                    # impedance: impedance per well pair (input as GPa*s/m^3 and converted to KPa/kg/s
                    # (assuming 1000 for density; density will be corrected for later))
                    elif ParameterToModify.Name == "Reservoir Impedance":
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
        model.logger.info(f"read parameters complete {self.__class__.__name__}: {__name__}")

    def Calculate(self, model: Model) -> None:
        """
        The Calculate function is where all the calculations are done.
        This function can be called multiple times, and will only recalculate what has changed each time it is called.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing, but it does make calculations and set values in the model
        """
        model.logger.info(f'Init {self.__class__.__name__}: {__name__}')

        # This is where all the calculations are made using all the values that have been set.
        # If you subclass this class, you can choose to run these calculations before (or after) your calculations,
        # but that assumes you have set all the values that are required for these calculations
        # If you choose to subclass this master class, you can also choose to override this method (or not),
        # and if you do, do it before or after you call you own version of this method.  If you do, you can also
        # choose to call this method from you class, which can effectively run the calculations of the superclass,
        # making all thr values available to your methods. but you had better have set all the parameters!

        self.Phydrostaticcalc.value = get_hydrostatic_pressure_kPa(model.reserv.Trock.value, model.reserv.Tsurf.value,
                                                                   model.reserv.depth.quantity().to('m').magnitude,
                                                                   model.reserv.averagegradient.value,
                                                                   model.reserv.lithostatic_pressure()) if self.usebuiltinhydrostaticpressurecorrelation else self.Phydrostatic.quantity().to(
            self.Phydrostaticcalc.CurrentUnits).magnitude

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
            if hasattr(model.reserv, 'InputDepth'):
                d = model.reserv.InputDepth.value
            else:
                d = model.reserv.depth.value
            self.ProdTempDrop.value = RameyCalc(model.reserv.krock.value,
                                                model.reserv.rhorock.value,
                                                model.reserv.cprock.value,
                                                self.prodwelldiam.value, model.reserv.timevector.value,
                                                model.surfaceplant.utilization_factor.value,
                                                self.prodwellflowrate.value,
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
                TResOutputRepeated = np.tile(model.reserv.Tresoutput.value[0:indexfirstmaxdrawdown],
                                             self.redrill.value + 1)
                model.reserv.Tresoutput.value = TResOutputRepeated[0:len(self.ProducedTemperature.value)]

        # calculate pressure drops and pumping power
        self.DPProdWell.value, f3, vprod, self.rhowaterprod = WellPressureDrop(
            model, model.reserv.Tresoutput.value - self.ProdTempDrop.value / 4.0, self.prodwellflowrate.value,
            self.prodwelldiam.value, self.impedancemodelused.value, model.reserv.depth.value)
        self.DPInjWell.value, f1, vinj, self.rhowaterinj = InjectionWellPressureDrop(
            model, self.Tinj.value, self.prodwellflowrate.value, self.injwelldiam.value, self.impedancemodelused.value,
            model.reserv.depth.value, self.nprod.value, self.ninj.value, model.reserv.waterloss.value)

        if self.impedancemodelused.value:
            # assumed everything stays liquid throughout, based on TARB in Geophires v1.2
            self.DPOverall.value, self.PumpingPower.value, self.DPProdWell.value, self.DPReserv.value, self.DPBouyancy.value = \
                ProdPressureDropsAndPumpingPowerUsingImpedenceModel(f3, vprod, self.rhowaterinj, self.rhowaterprod,
                                                                    model.reserv.rhowater.value,
                                                                    model.reserv.depth.value,
                                                                    self.prodwellflowrate.value,
                                                                    self.prodwelldiam.value,
                                                                    self.impedance.value, self.nprod.value,
                                                                    model.reserv.waterloss.value,
                                                                    model.surfaceplant.pump_efficiency.value)
            self.DPOverall.value, self.PumpingPower.value, self.DPInjWell.value = \
                InjPressureDropsAndPumpingPowerUsingImpedenceModel(f1, vinj, self.rhowaterinj, model.reserv.depth.value,
                                                                   self.prodwellflowrate.value, self.injwelldiam.value,
                                                                   self.ninj.value, model.reserv.waterloss.value,
                                                                   model.surfaceplant.pump_efficiency.value,
                                                                   self.DPOverall.value)

        else:
            # PI and II are used
            self.PumpingPower.value, self.PumpingPowerProd.value, self.DPProdWell.value, self.Pprodwellhead.value = \
                ProdPressureDropAndPumpingPowerUsingIndexes(model,
                                                            self.productionwellpumping.value,
                                                            self.usebuiltinppwellheadcorrelation,
                                                            model.reserv.Trock.value,
                                                            model.reserv.depth.value,
                                                            self.ppwellhead.value,
                                                            self.PI.value, self.prodwellflowrate.value, f3, vprod,
                                                            self.prodwelldiam.value, self.nprod.value,
                                                            model.surfaceplant.pump_efficiency.value, self.rhowaterprod)
            self.PumpingPower.value, self.PumpingPowerInj.value, self.DPInjWell.value, model.surfaceplant.plant_outlet_pressure.value, self.Pprodwellhead.value = \
                InjPressureDropAndPumpingPowerUsingIndexes(model,
                                                           self.productionwellpumping.value,
                                                           self.usebuiltinppwellheadcorrelation,
                                                           model.surfaceplant.usebuiltinoutletplantcorrelation.value,
                                                           model.reserv.Trock.value,
                                                           model.reserv.depth.value,
                                                           self.ppwellhead.value, self.II.value,
                                                           self.prodwellflowrate.value, f1, vinj,
                                                           self.injwelldiam.value, self.nprod.value,
                                                           self.ninj.value, model.reserv.waterloss.value,
                                                           model.surfaceplant.pump_efficiency.value, self.rhowaterinj,
                                                           model.surfaceplant.plant_outlet_pressure.value,
                                                           self.PumpingPowerProd.value)

        model.logger.info(f'complete {self.__class__.__name__}: {__name__}')

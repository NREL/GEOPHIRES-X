import sys
import os
import math
import numpy as np
from .Parameter import floatParameter, intParameter, OutputParameter, ReadParameter
from .Units import *
import geophires_x.Model as Model
from .WellBores import WellBores


class SUTRAWellBores(WellBores):
    def __init__(self, model: Model):
        """
        The __init__ function is the constructor for a class.  It is called whenever an instance of the class is created.
        The __init__ function can take arguments, but self is always the first one. Self refers to the instance of the
         object that has already been created, and it's used to access variables that belong to that object.
        Set up all the Parameters that will be predefined by this class using the different types of parameter classes.
        Setting up includes giving it a name, a default value, The Unit Type (length, volume, temperature, etc.)
        and Unit Name of that value, sets it as required (or not), sets allowable range, the error message
        if that range is exceeded, the ToolTip Text, and the name of teh class that created it.
        This includes setting up temporary variables that will be available to all the class but noy read in by user,
        or used for Output
        This also includes all Parameters that are calculated and then published using the Printouts function.
        If you choose to subclass this master class, you can do so before or after you create your own parameters.
        If you do, you can also choose to call this method from you class, which will effectively add and set all
        these parameters to your class.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing, and is used to initialize the class
        """
        model.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')
        super().__init__(model)

        self.rhowaterprod = self.rhowaterinj = 0.0

        # These dictionaries contain a list of all the parameters set in this object, stored as "Parameter" and
        # OutputParameter Objects.  This will allow us later to access them in a user interface and get that list,
        # along with unit type, preferred units, etc.
        self.ParameterDict = {}
        self.OutputParameterDict = {}

        self.nprod = self.ParameterDict[self.nprod.Name] = intParameter(
            "Number of Production Wells",
            value=1,
            DefaultValue=1,
            AllowableRange=list(range(1, 201, 1)),
            UnitType=Units.NONE,
            Required=True,
            ErrMessage="assume default number of production wells (1)",
            ToolTipText="Number of (identical) production wells",
        )
        self.ninj = self.ParameterDict[self.ninj.Name] = intParameter(
            "Number of Injection Wells",
            value=1,
            DefaultValue=1,
            AllowableRange=list(range(0, 201, 1)),
            UnitType=Units.NONE,
            Required=True,
            ErrMessage="assume default number of injection wells (1)",
            ToolTipText="Number of (identical) injection wells",
        )
        self.prodwelldiam = self.ParameterDict[self.prodwelldiam.Name] = floatParameter(
            "Production Well Diameter",
            value=8.0,
            DefaultValue=8.0,
            Min=1.0,
            Max=30.0,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.INCHES,
            CurrentUnits=LengthUnit.INCHES,
            Required=True,
            ErrMessage="assume default production well diameter (8 inch)",
            ToolTipText="Inner diameter of production wellbore (assumed constant along the wellbore) to calculate \
            frictional pressure drop and wellbore heat transmission with Rameys model",
        )
        self.injwelldiam = self.ParameterDict[self.injwelldiam.Name] = floatParameter(
            "Injection Well Diameter",
            value=8.0,
            DefaultValue=8.0,
            Min=1.0,
            Max=30.0,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.INCHES,
            CurrentUnits=LengthUnit.INCHES,
            Required=True,
            ErrMessage="assume default injection well diameter (8 inch)",
            ToolTipText="Inner diameter of production wellbore (assumed constant along the wellbore) to calculate \
            frictional pressure drop and wellbore heat transmission with Rameys model",
        )

        self.impedance = self.ParameterDict[self.impedance.Name] = floatParameter(
            "Reservoir Impedance",
            value=1000.0,
            DefaultValue=1000.0,
            Min=1e-4,
            Max=1e4,
            UnitType=Units.IMPEDANCE,
            PreferredUnits=ImpedanceUnit.GPASPERM3,
            CurrentUnits=ImpedanceUnit.GPASPERM3,
            ErrMessage="assume default reservoir impedance (0.1 GPa*s/m^3)",
            ToolTipText='Reservoir resistance to flow per well-pair. For EGS-type reservoirs when the injection well '
                        'is in hydraulic communication with the production well, this parameter specifies the overall '
                        'pressure drop in the reservoir between injection well and production well (see docs)',
        )

        self.Tinj = self.ParameterDict[self.Tinj.Name] = floatParameter(
            "Injection Temperature",
            value=70.0,
            DefaultValue=70.0,
            Min=0.0,
            Max=200.0,
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS,
            Required=True,
            ErrMessage="assume default injection temperature (70 deg.C)",
            ToolTipText="Constant geofluid injection temperature at injection wellhead.",
        )

        # local variable initiation
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = os.path.abspath(__file__)

        # Results - used by other objects or printed in output downstream
        self.DPInjWell = self.OutputParameterDict[self.DPInjWell.Name] = OutputParameter(
            Name="Injection Well Pressure Drop",
            value=[0.0],
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL,
        )
        self.DPReserv = self.OutputParameterDict[self.DPReserv.Name] = OutputParameter(
            Name="Reservoir Pressure Drop",
            value=[0.0],
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL,
        )
        self.DPProdWell = self.OutputParameterDict[self.DPProdWell.Name] = OutputParameter(
            Name="Production Well Pump Pressure Drop",
            value=[0.0],
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL,
        )

        self.DPOverall = self.OutputParameterDict[self.DPOverall.Name] = OutputParameter(
            Name="Total Pressure Drop",
            value=[0.0],
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL,
        )
        self.PumpingPower = self.OutputParameterDict[self.PumpingPower.Name] = OutputParameter(
            Name="PumpingPower",
            value=[0.0],
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.KW,
            CurrentUnits=PowerUnit.KW,
        )

        self.ProducedTemperature = self.OutputParameterDict[self.ProducedTemperature.Name] = OutputParameter(
            Name="Produced Temperature",
            value=[0.0],
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS,
        )

        self.Tinj = self.OutputParameterDict[self.Tinj.Name] = OutputParameter(
            Name="Injection Temperature",
            value=[0.0],
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS,
        )

        self.ProductionWellFlowRates = self.OutputParameterDict[self.ProductionWellFlowRates.Name] = OutputParameter(
            Name="Production Well Flow Rate Profile",
            value=[0.0],
            UnitType=Units.FLOWRATE,
            PreferredUnits=FlowRateUnit.KGPERSEC,
            CurrentUnits=FlowRateUnit.KGPERSEC,
        )

        model.logger.info(f'Complete {str(__class__)}: {sys._getframe().f_code.co_name}')

    def __str__(self):
        return "WellBores"

    def read_parameters(self, model: Model) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary and stores them in the parameters.
        It also handles special cases that need to be handled after a value has been read in and checked.
        If you choose to subclass this master class, you can also choose to override this method (or not).
        Deal with all the parameter values that the user has provided.  They should really only provide values that
        they want to change from the default values, but they can provide a value that is already set because it is a
        default value set in __init__.  It will ignore those.
        This also deals with all the special cases that need to be taken care of after a value has been
        read in and checked.
        If you choose to subclass this master class, you can also choose to override this method (or not),
        and if you do, do it before or after you call you own version of this method.  If you do, you can also choose
        to call this method from you class, which can modify all these superclass parameters in your class.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        if len(model.InputParameters) > 0:
            # loop through all the parameters that the user wishes to set, looking for parameters that match this object
            for item in self.ParameterDict.items():
                ParameterToModify = item[1]
                key = ParameterToModify.Name.strip()
                if key in model.InputParameters:
                    ParameterReadIn = model.InputParameters[key]
                    ReadParameter(ParameterReadIn, ParameterToModify, model)  # this should handle all non-special cases

                    # handle special cases
                    # impedance: impedance per well pair (input as GPa*s/m^3 and converted to KPa/kg/s
                    # (assuming 1000 for density; density will be corrected for later))
                    if ParameterToModify.Name == "Reservoir Impedance":
                        # shift it by a constant to make the units right, per line 619 of GEOPHIRES 2
                        self.impedance.value = self.impedance.value * (1e6 / 1e3)

        else:
            model.logger.info("No parameters read because no content provided")
        model.logger.info("read parameters complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

    def Calculate(self, model: Model) -> None:
        """
        The Calculate function is where all the calculations are done.
        This function can be called multiple times, and will only recalculate what has changed each time it is called.
        This is where all the calculations are made using all the values that have been set.
        If you subclass this class, you can choose to run these calculations before (or after) your calculations,
        but that assumes you have set all the values that are required for these calculations
        If you choose to subclass this master class, you can also choose to override this method (or not),
        and if you do, do it before or after you call you own version of this method.  If you do, you can also
        choose to call this method from you class, which can effectively run the calculations of the superclass,
        making all thr values available to your methods. but you had better have set all the parameters!
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing, but it does make calculations and set values in the model
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        # special case: production and injection well diameters are input as inches and call calculations
        # assume meters! Check and change if needed, assuming anything > 2 must be talking about inches
        if self.injwelldiam.value > 2.0:
            self.injwelldiam.value = self.injwelldiam.value * 0.0254
            self.injwelldiam.CurrentUnits = LengthUnit.METERS
        if self.prodwelldiam.value > 2.0:
            self.prodwelldiam.value = self.prodwelldiam.value * 0.0254
            self.prodwelldiam.CurrentUnits = LengthUnit.METERS

        # get wellbore flow rates from SUTRA data
        prodwellflowrates = np.append(
            model.reserv.BalanceWellFlowRate.value[0:-1:2], model.reserv.BalanceWellFlowRate.value[-1]
        )
        injwellflowrates = np.append(
            model.reserv.StorageWellFlowRate.value[0:-1:2], model.reserv.StorageWellFlowRate.value[-1]
        )
        self.ProductionWellFlowRates.value = prodwellflowrates

        # calculate wellbore temperature drop (not considered in SUTRA for now) (wellhead inj and prod directly comes from SUTRA)
        self.ProducedTemperature.value = np.append(
            model.reserv.StorageWellTemperature.value[0:-1:2], model.reserv.StorageWellTemperature.value[-1]
        )
        self.Tinj.value = np.append(
            model.reserv.BalanceWellTemperature.value[0:-1:2], model.reserv.BalanceWellTemperature.value[-1]
        )

        # redrilling (not considered in SUTRA)

        # calculate pressure drop production well [kPa]
        self.DPProdWell.value = np.zeros(len(model.reserv.timevector.value))
        rhowaterprod = 1000
        muwaterprod = 1e-3
        vprod = abs(prodwellflowrates) / rhowaterprod / (math.pi / 4.0 * self.prodwelldiam.value**2)
        Rewaterprod = 4.0 * abs(prodwellflowrates) / (muwaterprod * math.pi * self.prodwelldiam.value)
        for i in range(len(Rewaterprod)):
            if vprod[i] == 0:
                self.DPProdWell.value[i] = 0
            else:
                if Rewaterprod[i] < 2300:
                    f = 64.0 / Rewaterprod[i]
                else:
                    relroughness = 1e-4 / self.prodwelldiam.value
                    f = 1.0 / np.power(-2 * np.log10(relroughness / 3.7 + 5.74 / np.power(Rewaterprod[i], 0.9)), 2.0)
                    f = 1.0 / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewaterprod[i] / np.sqrt(f))), 2.0)
                    f = 1.0 / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewaterprod[i] / np.sqrt(f))), 2.0)
                    f = 1.0 / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewaterprod[i] / np.sqrt(f))), 2.0)
                    f = 1.0 / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewaterprod[i] / np.sqrt(f))), 2.0)
                    f = 1.0 / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewaterprod[i] / np.sqrt(f))), 2.0)

                self.DPProdWell.value[i] = (
                    f * (rhowaterprod * vprod[i] ** 2 / 2) * (model.reserv.depth.value / self.prodwelldiam.value) / 1e3
                )  # /1E3 to convert from Pa to kPa

        # calculate pressure drop injection well [kPa]
        self.DPInjWell.value = np.zeros(len(model.reserv.timevector.value))
        rhowaterinj = 1000
        muwaterinj = 1e-3
        vinj = abs(injwellflowrates) / rhowaterinj / (math.pi / 4.0 * self.injwelldiam.value**2)
        Rewaterinj = 4.0 * abs(injwellflowrates) / (muwaterinj * math.pi * self.injwelldiam.value)
        for i in range(len(Rewaterinj)):
            if vinj[i] == 0:
                self.DPInjWell.value[i] = 0
            else:
                if Rewaterinj[i] < 2300:
                    f = 64.0 / Rewaterinj[i]
                else:
                    relroughness = 1e-4 / self.injwelldiam.value
                    f = 1.0 / np.power(-2 * np.log10(relroughness / 3.7 + 5.74 / np.power(Rewaterinj[i], 0.9)), 2.0)
                    f = 1.0 / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewaterinj[i] / np.sqrt(f))), 2.0)
                    f = 1.0 / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewaterinj[i] / np.sqrt(f))), 2.0)
                    f = 1.0 / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewaterinj[i] / np.sqrt(f))), 2.0)
                    f = 1.0 / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewaterinj[i] / np.sqrt(f))), 2.0)
                    f = 1.0 / np.power((-2 * np.log10(relroughness / 3.7 + 2.51 / Rewaterinj[i] / np.sqrt(f))), 2.0)

                self.DPInjWell.value[i] = (
                    f * (rhowaterinj * vinj[i] ** 2 / 2) * (model.reserv.depth.value / self.injwelldiam.value) / 1e3
                )  # /1E3 to convert from Pa to kPa

        # Calculate buoyancy pressure drop [kPa]
        DP_buoyancy = (
            (rhowaterprod - rhowaterinj) * model.reserv.depth.value * 9.81 / 1e3
        )  # /1E3 to convert from Pa to kPa

        # Calculate reservoir pressure drop [kPa]
        DP_reservoir = abs(prodwellflowrates) / (0.5 * rhowaterinj + 0.5 * rhowaterprod) * self.impedance.value

        # Calculate overall pressure drop
        self.DPOverall.value = self.DPProdWell.value + self.DPInjWell.value + DP_buoyancy + DP_reservoir

        # calculate pumping power [kWe] (approximate)
        self.PumpingPower.value = (
            self.DPOverall.value
            * abs(prodwellflowrates)
            / (0.5 * rhowaterinj + 0.5 * rhowaterprod)
            / model.surfaceplant.pump_efficiency.value
        )

        self._sync_output_params_from_input_params()

        model.logger.info(f'complete {str(__class__)}: {sys._getframe().f_code.co_name}')

import sys
import os
import numpy as np
from .OptionList import EndUseOptions, PowerPlantType
from .Parameter import floatParameter, intParameter, OutputParameter, ReadParameter
from .Units import *
import geophires_x.Model as Model


class SurfacePlant:
    def __init__(self, model:Model):
        """
        The __init__ function is called automatically when a class is instantiated.
        It initializes the attributes of an object, and sets default values for certain arguments that can be overridden
         by user input.
        The __init__ function is used to set up all the parameters in the Surfaceplant.
        :param self: Store data that will be used by the class
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: None
        :doc-author: Malcolm Ross
        """

        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)
        self.Tinj = 0.0

        # Set up all the Parameters that will be predefined by this class using the different types of parameter classes.
        # Setting up includes giving it a name, a default value, The Unit Type (length, volume, temperature, etc) and
        # Unit Name of that value, sets it as required (or not), sets allowable range, the error message if that range
        # is exceeded, the ToolTip Text, and the name of teh class that created it.
        # This includes setting up temporary variables that will be available to all the class but noy read in by user,
        # or used for Output
        # This also includes all Parameters that are calculated and then published using the Printouts function.

        # These dictionaries contain a list of all the parameters set in this object, stored as "Parameter" and
        # "OutputParameter" Objects.  This will allow us later to access them in a user interface and get that list,
        # along with unit type, preferred units, etc.
        self.ParameterDict = {}
        self.OutputParameterDict = {}

        self.enduseoption = self.ParameterDict[self.enduseoption.Name] = intParameter(
            "End-Use Option",
            value=EndUseOptions.ELECTRICITY,
            AllowableRange=[1, 2, 31, 32, 41, 42, 51, 52],
            UnitType=Units.NONE,
            ErrMessage="assume default end-use option (1: electricity only)",
            ToolTipText="Select the end-use application of the geofluid heat (see docs for details)"
        )
        self.pptype = self.ParameterDict[self.pptype.Name] = intParameter(
            "Power Plant Type",
            value=PowerPlantType.SUB_CRITICAL_ORC,
            AllowableRange=[1, 2, 3, 4],
            UnitType=Units.NONE,
            ErrMessage="assume default power plant type (1: subcritical ORC)",
            ToolTipText="Specify the type of power plant in case of electricity generation. 1: Subcritical ORC, \
            2: Supercritical ORC, 3: Single-flash, 4: Double-flash"
        )
        self.pumpeff = self.ParameterDict[self.pumpeff.Name] = floatParameter(
            "Circulation Pump Efficiency",
            value=0.75,
            DefaultValue=0.75,
            Min=0.1,
            Max=1.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Required=True,
            ErrMessage="assume default circulation pump efficiency (0.75)",
            ToolTipText="Specify the overall efficiency of the injection and production well pumps"
        )
        self.utilfactor = self.ParameterDict[self.utilfactor.Name] = floatParameter(
            "Utilization Factor",
            value=0.9,
            DefaultValue=0.9,
            Min=0.1,
            Max=1.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            Required=True,
            ErrMessage="assume default utilization factor (0.9)",
            ToolTipText="Ratio of the time the plant is running in normal production in a 1-year time period."
        )
        self.enduseefficiencyfactor = self.ParameterDict[self.enduseefficiencyfactor.Name] = floatParameter(
            "End-Use Efficiency Factor",
            value=0.9,
            DefaultValue=0.9,
            Min=0.1,
            Max=1.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default end-use efficiency factor (0.9)",
            ToolTipText="Constant thermal efficiency of the direct-use application"
        )
        self.chpfraction = self.ParameterDict[self.chpfraction.Name] = floatParameter(
            "CHP Fraction",
            value=0.5,
            DefaultValue=0.5,
            Min=0.0001,
            Max=0.9999,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default CHP fraction (0.5)",
            ToolTipText="Fraction of produced geofluid flow rate going to direct-use heat application in \
            CHP parallel cycle"
        )
        self.Tchpbottom = self.ParameterDict[self.Tchpbottom.Name] = floatParameter(
            "CHP Bottoming Entering Temperature",
            value=150.0,
            DefaultValue=150.0,
            Min=0,
            Max=400,
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS,
            ErrMessage="assume default CHP bottom temperature (150 deg.C)",
            ToolTipText="Power plant entering geofluid temperature used in CHP bottoming cycle"
        )
        self.Tenv = self.ParameterDict[self.Tenv.Name] = floatParameter(
            "Ambient Temperature",
            value=15.0,
            DefaultValue=15.0,
            Min=-50,
            Max=50,
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS,
            ErrMessage="assume default ambient temperature (15 deg.C)",
            ToolTipText="Ambient (or dead-state) temperature used for calculating power plant utilization efficiency"
        )
        self.plantlifetime = self.ParameterDict[self.plantlifetime.Name] = intParameter(
            "Plant Lifetime",
            value=30,
            DefaultValue=30.0,
            AllowableRange=list(range(1, 101, 1)),
            UnitType=Units.TIME,
            PreferredUnits=TimeUnit.YEAR,
            CurrentUnits=TimeUnit.YEAR,
            Required=True,
            ErrMessage="assume default plant lifetime (30 years)",
            ToolTipText="System lifetime"
        )
        self.pipinglength = self.ParameterDict[self.pipinglength.Name] = floatParameter(
            "Surface Piping Length",
            value=0.0,
            DefaultValue=0.0,
            Min=0,
            Max=100,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.KILOMETERS,
            CurrentUnits=LengthUnit.KILOMETERS,
            ErrMessage="assume default piping length (5km)"
        )
        self.Pplantoutlet = self.ParameterDict[self.Pplantoutlet.Name] = floatParameter(
            "Plant Outlet Pressure",
            value=100.0,
            DefaultValue=100.0,
            Min=0.01,
            Max=10000.0,
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL,
            ErrMessage="assume default plant outlet pressure (100 kPa)",
            ToolTipText="Constant plant outlet pressure equal to injection well pump(s) suction pressure"
        )
        self.elecprice = self.ParameterDict[self.elecprice.Name] = floatParameter(
            "Electricity Rate",
            value=0.07,
            DefaultValue=0.07,
            Min=0.0,
            Max=1.0,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH,
            ErrMessage="assume default electricity rate ($0.07/kWh)",
            ToolTipText="Price of electricity to calculate pumping costs in direct-use heat only mode or revenue \
            from electricity sales in CHP mode."
        )
        self.heatprice = self.ParameterDict[self.heatprice.Name] = floatParameter(
            "Heat Rate",
            value=0.02,
            DefaultValue=0.02,
            Min=0.0,
            Max=1.0,
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.DOLLARSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH,
            ErrMessage="assume default heat rate ($0.02/kWh)",
            ToolTipText="Price of heat to calculate revenue from heat sales in CHP mode."
        )
        self.ConstructionYears = self.ParameterDict[self.ConstructionYears.Name] = intParameter(
            "Construction Years",
            value=1,
            DefaultValue=1,
            AllowableRange=list(range(1, 15, 1)),
            UnitType=Units.NONE,
            ErrMessage="assume default number of years in construction (1)",
            ToolTipText="Number of years spent in construction (assumes whole years, no fractions)"
        )

        # local variable initialization
        self.setinjectionpressurefixed = False
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = os.path.abspath(__file__)

        # Results - used by other objects or printed in output downstream
        self.usebuiltinoutletplantcorrelation = self.OutputParameterDict[self.usebuiltinoutletplantcorrelation.Name] = OutputParameter(
            Name="usebuiltinoutletplantcorrelation",
            value=False,
            UnitType=Units.NONE
        )
        self.TenteringPP = self.OutputParameterDict[self.TenteringPP.Name] = OutputParameter(
            Name="TenteringPP",
            value=[],
            UnitType=Units.TEMPERATURE,
            PreferredUnits=TemperatureUnit.CELSIUS,
            CurrentUnits=TemperatureUnit.CELSIUS
        )
        self.HeatkWhExtracted = self.OutputParameterDict[self.HeatkWhExtracted.Name] = OutputParameter(
            Name="annual heat production",
            value=[],
            UnitType=Units.ENERGYFREQUENCY,
            PreferredUnits=EnergyFrequencyUnit.GWPERYEAR,
            CurrentUnits=EnergyFrequencyUnit.GWPERYEAR
        )
        self.PumpingkWh = self.OutputParameterDict[self.PumpingkWh.Name] = OutputParameter(
            Name="annual electricity production",
            value=[],
            UnitType=Units.ENERGYFREQUENCY,
            PreferredUnits=EnergyFrequencyUnit.KWPERYEAR,
            CurrentUnits=EnergyFrequencyUnit.KWPERYEAR
        )
        self.ElectricityProduced = self.OutputParameterDict[self.ElectricityProduced.Name] = OutputParameter(
            Name="Total Electricity Generation",
            value=[0.0],
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )
        self.NetElectricityProduced = self.OutputParameterDict[self.NetElectricityProduced.Name] = OutputParameter(
            Name="Net Electricity Production",
            value=[0.0],
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )
        self.TotalkWhProduced = self.OutputParameterDict[self.TotalkWhProduced.Name] = OutputParameter(
            Name="Total Electricity Generation",
            value=[0.0],
            UnitType=Units.ENERGY,
            PreferredUnits=EnergyUnit.KWH,
            CurrentUnits=EnergyUnit.KWH
        )
        self.NetkWhProduced = self.OutputParameterDict[self.NetkWhProduced.Name] = OutputParameter(
            Name="Net Electricity Generation",
            value=[0.0],
            UnitType=Units.ENERGY,
            PreferredUnits=EnergyUnit.KWH,
            CurrentUnits=EnergyUnit.KWH
        )
        self.FirstLawEfficiency = self.OutputParameterDict[self.FirstLawEfficiency.Name] = OutputParameter(
            Name="First Law Efficiency",
            value=[0.0],
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.PERCENT,
            CurrentUnits=PercentUnit.PERCENT
        )
        self.HeatExtracted = self.OutputParameterDict[self.HeatExtracted.Name] = OutputParameter(
            Name="Heat Extracted",
            value=[0.0],
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )
        self.HeatProduced = self.OutputParameterDict[self.HeatProduced.Name] = OutputParameter(
            Name="Heat Produced in MW",
            value=[0.0],
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )
        self.HeatkWhProduced = self.OutputParameterDict[self.HeatkWhProduced.Name] = OutputParameter(
            Name="Heat Produced in kWh",
            value=[0.0],
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.KW,
            CurrentUnits=PowerUnit.KW
        )
        self.Availability = self.OutputParameterDict[self.Availability.Name] = OutputParameter(
            Name="Geofluid Availability",
            value=[0.0],
            UnitType=Units.AVAILABILITY,
            PreferredUnits=AvailabilityUnit.MWPERKGPERSEC,
            CurrentUnits=AvailabilityUnit.MWPERKGPERSEC
        )
        self.RemainingReservoirHeatContent = self.OutputParameterDict[self.RemainingReservoirHeatContent.Name] = OutputParameter(
            Name="Remaining Reservoir Heat Content",
            value=[0.0],
            UnitType=Units.POWER,
            PreferredUnits=PowerUnit.MW,
            CurrentUnits=PowerUnit.MW
        )

        model.logger.info("Complete "+ str(__class__) + ": " + sys._getframe().f_code.co_name)

    def __str__(self):
        return "SurfacePlant"

    def read_parameters(self, model:Model) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary and stores them in the parameters.
        It also handles special cases that need to be handled after a value has been read in and checked.
        If you choose to subclass this master class, you can also choose to override this method (or not), and if you do
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
        # and if you do, do it before or after you call you own version of this method.
        # If you do, you can also choose to call this method from you class, which can effectively modify all
        # these superclass parameters in your class.

        if len(model.InputParameters) > 0:
            # loop thru all the parameters that the user wishes to set, looking for parameters that match this object
            for item in self.ParameterDict.items():
                ParameterToModify = item[1]
                key = ParameterToModify.Name.strip()
                if key in model.InputParameters:
                    ParameterReadIn = model.InputParameters[key]
                    # Before we change the parameter, let's assume that the unit preferences will match -
                    # if they don't, the later code will fix this.
                    ParameterToModify.CurrentUnits = ParameterToModify.PreferredUnits
                    # this should handle all the non-special cases
                    ReadParameter(ParameterReadIn, ParameterToModify, model)

                    # handle special cases
                    if ParameterToModify.Name == "End-Use Option":
                        if ParameterReadIn.sValue == str(1):
                            ParameterToModify.value = EndUseOptions.ELECTRICITY
                        elif ParameterReadIn.sValue == str(2):
                            ParameterToModify.value = EndUseOptions.HEAT
                        elif ParameterReadIn.sValue == str(31):
                            ParameterToModify.value = EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT
                        elif ParameterReadIn.sValue == str(32):
                            ParameterToModify.value = EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICTY
                        elif ParameterReadIn.sValue == str(41):
                            ParameterToModify.value = EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT
                        elif ParameterReadIn.sValue == str(42):
                            ParameterToModify.value = EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICTY
                        elif ParameterReadIn.sValue == str(51):
                            ParameterToModify.value = EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT
                        else:
                            ParameterToModify.value = EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICTY
                    if ParameterToModify.Name == "Power Plant Type":
                        if ParameterReadIn.sValue == str(1):
                            ParameterToModify.value = PowerPlantType.SUB_CRITICAL_ORC
                        elif ParameterReadIn.sValue == str(2):
                            ParameterToModify.value = PowerPlantType.SUPER_CRITICAL_ORC
                        elif ParameterReadIn.sValue == str(3):
                            ParameterToModify.value = PowerPlantType.SINGLE_FLASH
                        else:
                            ParameterToModify.value = PowerPlantType.DOUBLE_FLASH
                        if self.enduseoption.value == EndUseOptions.ELECTRICITY:
                            # simple single- or double-flash power plant assumes no production well pumping
                            if ParameterToModify.value in [PowerPlantType.SINGLE_FLASH, PowerPlantType.DOUBLE_FLASH]:
                                model.wellbores.impedancemodelallowed.value = False
                                model.wellbores.productionwellpumping.value = False
                                self.setinjectionpressurefixed = True
                        elif self.enduseoption.value in \
                            [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT, EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICTY]:
                            # co-generation topping cycle with single- or double-flash power plant assumes no production well pumping
                            if ParameterToModify.value in [PowerPlantType.SINGLE_FLASH, PowerPlantType.DOUBLE_FLASH]:
                                model.wellbores.impedancemodelallowed.value = False
                                model.wellbores.productionwellpumping.value = False
                                self.setinjectionpressurefixed = True
                        elif self.enduseoption.value in \
                            [EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICTY]:
                            # co-generation bottoming cycle with single- or double-flash power plant assumes
                            # production well pumping
                            if ParameterToModify.value in [PowerPlantType.SINGLE_FLASH, PowerPlantType.DOUBLE_FLASH]:
                                model.wellbores.impedancemodelallowed.value = False
                                self.setinjectionpressurefixed = True
                        elif self.enduseoption.value in \
                            [EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICTY]:
                            # co-generation parallel cycle with single- or double-flash power plant assumes
                            # production well pumping
                            if ParameterToModify.value in [PowerPlantType.SINGLE_FLASH, PowerPlantType.DOUBLE_FLASH]:
                                model.wellbores.impedancemodelallowed.value = False
                                self.setinjectionpressurefixed = True
                    if ParameterToModify.Name == "Plant Outlet Pressure":
                        if ParameterToModify.value < 0 or ParameterToModify.value > 10000:
                                if self.setinjectionpressurefixed:
                                    ParameterToModify.value = 100
                                    print("Warning: Provided plant outlet pressure outside of range 0-10000. \
                                    GEOPHIRES will assume default plant outlet pressure (100 kPa)")
                                    model.logger.warning("Provided plant outlet pressure outside of range 0-10000. \
                                    GEOPHIRES will assume default plant outlet pressure (100 kPa)")
                                else:
                                    self.usebuiltinoutletplantcorrelation.value = True
                                    print("Warning: Provided plant outlet pressure outside of range 0-10000 kPa. \
                                    GEOPHIRES will calculate plant outlet pressure based on \
                                    production wellhead pressure and surface equipment pressure drop of 10 psi")
                                    model.logger.warning("Provided plant outlet pressure outside of range 0-10000 kPa. \
                                    GEOPHIRES will calculate plant outlet pressure based on \
                                    production wellhead pressure and surface equipment pressure drop of 10 psi")
            if "Plant Outlet Pressure" not in model.InputParameters:
                if self.setinjectionpressurefixed:
                    self.usebuiltinoutletplantcorrelation.value = False
                    self.Pplantoutlet.value = 100
                    print("Warning: No valid plant outlet pressure provided. \
                    GEOPHIRES will assume default plant outlet pressure (100 kPa)")
                    model.logger.warning("No valid plant outlet pressure provided. \
                    GEOPHIRES will assume default plant outlet pressure (100 kPa)")
                else:
                    self.usebuiltinoutletplantcorrelation.value = True
                    print("Warning: No valid plant outlet pressure provided. GEOPHIRES will calculate plant outlet \
                    pressure based on production wellhead pressure and surface equipment pressure drop of 10 psi")
                    model.logger.warning("No valid plant outlet pressure provided. GEOPHIRES will calculate plant outlet\
                     pressure based on production wellhead pressure and surface equipment pressure drop of 10 psi")

        else:
            model.logger.info("No parameters read because no content provided")
        model.logger.info("complete "+ str(__class__) + ": " + sys._getframe().f_code.co_name)

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
        # and if you do, do it before or after you call you own version of this method.  If you do, you can also choose
        # to call this method from you class, which can effectively run the calculations of the superclass, making all
        # the values available to your methods. but you had better have set all the parameters!

        # calculate produced electricity/direct-use heat
        if self.enduseoption.value == EndUseOptions.HEAT: # direct-use
            self.HeatExtracted.value = model.wellbores.nprod.value * model.wellbores.prodwellflowrate.value * \
                                       model.reserv.cpwater.value*(model.wellbores.ProducedTemperature.value -
                                       model.wellbores.Tinj.value)/1E6  # heat extracted from geofluid [MWth]
            # useful direct-use heat provided to application [MWth]
            self.HeatProduced.value = self.HeatExtracted.value*self.enduseefficiencyfactor.value
        else:
            if self.enduseoption.value in [EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICTY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT]:
                self.TenteringPP.value = self.Tchpbottom.value
            else:
                self.TenteringPP.value = model.wellbores.ProducedTemperature.value
            # Availability water (copied from GEOPHIRES v1.0 Fortran Code)
            A = 4.041650
            B = -1.204E-2
            C = 1.60500E-5
            T0 = self.Tenv.value + 273.15
            T1 = self.TenteringPP.value + 273.15
            T2 = self.Tenv.value + 273.15
            self.Availability.value = ((A-B*T0)*(T1-T2)+(B-C*T0)/2.0*(T1**2-T2**2)+C/3.0*(T1**3-T2**3)-A*T0*np.log(T1/T2))*2.2046/947.83    # MJ/kg

            if self.pptype.value == PowerPlantType.SUB_CRITICAL_ORC:
                if self.Tenv.value < 15.:
                    C1 = 2.746E-3
                    C0 = -8.3806E-2
                    D1 = 2.713E-3
                    D0 = -9.1841E-2
                    Tfraction = (self.Tenv.value-5.)/10.
                else:
                    C1 = 2.713E-3
                    C0 = -9.1841E-2
                    D1 = 2.676E-3
                    D0 = -1.012E-1
                    Tfraction = (self.Tenv.value-15.)/10.
                etaull = C1*self.TenteringPP.value + C0
                etauul = D1*self.TenteringPP.value + D0
                etau = (1-Tfraction)*etaull + Tfraction*etauul
                if self.Tenv.value < 15.:
                    C1 = 0.0894
                    C0 = 55.6
                    D1 = 0.0894
                    D0 = 62.6
                    Tfraction = (self.Tenv.value-5.)/10.
                else:
                    C1 = 0.0894
                    C0 = 62.6
                    D1 = 0.0894
                    D0 = 69.6
                    Tfraction = (self.Tenv.value-15.)/10.
                reinjtll = C1*self.TenteringPP.value + C0
                reinjtul = D1*self.TenteringPP.value + D0
                ReinjTemp = (1.-Tfraction)*reinjtll + Tfraction*reinjtul
            elif self.pptype.value == PowerPlantType.SUPER_CRITICAL_ORC:
                if self.Tenv.value < 15.:
                    C2 = -1.55E-5
                    C1 = 7.604E-3
                    C0 = -3.78E-1
                    D2 = -1.499E-5
                    D1 = 7.4268E-3
                    D0 = -3.7915E-1
                    Tfraction = (self.Tenv.value-5.)/10.
                else:
                    C2 = -1.499E-5
                    C1 = 7.4268E-3
                    C0 = -3.7915E-1
                    D2 = -1.55E-5
                    D1 = 7.55136E-3
                    D0 = -4.041E-1
                    Tfraction = (self.Tenv.value-15.)/10.
                etaull = C2*self.TenteringPP.value**2 + C1*self.TenteringPP.value + C0
                etauul = D2*self.TenteringPP.value**2 + D1*self.TenteringPP.value + D0
                etau = (1-Tfraction)*etaull + Tfraction*etauul
                if self.Tenv.value < 15.:
                    C1 = 0.02
                    C0 = 49.26
                    D1 = 0.02
                    D0 = 56.26
                    Tfraction = (self.Tenv.value-5.)/10.
                else:
                    C1 = 0.02
                    C0 = 56.26
                    D1 = 0.02
                    D0 = 63.26
                    Tfraction = (self.Tenv.value-15.)/10.
                reinjtll = C1*self.TenteringPP.value + C0
                reinjtul = D1*self.TenteringPP.value + D0
                ReinjTemp = (1.-Tfraction)*reinjtll + Tfraction*reinjtul
            elif self.pptype.value == PowerPlantType.SINGLE_FLASH:
                if self.Tenv.value < 15.:
                    C2 = -4.27318E-7
                    C1 = 8.65629E-4
                    C0 = 1.78931E-1
                    D2 = -5.85412E-7
                    D1 = 9.68352E-4
                    D0 = 1.58056E-1
                    Tfraction = (self.Tenv.value-5.)/10.
                else:
                    C2 = -5.85412E-7
                    C1 = 9.68352E-4
                    C0 = 1.58056E-1
                    D2 = -7.78996E-7
                    D1 = 1.09230E-3
                    D0 = 1.33708E-1
                    Tfraction = (self.Tenv.value-15.)/10.
                etaull = C2*self.TenteringPP.value**2 + C1*self.TenteringPP.value + C0
                etauul = D2*self.TenteringPP.value**2 + D1*self.TenteringPP.value + D0
                etau = (1.-Tfraction)*etaull + Tfraction*etauul
                if self.Tenv.value < 15.:
                    C2 = -1.11519E-3
                    C1 = 7.79126E-1
                    C0 = -10.2242
                    D2 = -1.10232E-3
                    D1 = 7.83893E-1
                    D0 = -5.17039
                    Tfraction = (self.Tenv.value-5.)/10.
                else:
                    C2 = -1.10232E-3
                    C1 = 7.83893E-1
                    C0 = -5.17039
                    D2 = -1.08914E-3
                    D1 = 7.88562E-1
                    D0 = -1.89707E-1
                    Tfraction = (self.Tenv.value-15.)/10.
                reinjtll = C2*self.TenteringPP.value**2 + C1*self.TenteringPP.value + C0
                reinjtul = D2*self.TenteringPP.value**2 + D1*self.TenteringPP.value + D0
                ReinjTemp = (1.-Tfraction)*reinjtll + Tfraction*reinjtul
            elif self.pptype.value == PowerPlantType.DOUBLE_FLASH:
                if self.Tenv.value < 15.:
                    C2 = -1.200E-6
                    C1 = 1.22731E-3
                    C0 = 2.26956E-1
                    D2 = -1.42165E-6
                    D1 = 1.37050E-3
                    D0 = 1.99847E-1
                    Tfraction = (self.Tenv.value-5.)/10.
                else:
                    C2 = -1.42165E-6
                    C1 = 1.37050E-3
                    C0 = 1.99847E-1
                    D2 = -1.66771E-6
                    D1 = 1.53079E-3
                    D0 = 1.69439E-1
                    Tfraction = (self.Tenv.value-15.)/10.
                etaull = C2*self.TenteringPP.value**2 + C1*self.TenteringPP.value + C0
                etauul = D2*self.TenteringPP.value**2 + D1*self.TenteringPP.value + D0
                etau = (1.-Tfraction)*etaull + Tfraction*etauul
                if self.Tenv.value < 15.:
                    C2 = -7.70928E-4
                    C1 = 5.02466E-1
                    C0 = 5.22091
                    D2 = -7.69455E-4
                    D1 = 5.09406E-1
                    D0 = 11.6859
                    Tfraction = (self.Tenv.value-5.)/10.
                else:
                    C2 = -7.69455E-4
                    C1 = 5.09406E-1
                    C0 = 11.6859
                    D2 = -7.67751E-4
                    D1 = 5.16356E-1
                    D0 = 18.0798
                    Tfraction = (self.Tenv.value-15.)/10.
                reinjtll = C2*self.TenteringPP.value**2 + C1*self.TenteringPP.value + C0
                reinjtul = D2*self.TenteringPP.value**2 + D1*self.TenteringPP.value + D0
                ReinjTemp = (1.-Tfraction)*reinjtll + Tfraction*reinjtul

            # check if reinjectemp (model calculated) >= Tinj (user provided)
            if self.enduseoption.value == EndUseOptions.ELECTRICITY:  # pure electricity
                if np.min(ReinjTemp) < model.wellbores.Tinj.value:
                    model.wellbores.Tinj.value = np.min(ReinjTemp)
                    print("Warning: injection temperature lowered")
                    model.logger.warning("injection temperature lowered")
            elif self.enduseoption.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICTY, EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT]:  # enduseoption = 3: cogen topping cycle
                if np.min(ReinjTemp) < model.wellbores.Tinj.value:
                    self.Tinj = np.min(ReinjTemp)
                    print("Warning: injection temperature lowered")
                    model.logger.warning("injection temperature lowered")
            elif self.enduseoption.value in [EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICTY]:  # enduseoption = 4: cogen bottoming cycle
                if np.min(ReinjTemp) < model.wellbores.Tinj.value:
                    model.wellbores.Tinj.value = np.min(ReinjTemp)
                    print("Warning: injection temperature lowered")
                    model.logger.warning("injection temperature lowered")
            elif self.enduseoption.value in [EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICTY, EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT]:  # cogen split of mass flow rate
                if np.min(ReinjTemp) < model.wellbores.Tinj.value:
                    model.wellbores.Tinj.value = np.min(ReinjTemp)
                    print("Warning: injection temperature incorrect but cannot be lowered")
                    model.logger.warning("injection temperature incorrect but cannot be lowered")

            # calculate electricity/heat
            if self.enduseoption.value == EndUseOptions.ELECTRICITY: # pure electricity
                self.ElectricityProduced.value = self.Availability.value*etau*model.wellbores.nprod.value*model.wellbores.prodwellflowrate.value
                self.HeatExtracted.value = model.wellbores.nprod.value*model.wellbores.prodwellflowrate.value*model.reserv.cpwater.value *\
                                           (model.wellbores.ProducedTemperature.value - model.wellbores.Tinj.value)/1E6  # Heat extracted from geofluid [MWth]
                HeatExtractedTowardsElectricity = self.HeatExtracted.value
            # enduseoption = 3: cogen topping cycle
            elif self.enduseoption.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICTY, EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT]:
                self.ElectricityProduced.value = self.Availability.value*etau*model.wellbores.nprod.value*model.wellbores.prodwellflowrate.value
                self.HeatExtracted.value = model.wellbores.nprod.value*model.wellbores.prodwellflowrate.value*model.reserv.cpwater.value *\
                                           (model.wellbores.ProducedTemperature.value - model.wellbores.Tinj.value)/1E6  # Heat extracted from geofluid [MWth]
                self.HeatProduced.value = self.enduseefficiencyfactor.value*model.wellbores.nprod.value *\
                                          model.wellbores.prodwellflowrate.value*model.reserv.cpwater.value *\
                                          (ReinjTemp - model.wellbores.Tinj.value)/1E6  # Useful heat for direct-use application [MWth]
                HeatExtractedTowardsElectricity = model.wellbores.nprod.value*model.wellbores.prodwellflowrate.value *\
                                                  model.reserv.cpwater.value*(model.wellbores.ProducedTemperature.value - ReinjTemp)/1E6
            # enduseoption = 4: cogen bottoming cycle
            elif self.enduseoption.value in [EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICTY]:
                self.ElectricityProduced.value = self.Availability.value*etau*model.wellbores.nprod.value*model.wellbores.prodwellflowrate.value
                self.HeatExtracted.value = model.wellbores.nprod.value*model.wellbores.prodwellflowrate.value*model.reserv.cpwater.value *\
                                           (model.wellbores.ProducedTemperature.value - model.wellbores.Tinj.value)/1E6  # Heat extracted from geofluid [MWth]
                self.valueHeatProduced.value = self.enduseefficiencyfactor.value*model.wellbores.nprod.value *\
                                               model.wellbores.prodwellflowrate*model.reserv.cpwater.value *\
                                               (model.wellbores.ProducedTemperature.value - self.Tchpbottom.value)/1E6  # Useful heat for direct-use application [MWth]
                HeatExtractedTowardsElectricity = model.wellbores.nprod.value*model.wellbores.prodwellflowrate.value *\
                                                  model.reserv.cpwater.value*(self.Tchpbottom.value - model.wellbores.Tinj.value)/1E6
            # enduseoption = 5: cogen split of mass flow rate
            elif self.enduseoption.value in [EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICTY, EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT]:
                self.ElectricityProduced.value = self.Availability.value*etau*model.wellbores.nprod.value *\
                                                 model.wellbores.prodwellflowrate.value*(1.-self.chpfraction.value)  # electricity part [MWe]
                self.HeatExtracted.value = model.wellbores.nprod.value*model.wellbores.prodwellflowrate.value *\
                                           model.reserv.cpwater.value*(model.wellbores.ProducedTemperature.value -
                                           model.wellbores.Tinj.value)/1E6  # Total amount of heat extracted from geofluid [MWth]
                self.HeatProduced.value = self.enduseefficiencyfactor.value*self.chpfraction.value *\
                                          model.wellbores.nprod.value*model.wellbores.prodwellflowrate.value *\
                                          model.reserv.cpwater.value*(model.wellbores.ProducedTemperature.value -
                                          model.wellbores.Tinj.value)/1E6  # useful heat part for direct-use application [MWth]
                HeatExtractedTowardsElectricity = (1.-self.chpfraction.value)*model.wellbores.nprod.value *\
                                                  model.wellbores.prodwellflowrate.value*model.reserv.cpwater.value *\
                                                  (model.wellbores.ProducedTemperature.value - model.wellbores.Tinj.value)/1E6

            # subtract pumping power for net electricity and  calculate first law efficiency
            if self.enduseoption.value != EndUseOptions.HEAT:
                self.NetElectricityProduced.value = self.ElectricityProduced.value - model.wellbores.PumpingPower.value
                self.FirstLawEfficiency.value = self.NetElectricityProduced.value/HeatExtractedTowardsElectricity

        # Calculate annual electricity/heat production
        # all end-use options have "heat extracted from reservoir" and pumping kWs
        self.HeatkWhExtracted.value = np.zeros(self.plantlifetime.value)
        self.PumpingkWh.value = np.zeros(self.plantlifetime.value)
        for i in range(0, self.plantlifetime.value):
            self.HeatkWhExtracted.value[i] = np.trapz(self.HeatExtracted.value[(0+i*model.economics.timestepsperyear.value):((i+1)*model.economics.timestepsperyear.value)+1], dx=1./model.economics.timestepsperyear.value*365.*24.)*1000.*self.utilfactor.value
            self.PumpingkWh.value[i] = np.trapz(model.wellbores.PumpingPower.value[(0+i*model.economics.timestepsperyear.value):((i+1)*model.economics.timestepsperyear.value)+1], dx=1./model.economics.timestepsperyear.value*365.*24.)*1000.*self.utilfactor.value
        if self.enduseoption.value != EndUseOptions.HEAT:  # all these end-use options have an electricity generation component
            self.TotalkWhProduced.value = np.zeros(self.plantlifetime.value)
            self.NetkWhProduced.value = np.zeros(self.plantlifetime.value)
            for i in range(0, self.plantlifetime.value):
                self.TotalkWhProduced.value[i] = np.trapz(self.ElectricityProduced.value[(0+i*model.economics.timestepsperyear.value):((i+1)*model.economics.timestepsperyear.value)+1], dx=1./model.economics.timestepsperyear.value*365.*24.)*1000.*self.utilfactor.value
                self.NetkWhProduced.value[i] = np.trapz(self.NetElectricityProduced.value[(0+i*model.economics.timestepsperyear.value):((i+1)*model.economics.timestepsperyear.value)+1], dx=1./model.economics.timestepsperyear.value*365.*24.)*1000.*self.utilfactor.value
        if self.enduseoption.value != EndUseOptions.ELECTRICITY:  # all those end-use options have a direct-use component
            self.HeatkWhProduced.value = np.zeros(self.plantlifetime.value)
            for i in range(0, self.plantlifetime.value):
                self.HeatkWhProduced.value[i] = np.trapz(self.HeatProduced.value[(0+i*model.economics.timestepsperyear.value):((i+1)*model.economics.timestepsperyear.value)+1], dx=1./model.economics.timestepsperyear.value*365.*24.)*1000.*self.utilfactor.value

        #calculate reservoir heat content
        self.RemainingReservoirHeatContent.value = model.reserv.InitialReservoirHeatContent.value-np.cumsum(self.HeatkWhExtracted.value)*3600*1E3/1E15

        model.logger.info("complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

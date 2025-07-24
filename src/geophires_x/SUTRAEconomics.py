import sys
import os
import numpy as np
import geophires_x.Model as Model
import geophires_x.Economics as Economics
from geophires_x.OptionList import WellDrillingCostCorrelation, EconomicModel
from geophires_x.Parameter import intParameter, floatParameter, OutputParameter, ReadParameter, boolParameter
from geophires_x.Units import *


class SUTRAEconomics(Economics.Economics):
    """
    Class to support the default economic calculations in GEOPHIRES
    """

    def __init__(self, model: Model):
        model.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')
        super().__init__(model)

        self.LCOH = self.OutputParameterDict[self.LCOH.Name] = OutputParameter(
            "Heat Sale Price Model",
            display_name='Direct-Use heat breakeven price (LCOH)',
            value=[0.025],
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.CENTSSPERKWH,
            CurrentUnits=EnergyCostUnit.CENTSSPERKWH,
        )

        # local variable initialization
        self.Cpumps = 0.0
        self.InputFile = ""
        self.C1well = 0.0
        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = os.path.abspath(__file__)

        self.Coam = self.OutputParameterDict[self.Coam.Name] = OutputParameter(
            Name="Total O&M Cost",
            value=-999.9,
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.KDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.KDOLLARSPERYEAR,
        )
        self.annualpumpingcosts = self.OutputParameterDict[self.annualpumpingcosts.Name] = OutputParameter(
            Name="Annual Pumping Costs",
            value=-0.0,
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.KDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.KDOLLARSPERYEAR,
        )
        self.annualngcost = self.OutputParameterDict[self.annualngcost.Name] = OutputParameter(
            Name="Annual Peaking Fuel Cost",
            value=0,
            UnitType=Units.CURRENCYFREQUENCY,
            PreferredUnits=CurrencyFrequencyUnit.KDOLLARSPERYEAR,
            CurrentUnits=CurrencyFrequencyUnit.KDOLLARSPERYEAR,
        )

        model.logger.info(f'Complete {__class__!s}: {sys._getframe().f_code.co_name}')

    def read_parameters(self, model: Model) -> None:
        """
        read_parameters read and update the Economics parameters and handle the special cases that need to be taken care of after a
        value has been read in and checked. This is called from the main Model class. It is not called from the __init__
        function because the user may not want to read in the parameters from the input file, but may want to set them
        in the user interface.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing, but it does make calculations and set values in the model
        """
        model.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')

        # Deal with all the parameter values that the user has provided.  They should really only provide values
        # that they want to change from the default values, but they can provide a value that is already set
        # because it is a default value set in __init__.  It will ignore those.
        # This also deals with all the special cases that need to be taken care of after a
        # value has been read in and checked.
        # If you choose to subclass this master class, you can also choose to override this method (or not),
        # and if you do, do it before or after you call you own version of this method.  If you do, you can also
        # choose to call this method from you class, which can effectively modify all these superclass parameters
        # in your class.

        if len(model.InputParameters) > 0:
            # loop through all the parameters that the user wishes to set, looking for parameters that match this object
            for item in self.ParameterDict.items():
                ParameterToModify = item[1]
                key = ParameterToModify.Name.strip()
                if key in model.InputParameters:
                    ParameterReadIn = model.InputParameters[key]

                    # this should handle all the non-special cases
                    ReadParameter(ParameterReadIn, ParameterToModify, model)

                    # handle special cases
                    if ParameterToModify.Name == 'Economic Model':
                       self.econmodel.value = EconomicModel.from_input_string(ParameterReadIn.sValue)
                    elif ParameterToModify.Name == 'Well Drilling Cost Correlation':
                        ParameterToModify.value = WellDrillingCostCorrelation.from_input_string(ParameterReadIn.sValue)
        else:
            model.logger.info('No parameters read because no content provided')

        self.sync_interest_rate(model)

        model.logger.info(f'Complete {__class__!s}: {sys._getframe().f_code.co_name}')

    def Calculate(self, model: Model) -> None:
        """
        The Calculate function is where all the calculations are done.
        This function can be called multiple times, and will only recalculate what has changed each time it is called.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing, but it does make calculations and set values in the model
        """
        model.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')

        # This is where all the calculations are made using all the values that have been set.
        # If you subclass this class, you can choose to run these calculations before (or after) your calculations,
        # but that assumes you have set all the values that are required for these calculations
        # If you choose to subclass this master class, you can also choose to override this method (or not),
        # and if you do, do it before or after you call you own version of this method.  If you do,
        # you can also choose to call this method from you class, which can effectively run the calculations
        # of the superclass, making all thr values available to your methods. but you had
        # better have set all the parameters!

        # CAPEX
        # Drilling

        self.C1well = 0
        if self.per_production_well_cost.Valid:
            self.C1well = self.ccwellfixed.value
            self.Cwell.value = self.C1well * (model.wellbores.nprod.value + model.wellbores.ninj.value)
        else:
            if model.reserv.depth.value > 7000.0 or model.reserv.depth.value < 500:
                print('Warning: simple user-specified cost per meter used for drilling depth < 500 or > 7000 m')
                model.logger.warning(
                    'Warning: simple user-specified cost per meter used for drilling depth < 500 or > 7000 m'
                )

            self.C1well = self.wellcorrelation.value.calculate_cost_MUSD(model.reserv.depth.value)

            self.C1well = self.C1well * self.production_well_cost_adjustment_factor.value
            self.Cwell.value = self.C1well * (model.wellbores.nprod.value + model.wellbores.ninj.value)

        # Boiler
        self.peakingboilercost.value = (
            self.peaking_boiler_cost_per_kW.quantity().to('USD/kW').magnitude
            * model.surfaceplant.max_peaking_boiler_demand.value
            / self.peakingboilerefficiency.value
            / 1000
        )

        # Circulation Pump
        pumphp = np.max(model.wellbores.PumpingPower.value) * 1.341
        numberofpumps = np.ceil(pumphp / 2000)  # pump can be maximum 2,000 hp
        if numberofpumps == 0:
            self.Cpumps = 0.0
        else:
            pumphpcorrected = pumphp / numberofpumps
            self.Cpumps = numberofpumps * 1.5 * ((1750 * pumphpcorrected**0.7) * 3 * pumphpcorrected ** (-0.11)) / 1e6

        # Total CAPEX ($M)
        self.CCap.value = self.Cwell.value + self.peakingboilercost.value + self.Cpumps

        # OPEX
        # Pumping
        self.annualpumpingcosts.value = (
            model.surfaceplant.PumpingkWh.value * model.surfaceplant.electricity_cost_to_buy.value / 1e3
        )

        # Natural Gas
        self.annualngcost.value = (
            model.surfaceplant.AnnualAuxiliaryHeatProduced.value
            * self.ngprice.value
            / self.peakingboilerefficiency.value
            * 1e3
        )

        # Price for the heat injected currently not considered

        # Total O&M cost ($K/year)
        self.Coam.value = self.annualpumpingcosts.value + self.annualngcost.value

        # LCOH
        discountvector = 1.0 / np.power(
            1 + self.discountrate.value,
            np.linspace(0, model.surfaceplant.plant_lifetime.value - 1, model.surfaceplant.plant_lifetime.value),
        )
        self.LCOH.value = (
            ((1 + self.inflrateconstruction.value) * self.CCap.value + np.sum(self.Coam.value * discountvector))
            / np.sum(model.surfaceplant.AnnualTotalHeatProduced.value * 1e6 * discountvector)
            * 1e8
        )  # cents/kWh

        self._calculate_derived_outputs(model)
        model.logger.info(f'complete {str(__class__)}: {sys._getframe().f_code.co_name}')

    def __str__(self):
        return "Economics"

import datetime
import time
import sys

import geophires_x
import geophires_x.Model as Model
from geophires_x.Outputs import Outputs
from geophires_x.OptionList import EconomicModel

import numpy as np

NL="\n"


class SUTRAOutputs(Outputs):

    def __init__(self, model:Model, output_file:str ='HDR.out'):
        """
        The __init__ function is called automatically when a class is instantiated.
        It initializes the attributes of an object, and sets default values for certain arguments that can be
        overridden by user input.
        The __init__ function is used to set up all the parameters in the Outputs.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """

        model.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')

        # Dictionary to hold the Units definitions that the user wants for outputs created by GEOPHIRES.
        # It is empty by default initially - this will expand as the user desires are read from the input file
        self.ParameterDict = {}
        self.printoutput = True
        self.output_file = output_file

        model.logger.info(f'Complete {str(__class__)}: {sys._getframe().f_code.co_name}')

    def __str__(self):
        return 'SUTRAOutputs'


    def PrintOutputs(self, model: Model):
        """
        PrintOutputs writes the standard outputs to the output file.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        model.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')

        self._convert_units(model)

        # write results to output file and screen
        try:
            with open(self.output_file,'w', encoding='UTF-8') as f:
                f.write('                               *****************\n')
                f.write('                               ***CASE REPORT***\n')
                f.write('                               *****************\n')
                f.write(NL)
                f.write("Simulation Metadata\n")
                f.write("----------------------\n")
                f.write(f' GEOPHIRES Version: {geophires_x.__version__}\n')
                f.write(" Simulation Date: "+ datetime.datetime.now().strftime("%Y-%m-%d\n"))
                f.write(" Simulation Time:  "+ datetime.datetime.now().strftime("%H:%M\n"))
                f.write(" Calculation Time: "+"{0:10.3f}".format((time.time()-model.tic)) + " sec\n")

                f.write(NL)
                f.write('                           ***SUMMARY OF RESULTS***\n')
                f.write(NL)
                f.write("      End-Use Option: " + str(model.surfaceplant.enduse_option.value.value) + NL)
                f.write("      Reservoir Model = " + str(model.reserv.resoption.value.value) + " Model\n")
                f.write(f"      Direct-Use heat breakeven price:                  {model.economics.LCOH.value:10.2f} " + model.economics.LCOH.CurrentUnits.value + NL)

                f.write(f"      Number of Production Wells:                    {model.wellbores.nprod.value:10.0f}"+NL)
                f.write(f"      Number of Injection Wells:                     {model.wellbores.ninj.value:10.0f}"+NL)
                f.write(f"      Lifetime Average Well Flow Rate:               {np.average(abs(model.wellbores.ProductionWellFlowRates.value)):10.1f} "  + model.wellbores.ProductionWellFlowRates.CurrentUnits.value + NL)
                f.write(f"      Well depth:                                    {model.reserv.depth.value:10.1f} " +model.reserv.depth.CurrentUnits.value + NL)

                f.write(NL)
                f.write(NL)
                f.write('                           ***ECONOMIC PARAMETERS***\n')
                f.write(NL)
                if model.economics.econmodel.value == EconomicModel.FCR:
                    f.write("      Economic Model = " + model.economics.econmodel.value.value + NL)
                    f.write(f"      Fixed Charge Rate (FCR):                          {model.economics.FCR.value*100.0:10.2f} " + model.economics.FCR.CurrentUnits.value + NL)
                elif model.economics.econmodel.value == EconomicModel.STANDARDIZED_LEVELIZED_COST:
                    f.write("      Economic Model = " + model.economics.econmodel.value.value + NL)
                    f.write(f'      {model.economics.interest_rate.Name}:                                    {model.economics.interest_rate.value:10.2f} {model.economics.interest_rate.CurrentUnits.value}\n')

                elif model.economics.econmodel.value == EconomicModel.BICYCLE:
                    f.write("      Economic Model  = " + model.economics.econmodel.value.value + NL)
                f.write(f"      Accrued financing during construction:            {model.economics.inflrateconstruction.value*100:10.2f} " + model.economics.inflrateconstruction.PreferredUnits.value + NL)
                f.write(f"      Project lifetime:                              {model.surfaceplant.plant_lifetime.value:10.0f} " + model.surfaceplant.plant_lifetime.CurrentUnits.value + NL)

                f.write(NL)
                f.write('                          ***ENGINEERING PARAMETERS***\n')
                f.write(NL)
                f.write(f"      Number of Production Wells:                    {model.wellbores.nprod.value:10.0f}" + NL)
                f.write(f"      Number of Injection Wells:                     {model.wellbores.ninj.value:10.0f}" + NL)
                f.write(f"      Well depth:                                    {model.reserv.depth.value:10.1f} " + model.reserv.depth.CurrentUnits.value + NL)

                pump_efficiency_display_unit = model.surfaceplant.pump_efficiency.CurrentUnits.value
                pump_efficiency_display = f'{model.surfaceplant.pump_efficiency.value:10.1f} {pump_efficiency_display_unit}'
                f.write(f'      Pump efficiency:                               {pump_efficiency_display}{NL}')

                f.write(f"      Lifetime Average Well Flow Rate:               {np.average(abs(model.wellbores.ProductionWellFlowRates.value)):10.1f} "  + model.wellbores.ProductionWellFlowRates.CurrentUnits.value + NL)
                f.write(f'      {model.wellbores.injection_well_casing_inner_diameter.display_name}:                          {model.wellbores.injection_well_casing_inner_diameter.value:10.3f} {model.wellbores.injection_well_casing_inner_diameter.CurrentUnits.value}\n')
                f.write(f'      {model.wellbores.production_well_casing_inner_diameter.display_name}:                         {model.wellbores.production_well_casing_inner_diameter.value:10.3f} {model.wellbores.production_well_casing_inner_diameter.CurrentUnits.value}\n')
                f.write(NL)
                f.write(NL)
                f.write("                           ***RESERVOIR SIMULATION RESULTS***" + NL)
                f.write(NL)
                f.write(f"      Maximum Storage Well Temperature:              {np.max(model.wellbores.ProducedTemperature.value):10.1f} " + model.wellbores.ProducedTemperature.PreferredUnits.value + NL)
                f.write(f"      Average Storage Well Temperature:              {np.average(model.wellbores.ProducedTemperature.value):10.1f} " + model.wellbores.ProducedTemperature.PreferredUnits.value + NL)
                f.write(f"      Minimum Storage Well Temperature:              {np.min(model.wellbores.ProducedTemperature.value):10.1f} " + model.wellbores.ProducedTemperature.PreferredUnits.value + NL)
                f.write(f"      Maximum Balance Well Temperature:              {np.max(model.wellbores.Tinj.value):10.1f} " + model.wellbores.Tinj.PreferredUnits.value + NL)
                f.write(f"      Average Balance Well Temperature:              {np.average(model.wellbores.Tinj.value):10.1f} " + model.wellbores.Tinj.PreferredUnits.value + NL)
                f.write(f"      Minimum Balance Well Temperature:              {np.min(model.wellbores.Tinj.value):10.1f} " + model.wellbores.Tinj.PreferredUnits.value + NL)
                f.write(f"      Maximum Annual Heat Stored:                    {np.max(model.reserv.AnnualHeatStored.value):10.1f} " + model.reserv.AnnualHeatStored.PreferredUnits.value + NL)
                f.write(f"      Average Annual Heat Stored:                    {np.average(model.reserv.AnnualHeatStored.value):10.1f} " + model.reserv.AnnualHeatStored.PreferredUnits.value + NL)
                f.write(f"      Minimum Annual Heat Stored:                    {np.min(model.reserv.AnnualHeatStored.value):10.1f} " + model.reserv.AnnualHeatStored.PreferredUnits.value + NL)
                f.write(f"      Maximum Annual Heat Supplied:                  {np.max(model.reserv.AnnualHeatSupplied.value):10.1f} " + model.reserv.AnnualHeatSupplied.PreferredUnits.value + NL)
                f.write(f"      Average Annual Heat Supplied:                  {np.average(model.reserv.AnnualHeatSupplied.value):10.1f} " + model.reserv.AnnualHeatSupplied.PreferredUnits.value + NL)
                f.write(f"      Minimum Annual Heat Supplied:                  {np.min(model.reserv.AnnualHeatSupplied.value):10.1f} " + model.reserv.AnnualHeatSupplied.PreferredUnits.value + NL)
                f.write(f"      Average Round-Trip Efficiency:                 {np.average(model.reserv.AnnualRTESEfficiency.value):10.1f} " + model.reserv.AnnualRTESEfficiency.PreferredUnits.value + NL)
                f.write(f"      Total Average Pressure Drop:                   {np.average(model.wellbores.DPOverall.value):10.1f} " + model.wellbores.DPOverall.PreferredUnits.value + NL)
                f.write(NL)
                f.write(NL)
                f.write('                           ***SURFACE EQUIPMENT SIMULATION RESULTS***\n')
                f.write(NL)
                f.write(f"      Average RTES Heating Production:               {np.average(model.surfaceplant.HeatProduced.value):10.2f} " + model.surfaceplant.HeatProduced.PreferredUnits.value + NL)
                f.write(f"      Average Auxiliary Heating Production:          {np.average(model.surfaceplant.AuxiliaryHeatProduced.value):10.2f} " + model.surfaceplant.AuxiliaryHeatProduced.PreferredUnits.value + NL)
                f.write(f"      Average Annual RTES Heating Production:        {np.average(model.surfaceplant.AnnualHeatProduced.value):10.2f} " + model.surfaceplant.AnnualHeatProduced.PreferredUnits.value + NL)
                f.write(f"      Average Annual Auxiliary Heating Production:   {np.average(model.surfaceplant.AnnualAuxiliaryHeatProduced.value):10.2f} " + model.surfaceplant.AnnualAuxiliaryHeatProduced.PreferredUnits.value + NL)
                f.write(f"      Average Annual Total Heating Production:       {np.average(model.surfaceplant.AnnualTotalHeatProduced.value):10.2f} " + model.surfaceplant.AnnualTotalHeatProduced.PreferredUnits.value + NL)
                f.write(f"      Average Pumping Power:                         {np.average(model.wellbores.PumpingPower.value):10.2f} {model.wellbores.PumpingPower.CurrentUnits.value}{NL}")
                f.write(f"      Average Annual Electricity Use for Pumping:    {np.average(model.surfaceplant.PumpingkWh.value):10.2f} " + model.surfaceplant.PumpingkWh.PreferredUnits.value + NL)
                f.write(NL)
                f.write(NL)
                f.write('                          ***CAPITAL COSTS (M$)***\n')
                f.write(NL)
                f.write(f"      Drilling and Completion Costs:                 {model.economics.Cwell.value:10.2f} " + model.economics.Cwell.CurrentUnits.value + NL)
                if model.economics.cost_one_production_well.value != model.economics.cost_one_injection_well.value:
                    f.write(
                        f'             Drilling and completion costs per production well:   {model.economics.cost_one_production_well.value:10.2f} ' + model.economics.cost_one_production_well.CurrentUnits.value + NL)
                    f.write(
                        f'             Drilling and completion costs per injection well:    {model.economics.cost_one_injection_well.value:10.2f} ' + model.economics.cost_one_injection_well.CurrentUnits.value + NL)
                else:
                    f.write(f"      Drilling and Completion Costs per Well:        {model.economics.Cwell.value / (model.wellbores.nprod.value + model.wellbores.ninj.value):10.2f} " + model.economics.Cwell.CurrentUnits.value + NL)
                f.write(f"      Auxiliary Heater Cost:                         {model.economics.peakingboilercost.value:10.2f} " + model.economics.peakingboilercost.CurrentUnits.value + NL)
                f.write(f"      Pump Cost:                                     {model.economics.Cpumps:10.2f} " + model.economics.peakingboilercost.CurrentUnits.value + NL)
                f.write(f"      Total Capital Costs:                           {model.economics.CCap.value:10.2f} " + model.economics.CCap.CurrentUnits.value + NL)
                f.write(NL)
                f.write(NL)
                f.write('                ***OPERATING AND MAINTENANCE COSTS (M$/yr)***\n')
                f.write(NL)
                f.write(f"      Average annual auxiliary fuel cost:            {np.average(model.economics.annualngcost.value):10.2f} " + model.economics.annualngcost.CurrentUnits.value + NL)
                f.write(f"      Average annual pumping cost:                   {np.average(model.economics.annualpumpingcosts.value):10.2f} " + model.economics.annualpumpingcosts.CurrentUnits.value + NL)
                f.write(f"      Total average annual O&M costs:                {np.average(model.economics.Coam.value):10.2f} " + model.economics.Coam.CurrentUnits.value + NL)


        except BaseException as ex:
            tb = sys.exc_info()[2]
            print(str(ex))
            msg = "Error: GEOPHIRES Failed to write the output file.  Exiting....Line %i" % tb.tb_lineno
            print(msg)
            model.logger.critical(str(ex))
            model.logger.critical(msg)
            raise RuntimeError(msg)

        model.logger.info(f'Complete {str(__class__)}: {sys._getframe().f_code.co_name}')

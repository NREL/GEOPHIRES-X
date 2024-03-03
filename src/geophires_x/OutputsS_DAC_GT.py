import sys
from geophires_x.Outputs import Outputs

NL = "\n"


class OutputsS_DAC_GT(Outputs):
    """
    Class to handles output of the SDAC_GT values
    """
    def PrintOutputs(self, model):
        """
        The PrintOutputs function prints the results of the SDAC_GT to a text file and to the screen.
        :param model: Model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        # now do S_DAC_GT output, which will append to the original output
        # write results to output file and screen
        try:
            if len(sys.argv) > 2:
                self.output_file = sys.argv[2]
            with open(self.output_file, 'a', encoding='UTF-8') as f:
                f.write(NL)
                f.write(NL)
                f.write("                            ***S_DAC_GT ECONOMICS***" + NL)
                f.write(NL)
                f.write(NL)
                f.write(f"      S-DAC-GT Report: Levelized Cost of Direct Air Capture (LCOD)" + NL)
                f.write(f"      Using grid-based electricity only: {model.sdacgteconomics.LCOD_elec.value:10.2f} " + model.sdacgteconomics.LCOD_elec.PreferredUnits.value + NL)
                f.write(f"      Using natural gas only:            {model.sdacgteconomics.LCOD_ng.value:10.2f} " + model.sdacgteconomics.LCOD_ng.PreferredUnits.value + NL)
                f.write(f"      Using geothermal energy only:      {model.sdacgteconomics.LCOD_geo.value:10.2f} " + model.sdacgteconomics.LCOD_geo.PreferredUnits.value + NL + NL)
                f.write(f"      S-DAC-GT Report: CO2 Intensity of process (percent of CO2 mitigated that is emitted by S-DAC process)" + NL)
                f.write(f"      Using grid-based electricity only: {model.sdacgteconomics.CO2total_elec.value*100.0:10.2f}%" + NL)
                f.write(f"      Using natural gas only:            {model.sdacgteconomics.CO2total_ng.value*100:10.2f}%" + NL)
                f.write(f"      Using geothermal energy only:      {model.sdacgteconomics.CO2total_geo.value*100:10.2f}%" + NL + NL)
                f.write(f"      Geothermal LCOH:                     {model.sdacgteconomics.LCOH.value:10.4f} " + model.sdacgteconomics.LCOH.PreferredUnits.value + NL)
                f.write(f"      Geothermal Ratio (electricity vs heat):{model.sdacgteconomics.percent_thermal_energy_going_to_heat.value*100:10.4f}%" + NL)
                f.write(f"      Percent Energy Devoted To Process: {model.sdacgteconomics.EnergySplit.value*100:10.4f}%" + NL + NL)
                f.write(f"      Total Tonnes of CO2 Captured:      {model.sdacgteconomics.CarbonExtractedTotal.value:,.2f} " + model.sdacgteconomics.CarbonExtractedTotal.PreferredUnits.value + NL)
                f.write(f"      Total Cost of Capture:             {model.sdacgteconomics.S_DAC_GTCummCashFlow.value[len(model.sdacgteconomics.S_DAC_GTCummCashFlow.value)-1]:,.2f} " + model.sdacgteconomics.S_DAC_GTCummCashFlow.PreferredUnits.value + NL)
                f.write(NL)
                f.write(NL)
                f.write("                **********************" + NL)
                f.write("                *  S_DAC_GT PROFILE  *" + NL)
                f.write("                **********************" + NL)
                f.write("Year       Carbon      Cumm. Carbon     S_DAC_GT           S_DAC_GT Cumm.      Cumm. Cost" + NL)
                f.write("Since      Captured     Captured       Annual Cost          Cash Flow        Cost Per Tonne" + NL)
                f.write("Start     ("+model.sdacgteconomics.CarbonExtractedAnnually.PreferredUnits.value +
                                              ")   ("+model.sdacgteconomics.S_DAC_GTCummCarbonExtracted.PreferredUnits.value +
                                                             ")          ("+model.sdacgteconomics.S_DAC_GTAnnualCost.PreferredUnits.value +
                                             ")               ("+model.sdacgteconomics.S_DAC_GTCummCashFlow.PreferredUnits.value +
                                             ")           ("+model.sdacgteconomics.CummCostPerTonne.PreferredUnits.value + ")" +NL)
                i = 0
                for i in range(0, model.surfaceplant.plant_lifetime.value, 1):
                    f.write(f"   {i+1:3.0f}    {model.sdacgteconomics.CarbonExtractedAnnually.value[i]:,.2f}   {model.sdacgteconomics.S_DAC_GTCummCarbonExtracted.value[i]:,.2f}    {model.sdacgteconomics.S_DAC_GTAnnualCost.value[i]:,.2f}         {model.sdacgteconomics.S_DAC_GTCummCashFlow.value[i]:,.2f}         {model.sdacgteconomics.CummCostPerTonne.value[i]:.2f}" + NL)
                    i = i + 1

        except BaseException as ex:
            tb = sys.exc_info()[2]
            print(str(ex))
            print("Error: GEOPHIRES failed to Failed to write the output file.  Exiting....Line %i" % tb.tb_lineno)
            model.logger.critical(str(ex))
            model.logger.critical("Error: GEOPHIRES failed to Failed to write the output file.  Exiting....Line %i" % tb.tb_lineno)
            sys.exit()

        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

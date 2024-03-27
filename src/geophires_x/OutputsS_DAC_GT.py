import sys
import pandas as pd
from geophires_x.Outputs import Outputs, OutputTableItem

NL = "\n"


class OutputsS_DAC_GT(Outputs):
    """
    Class to handles output of the SDAC_GT values
    """
    def PrintOutputs(self, model) -> tuple:
        """
        The PrintOutputs function prints the results of the SDAC_GT to a text file and to the screen.
        :param model: Model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing
        """
        model.logger.info(f'Init  {str(__class__)}: {__name__}')

        # now do S_DAC_GT output, which will append to the original output
        # write results to output file and screen
        try:
            with open(self.output_file, 'a', encoding='UTF-8') as f:
                sdac_results: list[OutputTableItem] = []
                f.write(NL)
                f.write(NL)
                f.write("                            ***S_DAC_GT ECONOMICS***" + NL)
                f.write(NL)
                f.write(NL)
                f.write(f"      S-DAC-GT Report: Levelized Cost of Direct Air Capture (LCOD)" + NL)
                sdac_results.append(OutputTableItem('S-DAC-GT Report: Levelized Cost of Direct Air Capture (LCOD)'))
                f.write(f"      Using grid-based electricity only: {model.sdacgteconomics.LCOD_elec.value:10.2f} " + model.sdacgteconomics.LCOD_elec.PreferredUnits.value + NL)
                sdac_results.append(OutputTableItem('Using grid-based electricity only', '{0:10.2f}'.format(model.sdacgteconomics.LCOD_elec.value), model.sdacgteconomics.LCOD_elec.PreferredUnits.value))
                f.write(f"      Using natural gas only:            {model.sdacgteconomics.LCOD_ng.value:10.2f} " + model.sdacgteconomics.LCOD_ng.PreferredUnits.value + NL)
                sdac_results.append(OutputTableItem('Using natural gas only', '{0:10.2f}'.format(model.sdacgteconomics.LCOD_ng.value), model.sdacgteconomics.LCOD_ng.PreferredUnits.value))
                f.write(f"      Using geothermal energy only:      {model.sdacgteconomics.LCOD_geo.value:10.2f} " + model.sdacgteconomics.LCOD_geo.PreferredUnits.value + NL + NL)
                sdac_results.append(OutputTableItem('Using geothermal energy only', '{0:10.2f}'.format(model.sdacgteconomics.LCOD_geo.value), model.sdacgteconomics.LCOD_geo.PreferredUnits.value))
                f.write(f"      S-DAC-GT Report: CO2 Intensity of process (percent of CO2 mitigated that is emitted by S-DAC process)" + NL)
                sdac_results.append(OutputTableItem('S-DAC-GT Report: CO2 Intensity of process (percent of CO2 mitigated that is emitted by S-DAC process)'))
                f.write(f"      Using grid-based electricity only: {model.sdacgteconomics.CO2total_elec.value*100.0:10.2f}%" + NL)
                sdac_results.append(OutputTableItem('Using grid-based electricity only', '{0:10.2f}'.format(model.sdacgteconomics.CO2total_elec.value*100.0), '%'))
                f.write(f"      Using natural gas only:            {model.sdacgteconomics.CO2total_ng.value*100:10.2f}%" + NL)
                sdac_results.append(OutputTableItem('Using natural gas only', '{0:10.2f}'.format(model.sdacgteconomics.CO2total_ng.value*100.0), '%'))
                f.write(f"      Using geothermal energy only:      {model.sdacgteconomics.CO2total_geo.value*100:10.2f}%" + NL + NL)
                sdac_results.append(OutputTableItem('Using geothermal energy only', '{0:10.2f}'.format(model.sdacgteconomics.CO2total_geo.value*100.0), '%'))
                f.write(f"      Geothermal LCOH:                     {model.sdacgteconomics.LCOH.value:10.4f} " + model.sdacgteconomics.LCOH.PreferredUnits.value + NL)
                sdac_results.append(OutputTableItem('Geothermal LCOH', '{0:10.4f}'.format(model.sdacgteconomics.LCOH.value), model.sdacgteconomics.LCOH.PreferredUnits.value))
                f.write(f"      Geothermal Ratio (electricity vs heat):{model.sdacgteconomics.percent_thermal_energy_going_to_heat.value*100:10.4f}%" + NL)
                sdac_results.append(OutputTableItem('Geothermal Ratio (electricity vs heat)', '{0:10.4f}'.format(model.sdacgteconomics.percent_thermal_energy_going_to_heat.value*100.0), '%'))
                f.write(f"      Percent Energy Devoted To Process: {model.sdacgteconomics.EnergySplit.value*100:10.4f}%" + NL + NL)
                sdac_results.append(OutputTableItem('Percent Energy Devoted To Process', '{0:10.4f}'.format(model.sdacgteconomics.EnergySplit.value*100.0), '%'))
                f.write(f"      Total Tonnes of CO2 Captured:      {model.sdacgteconomics.CarbonExtractedTotal.value:,.2f} " + model.sdacgteconomics.CarbonExtractedTotal.PreferredUnits.value + NL)
                sdac_results.append(OutputTableItem('Total Tonnes of CO2 Captured', '{0:,.2f}'.format(model.sdacgteconomics.CarbonExtractedTotal.value), model.sdacgteconomics.CarbonExtractedTotal.PreferredUnits.value))
                f.write(f"      Total Cost of Capture:             {model.sdacgteconomics.S_DAC_GTCummCashFlow.value[len(model.sdacgteconomics.S_DAC_GTCummCashFlow.value)-1]:,.2f} " + model.sdacgteconomics.S_DAC_GTCummCashFlow.PreferredUnits.value + NL)
                sdac_results.append(OutputTableItem('Total Cost of Capture', '{0:,.2f}'.format(model.sdacgteconomics.S_DAC_GTCummCashFlow.value[len(model.sdacgteconomics.S_DAC_GTCummCashFlow.value)-1]), model.sdacgteconomics.S_DAC_GTCummCashFlow.PreferredUnits.value))
                f.write(NL)

                # Build the data frame to hold the SDAC result profile
                sdac_df = pd.DataFrame()
                # add the columns as needed based on the output.
                # Note that the correct format for that column is stashed in the title of that column
                # so that it can be used in the write statement.
                sdac_df[f'Year|:3.0f'] = [i for i in range(1, (model.surfaceplant.plant_lifetime.value + 1))]
                sdac_df[f'Carbon Captured ({model.sdacgteconomics.CarbonExtractedAnnually.PreferredUnits.value})|:,.2f'] = \
                    model.sdacgteconomics.CarbonExtractedAnnually.value
                sdac_df[f'Cum. Carbon Captured ({model.sdacgteconomics.S_DAC_GTCummCarbonExtracted.PreferredUnits.value})|:,.2f'] = \
                    model.sdacgteconomics.S_DAC_GTCummCarbonExtracted.value
                sdac_df[f'S_DAC_GT Annual Cost ({model.sdacgteconomics.S_DAC_GTAnnualCost.PreferredUnits.value})|:,.2f'] = \
                model.sdacgteconomics.S_DAC_GTAnnualCost.value
                sdac_df[f'S_DAC_GT Cumulative Cash Flow ({model.sdacgteconomics.S_DAC_GTCummCashFlow.PreferredUnits.value})|:,.2f'] = \
                    model.sdacgteconomics.S_DAC_GTCummCashFlow.value
                sdac_df[f'Cum. Cost Per Tonne ({model.sdacgteconomics.CummCostPerTonne.PreferredUnits.value})|:,.2f'] = \
                    model.sdacgteconomics.CummCostPerTonne.value

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

        model.logger.info(f'Complete {str(__class__)}: {__name__}')

        sdac_df = sdac_df.reset_index()
        return sdac_df, sdac_results

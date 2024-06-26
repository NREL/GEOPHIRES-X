import sys
import pandas as pd
from geophires_x.Outputs import Outputs, OutputTableItem


NL = "\n"


class OutputsAddOns(Outputs):
    """
    Class to handle output of the AddOns values
    """
    def PrintOutputs(self, model) -> tuple:

        """
        The PrintOutputs function prints the results of the AddOns to a text file and to the screen.
        :param model: Model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        model.logger.info(f'Init {str(__class__)}: {__name__}')

        # now do AddOn output, which will append to the original output
        # write results to output file and screen
        try:
            with open(self.output_file, 'a', encoding='UTF-8') as f:
                addon_results: list[OutputTableItem] = []
                f.write(NL)
                f.write(NL)
                f.write("                                ***EXTENDED ECONOMICS***\n")
                f.write(NL)
                if model.economics.LCOE.value > -999.0:
                    f.write(f"      Adjusted Project LCOE (after incentives, grants, AddOns,etc):     {model.economics.LCOE.value:10.2f} " + model.economics.LCOE.PreferredUnits.value + NL)
                    addon_results.append(OutputTableItem('Adjusted Project LCOE (after incentives, grants, AddOns,etc)', '{0:10.2f}'.format(model.economics.LCOE.value), model.economics.LCOE.PreferredUnits.value))
                if model.economics.LCOH.value > -999.0:
                    f.write(f"      Adjusted Project LCOH (after incentives, grants, AddOns,etc):     {model.economics.LCOH.value:10.2f} " + model.economics.LCOH.PreferredUnits.value + NL)
                    addon_results.append(OutputTableItem('Adjusted Project LCOH (after incentives, grants, AddOns,etc)', '{0:10.2f}'.format(model.economics.LCOH.value), model.economics.LCOH.PreferredUnits.value))
                f.write(f"      Adjusted Project CAPEX (after incentives, grants, AddOns, etc):   {model.addeconomics.AdjustedProjectCAPEX.value:10.2f} " + model.addeconomics.AdjustedProjectCAPEX.PreferredUnits.value + NL)
                addon_results.append(OutputTableItem('Adjusted Project CAPEX (after incentives, grants, AddOns, etc)', '{0:10.2f}'.format(model.addeconomics.AdjustedProjectCAPEX.value), model.addeconomics.AdjustedProjectCAPEX.PreferredUnits.value))
                f.write(f"      Adjusted Project OPEX (after incentives, grants, AddOns, etc):    {model.addeconomics.AdjustedProjectOPEX.value:10.2f} " + model.addeconomics.AdjustedProjectOPEX.PreferredUnits.value + NL)
                addon_results.append(OutputTableItem('Adjusted Project OPEX (after incentives, grants, AddOns, etc)', '{0:10.2f}'.format(model.addeconomics.AdjustedProjectOPEX.value), model.addeconomics.AdjustedProjectOPEX.PreferredUnits.value))
                f.write(f"      Project NPV   (including AddOns):                                 {model.addeconomics.ProjectNPV.value:10.2f} " + model.addeconomics.ProjectNPV.PreferredUnits.value + NL)
                addon_results.append(OutputTableItem('Project NPV (including AddOns)', '{0:10.2f}'.format(model.addeconomics.ProjectNPV.value), model.addeconomics.ProjectNPV.PreferredUnits.value))
                f.write(f"      Project IRR   (including AddOns):                                 {model.addeconomics.ProjectIRR.value:10.2f} " + model.addeconomics.ProjectIRR.PreferredUnits.value + NL)
                addon_results.append(OutputTableItem('Project IRR (including AddOns)', '{0:10.2f}'.format(model.addeconomics.ProjectIRR.value), model.addeconomics.ProjectIRR.PreferredUnits.value))
                f.write(f"      Project VIR=PI=PIR   (including AddOns):                          {model.addeconomics.ProjectVIR.value:10.2f}" + NL)
                addon_results.append(OutputTableItem('Project VIR=PI=PIR (including AddOns)', '{0:10.2f}'.format(model.addeconomics.ProjectVIR.value), ''))
                f.write(f"      Project MOIC  (including AddOns):                                 {model.addeconomics.ProjectMOIC.value:10.2f}" + NL)
                addon_results.append(OutputTableItem('Project MOIC (including AddOns)', '{0:10.2f}'.format(model.addeconomics.ProjectMOIC.value), ''))
                if model.addeconomics.AddOnCAPEXTotal.value + model.addeconomics.AddOnOPEXTotalPerYear.value != 0:
                    f.write(f"      Total Add-on CAPEX:                                               {model.addeconomics.AddOnCAPEXTotal.value:10.2f} " + model.addeconomics.AddOnCAPEXTotal.PreferredUnits.value + NL)
                    addon_results.append(OutputTableItem('Total Add-on CAPEX', '{0:10.2f}'.format(model.addeconomics.AddOnCAPEXTotal.value), model.addeconomics.AddOnCAPEXTotal.PreferredUnits.value))
                    f.write(f"      Total Add-on OPEX:                                                {model.addeconomics.AddOnOPEXTotalPerYear.value:10.2f} " + model.addeconomics.AddOnOPEXTotalPerYear.PreferredUnits.value + NL)
                    addon_results.append(OutputTableItem('Total Add-on OPEX', '{0:10.2f}'.format(model.addeconomics.AddOnOPEXTotalPerYear.value), model.addeconomics.AddOnOPEXTotalPerYear.PreferredUnits.value))
                    f.write(f"      Total Add-on Net Elec:                                            {model.addeconomics.AddOnElecGainedTotalPerYear.value:10.2f} " + model.addeconomics.AddOnElecGainedTotalPerYear.PreferredUnits.value + NL)
                    addon_results.append(OutputTableItem('Total Add-on Net Elec', '{0:10.2f}'.format(model.addeconomics.AddOnElecGainedTotalPerYear.value), model.addeconomics.AddOnElecGainedTotalPerYear.PreferredUnits.value))
                    f.write(f"      Total Add-on Net Heat:                                            {model.addeconomics.AddOnHeatGainedTotalPerYear.value:10.2f} " + model.addeconomics.AddOnHeatGainedTotalPerYear.PreferredUnits.value + NL)
                    addon_results.append(OutputTableItem('Total Add-on Net Heat', '{0:10.2f}'.format(model.addeconomics.AddOnHeatGainedTotalPerYear.value), model.addeconomics.AddOnHeatGainedTotalPerYear.PreferredUnits.value))
                    f.write(f"      Total Add-on Profit:                                              {model.addeconomics.AddOnProfitGainedTotalPerYear.value:10.2f} " + model.addeconomics.AddOnProfitGainedTotalPerYear.PreferredUnits.value + NL)
                    addon_results.append(OutputTableItem('Total Add-on Profit', '{0:10.2f}'.format(model.addeconomics.AddOnProfitGainedTotalPerYear.value), model.addeconomics.AddOnProfitGainedTotalPerYear.PreferredUnits.value))
                    f.write(f"      AddOns Payback Period:                                            {model.addeconomics.AddOnPaybackPeriod.value:10.2f} " + model.addeconomics.AddOnPaybackPeriod.PreferredUnits.value + NL)
                    addon_results.append(OutputTableItem('AddOns Payback Period', '{0:10.2f}'.format(model.addeconomics.AddOnPaybackPeriod.value), model.addeconomics.AddOnPaybackPeriod.PreferredUnits.value))

                    ae = model.addeconomics

                    # Build the data frame to hold the SDAC result profile
                    addon_df = pd.DataFrame()
                    # add the columns as needed based on the output.
                    # Note that the correct format for that column is stashed in the title of that column
                    # so that it can be used in the write statement.
                    addon_df[f'Year|:2.0f'] = [i for i in range(1, (model.surfaceplant.plant_lifetime.value + 1))]
                    addon_df[f'Electricity:Price ({ae.ElecPrice.PreferredUnits.value})|:10.2f'] = ae.ElecPrice.value
                    addon_df[f'Electricity:Revenue ({ae.AddOnElecRevenue.PreferredUnits.value})|:10.2f'] = ae.AddOnElecRevenue.value
                    addon_df[f'Heat:Price ({ae.HeatPrice.PreferredUnits.value})|:10.2f'] = ae.HeatPrice.value
                    addon_df[f'Heat:Revenue ({ae.AddOnHeatRevenue.PreferredUnits.value})|:10.2f'] = ae.AddOnHeatRevenue.value
                    addon_df[f'Add-on:Revenue ({ae.AddOnRevenue.PreferredUnits.value})|:10.2f'] = ae.AddOnRevenue.value
                    addon_df[f'Add-on:Cash Flow ({ae.AddOnCashFlow.PreferredUnits.value})|:10.2f'] = ae.AddOnCashFlow.value[0:len(ae.AddOnCashFlow.value) - 1]
                    addon_df[f'Add-on:Cumulative Cash Flow ({ae.AddOnCummCashFlow.PreferredUnits.value})|:10.2f'] = ae.AddOnCummCashFlow.value[0:len(ae.AddOnCummCashFlow.value) - 1]
                    addon_df[f'Project:Cash Flow ({ae.ProjectCashFlow.PreferredUnits.value})|:10.2f'] = ae.ProjectCashFlow.value[0:len(ae.ProjectCashFlow.value) - 1]
                    addon_df[f'Project:Cumulative Cash Flow ({ae.ProjectCummCashFlow.PreferredUnits.value})|:10.2f'] = ae.ProjectCummCashFlow.value[0:len(ae.ProjectCummCashFlow.value) - 1]

                    f.write(NL)
                    f.write(NL)
                    f.write("                             *******************************" + NL)
                    f.write("                             *  EXTENDED ECONOMIC PROFILE  *" + NL)
                    f.write("                             *******************************" + NL)
                    f.write(
                        "Year        Electricity             Heat             Add-on  Annual AddOn Cumm. AddOn  Annual Project Cumm. Project" + NL)
                    f.write(
                        "Since     Price   Revenue      Price   Revenue      Revenue   Cash Flow    Cash Flow    Cash Flow       Cash Flow" + NL)

                    f.write("Start    ("
                            + ae.ElecPrice.PreferredUnits.value +
                            ")(" + ae.AddOnElecRevenue.PreferredUnits.value +
                            ") (" + ae.HeatPrice.PreferredUnits.value +
                            ")(" + ae.AddOnHeatRevenue.PreferredUnits.value +
                            ") (" + ae.AddOnRevenue.PreferredUnits.value +
                            ")    (" + ae.AddOnCashFlow.PreferredUnits.value +
                            ")  (" + ae.AddOnCummCashFlow.PreferredUnits.value +
                            ")       (" + ae.ProjectCashFlow.PreferredUnits.value +
                            ")        (" + ae.ProjectCummCashFlow.PreferredUnits.value + ")\n")
                    # running years...
                    for ii in range(0, (
                        model.surfaceplant.construction_years.value + model.surfaceplant.plant_lifetime.value - 1), 1):
                        f.write(
                            f"   {ii + 1:3.0f}    {model.economics.ElecPrice.value[ii]:5.3f}   {model.addeconomics.AddOnElecRevenue.value[ii]:5.4f}        {model.economics.HeatPrice.value[ii]:5.3f}   {model.addeconomics.AddOnHeatRevenue.value[ii]:5.4f}        {model.addeconomics.AddOnRevenue.value[ii]:5.2f}        {model.addeconomics.AddOnCashFlow.value[ii]:5.2f}     {model.addeconomics.AddOnCummCashFlow.value[ii]:5.2f}        {model.addeconomics.ProjectCashFlow.value[ii]:5.2f}           {model.addeconomics.ProjectCummCashFlow.value[ii]:5.2f}\n")

        except BaseException as ex:
            tb = sys.exc_info()[2]
            print(str(ex))
            err_msg = "Error: GEOPHIRES failed to Failed to write the output file.  Exiting....Line %i" % tb.tb_lineno
            print(err_msg)
            model.logger.critical(str(ex))
            model.logger.critical(err_msg)
            sys.exit()

        model.logger.info(f'Complete {str(__class__)}: {__name__}')

        addon_df = addon_df.reset_index()
        return addon_df, addon_results

import sys
from geophires_x.Outputs import Outputs

NL = "\n"


class OutputsAddOns(Outputs):
    """
    Class to handle output of the AddOns values
    """

    def PrintOutputs(self, model):

        """
        The PrintOutputs function prints the results of the AddOns to a text file and to the screen.
        :param model: Model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        model.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')

        # now do AddOn output, which will append to the original output
        # write results to output file and screen
        try:
            with open(self.output_file, 'a', encoding='UTF-8') as f:
                f.write(NL)
                f.write(NL)
                f.write("                                ***EXTENDED ECONOMICS***\n")
                f.write(NL)
                if model.economics.LCOE.value > -999.0:
                    f.write(
                        f"      Adjusted Project LCOE (after incentives, grants, AddOns,etc):     {model.economics.LCOE.value:10.2f} " + model.economics.LCOE.PreferredUnits.value + NL)
                if model.economics.LCOH.value > -999.0:
                    f.write(
                        f"      Adjusted Project LCOH (after incentives, grants, AddOns,etc):     {model.economics.LCOH.value:10.2f} " + model.economics.LCOH.PreferredUnits.value + NL)
                f.write(
                    f"      Adjusted Project CAPEX (after incentives, grants, AddOns, etc):   {model.addeconomics.AdjustedProjectCAPEX.value:10.2f} " + model.addeconomics.AdjustedProjectCAPEX.PreferredUnits.value + NL)
                f.write(
                    f"      Adjusted Project OPEX (after incentives, grants, AddOns, etc):    {model.addeconomics.AdjustedProjectOPEX.value:10.2f} " + model.addeconomics.AdjustedProjectOPEX.PreferredUnits.value + NL)
                f.write(
                    f"      Project NPV   (including AddOns):                                 {model.addeconomics.ProjectNPV.value:10.2f} " + model.addeconomics.ProjectNPV.PreferredUnits.value + NL)
                f.write(
                    f"      Project IRR   (including AddOns):                                 {model.addeconomics.ProjectIRR.value:10.2f} " + model.addeconomics.ProjectIRR.PreferredUnits.value + NL)
                f.write(
                    f"      Project VIR=PI=PIR   (including AddOns):                          {model.addeconomics.ProjectVIR.value:10.2f}" + NL)
                f.write(
                    f"      Project MOIC  (including AddOns):                                 {model.addeconomics.ProjectMOIC.value:10.2f}" + NL)
                if model.addeconomics.AddOnCAPEXTotal.value + model.addeconomics.AddOnOPEXTotalPerYear.value != 0:
                    f.write(
                        f"      Total Add-on CAPEX:                                               {model.addeconomics.AddOnCAPEXTotal.value:10.2f} " + model.addeconomics.AddOnCAPEXTotal.PreferredUnits.value + NL)
                    f.write(
                        f"      Total Add-on OPEX:                                                {model.addeconomics.AddOnOPEXTotalPerYear.value:10.2f} " + model.addeconomics.AddOnOPEXTotalPerYear.PreferredUnits.value + NL)
                    f.write(
                        f"      Total Add-on Net Elec:                                            {model.addeconomics.AddOnElecGainedTotalPerYear.value:10.2f} " + model.addeconomics.AddOnElecGainedTotalPerYear.PreferredUnits.value + NL)
                    f.write(
                        f"      Total Add-on Net Heat:                                            {model.addeconomics.AddOnHeatGainedTotalPerYear.value:10.2f} " + model.addeconomics.AddOnHeatGainedTotalPerYear.PreferredUnits.value + NL)
                    f.write(
                        f"      Total Add-on Profit:                                              {model.addeconomics.AddOnProfitGainedTotalPerYear.value:10.2f} " + model.addeconomics.AddOnProfitGainedTotalPerYear.PreferredUnits.value + NL)
                    f.write(
                        f"      AddOns Payback Period:                                            {model.addeconomics.AddOnPaybackPeriod.value:10.2f} " + model.addeconomics.AddOnPaybackPeriod.PreferredUnits.value + NL)
                    f.write(NL)
                    f.write(NL)
                    f.write("                             *******************************" + NL)
                    f.write("                             *  EXTENDED ECONOMIC PROFILE  *" + NL)
                    f.write("                             *******************************" + NL)
                    f.write(
                        "Year        Electricity             Heat             Add-on  Annual AddOn Cumm. AddOn  Annual Project Cumm. Project" + NL)
                    f.write(
                        "Since     Price   Revenue      Price   Revenue      Revenue   Cash Flow    Cash Flow    Cash Flow       Cash Flow" + NL)

                    ae = model.addeconomics
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

        model.logger.info(f'Complete {str(__class__)}: {sys._getframe().f_code.co_name}')

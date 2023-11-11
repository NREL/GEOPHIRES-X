import sys
from geophires_x.Outputs import Outputs
from geophires_x.Model import Model

NL = "\n"


class OutputsAddOns(Outputs):
    """
    Class to handles output of the AddOns values
    """
    def PrintOutputs(self, model: Model):
        """
        The PrintOutputs function prints the results of the AddOns to a text file and to the screen.
        :param model: Model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        # now do AddOn output, which will append to the original output
        # write results to output file and screen
        try:
            outputfile = "HDR.out"
            if len(sys.argv) > 2:
                outputfile = sys.argv[2]
            with open(outputfile, 'a', encoding='UTF-8') as f:
                f.write(NL)
                f.write(NL)
                f.write("                                ***EXTENDED ECONOMICS***" + NL)
                f.write(NL)
                if model.economics.LCOE.value > -999.0:
                    f.write(f"      Adjusted Project LCOE (after incentives, grants, AddOns,etc):     {model.economics.LCOE.value:10.2f} " + model.economics.LCOE.PreferredUnits.value + NL)
                if model.economics.LCOH.value > -999.0:
                    f.write(f"      Adjusted Project LCOH (after incentives, grants, AddOns,etc):     {model.economics.LCOH.value:10.2f} " + model.economics.LCOH.PreferredUnits.value + NL)
                f.write(f"      Adjusted Project CAPEX (after incentives, grants, AddOns, etc):   {model.addeconomics.AdjustedProjectCAPEX.value:10.2f} " + model.addeconomics.AdjustedProjectCAPEX.PreferredUnits.value + NL)
                f.write(f"      Adjusted Project OPEX (after incentives, grants, AddOns, etc):    {model.addeconomics.AdjustedProjectOPEX.value:10.2f} " + model.addeconomics.AdjustedProjectOPEX.PreferredUnits.value + NL)
                f.write(f"      Project NPV   (including AddOns):                                 {model.addeconomics.ProjectNPV.value:10.2f} " + model.addeconomics.ProjectNPV.PreferredUnits.value + NL)
                f.write(f"      Project IRR   (including AddOns):                                 {model.addeconomics.ProjectIRR.value:10.2f} " + model.addeconomics.ProjectIRR.PreferredUnits.value + NL)
                f.write(f"      Project VIR=PI=PIR   (including AddOns):                          {model.addeconomics.ProjectVIR.value:10.2f}" + NL)
                f.write(f"      Project MOIC  (including AddOns):                                 {model.addeconomics.ProjectMOIC.value:10.2f}" + NL)
                f.write(f"      Project Payback Period       (including AddOns):                  {model.addeconomics.ProjectPaybackPeriod.value:10.2f} " + model.addeconomics.ProjectPaybackPeriod.PreferredUnits.value + NL)
                if model.addeconomics.AddOnCAPEXTotal.value + model.addeconomics.AddOnOPEXTotalPerYear.value != 0:
                    f.write(f"      Total Add-on CAPEX:                                               {model.addeconomics.AddOnCAPEXTotal.value:10.2f} " + model.addeconomics.AddOnCAPEXTotal.PreferredUnits.value + NL)
                    f.write(f"      Total Add-on OPEX:                                                {model.addeconomics.AddOnOPEXTotalPerYear.value:10.2f} " + model.addeconomics.AddOnOPEXTotalPerYear.PreferredUnits.value + NL)
                    f.write(f"      Total Add-on Net Elec:                                            {model.addeconomics.AddOnElecGainedTotalPerYear.value:10.2f} " + model.addeconomics.AddOnElecGainedTotalPerYear.PreferredUnits.value + NL)
                    f.write(f"      Total Add-on Net Heat:                                            {model.addeconomics.AddOnHeatGainedTotalPerYear.value:10.2f} " + model.addeconomics.AddOnHeatGainedTotalPerYear.PreferredUnits.value + NL)
                    f.write(f"      Total Add-on Profit:                                              {model.addeconomics.AddOnProfitGainedTotalPerYear.value:10.2f} " + model.addeconomics.AddOnProfitGainedTotalPerYear.PreferredUnits.value + NL)
                    f.write(f"      AddOns Payback Period:                                            {model.addeconomics.AddOnPaybackPeriod.value:10.2f} " + model.addeconomics.AddOnPaybackPeriod.PreferredUnits.value + NL)
                    f.write(NL)
                    f.write(NL)
                    f.write("                             *******************************" + NL)
                    f.write("                             *  EXTENDED ECONOMIC PROFILE  *" + NL)
                    f.write("                             *******************************" + NL)
                    f.write("Year        Electricity             Heat             Add-on  Annual AddOn Cumm. AddOn  Annual Project Cumm. Project" + NL)
                    f.write("Since     Price   Revenue      Price   Revenue      Revenue   Cash Flow    Cash Flow    Cash Flow       Cash Flow" + NL)
                    f.write("Start    ("
                                        + model.addeconomics.ElecPrice.PreferredUnits.value +
                                         ")(" + model.addeconomics.AddOnElecRevenue.PreferredUnits.value +
                                                   ") (" + model.addeconomics.HeatPrice.PreferredUnits.value +
                                                                ")(" + model.addeconomics.AddOnHeatRevenue.PreferredUnits.value +
                                                                         ") (" + model.addeconomics.AddOnRevenue.PreferredUnits.value +
                                                                                ")    (" + model.addeconomics.AddOnCashFlow.PreferredUnits.value +
                                                                                        ")  (" + model.addeconomics.AddOnCummCashFlow.PreferredUnits.value +
                                                                                ")       (" + model.addeconomics.ProjectCashFlow.PreferredUnits.value +
                                                                                        ")        (" + model.addeconomics.ProjectCummCashFlow.PreferredUnits.value+")" + NL)
                    i = 0
                    for i in range(0, model.surfaceplant.ConstructionYears.value, 1):
                        # construction years...
                        f.write(f"   {i+1:3.0f}                                                            {model.addeconomics.AddOnCashFlow.value[i]:5.2f}     {model.addeconomics.AddOnCummCashFlow.value[i]:5.2f}      {model.addeconomics.ProjectCashFlow.value[i]:5.2f}           {model.addeconomics.ProjectCummCashFlow.value[i]:5.2f}" + NL)
                        i = i + 1
                    ii = 0
                    for ii in range(0, (model.surfaceplant.ConstructionYears.value + model.surfaceplant.plantlifetime.value - 1), 1):
                        # running years...
                        f.write(f"   {i+1:3.0f}    {model.economics.ElecPrice.value[ii]:5.3f}   {model.addeconomics.AddOnElecRevenue.value[ii]:5.4f}        {model.economics.HeatPrice.value[ii]:5.3f}   {model.addeconomics.AddOnHeatRevenue.value[ii]:5.4f}        {model.addeconomics.AddOnRevenue.value[ii]:5.2f}        {model.addeconomics.AddOnCashFlow.value[ii]:5.2f}     {model.addeconomics.AddOnCummCashFlow.value[ii]:5.2f}        {model.addeconomics.ProjectCashFlow.value[ii]:5.2f}           {model.addeconomics.ProjectCummCashFlow.value[ii]:5.2f}" + NL)
                        ii = ii + 1

        except BaseException as ex:
            tb = sys.exc_info()[2]
            print(str(ex))
            print("Error: GEOPHIRES failed to Failed to write the output file.  Exiting....Line %i" % tb.tb_lineno)
            model.logger.critical(str(ex))
            model.logger.critical("Error: GEOPHIRES failed to Failed to write the output file.  Exiting....Line %i" % tb.tb_lineno)
            sys.exit()

        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

import sys
from geophires_x.Outputs import Outputs
import numpy as np

NL = "\n"


class OutputsCCUS(Outputs):
    """
    Class to handles output of the CCUS values
    """
    def PrintOutputs(self, model):
        """
        The PrintOutputs function prints the results of the CCUS to a text file and to the screen.
        :param model: Model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: Nothing
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        if np.sum(model.ccuseconomics.CCUSRevenue.value) == 0:
            return   # don't bother if we have nothing to report.

        # now do CCUS output, which will append to the original output
        # write results to output file and screen
        try:
            with open(self.output_file, 'a', encoding='UTF-8') as f:
                f.write(NL)
                f.write(NL)
                f.write("                                ***CCUS ECONOMICS***" + NL)
                f.write(NL)
                f.write(NL)
                f.write(f"      Total Avoided Carbon Production:                       {model.ccuseconomics.CarbonThatWouldHaveBeenProducedTotal.value:10.2f} " + model.ccuseconomics.CarbonThatWouldHaveBeenProducedTotal.PreferredUnits.value + NL)
                f.write(f"      Project NPV            (including carbon credit):      {model.ccuseconomics.ProjectNPV.value:10.2f} " + model.ccuseconomics.ProjectNPV.PreferredUnits.value + NL)
                f.write(f"      Project IRR            (including carbon credit):      {model.ccuseconomics.ProjectIRR.value:10.2f} " + model.ccuseconomics.ProjectIRR.PreferredUnits.value + NL)
                f.write(f"      Project VIR=IR=PIR     (including carbon credit):      {model.ccuseconomics.ProjectVIR.value:10.2f}" + NL)
                f.write(f"      Project MOIC           (including carbon credit):      {model.ccuseconomics.ProjectMOIC.value:10.2f}" + NL)
                f.write(NL)
                f.write(NL)
                f.write("                    ******************" + NL)
                f.write("                    *  CCUS PROFILE  *" + NL)
                f.write("                    ******************" + NL)
                f.write("Year       Carbon          CCUS               CCUS Annual   CCUS Cumm.  Project Annual   Project Cumm." + NL)
                f.write("Since      Avoided    Price   Revenue          Cash Flow    Cash Flow      Cash Flow       Cash Flow" + NL)
                f.write("Start      ("+model.ccuseconomics.CarbonThatWouldHaveBeenProducedAnnually.PreferredUnits.value +
                                             ")   ("+model.ccuseconomics.CCUSPrice.PreferredUnits.value +
                                             ") ("+model.ccuseconomics.CCUSRevenue.PreferredUnits.value +
                                             ")        ("+model.ccuseconomics.CCUSCashFlow.PreferredUnits.value +
                                             ")    ("+model.ccuseconomics.CCUSCummCashFlow.PreferredUnits.value +
                                             ")         ("+model.ccuseconomics.ProjectCashFlow.PreferredUnits.value +
                                             ")        ("+model.ccuseconomics.ProjectCummCashFlow.PreferredUnits.value + ")" + NL)
                i = 0
                for i in range(0, model.surfaceplant.construction_years.value, 1):
                    # construction years...
                    f.write(f"   {i+1:3.0f}                                                                     {model.ccuseconomics.ProjectCashFlow.value[i]:5.2f}           {model.ccuseconomics.ProjectCummCashFlow.value[i]:5.2f}" + NL)
                    i = i + 1

                ii = 0
                for ii in range(0, model.surfaceplant.plant_lifetime.value, 1):
                    # running years...
                    f.write(f"   {ii+1+model.surfaceplant.construction_years.value:3.0f}  {model.ccuseconomics.CarbonThatWouldHaveBeenProducedAnnually.value[ii]:5.3f}  {model.ccuseconomics.CCUSPrice.value[ii]:5.3f}   {model.ccuseconomics.CCUSRevenue.value[ii]:5.2f}             {model.ccuseconomics.CCUSCashFlow.value[ii]:5.2f}        {model.ccuseconomics.CCUSCummCashFlow.value[ii]:5.2f}          {model.ccuseconomics.ProjectCashFlow.value[ii + model.surfaceplant.construction_years.value]:5.2f}           {model.ccuseconomics.ProjectCummCashFlow.value[ii + model.surfaceplant.construction_years.value]:5.2f}" + NL)
                    ii = ii + 1

        except BaseException as ex:
            tb = sys.exc_info()[2]
            print(str(ex))
            print("Error: GEOPHIRES failed to Failed to write the output file.  Exiting....Line %i" % tb.tb_lineno)
            model.logger.critical(str(ex))
            model.logger.critical("Error: GEOPHIRES failed to Failed to write the output file.  Exiting....Line %i" % tb.tb_lineno)
            sys.exit()

        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

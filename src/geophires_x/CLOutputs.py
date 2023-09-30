import sys
from geophires_x.Outputs import Outputs
from geophires_x.Model import Model

NL = "\n"


class CLOutputs(Outputs):
    """description of class"""
    def PrintOutputs(self, model: Model):
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        # now do CL output, which will append to the original output
        # ---------------------------------------
        # write results to output file and screen
        # ---------------------------------------
        try:
            outputfile = "HDR.out"
            if len(sys.argv) > 2:
                outputfile = sys.argv[2]
            with open(outputfile, 'a', encoding='UTF-8') as f:
                f.write(NL)
                f.write(NL)
                f.write("                                ***CLOSED-LOOP ECONOMICS***" + NL)
                f.write(NL)
                f.write(NL)
                f.write(f"      Cost per horizontal section:      {model.economics.C1well.value:10.2f} " +
                        model.economics.C1well.PreferredUnits.value + NL)
                f.write(f"      Total Cost of horizontal section: {model.economics.CHorizwell.value:10.2f} " +
                        model.economics.CHorizwell.PreferredUnits.value + NL)
                f.write(NL)
                f.write(NL)
                f.write("                    ********************************************************" + NL)
                f.write("                    *  CLOSED-LOOP PER LATERAL PERFORMANCE PROFILE         *" + NL)
                f.write("                    *      (EACH SEGMENT ASSUMED TO BE EQUIVALENT          *" + NL)
                f.write("                    *  AND PLACED FAR ENOUGH APART SO AS TO NOT INTERFERE) *" + NL)
                f.write("                    ********************************************************" + NL)
                f.write("Year       Horiz Section         Horiz Pressure" + NL)
                f.write("Since      Output Temperature    Drop" + NL)
                f.write("Start      ("+model.wellbores.HorizontalProducedTemperature.PreferredUnits.value+")" +
                        "                ("+model.wellbores.HorizontalPressureDrop.PreferredUnits.value + ")" + NL)
                i = 0
                ii = 0
                for i in range(0, len(model.wellbores.HorizontalProducedTemperature.value), 1):
                    # construction years...
                    f.write(f"   {i+1:3.0f}     {model.wellbores.HorizontalProducedTemperature.value[i]:5.2f}                {model.wellbores.HorizontalPressureDrop.value[i]:5.2f}" + NL)
                    i = i + 1
                    ii = ii + model.economics.timestepsperyear.value

        except BaseException as ex:
            tb = sys.exc_info()[2]
            print(str(ex))
            print("Error: GEOPHIRES Failed to write the output file.  Exiting....Line %i" % tb.tb_lineno)
            model.logger.critical(str(ex))
            model.logger.critical("Error: GEOPHIRES Failed to write the output file.  Exiting....Line %i" % tb.tb_lineno)
            sys.exit()

        model.logger.info("Complete " + str(__class__) + ": " + sys._getframe().f_code.co_name)

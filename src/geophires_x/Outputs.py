import datetime
import time
import sys
import numpy as np
import geophires_x.Model as Model
from .Parameter import ConvertUnitsBack, ConvertOutputUnits, LookupUnits
from .OptionList import EndUseOptions, EconomicModel, ReservoirModel, FractureShape, ReservoirVolume
from matplotlib import pyplot as plt
from .Units import *

NL="\n"

class Outputs:
    def __init__(self, model:Model):
        """
        The __init__ function is called automatically when a class is instantiated.
        It initializes the attributes of an object, and sets default values for certain arguments that can be
        overridden by user input.
        The __init__ function is used to set up all the parameters in the Outputs.
        :param self: Store data that will be used by the class
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: None
        :doc-author: Malcolm Ross
        """

        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        # Dictionary to hold the Units definitions that the user wants for outputs created by GEOPHIRES.
        # It is empty by default initially - this will expand as the user desires are read from the input file
        self.ParameterDict = {}
        self.printoutput = True

        model.logger.info("Complete "+ str(__class__) + ": " + sys._getframe().f_code.co_name)

    def __str__(self):
        return "Outputs"

    def read_parameters(self, model:Model) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary and stores them in the parameters.
        It also handles special cases that need to be handled after a value has been read in and checked.
        If you choose to subclass this master class, you can also choose to override this method (or not), and if you do
        :param self: Access variables that belong to a class
        :param model: The container class of the application, giving access to everything else, including the logger
        :return: None
        :doc-author: Malcolm Ross
        #Deal with all the parameter values that the user has provided.  They should really only provide values that
        they want to change from the default values, but they can provide a value that is already set because it is a
        default value set in __init__.  It will ignore those.
        #This also deals with all the special cases that need to be taken care of after a value has been read in
        and checked.
        #If you choose to subclass this master class, you can also choose to override this method (or not),
        and if you do, do it before or after you call you own version of this method.  If you do, you can also choose
        to call this method from you class, which can effectively modify all these superclass parameters in your class.
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        if len(model.InputParameters) > 0:
            # if the user wants it, we need to know if the user wants to copy the contents of the
            # output file to the screen - this serves as the screen report
            if "Print Output to Console" in model.InputParameters:
                ParameterReadIn = model.InputParameters["Print Output to Console"]
                if ParameterReadIn.sValue == "0":
                    self.printoutput = False

            # loop through all the parameters that the user wishes to set, looking for parameters that contain the
            # prefix "Units:" - that means we want to set a special case for converting this
            # output parameter to new units
            for key in model.InputParameters.keys():
                if key.startswith("Units:"):
                    self.ParameterDict[key.replace("Units:", "")] = LookupUnits(model.InputParameters[key].sValue)[0]

                    # handle special cases

        model.logger.info("Complete "+ str(__class__) + ": " + sys._getframe().f_code.co_name)

    def PrintOutputs(self, model:Model):
        """
        PrintOutputs writes the standard outputs to the output file.
        Args:
            model (Model): The container class of the application, giving access to everything else, including the logger
        """
        model.logger.info("Init " + str(__class__) + ": " + sys._getframe().f_code.co_name)

        # Deal with converting Units back to PreferredUnits, if required.
        # before we write the outputs, we go thru all the parameters for all of the objects and set the values back
        # to the units that the user entered the data in
        # We do this because the value may be displayed in the output, and we want the user to recginze their value,
        # not some converted value
        for obj in [model.reserv, model.wellbores, model.surfaceplant, model.economics]:
            for key in obj.ParameterDict:
                param = obj.ParameterDict[key]
                if not param.UnitsMatch: ConvertUnitsBack(param, model)

        # now we need to loop through all thw output parameters to update their units to
        # whatever units the user has specified.
        # i.e., they may have specified that all LENGTH results must be in feet, so we need to convert those
        # from whatever LENGTH unit they are to feet.
        # same for all the other classes of units (TEMPERATURE, DENSITY, etc).

        for obj in [model.reserv, model.wellbores, model.surfaceplant, model.economics]:
            for key in obj.OutputParameterDict:
                if key in self.ParameterDict:
                    if self.ParameterDict[key] != obj.OutputParameterDict[key].CurrentUnits:
                        ConvertOutputUnits(obj.OutputParameterDict[key], self.ParameterDict[key], model)

        # write results to output file and screen

        try:
            outputfile = "HDR.out"
            if len(sys.argv) > 2: outputfile = sys.argv[2]
            with open(outputfile,'w', encoding='UTF-8') as f:
                f.write('                               *****************\n')
                f.write('                               ***CASE REPORT***\n')
                f.write('                               *****************\n')
                f.write(NL)
                f.write("Simulation Metadata\n")
                f.write("----------------------\n")
                f.write(" GEOPHIRES Version: 3.0\n")
                f.write(" GEOPHIRES Build Date: 2022-06-30\n")
                f.write(" Simulation Date: "+ datetime.datetime.now().strftime("%Y-%m-%d\n"))
                f.write(" Simulation Time:  "+ datetime.datetime.now().strftime("%H:%M\n"))
                f.write(" Calculation Time: "+"{0:10.3f}".format((time.time()-model.tic)) + " sec\n")

                f.write(NL)
                f.write('                           ***SUMMARY OF RESULTS***\n')
                f.write(NL)
                f.write("      End-Use Option: " + str(model.surfaceplant.enduseoption.value.value) + NL)
                if model.surfaceplant.enduseoption.value == EndUseOptions.DISTRICT_HEATING:
                    f.write(f"      Annual District Heating Demand:                   {np.average(model.surfaceplant.annualheatingdemand.value):10.2f} "+ model.surfaceplant.annualheatingdemand.CurrentUnits.value + NL)
                    f.write(f"      Average Annual Geothermal Heat Production:        {sum(model.surfaceplant.dhgeothermalheating.value*24)/model.surfaceplant.plantlifetime.value/1e3:10.2f} "+ model.surfaceplant.annualheatingdemand.CurrentUnits.value + NL)
                    f.write(f"      Average Annual Peaking Fuel Heat Production:      {sum(model.surfaceplant.dhnaturalgasheating.value*24)/model.surfaceplant.plantlifetime.value/1e3:10.2f} "+ model.surfaceplant.annualheatingdemand.CurrentUnits.value + NL)

                if model.surfaceplant.enduseoption.value in [EndUseOptions.ELECTRICITY, EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT, EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICTY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICTY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICTY]: #there is an electricity componenent
                    f.write(f"      Average Net Electricity Production:               {np.average(model.surfaceplant.NetElectricityProduced.value):10.2f} " + model.surfaceplant.NetElectricityProduced.CurrentUnits.value + NL)
                if model.surfaceplant.enduseoption.value != EndUseOptions.ELECTRICITY:    # there is a direct-use component
                    f.write(f"      Average Direct-Use Heat Production:               {np.average(model.surfaceplant.HeatProduced.value):10.2f} "+ model.surfaceplant.HeatProduced.CurrentUnits.value + NL)

                if model.surfaceplant.enduseoption.value == EndUseOptions.ABSORPTION_CHILLER:
                    f.write(f"      Average Cooling Production:                       {np.average(model.surfaceplant.CoolingProduced.value):10.2f} "+ model.surfaceplant.CoolingProduced.CurrentUnits.value + NL)

                if model.surfaceplant.enduseoption.value in [EndUseOptions.ELECTRICITY, EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,  EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT]:    #levelized cost expressed as LCOE
                    f.write(f"      Electricity breakeven price:                      {model.economics.LCOE.value:10.2f} " + model.economics.LCOE.CurrentUnits.value + NL)
                elif model.surfaceplant.enduseoption.value in [EndUseOptions.HEAT, EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICTY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICTY,  EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICTY, EndUseOptions.HEAT_PUMP,EndUseOptions.DISTRICT_HEATING]:    #levelized cost expressed as LCOH
                    f.write(f"      Direct-Use heat breakeven price:                  {model.economics.LCOH.value:10.2f} " + model.economics.LCOH.CurrentUnits.value + NL)

                elif model.surfaceplant.enduseoption.value == EndUseOptions.ABSORPTION_CHILLER:
                    f.write(f"      Direct-Use Cooling Breakeven Price:               {model.economics.LCOC.value:10.2f} " + model.economics.LCOC.CurrentUnits.value + NL)

                f.write(f"      Number of production wells:                    {model.wellbores.nprod.value:10.0f}"+NL)
                f.write(f"      Number of injection wells:                     {model.wellbores.ninj.value:10.0f}"+NL)
                f.write(f"      Flowrate per production well:                    {model.wellbores.prodwellflowrate.value:10.1f} "  + model.wellbores.prodwellflowrate.CurrentUnits.value + NL)
                f.write(f"      Well depth (or total length, if not vertical):   {model.reserv.depth.value:10.1f} " +model.reserv.depth.CurrentUnits.value + NL)

                if model.reserv.numseg.value == 1:
                    f.write(f"      Geothermal gradient:                                {model.reserv.gradient.value[0]:10.4f} " + model.reserv.gradient.CurrentUnits.value + NL)
                else:
                    for i in range(1, model.reserv.numseg.value):
                        f.write(f"      Segment {str(i):s}   Geothermal gradient:                      {model.reserv.gradient.value[i-1]:10.4f} " + model.reserv.gradient.CurrentUnits.value +NL)
                        f.write(f"      Segment {str(i):s}   Thickness (km):                           {model.reserv.layerthickness.value[i-1]:10.0f} " + model.reserv.layerthickness.CurrentUnits.value + NL)
                        f.write(f"      Segment {str(i+1):s} Geothermal gradient:                      {model.reserv.gradient.value[i]:10.4f} " + model.reserv.gradient.CurrentUnits.value + NL)

                f.write(NL)
                f.write(NL)
                f.write('                           ***ECONOMIC PARAMETERS***\n')
                f.write(NL)
                if model.economics.econmodel.value == EconomicModel.FCR:
                    f.write("      Economic Model = " + model.economics.econmodel.value.value + NL)
                    f.write(f"      Fixed Charge Rate (FCR):                          {model.economics.FCR.value*100.0:10.2f} " + model.economics.FCR.CurrentUnits.value + NL)
                elif model.economics.econmodel.value == EconomicModel.STANDARDIZED_LEVELIZED_COST:
                    f.write("      Economic Model = " + model.economics.econmodel.value.value + NL)
                    f.write(f"      Interest Rate:                                    {model.economics.discountrate.value*100.0:10.2f} " + model.economics.discountrate.CurrentUnits.value + NL)
                elif model.economics.econmodel.value == EconomicModel.BICYCLE:
                    f.write("      Economic Model  = " + model.economics.econmodel.value.value + NL)
                f.write(f"      Accrued financing during construction:            {model.economics.inflrateconstruction.value*100:10.2f} " + model.economics.inflrateconstruction.CurrentUnits.value + NL)
                f.write(f"      Project lifetime:                              {model.surfaceplant.plantlifetime.value:10.0f} " + model.surfaceplant.plantlifetime.CurrentUnits.value + NL)
                f.write(f"      Capacity factor:                                 {model.surfaceplant.utilfactor.value*100:10.1f} %" + NL)
                f.write(f"      Project NPV:                                     {model.economics.ProjectNPV.value:10.2f} " + model.economics.ProjectNPV.PreferredUnits.value + NL)
                f.write(f"      Project IRR:                                     {model.economics.ProjectIRR.value:10.2f} " + model.economics.ProjectIRR.PreferredUnits.value + NL)
                f.write(f"      Project VIR=PI=PIR:                              {model.economics.ProjectVIR.value:10.2f}" + NL)
                f.write(f"      Project MOIC:                                    {model.economics.ProjectMOIC.value:10.2f}" + NL)

                f.write(NL)
                f.write('                          ***ENGINEERING PARAMETERS***\n')
                f.write(NL)
                f.write(f"      Number of Production Wells:                    {model.wellbores.nprod.value:10.0f}" + NL)
                f.write(f"      Number of Injection Wells:                     {model.wellbores.ninj.value:10.0f}" + NL)
                f.write(f"      Well depth (or total length, if not vertical):   {model.reserv.depth.value:10.1f} " + model.reserv.depth.CurrentUnits.value + NL)
                f.write(f"      Water loss rate:                                 {model.reserv.waterloss.value*100:10.1f} " + model.reserv.waterloss.CurrentUnits.value + NL)
                f.write(f"      Pump efficiency:                                 {model.surfaceplant.pumpeff.value*100:10.1f} " + model.surfaceplant.pumpeff.CurrentUnits.value + NL)
                f.write(f"      Injection temperature:                           {model.wellbores.Tinj.value:10.1f} " + model.wellbores.Tinj.CurrentUnits.value + NL)
                if model.wellbores.rameyoptionprod.value:
                    f.write("      Production Wellbore heat transmission calculated with Ramey's model\n")
                    f.write(f"      Average production well temperature drop:        {np.average(model.wellbores.ProdTempDrop.value):10.1f} " + model.wellbores.ProdTempDrop.PreferredUnits.value + NL)
                else:
                    f.write("      User-provided production well temperature drop\n")
                    f.write(f"      Constant production well temperature drop:       {model.wellbores.tempdropprod.value:10.1f} " + model.wellbores.tempdropprod.PreferredUnits.value + NL)
                f.write(f"      Flowrate per production well:                    {model.wellbores.prodwellflowrate.value:10.1f} " + model.wellbores.prodwellflowrate.CurrentUnits.value + NL)
                f.write(f"      Injection well casing ID:                          {model.wellbores.injwelldiam.value:10.3f} " + model.wellbores.injwelldiam.CurrentUnits.value + NL)
                f.write(f"      Production well casing ID:                         {model.wellbores.prodwelldiam.value:10.3f} " + model.wellbores.prodwelldiam.CurrentUnits.value + NL)
                f.write(f"      Number of times redrilling:                    {model.wellbores.redrill.value:10.0f}"+NL)
                if model.surfaceplant.enduseoption.value in [EndUseOptions.ELECTRICITY, EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT, EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICTY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICTY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICTY]:
                    f.write("      Power plant type:                                       " +  str(model.surfaceplant.pptype.value.value) + NL)
                f.write(NL)
                f.write(NL)
                f.write('                         ***RESOURCE CHARACTERISTICS***\n')
                f.write(NL)
                f.write(f"      Maximum reservoir temperature:                   {model.reserv.Tmax.value:10.1f} " + model.reserv.Tmax.CurrentUnits.value + NL)
                f.write(f"      Number of segments:                            {model.reserv.numseg.value:10.0f} " + NL)
                if model.reserv.numseg.value == 1:
                    f.write(f"      Geothermal gradient:                                {model.reserv.gradient.value[0]:10.4f} " + model.reserv.gradient.CurrentUnits.value + NL)
                else:
                    for i in range(1, model.reserv.numseg.value):
                        f.write(f"      Segment " + str(i) + " geothermal gradient:                   {model.reserv.gradient.value[i-1]:10.4f} " + model.reserv.gradient.CurrentUnits.value + NL)
                        f.write(f"      Segment " + str(i) + " thickness:                           {model.reserv.layerthickness.value[i-1]:10.0f} " + model.reserv.layerthickness.CurrentUnits.value + NL)
                        f.write(f"      Segment " + str(i+1) + " geothermal gradient:                   {model.reserv.gradient.value[i]:10.4f} " + model.reserv.gradient.CurrentUnits.value + NL)

                f.write(NL)
                f.write(NL)
                f.write('                           ***RESERVOIR PARAMETERS***\n')
                f.write(NL)
                if model.wellbores.IsAGS.value:
                    f.write("The AGS models contain an intrinsic reservoir model that doesn't expose values that can be used in extensive reporting." + NL)
                else:
                    f.write("      Reservoir Model = " + str(model.reserv.resoption.value.value) + " Model\n")
                    if model.reserv.resoption.value == ReservoirModel.SINGLE_FRACTURE:
                        f.write(f"      m/A Drawdown Parameter:                                 {model.reserv.drawdp.value:.5f} " + model.reserv.drawdp.CurrentUnits.value + NL)
                    elif model.reserv.resoption.value == ReservoirModel.ANNUAL_PERCENTAGE:
                        f.write(f"      Annual Thermal Drawdown:                                {model.reserv.drawdp.value*100:.3f} " + model.reserv.drawdp.CurrentUnits.value + NL)

                    f.write(f"      Bottom-hole temperature:                          {model.reserv.Trock.value:10.2f} " + model.reserv.Trock.CurrentUnits.value +  NL)
                    if model.reserv.resoption.value in [ReservoirModel.ANNUAL_PERCENTAGE, ReservoirModel.USER_PROVIDED_PROFILE, ReservoirModel.TOUGH2_SIMULATOR]:
                        f.write('      Warning: the reservoir dimensions and thermo-physical properties \n')
                        f.write('               listed below are default values if not provided by the user.   \n')
                        f.write('               They are only used for calculating remaining heat content.  \n')

                    if model.reserv.resoption.value in [ReservoirModel.MULTIPLE_PARALLEL_FRACTURES, ReservoirModel.LINEAR_HEAT_SWEEP]:
                        f.write("      Fracture model = " + model.reserv.fracshape.value.value + NL)
                        if model.reserv.fracshape.value == FractureShape.CIRCULAR_AREA:
                            f.write(f"      Well seperation: fracture diameter:               {model.reserv.fracheightcalc.value:10.2f} " + model.reserv.fracheight.CurrentUnits.value + NL)
                        elif model.reserv.fracshape.value == FractureShape.CIRCULAR_DIAMETER:
                            f.write(f"      Well seperation: fracture diameter:               {model.reserv.fracheightcalc.value:10.2f} " + model.reserv.fracheight.CurrentUnits.value + NL)
                        elif model.reserv.fracshape.value == FractureShape.SQUARE:
                            f.write(f"      Well seperation: fracture height:                 {model.reserv.fracheightcalc.value:10.2f} " + model.reserv.fracheight.CurrentUnits.value + NL)
                        elif model.reserv.fracshape.value == FractureShape.RECTANGULAR:
                            f.write(f"      Well seperation: fracture height:                 {model.reserv.fracheightcalc.value:10.2f} " + model.reserv.fracheight.CurrentUnits.value + NL)
                            f.write(f"      Fracture width:                                             {model.reserv.fracwidthcalc.value:10.2f} " + model.reserv.fracwidth.CurrentUnits.value + NL)
                        f.write(f"      Fracture area:                                    {model.reserv.fracareacalc.value:10.2f} " + model.reserv.fracarea.CurrentUnits.value + NL)
                    if model.reserv.resvoloption.value == ReservoirVolume.FRAC_NUM_SEP:
                        f.write('      Reservoir volume calculated with fracture separation and number of fractures as input\n')
                    elif model.reserv.resvoloption.value == ReservoirVolume.RES_VOL_FRAC_SEP:
                        f.write('      Number of fractures calculated with reservoir volume and fracture separation as input\n')
                    elif model.reserv.resvoloption.value == ReservoirVolume.FRAC_NUM_SEP:
                        f.write('      Fracture separation calculated with reservoir volume and number of fractures as input\n')
                    elif model.reserv.resvoloption.value == ReservoirVolume.RES_VOL_ONLY:
                        f.write('      Reservoir volume provided as input\n')
                    if model.reserv.resvoloption.value in [ReservoirVolume.FRAC_NUM_SEP, ReservoirVolume.RES_VOL_FRAC_SEP,ReservoirVolume.FRAC_NUM_SEP]:
                        f.write(f"      Number of fractures:                              {model.reserv.fracnumbcalc.value:10.2f}" + NL)
                        f.write(f"      Fracture separation:                              {model.reserv.fracsepcalc.value:10.2f} " + model.reserv.fracsep.CurrentUnits.value + NL)
                    f.write(f"      Reservoir volume:                              {model.reserv.resvolcalc.value:10.0f} " + model.reserv.resvol.CurrentUnits.value + NL)
                    if model.wellbores.impedancemodelused.value:
                        f.write(f"      Reservoir impedance:                              {model.wellbores.impedance.value/1000:10.2f} " + model.wellbores.impedance.CurrentUnits.value + NL)
                    else:
                        f.write(f"      Reservoir hydrostatic pressure:                   {model.wellbores.Phydrostaticcalc.value:10.2f} " + model.wellbores.Phydrostaticcalc.CurrentUnits.value + NL)
                        f.write(f"      Plant outlet pressure:                            {model.surfaceplant.Pplantoutlet.value:10.2f} " + model.surfaceplant.Pplantoutlet.CurrentUnits.value + NL)
                        if model.wellbores.productionwellpumping.value:
                            f.write(f"      Production wellhead pressure:                     {model.wellbores.Pprodwellhead.value:10.2f} " + model.wellbores.Pprodwellhead.CurrentUnits.value + NL)
                            f.write(f"      Productivity Index:                               {model.wellbores.PI.value:10.2f} " + model.wellbores.PI.CurrentUnits.value + NL)
                        f.write(f"      Injectivity Index:                                {model.wellbores.II.value:10.2f} " + model.wellbores.II.CurrentUnits.value + NL)

                    f.write(f"      Reservoir density:                                {model.reserv.rhorock.value:10.2f} " + model.reserv.rhorock.CurrentUnits.value + NL)
                    if model.wellbores.rameyoptionprod.value or model.reserv.resoption.value in [ReservoirModel.MULTIPLE_PARALLEL_FRACTURES, ReservoirModel.LINEAR_HEAT_SWEEP, ReservoirModel.SINGLE_FRACTURE, ReservoirModel.TOUGH2_SIMULATOR]:
                        f.write(f"      Reservoir thermal conductivity:                   {model.reserv.krock.value:10.2f} " + model.reserv.krock.CurrentUnits.value + NL)
                    f.write(f"      Reservoir heat capacity:                          {model.reserv.cprock.value:10.2f} " + model.reserv.cprock.CurrentUnits.value + NL)
                    if model.reserv.resoption.value == ReservoirModel.LINEAR_HEAT_SWEEP or (model.reserv.resoption.value == ReservoirModel.TOUGH2_SIMULATOR and model.reserv.usebuiltintough2model):
                        f.write(f"      Reservoir porosity:                               {model.reserv.porrock.value*100:10.2f} " + model.reserv.porrock.CurrentUnits.value + NL)
                    if model.reserv.resoption.value == ReservoirModel.TOUGH2_SIMULATOR and model.reserv.usebuiltintough2model:
                        f.write(f"      Reservoir permeability:                           {model.reserv.permrock.value:10.2E} " + model.reserv.permrock.CurrentUnits.value + NL)
                        f.write(f"      Reservoir thickness:                              {model.reserv.resthickness.value:10.2f} " + model.reserv.resthickness.CurrentUnits.value + NL)
                        f.write(f"      Reservoir width:                                  {model.reserv.reswidth.value:10.2f} " + model.reserv.reswidth.CurrentUnits.value + NL)
                        f.write(f"      Well separation:                                  {model.wellbores.wellsep.value:10.2f} " + model.wellbores.wellsep.CurrentUnits.value + NL)

                f.write(NL)
                f.write(NL)
                f.write("                           ***RESERVOIR SIMULATION RESULTS***" + NL)
                f.write(NL)
                f.write(f"      Maximum Production Temperature:                  {np.max(model.wellbores.ProducedTemperature.value):10.1f} " + model.wellbores.ProducedTemperature.PreferredUnits.value + NL)
                f.write(f"      Average Production Temperature:                  {np.average(model.wellbores.ProducedTemperature.value):10.1f} " + model.wellbores.ProducedTemperature.PreferredUnits.value + NL)
                f.write(f"      Minimum Production Temperature:                  {np.min(model.wellbores.ProducedTemperature.value):10.1f} " + model.wellbores.ProducedTemperature.PreferredUnits.value + NL)
                f.write(f"      Initial Production Temperature:                  {model.wellbores.ProducedTemperature.value[0]:10.1f} " + model.wellbores.ProducedTemperature.PreferredUnits.value + NL)
                if model.wellbores.IsAGS.value:
                    f.write("The AGS models contain an intrinsic reservoir model that doesn't expose values that can be used in extensive reporting." + NL)
                else:
                    f.write(f"      Average Reservoir Heat Extraction:                {np.average(model.surfaceplant.HeatExtracted.value):10.2f} " + model.surfaceplant.HeatExtracted.PreferredUnits.value + NL)
                    if model.wellbores.rameyoptionprod.value:
                        f.write("      Production Wellbore Heat Transmission Model = Ramey Model" + NL)
                        f.write(f"      Average Production Well Temperature Drop:        {np.average(model.wellbores.ProdTempDrop.value):10.1f} " + model.wellbores.ProdTempDrop.PreferredUnits.value + NL)
                    else:
                        f.write(f" Wellbore Heat Transmission Model = Constant Temperature Drop:{model.wellbores.tempdropprod.value:10.1f} " + model.wellbores.tempdropprod.PreferredUnits.value + NL)
                    if model.wellbores.impedancemodelused.value:
                        f.write(f"      Total Average Pressure Drop:                     {np.average(model.wellbores.DPOverall.value):10.1f} " + model.wellbores.DPOverall.PreferredUnits.value + NL)
                        f.write(f"      Average Injection Well Pressure Drop:            {np.average(model.wellbores.DPInjWell.value):10.1f} " + model.wellbores.DPInjWell.PreferredUnits.value + NL)
                        f.write(f"      Average Reservoir Pressure Drop:                 {np.average(model.wellbores.DPReserv.value):10.1f} " + model.wellbores.DPReserv.PreferredUnits.value + NL)
                        f.write(f"      Average Production Well Pressure Drop:           {np.average(model.wellbores.DPProdWell.value):10.1f} " + model.wellbores.DPProdWell.PreferredUnits.value + NL)
                        f.write(f"      Average Buoyancy Pressure Drop:                  {np.average(model.wellbores.DPBouyancy.value):10.1f} " + model.wellbores.DPBouyancy.PreferredUnits.value + NL)
                    else:
                        f.write(f"      Average Injection Well Pump Pressure Drop:       {np.average(model.wellbores.DPInjWell.value):10.1f} " + model.wellbores.DPInjWell.PreferredUnits.value + NL)
                        if model.wellbores.productionwellpumping.value:
                            f.write(f"      Average Production Well Pump Pressure Drop:      {np.average(model.wellbores.DPProdWell.value):10.1f} " + model.wellbores.DPProdWell.PreferredUnits.value + NL)

                f.write(NL)
                f.write(NL)
                f.write('                          ***CAPITAL COSTS (M$)***\n')
                f.write(NL)
                if not model.economics.totalcapcost.Valid:
                    f.write(f"         Drilling and completion costs:                 {model.economics.Cwell.value:10.2f} " + model.economics.Cwell.CurrentUnits.value + NL)
                    f.write(f"         Drilling and completion costs per well:        {model.economics.Cwell.value/(model.wellbores.nprod.value+model.wellbores.ninj.value):10.2f} " + model.economics.Cwell.CurrentUnits.value + NL)
                    f.write(f"         Stimulation costs:                             {model.economics.Cstim.value:10.2f} " + model.economics.Cstim.CurrentUnits.value + NL)
                    f.write(f"         Surface power plant costs:                     {model.economics.Cplant.value:10.2f} " + model.economics.Cplant.CurrentUnits.value + NL)
                    if model.surfaceplant.enduseoption.value == EndUseOptions.ABSORPTION_CHILLER:
                        f.write(f"            of which Absorption Chiller Cost:           {model.economics.chillercapex.value:10.2f} " + model.economics.Cplant.CurrentUnits.value + NL)
                    if model.surfaceplant.enduseoption.value == EndUseOptions.HEAT_PUMP:
                        f.write(f"            of which Heat Pump Cost:                    {model.economics.heatpumpcapex.value:10.2f} " + model.economics.Cplant.CurrentUnits.value + NL)
                    if model.surfaceplant.enduseoption.value == EndUseOptions.DISTRICT_HEATING:
                        f.write(f"            of which Peaking Boiler Cost:               {model.economics.peakingboilercost.value:10.2f} " + model.economics.peakingboilercost.CurrentUnits.value + NL)
                    f.write(f"         Field gathering system costs:                  {model.economics.Cgath.value:10.2f} " + model.economics.Cgath.CurrentUnits.value + NL)
                    if model.surfaceplant.pipinglength.value > 0: f.write(f"         Transmission pipeline cost                     {model.economics.Cpiping.value:10.2f} " + model.economics.Cpiping.CurrentUnits.value + NL)
                    if model.surfaceplant.enduseoption.value == EndUseOptions.DISTRICT_HEATING:
                        f.write(f"         District Heating System Cost:                  {model.economics.dhdistrictcost.value:10.2f} " + model.economics.dhdistrictcost.CurrentUnits.value + NL)
                    f.write(f"         Total surface equipment costs:                 {(model.economics.Cplant.value+model.economics.Cgath.value):10.2f} " + model.economics.Cplant.CurrentUnits.value + NL)
                    f.write(f"         Exploration costs:                             {model.economics.Cexpl.value:10.2f} " + model.economics.Cexpl.CurrentUnits.value + NL)
                if model.economics.totalcapcost.Valid and model.wellbores.redrill.value > 0:
                    f.write(f"         Drilling and completion costs (for redrilling):{model.economics.Cwell.value:10.2f} " + model.economics.Cwell.CurrentUnits.value + NL)
                    f.write(f"      Drilling and completion costs per redrilled well: {(model.economics.Cwell.value/(model.wellbores.nprod.value+model.wellbores.ninj.value)):10.2f} " + model.economics.Cwell.CurrentUnits.value + NL)
                    f.write(f"         Stimulation costs (for redrilling):            {model.economics.Cstim.value:10.2f} " + model.economics.Cstim.CurrentUnits.value + NL)
                f.write(f"      Total capital costs:                              {model.economics.CCap.value:10.2f} " + model.economics.CCap.CurrentUnits.value + NL)
                if model.economics.econmodel.value == EconomicModel.FCR:
                    f.write(f"      Annualized capital costs:                         {(model.economics.CCap.value*(1+model.economics.inflrateconstruction.value)*model.economics.FCR.value):10.2f} " + model.economics.CCap.CurrentUnits.value + NL)

                f.write(NL)
                f.write(NL)
                f.write('                ***OPERATING AND MAINTENANCE COSTS (M$/yr)***\n')
                f.write(NL)
                if not model.economics.oamtotalfixed.Valid:
                    f.write(f"         Wellfield maintenance costs:                   {model.economics.Coamwell.value:10.2f} " + model.economics.Coamwell.CurrentUnits.value + NL)
                    f.write(f"         Power plant maintenance costs:                 {model.economics.Coamplant.value:10.2f} " + model.economics.Coamplant.CurrentUnits.value + NL)
                    f.write(f"         Water costs:                                   {model.economics.Coamwater.value:10.2f} " + model.economics.Coamwater.CurrentUnits.value + NL)
                    if model.surfaceplant.enduseoption.value in [EndUseOptions.HEAT, EndUseOptions.ABSORPTION_CHILLER, EndUseOptions.HEAT_PUMP, EndUseOptions.DISTRICT_HEATING]:
                        f.write(f"         Average Reservoir Pumping Cost:                {model.economics.averageannualpumpingcosts.value:10.2f} " + model.economics.averageannualpumpingcosts.CurrentUnits.value + NL)
                    if model.surfaceplant.enduseoption.value ==  EndUseOptions.ABSORPTION_CHILLER:
                        f.write(f"         Absorption Chiller O&M Cost:                   {model.economics.chilleropex.value:10.2f} " + model.economics.chilleropex.CurrentUnits.value + NL)
                    if model.surfaceplant.enduseoption.value ==  EndUseOptions.HEAT_PUMP:
                        f.write(f"         Average Heat Pump Electricity Cost:            {model.economics.averageannualheatpumpelectricitycost.value:10.2f} " + model.economics.averageannualheatpumpelectricitycost.CurrentUnits.value + NL)
                    if model.surfaceplant.enduseoption.value == EndUseOptions.DISTRICT_HEATING:
                        f.write(f"         Annual District Heating O&M Cost:              {model.economics.dhdistrictoandmcost.value:10.2f} " + model.economics.dhdistrictoandmcost.CurrentUnits.value + NL)
                        f.write(f"         Average Annual Peaking Fuel Cost:              {model.economics.averageannualngcost.value:10.2f} " + model.economics.averageannualngcost.CurrentUnits.value + NL)

                    f.write(f"      Total operating and maintenance costs:            {(model.economics.Coam.value + model.economics.averageannualpumpingcosts.value+model.economics.averageannualheatpumpelectricitycost.value):10.2f} " + model.economics.Coam.CurrentUnits.value + NL)
                else:
                    f.write(f"      Total operating and maintenance costs:            {model.economics.Coam.value:10.2f} " + model.economics.Coam.CurrentUnits.value + NL)

                f.write(NL)
                f.write(NL)
                f.write('                           ***SURFACE EQUIPMENT SIMULATION RESULTS***\n')
                f.write(NL)
                if model.surfaceplant.enduseoption.value in [EndUseOptions.ELECTRICITY, EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT, EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICTY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICTY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICTY]: #there is an electricity componenent:
                    f.write(f"      Initial geofluid availability:                    {model.surfaceplant.Availability.value[0]:10.2f} " + model.surfaceplant.Availability.PreferredUnits.value + NL)
                    f.write(f"      Maximum Total Electricity Generation:             {np.max(model.surfaceplant.ElectricityProduced.value):10.2f} " + model.surfaceplant.ElectricityProduced.PreferredUnits.value + NL)
                    f.write(f"      Average Total Electricity Generation:             {np.average(model.surfaceplant.ElectricityProduced.value):10.2f} " + model.surfaceplant.ElectricityProduced.PreferredUnits.value + NL)
                    f.write(f"      Minimum Total Electricity Generation:             {np.min(model.surfaceplant.ElectricityProduced.value):10.2f} " + model.surfaceplant.ElectricityProduced.PreferredUnits.value + NL)
                    f.write(f"      Initial Total Electricity Generation:             {model.surfaceplant.ElectricityProduced.value[0]:10.2f} " + model.surfaceplant.ElectricityProduced.PreferredUnits.value + NL)
                    f.write(f"      Maximum Net Electricity Generation:               {np.max(model.surfaceplant.NetElectricityProduced.value):10.2f} " + model.surfaceplant.NetElectricityProduced.PreferredUnits.value + NL)
                    f.write(f"      Average Net Electricity Generation:               {np.average(model.surfaceplant.NetElectricityProduced.value):10.2f} " + model.surfaceplant.NetElectricityProduced.PreferredUnits.value + NL)
                    f.write(f"      Minimum Net Electricity Generation:               {np.min(model.surfaceplant.NetElectricityProduced.value):10.2f} " + model.surfaceplant.NetElectricityProduced.PreferredUnits.value + NL)
                    f.write(f"      Initial Net Electricity Generation:               {model.surfaceplant.NetElectricityProduced.value[0]:10.2f} " + model.surfaceplant.NetElectricityProduced.PreferredUnits.value + NL)
                    f.write(f"      Average Annual Total Electricity Generation:      {np.average(model.surfaceplant.TotalkWhProduced.value/1E6):10.2f} GWh" + NL)
                    f.write(f"      Average Annual Net Electricity Generation:        {np.average(model.surfaceplant.NetkWhProduced.value/1E6):10.2f} GWh" + NL)
                    if model.wellbores.PumpingPower.value[0] > 0.0: f.write(f"      Initial pumping power/net installed power:        {(model.wellbores.PumpingPower.value[0]/model.wellbores.PumpingPower.value[0]*100):10.2f} %" + NL)
                if model.surfaceplant.enduseoption.value in [EndUseOptions.HEAT,EndUseOptions.ABSORPTION_CHILLER,EndUseOptions.HEAT_PUMP,EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT, EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICTY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICTY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICTY]: #geothermal heating component:
                    f.write(f"      Maximum Net Heat Production:                      {np.max(model.surfaceplant.HeatProduced.value):10.2f} " + model.surfaceplant.HeatProduced.PreferredUnits.value + NL)
                    f.write(f"      Average Net Heat Production:                      {np.average(model.surfaceplant.HeatProduced.value):10.2f} " + model.surfaceplant.HeatProduced.PreferredUnits.value + NL)
                    f.write(f"      Minimum Net Heat Production:                      {np.min(model.surfaceplant.HeatProduced.value):10.2f} " + model.surfaceplant.HeatProduced.PreferredUnits.value + NL)
                    f.write(f"      Initial Net Heat Production:                      {model.surfaceplant.HeatProduced.value[0]:10.2f} " + model.surfaceplant.HeatProduced.PreferredUnits.value + NL)
                    f.write(f"      Average Annual Heat Production:                   {np.average(model.surfaceplant.HeatkWhProduced.value/1E6):10.2f} GWh" + NL)

                if model.surfaceplant.enduseoption.value == EndUseOptions.HEAT_PUMP:
                    f.write(f"      Average Annual Heat Pump Electricity Use:         {np.average(model.surfaceplant.HeatPumpElectricitykWhUsed.value/1E6):10.2f} " + "GWh/year" + NL)
                if model.surfaceplant.enduseoption.value == EndUseOptions.ABSORPTION_CHILLER:
                    f.write(f"      Maximum Cooling Production:                       {np.max(model.surfaceplant.CoolingProduced.value):10.2f} " + model.surfaceplant.CoolingProduced.PreferredUnits.value + NL)
                    f.write(f"      Average Cooling Production:                       {np.average(model.surfaceplant.CoolingProduced.value):10.2f} " + model.surfaceplant.CoolingProduced.PreferredUnits.value + NL)
                    f.write(f"      Minimum Cooling Production:                       {np.min(model.surfaceplant.CoolingProduced.value):10.2f} " + model.surfaceplant.CoolingProduced.PreferredUnits.value + NL)
                    f.write(f"      Initial Cooling Production:                       {model.surfaceplant.CoolingProduced.value[0]:10.2f} " + model.surfaceplant.CoolingProduced.PreferredUnits.value + NL)
                    f.write(f"      Average Annual Cooling Production:                {np.average(model.surfaceplant.CoolingkWhProduced.value/1E6):10.2f} " + "GWh/year" + NL)

                if model.surfaceplant.enduseoption.value == EndUseOptions.DISTRICT_HEATING:
                    f.write(f"      Annual District Heating Demand:                   {model.surfaceplant.annualheatingdemand.value:10.2f} " + model.surfaceplant.annualheatingdemand.PreferredUnits.value + NL)
                    f.write(f"      Maximum Daily District Heating Demand:            {np.max(model.surfaceplant.dailyheatingdemand.value):10.2f} " + model.surfaceplant.dailyheatingdemand.PreferredUnits.value + NL)
                    f.write(f"      Average Daily District Heating Demand:            {np.average(model.surfaceplant.dailyheatingdemand.value):10.2f} " + model.surfaceplant.dailyheatingdemand.PreferredUnits.value + NL)
                    f.write(f"      Minimum Daily District Heating Demand:            {np.min(model.surfaceplant.dailyheatingdemand.value):10.2f} " + model.surfaceplant.dailyheatingdemand.PreferredUnits.value + NL)
                    f.write(f"      Maximum Geothermal Heating Production:            {np.max(model.surfaceplant.dhgeothermalheating.value):10.2f} " + model.surfaceplant.dhgeothermalheating.PreferredUnits.value + NL)
                    f.write(f"      Average Geothermal Heating Production:            {np.average(model.surfaceplant.dhgeothermalheating.value):10.2f} " + model.surfaceplant.dhgeothermalheating.PreferredUnits.value + NL)
                    f.write(f"      Minimum Geothermal Heating Production:            {np.min(model.surfaceplant.dhgeothermalheating.value):10.2f} " + model.surfaceplant.dhgeothermalheating.PreferredUnits.value + NL)
                    f.write(f"      Maximum Peaking Boiler Heat Production:           {np.max(model.surfaceplant.dhnaturalgasheating.value):10.2f} " + model.surfaceplant.dhnaturalgasheating.PreferredUnits.value + NL)
                    f.write(f"      Average Peaking Boiler Heat Production:           {np.average(model.surfaceplant.dhnaturalgasheating.value):10.2f} " + model.surfaceplant.dhnaturalgasheating.PreferredUnits.value + NL)
                    f.write(f"      Minimum Peaking Boiler Heat Production:           {np.min(model.surfaceplant.dhnaturalgasheating.value):10.2f} " + model.surfaceplant.dhnaturalgasheating.PreferredUnits.value + NL)

                f.write(f"      Average Pumping Power:                            {np.average(model.wellbores.PumpingPower.value):10.2f} " + model.wellbores.PumpingPower.PreferredUnits.value + NL)


                f.write(NL)
                f.write('                            ************************************************************\n')
                f.write('                            *  HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE  *\n')
                f.write('                            ************************************************************\n')
                if model.surfaceplant.enduseoption.value == EndUseOptions.ELECTRICITY:   #only electricity
                    f.write('  YEAR       THERMAL               GEOFLUID               PUMP               NET               FIRST LAW\n')
                    f.write('             DRAWDOWN             TEMPERATURE             POWER             POWER              EFFICIENCY\n')
                    f.write("                                     (" + model.wellbores.ProducedTemperature.CurrentUnits.value+")               (" + model.wellbores.PumpingPower.CurrentUnits.value + ")              (" + model.surfaceplant.NetElectricityProduced.CurrentUnits.value + ")                  (%)\n")
                    for i in range(0, model.surfaceplant.plantlifetime.value):
                        f.write('  {0:2.0f}         {1:8.4f}              {2:8.2f}             {3:8.4f}          {4:8.4f}              {5:8.4f}'.format(i+1,
                                                model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value]/model.wellbores.ProducedTemperature.value[0],
                                                                        model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value],
                                                                                                        model.wellbores.PumpingPower.value[i*model.economics.timestepsperyear.value],
                                                                                                                            model.surfaceplant.NetElectricityProduced.value[i*model.economics.timestepsperyear.value],
                                                                                                                                                        model.surfaceplant.FirstLawEfficiency.value[i*model.economics.timestepsperyear.value]*100)+NL)
                elif model.surfaceplant.enduseoption.value == EndUseOptions.HEAT: #only direct-use
                    f.write('  YEAR       THERMAL               GEOFLUID               PUMP               NET\n')
                    f.write('             DRAWDOWN             TEMPERATURE             POWER              HEAT\n')
                    f.write('                                   (deg C)                (MW)               (MW)\n')
                    for i in range(0, model.surfaceplant.plantlifetime.value):
                        f.write('  {0:2.0f}         {1:8.4f}              {2:8.2f}             {3:8.4f}          {4:8.4f}'.format(i,
                                                model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value]/model.wellbores.ProducedTemperature.value[0],
                                                                        model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value],
                                                                                                        model.wellbores.PumpingPower.value[i*model.economics.timestepsperyear.value],
                                                                                                                                model.surfaceplant.HeatProduced.value[i*model.economics.timestepsperyear.value])+NL)


                elif model.surfaceplant.enduseoption.value in [EndUseOptions.HEAT_PUMP]: #heat pump
                    f.write('  YEAR         THERMAL              GEOFLUID               PUMP               NET             HEAT PUMP\n')
                    f.write('               DRAWDOWN            TEMPERATURE             POWER              HEAT         ELECTRICITY USE\n')
                    f.write('                                    (deg C)                (MWe)              (MWt)             (MWe)\n')
                    for i in range(0, model.surfaceplant.plantlifetime.value):
                        f.write('  {0:2.0f}          {1:8.4f}             {2:8.2f}              {3:8.4f}           {4:8.4f}          {5:8.4f}'.format(i,
                                                model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value]/model.wellbores.ProducedTemperature.value[0],
                                                                        model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value],
                                                                                                        model.wellbores.PumpingPower.value[i*model.economics.timestepsperyear.value],
                                                                                                                                model.surfaceplant.HeatProduced.value[i*model.economics.timestepsperyear.value],model.surfaceplant.HeatPumpElectricityUsed.value[i*model.economics.timestepsperyear.value])+NL)

                elif model.surfaceplant.enduseoption.value in [EndUseOptions.DISTRICT_HEATING]: #district heating
                    f.write('  YEAR         THERMAL              GEOFLUID               PUMP              GEOTHERMAL\n')
                    f.write('               DRAWDOWN            TEMPERATURE             POWER            HEAT OUTPUT\n')
                    f.write('                                    (deg C)                (MWe)               (MWt)\n')
                    for i in range(0, model.surfaceplant.plantlifetime.value):
                        f.write('  {0:2.0f}          {1:8.4f}             {2:8.2f}              {3:8.4f}            {4:8.4f}'.format(i,
                                                model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value]/model.wellbores.ProducedTemperature.value[0],
                                                                        model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value],
                                                                                                        model.wellbores.PumpingPower.value[i*model.economics.timestepsperyear.value],
                                                                                                                                model.surfaceplant.HeatProduced.value[i*model.economics.timestepsperyear.value])+NL)


                elif model.surfaceplant.enduseoption.value in [EndUseOptions.ABSORPTION_CHILLER]: #absorption chiller
                    f.write('  YEAR         THERMAL              GEOFLUID               PUMP               NET              NET\n')
                    f.write('               DRAWDOWN            TEMPERATURE             POWER              HEAT             COOLING\n')
                    f.write('                                    (deg C)                (MWe)              (MWt)            (MWt)\n')
                    for i in range(0, model.surfaceplant.plantlifetime.value):
                        f.write('  {0:2.0f}          {1:8.4f}             {2:8.2f}              {3:8.4f}           {4:8.4f}         {5:8.4f}'.format(i,
                                                model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value]/model.wellbores.ProducedTemperature.value[0],
                                                                        model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value],
                                                                                                        model.wellbores.PumpingPower.value[i*model.economics.timestepsperyear.value],
                                                                                                                                model.surfaceplant.HeatProduced.value[i*model.economics.timestepsperyear.value],model.surfaceplant.CoolingProduced.value[i*model.economics.timestepsperyear.value],)+NL)


                elif model.surfaceplant.enduseoption.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT,EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICTY,EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICTY,EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT,EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICTY]:  # co-gen
                    f.write('  YEAR     THERMAL             GEOFLUID             PUMP             NET              NET             FIRST LAW\n')
                    f.write('           DRAWDOWN           TEMPERATURE           POWER           POWER             HEAT            EFFICIENCY\n')
                    f.write('                                (deg C)             (MW)            (MW)              (MW)               (%)\n')
                    for i in range(0, model.surfaceplant.plantlifetime.value):
                        f.write('  {0:2.0f}       {1:8.4f}            {2:8.2f}           {3:8.4f}        {4:8.4f}            {5:8.4f}             {6:8.4f}'.format(i,
                                                model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value]/model.wellbores.ProducedTemperature.value[0],
                                                                        model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value],
                                                                                                    model.wellbores.PumpingPower.value[i*model.economics.timestepsperyear.value],
                                                                                                                            model.surfaceplant.NetElectricityProduced.value[i*model.economics.timestepsperyear.value],
                                                                                                                                                    model.surfaceplant.HeatProduced.value[i*model.economics.timestepsperyear.value],
                                                                                                                                                                                model.surfaceplant.FirstLawEfficiency.value[i*model.economics.timestepsperyear.value]*100)+NL)
                f.write(NL)

                f.write(NL)
                f.write('                              *******************************************************************\n')
                f.write('                              *  ANNUAL HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE  *\n')
                f.write('                              *******************************************************************\n')
                if model.surfaceplant.enduseoption.value == EndUseOptions.ELECTRICITY:  #only electricity
                    f.write('  YEAR             ELECTRICITY                   HEAT                RESERVOIR            PERCENTAGE OF\n')
                    f.write('                    PROVIDED                   EXTRACTED            HEAT CONTENT        TOTAL HEAT MINED\n')
                    f.write('                   (GWh/year)                  (GWh/year)            (10^15 J)                 (%)\n')
                    for i in range(0, model.surfaceplant.plantlifetime.value):
                        f.write('  {0:2.0f}              {1:8.1f}                    {2:8.1f}              {3:8.2f}               {4:8.2f}'.format(i+1,
                                                model.surfaceplant.NetkWhProduced.value[i]/1E6,
                                                                            model.surfaceplant.HeatkWhExtracted.value[i]/1E6,
                                                                                                    model.surfaceplant.RemainingReservoirHeatContent.value[i],
                                                                                                                            (model.reserv.InitialReservoirHeatContent.value-model.surfaceplant.RemainingReservoirHeatContent.value[i])*100/model.reserv.InitialReservoirHeatContent.value)+NL)
                elif model.surfaceplant.enduseoption.value == EndUseOptions.HEAT: #only direct-use
                    f.write('  YEAR               HEAT                       HEAT                RESERVOIR            PERCENTAGE OF\n')
                    f.write('                    PROVIDED                   EXTRACTED            HEAT CONTENT        TOTAL HEAT MINED\n')
                    f.write('                   (GWh/year)                  (GWh/year)            (10^15 J)                 (%)\n')
                    for i in range(0, model.surfaceplant.plantlifetime.value):
                        f.write('  {0:2.0f}              {1:8.1f}                    {2:8.1f}              {3:8.2f}               {4:8.2f}'.format(i+1,
                                                model.surfaceplant.HeatkWhProduced.value[i]/1E6,
                                                                            model.surfaceplant.HeatkWhExtracted.value[i]/1E6,
                                                                                                    model.surfaceplant.RemainingReservoirHeatContent.value[i],
                                                                                                                            (model.reserv.InitialReservoirHeatContent.value-model.surfaceplant.RemainingReservoirHeatContent.value[i])*100/model.reserv.InitialReservoirHeatContent.value)+NL)


                elif model.surfaceplant.enduseoption.value == EndUseOptions.ABSORPTION_CHILLER: #absorption chiller
                    f.write('  YEAR              COOLING                 HEAT                RESERVOIR            PERCENTAGE OF\n')
                    f.write('                    PROVIDED              EXTRACTED            HEAT CONTENT        TOTAL HEAT MINED\n')
                    f.write('                   (GWh/year)             (GWh/year)            (10^15 J)                 (%)\n')
                    for i in range(0, model.surfaceplant.plantlifetime.value):
                        f.write('  {0:2.0f}              {1:8.1f}               {2:8.1f}              {3:8.2f}               {4:8.2f}'.format(i+1,
                                                model.surfaceplant.CoolingkWhProduced.value[i]/1E6,
                                                                            model.surfaceplant.HeatkWhExtracted.value[i]/1E6,
                                                                                                    model.surfaceplant.RemainingReservoirHeatContent.value[i],
                                                                                                                            (model.reserv.InitialReservoirHeatContent.value-model.surfaceplant.RemainingReservoirHeatContent.value[i])*100/model.reserv.InitialReservoirHeatContent.value)+NL)


                elif model.surfaceplant.enduseoption.value == EndUseOptions.HEAT_PUMP: #heat pump
                    f.write('  YEAR              HEATING             RESERVOIR HEAT          HEAT PUMP          RESERVOIR           PERCENTAGE OF\n')
                    f.write('                    PROVIDED              EXTRACTED          ELECTRICITY USE      HEAT CONTENT        TOTAL HEAT MINED\n')
                    f.write('                   (GWh/year)             (GWh/year)           (GWh/year)           (10^15 J)                (%)\n')
                    for i in range(0, model.surfaceplant.plantlifetime.value):
                        f.write('  {0:2.0f}              {1:8.1f}               {2:8.1f}             {3:8.2f}             {4:8.2f}              {5:8.2f}'.format(i+1,
                                                model.surfaceplant.HeatkWhProduced.value[i]/1E6,
                                                                            model.surfaceplant.HeatkWhExtracted.value[i]/1E6,model.surfaceplant.HeatPumpElectricitykWhUsed.value[i]/1E6,
                                                                                                    model.surfaceplant.RemainingReservoirHeatContent.value[i],
                                                                                                                            (model.reserv.InitialReservoirHeatContent.value-model.surfaceplant.RemainingReservoirHeatContent.value[i])*100/model.reserv.InitialReservoirHeatContent.value)+NL)

                elif model.surfaceplant.enduseoption.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT, EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICTY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICTY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICTY]: #co-gen
                    f.write('  YEAR             HEAT                 ELECTRICITY                HEAT              RESERVOIR        PERCENTAGE OF\n')
                    f.write('                  PROVIDED               PROVIDED                EXTRACTED          HEAT CONTENT    TOTAL HEAT MINED\n')
                    f.write('                 (GWh/year)             (GWh/year)               (GWh/year)          (10^15 J)           (%)\n')
                    for i in range(0, model.surfaceplant.plantlifetime.value):
                        f.write('  {0:2.0f}            {1:8.1f}               {2:8.1f}                  {3:8.2f}            {4:8.2f}             {5:8.2f}'.format(i+1,
                                            model.surfaceplant.HeatkWhProduced.value[i]/1E6,
                                                                        model.surfaceplant.NetkWhProduced.value[i]/1E6,
                                                                                                    model.surfaceplant.HeatkWhExtracted.value[i]/1E6,
                                                                                                                            model.surfaceplant.RemainingReservoirHeatContent.value[i],
                                                                                                                                                (model.reserv.InitialReservoirHeatContent.value-model.surfaceplant.RemainingReservoirHeatContent.value[i])*100/model.reserv.InitialReservoirHeatContent.value)+NL)

                elif model.surfaceplant.enduseoption.value in [EndUseOptions.DISTRICT_HEATING]: #district-heating
                    f.write('  YEAR           GEOTHERMAL          PEAKING BOILER       RESERVOIR HEAT          RESERVOIR         PERCENTAGE OF\n')
                    f.write('              HEATING PROVIDED      HEATING PROVIDED        EXTRACTED            HEAT CONTENT     TOTAL HEAT MINED\n')
                    f.write('                 (GWh/year)            (GWh/year)           (GWh/year)            (10^15 J)              (%)\n')
                    for i in range(0, model.surfaceplant.plantlifetime.value):
                        f.write('  {0:2.0f}            {1:8.1f}              {2:8.1f}              {3:8.2f}             {4:8.2f}            {5:8.2f}'.format(i+1,
                                            model.surfaceplant.HeatkWhProduced.value[i]/1E6,
                                                                        model.surfaceplant.annualngdemand.value[i]/1E3,
                                                                                                    model.surfaceplant.HeatkWhExtracted.value[i]/1E6,
                                                                                                                            model.surfaceplant.RemainingReservoirHeatContent.value[i],
                                                                                                                                                (model.reserv.InitialReservoirHeatContent.value-model.surfaceplant.RemainingReservoirHeatContent.value[i])*100/model.reserv.InitialReservoirHeatContent.value)+NL)



                f.write(NL)

            # MIR MIR if model.wellbores.HasHorizontalSection.value: model.cloutputs.PrintOutputs(model)
            if model.economics.DoAddOnCalculations.value: model.addoutputs.PrintOutputs(model)
            if model.economics.DoCCUSCalculations.value: model.ccusoutputs.PrintOutputs(model)
            if model.economics.DoSDACGTCalculations.value: model.sdacgtoutputs.PrintOutputs(model)
        except BaseException as ex:
            tb = sys.exc_info()[2]
            print (str(ex))
            print("Error: GEOPHIRES Failed to write the output file.  Exiting....Line %i" % tb.tb_lineno)
            model.logger.critical(str(ex))
            model.logger.critical("Error: GEOPHIRES Failed to write the output file.  Exiting....Line %i" % tb.tb_lineno)
            sys.exit()

        model.logger.info("Complete "+ str(__class__) + ": " + sys._getframe().f_code.co_name)

    def MakeDistrictHeatingPlot(self, model: Model):
        plt.close('all')
        year_day = np.arange(1, 366, 1)  # make an array of days for plot x-axis
        plt.plot(year_day, model.surfaceplant.dailyheatingdemand.value, label='District Heating Demand')
        plt.fill_between(year_day, 0, model.surfaceplant.dhgeothermalheating.value[0:365] * 24, color="g", alpha=0.5,label='Geothermal Heat Supply')
        plt.fill_between(year_day, model.surfaceplant.dhgeothermalheating.value[0:365] * 24,model.surfaceplant.dailyheatingdemand.value, color="r", alpha=0.5,label='Natural Gas Heat Supply')
        plt.xlabel('Ordinal Day')
        plt.ylabel('Heating Demand/Supply [MWh/day]')
        plt.ylim([0, max(model.surfaceplant.dailyheatingdemand.value) * 1.05])
        plt.legend()
        plt.title('Geothermal district heating system with peaking boilers')
        plt.show()

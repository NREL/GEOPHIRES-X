import datetime
import time
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import geophires_x
import geophires_x.Model as Model
from geophires_x.Economics import Economics
from geophires_x.OutputsRich import OutputTableItem, ShortenArrayToAnnual, \
    Write_Text_Output, Write_HTML_Output, Plot_Tables_Into_HTML, MakeDistrictHeatingPlot
from geophires_x.Parameter import ConvertUnitsBack, ConvertOutputUnits, LookupUnits, strParameter, boolParameter, \
    OutputParameter, ReadParameter
from geophires_x.OptionList import EndUseOptions, EconomicModel, ReservoirModel, FractureShape, ReservoirVolume, \
    PlantType
from geophires_x.Parameter import Parameter

NL = '\n'


class Outputs:
    """
    This class handles all the outputs for the GEOPHIRESv3 model.
    """

    VERTICAL_WELL_DEPTH_OUTPUT_NAME = 'Well depth'

    def __init__(self, model:Model, output_file:str ='HDR.out'):
        model.logger.info(f'Init {__class__!s}: {__name__}')
        self.ParameterDict = {}
        self.OutputParameterDict = {}
        self.filepath_parameter_names = []

        def filepath_parameter(p: Parameter) -> Parameter:
            self.filepath_parameter_names.append(p.Name)
            return p

        self.text_output_file = self.ParameterDict[self.text_output_file.Name] = filepath_parameter(strParameter(
                'Improved Text Output File',
                DefaultValue='GEOPHIRES_Text.html',
                Required=False,
                Provided=False,
                ErrMessage='assume no improved text output',
                ToolTipText='Provide a improved text output name if you want to have improved text output (no output if not provided)',
        ))

        self.html_output_file = self.ParameterDict[self.html_output_file.Name] = filepath_parameter(strParameter(
                'HTML Output File',
                DefaultValue='GEOPHIRES.html',
                Required=False,
                Provided=False,
                ErrMessage='assume no HTML output',
                ToolTipText='Provide a HTML output name if you want to have HTML output (no output if not provided)',
        ))

        self.printoutput = self.ParameterDict[self.printoutput.Name] = boolParameter(
                'Print Output to Console',
                DefaultValue=True,
                Required=False,
                Provided=False,
                ErrMessage='assume no output to console',
                ToolTipText='Provide a 0 if you do not want to print output to the console',
            )

        # Dictionary to hold the Units definitions that the user wants for outputs created by GEOPHIRES.
        # It is empty by default initially - this will expand as the user desires are read from the input file
        self.printoutput = True
        self.output_file = output_file

        model.logger.info(f'Complete {__class__!s}: {__name__}')

    def __str__(self):
        return 'Outputs'

    def read_parameters(self, model: Model, default_output_path: Path = None) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary and stores them in the parameters.
        It also handles special cases that need to be handled after a value has been read in and checked.
        If you choose to subclass this master class, you can also choose to override this method (or not), and if you do
        Deal with all the parameter values that the user has provided.  They should really only provide values that
        they want to change from the default values, but they can provide a value that is already set because it is a
        default value set in __init__.  It will ignore those.
        This also deals with all the special cases that need to be taken care of after a value has been read in
        and checked.
        If you choose to subclass this master class, you can also choose to override this method (or not),
        and if you do, do it before or after you call you own version of this method.  If you do, you can also choose
        to call this method from you class, which can effectively modify all these superclass parameters in your class.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :param default_output_path: Relative path for non-absolute output path parameters
        :type default_output_path: pathlib.Path
        :return: None
        """
        model.logger.info(f'Init {__class__!s}: {__name__}')
        if len(model.InputParameters) > 0:
            # loop through all the parameters that the user wishes to set, looking for parameters that match this object
            for item in self.ParameterDict.items():
                ParameterToModify = item[1]
                key = ParameterToModify.Name.strip()
                if key in model.InputParameters:
                    ParameterReadIn = model.InputParameters[key]

                    if key in self.filepath_parameter_names:
                        if not Path(ParameterReadIn.sValue).is_absolute() and default_output_path is not None:
                            original_val = ParameterReadIn.sValue
                            ParameterReadIn.sValue = str(
                                default_output_path.joinpath(Path(ParameterReadIn.sValue)).absolute())
                            model.logger.info(f'Adjusted {key} path to {ParameterReadIn.sValue} because original value '
                                              f'({original_val}) was not an absolute path.')

                    # this should handle all the non-special cases
                    ReadParameter(ParameterReadIn, ParameterToModify, model)

        # handle the special cases
        if len(model.InputParameters) > 0:
            # if the user wants it, we need to know if the user wants to copy the contents of the
            # output file to the screen - this serves as the screen report
            if 'Print Output to Console' in model.InputParameters:
                ParameterReadIn = model.InputParameters['Print Output to Console']
                if ParameterReadIn.sValue == '0':
                    self.printoutput = False

            # loop through all the parameters that the user wishes to set, looking for parameters that contain the
            # prefix "Units:" - that means we want to set a special case for converting this
            # output parameter to new units
            for key in model.InputParameters.keys():
                if key.startswith('Units:'):
                    self.ParameterDict[key.replace('Units:', '')] = LookupUnits(model.InputParameters[key].sValue)[0]

        model.logger.info(f'Complete {__class__!s}: {__name__}')

    def _convert_units(self, model: Model):
        # Deal with converting Units back to PreferredUnits, if required.
        # before we write the outputs, we go thru all the parameters for all of the objects and set the values back
        # to the units that the user entered the data in
        # We do this because the value may be displayed in the output, and we want the user to recginze their value,
        # not some converted value
        for obj in [model.reserv, model.wellbores, model.surfaceplant, model.economics]:
            for key in obj.ParameterDict:
                param = obj.ParameterDict[key]
                if not param.UnitsMatch:
                    ConvertUnitsBack(param, model)

        # now we need to loop through all the output parameters to update their units to
        # whatever units the user has specified.
        # i.e., they may have specified that all LENGTH results must be in feet, so we need to convert those
        # from whatever LENGTH unit they are to feet.
        # same for all the other classes of units (TEMPERATURE, DENSITY, etc).

        for obj in [model.reserv, model.wellbores, model.surfaceplant, model.economics]:
            for key in obj.OutputParameterDict:
                output_param:OutputParameter = obj.OutputParameterDict[key]
                if key in self.ParameterDict:
                    if self.ParameterDict[key] != output_param.CurrentUnits:
                        ConvertOutputUnits(output_param, self.ParameterDict[key], model)
                elif not output_param.UnitsMatch:
                    obj.OutputParameterDict[key] = output_param.with_preferred_units()

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
            with open(self.output_file, 'w', encoding='UTF-8') as f:

                econ: Economics = model.economics

                f.write('                               *****************\n')
                f.write('                               ***CASE REPORT***\n')
                f.write('                               *****************\n')
                f.write(NL)
                f.write('Simulation Metadata\n')
                f.write('----------------------\n')
                f.write(f' GEOPHIRES Version: {geophires_x.__version__}\n')
                f.write(' Simulation Date: '+ datetime.datetime.now().strftime('%Y-%m-%d\n'))
                f.write(' Simulation Time:  '+ datetime.datetime.now().strftime('%H:%M\n'))
                f.write(' Calculation Time: '+'{0:10.3f}'.format((time.time()-model.tic)) + ' sec\n')

                f.write(NL)
                f.write('                           ***SUMMARY OF RESULTS***\n')
                f.write(NL)
                f.write('      End-Use Option: ' + str(model.surfaceplant.enduse_option.value.value) + NL)
                if model.surfaceplant.plant_type.value in [PlantType.ABSORPTION_CHILLER, PlantType.HEAT_PUMP, PlantType.DISTRICT_HEATING]:
                    f.write('      Surface Application: ' + str(model.surfaceplant.plant_type.value.value) + NL)
                if model.surfaceplant.enduse_option.value in [EndUseOptions.ELECTRICITY, EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT, EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]: # there is an electricity component
                    f.write(f'      Average Net Electricity Production:               {np.average(model.surfaceplant.NetElectricityProduced.value):10.2f} ' + model.surfaceplant.NetElectricityProduced.CurrentUnits.value + NL)
                if model.surfaceplant.enduse_option.value is not EndUseOptions.ELECTRICITY:    # there is a direct-use component
                    f.write(f'      Average Direct-Use Heat Production:               {np.average(model.surfaceplant.HeatProduced.value):10.2f} '+ model.surfaceplant.HeatProduced.CurrentUnits.value + NL)
                if model.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
                    f.write(f'      Annual District Heating Demand:                   {np.average(model.surfaceplant.annual_heating_demand.value):10.2f} ' + model.surfaceplant.annual_heating_demand.CurrentUnits.value + NL)
                    f.write(f'      Average Annual Geothermal Heat Production:        {sum(model.surfaceplant.dh_geothermal_heating.value * 24) / model.surfaceplant.plant_lifetime.value / 1e3:10.2f} ' + model.surfaceplant.annual_heating_demand.CurrentUnits.value + NL)
                    f.write(f'      Average Annual Peaking Fuel Heat Production:      {sum(model.surfaceplant.dh_natural_gas_heating.value * 24) / model.surfaceplant.plant_lifetime.value / 1e3:10.2f} ' + model.surfaceplant.annual_heating_demand.CurrentUnits.value + NL)
                if model.surfaceplant.plant_type.value == PlantType.ABSORPTION_CHILLER:
                    f.write(f'      Average Cooling Production:                       {np.average(model.surfaceplant.cooling_produced.value):10.2f} ' + model.surfaceplant.cooling_produced.CurrentUnits.value + NL)

                if model.surfaceplant.enduse_option.value in [EndUseOptions.ELECTRICITY]:
                    f.write(f'      Electricity breakeven price:                      {model.economics.LCOE.value:10.2f} ' + model.economics.LCOE.CurrentUnits.value + NL)
                elif model.surfaceplant.enduse_option.value in [EndUseOptions.HEAT] and \
                    model.surfaceplant.plant_type.value not in [PlantType.ABSORPTION_CHILLER]:
                    f.write(f'      Direct-Use heat breakeven price (LCOH):            {model.economics.LCOH.value:10.2f} ' + model.economics.LCOH.CurrentUnits.value + NL)
                elif model.surfaceplant.enduse_option.value in [EndUseOptions.HEAT] and model.surfaceplant.plant_type.value == PlantType.ABSORPTION_CHILLER:
                    f.write(f'      Direct-Use Cooling Breakeven Price (LCOC):         {model.economics.LCOC.value:10.2f} ' + model.economics.LCOC.CurrentUnits.value + NL)
                elif model.surfaceplant.enduse_option.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT,
                                                              EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                              EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT,
                                                              EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY,
                                                              EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY,
                                                              EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]:
                    f.write(f'      Electricity breakeven price:                      {model.economics.LCOE.value:10.2f} ' + model.economics.LCOE.CurrentUnits.value + NL)
                    f.write(f'      Direct-Use heat breakeven price (LCOH):           {model.economics.LCOH.value:10.2f} ' + model.economics.LCOH.CurrentUnits.value + NL)

                f.write(f'      Number of production wells:                    {model.wellbores.nprod.value:10.0f}'+NL)
                f.write(f'      Number of injection wells:                     {model.wellbores.ninj.value:10.0f}'+NL)
                f.write(f'      Flowrate per production well:                    {model.wellbores.prodwellflowrate.value:10.1f} '  + model.wellbores.prodwellflowrate.CurrentUnits.value + NL)
                f.write(f'      {Outputs._field_label(Outputs.VERTICAL_WELL_DEPTH_OUTPUT_NAME, 49)}{model.reserv.depth.value:10.1f} ' + model.reserv.depth.CurrentUnits.value + NL)

                if model.reserv.numseg.value == 1:
                    f.write(f'      Geothermal gradient:                             {model.reserv.gradient.value[0]:10.4g} ' + model.reserv.gradient.CurrentUnits.value + NL)
                else:
                    for i in range(1, model.reserv.numseg.value):
                        f.write(f'      Segment {str(i):s}   Geothermal gradient:                    {model.reserv.gradient.value[i-1]:10.4g} ' + model.reserv.gradient.CurrentUnits.value +NL)
                        f.write(f'      Segment {str(i):s}   Thickness:                         {round(model.reserv.layerthickness.value[i-1], 10)} {model.reserv.layerthickness.CurrentUnits.value}\n')
                    f.write(f'      Segment {str(i+1):s}   Geothermal gradient:                    {model.reserv.gradient.value[i]:10.4g} ' + model.reserv.gradient.CurrentUnits.value + NL)
                if model.economics.DoCarbonCalculations.value:
                    f.write(f'      Total Avoided Carbon Emissions:                       {model.economics.CarbonThatWouldHaveBeenProducedTotal.value:10.2f} '
                            f'{model.economics.CarbonThatWouldHaveBeenProducedTotal.CurrentUnits.value}\n')

                f.write(NL)
                f.write(NL)
                f.write('                           ***ECONOMIC PARAMETERS***\n')
                f.write(NL)
                if model.economics.econmodel.value == EconomicModel.FCR:
                    f.write('      Economic Model = ' + model.economics.econmodel.value.value + NL)
                    f.write(f'      Fixed Charge Rate (FCR):                          {model.economics.FCR.value*100.0:10.2f} ' + model.economics.FCR.CurrentUnits.value + NL)
                elif model.economics.econmodel.value == EconomicModel.STANDARDIZED_LEVELIZED_COST:
                    f.write('      Economic Model = ' + model.economics.econmodel.value.value + NL)
                    f.write(f'      {model.economics.interest_rate.Name}:                                    {model.economics.interest_rate.value:10.2f} {model.economics.interest_rate.CurrentUnits.value}\n')

                elif model.economics.econmodel.value == EconomicModel.BICYCLE:
                    f.write('      Economic Model  = ' + model.economics.econmodel.value.value + NL)
                f.write(f'      Accrued financing during construction:            {model.economics.inflrateconstruction.value*100:10.2f} ' + model.economics.inflrateconstruction.CurrentUnits.value + NL)
                f.write(f'      Project lifetime:                              {model.surfaceplant.plant_lifetime.value:10.0f} ' + model.surfaceplant.plant_lifetime.CurrentUnits.value + NL)
                f.write(f'      Capacity factor:                                 {model.surfaceplant.utilization_factor.value * 100:10.1f} %' + NL)

                e_npv = model.economics.ProjectNPV
                npv_field_label = Outputs._field_label('Project NPV', 49)
                # TODO should use CurrentUnits instead of PreferredUnits
                f.write(f'      {npv_field_label}{e_npv.value:10.2f} {e_npv.PreferredUnits.value}\n')

                f.write(f'      Project IRR:                                     {model.economics.ProjectIRR.value:10.2f} ' + model.economics.ProjectIRR.PreferredUnits.value + NL)
                f.write(f'      Project VIR=PI=PIR:                              {model.economics.ProjectVIR.value:10.2f}' + NL)
                f.write(f'      {model.economics.ProjectMOIC.Name}:                                    {model.economics.ProjectMOIC.value:10.2f}' + NL)

                payback_period_val = model.economics.ProjectPaybackPeriod.value
                project_payback_period_display = f'{payback_period_val:10.2f} {model.economics.ProjectPaybackPeriod.PreferredUnits.value}' \
                    if payback_period_val > 0.0 else 'N/A'
                f.write(f'      Project Payback Period:                          {project_payback_period_display}\n')

                if model.surfaceplant.enduse_option.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT,
                                                              EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                              EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT,
                                                              EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY,
                                                              EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY,
                                                              EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]:
                    f.write(f'      CHP: Percent cost allocation for electrical plant: {model.economics.CAPEX_heat_electricity_plant_ratio.value*100.0:10.2f} %\n')

                if model.surfaceplant.enduse_option.value in [EndUseOptions.ELECTRICITY]:
                    f.write(f'      Estimated Jobs Created:                                 {model.economics.jobs_created.value}\n')


                f.write(NL)
                f.write('                          ***ENGINEERING PARAMETERS***\n')
                f.write(NL)
                f.write(f'      Number of Production Wells:                    {model.wellbores.nprod.value:10.0f}' + NL)
                f.write(f'      Number of Injection Wells:                     {model.wellbores.ninj.value:10.0f}' + NL)
                f.write(f'      {Outputs._field_label(Outputs.VERTICAL_WELL_DEPTH_OUTPUT_NAME, 49)}{model.reserv.depth.value:10.1f} ' + model.reserv.depth.CurrentUnits.value + NL)
                f.write(f'      Water loss rate:                                 {model.reserv.waterloss.value*100:10.1f} ' + model.reserv.waterloss.CurrentUnits.value + NL)
                f.write(f'      Pump efficiency:                                 {model.surfaceplant.pump_efficiency.value:10.1f} ' + model.surfaceplant.pump_efficiency.CurrentUnits.value + NL)
                f.write(f'      Injection temperature:                           {model.wellbores.Tinj.value:10.1f} ' + model.wellbores.Tinj.CurrentUnits.value + NL)
                if model.wellbores.rameyoptionprod.value:
                    f.write('      Production Wellbore heat transmission calculated with Ramey\'s model\n')
                    f.write(f'      Average production well temperature drop:        {np.average(model.wellbores.ProdTempDrop.value):10.1f} ' + model.wellbores.ProdTempDrop.PreferredUnits.value + NL)
                else:
                    f.write('      User-provided production well temperature drop\n')
                    f.write(f'      Constant production well temperature drop:       {model.wellbores.tempdropprod.value:10.1f} ' + model.wellbores.tempdropprod.PreferredUnits.value + NL)
                f.write(f'      Flowrate per production well:                    {model.wellbores.prodwellflowrate.value:10.1f} ' + model.wellbores.prodwellflowrate.CurrentUnits.value + NL)
                f.write(f'      Injection well casing ID:                          {model.wellbores.injwelldiam.value:10.3f} ' + model.wellbores.injwelldiam.CurrentUnits.value + NL)
                f.write(f'      Production well casing ID:                         {model.wellbores.prodwelldiam.value:10.3f} ' + model.wellbores.prodwelldiam.CurrentUnits.value + NL)
                f.write(f'      Number of times redrilling:                    {model.wellbores.redrill.value:10.0f}'+NL)
                if model.surfaceplant.enduse_option.value in [EndUseOptions.ELECTRICITY, EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT, EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]:
                    f.write('      Power plant type:                                       ' + str(model.surfaceplant.plant_type.value.value) + NL)
                f.write(NL)
                f.write(NL)
                f.write('                         ***RESOURCE CHARACTERISTICS***\n')
                f.write(NL)
                f.write(f'      Maximum reservoir temperature:                   {model.reserv.Tmax.value:10.1f} ' + model.reserv.Tmax.CurrentUnits.value + NL)
                f.write(f'      Number of segments:                            {model.reserv.numseg.value:10.0f} ' + NL)
                if model.reserv.numseg.value == 1:
                    f.write(f'      Geothermal gradient:                                {model.reserv.gradient.value[0]:10.4g} ' + model.reserv.gradient.CurrentUnits.value + NL)
                else:
                    for i in range(1, model.reserv.numseg.value):
                        f.write(f'      Segment {str(i):s}   Geothermal gradient:                    {model.reserv.gradient.value[i-1]:10.4g} ' + model.reserv.gradient.CurrentUnits.value +NL)
                        f.write(f'      Segment {str(i):s}   Thickness:                         {round(model.reserv.layerthickness.value[i-1], 10)} {model.reserv.layerthickness.CurrentUnits.value}\n')
                    f.write(f'      Segment {str(i+1):s}   Geothermal gradient:                    {model.reserv.gradient.value[i]:10.4g} ' + model.reserv.gradient.CurrentUnits.value + NL)

                f.write(NL)
                f.write(NL)
                f.write('                           ***RESERVOIR PARAMETERS***\n')
                f.write(NL)
                if model.wellbores.IsAGS.value:
                    f.write('The AGS models contain an intrinsic reservoir model that doesn\'t expose values that can be used in extensive reporting.' + NL)
                else:
                    f.write('      Reservoir Model = ' + str(model.reserv.resoption.value.value) + ' Model\n')
                    if model.reserv.resoption.value is ReservoirModel.SINGLE_FRACTURE:
                        f.write(f'      m/A Drawdown Parameter:                                 {model.reserv.drawdp.value:.5f} ' + model.reserv.drawdp.CurrentUnits.value + NL)
                    elif model.reserv.resoption.value is ReservoirModel.ANNUAL_PERCENTAGE:
                        f.write(f'      Annual Thermal Drawdown:                                {model.reserv.drawdp.value*100:.3f} ' + model.reserv.drawdp.CurrentUnits.value + NL)
                    f.write(f'      Bottom-hole temperature:                          {model.reserv.Trock.value:10.2f} ' + model.reserv.Trock.CurrentUnits.value +  NL)
                    if model.reserv.resoption.value in [ReservoirModel.ANNUAL_PERCENTAGE, ReservoirModel.USER_PROVIDED_PROFILE, ReservoirModel.TOUGH2_SIMULATOR]:
                        f.write('      Warning: the reservoir dimensions and thermo-physical properties \n')
                        f.write('               listed below are default values if not provided by the user.   \n')
                        f.write('               They are only used for calculating remaining heat content.  \n')

                    if model.reserv.resoption.value in [ReservoirModel.MULTIPLE_PARALLEL_FRACTURES, ReservoirModel.LINEAR_HEAT_SWEEP]:
                        f.write('      Fracture model = ' + model.reserv.fracshape.value.value + NL)
                        if model.reserv.fracshape.value == FractureShape.CIRCULAR_AREA:
                            f.write(f'      Well separation: fracture diameter:               {model.reserv.fracheightcalc.value:10.2f} ' + model.reserv.fracheight.CurrentUnits.value + NL)
                        elif model.reserv.fracshape.value == FractureShape.CIRCULAR_DIAMETER:
                            f.write(f'      Well separation: fracture diameter:               {model.reserv.fracheightcalc.value:10.2f} ' + model.reserv.fracheight.CurrentUnits.value + NL)
                        elif model.reserv.fracshape.value == FractureShape.SQUARE:
                            f.write(f'      Well separation: fracture height:                 {model.reserv.fracheightcalc.value:10.2f} ' + model.reserv.fracheight.CurrentUnits.value + NL)
                        elif model.reserv.fracshape.value == FractureShape.RECTANGULAR:
                            f.write(f'      Well separation: fracture height:                 {model.reserv.fracheightcalc.value:10.2f} ' + model.reserv.fracheight.CurrentUnits.value + NL)
                            f.write(f'      Fracture width:                                             {model.reserv.fracwidthcalc.value:10.2f} ' + model.reserv.fracwidth.CurrentUnits.value + NL)
                        f.write(f'      Fracture area:                                    {model.reserv.fracareacalc.value:10.2f} ' + model.reserv.fracarea.CurrentUnits.value + NL)
                    if model.reserv.resvoloption.value == ReservoirVolume.FRAC_NUM_SEP:
                        f.write('      Reservoir volume calculated with fracture separation and number of fractures as input\n')
                    elif model.reserv.resvoloption.value == ReservoirVolume.RES_VOL_FRAC_SEP:
                        f.write('      Number of fractures calculated with reservoir volume and fracture separation as input\n')
                    elif model.reserv.resvoloption.value == ReservoirVolume.FRAC_NUM_SEP:
                        f.write('      Fracture separation calculated with reservoir volume and number of fractures as input\n')
                    elif model.reserv.resvoloption.value == ReservoirVolume.RES_VOL_ONLY:
                        f.write('      Reservoir volume provided as input\n')
                    if model.reserv.resvoloption.value in [ReservoirVolume.FRAC_NUM_SEP, ReservoirVolume.RES_VOL_FRAC_SEP,ReservoirVolume.FRAC_NUM_SEP]:
                        f.write(f'      Number of fractures:                              {model.reserv.fracnumbcalc.value:10.2f}' + NL)
                        f.write(f'      Fracture separation:                              {model.reserv.fracsepcalc.value:10.2f} ' + model.reserv.fracsep.CurrentUnits.value + NL)
                    f.write(f'      Reservoir volume:                              {model.reserv.resvolcalc.value:10.0f} ' + model.reserv.resvol.CurrentUnits.value + NL)

                    if model.wellbores.impedancemodelused.value:
                        # See note re: unit conversion:
                        # https://github.com/NREL/GEOPHIRES-X/blob/d51eb8d1dc8b21c7a79c4d35f296d740347658e0/src/geophires_x/WellBores.py#L1280-L1282
                        f.write(f'      Reservoir impedance:                              {model.wellbores.impedance.value/1000:10.4f} {model.wellbores.impedance.CurrentUnits.value}\n')
                    else:
                        if model.wellbores.overpressure_percentage.Provided:
                            # write the reservoir pressure as an average in the overpressure case
                            f.write(f'      Average reservoir pressure:                       {model.wellbores.average_production_reservoir_pressure.value:10.2f} ' + model.wellbores.average_production_reservoir_pressure.CurrentUnits.value + NL)
                        else:
                            # write the reservoir pressure as a single value
                            f.write(f'      Reservoir hydrostatic pressure:                       {model.wellbores.production_reservoir_pressure.value[0]:10.2f} ' + model.wellbores.production_reservoir_pressure.CurrentUnits.value + NL)
                        f.write(f'      Plant outlet pressure:                            {model.surfaceplant.plant_outlet_pressure.value:10.2f} ' + model.surfaceplant.plant_outlet_pressure.CurrentUnits.value + NL)
                        if model.wellbores.productionwellpumping.value:
                            f.write(f'      Production wellhead pressure:                     {model.wellbores.Pprodwellhead.value:10.2f} ' + model.wellbores.Pprodwellhead.CurrentUnits.value + NL)
                            f.write(f'      Productivity Index:                               {model.wellbores.PI.value:10.2f} ' + model.wellbores.PI.CurrentUnits.value + NL)
                        f.write(f'      Injectivity Index:                                {model.wellbores.II.value:10.2f} ' + model.wellbores.II.CurrentUnits.value + NL)

                    f.write(f'      Reservoir density:                                {model.reserv.rhorock.value:10.2f} ' + model.reserv.rhorock.CurrentUnits.value + NL)
                    if model.wellbores.rameyoptionprod.value or model.reserv.resoption.value in [ReservoirModel.MULTIPLE_PARALLEL_FRACTURES, ReservoirModel.LINEAR_HEAT_SWEEP, ReservoirModel.SINGLE_FRACTURE, ReservoirModel.TOUGH2_SIMULATOR]:
                        f.write(f'      Reservoir thermal conductivity:                   {model.reserv.krock.value:10.2f} {model.reserv.krock.CurrentUnits.value}{NL}')
                    f.write(f'      Reservoir heat capacity:                          {model.reserv.cprock.value:10.2f} ' + model.reserv.cprock.CurrentUnits.value + NL)
                    if model.reserv.resoption.value is ReservoirModel.LINEAR_HEAT_SWEEP or (model.reserv.resoption.value is ReservoirModel.TOUGH2_SIMULATOR and model.reserv.usebuiltintough2model):
                        f.write(f'      Reservoir porosity:                               {model.reserv.porrock.value*100:10.2f} ' + model.reserv.porrock.CurrentUnits.value + NL)
                    if model.reserv.resoption.value is ReservoirModel.TOUGH2_SIMULATOR and model.reserv.usebuiltintough2model:
                        f.write(f'      Reservoir permeability:                           {model.reserv.permrock.value:10.2E} ' + model.reserv.permrock.CurrentUnits.value + NL)
                        f.write(f'      Reservoir thickness:                              {model.reserv.resthickness.value:10.2f} ' + model.reserv.resthickness.CurrentUnits.value + NL)
                        f.write(f'      Reservoir width:                                  {model.reserv.reswidth.value:10.2f} ' + model.reserv.reswidth.CurrentUnits.value + NL)
                        f.write(f'      Well separation:                                  {model.wellbores.wellsep.value:10.2f} ' + model.wellbores.wellsep.CurrentUnits.value + NL)

                f.write(NL)
                f.write(NL)
                f.write('                           ***RESERVOIR SIMULATION RESULTS***' + NL)
                f.write(NL)
                f.write(f'      Maximum Production Temperature:                  {np.max(model.wellbores.ProducedTemperature.value):10.1f} ' + model.wellbores.ProducedTemperature.PreferredUnits.value + NL)
                f.write(f'      Average Production Temperature:                  {np.average(model.wellbores.ProducedTemperature.value):10.1f} ' + model.wellbores.ProducedTemperature.PreferredUnits.value + NL)
                f.write(f'      Minimum Production Temperature:                  {np.min(model.wellbores.ProducedTemperature.value):10.1f} ' + model.wellbores.ProducedTemperature.PreferredUnits.value + NL)
                f.write(f'      Initial Production Temperature:                  {model.wellbores.ProducedTemperature.value[0]:10.1f} ' + model.wellbores.ProducedTemperature.PreferredUnits.value + NL)
                if model.wellbores.IsAGS.value:
                    f.write('The AGS models contain an intrinsic reservoir model that doesn\'t expose values that can be used in extensive reporting.' + NL)
                else:
                    f.write(f'      Average Reservoir Heat Extraction:                {np.average(model.surfaceplant.HeatExtracted.value):10.2f} ' + model.surfaceplant.HeatExtracted.PreferredUnits.value + NL)
                    if model.wellbores.rameyoptionprod.value:
                        f.write('      Production Wellbore Heat Transmission Model = Ramey Model' + NL)
                        f.write(f'      Average Production Well Temperature Drop:        {np.average(model.wellbores.ProdTempDrop.value):10.1f} ' + model.wellbores.ProdTempDrop.PreferredUnits.value + NL)
                    else:
                        f.write(f'      Wellbore Heat Transmission Model = Constant Temperature Drop:{model.wellbores.tempdropprod.value:10.1f} ' + model.wellbores.tempdropprod.PreferredUnits.value + NL)
                    if model.wellbores.impedancemodelused.value:
                        f.write(f'      Total Average Pressure Drop:                     {np.average(model.wellbores.DPOverall.value):10.1f} ' + model.wellbores.DPOverall.PreferredUnits.value + NL)
                        f.write(f'      Average Injection Well Pressure Drop:            {np.average(model.wellbores.DPInjWell.value):10.1f} ' + model.wellbores.DPInjWell.PreferredUnits.value + NL)
                        f.write(f'      Average Reservoir Pressure Drop:                 {np.average(model.wellbores.DPReserv.value):10.1f} ' + model.wellbores.DPReserv.PreferredUnits.value + NL)
                        f.write(f'      Average Production Well Pressure Drop:           {np.average(model.wellbores.DPProdWell.value):10.1f} ' + model.wellbores.DPProdWell.PreferredUnits.value + NL)
                        f.write(f'      Average Buoyancy Pressure Drop:                  {np.average(model.wellbores.DPBouyancy.value):10.1f} ' + model.wellbores.DPBouyancy.PreferredUnits.value + NL)
                    else:
                        f.write(f'      Average Injection Well Pump Pressure Drop:       {np.average(model.wellbores.DPInjWell.value):10.1f} ' + model.wellbores.DPInjWell.PreferredUnits.value + NL)
                        if model.wellbores.productionwellpumping.value:
                            f.write(f'      Average Production Well Pump Pressure Drop:      {np.average(model.wellbores.DPProdWell.value):10.1f} ' + model.wellbores.DPProdWell.PreferredUnits.value + NL)

                f.write(NL)
                f.write(NL)
                f.write('                          ***CAPITAL COSTS (M$)***\n')
                f.write(NL)
                if not model.economics.totalcapcost.Valid:
                    f.write(f'         Drilling and completion costs:                 {model.economics.Cwell.value:10.2f} ' + model.economics.Cwell.CurrentUnits.value + NL)
                    if econ.cost_lateral_section.value > 0.0:
                        f.write(f'             Drilling and completion costs per vertical production well:   {econ.cost_one_production_well.value:10.2f} ' + econ.cost_one_production_well.CurrentUnits.value + NL)
                        f.write(f'             Drilling and completion costs per vertical injection well:    {econ.cost_one_injection_well.value:10.2f} ' + econ.cost_one_injection_well.CurrentUnits.value + NL)
                        f.write(f'             {econ.cost_per_lateral_section.Name}:       {econ.cost_per_lateral_section.value:10.2f} {econ.cost_lateral_section.CurrentUnits.value}\n')
                    elif round(econ.cost_one_production_well.value, 4) != round(econ.cost_one_injection_well.value, 4) and \
                            model.economics.cost_one_injection_well.value != -1:
                        f.write(f'             Drilling and completion costs per production well:   {econ.cost_one_production_well.value:10.2f} ' + econ.cost_one_production_well.CurrentUnits.value + NL)
                        f.write(f'             Drilling and completion costs per injection well:    {econ.cost_one_injection_well.value:10.2f} ' + econ.cost_one_injection_well.CurrentUnits.value + NL)
                    else:
                        f.write(f'         Drilling and completion costs per well:        {model.economics.Cwell.value/(model.wellbores.nprod.value+model.wellbores.ninj.value):10.2f} ' + model.economics.Cwell.CurrentUnits.value + NL)
                    f.write(f'         Stimulation costs:                             {model.economics.Cstim.value:10.2f} ' + model.economics.Cstim.CurrentUnits.value + NL)
                    f.write(f'         Surface power plant costs:                     {model.economics.Cplant.value:10.2f} ' + model.economics.Cplant.CurrentUnits.value + NL)
                    if model.surfaceplant.plant_type.value == PlantType.ABSORPTION_CHILLER:
                        f.write(f'            of which Absorption Chiller Cost:           {model.economics.chillercapex.value:10.2f} ' + model.economics.Cplant.CurrentUnits.value + NL)
                    if model.surfaceplant.plant_type.value == PlantType.HEAT_PUMP:
                        f.write(f'            of which Heat Pump Cost:                    {model.economics.heatpumpcapex.value:10.2f} ' + model.economics.Cplant.CurrentUnits.value + NL)
                    if model.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
                        f.write(f'            of which Peaking Boiler Cost:               {model.economics.peakingboilercost.value:10.2f} ' + model.economics.peakingboilercost.CurrentUnits.value + NL)
                    f.write(f'         Field gathering system costs:                  {model.economics.Cgath.value:10.2f} ' + model.economics.Cgath.CurrentUnits.value + NL)
                    if model.surfaceplant.piping_length.value > 0:
                        f.write(f'         Transmission pipeline cost:                    {model.economics.Cpiping.value:10.2f} ' + model.economics.Cpiping.CurrentUnits.value + NL)
                    if model.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
                        f.write(f'         District Heating System Cost:                  {model.economics.dhdistrictcost.value:10.2f} ' + model.economics.dhdistrictcost.CurrentUnits.value + NL)
                    f.write(f'         Total surface equipment costs:                 {(model.economics.Cplant.value+model.economics.Cgath.value):10.2f} ' + model.economics.Cplant.CurrentUnits.value + NL)
                    f.write(f'         Exploration costs:                             {model.economics.Cexpl.value:10.2f} ' + model.economics.Cexpl.CurrentUnits.value + NL)
                if model.economics.totalcapcost.Valid and model.wellbores.redrill.value > 0:
                    f.write(f'         Drilling and completion costs (for redrilling):{model.economics.Cwell.value:10.2f} ' + model.economics.Cwell.CurrentUnits.value + NL)
                    f.write(f'      Drilling and completion costs per redrilled well: {(model.economics.Cwell.value/(model.wellbores.nprod.value+model.wellbores.ninj.value)):10.2f} ' + model.economics.Cwell.CurrentUnits.value + NL)
                    f.write(f'         Stimulation costs (for redrilling):            {model.economics.Cstim.value:10.2f} ' + model.economics.Cstim.CurrentUnits.value + NL)
                if model.economics.RITCValue.value:
                    f.write(f'         Investment Tax Credit:                         {-1*model.economics.RITCValue.value:10.2f} ' + model.economics.RITCValue.CurrentUnits.value + NL)
                f.write(f'      Total capital costs:                              {model.economics.CCap.value:10.2f} ' + model.economics.CCap.CurrentUnits.value + NL)
                if model.economics.econmodel.value == EconomicModel.FCR:
                    f.write(f'      Annualized capital costs:                         {(model.economics.CCap.value*(1+model.economics.inflrateconstruction.value)*model.economics.FCR.value):10.2f} ' + model.economics.CCap.CurrentUnits.value + NL)

                f.write(NL)
                f.write(NL)
                f.write('                ***OPERATING AND MAINTENANCE COSTS (M$/yr)***\n')
                f.write(NL)
                if not model.economics.oamtotalfixed.Valid:
                    f.write(f'         Wellfield maintenance costs:                   {model.economics.Coamwell.value:10.2f} ' + model.economics.Coamwell.CurrentUnits.value + NL)
                    f.write(f'         Power plant maintenance costs:                 {model.economics.Coamplant.value:10.2f} ' + model.economics.Coamplant.CurrentUnits.value + NL)
                    f.write(f'         Water costs:                                   {model.economics.Coamwater.value:10.2f} ' + model.economics.Coamwater.CurrentUnits.value + NL)
                    if model.surfaceplant.plant_type.value in [PlantType.INDUSTRIAL, PlantType.ABSORPTION_CHILLER, PlantType.HEAT_PUMP, PlantType.DISTRICT_HEATING]:
                        f.write(f'         Average Reservoir Pumping Cost:                {model.economics.averageannualpumpingcosts.value:10.2f} ' + model.economics.averageannualpumpingcosts.CurrentUnits.value + NL)
                    if model.surfaceplant.plant_type.value ==  PlantType.ABSORPTION_CHILLER:
                        f.write(f'         Absorption Chiller O&M Cost:                   {model.economics.chilleropex.value:10.2f} ' + model.economics.chilleropex.CurrentUnits.value + NL)
                    if model.surfaceplant.plant_type.value ==  PlantType.HEAT_PUMP:
                        f.write(f'         Average Heat Pump Electricity Cost:            {model.economics.averageannualheatpumpelectricitycost.value:10.2f} ' + model.economics.averageannualheatpumpelectricitycost.CurrentUnits.value + NL)
                    if model.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
                        f.write(f'         Annual District Heating O&M Cost:              {model.economics.dhdistrictoandmcost.value:10.2f} ' + model.economics.dhdistrictoandmcost.CurrentUnits.value + NL)
                        f.write(f'         Average Annual Peaking Fuel Cost:              {model.economics.averageannualngcost.value:10.2f} ' + model.economics.averageannualngcost.CurrentUnits.value + NL)

                    f.write(f'      Total operating and maintenance costs:            {(model.economics.Coam.value + model.economics.averageannualpumpingcosts.value+model.economics.averageannualheatpumpelectricitycost.value):10.2f} ' + model.economics.Coam.CurrentUnits.value + NL)
                else:
                    f.write(f'      Total operating and maintenance costs:            {model.economics.Coam.value:10.2f} ' + model.economics.Coam.CurrentUnits.value + NL)

                f.write(NL)
                f.write(NL)
                f.write('                           ***SURFACE EQUIPMENT SIMULATION RESULTS***\n')
                f.write(NL)
                if model.surfaceplant.enduse_option.value in [EndUseOptions.ELECTRICITY, EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT, EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]: # there is an electricity componenent:
                    f.write(f'      Initial geofluid availability:                    {model.surfaceplant.Availability.value[0]:10.2f} ' + model.surfaceplant.Availability.PreferredUnits.value + NL)
                    f.write(f'      Maximum Total Electricity Generation:             {np.max(model.surfaceplant.ElectricityProduced.value):10.2f} ' + model.surfaceplant.ElectricityProduced.PreferredUnits.value + NL)
                    f.write(f'      Average Total Electricity Generation:             {np.average(model.surfaceplant.ElectricityProduced.value):10.2f} ' + model.surfaceplant.ElectricityProduced.PreferredUnits.value + NL)
                    f.write(f'      Minimum Total Electricity Generation:             {np.min(model.surfaceplant.ElectricityProduced.value):10.2f} ' + model.surfaceplant.ElectricityProduced.PreferredUnits.value + NL)
                    f.write(f'      Initial Total Electricity Generation:             {model.surfaceplant.ElectricityProduced.value[0]:10.2f} ' + model.surfaceplant.ElectricityProduced.PreferredUnits.value + NL)
                    f.write(f'      Maximum Net Electricity Generation:               {np.max(model.surfaceplant.NetElectricityProduced.value):10.2f} ' + model.surfaceplant.NetElectricityProduced.PreferredUnits.value + NL)
                    f.write(f'      Average Net Electricity Generation:               {np.average(model.surfaceplant.NetElectricityProduced.value):10.2f} ' + model.surfaceplant.NetElectricityProduced.PreferredUnits.value + NL)
                    f.write(f'      Minimum Net Electricity Generation:               {np.min(model.surfaceplant.NetElectricityProduced.value):10.2f} ' + model.surfaceplant.NetElectricityProduced.PreferredUnits.value + NL)
                    f.write(f'      Initial Net Electricity Generation:               {model.surfaceplant.NetElectricityProduced.value[0]:10.2f} ' + model.surfaceplant.NetElectricityProduced.PreferredUnits.value + NL)
                    f.write(f'      Average Annual Total Electricity Generation:      {np.average(model.surfaceplant.TotalkWhProduced.value/1E6):10.2f} GWh' + NL)
                    f.write(f'      Average Annual Net Electricity Generation:        {np.average(model.surfaceplant.NetkWhProduced.value/1E6):10.2f} GWh' + NL)

                    if model.wellbores.PumpingPower.value[0] > 0.0:
                        ipp_nip = model.wellbores.PumpingPower.value[0] / model.surfaceplant.NetElectricityProduced.value[0]
                        f.write(f'      Initial pumping power/net installed power:        {(ipp_nip*100):10.2f} %\n')

                if model.surfaceplant.enduse_option.value in [EndUseOptions.HEAT, PlantType.ABSORPTION_CHILLER, PlantType.HEAT_PUMP, EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT, EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]: # geothermal heating component:
                    f.write(f'      Maximum Net Heat Production:                      {np.max(model.surfaceplant.HeatProduced.value):10.2f} ' + model.surfaceplant.HeatProduced.PreferredUnits.value + NL)
                    f.write(f'      Average Net Heat Production:                      {np.average(model.surfaceplant.HeatProduced.value):10.2f} ' + model.surfaceplant.HeatProduced.PreferredUnits.value + NL)
                    f.write(f'      Minimum Net Heat Production:                      {np.min(model.surfaceplant.HeatProduced.value):10.2f} ' + model.surfaceplant.HeatProduced.PreferredUnits.value + NL)
                    f.write(f'      Initial Net Heat Production:                      {model.surfaceplant.HeatProduced.value[0]:10.2f} ' + model.surfaceplant.HeatProduced.PreferredUnits.value + NL)
                    f.write(f'      Average Annual Heat Production:                   {np.average(model.surfaceplant.HeatkWhProduced.value/1E6):10.2f} GWh' + NL)

                if model.surfaceplant.plant_type.value == PlantType.HEAT_PUMP:
                    f.write(f'      Average Annual Heat Pump Electricity Use:         {np.average(model.surfaceplant.heat_pump_electricity_kwh_used.value / 1E6):10.2f} ' + 'GWh/year' + NL)
                if model.surfaceplant.plant_type.value == PlantType.ABSORPTION_CHILLER:
                    f.write(f'      Maximum Cooling Production:                       {np.max(model.surfaceplant.cooling_produced.value):10.2f} ' + model.surfaceplant.cooling_produced.PreferredUnits.value + NL)
                    f.write(f'      Average Cooling Production:                       {np.average(model.surfaceplant.cooling_produced.value):10.2f} ' + model.surfaceplant.cooling_produced.PreferredUnits.value + NL)
                    f.write(f'      Minimum Cooling Production:                       {np.min(model.surfaceplant.cooling_produced.value):10.2f} ' + model.surfaceplant.cooling_produced.PreferredUnits.value + NL)
                    f.write(f'      Initial Cooling Production:                       {model.surfaceplant.cooling_produced.value[0]:10.2f} ' + model.surfaceplant.cooling_produced.PreferredUnits.value + NL)
                    f.write(f'      Average Annual Cooling Production:                {np.average(model.surfaceplant.cooling_kWh_Produced.value / 1E6):10.2f} ' + 'GWh/year' + NL)

                if model.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
                    f.write(f'      Annual District Heating Demand:                   {model.surfaceplant.annual_heating_demand.value:10.2f} ' + model.surfaceplant.annual_heating_demand.PreferredUnits.value + NL)
                    f.write(f'      Maximum Daily District Heating Demand:            {np.max(model.surfaceplant.daily_heating_demand.value):10.2f} ' + model.surfaceplant.daily_heating_demand.PreferredUnits.value + NL)
                    f.write(f'      Average Daily District Heating Demand:            {np.average(model.surfaceplant.daily_heating_demand.value):10.2f} ' + model.surfaceplant.daily_heating_demand.PreferredUnits.value + NL)
                    f.write(f'      Minimum Daily District Heating Demand:            {np.min(model.surfaceplant.daily_heating_demand.value):10.2f} ' + model.surfaceplant.daily_heating_demand.PreferredUnits.value + NL)
                    f.write(f'      Maximum Geothermal Heating Production:            {np.max(model.surfaceplant.dh_geothermal_heating.value):10.2f} ' + model.surfaceplant.dh_geothermal_heating.PreferredUnits.value + NL)
                    f.write(f'      Average Geothermal Heating Production:            {np.average(model.surfaceplant.dh_geothermal_heating.value):10.2f} ' + model.surfaceplant.dh_geothermal_heating.PreferredUnits.value + NL)
                    f.write(f'      Minimum Geothermal Heating Production:            {np.min(model.surfaceplant.dh_geothermal_heating.value):10.2f} ' + model.surfaceplant.dh_geothermal_heating.PreferredUnits.value + NL)
                    f.write(f'      Maximum Peaking Boiler Heat Production:           {np.max(model.surfaceplant.dh_natural_gas_heating.value):10.2f} ' + model.surfaceplant.dh_natural_gas_heating.PreferredUnits.value + NL)
                    f.write(f'      Average Peaking Boiler Heat Production:           {np.average(model.surfaceplant.dh_natural_gas_heating.value):10.2f} ' + model.surfaceplant.dh_natural_gas_heating.PreferredUnits.value + NL)
                    f.write(f'      Minimum Peaking Boiler Heat Production:           {np.min(model.surfaceplant.dh_natural_gas_heating.value):10.2f} ' + model.surfaceplant.dh_natural_gas_heating.PreferredUnits.value + NL)

                f.write(f'      Average Pumping Power:                            {np.average(model.wellbores.PumpingPower.value):10.2f} {model.wellbores.PumpingPower.CurrentUnits.value}{NL}')

                if model.surfaceplant.heat_to_power_conversion_efficiency.value is not None:
                    hpce = model.surfaceplant.heat_to_power_conversion_efficiency
                    f.write(f'      {Outputs._field_label(hpce.Name, 50)}'
                            f'{hpce.value:10.2f} {model.surfaceplant.heat_to_power_conversion_efficiency.CurrentUnits.value}\n')

                f.write(NL)
                f.write('                            ************************************************************\n')
                f.write('                            *  HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE  *\n')
                f.write('                            ************************************************************\n')
                if model.surfaceplant.enduse_option.value == EndUseOptions.ELECTRICITY: # only electricity
                    f.write('  YEAR       THERMAL               GEOFLUID               PUMP               NET               FIRST LAW\n')
                    f.write('             DRAWDOWN             TEMPERATURE             POWER             POWER              EFFICIENCY\n')
                    f.write('                                     (' + model.wellbores.ProducedTemperature.CurrentUnits.value+')               (' + model.wellbores.PumpingPower.CurrentUnits.value + ')              (' + model.surfaceplant.NetElectricityProduced.CurrentUnits.value + ')                  (%)\n')
                    for i in range(0, model.surfaceplant.plant_lifetime.value):
                        f.write('  {0:2.0f}         {1:8.4f}              {2:8.2f}             {3:8.4f}          {4:8.4f}              {5:8.4f}'.format(i+1,
                                                model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value]/model.wellbores.ProducedTemperature.value[0],
                                                                        model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value],
                                                                                                        model.wellbores.PumpingPower.value[i*model.economics.timestepsperyear.value],
                                                                                                                            model.surfaceplant.NetElectricityProduced.value[i*model.economics.timestepsperyear.value],
                                                                                                                                                        model.surfaceplant.FirstLawEfficiency.value[i*model.economics.timestepsperyear.value]*100)+NL)
                elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value not in [PlantType.HEAT_PUMP, PlantType.DISTRICT_HEATING, PlantType.ABSORPTION_CHILLER]: # only direct-use
                    f.write('  YEAR       THERMAL               GEOFLUID               PUMP               NET\n')
                    f.write('             DRAWDOWN             TEMPERATURE             POWER              HEAT\n')
                    f.write('                                   (deg C)                (MW)               (MW)\n')
                    for i in range(0, model.surfaceplant.plant_lifetime.value):
                        f.write('  {0:2.0f}         {1:8.4f}              {2:8.2f}             {3:8.4f}          {4:8.4f}'.format(i,
                                                model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value]/model.wellbores.ProducedTemperature.value[0],
                                                                        model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value],
                                                                                                        model.wellbores.PumpingPower.value[i*model.economics.timestepsperyear.value],
                                                                                                                                model.surfaceplant.HeatProduced.value[i*model.economics.timestepsperyear.value])+NL)

                elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value in [PlantType.HEAT_PUMP]: # heat pump
                    f.write('  YEAR         THERMAL              GEOFLUID               PUMP               NET             HEAT PUMP\n')
                    f.write('               DRAWDOWN            TEMPERATURE             POWER              HEAT         ELECTRICITY USE\n')
                    f.write('                                    (deg C)                (MWe)              (MWt)             (MWe)\n')
                    for i in range(0, model.surfaceplant.plant_lifetime.value):
                        f.write('  {0:2.0f}          {1:8.4f}             {2:8.2f}              {3:8.4f}           {4:8.4f}          {5:8.4f}'.format(i,
                                                                                                                                                      model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value] / model.wellbores.ProducedTemperature.value[0],
                                                                                                                                                      model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value],
                                                                                                                                                      model.wellbores.PumpingPower.value[i*model.economics.timestepsperyear.value],
                                                                                                                                                      model.surfaceplant.HeatProduced.value[i*model.economics.timestepsperyear.value], model.surfaceplant.heat_pump_electricity_used.value[i * model.economics.timestepsperyear.value]) + NL)

                elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value in [PlantType.DISTRICT_HEATING]: # district heating
                    f.write('  YEAR         THERMAL              GEOFLUID               PUMP              GEOTHERMAL\n')
                    f.write('               DRAWDOWN            TEMPERATURE             POWER            HEAT OUTPUT\n')
                    f.write('                                    (deg C)                (MWe)               (MWt)\n')
                    for i in range(0, model.surfaceplant.plant_lifetime.value):
                        f.write('  {0:2.0f}          {1:8.4f}             {2:8.2f}              {3:8.4f}            {4:8.4f}'.format(i,
                                                model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value]/model.wellbores.ProducedTemperature.value[0],
                                                                        model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value],
                                                                                                        model.wellbores.PumpingPower.value[i*model.economics.timestepsperyear.value],
                                                                                                                                model.surfaceplant.HeatProduced.value[i*model.economics.timestepsperyear.value])+NL)

                elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and model.surfaceplant.plant_type.value in [PlantType.ABSORPTION_CHILLER]: # absorption chiller
                    f.write('  YEAR         THERMAL              GEOFLUID               PUMP               NET              NET\n')
                    f.write('               DRAWDOWN            TEMPERATURE             POWER              HEAT             COOLING\n')
                    f.write('                                    (deg C)                (MWe)              (MWt)            (MWt)\n')
                    for i in range(0, model.surfaceplant.plant_lifetime.value):
                        f.write('  {0:2.0f}          {1:8.4f}             {2:8.2f}              {3:8.4f}           {4:8.4f}         {5:8.4f}'.format(i,
                                                                                                                                                     model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value] / model.wellbores.ProducedTemperature.value[0],
                                                                                                                                                     model.wellbores.ProducedTemperature.value[i*model.economics.timestepsperyear.value],
                                                                                                                                                     model.wellbores.PumpingPower.value[i*model.economics.timestepsperyear.value],
                                                                                                                                                     model.surfaceplant.HeatProduced.value[i*model.economics.timestepsperyear.value], model.surfaceplant.cooling_produced.value[i * model.economics.timestepsperyear.value], ) + NL)

                elif model.surfaceplant.enduse_option.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT, EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]:  # co-gen
                    f.write('  YEAR     THERMAL             GEOFLUID             PUMP             NET              NET             FIRST LAW\n')
                    f.write('           DRAWDOWN           TEMPERATURE           POWER           POWER             HEAT            EFFICIENCY\n')
                    f.write('                                (deg C)             (MW)            (MW)              (MW)               (%)\n')
                    for i in range(0, model.surfaceplant.plant_lifetime.value):
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
                if model.surfaceplant.enduse_option.value == EndUseOptions.ELECTRICITY:  # only electricity
                    f.write('  YEAR             ELECTRICITY                   HEAT                RESERVOIR            PERCENTAGE OF\n')
                    f.write('                    PROVIDED                   EXTRACTED            HEAT CONTENT        TOTAL HEAT MINED\n')
                    f.write('                   (GWh/year)                  (GWh/year)            (10^15 J)                 (%)\n')
                    for i in range(0, model.surfaceplant.plant_lifetime.value):
                        f.write('  {0:2.0f}              {1:8.1f}                    {2:8.1f}              {3:8.2f}               {4:8.2f}'.format(i+1,
                                                model.surfaceplant.NetkWhProduced.value[i]/1E6,
                                                                            model.surfaceplant.HeatkWhExtracted.value[i]/1E6,
                                                                                                    model.surfaceplant.RemainingReservoirHeatContent.value[i],
                                                                                                                            (model.reserv.InitialReservoirHeatContent.value-model.surfaceplant.RemainingReservoirHeatContent.value[i])*100/model.reserv.InitialReservoirHeatContent.value)+NL)
                elif model.surfaceplant.plant_type.value == PlantType.ABSORPTION_CHILLER: # absorption chiller
                    f.write('  YEAR              COOLING                 HEAT                RESERVOIR            PERCENTAGE OF\n')
                    f.write('                    PROVIDED              EXTRACTED            HEAT CONTENT        TOTAL HEAT MINED\n')
                    f.write('                   (GWh/year)             (GWh/year)            (10^15 J)                 (%)\n')
                    for i in range(0, model.surfaceplant.plant_lifetime.value):
                        f.write('  {0:2.0f}              {1:8.1f}               {2:8.1f}              {3:8.2f}               {4:8.2f}'.format(i + 1,
                                                                                                                                              model.surfaceplant.cooling_kWh_Produced.value[i] / 1E6,
                                                                                                                                              model.surfaceplant.HeatkWhExtracted.value[i] / 1E6,
                                                                                                                                              model.surfaceplant.RemainingReservoirHeatContent.value[i],
                                                                                                                                              (model.reserv.InitialReservoirHeatContent.value-model.surfaceplant.RemainingReservoirHeatContent.value[i]) * 100 / model.reserv.InitialReservoirHeatContent.value)+NL)

                elif model.surfaceplant.plant_type.value == PlantType.HEAT_PUMP: # heat pump
                    f.write('  YEAR              HEATING             RESERVOIR HEAT          HEAT PUMP          RESERVOIR           PERCENTAGE OF\n')
                    f.write('                    PROVIDED              EXTRACTED          ELECTRICITY USE      HEAT CONTENT        TOTAL HEAT MINED\n')
                    f.write('                   (GWh/year)             (GWh/year)           (GWh/year)           (10^15 J)                (%)\n')
                    for i in range(0, model.surfaceplant.plant_lifetime.value):
                        f.write('  {0:2.0f}              {1:8.1f}               {2:8.1f}             {3:8.2f}             {4:8.2f}              {5:8.2f}'.format(i + 1,
                                                                                                                                                                 model.surfaceplant.HeatkWhProduced.value[i] / 1E6,
                                                                                                                                                                 model.surfaceplant.HeatkWhExtracted.value[i] / 1E6, model.surfaceplant.heat_pump_electricity_kwh_used.value[i] / 1E6,
                                                                                                                                                                 model.surfaceplant.RemainingReservoirHeatContent.value[i],
                                                                                                                                                                 (model.reserv.InitialReservoirHeatContent.value-model.surfaceplant.RemainingReservoirHeatContent.value[i]) * 100 / model.reserv.InitialReservoirHeatContent.value)+NL)

                elif model.surfaceplant.enduse_option.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT, EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY, EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT, EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]: #co-gen
                    f.write('  YEAR             HEAT                 ELECTRICITY                HEAT              RESERVOIR        PERCENTAGE OF\n')
                    f.write('                  PROVIDED               PROVIDED                EXTRACTED          HEAT CONTENT    TOTAL HEAT MINED\n')
                    f.write('                 (GWh/year)             (GWh/year)               (GWh/year)          (10^15 J)           (%)\n')
                    for i in range(0, model.surfaceplant.plant_lifetime.value):
                        f.write('  {0:2.0f}            {1:8.1f}               {2:8.1f}                  {3:8.2f}            {4:8.2f}             {5:8.2f}'.format(i+1,
                                            model.surfaceplant.HeatkWhProduced.value[i]/1E6,
                                                                        model.surfaceplant.NetkWhProduced.value[i]/1E6,
                                                                                                    model.surfaceplant.HeatkWhExtracted.value[i]/1E6,
                                                                                                                            model.surfaceplant.RemainingReservoirHeatContent.value[i],
                                                                                                                                                (model.reserv.InitialReservoirHeatContent.value-model.surfaceplant.RemainingReservoirHeatContent.value[i])*100/model.reserv.InitialReservoirHeatContent.value)+NL)

                elif model.surfaceplant.plant_type.value in [PlantType.DISTRICT_HEATING]: # district-heating
                    f.write('  YEAR           GEOTHERMAL          PEAKING BOILER       RESERVOIR HEAT          RESERVOIR         PERCENTAGE OF\n')
                    f.write('              HEATING PROVIDED      HEATING PROVIDED        EXTRACTED            HEAT CONTENT     TOTAL HEAT MINED\n')
                    f.write('                 (GWh/year)            (GWh/year)           (GWh/year)            (10^15 J)              (%)\n')
                    for i in range(0, model.surfaceplant.plant_lifetime.value):
                        f.write('  {0:2.0f}            {1:8.1f}              {2:8.1f}              {3:8.2f}             {4:8.2f}            {5:8.2f}'.format(i + 1,
                                                                                                                                                             model.surfaceplant.HeatkWhProduced.value[i] / 1E6,
                                                                                                                                                             model.surfaceplant.annual_ng_demand.value[i] / 1E3,
                                                                                                                                                             model.surfaceplant.HeatkWhExtracted.value[i] / 1E6,
                                                                                                                                                             model.surfaceplant.RemainingReservoirHeatContent.value[i],
                                                                                                                                                             (model.reserv.InitialReservoirHeatContent.value-model.surfaceplant.RemainingReservoirHeatContent.value[i]) * 100 / model.reserv.InitialReservoirHeatContent.value)+NL)
                elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT: # only direct-use
                    f.write('  YEAR               HEAT                       HEAT                RESERVOIR            PERCENTAGE OF\n')
                    f.write('                    PROVIDED                   EXTRACTED            HEAT CONTENT        TOTAL HEAT MINED\n')
                    f.write('                   (GWh/year)                  (GWh/year)            (10^15 J)                 (%)\n')
                    for i in range(0, model.surfaceplant.plant_lifetime.value):
                        f.write('  {0:2.0f}              {1:8.1f}                    {2:8.1f}              {3:8.2f}               {4:8.2f}'.format(i+1,
                                                model.surfaceplant.HeatkWhProduced.value[i]/1E6,
                                                                            model.surfaceplant.HeatkWhExtracted.value[i]/1E6,
                                                                                                    model.surfaceplant.RemainingReservoirHeatContent.value[i],
                                                                                                                            (model.reserv.InitialReservoirHeatContent.value-model.surfaceplant.RemainingReservoirHeatContent.value[i])*100/model.reserv.InitialReservoirHeatContent.value)+NL)

                f.write(NL)
                f.write(NL)
                f.write('                             ********************************\n')
                f.write('                             *  REVENUE & CASHFLOW PROFILE  *\n')
                f.write('                             ********************************\n')
                f.write(
                    'Year            Electricity             |            Heat                  |           Cooling                 |         Carbon                    |          Project' + NL)
                f.write(
                    'Since     Price   Ann. Rev.  Cumm. Rev. |   Price   Ann. Rev.   Cumm. Rev. |  Price   Ann. Rev.   Cumm. Rev.   |   Price   Ann. Rev.   Cumm. Rev.  | OPEX    Net Rev.      Net Cashflow' + NL)

                def o(output_param: OutputParameter):
                    # TODO generalize this and/or FIXME make it unnecessary
                    if output_param.Name in econ.OutputParameterDict:
                        return econ.OutputParameterDict[output_param.Name]
                    else:
                        return output_param

                f.write('Start    ('
                        + o(econ.ElecPrice).CurrentUnits.value +
                        ')(' + o(econ.ElecRevenue).CurrentUnits.value +
                        ') (' + o(econ.ElecCummRevenue).CurrentUnits.value +
                        ')    |(' + o(econ.HeatPrice).CurrentUnits.value +
                        ') (' + o(econ.HeatRevenue).CurrentUnits.value +
                        ')    (' + o(econ.HeatCummRevenue).CurrentUnits.value +
                        ')   |(' + o(econ.CoolingPrice).CurrentUnits.value +
                        ') (' + o(econ.CoolingRevenue).CurrentUnits.value +
                        ')    (' + o(econ.CoolingCummRevenue).CurrentUnits.value +
                        ')    |(' + o(econ.CarbonPrice).CurrentUnits.value +
                        ')    (' + o(econ.CarbonRevenue).CurrentUnits.value +
                        ')    (' + o(econ.CarbonCummCashFlow).CurrentUnits.value +
                        ')    |(' + o(econ.Coam).CurrentUnits.value +
                        ') (' + o(econ.TotalRevenue).CurrentUnits.value +
                        ')    (' + o(econ.TotalCummRevenue).CurrentUnits.value + ')\n')
                f.write(
                    '________________________________________________________________________________________________________________________________________________________________________________________' + NL)
                # running years...
                for ii in range(0, (
                    model.surfaceplant.construction_years.value + model.surfaceplant.plant_lifetime.value), 1):
                    if ii < model.surfaceplant.construction_years.value:
                        opex = 0.0   # zero out the OPEX during construction years
                    else:
                        opex = o(econ.Coam).value
                    f.write(
                        f'{ii:3.0f}     {o(econ.ElecPrice).value[ii]:5.2f}          {o(econ.ElecRevenue).value[ii]:5.2f}  {o(econ.ElecCummRevenue).value[ii]:5.2f}     |   {o(econ.HeatPrice).value[ii]:5.2f}    {o(econ.HeatRevenue).value[ii]:5.2f}        {o(econ.HeatCummRevenue).value[ii]:5.2f}    |   {o(econ.CoolingPrice).value[ii]:5.2f}    {o(econ.CoolingRevenue).value[ii]:5.2f}        {o(econ.CoolingCummRevenue).value[ii]:5.2f}     |   {o(econ.CarbonPrice).value[ii]:5.2f}    {o(econ.CarbonRevenue).value[ii]:5.2f}        {o(econ.CarbonCummCashFlow).value[ii]:5.2f}     | {opex:5.2f}     {o(econ.TotalRevenue).value[ii]:5.2f}     {o(econ.TotalCummRevenue).value[ii]:5.2f}\n')
                f.write(NL)

                # if we are dealing with overpressure and two different reservoirs, show a table reporting the values
                if model.wellbores.overpressure_percentage.Provided:
                    f.write(NL)
                    f.write('                            ***************************************\n')
                    f.write('                            *  RESERVOIR POWER REQUIRED PROFILES  *\n')
                    f.write('                            ***************************************\n')
                    f.write('  YEAR     PROD PUMP     INJECT PUMP     TOTAL PUMP\n')
                    f.write('             POWER          POWER           POWER\n')
                    f.write('             (' + model.wellbores.PumpingPowerProd.CurrentUnits.value+')           (' + model.wellbores.PumpingPowerInj.CurrentUnits.value + ')            (' + model.surfaceplant.NetElectricityProduced.CurrentUnits.value + ')                  \n')
                    for i in range(0, model.surfaceplant.plant_lifetime.value):
                        f.write('  {0:2.0f}     {1:8.4f}        {2:8.4f}       {3:8.4f}'.format(i+1,
                            model.wellbores.PumpingPowerProd.value[i*model.economics.timestepsperyear.value],
                            model.wellbores.PumpingPowerInj.value[i*model.economics.timestepsperyear.value],
                            model.wellbores.PumpingPower.value[i*model.economics.timestepsperyear.value]))
                        f.write(NL)
                    f.write(NL)\

        except BaseException as ex:
            tb = sys.exc_info()[2]
            msg = 'Error: GEOPHIRES Failed to write the output file. Exiting....Line %i' % tb.tb_lineno
            print(str(ex))
            print(msg)
            model.logger.critical(str(ex))
            model.logger.critical(msg)
            raise RuntimeError(msg) from ex

        Outputs.print_outputs_rich(self.output_file, self.text_output_file, self.html_output_file, model)

        model.logger.info(f'Complete {__class__!s}: {sys._getframe().f_code.co_name}')


    @staticmethod
    def print_outputs_rich(output_file: str, text_output_file: strParameter, html_output_file: strParameter, model: Model):

        # data structures and assignments for HTML and Improved Text Output formats
        simulation_metadata = []
        summary = []
        economic_parameters = []
        engineering_parameters = []
        resource_characteristics = []
        reservoir_parameters = []
        reservoir_stimulation_results = []
        CAPEX = []
        OPEX = []
        surface_equipment_results = []
        addon_results = []
        sdac_resa_results = []
        pumping_power_results = []

        simulation_metadata.append(OutputTableItem('GEOPHIRES Version', geophires_x.__version__))
        simulation_metadata.append(OutputTableItem('Simulation Date', datetime.datetime.now().strftime('%Y-%m-%d')))
        simulation_metadata.append(OutputTableItem('Simulation Time', datetime.datetime.now().strftime('%H:%M')))
        simulation_metadata.append(
            OutputTableItem('Calculation Time', '{0:10.3f}'.format((time.time() - model.tic)) + ' sec'))

        summary.append(OutputTableItem('End-Use Option', str(model.surfaceplant.enduse_option.value.value)))

        if model.surfaceplant.enduse_option.value in [EndUseOptions.ELECTRICITY,
                                                      EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT,
                                                      EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY,
                                                      EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY,
                                                      EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                      EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT,
                                                      EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]:  # there is an electricity component
            summary.append(OutputTableItem('Average Net Electricity Production', '{0:10.2f}'.format(
                np.average(model.surfaceplant.NetElectricityProduced.value)),
                                           model.surfaceplant.NetElectricityProduced.CurrentUnits.value))
        if model.surfaceplant.enduse_option.value is not EndUseOptions.ELECTRICITY:  # there is a direct-use component
            summary.append(OutputTableItem('Average Direct-Use Heat Production',
                                           '{0:10.2f}'.format(np.average(model.surfaceplant.HeatProduced.value)),
                                           model.surfaceplant.HeatProduced.CurrentUnits.value))
        if model.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
            summary.append(OutputTableItem('Annual District Heating Demand', '{0:10.2f}'.format(
                np.average(model.surfaceplant.annual_heating_demand.value)),
                                           model.surfaceplant.annual_heating_demand.CurrentUnits.value))
            summary.append(OutputTableItem('Average Annual Geothermal Heat Production', '{0:10.2f}'.format(
                sum(model.surfaceplant.dh_geothermal_heating.value * 24) / model.surfaceplant.plant_lifetime.value / 1e3),
                                           model.surfaceplant.annual_heating_demand.CurrentUnits.value))
            summary.append(OutputTableItem('Average Annual Peaking Fuel Heat Production', '{0:10.2f}'.format(
                sum(model.surfaceplant.dh_natural_gas_heating.value * 24) / model.surfaceplant.plant_lifetime.value / 1e3),
                                           model.surfaceplant.annual_heating_demand.CurrentUnits.value))
        if model.surfaceplant.plant_type.value == PlantType.ABSORPTION_CHILLER:
            summary.append(OutputTableItem('Average Cooling Production',
                                           '{0:10.2f}'.format(np.average(model.surfaceplant.cooling_produced.value)),
                                           model.surfaceplant.cooling_produced.CurrentUnits.value))

        if model.surfaceplant.enduse_option.value in [EndUseOptions.ELECTRICITY]:
            summary.append(
                OutputTableItem('Electricity breakeven price', '{0:10.2f}'.format(model.economics.LCOE.value),
                                model.economics.LCOE.CurrentUnits.value))
        elif model.surfaceplant.enduse_option.value in [EndUseOptions.HEAT] and model.surfaceplant.plant_type.value not in [PlantType.ABSORPTION_CHILLER]:
            summary.append(OutputTableItem('Direct-Use heat breakeven price (LCOH)',
                                           '{0:10.2f}'.format(model.economics.LCOH.value),
                                           model.economics.LCOH.CurrentUnits.value))
        elif (model.surfaceplant.enduse_option.value in [EndUseOptions.HEAT] and
              model.surfaceplant.plant_type.value == PlantType.ABSORPTION_CHILLER):
            summary.append(OutputTableItem('Direct-Use Cooling Breakeven Price (LCOC)',
                                           '{0:10.2f}'.format(model.economics.LCOC.value),
                                           model.economics.LCOC.CurrentUnits.value))
        elif model.surfaceplant.enduse_option.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT,
                                                        EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                        EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT,
                                                        EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY,
                                                        EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY,
                                                        EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]:
            summary.append(
                OutputTableItem('Electricity breakeven price', '{0:10.2f}'.format(model.economics.LCOE.value),
                                model.economics.LCOE.CurrentUnits.value))
            summary.append(OutputTableItem('Direct-Use heat breakeven price (LCOH)',
                                           '{0:10.2f}'.format(model.economics.LCOH.value),
                                           model.economics.LCOH.CurrentUnits.value))

        summary.append(OutputTableItem('Number of production wells', '{0:10.0f}'.format(model.wellbores.nprod.value)))
        summary.append(OutputTableItem('Number of injection wells', '{0:10.0f}'.format(model.wellbores.ninj.value)))
        summary.append(
            OutputTableItem('Flowrate per production well', '{0:10.1f}'.format(model.wellbores.prodwellflowrate.value),
                            model.wellbores.prodwellflowrate.CurrentUnits.value))
        summary.append(OutputTableItem(Outputs.VERTICAL_WELL_DEPTH_OUTPUT_NAME,
                                       '{0:10.1f}'.format(model.reserv.depth.value),
                                       model.reserv.depth.CurrentUnits.value))

        if model.reserv.numseg.value == 1:
            summary.append(OutputTableItem('Geothermal gradient', '{0:10.4g}'.format(model.reserv.gradient.value[0]),
                                           model.reserv.gradient.CurrentUnits.value))
        else:
            for i in range(1, model.reserv.numseg.value):
                summary.append(OutputTableItem(f'Segment {str(i)} Geothermal gradient',
                                               '{0:10.4g}'.format(model.reserv.gradient.value[i - 1]),
                                               model.reserv.gradient.CurrentUnits.value))
                summary.append(OutputTableItem(f'Segment {str(i)} Thickness',
                                               '{0:10.0f}'.format(model.reserv.layerthickness.value[i - 1]),
                                               model.reserv.layerthickness.CurrentUnits.value))
            summary.append(OutputTableItem(f'Segment {str(i + 1)} Geothermal gradient',
                                           '{0:10.4g}'.format(model.reserv.gradient.value[i]),
                                           model.reserv.gradient.CurrentUnits.value))

        if model.economics.DoCarbonCalculations.value:
            summary.append(OutputTableItem('Total Avoided Carbon Emissions', '{0:10.2f}'.format(
                model.economics.CarbonThatWouldHaveBeenProducedTotal.value),
                                           model.economics.CarbonThatWouldHaveBeenProducedTotal.CurrentUnits.value))

        if model.economics.econmodel.value == EconomicModel.FCR:
            economic_parameters.append(OutputTableItem('Economic Model', model.economics.econmodel.value.value))
            economic_parameters.append(
                OutputTableItem('Fixed Charge Rate (FCR)', '{0:10.2f}'.format(model.economics.FCR.value * 100.0),
                                model.economics.FCR.CurrentUnits.value))
        elif model.economics.econmodel.value == EconomicModel.STANDARDIZED_LEVELIZED_COST:
            economic_parameters.append(OutputTableItem('Economic Model', model.economics.econmodel.value.value))
            economic_parameters.append(
                OutputTableItem('Interest Rate', '{0:10.2f}'.format(model.economics.discountrate.value * 100.0),
                                model.economics.discountrate.CurrentUnits.value))
        elif model.economics.econmodel.value == EconomicModel.BICYCLE:
            economic_parameters.append(OutputTableItem('Economic Model', model.economics.econmodel.value.value))
        economic_parameters.append(OutputTableItem('Accrued financing during construction',
                                                   '{0:10.2f}'.format(model.economics.inflrateconstruction.value * 100),
                                                   model.economics.inflrateconstruction.CurrentUnits.value))
        economic_parameters.append(
            OutputTableItem('Project lifetime', '{0:10.0f}'.format(model.surfaceplant.plant_lifetime.value),
                            model.surfaceplant.plant_lifetime.CurrentUnits.value))
        economic_parameters.append(
            OutputTableItem('Capacity factor', '{0:10.1f}'.format(model.surfaceplant.utilization_factor.value * 100),
                            '%'))
        economic_parameters.append(OutputTableItem('Project NPV', '{0:10.2f}'.format(model.economics.ProjectNPV.value),
                                                   model.economics.ProjectNPV.PreferredUnits.value))
        economic_parameters.append(OutputTableItem('Project IRR', '{0:10.2f}'.format(model.economics.ProjectIRR.value),
                                                   model.economics.ProjectIRR.PreferredUnits.value))
        economic_parameters.append(
            OutputTableItem('Project VIR=PI=PIR', '{0:10.2f}'.format(model.economics.ProjectVIR.value)))
        economic_parameters.append(
            OutputTableItem('Project MOIC', '{0:10.2f}'.format(model.economics.ProjectMOIC.value)))

        payback_period_val = model.economics.ProjectPaybackPeriod.value
        project_payback_period_display = f'{payback_period_val:10.2f} {model.economics.ProjectPaybackPeriod.PreferredUnits.value}' \
            if payback_period_val > 0.0 else 'N/A'
        economic_parameters.append(OutputTableItem('Project Payback Period', project_payback_period_display))

        if model.surfaceplant.enduse_option.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT,
                                                      EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                      EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT,
                                                      EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY,
                                                      EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY,
                                                      EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]:
            economic_parameters.append(OutputTableItem('CHP: Percent cost allocation for electrical plant',
                                                       '{0:10.2f}'.format(
                                                           model.economics.CAPEX_heat_electricity_plant_ratio.value * 100.0),
                                                       '%'))

        engineering_parameters.append(
            OutputTableItem('Number of Production Wells', '{0:10.0f}'.format(model.wellbores.nprod.value)))
        engineering_parameters.append(
            OutputTableItem('Number of Injection Wells', '{0:10.0f}'.format(model.wellbores.ninj.value)))
        engineering_parameters.append(OutputTableItem(Outputs.VERTICAL_WELL_DEPTH_OUTPUT_NAME,
                                                      '{0:10.1f}'.format(model.reserv.depth.value),
                                                      model.reserv.depth.CurrentUnits.value))
        engineering_parameters.append(
            OutputTableItem('Water loss rate', '{0:10.1f}'.format(model.reserv.waterloss.value * 100),
                            model.reserv.waterloss.CurrentUnits.value))
        engineering_parameters.append(
            OutputTableItem('Pump efficiency', '{0:10.1f}'.format(model.surfaceplant.pump_efficiency.value * 100),
                            model.surfaceplant.pump_efficiency.CurrentUnits.value))
        engineering_parameters.append(
            OutputTableItem('Injection temperature', '{0:10.1f}'.format(model.wellbores.Tinj.value),
                            model.wellbores.Tinj.CurrentUnits.value))
        if model.wellbores.rameyoptionprod.value:
            engineering_parameters.append(
                OutputTableItem('Production Wellbore heat transmission calculated with Rameys model'))
            engineering_parameters.append(OutputTableItem('Average production well temperature drop',
                                                          '{0:10.1f}'.format(
                                                              np.average(model.wellbores.ProdTempDrop.value)),
                                                          model.wellbores.ProdTempDrop.PreferredUnits.value))
        else:
            engineering_parameters.append(OutputTableItem('User-provided production well temperature drop'))
            engineering_parameters.append(OutputTableItem('Constant production well temperature drop',
                                                          '{0:10.1f}'.format(model.wellbores.tempdropprod.value),
                                                          model.wellbores.tempdropprod.PreferredUnits.value))
        engineering_parameters.append(
            OutputTableItem('Flowrate per production well', '{0:10.1f}'.format(model.wellbores.prodwellflowrate.value),
                            model.wellbores.prodwellflowrate.CurrentUnits.value))
        engineering_parameters.append(
            OutputTableItem('Injection well casing ID', '{0:10.3f}'.format(model.wellbores.injwelldiam.value),
                            model.wellbores.injwelldiam.CurrentUnits.value))
        engineering_parameters.append(
            OutputTableItem('Production well casing ID', '{0:10.3f}'.format(model.wellbores.prodwelldiam.value),
                            model.wellbores.prodwelldiam.CurrentUnits.value))
        engineering_parameters.append(
            OutputTableItem('Number of times redrilling', '{0:10.0f}'.format(model.wellbores.redrill.value)))
        if model.surfaceplant.enduse_option.value in [EndUseOptions.ELECTRICITY,
                                                      EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT,
                                                      EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY,
                                                      EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY,
                                                      EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                      EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT,
                                                      EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]:
            engineering_parameters.append(
                OutputTableItem('Power plant type', model.surfaceplant.plant_type.value.value))

            resource_characteristics.append(
                OutputTableItem('Maximum reservoir temperature', '{0:10.1f}'.format(model.reserv.Tmax.value),
                                model.reserv.Tmax.CurrentUnits.value))
            resource_characteristics.append(
                OutputTableItem('Number of segments', '{0:10.0f}'.format(model.reserv.numseg.value)))
            if model.reserv.numseg.value == 1:
                resource_characteristics.append(
                    OutputTableItem('Geothermal gradient', '{0:10.4g}'.format(model.reserv.gradient.value[0]),
                                    model.reserv.gradient.CurrentUnits.value))
            else:
                for i in range(1, model.reserv.numseg.value):
                    resource_characteristics.append(OutputTableItem(f'Segment {str(i)} Geothermal gradient',
                                                                    '{0:10.4g}'.format(
                                                                        model.reserv.gradient.value[i - 1]),
                                                                    model.reserv.gradient.CurrentUnits.value))
                    resource_characteristics.append(OutputTableItem(f'Segment {str(i)} Thickness', '{0:10.0f}'.format(
                        model.reserv.layerthickness.value[i - 1]), model.reserv.layerthickness.CurrentUnits.value))
                resource_characteristics.append(OutputTableItem(f'Segment {str(i + 1)} Geothermal gradient',
                                                                '{0:10.4g}'.format(model.reserv.gradient.value[i]),
                                                                model.reserv.gradient.CurrentUnits.value))
        if model.wellbores.IsAGS.value:
            reservoir_parameters.append(
                OutputTableItem('The AGS models contain an intrinsic reservoir model that doesn\'t expose values that can be used in extensive reporting.'))
        else:
            reservoir_parameters.append(
                OutputTableItem('Reservoir Model', str(model.reserv.resoption.value.value) + ' Model'))
            if model.reserv.resoption.value is ReservoirModel.SINGLE_FRACTURE:
                reservoir_parameters.append(
                    OutputTableItem('m/A Drawdown Parameter', '{0:.5f}'.format(model.reserv.drawdp.value),
                                    model.reserv.drawdp.CurrentUnits.value))
            elif model.reserv.resoption.value is ReservoirModel.ANNUAL_PERCENTAGE:
                reservoir_parameters.append(
                    OutputTableItem('Annual Thermal Drawdown', '{0:.3f}'.format(model.reserv.drawdp.value * 100),
                                    model.reserv.drawdp.CurrentUnits.value))
            reservoir_parameters.append(
                OutputTableItem('Bottom-hole temperature', '{0:10.2f}'.format(model.reserv.Trock.value),
                                model.reserv.Trock.CurrentUnits.value))
            if model.reserv.resoption.value in [ReservoirModel.ANNUAL_PERCENTAGE, ReservoirModel.USER_PROVIDED_PROFILE,
                                                ReservoirModel.TOUGH2_SIMULATOR]:
                reservoir_parameters.append(
                    OutputTableItem('Warning: the reservoir dimensions and thermo-physical properties'))
                reservoir_parameters.append(
                    OutputTableItem('listed below are default values if not provided by the user.'))
                reservoir_parameters.append(
                    OutputTableItem('They are only used for calculating remaining heat content.'))

            if model.reserv.resoption.value in [ReservoirModel.MULTIPLE_PARALLEL_FRACTURES,
                                                ReservoirModel.LINEAR_HEAT_SWEEP]:
                reservoir_parameters.append(OutputTableItem('Fracture model', model.reserv.fracshape.value.value))
                if model.reserv.fracshape.value == FractureShape.CIRCULAR_AREA:
                    reservoir_parameters.append(OutputTableItem('Well separation: fracture diameter',
                                                                '{0:10.2f}'.format(model.reserv.fracheightcalc.value),
                                                                model.reserv.fracheight.CurrentUnits.value))
                elif model.reserv.fracshape.value == FractureShape.CIRCULAR_DIAMETER:
                    reservoir_parameters.append(OutputTableItem('Well separation: fracture diameter',
                                                                '{0:10.2f}'.format(model.reserv.fracheightcalc.value),
                                                                model.reserv.fracheight.CurrentUnits.value))
                elif model.reserv.fracshape.value == FractureShape.SQUARE:
                    reservoir_parameters.append(OutputTableItem('Well separation: fracture height',
                                                                '{0:10.2f}'.format(model.reserv.fracheightcalc.value),
                                                                model.reserv.fracheight.CurrentUnits.value))
                elif model.reserv.fracshape.value == FractureShape.RECTANGULAR:
                    reservoir_parameters.append(OutputTableItem('Well separation: fracture height',
                                                                '{0:10.2f}'.format(model.reserv.fracheightcalc.value),
                                                                model.reserv.fracheight.CurrentUnits.value))
                    reservoir_parameters.append(
                        OutputTableItem('Fracture width', '{0:10.2f}'.format(model.reserv.fracwidthcalc.value),
                                        model.reserv.fracwidth.CurrentUnits.value))
                reservoir_parameters.append(
                    OutputTableItem('Fracture area', '{0:10.2f}'.format(model.reserv.fracareacalc.value),
                                    model.reserv.fracarea.CurrentUnits.value))
            if model.reserv.resvoloption.value == ReservoirVolume.FRAC_NUM_SEP:
                reservoir_parameters.append(
                    OutputTableItem('Reservoir volume calculated with fracture separation and number of fractures as input'))
            elif model.reserv.resvoloption.value == ReservoirVolume.RES_VOL_FRAC_SEP:
                reservoir_parameters.append(
                    OutputTableItem('Number of fractures calculated with reservoir volume and fracture separation as input'))
            elif model.reserv.resvoloption.value == ReservoirVolume.FRAC_NUM_SEP:
                reservoir_parameters.append(
                    OutputTableItem('Fracture separation calculated with reservoir volume and number of fractures as input'))
            elif model.reserv.resvoloption.value == ReservoirVolume.RES_VOL_ONLY:
                reservoir_parameters.append(OutputTableItem('Reservoir volume provided as input'))
            if model.reserv.resvoloption.value in [ReservoirVolume.FRAC_NUM_SEP, ReservoirVolume.RES_VOL_FRAC_SEP,
                                                   ReservoirVolume.FRAC_NUM_SEP]:
                reservoir_parameters.append(
                    OutputTableItem('Number of fractures', '{0:10.2f}'.format(model.reserv.fracnumbcalc.value)))
                reservoir_parameters.append(
                    OutputTableItem('Fracture separation', '{0:10.2f}'.format(model.reserv.fracsepcalc.value),
                                    model.reserv.fracsep.CurrentUnits.value))
            reservoir_parameters.append(
                OutputTableItem('Reservoir volume', '{0:10.0f}'.format(model.reserv.resvolcalc.value),
                                model.reserv.resvol.CurrentUnits.value))
            if model.wellbores.impedancemodelused.value:
                reservoir_parameters.append(
                    OutputTableItem('Reservoir impedance', '{0:10.2f}'.format(model.wellbores.impedance.value / 1000),
                                    model.wellbores.impedance.CurrentUnits.value))
            else:
                reservoir_parameters.append(OutputTableItem('Average reservoir pressure',
                                                            '{0:10.2f}'.format(model.wellbores.average_production_reservoir_pressure.value),
                                                            model.wellbores.average_production_reservoir_pressure.CurrentUnits.value))
                reservoir_parameters.append(OutputTableItem('Plant outlet pressure', '{0:10.2f}'.format(
                    model.surfaceplant.plant_outlet_pressure.value),
                                                            model.surfaceplant.plant_outlet_pressure.CurrentUnits.value))
                if model.wellbores.productionwellpumping.value:
                    reservoir_parameters.append(OutputTableItem('Production wellhead pressure',
                                                                '{0:10.2f}'.format(model.wellbores.Pprodwellhead.value),
                                                                model.wellbores.Pprodwellhead.CurrentUnits.value))
                    reservoir_parameters.append(
                        OutputTableItem('Productivity Index', '{0:10.2f}'.format(model.wellbores.PI.value),
                                        model.wellbores.PI.CurrentUnits.value))
                reservoir_parameters.append(
                    OutputTableItem('Injectivity Index', '{0:10.2f}'.format(model.wellbores.II.value),
                                    model.wellbores.II.CurrentUnits.value))
            reservoir_parameters.append(
                OutputTableItem('Reservoir density', '{0:10.2f}'.format(model.reserv.rhorock.value),
                                model.reserv.rhorock.CurrentUnits.value))
            if model.wellbores.rameyoptionprod.value or model.reserv.resoption.value in [
                ReservoirModel.MULTIPLE_PARALLEL_FRACTURES, ReservoirModel.LINEAR_HEAT_SWEEP,
                ReservoirModel.SINGLE_FRACTURE, ReservoirModel.TOUGH2_SIMULATOR]:
                reservoir_parameters.append(
                    OutputTableItem('Reservoir thermal conductivity', '{0:10.2f}'.format(model.reserv.krock.value),
                                    model.reserv.krock.CurrentUnits.value))
            reservoir_parameters.append(
                OutputTableItem('Reservoir heat capacity', '{0:10.2f}'.format(model.reserv.cprock.value),
                                model.reserv.cprock.CurrentUnits.value))
            if model.reserv.resoption.value is ReservoirModel.LINEAR_HEAT_SWEEP or (
                model.reserv.resoption.value is ReservoirModel.TOUGH2_SIMULATOR and model.reserv.usebuiltintough2model):
                reservoir_parameters.append(
                    OutputTableItem('Reservoir porosity', '{0:10.2f}'.format(model.reserv.porrock.value * 100),
                                    model.reserv.porrock.CurrentUnits.value))
            if model.reserv.resoption.value is ReservoirModel.TOUGH2_SIMULATOR and model.reserv.usebuiltintough2model:
                reservoir_parameters.append(
                    OutputTableItem('Reservoir permeability', '{0:10.2E}'.format(model.reserv.permrock.value),
                                    model.reserv.permrock.CurrentUnits.value))
                reservoir_parameters.append(
                    OutputTableItem('Reservoir thickness', '{0:10.2f}'.format(model.reserv.resthickness.value),
                                    model.reserv.resthickness.CurrentUnits.value))
                reservoir_parameters.append(
                    OutputTableItem('Reservoir width', '{0:10.2f}'.format(model.reserv.reswidth.value),
                                    model.reserv.reswidth.CurrentUnits.value))
                reservoir_parameters.append(
                    OutputTableItem('Well separation', '{0:10.2f}'.format(model.wellbores.wellsep.value),
                                    model.wellbores.wellsep.CurrentUnits.value))

        reservoir_stimulation_results.append(OutputTableItem('Maximum Production Temperature', '{0:10.1f}'.format(
            np.max(model.wellbores.ProducedTemperature.value)), model.wellbores.ProducedTemperature.PreferredUnits.value))
        reservoir_stimulation_results.append(OutputTableItem('Average Production Temperature', '{0:10.1f}'.format(
            np.average(model.wellbores.ProducedTemperature.value)), model.wellbores.ProducedTemperature.PreferredUnits.value))
        reservoir_stimulation_results.append(OutputTableItem('Minimum Production Temperature', '{0:10.1f}'.format(
            np.min(model.wellbores.ProducedTemperature.value)), model.wellbores.ProducedTemperature.PreferredUnits.value))
        reservoir_stimulation_results.append(OutputTableItem('Initial Production Temperature', '{0:10.1f}'.format(
            model.wellbores.ProducedTemperature.value[0]), model.wellbores.ProducedTemperature.PreferredUnits.value))
        if model.wellbores.IsAGS.value:
            reservoir_stimulation_results.append(
                OutputTableItem('The AGS models contain an intrinsic reservoir model that doesn\'t expose values that can be used in extensive reporting.'))
        else:
            reservoir_stimulation_results.append(OutputTableItem('Average Reservoir Heat Extraction',
                                                                 '{0:10.2f}'.format(np.average(
                                                                     model.surfaceplant.HeatExtracted.value)),
                                                                 model.surfaceplant.HeatExtracted.PreferredUnits.value))
            if model.wellbores.rameyoptionprod.value:
                reservoir_stimulation_results.append(
                    OutputTableItem('Production Wellbore Heat Transmission Model', 'Ramey Model'))
                reservoir_stimulation_results.append(OutputTableItem('Average Production Well Temperature Drop',
                                                                     '{0:10.1f}'.format(np.average(
                                                                         model.wellbores.ProdTempDrop.value)),
                                                                     model.wellbores.ProdTempDrop.PreferredUnits.value))
            else:
                reservoir_stimulation_results.append(
                    OutputTableItem('Wellbore Heat Transmission Model = Constant Temperature Drop',
                                    '{0:10.1f}'.format(model.wellbores.tempdropprod.value),
                                    model.wellbores.tempdropprod.PreferredUnits.value))
            if model.wellbores.impedancemodelused.value:
                reservoir_stimulation_results.append(OutputTableItem('Total Average Pressure Drop', '{0:10.1f}'.format(
                    np.average(model.wellbores.DPOverall.value)), model.wellbores.DPOverall.PreferredUnits.value))
                reservoir_stimulation_results.append(OutputTableItem('Average Injection Well Pressure Drop',
                                                                     '{0:10.1f}'.format(
                                                                         np.average(model.wellbores.DPInjWell.value)),
                                                                     model.wellbores.DPInjWell.PreferredUnits.value))
                reservoir_stimulation_results.append(OutputTableItem('Average Reservoir Pressure Drop',
                                                                     '{0:10.1f}'.format(
                                                                         np.average(model.wellbores.DPReserv.value)),
                                                                     model.wellbores.DPReserv.PreferredUnits.value))
                reservoir_stimulation_results.append(OutputTableItem('Average Production Well Pressure Drop',
                                                                     '{0:10.1f}'.format(
                                                                         np.average(model.wellbores.DPProdWell.value)),
                                                                     model.wellbores.DPProdWell.PreferredUnits.value))
                reservoir_stimulation_results.append(OutputTableItem('Average Buoyancy Pressure Drop',
                                                                     '{0:10.1f}'.format(
                                                                         np.average(model.wellbores.DPBouyancy.value)),
                                                                     model.wellbores.DPBouyancy.PreferredUnits.value))
            else:
                reservoir_stimulation_results.append(OutputTableItem('Average Injection Well Pump Pressure Drop',
                                                                     '{0:10.1f}'.format(
                                                                         np.average(model.wellbores.DPInjWell.value)),
                                                                     model.wellbores.DPInjWell.PreferredUnits.value))
                if model.wellbores.productionwellpumping.value:
                    reservoir_stimulation_results.append(OutputTableItem('Average Production Well Pump Pressure Drop',
                                                                         '{0:10.1f}'.format(np.average(
                                                                             model.wellbores.DPProdWell.value)),
                                                                         model.wellbores.DPProdWell.PreferredUnits.value))
        if not model.economics.totalcapcost.Valid:
            CAPEX.append(
                OutputTableItem('Drilling and completion costs', '{0:10.2f}'.format(model.economics.Cwell.value),
                                model.economics.Cwell.CurrentUnits.value))

            if model.economics.cost_one_production_well.value != model.economics.cost_one_injection_well.value and \
                model.economics.cost_one_injection_well.value != -1:
                CAPEX.append(OutputTableItem('Drilling and completion costs per production well',
                                             '{0:10.2f}'.format(model.economics.cost_one_production_well.value,
                                              model.economics.cost_one_production_well.CurrentUnits.value)))
                CAPEX.append(OutputTableItem('Drilling and completion costs per injection well, '
                                             '{0:10.2f}'.format(model.economics.cost_one_injection_well.value,
                                             model.economics.cost_one_injection_well.CurrentUnits.value)))
            else:
                CAPEX.append(OutputTableItem('Drilling and completion costs per well', '{0:10.2f}'.format(
                    model.economics.Cwell.value / (model.wellbores.nprod.value + model.wellbores.ninj.value)),
                                             model.economics.Cwell.CurrentUnits.value))
            CAPEX.append(OutputTableItem('Stimulation costs', '{0:10.2f}'.format(model.economics.Cstim.value),
                                         model.economics.Cstim.CurrentUnits.value))
            CAPEX.append(OutputTableItem('Surface power plant costs', '{0:10.2f}'.format(model.economics.Cplant.value),
                                         model.economics.Cplant.CurrentUnits.value))
            if model.surfaceplant.plant_type.value == PlantType.ABSORPTION_CHILLER:
                CAPEX.append(
                    OutputTableItem('Absorption Chiller Cost', '{0:10.2f}'.format(model.economics.chillercapex.value),
                                    model.economics.Cplant.CurrentUnits.value))
            if model.surfaceplant.plant_type.value == PlantType.HEAT_PUMP:
                CAPEX.append(OutputTableItem('Heat Pump Cost', '{0:10.2f}'.format(model.economics.heatpumpcapex.value),
                                             model.economics.Cplant.CurrentUnits.value))
            if model.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
                CAPEX.append(
                    OutputTableItem('Peaking Boiler Cost', '{0:10.2f}'.format(model.economics.peakingboilercost.value),
                                    model.economics.peakingboilercost.CurrentUnits.value))
            CAPEX.append(
                OutputTableItem('Field gathering system costs', '{0:10.2f}'.format(model.economics.Cgath.value),
                                model.economics.Cgath.CurrentUnits.value))
            if model.surfaceplant.piping_length.value > 0:
                CAPEX.append(
                    OutputTableItem('Transmission pipeline cost', '{0:10.2f}'.format(model.economics.Cpiping.value),
                                    model.economics.Cpiping.CurrentUnits.value))
            if model.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
                CAPEX.append(OutputTableItem('District Heating System Cost',
                                             '{0:10.2f}'.format(model.economics.dhdistrictcost.value),
                                             model.economics.dhdistrictcost.CurrentUnits.value))
            CAPEX.append(OutputTableItem('Total surface equipment costs',
                                         '{0:10.2f}'.format(model.economics.Cplant.value + model.economics.Cgath.value),
                                         model.economics.Cplant.CurrentUnits.value))
            CAPEX.append(OutputTableItem('Exploration costs', '{0:10.2f}'.format(model.economics.Cexpl.value),
                                         model.economics.Cexpl.CurrentUnits.value))
        if model.economics.totalcapcost.Valid and model.wellbores.redrill.value > 0:
            CAPEX.append(OutputTableItem('Drilling and completion costs (for redrilling)',
                                         '{0:10.2f}'.format(model.economics.Cwell.value),
                                         model.economics.Cwell.CurrentUnits.value))
            CAPEX.append(OutputTableItem('Drilling and completion costs per redrilled well', '{0:10.2f}'.format(
                model.economics.Cwell.value / (model.wellbores.nprod.value + model.wellbores.ninj.value)),
                                         model.economics.Cwell.CurrentUnits.value))
            CAPEX.append(
                OutputTableItem('Stimulation costs (for redrilling)', '{0:10.2f}'.format(model.economics.Cstim.value),
                                model.economics.Cstim.CurrentUnits.value))
        if model.economics.RITC.Provided:
            CAPEX.append(
                OutputTableItem('Investment tax Credit', '{0:10.2f}'.format(-1 * model.economics.RITCValue.value),
                                model.economics.RITCValue.CurrentUnits.value))
        CAPEX.append(OutputTableItem('Total capital costs', '{0:10.2f}'.format(model.economics.CCap.value),
                                     model.economics.CCap.CurrentUnits.value))
        if model.economics.econmodel.value == EconomicModel.FCR:
            CAPEX.append(OutputTableItem('Annualized capital costs', '{0:10.2f}'.format(model.economics.CCap.value * (
                    1 + model.economics.inflrateconstruction.value) * model.economics.FCR.value),
                                         model.economics.CCap.CurrentUnits.value))

        if not model.economics.oamtotalfixed.Valid:
            OPEX.append(
                OutputTableItem('Wellfield maintenance costs', '{0:10.2f}'.format(model.economics.Coamwell.value),
                                model.economics.Coamwell.CurrentUnits.value))
            OPEX.append(
                OutputTableItem('Power plant maintenance costs', '{0:10.2f}'.format(model.economics.Coamplant.value),
                                model.economics.Coamplant.CurrentUnits.value))
            OPEX.append(OutputTableItem('Water costs', '{0:10.2f}'.format(model.economics.Coamwater.value),
                                        model.economics.Coamwater.CurrentUnits.value))
            if model.surfaceplant.plant_type.value in [PlantType.INDUSTRIAL, PlantType.ABSORPTION_CHILLER,
                                                       PlantType.HEAT_PUMP, PlantType.DISTRICT_HEATING]:
                OPEX.append(OutputTableItem('Average Reservoir Pumping Cost',
                                            '{0:10.2f}'.format(model.economics.averageannualpumpingcosts.value),
                                            model.economics.averageannualpumpingcosts.CurrentUnits.value))
            if model.surfaceplant.plant_type.value == PlantType.ABSORPTION_CHILLER:
                OPEX.append(OutputTableItem('Absorption Chiller O&M Cost',
                                            '{0:10.2f}'.format(model.economics.chilleropex.value),
                                            model.economics.chilleropex.CurrentUnits.value))
            if model.surfaceplant.plant_type.value == PlantType.HEAT_PUMP:
                OPEX.append(OutputTableItem('Average Heat Pump Electricity Cost', '{0:10.2f}'.format(
                    model.economics.averageannualheatpumpelectricitycost.value),
                                            model.economics.averageannualheatpumpelectricitycost.CurrentUnits.value))
            if model.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
                OPEX.append(OutputTableItem('Annual District Heating O&M Cost',
                                            '{0:10.2f}'.format(model.economics.dhdistrictoandmcost.value),
                                            model.economics.dhdistrictoandmcost.CurrentUnits.value))
                OPEX.append(OutputTableItem('Average Annual Peaking Fuel Cost',
                                            '{0:10.2f}'.format(model.economics.averageannualngcost.value),
                                            model.economics.averageannualngcost.CurrentUnits.value))
            OPEX.append(OutputTableItem('Total operating and maintenance costs', '{0:10.2f}'.format(
                model.economics.Coam.value + model.economics.averageannualpumpingcosts.value + model.economics.averageannualheatpumpelectricitycost.value),
                                        model.economics.Coam.CurrentUnits.value))
        else:
            OPEX.append(
                OutputTableItem('Total operating and maintenance costs', '{0:10.2f}'.format(model.economics.Coam.value),
                                model.economics.Coam.CurrentUnits.value))

        if model.surfaceplant.enduse_option.value in [EndUseOptions.ELECTRICITY,
                                                      EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT,
                                                      EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY,
                                                      EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY,
                                                      EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                      EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT,
                                                      EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]:  # there is an electricity componenent:
            surface_equipment_results.append(OutputTableItem('Initial geofluid availability', '{0:10.2f}'.format(
                model.surfaceplant.Availability.value[0]), model.surfaceplant.Availability.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Maximum Total Electricity Generation', '{0:10.2f}'.format(
                np.max(model.surfaceplant.ElectricityProduced.value)), model.surfaceplant.ElectricityProduced.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Average Total Electricity Generation', '{0:10.2f}'.format(
                np.average(model.surfaceplant.ElectricityProduced.value)), model.surfaceplant.ElectricityProduced.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Minimum Total Electricity Generation', '{0:10.2f}'.format(
                np.min(model.surfaceplant.ElectricityProduced.value)), model.surfaceplant.ElectricityProduced.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Initial Total Electricity Generation', '{0:10.2f}'.format(
                model.surfaceplant.ElectricityProduced.value[0]), model.surfaceplant.ElectricityProduced.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Maximum Net Electricity Generation', '{0:10.2f}'.format(
                np.max(model.surfaceplant.NetElectricityProduced.value)), model.surfaceplant.NetElectricityProduced.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Average Net Electricity Generation', '{0:10.2f}'.format(
                np.average(model.surfaceplant.NetElectricityProduced.value)), model.surfaceplant.NetElectricityProduced.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Minimum Net Electricity Generation', '{0:10.2f}'.format(
                np.min(model.surfaceplant.NetElectricityProduced.value)), model.surfaceplant.NetElectricityProduced.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Initial Net Electricity Generation', '{0:10.2f}'.format(
                model.surfaceplant.NetElectricityProduced.value[0]), model.surfaceplant.NetElectricityProduced.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Average Annual Total Electricity Generation',
                                                             f'{0:10.2f}'.format(np.average(model.surfaceplant.TotalkWhProduced.value / 1E6)),
                                                             f'GWh'))
            surface_equipment_results.append(OutputTableItem('Average Annual Net Electricity Generation',
                                                             f'{0:10.2f}'.format(np.average(model.surfaceplant.NetkWhProduced.value / 1E6)),
                                                             f'GWh'))

            if model.wellbores.PumpingPower.value[0] > 0.0:
                ipp_nip = model.wellbores.PumpingPower.value[0] / model.surfaceplant.NetElectricityProduced.value[0]
                surface_equipment_results.append(
                    OutputTableItem('Initial pumping power/net installed power', '{0:10.2f}'.format(ipp_nip * 100),
                                    '%'))

        if model.surfaceplant.enduse_option.value in [EndUseOptions.HEAT, PlantType.ABSORPTION_CHILLER,
                                                      PlantType.HEAT_PUMP,
                                                      EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT,
                                                      EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY,
                                                      EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY,
                                                      EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                      EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT,
                                                      EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]:  # geothermal heating component:
            surface_equipment_results.append(OutputTableItem('Maximum Net Heat Production', '{0:10.2f}'.format(
                np.max(model.surfaceplant.HeatProduced.value)), model.surfaceplant.HeatProduced.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Average Net Heat Production', '{0:10.2f}'.format(
                np.average(model.surfaceplant.HeatProduced.value)), model.surfaceplant.HeatProduced.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Minimum Net Heat Production', '{0:10.2f}'.format(
                np.min(model.surfaceplant.HeatProduced.value)), model.surfaceplant.HeatProduced.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Initial Net Heat Production', '{0:10.2f}'.format(
                model.surfaceplant.HeatProduced.value[0]), model.surfaceplant.HeatProduced.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Average Annual Heat Production', '{0:10.2f}'.format(
                np.average(model.surfaceplant.HeatkWhProduced.value / 1E6), 'GWh')))

        if model.surfaceplant.plant_type.value == PlantType.HEAT_PUMP:
            surface_equipment_results.append(OutputTableItem('Average Annual Heat Pump Electricity Use',
                                                             '{0:10.2f}'.format(np.average(model.surfaceplant.heat_pump_electricity_kwh_used.value / 1E6),
                                                                                'GWh/year')))
        if model.surfaceplant.plant_type.value == PlantType.ABSORPTION_CHILLER:
            surface_equipment_results.append(OutputTableItem('Maximum Cooling Production', '{0:10.2f}'.format(
                np.max(model.surfaceplant.cooling_produced.value)), model.surfaceplant.cooling_produced.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Average Cooling Production', '{0:10.2f}'.format(
                np.average(model.surfaceplant.cooling_produced.value)),
                                                             model.surfaceplant.cooling_produced.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Minimum Cooling Production', '{0:10.2f}'.format(
                np.min(model.surfaceplant.cooling_produced.value)),
                                                             model.surfaceplant.cooling_produced.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Initial Cooling Production', '{0:10.2f}'.format(
                model.surfaceplant.cooling_produced.value[0]),
                                                             model.surfaceplant.cooling_produced.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Average Annual Cooling Production', '{0:10.2f}'.format(
                np.average(model.surfaceplant.cooling_kWh_Produced.value / 1E6), 'GWh/year')))

        if model.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
            surface_equipment_results.append(OutputTableItem('Annual District Heating Demand', '{0:10.2f}'.format(
                model.surfaceplant.annual_heating_demand.value), model.surfaceplant.annual_heating_demand.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Maximum Daily District Heating Demand',
                                                             '{0:10.2f}'.format(np.max(model.surfaceplant.daily_heating_demand.value)),
                                                             model.surfaceplant.daily_heating_demand.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Average Daily District Heating Demand',
                                                             '{0:10.2f}'.format(np.average(model.surfaceplant.daily_heating_demand.value)),
                                                             model.surfaceplant.daily_heating_demand.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Minimum Daily District Heating Demand',
                                                             '{0:10.2f}'.format(np.min(model.surfaceplant.daily_heating_demand.value)),
                                                             model.surfaceplant.daily_heating_demand.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Maximum Geothermal Heating Production',
                                                             '{0:10.2f}'.format(np.max(model.surfaceplant.dh_geothermal_heating.value)),
                                                             model.surfaceplant.dh_geothermal_heating.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Average Geothermal Heating Production',
                                                             '{0:10.2f}'.format(np.average(model.surfaceplant.dh_geothermal_heating.value)),
                                                             model.surfaceplant.dh_geothermal_heating.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Minimum Geothermal Heating Production',
                                                             '{0:10.2f}'.format(np.min(model.surfaceplant.dh_geothermal_heating.value)),
                                                             model.surfaceplant.dh_geothermal_heating.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Maximum Peaking Boiler Heat Production',
                                                             '{0:10.2f}'.format(np.max(model.surfaceplant.dh_natural_gas_heating.value)),
                                                             model.surfaceplant.dh_natural_gas_heating.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Average Peaking Boiler Heat Production',
                                                             '{0:10.2f}'.format(np.average(model.surfaceplant.dh_natural_gas_heating.value)),
                                                             model.surfaceplant.dh_natural_gas_heating.PreferredUnits.value))
            surface_equipment_results.append(OutputTableItem('Minimum Peaking Boiler Heat Production',
                                                             '{0:10.2f}'.format(np.min(model.surfaceplant.dh_natural_gas_heating.value)),
                                                             model.surfaceplant.dh_natural_gas_heating.PreferredUnits.value))
        surface_equipment_results.append(
            OutputTableItem('Average Pumping Power', '{0:10.2f}'.format(np.average(model.wellbores.PumpingPower.value)),
                            model.wellbores.PumpingPower.CurrentUnits.value))

        # Build the data frame to hold the heating, cooling, and/or electricity production profile
        hce: pd.DataFrame = pd.DataFrame()

        # add the columns as needed based on the output.
        # Note that the correct format for that column is stashed in the title of that column
        # so that it can be used in the write statement.
        hce[f'Year|:2.0f'] = [i for i in range(1, (model.surfaceplant.plant_lifetime.value + 1))]
        short_pt = ShortenArrayToAnnual(model.wellbores.ProducedTemperature.value,
                                        model.surfaceplant.plant_lifetime.value,
                                        model.economics.timestepsperyear.value)
        hce[f'Thermal Drawdown (%)|:8.4f'] = short_pt / short_pt[0]

        hce[
            f'Geofluid Temperature ({model.wellbores.ProducedTemperature.CurrentUnits.value})|:8.2f'] = ShortenArrayToAnnual(
            model.wellbores.ProducedTemperature.value,
            model.surfaceplant.plant_lifetime.value, model.economics.timestepsperyear.value)
        hce[f'Pump Power ({model.wellbores.PumpingPower.CurrentUnits.value})|:8.4f'] = ShortenArrayToAnnual(
            model.wellbores.PumpingPower.value,
            model.surfaceplant.plant_lifetime.value, model.economics.timestepsperyear.value)

        # only electricity
        if model.surfaceplant.enduse_option.value == EndUseOptions.ELECTRICITY:
            hce[
                f'Net Power ({model.surfaceplant.NetElectricityProduced.CurrentUnits.value})|:8.4f'] = ShortenArrayToAnnual(
                model.surfaceplant.NetElectricityProduced.value,
                model.surfaceplant.plant_lifetime.value, model.economics.timestepsperyear.value)
            hce[f'First Law Efficiency (%)|:8.4f'] = ShortenArrayToAnnual(
                model.surfaceplant.FirstLawEfficiency.value * 100,
                model.surfaceplant.plant_lifetime.value, model.economics.timestepsperyear.value)

        # only direct-use
        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and \
            model.surfaceplant.plant_type.value not in \
            [PlantType.HEAT_PUMP, PlantType.DISTRICT_HEATING, PlantType.ABSORPTION_CHILLER]:
            hce[f'Net Heat ({model.surfaceplant.HeatProduced.CurrentUnits.value})|:8.4f'] = \
                ShortenArrayToAnnual(model.surfaceplant.HeatProduced.value,
                                     model.surfaceplant.plant_lifetime.value, model.economics.timestepsperyear.value)

        # heat pump
        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and \
            model.surfaceplant.plant_type.value in [PlantType.HEAT_PUMP]:
            hce[f'Net Heat ({model.surfaceplant.HeatProduced.CurrentUnits.value})|:8.4f'] = \
                ShortenArrayToAnnual(model.surfaceplant.HeatProduced.value,
                                     model.surfaceplant.plant_lifetime.value, model.economics.timestepsperyear.value)
            hce[
                f'Heat Pump Electricity Used ({model.surfaceplant.heat_pump_electricity_used.CurrentUnits.value}|:8.4f'] = \
                ShortenArrayToAnnual(model.surfaceplant.heat_pump_electricity_used.value,
                                     model.surfaceplant.plant_lifetime.value, model.economics.timestepsperyear.value)

        # district heating
        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT \
            and model.surfaceplant.plant_type.value in [PlantType.DISTRICT_HEATING]:
            hce[f'Geothermal Heat Output ({model.surfaceplant.HeatProduced.CurrentUnits.value})|:8.4f'] = \
                ShortenArrayToAnnual(model.surfaceplant.HeatProduced.value,
                                     model.surfaceplant.plant_lifetime.value, model.economics.timestepsperyear.value)

        # absorption chiller
        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT and \
            model.surfaceplant.plant_type.value in [PlantType.ABSORPTION_CHILLER]:
            hce[f'Net Heat ({model.surfaceplant.HeatProduced.CurrentUnits.value})|:8.4f'] = \
                ShortenArrayToAnnual(model.surfaceplant.HeatProduced.value,
                                     model.surfaceplant.plant_lifetime.value,
                                     model.economics.timestepsperyear.value)
            hce[f'Net Cooling ({model.surfaceplant.HeatProduced.CurrentUnits.value})|:8.4f'] = \
                ShortenArrayToAnnual(model.surfaceplant.cooling_produced.value,
                                     model.surfaceplant.plant_lifetime.value,
                                     model.economics.timestepsperyear.value)

        # co-generation
        elif model.surfaceplant.enduse_option.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT,
                                                        EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY,
                                                        EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY,
                                                        EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                        EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT,
                                                        EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]:
            hce[f'Net Power ({model.surfaceplant.NetElectricityProduced.CurrentUnits.value})|:8.4f'] = \
                ShortenArrayToAnnual(model.surfaceplant.NetElectricityProduced.value,
                                     model.surfaceplant.plant_lifetime.value,
                                     model.economics.timestepsperyear.value)
            hce[f'Net Heat ({model.surfaceplant.HeatProduced.CurrentUnits.value})|:8.4f'] = \
                ShortenArrayToAnnual(model.surfaceplant.HeatProduced.value, model.surfaceplant.plant_lifetime.value,
                                     model.economics.timestepsperyear.value)
            hce[f'First Law Efficiency (%)|:8.4f'] = ShortenArrayToAnnual(model.surfaceplant.FirstLawEfficiency.value,
                                                                          model.surfaceplant.plant_lifetime.value,
                                                                          model.economics.timestepsperyear.value) * 100
        hce = hce.reset_index()

        # Build the data frame to hold the annual heating, cooling, and/or electricity production profile
        ahce: pd.DataFrame = pd.DataFrame()

        # add the columns as needed based on the output.
        # Note that the correct format for that column is stashed in the title of that column
        # so that it can be used in the write statement.
        ahce[f'Year|:2.0f'] = [i for i in range(1, (model.surfaceplant.plant_lifetime.value + 1))]

        # only electricity
        if model.surfaceplant.enduse_option.value == EndUseOptions.ELECTRICITY:
            ahce[f'Electricity Provided ({model.surfaceplant.NetkWhProduced.CurrentUnits.value})|:8.1f'] = \
                model.surfaceplant.NetkWhProduced.value / 1E6

        # absorption chiller
        elif model.surfaceplant.plant_type.value == PlantType.ABSORPTION_CHILLER:
            ahce[f'Cooling Provided ({model.surfaceplant.cooling_kWh_Produced.CurrentUnits.value})|:8.1f'] = \
                ShortenArrayToAnnual(model.surfaceplant.cooling_kWh_Produced.value,
                                     model.surfaceplant.plant_lifetime.value,
                                     model.economics.timestepsperyear.value) / 1E6

        # heat pump
        elif model.surfaceplant.plant_type.value == PlantType.HEAT_PUMP:
            ahce[f'Heating Provided ({model.surfaceplant.HeatkWhProduced.CurrentUnits.value})|:8.1f'] = \
                ShortenArrayToAnnual(model.surfaceplant.HeatkWhProduced.value, model.surfaceplant.plant_lifetime.value,
                                     model.economics.timestepsperyear.value) / 1E6
            ahce[f'Reservoir Heat Extracted ({model.surfaceplant.HeatkWhExtracted.CurrentUnits.value})|:8.1f'] = \
                ShortenArrayToAnnual(model.surfaceplant.HeatkWhExtracted.value, model.surfaceplant.plant_lifetime.value,
                                     model.economics.timestepsperyear.value) / 1E6
            ahce[
                f'Heat Pump Electricity Used ({model.surfaceplant.heat_pump_electricity_kwh_used.CurrentUnits.value})|:8.1f'] = \
                ShortenArrayToAnnual(model.surfaceplant.heat_pump_electricity_kwh_used.value,
                                     model.surfaceplant.plant_lifetime.value,
                                     model.economics.timestepsperyear.value) / 1E6

        # co-generation
        elif model.surfaceplant.enduse_option.value in [EndUseOptions.COGENERATION_TOPPING_EXTRA_HEAT,
                                                        EndUseOptions.COGENERATION_TOPPING_EXTRA_ELECTRICITY,
                                                        EndUseOptions.COGENERATION_BOTTOMING_EXTRA_ELECTRICITY,
                                                        EndUseOptions.COGENERATION_BOTTOMING_EXTRA_HEAT,
                                                        EndUseOptions.COGENERATION_PARALLEL_EXTRA_HEAT,
                                                        EndUseOptions.COGENERATION_PARALLEL_EXTRA_ELECTRICITY]:
            ahce[f'Heating Provided ({model.surfaceplant.HeatkWhProduced.CurrentUnits.value})|:8.1f'] = \
                ShortenArrayToAnnual(model.surfaceplant.HeatkWhProduced.value,
                                     model.surfaceplant.plant_lifetime.value,
                                     model.economics.timestepsperyear.value) / 1E6
            ahce[f'Electricity Provided ({model.surfaceplant.NetkWhProduced.CurrentUnits.value})|:8.1f'] = \
                ShortenArrayToAnnual(model.surfaceplant.NetkWhProduced.value,
                                     model.surfaceplant.plant_lifetime.value,
                                     model.economics.timestepsperyear.value) / 1E6

        # district-heating
        elif model.surfaceplant.plant_type.value in [PlantType.DISTRICT_HEATING]:
            ahce[f'Electricity Provided ({model.surfaceplant.HeatkWhProduced.CurrentUnits.value})|:8.1f'] = \
                ShortenArrayToAnnual(model.surfaceplant.HeatkWhProduced.value,
                                     model.surfaceplant.plant_lifetime.value,
                                     model.economics.timestepsperyear.value) / 1E6
            ahce[f'Peaking Boiler Heat Provided ({model.surfaceplant.annual_ng_demand.CurrentUnits.value})|:8.1f'] = \
                ShortenArrayToAnnual(model.surfaceplant.annual_ng_demand.value,
                                     model.surfaceplant.plant_lifetime.value,
                                     model.economics.timestepsperyear.value) / 1E3

        elif model.surfaceplant.enduse_option.value == EndUseOptions.HEAT:  # only direct-use
            ahce[f'Heating Provided ({model.surfaceplant.HeatkWhProduced.CurrentUnits.value})|:8.1f'] = \
                ShortenArrayToAnnual(model.surfaceplant.HeatkWhProduced.value, model.surfaceplant.plant_lifetime.value,
                                     model.economics.timestepsperyear.value) / 1E6

        # three columns always at the end of each style of table
        ahce[f'Heat Extracted({model.surfaceplant.HeatkWhExtracted.CurrentUnits.value})|:8.2f'] = \
            model.surfaceplant.HeatkWhExtracted.value / 1E6
        ahce[f'Reservoir Heat Content ({model.surfaceplant.RemainingReservoirHeatContent.CurrentUnits.value})|:8.2f'] = \
            model.surfaceplant.RemainingReservoirHeatContent.value
        ahce[f'Percentage of Total Heat Mined (%)|:8.2f'] = \
            (
                    model.reserv.InitialReservoirHeatContent.value - model.surfaceplant.RemainingReservoirHeatContent.value) * 100. \
            / model.reserv.InitialReservoirHeatContent.value
        ahce = ahce.reset_index()

        # Build the data frame to hold the revenue and cashflow profile
        econ: Economics = model.economics
        # create a Coam array and zero out the OPEX during construction years
        construction_years_zeros = np.zeros(model.surfaceplant.construction_years.value)
        Coam = np.zeros(model.surfaceplant.construction_years.value + model.surfaceplant.plant_lifetime.value)
        for ii in range(model.surfaceplant.construction_years.value, model.surfaceplant.plant_lifetime.value + 1):
            Coam[ii] = econ.Coam.value

        cashflow: pd.DataFrame = pd.DataFrame()

        # add the columns as needed based on the output.
        # Note that the correct format for that column is stashed in the title of that column
        # so that it can be used in the write statement.
        # note that the price arrays need to be extended by the number of construction years. with price = 0
        cashflow[f'Year|:3.0f'] = [i for i in range(1,
                                                    model.surfaceplant.plant_lifetime.value + model.surfaceplant.construction_years.value + 1)]
        cashflow[f'Electricity:Price ({econ.ElecPrice.CurrentUnits.value})|:7.4f'] = econ.ElecPrice.value
        cashflow[f'Electricity:Ann. Rev. ({econ.ElecRevenue.CurrentUnits.value})|:5.2f'] = econ.ElecRevenue.value
        cashflow[
            f'Electricity:Cumm. Rev. ({econ.ElecCummRevenue.CurrentUnits.value})|:5.2f'] = econ.ElecCummRevenue.value
        cashflow[f'Heat:Price ({econ.HeatPrice.CurrentUnits.value})|:7.4f'] = econ.HeatPrice.value
        cashflow[f'Heat:Ann. Rev. ({econ.HeatRevenue.CurrentUnits.value})|:5.2f'] = econ.HeatRevenue.value
        cashflow[f'Heat:Cumm. Rev. ({econ.HeatCummRevenue.CurrentUnits.value})|:5.2f'] = econ.HeatCummRevenue.value
        cashflow[f'Cooling:Price ({econ.CoolingPrice.CurrentUnits.value})|:7.4f'] = econ.CoolingPrice.value
        cashflow[f'Cooling:Ann. Rev. ({econ.CoolingRevenue.CurrentUnits.value})|:5.2f'] = econ.CoolingRevenue.value
        cashflow[
            f'Cooling:Cumm. Rev. ({econ.CoolingCummRevenue.CurrentUnits.value})|:5.2f'] = econ.CoolingCummRevenue.value
        cashflow[f'Carbon:Price ({econ.CarbonPrice.CurrentUnits.value})|:7.4f'] = econ.CarbonPrice.value
        cashflow[f'Carbon:Ann. Rev. ({econ.CarbonRevenue.CurrentUnits.value})|:5.2f'] = econ.CarbonRevenue.value
        cashflow[
            f'Carbon:Cumm. Rev. ({econ.CarbonCummCashFlow.CurrentUnits.value})|:5.2f'] = econ.CarbonCummCashFlow.value
        cashflow[f'Project:OPEX ({econ.Coam.CurrentUnits.value})|:5.2f'] = Coam
        cashflow[f'Project:Net Rev. ({econ.TotalRevenue.CurrentUnits.value})|:5.2f'] = econ.TotalRevenue.value
        cashflow[
            f'Project:Net Cashflow ({econ.TotalCummRevenue.CurrentUnits.value})|:5.2f'] = econ.TotalCummRevenue.value
        cashflow = cashflow.reset_index()

        # Build the data frame to hold the pumping power profiles
        pumping_power_profiles: pd.DataFrame = pd.DataFrame()

        if model.wellbores.overpressure_percentage.Provided and model.wellbores.injection_reservoir_depth.Provided:
            # add the columns as needed based on the output.
            # Note that the correct format for that column is stashed in the title of that column
            # so that it can be used in the write statement.
            pumping_power_profiles[f'Year|:2.0f'] = [i for i in range(1, (model.surfaceplant.plant_lifetime.value + 1))]
            pumping_power_profiles[f'Prod Pump Power ({model.wellbores.PumpingPowerProd.CurrentUnits.value})|:8.4f'] = ShortenArrayToAnnual(
                model.wellbores.PumpingPowerProd.value,
                model.surfaceplant.plant_lifetime.value, model.economics.timestepsperyear.value)
            pumping_power_profiles[f'Inject Pump Power ({model.wellbores.PumpingPowerInj.CurrentUnits.value})|:8.4f'] = ShortenArrayToAnnual(
                model.wellbores.PumpingPowerInj.value,
                model.surfaceplant.plant_lifetime.value, model.economics.timestepsperyear.value)
            pumping_power_profiles[f'Pump Power ({model.wellbores.PumpingPower.CurrentUnits.value})|:8.4f'] = ShortenArrayToAnnual(
                model.wellbores.PumpingPower.value,
                model.surfaceplant.plant_lifetime.value, model.economics.timestepsperyear.value)

        pumping_power_profiles = pumping_power_profiles.reset_index()

        addon_df = pd.DataFrame()
        sdac_df = pd.DataFrame()
        addon_results: list[OutputTableItem] = []
        sdac_results: list[OutputTableItem] = []

        if model.economics.DoAddOnCalculations.value:
            addon_df, addon_results = model.addoutputs.PrintOutputs(model)
        if model.economics.DoSDACGTCalculations.value:
            sdac_df, sdac_results = model.sdacgtoutputs.PrintOutputs(model)

        if text_output_file.Provided:
            Write_Text_Output(output_file, simulation_metadata, summary, economic_parameters,
                              engineering_parameters,
                              resource_characteristics, reservoir_parameters, reservoir_stimulation_results, CAPEX,
                              OPEX,
                              surface_equipment_results, sdac_results, addon_results, hce, ahce, cashflow,
                              pumping_power_profiles, sdac_df, addon_df)

            # Get rid of any trailing spaces in that output file - they are confusing the testing code
            with open(output_file, 'r+') as fp:
                lines = fp.readlines()
                fp.seek(0)
                fp.truncate()
                for line in lines:
                    line = line.rstrip() + '\n'
                    fp.write(line)

        # uncomment these to allow for testing of the HTML output
        #        self.html_output_file.value = 'd:\\temp\\test_table_geophires.html'
        #        self.html_output_file.Provided = True
        if html_output_file.Provided:
            Write_HTML_Output(html_output_file.value, simulation_metadata, summary, economic_parameters,
                              engineering_parameters, resource_characteristics, reservoir_parameters,
                              reservoir_stimulation_results, CAPEX, OPEX, surface_equipment_results, sdac_results,
                              addon_results, hce, ahce, cashflow, pumping_power_profiles, sdac_df, addon_df)

            Plot_Tables_Into_HTML(model.surfaceplant.enduse_option, model.surfaceplant.plant_type,
                                  html_output_file.value, hce, ahce, cashflow, pumping_power_profiles, sdac_df,
                                  addon_df)
            # make district heating plot
            if model.surfaceplant.plant_type.value == PlantType.DISTRICT_HEATING:
                MakeDistrictHeatingPlot(html_output_file.value, model.surfaceplant.dh_geothermal_heating.value,
                                        model.surfaceplant.daily_heating_demand.value)


    @staticmethod
    def _field_label(field_name:str, print_width_before_value: int) -> str:
        return f'{field_name}:{" " * (print_width_before_value - len(field_name) - 1)}'

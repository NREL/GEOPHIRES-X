import sys
from functools import lru_cache

import numpy as np
import pandas as pd
from scipy.special import erf, erfc, jv, yv, exp1
from scipy.interpolate import interp1d
from scipy.integrate import trapezoid
import scipy.io as sio
import matplotlib.pyplot as plt

import CoolProp.CoolProp as CP

import geophires_x.Model as Model
from .CylindricalReservoir import CylindricalReservoir
from .OptionList import FlowrateModel, InjectionTemperatureModel, Configuration
from .Parameter import intParameter, floatParameter, OutputParameter, ReadParameter, strParameter, boolParameter
from .Reservoir import Reservoir
from .Units import *
from functools import lru_cache


def interpolator(time_value: float, times: np.ndarray, values: np.ndarray) -> float:
    """
    Interpolates values based on time
    :param time_value: Time value
    :type time_value: float
    :param values: Values
    :type values: float
    :return: Interpolated value
    :rtype: float
    """
    for i in range(1, len(times)):
        if times[i] == time_value:
            return values[i]
        if time_value < times[i]:
            time_diff = times[i] - times[i - 1]
            value_diff = values[i] - values[i - 1]
            ratio = (time_value - times[i - 1]) / time_diff
            return values[i - 1] + ratio * value_diff


def generate_wireframe_model(lateral_endpoint_depth: float, number_of_laterals: int, lateral_spacing: float, element_length: float,
                             junction_depth:float, vertical_section_depth: float, angle: float,
                             vertical_well_spacing: float, generate_graphics: bool = False) -> tuple:

    # Generate inj well profile
    zinj = np.linspace(0, -vertical_section_depth, round(vertical_section_depth / element_length))
    yinj = np.zeros(len(zinj))
    xinj = np.zeros(len(zinj))

    inclined_length = abs(-junction_depth - zinj[-1]) / np.cos(angle)
    number_of_elements_inclined_length = round(inclined_length / element_length)

    zinj_inclined_length = np.linspace(zinj[-1], -junction_depth, number_of_elements_inclined_length)
    yinj_inclined_length = np.linspace(yinj[-1], yinj[-1], number_of_elements_inclined_length)
    xinj_inclined_length = np.linspace(xinj[-1], inclined_length * np.sin(angle), number_of_elements_inclined_length)

    zinj = np.concatenate((zinj, zinj_inclined_length[1:]))
    xinj = np.concatenate((xinj, xinj_inclined_length[1:]))
    yinj = np.concatenate((yinj, yinj_inclined_length[1:]))

    # Generate prod well profile
    zprod = np.flip(zinj)
    xprod = np.flip(xinj)
    yprod = np.flip(yinj + vertical_well_spacing)

    # Generate laterals
    x_laterals_inj = np.zeros(number_of_laterals)
    y_laterals_inj = np.zeros(number_of_laterals)
    z_laterals_inj = np.zeros(number_of_laterals)

    for i in range(number_of_laterals):
        y_laterals_inj[i] = yinj[-1] - (lateral_spacing * (number_of_laterals - 1)) / 2 + i * lateral_spacing - (
                yinj[-1] - yprod[0]) / 2
        x_laterals_inj[i] = xinj[-1] + element_length * 3 * np.sin(angle)
        z_laterals_inj[i] = zinj[-1] - element_length * 3 * np.cos(angle)

    # Generate template
    lateral_length = (lateral_endpoint_depth - abs(z_laterals_inj[0])) / np.cos(angle)
    number_of_elements_lateral = round(lateral_length / element_length)
    z_template_lateral = np.linspace(z_laterals_inj[-1], -lateral_endpoint_depth, number_of_elements_lateral)
    x_template_lateral = np.linspace(x_laterals_inj[-1], x_laterals_inj[-1] + lateral_length * np.sin(angle),
                                     number_of_elements_lateral)
    y_template_lateral = np.full(number_of_elements_lateral, y_laterals_inj[-1])

    # Add section upwards
    z_template_lateral = np.concatenate((z_template_lateral, [z_template_lateral[-1] + element_length, z_template_lateral[-1] + element_length * 2]))
    x_template_lateral = np.concatenate((x_template_lateral, [x_template_lateral[-1], x_template_lateral[-1]]))
    y_template_lateral = np.concatenate((y_template_lateral, [y_template_lateral[-1], y_template_lateral[-1]]))

    # Add loop back
    z_template_lateral = np.concatenate((z_template_lateral, np.flip(z_template_lateral[1:-3]) + element_length * 2))
    x_template_lateral = np.concatenate((x_template_lateral, np.flip(x_template_lateral[1:-3])))
    y_template_lateral = np.concatenate((y_template_lateral, np.flip(y_template_lateral[1:-3])))

    # Generate feedways
    xlat = np.zeros((3, number_of_laterals))
    ylat = np.zeros((3, number_of_laterals))
    zlat = np.zeros((3, number_of_laterals))

    for i in range(number_of_laterals):
        xlat[0:3, i] = np.linspace(xinj[-1], x_laterals_inj[i], 3)
        ylat[0:3, i] = np.linspace(yinj[-1], y_laterals_inj[i], 3)
        zlat[0:3, i] = np.linspace(zinj[-1], z_laterals_inj[i], 3)

    xlat = np.vstack((xlat, np.zeros((len(x_template_lateral) - 1, number_of_laterals))))
    ylat = np.vstack((ylat, np.zeros((len(x_template_lateral) - 1, number_of_laterals))))
    zlat = np.vstack((zlat, np.zeros((len(x_template_lateral) - 1, number_of_laterals))))

    # Add template
    for i in range(number_of_laterals):
        adjusted_template = np.vstack((x_template_lateral, y_template_lateral, z_template_lateral)).T + np.array(
            [x_laterals_inj[i], y_laterals_inj[i], z_laterals_inj[i]]) - np.array(
            [x_template_lateral[0], y_template_lateral[0], z_template_lateral[0]])
        xlat[3:, i] = adjusted_template[1:, 0]
        ylat[3:, i] = adjusted_template[1:, 1]
        zlat[3:, i] = adjusted_template[1:, 2]

    # Add sections back to production point
    xreturn = np.zeros((3, number_of_laterals))
    yreturn = np.zeros((3, number_of_laterals))
    zreturn = np.zeros((3, number_of_laterals))

    for i in range(number_of_laterals):
        xreturn[:, i] = np.linspace(xlat[-1, i], xprod[0], 3)
        yreturn[:, i] = np.linspace(ylat[-1, i], yprod[0], 3)
        zreturn[:, i] = np.linspace(zlat[-1, i], zprod[0], 3)

    xlat = np.vstack((xlat, xreturn[1:, :]))
    ylat = np.vstack((ylat, yreturn[1:, :]))
    zlat = np.vstack((zlat, zreturn[1:, :]))

    if generate_graphics:
        # Plot profile
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot(xinj, yinj, zinj, 'b-o', linewidth=2)
        ax.plot(xprod, yprod, zprod, 'r-o', linewidth=2)

        for i in range(number_of_laterals):
            ax.plot(xlat[:, i], ylat[:, i], zlat[:, i], 'k-o', linewidth=2)

        ax.set_facecolor('white')
        ax.tick_params(axis='both', which='major', labelsize=22)
        ax.set_xlabel('x (m)', fontsize=22)
        ax.set_ylabel('y (m)', fontsize=22)
        ax.set_zlabel('Depth (m)', fontsize=22)
        # ax.legend(['Injection Well', 'Production Well', 'Lateral(s)'], fontsize=22)  # Uncomment to add legend

        az, el = 71.5676, 10.4739
        ax.view_init(az, el)
        show_plot(block=False)

    return xinj, yinj, zinj, xprod, yprod, zprod, xlat, ylat, zlat


class SBTReservoir(CylindricalReservoir):
    """
     The following code calculates the temperature profile in a U-shaped geothermal well using the SBT algorithm.
    """

    def __init__(self, model: Model):
        """
        The __init__ function is called automatically when a class is instantiated.
        It initializes the attributes of an object, and sets default values for certain arguments that can be overridden by user input.
        The __init__ function is used to set up all the parameters in the Reservoir.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        model.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')
        super().__init__(model)

        # Set up all the Parameters that will be predefined by this class using the different types of parameter classes
        # Setting up includes giving it a name, a default value, The Unit Type (length, volume, temperature, etc) and
        # Unit Name of that value, sets it as required (or not), sets allowable range, the error message if that range
        # is exceeded, the ToolTip Text, and the name of the class that created it.
        # This includes setting up temporary variables that will be available to all the class but noy read in by user,
        # or used for Output
        # This also includes all Parameters that are calculated and then published using the Printouts function.
        # If you choose to subclass this master class, you can do so before or after you create your own parameters.
        # If you do, you can also choose to call this method from you class, which will effectively add and set all
        # these parameters to your class.

        # These dictionaries contain a list of all the parameters set in this object, stored as "Parameter" and
        # OutputParameter Objects.  This will allow us later to access them in a user interface and get that list,
        # along with unit type, preferred units, etc.

        self.flow_rate_model = self.ParameterDict[self.flow_rate_model.Name] = intParameter(
            "Flowrate Model",
            DefaultValue=FlowrateModel.USER_SUPPLIED,
            AllowableRange=[1, 2],
            UnitType=Units.NONE,
            ErrMessage="assume constant user-provided flowrate (1)",
            ToolTipText="Must be 1 or 2. '1' means the user provides a constant mass flow rate. "
                        "'1' means the user provides an excel file with a mass flow rate profile."
        )
        self.flow_rate_file = self.ParameterDict[self.flow_rate_file.Name] = strParameter(
            "Flowrate File",
            DefaultValue="",
            UnitType=Units.NONE,
            ErrMessage="assume no flowrate file",
            ToolTipText="Excel file with a mass flow rate profile"
        )
        self.injection_temperature_model = self.ParameterDict[self.injection_temperature_model.Name] = intParameter(
            "Injection Temperature Model",
            DefaultValue=InjectionTemperatureModel.USER_SUPPLIED,
            AllowableRange=[1, 2],
            UnitType=Units.NONE,
            ErrMessage="assume constant user-provided injection temperature (1)",
            ToolTipText="Must be 1 or 2. '1' means the user provides a constant injection temperature. "
                        "'1' means the user provides an excel file with an injection temperature profile."
        )
        self.injection_temperature_file = self.ParameterDict[self.injection_temperature_file.Name] = strParameter(
            "Injection Temperature File",
            DefaultValue="",
            UnitType=Units.NONE,
            ErrMessage="assume no injection temperature file",
            ToolTipText="Excel file with an injection temperature profile"
        )
        self.SBTAccuracyDesired = self.ParameterDict[self.SBTAccuracyDesired.Name] = intParameter(
            "SBT Accuracy Desired",
            DefaultValue=1,
            AllowableRange=[1, 5],
            UnitType=Units.NONE,
            ErrMessage="assume default SBT accuracy desired (1)",
            ToolTipText="Must be 1, 2, 3, 4 or 5 with 1 lowest accuracy and 5 highest accuracy. "
                        "Lowest accuracy runs fastest. Accuracy level impacts number of discretizations for "
                        "numerical integration and decision tree thresholds in SBT algorithm."
        )
        self.percent_implicit = self.ParameterDict[self.percent_implicit.Name] = floatParameter(
            "SBT Percent Implicit Euler Scheme",
            DefaultValue=1.0,
            Min=0.0,
            Max=1.0,
            UnitType=Units.PERCENT,
            PreferredUnits=PercentUnit.TENTH,
            CurrentUnits=PercentUnit.TENTH,
            ErrMessage="assume default percent implicit (1.0)",
            ToolTipText="Should be between 0 and 1. Most stable is setting it to 1 which results in "
                        "a fully implicit Euler scheme when calculating the fluid temperature at each time step. "
                        "With a value of 0, the convective term is modelled using explicit Euler. "
                        "A value of 0.5 would model the convective term 50% explicit and 50% implicit, "
                        "which may be slightly more accurate than fully implicit."
        )
        self.initial_timestep_count = self.ParameterDict[self.initial_timestep_count.Name] = intParameter(
            'SBT Initial Timestep Count',
            DefaultValue=5,
            AllowableRange = [1,150],
            UnitType=Units.NONE,
            ErrMessage='assume default for Initial Timestep Count (5)',
            ToolTipText='The number of timesteps in the first ~3 hours of model'
        )
        self.final_timestep_count = self.ParameterDict[self.final_timestep_count.Name] = floatParameter(
            'SBT Final Timestep Count',
            DefaultValue=70,
            Min=5,
            Max=1000,
            UnitType=Units.NONE,
            ErrMessage='assume default for Final Timestep Count 70)',
            ToolTipText='The number of timesteps after the first ~3 hours of model'
        )
        self.initial_final_timestep_transition = self.ParameterDict[self.initial_final_timestep_transition.Name] = floatParameter(
            'SBT Initial to Final Timestep Transition',
            DefaultValue=9900,
            Min=1,
            Max=40_000_000,
            UnitType=Units.TIME,
            PreferredUnits=TimeUnit.SECOND,
            CurrentUnits=TimeUnit.SECOND,
            ErrMessage='assume default for Initial to Final Timestep Transition (9900 seconds)',
            ToolTipText='The time in secs at which the time arrays switches from closely spaced linear to logarithmic'
        )
        self.generate_wireframe_graphics = self.ParameterDict[self.generate_wireframe_graphics.Name] = boolParameter(
            'SBT Generate Wireframe Graphics',
            DefaultValue=False,
            UnitType=Units.NONE,
            ErrMessage='assume default for SBT Generate Wireframe Graphics (False)',
            ToolTipText='Switch to control the generation of a wireframe drawing of a SBT wells configuration'
        )

        sclass = str(__class__).replace("<class \'", "")
        self.MyClass = sclass.replace("\'>", "")
        self.MyPath = os.path.abspath(__file__)

        # Saved Outputs

        self.NonLinearTime_temperature = self.OutputParameterDict[self.NonLinearTime_temperature.Name] = OutputParameter(
            "NonLinear Time vs Temperature",
            UnitType=Units.NONE
        )

        model.logger.info(f'Complete {str(__class__)}: {sys._getframe().f_code.co_name}')

    def __str__(self):
        return "SBTReservoir"

    def read_parameters(self, model: Model) -> None:
        """
        The read_parameters function reads in the parameters from a dictionary created by reading the user-provided file
        and updates the parameter values for this object.
        The function reads in all the parameters that relate to this object, including those that are inherited from
        other objects. It then updates any of these parameter values that have been changed by the user.
        It also handles any special cases.
        :param model: The container class of the application, giving access to everything else, including the logger
        :type model: :class:`~geophires_x.Model.Model`
        :return: None
        """
        model.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')
        super().read_parameters(model)

        # Deal with all the parameter values that the user has provided.  They should really only provide values
        # that they want to change from the default values, but they can provide a value that is already set
        # because it is a default value set in __init__.  It will ignore those.
        # This also deals with all the special cases that need to be taken care of
        # after a value has been read in and checked.
        # If you choose to subclass this master class, you can also choose to override this method (or not),
        # and if you do, do it before or after you call you own version of this method.  If you do, you can
        # also choose to call this method from you class, which can effectively modify all these
        # superclass parameters in your class.

        if len(model.InputParameters) > 0:
            # loop through all the parameters that the user wishes to set, looking for parameters that match this object
            for item in self.ParameterDict.items():
                ParameterToModify = item[1]
                key = ParameterToModify.Name.strip()
                if key in model.InputParameters:
                    ParameterReadIn = model.InputParameters[key]

                    # TODO: refactor GEOPHIRES such that parameters are read in immutably and only accessed with
                    #  explicit units, with conversion only occurring in the getter as necessary

                    ReadParameter(ParameterReadIn, ParameterToModify, model)  # this handles all non-special cases

                    # handle special cases
                    if ParameterToModify.Name == "Flowrate Model":
                        if ParameterReadIn.sValue == '1':
                            ParameterToModify.value = FlowrateModel.USER_SUPPLIED
                        elif ParameterReadIn.sValue == '2':
                            ParameterToModify.value = FlowrateModel.FILE_SUPPLIED

                    elif ParameterToModify.Name == 'Injection Temperature Model':
                        if ParameterReadIn.sValue == '1':
                            ParameterToModify.value = InjectionTemperatureModel.USER_SUPPLIED
                        elif ParameterReadIn.sValue == '2':
                            ParameterToModify.value = InjectionTemperatureModel.FILE_SUPPLIED
        else:
            model.logger.info("No parameters read because no content provided")

        model.logger.info(f'complete {str(__class__)}: {sys._getframe().f_code.co_name}')

    def Calculate(self, model):
        """
        The Calculate function is the main function that is called to run the calculations for this object.
        In this case, it just calls the appropriate function based on the configuration of the wellbores.
        """
        model.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')

        # calculate the reservoir depth because there is no one single depth as there are for other reservoirs.
        # Make the depth at which this pressure is calculates to be the average of the junction box depth and
        # the lateral endpoint depths
        self.depth.value = (model.wellbores.junction_depth.quantity().to('km').magnitude +
                 model.wellbores.lateral_endpoint_depth.quantity().to('km').magnitude) / 2.0

        if model.wellbores.Configuration.value in [Configuration.ULOOP, Configuration.EAVORLOOP]:
            self.Calculate_Uloop(model)
        elif model.wellbores.Configuration.value == Configuration.COAXIAL:
            self.Calculate_Coaxial(model)
        else:
            return
        model.logger.info(f'complete {str(__class__)}: {sys._getframe().f_code.co_name}')


    @lru_cache(maxsize=1024)
    #@profile
    def Calculate_Coaxial(self, model):
        """
        Calculate the coaxial version of the SBT model
        """
        model.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')

        raise NotImplementedError('SBT with coaxial configuration is not implemented at this time.')

        # Clear all equivalent: Initialize variables and import necessary libraries

        # SBT v2 for co-axial heat exchanger with high-temperature capability
        # last update: January 14th, 2024

        # 1. Input
        # Generally, the user should only make changes to this section

        fluid = 1  # Heat transfer fluid selection: 1 = H2O; 2 = CO2
        m = 20  # Total fluid mass flow rate [kg/s]
        Tin = 50  # Fluid input temperature [°C]
        Pin = 100  # Fluid input pressure [bar]
        Tsurf = 20  # Surface temperature [°C]
        GeoGradient = 100 / 1000  # Geothermal gradient [°C/m]
        self.krock.value = 2.83  # Rock thermal conductivity [W/m·K]
        k_m_boiler = self.krock.value * 6  # Thermal conductivity in boiler [W/m·K]
        self.cprock.value = 825  # Rock specific heat capacity [J/kg·K]
        self.rhorock.value = 2875  # Rock density [kg/m³]
        radius = 0.2286 / 2  # Wellbore radius [m]
        radiuscenterpipe = 0.127 / 2  # Inner radius of inner pipe [m]
        thicknesscenterpipe = 0.0127  # Thickness of inner pipe [m]
        k_center_pipe = 0.01  # Thermal conductivity of insulation of center pipe wall [W/m·K]
        perform_interpipe_heat_exchange_iteration = 0  # Perform additional iteration loop if problem with converging heat exchange
        coaxialflowtype = 1  # 1 = CXA (fluid injection in annulus); 2 = CXC (fluid injection in center pipe)
        piperoughness = 10 ** -6  # Pipe roughness to calculate friction pressure drop [m]
        times = np.concatenate(
            (np.arange(0, 1000, 100), np.logspace(np.log10(100 * 100), np.log10(20 * 365 * 24 * 3600), 75)))
        reltolerance = 1e-5  # Target maximum acceptable relative tolerance each time step
        maxnumberofiterations = 25  # Maximum number of iterations each time step
        variablefluidproperties = 1  # 0 means constant fluid properties, 1 means properties vary with temperature and pressure

        # Constant fluid properties if variablefluidproperties is 0
        if variablefluidproperties == 0:
            rho_f = 996  # Density of the fluid [kg/m³]
            cp_f = 4177  # Specific heat capacity of the fluid [J/kg·K]
            k_f = 0.615  # Thermal conductivity of the fluid [W/m·K]
            mu_f = 7.97 * 10 ** -4  # Dynamic viscosity of the fluid [Pa·s]

        initialtemperatureprofile = 1  # 0 to calculate initial temperature using Tsurf and GeoGradient, 1 to provide array initialtemperaturedata
        initialtemperaturedata = np.array([
            [0, 20],
            [-1499.9, 600],
            [-1500, 1000],
            [-2000, 1000]
        ])

        # Coordinates of the centerline of the co-axial heat exchanger
        # MIR z = np.arange(0, -2050, -50)
        z = np.arange(0, -2050, -50)
        x = np.zeros(len(z))
        y = np.zeros(len(z))

        # Specify boiler elements
        boilerelements = np.arange(31, 41)

        # Make 3D figure of borehole geometry to make sure it looks correct
        # fig = plt.figure()
        # ax = fig.add_subplot(111, projection='3d')
        # ax.plot3D(x, y, z, 'k-o', linewidth=2)
        # ax.set_xlabel('x (m)')
        # ax.set_ylabel('y (m)')
        # x.set_zlabel('Depth (m)')
        # x.set_title('Co-axial heat exchanger geometry')
        # plt.grid()
        # plt.show()

        # 2. Pre-Processing
        print('Start pre-processing ...')
        g = 9.81  # Gravitational acceleration [m/s²]
        gamma = 0.577215665  # Euler's constant
        alpha_m = self.krock.value / (self.rhorock.value * self.cprock.value)  # Rock thermal diffusivity [m²/s]
        alpha_m_boiler = self.krock.value / (self.rhorock.value * self.cprock.value)  # Boiler rock thermal diffusivity [m²/s]

        outerradiuscenterpipe = radiuscenterpipe + thicknesscenterpipe  # Outer radius of inner pipe [m]
        A_flow_annulus = np.pi * (radius ** 2 - outerradiuscenterpipe ** 2)  # Flow area of annulus pipe [m²]
        A_flow_centerpipe = np.pi * radiuscenterpipe ** 2  # Flow area of center pipe [m²]
        Dh_annulus = 2 * (radius - outerradiuscenterpipe)  # Hydraulic diameter of annulus [m]
        eps_annulus = Dh_annulus * piperoughness  # Relative roughness annulus [-]
        eps_centerpipe = 2 * radiuscenterpipe * piperoughness  # Relative roughness inner pipe [-]

        # These variables are set but never used, and sio.loadmat is causing a "No such file" error.
        # (see https://github.com/NREL/GEOPHIRES-X/issues/373)
        # Variable fluid properties logic
        #if variablefluidproperties == 0:
        #    Pvector = [1, 1e9]
        #    Tvector = [1, 1e4]
        #    density = np.full((2, 2), rho_f)
        #    heatcapacity = np.full((2, 2), cp_f)
        #    thermalconductivity = np.full((2, 2), k_f)
        #    viscosity = np.full((2, 2), mu_f)
        #    thermalexpansion = np.zeros((2, 2))
        #else:
        #    print('Loading fluid properties ...')
        #    if fluid == 1:
        #        # Load properties for water from pre-generated CoolProp data
        #        properties = sio.loadmat('properties_H2O_HT_v3.mat')
        #        print('Fluid properties for water loaded successfully')
        #    elif fluid == 2:
        #        # Load properties for CO2 from pre-generated CoolProp data
        #        properties = sio.loadmat('properties_CO2.mat')
        #        print('Fluid properties for CO2 loaded successfully')
        #    else:
        #        print('No valid fluid selected')
        #        exit()

        # Length of each segment [m]
        Deltaz = np.sqrt(np.diff(x) ** 2 + np.diff(y) ** 2 + np.diff(z) ** 2)
        TotalLength = np.sum(Deltaz)  # Total length of co-axial heat exchanger [m]

        # Geometry Quality Control
        LoverR = Deltaz / radius
        smallestLoverR = np.min(LoverR)
        if smallestLoverR < 10:
            print(
                'Warning: smallest ratio of segment length over radius is less than 10. Good practice is to keep this ratio larger than 10.')

        RelativeLengthChanges = np.diff(Deltaz) / Deltaz[:-1]
        if np.max(np.abs(RelativeLengthChanges)) > 0.5:
            print(
                'Warning: abrupt change(s) in segment length detected, which may cause numerical instabilities. Good practice is to avoid abrupt length changes to obtain smooth results.')

        if self.SBTAccuracyDesired.value == 1:
            NoArgumentsFinitePipeCorrection = 25
            NoDiscrFinitePipeCorrection = 200
            NoArgumentsInfCylIntegration = 25
            NoDiscrInfCylIntegration = 200
            LimitPointSourceModel = 1.5
            LimitCylinderModelRequired = 25
            LimitInfiniteModel = 0.05
            LimitNPSpacingTime = 0.1
            LimitSoverL = 1.5
            M = 3
        elif self.SBTAccuracyDesired.value == 2:
            NoArgumentsFinitePipeCorrection = 50
            NoDiscrFinitePipeCorrection = 400
            NoArgumentsInfCylIntegration = 50
            NoDiscrInfCylIntegration = 400
            LimitPointSourceModel = 2.5
            LimitCylinderModelRequired = 50
            LimitInfiniteModel = 0.01
            LimitNPSpacingTime = 0.04
            LimitSoverL = 2
            M = 4
        elif self.SBTAccuracyDesired.value == 3:
            NoArgumentsFinitePipeCorrection = 100
            NoDiscrFinitePipeCorrection = 500
            NoArgumentsInfCylIntegration = 100
            NoDiscrInfCylIntegration = 500
            LimitPointSourceModel = 5
            LimitCylinderModelRequired = 100
            LimitInfiniteModel = 0.004
            LimitNPSpacingTime = 0.02
            LimitSoverL = 3
            M = 5
        elif self.SBTAccuracyDesired.value == 4:
            NoArgumentsFinitePipeCorrection = 200
            NoDiscrFinitePipeCorrection = 1000
            NoArgumentsInfCylIntegration = 200
            NoDiscrInfCylIntegration = 1000
            LimitPointSourceModel = 10
            LimitCylinderModelRequired = 200
            LimitInfiniteModel = 0.002
            LimitNPSpacingTime = 0.01
            LimitSoverL = 5
            M = 10
        elif self.SBTAccuracyDesired.value == 5:
            NoArgumentsFinitePipeCorrection = 400
            NoDiscrFinitePipeCorrection = 2000
            NoArgumentsInfCylIntegration = 400
            NoDiscrInfCylIntegration = 2000
            LimitPointSourceModel = 20
            LimitCylinderModelRequired = 400
            LimitInfiniteModel = 0.001
            LimitNPSpacingTime = 0.005
            LimitSoverL = 9
            M = 20

        # Use alpha_m instead of alpha_m_boiler for more conservative estimates
        timeforpointssource = np.max(
            Deltaz) ** 2 / alpha_m * LimitPointSourceModel  # Minimum time step size when point source model becomes applicable [s]
        timeforlinesource = radius ** 2 / alpha_m * LimitCylinderModelRequired  # Minimum time step size when line source model becomes applicable [s]
        timeforfinitelinesource = np.max(
            Deltaz) ** 2 / alpha_m * LimitInfiniteModel  # Minimum time step size when finite line source model should be considered [s]

        print('Precalculate SBT distributions ...')
        # Precalculate the thermal response with a line and cylindrical heat source
        # Precalculate finite pipe correction
        fpcminarg = min(Deltaz) ** 2 / (4 * alpha_m * times[-1])
        fpcmaxarg = max(Deltaz) ** 2 / (4 * alpha_m * min(np.diff(times)))
        Amin1vector = np.logspace(np.log10(fpcminarg) - 0.1, np.log10(fpcmaxarg) + 0.1, NoArgumentsFinitePipeCorrection)
        finitecorrectiony = np.zeros(NoArgumentsFinitePipeCorrection)

        for i in range(len(Amin1vector)):
            Amin1 = Amin1vector[i]
            Amax1 = 16 ** 2
            if Amin1 > Amax1:
                Amax1 = 10 * Amin1
            Adomain1 = np.logspace(np.log10(Amin1), np.log10(Amax1), NoDiscrFinitePipeCorrection)
            finitecorrectiony[i] = trapezoid(-1. / (Adomain1 * 4 * np.pi * self.krock.value) * (erfc(0.5 * Adomain1 ** 0.5)),
                                             Adomain1)

        # Precalculate Bessel integration for infinite cylinder
        # MIR besselminarg = alpha_m * min(np.diff(times)) / max(radius)**2
        # MIR besselmaxarg = alpha_m * timeforlinesource / min(radius)**2
        besselminarg = alpha_m * min(np.diff(times)) / radius ** 2
        besselmaxarg = alpha_m * timeforlinesource / radius ** 2
        deltazbessel = np.logspace(-10, 8, NoDiscrInfCylIntegration)
        argumentbesselvec = np.logspace(np.log10(besselminarg) - 0.5, np.log10(besselmaxarg) + 0.5,
                                        NoArgumentsInfCylIntegration)
        besselcylinderresult = np.zeros(NoArgumentsInfCylIntegration)

        for i in range(len(argumentbesselvec)):
            argumentbessel = argumentbesselvec[i]
            besselcylinderresult[i] = (2 / self.krock.value / np.pi ** 3 *
                                       trapezoid((1 - np.exp(-deltazbessel ** 2 * argumentbessel)) /
                                                 (deltazbessel ** 3 * (
                                                         jv(1, deltazbessel) ** 2 + yv(1, deltazbessel) ** 2)),
                                                 deltazbessel))

        # Optional: Uncomment the lines below to plot the results
        # import matplotlib.pyplot as plt
        # plt.loglog(Amin1vector, finitecorrectiony, 'k-')
        # plt.loglog(argumentbesselvec, besselcylinderresult, 'r-')
        # plt.show()

        # Precalculate finite pipe correction for boiler
        fpcminarg = min(Deltaz) ** 2 / (4 * alpha_m_boiler * times[-1])
        fpcmaxarg = max(Deltaz) ** 2 / (4 * alpha_m_boiler * min(np.diff(times)))
        Amin1vector_boiler = np.logspace(np.log10(fpcminarg) - 0.1, np.log10(fpcmaxarg) + 0.1,
                                         NoArgumentsFinitePipeCorrection)
        finitecorrectiony_boiler = np.zeros(NoArgumentsFinitePipeCorrection)

        for i in range(len(Amin1vector_boiler)):
            Amin1 = Amin1vector_boiler[i]
            Amax1 = 16 ** 2
            if Amin1 > Amax1:
                Amax1 = 10 * Amin1
            Adomain1 = np.logspace(np.log10(Amin1), np.log10(Amax1), NoDiscrFinitePipeCorrection)
            finitecorrectiony_boiler[i] = trapezoid(
                -1. / (Adomain1 * 4 * np.pi * k_m_boiler) * (erfc(0.5 * Adomain1 ** 0.5)), Adomain1)

        # Precalculate Bessel integration for infinite cylinder for boiler
        # MIR besselminarg = alpha_m_boiler * min(np.diff(times)) / max(radius)**2
        # MIR besselmaxarg = alpha_m_boiler * timeforlinesource / min(radius)**2
        besselminarg = alpha_m_boiler * min(np.diff(times)) / radius ** 2
        besselmaxarg = alpha_m_boiler * timeforlinesource / radius ** 2
        deltazbessel = np.logspace(-10, 8, NoDiscrInfCylIntegration)
        argumentbesselvec_boiler = np.logspace(np.log10(besselminarg) - 0.5, np.log10(besselmaxarg) + 0.5,
                                               NoArgumentsInfCylIntegration)
        besselcylinderresult_boiler = np.zeros(NoArgumentsInfCylIntegration)

        for i in range(len(argumentbesselvec_boiler)):
            argumentbessel = argumentbesselvec_boiler[i]
            besselcylinderresult_boiler[i] = (2 / k_m_boiler / np.pi ** 3 *
                                              trapezoid((1 - np.exp(-deltazbessel ** 2 * argumentbessel)) /
                                                        (deltazbessel ** 3 * (
                                                                jv(1, deltazbessel) ** 2 + yv(1, deltazbessel) ** 2)),
                                                        deltazbessel))

        # Optional: Uncomment the lines below to plot the results
        # import matplotlib.pyplot as plt
        # plt.loglog(Amin1vector_boiler, finitecorrectiony_boiler, 'k-')
        # plt.loglog(argumentbesselvec_boiler, besselcylinderresult_boiler, 'r-')
        # plt.show()
        print('SBT distributions calculated successfully')

        # MIR N = len(x) - 1
        N = len(x) - 1
        Nboiler = len(boilerelements)
        Nreg = N - Nboiler
        #Nreg = 1 + N - Nboiler
        self.krock.value_vector = np.full(N, self.krock.value)
        k_m_vector = np.zeros(N)
        k_m_vector[Nreg:] = k_m_boiler
        alpha_m_vector = k_m_vector / self.rhorock.value / self.cprock.value

        SMatrix = np.zeros((N, N))
        for i in range(N):
            SMatrix[i, :] = np.sqrt((0.5 * x[i] + 0.5 * x[i + 1] - 0.5 * x[:-1] - 0.5 * x[1:]) ** 2 +
                                    (0.5 * y[i] + 0.5 * y[i + 1] - 0.5 * y[:-1] - 0.5 * y[1:]) ** 2 +
                                    (0.5 * z[i] + 0.5 * z[i + 1] - 0.5 * z[:-1] - 0.5 * z[1:]) ** 2)
        SoverL = SMatrix / (np.ones((N, 1)) * Deltaz)
        SMatrixSorted = np.sort(SMatrix, axis=1)
        SortedIndices = np.argsort(SMatrix, axis=1)
        SoverLSorted = SMatrixSorted / (np.ones((N, 1)) * Deltaz)
        mindexNPCP = np.argmax(np.min(SoverLSorted, axis=1) < LimitSoverL)

        midpointsx = 0.5 * x[1:] + 0.5 * x[:-1]
        midpointsy = 0.5 * y[1:] + 0.5 * y[:-1]
        midpointsz = 0.5 * z[1:] + 0.5 * z[:-1]
        #midpointsx = 0.5 * x + 0.5 * x
        #midpointsy = 0.5 * y + 0.5 * y
        #midpointsz = 0.5 * z + 0.5 * z
        verticalchange = np.diff(z)
        # MIR
        #verticalchange = np.append(verticalchange, verticalchange[-1])

        if initialtemperatureprofile == 0:
            BBinitial = Tsurf - GeoGradient * midpointsz
            Tfluidupnodes = Tsurf - GeoGradient * z
            Tfluiddownnodes = Tsurf - GeoGradient * z
        elif initialtemperatureprofile == 1:
            BBinitial = np.interp(midpointsz, initialtemperaturedata[:, 0], initialtemperaturedata[:, 1])
            #Tfluidupnodes = np.interp(z, initialtemperaturedata[:, 0], initialtemperaturedata[:, 1])
            #Tfluiddownnodes = np.interp(z, initialtemperaturedata[:, 0], initialtemperaturedata[:, 1])
            Tfluidupnodes = np.interp(z[:-1], initialtemperaturedata[:, 0], initialtemperaturedata[:, 1])
            Tfluiddownnodes = np.interp(z[:-1], initialtemperaturedata[:, 0], initialtemperaturedata[:, 1])

        # MIR Tfluiddownmidpoints = 0.5 * Tfluiddownnodes[1:] + 0.5 * Tfluiddownnodes[:-1]
        # MIR Tfluidupmidpoints = 0.5 * Tfluidupnodes[1:] + 0.5 * Tfluidupnodes[:-1]
        Tfluiddownmidpoints = 0.5 * Tfluiddownnodes + 0.5 * Tfluiddownnodes
        Tfluidupmidpoints = 0.5 * Tfluidupnodes + 0.5 * Tfluidupnodes

        MaxSMatrixSorted = np.max(SMatrixSorted, axis=1)
        indicesyoucanneglectupfront = alpha_m * np.outer(np.ones(N - 1), times) / (
                MaxSMatrixSorted[1:, np.newaxis] * np.ones((1, len(times)))) ** 2 / LimitNPSpacingTime
        indicesyoucanneglectupfront[indicesyoucanneglectupfront > 1] = 1

        lastneighbourtoconsider = np.zeros(len(times), dtype=int)
        for i in range(len(times)):
            lntc = np.where(indicesyoucanneglectupfront[:, i] == 1)[0]
            if len(lntc) == 0:
                lastneighbourtoconsider[i] = 1
            else:
                lastneighbourtoconsider[i] = max(2, lntc[-1])

        distributionx = np.array([np.linspace(x[i], x[i + 1], M + 1) for i in range(N)])
        distributiony = np.array([np.linspace(y[i], y[i + 1], M + 1) for i in range(N)])
        distributionz = np.array([np.linspace(z[i], z[i + 1], M + 1) for i in range(N)])

        # Calculate initial pressure distribution
        if fluid == 1:  # H2O
            Pfluidupnodes = Pin * 1e5 - 1000 * g * z
            Pfluiddownnodes = Pfluidupnodes
            Pfluidupmidpoints = Pin * 1e5 - 1000 * g * midpointsz
            Pfluiddownmidpoints = Pfluidupmidpoints
        elif fluid == 2:  # CO2
            Pfluidupnodes = Pin * 1e5 - 500 * g * z
            Pfluiddownnodes = Pfluidupnodes
            Pfluidupmidpoints = Pin * 1e5 - 500 * g * midpointsz
            Pfluiddownmidpoints = Pfluidupmidpoints

        kk = 1
        maxrelativechange = 1
        print(f'Calculating initial pressure field ... | Iteration = 1')
        while kk < maxnumberofiterations and maxrelativechange > reltolerance:
            Pfluidupmidpointsold = Pfluidupmidpoints.copy()
            Pfluiddownmidpointsold = Pfluiddownmidpoints.copy()
            densityfluidupmidpoints = CP.PropsSI('D', 'P', Pfluidupmidpoints, 'T', Tin + 273.15, 'Water')
            densityfluiddownmidpoints = densityfluidupmidpoints
            Pfluiddownnodes = Pin * 1e5 - np.cumsum([0] + g * verticalchange * densityfluiddownmidpoints)
            Pfluidupnodes = Pfluiddownnodes
            # MIR    Pfluiddownmidpoints = 0.5 * Pfluiddownnodes[1:] + 0.5 * Pfluiddownnodes[:-1]
            Pfluiddownmidpoints = 0.5 * Pfluiddownnodes + 0.5 * Pfluiddownnodes
            Pfluidupmidpoints = Pfluiddownmidpoints
            maxrelativechange = np.max(np.abs((Pfluiddownmidpointsold - Pfluiddownmidpoints) / Pfluiddownmidpointsold))
            kk += 1
            print(
                f'Calculating initial pressure field ... | Iteration = {kk} | Max. Rel. change = {maxrelativechange:.5f}')

        densityfluiddownnodes = CP.PropsSI('D', 'P', Pfluiddownnodes, 'T', Tfluiddownnodes + 273.15, 'Water')
        densityfluidupnodes = densityfluiddownnodes

        # HT Contribution
        Phasefluiddownnodes = CP.PropsSI('Phase', 'P', Pfluiddownnodes, 'T', Tfluiddownnodes + 273.15, 'Water')
        Phasefluidupnodes = CP.PropsSI('Phase', 'P', Pfluidupnodes, 'T', Tfluidupnodes + 273.15, 'Water')
        Qfluiddownnodes = np.where(Phasefluiddownnodes == 0, 0, 1)
        Qfluidupnodes = np.where(Phasefluidupnodes == 0, 0, 1)

        if maxrelativechange < reltolerance:
            print('Initial pressure field calculated successfully')
        else:
            print('Initial pressure field calculated but maximum relative tolerance not met')

        # Calculate velocity field right at start-up using initial density distribution
        if coaxialflowtype == 1:  # CXA
            velocityfluiddownmidpoints = m / A_flow_annulus / densityfluiddownmidpoints
            velocityfluidupmidpoints = m / A_flow_centerpipe / densityfluidupmidpoints
            velocityfluiddownnodes = m / A_flow_annulus / densityfluiddownnodes
            velocityfluidupnodes = m / A_flow_centerpipe / densityfluidupnodes
        elif coaxialflowtype == 2:  # CXC
            velocityfluiddownmidpoints = m / A_flow_centerpipe / densityfluiddownmidpoints
            velocityfluidupmidpoints = m / A_flow_annulus / densityfluidupmidpoints
            velocityfluiddownnodes = m / A_flow_centerpipe / densityfluiddownnodes
            velocityfluidupnodes = m / A_flow_annulus / densityfluidupnodes

        # Obtain initial viscosity distribution of fluid [Pa·s]
        viscosityfluiddownmidpoints = CP.PropsSI('V', 'P', Pfluiddownmidpoints, 'T', Tfluiddownmidpoints + 273.15,
                                                 'Water')
        viscosityfluidupmidpoints = CP.PropsSI('V', 'P', Pfluidupmidpoints, 'T', Tfluidupmidpoints + 273.15, 'Water')

        # Obtain initial specific heat capacity distribution of fluid [J/kg·K]
        heatcapacityfluiddownmidpoints = CP.PropsSI('C', 'P', Pfluiddownmidpoints, 'T', Tfluiddownmidpoints + 273.15,
                                                    'Water')
        heatcapacityfluidupmidpoints = CP.PropsSI('C', 'P', Pfluidupmidpoints, 'T', Tfluidupmidpoints + 273.15, 'Water')

        # Obtain initial thermal conductivity distribution of fluid [W/m·K]
        thermalconductivityfluiddownmidpoints = CP.PropsSI('L', 'P', Pfluiddownmidpoints, 'T',
                                                           Tfluiddownmidpoints + 273.15, 'Water')
        thermalconductivityfluidupmidpoints = CP.PropsSI('L', 'P', Pfluidupmidpoints, 'T', Tfluidupmidpoints + 273.15,
                                                         'Water')

        # Obtain initial thermal diffusivity distribution of fluid [m²/s]
        alphafluiddownmidpoints = thermalconductivityfluiddownmidpoints / densityfluiddownmidpoints / heatcapacityfluiddownmidpoints
        alphafluidupmidpoints = thermalconductivityfluidupmidpoints / densityfluidupmidpoints / heatcapacityfluidupmidpoints

        # Obtain initial thermal expansion coefficient distribution of fluid [1/K]
        thermalexpansionfluiddownmidpoints = CP.PropsSI('ISOBARIC_EXPANSION_COEFFICIENT', 'P', Pfluiddownmidpoints, 'T',
                                                        Tfluiddownmidpoints + 273.15, 'Water')
        thermalexpansionfluidupmidpoints = CP.PropsSI('ISOBARIC_EXPANSION_COEFFICIENT', 'P', Pfluidupmidpoints, 'T',
                                                      Tfluidupmidpoints + 273.15, 'Water')

        # Obtain initial Prandtl number distribution of fluid [-]
        Prandtlfluiddownmidpoints = viscosityfluiddownmidpoints / densityfluiddownmidpoints / alphafluiddownmidpoints
        Prandtlfluidupmidpoints = viscosityfluidupmidpoints / densityfluidupmidpoints / alphafluidupmidpoints

        # Obtain initial Reynolds number distribution of fluid [-]
        if coaxialflowtype == 1:  # CXA (injection in annulus)
            Refluiddownmidpoints = densityfluiddownmidpoints * velocityfluiddownmidpoints * Dh_annulus / viscosityfluiddownmidpoints
            Refluidupmidpoints = densityfluidupmidpoints * velocityfluidupmidpoints * 2 * radiuscenterpipe / viscosityfluidupmidpoints
        elif coaxialflowtype == 2:  # CXC (injection in center pipe)
            Refluiddownmidpoints = densityfluiddownmidpoints * velocityfluiddownmidpoints * 2 * radiuscenterpipe / viscosityfluiddownmidpoints
            Refluidupmidpoints = densityfluidupmidpoints * velocityfluidupmidpoints * Dh_annulus / viscosityfluidupmidpoints

        # Initialize SBT algorithm linear system of equation matrices
        L = np.zeros((4 * N, 4 * N))
        R = np.zeros((4 * N, 1))
        Q = np.zeros((N, len(times)))
        self.Tresoutput.value = np.zeros(len(times))
        Poutput = np.zeros(len(times))
        self.Tresoutput.value[0] = Tsurf
        Poutput[0] = Pin * 1e5

        #Tfluidupnodesstore = np.zeros((N + 1, len(times)))
        #Tfluiddownnodesstore = np.zeros((N + 1, len(times)))
        Tfluidupnodesstore = np.zeros((N, len(times)))
        Tfluiddownnodesstore = np.zeros((N, len(times)))
        Tfluidupmidpointsstore = np.zeros((N, len(times)))
        #Tfluidupmidpointsstore = np.zeros((N + 1, len(times)))
        Tfluiddownmidpointsstore = np.zeros((N, len(times)))
        #Tfluiddownmidpointsstore = np.zeros((N + 1, len(times)))
        #Pfluidupnodesstore = np.zeros((N + 1, len(times)))
        #Pfluiddownnodesstore = np.zeros((N + 1, len(times)))
        Pfluidupnodesstore = np.zeros((N, len(times)))
        Pfluiddownnodesstore = np.zeros((N, len(times)))
        Pfluidupmidpointsstore = np.zeros((N, len(times)))
        Pfluiddownmidpointsstore = np.zeros((N, len(times)))
        #Pfluidupmidpointsstore = np.zeros((N + 1, len(times)))
        #Pfluiddownmidpointsstore = np.zeros((N + 1, len(times)))
        #Qfluidupnodesstore = np.zeros((N + 1, len(times)))
        #Qfluiddownnodesstore = np.zeros((N + 1, len(times)))
        #Phasefluidupnodesstore = np.zeros((N + 1, len(times)))
        #Phasefluiddownnodesstore = np.zeros((N + 1, len(times)))
        #Hfluidupnodesstore = np.zeros((N + 1, len(times)))
        #Hfluiddownnodesstore = np.zeros((N + 1, len(times)))
        Qfluidupnodesstore = np.zeros((N, len(times)))
        Qfluiddownnodesstore = np.zeros((N, len(times)))
        Phasefluidupnodesstore = np.zeros((N, len(times)))
        Phasefluiddownnodesstore = np.zeros((N, len(times)))
        Hfluidupnodesstore = np.zeros((N, len(times)))
        Hfluiddownnodesstore = np.zeros((N, len(times)))
        Qinterexchangestore = np.zeros((N, len(times)))
        QinterexchangeUp = np.zeros(N)
        velocityfluiddownmidpointsstore = np.zeros((N, len(times)))
        heatcapacityfluidupmidpointsstore = np.zeros((N, len(times)))

        # Store initial values
        Tfluidupnodesstore[:, 0] = Tfluidupnodes
        Tfluiddownnodesstore[:, 0] = Tfluiddownnodes
        Tfluidupmidpointsstore[:, 0] = BBinitial
        Tfluiddownmidpointsstore[:, 0] = BBinitial
        Pfluidupnodesstore[:, 0] = Pfluidupnodes
        Pfluiddownnodesstore[:, 0] = Pfluiddownnodes
        Pfluidupmidpointsstore[:, 0] = Pfluidupmidpoints
        Pfluiddownmidpointsstore[:, 0] = Pfluiddownmidpoints
        Qfluiddownnodesstore[:, 0] = Qfluiddownnodes
        Qfluidupnodesstore[:, 0] = Qfluidupnodes
        Phasefluidupnodesstore[:, 0] = Phasefluidupnodes
        Phasefluiddownnodesstore[:, 0] = Phasefluiddownnodes
        Qinterexchangestore[:, 0] = np.zeros(N)
        velocityfluiddownmidpointsstore[:, 0] = velocityfluiddownmidpoints
        heatcapacityfluidupmidpointsstore[:, 0] = heatcapacityfluidupmidpoints

        print('Pre-processing completed successfully. Starting simulation ...')

        # 3. Calculating
        import time
        start_time = time.time()

        for i in range(1, len(times)):
            Deltat = times[i] - times[i - 1]

            if k_center_pipe > 1:
                if times[i] < 1000:
                    k_center_pipe_corr = 1
                elif times[i] < 10000:
                    k_center_pipe_corr = max(1, 0.25 * k_center_pipe)
                else:
                    k_center_pipe_corr = k_center_pipe
            else:
                k_center_pipe_corr = k_center_pipe

            if alpha_m * Deltat / radius ** 2 > LimitCylinderModelRequired:
                CPCP = np.full(N, 1 / (4 * np.pi * self.krock.value) * expi(radius ** 2 / (4 * alpha_m * Deltat)))
            else:
                # MIR   CPCP = np.interp(alpha_m * Deltat / radius ** 2, argumentbesselvec, besselcylinderresult)
                # Calculate the interpolated values
                interp_cylinder = interp1d(argumentbesselvec, besselcylinderresult, kind='linear',
                                           fill_value="extrapolate")
                interp_cylinder_boiler = interp1d(argumentbesselvec_boiler, besselcylinderresult_boiler, kind='linear',
                                                  fill_value="extrapolate")

                # Interpolation results
                interp_value_cylinder = interp_cylinder(alpha_m * Deltat / radius ** 2)
                interp_value_cylinder_boiler = interp_cylinder_boiler(alpha_m_boiler * Deltat / radius ** 2)

                # Create arrays filled with the interpolated values
                ones_cylinder = np.ones(Nreg) * interp_value_cylinder
                ones_cylinder_boiler = np.ones(Nboiler) * interp_value_cylinder_boiler

                # Combine the two arrays
                CPCP = np.concatenate((ones_cylinder, ones_cylinder_boiler))

            if Deltat > timeforfinitelinesource:
                CPCP += np.interp(Deltaz ** 2 / (4 * alpha_m * Deltat), Amin1vector, finitecorrectiony)

            if i > 1:
                CPOP = np.zeros((N, i - 1))
                for j in range(i - 1):
                    t1 = times[i] - times[j]
                    t2 = times[i] - times[j + 1]
                    CPOP[:, j] = Deltaz / (4 * np.pi * np.sqrt(alpha_m * np.pi) * self.krock.value) * (
                            1 / np.sqrt(t1) - 1 / np.sqrt(t2))

                indexpsstart = 1
                indexpsend = np.where(timeforpointssource < (times[i] - times[:i]))[0]
                if len(indexpsend) == 0:
                    indexpsend = indexpsstart - 1
                else:
                    indexpsend = indexpsend[-1] - 1

                indexlsstart = indexpsend + 1
                indexlsend = np.where(timeforlinesource < (times[i] - times[:i]))[0]
                if len(indexlsend) == 0:
                    indexlsend = indexlsstart - 1
                else:
                    indexlsend = indexlsend[-1] - 1

                indexcsstart = max(indexpsend, indexlsend) + 1
                indexcsend = i - 2

                if indexcsstart <= indexcsend:
                    CPOP[:, indexcsstart:indexcsend] = np.interp(
                        alpha_m * (times[i] - times[indexcsstart:indexcsend]) / radius ** 2, argumentbesselvec,
                        besselcylinderresult)

                indexflsstart = indexpsend + 1
                indexflsend = np.where(timeforfinitelinesource < (times[i] - times[:i]))[0]
                if len(indexflsend) == 0:
                    indexflsend = indexflsstart - 1
                else:
                    indexflsend = indexflsend[-1] - 1

                if indexflsend >= indexflsstart:
                    CPOP[:, indexflsstart:indexflsend] += np.interp(
                        Deltaz ** 2 / (4 * alpha_m * (times[i] - times[indexflsstart:indexflsend])), Amin1vector,
                        finitecorrectiony)

            NPCP = np.zeros((N, N))
            NPCP += np.diag(CPCP)

            spacingtest = alpha_m * Deltat / SMatrixSorted[:, 1:] ** 2 / LimitNPSpacingTime
            maxspacingtest = np.max(spacingtest, axis=1)
            if maxspacingtest[0] < 1:
                maxindextoconsider = 0
            else:
                maxindextoconsider = np.where(maxspacingtest > 1)[0][-1]

            #if mindexNPCP < maxindextoconsider + 1:
            if mindexNPCP < maxindextoconsider:
                indicestocalculate = SortedIndices[:, mindexNPCP + 1:maxindextoconsider + 1]
                NPCP[range(N), indicestocalculate] = Deltaz[indicestocalculate] / (
                        4 * np.pi * k_m_vector[indicestocalculate] * SMatrix[range(N), indicestocalculate]) * erfc(
                    SMatrix[range(N), indicestocalculate] / np.sqrt(4 * alpha_m_vector[indicestocalculate] * Deltat))

            BB = np.zeros(N)
            if i > 1 and lastneighbourtoconsider[i] > 0:
                SMatrixRelevant = SMatrixSorted[:, 1:lastneighbourtoconsider[i] + 1]
                SoverLRelevant = SoverLSorted[:, 1:lastneighbourtoconsider[i] + 1]
                SortedIndicesRelevant = SortedIndices[:, 1:lastneighbourtoconsider[i] + 1]

                maxtimeindexmatrix = alpha_m * (times[i] - times[1:i]) / (SMatrixRelevant.flatten()[:, None] ** 2)
                allindices = np.arange(N * lastneighbourtoconsider[i] * (i - 1))
                pipeheatcomesfrom = SortedIndicesRelevant.flatten()[:, None]
                pipeheatgoesto = np.tile(np.arange(N), (lastneighbourtoconsider[i], 1)).flatten()[:, None]
                indicestoneglect = np.where(maxtimeindexmatrix.flatten() < LimitNPSpacingTime)[0]
                maxtimeindexmatrix = np.delete(maxtimeindexmatrix, indicestoneglect, axis=0)
                allindices = np.delete(allindices, indicestoneglect)

                indicesFoSlargerthan = np.where(maxtimeindexmatrix.flatten() > 10)[0]
                indicestotakeforpsFoS = allindices[indicesFoSlargerthan]

                allindices2 = np.delete(allindices, indicesFoSlargerthan)
                SoverLinearized = SoverLRelevant.flatten()[:, None]
                indicestotakeforpsSoverL = np.where(SoverLinearized.flatten() > LimitSoverL)[0]
                overallindicestotake = np.unique(np.concatenate((indicestotakeforpsSoverL, indicestotakeforpsFoS)))

                npipesheatsource = pipeheatcomesfrom[overallindicestotake]
                npipesheatreceiving = pipeheatgoesto[overallindicestotake]
                BB += np.bincount(npipesheatreceiving.flatten(),
                                  weights=Q[pipeheatcomesfrom[overallindicestotake], :-1].flatten() * Deltaz[
                                      npipesheatsource.flatten()] / (
                                                  4 * np.pi * k_m_vector[npipesheatsource.flatten()] * SMatrix[
                                                  pipeheatgoesto[overallindicestotake], pipeheatcomesfrom[
                                                      overallindicestotake]].flatten()) * erfc(SMatrix[pipeheatgoesto[
                                      overallindicestotake], pipeheatcomesfrom[
                                      overallindicestotake]].flatten() / np.sqrt(
                                      4 * alpha_m_vector[npipesheatsource.flatten()] * (times[i] - times[:-1]))),
                                  minlength=N)

            if i > 1:
                maxindextocalculate = lastneighbourtoconsider[i]
                maxindex = lastneighbourtoconsider[i] * (i - 1)
                maxtimeindexmatrix = alpha_m * (times[i] - times[1:i]) / (
                        SMatrixSorted[:, 1:maxindextocalculate + 1].flatten()[:, None] ** 2)
                allindices = np.arange(N * lastneighbourtoconsider[i] * (i - 1))
                allindices = np.delete(allindices, np.where(maxtimeindexmatrix.flatten() < LimitNPSpacingTime)[0])
                pipeheatcomesfrom = SortedIndices[:, 1:maxindextocalculate + 1].flatten()[:, None]
                pipeheatgoesto = np.tile(np.arange(N), (lastneighbourtoconsider[i], 1)).flatten()[:, None]
                NPCP[pipeheatgoesto.flatten()[allindices], pipeheatcomesfrom.flatten()[allindices]] += Deltaz[
                                                                                                           pipeheatcomesfrom.flatten()[
                                                                                                               allindices]] / (
                                                                                                               4 * np.pi *
                                                                                                               k_m_vector[
                                                                                                                   pipeheatcomesfrom.flatten()[
                                                                                                                       allindices]] *
                                                                                                               SMatrix[
                                                                                                                   pipeheatgoesto.flatten()[
                                                                                                                       allindices],
                                                                                                                   pipeheatcomesfrom.flatten()[
                                                                                                                       allindices]]) * erfc(
                    SMatrix[pipeheatgoesto.flatten()[allindices], pipeheatcomesfrom.flatten()[allindices]] / np.sqrt(
                        4 * alpha_m_vector[pipeheatcomesfrom.flatten()[allindices]] * Deltat))

            Vvector = 2 * np.pi * radius ** 2 * self.rhorock.value * self.cprock.value

            L[0:N, 0:N] = np.diag(Vvector / Deltat + np.sum(NPCP, axis=1))
            L[0:N, 3 * N:4 * N] = -1 * np.eye(N)

            L[N:2 * N, N:2 * N] = np.diag(Vvector / Deltat + np.sum(NPCP, axis=1))
            L[N:2 * N, 3 * N:4 * N] = -1 * np.eye(N)

            L[2 * N:3 * N, 0:N] = -1 * np.eye(N)
            L[2 * N:3 * N, 3 * N:4 * N] = np.diag(velocityfluidupmidpoints)
            L[2 * N:3 * N, 3 * N:4 * N] -= np.diag(velocityfluiddownmidpoints)
            L[2 * N:3 * N, 2 * N:3 * N] = np.diag(densityfluidupmidpoints) - np.diag(densityfluiddownmidpoints)

            L[3 * N:4 * N, 2 * N:3 * N] = np.diag(heatcapacityfluidupmidpoints)
            L[3 * N:4 * N, 0:N] = np.diag(densityfluidupmidpoints * heatcapacityfluidupmidpoints)
            L[3 * N:4 * N, 3 * N:4 * N] = np.diag(np.pi * (
                    2 * radiuscenterpipe) ** 2 * thermalconductivityfluidupmidpoints * velocityfluidupmidpoints * Deltat)

            Q[:, i] = BB

            #R[0:N] = Vvector * Tfluiddownmidpointsstore[:, i - 1] / Deltat
            #R[0:N] += Q[:, i]
            #R[N:2 * N] = Vvector * Tfluidupmidpointsstore[:, i - 1] / Deltat
            #R[N:2 * N] += Q[:, i]
            R[0:N, 0] = Vvector * Tfluiddownmidpointsstore[:, i - 1] / Deltat
            R[0:N, 0] += Q[:, i]
            R[N:2 * N, 0] = Vvector * Tfluidupmidpointsstore[:, i - 1] / Deltat
            R[N:2 * N, 0] += Q[:, i]

            #R[2 * N:3 * N] = Pfluidupmidpointsstore[:, i - 1] - Pfluiddownmidpointsstore[:,
            #                                                    i - 1] + velocityfluiddownmidpointsstore[:,
            #                                                             i - 1] * Pfluiddownmidpointsstore[:,
            #                                                                      i - 1] * Deltat
            R[2 * N:3 * N, 0] = Pfluidupmidpointsstore[:, i - 1] - Pfluiddownmidpointsstore[:,
                                                                i - 1] + velocityfluiddownmidpointsstore[:,
                                                                         i - 1] * Pfluiddownmidpointsstore[:,
                                                                                  i - 1] * Deltat

            #R[3 * N:4 * N] = heatcapacityfluidupmidpointsstore[:, i - 1] * Tfluidupmidpointsstore[:, i - 1]
            R[3 * N:4 * N, 0] = heatcapacityfluidupmidpointsstore[:, i - 1] * Tfluidupmidpointsstore[:, i - 1]

            try:
                solutions = np.linalg.solve(L, R)
            except np.linalg.LinAlgError:
                print(f'Simulation terminated prematurely due to linear algebra error at time step {i}.')
                break

            #BB = solutions[0:N]
            BB = solutions[0:N, 0]
            Tfluidupmidpointsstore[:, i] = BB
            Tfluidupmidpoints = BB
            Tfluidupmidpoints = Tfluidupmidpoints

            #BB = solutions[N:2 * N]
            BB = solutions[N:2 * N, 0]
            Tfluiddownmidpointsstore[:, i] = BB
            Tfluiddownmidpoints = BB
            Tfluiddownmidpoints = Tfluiddownmidpoints

            #BB = solutions[2 * N:3 * N]
            BB = solutions[2 * N:3 * N, 0]
            Pfluidupmidpointsstore[:, i] = BB
            Pfluidupmidpoints = BB
            Pfluidupmidpoints = Pfluidupmidpoints

            #BB = solutions[3 * N:4 * N]
            BB = solutions[3 * N:4 * N, 0]
            Pfluiddownmidpointsstore[:, i] = BB
            Pfluiddownmidpoints = BB
            Pfluiddownmidpoints = Pfluiddownmidpoints

            Pfluidupmidpoints = Pfluidupmidpointsstore[:, i - 1] + velocityfluidupmidpoints * Deltat
            Pfluiddownmidpoints = Pfluiddownmidpointsstore[:, i - 1] + velocityfluiddownmidpoints * Deltat

            Pfluidupnodes = np.append(Pfluidupnodesstore[0, i], np.diff(Pfluidupmidpoints))
            Pfluiddownnodes = np.append(Pfluiddownnodesstore[0, i], np.diff(Pfluiddownmidpoints))

            Pfluidupnodesstore[:, i] = Pfluidupnodes
            Pfluiddownnodesstore[:, i] = Pfluiddownnodes

            Qinterexchangestore[:, i] = QinterexchangeUp

            if Tfluidupmidpointsstore[-1, i] >= 100:
                print(f'Warning: fluid temperature exceeds boiling point at time step {i}. Simulation may be invalid.')

            if Tfluiddownmidpointsstore[-1, i] >= 100:
                print(f'Warning: fluid temperature exceeds boiling point at time step {i}. Simulation may be invalid.')

        end_time = time.time()
        print(f'Simulation completed successfully in {end_time - start_time:.2f} seconds.')

        # plt.figure()
        # plt.plot(times / (24 * 3600), Tfluiddownmidpointsstore[-1, :], label='Tfluiddownmidpoints')
        # plt.plot(times / (24 * 3600), Tfluidupmidpointsstore[-1, :], label='Tfluidupmidpoints')
        # plt.xlabel('Time (days)')
        # plt.ylabel('Temperature (°C)')
        # lt.legend()
        # plt.title('Temperature vs Time')
        # plt.grid()
        # plt.show()

        model.logger.info(f'complete {str(__class__)}: {sys._getframe().f_code.co_name}')

    @lru_cache(maxsize=1024)
    #@profile
    def Calculate_Uloop(self, model):
        """
        Calculate the U-loop version of the SBT model
        """
        model.logger.info(f'Init {str(__class__)}: {sys._getframe().f_code.co_name}')
        self.averagegradient.value = np.average(self.gradient.value[0:self.numseg.value])
        self.Trock.value = self.Tsurf.value + (self.averagegradient.value * model.wellbores.lateral_endpoint_depth.value)

        lateralflowallocation = []
        for i in range(model.wellbores.numnonverticalsections.value):
            lateralflowallocation.append(1 / model.wellbores.numnonverticalsections.value)

        # interpolate time steps - but consider ignoring the first step.
        # simulation times [s] (must start with 0; to obtain smooth results,
        # abrupt changes in time step size should be avoided. logarithmic spacing is recommended)
        initial_times = np.linspace(0, self.initial_final_timestep_transition.value, self.initial_timestep_count.value)
        initial_time_interval = initial_times[1] - initial_times[0]
        final_start = self.initial_final_timestep_transition.value + initial_time_interval
        final_times = np.logspace(np.log10(final_start), np.log10(model.surfaceplant.plant_lifetime.value * 365 * 24 * 3600), int(self.final_timestep_count.value))
        times = np.concatenate([initial_times, final_times])
        # Note 1: When providing a variable injection temperature or flow rate, a finer time grid should be considered.
        # Below is one with long term time steps of about 36 days.
        # times = [0] + list(range(100, 10000, 100)) + list(np.logspace(np.log10(100*100), np.log10(0.1*365*24*3600), 40)) + list(np.arange(0.2*365*24*3600, 20*365*24*3600, 0.1*365*24*3600))
        # Note 2: To capture the start-up effects, several small time steps need to be taken during
        # the first 99000 seconds in the time vector considered.
        # To speed up the simulation, this can be avoided with limited impact on the long-term results.
        # For example, an alternative time vector would be:
        # times = [0] + list(range(100, 1000, 100)) + list(range(1000, 10000, 1000)) + list(np.logspace(np.log10(100*100), np.log10(20*365*24*3600), 75))

        # (x,y,z)-coordinates of centerline of injection well, production well and laterals
        # The vectors storing the x-, y- and z-coordinates should be column vectors
        # To obtain smooth results, abrupt changes in segment lengths should be avoided.
        # Coordinates of injection well (coordinates are provided from top to bottom in the direction of flow)
        xinj, yinj, zinj, xprod, yprod, zprod, xlat, ylat, zlat = generate_wireframe_model(model.wellbores.lateral_endpoint_depth.value,
                                                                                           model.wellbores.numnonverticalsections.value,
                                                                                           model.wellbores.lateral_spacing.value,
                                                                                           model.wellbores.element_length.value,
                                                                                           model.wellbores.junction_depth.value,
                                                                                           model.wellbores.vertical_section_length.value,
                                                                                           model.wellbores.lateral_inclination_angle.value * np.pi / 180.0,
                                                                                           model.wellbores.vertical_wellbore_spacing.value,
                                                                                           self.generate_wireframe_graphics.value)

        # Merge x-, y-, and z-coordinates
        x = np.concatenate((xinj, xprod))
        y = np.concatenate((yinj, yprod))
        z = np.concatenate((zinj, zprod))

        for i in range(model.wellbores.numnonverticalsections.value):
            x = np.concatenate((x, xlat[:, i].reshape(-1, 1).flatten()))
            y = np.concatenate((y, ylat[:, i].reshape(-1, 1).flatten()))
            z = np.concatenate((z, zlat[:, i].reshape(-1, 1).flatten()))

        gamma = 0.577215665  # Euler's constant
        alpha_f = model.surfaceplant.k_fluid.value / model.surfaceplant.rho_fluid.value / model.surfaceplant.cp_fluid.value  # Fluid thermal diffusivity [m2/s]
        Pr_f = model.surfaceplant.mu_fluid.value / model.surfaceplant.rho_fluid.value / alpha_f  # Fluid Prandtl number [-]
        alpha_m = self.krock.value / self.rhorock.value / self.cprock.value  # Thermal diffusivity medium [m2/s]

        # interconnections lists the indices of interconnections between inj, prod, and laterals
        # (this will be used to take care of the duplicate coordinates of the start and end points of the laterals)
        interconnections = np.concatenate((np.array([len(xinj)],dtype=int), np.array([len(xprod)],dtype=int), (np.ones(model.wellbores.numnonverticalsections.value - 1, dtype=int) * len(xlat))))
        interconnections = np.cumsum(interconnections)

        # radiusvector stores radius of each element in a vector [m]
        radiusvector = np.concatenate([np.ones(len(xinj) + len(xprod) - 2) * (model.wellbores.prodwelldiam.quantity().to('m').magnitude / 2), np.ones(model.wellbores.numnonverticalsections.value * len(xlat) - model.wellbores.numnonverticalsections.value) * (model.wellbores.nonverticalwellborediameter.quantity().to('m').magnitude / 2.0)])
        Dvector = radiusvector * 2  # Diameter of each element [m]
        lateralflowallocation = lateralflowallocation / np.sum(lateralflowallocation)  # Ensure the sum equals 1

        Deltaz = np.sqrt((x[1:] - x[:-1]) ** 2 + (y[1:] - y[:-1]) ** 2 + (z[1:] - z[:-1]) ** 2)  # Length of each segment [m]
        Deltaz = np.delete(Deltaz, interconnections - 1)  # Removes the phantom elements due to duplicate coordinates
        TotalLength = np.sum(Deltaz)  # Total length of all elements (for informational purposes only) [m]

        # Quality Control
        LoverR = Deltaz / radiusvector  # Ratio of pipe segment length to radius along the wellbore [-]
        smallestLoverR = np.min(LoverR)  # Smallest ratio of pipe segment length to pipe radius. This ratio should be larger than 10. [-]

        if smallestLoverR < 10:
            msg = 'Warning: smallest ratio of segment length over radius is less than 10. Good practice is to keep this ratio larger than 10.'
            print(f'{msg}')
            model.logger.warning(msg)

        if model.wellbores.numnonverticalsections.value > 1:
           DeltazOrdered = np.concatenate((Deltaz[0:(interconnections[0]-1)], Deltaz[(interconnections[1]-2):(interconnections[2]-3)], Deltaz[(interconnections[0]-1):(interconnections[1]-2)]))
        else:
            DeltazOrdered = np.concatenate((Deltaz[0:interconnections[0] - 1], Deltaz[interconnections[1] - 1:-1], Deltaz[interconnections[0]:interconnections[1] - 2]))

        RelativeLengthChanges = (DeltazOrdered[1:] - DeltazOrdered[:-1]) / DeltazOrdered[:-1]

        if max(abs(RelativeLengthChanges)) > 0.6:
            msg = 'Warning: abrupt change(s) in segment length detected, which may cause numerical instabilities. Good practice is to avoid abrupt length changes to obtain smooth results.'
            print(f'{msg}')
            model.logger.warning(msg)

        for dd in range(1, model.wellbores.numnonverticalsections.value + 1):
            if abs(xinj[-1] - xlat[0][dd - 1]) > 1e-12 or abs(yinj[-1] - ylat[0][dd - 1]) > 1e-12 or abs(zinj[-1] - zlat[0][dd - 1]) > 1e-12:
                msg = f'Error: Coordinate mismatch between bottom of injection well and start of lateral #{dd}'
                print(f'{msg}')
                model.logger.fatal(msg)
                model.logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')
                raise ValueError(msg)

            if abs(xprod[0] - xlat[-1][dd - 1]) > 1e-12 or abs(yprod[0] - ylat[-1][dd - 1]) > 1e-12 or abs(zprod[0] - zlat[-1][dd - 1]) > 1e-12:
                msg = f'Error: Coordinate mismatch between bottom of production well and end of lateral #{dd}'
                print(f'{msg}')
                model.logger.fatal(msg)
                model.logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')
                raise ValueError(msg)

        if len(lateralflowallocation) != model.wellbores.numnonverticalsections.value:
            msg = 'Error: Length of array "lateralflowallocation" does not match the number of laterals'
            print(f'{msg}')
            model.logger.fatal(msg)
            model.logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')
            raise ValueError(msg)

        # Read injection temperature profile if provided
        Tinstore = [0] * len(times)
        if self.injection_temperature_model == 2:
            # User has provided injection temperature in an Excel spreadsheet.
            num = pd.read_excel(self.injection_temperature_file.value)
            Tintimearray = np.array(num.iloc[:, 0])
            Tintemperaturearray = np.array(num.iloc[:, 1])
            # Quality control
            if len(Tintimearray) < 2:
                msg = 'Error: Provided injection temperature profile should have at least 2 values'
                print(f'{msg}')
                model.logger.fatal(msg)
                model.logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')
                raise ValueError(msg)

            if Tintimearray[0] != 0:
                msg = 'Error: First time value in the user-provided injection temperature profile does not equal 0 s'
                print(f'{msg}')
                model.logger.fatal(msg)
                model.logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')
                raise ValueError(msg)

            if abs(Tintimearray[-1] - times[-1]) > 10e-6:
                msg = 'Error: Last time value in the user-provided injection temperature profile does not equal the final value in the "times" array'
                print(f'{msg}')
                model.logger.fatal(msg)
                model.logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')
                raise ValueError(msg)

            else:
                # Ensure final time values "exactly" match to prevent interpolation issues at the final time step
                Tintimearray[-1] = times[-1]
            Tinstore[0] = Tintemperaturearray[0]
        else:
            Tinstore[0] = model.wellbores.Tinj.value

        # The value for m used at each time step is stored in this array (is either constant or interpolated from a user-provided mass flow rate profile)
        mstore = np.zeros(len(times))

        # User has provided mass flow rate in an Excel spreadsheet.
        if self.flow_rate_model.value == 2:
            data = pd.read_excel(self.flow_rate_file.value)
            mtimearray = data.iloc[:, 0].values  # This array has the times provided by the user
            mflowratearray = data.iloc[:, 1].values  # This array has the injection temperatures provided by the user

            # Quality control
            if len(mtimearray) < 2:
                msg = 'Error: Provided flow rate profile should have at least 2 values'
                print(f'{msg}')
                model.logger.fatal(msg)
                model.logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')
                raise ValueError(msg)

            if mtimearray[0] != 0:
                msg = 'Error: First time value in user-provided flow rate profile does not equal to 0 s'
                print(f'{msg}')
                model.logger.fatal(msg)
                model.logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')
                raise ValueError(msg)

            if abs(mtimearray[-1] - times[-1]) > 10e-6:
                msg = 'Error: Last time value in user-provided flow rate profile does not equal to final value in "times" array'
                print(f'{msg}')
                model.logger.fatal(msg)
                model.logger.info(f'Complete {str(__name__)}: {sys._getframe().f_code.co_name}')
                raise ValueError(msg)

            else:
                # Ensure final time values "exactly" match to prevent interpolation issues at the final time step
                mtimearray[-1] = times[-1]

            mstore[0] = mflowratearray[0]
        else:
            mstore[0] = model.wellbores.prodwellflowrate.value

        # assume default values
        NoArgumentsFinitePipeCorrection = 25
        NoDiscrFinitePipeCorrection = 200
        NoArgumentsInfCylIntegration = 25
        NoDiscrInfCylIntegration = 200
        LimitPointSourceModel = 1.5
        LimitCylinderModelRequired = 25
        LimitInfiniteModel = 0.05
        LimitNPSpacingTime = 0.1
        LimitSoverL = 1.5
        M = 3
        if self.SBTAccuracyDesired.value == 2:
            NoArgumentsFinitePipeCorrection = 50
            NoDiscrFinitePipeCorrection = 400
            NoArgumentsInfCylIntegration = 50
            NoDiscrInfCylIntegration = 400
            LimitPointSourceModel = 2.5
            LimitCylinderModelRequired = 50
            LimitInfiniteModel = 0.01
            LimitNPSpacingTime = 0.04
            LimitSoverL = 2
            M = 4
        elif self.SBTAccuracyDesired.value == 3:
            NoArgumentsFinitePipeCorrection = 100
            NoDiscrFinitePipeCorrection = 500
            NoArgumentsInfCylIntegration = 100
            NoDiscrInfCylIntegration = 500
            LimitPointSourceModel = 5
            LimitCylinderModelRequired = 100
            LimitInfiniteModel = 0.004
            LimitNPSpacingTime = 0.02
            LimitSoverL = 3
            M = 5
        elif self.SBTAccuracyDesired.value == 4:
            NoArgumentsFinitePipeCorrection = 200
            NoDiscrFinitePipeCorrection = 1000
            NoArgumentsInfCylIntegration = 200
            NoDiscrInfCylIntegration = 1000
            LimitPointSourceModel = 10
            LimitCylinderModelRequired = 200
            LimitInfiniteModel = 0.002
            LimitNPSpacingTime = 0.01
            LimitSoverL = 5
            M = 10
        elif self.SBTAccuracyDesired.value == 5:
            NoArgumentsFinitePipeCorrection = 400
            NoDiscrFinitePipeCorrection = 2000
            NoArgumentsInfCylIntegration = 400
            NoDiscrInfCylIntegration = 2000
            LimitPointSourceModel = 20
            LimitCylinderModelRequired = 400
            LimitInfiniteModel = 0.001
            LimitNPSpacingTime = 0.005
            LimitSoverL = 9
            M = 20

        timeforpointssource = max(Deltaz)**2 / alpha_m * LimitPointSourceModel  # Calculates minimum time step size when point source model becomes applicable [s]
        timeforlinesource = max(radiusvector)**2 / alpha_m * LimitCylinderModelRequired  # Calculates minimum time step size when line source model becomes applicable [s]
        timeforfinitelinesource = max(Deltaz)**2 / alpha_m * LimitInfiniteModel  # Calculates minimum time step size when finite line source model should be considered [s]

        fpcminarg = min(Deltaz)**2 / (4 * alpha_m * times[-1])
        fpcmaxarg = max(Deltaz)**2 / (4 * alpha_m * (min(times[1:] - times[:-1])))
        Amin1vector = np.logspace(np.log10(fpcminarg) - 0.1, np.log10(fpcmaxarg) + 0.1, NoArgumentsFinitePipeCorrection)
        finitecorrectiony = np.zeros(NoArgumentsFinitePipeCorrection)

        for i, Amin1 in enumerate(Amin1vector):
            Amax1 = (16)**2
            if Amin1 > Amax1:
                Amax1 = 10 * Amin1
            Adomain1 = np.logspace(np.log10(Amin1), np.log10(Amax1), NoDiscrFinitePipeCorrection)
            finitecorrectiony[i] = np.trapz(-1 / (Adomain1 * 4 * np.pi * self.krock.value) * erfc(1/2 * np.power(Adomain1, 1/2)), Adomain1)

        besselminarg = alpha_m * (min(times[1:] - times[:-1])) / max(radiusvector)**2
        besselmaxarg = alpha_m * timeforlinesource / min(radiusvector)**2
        deltazbessel = np.logspace(-10, 8, NoDiscrInfCylIntegration)
        argumentbesselvec = np.logspace(np.log10(besselminarg) - 0.5, np.log10(besselmaxarg) + 0.5, NoArgumentsInfCylIntegration)
        besselcylinderresult = np.zeros(NoArgumentsInfCylIntegration)

        for i, argumentbessel in enumerate(argumentbesselvec):
            besselcylinderresult[i] = 2 / (self.krock.value * np.pi**3) * np.trapz((1 - np.exp(-deltazbessel**2 * argumentbessel)) / (deltazbessel**3 * (jv(1, deltazbessel)**2 + yv(1, deltazbessel)**2)), deltazbessel)

        N = len(Deltaz)  # Number of elements
        elementcenters = 0.5 * np.column_stack((x[1:], y[1:], z[1:])) + 0.5 * np.column_stack((x[:-1], y[:-1], z[:-1]))  # Matrix that stores the mid point coordinates of each element
        interconnections = interconnections - 1
        elementcenters = np.delete(elementcenters, interconnections.reshape(-1,1), axis=0)  # Remove duplicate coordinates
        SMatrix = np.zeros((N, N))  # Initializes the spacing matrix, which holds the distance between center points of each element [m]

        for i in range(N):
            SMatrix[i, :] = np.sqrt((elementcenters[i, 0] - elementcenters[:, 0])**2 + (elementcenters[i, 1] - elementcenters[:, 1])**2 + (elementcenters[i, 2] - elementcenters[:, 2])**2)

        SoverL = np.zeros((N, N))  # Initializes the ratio of spacing to element length matrix

        for i in range(N):
             SMatrix[i, :] = np.sqrt((elementcenters[i, 0] - elementcenters[:, 0])**2 + (elementcenters[i, 1] - elementcenters[:, 1])**2 + (elementcenters[i, 2] - elementcenters[:, 2])**2)
        SoverL[i, :] = SMatrix[i, :] / Deltaz[i]

        SortedIndices = np.argsort(SMatrix, axis=1, kind = 'stable') # Getting the indices of the sorted elements
        SMatrixSorted = np.take_along_axis(SMatrix, SortedIndices, axis=1)  # Sorting the spacing matrix

        SoverLSorted = SMatrixSorted / Deltaz

        mindexNPCP = np.where(np.min(SoverLSorted, axis=0) < LimitSoverL)[0][-1]  # Finding the index where the ratio is less than the limit

        midpointsx = elementcenters[:, 0]  # x-coordinate of center of each element [m]
        midpointsy = elementcenters[:, 1]  # y-coordinate of center of each element [m]
        midpointsz = elementcenters[:, 2]  # z-coordinate of center of each element [m]
        BBinitial = self.Tsurf.value - (self.gradient1.value / 1000.0) * midpointsz  # Initial temperature at center of each element [degC]

        previouswaterelements = np.zeros(N)
        previouswaterelements[0:] = np.arange(-1,N-1)

        for i in range(model.wellbores.numnonverticalsections.value ):
            previouswaterelements[interconnections[i + 1] - i-1] = len(xinj) - 2

        previouswaterelements[len(xinj) - 1] = 0

        lateralendpoints = []
        for i in range(1,model.wellbores.numnonverticalsections.value +1):
            lateralendpoints.append(len(xinj) - 2 + len(xprod) - 1 + i * ((xlat[:, 0]).size- 1))
        lateralendpoints = np.array(lateralendpoints)

        MaxSMatrixSorted = np.max(SMatrixSorted, axis=0)

        indicesyoucanneglectupfront = alpha_m * (np.ones((N-1, 1)) * times) / (MaxSMatrixSorted[1:].reshape(-1, 1) * np.ones((1, len(times))))**2 / LimitNPSpacingTime
        indicesyoucanneglectupfront[indicesyoucanneglectupfront > 1] = 1

        lastneighbourtoconsider = np.zeros(len(times))
        for i in range(len(times)):
            lntc = np.where(indicesyoucanneglectupfront[:, i] == 1)[0]
            if len(lntc) == 0:
                lastneighbourtoconsider[i] = 1
            else:
                lastneighbourtoconsider[i] = max(2, lntc[-1] + 1)

        distributionx = np.zeros((len(x) - 1, M + 1))
        distributiony = np.zeros((len(x) - 1, M + 1))
        distributionz = np.zeros((len(x) - 1, M + 1))

        for i in range(len(x) - 1):
            distributionx[i, :] = np.linspace(x[i], x[i + 1], M + 1).reshape(-1)
            distributiony[i, :] = np.linspace(y[i], y[i + 1], M + 1).reshape(-1)
            distributionz[i, :] = np.linspace(z[i], z[i + 1], M + 1).reshape(-1)

        # Remove duplicates
        distributionx = np.delete(distributionx, interconnections, axis=0)
        distributiony = np.delete(distributiony, interconnections, axis=0)
        distributionz = np.delete(distributionz, interconnections, axis=0)

        # Initialize SBT algorithm linear system of equation matrices
        L = np.zeros((3 * N, 3 * N))                # Will store the "left-hand side" of the system of equations
        R = np.zeros((3 * N, 1))                    # Will store the "right-hand side" of the system of equations
        Q = np.zeros((N, len(times)))               # Initializes the heat pulse matrix, i.e., the heat pulse emitted by each element at each time step
        self.Tresoutput.value = np.zeros(len(times))              # Initializes the production temperatures array
        Twprevious = BBinitial                       # At time zero, the initial fluid temperature corresponds to the initial local rock temperature
        self.Tresoutput.value[0] = self.Tsurf.value                           # At time zero, the outlet temperature is the initial local fluid temperature at the surface, which corresponds to the surface temperature
        TwMatrix = np.zeros((len(times), N))         # Initializes the matrix that holds the fluid temperature over time
        TwMatrix[0, :] = Twprevious

        count = 0
        for i in range(1, len(times)):
            count = count + 1
            Deltat = times[i] - times[i - 1]  # Current time step size [s]

            # If the user has provided an injection temperature profile, current value of model.wellbores.Tinj.value is calculated
            if self.injection_temperature_model == 2:
                model.wellbores.Tinj.value = np.interp(times[i], Tintimearray, Tintemperaturearray)
            Tinstore[i] = model.wellbores.Tinj.value  # Value that is used for model.wellbores.Tinj.value at each time step gets stored for postprocessing purposes

            # If the user has provided a flow rate profile, current value of model.wellbores.prodwellflowrate.value is calculated
            if self.flow_rate_model.value == 2:
                model.wellbores.prodwellflowrate.value = np.interp(times[i], mtimearray, mflowratearray)
            mstore[i] = model.wellbores.prodwellflowrate.value  # Value that is used for model.wellbores.prodwellflowrate.value at each time step gets stored for postprocessing purposes

            # Velocities and thermal resistances are calculated each time step as the flow rate is allowed to vary each time step
            uvertical = model.wellbores.prodwellflowrate.value / model.surfaceplant.rho_fluid.value / (np.pi * (model.wellbores.prodwelldiam.quantity().to('m').magnitude / 2) ** 2)  # Fluid velocity in vertical injector and producer [m/s]
            ulateral = model.wellbores.prodwellflowrate.value / model.surfaceplant.rho_fluid.value / (np.pi * (model.wellbores.nonverticalwellborediameter.quantity().to('m').magnitude / 2.0) ** 2) * lateralflowallocation  # Fluid velocity in each lateral [m/s]
            uvector = np.hstack((uvertical * np.ones(len(xinj) + len(xprod) - 2)))

            for dd in range(model.wellbores.numnonverticalsections.value ):
                uvector = np.hstack((uvector, ulateral[dd] * np.ones(len(xlat[:, 0]) - 1)))

            if model.wellbores.prodwellflowrate.value > 0.1:
                Revertical = model.surfaceplant.rho_fluid.value * uvertical * (2 * (model.wellbores.prodwelldiam.quantity().to('m').magnitude / 2)) / model.surfaceplant.mu_fluid.value  # Fluid Reynolds number in injector and producer [-]
                Nuvertical = 0.023 * Revertical ** (4 / 5) * Pr_f ** 0.4  # Nusselt Number in injector and producer (we assume turbulent flow) [-]
            else:
                Nuvertical = 1  # At low flow rates, we assume we are simulating the condition of well shut-in and set the Nusselt number to 1 (i.e., conduction only) [-]

            hvertical = Nuvertical * model.surfaceplant.k_fluid.value / (2 * (model.wellbores.prodwelldiam.quantity().to('m').magnitude / 2))  # Heat transfer coefficient in injector and producer [W/m2/K]
            Rtvertical = 1 / (np.pi * hvertical * 2 * (model.wellbores.prodwelldiam.quantity().to('m').magnitude / 2))  # Thermal resistance in injector and producer (open-hole assumed)

            if model.wellbores.prodwellflowrate.value > 0.1:
                Relateral = model.surfaceplant.rho_fluid.value * ulateral * (2 * (model.wellbores.nonverticalwellborediameter.quantity().to('m').magnitude / 2.0)) / model.surfaceplant.mu_fluid.value  # Fluid Reynolds number in lateral [-]
                Nulateral = 0.023 * Relateral ** (4 / 5) * Pr_f ** 0.4  # Nusselt Number in lateral (we assume turbulent flow) [-]
            else:
                Nulateral = np.ones(model.wellbores.numnonverticalsections.value)  # At low flow rates, we assume we are simulating the condition of well shut-in and set the Nusselt number to 1 (i.e., conduction only) [-]

            hlateral = Nulateral * model.surfaceplant.k_fluid.value / (2 * (model.wellbores.nonverticalwellborediameter.quantity().to('m').magnitude / 2.0))  # Heat transfer coefficient in lateral [W/m2/K]
            Rtlateral = 1 / (np.pi * hlateral * 2 * (model.wellbores.nonverticalwellborediameter.quantity().to('m').magnitude / 2.0))  # Thermal resistance in lateral (open-hole assumed)

            Rtvector = Rtvertical * np.ones(len(radiusvector))  # Store thermal resistance of each element in a vector

            for dd in range(1, model.wellbores.numnonverticalsections.value + 1):
                if dd < model.wellbores.numnonverticalsections.value:
                    Rtvector[interconnections[dd] - dd : interconnections[dd + 1] - dd] = Rtlateral[dd - 1] * np.ones(len(xlat[:, 0]))
                else:
                    Rtvector[interconnections[dd] - model.wellbores.numnonverticalsections.value :] = Rtlateral[dd - 1] * np.ones(len(xlat[:, 0]) - 1)

            # CPCP (= Current pipe, current pulses)
            if alpha_m * Deltat / max(radiusvector)**2 > LimitCylinderModelRequired:
                CPCP = np.ones(N) * 1 / (4 * np.pi * self.krock.value) * exp1(radiusvector**2 / (4 * alpha_m * Deltat)) # Use line source model if possible
            else:
                CPCP = np.ones(N) * np.interp(alpha_m * Deltat / radiusvector**2, argumentbesselvec, besselcylinderresult) # Use cylindrical source model if required

            if Deltat > timeforfinitelinesource:  # For long time steps, the finite length correction should be applied
                CPCP = CPCP + np.interp(Deltaz**2 / (4 * alpha_m * Deltat), Amin1vector, finitecorrectiony)

            # CPOP (= Current pipe, old pulses)
            if i > 1:  # After the second time step, we need to keep track of previous heat pulses
                CPOP = np.zeros((N, i-1))
                indexpsstart = 0
                indexpsend = np.where(timeforpointssource < (times[i] - times[1:i]))[-1]
                if indexpsend.size > 0:
                    indexpsend = indexpsend[-1] + 1
                else:
                    indexpsend = indexpsstart - 1
                if indexpsend >= indexpsstart:  # Use point source model if allowed

                    CPOP[:, 0:indexpsend] = Deltaz * np.ones((N, indexpsend)) / (4 * np.pi * np.sqrt(alpha_m * np.pi) * self.krock.value) * (
                            np.ones(N) * (1 / np.sqrt(times[i] - times[indexpsstart + 1:indexpsend + 2]) -
                            1 / np.sqrt(times[i] - times[indexpsstart:indexpsend+1])))
                indexlsstart = indexpsend + 1
                indexlsend = np.where(timeforlinesource < (times[i] - times[1:i]))[0]
                if indexlsend.size == 0:
                    indexlsend = indexlsstart - 1
                else:
                    indexlsend = indexlsend[-1]

                if indexlsend >= indexlsstart:  # Use line source model for more recent heat pulse events

                    CPOP[:, indexlsstart:indexlsend+1] = np.ones((N,1)) * 1 / (4*np.pi*self.krock.value) * (exp1((radiusvector**2).reshape(len(radiusvector ** 2),1) / (4*alpha_m*(times[i]-times[indexlsstart:indexlsend+1])).reshape(1,len(4 * alpha_m * (times[i] - times[indexlsstart:indexlsend+1]))))-\
                        exp1((radiusvector**2).reshape(len(radiusvector ** 2),1) / (4 * alpha_m * (times[i]-times[indexlsstart+1:indexlsend+2])).reshape(1,len(4 * alpha_m * (times[i] - times[indexlsstart+1:indexlsend+2])))))
                    #pdb.set_trace()
                indexcsstart = max(indexpsend, indexlsend) + 1
                indexcsend = i - 2

                if indexcsstart <= indexcsend:  # Use cylindrical source model for the most recent heat pulses

                    CPOPPH = np.zeros((CPOP[:, indexcsstart:indexcsend+1].shape))
                    CPOPdim = CPOP[:, indexcsstart:indexcsend+1].shape
                    CPOPPH = CPOPPH.T.ravel()
                    CPOPPH = (np.ones(N) * (
                                np.interp(alpha_m * (times[i] - times[indexcsstart:indexcsend+1]).reshape(len(times[i] - times[indexcsstart:indexcsend+1]),1) / (radiusvector ** 2).reshape(len(radiusvector ** 2),1).T, argumentbesselvec, besselcylinderresult) - \
                                np.interp(alpha_m * (times[i] - times[indexcsstart+1: indexcsend+2]).reshape(len(times[i] - times[indexcsstart+1:indexcsend+2]),1) / (radiusvector ** 2).reshape(len(radiusvector ** 2),1).T, argumentbesselvec, besselcylinderresult))).reshape(-1,1)
                    CPOPPH=CPOPPH.reshape((CPOPdim),order='F')
                    CPOP[:, indexcsstart:indexcsend+1] = CPOPPH
                indexflsstart = indexpsend + 1
                indexflsend = np.where(timeforfinitelinesource < (times[i] - times[1:i]))[-1]
                if indexflsend.size == 0:
                    indexflsend = indexflsstart - 1
                else:
                    indexflsend = indexflsend[-1] - 1

                if indexflsend >= indexflsstart:  # Perform finite length correction if needed
                    CPOP[:, indexflsstart:indexflsend+2] = CPOP[:, indexflsstart:indexflsend+2] + (np.interp(np.matmul((Deltaz.reshape(len(Deltaz),1) ** 2),np.ones((1,indexflsend-indexflsstart+2))) / np.matmul(np.ones((N,1)),(4 * alpha_m * (times[i] - times[indexflsstart:indexflsend+2]).reshape(len(times[i] - times[indexflsstart:indexflsend+2]),1)).T), Amin1vector, finitecorrectiony) - \
                    np.interp(np.matmul((Deltaz.reshape(len(Deltaz),1) ** 2),np.ones((1,indexflsend-indexflsstart+2))) / np.matmul(np.ones((N,1)),(4 * alpha_m * (times[i] - times[indexflsstart+1:indexflsend+3]).reshape(len(times[i] - times[indexflsstart:indexflsend+2]),1)).T), Amin1vector, finitecorrectiony))

            NPCP = np.zeros((N, N))
            np.fill_diagonal(NPCP, CPCP)

            spacingtest = alpha_m * Deltat / SMatrixSorted[:, 1:]**2 / LimitNPSpacingTime
            maxspacingtest = np.max(spacingtest,axis=0)

            if maxspacingtest[0] < 1:
                    maxindextoconsider = 0
            else:
                   maxindextoconsider = np.where(maxspacingtest > 1)[0][-1]+1

            if mindexNPCP < maxindextoconsider + 1:
                indicestocalculate = SortedIndices[:, mindexNPCP + 1:maxindextoconsider + 1]
                indicestocalculatetranspose = indicestocalculate.T
                indicestocalculatelinear = indicestocalculate.ravel()
                indicestostorematrix = (indicestocalculate - 1) * N + np.arange(1, N) * np.ones((1, maxindextoconsider - mindexNPCP + 1))
                indicestostorematrixtranspose = indicestostorematrix.T
                indicestostorelinear = indicestostorematrix.ravel()
                NPCP[indicestostorelinear] = Deltaz[indicestocalculatelinear] / (4 * np.pi * self.krock.value * SMatrix[indicestostorelinear]) * erf(SMatrix[indicestostorelinear] / np.sqrt(4 * alpha_m * Deltat))

            # Calculate and store neighbouring pipes for current pulse as set of line sources
            if mindexNPCP > 1 and maxindextoconsider > 0:
                lastindexfls = min(mindexNPCP, maxindextoconsider + 1)
                indicestocalculate = SortedIndices[:, 1:lastindexfls]
                indicestocalculatetranspose = indicestocalculate.T
                indicestocalculatelinear = indicestocalculate.ravel()
                indicestostorematrix = (indicestocalculate) * N + np.arange(N).reshape(-1,1) * np.ones((1, lastindexfls - 1), dtype=int)
                indicestostorematrixtranspose = indicestostorematrix.T
                indicestostorelinear = indicestostorematrix.ravel()
                midpointindices = np.matmul(np.ones((lastindexfls - 1, 1)), np.arange( N ).reshape(1,N)).T
                midpointsindices = midpointindices.ravel().astype(int)
                rultimate = np.sqrt(np.square((midpointsx[midpointsindices].reshape(len(midpointsindices),1)*( np.ones((1, M + 1))) - distributionx[indicestocalculatelinear,:])) +
                                    np.square((midpointsy[midpointsindices].reshape(len(midpointsindices),1)*( np.ones((1, M + 1))) - distributiony[indicestocalculatelinear,:])) +
                                    np.square((midpointsz[midpointsindices].reshape(len(midpointsindices),1)*( np.ones((1, M + 1))) - distributionz[indicestocalculatelinear,:])))

                NPCP[np.unravel_index(indicestostorelinear, NPCP.shape, 'F')] =  Deltaz[indicestocalculatelinear] / M * np.sum((1 - erf(rultimate / np.sqrt(4 * alpha_m * Deltat))) / (4 * np.pi * self.krock.value * rultimate) * np.matmul(np.ones((N*(lastindexfls-1),1)),np.concatenate((np.array([1/2]), np.ones(M-1), np.array([1/2]))).reshape(-1,1).T), axis=1)

            # NPOP (= Neighbouring pipes, old pulses)
            BB = np.zeros((N, 1))
            if i > 1 and lastneighbourtoconsider[i] > 0:
                SMatrixRelevant = SMatrixSorted[:, 1 : int(lastneighbourtoconsider[i] + 1)]
                SoverLRelevant = SoverLSorted[:, 1 : int(lastneighbourtoconsider[i]) + 1]
                SortedIndicesRelevant = SortedIndices[:, 1 : int(lastneighbourtoconsider[i]) + 1]
                maxtimeindexmatrix = alpha_m * np.ones((N * int(lastneighbourtoconsider[i]), 1)) * (times[i] - times[1:i]) / (SMatrixRelevant.ravel().reshape(-1,1) * np.ones((1,i-1)))**2

                allindices = np.arange(N * int(lastneighbourtoconsider[i]) * (i - 1))
                pipeheatcomesfrom = np.matmul(SortedIndicesRelevant.T.ravel().reshape(len(SortedIndicesRelevant.ravel()),1), np.ones((1,i - 1)))
                pipeheatgoesto = np.arange(N).reshape(N,1) * np.ones((1, int(lastneighbourtoconsider[i])))
                pipeheatgoesto = pipeheatgoesto.transpose().ravel().reshape(len(pipeheatgoesto.ravel()),1) * np.ones((1, i - 1))
                # Delete everything smaller than LimitNPSpacingTime
                indicestoneglect = np.where((maxtimeindexmatrix.transpose()).ravel() < LimitNPSpacingTime)[0]

                maxtimeindexmatrix = np.delete(maxtimeindexmatrix, indicestoneglect)
                allindices = np.delete(allindices, indicestoneglect)
                indicesFoSlargerthan = np.where(maxtimeindexmatrix.ravel() > 10)[0]
                indicestotakeforpsFoS = allindices[indicesFoSlargerthan]

                allindices2 = allindices.copy()
                allindices2[indicesFoSlargerthan] = []
                SoverLinearized = SoverLRelevant.ravel().reshape(len(SoverLRelevant.ravel()),1) * np.ones((1, i - 1))
                indicestotakeforpsSoverL = np.where(SoverLinearized.transpose().ravel()[allindices2] > LimitSoverL)[0]
                overallindicestotakeforpsSoverL = allindices2[indicestotakeforpsSoverL]
                remainingindices = allindices2.copy()

                remainingindices=np.delete(remainingindices,indicestotakeforpsSoverL)

                NPOP = np.zeros((N * int(lastneighbourtoconsider[i]), i - 1))

                # Use point source model when FoS is very large
                if len(indicestotakeforpsFoS) > 0:
                    deltatlinear1 = np.ones(N * int(lastneighbourtoconsider[i]), 1) * (times[i] - times[1:i-1])
                    deltatlinear1 = deltatlinear1.ravel()[indicestotakeforpsFoS]
                    deltatlinear2 = np.ones((N * int(lastneighbourtoconsider[i]), 1)) * (times[i] - times[0:i-2])
                    deltatlinear2 = deltatlinear2[indicestotakeforpsFoS]
                    deltazlinear = pipeheatcomesfrom[indicestotakeforpsFoS]
                    SMatrixlinear = SMatrixRelevant.flatten(order='F')
                    NPOPFoS = Deltaz[deltazlinear] / (4 * np.pi * self.krock.value * SMatrixlinear[indicestotakeforpsFoS]) * (erfc(SMatrixlinear[indicestotakeforpsFoS] / np.sqrt(4 * alpha_m * deltatlinear2)) -
                        erfc(SMatrixlinear[indicestotakeforpsFoS] / np.sqrt(4 * alpha_m * deltatlinear1)))

                    NPOP[indicestotakeforpsFoS] = NPOPFoS

                # Use point source model when SoverL is very large
                if len(overallindicestotakeforpsSoverL) > 0:
                    deltatlinear1 = np.ones((N * int(lastneighbourtoconsider[i]), 1)) * (times[i] - times[1:i-2]).ravel()
                    deltatlinear1 = deltatlinear1[overallindicestotakeforpsSoverL]
                    deltatlinear2 = np.ones((N * int(lastneighbourtoconsider[i]), 1)) * (times[i] - times[0:i-2]).ravel()
                    deltatlinear2 = deltatlinear2[overallindicestotakeforpsSoverL]
                    deltazlinear = pipeheatcomesfrom[overallindicestotakeforpsSoverL]
                    SMatrixlinear = SMatrixRelevant.flatten(order='F')
                    NPOPSoverL = Deltaz[deltazlinear] / (4 * np.pi * self.krock.value * SMatrixlinear[overallindicestotakeforpsSoverL]) * (erfc(SMatrixlinear[overallindicestotakeforpsSoverL] / np.srt(4 * alpha_m * deltatlinear2)) -
                        erfc(SMatrixlinear[overallindicestotakeforpsSoverL] / np.sqrt(4 * alpha_m * deltatlinear1)))

                    NPOP[overallindicestotakeforpsSoverL] = NPOPSoverL

                # Use finite line source model for remaining pipe segments
                if len(remainingindices) > 0:
                    deltatlinear1 = np.ones((N * int(lastneighbourtoconsider[i]), 1)) * (times[i] - times[1:i])
                    deltatlinear1 = (deltatlinear1.transpose()).ravel()[remainingindices]
                    deltatlinear2 = np.ones((N * int(lastneighbourtoconsider[i]), 1)) * (times[i] - times[0:i-1])
                    deltatlinear2 = (deltatlinear2.transpose()).ravel()[remainingindices]
                    deltazlinear = (pipeheatcomesfrom.T).ravel()[remainingindices]
                    midpointstuff = (pipeheatgoesto.transpose()).ravel()[remainingindices]
                    rultimate = np.sqrt(np.square((midpointsx[midpointstuff.astype(int)].reshape(len(midpointsx[midpointstuff.astype(int)]),1)*( np.ones((1, M + 1))) - distributionx[deltazlinear.astype(int),:])) +
                                     np.square((midpointsy[midpointstuff.astype(int)].reshape(len(midpointsy[midpointstuff.astype(int)]),1)*( np.ones((1, M + 1))) - distributiony[deltazlinear.astype(int),:])) +
                                     np.square((midpointsz[midpointstuff.astype(int)].reshape(len(midpointsz[midpointstuff.astype(int)]),1)*( np.ones((1, M + 1))) - distributionz[deltazlinear.astype(int),:])))
                    NPOPfls = Deltaz[deltazlinear.astype(int)].reshape(len(Deltaz[deltazlinear.astype(int)]),1).T / M * np.sum((-erf(rultimate / np.sqrt(4 * alpha_m * np.ravel(deltatlinear2).reshape(len(np.ravel(deltatlinear2)),1)*np.ones((1, M + 1)))) + erf(rultimate / np.sqrt(4 * alpha_m * np.ravel(deltatlinear1).reshape(len(np.ravel(deltatlinear1)),1)*np.ones((1, M + 1))))) / (4 * np.pi * self.krock.value * rultimate) *  np.matmul((np.ones((len(remainingindices),1))),(np.concatenate((np.array([1/2]),np.ones(M - 1),np.array([1/2])))).reshape(-1,1).T), axis=1)
                    NPOPfls = NPOPfls.T
                    dimensions = NPOP.shape
                    NPOP=NPOP.T.ravel()
                    NPOP[remainingindices.reshape((len(remainingindices),1))] = NPOPfls
                    NPOP = NPOP.reshape((dimensions[1],dimensions[0])).T

            # Put everything together and calculate BB (= impact of all previous heat pulses from old neighbouring elements on current element at current time)
                Qindicestotake = SortedIndicesRelevant.ravel().reshape((N * int(lastneighbourtoconsider[i]), 1))*np.ones((1,i-1)) + \
                                np.ones((N * int(lastneighbourtoconsider[i]), 1)) * N * np.arange(i - 1)
                Qindicestotake = Qindicestotake.astype(int)
                Qlinear = Q.T.ravel()[Qindicestotake]
                BBPS = NPOP * Qlinear
                BBPS = np.sum(BBPS, axis=1)
                BBPSindicestotake = np.arange(N).reshape((N, 1)) + N * np.arange(int(lastneighbourtoconsider[i])).reshape((1, int(lastneighbourtoconsider[i])))
                BBPSMatrix = BBPS[BBPSindicestotake]
                BB = np.sum(BBPSMatrix, axis=1)

            if i > 1:
                BBCPOP = np.sum(CPOP * Q[:, 1:i], axis=1)
            else:
                BBCPOP = np.zeros(N)

            # Populate L and R for fluid heat balance for first element (which has the injection temperature specified)
            L[0, 0] = 1 / Deltat + uvector[0] / Deltaz[0] * (self.percent_implicit.value) * 2
            L[0, 2] = -4 / np.pi / Dvector[0]**2 / model.surfaceplant.rho_fluid.value / model.surfaceplant.cp_fluid.value
            R[0, 0] = 1 / Deltat * Twprevious[0] + uvector[0] / Deltaz[0] * model.wellbores.Tinj.value * 2 - uvector[0] / Deltaz[0] * Twprevious[0] * (1 - self.percent_implicit.value) * 2

            # Populate L and R for rock temperature equation for first element
            L[1, 0] = 1
            L[1, 1] = -1
            L[1, 2] = Rtvector[0]
            R[1, 0] = 0
            # Populate L and R for SBT algorithm for first element
            L[2, np.arange(2,3*N,3)] = NPCP[0,0:N]
            L[2,1] = 1
            R[2, 0] = -BBCPOP[0].item() - BB[0].item() + BBinitial[0].item()

            for iiii in range(2, N+1):
                # Heat balance equation
                L[0+(iiii - 1) * 3,  (iiii - 1) * 3] = 1 / Deltat + uvector[iiii-1] / Deltaz[iiii-1] / 2 * (self.percent_implicit.value) * 2
                L[0+(iiii - 1) * 3, 2 + (iiii - 1) * 3] = -4 / np.pi / Dvector[iiii-1] ** 2 / model.surfaceplant.rho_fluid.value / model.surfaceplant.cp_fluid.value

                if iiii == len(xinj):  # Upcoming pipe has first element temperature sum of all incoming water temperatures
                   for j in range(len(lateralendpoints)):
                    L[0+ (iiii - 1) * 3, 0 + (lateralendpoints[j]) * 3] = -ulateral[j] / Deltaz[iiii-1] / 2 / (self.percent_implicit.value) * 2
                    R[0+(iiii - 1) * 3, 0] = 1 / Deltat * Twprevious[iiii-1] + uvector[iiii-1] / Deltaz[iiii-1] * (
                            -Twprevious[iiii-1] + np.sum(lateralflowallocation[j] * Twprevious[lateralendpoints[j]])) / 2 * (
                                                       1 - self.percent_implicit.value) * 2
                else:
                    L[0+(iiii-1) * 3, 0 + (int(previouswaterelements[iiii-1])) * 3] = -uvector[iiii-1] / Deltaz[iiii-1] / 2 * (
                            self.percent_implicit.value) * 2
                    R[0+(iiii-1) * 3, 0] = 1 / Deltat * Twprevious[iiii-1] + uvector[iiii-1] / Deltaz[iiii-1] * (
                            -Twprevious[iiii-1] + Twprevious[int(previouswaterelements[iiii-1])]) / 2 * (1 - self.percent_implicit.value) * 2

                # Rock temperature equation
                L[1 + (iiii - 1) * 3,  (iiii - 1) * 3] = 1
                L[1 + (iiii - 1) * 3, 1 + (iiii - 1) * 3] = -1
                L[1 + (iiii - 1) * 3, 2 + (iiii - 1) * 3] = Rtvector[iiii-1]
                R[1 + (iiii - 1) * 3, 0] = 0

                # SBT equation
                L[2 + (iiii - 1) * 3, np.arange(2,3*N,3)] = NPCP[iiii-1, :N]
                L[2 + (iiii - 1) * 3, 1 + (iiii - 1) * 3] = 1
                R[2 + (iiii - 1) * 3, 0] = -BBCPOP[iiii - 1].item() - BB[iiii - 1].item() + BBinitial[iiii - 1].item()

            # Solving the linear system of equations
            Sol = np.linalg.solve(L, R)

            # Extracting Q array for current heat pulses
            Q[:, i] = Sol.ravel()[2::3]

            # Extracting fluid temperature
            TwMatrix[i, :] = Sol.ravel()[np.arange(0,3*N,3)]

            # Storing fluid temperature for the next time step
            Twprevious = Sol.ravel()[np.arange(0,3*N,3)]

            # Calculating the fluid outlet temperature at the top of the first element
            top_element_index = len(xinj) + len(xprod) - 3
            self.Tresoutput.value[i] = Twprevious[top_element_index] + (Twprevious[top_element_index] - Twprevious[top_element_index - 1]) * 0.5
            if False:
                print(times[i] / 3.154e+7, ',', self.Tresoutput.value[i])

        # Save the nonlinear Time results as 2D array Output Parameter
        self.NonLinearTime_temperature.value = np.column_stack((times, self.Tresoutput.value))

        # define the linear time array, in years
        self.timevector.value = np.linspace(0, model.surfaceplant.plant_lifetime.value, model.economics.timestepsperyear.value * model.surfaceplant.plant_lifetime.value)

        # Now interpolate that non-linear time array into a linear array in time with associated values.
        # times locally are in seconds, so convert to years to match the linear time array, which is in years
        times_years = times / 3.154e+7
        times_years[0] = 0.0  # Ensure the first time step is 0.0
        times_years[-1] = model.surfaceplant.plant_lifetime.value  # Ensure the last time step is the plant lifetime

        # Calculate the maximum temperature for the SBT output.
        max_temperature = np.max(self.Tresoutput.value)

        # Replace the first year of values in the SBT output array
        # with the maximum temperature for the first year of the SBT output.
        # This moderates the behavior for the first few months of the SBT output.
        i = 0
        while times_years[i] < 1.0:
            self.Tresoutput.value[i] = max_temperature
            i = i + 1

        linear_values = []
        # interpolate the values of self.Tresoutput.value to the linear time array
        for t in self.timevector.value:
            linear_values.append(interpolator(t, times_years, self.Tresoutput.value))
        self.Tresoutput.value = linear_values

        # Calculate the Initial Reservoir Heat Content
        self.InitialReservoirHeatContent.value = mstore[0] * model.surfaceplant.cp_fluid.value * (self.Tresoutput.value[0] - Tinstore[0]) / 1e6  # Calculates the heat production [MW]

        model.logger.info(f'complete {str(__class__)}: {sys._getframe().f_code.co_name}')

# FIXME WIP/broken
# ruff: noqa

import logging
import unittest

import pytest

from geophires_x.GeoPHIRESUtils import DensityWater
from geophires_x.GeoPHIRESUtils import EnthalpyH20_func
from geophires_x.GeoPHIRESUtils import EntropyH20_func
from geophires_x.GeoPHIRESUtils import HeatCapacityWater
from geophires_x.GeoPHIRESUtils import RecoverableHeat
from geophires_x.GeoPHIRESUtils import VaporPressureWater
from geophires_x.Parameter import OutputParameter
from geophires_x.Parameter import floatParameter
from geophires_x.Parameter import intParameter
from geophires_x.Units import EnthalpyUnit
from geophires_x.Units import HeatUnit
from geophires_x.Units import MassUnit
from geophires_x.Units import PercentUnit
from geophires_x.Units import PowerUnit
from geophires_x.Units import TemperatureUnit
from geophires_x.Units import Units
from geophires_x.Units import VolumeUnit
from hip_ra.HIP_RA import HIP_RA


class TestHipRa(unittest.TestCase):
    #  The class initializes successfully with default parameters and logging enabled.
    def test_initialization_with_default_parameters_and_logging_enabled(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        assert hip_ra.logger.isEnabledFor(logging.INFO) == True
        assert hip_ra.reservoir_temperature.Name == 'Reservoir Temperature'
        assert hip_ra.reservoir_temperature.value == 150.0
        assert hip_ra.reservoir_temperature.Min == 50
        assert hip_ra.reservoir_temperature.Max == 1000
        assert hip_ra.reservoir_temperature.UnitType == Units.TEMPERATURE
        assert hip_ra.reservoir_temperature.PreferredUnits == TemperatureUnit.CELSIUS
        assert hip_ra.reservoir_temperature.CurrentUnits == TemperatureUnit.CELSIUS
        assert hip_ra.reservoir_temperature.Required == True
        assert hip_ra.reservoir_temperature.ErrMessage == 'assume default reservoir temperature (150 deg-C)'
        assert hip_ra.reservoir_temperature.ToolTipText == 'Reservoir Temperature [150 dec-C]'

    #  The class reads input parameters from a file and updates the corresponding attributes.
    def test_reading_input_parameters_from_file_and_updating_attributes(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        hip_ra.read_parameters()
        assert hip_ra.reservoir_temperature.value == 150.0
        assert hip_ra.rejection_temperature.value == 25.0
        assert hip_ra.reservoir_porosity.value == 18.0
        assert hip_ra.reservoir_area.value == 81.0
        assert hip_ra.reservoir_thickness.value == 0.286
        assert hip_ra.reservoir_life_cycle.value == 30
        assert hip_ra.rock_heat_capacity.value == 2840000000000.0
        assert hip_ra.fluid_heat_capacity.value == -1.0
        assert hip_ra.rock_heat_capacity.value == 1.0
        assert hip_ra.fluid_density.value == -1.0
        assert hip_ra.rock_density.value == 2550000000000.0
        assert hip_ra.RecoverableHeat.value == -1.0
        assert hip_ra.WaterContent.value == 18.0
        assert hip_ra.RockContent.value == 82.0
        assert hip_ra.rejection_temperature_k.value == 298.15
        assert hip_ra.rejection_entropy.value == 0.367
        assert hip_ra.rejection_enthalpy.value == 104.8

    #  The class calculates the output parameters based on the input parameters.
    def test_calculating_output_parameters_based_on_input_parameters(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        hip_ra.read_parameters()
        hip_ra.Calculate()
        assert hip_ra.reservoir_volume.value == pytest.approx(23.166, abs=1e-3)
        assert hip_ra.reservoir_stored_heat.value == pytest.approx(1.034e14, abs=1e10)
        assert hip_ra.reservoir_mass.value == pytest.approx(4.159e13, abs=1e10)
        assert hip_ra.reservoir_enthalpy.value == pytest.approx(0.0, abs=1e-3)
        assert hip_ra.wellhead_heat.value == pytest.approx(0.0, abs=1e-3)
        assert hip_ra.reservoir_recovery_factor.value == pytest.approx(0.0, abs=1e-3)
        assert hip_ra.reservoir_available_heat.value == pytest.approx(0.0, abs=1e-3)
        assert hip_ra.reservoir_producible_heat.value == pytest.approx(0.0, abs=1e-3)
        assert hip_ra.reservoir_producible_electricity.value == pytest.approx(0.0, abs=1e-3)

    #  The class prints the output parameters to a file.
    def test_printing_output_parameters_to_file(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        hip_ra.read_parameters()
        hip_ra.Calculate()
        hip_ra.PrintOutputs()
        with open('HIP.out') as f:
            content = f.readlines()
            assert content[0].strip() == '                               *********************'
            assert content[1].strip() == '                               ***HIP CASE REPORT***'
            assert content[2].strip() == '                               *********************'
            assert content[4].strip() == '                           ***SUMMARY OF RESULTS***'
            assert content[6].strip() == '      Reservoir Temperature:          150.00 deg-C'
            assert content[7].strip() == '      Reservoir Volume:               23.17 km3'
            assert content[8].strip() == '      Stored Heat:                    1.03e+14 kJ'
            assert content[9].strip() == '      Fluid Produced:                 4.16e+13 kg'
            assert content[10].strip() == '      Enthalpy:                       0.00 kJ/kg'
            assert content[11].strip() == '      Wellhead Heat:                  0.00 kJ'
            assert content[12].strip() == '      Recovery Factor:                0.00 %'
            assert content[13].strip() == '      Available Heat:                 0.00 kJ'
            assert content[14].strip() == '      Producible Heat:                0.00 kJ'
            assert content[15].strip() == '      Producible Electricity:         0.00 MW'

    #  The class handles the case when no parameters are provided in the input file.
    def test_handling_no_parameters_in_input_file(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        hip_ra.read_parameters()
        assert hip_ra.reservoir_temperature.value == 150.0
        assert hip_ra.rejection_temperature.value == 25.0
        assert hip_ra.reservoir_porosity.value == 18.0
        assert hip_ra.reservoir_area.value == 81.0
        assert hip_ra.reservoir_thickness.value == 0.286
        assert hip_ra.reservoir_life_cycle.value == 30
        assert hip_ra.rock_heat_capacity.value == 2840000000000.0
        assert hip_ra.fluid_heat_capacity.value == -1.0
        assert hip_ra.HeatCapacityOfRock.value == 1.0
        assert hip_ra.fluid_density.value == -1.0
        assert hip_ra.rock_density.value == 2550000000000.0
        assert hip_ra.RecoverableHeat.value == -1.0
        assert hip_ra.WaterContent.value == 18.0
        assert hip_ra.RockContent.value == 82.0
        assert hip_ra.rejection_temperature_k.value == 298.15
        assert hip_ra.rejection_entropy.value == 0.367
        assert hip_ra.rejection_enthalpy.value == 104.8

    #  The class handles the case when the input file is not found.
    def test_handling_input_file_not_found(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        with pytest.raises(FileNotFoundError):
            hip_ra.read_parameters()

    #  The class handles the case when the input file cannot be accessed due to permission issues.
    def test_handling_input_file_permission_issues(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        with pytest.raises(PermissionError):
            hip_ra.read_parameters()

    #  The class handles the case when an exception occurs while writing the output file.
    def test_handling_exception_while_writing_output_file(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        hip_ra.read_parameters()
        hip_ra.Calculate()
        with pytest.raises(Exception):
            hip_ra.PrintOutputs()

    #  The class handles the case when the output file is empty.
    def test_handling_empty_output_file(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        hip_ra.read_parameters()
        hip_ra.Calculate()
        hip_ra.PrintOutputs()
        with open('HIP.out', 'w') as f:
            f.write('')
        with pytest.raises(AssertionError):
            hip_ra.PrintOutputs()

    #  The class handles the case when the units of the output parameters do not match the preferred units.
    def test_handling_output_parameter_units_not_matching_preferred_units(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        hip_ra.read_parameters()
        hip_ra.Calculate()
        hip_ra.reservoir_volume.CurrentUnits = VolumeUnit.METERS3
        hip_ra.reservoir_stored_heat.CurrentUnits = HeatUnit.J
        hip_ra.reservoir_mass.CurrentUnits = MassUnit.GRAM
        hip_ra.reservoir_enthalpy.CurrentUnits = EnthalpyUnit.KJPERKG
        hip_ra.wellhead_heat.CurrentUnits = HeatUnit.J
        hip_ra.reservoir_recovery_factor.CurrentUnits = PercentUnit.PERCENT
        hip_ra.reservoir_available_heat.CurrentUnits = HeatUnit.J
        hip_ra.reservoir_producible_heat.CurrentUnits = HeatUnit.J
        hip_ra.reservoir_producible_electricity.CurrentUnits = PowerUnit.W
        hip_ra.PrintOutputs()
        with open('HIP.out') as f:
            content = f.readlines()
            assert content[7].strip() == '      Reservoir Volume:               2.32e+10 m3'
            assert content[8].strip() == '      Stored Heat:                    1.03e+14 J'
            assert content[9].strip() == '      Fluid Produced:                 4.16e+13 g'
            assert content[10].strip() == '      Enthalpy:                       0.00 J/kg'
            assert content[11].strip() == '      Wellhead Heat:                  0.00 J'
            assert content[12].strip() == '      Recovery Factor:                0.00 %'
            assert content[13].strip() == '      Available Heat:                 0.00 J'
            assert content[14].strip() == '      Producible Heat:                0.00 J'
            assert content[15].strip() == '      Producible Electricity:         0.00 W'

    #  The class converts units of the output parameters if specified in the input file.
    def test_convert_units_of_output_parameters(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        hip_ra.OutputParameterDict['Reservoir Volume (reservoir)'].CurrentUnits = VolumeUnit.METERS3
        hip_ra.OutputParameterDict['Stored Heat (reservoir)'].CurrentUnits = HeatUnit.J

        # FIXME WIP
        # hip_ra.OutputParameterDict['Fluid Produced'].CurrentUnits = MassUnit.GRAM

        hip_ra.OutputParameterDict['Enthalpy (reservoir)'].CurrentUnits = EnthalpyUnit.KJPERKG
        hip_ra.OutputParameterDict['Wellhead Heat (reservoir)'].CurrentUnits = HeatUnit.J
        hip_ra.OutputParameterDict['Recovery Factor (reservoir)'].CurrentUnits = PercentUnit.PERCENT
        hip_ra.OutputParameterDict['Available Heat (reservoir)'].CurrentUnits = HeatUnit.J
        hip_ra.OutputParameterDict['Producible Heat (reservoir)'].CurrentUnits = HeatUnit.J
        hip_ra.OutputParameterDict['Producible Electricity (reservoir)'].CurrentUnits = PowerUnit.W
        hip_ra.PrintOutputs()
        assert hip_ra.OutputParameterDict['Reservoir Volume (reservoir)'].CurrentUnits == VolumeUnit.KILOMETERS3
        assert hip_ra.OutputParameterDict['Stored Heat (reservoir)'].CurrentUnits == HeatUnit.KJ

        # FIXME WIP
        # assert hip_ra.OutputParameterDict['Fluid Produced'].CurrentUnits == MassUnit.KILOGRAM

        assert hip_ra.OutputParameterDict['Enthalpy (reservoir)'].CurrentUnits == EnthalpyUnit.KJPERKG
        assert hip_ra.OutputParameterDict['Wellhead Heat (reservoir)'].CurrentUnits == HeatUnit.KJ
        assert hip_ra.OutputParameterDict['Recovery Factor (reservoir)'].CurrentUnits == PercentUnit.PERCENT
        assert hip_ra.OutputParameterDict['Available Heat (reservoir)'].CurrentUnits == HeatUnit.KJ
        assert hip_ra.OutputParameterDict['Producible Heat (reservoir)'].CurrentUnits == HeatUnit.KJ
        assert hip_ra.OutputParameterDict['Producible Electricity (reservoir)'].CurrentUnits == PowerUnit.MW

    #  The class handles the case when the density of water is less than the minimum allowed value.
    def test_handle_low_density_of_water(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        hip_ra.fluid_density.value = -1.0
        hip_ra.reservoir_temperature.value = 100.0
        hip_ra.Calculate()
        assert hip_ra.fluid_density.value == pytest.approx(999.7, abs=1e-2)

    #  The class handles the case when the heat capacity of water is less than the minimum allowed value.
    def test_handle_low_heat_capacity_of_water(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        hip_ra.fluid_heat_capacity.value = -1.0
        hip_ra.reservoir_temperature.value = 100.0
        hip_ra.Calculate()
        assert hip_ra.fluid_heat_capacity.value == pytest.approx(4.18, abs=1e-2)


class Test__Init__:
    #  The '__init__' method initializes the logger attribute with the 'root' logger.
    def test_logger_initialized_with_root_logger(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        assert hip_ra.logger.name == 'root'

    #  If 'enable_geophires_logging_config' is True, the method configures the logger using the 'logging.conf' file and sets the logger level to INFO.
    def test_logger_configured_with_logging_conf_file(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        assert hip_ra.logger.level == logging.INFO

    def test_float_parameters_initialized(self):
        hip_ra: HIP_RA = HIP_RA(enable_hip_ra_logging_config=False)
        assert isinstance(hip_ra.reservoir_temperature, floatParameter)
        assert isinstance(hip_ra.rejection_temperature, floatParameter)
        assert isinstance(hip_ra.reservoir_porosity, floatParameter)
        assert isinstance(hip_ra.reservoir_area, floatParameter)
        assert isinstance(hip_ra.reservoir_thickness, floatParameter)
        assert isinstance(hip_ra.rock_heat_capacity, floatParameter)
        assert isinstance(hip_ra.fluid_heat_capacity, floatParameter)
        assert isinstance(hip_ra.rock_heat_capacity, floatParameter)
        assert isinstance(hip_ra.fluid_density, floatParameter)
        assert isinstance(hip_ra.rock_density, floatParameter)
        assert isinstance(hip_ra.fluid_recoverable_heat, floatParameter)
        assert isinstance(hip_ra.volume_fluid, OutputParameter)
        assert isinstance(hip_ra.volume_rock, OutputParameter)

        # TODO should these be initialized?
        # assert isinstance(hip_ra.rejection_temperature_k, floatParameter)
        # assert isinstance(hip_ra.rejection_entropy, floatParameter)
        # assert isinstance(hip_ra.rejection_enthalpy, floatParameter)

    #  The method initializes several intParameter objects and assigns them to corresponding attributes in the ParameterDict dictionary.
    def test_int_parameters_initialized(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        assert isinstance(hip_ra.reservoir_life_cycle, intParameter)

    #  The method initializes several OutputParameter objects and assigns them to corresponding attributes in the OutputParameterDict dictionary.
    def test_output_parameters_initialized(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        assert isinstance(hip_ra.reservoir_volume, OutputParameter)
        assert isinstance(hip_ra.reservoir_stored_heat, OutputParameter)
        assert isinstance(hip_ra.reservoir_mass, OutputParameter)
        assert isinstance(hip_ra.reservoir_enthalpy, OutputParameter)
        assert isinstance(hip_ra.wellhead_heat, OutputParameter)
        assert isinstance(hip_ra.reservoir_recovery_factor, OutputParameter)
        assert isinstance(hip_ra.reservoir_available_heat, OutputParameter)
        assert isinstance(hip_ra.reservoir_producible_heat, OutputParameter)
        assert isinstance(hip_ra.reservoir_producible_electricity, OutputParameter)

    #  The 'enable_geophires_logging_config' parameter is False, so the logger is not configured.
    def test_logger_not_configured_when_enable_geophires_logging_config_is_false(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        assert hip_ra.logger.level == logging.NOTSET

    #  The 'enable_geophires_logging_config' parameter is not provided, so the default value of True is used.
    def test_logger_configured_when_enable_geophires_logging_config_is_not_provided(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        assert hip_ra.logger.level == logging.INFO

    #  The 'reservoir_temperature' floatParameter object is initialized with a value below the minimum allowed value (50).
    def test_reservoir_temperature_initialized_with_value_below_minimum(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        assert hip_ra.reservoir_temperature.value == 50.0

    #  The 'reservoir_temperature' floatParameter object is initialized with a value above the maximum allowed value (1000).
    def test_reservoir_temperature_initialized_with_value_above_maximum(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        assert hip_ra.reservoir_temperature.value == 1000.0

    #  The 'reservoir_thickness' floatParameter object is initialized with a value of 0, which is the minimum allowed value.
    def test_reservoir_thickness_initialized_with_minimum_value(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        assert hip_ra.reservoir_thickness.value == 0.0


class TestCalculate:
    #  Calculates the stored heat in the reservoir
    def test_calculate_stored_heat(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        hip_ra.Calculate()
        assert hip_ra.reservoir_stored_heat.value == hip_ra.reservoir_volume.value * (
            hip_ra.rock_heat_capacity.value * (hip_ra.reservoir_temperature.value - hip_ra.rejection_temperature.value)
        )

    #  Calculates the maximum energy out per unit of mass
    def test_calculate_maximum_energy(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        hip_ra.Calculate()
        assert hip_ra.reservoir_enthalpy.value == (
            (EnthalpyH20_func(hip_ra.reservoir_temperature.value) - hip_ra.rejection_enthalpy.value)
            - (
                hip_ra.rejection_temperature_k.value
                * (EntropyH20_func(hip_ra.reservoir_temperature.value) - hip_ra.rejection_entropy.value)
            )
        )

    #  Calculates the heat recovery at the wellhead
    def test_calculate_heat_recovery(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        hip_ra.Calculate()
        assert hip_ra.wellhead_heat.value == hip_ra.reservoir_mass.value * (
            EnthalpyH20_func(hip_ra.reservoir_temperature.value) - hip_ra.rejection_temperature_k.value
        )

    #  Calculates the available heat
    def test_calculate_available_heat(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        hip_ra.Calculate()
        assert hip_ra.reservoir_available_heat.value == (
            hip_ra.reservoir_mass.value
            * hip_ra.reservoir_enthalpy.value
            * hip_ra.reservoir_recovery_factor.value
            * RecoverableHeat(hip_ra.recoverable_rock_heat.value, hip_ra.reservoir_temperature.value)
        )

    #  Calculates the mass of the fluid in the reservoir with wrong formula
    def test_calculate_mass_of_fluid_wrong_formula(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        hip_ra.Calculate()
        assert (
            hip_ra.reservoir_mass.value
            == (hip_ra.reservoir_volume.value * (hip_ra.reservoir_porosity.value / 100.0)) * hip_ra.fluid_density.value
        )

    #  Calculates the density of water with wrong formula
    def test_calculate_density_of_water_wrong_formula(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        hip_ra.Calculate()
        if hip_ra.fluid_density.value < hip_ra.fluid_density.Min:
            hip_ra.fluid_density.value = DensityWater(hip_ra.reservoir_temperature.value) * 1_000_000_000.0
        assert hip_ra.fluid_density.value >= hip_ra.fluid_density.Min

    #  Calculates the heat capacity of water with wrong formula
    def test_calculate_heat_capacity_of_water_wrong_formula(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        hip_ra.Calculate()
        if hip_ra.fluid_heat_capacity.value < hip_ra.fluid_heat_capacity.Min:
            hip_ra.fluid_heat_capacity.value = HeatCapacityWater(hip_ra.reservoir_temperature.value) / 1000.0
        assert hip_ra.fluid_heat_capacity.value >= hip_ra.fluid_heat_capacity.Min

    #  Calculates the stored heat in the reservoir with negative values
    def test_calculate_stored_heat_negative_values(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        hip_ra.rock_heat_capacity.value = -1e12
        hip_ra.Calculate()
        assert hip_ra.reservoir_stored_heat.value == hip_ra.reservoir_volume.value * (
            hip_ra.rock_heat_capacity.value * (hip_ra.reservoir_temperature.value - hip_ra.rejection_temperature.value)
        )

    #  Calculates the maximum energy out per unit of mass with negative values
    def test_calculate_maximum_energy_negative_values(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        hip_ra.rejection_enthalpy.value = 1e12
        hip_ra.Calculate()
        assert hip_ra.reservoir_enthalpy.value == (
            (EnthalpyH20_func(hip_ra.reservoir_temperature.value) - hip_ra.rejection_enthalpy.value)
            - (
                hip_ra.rejection_temperature_k.value
                * (EntropyH20_func(hip_ra.reservoir_temperature.value) - hip_ra.rejection_entropy.value)
            )
        )

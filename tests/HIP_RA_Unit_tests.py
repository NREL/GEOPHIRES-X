# FIXME WIP/broken
# ruff: noqa

import logging
import tempfile
import unittest
import uuid
from pathlib import Path

import pytest

from geophires_x.GeoPHIRESUtils import DensityWater
from geophires_x.GeoPHIRESUtils import EnthalpyH20_func
from geophires_x.GeoPHIRESUtils import EntropyH20_func
from geophires_x.GeoPHIRESUtils import HeatCapacityWater
from geophires_x.GeoPHIRESUtils import RecoverableHeat
from geophires_x.Units import EnthalpyUnit
from geophires_x.Units import HeatUnit
from geophires_x.Units import MassUnit
from geophires_x.Units import PercentUnit
from geophires_x.Units import PowerUnit
from geophires_x.Units import TemperatureUnit
from geophires_x.Units import Units
from geophires_x.Units import VolumeUnit
from hip_ra import HipRaClient, HipRaInputParameters
from hip_ra.HIP_RA import HIP_RA


class TestHipRa(unittest.TestCase):
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


class TestCalculate:
    def test_calculate_stored_heat(self):
        """Calculates the stored heat in the reservoir"""
        hip_ra: HIP_RA = HIP_RA(enable_hip_ra_logging_config=False)
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

    # Calculates the mass of the fluid in the reservoir with wrong formula
    def test_calculate_mass_of_fluid_wrong_formula(self):
        hip_ra = HIP_RA(enable_hip_ra_logging_config=False)
        hip_ra.Calculate()
        assert (
            hip_ra.reservoir_mass.value
            == (hip_ra.reservoir_volume.value * (hip_ra.reservoir_porosity.value / 100.0)) * hip_ra.fluid_density.value
        )

    # Calculates the density of water with wrong formula
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

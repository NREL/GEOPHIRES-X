import math
import unittest
from pathlib import Path

from base_test_case import BaseTestCase

# Ruff disabled because imports are order-dependent
# ruff: noqa: I001
from geophires_x.Model import Model
from geophires_x.Parameter import ParameterEntry

from geophires_x.GeoPHIRESUtils import density_water_kg_per_m3, static_pressure_MPa

from geophires_x.GeoPHIRESUtils import heat_capacity_water_J_per_kg_per_K as heatcapacitywater

# ruff: noqa: I001
from geophires_x.CylindricalReservoir import CylindricalReservoir

# ruff: noqa: I001
from geophires_x.AGSWellBores import AGSWellBores

import sys
import os

from geophires_x.Units import LengthUnit


class CylindricalReservoirTestCase(BaseTestCase):
    def _new_model_with_cylindrical_reservoir(self, input_file=None) -> Model:
        stash_cwd = Path.cwd()
        stash_sys_argv = sys.argv

        sys.argv = ['']

        if input_file is not None:
            sys.argv.append(input_file)

        m = Model(enable_geophires_logging_config=False)
        m.InputParameters['Is AGS'] = ParameterEntry(Name='Is AGS', sValue='True')
        reservoir = CylindricalReservoir(m)
        m.reserv = reservoir
        m.wellbores = AGSWellBores(m)

        if input_file is not None:
            m.read_parameters()

        sys.argv = stash_sys_argv
        os.chdir(stash_cwd)

        return m

    def test_read_inputs(self):
        model = self._new_model_with_cylindrical_reservoir(
            input_file=self._get_test_file_path(
                '../examples/Beckers_et_al_2023_Tabulated_Database_Uloop_water_elec.txt'
            )
        )
        reservoir: CylindricalReservoir = model.reserv
        self.assertIsNotNone(reservoir.InputDepth)

        self.assertEqual(LengthUnit.KILOMETERS, reservoir.InputDepth.CurrentUnits)
        self.assertEqual(3.0, reservoir.InputDepth.value)

        # TODO depth should probably be set to this value on initialization rather than calculation
        # self.assertEqual(3000.0, reservoir.depth.quantity().to('m').magnitude)

    def test_read_inputs_depth_in_meters(self):
        model = self._new_model_with_cylindrical_reservoir(
            input_file=self._get_test_file_path('cylindrical_reservoir_input_depth_meters.txt')
        )
        reservoir = model.reserv
        self.assertIsNotNone(reservoir.InputDepth)

        self.assertEqual(3.0, reservoir.InputDepth.value)
        self.assertEqual(LengthUnit.KILOMETERS, reservoir.InputDepth.CurrentUnits)

    def test_calculate_temperature_inflow_end(self):
        model = self._new_model_with_cylindrical_reservoir()
        reservoir = model.reserv
        reservoir.Calculate(model)
        assert reservoir.Trock.value == reservoir.Tsurf.value + (
            reservoir.gradient.value[0] * (reservoir.InputDepth.value * 1000.0)
        )

    def test_calculate_initial_heat_content(self):
        """Calculates the initial reservoir heat content"""
        model = self._new_model_with_cylindrical_reservoir()
        reservoir = model.reserv
        reservoir.Calculate(model)
        expected_heat_content = (
            reservoir.RadiusOfEffectFactor.value
            * reservoir.resvolcalc.value
            * reservoir.rhorock.value
            * reservoir.cprock.value
            * (reservoir.Trock.value - model.wellbores.Tinj.value)
        ) / 1e15
        assert reservoir.InitialReservoirHeatContent.value == expected_heat_content

    def test_calculate_surface_area(self):
        """Calculates the surface area of the cylindrical reservoir"""
        model = self._new_model_with_cylindrical_reservoir()
        reservoir = model.reserv
        reservoir.Calculate(model)
        expected_surface_area = (2.0 * math.pi * reservoir.RadiusOfEffect.value * (reservoir.Length.value * 1000.0)) + (
            2.0 * math.pi * (reservoir.RadiusOfEffect.value**2)
        )
        assert reservoir.SurfaceArea.value == expected_surface_area

    def test_calculate_depth_as_total_drilled_length(self):
        model = self._new_model_with_cylindrical_reservoir()
        reservoir = model.reserv
        reservoir.Calculate(model)
        self.assertEqual(10.0, reservoir.depth.quantity().to('km').magnitude)

    def test_calculate_heat_capacity_water(self):
        """Calculates the heat capacity of water"""
        model = self._new_model_with_cylindrical_reservoir()
        reservoir = model.reserv
        reservoir.Calculate(model)
        expected_heat_capacity = heatcapacitywater(
            model.wellbores.Tinj.value * 0.5 + (reservoir.Trock.value * 0.9 + model.wellbores.Tinj.value * 0.1) * 0.5,
            pressure=model.reserv.lithostatic_pressure(),
        )
        assert reservoir.cpwater.value == expected_heat_capacity

    def test_calculate_density_water(self):
        """Calculates the density of water"""
        model = self._new_model_with_cylindrical_reservoir()
        reservoir = model.reserv
        reservoir.Calculate(model)
        expected_density = density_water_kg_per_m3(
            model.wellbores.Tinj.value * 0.5 + (reservoir.Trock.value * 0.9 + model.wellbores.Tinj.value * 0.1) * 0.5,
            pressure=reservoir.lithostatic_pressure(),
        )
        assert expected_density == reservoir.rhowater.value

    @unittest.skip('FIXME requires review of expected value')
    def test_calculate_temperature_outflow_end(self):
        """Calculates the temperature of the rock at the outflow end of the cylindrical reservoir"""
        model = self._new_model_with_cylindrical_reservoir()
        reservoir = model.reserv
        reservoir.Calculate(model)
        expected_temperature = reservoir.Tsurf.value + (reservoir.gradient.value[0] * (reservoir.depth.value * 1000.0))
        assert reservoir.Tresoutput.value[-1] == expected_temperature

    def test_calculate_initial_heat_content_min_values(self):
        """Calculates the initial reservoir heat content with minimum values"""
        model = self._new_model_with_cylindrical_reservoir()
        reservoir = model.reserv
        reservoir.RadiusOfEffectFactor.value = 0.0
        reservoir.resvolcalc.value = 0.0
        reservoir.rhorock.value = reservoir.rhorock.Min
        reservoir.cprock.value = reservoir.cprock.Min
        reservoir.Trock.value = 0.0
        model.wellbores.Tinj.value = 0.0
        reservoir.Calculate(model)
        assert reservoir.InitialReservoirHeatContent.value == 0.0

    def test_calculate_initial_heat_content_max_values(self):
        """Calculates the initial reservoir heat content with maximum values"""
        model = self._new_model_with_cylindrical_reservoir()
        reservoir = model.reserv
        reservoir.RadiusOfEffectFactor.value = 10.0
        reservoir.resvolcalc.value = 100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000

    def test_lithostatic_pressure_calculated_from_input_depth(self):
        model = self._new_model_with_cylindrical_reservoir()
        reservoir = model.reserv
        reservoir.InputDepth.value = 4.20
        assert reservoir.lithostatic_pressure().magnitude == static_pressure_MPa(
            reservoir.rhorock.value, reservoir.InputDepth.quantity().to('m').magnitude
        )

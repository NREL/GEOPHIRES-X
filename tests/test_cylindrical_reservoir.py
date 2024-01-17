import math
import unittest

# Ruff disabled because imports are order-dependent
# ruff: noqa: I001
from geophires_x.Model import Model

# ruff: noqa: I001
from geophires_x.Reservoir import densitywater

# ruff: noqa: I001
from geophires_x.Reservoir import heatcapacitywater

# ruff: noqa: I001
from geophires_x.CylindricalReservoir import CylindricalReservoir

# ruff: noqa: I001
from geophires_x.AGSWellBores import AGSWellBores


class CylindricalReservoirTestCase(unittest.TestCase):
    def _new_model(self) -> Model:
        m = Model(enable_geophires_logging_config=False)
        m.InputParameters['Is AGS'] = True
        reservoir = CylindricalReservoir(m)
        m.reserv = reservoir
        m.wellbores = AGSWellBores(m)
        return m

    def test_calculate_temperature_inflow_end(self):
        """Calculates the temperature of the rock at the inflow end of the cylindrical reservoir"""
        model = self._new_model()
        reservoir = model.reserv
        reservoir.Calculate(model)
        assert reservoir.Trock.value == reservoir.Tsurf.value + (
            reservoir.gradient.value[0] * (reservoir.InputDepth.value * 1000.0)
        )

    def test_calculate_initial_heat_content(self):
        """Calculates the initial reservoir heat content"""
        model = self._new_model()
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
        model = self._new_model()
        reservoir = model.reserv
        reservoir.Calculate(model)
        expected_surface_area = (2.0 * math.pi * reservoir.RadiusOfEffect.value * (reservoir.Length.value * 1000.0)) + (
            2.0 * math.pi * (reservoir.RadiusOfEffect.value**2)
        )
        assert reservoir.SurfaceArea.value == expected_surface_area

    def test_calculate_heat_capacity_water(self):
        """Calculates the heat capacity of water"""
        model = self._new_model()
        reservoir = model.reserv
        reservoir.Calculate(model)
        expected_heat_capacity = heatcapacitywater(
            model.wellbores.Tinj.value * 0.5 + (reservoir.Trock.value * 0.9 + model.wellbores.Tinj.value * 0.1) * 0.5
        )
        assert reservoir.cpwater.value == expected_heat_capacity

    #  Calculates the density of water
    def test_calculate_density_water(self):
        """Calculates the heat capacity of water"""
        model = self._new_model()
        reservoir = model.reserv
        reservoir.Calculate(model)
        expected_density = densitywater(
            model.wellbores.Tinj.value * 0.5 + (reservoir.Trock.value * 0.9 + model.wellbores.Tinj.value * 0.1) * 0.5
        )
        assert reservoir.rhowater.value == expected_density

    @unittest.skip('FIXME requires review of expected value')
    def test_calculate_temperature_outflow_end(self):
        """Calculates the temperature of the rock at the outflow end of the cylindrical reservoir"""
        model = self._new_model()
        reservoir = model.reserv
        reservoir.Calculate(model)
        expected_temperature = reservoir.Tsurf.value + (reservoir.gradient.value[0] * (reservoir.depth.value * 1000.0))
        assert reservoir.Tresoutput.value[-1] == expected_temperature

    def test_calculate_initial_heat_content_min_values(self):
        """Calculates the initial reservoir heat content with minimum values"""
        model = self._new_model()
        reservoir = model.reserv
        reservoir.RadiusOfEffectFactor.value = 0.0
        reservoir.resvolcalc.value = 0.0
        reservoir.rhorock.value = 0.0
        reservoir.cprock.value = 0.0
        reservoir.Trock.value = 0.0
        model.wellbores.Tinj.value = 0.0
        reservoir.Calculate(model)
        assert reservoir.InitialReservoirHeatContent.value == 0.0

    def test_calculate_initial_heat_content_max_values(self):
        """Calculates the initial reservoir heat content with maximum values"""
        model = self._new_model()
        reservoir = model.reserv
        reservoir.RadiusOfEffectFactor.value = 10.0
        reservoir.resvolcalc.value = 100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000

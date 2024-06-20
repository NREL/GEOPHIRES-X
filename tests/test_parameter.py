import os
import sys
import unittest
from pathlib import Path

from geophires_x.Model import Model
from geophires_x.Parameter import ConvertUnitsBack
from geophires_x.Parameter import OutputParameter
from geophires_x.Parameter import Parameter
from geophires_x.Parameter import floatParameter
from geophires_x.Parameter import listParameter
from geophires_x.Units import CostPerMassUnit
from geophires_x.Units import CurrencyUnit
from geophires_x.Units import EnergyCostUnit
from geophires_x.Units import LengthUnit
from geophires_x.Units import PressureUnit
from geophires_x.Units import Units
from tests.base_test_case import BaseTestCase


class ParameterTestCase(BaseTestCase):
    def test_convert_units_back(self):
        model = self._new_model()  # TODO mock instead

        param_to_modify: Parameter = floatParameter(
            Name='Production Well Diameter',
            Required=True,
            Provided=True,
            Valid=True,
            ErrMessage='assume default production well diameter (8 inch)',
            InputComment='',
            ToolTipText='Inner diameter of production wellbore (assumed constant along the wellbore) to calculate             frictional pressure drop and wellbore heat transmission with Rameys model',
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.INCHES,
            CurrentUnits=LengthUnit.METERS,
            value=0.17779999999999999,
            DefaultValue=8.0,
            Min=1.0,
            Max=30.0,
        )
        self.assertFalse(param_to_modify.UnitsMatch)

        ConvertUnitsBack(param_to_modify, model)

        self.assertEqual(param_to_modify.value, 7.0)
        self.assertEqual(param_to_modify.CurrentUnits, LengthUnit.INCHES)

    def test_set_default_value(self):
        without_val = floatParameter(
            'Average Reservoir Pressure',
            DefaultValue=29430,  # Calculated from example1
            Min=1e2,
            Max=1e5,
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL,
            ErrMessage='calculate reservoir pressure using built-in correlation',
            ToolTipText='Reservoir hydrostatic far-field pressure.  Default value is calculated with built-in modified \
                    Xie-Bloomfield-Shook equation (DOE, 2016).',
        )
        self.assertEqual(29430, without_val.value)

        with_val = floatParameter(
            'Average Reservoir Pressure',
            value=1e2,
            DefaultValue=29430,
            Min=1e2,
            Max=1e5,
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL,
            ErrMessage='calculate reservoir pressure using built-in correlation',
            ToolTipText='Reservoir hydrostatic far-field pressure.  Default value is calculated with built-in modified \
                    Xie-Bloomfield-Shook equation (DOE, 2016).',
        )
        self.assertEqual(1e2, with_val.value)

    def test_set_default_value_list(self):
        without_val = listParameter(
            'Thicknesses',
            DefaultValue=[100_000.0, 0.01, 0.01, 0.01, 0.01],
            Min=0.01,
            Max=100.0,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.KILOMETERS,
            CurrentUnits=LengthUnit.KILOMETERS,
            ErrMessage='assume default layer thicknesses (100,000, 0, 0, 0 km)',
            ToolTipText='Thicknesses of rock segments',
        )

        self.assertEqual([100_000.0, 0.01, 0.01, 0.01, 0.01], without_val.value)

        with_val = listParameter(
            'Thicknesses',
            value=[1, 2, 3],
            DefaultValue=[100_000.0, 0.01, 0.01, 0.01, 0.01],
            Min=0.01,
            Max=100.0,
            UnitType=Units.LENGTH,
            PreferredUnits=LengthUnit.KILOMETERS,
            CurrentUnits=LengthUnit.KILOMETERS,
            ErrMessage='assume default layer thicknesses (100,000, 0, 0, 0 km)',
            ToolTipText='Thicknesses of rock segments',
        )

        self.assertEqual([1, 2, 3], with_val.value)

    def test_output_parameter_with_preferred_units(self):
        op: OutputParameter = OutputParameter(
            Name='Electricity Sale Price Model',
            value=[
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
                0.055,
            ],
            ToolTipText='This is ToolTip Text',
            UnitType=Units.ENERGYCOST,
            PreferredUnits=EnergyCostUnit.CENTSSPERKWH,
            CurrentUnits=EnergyCostUnit.DOLLARSPERKWH,
        )

        result = op.with_preferred_units()
        self.assertIsNotNone(result)
        self.assertEqual(5.5, result.value[0])
        self.assertEqual(5.5, result.value[-1])

    def test_convert_units_back_currency(self):
        model = self._new_model()

        param = floatParameter(
            'CAPEX',
            DefaultValue=1379.0,
            UnitType=Units.COSTPERMASS,
            PreferredUnits=CostPerMassUnit.DOLLARSPERMT,
            CurrentUnits=CostPerMassUnit.CENTSSPERMT,
        )

        ConvertUnitsBack(param, model)
        self.assertEqual(param.CurrentUnits, CostPerMassUnit.DOLLARSPERMT)
        self.assertAlmostEqual(param.value, 13.79, places=2)

        with self.assertRaises(RuntimeError) as re:
            # TODO update once https://github.com/NREL/GEOPHIRES-X/issues/236?title=Currency+conversions+disabled is
            #   addressed
            param2 = floatParameter(
                'OPEX',
                DefaultValue=240,
                UnitType=Units.CURRENCY,
                PreferredUnits=CurrencyUnit.DOLLARS,
                CurrentUnits=CurrencyUnit.EUR,
            )
            ConvertUnitsBack(param2, model)

            self.assertIn('GEOPHIRES failed to convert your units for OPEX', str(re))

    def _new_model(self) -> Model:
        stash_cwd = Path.cwd()
        stash_sys_argv = sys.argv

        sys.argv = ['']

        m = Model(enable_geophires_logging_config=False)

        sys.argv = stash_sys_argv
        os.chdir(stash_cwd)

        return m


if __name__ == '__main__':
    unittest.main()

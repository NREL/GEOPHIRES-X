import os
import sys
import unittest
from pathlib import Path

from base_test_case import BaseTestCase
from geophires_x.Model import Model
from geophires_x.Parameter import Parameter
from geophires_x.Parameter import floatParameter
from geophires_x.Parameter import parameter_with_units_converted_back_to_preferred_units
from geophires_x.Units import LengthUnit
from geophires_x.Units import PressureUnit
from geophires_x.Units import Units


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
            UnitsMatch=False,
            value=0.17779999999999999,
            DefaultValue=8.0,
            Min=1.0,
            Max=30.0,
        )

        result = parameter_with_units_converted_back_to_preferred_units(param_to_modify, model)

        self.assertEqual(result.value, 7.0)
        self.assertEqual(result.CurrentUnits, LengthUnit.INCHES)

    def test_set_default_value(self):
        without_val = floatParameter(
            'Reservoir Hydrostatic Pressure',
            # value=1E2,
            DefaultValue=29430,  # Calculated from example1
            Min=1e2,
            Max=1e5,
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL,
            ErrMessage='calculate reservoir hydrostatic pressure using built-in correlation',
            ToolTipText='Reservoir hydrostatic far-field pressure.  Default value is calculated with built-in modified \
                    Xie-Bloomfield-Shook equation (DOE, 2016).',
        )
        self.assertEqual(29430, without_val.value)

        with_val = floatParameter(
            'Reservoir Hydrostatic Pressure',
            value=1e2,
            DefaultValue=29430,
            Min=1e2,
            Max=1e5,
            UnitType=Units.PRESSURE,
            PreferredUnits=PressureUnit.KPASCAL,
            CurrentUnits=PressureUnit.KPASCAL,
            ErrMessage='calculate reservoir hydrostatic pressure using built-in correlation',
            ToolTipText='Reservoir hydrostatic far-field pressure.  Default value is calculated with built-in modified \
                    Xie-Bloomfield-Shook equation (DOE, 2016).',
        )
        self.assertEqual(1e2, with_val.value)

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

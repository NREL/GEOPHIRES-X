from __future__ import annotations

import csv
import json
import re
from io import StringIO
from pathlib import Path
from types import MappingProxyType

from .common import _get_logger
from .geophires_input_parameters import EndUseOption


class _EqualSignDelimitedField:
    def __init__(self, field_name: str):
        self.field_name: str = field_name


class _StringValueField:
    def __init__(self, field_name: str):
        self.field_name: str = field_name


class GeophiresXResult:
    _RESULT_FIELDS_BY_CATEGORY = MappingProxyType(
        {
            'SUMMARY OF RESULTS': [
                _StringValueField('End-Use Option'),
                _StringValueField('End-Use'),
                'Average Net Electricity Production',
                'Electricity breakeven price',
                'Average Direct-Use Heat Production',
                'Direct-Use heat breakeven price',
                'Direct-Use heat breakeven price (LCOH)',
                'Direct-Use Cooling Breakeven Price (LCOC)',
                'Annual District Heating Demand',
                'Average Cooling Production',
                'Average Annual Geothermal Heat Production',
                'Average Annual Peaking Fuel Heat Production',
                'Direct-Use Cooling Breakeven Price',
                'Number of production wells',
                'Number of injection wells',
                'Flowrate per production well',
                'Well depth',
                'Well depth (or total length, if not vertical)',
                'Geothermal gradient',
                'Segment 1   Geothermal gradient',
                'Segment 1   Thickness',
                'Segment 2   Geothermal gradient',
                'Segment 2   Thickness',
                'Segment 3   Geothermal gradient',
                'Segment 3   Thickness',
                'Segment 4   Geothermal gradient',
                # AGS/CLGS
                'LCOE',
                'LCOH',
                'Lifetime Average Well Flow Rate',  # SUTRA
                'Total Avoided Carbon Emissions',
            ],
            'ECONOMIC PARAMETERS': [
                _EqualSignDelimitedField('Economic Model'),
                'Interest Rate',  # %
                'Accrued financing during construction',
                'Project lifetime',
                'Capacity factor',
                'Project NPV',
                'Project IRR',
                'Project VIR=PI=PIR',
                'Project MOIC',
                'Fixed Charge Rate (FCR)',  # SUTRA
                'Project Payback Period',
                'CHP: Percent cost allocation for electrical plant',
            ],
            'EXTENDED ECONOMICS': [
                'Adjusted Project LCOE (after incentives, grants, AddOns,etc)',
                'Adjusted Project LCOH (after incentives, grants, AddOns,etc)',
                'Adjusted Project CAPEX (after incentives, grants, AddOns, etc)',
                'Adjusted Project OPEX (after incentives, grants, AddOns, etc)',
                'Project NPV   (including AddOns)',
                'Project IRR   (including AddOns)',
                'Project VIR=PI=PIR   (including AddOns)',
                'Project MOIC  (including AddOns)',
                'Project Payback Period       (including AddOns)',
                'Total Add-on CAPEX',
                'Total Add-on OPEX',
                'Total Add-on Net Elec',
                'Total Add-on Net Heat',
                'Total Add-on Profit',
                'AddOns Payback Period',
            ],
            'CCUS ECONOMICS': [
                'Total Avoided Carbon Production',
                'Project NPV            (including carbon credit)',
                'Project IRR            (including carbon credit)',
                'Project VIR=IR=PIR     (including carbon credit)',
                'Project MOIC           (including carbon credit)',
                'Project Payback Period (including carbon credit)',
            ],
            'ENGINEERING PARAMETERS': [
                'Number of Production Wells',
                'Number of Injection Wells',
                'Well depth (or total length, if not vertical)',
                'Water loss rate',  # %
                'Pump efficiency',  # %
                'Injection temperature',
                'Injection Temperature',
                'Average production well temperature drop',
                'Flowrate per production well',
                'Injection well casing ID',
                'Production well casing ID',
                'Number of times redrilling',
                _StringValueField('Power plant type'),
                # AGS/CLGS
                _StringValueField('Fluid'),
                _StringValueField('Design'),
                'Flow rate',
                'Lateral Length',
                'Vertical Depth',
                'Wellbore Diameter',
                # SUTRA
                'Lifetime Average Well Flow Rate',
                'Injection well casing ID',
                'Production well casing ID',
            ],
            'RESOURCE CHARACTERISTICS': [
                'Maximum reservoir temperature',
                'Number of segments',
                'Geothermal gradient',
                'Segment 1   Geothermal gradient',
                'Segment 1   Thickness',
                'Segment 2   Geothermal gradient',
                'Segment 2   Thickness',
                'Segment 3   Geothermal gradient',
                'Segment 3   Thickness',
                'Segment 4   Geothermal gradient',
            ],
            'RESERVOIR PARAMETERS': [
                _EqualSignDelimitedField('Reservoir Model'),
                _EqualSignDelimitedField('Fracture model'),
                # TODO moved to power generation profile, parse from there
                #  'Annual Thermal Drawdown (%/year)',
                'Bottom-hole temperature',
                'Well separation: fracture height',
                'Fracture area',
                'Fracture width',
                'Reservoir volume',
                'Reservoir hydrostatic pressure',
                'Plant outlet pressure',
                'Production wellhead pressure',
                'Productivity Index',
                'Injectivity Index',
                'Reservoir density',
                'Reservoir thermal conductivity',
                'Reservoir heat capacity',
                'Reservoir porosity',
                'Thermal Conductivity',
            ],
            'RESERVOIR SIMULATION RESULTS': [
                'Maximum Production Temperature',
                'Average Production Temperature',
                'Minimum Production Temperature',
                'Initial Production Temperature',
                'Average Reservoir Heat Extraction',
                _EqualSignDelimitedField('Production Wellbore Heat Transmission Model'),
                'Average Production Well Temperature Drop',
                'Average Injection Well Pump Pressure Drop',
                'Average Production Well Pump Pressure Drop',
                'Average Production Pressure',
                'Average Heat Production',
                'First Year Heat Production',
                'Average Net Electricity Production',
                'First Year Electricity Production',
                'Maximum Storage Well Temperature',
                'Average Storage Well Temperature',
                'Minimum Storage Well Temperature',
                'Maximum Balance Well Temperature',
                'Average Balance Well Temperature',
                'Minimum Balance Well Temperature',
                'Maximum Annual Heat Stored',
                'Average Annual Heat Stored',
                'Minimum Annual Heat Stored',
                'Maximum Annual Heat Supplied',
                'Average Annual Heat Supplied',
                'Minimum Annual Heat Supplied',
                'Average Round-Trip Efficiency',
                'Total Average Pressure Drop',
            ],
            'CAPITAL COSTS (M$)': [
                'Drilling and completion costs',
                'Drilling and completion costs per well',
                'Stimulation costs',
                'Surface power plant costs',
                'of which Absorption Chiller Cost',
                'of which Heat Pump Cost',
                'of which Peaking Boiler Cost',
                'District Heating System Cost',
                'Field gathering system costs',
                'Total surface equipment costs',
                'Exploration costs',
                'Total capital costs',
                # AGS/CLGS
                'Total CAPEX',
                'Drilling Cost',
                # SUTRA
                'Drilling and Completion Costs',
                'Drilling and Completion Costs per Well',
                'Auxiliary Heater Cost',
                'Pump Cost',
                'Total Capital Costs',
            ],
            'OPERATING AND MAINTENANCE COSTS (M$/yr)': [
                'Wellfield maintenance costs',
                'Power plant maintenance costs',
                'Water costs',
                'Average Reservoir Pumping Cost',
                'Absorption Chiller O&M Cost',
                'Average Heat Pump Electricity Cost',
                'Annual District Heating O&M Cost',
                'Average Annual Peaking Fuel Cost',
                'Average annual pumping costs',
                'Total operating and maintenance costs',
                # AGS/CLGS
                'OPEX',
                # SUTRA
                'Average annual auxiliary fuel cost',
                'Average annual pumping cost',
                'Total average annual O&M costs',
            ],
            'SURFACE EQUIPMENT SIMULATION RESULTS': [
                'Initial geofluid availability',
                'Maximum Total Electricity Generation',
                'Average Total Electricity Generation',
                'Minimum Total Electricity Generation',
                'Initial Total Electricity Generation',
                'Maximum Net Electricity Generation',
                'Average Net Electricity Generation',
                'Minimum Net Electricity Generation',
                'Initial Net Electricity Generation',
                'Average Annual Total Electricity Generation',
                'Average Annual Net Electricity Generation',
                'Maximum Net Heat Production',
                'Average Net Heat Production',
                'Minimum Net Heat Production',
                'Initial Net Heat Production',
                'Average Annual Heat Production',
                'Average Pumping Power',
                'Average Annual Heat Pump Electricity Use',
                'Maximum Cooling Production',
                'Average Cooling Production',
                'Minimum Cooling Production',
                'Initial Cooling Production',
                'Average Annual Cooling Production',
                'Annual District Heating Demand',
                'Maximum Daily District Heating Demand',
                'Average Daily District Heating Demand',
                'Minimum Daily District Heating Demand',
                'Maximum Geothermal Heating Production',
                'Average Geothermal Heating Production',
                'Minimum Geothermal Heating Production',
                'Maximum Peaking Boiler Heat Production',
                'Average Peaking Boiler Heat Production',
                'Minimum Peaking Boiler Heat Production',
                # AGS/CLGS
                'Surface Plant Cost',
                'Initial pumping power/net installed power',
                # SUTRA
                'Average RTES Heating Production',
                'Average Auxiliary Heating Production',
                'Average Annual RTES Heating Production',
                'Average Annual Auxiliary Heating Production',
                'Average Annual Total Heating Production',
                'Average Annual Electricity Use for Pumping',
            ],
        }
    )

    _METADATA_FIELDS = (
        # 'End-Use Option',
        'Economic Model',
        'Reservoir Model',
    )

    def __init__(self, output_file_path, logger_name=None):
        if logger_name is None:
            logger_name = __name__
        self._logger = _get_logger(logger_name)
        self.output_file_path = output_file_path

        f = open(self.output_file_path)
        self._lines = list(f.readlines())
        f.close()

        # TODO generic-er result value map

        self.result = {}
        for category_fields in GeophiresXResult._RESULT_FIELDS_BY_CATEGORY.items():
            category = category_fields[0]
            fields = category_fields[1]

            self.result[category] = {}
            for field in fields:
                if isinstance(field, _EqualSignDelimitedField):
                    self.result[category][field.field_name] = self._get_equal_sign_delimited_field(field.field_name)
                else:
                    is_string_field = isinstance(field, _StringValueField)
                    field_name = field.field_name if is_string_field else field
                    self.result[category][field_name] = self._get_result_field(
                        field_name, is_string_value_field=is_string_field
                    )

        try:
            self.result['POWER GENERATION PROFILE'] = self._get_power_generation_profile()
            self.result['HEAT AND/OR ELECTRICITY EXTRACTION AND GENERATION PROFILE'] = (
                self._get_heat_electricity_extraction_generation_profile()
            )
        except Exception as e:
            # FIXME
            self._logger.error(f'Failed to parse power and/or extraction profiles: {e}')

        eep = self._get_extended_economic_profile()
        if eep is not None:
            self.result['EXTENDED ECONOMIC PROFILE'] = eep

        revenue_and_cashflow_profile = self._get_revenue_and_cashflow_profile()
        if revenue_and_cashflow_profile is not None:
            self.result['REVENUE & CASHFLOW PROFILE'] = revenue_and_cashflow_profile

        ccus_profile = self._get_ccus_profile()
        if ccus_profile is not None:
            self.result['CCUS PROFILE'] = ccus_profile

        self.result['metadata'] = {'output_file_path': self.output_file_path}
        for metadata_field in GeophiresXResult._METADATA_FIELDS:
            self.result['metadata'][metadata_field] = self._get_equal_sign_delimited_field(metadata_field)

        if self._get_end_use_option() is not None:
            self.result['metadata']['End-Use Option'] = self._get_end_use_option().name

    @property
    def direct_use_heat_breakeven_price_USD_per_MMBTU(self):
        summary = self.result['SUMMARY OF RESULTS']

        # LCOH suffix added in 49ff3a1213ac778ed53120626807e9a680d1ddcf,
        # check for either (could be reading result generated prior to addition of suffix)
        field_names = ['Direct-Use heat breakeven price', 'Direct-Use heat breakeven price (LCOH)']
        for field_name in field_names:
            if field_name in summary and summary[field_name] is not None:
                return summary[field_name]['value']

        return None

    def as_csv(self) -> str:
        f = StringIO()
        w = csv.writer(f)

        w.writerow(['Category', 'Field', 'Year', 'Value', 'Units'])

        csv_entries = []
        for category, fields in self.result.items():
            if category == 'metadata':
                continue

            if isinstance(fields, dict):
                for field, value_unit in fields.items():

                    class ValueUnit:
                        def __init__(self, v_u):
                            self.value_display = v_u
                            self.unit_display = ''
                            if isinstance(v_u, dict):
                                self.value_display = v_u['value']
                                self.unit_display = v_u['unit']

                    if value_unit is not None:
                        field_display = field.replace(',', r'\,')
                        v_u = ValueUnit(value_unit)
                        csv_entries.append([category, field_display, '', v_u.value_display, v_u.unit_display])
            else:
                if category not in (
                    'POWER GENERATION PROFILE',
                    'HEAT AND/OR ELECTRICITY EXTRACTION AND GENERATION PROFILE',
                    'EXTENDED ECONOMIC PROFILE',
                    'CCUS PROFILE',
                    'REVENUE & CASHFLOW PROFILE',
                ):
                    raise RuntimeError('unexpected category')

                for i in range(len(fields[0][1:])):
                    field_profile = fields[0][i + 1]
                    unit_split = field_profile.split(' (')
                    field_display = unit_split[0]
                    unit_display = ''
                    if len(unit_split) > 1:
                        unit_display = unit_split[1].replace(')', '')
                    for j in range(len(fields[1:])):
                        year_entry = fields[j + 1]
                        year = year_entry[0]
                        profile_year_val = year_entry[i + 1]
                        csv_entries.append([category, field_display, year, profile_year_val, unit_display])

        for csv_entry in csv_entries:
            w.writerow(csv_entry)

        return f.getvalue()

    @property
    def json_output_file_path(self) -> Path:
        return Path(self.output_file_path).with_suffix('.json')

    @property
    def _json_fields(self) -> MappingProxyType:
        # https://github.com/NREL/python-geophires-x/issues/9
        try:
            with open(self.json_output_file_path) as jf:
                return json.loads(''.join(jf.readlines()))
        except FileNotFoundError:
            return {}

    def _get_result_field(self, field_name: str, is_string_value_field: bool = False):
        # TODO make this less fragile with proper regex
        matching_lines = set(filter(lambda line: f'    {field_name}: ' in line, self._lines))

        if len(matching_lines) == 0:
            self._logger.debug(f'Field not found: {field_name}')
            return None

        if len(matching_lines) > 1:
            self._logger.warning(
                f'Found multiple ({len(matching_lines)}) entries for field: {field_name}\n\t{matching_lines}'
            )

        matching_line = matching_lines.pop()
        val_and_unit_str = re.sub(r'\s\s+', '', matching_line.replace(f'{field_name}:', '').replace('\n', ''))
        if is_string_value_field:
            return {'value': val_and_unit_str, 'unit': None}
        val_and_unit_tuple = val_and_unit_str.strip().split(' ')
        str_val = val_and_unit_tuple[0]

        unit = None
        if len(val_and_unit_tuple) == 2:
            unit = val_and_unit_tuple[1]
        elif field_name.startswith('Number'):
            unit = 'count'

        return {'value': self._parse_number(str_val, field=f'field "{field_name}"'), 'unit': unit}

    def _get_equal_sign_delimited_field(self, field_name):
        metadata_marker = f'{field_name} = '
        matching_lines = set(filter(lambda line: metadata_marker in line, self._lines))

        if len(matching_lines) == 0:
            self._logger.debug(f'Equal sign-delimited field not found: {field_name}')
            return None

        if len(matching_lines) > 1:
            self._logger.warning(
                f'Found multiple ({len(matching_lines)}) entries for equal sign-delimited field: {field_name}\n\t{matching_lines}'
            )

        return matching_lines.pop().split(metadata_marker)[1].replace('\n', '')

    @property
    def power_generation_profile(self):
        return self.result['POWER GENERATION PROFILE']

    def _get_power_generation_profile(self):
        profile_lines = None
        try:
            profile_lines = self._get_profile_lines('HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE')
        except IndexError:
            profile_lines = self._get_profile_lines('POWER GENERATION PROFILE')
        return self._get_data_from_profile_lines(profile_lines)

    @property
    def heat_electricity_extraction_generation_profile(self):
        return self.result['HEAT AND/OR ELECTRICITY EXTRACTION AND GENERATION PROFILE']

    def _get_heat_electricity_extraction_generation_profile(self):
        profile_lines = None
        try:
            profile_lines = self._get_profile_lines('ANNUAL HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE')
        except IndexError:
            profile_lines = self._get_profile_lines('HEAT AND/OR ELECTRICITY EXTRACTION AND GENERATION PROFILE')
        return self._get_data_from_profile_lines(profile_lines)

    def _get_revenue_and_cashflow_profile(self):
        def extract_table_header(lines: list) -> list:
            # Tried various regexy approaches to extract this programmatically but landed on hard-coding.
            return [
                'Year Since Start',
                'Electricity Price (cents/kWh)',
                'Electricity Ann. Rev. (MUSD/yr)',
                'Electricity Cumm. Rev. (MUSD)',
                'Heat Price (cents/kWh)',
                'Heat Ann. Rev. (MUSD/yr)',
                'Heat Cumm. Rev. (MUSD)',
                'Cooling Price (cents/kWh)',
                'Cooling Ann. Rev. (MUSD/yr)',
                'Cooling Cumm. Rev. (MUSD)',
                'Carbon Price (USD/tonne)',
                'Carbon Ann. Rev. (MUSD/yr)',
                'Carbon Cumm. Rev. (MUSD)',
                'Project OPEX (MUSD/yr)',
                'Project Net Rev. (MUSD/yr)',
                'Project Net Cashflow (MUSD)',
            ]

        try:
            lines = self._get_profile_lines('REVENUE & CASHFLOW PROFILE')
            profile = [extract_table_header(lines)]
            if re.fullmatch('^_+$', lines[5]) is not None:
                del lines[5]
            profile.extend(self._extract_addons_style_table_data(lines))
            return profile
        except BaseException as e:
            self._logger.debug(f'Failed to get revenue & cashflow profile: {e}')
            return None

    def _get_extended_economic_profile(self):
        def extract_table_header(lines: list) -> list:
            # Tried various regexy approaches to extract this programmatically but landed on hard-coding.
            return [
                'Year Since Start',
                'Electricity Price (cents/kWh)',
                'Electricity Revenue (MUSD/yr)',
                'Heat Price (cents/kWh)',
                'Heat Revenue (MUSD/yr)',
                'Add-on Revenue (MUSD/yr)',
                'Annual AddOn Cash Flow (MUSD/yr)',
                'Cumm. AddOn Cash Flow (MUSD)',
                'Annual Project Cash Flow (MUSD/yr)',
                'Cumm. Project Cash Flow (MUSD)',
            ]

        try:
            lines = self._get_profile_lines('EXTENDED ECONOMIC PROFILE')
            profile = [extract_table_header(lines)]
            profile.extend(self._extract_addons_style_table_data(lines))
            return profile
        except BaseException as e:
            self._logger.debug(f'Failed to get extended economic profile: {e}')
            return None

    def _get_ccus_profile(self):
        """
        FIXME TODO - transform from revenue & cashflow if present (CCUS profile replaced by revenue & cashflow
            profile in 49ff3a1213ac778ed53120626807e9a680d1ddcf)
        """

        def extract_table_header(lines: list) -> list:
            # Tried various regexy approaches to extract this programmatically but landed on hard-coding.
            return [
                'Year Since Start',
                'Carbon Avoided (pound)',
                'CCUS Price (USD/lb)',  # Carbon Price (USD/tonne)
                'CCUS Revenue (MUSD/yr)',  # Carbon Ann. Rev. (MUSD/yr)
                'CCUS Annual Cash Flow (MUSD/yr)',
                'CCUS Cumm. Cash Flow (MUSD)',  # Carbon Cumm. Rev. (MUSD)
                'Project Annual Cash Flow (MUSD/yr)',
                'Project Cumm. Cash Flow (MUSD)',
            ]

        try:
            lines = self._get_profile_lines('CCUS PROFILE')
            profile = [extract_table_header(lines)]
            profile.extend(self._extract_addons_style_table_data(lines))
            return profile
        except BaseException as e:
            self._logger.debug(f'Failed to get CCUS profile: {e}')
            return None

    def _extract_addons_style_table_data(self, lines: list):
        """TODO consolidate with _get_data_from_profile_lines"""

        # Skip the lines up to the header and split the rest using whitespaces
        lines_splitted = [line.replace('|', '').split() for line in lines[5:]]

        # The number of columns is determined by the line with the most elements
        num_of_columns = max(len(line) for line in lines_splitted)

        table_data = []

        # Parse the contents of each row
        for line in lines_splitted:
            row_data = ['' for _ in range(num_of_columns)]
            while len(line) < num_of_columns:
                line.insert(1, '')

            if not any(line):
                continue

            for i in range(len(line)):
                row_data[i] = self._parse_number(line[i])
            table_data.append(row_data)

        return table_data

    def _get_profile_lines(self, profile_name):
        s1 = f'*  {profile_name}  *'
        s2 = '\n\n'
        return ''.join(self._lines).split(s1)[1].split(s2)[0].split('\n')  # [5:]

    def _get_data_from_profile_lines(self, profile_lines):
        data_lines = profile_lines[5:]

        header_lines = profile_lines[2:5]
        data_headers = None
        for idx, header_line in enumerate(header_lines):
            cols = re.split(r'\s\s+', header_line)[1:]

            if idx == 0:
                data_headers = [''] * len(cols)

            for idxc, col in enumerate(cols):
                data_header_idx = idxc
                if data_headers[0] == 'YEAR' and idx > 0 and idxc >= 0:
                    data_header_idx += 1

                if data_headers[1] == 'THERMAL DRAWDOWN' and idx > 1:  # and idxc > 0:
                    data_header_idx += 1

                data_headers[data_header_idx] = f'{data_headers[data_header_idx]} {col.strip()}'.lstrip()

        data = [data_headers]
        str_entries = filter(lambda entry: len(entry) > 1, [re.split(r'\s+', line)[1:] for line in data_lines])
        data.extend([self._parse_number(str_entry) for str_entry in x] for x in str_entries)
        return data

    def _parse_number(self, number_str, field='string') -> int | float:
        try:
            if '.' in number_str:
                # TODO should probably ideally use decimal.Decimal to preserve precision,
                #  i.e. 1.00 for USD instead of 1.0
                return float(number_str)
            else:
                return int(number_str)
        except BaseException:
            self._logger.warning(f'Unable to parse {field} as number: {number_str}')
            return None

    def _get_end_use_option(self) -> EndUseOption:
        try:
            end_use_option_snippet = next(filter(lambda x: 'End-Use Option: ' in x, self._lines)).split(
                'End-Use Option: '
            )[1]

            if 'Direct-Use Heat' in end_use_option_snippet:
                return EndUseOption.DIRECT_USE_HEAT
            elif 'Electricity' in end_use_option_snippet:
                return EndUseOption.ELECTRICITY
        except StopIteration:
            # FIXME clean up
            try:
                end_use_option_snippet = next(filter(lambda x: 'End-Use: ' in x, self._lines)).split('End-Use: ')[1]

                if 'Direct-Use Heat' in end_use_option_snippet:
                    return EndUseOption.DIRECT_USE_HEAT
                elif 'Electricity' in end_use_option_snippet:
                    return EndUseOption.ELECTRICITY
            except StopIteration:
                # FIXME
                self._logger.error('Failed to parse End-Use Option')

        return None

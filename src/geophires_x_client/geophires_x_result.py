import re
from types import MappingProxyType

from .common import _get_logger
from .geophires_input_parameters import EndUseOption


class GeophiresXResult:
    _RESULT_FIELDS_BY_CATEGORY = MappingProxyType(
        {
            'SUMMARY OF RESULTS': [
                # TODO uses colon delimiter inconsistently
                # 'End-Use Option',
                'End-Use',
                'Average Net Electricity Production',
                'Electricity breakeven price',
                'Average Direct-Use Heat Production',
                'Direct-Use heat breakeven price',
                'Annual District Heating Demand',
                'Average Cooling Production',
                'Average Annual Geothermal Heat Production',
                'Average Annual Peaking Fuel Heat Production',
                'Direct-Use Cooling Breakeven Price',
                'Number of production wells',
                'Number of injection wells',
                'Flowrate per production well',
                'Well depth',
                'Geothermal gradient',
                # AGS/CLGS
                'LCOE',
                'LCOH',
            ],
            'ECONOMIC PARAMETERS': [
                'Interest Rate',  # %
                'Accrued financing during construction',
                'Project lifetime',
                'Capacity factor',
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
                'Production well casing ID',  # TODO correct typo upstream
                'Number of times redrilling',
                # 'Power plant type', # Not a number - TODO parse non-number values without throwing exception
                # AGS/CLGS
                'Fluid',
                'Design',
                'Flow rate',
                'Lateral Length',
                'Vertical Depth',
                'Wellbore Diameter',
            ],
            'RESOURCE CHARACTERISTICS': ['Maximum reservoir temperature', 'Number of segments', 'Geothermal gradient'],
            'RESERVOIR PARAMETERS': [
                # TODO 'Reservoir Model = 1-D Linear Heat Sweep Model'
                # TODO 'Fracture model = Rectangular'
                # TODO moved to power generation profile, parse from there
                #  'Annual Thermal Drawdown (%/year)',
                'Bottom-hole temperature',
                'Well seperation: fracture height',  # TODO correct typo upstream
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
                # TODO 'Production Wellbore Heat Transmission Model = Ramey Model'
                'Average Production Well Temperature Drop',
                'Average Injection Well Pump Pressure Drop',
                'Average Production Well Pump Pressure Drop',
                'Average Production Pressure',
                'Average Heat Production',
                'First Year Heat Production',
                'Average Net Electricity Production',
                'First Year Electricity Production',
            ],
            'CAPITAL COSTS (M$)': [
                'Drilling and completion costs',
                'Drilling and completion costs per well',
                'Stimulation costs',
                'Surface power plant costs',
                # TODO 'of which [...] costs'
                'District Heating System Cost',
                'Field gathering system costs',
                'Total surface equipment costs',
                'Exploration costs',
                'Total capital costs',
                # AGS/CLGS
                'Total CAPEX',
                'Drilling Cost',
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
            ],
        }
    )

    _METADATA_FIELDS = (
        # 'End-Use Option',
        'Economic Model',
        'Reservoir Model',
    )

    def __init__(self, output_file_path, logger_name='root'):
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
                self.result[category][field] = self._get_result_field(field)

        try:
            self.result['POWER GENERATION PROFILE'] = self._get_power_generation_profile()
            self.result[
                'HEAT AND/OR ELECTRICITY EXTRACTION AND GENERATION PROFILE'
            ] = self._get_heat_electricity_extraction_generation_profile()
        except Exception as e:
            # FIXME
            self._logger.error(f'Failed to parse power and/or extraction profiles: {e}')

        self.result['metadata'] = {'output_file_path': self.output_file_path}
        for metadata_field in GeophiresXResult._METADATA_FIELDS:
            self.result['metadata'][metadata_field] = self._get_metadata_field(metadata_field)

        if self._get_end_use_option() is not None:
            self.result['metadata']['End-Use Option'] = self._get_end_use_option().name

    @property
    def direct_use_heat_breakeven_price_USD_per_MMBTU(self):
        summary = self.result['SUMMARY OF RESULTS']
        if 'Direct-Use heat breakeven price' in summary and summary['Direct-Use heat breakeven price'] is not None:
            return summary['Direct-Use heat breakeven price']['value']
        else:
            return None

    def _get_result_field(self, field):
        # TODO make this less fragile with proper regex
        matching_lines = set(filter(lambda line: f'  {field}:  ' in line, self._lines))

        if len(matching_lines) == 0:
            self._logger.warning(f'Field not found: {field}')
            return None

        if len(matching_lines) > 1:
            self._logger.warning(
                f'Found multiple ({len(matching_lines)}) entries for field: {field}\n\t{matching_lines}'
            )

        matching_line = matching_lines.pop()
        val_and_unit_str = re.sub(r'\s\s+', '', matching_line.replace(f'{field}:', '').replace('\n', ''))
        val_and_unit_tuple = val_and_unit_str.strip().split(' ')
        str_val = val_and_unit_tuple[0]

        unit = None
        if len(val_and_unit_tuple) == 2:
            unit = val_and_unit_tuple[1]
        elif field.startswith('Number'):
            unit = 'count'

        return {'value': self._parse_number(str_val, field=f'field "{field}"'), 'unit': unit}

    def _get_metadata_field(self, metadata_field):
        metadata_marker = f'{metadata_field} = '
        matching_lines = set(filter(lambda line: metadata_marker in line, self._lines))

        if len(matching_lines) == 0:
            self._logger.warning(f'Metadata Field not found: {metadata_field}')
            return None

        if len(matching_lines) > 1:
            self._logger.warning(
                f'Found multiple ({len(matching_lines)}) entries for metadata field: {metadata_field}\n\t{matching_lines}'
            )

        return matching_lines.pop().split(metadata_marker)[1].replace('\n', '')

    @property
    def power_generation_profile(self):
        return self.result['POWER GENERATION PROFILE']

    def _get_power_generation_profile(self):
        profile_lines = None
        try:
            s1 = '*  HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE  *'
            s2 = '***************************************************************'  # header of next profile
            profile_lines = ''.join(self._lines).split(s1)[1].split(s2)[0].split('\n')  # [5:]
        except IndexError:
            s1 = '*  POWER GENERATION PROFILE  *'
            s2 = '***************************************************************'  # header of next profile
            profile_lines = ''.join(self._lines).split(s1)[1].split(s2)[0].split('\n')  # [5:]
        return self._get_data_from_profile_lines(profile_lines)

    @property
    def heat_electricity_extraction_generation_profile(self):
        return self.result['HEAT AND/OR ELECTRICITY EXTRACTION AND GENERATION PROFILE']

    def _get_heat_electricity_extraction_generation_profile(self):
        profile_lines = None
        try:
            s1 = '*  ANNUAL HEATING, COOLING AND/OR ELECTRICITY PRODUCTION PROFILE  *'
            profile_lines = ''.join(self._lines).split(s1)[1].split('\n')
        except IndexError:
            s1 = '*  HEAT AND/OR ELECTRICITY EXTRACTION AND GENERATION PROFILE  *'
            profile_lines = ''.join(self._lines).split(s1)[1].split('\n')
        return self._get_data_from_profile_lines(profile_lines)

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

    def _parse_number(self, number_str, field='string'):
        try:
            if '.' in number_str:
                return float(number_str)
            else:
                return int(number_str)
        except TypeError:
            self._logger.error(f'Unable to parse {field} as number: {number_str}')
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

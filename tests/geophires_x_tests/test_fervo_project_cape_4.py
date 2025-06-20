import re
from typing import Any

from base_test_case import BaseTestCase
from geophires_x.GeoPHIRESUtils import sig_figs
from geophires_x.Parameter import HasQuantity
from geophires_x_client import GeophiresInputParameters
from geophires_x_client import GeophiresXClient
from geophires_x_client import GeophiresXResult


class FervoProjectCape4TestCase(BaseTestCase):

    def test_fervo_project_cape_4_results_against_reference_values(self):
        """
        Asserts that results conform to some of the key reference values claimed in docs/Fervo_Project_Cape-4.md.
        """

        r = GeophiresXClient().get_geophires_result(
            GeophiresInputParameters(from_file_path=self._get_test_file_path('../examples/Fervo_Project_Cape-4.txt'))
        )

        min_net_gen = r.result['SURFACE EQUIPMENT SIMULATION RESULTS']['Minimum Net Electricity Generation']['value']
        self.assertGreater(min_net_gen, 500)
        self.assertLess(min_net_gen, 505)

        max_total_gen = r.result['SURFACE EQUIPMENT SIMULATION RESULTS']['Maximum Total Electricity Generation'][
            'value'
        ]
        self.assertGreater(max_total_gen, 600)
        self.assertLess(max_total_gen, 650)

        lcoe = r.result['SUMMARY OF RESULTS']['Electricity breakeven price']['value']
        self.assertGreater(lcoe, 7.5)
        self.assertLess(lcoe, 8.5)

        redrills = r.result['ENGINEERING PARAMETERS']['Number of times redrilling']['value']
        self.assertGreater(redrills, 2)
        self.assertLess(redrills, 7)

        well_cost = r.result['CAPITAL COSTS (M$)']['Drilling and completion costs per well']['value']
        self.assertLess(well_cost, 4.0)
        self.assertGreater(well_cost, 3.0)

        pumping_power_pct = r.result['SURFACE EQUIPMENT SIMULATION RESULTS'][
            'Initial pumping power/net installed power'
        ]['value']
        self.assertGreater(pumping_power_pct, 13)
        self.assertLess(pumping_power_pct, 17)

    def test_case_study_documentation(self):
        """
        Parses result values from case study documentation markdown and checks that they match the actual result.
        Useful for catching when minor updates are made to the case study which need to be manually synced to the
        documentation.
        """

        def _parse_value_unit(raw_string: str) -> dict:
            """
            A helper function to parse a string and extract a numerical value and its unit.
            It handles various formats like currency, percentages, and scientific notation.
            """
            # First, strip any parenthetical notes, e.g., "(based on...)"
            clean_str = re.split(r'\(', raw_string)[0].strip()

            # Case 1: LCOE format ($X.X/MWh -> cents/kWh)
            match = re.match(r'^\$(\d+\.?\d*)/MWh$', clean_str)
            if match:
                value_ = float(match.group(1))
                # Convert $/MWh to cents/kWh by dividing by 10
                return {'value': round(value_ / 10, 2), 'unit': 'cents/kWh'}

            # Case 2: Billion dollar format ($X.XB -> MUSD)
            match = re.match(r'^\$(\d+\.?\d*)B$', clean_str)
            if match:
                value_ = float(match.group(1))
                return {'value': value_ * 1000, 'unit': 'MUSD'}

            # Case 3: Million dollar format ($X.XM...)
            match = re.match(r'^\$(\d+\.?\d*)M', clean_str)
            if match:
                value_ = float(match.group(1))
                return {'value': value_, 'unit': 'MUSD'}

            # Case 4: Dollar per kW format ($X/kW -> USD/kW)
            match = re.match(r'^\$(\d+\.?\d*)/kW$', clean_str)
            if match:
                value_ = float(match.group(1))
                return {'value': value_, 'unit': 'USD/kW'}

            # Case 5: Percentage format (X.X%)
            match = re.match(r'^(\d+\.?\d*)%$', clean_str)
            if match:
                value_ = float(match.group(1))
                return {'value': value_, 'unit': '%'}

            # Case 6: Temperature format (X℃ -> degC)
            match = re.match(r'^(\d+\.?\d*)℃$', clean_str)
            if match:
                value_ = float(match.group(1))
                return {'value': value_, 'unit': 'degC'}

            # Case 7: Scientific notation format (X.X×10⁶ Y) # ruff: noqa: RUF003
            match = re.match(r'^(\d+\.?\d*)\s*[×xX]\s*10[⁶6]\s*(.*)$', clean_str)
            if match:
                base_value = float(match.group(1))
                unit = match.group(2).strip()
                return {'value': base_value * 1e6, 'unit': unit}

            # Case 8: Standard number and unit (e.g., "503 MW")
            match = re.match(r'^(\d+\.?\d*)\s*([a-zA-Z²³\/]+)$', clean_str)
            if match:
                value_ = float(match.group(1))
                unit = match.group(2)
                return {'value': value_, 'unit': unit}

            # Case 9: Dimensionless integer number (e.g., "3")
            match = re.match(r'^(\d+)$', clean_str)
            if match:
                value_ = int(match.group(1))
                return {'value': value_, 'unit': 'count'}

            # Fallback for any unhandled formats
            return {'value': clean_str, 'unit': 'unknown'}

        def parse_markdown_results_structured(markdown_text: str) -> dict:
            """
            Parses result values from markdown into a structured dictionary with values and units.
            """
            raw_results = {}
            table_pattern = re.compile(r'^\s*\|\s*(?!-)([^|]+?)\s*\|\s*([^|]+?)\s*\|', re.MULTILINE)

            try:
                results_start_index = markdown_text.index('## Results')
                search_area = markdown_text[results_start_index:]

                matches = table_pattern.findall(search_area)

                # Use key_ and value_ to avoid shadowing
                for match in matches:
                    key_ = match[0].strip()
                    value_ = match[1].strip()
                    if key_.lower() not in ('metric', 'parameter'):
                        raw_results[key_] = value_
            except ValueError:
                print("Warning: '## Results' section not found.")
                return {}

            # Consistency check
            special_case_pattern = re.compile(r'LCOE\s*=\s*(\S+)\s*and\s*CAPEX\s*=\s*(\S+)')
            special_case_match = special_case_pattern.search(markdown_text)
            if special_case_match:
                lcoe_text = special_case_match.group(1).rstrip('.,;')
                lcoe_table_base = raw_results.get('LCOE', '').split('(')[0].strip()
                if lcoe_text != lcoe_table_base:
                    raise ValueError(
                        f'LCOE mismatch: Text value ({lcoe_text}) does not match table value ({lcoe_table_base}).'
                    )

            # Now, process the raw results into the structured format
            structured_results = {}
            # Use key_ and value_ to avoid shadowing
            for key_, value_ in raw_results.items():
                if key_ in [
                    'After-tax IRR',
                    'Average Production Temperature',
                    'LCOE',
                    'Maximum Total Electricity Generation',
                    'Minimum Net Electricity Generation',
                    'Number of times redrilling',
                    'Project capital costs: Total CAPEX',
                    'Project capital costs: $/kW',
                    'WACC',
                    'Well Drilling and Completion Cost',
                ]:
                    structured_results[key_] = _parse_value_unit(value_)

            return structured_results

        results_in_markdown = parse_markdown_results_structured(
            '\n'.join(self._get_test_file_content('../../docs/Fervo_Project_Cape-4.md'))
        )

        self.assertEqual(3.96, results_in_markdown['Well Drilling and Completion Cost']['value'])
        self.assertEqual('MUSD', results_in_markdown['Well Drilling and Completion Cost']['unit'])

        class Q(HasQuantity):
            def __init__(self, vu: dict[str, Any]):
                self.value = vu['value']

                # https://stackoverflow.com/questions/2280334/shortest-way-of-creating-an-object-with-arbitrary-attributes-in-python
                self.CurrentUnits = type('', (), {})()

                self.CurrentUnits.value = vu['unit']

        capex_q = Q(results_in_markdown['Project capital costs: Total CAPEX']).quantity()
        markdown_capex_USD_per_kW = (
            capex_q.to('USD').magnitude
            / Q(results_in_markdown['Maximum Total Electricity Generation']).quantity().to('kW').magnitude
        )
        self.assertAlmostEqual(
            sig_figs(markdown_capex_USD_per_kW, 3), results_in_markdown['Project capital costs: $/kW']['value']
        )

        field_mapping = {
            'LCOE': 'Electricity breakeven price',
            'Project capital costs: Total CAPEX': 'Total CAPEX',
            'Well Drilling and Completion Cost': 'Drilling and completion costs per well',
        }

        ignore_keys = ['Project capital costs: $/kW', 'Total fracture surface area per production well']

        example_result = GeophiresXResult(self._get_test_file_path('../examples/Fervo_Project_Cape-4.out'))
        example_result_values_in_documentation = {}
        for key, _ in results_in_markdown.items():
            if key not in ignore_keys:
                mapped_key = field_mapping.get(key) if key in field_mapping else key
                entry = example_result._get_result_field(mapped_key)
                if entry is not None and 'value' in entry:
                    entry['value'] = sig_figs(entry['value'], 3)

                example_result_values_in_documentation[key] = entry

        for ignore_key in ignore_keys:
            if ignore_key in results_in_markdown:
                del results_in_markdown[ignore_key]

        self.assertDictAlmostEqual(results_in_markdown, example_result_values_in_documentation, places=3)

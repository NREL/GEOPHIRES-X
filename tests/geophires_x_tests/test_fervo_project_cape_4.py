from base_test_case import BaseTestCase
from geophires_x_client import GeophiresInputParameters
from geophires_x_client import GeophiresXClient


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

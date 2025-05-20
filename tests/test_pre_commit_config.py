import re
import unittest


class PreCommitConfigTestCase(unittest.TestCase):
    """
    Utility for making updates to .pre-commit-config.yaml
    """

    def test_pre_commit_exclude_pattern(self):
        pattern = r'^(\.tox|ci/templates|\.bumpversion\.cfg|src/geophires_x(?!/(GEOPHIRESv3|EconomicsSam|EconomicsSamCashFlow)\.py))(/|$)'
        self.assertFalse(re.match(pattern, 'src/geophires_x/GEOPHIRESv3.py'))
        self.assertFalse(re.match(pattern, 'src/geophires_x/EconomicsSam.py'))
        self.assertFalse(re.match(pattern, 'src/geophires_x/EconomicsSamCashFlow.py'))
        self.assertTrue(re.match(pattern, 'src/geophires_x/Economics.py'))


if __name__ == '__main__':
    unittest.main()

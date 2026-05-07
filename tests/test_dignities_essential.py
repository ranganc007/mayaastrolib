"""Smoke tests for mayaastrolib.dignities.essential.

Reference: recipes/essentialdignities.py.
"""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.dignities import essential
from mayaastrolib.geopos import GeoPos


class EssentialDignityTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)
        self.sun = self.chart.get(const.SUN)

    def test_module_imports(self):
        self.assertIsNotNone(essential)

    def test_score_returns_int(self):
        score = essential.score(self.sun.id, self.sun.sign, self.sun.signlon)
        self.assertIsInstance(score, int)

    def test_essential_info_has_score(self):
        info = essential.EssentialInfo(self.sun)
        self.assertIsInstance(info.score, int)

    def test_ruler_returns_planet_id(self):
        ruler_id = essential.ruler(self.sun.sign)
        self.assertIn(ruler_id, const.LIST_SEVEN_PLANETS)


if __name__ == "__main__":
    unittest.main()

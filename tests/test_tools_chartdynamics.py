"""Smoke tests for flatlib.tools.chartdynamics.

Reference: recipes/chartdynamics.py.
"""

import unittest

from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.tools.chartdynamics import ChartDynamics


class ChartDynamicsTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)
        self.dyn = ChartDynamics(self.chart)

    def test_chart_dynamics_constructs(self):
        self.assertIsNotNone(self.dyn)

    def test_in_dignities_returns_list(self):
        result = self.dyn.inDignities(const.JUPITER, const.SUN)
        self.assertIsInstance(result, list)

    def test_is_voc_returns_bool(self):
        voc = self.dyn.isVOC(const.MERCURY)
        self.assertIsInstance(voc, bool)


if __name__ == "__main__":
    unittest.main()

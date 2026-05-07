"""Smoke tests for mayaastrolib.tools.chartdynamics.

Reference: recipes/chartdynamics.py.
"""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.tools.chartdynamics import ChartDynamics


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

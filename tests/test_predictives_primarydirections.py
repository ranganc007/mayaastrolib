"""Smoke tests for flatlib.predictives.primarydirections.

Reference: recipes/primarydirections.py.
"""

import unittest

from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.predictives import primarydirections
from flatlib.predictives.primarydirections import PDTable, PrimaryDirections


class PrimaryDirectionsTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)
        self.pos = pos

    def test_module_imports(self):
        self.assertIsNotNone(primarydirections)

    def test_get_arc_returns_float(self):
        prom = self.chart.get(const.MARS)
        sig = self.chart.get(const.MERCURY)
        mc = self.chart.get(const.MC)
        arc = primarydirections.getArc(prom, sig, mc, self.pos, zerolat=True)
        self.assertIsInstance(arc, float)

    def test_primary_directions_class_constructs(self):
        pd = PrimaryDirections(self.chart)
        result = pd.getArc(pd.N(const.MARS), pd.N(const.MERCURY))
        self.assertIn("arcm", result)
        self.assertIn("arcz", result)

    def test_pdtable_constructs(self):
        table = PDTable(self.chart, const.MAJOR_ASPECTS)
        self.assertIsNotNone(table)


if __name__ == "__main__":
    unittest.main()

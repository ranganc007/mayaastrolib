"""Smoke tests for flatlib.predictives.profections.

Reference: recipes/profections.py.
"""

import unittest

from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.predictives import profections


class ProfectionsTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2011/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)
        self.target = Datetime("2015/04/06", "10:40", "+01:00")

    def test_module_imports(self):
        self.assertIsNotNone(profections)

    def test_compute_returns_chart_with_asc(self):
        pchart = profections.compute(self.chart, self.target)
        asc = pchart.get(const.ASC)
        self.assertIsNotNone(asc)
        self.assertIsNotNone(asc.sign)


if __name__ == "__main__":
    unittest.main()

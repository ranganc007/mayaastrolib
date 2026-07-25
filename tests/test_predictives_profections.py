"""Smoke tests for mayaastrolib.predictives.profections.

Reference: recipes/profections.py.
"""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.predictives import profections


class ProfectionsTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2011/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)
        self.target = Datetime("2015/04/06", "10:40", "+01:00")

    def test_module_imports(self):
        self.assertIsNotNone(profections)

    def test_profected_chart_has_asc(self):
        # profections.compute() was removed in 1.0; Chart.profected is the
        # entry point. The module is kept importable for the 1.0 cycle.
        pchart = self.chart.profected(target_date=self.target)
        asc = pchart.get(const.ASC)
        self.assertIsNotNone(asc)
        self.assertIsNotNone(asc.sign)


if __name__ == "__main__":
    unittest.main()

"""Smoke tests for flatlib.predictives.returns.

Reference: recipes/solarreturn.py.
"""

import unittest

from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.predictives import returns


class SolarReturnTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2013/06/13", "17:00", "+01:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)
        self.target = Datetime("2015/04/06", "10:40", "+01:00")

    def test_module_imports(self):
        self.assertIsNotNone(returns)

    def test_next_solar_return_returns_chart(self):
        sr = returns.nextSolarReturn(self.chart, self.target)
        self.assertIsInstance(sr, Chart)
        self.assertIsNotNone(sr.get(const.ASC))


if __name__ == "__main__":
    unittest.main()

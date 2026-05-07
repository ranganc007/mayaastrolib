"""Smoke tests for flatlib.protocols.temperament.

Reference: recipes/temperament.py.
"""

import unittest

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.protocols.temperament import Temperament


class TemperamentTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)

    def test_temperament_constructs(self):
        t = Temperament(self.chart)
        self.assertIsNotNone(t)

    def test_temperament_factors_iterable(self):
        t = Temperament(self.chart)
        factors = t.getFactors()
        self.assertIsNotNone(factors)
        list(factors)

    def test_temperament_score_is_dict(self):
        t = Temperament(self.chart)
        score = t.getScore()
        self.assertIsInstance(score, dict)


if __name__ == "__main__":
    unittest.main()

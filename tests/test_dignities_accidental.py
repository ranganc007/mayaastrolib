"""Smoke tests for flatlib.dignities.accidental.

Reference: recipes/accidentaldignities.py.
"""

import unittest

from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.dignities import accidental
from flatlib.dignities.accidental import AccidentalDignity
from flatlib.geopos import GeoPos


class AccidentalDignityTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)
        self.venus = self.chart.get(const.VENUS)
        self.sun = self.chart.get(const.SUN)

    def test_module_imports(self):
        self.assertIsNotNone(accidental)

    def test_sun_relation_returns_string_or_none(self):
        # None when the planet has no special Sun relation (combust/cazimi/etc).
        rel = accidental.sunRelation(self.venus, self.sun)
        self.assertTrue(rel is None or isinstance(rel, str))

    def test_accidental_dignity_score_is_numeric(self):
        adign = AccidentalDignity(self.venus, self.chart)
        score = adign.score()
        self.assertIsInstance(score, (int, float))


if __name__ == "__main__":
    unittest.main()

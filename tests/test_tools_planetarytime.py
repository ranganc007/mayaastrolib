"""Smoke tests for mayaastrolib.tools.planetarytime.

Reference: recipes/planetarytime.py.
"""

import unittest

from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.tools import planetarytime
from mayaastrolib.tools.planetarytime import HourTable


class PlanetaryTimeTests(unittest.TestCase):
    def setUp(self):
        self.date = Datetime("2015/03/13", "17:00", "+00:00")
        self.pos = GeoPos("38n32", "8w54")

    def test_module_imports(self):
        self.assertIsNotNone(planetarytime)

    def test_get_hour_table_returns_hourtable(self):
        ht = planetarytime.getHourTable(self.date, self.pos)
        self.assertIsInstance(ht, HourTable)

    def test_hour_table_rulers_are_strings(self):
        ht = planetarytime.getHourTable(self.date, self.pos)
        self.assertIsInstance(ht.dayRuler(), str)
        self.assertIsInstance(ht.nightRuler(), str)
        self.assertIsInstance(ht.hourRuler(), str)


if __name__ == "__main__":
    unittest.main()

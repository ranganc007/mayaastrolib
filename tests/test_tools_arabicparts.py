"""Smoke tests for flatlib.tools.arabicparts.

Reference: recipes/arabicparts.py.
"""

import unittest

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.object import GenericObject
from flatlib.tools import arabicparts


class ArabicPartsTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)

    def test_module_imports(self):
        self.assertIsNotNone(arabicparts)

    def test_get_part_returns_generic_object(self):
        part = arabicparts.getPart(arabicparts.PARS_FORTUNA, self.chart)
        self.assertIsInstance(part, GenericObject)
        self.assertIsNotNone(part.sign)


if __name__ == "__main__":
    unittest.main()

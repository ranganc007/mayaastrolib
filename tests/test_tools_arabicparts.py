"""Smoke tests for mayaastrolib.tools.arabicparts.

Reference: recipes/arabicparts.py.
"""

import unittest

from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.object import GenericObject
from mayaastrolib.tools import arabicparts


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

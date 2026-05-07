"""Smoke tests for mayaastrolib.protocols.almutem.

Reference: recipes/almutem.py.
"""

import unittest

from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.protocols import almutem


class AlmutemTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)

    def test_module_imports(self):
        self.assertIsNotNone(almutem)

    def test_compute_returns_score_dict(self):
        alm = almutem.compute(self.chart)
        self.assertIn("Score", alm)
        self.assertIsInstance(alm["Score"], dict)
        self.assertGreater(len(alm["Score"]), 0)


if __name__ == "__main__":
    unittest.main()

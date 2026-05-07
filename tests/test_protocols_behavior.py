"""Smoke tests for mayaastrolib.protocols.behavior.

Reference: recipes/behavior.py.
"""

import unittest

from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.protocols import behavior


class BehaviorTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)

    def test_module_imports(self):
        self.assertIsNotNone(behavior)

    def test_compute_returns_iterable(self):
        factors = behavior.compute(self.chart)
        # Recipe iterates over the result, so it must be iterable.
        self.assertIsNotNone(factors)
        list(factors)  # consume; raises if not iterable


if __name__ == "__main__":
    unittest.main()

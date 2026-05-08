"""Tests for Object.antiscion / Object.cantiscion (Task 010).

Antiscia preserve dynamics — the reflected position shares
``lonspeed`` / ``latspeed`` with the original. The legacy
``Object.antiscia`` / ``Object.cantiscia`` are now deprecated thin
wrappers and emit ``DeprecationWarning``.
"""

import unittest
import warnings

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos


def _chart():
    date = Datetime("2015/03/13", "17:00", "+00:00")
    pos = GeoPos("38n32", "8w54")
    return Chart(date, pos)


class AntiscionTests(unittest.TestCase):
    def setUp(self):
        self.chart = _chart()
        self.sun = self.chart.get(const.SUN)

    def test_antiscion_returns_object(self):
        anti = self.sun.antiscion()
        self.assertIsNotNone(anti)
        self.assertEqual(type(anti).__name__, type(self.sun).__name__)

    def test_antiscion_preserves_lonspeed(self):
        anti = self.sun.antiscion()
        self.assertEqual(anti.lonspeed, self.sun.lonspeed)

    def test_antiscion_preserves_latspeed(self):
        anti = self.sun.antiscion()
        self.assertEqual(anti.latspeed, self.sun.latspeed)

    def test_antiscion_movement_matches_original(self):
        anti = self.sun.antiscion()
        self.assertEqual(anti.movement, self.sun.movement)

    def test_antiscion_longitude_formula(self):
        anti = self.sun.antiscion()
        expected = (360 - self.sun.lon + 180) % 360
        self.assertAlmostEqual(anti.lon, expected, places=5)

    def test_antiscion_does_not_mutate_original(self):
        original_lon = self.sun.lon
        self.sun.antiscion()
        self.assertEqual(self.sun.lon, original_lon)

    def test_antiscion_changes_type_to_generic(self):
        anti = self.sun.antiscion()
        self.assertEqual(anti.type, const.OBJ_GENERIC)


class CantiscionTests(unittest.TestCase):
    def setUp(self):
        self.chart = _chart()
        self.sun = self.chart.get(const.SUN)

    def test_cantiscion_returns_object(self):
        c = self.sun.cantiscion()
        self.assertIsNotNone(c)

    def test_cantiscion_preserves_speed(self):
        c = self.sun.cantiscion()
        self.assertEqual(c.lonspeed, self.sun.lonspeed)

    def test_cantiscion_longitude_formula(self):
        c = self.sun.cantiscion()
        expected = (360 - self.sun.lon) % 360
        self.assertAlmostEqual(c.lon, expected, places=5)


class DeprecatedAntisciaTests(unittest.TestCase):
    def setUp(self):
        self.chart = _chart()
        self.sun = self.chart.get(const.SUN)

    def test_antiscia_warns(self):
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            self.sun.antiscia()
        self.assertTrue(
            any(issubclass(w.category, DeprecationWarning) for w in captured),
            "Object.antiscia() should emit DeprecationWarning",
        )

    def test_antiscia_returns_same_as_antiscion(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            legacy = self.sun.antiscia()
        modern = self.sun.antiscion()
        self.assertAlmostEqual(legacy.lon, modern.lon, places=5)

    def test_cantiscia_warns(self):
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            self.sun.cantiscia()
        self.assertTrue(
            any(issubclass(w.category, DeprecationWarning) for w in captured),
            "Object.cantiscia() should emit DeprecationWarning",
        )


if __name__ == "__main__":
    unittest.main()

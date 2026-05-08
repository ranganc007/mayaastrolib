"""Tests for Object.with_longitude (Task 010).

Covers the new coordinate-transform primitive that replaces the
in-place ``relocate()`` mutation, and the None-speed handling on
``movement`` / ``isFast`` / ``isDirect`` / ``isRetrograde`` /
``isStationary``.
"""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos


def _chart():
    date = Datetime("2015/03/13", "17:00", "+00:00")
    pos = GeoPos("38n32", "8w54")
    return Chart(date, pos)


class WithLongitudeTests(unittest.TestCase):
    def setUp(self):
        self.chart = _chart()
        self.sun = self.chart.get(const.SUN)

    def test_returns_new_instance(self):
        new = self.sun.with_longitude(100.0)
        self.assertIsNot(new, self.sun)

    def test_does_not_mutate_original(self):
        original_lon = self.sun.lon
        self.sun.with_longitude(100.0)
        self.assertEqual(self.sun.lon, original_lon)

    def test_default_clears_speed(self):
        new = self.sun.with_longitude(100.0)
        self.assertIsNone(new.lonspeed)
        self.assertIsNone(new.latspeed)

    def test_preserve_speed_keeps_speed(self):
        new = self.sun.with_longitude(100.0, preserve_speed=True)
        self.assertEqual(new.lonspeed, self.sun.lonspeed)
        self.assertEqual(new.latspeed, self.sun.latspeed)

    def test_sign_recalculated(self):
        # 100° is in Cancer (90-120)
        new = self.sun.with_longitude(100.0)
        self.assertEqual(new.sign, const.CANCER)
        self.assertAlmostEqual(new.signlon, 10.0, places=5)

    def test_modulo_360(self):
        new = self.sun.with_longitude(370.0)
        self.assertAlmostEqual(new.lon, 10.0, places=5)


class MovementWithNoSpeedTests(unittest.TestCase):
    def setUp(self):
        self.chart = _chart()
        self.sun = self.chart.get(const.SUN)

    def test_movement_is_none_when_speed_none(self):
        symbolic = self.sun.with_longitude(100.0)
        self.assertIsNone(symbolic.movement)

    def test_movement_is_falsy_when_none(self):
        symbolic = self.sun.with_longitude(100.0)
        self.assertFalse(symbolic.movement)

    def test_movement_is_real_when_speed_preserved(self):
        antiscion_like = self.sun.with_longitude(100.0, preserve_speed=True)
        self.assertIsNotNone(antiscion_like.movement)
        self.assertIn(
            antiscion_like.movement,
            [const.DIRECT, const.RETROGRADE, const.STATIONARY],
        )

    def test_isRetrograde_is_none_when_speed_none(self):
        symbolic = self.sun.with_longitude(100.0)
        self.assertIsNone(symbolic.isRetrograde())

    def test_isDirect_is_none_when_speed_none(self):
        symbolic = self.sun.with_longitude(100.0)
        self.assertIsNone(symbolic.isDirect())

    def test_isStationary_is_none_when_speed_none(self):
        symbolic = self.sun.with_longitude(100.0)
        self.assertIsNone(symbolic.isStationary())

    def test_isFast_is_none_when_speed_none(self):
        symbolic = self.sun.with_longitude(100.0)
        self.assertIsNone(symbolic.isFast())


class GenericObjectWithLongitudeTests(unittest.TestCase):
    """House and angle (GenericObject subclasses) also support
    with_longitude — preserve_speed is a no-op for them.
    """

    def setUp(self):
        self.chart = _chart()

    def test_house_with_longitude(self):
        h1 = self.chart.getHouse(const.HOUSE1)
        new_h = h1.with_longitude(h1.lon + 30.0)
        self.assertIsNot(new_h, h1)
        self.assertAlmostEqual(new_h.lon, (h1.lon + 30.0) % 360, places=5)

    def test_angle_with_longitude(self):
        asc = self.chart.getAngle(const.ASC)
        new_asc = asc.with_longitude(asc.lon + 90.0)
        self.assertAlmostEqual(new_asc.lon, (asc.lon + 90.0) % 360, places=5)


if __name__ == "__main__":
    unittest.main()

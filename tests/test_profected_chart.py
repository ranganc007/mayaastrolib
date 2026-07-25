"""Tests for Chart.profected (Task 010).

The profected chart represents natal positions rotated forward by one
sign per year. Because rotated positions are symbolic, planet speeds
are cleared (``lonspeed = latspeed = None``) and dynamics-derived
attributes (``movement``, ``isRetrograde``) return ``None``. This is
the bug fix the task exists to deliver — the legacy
``profections.compute()`` left speeds stale. That function was removed
in 1.0; the longitudes it produced are pinned below as literals so the
equivalence it used to prove is still guarded.
"""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos


def _natal():
    date = Datetime("1980/06/15", "12:00", "+00:00")
    pos = GeoPos("51n30", "0w08")  # London
    return Chart(date, pos)


class ProfectedChartTests(unittest.TestCase):
    def setUp(self):
        self.natal = _natal()

    def test_profected_returns_chart(self):
        p = self.natal.profected(years=42)
        self.assertIsInstance(p, Chart)

    def test_profected_is_symbolic(self):
        p = self.natal.profected(years=42)
        self.assertTrue(p.is_symbolic)
        self.assertEqual(p.symbolic_kind, "profection")

    def test_natal_not_symbolic(self):
        self.assertFalse(self.natal.is_symbolic)
        self.assertIsNone(self.natal.symbolic_kind)

    def test_profected_planets_have_no_speed(self):
        p = self.natal.profected(years=42)
        sun = p.get(const.SUN)
        self.assertIsNone(sun.lonspeed)
        self.assertIsNone(sun.latspeed)

    def test_profected_planets_have_real_position(self):
        p = self.natal.profected(years=42)
        sun = p.get(const.SUN)
        self.assertIsNotNone(sun.sign)
        self.assertGreaterEqual(sun.signlon, 0)
        self.assertLess(sun.signlon, 30)

    def test_profected_movement_is_none(self):
        """The original bug: is_retrograde() / movement returned the
        natal value. Now they return None for symbolic positions.
        """
        p = self.natal.profected(years=42)
        sun = p.get(const.SUN)
        self.assertIsNone(sun.movement)
        self.assertIsNone(sun.isRetrograde())

    def test_42_years_rotates_by_180(self):
        # 42 % 12 = 6 signs = 180°
        p = self.natal.profected(years=42)
        natal_sun_lon = self.natal.get(const.SUN).lon
        prof_sun_lon = p.get(const.SUN).lon
        diff = (prof_sun_lon - natal_sun_lon) % 360
        self.assertAlmostEqual(diff, 180.0, places=2)

    def test_zero_years_returns_natal_positions(self):
        p = self.natal.profected(years=0)
        natal_sun = self.natal.get(const.SUN)
        prof_sun = p.get(const.SUN)
        self.assertAlmostEqual(prof_sun.lon, natal_sun.lon, places=5)

    def test_requires_exactly_one_arg(self):
        with self.assertRaises(ValueError):
            self.natal.profected()
        with self.assertRaises(ValueError):
            self.natal.profected(
                years=42,
                target_date=Datetime("2022/06/15", "12:00", "+00:00"),
            )

    def test_natal_unchanged_after_profected(self):
        """Building a profected chart must not mutate the natal."""
        natal_sun_lon = self.natal.get(const.SUN).lon
        natal_sun_speed = self.natal.get(const.SUN).lonspeed
        self.natal.profected(years=42)
        self.assertEqual(self.natal.get(const.SUN).lon, natal_sun_lon)
        self.assertEqual(self.natal.get(const.SUN).lonspeed, natal_sun_speed)

    def test_profected_houses_rotate(self):
        p = self.natal.profected(years=12)
        # 12 % 12 = 0 → no rotation
        natal_h1 = self.natal.getHouse(const.HOUSE1).lon
        prof_h1 = p.getHouse(const.HOUSE1).lon
        self.assertAlmostEqual(prof_h1, natal_h1, places=5)

        p3 = self.natal.profected(years=3)
        # 3 × 30 = 90°
        prof_h1_3 = p3.getHouse(const.HOUSE1).lon
        diff = (prof_h1_3 - natal_h1) % 360
        self.assertAlmostEqual(diff, 90.0, places=2)

    def test_profected_repr_shows_symbolic_kind(self):
        p = self.natal.profected(years=42)
        self.assertIn("profection", repr(p))


class ProfectedTargetDateTests(unittest.TestCase):
    def setUp(self):
        self.natal = _natal()
        self.target = Datetime("2022/06/15", "12:00", "+00:00")

    def test_target_date_returns_symbolic_chart(self):
        p = self.natal.profected(target_date=self.target)
        self.assertTrue(p.is_symbolic)
        self.assertEqual(p.symbolic_kind, "profection")

    def test_target_date_matches_legacy_compute_longitudes(self):
        """Pins the longitudes the pre-1.0 ``profections.compute()`` produced.

        The two paths were verified byte-identical (delta 0.0) against the
        legacy implementation immediately before it was deleted in Task
        v1.0-02; these literals were captured from that run. They keep the
        profection math itself under regression test now that there is no
        second implementation to compare against.
        """
        new = self.natal.profected(target_date=self.target)
        legacy_longitudes = [
            (const.SUN, 264.5077101262),
            (const.MOON, 297.6290048171),
            (const.MARS, 346.7533196812),
            (const.JUPITER, 333.7673974701),
        ]
        for pid, expected in legacy_longitudes:
            self.assertAlmostEqual(
                new.get(pid).lon,
                expected,
                places=4,
                msg=f"{pid} longitude drifted from the pre-1.0 profection math",
            )


if __name__ == "__main__":
    unittest.main()

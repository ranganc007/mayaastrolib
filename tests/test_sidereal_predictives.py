"""Tests for zodiac-aware predictives under sidereal mode — Task 027."""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos


class SiderealSolarReturnTests(unittest.TestCase):
    def setUp(self):
        self.date = Datetime("1980/06/15", "14:30", "+05:30")
        self.pos = GeoPos("28n36", "77e12")
        self.sid = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)

    def test_sr_chart_inherits_zodiac_and_ayanamsa(self):
        sr = self.sid.solarReturn(year=2024)
        self.assertEqual(sr.zodiac, const.ZODIAC_SIDEREAL)
        self.assertEqual(sr.ayanamsa, const.AYANAMSA_LAHIRI)

    def test_sr_sun_returns_to_natal_sidereal_sun(self):
        natal_sun = self.sid.getObject(const.SUN).lon % 360.0
        sr = self.sid.solarReturn(year=2024)
        sr_sun = sr.getObject(const.SUN).lon % 360.0
        diff = min(abs(sr_sun - natal_sun), 360.0 - abs(sr_sun - natal_sun))
        self.assertLess(diff, 0.001)

    def test_sr_by_year_and_by_target_date_agree(self):
        sr_year = self.sid.solarReturn(year=2024)
        # target_date at the start of 2024 should walk to the same SR.
        sr_td = self.sid.solarReturn(target_date=Datetime("2024/01/01", "00:00", "+05:30"))
        self.assertAlmostEqual(sr_year.date.jd, sr_td.date.jd, places=4)

    def test_birth_year_sr_is_near_birth(self):
        sr = self.sid.solarReturn(year=1980)
        self.assertLess(abs(sr.date.jd - self.date.jd), 1.5)

    def test_consecutive_years_differ_by_one_year(self):
        sr1 = self.sid.solarReturn(year=2024)
        sr2 = self.sid.solarReturn(year=2025)
        self.assertAlmostEqual(sr2.date.jd - sr1.date.jd, 365.25, delta=1.5)


class TropicalSolarReturnUnchangedTests(unittest.TestCase):
    def test_tropical_sr_still_works_and_stays_tropical(self):
        date = Datetime("1980/06/15", "14:30", "+05:30")
        pos = GeoPos("28n36", "77e12")
        trop = Chart(date, pos)
        sr = trop.solarReturn(year=2024)
        self.assertEqual(sr.zodiac, const.ZODIAC_TROPICAL)
        # SR Sun returns to the natal tropical Sun.
        diff = min(
            abs(sr.getObject(const.SUN).lon - trop.getObject(const.SUN).lon),
            360.0 - abs(sr.getObject(const.SUN).lon - trop.getObject(const.SUN).lon),
        )
        self.assertLess(diff, 0.001)


class SiderealProfectionTests(unittest.TestCase):
    def setUp(self):
        self.date = Datetime("1980/06/15", "14:30", "+05:30")
        self.pos = GeoPos("28n36", "77e12")
        self.sid = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)

    def test_profected_by_years_preserves_zodiac(self):
        prof = self.sid.profected(years=5)
        self.assertEqual(prof.zodiac, const.ZODIAC_SIDEREAL)
        self.assertTrue(prof.is_symbolic)
        self.assertEqual(prof.symbolic_kind, "profection")

    def test_profected_by_years_rotates_30_per_year(self):
        prof = self.sid.profected(years=1)
        natal_sun = self.sid.getObject(const.SUN).lon
        prof_sun = prof.getObject(const.SUN).lon
        diff = (prof_sun - natal_sun) % 360.0
        self.assertAlmostEqual(diff, 30.0, places=4)

    def test_profected_by_target_date_preserves_zodiac(self):
        prof = self.sid.profected(target_date=Datetime("2024/06/20", "00:00", "+05:30"))
        self.assertEqual(prof.zodiac, const.ZODIAC_SIDEREAL)
        self.assertTrue(prof.is_symbolic)


class SiderealDirectionsRejectedTests(unittest.TestCase):
    def test_directions_raises_on_sidereal_chart(self):
        date = Datetime("1980/06/15", "14:30", "+05:30")
        pos = GeoPos("28n36", "77e12")
        sid = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        with self.assertRaises(NotImplementedError):
            sid.directions()

    def test_directions_still_works_on_tropical_chart(self):
        date = Datetime("1980/06/15", "14:30", "+05:30")
        pos = GeoPos("28n36", "77e12")
        trop = Chart(date, pos)
        from mayaastrolib.predictives.primarydirections import PrimaryDirections

        self.assertIsInstance(trop.directions(), PrimaryDirections)


if __name__ == "__main__":
    unittest.main()

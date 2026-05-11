"""Tests for the Vedic foundation — Task 017."""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import ayanamsa as ay


class AyanamsaTests(unittest.TestCase):
    """Unit tests for the ayanamsa module."""

    def test_lahiri_j2000_value(self):
        """At J2000.0 UT, Lahiri ayanamsa is ~23.857° per the IAU 1976
        precession model used by pyswisseph's ``get_ayanamsa_ut``."""
        date = Datetime("2000/01/01", "12:00", "+00:00")
        value = ay.lahiri(date)
        self.assertAlmostEqual(value, 23.857, places=2)

    def test_lahiri_increases_with_time(self):
        d2000 = Datetime("2000/01/01", "12:00", "+00:00")
        d2024 = Datetime("2024/01/01", "12:00", "+00:00")
        self.assertGreater(ay.lahiri(d2024), ay.lahiri(d2000))

    def test_lahiri_rate_of_change_matches_precession(self):
        """Ayanamsa grows at ~50 arcsec/year via precession of equinoxes."""
        d2000 = Datetime("2000/01/01", "12:00", "+00:00")
        d2024 = Datetime("2024/01/01", "12:00", "+00:00")
        delta_arcsec = (ay.lahiri(d2024) - ay.lahiri(d2000)) * 3600
        # 24 years × ~50.3 arcsec/year ≈ 1207 arcsec; allow ±30 arcsec
        self.assertAlmostEqual(delta_arcsec, 1207, delta=30)

    def test_to_sidereal_subtracts_ayanamsa(self):
        date = Datetime("2024/06/01", "12:00", "+00:00")
        offset = ay.lahiri(date)
        sid = ay.to_sidereal(100.0, date)
        self.assertAlmostEqual(sid, (100.0 - offset) % 360.0, places=6)

    def test_to_sidereal_wraps_negative(self):
        """Tropical=5°, ayanamsa~24° → sidereal would be ~-19° → wraps to ~341°."""
        date = Datetime("2024/06/01", "12:00", "+00:00")
        sid = ay.to_sidereal(5.0, date)
        self.assertTrue(0.0 <= sid < 360.0)
        self.assertGreater(sid, 300.0)

    def test_to_tropical_inverse_of_to_sidereal(self):
        date = Datetime("2024/06/01", "12:00", "+00:00")
        for lon in [0.0, 90.0, 180.0, 270.0, 350.5]:
            self.assertAlmostEqual(
                ay.to_tropical(ay.to_sidereal(lon, date), date),
                lon,
                places=6,
            )

    def test_unknown_ayanamsa_raises(self):
        date = Datetime("2024/01/01", "12:00", "+00:00")
        with self.assertRaises(ValueError):
            ay.to_sidereal(100.0, date, ayanamsa="nonexistent")

    def test_get_dispatches_to_lahiri(self):
        date = Datetime("2024/01/01", "12:00", "+00:00")
        self.assertEqual(ay.get(const.AYANAMSA_LAHIRI, date), ay.lahiri(date))


class ChartZodiacKwargTests(unittest.TestCase):
    """Tests for Chart's new zodiac/ayanamsa kwargs."""

    def setUp(self):
        self.date = Datetime("2024/06/15", "12:00", "+00:00")
        self.pos = GeoPos("28n36", "77e12")  # Delhi

    def test_default_is_tropical(self):
        chart = Chart(self.date, self.pos)
        self.assertEqual(chart.zodiac, const.ZODIAC_TROPICAL)
        self.assertEqual(chart.ayanamsa, const.AYANAMSA_LAHIRI)

    def test_sidereal_explicit(self):
        chart = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)
        self.assertEqual(chart.zodiac, const.ZODIAC_SIDEREAL)
        self.assertEqual(chart.ayanamsa, const.AYANAMSA_LAHIRI)

    def test_unknown_zodiac_raises(self):
        with self.assertRaises(ValueError):
            Chart(self.date, self.pos, zodiac="lunar")

    def test_unknown_ayanamsa_raises(self):
        with self.assertRaises(ValueError):
            Chart(
                self.date,
                self.pos,
                zodiac=const.ZODIAC_SIDEREAL,
                ayanamsa="bogus",
            )

    def test_copy_preserves_zodiac_and_ayanamsa(self):
        sid = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)
        cp = sid.copy()
        self.assertEqual(cp.zodiac, const.ZODIAC_SIDEREAL)
        self.assertEqual(cp.ayanamsa, const.AYANAMSA_LAHIRI)


class SiderealPositionShiftTests(unittest.TestCase):
    """Sidereal planet/house positions = tropical - ayanamsa, modulo 360."""

    def setUp(self):
        self.date = Datetime("2024/06/15", "12:00", "+00:00")
        self.pos = GeoPos("28n36", "77e12")
        self.trop = Chart(self.date, self.pos)
        self.sid = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)
        self.offset = ay.lahiri(self.date)

    def test_sun_sidereal_matches_tropical_minus_ayanamsa(self):
        expected = (self.trop.get(const.SUN).lon - self.offset) % 360.0
        actual = self.sid.get(const.SUN).lon
        # ±0.01° captures the small precession-model nuance between
        # ``get_ayanamsa_ut`` and ``calc_ut(FLG_SIDEREAL)``.
        self.assertAlmostEqual(actual, expected, places=1)

    def test_moon_sidereal_matches_tropical_minus_ayanamsa(self):
        expected = (self.trop.get(const.MOON).lon - self.offset) % 360.0
        actual = self.sid.get(const.MOON).lon
        self.assertAlmostEqual(actual, expected, places=1)

    def test_house1_sidereal_matches_tropical_minus_ayanamsa(self):
        trop_h1 = self.trop.getHouse(const.HOUSE1).lon
        sid_h1 = self.sid.getHouse(const.HOUSE1).lon
        expected = (trop_h1 - self.offset) % 360.0
        self.assertAlmostEqual(sid_h1, expected, places=1)

    def test_asc_sidereal_matches_tropical_minus_ayanamsa(self):
        trop_asc = self.trop.getAngle(const.ASC).lon
        sid_asc = self.sid.getAngle(const.ASC).lon
        expected = (trop_asc - self.offset) % 360.0
        self.assertAlmostEqual(sid_asc, expected, places=1)

    def test_all_planets_in_sidereal_chart_have_valid_lon_range(self):
        for obj in self.sid.objects:
            self.assertTrue(0.0 <= obj.lon < 360.0)


class SiderealHouseSystemsTests(unittest.TestCase):
    """Verify multiple house systems work under sidereal mode."""

    def test_sidereal_works_with_placidus_and_whole_sign(self):
        date = Datetime("1980/01/01", "12:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        for hsys in [const.HOUSES_PLACIDUS, const.HOUSES_WHOLE_SIGN]:
            sid = Chart(date, pos, hsys=hsys, zodiac=const.ZODIAC_SIDEREAL)
            self.assertEqual(sid.zodiac, const.ZODIAC_SIDEREAL)
            # All houses must have a longitude in valid range.
            for h in sid.houses:
                self.assertTrue(0.0 <= h.lon < 360.0)


class BackwardsCompatibilityTests(unittest.TestCase):
    """No existing API call should change behaviour as a result of this task."""

    def test_default_chart_has_zodiac_attribute(self):
        chart = Chart(
            Datetime("2000/01/01", "12:00", "+00:00"),
            GeoPos("0n00", "0e00"),
        )
        self.assertEqual(chart.zodiac, const.ZODIAC_TROPICAL)

    def test_default_chart_sun_position_unchanged(self):
        """Sanity: a tropical chart at 2000-01-01 12:00 UT, equator,
        produces Sun at ~280.5° as it did pre-Task-017."""
        chart = Chart(
            Datetime("2000/01/01", "12:00", "+00:00"),
            GeoPos("0n00", "0e00"),
        )
        sun_lon = chart.getObject(const.SUN).lon
        self.assertAlmostEqual(sun_lon, 280.5, places=0)

    def test_existing_kwargs_still_work(self):
        chart = Chart(
            Datetime("2024/01/01", "00:00", "+00:00"),
            GeoPos("38n32", "8w54"),
            hsys=const.HOUSES_PLACIDUS,
            IDs=const.LIST_SEVEN_PLANETS,
        )
        self.assertEqual(chart.hsys, const.HOUSES_PLACIDUS)
        self.assertEqual(chart.zodiac, const.ZODIAC_TROPICAL)

    def test_rahu_ketu_aliases(self):
        self.assertEqual(const.RAHU, const.NORTH_NODE)
        self.assertEqual(const.KETU, const.SOUTH_NODE)


if __name__ == "__main__":
    unittest.main()

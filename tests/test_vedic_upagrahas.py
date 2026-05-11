"""Tests for Vedic Upagrahas — Task 023."""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import upagrahas as up


class SunDerivedFormulaTests(unittest.TestCase):
    """School B (Phaladeepika) Sun-longitude-derived points."""

    def test_dhuma_is_sun_plus_133_20(self):
        d = up.sun_derived_upagrahas(100.0)
        self.assertAlmostEqual(d[up.DHUMA], (100.0 + 133.0 + 20.0 / 60.0) % 360.0, places=6)

    def test_vyatipata_plus_dhuma_is_360(self):
        d = up.sun_derived_upagrahas(100.0)
        self.assertAlmostEqual((d[up.DHUMA] + d[up.VYATIPATA]) % 360.0, 0.0, places=6)

    def test_parivesha_is_vyatipata_plus_180(self):
        d = up.sun_derived_upagrahas(217.5)
        self.assertAlmostEqual(d[up.PARIVESHA], (d[up.VYATIPATA] + 180.0) % 360.0, places=6)

    def test_indrachapa_plus_parivesha_is_360(self):
        d = up.sun_derived_upagrahas(217.5)
        self.assertAlmostEqual((d[up.INDRACHAPA] + d[up.PARIVESHA]) % 360.0, 0.0, places=6)

    def test_upaketu_is_chapa_plus_16_40(self):
        d = up.sun_derived_upagrahas(42.0)
        self.assertAlmostEqual(
            d[up.UPAKETU], (d[up.INDRACHAPA] + 16.0 + 40.0 / 60.0) % 360.0, places=6
        )

    def test_all_in_range(self):
        for sun_lon in [0.0, 90.0, 180.0, 270.0, 355.5]:
            for v in up.sun_derived_upagrahas(sun_lon).values():
                self.assertTrue(0.0 <= v < 360.0)

    def test_five_points(self):
        self.assertEqual(len(up.sun_derived_upagrahas(0.0)), 5)


class GulikaTests(unittest.TestCase):
    """School A weekday-portion ascendant method."""

    def setUp(self):
        self.pos = GeoPos("28n36", "77e12")  # Delhi

    def test_gulika_returns_valid_longitude(self):
        chart = Chart(
            Datetime("2024/06/15", "12:00", "+05:30"), self.pos, zodiac=const.ZODIAC_SIDEREAL
        )
        g = up.gulika_longitude(chart)
        self.assertTrue(0.0 <= g < 360.0)

    def test_gulika_differs_day_vs_night(self):
        day_chart = Chart(
            Datetime("2024/06/15", "12:00", "+05:30"), self.pos, zodiac=const.ZODIAC_SIDEREAL
        )
        night_chart = Chart(
            Datetime("2024/06/15", "02:00", "+05:30"), self.pos, zodiac=const.ZODIAC_SIDEREAL
        )
        g_day = up.gulika_longitude(day_chart)
        g_night = up.gulika_longitude(night_chart)
        self.assertGreater(abs(g_day - g_night), 1.0)

    def test_saturday_day_gulika_is_ascendant_near_sunrise(self):
        # 2024-06-15 is a Saturday → day-lord Saturn rules the 1st daytime
        # part → Gulika's longitude ≈ the sidereal ascendant at sunrise.
        from mayaastrolib.ephem import ephem as _ephem
        from mayaastrolib.ephem import swe as _swe

        date = Datetime("2024/06/15", "12:00", "+05:30")
        chart = Chart(date, self.pos, zodiac=const.ZODIAC_SIDEREAL)
        sunrise = _ephem.lastSunrise(date, self.pos)
        _h, angles = _swe.sweHousesLon(
            sunrise.jd,
            self.pos.lat,
            self.pos.lon,
            const.HOUSES_DEFAULT,
            zodiac=const.ZODIAC_SIDEREAL,
            ayanamsa=const.AYANAMSA_LAHIRI,
        )
        self.assertAlmostEqual(up.gulika_longitude(chart), angles[0] % 360.0, places=4)


class UpagrahasEntryPointTests(unittest.TestCase):
    def setUp(self):
        self.pos = GeoPos("28n36", "77e12")
        self.date = Datetime("1947/08/15", "00:00", "+05:30")

    def test_school_b_returns_five(self):
        chart = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)
        result = up.upagrahas(chart, school="B")
        self.assertEqual(
            set(result.keys()),
            {up.DHUMA, up.VYATIPATA, up.PARIVESHA, up.INDRACHAPA, up.UPAKETU},
        )

    def test_school_a_includes_gulika(self):
        chart = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)
        result = up.upagrahas(chart, school="A")
        self.assertIn(up.GULIKA, result)
        self.assertEqual(len(result), 6)

    def test_default_school_is_b(self):
        chart = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)
        self.assertNotIn(up.GULIKA, up.upagrahas(chart))

    def test_unknown_school_raises(self):
        chart = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)
        with self.assertRaises(ValueError):
            up.upagrahas(chart, school="C")

    def test_result_sign_consistent_with_longitude(self):
        chart = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)
        for r in up.upagrahas(chart, school="A").values():
            sign_idx = int(r.sidereal_longitude // 30.0)
            self.assertEqual(r.sign, const.LIST_SIGNS[sign_idx])
            self.assertAlmostEqual(r.deg_in_sign, r.sidereal_longitude - sign_idx * 30.0, places=6)

    def test_tropical_and_sidereal_chart_agree_on_sun_derived(self):
        tropical = Chart(self.date, self.pos)
        sidereal = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)
        rt = up.upagrahas(tropical, school="B")
        rs = up.upagrahas(sidereal, school="B")
        for name in (up.DHUMA, up.VYATIPATA, up.PARIVESHA, up.INDRACHAPA, up.UPAKETU):
            self.assertAlmostEqual(
                rt[name].sidereal_longitude, rs[name].sidereal_longitude, places=2
            )


class FrozenDataclassTests(unittest.TestCase):
    def test_result_is_frozen(self):
        r = up._make_result(up.DHUMA, 100.0)
        with self.assertRaises(AttributeError):
            r.name = "Other"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()

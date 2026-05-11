"""Tests for KP sub-sub-lord, horary, and Ruling Planets — Task 030."""

import unittest

from mayaastrolib import const
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import kp


class SubSubLordTests(unittest.TestCase):
    def test_zero_degrees_is_ketu_all_the_way_down(self):
        # Ashwini's lord is Ketu; its first sub is Ketu's; that sub's
        # first sub-sub is Ketu's. So at 0.0° the whole chain is Ketu.
        self.assertEqual(kp.sub_sub_lord_at(0.0), const.KETU)

    def test_with_sub_sub_adds_the_key(self):
        chain = kp.sub_lord_at(45.7, with_sub_sub=True)
        self.assertIn("sub_sub_lord", chain)
        # Without the flag the key is absent.
        self.assertNotIn("sub_sub_lord", kp.sub_lord_at(45.7))

    def test_sub_sub_is_a_planet(self):
        valid = set(kp.SIGN_LORDS) | {const.RAHU, const.KETU}
        for lon in [0.0, 12.3, 50.0, 123.45, 200.0, 333.33]:
            self.assertIn(kp.sub_sub_lord_at(lon), valid)

    def test_sub_sub_changes_within_a_sub(self):
        # Within Ashwini's Ketu-sub (0° to 7/120 × 13°20' ≈ 0.778°), the
        # sub-sub starts at Ketu and changes as we move through the sub.
        self.assertEqual(kp.sub_sub_lord_at(0.01), const.KETU)
        # Somewhere later in the Ketu-sub the sub-sub-lord has changed.
        self.assertNotEqual(kp.sub_sub_lord_at(0.6), const.KETU)
        # And the sub-lord is still Ketu throughout (we're inside the Ketu sub).
        self.assertEqual(kp._sub_lord(0.6), const.KETU)

    def test_sub_lord_at_chain_consistent_with_helpers(self):
        for lon in [10.0, 100.0, 250.5]:
            chain = kp.sub_lord_at(lon, with_sub_sub=True)
            self.assertEqual(chain["sub_lord"], kp._sub_lord(lon))
            self.assertEqual(chain["sub_sub_lord"], kp.sub_sub_lord_at(lon))


class HoraryTests(unittest.TestCase):
    def test_prashna_to_longitude_midpoints(self):
        # Prashna N is the midpoint of the Nth (1-indexed) KP row.
        rows = kp.kp_table()
        for n in (1, 100, 249):
            row = rows[n - 1]
            start, end = row["start_lon"], row["end_lon"]
            if end <= start:
                end += 360.0
            expected = ((start + end) / 2.0) % 360.0
            self.assertAlmostEqual(kp.prashna_to_longitude(n), expected, places=9)

    def test_prashna_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            kp.prashna_to_longitude(0)
        with self.assertRaises(ValueError):
            kp.prashna_to_longitude(250)

    def test_kp_horary_shape(self):
        h = kp.kp_horary(150)
        self.assertEqual(h["prashna"], 150)
        self.assertAlmostEqual(h["lagna_longitude"], kp.prashna_to_longitude(150), places=9)
        self.assertIn("sub_lord", h["lagna"])
        self.assertIn("sub_sub_lord", h["lagna"])
        # The Lagna chain must be self-consistent with sub_lord_at.
        self.assertEqual(h["lagna"], kp.sub_lord_at(h["lagna_longitude"], with_sub_sub=True))


class RulingPlanetsTests(unittest.TestCase):
    def setUp(self):
        # 2024-06-15 is a Saturday → day-lord Saturn.
        self.date = Datetime("2024/06/15", "14:30", "+05:30")
        self.pos = GeoPos("28n36", "77e12")

    def test_keys(self):
        rp = kp.ruling_planets(self.date, self.pos)
        self.assertEqual(
            set(rp.keys()),
            {
                "day_lord",
                "moon_sign_lord",
                "moon_star_lord",
                "moon_sub_lord",
                "lagna_sign_lord",
                "lagna_star_lord",
                "lagna_sub_lord",
                "all",
            },
        )

    def test_saturday_day_lord_is_saturn(self):
        self.assertEqual(kp.ruling_planets(self.date, self.pos)["day_lord"], const.SATURN)

    def test_sunday_day_lord_is_sun(self):
        # 2024-06-16 is a Sunday.
        sunday = Datetime("2024/06/16", "12:00", "+05:30")
        self.assertEqual(kp.ruling_planets(sunday, self.pos)["day_lord"], const.SUN)

    def test_moon_and_lagna_chains_consistent(self):
        from mayaastrolib.chart import Chart

        rp = kp.ruling_planets(self.date, self.pos)
        chart = Chart(
            self.date,
            self.pos,
            zodiac=const.ZODIAC_SIDEREAL,
            ayanamsa=const.AYANAMSA_KRISHNAMURTI,
        )
        moon_chain = kp.sub_lord_at(chart.getObject(const.MOON).lon % 360.0)
        lagna_chain = kp.sub_lord_at(chart.getAngle(const.ASC).lon % 360.0)
        self.assertEqual(rp["moon_sign_lord"], moon_chain["sign_lord"])
        self.assertEqual(rp["moon_star_lord"], moon_chain["star_lord"])
        self.assertEqual(rp["moon_sub_lord"], moon_chain["sub_lord"])
        self.assertEqual(rp["lagna_sign_lord"], lagna_chain["sign_lord"])
        self.assertEqual(rp["lagna_star_lord"], lagna_chain["star_lord"])
        self.assertEqual(rp["lagna_sub_lord"], lagna_chain["sub_lord"])

    def test_all_is_the_distinct_set(self):
        rp = kp.ruling_planets(self.date, self.pos)
        keys = [k for k in rp if k != "all"]
        self.assertEqual(rp["all"], {rp[k] for k in keys})


if __name__ == "__main__":
    unittest.main()

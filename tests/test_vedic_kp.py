"""Tests for Vedic KP sub-lords — Task 025."""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import kp
from mayaastrolib.vedic import nakshatras as nak


class KPTableTests(unittest.TestCase):
    def test_table_has_249_rows(self):
        self.assertEqual(len(kp.kp_table()), 249)

    def test_rows_tile_360_degrees(self):
        total = 0.0
        for r in kp.kp_table():
            s, e = r["start_lon"], r["end_lon"]
            if e <= s:
                e += 360.0
            self.assertGreater(e - s, 0.0)
            total += e - s
        self.assertAlmostEqual(total, 360.0, places=6)

    def test_rows_are_contiguous(self):
        rows = kp.kp_table()
        for i in range(len(rows)):
            cur_end = rows[i]["end_lon"]
            nxt_start = rows[(i + 1) % len(rows)]["start_lon"]
            self.assertAlmostEqual(cur_end % 360.0, nxt_start % 360.0, places=6)

    def test_sign_lord_consistent_with_start(self):
        for r in kp.kp_table():
            # Use a point strictly inside the row to avoid boundary cases.
            s, e = r["start_lon"], r["end_lon"]
            if e <= s:
                e += 360.0
            mid = ((s + e) / 2.0) % 360.0
            expected = kp.SIGN_LORDS[int(mid // 30.0)]
            self.assertEqual(r["sign_lord"], expected)

    def test_every_row_sub_lord_is_a_planet(self):
        valid = set(kp.SIGN_LORDS) | {const.RAHU, const.KETU}
        for r in kp.kp_table():
            self.assertIn(r["sub_lord"], valid)


class SubLordAtTests(unittest.TestCase):
    def test_zero_degrees(self):
        chain = kp.sub_lord_at(0.0)
        self.assertEqual(chain["sign"], const.ARIES)
        self.assertEqual(chain["sign_lord"], const.MARS)
        self.assertEqual(chain["nakshatra"], "Ashwini")
        self.assertEqual(chain["star_lord"], const.KETU)
        self.assertEqual(chain["sub_lord"], const.KETU)
        self.assertEqual(chain["pada"], 1)

    def test_first_sub_of_ashwini_is_ketu(self):
        # Ketu's sub = 7/120 × 13°20' = 0.7778°.
        self.assertEqual(kp.sub_lord_at(0.5)["sub_lord"], const.KETU)

    def test_second_sub_of_ashwini_is_venus(self):
        # Ashwini's sub order: Ketu, Venus, Sun, … — 0.9° is past Ketu's 0.778°.
        self.assertEqual(kp.sub_lord_at(0.9)["sub_lord"], const.VENUS)

    def test_30_degree_boundary_bisects_a_sub(self):
        before = kp.sub_lord_at(29.9)
        after = kp.sub_lord_at(30.1)
        # Same sub-lord (one sub split by the sign boundary)…
        self.assertEqual(before["sub_lord"], after["sub_lord"])
        # …but different sign and sign-lord.
        self.assertNotEqual(before["sign"], after["sign"])
        self.assertNotEqual(before["sign_lord"], after["sign_lord"])

    def test_consistent_with_nakshatra_module(self):
        for lon in [12.0, 45.7, 123.4, 200.0, 333.3]:
            chain = kp.sub_lord_at(lon)
            n = nak.of_longitude(lon)
            self.assertEqual(chain["nakshatra"], n.name)
            self.assertEqual(chain["star_lord"], n.lord)
            self.assertEqual(chain["pada"], n.pada)

    def test_wraparound(self):
        self.assertEqual(kp.sub_lord_at(360.0)["sign"], const.ARIES)
        self.assertEqual(kp.sub_lord_at(-1.0)["sign"], const.PISCES)


class KPSublordsChartTests(unittest.TestCase):
    def setUp(self):
        self.date = Datetime("1947/08/15", "00:00", "+05:30")
        self.pos = GeoPos("28n36", "77e12")

    def test_returns_chains_for_7_planets_and_asc(self):
        chart = Chart(
            self.date,
            self.pos,
            zodiac=const.ZODIAC_SIDEREAL,
            ayanamsa=const.AYANAMSA_KRISHNAMURTI,
        )
        result = kp.kp_sublords(chart)
        expected = {
            const.SUN,
            const.MOON,
            const.MARS,
            const.MERCURY,
            const.JUPITER,
            const.VENUS,
            const.SATURN,
            const.ASC,
        }
        self.assertEqual(set(result.keys()), expected)
        for chain in result.values():
            self.assertIn("sub_lord", chain)
            self.assertIn("star_lord", chain)
            self.assertIn("sign_lord", chain)

    def test_tropical_chart_with_kp_ayanamsa_agrees_with_sidereal(self):
        tropical = Chart(self.date, self.pos)  # tropical
        sidereal = Chart(
            self.date,
            self.pos,
            zodiac=const.ZODIAC_SIDEREAL,
            ayanamsa=const.AYANAMSA_KRISHNAMURTI,
        )
        rt = kp.kp_sublords(tropical, ayanamsa=const.AYANAMSA_KRISHNAMURTI)
        rs = kp.kp_sublords(sidereal)
        for body in (const.SUN, const.MOON, const.SATURN, const.ASC):
            self.assertEqual(rt[body]["sub_lord"], rs[body]["sub_lord"])
            self.assertEqual(rt[body]["star_lord"], rs[body]["star_lord"])
            self.assertEqual(rt[body]["sign"], rs[body]["sign"])

    def test_default_ayanamsa_is_krishnamurti(self):
        # Building a tropical chart and calling kp_sublords with no
        # ayanamsa arg should use the KP ayanamsa, not Lahiri.
        tropical = Chart(self.date, self.pos)
        with_default = kp.kp_sublords(tropical)
        with_kp = kp.kp_sublords(tropical, ayanamsa=const.AYANAMSA_KRISHNAMURTI)
        self.assertEqual(with_default[const.SUN]["sub_lord"], with_kp[const.SUN]["sub_lord"])


if __name__ == "__main__":
    unittest.main()

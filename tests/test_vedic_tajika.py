"""Tests for Vedic Tajika — varshapravesh + Mudda dasha (Task 024)."""

import unittest

import swisseph

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.ephem.tools import MAX_ERROR
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import nakshatras as nak
from mayaastrolib.vedic import tajika
from mayaastrolib.vedic.dasha import VIMSHOTTARI_ORDER, VIMSHOTTARI_YEARS


class SiderealSunReturnTests(unittest.TestCase):
    def test_converges_to_target(self):
        # Pick a start jd, find when the sidereal Sun is at, say, 100°.
        start = Datetime("2024/01/01", "00:00", "+00:00").jd
        jd = tajika.sidereal_sun_return_jd(start, 100.0)
        # Feed it back: sidereal Sun at that jd should be ~100°.
        swisseph.set_sid_mode(swisseph.SIDM_LAHIRI)
        sun_sid = swisseph.calc_ut(jd, 0, swisseph.FLG_SIDEREAL)[0][0] % 360.0
        diff = min(abs(sun_sid - 100.0), 360.0 - abs(sun_sid - 100.0))
        self.assertLessEqual(diff, MAX_ERROR * 2)

    def test_returns_jd_at_or_after_start(self):
        start = Datetime("2024/06/01", "00:00", "+00:00").jd
        jd = tajika.sidereal_sun_return_jd(start, 250.0)
        self.assertGreaterEqual(jd, start)


class VarshapraveshTests(unittest.TestCase):
    def setUp(self):
        self.date = Datetime("1980/06/15", "14:30", "+05:30")
        self.pos = GeoPos("28n36", "77e12")
        self.natal = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)

    def test_birth_year_varshapravesh_is_near_birth(self):
        # The natal Sun is at its natal position at birth, by definition,
        # so the varshapravesh of the birth year ≈ the birth moment.
        vp = tajika.varshapravesh(self.natal, 1980)
        self.assertLess(abs(vp.jd - self.date.jd), 1.0)

    def test_consecutive_years_differ_by_one_year(self):
        vp_2024 = tajika.varshapravesh(self.natal, 2024)
        vp_2025 = tajika.varshapravesh(self.natal, 2025)
        self.assertAlmostEqual(vp_2025.jd - vp_2024.jd, 365.25, delta=1.0)

    def test_sun_at_varshapravesh_equals_natal_sidereal_sun(self):
        natal_sid_sun = self.natal.getObject(const.SUN).lon % 360.0
        vp = tajika.varshapravesh(self.natal, 2024)
        swisseph.set_sid_mode(swisseph.SIDM_LAHIRI)
        sun_at_vp = swisseph.calc_ut(vp.jd, 0, swisseph.FLG_SIDEREAL)[0][0] % 360.0
        diff = min(abs(sun_at_vp - natal_sid_sun), 360.0 - abs(sun_at_vp - natal_sid_sun))
        self.assertLess(diff, 0.001)

    def test_works_from_tropical_natal_chart(self):
        tropical_natal = Chart(self.date, self.pos)  # tropical
        vp_from_tropical = tajika.varshapravesh(tropical_natal, 2024)
        vp_from_sidereal = tajika.varshapravesh(self.natal, 2024)
        # Should agree closely (within a day — the ~0.004° precession-model
        # gap between get_ayanamsa_ut and calc_ut(FLG_SIDEREAL) scales to
        # a small fraction of a day at the Sun's ~1°/day motion).
        self.assertLess(abs(vp_from_tropical.jd - vp_from_sidereal.jd), 1.0)


class MuddaDashaTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("1980/06/15", "14:30", "+05:30")
        pos = GeoPos("28n36", "77e12")
        natal = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        self.vp = tajika.varshapravesh(natal, 2024)
        self.md = tajika.mudda_dasha(self.vp)

    def test_nine_periods(self):
        self.assertEqual(len(self.md), 9)

    def test_durations_sum_to_one_year(self):
        total = sum(p.end.jd - p.start.jd for p in self.md)
        self.assertAlmostEqual(total, tajika.TAJIKA_YEAR_DAYS, delta=0.01)

    def test_first_period_starts_at_varshapravesh(self):
        self.assertAlmostEqual(self.md[0].start.jd, self.vp.jd, places=6)

    def test_first_lord_matches_vp_moon_nakshatra_lord(self):
        swisseph.set_sid_mode(swisseph.SIDM_LAHIRI)
        moon_sid = swisseph.calc_ut(self.vp.jd, 1, swisseph.FLG_SIDEREAL)[0][0] % 360.0
        expected_lord = nak.of_longitude(moon_sid).lord
        self.assertEqual(self.md[0].lord, expected_lord)

    def test_lords_follow_vimshottari_cycle(self):
        start_idx = VIMSHOTTARI_ORDER.index(self.md[0].lord)
        for i, period in enumerate(self.md):
            self.assertEqual(period.lord, VIMSHOTTARI_ORDER[(start_idx + i) % 9])

    def test_period_durations_match_proportions(self):
        for period in self.md:
            days = period.end.jd - period.start.jd
            expected = (VIMSHOTTARI_YEARS[period.lord] / 120.0) * tajika.TAJIKA_YEAR_DAYS
            self.assertAlmostEqual(days, expected, delta=0.01)

    def test_periods_are_chronological_and_contiguous(self):
        for i in range(len(self.md) - 1):
            self.assertAlmostEqual(self.md[i].end.jd, self.md[i + 1].start.jd, places=6)


if __name__ == "__main__":
    unittest.main()


class SahamTableIntegrityTests(unittest.TestCase):
    """Guards for the Saham table itself (Task v1.0-07b).

    The table is the place a mis-remembered classical formula would land,
    and a wrong formula usually is not obviously wrong — it just quietly
    duplicates one already present. These make that visible.
    """

    def _sahams_for(self, date, pos, year):
        natal = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        annual = Chart(tajika.varshapravesh(natal, year), pos, zodiac=const.ZODIAC_SIDEREAL)
        return tajika.sahams(annual)

    def test_every_formula_is_a_four_tuple(self):
        for name, formula in tajika._SAHAM_FORMULAS.items():
            with self.subTest(saham=name):
                self.assertEqual(len(formula), 4, f"{name}: expected (a, b, c, reversible)")

    def test_no_two_sahams_are_the_same_point(self):
        """Two Sahams landing on the same degree means the same formula twice.

        `a - b + c` is commutative in a and c, so distinct-looking entries
        can be algebraically identical. Checked on two charts — one diurnal,
        one nocturnal — because some collisions only show up in one, the
        day/night term swap hiding them in the other.
        """
        charts = [
            (Datetime("1990/06/15", "14:30", "+05:30"), GeoPos("28n36", "77e12"), 2020),
            (Datetime("1961/08/04", "19:24", "-10:00"), GeoPos("21n18", "157w51"), 2005),
        ]
        for date, pos, year in charts:
            sahams = self._sahams_for(date, pos, year)
            seen = {}
            for name, lon in sahams.items():
                key = round(lon, 6)
                with self.subTest(chart=str(date), saham=name):
                    self.assertNotIn(
                        key,
                        seen,
                        f"{name} lands on the same degree as {seen.get(key)} — "
                        f"the two formulas are algebraically identical",
                    )
                seen[key] = name

    def test_all_sahams_are_normalised(self):
        sahams = self._sahams_for(
            Datetime("1990/06/15", "14:30", "+05:30"), GeoPos("28n36", "77e12"), 2020
        )
        for name, lon in sahams.items():
            with self.subTest(saham=name):
                self.assertGreaterEqual(lon, 0.0)
                self.assertLess(lon, 360.0)

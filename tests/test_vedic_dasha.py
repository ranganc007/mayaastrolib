"""Tests for Vimshottari dasha — Task 020."""

import datetime as _stdlib_dt
import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import dasha
from mayaastrolib.vedic import nakshatras as nak


class BirthBalanceTests(unittest.TestCase):
    def test_moon_at_start_of_nakshatra_has_full_remaining(self):
        # Ashwini starts at 0°; Moon at 0° has the full Ketu MD ahead.
        ashwini = nak.of_longitude(0.0)
        lord, remaining = dasha._birth_balance(ashwini, 0.0)
        self.assertEqual(lord, const.KETU)
        self.assertAlmostEqual(remaining, 7.0, places=4)

    def test_moon_at_end_of_nakshatra_has_zero_remaining(self):
        # End of Ashwini = 13°20'.
        ashwini = nak.of_longitude(0.0)
        _, remaining = dasha._birth_balance(ashwini, 13.0 + 20.0 / 60.0)
        self.assertAlmostEqual(remaining, 0.0, places=2)

    def test_moon_at_midpoint_has_half_remaining(self):
        ashwini = nak.of_longitude(0.0)
        _, remaining = dasha._birth_balance(ashwini, (13.0 + 20.0 / 60.0) / 2.0)
        self.assertAlmostEqual(remaining, 3.5, places=2)


class VimshottariStructureTests(unittest.TestCase):
    def setUp(self):
        self.date = Datetime("1980/01/01", "12:00", "+05:30")
        self.pos = GeoPos("28n36", "77e12")
        self.chart = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)

    def test_sequence_length_covers_at_least_120_years(self):
        result = dasha.vimshottari(self.chart)
        first_start = result.sequence[0].start.to_pydatetime()
        last_end = result.sequence[-1].end.to_pydatetime()
        total_days = (last_end - first_start).total_seconds() / 86400.0
        # Should cover at least 120 years from the first MD's start.
        self.assertGreaterEqual(total_days, 120 * 365.25 - 1)

    def test_md_sequence_follows_vimshottari_order(self):
        result = dasha.vimshottari(self.chart)
        for i in range(len(result.sequence) - 1):
            lord_i = result.sequence[i].lord
            lord_next = result.sequence[i + 1].lord
            expected_next = dasha._next_lord(lord_i)
            self.assertEqual(lord_next, expected_next, f"MD {i} → {i + 1} broken")

    def test_md_durations_match_table(self):
        result = dasha.vimshottari(self.chart)
        # Skip the first (partial) and last (may be truncated). Middle MDs
        # should each be the full duration of their lord.
        for md in result.sequence[1:-1]:
            actual_days = (
                md.end.to_pydatetime() - md.start.to_pydatetime()
            ).total_seconds() / 86400.0
            expected_days = dasha.VIMSHOTTARI_YEARS[md.lord] * dasha.DAYS_PER_VIMSHOTTARI_YEAR
            self.assertAlmostEqual(actual_days, expected_days, delta=1.0)

    def test_first_md_starts_before_birth(self):
        """The first MD is a partial — it began before birth."""
        result = dasha.vimshottari(self.chart)
        first_md = result.sequence[0]
        self.assertLess(
            first_md.start.to_pydatetime(),
            self.date.to_pydatetime(),
        )
        # And ends after birth.
        self.assertGreaterEqual(
            first_md.end.to_pydatetime(),
            self.date.to_pydatetime(),
        )

    def test_first_md_lord_matches_natal_nakshatra_lord(self):
        result = dasha.vimshottari(self.chart)
        self.assertEqual(result.birth_balance_lord, result.janma_nakshatra.lord)
        self.assertEqual(result.sequence[0].lord, result.janma_nakshatra.lord)


class AntardashaTests(unittest.TestCase):
    def setUp(self):
        # Build a 20-year Venus MD starting at a known date for testing.
        start = Datetime("2000/01/01", "00:00", "+00:00")
        end_pydt = start.to_pydatetime() + _stdlib_dt.timedelta(
            days=20 * dasha.DAYS_PER_VIMSHOTTARI_YEAR
        )
        end = Datetime.from_pydatetime(end_pydt)
        self.venus_md = dasha.DashaPeriod(
            lord=const.VENUS,
            start=start,
            end=end,
            level=1,
        )

    def test_nine_antardashas(self):
        ads = dasha.antardashas(self.venus_md)
        self.assertEqual(len(ads), 9)

    def test_first_antardasha_is_md_lord(self):
        ads = dasha.antardashas(self.venus_md)
        self.assertEqual(ads[0].lord, const.VENUS)

    def test_antardasha_sequence(self):
        ads = dasha.antardashas(self.venus_md)
        expected_order = [
            const.VENUS,
            const.SUN,
            const.MOON,
            const.MARS,
            const.RAHU,
            const.JUPITER,
            const.SATURN,
            const.MERCURY,
            const.KETU,
        ]
        self.assertEqual([a.lord for a in ads], expected_order)

    def test_antardasha_durations_sum_to_md(self):
        ads = dasha.antardashas(self.venus_md)
        md_days = (
            self.venus_md.end.to_pydatetime() - self.venus_md.start.to_pydatetime()
        ).total_seconds() / 86400.0
        ad_days_total = sum(
            (a.end.to_pydatetime() - a.start.to_pydatetime()).total_seconds() / 86400.0 for a in ads
        )
        self.assertAlmostEqual(ad_days_total, md_days, delta=0.01)

    def test_venus_ad_within_venus_md_is_20_over_120_of_total(self):
        ads = dasha.antardashas(self.venus_md)
        venus_ad = ads[0]
        ad_days = (
            venus_ad.end.to_pydatetime() - venus_ad.start.to_pydatetime()
        ).total_seconds() / 86400.0
        expected_days = (20.0 / 120.0) * 20.0 * dasha.DAYS_PER_VIMSHOTTARI_YEAR
        self.assertAlmostEqual(ad_days, expected_days, delta=0.01)


class PratyantarTests(unittest.TestCase):
    def test_pratyantar_sums_to_antardasha(self):
        start = Datetime("2000/01/01", "00:00", "+00:00")
        end_pydt = start.to_pydatetime() + _stdlib_dt.timedelta(
            days=20 * dasha.DAYS_PER_VIMSHOTTARI_YEAR
        )
        end = Datetime.from_pydatetime(end_pydt)
        venus_md = dasha.DashaPeriod(
            lord=const.VENUS,
            start=start,
            end=end,
            level=1,
        )
        ads = dasha.antardashas(venus_md)
        sun_ad = ads[1]  # Sun AD within Venus MD
        prs = dasha.pratyantar_dashas(sun_ad)
        self.assertEqual(len(prs), 9)
        self.assertEqual(prs[0].lord, const.SUN)  # starts with AD lord
        ad_days = (
            sun_ad.end.to_pydatetime() - sun_ad.start.to_pydatetime()
        ).total_seconds() / 86400.0
        pr_total = sum(
            (p.end.to_pydatetime() - p.start.to_pydatetime()).total_seconds() / 86400.0 for p in prs
        )
        self.assertAlmostEqual(pr_total, ad_days, delta=0.01)


class CurrentPeriodTests(unittest.TestCase):
    def test_target_returns_active_md_ad_pratyantar(self):
        date = Datetime("1947/08/15", "00:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        target = Datetime("2024/06/01", "12:00", "+00:00")
        result = dasha.vimshottari(chart, target=target)
        self.assertIsNotNone(result.current_md)
        self.assertIsNotNone(result.current_ad)
        self.assertIsNotNone(result.current_pratyantar)

    def test_target_at_birth_returns_first_md(self):
        date = Datetime("1980/01/01", "12:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        result = dasha.vimshottari(chart, target=date)
        self.assertIsNotNone(result.current_md)
        self.assertEqual(result.current_md.lord, result.birth_balance_lord)


class TargetOutsideSequenceTests(unittest.TestCase):
    def test_target_before_first_md_returns_none(self):
        date = Datetime("1980/01/01", "12:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        result = dasha.vimshottari(chart, target=Datetime("1700/01/01", "00:00", "+00:00"))
        self.assertIsNone(result.current_md)

    def test_target_after_120_years_returns_none(self):
        date = Datetime("1980/01/01", "12:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        result = dasha.vimshottari(chart, target=Datetime("2300/01/01", "00:00", "+00:00"))
        self.assertIsNone(result.current_md)

    def test_no_target_returns_none_currents(self):
        date = Datetime("1980/01/01", "12:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        result = dasha.vimshottari(chart)
        self.assertIsNone(result.current_md)
        self.assertIsNone(result.current_ad)
        self.assertIsNone(result.current_pratyantar)


class TropicalChartAgreementTests(unittest.TestCase):
    def test_vimshottari_from_tropical_matches_sidereal(self):
        date = Datetime("1947/08/15", "00:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        tropical_chart = Chart(date, pos)
        sidereal_chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        rt = dasha.vimshottari(tropical_chart)
        rs = dasha.vimshottari(sidereal_chart)
        self.assertEqual(rt.birth_balance_lord, rs.birth_balance_lord)
        # ±0.01 year (~3.6 days) absorbs the small precession-model gap
        # between get_ayanamsa_ut (used by to_sidereal) and
        # calc_ut(FLG_SIDEREAL) (used by sidereal Chart construction).
        # This is the same ~0.004° gap documented in Task 017's
        # PROJECT-LOG entry; it scales to ~0.006 years here.
        self.assertAlmostEqual(rt.birth_balance_years, rs.birth_balance_years, delta=0.01)


if __name__ == "__main__":
    unittest.main()

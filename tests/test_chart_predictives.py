"""Tests for Chart-method predictives (Task 013).

Item 17 from the audit: predictives and tools were top-level
functions, not Chart methods. Task 010 partially addressed this
with `Chart.profected`. Task 013 adds method-style entry points for
the rest:

- `Chart.solarReturn(year=, target_date=)` (extended)
- `Chart.directions()` (new)
- `Chart.arabicPart(part_id)` (new)
- `Chart.planetaryHour(date=None)` (new)

Plus deprecation of `tools.arabicparts.getPart()`.
"""

import unittest
import warnings

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos


def _natal():
    date = Datetime("1980/06/15", "12:00", "+00:00")
    pos = GeoPos("51n30", "0w08")
    return Chart(date, pos)


def _sample_chart():
    date = Datetime("2015/03/13", "17:00", "+00:00")
    pos = GeoPos("38n32", "8w54")
    return Chart(date, pos)


class ChartSolarReturnTests(unittest.TestCase):
    def setUp(self):
        self.natal = _natal()

    def test_year_returns_chart(self):
        sr = self.natal.solarReturn(year=2022)
        self.assertIsInstance(sr, Chart)

    def test_year_positional_still_works(self):
        # Backwards compat: existing code that called solarReturn(2022)
        # positionally must keep working.
        sr = self.natal.solarReturn(2022)
        self.assertIsInstance(sr, Chart)

    def test_solar_return_is_not_symbolic(self):
        sr = self.natal.solarReturn(year=2022)
        self.assertFalse(sr.is_symbolic)
        self.assertIsNone(sr.symbolic_kind)

    def test_solar_return_planets_have_real_speed(self):
        # Real (ephemeris-derived) chart, not symbolic — speeds present.
        sr = self.natal.solarReturn(year=2022)
        self.assertIsNotNone(sr.get(const.SUN).lonspeed)

    def test_target_date_returns_chart(self):
        target = Datetime("2022/05/01", "00:00", "+00:00")
        sr = self.natal.solarReturn(target_date=target)
        self.assertIsInstance(sr, Chart)

    def test_target_date_finds_next_return_after_anchor(self):
        target = Datetime("2022/05/01", "00:00", "+00:00")
        sr = self.natal.solarReturn(target_date=target)
        # Birthday is June 15, anchor is May 1 of same year — SR should
        # land in mid-June 2022 (the 42nd birthday). Compare via JD so
        # we don't depend on Date's internal attribute layout.
        self.assertGreater(sr.date.jd, target.jd)
        # And it should be before May 1 of the next year (2023):
        next_year = Datetime("2023/05/01", "00:00", "+00:00")
        self.assertLess(sr.date.jd, next_year.jd)

    def test_year_and_target_date_raises(self):
        with self.assertRaises(ValueError):
            self.natal.solarReturn(
                year=2022,
                target_date=Datetime("2022/05/01", "00:00", "+00:00"),
            )

    def test_neither_arg_raises(self):
        with self.assertRaises(ValueError):
            self.natal.solarReturn()


class ChartDirectionsTests(unittest.TestCase):
    def setUp(self):
        self.natal = _natal()

    def test_directions_returns_primary_directions(self):
        from mayaastrolib.predictives.primarydirections import PrimaryDirections

        d = self.natal.directions()
        self.assertIsInstance(d, PrimaryDirections)

    def test_directions_uses_self_chart(self):
        d = self.natal.directions()
        self.assertIs(d.chart, self.natal)


class ChartArabicPartTests(unittest.TestCase):
    def setUp(self):
        self.chart = _sample_chart()

    def test_pars_fortuna_returns_object(self):
        from mayaastrolib.tools.arabicparts import PARS_FORTUNA

        part = self.chart.arabicPart(PARS_FORTUNA)
        self.assertIsNotNone(part)
        self.assertEqual(part.id, PARS_FORTUNA)
        self.assertEqual(part.type, const.OBJ_ARABIC_PART)

    def test_arabicPart_does_not_warn(self):
        from mayaastrolib.tools.arabicparts import PARS_FORTUNA

        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            self.chart.arabicPart(PARS_FORTUNA)
        # The chart-method path must not emit the deprecation warning.
        deprecations = [w for w in captured if issubclass(w.category, DeprecationWarning)]
        self.assertEqual(deprecations, [])

    def test_arabicPart_matches_legacy_getPart(self):
        from mayaastrolib.tools import arabicparts

        new_part = self.chart.arabicPart(arabicparts.PARS_FORTUNA)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            legacy_part = arabicparts.getPart(arabicparts.PARS_FORTUNA, self.chart)
        self.assertAlmostEqual(new_part.lon, legacy_part.lon, places=5)


class ChartPlanetaryHourTests(unittest.TestCase):
    def setUp(self):
        self.chart = _sample_chart()

    def test_planetary_hour_returns_table(self):
        from mayaastrolib.tools.planetarytime import HourTable

        ht = self.chart.planetaryHour()
        self.assertIsInstance(ht, HourTable)

    def test_planetary_hour_uses_chart_date_by_default(self):
        ht = self.chart.planetaryHour()
        # Default: ht.date should be the chart's date.
        self.assertEqual(ht.date.jd, self.chart.date.jd)

    def test_planetary_hour_accepts_date_override(self):
        target = Datetime("2015/03/14", "06:00", "+00:00")
        ht = self.chart.planetaryHour(date=target)
        self.assertEqual(ht.date.jd, target.jd)


class DeprecatedGetPartTests(unittest.TestCase):
    def setUp(self):
        self.chart = _sample_chart()

    def test_get_part_warns(self):
        from mayaastrolib.tools import arabicparts

        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            arabicparts.getPart(arabicparts.PARS_FORTUNA, self.chart)
        self.assertTrue(
            any(issubclass(w.category, DeprecationWarning) for w in captured),
            "tools.arabicparts.getPart should emit DeprecationWarning",
        )

    def test_get_part_still_returns_correct_part(self):
        from mayaastrolib.tools import arabicparts

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            part = arabicparts.getPart(arabicparts.PARS_FORTUNA, self.chart)
        self.assertEqual(part.id, arabicparts.PARS_FORTUNA)


if __name__ == "__main__":
    unittest.main()

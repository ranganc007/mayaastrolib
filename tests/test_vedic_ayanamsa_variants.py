"""Tests for the additional ayanamsa variants — Task 017b."""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import ayanamsa as ay


class AyanamsaVariantTests(unittest.TestCase):
    def setUp(self):
        self.date = Datetime("2000/01/01", "12:00", "+00:00")

    def test_all_four_in_list(self):
        self.assertEqual(
            set(const.LIST_AYANAMSAS),
            {
                const.AYANAMSA_LAHIRI,
                const.AYANAMSA_KRISHNAMURTI,
                const.AYANAMSA_RAMAN,
                const.AYANAMSA_FAGAN_BRADLEY,
            },
        )

    def test_lahiri_j2000(self):
        self.assertAlmostEqual(ay.lahiri(self.date), 23.857, places=2)

    def test_each_variant_returns_a_plausible_value(self):
        # All four should be in the 22°–25° range at J2000.0 (precession
        # since their respective epochs).
        for fn in (ay.lahiri, ay.krishnamurti, ay.raman, ay.fagan_bradley):
            v = fn(self.date)
            self.assertTrue(22.0 < v < 25.5, f"{fn.__name__}={v}")

    def test_variants_are_distinct(self):
        vals = {
            ay.lahiri(self.date),
            ay.krishnamurti(self.date),
            ay.raman(self.date),
            ay.fagan_bradley(self.date),
        }
        self.assertEqual(len(vals), 4)

    def test_get_dispatches(self):
        self.assertEqual(ay.get(const.AYANAMSA_RAMAN, self.date), ay.raman(self.date))
        self.assertEqual(ay.get(const.AYANAMSA_KRISHNAMURTI, self.date), ay.krishnamurti(self.date))

    def test_unknown_ayanamsa_raises(self):
        with self.assertRaises(ValueError):
            ay.get("yukteshwar", self.date)

    def test_to_sidereal_with_each_variant(self):
        for variant in const.LIST_AYANAMSAS:
            offset = ay.get(variant, self.date)
            self.assertAlmostEqual(
                ay.to_sidereal(100.0, self.date, ayanamsa=variant),
                (100.0 - offset) % 360.0,
                places=6,
            )


class ChartWithVariantAyanamsaTests(unittest.TestCase):
    def setUp(self):
        self.date = Datetime("2000/01/01", "12:00", "+00:00")
        self.pos = GeoPos("28n36", "77e12")

    def test_chart_accepts_each_variant(self):
        for variant in const.LIST_AYANAMSAS:
            chart = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL, ayanamsa=variant)
            self.assertEqual(chart.ayanamsa, variant)
            self.assertTrue(0.0 <= chart.getObject(const.SUN).lon < 360.0)

    def test_different_variants_give_different_sun_positions(self):
        suns = set()
        for variant in const.LIST_AYANAMSAS:
            chart = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL, ayanamsa=variant)
            suns.add(round(chart.getObject(const.SUN).lon, 3))
        self.assertEqual(len(suns), 4)

    def test_sun_shift_matches_ayanamsa(self):
        tropical = Chart(self.date, self.pos)
        for variant in const.LIST_AYANAMSAS:
            sidereal = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL, ayanamsa=variant)
            offset = ay.get(variant, self.date)
            expected = (tropical.getObject(const.SUN).lon - offset) % 360.0
            self.assertAlmostEqual(sidereal.getObject(const.SUN).lon, expected, places=1)

    def test_unknown_ayanamsa_in_chart_raises(self):
        with self.assertRaises(ValueError):
            Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL, ayanamsa="bogus")


if __name__ == "__main__":
    unittest.main()

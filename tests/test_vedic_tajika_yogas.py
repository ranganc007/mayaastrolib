"""Tests for the higher-order Tajika yogas — Kamboola, Gairi-Kamboola,
Khallasara (Task 042)."""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import tajika, tajika_aspects


class _AnnualBase(unittest.TestCase):
    def setUp(self):
        self.date = Datetime("1980/06/15", "14:30", "+05:30")
        self.pos = GeoPos("28n36", "77e12")
        self.natal = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)
        self.vp = tajika.varshapravesh(self.natal, 2024)
        self.annual = Chart(self.vp, self.pos, zodiac=const.ZODIAC_SIDEREAL)


class TajikaYogasStructureTests(_AnnualBase):
    def test_returns_expected_keys(self):
        y = tajika_aspects.tajika_yogas(self.annual)
        for key in (
            tajika_aspects.KAMBOOLA,
            "kamboola_aspects",
            tajika_aspects.GAIRI_KAMBOOLA,
            "gairi_kamboola_aspects",
            tajika_aspects.KHALLASARA,
        ):
            self.assertIn(key, y)

    def test_flags_are_bool(self):
        y = tajika_aspects.tajika_yogas(self.annual)
        for key in (
            tajika_aspects.KAMBOOLA,
            tajika_aspects.GAIRI_KAMBOOLA,
            tajika_aspects.KHALLASARA,
        ):
            self.assertIsInstance(y[key], bool)

    def test_kamboola_consistent_with_aspects(self):
        y = tajika_aspects.tajika_yogas(self.annual)
        # If Kamboola is reported, there must be a Moon Ithasala in the list,
        # and every such aspect must indeed involve the Moon and be Ithasala.
        self.assertEqual(y[tajika_aspects.KAMBOOLA], bool(y["kamboola_aspects"]))
        for a in y["kamboola_aspects"]:
            self.assertEqual(a.kind, tajika_aspects.ITHASALA)
            self.assertIn(const.MOON, a.planets)

    def test_khallasara_matches_absence_of_ithasala(self):
        aspects = tajika_aspects.tajika_aspects(self.annual)
        any_ithasala = any(a.kind == tajika_aspects.ITHASALA for a in aspects)
        y = tajika_aspects.tajika_yogas(self.annual)
        self.assertEqual(y[tajika_aspects.KHALLASARA], not any_ithasala)

    def test_kamboola_and_khallasara_mutually_exclusive(self):
        # Kamboola requires a Moon Ithasala; Khallasara requires no Ithasala
        # at all — they cannot both hold.
        y = tajika_aspects.tajika_yogas(self.annual)
        self.assertFalse(y[tajika_aspects.KAMBOOLA] and y[tajika_aspects.KHALLASARA])

    def test_gairi_kamboola_excluded_when_kamboola(self):
        y = tajika_aspects.tajika_yogas(self.annual)
        if y[tajika_aspects.KAMBOOLA]:
            self.assertFalse(y[tajika_aspects.GAIRI_KAMBOOLA])

    def test_raises_on_symbolic_chart(self):
        symbolic = self.natal.profected(years=5)
        with self.assertRaises(ValueError):
            tajika_aspects.tajika_yogas(symbolic)


if __name__ == "__main__":
    unittest.main()

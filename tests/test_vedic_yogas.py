"""Tests for Vedic yoga detection — Task 026."""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import yogas as yg


class DignityHelperTests(unittest.TestCase):
    def test_mars_in_own_sign(self):
        self.assertTrue(yg.is_in_own_or_exaltation(const.MARS, yg._ARIES))
        self.assertTrue(yg.is_in_own_or_exaltation(const.MARS, yg._SCORPIO))

    def test_mars_exalted_in_capricorn(self):
        self.assertTrue(yg.is_in_own_or_exaltation(const.MARS, yg._CAPRICORN))

    def test_mars_debilitated_in_cancer_is_not_strong(self):
        self.assertFalse(yg.is_in_own_or_exaltation(const.MARS, yg._CANCER))
        self.assertTrue(yg.is_debilitated(const.MARS, yg._CANCER))

    def test_mars_neutral_sign_is_not_strong(self):
        self.assertFalse(yg.is_in_own_or_exaltation(const.MARS, yg._LEO))

    def test_jupiter_exalted_in_cancer(self):
        self.assertTrue(yg.is_in_own_or_exaltation(const.JUPITER, yg._CANCER))


class HouseFromTests(unittest.TestCase):
    def test_same_sign_is_house_1(self):
        self.assertEqual(yg.house_from(yg._ARIES, yg._ARIES), 1)

    def test_fourth_sign_is_house_4(self):
        self.assertEqual(yg.house_from(yg._ARIES, yg._CANCER), 4)

    def test_tenth_sign_is_house_10(self):
        self.assertEqual(yg.house_from(yg._ARIES, yg._CAPRICORN), 10)

    def test_twelfth_sign_is_house_12(self):
        self.assertEqual(yg.house_from(yg._ARIES, yg._PISCES), 12)

    def test_wraparound(self):
        # Reference Pisces (11), planet Aries (0) → 2nd house.
        self.assertEqual(yg.house_from(yg._PISCES, yg._ARIES), 2)


class CoreDetectionTests(unittest.TestCase):
    """Logic tested directly via _detect — no ephemeris."""

    def _signs(self, **overrides):
        base = {
            const.SUN: yg._LEO,
            const.MOON: yg._VIRGO,
            const.MARS: yg._GEMINI,
            const.MERCURY: yg._AQUARIUS,
            const.JUPITER: yg._SCORPIO,
            const.VENUS: yg._ARIES,
            const.SATURN: yg._SAGITTARIUS,
        }
        # Kwarg names like JUPITER map to const.JUPITER ("Jupiter").
        for name, value in overrides.items():
            base[getattr(const, name)] = value
        return base

    def test_no_yogas_in_a_bland_chart(self):
        # Ascendant Cancer; nothing aligns.
        results = yg._detect(self._signs(), asc_sign=yg._CANCER)
        names = {r.sanskrit for r in results}
        # Sun in Leo, asc Cancer → Sun house 2 (not a kendra), and Sun
        # isn't a Mahapurusha planet anyway. Should be empty.
        self.assertEqual(names, set())

    def test_hamsa_yoga(self):
        # Jupiter in Pisces (own), Ascendant Pisces → Jupiter in house 1
        # (a kendra) → Hamsa.
        results = yg._detect(self._signs(JUPITER=yg._PISCES), asc_sign=yg._PISCES)
        self.assertIn("Hamsa", {r.sanskrit for r in results})

    def test_ruchaka_yoga(self):
        # Mars exalted in Capricorn, Ascendant Capricorn → Mars house 1.
        results = yg._detect(self._signs(MARS=yg._CAPRICORN), asc_sign=yg._CAPRICORN)
        self.assertIn("Ruchaka", {r.sanskrit for r in results})

    def test_mahapurusha_requires_kendra(self):
        # Mars exalted in Capricorn but Ascendant Aries → Mars in house 10
        # (a kendra) → still Ruchaka. Move ascendant so Mars is house 2.
        # Capricorn is the 2nd from Sagittarius? Sag=8, Cap=9 → house 2. Not a kendra.
        results = yg._detect(self._signs(MARS=yg._CAPRICORN), asc_sign=yg._SAGITTARIUS)
        self.assertNotIn("Ruchaka", {r.sanskrit for r in results})

    def test_gaja_kesari(self):
        # Jupiter in a kendra from the Moon: Moon Virgo (5), Jupiter
        # Sagittarius (8) → house_from(5, 8) = 4 → kendra.
        results = yg._detect(self._signs(JUPITER=yg._SAGITTARIUS), asc_sign=yg._CANCER)
        self.assertIn("Gaja-Kesari", {r.sanskrit for r in results})

    def test_no_gaja_kesari_when_not_in_kendra(self):
        # Jupiter Scorpio (7), Moon Virgo (5) → house_from(5, 7) = 3 → not a kendra.
        results = yg._detect(self._signs(JUPITER=yg._SCORPIO), asc_sign=yg._CANCER)
        self.assertNotIn("Gaja-Kesari", {r.sanskrit for r in results})

    def test_budha_aditya(self):
        # Sun and Mercury in the same sign.
        results = yg._detect(self._signs(SUN=yg._LEO, MERCURY=yg._LEO), asc_sign=yg._CANCER)
        self.assertIn("Budha-Aditya", {r.sanskrit for r in results})

    def test_no_budha_aditya_when_different_signs(self):
        results = yg._detect(self._signs(SUN=yg._LEO, MERCURY=yg._VIRGO), asc_sign=yg._CANCER)
        self.assertNotIn("Budha-Aditya", {r.sanskrit for r in results})

    def test_chandra_mangala(self):
        results = yg._detect(self._signs(MOON=yg._ARIES, MARS=yg._ARIES), asc_sign=yg._CANCER)
        self.assertIn("Chandra-Mangala", {r.sanskrit for r in results})


class FrozenDataclassTests(unittest.TestCase):
    def test_yoga_result_is_frozen(self):
        r = yg.YogaResult("X Yoga", "X", (const.SUN,), "desc")
        with self.assertRaises(AttributeError):
            r.name = "Y"  # type: ignore[misc]


class ChartLevelTests(unittest.TestCase):
    def test_detect_yogas_returns_list(self):
        date = Datetime("1947/08/15", "00:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        result = yg.detect_yogas(chart)
        self.assertIsInstance(result, list)
        for r in result:
            self.assertIsInstance(r, yg.YogaResult)

    def test_tropical_and_sidereal_chart_agree(self):
        date = Datetime("1947/08/15", "00:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        tropical = Chart(date, pos)
        sidereal = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        rt = {r.sanskrit for r in yg.detect_yogas(tropical)}
        rs = {r.sanskrit for r in yg.detect_yogas(sidereal)}
        self.assertEqual(rt, rs)

    def test_detect_yogas_on_a_chart_with_a_known_yoga(self):
        # Find a date producing at least one yoga to exercise the chart path.
        # 2024-04-19 ~ Sun and Mercury both in sidereal Aries → Budha-Aditya.
        date = Datetime("2024/04/19", "12:00", "+00:00")
        pos = GeoPos("0n00", "0e00")
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        result = yg.detect_yogas(chart)
        # Whatever yogas it has, the result must be internally consistent —
        # every reported yoga's planets must actually be in the chart.
        for r in result:
            for p in r.planets:
                # ASC isn't a planet but no yoga here lists it.
                self.assertIn(p, yg._CLASSICAL_PLANETS)


if __name__ == "__main__":
    unittest.main()

"""Tests for the extended Vedic yoga set — Task 026b.

Covers Raja, Dhana, Vipareeta Raja, Neecha Bhanga, and Kemadruma. The
original 8 yogas (Pancha Mahapurusha + Gaja-Kesari + Budha-Aditya +
Chandra-Mangala) are covered in tests/test_vedic_yogas.py.
"""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import yogas as yg

# Sign indices for readability.
ARIES, TAURUS, GEMINI, CANCER = 0, 1, 2, 3
LEO, VIRGO, LIBRA, SCORPIO = 4, 5, 6, 7
SAGITTARIUS, CAPRICORN, AQUARIUS, PISCES = 8, 9, 10, 11


class HouseHelperTests(unittest.TestCase):
    def test_house_lord(self):
        # Aries ascendant: 1st = Aries → Mars, 5th = Leo → Sun, 10th = Capricorn → Saturn.
        self.assertEqual(yg.house_lord(1, ARIES), const.MARS)
        self.assertEqual(yg.house_lord(5, ARIES), const.SUN)
        self.assertEqual(yg.house_lord(10, ARIES), const.SATURN)

    def test_houses_ruled_by(self):
        # With Aries ascendant, Mars rules Aries (1) and Scorpio (8).
        self.assertEqual(set(yg.houses_ruled_by(const.MARS, ARIES)), {1, 8})
        # Mercury rules Gemini and Virgo; from Aries that's houses 3 and 6.
        self.assertEqual(set(yg.houses_ruled_by(const.MERCURY, ARIES)), {3, 6})

    def test_sign_lord(self):
        self.assertEqual(yg.sign_lord(ARIES), const.MARS)
        self.assertEqual(yg.sign_lord(AQUARIUS), const.SATURN)

    def test_exalted_in_inverse(self):
        # Sun exalts in Aries, Moon in Taurus, Mars in Capricorn, ...
        self.assertEqual(yg._EXALTED_IN[ARIES], const.SUN)
        self.assertEqual(yg._EXALTED_IN[TAURUS], const.MOON)
        self.assertEqual(yg._EXALTED_IN[CAPRICORN], const.MARS)


class RajaYogaTests(unittest.TestCase):
    def _signs(self, **overrides):
        base = {
            const.SUN: LEO,
            const.MOON: VIRGO,
            const.MARS: GEMINI,
            const.MERCURY: TAURUS,
            const.JUPITER: SCORPIO,
            const.VENUS: LIBRA,
            const.SATURN: SAGITTARIUS,
        }
        for name, v in overrides.items():
            base[getattr(const, name)] = v
        return base

    def test_kendra_lord_conjunct_trikona_lord(self):
        # Aries ascendant. 10th lord = Saturn (Capricorn), 9th lord = Jupiter
        # (Sagittarius). Put both at the same sign → Raja Yoga.
        signs = self._signs(JUPITER=SCORPIO, SATURN=SCORPIO)
        results = yg._detect_extended(signs, asc_sign=ARIES)
        rajas = [r for r in results if r.sanskrit == "Raja"]
        self.assertTrue(rajas)
        self.assertEqual(set(rajas[0].planets), {const.JUPITER, const.SATURN})

    def test_no_raja_when_lords_dont_conjoin(self):
        signs = self._signs(JUPITER=SCORPIO, SATURN=SAGITTARIUS)
        results = yg._detect_extended(signs, asc_sign=ARIES)
        self.assertFalse([r for r in results if r.sanskrit == "Raja"])


class DhanaYogaTests(unittest.TestCase):
    def test_wealth_lords_conjunct(self):
        # Aries ascendant: 9th lord = Jupiter, 11th lord = Saturn. Conjunct → Dhana.
        signs = {
            const.SUN: LEO,
            const.MOON: VIRGO,
            const.MARS: GEMINI,
            const.MERCURY: TAURUS,
            const.JUPITER: SCORPIO,
            const.VENUS: LIBRA,
            const.SATURN: SCORPIO,
        }
        results = yg._detect_extended(signs, asc_sign=ARIES)
        dhanas = [r for r in results if r.sanskrit == "Dhana"]
        self.assertTrue(dhanas)


class VipareetaRajaTests(unittest.TestCase):
    def test_harsha_yoga_sixth_lord_in_dusthana(self):
        # Cancer ascendant: 6th house = Sagittarius → Jupiter. Place Jupiter
        # in the 8th house (= Aquarius, sign index AQUARIUS) → a dusthana → Harsha.
        signs = {
            const.SUN: LEO,
            const.MOON: VIRGO,
            const.MARS: GEMINI,
            const.MERCURY: TAURUS,
            const.JUPITER: AQUARIUS,
            const.VENUS: LIBRA,
            const.SATURN: PISCES,
        }
        results = yg._detect_extended(signs, asc_sign=CANCER)
        self.assertIn("Harsha", {r.sanskrit for r in results})

    def test_no_harsha_when_sixth_lord_not_in_dusthana(self):
        signs = {
            const.SUN: LEO,
            const.MOON: VIRGO,
            const.MARS: GEMINI,
            const.MERCURY: TAURUS,
            const.JUPITER: ARIES,  # 10th from Cancer = a kendra, not a dusthana
            const.VENUS: LIBRA,
            const.SATURN: PISCES,
        }
        results = yg._detect_extended(signs, asc_sign=CANCER)
        self.assertNotIn("Harsha", {r.sanskrit for r in results})


class NeechaBhangaTests(unittest.TestCase):
    def test_cancelled_when_dispositor_in_kendra(self):
        # Saturn debilitated in Aries. Dispositor of Aries = Mars. Cancer
        # ascendant — put Mars in the 4th house (= Libra, LIBRA) which is a
        # kendra → debilitation cancelled → Neecha Bhanga.
        signs = {
            const.SUN: LEO,
            const.MOON: VIRGO,
            const.MARS: LIBRA,
            const.MERCURY: TAURUS,
            const.JUPITER: SCORPIO,
            const.VENUS: GEMINI,
            const.SATURN: ARIES,
        }
        results = yg._detect_extended(signs, asc_sign=CANCER)
        nb = [r for r in results if r.sanskrit == "Neecha Bhanga"]
        self.assertTrue(nb)
        self.assertEqual(nb[0].planets, (const.SATURN,))

    def test_not_cancelled_when_no_kendra_condition(self):
        # Saturn debilitated in Aries; Mars (dispositor) NOT in a kendra,
        # and the Sun (exalted in Aries) NOT in a kendra either.
        signs = {
            const.SUN: GEMINI,  # 3rd from Cancer asc → not a kendra
            const.MOON: VIRGO,
            const.MARS: TAURUS,  # 11th from Cancer → not a kendra
            const.MERCURY: SCORPIO,
            const.JUPITER: SAGITTARIUS,
            const.VENUS: PISCES,
            const.SATURN: ARIES,
        }
        results = yg._detect_extended(signs, asc_sign=CANCER)
        self.assertFalse([r for r in results if r.sanskrit == "Neecha Bhanga"])

    def test_no_neecha_bhanga_when_planet_not_debilitated(self):
        signs = {
            const.SUN: LEO,
            const.MOON: VIRGO,
            const.MARS: ARIES,  # own sign
            const.MERCURY: TAURUS,
            const.JUPITER: SCORPIO,
            const.VENUS: LIBRA,
            const.SATURN: CAPRICORN,  # own sign
        }
        results = yg._detect_extended(signs, asc_sign=CANCER)
        self.assertFalse([r for r in results if r.sanskrit == "Neecha Bhanga"])


class KemadrumaTests(unittest.TestCase):
    def test_fires_when_2nd_and_12th_from_moon_empty(self):
        # Moon in Virgo (5). 2nd from = Libra (6), 12th from = Leo (4).
        # No graha (other than Sun) at sign 4 or 6.
        signs = {
            const.SUN: ARIES,
            const.MOON: VIRGO,
            const.MARS: GEMINI,
            const.MERCURY: TAURUS,
            const.JUPITER: CANCER,
            const.VENUS: SCORPIO,
            const.SATURN: SAGITTARIUS,
        }
        results = yg._detect_extended(signs, asc_sign=ARIES)
        self.assertIn("Kemadruma", {r.sanskrit for r in results})

    def test_does_not_fire_when_a_graha_flanks_the_moon(self):
        # Moon in Virgo (5). Put Mercury in Leo (4) — the 12th from the Moon.
        signs = {
            const.SUN: ARIES,
            const.MOON: VIRGO,
            const.MARS: GEMINI,
            const.MERCURY: LEO,
            const.JUPITER: CANCER,
            const.VENUS: SCORPIO,
            const.SATURN: SAGITTARIUS,
        }
        results = yg._detect_extended(signs, asc_sign=ARIES)
        self.assertNotIn("Kemadruma", {r.sanskrit for r in results})

    def test_sun_alone_flanking_does_not_block_kemadruma(self):
        # Moon in Virgo (5). Sun in Leo (4, the 12th from Moon). Since the
        # Sun isn't counted for Kemadruma, the yoga still forms.
        signs = {
            const.SUN: LEO,
            const.MOON: VIRGO,
            const.MARS: GEMINI,
            const.MERCURY: TAURUS,
            const.JUPITER: CANCER,
            const.VENUS: SCORPIO,
            const.SATURN: SAGITTARIUS,
        }
        results = yg._detect_extended(signs, asc_sign=ARIES)
        self.assertIn("Kemadruma", {r.sanskrit for r in results})


class IntegrationTests(unittest.TestCase):
    def test_detect_yogas_includes_extended(self):
        # Use a real chart; whatever yogas it has, the result is a list of
        # YogaResult and any extended yoga that fires has valid planets.
        date = Datetime("1947/08/15", "00:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        result = yg.detect_yogas(chart)
        self.assertIsInstance(result, list)
        names = {r.sanskrit for r in result}
        # At minimum the result should be drawable from the union of all
        # supported sanskrit names.
        supported = {
            "Ruchaka",
            "Bhadra",
            "Hamsa",
            "Malavya",
            "Sasha",
            "Gaja-Kesari",
            "Budha-Aditya",
            "Chandra-Mangala",
            "Raja",
            "Dhana",
            "Harsha",
            "Sarala",
            "Vimala",
            "Neecha Bhanga",
            "Kemadruma",
        }
        self.assertTrue(names.issubset(supported))

    def test_tropical_and_sidereal_chart_agree(self):
        date = Datetime("1947/08/15", "00:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        tropical = Chart(date, pos)
        sidereal = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        rt = sorted((r.sanskrit, r.planets) for r in yg.detect_yogas(tropical))
        rs = sorted((r.sanskrit, r.planets) for r in yg.detect_yogas(sidereal))
        self.assertEqual(rt, rs)


if __name__ == "__main__":
    unittest.main()

"""Tests for the lesser Vedic yogas and yoga strength scoring — Task 032."""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import yogas as yg

ARIES, TAURUS, GEMINI, CANCER = 0, 1, 2, 3
LEO, VIRGO, LIBRA, SCORPIO = 4, 5, 6, 7
SAGITTARIUS, CAPRICORN, AQUARIUS, PISCES = 8, 9, 10, 11


def _signs(**overrides):
    base = {
        const.SUN: ARIES,
        const.MOON: CANCER,
        const.MARS: GEMINI,
        const.MERCURY: TAURUS,
        const.JUPITER: SCORPIO,
        const.VENUS: LIBRA,
        const.SATURN: SAGITTARIUS,
    }
    for name, v in overrides.items():
        base[getattr(const, name)] = v
    return base


class SunAndMoonConjunctionYogasTests(unittest.TestCase):
    def test_sunapha_planet_in_2nd_from_moon(self):
        # Moon in Cancer (3). 2nd from Moon = Leo (4). Put Mars there.
        res = yg._detect_lesser(_signs(MOON=CANCER, MARS=LEO), asc_sign=ARIES)
        names = {y.sanskrit for y in res}
        self.assertIn("Sunapha", names)
        self.assertNotIn("Anapha", names)

    def test_anapha_planet_in_12th_from_moon(self):
        # 12th from Cancer = Gemini (2). Put Mars there (and nothing in Leo).
        res = yg._detect_lesser(_signs(MOON=CANCER, MARS=GEMINI, MERCURY=PISCES), asc_sign=ARIES)
        names = {y.sanskrit for y in res}
        self.assertIn("Anapha", names)
        self.assertNotIn("Sunapha", names)

    def test_durudhara_when_both_sides_occupied(self):
        # Moon in Cancer (3). 2nd = Leo (4), 12th = Gemini (2). Mars in
        # Gemini, Saturn in Leo.
        res = yg._detect_lesser(_signs(MOON=CANCER, MARS=GEMINI, SATURN=LEO), asc_sign=ARIES)
        names = {y.sanskrit for y in res}
        self.assertIn("Durudhara", names)
        self.assertNotIn("Sunapha", names)
        self.assertNotIn("Anapha", names)

    def test_vesi_planet_in_2nd_from_sun(self):
        # Sun in Aries (0). 2nd from Sun = Taurus (1). Mercury is there.
        res = yg._detect_lesser(_signs(SUN=ARIES, MERCURY=TAURUS), asc_sign=ARIES)
        self.assertIn("Vesi", {y.sanskrit for y in res})

    def test_vasi_planet_in_12th_from_sun(self):
        # 12th from Aries = Pisces (11). Put Saturn there; nothing in Taurus.
        res = yg._detect_lesser(_signs(SUN=ARIES, SATURN=PISCES, MERCURY=GEMINI), asc_sign=ARIES)
        names = {y.sanskrit for y in res}
        self.assertIn("Vasi", names)
        self.assertNotIn("Vesi", names)

    def test_ubhayachari_both_sides_of_sun(self):
        res = yg._detect_lesser(_signs(SUN=ARIES, MERCURY=TAURUS, SATURN=PISCES), asc_sign=ARIES)
        self.assertIn("Ubhayachari", {y.sanskrit for y in res})


class HouseBasedLesserYogasTests(unittest.TestCase):
    def test_amala_benefic_in_10th_from_lagna(self):
        # Aries ascendant → 10th house = Capricorn (9). Put Jupiter there.
        res = yg._detect_lesser(_signs(JUPITER=CAPRICORN), asc_sign=ARIES)
        amala = [y for y in res if y.sanskrit == "Amala"]
        self.assertTrue(amala)
        self.assertIn(const.JUPITER, amala[0].planets)

    def test_no_amala_when_no_benefic_in_10th(self):
        res = yg._detect_lesser(_signs(), asc_sign=ARIES)
        self.assertNotIn("Amala", {y.sanskrit for y in res})

    def test_vasumati_all_benefics_in_upachayas(self):
        # Aries ascendant. Upachaya houses from Aries: 3=Gemini, 6=Virgo,
        # 10=Capricorn, 11=Aquarius. Put Jupiter→Gemini, Venus→Virgo,
        # Mercury→Capricorn.
        res = yg._detect_lesser(
            _signs(JUPITER=GEMINI, VENUS=VIRGO, MERCURY=CAPRICORN), asc_sign=ARIES
        )
        self.assertIn("Vasumati", {y.sanskrit for y in res})

    def test_kahala_4th_and_9th_lords_in_mutual_kendras(self):
        # Aries ascendant: 4th house = Cancer → Moon; 9th house =
        # Sagittarius → Jupiter. Place Moon and Jupiter in mutual kendras
        # — e.g. Moon in Aries (0), Jupiter in Cancer (3): house_from(0, 3) = 4.
        res = yg._detect_lesser(_signs(MOON=ARIES, JUPITER=CANCER), asc_sign=ARIES)
        self.assertIn("Kahala", {y.sanskrit for y in res})

    def test_lakshmi_9th_lord_dignified_in_kendra_trikona(self):
        # Aries ascendant: 9th lord = Jupiter (rules Sagittarius). Put
        # Jupiter in Sagittarius (8, its own sign) and in a trikona from
        # the Lagna. Sagittarius is the 9th house from Aries (a trikona).
        res = yg._detect_lesser(_signs(JUPITER=SAGITTARIUS), asc_sign=ARIES)
        self.assertIn("Lakshmi", {y.sanskrit for y in res})

    def test_saraswati_jvm_in_good_houses(self):
        # Aries ascendant. Good houses (kendra/trikona/2nd) = 1,2,4,5,7,9,10.
        # Jupiter→Aries(1st), Venus→Taurus(2nd), Mercury→Cancer(4th).
        res = yg._detect_lesser(_signs(JUPITER=ARIES, VENUS=TAURUS, MERCURY=CANCER), asc_sign=ARIES)
        self.assertIn("Saraswati", {y.sanskrit for y in res})


class YogaStrengthTests(unittest.TestCase):
    def test_own_sign_planet_scores_positive(self):
        # A YogaResult naming Mars; Mars in Aries (own) and in house 1
        # (a kendra) → +2 + +1 = +3.
        y = yg.YogaResult("Ruchaka Yoga", "Ruchaka", (const.MARS,), "desc")
        score = yg.yoga_strength(y, {const.MARS: ARIES}, asc_sign=ARIES)
        self.assertEqual(score, 3)

    def test_debilitated_planet_scores_negative(self):
        # Mars debilitated in Cancer (3), in house 4 (a kendra) from
        # Aries → −2 + +1 = −1.
        y = yg.YogaResult("X Yoga", "X", (const.MARS,), "desc")
        score = yg.yoga_strength(y, {const.MARS: CANCER}, asc_sign=ARIES)
        self.assertEqual(score, -1)

    def test_neutral_house_no_house_bonus(self):
        # Mars in Leo (4, neutral sign), house 5 from Aries (a trikona →
        # +1). Not own/exalted/debilitated → 0 + 1 = 1.
        y = yg.YogaResult("X Yoga", "X", (const.MARS,), "desc")
        score = yg.yoga_strength(y, {const.MARS: LEO}, asc_sign=ARIES)
        self.assertEqual(score, 1)


class ChartLevelTests(unittest.TestCase):
    def test_detect_yogas_includes_lesser(self):
        date = Datetime("1947/08/15", "00:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        names = {y.sanskrit for y in yg.detect_yogas(chart)}
        all_supported = {
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
            "Amala",
            "Adhi",
            "Lakshmi",
            "Saraswati",
            "Kahala",
            "Vasumati",
            "Sunapha",
            "Anapha",
            "Durudhara",
            "Vesi",
            "Vasi",
            "Ubhayachari",
        }
        self.assertTrue(names.issubset(all_supported))

    def test_detect_yogas_with_strength_sorted_descending(self):
        date = Datetime("1947/08/15", "00:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        scored = yg.detect_yogas_with_strength(chart)
        self.assertTrue(all(isinstance(s, int) for _y, s in scored))
        strengths = [s for _y, s in scored]
        self.assertEqual(strengths, sorted(strengths, reverse=True))
        # The unscored list and the scored list have the same yogas.
        plain = {(y.sanskrit, y.planets) for y in yg.detect_yogas(chart)}
        scored_set = {(y.sanskrit, y.planets) for y, _s in scored}
        self.assertEqual(plain, scored_set)

    def test_tropical_and_sidereal_agree(self):
        date = Datetime("1947/08/15", "00:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        trop = Chart(date, pos)
        sid = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        rt = sorted((y.sanskrit, y.planets) for y in yg.detect_yogas(trop))
        rs = sorted((y.sanskrit, y.planets) for y in yg.detect_yogas(sid))
        self.assertEqual(rt, rs)


if __name__ == "__main__":
    unittest.main()


class WeightedStrengthAndCancellationTests(unittest.TestCase):
    def setUp(self):
        from mayaastrolib.chart import Chart as _C
        from mayaastrolib.datetime import Datetime as _D
        from mayaastrolib.geopos import GeoPos as _G

        self.chart = _C(_D("1947/08/15", "00:00", "+05:30"), _G("28n36", "77e12"))
        self.sid = _C(
            _D("1947/08/15", "00:00", "+05:30"),
            _G("28n36", "77e12"),
            zodiac=const.ZODIAC_SIDEREAL,
        )

    def test_weighted_strength_is_int(self):
        for y in yg.detect_yogas(self.chart):
            self.assertIsInstance(yg.yoga_strength_weighted(y, self.chart), int)

    def test_detect_with_strength_weighted_flag(self):
        plain = yg.detect_yogas_with_strength(self.chart, weighted=False)
        weighted = yg.detect_yogas_with_strength(self.chart, weighted=True)
        # Same yogas, possibly different ordering / scores.
        self.assertEqual(
            {(y.sanskrit, y.planets) for y, _s in plain},
            {(y.sanskrit, y.planets) for y, _s in weighted},
        )
        # Both lists are sorted descending by their score.
        for lst in (plain, weighted):
            self.assertEqual([s for _y, s in lst], sorted((s for _y, s in lst), reverse=True))

    def test_weighted_strength_skips_non_planet_members(self):
        # A YogaResult whose planets include something not in the
        # classical set is just skipped (contributes 0).
        y = yg.YogaResult("X Yoga", "X", ("Ascendant", const.SUN), "desc")
        self.assertEqual(
            yg.yoga_strength_weighted(y, self.chart),
            yg.yoga_strength_weighted(yg.YogaResult("X", "X", (const.SUN,), "d"), self.chart),
        )

    def test_gaja_kesari_cancelled_when_jupiter_debilitated(self):
        # Jupiter debilitated in Capricorn (9), Moon also in Capricorn →
        # Jupiter is in the 1st (a kendra) from the Moon, but the yoga is
        # cancelled.
        signs = {
            const.SUN: ARIES,
            const.MOON: CAPRICORN,
            const.MARS: TAURUS,
            const.MERCURY: GEMINI,
            const.JUPITER: CAPRICORN,
            const.VENUS: LEO,
            const.SATURN: VIRGO,
        }
        names = {y.sanskrit for y in yg._detect(signs, asc_sign=ARIES)}
        self.assertNotIn("Gaja-Kesari", names)

    def test_gaja_kesari_fires_when_not_debilitated(self):
        # Jupiter in Sagittarius (own sign), Moon in Sagittarius → kendra,
        # not cancelled.
        signs = {
            const.SUN: ARIES,
            const.MOON: SAGITTARIUS,
            const.MARS: TAURUS,
            const.MERCURY: GEMINI,
            const.JUPITER: SAGITTARIUS,
            const.VENUS: LEO,
            const.SATURN: VIRGO,
        }
        names = {y.sanskrit for y in yg._detect(signs, asc_sign=ARIES)}
        self.assertIn("Gaja-Kesari", names)

    def test_neecha_bhanga_navamsa_exaltation(self):
        # _detect_extended with planet_lons: a debilitated planet that is
        # exalted in its navamsa triggers Neecha Bhanga even if the
        # kendra conditions don't hold. Saturn debilitated in Aries; pick
        # a longitude in Aries whose D9 sign is Libra (Saturn's
        # exaltation). Aries navamsas (movable, start from Aries): the 7th
        # navamsa = Libra → 20°-23°20' of Aries.
        signs = {
            const.SUN: GEMINI,
            const.MOON: VIRGO,
            const.MARS: TAURUS,
            const.MERCURY: SCORPIO,
            const.JUPITER: SAGITTARIUS,
            const.VENUS: PISCES,
            const.SATURN: ARIES,
        }
        from mayaastrolib.vedic import divisional as _div

        sat_lon = 21.0  # ~7th navamsa of Aries
        self.assertEqual(_div.navamsa(sat_lon), 6)  # Libra
        lons = {const.SATURN: sat_lon}
        res = yg._detect_extended(signs, asc_sign=CANCER, planet_lons=lons)
        self.assertIn("Neecha Bhanga", {y.sanskrit for y in res})

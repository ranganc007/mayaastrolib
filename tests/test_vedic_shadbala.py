"""Tests for the six-fold Shadbala — Task 041.

Mixes pure-function unit tests (exact, ephemeris-independent) for each of
the six balas with chart-level structural and invariant checks.
"""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import shadbala as sb


class _ChartBase(unittest.TestCase):
    def setUp(self):
        self.date = Datetime("1980/06/15", "14:30", "+05:30")
        self.pos = GeoPos("28n36", "77e12")
        self.sidereal = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)
        self.tropical = Chart(self.date, self.pos)


# --------------------------------------------------------------------- #
#   Structure & invariants                                              #
# --------------------------------------------------------------------- #


class StructureTests(_ChartBase):
    def test_returns_all_seven_planets(self):
        res = sb.shadbala(self.sidereal)
        self.assertEqual(set(res.keys()), set(sb._CLASSICAL_PLANETS))

    def test_entry_has_all_six_balas(self):
        e = sb.shadbala(self.sidereal)[const.SUN]
        for key in ("sthana", "dig", "kala", "cheshta", "naisargika", "drik"):
            self.assertIn(key, e)

    def test_total_virupas_is_sum_of_six(self):
        for p, e in sb.shadbala(self.sidereal).items():
            expected = (
                e["sthana"]["total"]
                + e["dig"]
                + e["kala"]["total"]
                + e["cheshta"]
                + e["naisargika"]
                + e["drik"]
            )
            self.assertAlmostEqual(e["total_virupas"], expected, places=9, msg=p)

    def test_total_rupas_is_virupas_over_60(self):
        for e in sb.shadbala(self.sidereal).values():
            self.assertAlmostEqual(e["total_rupas"], e["total_virupas"] / 60.0, places=9)

    def test_all_totals_positive_and_plausible(self):
        # Real natal charts land roughly within 3..13 rupas per planet.
        for p, e in sb.shadbala(self.sidereal).items():
            self.assertGreater(e["total_virupas"], 0, p)
            self.assertTrue(2.0 <= e["total_rupas"] <= 14.0, f"{p}: {e['total_rupas']}")

    def test_sufficient_flag_matches_required(self):
        for p, e in sb.shadbala(self.sidereal).items():
            self.assertEqual(e["sufficient"], e["total_rupas"] >= e["required_rupas"])
            self.assertEqual(e["required_rupas"], sb.REQUIRED_RUPAS[p])

    def test_sthana_total_is_sum_of_its_components(self):
        s = sb.shadbala(self.sidereal)[const.MARS]["sthana"]
        self.assertAlmostEqual(s["total"], sum(s["components"].values()), places=9)
        self.assertEqual(
            set(s["components"]),
            {"uchcha", "saptavargaja", "oja_yugma", "kendradi", "drekkana"},
        )

    def test_kala_total_is_sum_of_its_components(self):
        k = sb.shadbala(self.sidereal)[const.MOON]["kala"]
        self.assertAlmostEqual(k["total"], sum(k["components"].values()), places=9)
        self.assertEqual(
            set(k["components"]),
            {"nathonnatha", "paksha", "tribhaga", "vara", "hora", "ayana"},
        )

    def test_tropical_and_sidereal_charts_agree(self):
        rt = sb.shadbala(self.tropical)
        rs = sb.shadbala(self.sidereal)
        # Same physical positions → totals within ~1 rupa (small discrete
        # differences only at sign boundaries in Saptavargaja/Drik).
        for p in sb._CLASSICAL_PLANETS:
            self.assertLess(abs(rt[p]["total_rupas"] - rs[p]["total_rupas"]), 1.0, p)


# --------------------------------------------------------------------- #
#   Naisargika Bala (exact constants)                                   #
# --------------------------------------------------------------------- #


class NaisargikaTests(unittest.TestCase):
    def test_exact_values(self):
        expected = {
            const.SUN: 60.0,
            const.MOON: 360.0 / 7,
            const.VENUS: 300.0 / 7,
            const.JUPITER: 240.0 / 7,
            const.MERCURY: 180.0 / 7,
            const.MARS: 120.0 / 7,
            const.SATURN: 60.0 / 7,
        }
        for p, v in expected.items():
            self.assertAlmostEqual(sb._naisargika_bala(p), v, places=9, msg=p)

    def test_ordering_sun_strongest_saturn_weakest(self):
        vals = {p: sb._naisargika_bala(p) for p in sb._CLASSICAL_PLANETS}
        order = sorted(vals, key=vals.get, reverse=True)
        self.assertEqual(order[0], const.SUN)
        self.assertEqual(order[-1], const.SATURN)


# --------------------------------------------------------------------- #
#   Uchcha Bala (exaltation distance)                                   #
# --------------------------------------------------------------------- #


class UchchaTests(unittest.TestCase):
    def test_full_at_exaltation_point(self):
        # Sun exalted at 10° Aries (sidereal lon 10.0).
        self.assertAlmostEqual(sb._uchcha_bala(const.SUN, 10.0), 60.0, places=6)

    def test_zero_at_debilitation_point(self):
        # Sun debilitated at 10° Libra (sidereal lon 190.0).
        self.assertAlmostEqual(sb._uchcha_bala(const.SUN, 190.0), 0.0, places=6)

    def test_thirty_at_ninety_degrees_from_debilitation(self):
        # 90° from the debilitation point → arc 90 / 3 = 30.
        self.assertAlmostEqual(sb._uchcha_bala(const.SUN, 100.0), 30.0, places=6)

    def test_in_range_for_all_planets(self):
        for p in sb._CLASSICAL_PLANETS:
            for lon in (0.0, 47.3, 123.0, 250.0, 359.9):
                self.assertTrue(0.0 <= sb._uchcha_bala(p, lon) <= 60.0 + 1e-6)


# --------------------------------------------------------------------- #
#   Kendradi / Drekkana / Oja-Yugma                                     #
# --------------------------------------------------------------------- #


class PositionalSubBalaTests(unittest.TestCase):
    def test_kendradi_angular_succedent_cadent(self):
        for h in (1, 4, 7, 10):
            self.assertEqual(sb._kendradi_bala(h), 60.0)
        for h in (2, 5, 8, 11):
            self.assertEqual(sb._kendradi_bala(h), 30.0)
        for h in (3, 6, 9, 12):
            self.assertEqual(sb._kendradi_bala(h), 15.0)

    def test_drekkana_masculine_first_decanate(self):
        # Sun (masculine) at 5° of a sign → 1st decanate → 15.
        self.assertEqual(sb._drekkana_bala(const.SUN, 5.0), 15.0)
        # Sun at 25° → 3rd decanate → 0.
        self.assertEqual(sb._drekkana_bala(const.SUN, 25.0), 0.0)

    def test_drekkana_feminine_third_decanate(self):
        self.assertEqual(sb._drekkana_bala(const.VENUS, 25.0), 15.0)
        self.assertEqual(sb._drekkana_bala(const.VENUS, 5.0), 0.0)

    def test_drekkana_hermaphrodite_middle_decanate(self):
        self.assertEqual(sb._drekkana_bala(const.MERCURY, 15.0), 15.0)
        self.assertEqual(sb._drekkana_bala(const.MERCURY, 5.0), 0.0)

    def test_oja_yugma_sun_in_odd_sign(self):
        # Sun at 5° Aries (odd sign idx 0): rasi odd → 15; navamsa of 5°
        # Aries is also odd-ish, but assert at least the rasi point lands.
        self.assertGreaterEqual(sb._oja_yugma_bala(const.SUN, 5.0), 15.0)

    def test_oja_yugma_moon_prefers_even(self):
        # Moon at 5° Taurus (even sign idx 1) gets the rasi point.
        self.assertGreaterEqual(sb._oja_yugma_bala(const.MOON, 35.0), 15.0)
        # Moon in an odd sign loses the rasi point.
        self.assertLess(sb._oja_yugma_bala(const.MOON, 5.0), 30.0)


# --------------------------------------------------------------------- #
#   Compound friendship & Saptavargaja                                  #
# --------------------------------------------------------------------- #


class FriendshipTests(unittest.TestCase):
    def test_natural_friend_in_friendly_house_is_great_friend(self):
        # Sun's natural friend Jupiter, placed 4 signs away (temporal friend).
        rel = sb._compound_relation(const.SUN, const.JUPITER, 0, 3)
        self.assertEqual(rel, "great_friend")

    def test_natural_enemy_in_unfriendly_house_is_great_enemy(self):
        # Sun's natural enemy Saturn, placed 6 signs away (temporal enemy).
        rel = sb._compound_relation(const.SUN, const.SATURN, 0, 6)
        self.assertEqual(rel, "great_enemy")

    def test_neutral_natural_resolves_by_temporal(self):
        # Sun-Mercury are natural neutrals; temporal friend → friend.
        self.assertEqual(sb._compound_relation(const.SUN, const.MERCURY, 0, 3), "friend")
        # temporal enemy (same/adjacent unfriendly house) → enemy.
        self.assertEqual(sb._compound_relation(const.SUN, const.MERCURY, 0, 6), "enemy")

    def test_saptavargaja_own_sign_scores_high(self):
        # A planet sitting in its own sign across vargas scores well above
        # the all-neutral floor. Sun at 5° Leo (own sign).
        signs = {p: 0 for p in sb._CLASSICAL_PLANETS}
        signs[const.SUN] = 4
        val = sb._saptavargaja_bala(const.SUN, 4 * 30.0 + 5.0, signs)
        self.assertGreater(val, 30.0)

    def test_saptavargaja_in_range(self):
        signs = {p: i for i, p in enumerate(sb._CLASSICAL_PLANETS)}
        for p in sb._CLASSICAL_PLANETS:
            v = sb._saptavargaja_bala(p, signs[p] * 30.0 + 12.0, signs)
            self.assertTrue(0.0 < v <= 7 * 45.0, f"{p}: {v}")


# --------------------------------------------------------------------- #
#   Dig Bala                                                            #
# --------------------------------------------------------------------- #


class DigBalaTests(unittest.TestCase):
    def setUp(self):
        self.angles = {"asc": 0.0, "mc": 270.0, "ic": 90.0, "desc": 180.0}

    def test_sun_full_at_mc(self):
        # Sun's strong angle is the MC; placed there → ~60.
        self.assertAlmostEqual(sb._dig_bala(const.SUN, 270.0, self.angles), 60.0, places=6)

    def test_sun_zero_at_ic(self):
        self.assertAlmostEqual(sb._dig_bala(const.SUN, 90.0, self.angles), 0.0, places=6)

    def test_saturn_full_at_desc(self):
        self.assertAlmostEqual(sb._dig_bala(const.SATURN, 180.0, self.angles), 60.0, places=6)

    def test_all_planets_in_range(self):
        for p in sb._CLASSICAL_PLANETS:
            for lon in (0.0, 45.0, 130.0, 270.0, 350.0):
                self.assertTrue(0.0 <= sb._dig_bala(p, lon, self.angles) <= 60.0 + 1e-6)


# --------------------------------------------------------------------- #
#   Kala sub-balas                                                      #
# --------------------------------------------------------------------- #


class KalaTests(unittest.TestCase):
    def test_nathonnatha_mercury_always_full(self):
        for h in (0.0, 6.0, 12.0, 18.0):
            self.assertEqual(sb._nathonnatha_bala(const.MERCURY, h), 60.0)

    def test_nathonnatha_day_planet_peaks_at_noon(self):
        self.assertAlmostEqual(sb._nathonnatha_bala(const.SUN, 12.0), 60.0, places=6)
        self.assertAlmostEqual(sb._nathonnatha_bala(const.SUN, 0.0), 0.0, places=6)

    def test_nathonnatha_night_planet_peaks_at_midnight(self):
        self.assertAlmostEqual(sb._nathonnatha_bala(const.SATURN, 0.0), 60.0, places=6)
        self.assertAlmostEqual(sb._nathonnatha_bala(const.SATURN, 12.0), 0.0, places=6)

    def test_paksha_full_moon_favours_benefics(self):
        # Full moon: Sun-Moon kendra = 180.
        sun, moon = 0.0, 180.0
        self.assertAlmostEqual(sb._paksha_bala(const.JUPITER, sun, moon), 60.0, places=6)
        self.assertAlmostEqual(sb._paksha_bala(const.SATURN, sun, moon), 0.0, places=6)

    def test_paksha_moon_is_doubled(self):
        sun, moon = 0.0, 180.0  # full moon → benefic share 60, Moon doubled
        self.assertAlmostEqual(sb._paksha_bala(const.MOON, sun, moon), 120.0, places=6)

    def test_ayana_sun_doubled_and_clamped(self):
        # Sun at +24° declination → (24+24)/48*60 = 60, doubled = 120.
        self.assertAlmostEqual(sb._ayana_bala(const.SUN, 24.0), 120.0, places=6)
        # Never negative.
        self.assertGreaterEqual(sb._ayana_bala(const.SATURN, 23.0), 0.0)

    def test_vara_bala_only_weekday_lord(self):
        self.assertEqual(sb._vara_bala(const.MARS, const.MARS), 45.0)
        self.assertEqual(sb._vara_bala(const.MARS, const.SUN), 0.0)

    def test_hora_first_hour_is_weekday_lord(self):
        # At 6:00 (sunrise), the hora lord equals the weekday lord.
        self.assertEqual(sb._hora_lord(const.SUN, 6.0), const.SUN)
        # The next hora steps in Chaldean order: Sun → Venus.
        self.assertEqual(sb._hora_lord(const.SUN, 7.0), const.VENUS)


# --------------------------------------------------------------------- #
#   Cheshta Bala                                                        #
# --------------------------------------------------------------------- #


class CheshtaTests(unittest.TestCase):
    def test_sun_cheshta_equals_ayana(self):
        d = {"retro": False, "speed": 1.0, "decl": 0.0}
        self.assertEqual(sb._cheshta_bala(const.SUN, d, ayana=42.0, paksha=10.0), 42.0)

    def test_moon_cheshta_equals_paksha(self):
        d = {"retro": False, "speed": 13.0, "decl": 0.0}
        self.assertEqual(sb._cheshta_bala(const.MOON, d, ayana=42.0, paksha=33.0), 33.0)

    def test_retrograde_star_planet_is_maximal(self):
        d = {"retro": True, "speed": -0.1, "decl": 0.0}
        self.assertEqual(sb._cheshta_bala(const.MARS, d, ayana=0.0, paksha=0.0), 60.0)

    def test_direct_mean_speed_is_moderate(self):
        # Mars at ~0.7 × mean motion → Sama band (30).
        d = {"retro": False, "speed": sb._MEAN_MOTION[const.MARS] * 0.7, "decl": 0.0}
        self.assertEqual(sb._cheshta_bala(const.MARS, d, ayana=0.0, paksha=0.0), 30.0)


# --------------------------------------------------------------------- #
#   Drik Bala                                                           #
# --------------------------------------------------------------------- #


class DrikTests(unittest.TestCase):
    # Sentinel sign 1: a planet there casts no full aspect onto sign 0
    # (7th lands on sign 7; Saturn 3rd/10th on 3/10; Jupiter 5th/9th on
    # 5/9; Mars 4th/8th on 4/8 — none is 0), so only the deliberately
    # placed aspecting planet contributes.
    def test_benefic_seventh_aspect_is_positive(self):
        # Jupiter (benefic) opposite the Sun → +60 / 4 = +15.
        signs = {p: 1 for p in sb._CLASSICAL_PLANETS}
        signs[const.SUN] = 0
        signs[const.JUPITER] = 6
        self.assertEqual(sb._drik_bala(const.SUN, signs), 15.0)

    def test_malefic_seventh_aspect_is_negative(self):
        signs = {p: 1 for p in sb._CLASSICAL_PLANETS}
        signs[const.SUN] = 0
        signs[const.SATURN] = 6
        self.assertEqual(sb._drik_bala(const.SUN, signs), -15.0)

    def test_special_aspects(self):
        # Saturn's 3rd & 10th special aspects.
        self.assertTrue(sb._casts_full_aspect(const.SATURN, 0, 2))  # 3rd
        self.assertTrue(sb._casts_full_aspect(const.SATURN, 0, 9))  # 10th
        # Jupiter's 5th & 9th.
        self.assertTrue(sb._casts_full_aspect(const.JUPITER, 0, 4))
        self.assertTrue(sb._casts_full_aspect(const.JUPITER, 0, 8))
        # Mars' 4th & 8th.
        self.assertTrue(sb._casts_full_aspect(const.MARS, 0, 3))
        self.assertTrue(sb._casts_full_aspect(const.MARS, 0, 7))
        # A non-special planet only aspects the 7th.
        self.assertFalse(sb._casts_full_aspect(const.SUN, 0, 3))
        self.assertTrue(sb._casts_full_aspect(const.SUN, 0, 6))


if __name__ == "__main__":
    unittest.main()

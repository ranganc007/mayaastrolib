"""Tests for Ashtakavarga prastara, shodhana, and kakshya — Task 031."""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import ashtakavarga as av


def _all_at(sign_idx):
    return {c: sign_idx for c in av.ASHTAKAVARGA_CONTRIBUTORS}


class PrastaraTests(unittest.TestCase):
    def test_prastara_has_all_8_contributors(self):
        pr = av.bhinnashtakavarga_prastara(const.SUN, _all_at(3))
        self.assertEqual(set(pr.keys()), set(av.ASHTAKAVARGA_CONTRIBUTORS))

    def test_rows_are_zero_or_one(self):
        pr = av.bhinnashtakavarga_prastara(const.MOON, _all_at(0))
        for row in pr.values():
            self.assertEqual(len(row), 12)
            for v in row:
                self.assertIn(v, (0, 1))

    def test_sum_reproduces_bhinnashtakavarga(self):
        signs = {c: (i * 3) % 12 for i, c in enumerate(av.ASHTAKAVARGA_CONTRIBUTORS)}
        for planet in av.ASHTAKAVARGA_PLANETS:
            pr = av.bhinnashtakavarga_prastara(planet, signs)
            summed = [sum(pr[c][i] for c in pr) for i in range(12)]
            self.assertEqual(summed, av.bhinnashtakavarga(planet, signs), f"{planet}")

    def test_unknown_planet_raises(self):
        with self.assertRaises(ValueError):
            av.bhinnashtakavarga_prastara(const.RAHU, _all_at(0))


class TrikonaShodhanaTests(unittest.TestCase):
    def test_subtracts_min_from_each_trine(self):
        bav = [1, 2, 3, 0, 5, 6, 7, 8, 9, 4, 1, 2]
        out = av.trikona_shodhana(bav)
        # Group {0,4,8} = [1,5,9] → min 1 → [0,4,8]
        # Group {1,5,9} = [2,6,4] → min 2 → [0,4,2]
        # Group {2,6,10} = [3,7,1] → min 1 → [2,6,0]
        # Group {3,7,11} = [0,8,2] → min 0 → unchanged [0,8,2]
        self.assertEqual(out, [0, 0, 2, 0, 4, 4, 6, 8, 8, 2, 0, 2])

    def test_does_not_mutate_input(self):
        bav = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        copy = list(bav)
        av.trikona_shodhana(bav)
        self.assertEqual(bav, copy)

    def test_zero_min_leaves_trine_unchanged(self):
        bav = [0] * 12
        bav[0] = 0  # trine {0,4,8} has a zero → unchanged
        bav[4] = 5
        bav[8] = 7
        out = av.trikona_shodhana(bav)
        self.assertEqual([out[0], out[4], out[8]], [0, 5, 7])

    def test_result_never_exceeds_input(self):
        bav = [3, 5, 1, 4, 2, 6, 0, 7, 2, 1, 3, 4]
        out = av.trikona_shodhana(bav)
        for o, i in zip(out, bav, strict=True):
            self.assertLessEqual(o, i)


class EkadhipatyaShodhanaTests(unittest.TestCase):
    def test_both_occupied_unchanged(self):
        bav = list(range(12))
        # Aries(0)/Scorpio(7) are the first pair; mark both occupied.
        out = av.ekadhipatya_shodhana(bav, occupied_signs={0, 7})
        self.assertEqual(out[0], bav[0])
        self.assertEqual(out[7], bav[7])

    def test_neither_occupied_equal_values_become_zero(self):
        bav = [0] * 12
        bav[1] = bav[6] = 4  # Taurus/Libra pair, equal, neither occupied
        out = av.ekadhipatya_shodhana(bav, occupied_signs=set())
        self.assertEqual(out[1], 0)
        self.assertEqual(out[6], 0)

    def test_neither_occupied_unequal_values_become_smaller(self):
        bav = [0] * 12
        bav[2], bav[5] = 5, 3  # Gemini/Virgo pair, neither occupied
        out = av.ekadhipatya_shodhana(bav, occupied_signs=set())
        self.assertEqual(out[2], 3)
        self.assertEqual(out[5], 3)

    def test_one_occupied_higher_value_zeros_the_unoccupied(self):
        bav = [0] * 12
        bav[8], bav[11] = 6, 2  # Sag/Pisces pair; occupy Sag (higher)
        out = av.ekadhipatya_shodhana(bav, occupied_signs={8})
        self.assertEqual(out[8], 6)
        self.assertEqual(out[11], 0)

    def test_does_not_mutate_input(self):
        bav = list(range(12))
        copy = list(bav)
        av.ekadhipatya_shodhana(bav, occupied_signs={0})
        self.assertEqual(bav, copy)


class ShodhitaSavTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("1947/08/15", "00:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        self.chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        self.planet_signs = {
            p: int(self.chart.getObject(p).lon // 30) % 12 for p in av.ASHTAKAVARGA_PLANETS
        }
        self.lagna = int(self.chart.getAngle(const.ASC).lon // 30) % 12

    def test_reduced_sav_total_less_than_337(self):
        red = av.shodhita_sarvashtakavarga(self.planet_signs, self.lagna)
        self.assertLess(red["grand_total"], 337)
        self.assertEqual(red["grand_total"], sum(red["per_rasi"]))

    def test_reduced_never_exceeds_full(self):
        full = av.sarvashtakavarga(self.planet_signs, self.lagna)
        red = av.shodhita_sarvashtakavarga(self.planet_signs, self.lagna)
        for r, f in zip(red["per_rasi"], full["per_rasi"], strict=True):
            self.assertLessEqual(r, f)

    def test_by_planet_has_all_seven(self):
        red = av.shodhita_sarvashtakavarga(self.planet_signs, self.lagna)
        self.assertEqual(set(red["by_planet"].keys()), set(av.ASHTAKAVARGA_PLANETS))


class KakshyaTests(unittest.TestCase):
    def test_kakshya_order_within_a_sign(self):
        # 8 kakshyas of 3°45' each, in fixed order from 0°.
        expected = [
            (1.0, const.SATURN),
            (4.0, const.JUPITER),
            (8.0, const.MARS),
            (12.0, const.SUN),
            (16.0, const.VENUS),
            (20.0, const.MERCURY),
            (24.0, const.MOON),
            (28.0, av.ASCENDANT),
        ]
        for deg, lord in expected:
            self.assertEqual(av.kakshya_of(deg), lord, f"{deg}°")

    def test_kakshya_repeats_each_sign(self):
        # 0° Aries and 30° Taurus (= sign boundary; 30° → 0° of next sign)
        # both start with the Saturn kakshya.
        self.assertEqual(av.kakshya_of(0.0), const.SATURN)
        self.assertEqual(av.kakshya_of(30.0), const.SATURN)
        self.assertEqual(av.kakshya_of(60.5), const.SATURN)

    def test_kakshya_transit_active(self):
        # Build a prastara where the Saturn contributor places a bindu
        # in sign 3 for the Sun. A transit at 1° of sign 3 (= 91°) is in
        # the Saturn kakshya → active.
        signs = _all_at(0)
        pr = av.bhinnashtakavarga_prastara(const.SUN, signs)
        # Find a sign where the Saturn-contributor row has a 1.
        saturn_row = pr[const.SATURN]
        active_sign = next(i for i, v in enumerate(saturn_row) if v == 1)
        # A longitude at ~1° of that sign is in the Saturn kakshya (0°-3°45').
        transit_lon = active_sign * 30.0 + 1.0
        lord, active = av.kakshya_transit_active(pr, transit_lon)
        self.assertEqual(lord, const.SATURN)
        self.assertTrue(active)
        # A sign where the Saturn-contributor row is 0 → not active.
        inactive_sign = next(i for i, v in enumerate(saturn_row) if v == 0)
        _l, a2 = av.kakshya_transit_active(pr, inactive_sign * 30.0 + 1.0)
        self.assertFalse(a2)


if __name__ == "__main__":
    unittest.main()


class ShodhanaVariantTests(unittest.TestCase):
    def test_trikona_zero_if_any_zero_variant(self):
        # Trine {3,7,11} = [0,8,2]: "subtract_min" leaves it unchanged
        # (min 0), "zero_if_any_zero" zeroes the whole trine.
        bav = [1, 2, 3, 0, 5, 6, 7, 8, 9, 4, 1, 2]
        sub = av.trikona_shodhana(bav, variant="subtract_min")
        zero = av.trikona_shodhana(bav, variant="zero_if_any_zero")
        self.assertEqual([sub[3], sub[7], sub[11]], [0, 8, 2])
        self.assertEqual([zero[3], zero[7], zero[11]], [0, 0, 0])
        # The trines without a zero behave the same under both variants.
        self.assertEqual([sub[0], sub[4], sub[8]], [zero[0], zero[4], zero[8]])

    def test_trikona_unknown_variant_raises(self):
        with self.assertRaises(ValueError):
            av.trikona_shodhana([0] * 12, variant="bogus")

    def test_ekadhipatya_zero_unoccupied_variant(self):
        # Sag/Pisces pair, Sag occupied with the *lower* value (2 vs 6).
        bav = [0] * 12
        bav[8], bav[11] = 2, 6  # Sag=2, Pisces=6
        default = av.ekadhipatya_shodhana(bav, occupied_signs={8})
        strict = av.ekadhipatya_shodhana(bav, occupied_signs={8}, variant="zero_unoccupied")
        # default: occ value (2) < unocc value (6) → both become min → 2/2.
        self.assertEqual([default[8], default[11]], [2, 2])
        # zero_unoccupied: the unoccupied sign is zeroed regardless → 2/0.
        self.assertEqual([strict[8], strict[11]], [2, 0])

    def test_ekadhipatya_unknown_variant_raises(self):
        with self.assertRaises(ValueError):
            av.ekadhipatya_shodhana([0] * 12, occupied_signs=set(), variant="bogus")

    def test_shodhita_sav_threads_variants(self):
        date = Datetime("1947/08/15", "00:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        planet_signs = {p: int(chart.getObject(p).lon // 30) % 12 for p in av.ASHTAKAVARGA_PLANETS}
        lagna = int(chart.getAngle(const.ASC).lon // 30) % 12
        default_sav = av.shodhita_sarvashtakavarga(planet_signs, lagna)
        strict_sav = av.shodhita_sarvashtakavarga(
            planet_signs,
            lagna,
            trikona_variant="zero_if_any_zero",
            ekadhipatya_variant="zero_unoccupied",
        )
        # The strict combination reduces at least as aggressively.
        self.assertLessEqual(strict_sav["grand_total"], default_sav["grand_total"])
        for s, d in zip(strict_sav["per_rasi"], default_sav["per_rasi"], strict=True):
            self.assertLessEqual(s, d)

"""Tests for Vedic divisional charts — Task 019."""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import divisional as div


class SignIndexHelperTests(unittest.TestCase):
    def test_aries_zero_to_30(self):
        for lon in [0.0, 15.0, 29.99]:
            self.assertEqual(div._sign_index(lon), div.ARIES)

    def test_taurus_30_to_60(self):
        for lon in [30.0, 45.0, 59.99]:
            self.assertEqual(div._sign_index(lon), div.TAURUS)

    def test_pisces_wraps(self):
        self.assertEqual(div._sign_index(359.99), div.PISCES)
        self.assertEqual(div._sign_index(360.0), div.ARIES)

    def test_deg_in_sign_at_taurus(self):
        # 37° = 7° within Taurus.
        self.assertAlmostEqual(div._deg_in_sign(37.0), 7.0)


class HoraTests(unittest.TestCase):
    """D2 — odd signs split Leo/Cancer; even signs split Cancer/Leo."""

    def test_aries_first_half_is_leo(self):
        self.assertEqual(div.hora(7.0), div.LEO)

    def test_aries_second_half_is_cancer(self):
        self.assertEqual(div.hora(22.0), div.CANCER)

    def test_taurus_first_half_is_cancer(self):
        self.assertEqual(div.hora(37.0), div.CANCER)

    def test_taurus_second_half_is_leo(self):
        self.assertEqual(div.hora(52.0), div.LEO)


class DrekkanaTests(unittest.TestCase):
    """D3 — first 10° same sign, second 10° 5th sign, third 10° 9th sign."""

    def test_aries_first_drekkana(self):
        self.assertEqual(div.drekkana(5.0), div.ARIES)

    def test_aries_second_drekkana_is_leo(self):
        self.assertEqual(div.drekkana(15.0), div.LEO)

    def test_aries_third_drekkana_is_sagittarius(self):
        self.assertEqual(div.drekkana(25.0), div.SAGITTARIUS)


class NavamsaTests(unittest.TestCase):
    """D9 — verify at every navamsa cusp of Aries plus a movable/fixed/dual rotation."""

    def test_aries_navamsa_progression(self):
        # Aries is movable; D9 starts from Aries and counts forward by 1.
        cases = [
            (0.5, div.ARIES),
            (3.5, div.TAURUS),
            (6.7, div.GEMINI),
            (10.0, div.CANCER),
            (13.5, div.LEO),
            (16.7, div.VIRGO),
            (20.0, div.LIBRA),
            (23.5, div.SCORPIO),
            (27.0, div.SAGITTARIUS),
        ]
        for lon, expected in cases:
            self.assertEqual(div.navamsa(lon), expected, f"lon={lon}")

    def test_taurus_navamsa_starts_from_capricorn(self):
        # Taurus is fixed; D9 starts from the 9th sign (Capricorn).
        self.assertEqual(div.navamsa(30.5), div.CAPRICORN)

    def test_gemini_navamsa_starts_from_libra(self):
        # Gemini is dual; D9 starts from the 5th sign (Libra).
        self.assertEqual(div.navamsa(60.5), div.LIBRA)


class TrimsamsaTests(unittest.TestCase):
    """D30 — unequal segments by sign parity. BPHS 6.29-32."""

    def test_aries_odd_segments(self):
        # Odd sign: Mars(0-5), Saturn(5-10), Jupiter(10-18), Mercury(18-25), Venus(25-30).
        self.assertEqual(div.trimsamsa(2.5), div.ARIES)
        self.assertEqual(div.trimsamsa(7.5), div.AQUARIUS)
        self.assertEqual(div.trimsamsa(14.0), div.SAGITTARIUS)
        self.assertEqual(div.trimsamsa(22.0), div.GEMINI)
        self.assertEqual(div.trimsamsa(27.0), div.LIBRA)

    def test_taurus_even_segments(self):
        # Even sign: Venus(0-5), Mercury(5-12), Jupiter(12-20), Saturn(20-25), Mars(25-30).
        self.assertEqual(div.trimsamsa(32.5), div.TAURUS)
        self.assertEqual(div.trimsamsa(38.0), div.VIRGO)
        self.assertEqual(div.trimsamsa(45.0), div.PISCES)
        self.assertEqual(div.trimsamsa(52.0), div.CAPRICORN)
        self.assertEqual(div.trimsamsa(57.0), div.SCORPIO)


class DvadasamsaTests(unittest.TestCase):
    """D12 — each sign divided into 12 parts of 2°30', counting from the sign itself."""

    def test_first_segment_of_aries(self):
        self.assertEqual(div.dvadasamsa(1.0), div.ARIES)

    def test_second_segment_of_aries(self):
        # 2°30' to 5° → Taurus.
        self.assertEqual(div.dvadasamsa(3.0), div.TAURUS)

    def test_last_segment_of_aries(self):
        # 27°30' to 30° → Pisces (12th from Aries).
        self.assertEqual(div.dvadasamsa(28.0), div.PISCES)


class ShastiamsaTests(unittest.TestCase):
    """D60 — odd signs count from the sign itself; even from the 12th from sign."""

    def test_odd_sign_first_shastiamsa_is_sign(self):
        self.assertEqual(div.shastiamsa(0.25), div.ARIES)

    def test_even_sign_first_shastiamsa_is_one_back(self):
        # Taurus is even → first shastiamsa is Aries (12th from Taurus).
        self.assertEqual(div.shastiamsa(30.25), div.ARIES)


class AllVargasTests(unittest.TestCase):
    """End-to-end with a real chart — verifies the chart wiring."""

    def test_all_vargas_returns_all_16(self):
        date = Datetime("1947/08/15", "00:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        result = div.all_vargas(chart)
        self.assertEqual(set(result.keys()), set(div.VARGA_NAMES))

    def test_d1_matches_chart_sign(self):
        date = Datetime("2024/06/15", "12:00", "+00:00")
        pos = GeoPos("28n36", "77e12")
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        result = div.all_vargas(chart)
        sun_sign = int(chart.getObject(const.SUN).lon // 30) % 12
        self.assertEqual(result["D1"][const.SUN], sun_sign)

    def test_tropical_and_sidereal_chart_agree(self):
        """all_vargas(tropical, ayanamsa=lahiri) ≡ all_vargas(sidereal)."""
        date = Datetime("2024/06/15", "12:00", "+00:00")
        pos = GeoPos("28n36", "77e12")
        tropical = Chart(date, pos)
        sidereal = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        r1 = div.all_vargas(tropical)
        r2 = div.all_vargas(sidereal)
        for varga in div.VARGA_NAMES:
            for planet in r1[varga]:
                self.assertEqual(
                    r1[varga][planet],
                    r2[varga][planet],
                    f"{varga} disagreement for {planet}",
                )

    def test_sign_idx_in_valid_range(self):
        date = Datetime("2024/06/15", "12:00", "+00:00")
        pos = GeoPos("28n36", "77e12")
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        result = div.all_vargas(chart)
        for varga in div.VARGA_NAMES:
            for planet, sign_idx in result[varga].items():
                self.assertTrue(
                    0 <= sign_idx <= 11,
                    f"{varga} {planet} sign_idx={sign_idx} out of range",
                )


if __name__ == "__main__":
    unittest.main()

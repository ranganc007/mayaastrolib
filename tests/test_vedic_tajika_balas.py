"""Tests for Tajika Muntha, Lord of Year, and Sahams — Task 024b."""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import tajika


class _Base(unittest.TestCase):
    def setUp(self):
        self.date = Datetime("1980/06/15", "14:30", "+05:30")
        self.pos = GeoPos("28n36", "77e12")
        self.natal = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)
        self.vp = tajika.varshapravesh(self.natal, 2024)
        self.annual = Chart(self.vp, self.pos, zodiac=const.ZODIAC_SIDEREAL)


class MunthaTests(_Base):
    def test_muntha_at_birth_year_is_natal_lagna_sign(self):
        natal_lagna = int(self.natal.getAngle(const.ASC).lon // 30) % 12
        m = tajika.muntha(self.natal, 1980)
        self.assertEqual(m["sign_idx"], natal_lagna)
        self.assertEqual(m["sign"], const.LIST_SIGNS[natal_lagna])
        self.assertEqual(m["lord"], tajika._SIGN_LORDS[natal_lagna])

    def test_muntha_advances_one_sign_per_year(self):
        m_birth = tajika.muntha(self.natal, 1980)
        m_plus3 = tajika.muntha(self.natal, 1983)
        self.assertEqual((m_plus3["sign_idx"] - m_birth["sign_idx"]) % 12, 3)

    def test_muntha_44_years_later(self):
        m_birth = tajika.muntha(self.natal, 1980)
        m_2024 = tajika.muntha(self.natal, 2024)
        self.assertEqual((m_2024["sign_idx"] - m_birth["sign_idx"]) % 12, 44 % 12)

    def test_muntha_lord_consistent(self):
        m = tajika.muntha(self.natal, 2024)
        self.assertEqual(m["lord"], tajika._SIGN_LORDS[m["sign_idx"]])


class LordOfYearTests(_Base):
    def test_five_candidates(self):
        cands = tajika.lord_of_year_candidates(self.annual, self.natal, 2024)
        self.assertEqual(len(cands), 5)
        labels = [c[0] for c in cands]
        self.assertEqual(labels, ["muntha", "annual_lagna", "sun_sign", "natal_lagna", "trirashi"])
        # Each candidate is a valid planet ID.
        for _label, planet in cands:
            self.assertIn(planet, tajika._SIGN_LORDS)

    def test_lord_of_year_is_one_of_the_candidates(self):
        cands = tajika.lord_of_year_candidates(self.annual, self.natal, 2024)
        loy = tajika.lord_of_year(self.annual, self.natal, 2024)
        self.assertIn(loy, cands)

    def test_lord_of_year_returns_label_and_planet(self):
        loy = tajika.lord_of_year(self.annual, self.natal, 2024)
        self.assertEqual(len(loy), 2)
        label, planet = loy
        self.assertIsInstance(label, str)
        self.assertIn(planet, tajika._SIGN_LORDS)

    def test_trirashi_pati_helper(self):
        # Day chart: 1st 10° of a sign → that sign's lord; 2nd → 5th sign's
        # lord; 3rd → 9th sign's lord. Sign 0 (Aries): 5th = Leo → Sun;
        # 9th = Sagittarius → Jupiter.
        self.assertEqual(
            tajika._trirashi_pati(5.0, is_diurnal=True), const.MARS
        )  # 1st part of Aries
        self.assertEqual(tajika._trirashi_pati(15.0, is_diurnal=True), const.SUN)  # 2nd part → Leo
        self.assertEqual(
            tajika._trirashi_pati(25.0, is_diurnal=True), const.JUPITER
        )  # 3rd part → Sag
        # Night reverses the order of the three parts.
        self.assertEqual(tajika._trirashi_pati(5.0, is_diurnal=False), const.JUPITER)
        self.assertEqual(tajika._trirashi_pati(25.0, is_diurnal=False), const.MARS)


class SahamsTests(_Base):
    def test_returns_the_full_curated_set(self):
        s = tajika.sahams(self.annual)
        expected = {
            tajika.SAHAM_PUNYA,
            tajika.SAHAM_VIDYA,
            tajika.SAHAM_YASAS,
            tajika.SAHAM_KARMA,
            tajika.SAHAM_PITRI,
            tajika.SAHAM_MATRI,
            tajika.SAHAM_BHRATRI,
            tajika.SAHAM_PUTRA,
            tajika.SAHAM_KALATRA,
            tajika.SAHAM_JEEVA,
            tajika.SAHAM_VIVAHA,
            tajika.SAHAM_VYAPARA,
            tajika.SAHAM_ROGA,
            tajika.SAHAM_BANDHU,
        }
        self.assertEqual(set(s.keys()), expected)
        self.assertEqual(len(s), 14)

    def test_yasas_uses_punya_saham(self):
        # Yasas (day) = Jupiter − Punya-Saham + Asc, so it must reference
        # the chart's Punya value, not the Sun.
        s = tajika.sahams(self.annual)
        asc = self.annual.getAngle(const.ASC).lon % 360.0
        jup = self.annual.getObject(const.JUPITER).lon % 360.0
        if self.annual.isDiurnal():
            expected = (jup - s[tajika.SAHAM_PUNYA] + asc) % 360.0
        else:
            expected = (s[tajika.SAHAM_PUNYA] - jup + asc) % 360.0
        self.assertAlmostEqual(s[tajika.SAHAM_YASAS], expected, places=4)

    def test_all_in_range(self):
        for v in tajika.sahams(self.annual).values():
            self.assertTrue(0.0 <= v < 360.0)

    def test_punya_and_vidya_are_reverses(self):
        # Punya = Moon − Sun + Asc, Vidya = Sun − Moon + Asc → sum ≡ 2·Asc.
        s = tajika.sahams(self.annual)
        asc = self.annual.getAngle(const.ASC).lon % 360.0
        self.assertAlmostEqual(
            (s[tajika.SAHAM_PUNYA] + s[tajika.SAHAM_VIDYA]) % 360.0, (2 * asc) % 360.0, places=4
        )

    def test_punya_matches_formula_for_diurnal_chart(self):
        # 1980-06-15 14:30 IST in Delhi is a daytime birth, so the
        # varshapravesh chart… actually the varshapravesh moment may be at
        # any hour. Compute the expected Punya from the chart's own
        # diurnal flag and verify our function agrees.
        asc = self.annual.getAngle(const.ASC).lon % 360.0
        sun = self.annual.getObject(const.SUN).lon % 360.0
        moon = self.annual.getObject(const.MOON).lon % 360.0
        if self.annual.isDiurnal():
            expected = (moon - sun + asc) % 360.0
        else:
            expected = (sun - moon + asc) % 360.0
        self.assertAlmostEqual(tajika.sahams(self.annual)[tajika.SAHAM_PUNYA], expected, places=4)

    def test_tropical_annual_chart_with_ayanamsa_agrees(self):
        tropical_annual = Chart(self.vp, self.pos)  # tropical
        st = tajika.sahams(tropical_annual, ayanamsa=const.AYANAMSA_LAHIRI)
        ss = tajika.sahams(self.annual)
        for name in st:
            self.assertAlmostEqual(st[name], ss[name], places=2)


if __name__ == "__main__":
    unittest.main()

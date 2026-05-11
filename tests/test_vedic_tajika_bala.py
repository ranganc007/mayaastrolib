"""Tests for Tajika Harsha Bala, Panchavargiya Bala, and aspects — Task 029."""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import tajika, tajika_aspects, tajika_bala


class _Base(unittest.TestCase):
    def setUp(self):
        self.date = Datetime("1980/06/15", "14:30", "+05:30")
        self.pos = GeoPos("28n36", "77e12")
        self.natal = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)
        self.vp = tajika.varshapravesh(self.natal, 2024)
        self.annual = Chart(self.vp, self.pos, zodiac=const.ZODIAC_SIDEREAL)


class HarshaBalaTests(_Base):
    def test_returns_all_seven_planets(self):
        hb = tajika_bala.harsha_bala(self.annual)
        self.assertEqual(set(hb.keys()), set(tajika_bala._CLASSICAL_PLANETS))

    def test_each_total_is_sum_of_components_and_in_range(self):
        for p, d in tajika_bala.harsha_bala(self.annual).items():
            self.assertEqual(d["total"], sum(d["components"].values()))
            self.assertTrue(0 <= d["total"] <= 25, f"{p}: {d['total']}")
            for v in d["components"].values():
                self.assertIn(v, (0, 5))

    def test_components_present(self):
        comps = tajika_bala.harsha_bala(self.annual)[const.SUN]["components"]
        self.assertEqual(set(comps.keys()), {"hemisphere", "gender", "dignity", "decanate", "joy"})

    def test_neutral_planets_always_get_gender_point(self):
        hb = tajika_bala.harsha_bala(self.annual)
        # Mercury and Saturn are neutral-gender → gender component is always 5.
        self.assertEqual(hb[const.MERCURY]["components"]["gender"], 5)
        self.assertEqual(hb[const.SATURN]["components"]["gender"], 5)

    def test_joy_house_component(self):
        # Construct a chart, find a planet in its joy house, verify the
        # joy component fires. The Sun joys in the 9th. Build a chart and
        # check whichever planets happen to be in their joy house.
        hb = tajika_bala.harsha_bala(self.annual)
        joys = {
            const.SUN: 9,
            const.MOON: 3,
            const.MARS: 6,
            const.MERCURY: 1,
            const.JUPITER: 11,
            const.VENUS: 5,
            const.SATURN: 12,
        }
        # Recompute houses to cross-check.
        asc_sign = int(self.annual.getAngle(const.ASC).lon // 30) % 12
        for p, joy_house in joys.items():
            sign = int(self.annual.getObject(p).lon // 30) % 12
            house = (sign - asc_sign) % 12 + 1
            expected = 5 if house == joy_house else 0
            self.assertEqual(hb[p]["components"]["joy"], expected, f"{p}")


class PanchavargiyaBalaTests(_Base):
    def test_returns_all_seven_planets(self):
        pv = tajika_bala.panchavargiya_bala(self.annual)
        self.assertEqual(set(pv.keys()), set(tajika_bala._CLASSICAL_PLANETS))

    def test_each_total_is_sum_of_components(self):
        for d in tajika_bala.panchavargiya_bala(self.annual).values():
            self.assertAlmostEqual(d["total"], sum(d["components"].values()), places=6)

    def test_components_present(self):
        comps = tajika_bala.panchavargiya_bala(self.annual)[const.SUN]["components"]
        self.assertEqual(set(comps.keys()), {"kshetra", "uchcha", "hadda", "drekkana", "navamsa"})

    def test_uchcha_bala_max_at_exaltation_point(self):
        # Build a chart where, say, the Sun is near 10° Aries (its
        # exaltation point) and verify uchcha bala ≈ 20. We can't force
        # a planet's position, so instead test the internal _uchcha
        # helper directly.
        # Sun exalts at 10° Aries (sign 0, deg 10).
        self.assertAlmostEqual(tajika_bala._uchcha(const.SUN, 0, 10.0), 20.0, places=6)
        # At the debilitation point (10° Libra = sign 6, deg 10): ≈ 0.
        self.assertAlmostEqual(tajika_bala._uchcha(const.SUN, 6, 10.0), 0.0, places=6)
        # Halfway: ≈ 10.
        # 90° from the exaltation point: sign 3, deg 10 (10° Cancer).
        self.assertAlmostEqual(tajika_bala._uchcha(const.SUN, 3, 10.0), 10.0, places=4)

    def test_kshetra_bala_own_sign_is_30(self):
        # Sun in Leo (sign 4) — its own sign.
        self.assertEqual(tajika_bala._kshetra(const.SUN, 4), 30.0)
        # Sun in Libra (sign 6) — its debilitation sign.
        self.assertEqual(tajika_bala._kshetra(const.SUN, 6), 0.0)


class TajikaAspectsTests(_Base):
    def test_returns_a_list_of_tajika_aspects(self):
        aspects = tajika_aspects.tajika_aspects(self.annual)
        self.assertIsInstance(aspects, list)
        for a in aspects:
            self.assertIn(
                a.kind, (tajika_aspects.ITHASALA, tajika_aspects.ISHARAFA, tajika_aspects.NAKTA)
            )

    def test_ithasala_isharafa_are_2_planet_nakta_is_3(self):
        for a in tajika_aspects.tajika_aspects(self.annual):
            if a.kind == tajika_aspects.NAKTA:
                self.assertEqual(len(a.planets), 3)
            else:
                self.assertEqual(len(a.planets), 2)

    def test_2_planet_aspects_are_within_orb(self):
        for a in tajika_aspects.tajika_aspects(self.annual):
            if a.kind in (tajika_aspects.ITHASALA, tajika_aspects.ISHARAFA):
                self.assertLessEqual(a.separation, a.orb)
                self.assertIn(a.aspect_angle, tajika_aspects.ASPECT_ANGLES)

    def test_raises_on_symbolic_chart(self):
        prof = self.natal.profected(years=5)
        with self.assertRaises(ValueError):
            tajika_aspects.tajika_aspects(prof)

    def test_pair_orb_is_average_of_deeptamshas(self):
        # Sun (15) + Mars (8) → 11.5.
        self.assertAlmostEqual(tajika_aspects._pair_orb(const.SUN, const.MARS), 11.5, places=6)

    def test_closest_aspect(self):
        # 58° apart → nearest Ptolemaic aspect is the 60° sextile, 2° off.
        ang, dist = tajika_aspects._closest_aspect(0.0, 58.0)
        self.assertEqual(ang, 60.0)
        self.assertAlmostEqual(dist, 2.0, places=6)
        # 92° apart → square, 2° off.
        ang2, dist2 = tajika_aspects._closest_aspect(10.0, 102.0)
        self.assertEqual(ang2, 90.0)
        self.assertAlmostEqual(dist2, 2.0, places=6)


if __name__ == "__main__":
    unittest.main()

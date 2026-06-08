"""Tests for the KP horary chart with house cusps — Task 042."""

import unittest

from mayaastrolib import const
from mayaastrolib.vedic import kp


class KpHoraryChartTests(unittest.TestCase):
    def test_returns_twelve_houses(self):
        chart = kp.kp_horary_chart(1)
        self.assertEqual(len(chart["houses"]), 12)

    def test_house1_equals_lagna(self):
        chart = kp.kp_horary_chart(120)
        self.assertAlmostEqual(chart["houses"][0]["longitude"], chart["lagna_longitude"], places=9)
        self.assertEqual(chart["lagna_longitude"], kp.prashna_to_longitude(120))

    def test_cusps_are_thirty_degrees_apart(self):
        chart = kp.kp_horary_chart(200)
        lons = [h["longitude"] for h in chart["houses"]]
        for i in range(12):
            expected = (lons[0] + i * 30.0) % 360.0
            self.assertAlmostEqual(lons[i], expected, places=9)

    def test_cusp_numbers_are_one_to_twelve(self):
        chart = kp.kp_horary_chart(50)
        self.assertEqual([h["cusp"] for h in chart["houses"]], list(range(1, 13)))

    def test_each_cusp_has_full_chain(self):
        chart = kp.kp_horary_chart(75)
        for h in chart["houses"]:
            for key in (
                "longitude",
                "sign",
                "sign_lord",
                "nakshatra",
                "star_lord",
                "pada",
                "sub_lord",
                "sub_sub_lord",
                "cusp",
            ):
                self.assertIn(key, h)

    def test_prashna_preserved(self):
        self.assertEqual(kp.kp_horary_chart(7)["prashna"], 7)

    def test_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            kp.kp_horary_chart(0)
        with self.assertRaises(ValueError):
            kp.kp_horary_chart(250)

    def test_opposite_cusps_are_180_apart(self):
        chart = kp.kp_horary_chart(33)
        h1 = chart["houses"][0]["longitude"]
        h7 = chart["houses"][6]["longitude"]
        diff = (h7 - h1) % 360.0
        self.assertAlmostEqual(diff, 180.0, places=9)

    def test_sign_lords_are_valid_planets(self):
        chart = kp.kp_horary_chart(140)
        valid = {
            const.SUN,
            const.MOON,
            const.MARS,
            const.MERCURY,
            const.JUPITER,
            const.VENUS,
            const.SATURN,
        }
        for h in chart["houses"]:
            self.assertIn(h["sign_lord"], valid)


if __name__ == "__main__":
    unittest.main()

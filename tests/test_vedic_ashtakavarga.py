"""Tests for Vedic Ashtakavarga — Task 021."""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import ashtakavarga as av


class TableInvariantTests(unittest.TestCase):
    """The canonical BPHS Ch. 66 tables have fixed per-planet totals."""

    def test_per_planet_totals(self):
        expected = {
            const.SUN: 48,
            const.MOON: 49,
            const.MARS: 39,
            const.MERCURY: 54,
            const.JUPITER: 56,
            const.VENUS: 52,
            const.SATURN: 39,
        }
        for planet, total in expected.items():
            actual = sum(len(v) for v in av.ASHTAKAVARGA_TABLES[planet].values())
            self.assertEqual(actual, total, f"{planet} BAV table total")

    def test_seven_totals_sum_to_337(self):
        grand = sum(
            sum(len(v) for v in av.ASHTAKAVARGA_TABLES[p].values()) for p in av.ASHTAKAVARGA_PLANETS
        )
        self.assertEqual(grand, 337)

    def test_every_table_has_all_8_contributors(self):
        for planet, table in av.ASHTAKAVARGA_TABLES.items():
            self.assertEqual(
                set(table.keys()),
                set(av.ASHTAKAVARGA_CONTRIBUTORS),
                f"{planet} table is missing a contributor",
            )

    def test_house_numbers_in_1_to_12(self):
        for planet, table in av.ASHTAKAVARGA_TABLES.items():
            for contributor, houses in table.items():
                for h in houses:
                    self.assertTrue(1 <= h <= 12, f"{planet}/{contributor}: house {h}")


class BhinnashtakavargaTests(unittest.TestCase):
    """A BAV is a 12-cell histogram of a fixed number of bindus."""

    def _all_at(self, sign_idx):
        return {c: sign_idx for c in av.ASHTAKAVARGA_CONTRIBUTORS}

    def test_bav_has_12_cells(self):
        bav = av.bhinnashtakavarga(const.SUN, self._all_at(0))
        self.assertEqual(len(bav), 12)

    def test_bav_sums_to_planet_total(self):
        for planet in av.ASHTAKAVARGA_PLANETS:
            bav = av.bhinnashtakavarga(planet, self._all_at(3))
            expected = sum(len(v) for v in av.ASHTAKAVARGA_TABLES[planet].values())
            self.assertEqual(sum(bav), expected, f"{planet}")

    def test_bav_shifts_with_positions(self):
        # Same configuration shifted by one sign → BAV rotated by one cell.
        bav_at_0 = av.bhinnashtakavarga(const.SUN, self._all_at(0))
        bav_at_1 = av.bhinnashtakavarga(const.SUN, self._all_at(1))
        rotated = bav_at_0[-1:] + bav_at_0[:-1]
        self.assertEqual(bav_at_1, rotated)

    def test_hand_computed_sun_cell_all_bodies_at_aries(self):
        # All 8 bodies at Aries (sign 0). For each contributor C, the Sun's
        # table houses h land in sign (0 + h - 1) % 12. Since all C are at
        # sign 0, cell value at sign s = number of (C, h) pairs with
        # (h - 1) % 12 == s, summed over all 8 contributors.
        bav = av.bhinnashtakavarga(const.SUN, self._all_at(0))
        # Count manually for cell 0 (h == 1) across all 8 contributors:
        # how many tables have house 1?
        expected_cell_0 = sum(
            1 for houses in av.ASHTAKAVARGA_TABLES[const.SUN].values() if 1 in houses
        )
        self.assertEqual(bav[0], expected_cell_0)

    def test_unknown_planet_raises(self):
        with self.assertRaises(ValueError):
            av.bhinnashtakavarga(const.RAHU, self._all_at(0))

    def test_missing_contributor_raises(self):
        partial = {const.SUN: 0, const.MOON: 0}
        with self.assertRaises(ValueError):
            av.bhinnashtakavarga(const.SUN, partial)


class SarvashtakavargaTests(unittest.TestCase):
    def test_grand_total_is_337(self):
        planet_signs = {p: i % 12 for i, p in enumerate(av.ASHTAKAVARGA_PLANETS)}
        result = av.sarvashtakavarga(planet_signs, lagna_sign=5)
        self.assertEqual(result["grand_total"], 337)

    def test_per_rasi_sums_to_grand_total(self):
        planet_signs = {p: 0 for p in av.ASHTAKAVARGA_PLANETS}
        result = av.sarvashtakavarga(planet_signs, lagna_sign=0)
        self.assertEqual(sum(result["per_rasi"]), result["grand_total"])

    def test_by_planet_has_all_7(self):
        planet_signs = {p: 0 for p in av.ASHTAKAVARGA_PLANETS}
        result = av.sarvashtakavarga(planet_signs, lagna_sign=0)
        self.assertEqual(set(result["by_planet"].keys()), set(av.ASHTAKAVARGA_PLANETS))

    def test_grand_total_invariant_for_random_positions(self):
        # Any chart configuration must produce SAV grand total 337.
        for lagna in range(12):
            planet_signs = {p: (i * 5 + lagna) % 12 for i, p in enumerate(av.ASHTAKAVARGA_PLANETS)}
            result = av.sarvashtakavarga(planet_signs, lagna_sign=lagna)
            self.assertEqual(result["grand_total"], 337, f"lagna={lagna}")


class ChartLevelTests(unittest.TestCase):
    def test_ashtakavarga_on_sidereal_chart(self):
        date = Datetime("1947/08/15", "00:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        result = av.ashtakavarga(chart)
        self.assertEqual(result["grand_total"], 337)
        self.assertEqual(len(result["per_rasi"]), 12)

    def test_tropical_and_sidereal_chart_agree(self):
        date = Datetime("1947/08/15", "00:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        tropical = Chart(date, pos)
        sidereal = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        rt = av.ashtakavarga(tropical)
        rs = av.ashtakavarga(sidereal)
        # The per-rasi distribution should match (signs are identical
        # under either zodiac path once ayanamsa is applied).
        self.assertEqual(rt["per_rasi"], rs["per_rasi"])


if __name__ == "__main__":
    unittest.main()

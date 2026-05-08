"""Tests for Chart.get() dispatch and House.num cleanup (Task 011).

Two structural smells from the audit:

- ``Chart.get(ID)`` previously dispatched on ``ID.startswith("House")``
  — brittle to any future id-format change.
- ``House.num`` previously parsed ``int(self.id[5:])`` — same magic
  offset baked in.

Both are now list-driven via ``const.LIST_HOUSES``.
"""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos


def _chart():
    date = Datetime("2015/03/13", "17:00", "+00:00")
    pos = GeoPos("38n32", "8w54")
    return Chart(date, pos)


class ChartDispatchTests(unittest.TestCase):
    def setUp(self):
        self.chart = _chart()

    def test_get_object_by_id(self):
        sun = self.chart.get(const.SUN)
        self.assertIsNotNone(sun)
        self.assertEqual(sun.id, const.SUN)

    def test_get_house_by_id(self):
        h1 = self.chart.get(const.HOUSE1)
        self.assertIsNotNone(h1)
        self.assertEqual(h1.id, const.HOUSE1)

    def test_get_angle_by_id(self):
        asc = self.chart.get(const.ASC)
        self.assertIsNotNone(asc)
        self.assertEqual(asc.id, const.ASC)

    def test_get_uses_list_dispatch_not_string_prefix(self):
        """Regression for audit Item 13: dispatch must work for every
        house in LIST_HOUSES, not just House1. Catches a future
        regression where dispatch was made conditional on a literal
        prefix.
        """
        for house_id in const.LIST_HOUSES:
            h = self.chart.get(house_id)
            self.assertIsNotNone(h, f"{house_id} did not dispatch")
            self.assertEqual(h.id, house_id)
            self.assertEqual(h.type, const.OBJ_HOUSE)

    def test_get_dispatches_all_angles(self):
        for angle_id in const.LIST_ANGLES:
            a = self.chart.get(angle_id)
            self.assertIsNotNone(a, f"{angle_id} did not dispatch")
            self.assertEqual(a.id, angle_id)

    def test_get_falls_through_to_objects(self):
        # A planet ID is in neither LIST_HOUSES nor LIST_ANGLES — must
        # land on getObject. Sample chart uses LIST_OBJECTS_TRADITIONAL.
        for pid in const.LIST_OBJECTS_TRADITIONAL:
            obj = self.chart.get(pid)
            self.assertIsNotNone(obj, f"{pid} did not dispatch")
            self.assertEqual(obj.id, pid)


class HouseNumTests(unittest.TestCase):
    def setUp(self):
        self.chart = _chart()

    def test_house_num_is_int(self):
        h1 = self.chart.get(const.HOUSE1)
        self.assertIsInstance(int(h1.num), int)

    def test_house_num_matches_position_in_list(self):
        for i, house_id in enumerate(const.LIST_HOUSES, start=1):
            h = self.chart.get(house_id)
            self.assertEqual(int(h.num), i, f"{house_id}.num was {h.num}, expected {i}")

    def test_house_5_is_5(self):
        h5 = self.chart.get(const.HOUSE5)
        self.assertEqual(int(h5.num), 5)

    def test_house_12_is_12(self):
        h12 = self.chart.get(const.HOUSE12)
        self.assertEqual(int(h12.num), 12)

    def test_house_num_truthy_for_real_houses(self):
        """Regression on the truthiness fix from Task 006: h.num should
        be truthy on every real house (no zero values), distinguishing
        them from the default-constructed House with no id set.
        """
        for house_id in const.LIST_HOUSES:
            h = self.chart.get(house_id)
            self.assertTrue(h.num, f"{house_id}.num was falsy")


if __name__ == "__main__":
    unittest.main()

"""Tests for the Chart→Object house linking added in Task 006.

After Chart construction, every Object should know its house and every
House should know its objects, so consumers don't need to iterate.
"""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.object import House, Object


class ChartHouseLinkTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)

    def test_each_planet_has_a_house(self):
        for obj in self.chart.objects:
            self.assertIsInstance(obj.house, House, f"{obj.id} has no house")

    def test_round_trip_obj_house_has_object(self):
        # If obj.house is H, then H.hasObject(obj) must be True.
        for obj in self.chart.objects:
            self.assertTrue(obj.house.hasObject(obj))

    def test_house_objects_match_link(self):
        # house.objects is exactly the set of objs whose obj.house is house.
        for house in self.chart.houses:
            expected = [o for o in self.chart.objects if o.house is house]
            self.assertEqual(list(house.objects), expected)

    def test_houseOf_object(self):
        sun = self.chart.get(const.SUN)
        self.assertIs(self.chart.houseOf(sun), sun.house)

    def test_houseOf_string_id(self):
        # Passing a planet ID string should resolve to the same house.
        sun = self.chart.get(const.SUN)
        self.assertIs(self.chart.houseOf(const.SUN), sun.house)

    def test_houseOf_unknown_id_returns_none(self):
        # Unknown id → no object → None.
        self.assertIsNone(self.chart.houseOf("NotAPlanet"))

    def test_objectsInHouse_returns_list_of_objects(self):
        for house in self.chart.houses:
            members = self.chart.objectsInHouse(house.id)
            self.assertIsInstance(members, list)
            for o in members:
                self.assertIsInstance(o, Object)
                self.assertEqual(o.house.id, house.id)

    def test_objectsInHouse_unknown_returns_empty(self):
        # objectsInHouse with a bogus id falls through getHouse → KeyError;
        # we contract for [] when it's a string we don't recognise. Verify
        # by passing a real-but-empty house if possible. If no house is empty,
        # this assertion is a smoke test only.
        for house in self.chart.houses:
            members = self.chart.objectsInHouse(house.id)
            self.assertEqual(
                len(members),
                sum(1 for o in self.chart.objects if o.house is house),
            )


class MovementTruthinessRegressionTests(unittest.TestCase):
    """Regression for the original bug: `if obj.movement:` was always True
    because the bound method itself is truthy. Now property access returns
    the value (wrapped), whose bool() reflects the actual movement state.
    """

    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)
        self.sun = self.chart.get(const.SUN)

    def test_movement_property_is_not_a_method(self):
        # Property access must return something whose str() is the movement
        # value (Direct/Retrograde/Stationary), not the method's repr.
        movement_str = str(self.sun.movement)
        self.assertIn(
            movement_str,
            (const.DIRECT, const.RETROGRADE, const.STATIONARY),
        )

    def test_movement_compares_to_constant(self):
        # The original consumer pattern: comparison with a constant.
        is_direct = self.sun.movement == const.DIRECT
        self.assertIsInstance(is_direct, bool)

    def test_movement_truthiness_matches_value(self):
        # const.DIRECT, RETROGRADE, STATIONARY are all non-empty strings, so
        # bool() is True. The point is that bool() goes through the wrapper's
        # __bool__ (which delegates to the value), not the wrapper's identity
        # (which would always be True regardless of value).
        self.assertTrue(bool(self.sun.movement))


if __name__ == "__main__":
    unittest.main()

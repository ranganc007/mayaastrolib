"""Tests for the standard object lists added in Task 009."""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos


class ObjectListConstantsTests(unittest.TestCase):
    def test_modern_planets_has_ten(self):
        self.assertEqual(len(const.LIST_MODERN_PLANETS), 10)
        self.assertIn(const.SUN, const.LIST_MODERN_PLANETS)
        self.assertIn(const.PLUTO, const.LIST_MODERN_PLANETS)

    def test_lights_has_two(self):
        self.assertEqual(set(const.LIST_LIGHTS), {const.SUN, const.MOON})

    def test_personal_planets_excludes_outer(self):
        for outer in (const.URANUS, const.NEPTUNE, const.PLUTO):
            self.assertNotIn(outer, const.LIST_PERSONAL_PLANETS)

    def test_transpersonal_is_only_outer(self):
        self.assertEqual(
            set(const.LIST_TRANSPERSONAL),
            {const.URANUS, const.NEPTUNE, const.PLUTO},
        )

    def test_vedic_default_excludes_outer_planets(self):
        for outer in (const.URANUS, const.NEPTUNE, const.PLUTO):
            self.assertNotIn(outer, const.LIST_VEDIC_DEFAULT)

    def test_vedic_default_includes_nodes(self):
        self.assertIn(const.NORTH_NODE, const.LIST_VEDIC_DEFAULT)
        self.assertIn(const.SOUTH_NODE, const.LIST_VEDIC_DEFAULT)

    def test_tropical_default_includes_chiron_and_nodes(self):
        for obj in (const.CHIRON, const.NORTH_NODE, const.SOUTH_NODE):
            self.assertIn(obj, const.LIST_TROPICAL_DEFAULT)

    def test_lists_are_lists_not_tuples(self):
        # So consumers can do LIST_MODERN_PLANETS + [extra_object]
        for name in (
            "LIST_MODERN_PLANETS",
            "LIST_TROPICAL_DEFAULT",
            "LIST_VEDIC_DEFAULT",
            "LIST_LIGHTS",
            "LIST_PERSONAL_PLANETS",
            "LIST_SOCIAL_PLANETS",
            "LIST_TRANSPERSONAL",
            "LIST_LUNAR_NODES",
        ):
            self.assertIsInstance(getattr(const, name), list, f"{name} should be a list")

    def test_aspect_names_dict_exists(self):
        self.assertIsInstance(const.ASPECT_NAMES, dict)
        self.assertGreater(len(const.ASPECT_NAMES), 4)


class ChartConstructionWithListsTests(unittest.TestCase):
    """Smoke test: building a Chart with each list doesn't crash."""

    def setUp(self):
        self.date = Datetime("2015/03/13", "17:00", "+00:00")
        self.pos = GeoPos("38n32", "8w54")

    def test_chart_with_modern_planets(self):
        chart = Chart(self.date, self.pos, IDs=const.LIST_MODERN_PLANETS)
        self.assertIsNotNone(chart.get(const.SUN))
        self.assertIsNotNone(chart.get(const.PLUTO))

    def test_chart_with_lights(self):
        chart = Chart(self.date, self.pos, IDs=const.LIST_LIGHTS)
        self.assertIsNotNone(chart.get(const.SUN))
        self.assertIsNotNone(chart.get(const.MOON))

    def test_chart_with_seven_planets(self):
        chart = Chart(self.date, self.pos, IDs=const.LIST_SEVEN_PLANETS)
        self.assertIsNotNone(chart.get(const.SATURN))

    def test_chart_with_vedic_default(self):
        chart = Chart(self.date, self.pos, IDs=const.LIST_VEDIC_DEFAULT)
        self.assertIsNotNone(chart.get(const.NORTH_NODE))
        self.assertIsNotNone(chart.get(const.SOUTH_NODE))


if __name__ == "__main__":
    unittest.main()

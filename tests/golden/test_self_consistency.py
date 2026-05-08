"""Self-consistency tests for charts.

These tests assert invariants that must hold regardless of any
reference implementation. They complement
:mod:`tests.golden.test_planet_positions` (which uses Skyfield as
reference) by catching a different class of bug: internal
arithmetic errors, frame mismatches, off-by-360 issues, broken
house ordering, etc.

No external dependency.
"""

from __future__ import annotations

import unittest

from mayaastrolib import aspects, const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos

# Three test charts at varied latitudes / dates for invariant testing.
# Times are UTC; LMT-to-UTC was hand-computed in
# tests/golden/generate_fixtures.py.
TEST_CHARTS: list[tuple[str, str, str, str, float, float]] = [
    ("temperate_einstein", "1879/03/14", "10:50:00", "+00:00", 48.4, 10.0),
    ("tropical_kahlo", "1907/07/06", "15:06:40", "+00:00", 19.333, -99.167),
    ("high_lat_amundsen", "1872/07/16", "02:46:48", "+00:00", 59.383, 10.8),
]


def _build(name: str, date_str: str, time_str: str, offset: str, lat: float, lon: float) -> Chart:
    return Chart(
        Datetime(date_str, time_str, offset),
        GeoPos(lat, lon),
        IDs=const.LIST_MODERN_PLANETS,
    )


class HouseInvariantTests(unittest.TestCase):
    """Houses must span exactly 360° and never overlap."""

    def test_houses_span_360_degrees(self):
        for name, *params in TEST_CHARTS:
            with self.subTest(chart=name):
                chart = _build(name, *params)
                houses = [chart.getHouse(hid) for hid in const.LIST_HOUSES]
                spans = []
                for i in range(12):
                    spans.append((houses[(i + 1) % 12].lon - houses[i].lon) % 360)
                total = sum(spans)
                self.assertAlmostEqual(
                    total,
                    360.0,
                    places=2,
                    msg=f"{name}: houses sum to {total:.4f}°, expected 360°",
                )

    def test_house_cusps_are_in_order(self):
        """Each successive cusp is reached by going forward in zodiac."""
        for name, *params in TEST_CHARTS:
            with self.subTest(chart=name):
                chart = _build(name, *params)
                houses = [chart.getHouse(hid) for hid in const.LIST_HOUSES]
                prev_lon = houses[0].lon
                for i in range(1, 12):
                    next_lon = houses[i].lon
                    forward_arc = (next_lon - prev_lon) % 360
                    self.assertGreater(
                        forward_arc,
                        0.0,
                        f"{name}: house {i + 1} cusp is at or before house {i}",
                    )
                    self.assertLess(
                        forward_arc,
                        360.0,
                        f"{name}: house {i + 1} cusp wraps past house {i}",
                    )
                    prev_lon = next_lon


class PlanetInvariantTests(unittest.TestCase):
    """Planet positions must be in valid ranges."""

    def test_planet_longitudes_in_range(self):
        for name, *params in TEST_CHARTS:
            with self.subTest(chart=name):
                chart = _build(name, *params)
                for planet_id in const.LIST_MODERN_PLANETS:
                    p = chart.get(planet_id)
                    self.assertGreaterEqual(p.lon, 0.0, f"{name} {planet_id}: lon {p.lon} < 0")
                    self.assertLess(p.lon, 360.0, f"{name} {planet_id}: lon {p.lon} >= 360")

    def test_planet_signlon_in_range(self):
        for name, *params in TEST_CHARTS:
            with self.subTest(chart=name):
                chart = _build(name, *params)
                for planet_id in const.LIST_MODERN_PLANETS:
                    p = chart.get(planet_id)
                    self.assertGreaterEqual(p.signlon, 0.0)
                    self.assertLess(p.signlon, 30.0)

    def test_each_planet_is_in_house(self):
        """``obj.house`` is set for every planet (Task 006 invariant)."""
        for name, *params in TEST_CHARTS:
            with self.subTest(chart=name):
                chart = _build(name, *params)
                for planet_id in const.LIST_MODERN_PLANETS:
                    p = chart.get(planet_id)
                    self.assertIsNotNone(p.house, f"{name} {planet_id}: house is None")


class AspectInvariantTests(unittest.TestCase):
    """Aspect computations must produce valid output."""

    def test_aspect_orb_is_non_negative(self):
        for name, *params in TEST_CHARTS:
            with self.subTest(chart=name):
                chart = _build(name, *params)
                sun = chart.get(const.SUN)
                moon = chart.get(const.MOON)
                asp = aspects.getAspect(sun, moon, const.MAJOR_ASPECTS)
                if asp is not None:
                    self.assertGreaterEqual(asp.orb, 0.0)

    def test_aspect_name_when_present(self):
        for name, *params in TEST_CHARTS:
            with self.subTest(chart=name):
                chart = _build(name, *params)
                sun = chart.get(const.SUN)
                moon = chart.get(const.MOON)
                asp = aspects.getAspect(sun, moon, const.MAJOR_ASPECTS)
                if asp is not None:
                    self.assertIn(asp.name, const.ASPECT_NAMES.values())


class SymbolicChartInvariantTests(unittest.TestCase):
    """Profected charts (Task 010) must satisfy symbolic-chart invariants."""

    def test_profected_chart_houses_still_span_360(self):
        for name, *params in TEST_CHARTS:
            with self.subTest(chart=name):
                natal = _build(name, *params)
                profected = natal.profected(years=42)
                houses = [profected.getHouse(hid) for hid in const.LIST_HOUSES]
                spans = []
                for i in range(12):
                    spans.append((houses[(i + 1) % 12].lon - houses[i].lon) % 360)
                total = sum(spans)
                self.assertAlmostEqual(total, 360.0, places=2)

    def test_profected_planets_have_no_speed(self):
        for name, *params in TEST_CHARTS:
            with self.subTest(chart=name):
                natal = _build(name, *params)
                profected = natal.profected(years=42)
                sun = profected.get(const.SUN)
                self.assertIsNone(sun.lonspeed)


if __name__ == "__main__":
    unittest.main()

"""Golden tests for Vedic sidereal planet positions — Task 017.

Strategy: reuse the Task 014 Skyfield-anchored tropical fixtures, subtract
the Lahiri ayanamsa value (computed once per chart via
``swisseph.get_ayanamsa_ut``), and verify that mayaastrolib's sidereal
chart construction (`Chart(..., zodiac=ZODIAC_SIDEREAL)`) produces the
same sidereal positions within ±2 arcminutes.

This is *more* independent than it looks: the tropical anchor is Skyfield
(an unrelated JPL DE-series implementation), and only the *ayanamsa
value* comes from pyswisseph. If the swisseph ``FLG_SIDEREAL`` calc_ut
path were buggy (e.g. wrong precession application), we would catch the
discrepancy here because the "expected" sidereal lon and the "actual"
sidereal lon are computed via two different code paths in swisseph.
"""

from __future__ import annotations

import json
import unittest
from datetime import datetime
from pathlib import Path

import swisseph

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos

FIXTURES_PATH = Path(__file__).parent / "fixtures.json"
TOLERANCE_ARCMIN = 2.0
TOLERANCE_DEG = TOLERANCE_ARCMIN / 60.0

PLANET_MAP = {
    const.SUN: "Sun",
    const.MOON: "Moon",
    const.MERCURY: "Mercury",
    const.VENUS: "Venus",
    const.MARS: "Mars",
    const.JUPITER: "Jupiter",
    const.SATURN: "Saturn",
    const.URANUS: "Uranus",
    const.NEPTUNE: "Neptune",
    const.PLUTO: "Pluto",
}


def _load_fixtures():
    with open(FIXTURES_PATH) as f:
        return json.load(f)


def _angular_diff(a, b):
    """Absolute angular distance in degrees with 360° wraparound."""
    diff = abs(a - b) % 360.0
    return min(diff, 360.0 - diff)


def _date_from_iso(iso_string):
    """Convert an ISO UTC string to a mayaastrolib Datetime."""
    py = datetime.fromisoformat(iso_string)
    date_str = f"{py.year}/{py.month:02d}/{py.day:02d}"
    time_str = f"{py.hour:02d}:{py.minute:02d}:{py.second:02d}"
    return Datetime(date_str, time_str, "+00:00")


class VedicSiderealGoldenTests(unittest.TestCase):
    """Verify sidereal positions against Skyfield-tropical minus Lahiri-ayanamsa."""

    def _check_chart(self, fixture):
        date = _date_from_iso(fixture["date_utc"])
        pos = GeoPos(fixture["location"]["lat"], fixture["location"]["lon"])
        chart = Chart(
            date,
            pos,
            IDs=const.LIST_MODERN_PLANETS,
            zodiac=const.ZODIAC_SIDEREAL,
        )

        # Compute the Lahiri ayanamsa for this date once.
        swisseph.set_sid_mode(swisseph.SIDM_LAHIRI)
        ayanamsa = swisseph.get_ayanamsa_ut(date.jd)

        for planet_id, fixture_key in PLANET_MAP.items():
            if fixture_key not in fixture["expected_positions"]:
                continue
            tropical_expected = fixture["expected_positions"][fixture_key]
            sidereal_expected = (tropical_expected - ayanamsa) % 360.0
            sidereal_actual = chart.getObject(planet_id).lon
            diff = _angular_diff(sidereal_actual, sidereal_expected)
            with self.subTest(chart=fixture["name"], planet=fixture_key):
                self.assertLessEqual(
                    diff,
                    TOLERANCE_DEG,
                    f"{fixture['name']} {fixture_key}: sidereal expected "
                    f"{sidereal_expected:.6f}°, got {sidereal_actual:.6f}°, "
                    f"diff {diff * 60:.2f}' > tolerance {TOLERANCE_ARCMIN}'",
                )

    def test_einstein_sidereal_positions(self):
        fixtures = _load_fixtures()
        self._check_chart(next(f for f in fixtures if f["name"] == "Albert Einstein"))

    def test_kahlo_sidereal_positions(self):
        fixtures = _load_fixtures()
        self._check_chart(next(f for f in fixtures if f["name"] == "Frida Kahlo"))

    def test_amundsen_sidereal_positions(self):
        fixtures = _load_fixtures()
        self._check_chart(next(f for f in fixtures if f["name"] == "Roald Amundsen"))


class VedicSiderealInvariantTests(unittest.TestCase):
    """Invariants that hold for any sidereal chart, no external anchor needed."""

    def test_sun_signlon_in_valid_range(self):
        date = Datetime("1980/01/01", "12:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        sun = chart.getObject(const.SUN)
        self.assertTrue(0.0 <= sun.lon < 360.0)
        # Sun's sidereal sign in early January is Sagittarius (Lahiri).
        # Verify the sign computed from lon matches what const.LIST_SIGNS gives.
        sign_idx = int(sun.lon // 30)
        self.assertEqual(sun.sign, const.LIST_SIGNS[sign_idx])


if __name__ == "__main__":
    unittest.main()

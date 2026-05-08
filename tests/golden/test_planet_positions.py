"""Golden tests for planet positions.

Compares mayaastrolib's planet longitudes against frozen Skyfield-
generated references in ``tests/golden/fixtures.json``. Tolerance is
±2 arcminutes per ``CLAUDE.md``.

Independence: mayaastrolib's runtime backend is Swiss Ephemeris (via
pyswisseph); Skyfield is an unrelated implementation built on NASA JPL
DE-series data. Two independent implementations agreeing to ±2 arcmin
is meaningful evidence of astronomical correctness.

To regenerate the fixtures (e.g. after adding a chart or updating
Skyfield):

.. code-block:: bash

    .venv-task014/bin/python tests/golden/generate_fixtures.py
"""

from __future__ import annotations

import json
import unittest
from datetime import datetime
from pathlib import Path

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos

FIXTURES_PATH = Path(__file__).parent / "fixtures.json"
TOLERANCE_ARCMIN = 2.0
TOLERANCE_DEG = TOLERANCE_ARCMIN / 60.0


# Mapping: mayaastrolib planet ID → fixture key
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


def _load_fixtures() -> list[dict]:
    with open(FIXTURES_PATH) as f:
        return json.load(f)


def _angular_diff(a: float, b: float) -> float:
    """Absolute angular distance in degrees, accounting for 360°
    wraparound (e.g. 359° vs 1° returns 2°, not 358°).
    """
    diff = abs(a - b) % 360
    return min(diff, 360 - diff)


def _build_chart(fixture: dict) -> Chart:
    """Construct a mayaastrolib Chart from a fixture's input metadata.

    Fixtures are stored in UTC, so we pass ``+00:00`` as the offset.
    Uses ``LIST_MODERN_PLANETS`` (Sun–Pluto) since Skyfield doesn't
    compute the lunar nodes / Pars Fortuna / Syzygy.
    """
    iso = fixture["date_utc"]
    dt = datetime.fromisoformat(iso)
    mdate = Datetime(
        dt.strftime("%Y/%m/%d"),
        dt.strftime("%H:%M:%S"),
        "+00:00",
    )
    loc = fixture["location"]
    pos = GeoPos(loc["lat"], loc["lon"])
    return Chart(mdate, pos, IDs=const.LIST_MODERN_PLANETS)


class GoldenPlanetPositionTests(unittest.TestCase):
    """Verify mayaastrolib planet positions match Skyfield reference."""

    @classmethod
    def setUpClass(cls):
        cls.fixtures = _load_fixtures()

    def test_each_chart_planets_match_reference(self):
        """Every (chart × planet) within ±2 arcmin of Skyfield."""
        for fixture in self.fixtures:
            chart = _build_chart(fixture)
            for mlib_id, fixture_key in PLANET_MAP.items():
                if fixture_key not in fixture["expected_positions"]:
                    continue
                with self.subTest(chart=fixture["name"], planet=fixture_key):
                    expected = fixture["expected_positions"][fixture_key]
                    actual = chart.get(mlib_id).lon
                    diff = _angular_diff(actual, expected)
                    self.assertLessEqual(
                        diff,
                        TOLERANCE_DEG,
                        f"{fixture['name']} {fixture_key}: "
                        f"expected {expected:.4f}°, got {actual:.4f}° "
                        f"(diff {diff * 60:.2f}', tolerance {TOLERANCE_ARCMIN}')",
                    )


if __name__ == "__main__":
    unittest.main()

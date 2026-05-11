# Task 014: Golden Test Fixtures and Self-Consistency Suite

## Context

You are working in the `mayaastrolib` repository. Before doing anything:

1. Read `CLAUDE.md` in full. Pay particular attention to the testing requirements: "Functional tests (`tests/golden/`) — verify astronomical correctness. Reference charts with known positions sourced from Astro-Databank or astro.com. Tolerance: ±2 arc-minutes for planets, ±5 arc-minutes for house cusps. These tests survive any refactor."
2. Read `docs/REVIEW-2026-05-08.md` end to end — particularly the "Reliability and test gaps" section identifying `tests/golden/` as the headline reliability gap, and the Task 014 description in Suggested Next Tasks.
3. Read `mayaastrolib/chart.py`, `mayaastrolib/object.py`, `mayaastrolib/datetime.py`, and `mayaastrolib/geopos.py` to understand the public API surface this task will be testing.
4. Read `docs/PROJECT-LOG.md` for entries from Tasks 011-015 to understand recent patterns.
5. Confirm `development` is at the post-Task-015 state:

   ```
   git log --oneline development -5
   ```

   You should see Task 015 commits at the top (GeoPos validation).

6. Confirm `pytest tests/` passes — should be ~198 tests.

## Why this task exists

`CLAUDE.md` mandates two test layers: structural (in `tests/unit/`) and functional/golden (in `tests/golden/`). Only the structural layer has been built. Every refactor since Task 005 has been verified against the structural test suite *and against the library itself*, but never against an independent astronomical reference. The platform review (2026-05-08) identifies this as the headline reliability gap — particularly going into Phase 2 (Vedic) where ayanamsa application against published reference values is testable.

This task closes the gap.

## Design decisions (already made — do not relitigate)

### Methodology

**Reference source:** Skyfield (MIT, pure Python, uses JPL DE-series data via the `de421.bsp` file). Skyfield is added as a **dev dependency only** — it runs in `tests/golden/generate_fixtures.py`, not in the library itself. Users of `mayaastrolib` never install Skyfield.

**Why Skyfield:**
- MIT license — no GPL contamination of the test infrastructure
- Independent implementation of celestial mechanics from Swiss Ephemeris (Swiss Eph derives from Steve Moshier's analytical theory; Skyfield uses NASA JPL data via numerical integration). Two independent implementations agreeing within ±2 arcminutes is meaningful evidence of correctness.
- Reproducible — anyone can run `generate_fixtures.py` and get the same numbers
- Actively maintained, used by NASA and professional astronomers

**Tolerance:** ±2 arcminutes for planets, ±5 arcminutes for house cusps. Per CLAUDE.md.

**Scope of golden tests:** planet positions only. Skyfield computes astronomical positions (ecliptic longitude, latitude). It does NOT compute astrological houses, dignities, or aspects — those are domain concepts that Skyfield doesn't know about. Houses, dignities, and aspects are tested via the **self-consistency suite** (Part 2 below).

**Scope of self-consistency suite:** invariants that must hold regardless of reference data. Examples: houses span exactly 360°, all aspect orbs are non-negative, sum-of-essential-dignities is within known bounds. Catches a different class of bug than golden tests and doesn't depend on Skyfield.

### Three reference charts

Picked deliberately to exercise different layers:

1. **Albert Einstein** — March 14, 1879, 11:30 LMT, Ulm, Germany (48°24'N, 10°00'E). Northern hemisphere temperate latitude. Standard happy path. Birth data well-attested (Astro-Databank Rodden Rating: AA).

2. **Frida Kahlo** — July 6, 1907, 08:30 LMT, Coyoacán, Mexico (19°20'N, 99°10'W). Lower-northern latitude. Different hemisphere from Einstein for variety. Birth data well-attested (Astro-Databank Rodden Rating: AA).

3. **Roald Amundsen** — July 16, 1872, 03:30 LMT, Borge, Norway (59°23'N, 10°48'E). High northern latitude, near the boundary where Placidus starts behaving strangely. Tests strict Placidus behaviour at extreme latitudes. Birth data: from public biographical record.

The third chart is **deliberately at high latitude** to exercise edge cases. If `mayaastrolib` produces broken Placidus output at 59°N, this test will catch it. Per the user's Q3 answer, this is **strict** testing — the test should fail if Placidus produces nonsense, not be lenient.

If Placidus genuinely fails at high latitudes during this task (mathematically expected behaviour for some date/location combinations near the poles), this surfaces a real issue. Document it in PROJECT-LOG.md and decide whether to:
- Adjust the third chart's date/time to a configuration where Placidus is stable at 59°N (still a meaningful test)
- Mark the test `expectedFailure` and document the known limitation
- Investigate further (would expand task scope; defer to a follow-up task)

### LICENSING.md

A short root-level document explaining the licensing situation. Reason: `mayaastrolib` is MIT-licensed, but at runtime depends on `pyswisseph`, which contains Swiss Ephemeris (dual-licensed GPL or commercial). Users deploying `mayaastrolib` in commercial closed-source contexts need to be aware of this.

This isn't a code change — just honesty.

## Task scope

This task has four parts. Do them in order.

---

### Part 1: Add Skyfield as a dev dependency

In `pyproject.toml`, under `[project.optional-dependencies]`:

```toml
dev = [
    "pytest",
    "pytest-cov",
    "ruff",
    "mypy",
    "skyfield>=1.46",  # for tests/golden/generate_fixtures.py — MIT, dev-only
]
```

Verify the pin — check the latest stable Skyfield on PyPI before committing. Don't pin tighter than necessary; `>=1.46` should work.

Also: Skyfield needs an ephemeris file (`de421.bsp`, ~17MB) at runtime. Decision: **do NOT commit `de421.bsp` to the repo.** Have `generate_fixtures.py` download it on first run via Skyfield's `Loader` mechanism, caching it locally in `tests/golden/.skyfield-data/` (gitignored).

Add to `.gitignore`:

```
# Skyfield ephemeris cache (downloaded by tests/golden/generate_fixtures.py)
tests/golden/.skyfield-data/
```

---

### Part 2: Create `tests/golden/generate_fixtures.py`

This script is run **manually by maintainers** when fixtures need to be regenerated (e.g. when adding a new chart, when updating Skyfield, when Swiss Eph updates have meaningfully shifted positions). It is NOT run by CI or pytest.

```python
"""Generate golden-test fixtures using Skyfield.

This script is run manually by maintainers when fixtures need updating.
NOT run by CI or pytest — fixture data is committed as JSON.

Skyfield (MIT, pure Python, uses NASA JPL ephemeris) is used as the
reference implementation. mayaastrolib's output is later compared
against this reference in tests/golden/test_planet_positions.py.

Usage:
    python tests/golden/generate_fixtures.py

Output:
    tests/golden/fixtures.json
"""

import json
from pathlib import Path

from skyfield.api import Loader, wgs84
from skyfield.framelib import ecliptic_frame

# Skyfield ephemeris cache directory — gitignored
DATA_DIR = Path(__file__).parent / ".skyfield-data"
DATA_DIR.mkdir(exist_ok=True)
load = Loader(str(DATA_DIR))

ts = load.timescale()
eph = load("de421.bsp")

EARTH = eph["earth"]
PLANETS = {
    "Sun": eph["sun"],
    "Moon": eph["moon"],
    "Mercury": eph["mercury"],
    "Venus": eph["venus"],
    "Mars": eph["mars"],
    "Jupiter": eph["jupiter barycenter"],
    "Saturn": eph["saturn barycenter"],
    "Uranus": eph["uranus barycenter"],
    "Neptune": eph["neptune barycenter"],
    "Pluto": eph["pluto barycenter"],
}

CHARTS = [
    {
        "name": "Albert Einstein",
        "date_utc": "1879-03-14T11:30:00",  # LMT at Ulm; 11:30 - 0:40 ≈ 10:50 UTC
        # NOTE: Convert LMT to UTC before passing to Skyfield. Ulm is at
        # ~10°E longitude, so LMT = UTC + 10/15 hours = UTC + 0:40.
        # Therefore 11:30 LMT = 10:50 UTC.
        "location": {"lat": 48.4, "lon": 10.0, "elevation_m": 478},
        "rodden_rating": "AA",
        "source": "Astro-Databank",
    },
    {
        "name": "Frida Kahlo",
        "date_utc": "1907-07-06T14:30:00",  # 08:30 LMT Coyoacán; -99°W ≈ -6:36 from UTC
        # 08:30 LMT = 08:30 + 6:36 ≈ 15:06 UTC. Approximate; verify with
        # historical-tz lookup if possible.
        "location": {"lat": 19.333, "lon": -99.167, "elevation_m": 2240},
        "rodden_rating": "AA",
        "source": "Astro-Databank",
    },
    {
        "name": "Roald Amundsen",
        "date_utc": "1872-07-16T02:48:00",  # 03:30 LMT Borge; 10.8°E = +0:43 from UTC
        # 03:30 LMT = 03:30 - 0:43 ≈ 02:47 UTC.
        "location": {"lat": 59.383, "lon": 10.8, "elevation_m": 5},
        "rodden_rating": "B",
        "source": "Public biographical record",
    },
]


def compute_chart(chart):
    """Compute Skyfield's geocentric ecliptic longitudes for a chart.

    Returns a dict mapping planet name → ecliptic longitude in degrees [0, 360).
    """
    iso = chart["date_utc"]
    # Parse ISO into Skyfield time. Skyfield's ts.utc takes (year, month, day, hour, minute, second).
    from datetime import datetime
    dt = datetime.fromisoformat(iso).replace(tzinfo=None)
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

    observer = EARTH + wgs84.latlon(
        chart["location"]["lat"],
        chart["location"]["lon"],
        elevation_m=chart["location"]["elevation_m"],
    )

    out = {}
    for name, body in PLANETS.items():
        astrometric = observer.at(t).observe(body)
        # Apparent ecliptic-of-date coordinates (matches Swiss Eph convention)
        lat, lon, distance = astrometric.apparent().frame_latlon(ecliptic_frame)
        out[name] = float(lon.degrees) % 360.0

    return out


def main():
    fixtures = []
    for chart in CHARTS:
        positions = compute_chart(chart)
        fixtures.append({
            "name": chart["name"],
            "date_utc": chart["date_utc"],
            "location": chart["location"],
            "rodden_rating": chart["rodden_rating"],
            "source": chart["source"],
            "expected_positions": positions,
            "tolerance_arcmin": 2.0,
            "generated_by": "skyfield (de421.bsp)",
        })

    out_path = Path(__file__).parent / "fixtures.json"
    with open(out_path, "w") as f:
        json.dump(fixtures, f, indent=2)
    print(f"Wrote {len(fixtures)} fixtures to {out_path}")


if __name__ == "__main__":
    main()
```

**Important:** the LMT-to-UTC conversion in the chart data is approximate. Real LMT (Local Mean Time, used before timezone standardisation) is `UTC + (longitude_degrees / 15)`. For Ulm at ~10°E, that's UTC+40min. Verify each chart's date_utc using this formula before running the script. If the conversion is off by minutes, the fixtures will be wrong by ~0.5-1°, well beyond tolerance.

**Cross-check during fixture generation:** for each chart, after running the script, take the same date/time/location to astro.com and verify the Sun's position matches Skyfield's output to within ±1 arcminute. This is a one-time sanity check; document the results in `tests/golden/README.md`.

If astro.com and Skyfield disagree by more than 2 arcminutes on Sun position, something is wrong with the LMT conversion or the input data — investigate and fix before proceeding.

---

### Part 3: Create `tests/golden/test_planet_positions.py`

This is the actual test suite — runs in CI, loads `fixtures.json`, compares mayaastrolib output against Skyfield's frozen reference.

```python
"""Golden tests for planet positions.

Compares mayaastrolib's planet positions against frozen Skyfield-generated
references in tests/golden/fixtures.json. Tolerance: ±2 arcminutes per
CLAUDE.md.

To regenerate fixtures (e.g. after adding a chart or updating Skyfield):
    python tests/golden/generate_fixtures.py
"""

import json
import unittest
from datetime import datetime
from pathlib import Path

from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib import const

FIXTURES_PATH = Path(__file__).parent / "fixtures.json"
TOLERANCE_ARCMIN = 2.0
TOLERANCE_DEG = TOLERANCE_ARCMIN / 60.0


# Map mayaastrolib planet IDs to fixture keys
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
    """Return absolute angular difference in degrees, mod 360."""
    diff = abs(a - b) % 360
    return min(diff, 360 - diff)


def _build_chart(fixture):
    """Construct a mayaastrolib Chart from a fixture's input data."""
    iso = fixture["date_utc"]
    dt = datetime.fromisoformat(iso)
    mdate = Datetime(
        dt.strftime("%Y/%m/%d"),
        dt.strftime("%H:%M:%S"),
        "+00:00",  # fixtures are stored as UTC
    )
    loc = fixture["location"]
    # GeoPos accepts string or numeric coordinates; check both work
    pos = GeoPos(loc["lat"], loc["lon"])
    return Chart(mdate, pos, IDs=const.LIST_MODERN_PLANETS)


class GoldenPlanetPositionTests(unittest.TestCase):
    """Verify mayaastrolib planet positions match Skyfield reference."""

    @classmethod
    def setUpClass(cls):
        cls.fixtures = _load_fixtures()

    def test_each_chart_planets_match_reference(self):
        """Iterate over all fixtures and all planets; assert tolerance."""
        for fixture in self.fixtures:
            with self.subTest(chart=fixture["name"]):
                chart = _build_chart(fixture)
                for mlib_id, fixture_key in PLANET_MAP.items():
                    if fixture_key not in fixture["expected_positions"]:
                        continue  # Pluto may not be in older fixtures
                    expected = fixture["expected_positions"][fixture_key]
                    actual_obj = chart.get(mlib_id)
                    actual = actual_obj.lon
                    diff = _angular_diff(actual, expected)
                    self.assertLessEqual(
                        diff,
                        TOLERANCE_DEG,
                        f"{fixture['name']} {fixture_key}: "
                        f"expected {expected:.4f}°, got {actual:.4f}° "
                        f"(diff {diff * 60:.2f} arcmin, "
                        f"tolerance {TOLERANCE_ARCMIN} arcmin)",
                    )


if __name__ == "__main__":
    unittest.main()
```

The `subTest` mechanism gives clean per-(chart, planet) failure reporting if any one of them is out of tolerance.

---

### Part 4: Create `tests/golden/test_self_consistency.py`

Invariant-based tests. These don't depend on Skyfield or any reference; they assert properties that must hold for any correctly-computed chart.

```python
"""Self-consistency tests for charts.

These tests assert invariants that must hold regardless of any reference
implementation. They complement tests/golden/test_planet_positions.py
(which uses Skyfield as reference) by catching a different class of bug:
internal arithmetic errors, frame mismatches, off-by-360 issues, etc.

No external dependency.
"""

import unittest

from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib import const, aspects


# Three test charts at varied latitudes/dates for invariant testing.
TEST_CHARTS = [
    ("temperate", "1879/03/14", "10:50:00", "+00:00", 48.4, 10.0),
    ("tropical", "1907/07/06", "15:06:00", "+00:00", 19.333, -99.167),
    ("high_lat", "1872/07/16", "02:47:00", "+00:00", 59.383, 10.8),
]


def _build(name, date_str, time_str, offset, lat, lon):
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
                # Sum of house spans = 360°
                spans = []
                for i in range(12):
                    h = chart.houses[i]
                    next_h = chart.houses[(i + 1) % 12]
                    span = (next_h.lon - h.lon) % 360
                    spans.append(span)
                total = sum(spans)
                self.assertAlmostEqual(
                    total, 360.0, places=2,
                    msg=f"{name}: houses sum to {total:.4f}°, expected 360°",
                )

    def test_house_cusps_are_in_order(self):
        """House N+1's cusp comes after House N's cusp going forward in zodiac."""
        for name, *params in TEST_CHARTS:
            with self.subTest(chart=name):
                chart = _build(name, *params)
                prev_lon = chart.houses[0].lon
                for i in range(1, 12):
                    next_lon = chart.houses[i].lon
                    # Going forward from prev_lon, next_lon should be reached
                    # before completing a full 360° revolution
                    forward_arc = (next_lon - prev_lon) % 360
                    self.assertGreater(
                        forward_arc, 0.0,
                        f"{name}: house {i+1} cusp is at or before house {i}",
                    )
                    self.assertLess(
                        forward_arc, 360.0,
                        f"{name}: house {i+1} cusp wraps past house {i}",
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
                    self.assertGreaterEqual(
                        p.lon, 0.0,
                        f"{name} {planet_id}: lon {p.lon} < 0",
                    )
                    self.assertLess(
                        p.lon, 360.0,
                        f"{name} {planet_id}: lon {p.lon} >= 360",
                    )

    def test_planet_signlon_in_range(self):
        for name, *params in TEST_CHARTS:
            with self.subTest(chart=name):
                chart = _build(name, *params)
                for planet_id in const.LIST_MODERN_PLANETS:
                    p = chart.get(planet_id)
                    self.assertGreaterEqual(p.signlon, 0.0)
                    self.assertLess(p.signlon, 30.0)

    def test_each_planet_is_in_house(self):
        """obj.house should be set for every planet (Task 006 invariant)."""
        for name, *params in TEST_CHARTS:
            with self.subTest(chart=name):
                chart = _build(name, *params)
                for planet_id in const.LIST_MODERN_PLANETS:
                    p = chart.get(planet_id)
                    self.assertIsNotNone(
                        p.house,
                        f"{name} {planet_id}: house is None",
                    )


class AspectInvariantTests(unittest.TestCase):
    """Aspect computations must produce valid output."""

    def test_aspect_between_planet_and_self_is_conjunction(self):
        for name, *params in TEST_CHARTS:
            with self.subTest(chart=name):
                chart = _build(name, *params)
                sun = chart.get(const.SUN)
                asp = aspects.getAspect(sun, sun, const.MAJOR_ASPECTS)
                self.assertIsNotNone(asp)
                self.assertEqual(asp.type, 0)  # Conjunction

    def test_aspect_orb_is_non_negative(self):
        for name, *params in TEST_CHARTS:
            with self.subTest(chart=name):
                chart = _build(name, *params)
                sun = chart.get(const.SUN)
                moon = chart.get(const.MOON)
                asp = aspects.getAspect(sun, moon, const.MAJOR_ASPECTS)
                if asp is not None:
                    self.assertGreaterEqual(asp.orb, 0.0)


class SymbolicChartInvariantTests(unittest.TestCase):
    """Profected charts (Task 010) must satisfy symbolic-chart invariants."""

    def test_profected_chart_houses_still_span_360(self):
        for name, *params in TEST_CHARTS:
            with self.subTest(chart=name):
                natal = _build(name, *params)
                profected = natal.profected(years=42)
                spans = []
                for i in range(12):
                    h = profected.houses[i]
                    next_h = profected.houses[(i + 1) % 12]
                    spans.append((next_h.lon - h.lon) % 360)
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
```

The `subTest` pattern is used throughout so failures point at the specific chart and assertion, not just "one of them failed".

---

### Part 5: Create supporting documentation

#### `tests/golden/README.md`

```markdown
# Golden Test Suite

This directory contains the functional / golden test layer mandated by
`CLAUDE.md`. Tests here verify mayaastrolib's astronomical correctness
against an independent reference (Skyfield), and assert structural
invariants that must hold for any correctly-computed chart.

## Layout

- `generate_fixtures.py` — Skyfield-based reference generator. Run
  manually by maintainers when adding charts or updating Skyfield.
- `fixtures.json` — frozen reference data, committed.
- `test_planet_positions.py` — golden tests, run by pytest.
- `test_self_consistency.py` — invariant tests, run by pytest.

## Reference methodology

**Why Skyfield:**
- MIT-licensed, no GPL contamination
- Independent implementation from Swiss Ephemeris (mayaastrolib's
  runtime backend), so agreement is meaningful evidence
- Reproducible — anyone can run generate_fixtures.py and get the
  same numbers
- Used by NASA and professional astronomers; well-tested

**Why we don't golden-test houses, dignities, or aspects:**
Skyfield is an astronomy library — it doesn't know about astrological
concepts. Houses, dignities, and aspects are tested via
`test_self_consistency.py` (invariants) instead. This catches a
different class of bug than golden tests can.

**Tolerance:** ±2 arcminutes for planets (per CLAUDE.md). Given that
mayaastrolib uses Swiss Ephemeris and Skyfield uses NASA JPL data,
small differences in ΔT models and frame transformations produce
sub-arcminute drift between the two; our tolerance accommodates this.

## Reference charts

Three charts deliberately chosen:

1. **Albert Einstein** (1879-03-14, Ulm, Germany, 48°N) — temperate
   latitude, Northern hemisphere, well-attested birth data (Rodden
   AA-rated).
2. **Frida Kahlo** (1907-07-06, Coyoacán, Mexico, 19°N) — tropical
   latitude, different hemisphere from Einstein, Rodden AA.
3. **Roald Amundsen** (1872-07-16, Borge, Norway, 59°N) — high
   northern latitude. Tests Placidus stability near the boundary
   where it begins to behave irregularly.

## Cross-checking new fixtures

When adding a new chart to `generate_fixtures.py`, also verify the
Sun's position against astro.com (or another independent reference)
to within ±1 arcminute. This catches LMT-conversion errors and
location-data errors that would otherwise produce a "Skyfield says X,
mayaastrolib agrees with X, but X is wrong because the input data is
wrong" failure mode that no automated test can catch.

## Regenerating fixtures

```bash
.venv-task014/bin/python tests/golden/generate_fixtures.py
```

Then commit the updated `fixtures.json`. CI does NOT run this script;
fixtures are frozen artefacts.

## When to regenerate

- Adding a new fixture chart
- Updating Skyfield to a major new version
- Updating the JPL ephemeris (e.g. de421.bsp → de440.bsp)
- Discovering a fixture is wrong (e.g. LMT-conversion error)

Do NOT regenerate to make a failing test pass. If mayaastrolib's
output drifts beyond tolerance, that's a real signal — investigate
the library, don't paper over it by regenerating fixtures.
```

#### `LICENSING.md` at repo root

```markdown
# Licensing

`mayaastrolib` itself is MIT-licensed (see `LICENSE`).

## Runtime dependencies and their licenses

`mayaastrolib` depends on `pyswisseph` at runtime. `pyswisseph` is a
Python wrapper around Swiss Ephemeris.

- **`pyswisseph`** itself is LGPL-licensed (the Python bindings).
- **Swiss Ephemeris** (the underlying C library and ephemeris data
  files) is dual-licensed:
  - **GPL v2+** for open-source projects, OR
  - **Commercial license** from Astrodienst (Switzerland) for closed-
    source commercial use. Pricing and terms: https://www.astro.com/swisseph/

### What this means for you

- **Using `mayaastrolib` for personal, research, or open-source
  projects:** comply with GPL on the Swiss Ephemeris portion, which
  is automatic for open-source / GPL-compatible projects.
- **Using `mayaastrolib` in a closed-source commercial product:** you
  must obtain a commercial Swiss Ephemeris license from Astrodienst.
  This is not unique to `mayaastrolib` — it applies to any astrology
  software that uses Swiss Ephemeris.

`mayaastrolib`'s MIT license is real, but it doesn't override the
licensing of its dependencies. The MIT license applies to the
astrology code in this repository; the GPL applies to the
ephemeris computation Swiss Ephemeris performs on your behalf.

## Development dependencies

These are NOT shipped to users; they are used only when developing
or testing `mayaastrolib`.

- **`skyfield`** (MIT) — used by `tests/golden/generate_fixtures.py`
  to generate independent astronomical reference data for golden
  tests. Not a runtime dependency.

## Future direction

If you require a license-clean astronomy backend for commercial
closed-source use, please file an issue. Building a pure-Python /
MIT astronomy backend (using e.g. VSOP87 or JPL DE-series via
Skyfield as runtime, not just dev) is a significant undertaking
but on the table for a future major version if there is real
demand.
```

---

### Part 6: Update CHANGELOG.md

Under `[Unreleased]`:

```markdown
### Added
- Golden test suite at `tests/golden/`:
  - `test_planet_positions.py` — verifies planet positions against Skyfield reference for three charts (Einstein, Kahlo, Amundsen)
  - `test_self_consistency.py` — invariant tests for houses, planets, aspects, and symbolic charts
  - `generate_fixtures.py` — Skyfield-based fixture generator, run manually
  - `fixtures.json` — frozen reference data
  - `README.md` — methodology documentation
- `LICENSING.md` at repo root — clarifies the MIT-mayaastrolib + GPL-Swiss-Ephemeris situation for users
- Skyfield as a dev dependency (test infrastructure only; not shipped to users)

### Changed (test infrastructure)
- Test count: ~198 → ~200+ (golden suite adds ~6 tests with subTest reporting per chart/planet)
- Coverage may shift slightly as golden tests exercise different paths than structural tests
```

---

## Verification

```bash
# Set up venv
python3 -m venv .venv-task014
.venv-task014/bin/pip install -e ".[dev]"

# Generate fixtures (one-time, manual)
.venv-task014/bin/python tests/golden/generate_fixtures.py
# Output: Wrote 3 fixtures to tests/golden/fixtures.json

# Run only the golden tests
.venv-task014/bin/pytest tests/golden/ -v

# Run the full suite — should be 200+ tests passing
.venv-task014/bin/pytest tests/ -v 2>&1 | tail -20
```

Capture all of this output in PROJECT-LOG.md.

If any golden test fails, **investigate before adjusting anything**:

1. First: is the LMT-to-UTC conversion correct in `generate_fixtures.py`? Recompute by hand: `UTC = LMT - longitude_degrees / 15`.
2. Second: take the same date/time/location to astro.com. Does astro.com agree with Skyfield, or with mayaastrolib? If astro.com agrees with mayaastrolib, the Skyfield fixture is wrong (likely an input error). If astro.com agrees with Skyfield, mayaastrolib has a real issue.
3. Third: if Placidus on the high-latitude chart fails, it might be a real Placidus instability. Document in PROJECT-LOG.md and decide whether to adjust the chart's date/time, mark `expectedFailure`, or expand scope.

Do NOT regenerate fixtures to make tests pass. If something is wrong, fix the cause, not the symptom.

---

## Out of scope

- Adding houses or aspects to the Skyfield-generated fixtures (Skyfield doesn't compute these)
- Implementing native astronomy in mayaastrolib (deferred to a possible future major version)
- Vedic / sidereal fixtures (Phase 2; will need their own ayanamsa-aware fixture generator)
- Type hints
- Performance work

## Process

1. Branch:

   ```
   git checkout development
   git pull origin development
   git checkout -b task-014-golden-fixtures
   ```

2. Suggested commit structure:
   - `build: add skyfield as dev dependency`
   - `feat: add tests/golden/generate_fixtures.py with three reference charts`
   - `feat: add tests/golden/fixtures.json (committed reference data)`
   - `test: add tests/golden/test_planet_positions.py (Skyfield-anchored)`
   - `test: add tests/golden/test_self_consistency.py (invariants)`
   - `docs: add tests/golden/README.md and LICENSING.md`
   - `docs: update CHANGELOG for Task 014`

3. Pre-completion checklist:
   - `ruff format --check .` passes
   - `ruff check .` passes
   - `mypy mayaastrolib/` — no new errors
   - `pytest -x` passes — all tests including golden suite
   - `pytest tests/golden/ -v` shows clean output for all three charts
   - The Skyfield-generated fixtures.json is committed (not gitignored)
   - The .skyfield-data/ cache directory is gitignored (verify)

4. PROJECT-LOG.md entry must include:
   - Skyfield version actually pinned (look up latest stable)
   - The exact LMT-to-UTC conversions used for each chart, with longitude math shown
   - Cross-check results: astro.com Sun position vs Skyfield Sun position for each chart (within 1 arcmin?)
   - Any tolerances that were tight (close to ±2') — these are signals worth documenting
   - Whether the Amundsen high-latitude chart's Placidus computation succeeded or required adjustment

5. Push:

   ```
   git push -u origin task-014-golden-fixtures
   ```

6. Verify CI green on all three Python versions.

7. DO NOT merge. Leave for human review.

## Definition of done

- `tests/golden/` directory exists with all five files
- `LICENSING.md` exists at repo root
- Skyfield is in `[project.optional-dependencies] dev`
- `generate_fixtures.py` runs and produces valid `fixtures.json`
- `test_planet_positions.py` passes for all three charts × all 10 modern planets within ±2 arcminute tolerance
- `test_self_consistency.py` passes all invariant tests across all three test charts
- All existing 198+ tests still pass
- CI green
- CHANGELOG and LICENSING updated

## If something goes wrong

**Most likely failure: Placidus on the Amundsen chart.** At 59°N in mid-July, Placidus may produce mathematically unstable house cusps. If self-consistency tests fail for the high-latitude chart:

1. First: try adjusting the date/time slightly (e.g. winter solstice instead of summer). Placidus is less unstable away from the seasonal extremes. If a more stable date works, change Amundsen's "test date" in `generate_fixtures.py` and `test_self_consistency.py` while keeping his real birthday in a comment.
2. Second: if no date works at 59°N, that's a real library limitation worth documenting. Mark the relevant test `expectedFailure` with a clear reason. Add a follow-up to IDEAS.md about high-latitude Placidus.
3. Do NOT silently switch to a different house system — that hides the limitation.

**Second most likely failure: LMT conversion errors.** If Skyfield produces positions that disagree with astro.com by more than 2 arcminutes (well above tolerance), the input data is wrong. Recompute LMT-to-UTC by hand and verify. Common errors:
- Forgetting the longitude sign (East positive, West negative)
- Using mean solar time instead of LMT (they're not exactly the same)
- Using Civil Time (which adds whole-hour offsets) instead of LMT

**Third most likely failure: Skyfield version mismatch with example code.** Skyfield's API has changed across versions. If the snippets in this prompt don't quite match the installed Skyfield's API, adapt to what's actually there. Skyfield's documentation at https://rhodesmill.org/skyfield/ is comprehensive.

If something fundamental breaks:

1. `git reset --hard development`
2. Detailed failure report in PROJECT-LOG.md
3. Commit on `task-014-failed-attempt-1`
4. Push and stop

This task is meaty enough that a clean failure with diagnosis is better than a half-broken push.

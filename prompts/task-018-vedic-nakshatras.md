# Task 018: Vedic Nakshatras

## Context

You are working in the `mayaastrolib` repository. Before doing anything:

1. Read `CLAUDE.md` in full.
2. Read `docs/2026-05-11-vedic-extension-spec.md` — particularly the `vedic/nakshatras.py` section under "Per-module API design".
3. Read `prompts/task-017-vedic-foundation.md` — this task is a direct successor and reuses Task 017's primitives (`vedic.ayanamsa.to_sidereal`, the `Chart.zodiac` kwarg).
4. Confirm Task 017 has merged to `development`:

   ```
   git log --oneline development -10 | grep task-017
   ```

   You should see the Task 017 merge commit. If not, STOP and complete Task 017 first.

5. Read `mayaastrolib/vedic/ayanamsa.py` (shipped by Task 017) — note the import pattern and docstring style.
6. Read `mayaastrolib/object.py` — note the `Object` class shape; `Nakshatra` will be a small dataclass-style result type, not an extension of `Object`.
7. Confirm `pytest tests/` passes — expected ~230 tests after Task 017.

## Why this task exists

The 27 nakshatras are the unit currency of Vedic predictive astrology: Vimshottari dasha is *defined* by which nakshatra the natal Moon falls in, panchang uses them for daily quality, transits to nakshatras drive timing techniques. Without a clean nakshatra primitive every downstream module reinvents the arithmetic.

This task ships pure nakshatra arithmetic — name, lord, pada — over sidereal longitude. No prediction, no scoring, no interpretation. Just the boundary table and the lookup.

## Design decisions (already made — do not relitigate)

- **Sanskrit names** per Task 017's foundation decision. Use Devanagari transliteration in the spelling we've adopted in the spec (`Ashwini`, `Bharani`, `Krittika`, …) — IAST diacritics are not needed; ASCII is enough.
- **The 27-nakshatra zodiac is exact division of 360° into 13°20' segments.** Each nakshatra has 4 padas of 3°20'. No partial-nakshatra ambiguity — boundaries are deterministic.
- **Nakshatra lookup operates on SIDEREAL longitude.** Tropical longitudes don't map cleanly to nakshatras (Ashwini's western edge is fixed sidereally, not tropically). If a caller passes a tropical longitude by accident, they get the wrong nakshatra silently — but that's their bug, not ours; this module accepts the longitude as-given.
- **The Vimshottari lord cycle is FIXED.** Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury — repeats three times to fill 27. This is BPHS canonical, no alternates.
- **`Nakshatra` is a frozen dataclass.** Read-only result, no mutation, no methods beyond `__repr__`. Future code (Task 020) computes dasha balances *from* a Nakshatra; it doesn't mutate the Nakshatra itself.
- **`tarabala` returns a 1..9 integer** (the cycle position), not the qualitative label ("Janma", "Sampat", "Vipat", ...). The label is presentational; the integer is the primitive. A presentation helper can be added in a downstream task if needed.

## Task scope

### Part 1: Module skeleton

Create `mayaastrolib/vedic/nakshatras.py`:

```python
"""Nakshatra (lunar mansion) arithmetic for Vedic Jyotisha.

The 27 nakshatras divide the sidereal zodiac into equal 13°20' segments.
Each nakshatra has:

- A name (Sanskrit)
- A ruling planet ("lord") in the Vimshottari Mahadasha cycle
- 4 padas (quarters), each 3°20'

References:
- Brihat Parashara Hora Shastra (BPHS) ch. 3, 9
- Muhurta Chintamani (for tarabala)
"""

from dataclasses import dataclass

from mayaastrolib import const
from mayaastrolib.datetime import Datetime
from mayaastrolib.vedic import ayanamsa as _ay


NAKSHATRA_NAMES = [
    "Ashwini",     "Bharani",     "Krittika",
    "Rohini",      "Mrigashira",  "Ardra",
    "Punarvasu",   "Pushya",      "Ashlesha",
    "Magha",       "Purva Phalguni", "Uttara Phalguni",
    "Hasta",       "Chitra",      "Swati",
    "Vishakha",    "Anuradha",    "Jyeshtha",
    "Mula",        "Purva Ashadha", "Uttara Ashadha",
    "Shravana",    "Dhanishtha",  "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

# Vimshottari rulership cycle — repeats three times over 27 nakshatras.
_VIMSHOTTARI_CYCLE = [
    const.KETU, const.VENUS, const.SUN,
    const.MOON, const.MARS, const.RAHU,
    const.JUPITER, const.SATURN, const.MERCURY,
]
NAKSHATRA_LORDS = _VIMSHOTTARI_CYCLE * 3

assert len(NAKSHATRA_NAMES) == 27
assert len(NAKSHATRA_LORDS) == 27

# Each nakshatra spans 13°20' = 13.333... degrees.
NAKSHATRA_SPAN_DEG = 360.0 / 27.0   # = 13.333...
PADA_SPAN_DEG = NAKSHATRA_SPAN_DEG / 4.0  # = 3.333...


@dataclass(frozen=True)
class Nakshatra:
    """A nakshatra at a particular sidereal longitude.

    Attributes:
        name: The Sanskrit name, e.g. "Ashwini".
        lord: The Vimshottari ruling planet ID, e.g. `const.KETU`.
        pada: Quarter index, 1..4.
        index: Zero-based index into `NAKSHATRA_NAMES`, 0..26.
    """
    name: str
    lord: str
    pada: int
    index: int


def of_longitude(sidereal_lon: float) -> Nakshatra:
    """Return the nakshatra at the given sidereal longitude.

    The longitude is reduced modulo 360 — callers needn't normalise first.

    Raises ValueError if the longitude is non-finite.
    """
    if not (sidereal_lon == sidereal_lon and sidereal_lon - sidereal_lon == 0):
        # NaN or +/-inf
        raise ValueError(f"sidereal_lon must be finite; got {sidereal_lon!r}")
    lon = sidereal_lon % 360.0
    idx = int(lon // NAKSHATRA_SPAN_DEG)
    # Pada is 1-indexed
    within = lon - idx * NAKSHATRA_SPAN_DEG
    pada = int(within // PADA_SPAN_DEG) + 1
    return Nakshatra(
        name=NAKSHATRA_NAMES[idx],
        lord=NAKSHATRA_LORDS[idx],
        pada=pada,
        index=idx,
    )


def janma_nakshatra(chart, ayanamsa: str = const.AYANAMSA_LAHIRI) -> Nakshatra:
    """Return the natal Moon's nakshatra ("birth star").

    If `chart.zodiac == ZODIAC_SIDEREAL`, reads the Moon's sidereal longitude
    directly. If `chart.zodiac == ZODIAC_TROPICAL`, applies `to_sidereal` with
    the supplied `ayanamsa` (default Lahiri) before computing the nakshatra.

    Args:
        chart: A `mayaastrolib.chart.Chart`.
        ayanamsa: Used only when the chart is tropical; ignored otherwise.
    """
    moon = chart.get(const.MOON)
    if chart.zodiac == const.ZODIAC_SIDEREAL:
        sid_lon = moon.lon
    else:
        sid_lon = _ay.to_sidereal(moon.lon, chart.date, ayanamsa=ayanamsa)
    return of_longitude(sid_lon)


def tarabala(natal_moon_nak: Nakshatra, transit_moon_nak: Nakshatra) -> int:
    """9-tara cycle position, 1..9.

    Counts nakshatras from the natal Moon's nakshatra to the transit Moon's
    nakshatra (inclusive forward), modulo 9. Per Muhurta Chintamani 6.6.

    The 1..9 numeric result maps to the qualitative names (Janma, Sampat,
    Vipat, Kshema, Pratyak, Sadhana, Naidhana, Mitra, Param Mitra), but the
    label-to-meaning mapping is presentational and lives downstream.
    """
    forward = (transit_moon_nak.index - natal_moon_nak.index) % 27
    return (forward % 9) + 1
```

### Part 2: Tests

Add `tests/test_vedic_nakshatras.py`:

```python
"""Tests for Vedic nakshatra arithmetic — Task 018."""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import nakshatras as nak


class NakshatraBoundaryTests(unittest.TestCase):
    """Boundary cases — each nakshatra starts at a known sidereal longitude."""

    def test_zero_degrees_is_ashwini_pada_1(self):
        n = nak.of_longitude(0.0)
        self.assertEqual(n.name, "Ashwini")
        self.assertEqual(n.lord, const.KETU)
        self.assertEqual(n.pada, 1)
        self.assertEqual(n.index, 0)

    def test_13_20_is_bharani_pada_1(self):
        # End of Ashwini = start of Bharani at exactly 13°20'
        n = nak.of_longitude(13.0 + 20.0/60.0)
        self.assertEqual(n.name, "Bharani")
        self.assertEqual(n.lord, const.VENUS)
        self.assertEqual(n.pada, 1)

    def test_just_before_bharani_is_ashwini_pada_4(self):
        n = nak.of_longitude(13.0 + 19.0/60.0)
        self.assertEqual(n.name, "Ashwini")
        self.assertEqual(n.pada, 4)

    def test_360_wraps_to_ashwini(self):
        n = nak.of_longitude(360.0)
        self.assertEqual(n.name, "Ashwini")

    def test_negative_longitude_wraps(self):
        # -1° should map to ~359° → Revati
        n = nak.of_longitude(-1.0)
        self.assertEqual(n.name, "Revati")

    def test_all_27_nakshatras_have_correct_lords(self):
        """Spot check: lord at each segment matches the Vimshottari cycle."""
        expected = [
            (0, const.KETU), (1, const.VENUS), (2, const.SUN),
            (3, const.MOON), (4, const.MARS), (5, const.RAHU),
            (6, const.JUPITER), (7, const.SATURN), (8, const.MERCURY),
            (9, const.KETU),  # cycle repeats
            (18, const.KETU), # third cycle
            (26, const.MERCURY),  # last nakshatra
        ]
        for idx, lord in expected:
            mid_lon = (idx + 0.5) * nak.NAKSHATRA_SPAN_DEG
            n = nak.of_longitude(mid_lon)
            self.assertEqual(n.lord, lord, f"Nakshatra {idx} ({n.name})")


class NakshatraPadaTests(unittest.TestCase):
    """Pada arithmetic — 4 padas per nakshatra of 3°20' each."""

    def test_pada_at_each_quarter(self):
        # In Ashwini (starts at 0°): pada 1 at 0°, pada 2 at 3°20', pada 3 at 6°40', pada 4 at 10°
        cases = [
            (0.5, 1), (3.0, 1),
            (3.5, 2), (6.0, 2),
            (7.0, 3), (9.0, 3),
            (10.5, 4), (13.0, 4),
        ]
        for lon, expected_pada in cases:
            n = nak.of_longitude(lon)
            self.assertEqual(n.pada, expected_pada, f"lon={lon}")


class JanmaNakshatraTests(unittest.TestCase):
    """Birth-star computation against a real chart."""

    def test_natal_moon_nakshatra_sidereal_chart(self):
        date = Datetime("1947/08/15", "00:00", "+05:30")  # Indian midnight
        pos = GeoPos("28n36", "77e12")  # Delhi
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        n = nak.janma_nakshatra(chart)
        # The Moon's sidereal longitude at this moment is in some
        # specific nakshatra — verify the lookup is internally
        # consistent: the Moon's sidereal lon should map to the
        # returned nakshatra.
        moon_lon = chart.get(const.MOON).lon
        self.assertEqual(n, nak.of_longitude(moon_lon))

    def test_natal_moon_nakshatra_tropical_chart_with_ayanamsa(self):
        date = Datetime("1947/08/15", "00:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        tropical_chart = Chart(date, pos)
        sidereal_chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        # The natal nakshatra should be the same whether we ask via a
        # tropical chart (with ayanamsa applied) or via a sidereal chart.
        n_from_tropical = nak.janma_nakshatra(tropical_chart)
        n_from_sidereal = nak.janma_nakshatra(sidereal_chart)
        self.assertEqual(n_from_tropical.name, n_from_sidereal.name)
        self.assertEqual(n_from_tropical.pada, n_from_sidereal.pada)


class TarabalaTests(unittest.TestCase):

    def test_self_to_self_is_1(self):
        ashwini = nak.of_longitude(0.0)
        self.assertEqual(nak.tarabala(ashwini, ashwini), 1)

    def test_natal_to_next_is_2(self):
        natal = nak.of_longitude(0.0)         # Ashwini
        transit = nak.of_longitude(15.0)      # Bharani
        self.assertEqual(nak.tarabala(natal, transit), 2)

    def test_natal_to_9_forward_is_9(self):
        natal = nak.of_longitude(0.0)         # idx 0
        # idx 8 = Ashlesha
        transit = nak.of_longitude(8 * nak.NAKSHATRA_SPAN_DEG + 1.0)
        self.assertEqual(nak.tarabala(natal, transit), 9)

    def test_natal_to_10_forward_wraps_to_1(self):
        natal = nak.of_longitude(0.0)
        transit = nak.of_longitude(9 * nak.NAKSHATRA_SPAN_DEG + 1.0)
        self.assertEqual(nak.tarabala(natal, transit), 1)


class FrozenDataclassTests(unittest.TestCase):

    def test_nakshatra_is_frozen(self):
        n = nak.of_longitude(0.0)
        with self.assertRaises(Exception):
            n.name = "Bharani"  # type: ignore[misc]
```

### Part 3: Update CHANGELOG.md

Under `[Unreleased]`:

```markdown
### Added (Task 018 — Vedic nakshatras)
- `mayaastrolib/vedic/nakshatras.py` — 27-nakshatra arithmetic.
  - `NAKSHATRA_NAMES`, `NAKSHATRA_LORDS` — canonical tables.
  - `of_longitude(sidereal_lon)` — sidereal-longitude → `Nakshatra`.
  - `janma_nakshatra(chart, ayanamsa=...)` — natal Moon's nakshatra.
    Accepts both tropical and sidereal charts.
  - `tarabala(natal_nak, transit_nak)` — 1..9 tara cycle position
    per Muhurta Chintamani 6.6.
- `Nakshatra` is a frozen dataclass — `name`, `lord`, `pada`, `index`.
```

## Out of scope

- Tarabala qualitative labels ("Janma", "Sampat", ...) — presentational, downstream
- Nakshatra-pada-based varga sign assignment (used in some D9 schemes) — Task 019
- Vimshottari dasha balance computation — Task 020 (depends on this module's `janma_nakshatra`)
- Tithi, yoga, karana — separate panchang task if requested
- Nakshatra deity / symbol / gana metadata — presentational, downstream

## Process

1. Branch:

   ```
   git checkout development
   git pull origin development
   git checkout -b task-018-vedic-nakshatras
   ```

2. Suggested commits:
   - `feat: add vedic.nakshatras with 27-nakshatra arithmetic`
   - `test: cover nakshatra boundaries, padas, tarabala, janma_nakshatra`
   - `docs: update CHANGELOG and PROJECT-LOG for Task 018`

3. Pre-completion checklist:
   - `ruff format --check .` passes
   - `ruff check .` passes
   - `mypy mayaastrolib/` — no new errors
   - `pytest -x` passes — ~230 existing + ~15 new
   - The Task 017 backwards-compatibility tests still pass

4. PROJECT-LOG.md entry must include:
   - Confirmation that `NAKSHATRA_LORDS` order matches BPHS (Ketu starts at Ashwini)
   - The expected nakshatra for the 1947-08-15 Delhi midnight Moon (your test fixture's "expected" should match a published source)

5. Push, verify CI green, DO NOT merge.

## Definition of done

- `mayaastrolib/vedic/nakshatras.py` exists with the API above
- All 5 test classes pass
- 27 nakshatras × 4 padas × correct lord assignment verified
- `janma_nakshatra` produces the same nakshatra from a tropical-with-ayanamsa chart as from a sidereal chart
- CHANGELOG entry; PROJECT-LOG entry
- CI green

## If something goes wrong

**Most likely failure: `const.RAHU` / `const.KETU` don't exist** — the codebase historically used `NORTH_NODE` / `SOUTH_NODE` names. Check `const.py` first; if so, alias them:

```python
const.RAHU = const.NORTH_NODE  # if needed
const.KETU = const.SOUTH_NODE
```

or use the existing names throughout. Whichever, document the choice in PROJECT-LOG.

**Second: pada arithmetic off-by-one.** The boundary between pada 1 and pada 2 is at *3°20' within the nakshatra*, not at 3°00'. The test cases above pin both sides. If your arithmetic is off by 20' you'll fail `test_pada_at_each_quarter`.

**Third: the `janma_nakshatra` consistency test fails.** Means the sidereal-chart Moon longitude doesn't equal `tropical_moon - ayanamsa` mod 360 — which would mean Task 017's shift isn't right. Don't fix it in Task 018; surface the regression to Task 017 territory and stop.

If something fundamental breaks:

1. `git reset --hard development`
2. Failure report in PROJECT-LOG.md
3. Commit on `task-018-failed-attempt-1`
4. Push and stop

Smallest task in the P0 chain. Failure here almost certainly means a Task 017 latent bug — go back, don't push through.

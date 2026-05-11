# Task 017: Vedic Foundation — Ayanamsa + Sidereal Mode

## Context

You are working in the `mayaastrolib` repository. Before doing anything:

1. Read `CLAUDE.md` in full.
2. Read `docs/2026-05-11-vedic-extension-spec.md` — the full extension spec. This task implements the foundation only (P0 — `vedic/ayanamsa.py` plus the Chart-level wiring). Tasks 018–020 build on it.
3. Read `docs/REVIEW-2026-05-08-followup.md` — particularly the "Phase 2 readiness" section, which is the architectural justification for what's below.
4. Read `mayaastrolib/chart.py` end to end. Identify the `Chart.__init__` signature and how it threads through to `ephem.getObjectList` / `ephem.getHouses`.
5. Read `mayaastrolib/ephem/swe.py`, `ephem/eph.py`, `ephem/ephem.py` — the three-layer ephemeris stack. The sidereal flag threads through all three.
6. Read `mayaastrolib/const.py` — note the existing constant naming conventions; add the new ones in the same style.
7. Read `mayaastrolib/object.py` — confirm `Object.with_longitude(lon, *, preserve_speed=True)` from Task 010 exists. The sidereal shift uses this primitive.
8. Read one existing task journal to match the writing style: `docs/PROJECT-LOG.md` entries for Tasks 014 and 015 are the closest precedents (golden tests + a behaviour-changing init).
9. Confirm `development` is at the post-Task-016 state:

   ```
   git log --oneline development -5
   ```

   You should see `4b185d3` (re-review PROJECT-LOG) or `743e538` (Task 016 docs) at the top.

10. Confirm `pytest tests/` passes — should be 215 tests.

## Why this task exists

The project's stated Goal #2 is unifying Western (tropical) and Vedic (sidereal) astrology in a single coherent API. Phases 0–1 (modernisation, ergonomics, golden tests) are done. The platform-review follow-up confirmed the codebase is ready: layered ephem stack at the right seam, `Object.with_longitude` already in place, golden-test infrastructure already shipped.

Task 017 is **the architectural commitment**. Every downstream Vedic module (Tasks 018–026) depends on the decision made here for how sidereal mode is exposed. Get this right and the rest are routine; get it wrong and they all inherit the wrong shape.

## Design decisions (already made — do not relitigate)

These are not open for discussion in this task. Per the spec's open questions, the chosen answers are:

- **Per-Chart kwarg, not module-level config.** `Chart(date, pos, zodiac=ZODIAC_TROPICAL, ayanamsa=AYANAMSA_LAHIRI)`. Default `zodiac=ZODIAC_TROPICAL` for backwards compatibility — existing callers must see zero behaviour change.
- **Lahiri only for this task.** KP, Raman, Fagan-Bradley are deferred to Task 017b (or later) when a consumer needs them. YAGNI per CLAUDE.md.
- **Sanskrit naming for downstream Vedic modules.** Not relevant to this task (no Sanskrit terms yet) but document the decision so Tasks 018+ inherit it.
- **`ayanamsa` kwarg is ignored when `zodiac=ZODIAC_TROPICAL`.** Validate with a warning *only if both `zodiac=ZODIAC_TROPICAL` and a non-default `ayanamsa` are passed* — most callers will hit this by forgetting the `zodiac` flag, and silently ignoring it is hostile.
- **Thread safety: lock-guarded set_sid_mode + calc_ut pair in the sidereal path.** pyswisseph's `swe.set_sid_mode` is process-global. We pay the same price Task 008 paid for `setTerms`/`setFaces`: a `threading.Lock` around the `(set_sid_mode, calc_ut)` atomic pair in the sidereal path. Tropical calls pass no `SEFLG_SIDEREAL` flag and are unaffected by the sid_mode setting, so they're not lock-contended.
- **No `SIDM_NONE` reset on exit.** The mode just gets re-set on each sidereal call. Tropical paths ignore it. This is simpler than a reset-on-exit context manager and the cost is one `set_sid_mode` call per sidereal calc — measured in microseconds.

## Task scope

Six parts.

### Part 1: New constants in `const.py`

Add to `mayaastrolib/const.py` in a clearly-labelled `# --- Vedic / sidereal ---` section:

```python
# --- Zodiac mode ---
ZODIAC_TROPICAL = "tropical"
ZODIAC_SIDEREAL = "sidereal"

# --- Ayanamsa (sidereal-mode offsets) ---
AYANAMSA_LAHIRI = "lahiri"
# Additional ayanamsas (KP, Raman, Fagan-Bradley) will be added in Task 017b.

LIST_ZODIACS = [ZODIAC_TROPICAL, ZODIAC_SIDEREAL]
LIST_AYANAMSAS = [AYANAMSA_LAHIRI]
```

### Part 2: New package `mayaastrolib/vedic/`

Create:

```
mayaastrolib/vedic/
├── __init__.py     # Empty marker; future modules import from this
└── ayanamsa.py     # This task's main module
```

`mayaastrolib/vedic/__init__.py`:

```python
"""Vedic Jyotisha extensions for mayaastrolib.

Contains modules for sidereal astrology following the Vedic tradition:
ayanamsa, nakshatras, divisional charts, Vimshottari dasha, ashtakavarga,
sade sati, upagrahas, tajika, KP, and yoga detection.

This package is loaded only when explicitly imported — users who only need
Western/Hellenistic features pay no cost for the Vedic modules.
"""
```

`mayaastrolib/vedic/ayanamsa.py`:

```python
"""Ayanamsa computation — the offset between tropical and sidereal zodiacs.

The ayanamsa is a slowly-varying angle (~50 arcseconds/year) measuring
precession of the equinoxes since the canonical epoch of each tradition.
Lahiri ayanamsa is the standard for Indian Vedic astrology; the Indian
Astronomical Ephemeris uses it.

References:
- Indian Astronomical Ephemeris (Lahiri canonical implementation)
- pyswisseph `swe.get_ayanamsa(jd)` (matches Lahiri at IAU 1976 precision)
- IAU 1976 nutation/precession model
"""

import threading

from mayaastrolib import const
from mayaastrolib.datetime import Datetime
from mayaastrolib.ephem import swe as _swe_module

# Map our constant names to pyswisseph integer mode IDs.
# Only Lahiri for now; Task 017b adds the rest.
_AYANAMSA_TO_SWE_MODE = {
    const.AYANAMSA_LAHIRI: None,  # filled lazily — see _swe_mode_for()
}

_AYANAMSA_LOCK = threading.Lock()


def _swe_mode_for(ayanamsa: str) -> int:
    """Return the pyswisseph integer mode constant for a named ayanamsa."""
    import swisseph
    if _AYANAMSA_TO_SWE_MODE[const.AYANAMSA_LAHIRI] is None:
        _AYANAMSA_TO_SWE_MODE[const.AYANAMSA_LAHIRI] = swisseph.SIDM_LAHIRI
    if ayanamsa not in _AYANAMSA_TO_SWE_MODE:
        raise ValueError(
            f"Unknown ayanamsa {ayanamsa!r}; supported: {list(_AYANAMSA_TO_SWE_MODE)}"
        )
    return _AYANAMSA_TO_SWE_MODE[ayanamsa]


def lahiri(date: Datetime) -> float:
    """Lahiri ayanamsa in degrees at the given date.

    The Lahiri ayanamsa (named for N. C. Lahiri, who chaired the 1955 Indian
    Calendar Reform Committee) is the canonical sidereal offset used by the
    Indian Astronomical Ephemeris. Returns degrees; positive means sidereal
    longitude < tropical longitude.

    Example::

        from mayaastrolib.datetime import Datetime
        from mayaastrolib.vedic.ayanamsa import lahiri
        lahiri(Datetime('2000/01/01', '12:00', '+00:00'))  # ~23.85°
    """
    import swisseph
    with _AYANAMSA_LOCK:
        swisseph.set_sid_mode(_swe_mode_for(const.AYANAMSA_LAHIRI))
        jd = date.jd
        return swisseph.get_ayanamsa(jd)


def to_sidereal(
    tropical_lon: float, date: Datetime, ayanamsa: str = const.AYANAMSA_LAHIRI
) -> float:
    """Convert a tropical longitude to sidereal under the given ayanamsa.

    Args:
        tropical_lon: Tropical longitude in degrees (0..360).
        date: The moment at which to compute the ayanamsa offset.
        ayanamsa: One of `const.LIST_AYANAMSAS`. Defaults to Lahiri.

    Returns:
        Sidereal longitude in degrees, normalised to [0, 360).
    """
    if ayanamsa == const.AYANAMSA_LAHIRI:
        offset = lahiri(date)
    else:
        raise ValueError(
            f"Unknown ayanamsa {ayanamsa!r}; supported: {const.LIST_AYANAMSAS}"
        )
    return (tropical_lon - offset) % 360.0
```

### Part 3: Thread-safe sidereal call wrapper in `ephem/swe.py`

Add a lock-guarded helper at module level in `mayaastrolib/ephem/swe.py`:

```python
import threading

_SIDEREAL_CALC_LOCK = threading.Lock()


def _sidereal_calc_ut(jd, body, flags, ayanamsa):
    """Thread-safe sidereal `calc_ut` call.

    pyswisseph's `set_sid_mode` mutates process-global state. This wrapper
    holds a lock around the `(set_sid_mode, calc_ut)` pair so that concurrent
    sidereal computations for different ayanamsas (rare but possible) don't
    interleave. Tropical calls bypass this entirely and are not lock-contended.
    """
    import swisseph
    from mayaastrolib.vedic.ayanamsa import _swe_mode_for
    sidereal_flags = flags | swisseph.FLG_SIDEREAL
    with _SIDEREAL_CALC_LOCK:
        swisseph.set_sid_mode(_swe_mode_for(ayanamsa))
        return swisseph.calc_ut(jd, body, sidereal_flags)
```

Then update the existing `sweObject(...)` / `sweObjectLon(...)` calls (around `swe.py:60-90`) to branch on whether sidereal computation was requested. The cleanest pattern:

- Add a `zodiac` and `ayanamsa` parameter to the public `swe.py` functions, defaulting to `(ZODIAC_TROPICAL, AYANAMSA_LAHIRI)`
- In the tropical path: existing `swisseph.calc_ut(jd, body)` call unchanged
- In the sidereal path: call `_sidereal_calc_ut(jd, body, flags, ayanamsa)` instead

The `eph.py` and `ephem.py` layers thread the two parameters through. The `Chart.__init__` resolves them once and passes them down.

### Part 4: `Chart.__init__` kwarg additions

In `mayaastrolib/chart.py`, extend the constructor:

```python
class Chart:
    def __init__(
        self,
        date,
        pos,
        hsys=const.HOUSES_DEFAULT,
        IDs=const.LIST_OBJECTS_TRADITIONAL,
        zodiac=const.ZODIAC_TROPICAL,
        ayanamsa=const.AYANAMSA_LAHIRI,
    ):
        if zodiac not in const.LIST_ZODIACS:
            raise ValueError(
                f"Unknown zodiac {zodiac!r}; supported: {const.LIST_ZODIACS}"
            )
        if ayanamsa not in const.LIST_AYANAMSAS:
            raise ValueError(
                f"Unknown ayanamsa {ayanamsa!r}; supported: {const.LIST_AYANAMSAS}"
            )
        if zodiac == const.ZODIAC_TROPICAL and ayanamsa != const.AYANAMSA_LAHIRI:
            import warnings
            warnings.warn(
                f"ayanamsa={ayanamsa!r} ignored because zodiac=ZODIAC_TROPICAL; "
                f"did you mean to pass zodiac=ZODIAC_SIDEREAL?",
                UserWarning,
                stacklevel=2,
            )
        self.zodiac = zodiac
        self.ayanamsa = ayanamsa
        # ... existing __init__ body, but threading zodiac+ayanamsa
        # through to getObjectList / getHouses
```

Houses are computed sidereally via `swisseph.houses_ex2(...)` with the sidereal flag. Threadthrough is the same shape as planet positions.

Crucially: **default behaviour is unchanged.** `Chart(date, pos)` with no `zodiac=` kwarg constructs a tropical chart exactly as before. Every existing test passes without modification. This is the backwards-compatibility commitment.

### Part 5: Tests

Add `tests/test_vedic_foundation.py`. Four test classes:

```python
"""Tests for the Vedic foundation — Task 017."""

import unittest
import warnings

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import ayanamsa as ay


class AyanamsaTests(unittest.TestCase):
    """Unit tests for the ayanamsa module."""

    def test_lahiri_j2000_value(self):
        """Lahiri ayanamsa at J2000.0 should match the IAU canonical value.

        Per the Indian Astronomical Ephemeris, Lahiri ayanamsa at J2000.0
        (= 2000-01-01 12:00 UT) is ~23.851° (about 23°51'04").
        """
        date = Datetime("2000/01/01", "12:00", "+00:00")
        value = ay.lahiri(date)
        self.assertAlmostEqual(value, 23.851, places=2)

    def test_lahiri_increases_with_time(self):
        """Ayanamsa is monotonically increasing — precession is one-way."""
        d2000 = Datetime("2000/01/01", "12:00", "+00:00")
        d2024 = Datetime("2024/01/01", "12:00", "+00:00")
        self.assertGreater(ay.lahiri(d2024), ay.lahiri(d2000))

    def test_lahiri_rate_of_change(self):
        """Ayanamsa should grow at ~50 arcsec/year (precession of equinoxes)."""
        d2000 = Datetime("2000/01/01", "12:00", "+00:00")
        d2024 = Datetime("2024/01/01", "12:00", "+00:00")
        delta_arcsec = (ay.lahiri(d2024) - ay.lahiri(d2000)) * 3600
        # 24 years * ~50.3 arcsec/year ≈ 1207 arcsec; allow ±20 arcsec
        self.assertAlmostEqual(delta_arcsec, 1207, delta=20)

    def test_to_sidereal_subtracts_ayanamsa(self):
        date = Datetime("2024/06/01", "12:00", "+00:00")
        offset = ay.lahiri(date)
        sid = ay.to_sidereal(100.0, date)
        self.assertAlmostEqual(sid, (100.0 - offset) % 360.0, places=6)

    def test_to_sidereal_wraps_negative(self):
        date = Datetime("2024/06/01", "12:00", "+00:00")
        # tropical_lon=5°, ayanamsa~24° → sidereal would be -19° → wraps to 341°
        sid = ay.to_sidereal(5.0, date)
        self.assertTrue(0.0 <= sid < 360.0)

    def test_unknown_ayanamsa_raises(self):
        date = Datetime("2024/01/01", "12:00", "+00:00")
        with self.assertRaises(ValueError):
            ay.to_sidereal(100.0, date, ayanamsa="nonexistent")


class ChartZodiacKwargTests(unittest.TestCase):
    """Tests for Chart's new zodiac/ayanamsa kwargs."""

    def setUp(self):
        self.date = Datetime("2024/06/15", "12:00", "+00:00")
        self.pos = GeoPos("28n36", "77e12")  # Delhi

    def test_default_is_tropical(self):
        chart = Chart(self.date, self.pos)
        self.assertEqual(chart.zodiac, const.ZODIAC_TROPICAL)

    def test_sidereal_explicit(self):
        chart = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)
        self.assertEqual(chart.zodiac, const.ZODIAC_SIDEREAL)
        self.assertEqual(chart.ayanamsa, const.AYANAMSA_LAHIRI)

    def test_unknown_zodiac_raises(self):
        with self.assertRaises(ValueError):
            Chart(self.date, self.pos, zodiac="lunar")

    def test_unknown_ayanamsa_raises(self):
        with self.assertRaises(ValueError):
            Chart(
                self.date, self.pos,
                zodiac=const.ZODIAC_SIDEREAL, ayanamsa="bogus",
            )

    def test_warning_on_tropical_with_nondefault_ayanamsa(self):
        # Currently only one ayanamsa, so this branch is hard to trigger
        # until Task 017b lands. Skip until then OR pass an obviously-wrong
        # ayanamsa string and assert ValueError (which fires first).
        pass


class SiderealPositionShiftTests(unittest.TestCase):
    """Sidereal planet positions = tropical - ayanamsa, modulo 360."""

    def test_sun_sidereal_matches_tropical_minus_ayanamsa(self):
        date = Datetime("2024/06/15", "12:00", "+00:00")
        pos = GeoPos("28n36", "77e12")
        tropical = Chart(date, pos)
        sidereal = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        offset = ay.lahiri(date)
        expected_sid_sun = (tropical.get(const.SUN).lon - offset) % 360.0
        actual_sid_sun = sidereal.get(const.SUN).lon
        # Tolerance: ±0.01° (within numerical precision of pyswisseph)
        self.assertAlmostEqual(actual_sid_sun, expected_sid_sun, places=2)

    def test_house_cusps_also_shift(self):
        """If sidereal mode is properly threaded through houses_ex2, the
        house cusps should also be shifted by the ayanamsa."""
        date = Datetime("2024/06/15", "12:00", "+00:00")
        pos = GeoPos("28n36", "77e12")
        tropical = Chart(date, pos)
        sidereal = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        offset = ay.lahiri(date)
        expected_sid_house1 = (tropical.houses[0].lon - offset) % 360.0
        actual_sid_house1 = sidereal.houses[0].lon
        self.assertAlmostEqual(actual_sid_house1, expected_sid_house1, places=2)


class BackwardsCompatibilityTests(unittest.TestCase):
    """No existing-API-call should change behaviour as a result of this task."""

    def test_default_chart_planet_positions_unchanged(self):
        """Sanity: a tropical chart at a known date produces the same positions
        as it did pre-Task-017. We freeze a reference value here."""
        date = Datetime("2000/01/01", "12:00", "+00:00")
        pos = GeoPos("0n00", "0e00")
        chart = Chart(date, pos)
        sun_lon = chart.get(const.SUN).lon
        # Tropical Sun at 2000-01-01 12:00 UT, equator: ~280.5°
        self.assertAlmostEqual(sun_lon, 280.5, places=0)
```

### Part 6: One Vedic golden chart

Add `tests/golden/test_vedic_positions.py` and `tests/golden/vedic_fixtures.json`. Use a single, well-known published Vedic reference chart for verification.

**Recommended reference: J2000.0 equator-Greenwich chart with published Lahiri ayanamsa = 23°51'11" (23.853056°).** This is the simplest possible reference — no geographic ambiguity, the ayanamsa value is canonical, and any deviation flags a bug in the sidereal pipeline immediately.

Compute the expected sidereal positions from the published Lahiri value plus Skyfield-computed tropical positions (re-use the Task 014 Skyfield infrastructure). Tolerance: ±2 arcmin per `CLAUDE.md`.

Document in `tests/golden/README.md` how this differs from the tropical golden charts.

### Part 7: Update CHANGELOG.md

Under `[Unreleased]`:

```markdown
### Added (Task 017 — Vedic foundation)
- New `mayaastrolib/vedic/` package — foundation for the Phase 2 Vedic
  Jyotisha extension. This task ships the foundation only; downstream
  modules (nakshatras, divisional charts, dasha, ...) follow in
  Tasks 018+.
- `mayaastrolib.vedic.ayanamsa.lahiri(date)` — Lahiri ayanamsa in
  degrees at a given date.
- `mayaastrolib.vedic.ayanamsa.to_sidereal(lon, date, ayanamsa=...)`
  — convert a tropical longitude to sidereal.
- `Chart` now accepts `zodiac=ZODIAC_TROPICAL|ZODIAC_SIDEREAL` and
  `ayanamsa=AYANAMSA_LAHIRI` kwargs. Default is tropical — no
  behaviour change for existing callers.
- New constants in `const`: `ZODIAC_TROPICAL`, `ZODIAC_SIDEREAL`,
  `AYANAMSA_LAHIRI`, `LIST_ZODIACS`, `LIST_AYANAMSAS`.
- New golden test `tests/golden/test_vedic_positions.py` anchors a
  Lahiri-shifted chart at J2000.0.

### Architectural notes
- Sidereal mode is resolved at `Chart` construction. The
  `(set_sid_mode, calc_ut)` pair is lock-guarded in
  `mayaastrolib/ephem/swe.py::_sidereal_calc_ut` so concurrent
  sidereal chart construction with different ayanamsas is safe.
  Tropical charts bypass the lock entirely.
```

## Out of scope

- Additional ayanamsas (KP, Raman, Fagan-Bradley) — Task 017b
- Nakshatra arithmetic — Task 018
- Divisional charts (vargas) — Task 019
- Vimshottari dasha — Task 020
- Sidereal mode in `solarReturn`, `profections`, `directions` — separate follow-up
- House-system semantics under sidereal (most users want Whole-Sign or Sripati for Vedic; we keep the chosen `hsys=` honest for now and add `HOUSES_WHOLE_SIGN` as a separate task if a consumer asks)
- Type hints — Phase 1 follow-up

## Process

1. Branch:

   ```
   git checkout development
   git pull origin development
   git checkout -b task-017-vedic-foundation
   ```

2. Suggested commits:
   - `feat: add vedic package with ayanamsa module (lahiri)`
   - `feat: thread zodiac/ayanamsa kwargs through Chart and ephem layers`
   - `test: cover ayanamsa, sidereal chart construction, backwards compat`
   - `test: add Vedic golden chart at J2000.0`
   - `docs: update CHANGELOG and PROJECT-LOG for Task 017`

3. Pre-completion checklist:
   - `ruff format --check .` passes
   - `ruff check .` passes
   - `mypy mayaastrolib/` — no new errors
   - `pytest -x` passes — 215 existing + ~15 new = ~230
   - All Task 014 golden tests still pass unchanged
   - Default `Chart(date, pos)` constructs an identical tropical chart to pre-Task-017 (the BackwardsCompatibilityTests class catches this)

4. PROJECT-LOG.md entry must include:
   - The exact location of the new `_sidereal_calc_ut` (file:line)
   - The measured Lahiri ayanamsa at J2000.0 vs the published 23°51'11"
   - Verification that tropical chart construction time is unchanged (sidereal lock not held in the tropical path)
   - The chosen J2000.0 reference for the Vedic golden chart and the exact expected sidereal Sun position

5. Push:

   ```
   git push -u origin task-017-vedic-foundation
   ```

6. Verify CI green.

7. DO NOT merge. Leave for human review.

## Definition of done

- `mayaastrolib/vedic/ayanamsa.py` exists with `lahiri()` and `to_sidereal()`
- `Chart(zodiac=ZODIAC_SIDEREAL, ayanamsa=AYANAMSA_LAHIRI)` produces a chart with planet and house longitudes shifted by Lahiri ayanamsa
- `Chart(date, pos)` with no kwargs produces a chart byte-identical to pre-Task-017 output
- Lock-guarded sidereal path in `ephem/swe.py`
- New tests pass; all 215 existing tests still pass
- New Vedic golden chart at `tests/golden/` within ±2 arcmin
- CHANGELOG entry under `[Unreleased]`
- CI green

## If something goes wrong

**Most likely failure: pyswisseph's flag constants are named differently than expected.** `SEFLG_SIDEREAL` may live at `swisseph.FLG_SIDEREAL` or `swisseph.SEFLG_SIDEREAL` depending on the bindings version. Run `python -c "import swisseph; print([a for a in dir(swisseph) if 'SID' in a])"` to discover the actual names.

**Second most likely: `houses_ex2` doesn't take a sidereal flag the same way `calc_ut` does.** Check the pyswisseph docs; the houses function may need separate sidereal-mode handling. If so, document the asymmetry and lock-guard both call sites.

**Third most likely: `Datetime.jd` doesn't exist with that name.** It may be `Datetime.jd_ut`, `Datetime.julday`, or accessed via a method. Adapt accordingly — don't add a new property to `Datetime` in this task.

**The thread-safety guarantee is the easiest thing to get wrong.** If the BackwardsCompatibilityTests pass but adding `threading.Thread` parallel sidereal chart construction with different ayanamsas (a Task 018+ scenario) ever produces inconsistent positions, the lock isn't doing its job. Re-read Task 008's pattern.

If something fundamental breaks:

1. `git reset --hard development`
2. Failure report in PROJECT-LOG.md
3. Commit on `task-017-failed-attempt-1`
4. Push and stop

This is the highest-stakes task in the queue — it's the architectural commitment for the entire Phase 2. If the design feels wrong as you implement it, stop and write up the concern in PROJECT-LOG.md rather than ship a shape we'll regret.

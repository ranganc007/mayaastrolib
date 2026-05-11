# Task 015: GeoPos Input Validation

## Context

You are working in the `mayaastrolib` repository. Before doing anything:

1. Read `CLAUDE.md` in full.
2. Read `mayaastrolib/geopos.py` end to end. Understand:
   - The `GeoPos` constructor signature
   - How latitude and longitude strings (e.g. `"38n32"`, `"8w54"`) are parsed
   - Where the float coercion lands
3. Read `docs/REVIEW-2026-05-08.md` — particularly the "GeoPos input validation is missing" section under Reliability and the Task 015 description in Suggested Next Tasks.
4. Read `docs/PROJECT-LOG.md` for entries from Tasks 011-013 to understand recent patterns.
5. Confirm `development` is at the post-Task-013 state:

   ```
   git log --oneline development -5
   ```

   You should see Task 013 commits at the top.

6. Confirm `pytest tests/` passes — should be 186 tests.

## Why this task exists

The platform review (2026-05-08) found that `GeoPos` accepts out-of-range latitudes without raising an error:

```python
>>> from mayaastrolib.geopos import GeoPos
>>> pos = GeoPos('200n00', '0w00')
>>> pos.lat
200.0
```

This is a real correctness bug. A latitude of 200° doesn't exist on Earth. Any chart constructed with this `GeoPos` will produce mathematically nonsensical output that doesn't visibly fail — it just silently computes garbage.

The library's defenses against bad input today are accidental:
- The `int()` cast on `"garbage"` happens to raise `ValueError`
- `swisseph.calc_ut` raises on unknown bodies
- `Datetime` parsing rejects malformed strings via Python's own datetime parsing

These work, but only because the bad inputs happen to fail at a layer below `GeoPos`. Out-of-range coordinates pass through every defensive layer because each one is doing a more local check (parse-correctly, exists-as-body) rather than a semantic check (latitude-in-valid-range).

This task adds explicit semantic validation at `GeoPos` construction.

## Design decisions (already made)

- **Validate on construction**, not lazily on first use. By the time a `GeoPos` is passed to `Chart()`, the bad value is already locked in; failing there would be too late.
- **Raise `ValueError`** with a helpful message that includes the offending value. Matches the convention of the rest of the codebase.
- **Validate range only** — don't try to validate "this is a real place on Earth" or anything fancier. The mathematical range is `lat ∈ [-90, 90]` and `lon ∈ [-180, 180]`; that's what the library needs to be safe.
- **Boundary inclusive** — `lat=90.0` and `lon=180.0` are valid (the poles and the antimeridian respectively). `lat=-90.0` and `lon=-180.0` likewise. `lon=180.0` and `lon=-180.0` are the same physical place but both should be accepted as valid floats.
- **Validate after coercion**, not during string parsing. Whatever turns `"200n00"` into `200.0` keeps working — the validation kicks in after the float exists.

## Task scope

### 1. Find where the float coercion lands

Read `geopos.py` to identify the exact point where `lat` and `lon` become floats. There are several possible patterns:

- Strings parsed in `__init__` directly
- Strings parsed by a helper function (e.g. `_parse_coord` or similar)
- Both string and numeric inputs accepted (string parsed; numeric used as-is)

Identify the parsing path used by the constructor. Whatever it is, the validation goes immediately after the float values exist.

### 2. Add the validation

Add range checks. Pseudocode:

```python
class GeoPos:
    def __init__(self, lat, lon):
        # ... existing parsing logic ...
        # self.lat and self.lon are now floats
        
        if not -90.0 <= self.lat <= 90.0:
            raise ValueError(
                f"Latitude must be in [-90, 90]; got {self.lat}"
            )
        if not -180.0 <= self.lon <= 180.0:
            raise ValueError(
                f"Longitude must be in [-180, 180]; got {self.lon}"
            )
```

Adapt to whatever the actual structure of the constructor is. If parsing happens in a helper, the validation can live there or in the constructor — pick wherever it reads more naturally.

**Important:** the error messages must include the offending value. "Latitude out of range" is unhelpful. "Latitude must be in [-90, 90]; got 200.0" is debuggable.

### 3. Tests

Add `tests/test_geopos_validation.py`:

```python
"""Tests for GeoPos input validation (Task 015)."""

import unittest

from mayaastrolib.geopos import GeoPos


class GeoPosValidationTests(unittest.TestCase):

    # --- Valid inputs continue to work ---

    def test_valid_string_lat_lon(self):
        pos = GeoPos("38n32", "8w54")
        self.assertAlmostEqual(pos.lat, 38.5333, places=2)
        self.assertAlmostEqual(pos.lon, -8.9, places=1)

    def test_valid_equator_prime_meridian(self):
        pos = GeoPos("0n00", "0e00")
        self.assertEqual(pos.lat, 0.0)
        self.assertEqual(pos.lon, 0.0)

    def test_valid_north_pole(self):
        # The pole itself is a degenerate case but valid as a latitude
        pos = GeoPos("90n00", "0e00")
        self.assertEqual(pos.lat, 90.0)

    def test_valid_south_pole(self):
        pos = GeoPos("90s00", "0e00")
        self.assertEqual(pos.lat, -90.0)

    def test_valid_antimeridian_east(self):
        pos = GeoPos("0n00", "180e00")
        self.assertEqual(pos.lon, 180.0)

    def test_valid_antimeridian_west(self):
        pos = GeoPos("0n00", "180w00")
        self.assertEqual(pos.lon, -180.0)

    # --- Out-of-range inputs raise ValueError ---

    def test_latitude_above_90_raises(self):
        with self.assertRaises(ValueError) as ctx:
            GeoPos("200n00", "0w00")
        # Error message should include the offending value
        self.assertIn("200", str(ctx.exception))

    def test_latitude_below_neg_90_raises(self):
        with self.assertRaises(ValueError) as ctx:
            GeoPos("100s00", "0w00")
        self.assertIn("-100", str(ctx.exception))

    def test_longitude_above_180_raises(self):
        with self.assertRaises(ValueError) as ctx:
            GeoPos("0n00", "200e00")
        self.assertIn("200", str(ctx.exception))

    def test_longitude_below_neg_180_raises(self):
        with self.assertRaises(ValueError) as ctx:
            GeoPos("0n00", "200w00")
        self.assertIn("-200", str(ctx.exception))

    def test_latitude_just_above_90_raises(self):
        # Boundary check: 90.0 valid, 90.0001 not
        with self.assertRaises(ValueError):
            GeoPos("90n01", "0w00")

    def test_longitude_just_above_180_raises(self):
        with self.assertRaises(ValueError):
            GeoPos("0n00", "180e01")

    # --- Numeric inputs (if supported) ---
    # If GeoPos accepts numeric input directly (e.g. GeoPos(38.5, -8.9)),
    # add equivalent tests for numeric out-of-range. If it only accepts
    # strings, skip this section.


if __name__ == "__main__":
    unittest.main()
```

The numeric-input tests are conditional. Read `GeoPos.__init__` to see whether it accepts numeric input. If yes, add a section testing numeric out-of-range. If only strings, skip.

### 4. Verify the predicted coverage improvement

The platform review predicted `geopos.py` coverage would jump from 69% to 90%+ after this task. Run coverage and confirm:

```bash
.venv-task015/bin/pytest tests/ --cov=mayaastrolib --cov-report=term-missing 2>&1 | grep -E "geopos|TOTAL"
```

Capture the before-and-after numbers in the PROJECT-LOG entry.

If coverage doesn't improve as predicted, investigate why — there may be uncovered lines in `geopos.py` that aren't validation-related (e.g. unused helper functions, edge cases in the string parser). Document any such residual gaps but don't try to close them in this task.

### 5. Update CHANGELOG.md

Under `[Unreleased]`:

```markdown
### Fixed
- `GeoPos` now validates that latitude ∈ [-90, 90] and longitude ∈ [-180, 180], raising `ValueError` with the offending value if out of range. Previously, out-of-range coordinates (e.g. `GeoPos('200n00', '0w00')`) silently produced charts with mathematically nonsensical output. Surfaced by the platform review (2026-05-08).
```

This goes under `Fixed`, not `Added`, because the validation closes a real correctness bug.

### 6. Update KNOWN-BUGS.md

Move the GeoPos validation entry from "Open" to "Resolved" (or add a new "Resolved" entry referencing this task). Pattern matches what was done for the eclipse fix in Task 004.

If `KNOWN-BUGS.md` doesn't currently have a GeoPos entry (since the bug was only surfaced by the review, not flagged earlier), add a Resolved entry with a brief note pointing at the review.

## Out of scope

- Validating geographic semantics beyond range (e.g. "is this on land", "is this a real place")
- Changing the input format accepted by `GeoPos` (string vs numeric vs both)
- Adding validation to other classes (`Datetime`, `Chart`, etc.) — separate concern, separate task if needed
- Type hints on `GeoPos` (Phase 1 follow-up)
- Performance work

## Process

1. Branch:

   ```
   git checkout development
   git pull origin development
   git checkout -b task-015-geopos-validation
   ```

2. Suggested commits:
   - `fix: validate latitude and longitude ranges in GeoPos`
   - `test: cover GeoPos validation including boundary cases`
   - `docs: update CHANGELOG and KNOWN-BUGS for Task 015`

3. Pre-completion checklist:
   - `ruff format --check .` passes
   - `ruff check .` passes
   - `mypy mayaastrolib/` — no new errors
   - `pytest -x` passes — 186 existing tests + 12 new = 198 total
   - Coverage on `geopos.py` improved measurably (predicted 69% → 90%+)

4. PROJECT-LOG.md entry must include:
   - The exact location of the new validation (file:line)
   - The before/after coverage numbers for `geopos.py`
   - Any residual coverage gaps (lines still uncovered after this task)
   - Whether numeric input was supported (and tested) or skipped

5. Push:

   ```
   git push -u origin task-015-geopos-validation
   ```

6. Verify CI green.

7. DO NOT merge. Leave for human review.

## Definition of done

- `GeoPos` raises `ValueError` for `lat` outside `[-90, 90]` or `lon` outside `[-180, 180]`
- The error message includes the offending numeric value
- All boundary cases (poles, antimeridian) remain valid
- All existing valid inputs (the strings used in test fixtures elsewhere) still work
- New tests in `test_geopos_validation.py` pass
- All existing 186 tests still pass
- Coverage on `geopos.py` measurably improved
- CI green
- CHANGELOG and KNOWN-BUGS updated

## If something goes wrong

The most likely failure mode: an existing test or fixture somewhere in the codebase uses an out-of-range GeoPos as a placeholder (e.g. `GeoPos("99n99", "999e99")` to mean "any location"). Adding validation would break that test.

If this happens:
1. Find the offending test/fixture — `pytest -x` will fail at the first occurrence
2. Update the test to use a real-but-arbitrary location (e.g. Greenwich: `GeoPos("0n00", "0e00")`)
3. Note the test was using a bogus placeholder in PROJECT-LOG.md — this is itself useful information

If the float coercion happens via a path that's hard to trace (e.g. multiple inheritance, dynamic dispatch), and the validation can't be cleanly inserted, fall back to validating in `__init__` after coercion regardless of how it happened. The constructor is the chokepoint; everything has to pass through it.

If something fundamental breaks:

1. `git reset --hard development`
2. Failure report in PROJECT-LOG.md
3. Commit on `task-015-failed-attempt-1`
4. Push and stop

This is a small task; failure here would be unusual.

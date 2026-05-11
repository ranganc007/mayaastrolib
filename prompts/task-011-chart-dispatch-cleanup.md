# Task 011: Chart Dispatch and House Numbering Cleanup

## Context

You are working in the `mayaastrolib` repository. Before doing anything:

1. Read `CLAUDE.md` in full.
2. Read `mayaastrolib/chart.py` — focus on the `Chart.get()` method.
3. Read `mayaastrolib/object.py` — focus on the `House` class, particularly `House.__init__` and `House.num` (which may be a property after Task 006).
4. Read `mayaastrolib/_compat.py` to remember the property migration pattern.
5. Read `docs/PROJECT-LOG.md` for entries from Tasks 006, 010 — these set patterns this task follows.
6. Confirm Task 010 is on `development`:

   ```
   git log --oneline development -5
   ```

   Should show recent Task 010 commits at the top.

7. Confirm `pytest tests/` passes — should be ~157 tests after Task 010.

## Why this task exists

Two small structural smells flagged by the deeper audit:

**Item 13 — `Chart.get(ID)` dispatches by string-prefix matching.**

The current implementation is approximately:

```python
def get(self, ID):
    if ID.startswith("House"):
        return self.getHouse(ID)
    elif ID in const.LIST_ANGLES:
        return self.getAngle(ID)
    else:
        return self.getObject(ID)
```

The literal `"House"` prefix is brittle. If house IDs ever change format (e.g. to `"H1".."H12"`), the dispatch silently breaks because angles and objects fall through into `getObject()`.

**Item 14 — `House.num` parses the ID string.**

`House.num` (or `House.num()` if it's a method) is implemented as `int(self.id[5:])`. The literal `5` is `len("House")`, baked in. Same brittleness as Item 13: change the ID format and the parsing breaks.

Both fixes are mechanical and uncontroversial.

## Task scope

### 1. Fix `Chart.get()` to dispatch by list membership

Update `Chart.get()` to use the existing list constants instead of string-prefix matching:

```python
def get(self, ID):
    """Return the object, house, or angle with the given ID.

    Args:
        ID: An ID from const.LIST_OBJECTS, const.LIST_HOUSES, or
            const.LIST_ANGLES.

    Returns:
        The matching Object, House, or Angle. Raises if ID is not
        recognised.

    Raises:
        KeyError: if ID is not found in any of objects, houses, or angles.
    """
    if ID in const.LIST_HOUSES:
        return self.getHouse(ID)
    if ID in const.LIST_ANGLES:
        return self.getAngle(ID)
    return self.getObject(ID)
```

Important: verify `const.LIST_HOUSES` exists in `mayaastrolib/const.py` before referencing it. If it doesn't (the constant might be named differently — `LIST_HOUSE_IDS`, `HOUSE_IDS`, etc.), find the actual canonical list. Check by:

```bash
grep -n "^LIST_" mayaastrolib/const.py | head -20
```

If `LIST_HOUSES` doesn't exist but the houses are defined as individual constants (`HOUSE1`, `HOUSE2`, etc.), add `LIST_HOUSES` to `const.py` as a list of those — keep it alongside `LIST_OBJECTS` and `LIST_ANGLES` for consistency.

### 2. Fix `House.num` to be a stored attribute

Read the current `House.__init__` to see how houses are constructed. Whatever the construction path is — usually `house = House(id="House5", lon=120.0, ...)` — the `num` (5 in this case) is derivable at construction time without parsing.

Update `House.__init__` to compute and store `num`:

```python
def __init__(self, id, lon, ...):
    ...existing init...
    self.id = id
    # Store num explicitly. Derived from id, but cached to avoid string parsing.
    self.num = const.LIST_HOUSES.index(id) + 1  # or whatever pattern fits
```

Alternative if list lookup is wrong: extract the integer from the ID at construction time *once*:

```python
self.num = int(id[len("House"):])  # parsed once, stored
```

Both work. The list-lookup version is cleaner if `LIST_HOUSES` exists and is ordered. The parse-once version is more robust to format changes (the parsing string still has magic `len("House")` but only in one place, in `__init__`, easier to find later).

If `House.num` is currently a `@property` (from Task 006 or earlier), the fix becomes:

- Keep the property
- Have it return `self._num` (the cached value)
- Set `self._num` in `__init__`

The deprecated method-style access from `_compat.py` should continue to work unchanged.

### 3. Verify nothing else relies on the string-prefix pattern

Search for any other code that does ID-by-string-matching:

```bash
grep -rn 'startswith("House"\|startswith("h\|\[5:\]' mayaastrolib/
```

If anything else parses house IDs by string position, fix it the same way (use the cached `num` attribute or list lookup). Document each occurrence in PROJECT-LOG.md.

### 4. Tests

Add `tests/test_chart_dispatch.py`:

```python
"""Tests for Chart.get() dispatch and House.num cleanup (Task 011)."""

import unittest

from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib import const


class ChartDispatchTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)

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
        """Regression: dispatch must work even if the literal 'House' prefix
        in IDs were changed. Verify by checking House dispatch works for
        every house in LIST_HOUSES, not just House1.
        """
        for house_id in const.LIST_HOUSES:
            h = self.chart.get(house_id)
            self.assertIsNotNone(h)
            self.assertEqual(h.id, house_id)


class HouseNumTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)

    def test_house_num_is_int(self):
        h1 = self.chart.get(const.HOUSE1)
        self.assertIsInstance(h1.num, int)

    def test_house_num_matches_id(self):
        for i, house_id in enumerate(const.LIST_HOUSES, start=1):
            h = self.chart.get(house_id)
            self.assertEqual(h.num, i)

    def test_house_5_is_5(self):
        h5 = self.chart.get(const.HOUSE5)
        self.assertEqual(h5.num, 5)

    def test_house_12_is_12(self):
        h12 = self.chart.get(const.HOUSE12)
        self.assertEqual(h12.num, 12)


if __name__ == "__main__":
    unittest.main()
```

The `test_get_uses_list_dispatch_not_string_prefix` test is the regression test for Item 13. It confirms that all 12 houses dispatch correctly, not just the first one.

### 5. Update CHANGELOG.md

Under `[Unreleased]`:

```markdown
### Changed (internal)
- `Chart.get(ID)` now dispatches by list membership rather than string-prefix
  matching. No user-facing behaviour change, but more robust to future
  identifier format changes.
- `House.num` is now stored as a real attribute rather than parsed from
  the ID string at access time. No user-facing behaviour change.
```

These are "Changed (internal)" because they don't affect public-facing behaviour, just internal robustness.

## Out of scope

- Renaming house IDs (would be a breaking change requiring a separate task)
- Type hints (Phase 1 follow-up later)
- Items 15, 16, 17 from the audit (separate tasks)
- Any new functionality

## Process

1. Branch:

   ```
   git checkout development
   git pull origin development
   git checkout -b task-011-chart-dispatch-cleanup
   ```

2. Suggested commits:
   - `refactor: dispatch Chart.get() by list membership not string prefix`
   - `refactor: store House.num as attribute, eliminate string parsing`
   - `test: cover Chart.get dispatch and House.num`
   - `docs: update CHANGELOG for Task 011`

3. Pre-completion checklist:
   - `ruff format --check .` passes
   - `ruff check .` passes
   - `mypy mayaastrolib/` — no new errors
   - `pytest -x` passes — all 157+ tests, plus the new ones

4. PROJECT-LOG.md entry must include:
   - The exact change to `Chart.get()` (before/after pseudocode)
   - The exact change to `House.__init__` and `House.num`
   - List of any other string-prefix or magic-offset patterns found by the grep search
   - Confirmation that all houses dispatch correctly (the regression test passing)

5. Push:

   ```
   git push -u origin task-011-chart-dispatch-cleanup
   ```

6. Verify CI green.

7. DO NOT merge. Leave for human review.

## Definition of done

- `Chart.get()` no longer uses `startswith("House")` for dispatch
- `House.num` is stored, not parsed, at access time
- `LIST_HOUSES` exists in `const.py` (added if it didn't, used as-is if it did)
- All 12 houses dispatch correctly through `Chart.get()`
- All existing 157+ tests still pass
- New tests in `test_chart_dispatch.py` pass
- CI green
- CHANGELOG updated

## If something goes wrong

Most likely failure mode: `LIST_HOUSES` doesn't exist in `const.py` and the existing house constants aren't structured as a clean list. If this happens:

1. Add the constant cleanly: `LIST_HOUSES = [HOUSE1, HOUSE2, ..., HOUSE12]`
2. Verify it's ordered (HOUSE1 first, HOUSE12 last)
3. Use it for both the dispatch in `Chart.get()` and the num computation in `House.__init__`

Second most likely: `House.num` is referenced as a method elsewhere (e.g. `h.num()`) by old test code. After this change, `h.num` returns an int directly — calling it as a method would fail. Search:

```bash
grep -rn "\.num()" tests/ recipes/
```

If any callers use method-style, they need updating. If `_compat`'s `_DualAccess` is wrapping `num`, both forms continue to work — verify which.

If something fundamental breaks:

1. `git reset --hard development`
2. Failure report in PROJECT-LOG.md
3. Commit on `task-011-failed-attempt-1`
4. Push and stop

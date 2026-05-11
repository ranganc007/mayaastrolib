# Task 013: Predictives as Chart Methods

## Context

You are working in the `mayaastrolib` repository. Before doing anything:

1. Read `CLAUDE.md` in full.
2. Read `mayaastrolib/chart.py` — specifically the `Chart.profected()` method added in Task 010. This task replicates that pattern for other predictives.
3. Read each of these modules end to end to understand their public APIs:
   - `mayaastrolib/predictives/returns.py` — `solarReturn()`, `lunarReturn()` (if exists)
   - `mayaastrolib/predictives/primarydirections.py` — `PrimaryDirections` class and helpers
   - `mayaastrolib/tools/arabicparts.py` — `getPart()`, `PARS_FORTUNA`, etc.
   - `mayaastrolib/tools/planetarytime.py` — `getNow()`, hour table functions
4. Read `mayaastrolib/_compat.py` for the deprecation pattern.
5. Read `docs/AUDIT-INVESTIGATIONS.md` (created by Task 012) — Item 16's findings affect how `chart.solarReturn()` should work.
6. Read `docs/PROJECT-LOG.md` for entries from Tasks 010, 011, 012.
7. Confirm Task 012 is on `development`:

   ```
   git log --oneline development -5
   ```

8. Confirm `pytest tests/` passes — should be 165+ tests by now.

## Why this task exists

Item 17 from the deeper audit:

> Tools/predictives are top-level functions, not Chart methods. `profections.compute(chart, date)`, `arabicparts.getPart(...)`, `planetarytime.getNow(...)`, `primarydirections.PrimaryDirections(...)`. Won't show up on `chart.` autocomplete; consumers must remember the import paths.

Task 010 partially addressed this by adding `chart.profected()`. This task completes the pattern for the remaining predictives:

- `chart.solarReturn(year)` → wraps `predictives.returns.solarReturn(chart, year)`
- `chart.lunarReturn(date)` → wraps `predictives.returns.lunarReturn(chart, date)` (if it exists)
- `chart.directions()` → wraps `predictives.primarydirections.PrimaryDirections(chart)`
- `chart.arabicPart(part_id)` → wraps `tools.arabicparts.getPart(part_id, chart)`
- `chart.planetaryHour(date=None)` → wraps `tools.planetarytime.getNow()` (or equivalent)

Each is a thin method on `Chart` that improves discoverability. The existing module-level functions stay, deprecated.

## Design decisions (already made)

**Same pattern as Task 010's `chart.profected()`:**
- Method on Chart, not classmethod
- Existing module-level function stays, becomes deprecated wrapper
- Deprecation warning points at the new method
- Removal planned for 1.0

**Solar/lunar returns are real charts, not symbolic.** Unlike profections (which rotate natal positions), returns find a *real moment in time* when a planet returns to its natal position. The resulting chart is computed from ephemeris for that real moment. So `is_symbolic=False` for return charts.

**Primary directions are symbolic.** They're a time-mapping technique applying coordinate transforms to natal positions. If `PrimaryDirections` returns an object that's chart-like, that chart gets `is_symbolic=True, symbolic_kind="direction"`.

**Solar return semantics depend on Task 012's findings.** If Task 012's `AUDIT-INVESTIGATIONS.md` recommended adding `solarReturnByAge()`, that recommendation already shipped in Task 012, and `chart.solarReturn(year=N)` here can simply wrap the existing `solarReturn()` semantic without changes. If Task 012 deferred Item 16, this task wraps the existing function as-is and notes in IDEAS.md that `chart.solarReturn` semantics inherit whatever the underlying function does.

**Read Task 012's outcome before writing this task's solar return wrapper.** Adapt accordingly.

## Task scope

### 1. `chart.solarReturn(year)`

Add to `Chart`:

```python
def solarReturn(self, year=None, target_date=None):
    """Return a solar return chart — the moment when the Sun returns
    to its natal position in or around the specified year.

    A solar return chart is a real chart computed for an ephemeris-
    derived moment, not a symbolic transformation of the natal. Its
    planets have real speeds and dynamics.

    Args:
        year: The calendar year to search in. The chart is computed
            for the first Sun-return moment in or after [the year-anchor
            point — see implementation notes].
        target_date: Alternative: a Datetime; the chart is computed for
            the Sun return nearest to this date. Mutually exclusive with year.

    Returns:
        A new Chart. Not symbolic — `is_symbolic=False`.

    Raises:
        ValueError: if both or neither of year/target_date are provided.

    See also:
        `predictives.returns.solarReturn()` — the underlying calculation.
    """
    if (year is None) == (target_date is None):
        raise ValueError("Pass exactly one of year= or target_date=")
    from mayaastrolib.predictives import returns
    if year is not None:
        return returns.solarReturn(self, year)
    else:
        # If the existing API doesn't support target_date, derive year
        # and search from there. Adapt to actual function signature.
        return returns.solarReturn(self, target_date.date.year)
```

The existing `predictives.returns.solarReturn(chart, year)` then becomes:

```python
def solarReturn(chart, year):
    """[DEPRECATED] Use chart.solarReturn(year=year) instead.

    Returns a solar return chart for the given year. Will be removed in 1.0.
    """
    import warnings
    warnings.warn(
        "predictives.returns.solarReturn(chart, year) is deprecated. "
        "Use chart.solarReturn(year=year) instead. "
        "Will be removed in 1.0.",
        DeprecationWarning,
        stacklevel=2,
    )
    # Keep the existing implementation
    return _solarReturn_impl(chart, year)
```

Rename the implementation to `_solarReturn_impl` (or keep the name and have `chart.solarReturn` call the deprecated wrapper without triggering its own warning — see implementation note below).

**Implementation note:** the deprecation warning should NOT fire when `chart.solarReturn()` is the caller. Two approaches:

a. Move the actual implementation to `_solarReturn_impl(chart, year)` (private). Both `chart.solarReturn()` and the deprecated `solarReturn(chart, year)` wrapper call `_solarReturn_impl()`. Only the wrapper warns.

b. Have `chart.solarReturn()` call `solarReturn(chart, year)` but suppress its warning with `warnings.catch_warnings()`. Uglier but no rename.

Option (a) is cleaner. Use it.

### 2. `chart.lunarReturn(target_date)` (if applicable)

Read `predictives/returns.py` first. If `lunarReturn()` exists, follow the same pattern as `solarReturn`. If it doesn't exist, skip — don't add new functionality in this task. Note in PROJECT-LOG.md.

### 3. `chart.directions()`

Add to `Chart`:

```python
def directions(self):
    """Return a PrimaryDirections instance for this chart.

    Primary directions are a symbolic predictive technique mapping
    natal angular relationships forward through time. The returned
    object exposes methods for computing specific directions and
    timing tables.

    Returns:
        A PrimaryDirections instance.

    See also:
        `predictives.primarydirections.PrimaryDirections` — the
        underlying class.
    """
    from mayaastrolib.predictives.primarydirections import PrimaryDirections
    return PrimaryDirections(self)
```

The constructor `PrimaryDirections(chart)` stays available but becomes deprecated:

```python
class PrimaryDirections:
    def __new__(cls, chart, *args, **kwargs):
        # If called via Chart.directions(), don't warn.
        # If called externally, warn.
        # Detect via inspect or via a private flag.
        ...
```

Actually, the cleanest approach is different: don't deprecate the class itself (it's a class, not a function — and `chart.directions()` returns an instance of it). The class stays public. Just point new users at `chart.directions()` in the docstring of `__init__`. No warning needed unless we genuinely want to remove the direct-instantiation path in 1.0.

**Decide:** is direct `PrimaryDirections(chart)` instantiation deprecated, or just discouraged in favour of `chart.directions()`?

I recommend: keep both as fully supported. `chart.directions()` is the discoverable path; `PrimaryDirections(chart)` is fine for advanced use. No deprecation warning. Just document that `chart.directions()` is the preferred entry point.

This is a deviation from the pattern for the function-style predictives (where the function gets deprecated). It's defensible because:
- A class isn't deprecated as easily as a function
- Direct instantiation is a Python convention people expect to keep working
- The Chart method is purely additive

Document this choice in PROJECT-LOG.md.

### 4. `chart.arabicPart(part_id)`

Add to `Chart`:

```python
def arabicPart(self, part_id):
    """Compute an Arabic part for this chart.

    Args:
        part_id: One of the part constants from tools.arabicparts
            (e.g. PARS_FORTUNA, PARS_SPIRIT).

    Returns:
        A GenericObject representing the part's position.

    Example:
        >>> from mayaastrolib.tools import arabicparts
        >>> fortuna = chart.arabicPart(arabicparts.PARS_FORTUNA)

    See also:
        `tools.arabicparts.getPart()` — the underlying function.
    """
    from mayaastrolib.tools.arabicparts import getPart
    return getPart(part_id, self)
```

Same deprecation pattern as solar return: rename the implementation to `_getPart_impl`, deprecate `getPart(part_id, chart)` as a wrapper that emits warning.

### 5. `chart.planetaryHour(date=None)`

Read `tools/planetarytime.py` first to understand what `getNow()` returns. Probably an `HourTable` for the current moment.

Add to `Chart`:

```python
def planetaryHour(self, date=None):
    """Return the planetary hour table for the chart's location at
    the given moment.

    Args:
        date: A Datetime. Defaults to the chart's own date.

    Returns:
        An HourTable instance.

    See also:
        `tools.planetarytime.getHourTable()` — the underlying function.
    """
    from mayaastrolib.tools.planetarytime import getHourTable
    if date is None:
        date = self.date
    return getHourTable(date, self.pos)
```

Adapt to whatever the actual signature is. The existing `getNow()` and `getHourTable()` stay; only deprecate if they take a chart-with-date-and-pos pair that the new method clearly supersedes.

If the planetary time module is purely date+location-based (not chart-based), `chart.planetaryHour()` is a convenience that uses the chart's date and pos. The underlying functions don't need deprecation because they have legitimate non-chart uses (e.g. "what's the planetary hour right now in Dublin" doesn't require a chart).

### 6. Tests

Add `tests/test_chart_predictives.py`:

```python
"""Tests for Chart-method predictives (Task 013)."""

import unittest
import warnings

from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib import const


class ChartSolarReturnTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("1980/06/15", "12:00", "+00:00")
        pos = GeoPos("51n30", "0w08")
        self.chart = Chart(date, pos)

    def test_solar_return_returns_chart(self):
        sr = self.chart.solarReturn(year=2022)
        self.assertIsInstance(sr, Chart)

    def test_solar_return_is_not_symbolic(self):
        sr = self.chart.solarReturn(year=2022)
        self.assertFalse(sr.is_symbolic)

    def test_solar_return_planets_have_real_speed(self):
        sr = self.chart.solarReturn(year=2022)
        sun = sr.get(const.SUN)
        self.assertIsNotNone(sun.lonspeed)

    def test_solar_return_requires_one_arg(self):
        with self.assertRaises(ValueError):
            self.chart.solarReturn()


class ChartDirectionsTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("1980/06/15", "12:00", "+00:00")
        pos = GeoPos("51n30", "0w08")
        self.chart = Chart(date, pos)

    def test_directions_returns_primary_directions(self):
        from mayaastrolib.predictives.primarydirections import PrimaryDirections
        d = self.chart.directions()
        self.assertIsInstance(d, PrimaryDirections)


class ChartArabicPartTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)

    def test_pars_fortuna(self):
        from mayaastrolib.tools.arabicparts import PARS_FORTUNA
        part = self.chart.arabicPart(PARS_FORTUNA)
        self.assertIsNotNone(part)


class ChartPlanetaryHourTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)

    def test_planetary_hour_returns_table(self):
        ht = self.chart.planetaryHour()
        self.assertIsNotNone(ht)


class DeprecatedTopLevelTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("1980/06/15", "12:00", "+00:00")
        pos = GeoPos("51n30", "0w08")
        self.chart = Chart(date, pos)

    def test_deprecated_solar_return_warns(self):
        from mayaastrolib.predictives import returns
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            returns.solarReturn(self.chart, 2022)
            self.assertTrue(
                any(issubclass(x.category, DeprecationWarning) for x in w),
            )

    def test_deprecated_get_part_warns(self):
        from mayaastrolib.tools import arabicparts
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            arabicparts.getPart(arabicparts.PARS_FORTUNA, self.chart)
            self.assertTrue(
                any(issubclass(x.category, DeprecationWarning) for x in w),
            )


if __name__ == "__main__":
    unittest.main()
```

Adapt assertions to match what each underlying function actually returns. If `arabicparts.getPart` returns a tuple, test for that. If it returns a `GenericObject`, test for that. Don't assume — read the code.

### 7. Update CHANGELOG.md

Under `[Unreleased]`:

```markdown
### Added
- `Chart.solarReturn(year)` — convenience for `predictives.returns.solarReturn()`
- `Chart.directions()` — convenience for `predictives.primarydirections.PrimaryDirections()`
- `Chart.arabicPart(part_id)` — convenience for `tools.arabicparts.getPart()`
- `Chart.planetaryHour(date=None)` — convenience for `tools.planetarytime.getHourTable()`

### Deprecated
- `predictives.returns.solarReturn(chart, year)` — use `chart.solarReturn(year=year)`. Removed in 1.0.
- `tools.arabicparts.getPart(part_id, chart)` — use `chart.arabicPart(part_id)`. Removed in 1.0.

### Notes
- `predictives.primarydirections.PrimaryDirections(chart)` is NOT deprecated. Direct instantiation remains supported. `chart.directions()` is the preferred discoverable entry point.
- `tools.planetarytime` functions are NOT deprecated. They have legitimate date+location uses without requiring a chart.
```

## Out of scope

- Changing what each predictive *does*
- Adding new predictives
- Type hints
- Touching the dignities module (already covered in Task 008)
- Phase 2 work

## Process

1. Branch:

   ```
   git checkout development
   git pull origin development
   git checkout -b task-013-predictives-as-methods
   ```

2. Suggested commits:
   - `feat: add Chart.solarReturn method`
   - `refactor: deprecate predictives.returns.solarReturn`
   - `feat: add Chart.directions method`
   - `feat: add Chart.arabicPart method`
   - `refactor: deprecate tools.arabicparts.getPart`
   - `feat: add Chart.planetaryHour method`
   - `test: cover Chart-method predictives`
   - `docs: update CHANGELOG and IDEAS for Task 013`

3. Pre-completion checklist:
   - `ruff format --check .` passes
   - `ruff check .` passes
   - `mypy mayaastrolib/` — no new errors
   - `pytest -x` passes — all tests
   - No internal-library calls to the deprecated functions (`grep -rn "returns.solarReturn\|arabicparts.getPart" mayaastrolib/`)

4. PROJECT-LOG.md entry must include:
   - Whether `lunarReturn` existed and was wrapped
   - The implementation choice for direction (deprecate `PrimaryDirections(chart)` vs not)
   - The exact signatures of the new Chart methods
   - The decision on `planetaryHour` deprecation (yes/no with reasoning)

5. Push:

   ```
   git push -u origin task-013-predictives-as-methods
   ```

6. Verify CI green.

7. DO NOT merge. Leave for human review.

## Definition of done

- `chart.solarReturn(year)` works and returns a non-symbolic Chart
- `chart.directions()` works and returns a PrimaryDirections
- `chart.arabicPart(part_id)` works and returns the part
- `chart.planetaryHour()` works and returns an hour table
- The corresponding deprecated functions emit warnings (where deprecated)
- Internal library code does NOT use deprecated paths
- All existing 165+ tests still pass
- New tests for each Chart method pass
- CI green
- CHANGELOG updated, IDEAS.md updated if anything was deferred

## If something goes wrong

Most likely failure: one of the underlying functions has a signature that doesn't fit the wrapper pattern cleanly. For instance, `solarReturn(chart, year)` might use `year` as a date object internally, not an integer. If this happens:

1. Read the existing function carefully
2. Make the Chart method accept whatever the natural input is (probably integer year — that's what consumers want)
3. Have the Chart method do whatever conversion is needed before calling the underlying function

If the underlying function is genuinely awkward to wrap (multiple required parameters, complex return types), the wrapper might be more involved. That's fine — wrap it cleanly with appropriate documentation.

If a predictive turns out not to exist (e.g. there's no `lunarReturn`), skip it cleanly. Note in the log. Don't invent functionality.

If something fundamental breaks:

1. `git reset --hard development`
2. Failure report in PROJECT-LOG.md
3. Commit on `task-013-failed-attempt-1`
4. Push and stop

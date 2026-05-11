# Task 010: Symbolic Charts and Relocate Semantics

## Context

You are working in the `mayaastrolib` repository. Before doing anything:

1. Read `CLAUDE.md` in full.
2. Read `mayaastrolib/object.py` end to end. Pay particular attention to `Object.relocate()`, `Object.copy()`, `Object.movement`, and any speed-related attributes (`lonspeed`, `latspeed`, `lon`, `signlon`, `sign`).
3. Read `mayaastrolib/aspects.py` end to end. Look at how `antiscia()` and `cantiscia()` are implemented (likely as module-level functions).
4. Read `mayaastrolib/predictives/profections.py` end to end. Understand `compute(chart, date)` — note that it loops over chart.objects and calls `relocate()` on each.
5. Read `mayaastrolib/_compat.py` (from Task 006) to understand the `_DualAccess` and `property_with_method_compat` patterns. This task uses the same patterns; do NOT invent new deprecation mechanisms.
6. Read `docs/PROJECT-LOG.md` for entries from Tasks 006-009. The relocate-doesn't-update-speeds bug was discovered during the deeper API audit (referenced in Task 008's log entry or in the audit notes).
7. Confirm Task 009 has been merged to `development`:

   ```
   git log --oneline development -10
   ```

   You should see Task 009's commits (Aspect.name, getAspect Optional, standard object lists). If not, STOP.

8. Confirm `pytest tests/` passes cleanly — full test suite (45+ tests by now).

## Why this task exists

`Object.relocate(lon)` mutates a planet's longitude in place but does NOT update `lonspeed` / `latspeed`. This is used by two parts of the library:

- **Antiscia/cantiscia** in `aspects.py` — coordinate reflection. The reflected position conceptually has the same orbital state as the original (when the original moves, so does its antiscion). Speed should be preserved. This use is correct.

- **Profections** in `predictives/profections.py` — rotates each planet by N×30° to compute a "profected chart" symbolic of N years of life. The rotated position is symbolic; orbital state is undefined for a hypothetical position. Speed should NOT be preserved. The current behaviour leaves stale speeds, so `is_retrograde()` on a profected chart returns the natal answer, which is wrong.

This task fixes both use cases by separating them at the API level and introducing an explicit notion of "symbolic chart" — a chart whose positions are derived/symbolic rather than computed from ephemeris.

## Design decisions (already made — do not relitigate)

These six decisions are baked in. Implement them as specified:

1. **Symbolic chart representation:** flag on `Chart`. `chart.is_symbolic` (bool) and `chart.symbolic_kind` (string like "profection", "direction"). Default `False` and `None` for ordinary charts.

2. **Profected entry point:** `chart.profected(years=N)` method on Chart. Also accepts `target_date=` for backwards compatibility with the existing semantics.

3. **Old `profections.compute()` API:** keep working, emit DeprecationWarning, recommend `chart.profected()`.

4. **Symbolic planet dynamics:** `obj.lonspeed = None` and `obj.latspeed = None` on symbolic objects. `obj.movement`, `obj.is_retrograde()` return None when speed is None. Document this.

5. **Antiscia API:** add `Object.antiscion()` and `Object.cantiscion()` methods returning new Objects. Keep `aspects.antiscia()` / `aspects.cantiscia()` as deprecated thin wrappers.

6. **Antiscia preserve speed.** Antiscion positions are NOT symbolic. They share dynamics with the original planet. `obj.antiscion().lonspeed == obj.lonspeed`.

## Task scope

This task has four parts. Implement them in order — later parts depend on earlier parts.

---

### Part 1: `Object.with_longitude()` — the new primitive

Add a new method to `Object` that returns a new Object instance with a different longitude. This replaces the in-place `relocate()` mutation pattern.

```python
def with_longitude(self, lon, *, preserve_speed=False):
    """Return a new Object at the given longitude.

    This is a coordinate transform — it does NOT recompute the object's
    orbital state from ephemeris.

    By default, speed-related attributes (lonspeed, latspeed) are set to
    None on the returned object, signalling that orbital dynamics are
    undefined for this hypothetical position. Methods that depend on
    speed (movement, is_retrograde) will return None for such objects.

    Args:
        lon: New longitude in degrees [0, 360).
        preserve_speed: If True, keep the original lonspeed/latspeed.
            Set this when the new position meaningfully shares dynamics
            with the original (e.g. antiscia, where the reflected point
            moves with the original planet). Defaults to False because
            most callers (profections, directions) want speed cleared.

    Returns:
        A new Object instance. The original is not modified.

    Example:
        >>> sun_at_15_aries = sun.with_longitude(15.0)
        >>> sun_at_15_aries.lonspeed  # None
        >>> sun_at_15_aries.movement  # None — undefined for symbolic position

        >>> antiscion = sun.with_longitude(reflected_lon, preserve_speed=True)
        >>> antiscion.lonspeed == sun.lonspeed  # True
    """
    new = self.copy()
    new.lon = lon % 360
    new.signlon = new.lon % 30
    new.sign = const.LIST_SIGNS[int(new.lon // 30)]
    if not preserve_speed:
        new.lonspeed = None
        new.latspeed = None
    return new
```

Verify the import for `const.LIST_SIGNS` and the sign-from-longitude calculation match the pattern used elsewhere in the file. Don't invent new logic — find the existing pattern and reuse it.

### Part 2: `Object.movement` and `is_retrograde` handle None speed

Currently `Object.movement` (a property after Task 006) computes movement from `lonspeed`. When `lonspeed is None`, what does it do?

Update the property logic:

```python
@property_with_method_compat
def movement(self):
    """Direction of motion: DIRECT, RETROGRADE, STATIONARY, or None.

    Returns None for symbolic positions where speed is undefined
    (e.g. profected planets). Falsy in boolean context, so
    `if obj.movement:` correctly skips the branch for symbolic objects.
    """
    if self.lonspeed is None:
        return None
    if abs(self.lonspeed) < MAX_ORBS[const.STATIONARY]:
        return const.STATIONARY
    return const.DIRECT if self.lonspeed >= 0 else const.RETROGRADE
```

Verify the `_DualAccess` wrapper from Task 006 handles a None value correctly. Specifically:
- `obj.movement` → returns None (or _DualAccess(None))
- `bool(obj.movement)` → False
- `obj.movement == const.DIRECT` → False
- `obj.movement is None` → True (this is the test that might be tricky if _DualAccess wraps the value)

If `obj.movement is None` doesn't work because of the wrapper, that's a problem. Two solutions:

a. Add a special-case in `_DualAccess` so `None` is returned unwrapped (cleanest)
b. Document that consumers should compare with `obj.movement == None` instead of `is None` (ugly)

Strongly prefer (a). Update `_compat.py` to return None directly when the underlying value is None:

```python
@functools.wraps(func)
def wrapper(self):
    value = func(self)
    if value is None:
        return None  # don't wrap None — preserves `is None` checks
    return _DualAccess(value, self)
```

Same treatment for `is_retrograde()`. If it currently returns a bool computed from speed, it should return None when speed is None.

Search for other speed-dependent methods on `Object`:

```bash
grep -n "lonspeed\|latspeed" mayaastrolib/object.py
```

Each one needs to handle None. Document the full list in PROJECT-LOG.md.

### Part 3: `Object.antiscion()` and `Object.cantiscion()`

Add two methods to Object:

```python
def antiscion(self):
    """Return the antiscion of this object — a new Object reflected
    across the Cancer-Capricorn (0° Cancer / 0° Capricorn) axis.

    Antiscia preserve dynamics — the reflected point moves with the
    original. The returned Object has the same lonspeed/latspeed as
    self.

    Returns:
        A new Object representing the antiscion position.

    Example:
        >>> sun_anti = sun.antiscion()
        >>> sun_anti.lonspeed == sun.lonspeed  # True
        >>> sun_anti.movement == sun.movement  # True
    """
    # Read aspects.antiscia() for the existing math — should be:
    # antiscion_lon = (180 - self.lon) % 360 OR similar
    # Verify against the existing implementation; do NOT reinvent.
    antiscion_lon = ...  # use existing formula from aspects.antiscia()
    return self.with_longitude(antiscion_lon, preserve_speed=True)


def cantiscion(self):
    """Return the cantiscion (contra-antiscion) of this object — reflected
    across the Aries-Libra axis.

    See `antiscion()` for semantics. Cantiscia also preserve dynamics.
    """
    cantiscion_lon = ...  # use existing formula from aspects.cantiscia()
    return self.with_longitude(cantiscion_lon, preserve_speed=True)
```

Read the existing `aspects.antiscia()` and `aspects.cantiscia()` carefully to extract the longitude formulas. They are likely something like:
- Antiscion: `(180 - lon) % 360` (mirrors across the 0° Cancer / 0° Capricorn axis)
- Cantiscion: `(360 - lon) % 360` (mirrors across the 0° Aries / 0° Libra axis)

But verify against the actual code — don't trust my pseudo-formulas.

Then update `aspects.antiscia()` and `aspects.cantiscia()` to be deprecated wrappers:

```python
def antiscia(obj):
    """[DEPRECATED] Use obj.antiscion() instead.
    
    Returns the antiscion position. Will be removed in 1.0.
    """
    import warnings
    warnings.warn(
        "aspects.antiscia(obj) is deprecated. Use obj.antiscion() instead. "
        "Will be removed in 1.0.",
        DeprecationWarning,
        stacklevel=2,
    )
    return obj.antiscion()
```

Same for `cantiscia`. The deprecated wrappers may currently return something other than an Object (e.g. just a longitude value) — check the existing return type. If they returned something non-Object, the deprecation wrapper may need to extract the relevant field from the new Object. Document this in PROJECT-LOG.md.

### Part 4: Symbolic charts and `Chart.profected()`

#### 4.1 Add the symbolic flag to Chart

In `mayaastrolib/chart.py`, modify `Chart.__init__`:

```python
def __init__(self, date, pos, ...existing args..., is_symbolic=False, symbolic_kind=None):
    """...
    
    Args:
        ... existing args ...
        is_symbolic: True if this chart represents derived/symbolic
            positions rather than computed-from-ephemeris ones. Default False.
        symbolic_kind: A string identifying the kind of symbolic chart.
            Common values: "profection", "direction". Default None.
            Only meaningful when is_symbolic=True.
    """
    ...existing init...
    self.is_symbolic = is_symbolic
    self.symbolic_kind = symbolic_kind
```

These are public attributes, documented, and should not change after construction.

Add a `__repr__` clue so symbolic charts are visibly distinct in debugging:

```python
def __repr__(self):
    if self.is_symbolic:
        return f"<{type(self).__name__} ({self.symbolic_kind}) {self.date}>"
    return f"<{type(self).__name__} {self.date}>"
```

If a `__repr__` already exists, just add the symbolic branch to it.

#### 4.2 Add `Chart.profected()` method

```python
def profected(self, years=None, target_date=None):
    """Return a profected chart — natal positions rotated forward by
    one sign per year of age.

    Profections are a symbolic predictive technique. The returned chart's
    planetary positions do NOT represent where the planets actually are
    at the target date — they are natal positions rotated by N×30°.
    Therefore, dynamics-derived attributes like `obj.movement` and
    `obj.is_retrograde()` return None for the profected chart's planets.

    Args:
        years: Age in years. The profected chart rotates by years×30°
            modulo 360. Mutually exclusive with target_date.
        target_date: A Datetime. Years are derived as the integer
            number of years between self.date and target_date.
            Mutually exclusive with years.

    Returns:
        A new Chart with is_symbolic=True, symbolic_kind="profection".
        Planets have lonspeed=latspeed=None.

    Raises:
        ValueError: if both or neither of years/target_date are provided.

    Example:
        >>> profected = natal.profected(years=42)
        >>> profected.is_symbolic  # True
        >>> profected.symbolic_kind  # "profection"
        >>> profected.get(const.SUN).movement  # None — undefined for symbolic
        >>> profected.get(const.SUN).sign  # Real sign at the rotated longitude
    """
    if (years is None) == (target_date is None):
        raise ValueError(
            "Pass exactly one of years= or target_date="
        )
    if target_date is not None:
        # Use existing year-counting logic — read profections.compute()
        # to understand how years are derived from a target date
        years = self._years_to(target_date)

    rotation_deg = (years % 12) * 30

    # Build a new chart with rotated objects
    new_chart = self._copy_for_symbolic(symbolic_kind="profection")
    for obj in new_chart.objects:
        rotated_lon = (obj.lon + rotation_deg) % 360
        # Replace in place — this is a freshly-copied chart, no aliasing
        rotated = obj.with_longitude(rotated_lon)
        # ... copy all relevant fields onto the in-place object, OR
        # ... rebuild the chart's objects list with the new objects
    
    # Re-link objects to houses on the new (symbolic) chart
    new_chart._link_objects_to_houses()

    return new_chart


def _copy_for_symbolic(self, symbolic_kind):
    """Return a deep-copy of this chart with the symbolic flag set.
    
    Internal helper for chart.profected() and similar.
    """
    new = copy.deepcopy(self)
    new.is_symbolic = True
    new.symbolic_kind = symbolic_kind
    return new


def _years_to(self, target_date):
    """Return integer years between self.date and target_date.

    Used by profected(target_date=...). Read profections.compute() for
    the existing implementation of this calculation — reuse the math.
    """
    ...
```

The `_years_to` math is already in `profections.compute()` — read that function and extract the calculation. Don't reinvent.

The "build a new chart with rotated objects" loop is the trickiest part. Two implementation options:

a. **Mutate the deep-copied objects in place.** After `deepcopy`, the new chart's objects are independent of the natal. Update `obj.lon`, `obj.signlon`, `obj.sign`, `obj.lonspeed=None`, `obj.latspeed=None` on each. Cheap, but mutates objects which we just argued against.

b. **Replace the objects list.** Create new Object instances via `with_longitude()` and replace `new_chart.objects = [...]`. Cleaner, but needs to preserve any other state on the objects (orbs, ID, type).

Pick (b) for purity. If (b) turns out to drop important state, fall back to (a) and document.

#### 4.3 Deprecate `profections.compute()`

```python
def compute(chart, date):
    """[DEPRECATED] Use chart.profected(target_date=date) instead.
    
    Returns a profected chart for the given target date.
    Will be removed in 1.0.
    """
    import warnings
    warnings.warn(
        "profections.compute(chart, date) is deprecated. Use "
        "chart.profected(target_date=date) instead. Returns the same "
        "result but with is_symbolic=True and properly cleared speeds. "
        "Will be removed in 1.0.",
        DeprecationWarning,
        stacklevel=2,
    )
    return chart.profected(target_date=date)
```

Note that the new return value (with is_symbolic=True and cleared speeds) is technically a behaviour change for callers of the old API. This is exactly the bug we're fixing. Document loudly in CHANGELOG.

#### 4.4 Deprecate `Object.relocate()`

```python
def relocate(self, lon):
    """[DEPRECATED] In-place version. Use with_longitude() instead.

    relocate() mutates self.lon but leaves lonspeed/latspeed stale.
    For antiscia, use obj.antiscion(). For arbitrary repositioning,
    use obj.with_longitude(lon) which returns a new Object with
    explicit speed handling.

    Will be removed in 1.0.
    """
    import warnings
    warnings.warn(
        "Object.relocate(lon) mutates in place and leaves speed attributes "
        "stale, which causes is_retrograde() and movement to return wrong "
        "answers. Use obj.with_longitude(lon) for a new Object, or "
        "obj.antiscion() / obj.cantiscion() for reflection. "
        "Will be removed in 1.0.",
        DeprecationWarning,
        stacklevel=2,
    )
    # Keep the existing in-place mutation logic for backwards compatibility
    self.lon = lon % 360
    self.signlon = self.lon % 30
    self.sign = const.LIST_SIGNS[int(self.lon // 30)]
    return self  # if existing API returned self
```

Internal callers of `relocate()` must be migrated to `with_longitude()` or `antiscion()`. Search:

```bash
grep -rn "\.relocate(" mayaastrolib/
```

For each call, decide:
- Antiscia/cantiscia path → `obj.antiscion()` or `obj.cantiscion()`
- Profections path → already replaced by `chart.profected()` machinery
- Anywhere else → `obj.with_longitude(lon)` (probably with `preserve_speed=False`, but verify case by case)

After migration, no internal code should call `relocate()`. The deprecation warning should only fire for external callers.

---

## Part 5: Tests

Add `tests/test_with_longitude.py`:

```python
"""Tests for Object.with_longitude (Task 010)."""

import unittest

from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib import const


class WithLongitudeTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)
        self.sun = self.chart.get(const.SUN)

    def test_returns_new_instance(self):
        new = self.sun.with_longitude(100.0)
        self.assertIsNot(new, self.sun)

    def test_does_not_mutate_original(self):
        original_lon = self.sun.lon
        self.sun.with_longitude(100.0)
        self.assertEqual(self.sun.lon, original_lon)

    def test_default_clears_speed(self):
        new = self.sun.with_longitude(100.0)
        self.assertIsNone(new.lonspeed)
        self.assertIsNone(new.latspeed)

    def test_preserve_speed_keeps_speed(self):
        new = self.sun.with_longitude(100.0, preserve_speed=True)
        self.assertEqual(new.lonspeed, self.sun.lonspeed)
        self.assertEqual(new.latspeed, self.sun.latspeed)

    def test_sign_recalculated(self):
        # 100° is in Cancer (90-120)
        new = self.sun.with_longitude(100.0)
        self.assertEqual(new.sign, const.CANCER)
        self.assertAlmostEqual(new.signlon, 10.0, places=5)

    def test_modulo_360(self):
        new = self.sun.with_longitude(370.0)
        self.assertAlmostEqual(new.lon, 10.0, places=5)


class MovementWithNoSpeedTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)
        self.sun = self.chart.get(const.SUN)

    def test_movement_is_none_when_speed_none(self):
        symbolic = self.sun.with_longitude(100.0)
        self.assertIsNone(symbolic.movement)

    def test_movement_is_falsy_when_none(self):
        symbolic = self.sun.with_longitude(100.0)
        self.assertFalse(symbolic.movement)

    def test_movement_is_real_when_speed_preserved(self):
        antiscion_like = self.sun.with_longitude(100.0, preserve_speed=True)
        # Should have a real movement value, not None
        self.assertIsNotNone(antiscion_like.movement)


if __name__ == "__main__":
    unittest.main()
```

Add `tests/test_antiscia.py`:

```python
"""Tests for Object.antiscion / Object.cantiscion (Task 010)."""

import unittest
import warnings

from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib import const, aspects


class AntiscionTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)
        self.sun = self.chart.get(const.SUN)

    def test_antiscion_returns_object(self):
        anti = self.sun.antiscion()
        self.assertIsNotNone(anti)
        # Should be the same type as self.sun
        self.assertEqual(type(anti).__name__, type(self.sun).__name__)

    def test_antiscion_preserves_speed(self):
        anti = self.sun.antiscion()
        self.assertEqual(anti.lonspeed, self.sun.lonspeed)

    def test_antiscion_movement_matches_original(self):
        anti = self.sun.antiscion()
        # movement is a property after Task 006
        self.assertEqual(anti.movement, self.sun.movement)

    def test_antiscion_longitude_is_reflection(self):
        # Verify the formula matches the original aspects.antiscia()
        anti = self.sun.antiscion()
        # The exact formula depends on what's in aspects.py — assert that
        # calling the deprecated path produces the same longitude
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            old_result = aspects.antiscia(self.sun)
        # If old API returned just a longitude, compare to anti.lon
        # If it returned an Object, compare longitudes
        # ... assertion depends on what aspects.antiscia returned ...


class CantiscionTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)
        self.sun = self.chart.get(const.SUN)

    def test_cantiscion_returns_object(self):
        c = self.sun.cantiscion()
        self.assertIsNotNone(c)

    def test_cantiscion_preserves_speed(self):
        c = self.sun.cantiscion()
        self.assertEqual(c.lonspeed, self.sun.lonspeed)


class DeprecatedAntisciaTests(unittest.TestCase):
    def test_aspects_antiscia_warns(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        chart = Chart(date, pos)
        sun = chart.get(const.SUN)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            aspects.antiscia(sun)
            self.assertTrue(
                any(issubclass(x.category, DeprecationWarning) for x in w),
            )


if __name__ == "__main__":
    unittest.main()
```

Add `tests/test_profected_chart.py`:

```python
"""Tests for Chart.profected (Task 010)."""

import unittest
import warnings

from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib import const
from mayaastrolib.predictives import profections


class ProfectedChartTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("1980/06/15", "12:00", "+00:00")
        pos = GeoPos("51n30", "0w08")  # London
        self.natal = Chart(date, pos)

    def test_profected_returns_chart(self):
        p = self.natal.profected(years=42)
        self.assertIsInstance(p, Chart)

    def test_profected_is_symbolic(self):
        p = self.natal.profected(years=42)
        self.assertTrue(p.is_symbolic)
        self.assertEqual(p.symbolic_kind, "profection")

    def test_natal_not_symbolic(self):
        self.assertFalse(self.natal.is_symbolic)
        self.assertIsNone(self.natal.symbolic_kind)

    def test_profected_planets_have_no_speed(self):
        p = self.natal.profected(years=42)
        sun = p.get(const.SUN)
        self.assertIsNone(sun.lonspeed)
        self.assertIsNone(sun.latspeed)

    def test_profected_planets_have_real_position(self):
        p = self.natal.profected(years=42)
        sun = p.get(const.SUN)
        self.assertIsNotNone(sun.sign)
        self.assertGreaterEqual(sun.signlon, 0)
        self.assertLess(sun.signlon, 30)

    def test_profected_movement_is_none(self):
        """The original bug: is_retrograde() / movement returned natal value.
        
        Now they should return None for symbolic positions.
        """
        p = self.natal.profected(years=42)
        sun = p.get(const.SUN)
        self.assertIsNone(sun.movement)

    def test_42_years_rotates_by_180(self):
        # 42 % 12 = 6 signs = 180°
        p = self.natal.profected(years=42)
        natal_sun_lon = self.natal.get(const.SUN).lon
        prof_sun_lon = p.get(const.SUN).lon
        diff = (prof_sun_lon - natal_sun_lon) % 360
        self.assertAlmostEqual(diff, 180.0, places=2)

    def test_zero_years_returns_natal_positions(self):
        p = self.natal.profected(years=0)
        natal_sun = self.natal.get(const.SUN)
        prof_sun = p.get(const.SUN)
        self.assertAlmostEqual(prof_sun.lon, natal_sun.lon, places=5)

    def test_requires_exactly_one_arg(self):
        with self.assertRaises(ValueError):
            self.natal.profected()
        with self.assertRaises(ValueError):
            self.natal.profected(
                years=42,
                target_date=Datetime("2022/06/15", "12:00", "+00:00"),
            )


class DeprecatedProfectionsComputeTests(unittest.TestCase):
    def test_compute_warns(self):
        date = Datetime("1980/06/15", "12:00", "+00:00")
        pos = GeoPos("51n30", "0w08")
        chart = Chart(date, pos)
        target = Datetime("2022/06/15", "12:00", "+00:00")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            profections.compute(chart, target)
            self.assertTrue(
                any(issubclass(x.category, DeprecationWarning) for x in w),
            )

    def test_compute_returns_symbolic_chart(self):
        """Behaviour change: compute() now returns symbolic chart with
        cleared speeds, fixing the bug it had."""
        date = Datetime("1980/06/15", "12:00", "+00:00")
        pos = GeoPos("51n30", "0w08")
        chart = Chart(date, pos)
        target = Datetime("2022/06/15", "12:00", "+00:00")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = profections.compute(chart, target)

        self.assertTrue(result.is_symbolic)
        self.assertIsNone(result.get(const.SUN).lonspeed)


class DeprecatedRelocateTests(unittest.TestCase):
    def test_relocate_warns(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        chart = Chart(date, pos)
        sun = chart.get(const.SUN)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            sun.relocate(100.0)
            self.assertTrue(
                any(issubclass(x.category, DeprecationWarning) for x in w),
            )


if __name__ == "__main__":
    unittest.main()
```

## Update CHANGELOG.md

Under `[Unreleased]`:

```markdown
### Added
- `Object.with_longitude(lon, *, preserve_speed=False)` — returns a new Object at the given longitude. By default clears speed (signalling symbolic position); `preserve_speed=True` keeps original dynamics (for antiscia).
- `Object.antiscion()` and `Object.cantiscion()` — return new Objects representing the antiscion/cantiscion positions.
- `Chart.profected(years=N)` and `Chart.profected(target_date=D)` — returns a profected chart with `is_symbolic=True` and properly cleared speeds.
- `Chart.is_symbolic` (bool) and `Chart.symbolic_kind` (str) — flag whether a chart represents derived positions rather than computed ones.
- `Object.movement` and `Object.is_retrograde()` now return None when speed is undefined (symbolic positions).

### Fixed
- Profected charts no longer report stale natal speed/retrograde state. Previously, `profections.compute()` rotated planet longitudes but left `lonspeed`/`latspeed` unchanged, so `is_retrograde()` on a profected chart returned the natal answer. The new `chart.profected()` correctly clears speed-derived attributes for symbolic positions.

### Deprecated
- `Object.relocate(lon)` — in-place mutation that leaves speeds stale. Use `obj.with_longitude(lon)` instead. Will be removed in 1.0.
- `aspects.antiscia(obj)` and `aspects.cantiscia(obj)` — use `obj.antiscion()` / `obj.cantiscion()`. Will be removed in 1.0.
- `predictives.profections.compute(chart, date)` — use `chart.profected(target_date=date)`. Will be removed in 1.0.

### Changed (behaviour)
- `predictives.profections.compute()` now returns a chart with `is_symbolic=True` and cleared speeds (via the new `chart.profected()` implementation it now wraps). Callers using the result for ephemeris-style queries (`is_retrograde`, `movement`) will see None where they previously got natal values. This is the bug fix referenced under Fixed.
```

## Update docs/PROPERTY-MIGRATION.md (or equivalent from Task 006)

Add an entry noting that `Object.movement` and `Object.is_retrograde` now return None for symbolic positions, and that the `_DualAccess` wrapper was updated to pass through None unwrapped.

## Update docs/IDEAS.md

Add this entry:

```markdown
## Predictives as Chart methods (full audit Item 17)

**Status:** Partially addressed in Task 010.

Task 010 added `Chart.profected()` as a method-style entry point.
Other predictives — solar/lunar returns, primary directions, transits —
remain as top-level functions in their own modules (`predictives.returns`,
`predictives.primarydirections`).

Future work should consider adding:
- `Chart.solarReturn(year)` → ProfectedChart equivalent for solar returns
- `Chart.lunarReturn(date)` → for lunar returns
- `Chart.directions(target_date)` → primary directions

These each have their own design questions:
- Solar return semantics (calendar year vs Nth birthday) — see audit Item 16
- Whether they're symbolic charts or real ones (returns are real, directions are symbolic)

Defer until Phase 2 design conversation.
```

## Out of scope

- Solar/lunar returns becoming methods (Item 17 is partially addressed; full coverage deferred)
- Primary directions API improvements
- Solar return semantic question (calendar year vs Nth birthday) — Item 16
- Type hints on the new methods — Phase 1 follow-up
- Thread-safety considerations for the new symbolic chart machinery — already thread-safe by being immutable, but verify

## Process

1. Branch from `development`:

   ```
   git checkout development
   git pull origin development
   git checkout -b task-010-symbolic-charts
   ```

2. Suggested commit structure (smaller commits help review enormously here):
   - `feat: add Object.with_longitude with preserve_speed flag`
   - `refactor: handle None speed in movement and is_retrograde`
   - `refactor: update _DualAccess to pass through None unwrapped`
   - `feat: add Object.antiscion and Object.cantiscion methods`
   - `refactor: deprecate aspects.antiscia and cantiscia as wrappers`
   - `feat: add is_symbolic and symbolic_kind to Chart`
   - `feat: add Chart.profected method with years and target_date`
   - `refactor: deprecate profections.compute as wrapper for Chart.profected`
   - `refactor: deprecate Object.relocate with migration message`
   - `refactor: migrate internal callers from relocate to with_longitude`
   - `test: cover with_longitude, antiscion, cantiscion`
   - `test: cover symbolic charts and Chart.profected`
   - `test: regression test for stale-speed bug on profected charts`
   - `docs: update CHANGELOG, IDEAS, PROPERTY-MIGRATION for Task 010`

3. Pre-completion checklist:
   - `ruff format --check .` passes
   - `ruff check .` passes
   - `mypy mayaastrolib/` — no new errors
   - `pytest -x` passes — all tests including new ones
   - The bug regression test (`test_profected_movement_is_none`) is the key one — it must pass
   - Internal `relocate()` calls are fully migrated; running `pytest` should NOT produce DeprecationWarnings for `relocate` from inside the library

4. PROJECT-LOG.md entry must include:
   - Full list of internal `relocate()` callers and what they were migrated to
   - The exact longitude formulas extracted from the original `aspects.antiscia()` / `cantiscia()` for the new methods
   - The full list of speed-dependent methods on Object that were updated to handle None
   - Confirmation that `_DualAccess` was updated to pass through None
   - Confirmation that the regression test for the stale-speed bug passes

5. Push:

   ```
   git push -u origin task-010-symbolic-charts
   ```

6. Verify CI green on all three Python versions.

7. DO NOT merge. This is the highest-stakes review since Task 005.

## Definition of done

- `Object.with_longitude()` exists with the correct semantics
- `Object.antiscion()` and `Object.cantiscion()` exist
- `Chart.profected()` exists and returns a properly symbolic chart
- `obj.movement`, `obj.is_retrograde()` return None for symbolic positions
- `chart.is_symbolic` is True for profected charts, False for natal
- All four deprecation paths (`relocate`, `aspects.antiscia`, `aspects.cantiscia`, `profections.compute`) emit warnings but still work
- No internal library code calls the deprecated APIs
- The original bug regression test passes — `profected_chart.get(SUN).movement` is None
- All existing 45+ tests still pass
- The new ~20 tests for this task pass
- CI green
- CHANGELOG updated with the four-section structure (Added, Fixed, Deprecated, Changed)

## If something goes wrong

This is a multi-part task with real interdependencies. Specific failure modes to watch for:

**The `_DualAccess` None-passthrough breaks something.** Task 006 wrote the wrapper to never return raw values. Adding the None passthrough is a behaviour change. If a test fails because something expected `_DualAccess(None)` and got `None`, the wrapper or the call site needs adjustment.

**`Chart.profected()` produces wrong sign assignments.** If the rotation math is wrong (off by 30°, off by ±1 modulo, etc.), the test `test_42_years_rotates_by_180` will fail. Cross-check against the existing `profections.compute()` math.

**A `_compat`-style decorator from Task 006 conflicts with the new None handling.** If `obj.movement` returns the right value type but `obj.movement is None` doesn't work because of wrapper semantics, the wrapper needs adjustment. See Part 2.

**Internal callers of `relocate()` are missed.** Run `grep -rn "\.relocate(" mayaastrolib/` after migration. Should return only the deprecated method definition itself, no callers.

**`aspects.antiscia()` may return a longitude, not an Object.** If the old API returned a number, the deprecated wrapper that wraps `obj.antiscion()` (which returns an Object) is a behaviour change. Decide: either return `obj.antiscion().lon` from the deprecated wrapper, or update the deprecation message to say the return type changed. The latter is cleaner. Document in CHANGELOG under "Changed (behaviour)".

If the task becomes unmanageable mid-flight:

1. `git reset --hard development`
2. Detailed failure report in PROJECT-LOG.md covering exactly what was tried, what failed, what surprised
3. Commit on `task-010-failed-attempt-1`
4. Push and stop

This task is large enough that a clean failure with diagnosis is genuinely better than a half-broken push. Don't be heroic — surface for review.

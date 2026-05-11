# Task 006: Object–Chart Integration

## Context

You are working in the `mayaastrolib` repository. Before doing anything:

1. Read `CLAUDE.md` in full.
2. Read `docs/RECON.md` for module structure and dependency graph.
3. Read `docs/PROJECT-LOG.md` for recent task entries (Tasks 002 through 005).
4. Confirm Task 005 (rename) has been merged to `development`:

   ```
   git log --oneline development -5
   ```

   The most recent commits should be from Task 005 (the rename and shim work). If they are not, STOP and report.

5. Confirm `pytest tests/` passes cleanly with at least 33 tests on `development`. If it doesn't, the safety net isn't in place and we shouldn't be making model changes. Stop and report.

## Why this task exists

A demo webapp built against `mayaastrolib` v0.3.0 surfaced two related model problems:

1. **No way to ask "what house is this planet in?"** Every consumer iterates `chart.houses` and calls `house.hasObject(obj)`. The library knows the answer but doesn't expose it.

2. **Methods that look like attributes silently misbehave.** `obj.movement` returns a bound method (which is truthy in conditionals); `obj.movement()` returns the actual string. Real bug encountered: `if obj.movement:` was always true because the method, not its return value, was being tested. Same pattern exists on `Object.gender`, `Object.faction`, `Object.element`, `House.condition`, `House.gender`, `Aspect.movement`, `FixedStar.orb`.

This task addresses both. It is the largest behavioural change in Phase 1, but every step is non-breaking: existing code continues to work.

## Design decisions (already made — do not relitigate)

**Where `obj.house` is set:** in `Chart.__init__`, after both objects and houses are computed. Not as a constructor parameter on `Object` (would couple the ephemeris layer to houses). Not as a back-reference property (introduces circular references and lazy-evaluation surprises). Stamped explicitly:

```python
# In Chart.__init__, after self.objects and self.houses exist:
for obj in self.objects:
    obj.house = self._compute_house_for(obj)  # or None for angles/fixed stars
for house in self.houses:
    house.objects = [o for o in self.objects if o.house is house]
```

**Method-vs-property migration:** add `@property` versions, keep method-style access working with a `DeprecationWarning`. Plan removal in version 1.0. Be loud about the deprecation — users should see it in normal pytest runs and in production logs.

## Task scope

### 1. Identify all method-style getters that should be properties

Read each of these files and list every method that:
- Takes only `self`
- Returns a derived value (not stored state)
- Is named in a way that suggests it's a property (no `get`, `is`, or `set` prefix)

Files to audit:
- `mayaastrolib/object.py` — `Object`, `House`, `FixedStar`, `GenericObject`
- `mayaastrolib/aspects.py` — `Aspect`, `AspectObject`

Suspected list (verify by reading):
- `Object.movement`, `Object.gender`, `Object.faction`, `Object.element`, `Object.orb`, `Object.meanMotion`
- `House.num`, `House.condition`, `House.gender`
- `Aspect.movement`, `Aspect.direction`
- `FixedStar.orb`

If a method is conceptually a *computation* that takes time or arguments, leave it as a method. If it's a *lookup* with no arguments, it's a property candidate.

Document the final list in `docs/PROPERTY-MIGRATION.md` with: class, method name, current return value, brief rationale.

### 2. Build the deprecation infrastructure

Create `mayaastrolib/_compat.py`:

```python
"""Compatibility shims for the method-to-property migration.

When a method is converted to a @property, the old method-style access
must keep working with a DeprecationWarning. This module provides the
helper that makes that happen.

Plan: remove this module and all its uses in version 1.0.
"""

import functools
import warnings


def property_with_method_compat(func):
    """Decorate a method so it works as both a property and a callable.

    Property access (the new way) returns the value directly.
    Method-style access (the old way) returns the value but emits a
    DeprecationWarning pointing at the call site.

    Usage:
        class Object:
            @property_with_method_compat
            def movement(self):
                return _compute_movement(self)

    Then both `obj.movement` and `obj.movement()` return the value;
    the latter emits a warning.
    """
    name = func.__name__

    class _DualAccess:
        def __init__(self, value, owner):
            self._value = value
            self._owner_class = type(owner).__name__

        def __call__(self):
            warnings.warn(
                f"{self._owner_class}.{name} is now a property, not a method. "
                f"Use `obj.{name}` instead of `obj.{name}()`. "
                f"Method-style access will be removed in version 1.0.",
                DeprecationWarning,
                stacklevel=2,
            )
            return self._value

        # Forward common operations to the value so legacy code keeps working
        def __eq__(self, other):
            return self._value == other

        def __ne__(self, other):
            return self._value != other

        def __bool__(self):
            return bool(self._value)

        def __hash__(self):
            return hash(self._value)

        def __repr__(self):
            return repr(self._value)

        def __str__(self):
            return str(self._value)

    @property
    @functools.wraps(func)
    def wrapper(self):
        value = func(self)
        return _DualAccess(value, self)

    return wrapper
```

Test this carefully. Write `tests/test_compat.py` covering:
- Property access returns value-equivalent
- Method access returns value AND emits DeprecationWarning
- Comparison operators (`==`, `!=`) work without dereferencing
- Boolean conversion works (this is the bug class — must return based on the *value*, not the wrapper's truthiness)
- Stringification works
- Hashing works (so the result can be used as a dict key)

The `__bool__` test is critical. Specifically test:

```python
def test_bool_returns_value_truthiness():
    """The original bug: bound method was truthy, value was falsy."""
    # Set up an Object whose movement is a falsy string ('' or similar).
    # Confirm that `if obj.movement:` evaluates to False, not True.
```

If there's no naturally falsy value in the affected methods, construct a synthetic test case.

### 3. Apply `@property_with_method_compat` to the identified methods

For each method in the list from Step 1, decorate it. Example:

```python
# Before
class Object(GenericObject):
    def movement(self):
        if abs(self.lonspeed) < MAX_ORBS[const.STATIONARY]:
            return const.STATIONARY
        return const.DIRECT if self.lonspeed >= 0 else const.RETROGRADE

# After
from mayaastrolib._compat import property_with_method_compat

class Object(GenericObject):
    @property_with_method_compat
    def movement(self):
        if abs(self.lonspeed) < MAX_ORBS[const.STATIONARY]:
            return const.STATIONARY
        return const.DIRECT if self.lonspeed >= 0 else const.RETROGRADE
```

Update internal call sites within `mayaastrolib/` to use property access (no parentheses). The library should not generate its own DeprecationWarnings.

Test sites to verify continue to work:
- `tests/test_chart.py`
- `tests/test_dignities_*.py`
- `tests/test_protocols_*.py`
- `tests/test_tools_*.py`
- All recipes in `recipes/`

If any test file uses method-style access, leave it alone for this task — it'll fire deprecation warnings in pytest output, and that's the point: visible deprecation. Document the warnings in PROJECT-LOG.md.

### 4. Add `obj.house` and `house.objects`

In `mayaastrolib/chart.py`, modify `Chart.__init__`:

After the existing initialisation (after `self.objects`, `self.houses`, `self.angles` are populated), add:

```python
# Stamp house membership onto each object. None for angles, fixed stars,
# and any object that doesn't fall in any house (shouldn't happen in
# practice, but defensive).
self._link_objects_to_houses()

def _link_objects_to_houses(self):
    """Set obj.house on each object and house.objects on each house."""
    for obj in self.objects:
        obj.house = None
        for house in self.houses:
            if house.hasObject(obj):
                obj.house = house
                break
    for house in self.houses:
        house.objects = [o for o in self.objects if o.house is house]
```

Make `obj.house` and `house.objects` documented public attributes. Add docstrings.

### 5. Add `Chart.houseOf(obj)` and `Chart.objectsInHouse(house_id)`

Convenience methods on `Chart`:

```python
def houseOf(self, obj):
    """Return the House containing obj, or None if obj is not in any house.
    
    Equivalent to obj.house, provided for callers who have the chart
    but only the object's id.
    
    Args:
        obj: An Object instance, or a planet ID string (e.g. const.SUN).
    
    Returns:
        The House instance, or None.
    """
    if isinstance(obj, str):
        obj = self.getObject(obj)
        if obj is None:
            return None
    return getattr(obj, 'house', None)

def objectsInHouse(self, house_id):
    """Return the list of Objects in the named house.
    
    Args:
        house_id: A house ID string (e.g. const.HOUSE5).
    
    Returns:
        List of Object instances, possibly empty.
    """
    house = self.getHouse(house_id)
    if house is None:
        return []
    return list(house.objects)
```

### 6. Tests

Add `tests/test_chart_house_links.py`:

- Building a Chart populates `obj.house` for every planet
- `obj.house` is None for angle objects (Asc, MC, Desc, IC) — verify this matches expected behaviour, document if not
- `obj.house.hasObject(obj)` is True (round-trip)
- `house.objects` contains exactly the objects whose `house is house`
- `chart.houseOf(planet)` returns the same as `planet.house`
- `chart.houseOf(const.SUN)` (passing a string) works
- `chart.objectsInHouse(const.HOUSE5)` returns a list whose every element has `house.id == 'House5'`

Also add a regression test for the original bug:

```python
def test_movement_property_truthiness():
    """obj.movement was a bound method, always truthy regardless of value.
    
    Bug discovered while building the demo webapp on 2026-05-07.
    Property access must return the value, whose truthiness reflects the
    actual movement state.
    """
    # Construct or compute a chart with a stationary planet (movement is
    # const.STATIONARY, which is a non-empty string and therefore truthy)
    # and verify that property access returns the string, not a method.
    # The key assertion: type(obj.movement) is str (or _DualAccess), not method.
    ...
```

### 7. Update CHANGELOG.md

Under `[Unreleased]`:

```markdown
### Added
- `Chart.houseOf(obj)` returns the house containing an object
- `Chart.objectsInHouse(house_id)` returns objects in a house
- `Object.house` attribute, set during Chart construction
- `House.objects` attribute, set during Chart construction
- Property-style access for `Object.movement`, `Object.gender`, `Object.faction`, `Object.element`, `Object.orb`, `Object.meanMotion`, `House.num`, `House.condition`, `House.gender`, `Aspect.movement`, `Aspect.direction`, `FixedStar.orb`

### Deprecated
- Method-style access for the above (e.g. `obj.movement()`). Emits DeprecationWarning. Will be removed in version 1.0. Use `obj.movement` instead.
```

## Out of scope

- Removing the method-style access (deferred to 1.0)
- Adding type hints (later in Phase 1)
- Fixing the global state in `dignities.essential` (Task 008)
- Datetime ergonomics (Task 007)
- Aspect API improvements (later)
- Any new astrology features

## Process

1. Branch from `development`:

   ```
   git checkout development
   git pull origin development
   git checkout -b task-006-object-chart-integration
   ```

2. Suggested commit structure:
   - `feat: add property_with_method_compat decorator with tests`
   - `feat: convert Object methods to properties (movement, gender, faction, element, orb, meanMotion)`
   - `feat: convert House methods to properties (num, condition, gender)`
   - `feat: convert Aspect methods to properties (movement, direction)`
   - `feat: convert FixedStar.orb to property`
   - `feat: link objects and houses on Chart construction`
   - `feat: add Chart.houseOf and Chart.objectsInHouse`
   - `test: regression test for property-truthiness bug`
   - `docs: update CHANGELOG and add PROPERTY-MIGRATION.md`

3. Pre-completion checklist:
   - `ruff format --check .` passes
   - `ruff check .` passes
   - `mypy mayaastrolib/` — no new errors compared to before
   - `pytest -x` passes — ALL tests, including new ones
   - The new tests in `test_chart_house_links.py` and `test_compat.py` all pass
   - DeprecationWarnings appear in pytest output for any tests that still use method-style access (this is expected and desirable — flush them out)

4. Append entry to `docs/PROJECT-LOG.md` covering:
   - Final list of methods converted to properties
   - Any unexpected method that didn't fit the property pattern (and why)
   - Any tests that broke and how they were fixed
   - Performance impact (if any) of the per-Chart house-linking step
   - The pytest output showing the regression test passes

5. Push:

   ```
   git push -u origin task-006-object-chart-integration
   ```

6. Verify CI is green on the branch.

7. DO NOT merge to development. Leave for human review.

## Definition of done

- All identified methods accept both property and method style access
- Method-style access emits DeprecationWarning
- The bug class (`if obj.movement:` always truthy) is fixed
- `obj.house` is set after Chart construction for every Object
- `house.objects` is set after Chart construction for every House
- `Chart.houseOf()` and `Chart.objectsInHouse()` exist and work
- New tests cover all of the above
- Existing 33+ tests still pass
- CI green on the branch
- CHANGELOG updated
- `docs/PROPERTY-MIGRATION.md` exists and documents the migration

## If something goes wrong

Most likely failure mode: the `_DualAccess` wrapper breaks something subtle. For example, if existing code does `chart.objects.filter(lambda o: o.movement == const.RETROGRADE)`, the `==` operator must work correctly — and it does in the design above, but only because we explicitly implemented `__eq__`. If a test fails because a comparison breaks, check whether the operator is forwarded.

Second most likely: a recipe calls method-style access (`obj.movement()`) and the test for that recipe now emits warnings into stdout. That's fine — note in the log and move on. Don't update recipes in this task.

If you discover a method that genuinely should NOT be a property (e.g. it has side effects, or takes time, or returns different values on different calls), document that in PROPERTY-MIGRATION.md as a deliberate exclusion. Don't force it into the property model.

If house linking fails for some object type (e.g. Pars Fortuna behaves oddly), set `obj.house = None` and add a note. Don't crash Chart construction over it.

If you can't complete the task in a reasonable time:

1. `git reset --hard development`
2. Detailed failure report in PROJECT-LOG.md
3. Commit on `task-006-failed-attempt-1` and push
4. Stop

A clean failure with diagnosis notes is better than a half-broken push.

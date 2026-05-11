# Task 009: Aspect API Improvements and Standard Object Lists

## Context

You are working in the `mayaastrolib` repository. Before doing anything:

1. Read `CLAUDE.md` in full.
2. Read `mayaastrolib/aspects.py` end to end. Pay particular attention to `Aspect`, `AspectObject`, and `getAspect()`. Note the existing patterns — what attributes Aspect exposes, how AspectObject is constructed, what NO_ASPECT looks like.
3. Read `mayaastrolib/const.py` end to end. Note the existing list constants (`LIST_SEVEN_PLANETS`, `LIST_OBJECTS`, etc.) and their structure.
4. Read `mayaastrolib/_compat.py` to understand the deprecation pattern established in Task 006. Use the same pattern in this task — do NOT invent a new deprecation mechanism.
5. Read `docs/PROJECT-LOG.md` for entries from Tasks 006, 007, 008. These set the patterns this task follows.
6. Confirm Task 008 has been merged to `development`:

   ```
   git log --oneline development -10
   ```

   Should show the Task 008 commits (parameterise dignities.essential, thread-safety tests). If not, STOP.

7. Confirm `pytest tests/` passes cleanly. The full test suite (40+ tests by now) must hold.

## Why this task exists

The audit conducted after Task 005 found multiple usability issues clustered around two areas. This task addresses both:

**Aspect API issues (audit items 9, 10, 11):**
- `asp.type` returns an integer (0, 60, 90, 120, 180), forcing every consumer to maintain a `{0: "Conjunction", ...}` mapping
- `asp.active` and `asp.passive` are stripped-down AspectObject wrappers, not the original Object — losing access to `.movement`, `.house`, `.element`, etc.
- `getAspect()` returns a sentinel Aspect with `type == NO_ASPECT` instead of `None`, requiring `.exists()` checks

**Object list issues (audit items 3, 12):**
- No canonical "modern planets" list — only `LIST_SEVEN_PLANETS` (traditional) or `LIST_OBJECTS` (everything including Pars Fortuna and Syzygy)
- No Vedic-default list for the upcoming Phase 2 work
- No semantic groupings (lights, personal, social, transpersonal) that consumers commonly want

Both are pure additions to the API. Backwards compatibility is preserved everywhere.

## Design decisions (already made — do not relitigate)

**Aspect API approach:** add new attributes/methods alongside the existing ones. Mark the legacy ones deprecated. Remove in 1.0. This matches the pattern established in Task 006.

**Object lists approach:** pure additions to `const.py`. No removals, no deprecations. The existing lists stay exactly as they are.

**Deprecation pattern:** reuse `mayaastrolib._compat.property_with_method_compat` from Task 006 where applicable. For the new patterns specific to this task (deprecating a sentinel return value), follow the same `warnings.warn(..., DeprecationWarning, stacklevel=2)` style with explicit migration guidance in the warning message.

## Task scope

### Part 1: Aspect API improvements

#### 1.1 Add `Aspect.name`

Add a `name` property to the `Aspect` class returning the human-readable string for the aspect type.

```python
ASPECT_NAMES = {
    0: "Conjunction",
    30: "Semi-Sextile",
    45: "Semi-Square",
    60: "Sextile",
    72: "Quintile",
    90: "Square",
    120: "Trine",
    135: "Sesquiquadrate",
    144: "Bi-Quintile",
    150: "Quincunx",
    180: "Opposition",
}
```

Verify the integer values match what the library actually uses (read `const.py` for the canonical list — the names above are illustrative, the actual angles are what matter). Add aspects only for values that exist in `const.LIST_ASPECTS` (or wherever the canonical list lives).

```python
class Aspect:
    @property
    def name(self):
        """Human-readable aspect name (e.g. 'Trine', 'Square').

        Returns 'No Aspect' if this is a sentinel Aspect with type == NO_ASPECT.
        See also `Aspect.exists()` and the new `getAspect()` behaviour
        that returns None instead of a sentinel.
        """
        return const.ASPECT_NAMES.get(self.type, "No Aspect")
```

Add `ASPECT_NAMES` to `mayaastrolib/const.py` as a public mapping. Consumers should be able to do `from mayaastrolib import const; const.ASPECT_NAMES[60]`.

#### 1.2 Preserve full Object reference on `Aspect`

Currently `Aspect.active` and `Aspect.passive` are `AspectObject` instances — frozen snapshots of the original Object's state at the time the aspect was computed. This loses access to `.movement`, `.house`, `.element`, and any other properties the Object exposes.

The fix: store the original Object reference. Expose:

- `Aspect.active` — keep the existing AspectObject for backwards compatibility (deprecated)
- `Aspect.passive` — same
- `Aspect.activeObj` — the full original Object
- `Aspect.passiveObj` — same

Wait — re-read the existing code first. There may be a cleaner option.

If `AspectObject` is rarely used externally and the migration is straightforward, the cleaner approach is:

- `Aspect.active` and `Aspect.passive` become the full Objects (breaking change in technicality, but only if anyone was accessing AspectObject-specific attributes)
- The old AspectObject snapshot becomes accessible as `Aspect.activeSnapshot` and `Aspect.passiveSnapshot` for backwards compatibility

**Decision rule:** read the existing test files (`tests/test_aspects.py` if it exists, plus any other test that touches Aspect) and the recipes. If they only access attributes that exist on both Object and AspectObject (id, sign, signlon), then go with the cleaner approach — make `active`/`passive` the full Objects. If they access AspectObject-specific attributes (e.g. fields the AspectObject computed and stored), keep the AspectObject available and add `activeObj`/`passiveObj` for the full reference.

Document the choice in PROJECT-LOG.md with reasoning.

#### 1.3 `getAspect()` returns `Optional[Aspect]`

Currently `getAspect(obj1, obj2, aspList)` returns an Aspect with `type == NO_ASPECT` when there's no aspect. The Pythonic API is to return `None`.

Approach: add a new `getAspect()` behaviour that returns `None`, and rename the old behaviour to `getAspectOrSentinel()` (deprecated).

```python
def getAspect(obj1, obj2, aspList):
    """Return the aspect between two objects, or None if no aspect exists.

    Args:
        obj1: First object.
        obj2: Second object.
        aspList: List of aspect angles to consider.

    Returns:
        An Aspect instance, or None if no aspect exists within orbs.

    Note:
        This replaces the previous behaviour where a sentinel Aspect with
        type == NO_ASPECT was returned. The old behaviour is available via
        `getAspectOrSentinel()` but is deprecated and will be removed in
        version 1.0.
    """
    asp = getAspectOrSentinel(obj1, obj2, aspList)
    if asp.type == const.NO_ASPECT:
        return None
    return asp


def getAspectOrSentinel(obj1, obj2, aspList):
    """[DEPRECATED] Return the aspect or a NO_ASPECT sentinel.

    Use getAspect() instead, which returns None for no-aspect cases.
    This function will be removed in version 1.0.
    """
    import warnings
    warnings.warn(
        "getAspectOrSentinel() is deprecated. Use getAspect(), which returns "
        "None when no aspect exists. This function will be removed in 1.0.",
        DeprecationWarning,
        stacklevel=2,
    )
    # ... existing logic that returns the sentinel ...
```

If renaming the existing function is awkward (e.g. it's heavily used internally), the alternative is to make `getAspect()` accept an opt-in parameter:

```python
def getAspect(obj1, obj2, aspList, return_none_on_miss=True):
    ...
```

Pick whichever is cleaner. Document the choice.

**Important:** update internal call sites within `mayaastrolib/` to handle `None` returns gracefully. Search for every call to `getAspect()`:

```bash
grep -rn "getAspect(" mayaastrolib/ tests/ recipes/
```

For each, decide whether the call site expected the sentinel pattern. If yes, update it to handle `None`. If the call site already used `.exists()` or compared `.type == NO_ASPECT`, update it to a clean `if aspect is not None:` check.

### Part 2: Standard object lists

#### 2.1 Add new constants to `const.py`

Append to `mayaastrolib/const.py`. Verify the planet ID constants exist before referencing them — some (Chiron, Pars Fortuna, North/South Node) may have specific IDs in the library that need to match.

```python
# ----------------------------------------------------------------------
# Standard object lists (added in Task 009)
#
# These are convenience groupings for common consumer use cases. The
# lists are pure references — adding new objects to a chart still
# requires passing the list explicitly to Chart(IDs=...).
# ----------------------------------------------------------------------

# All ten "modern" planets — Sun through Pluto
LIST_MODERN_PLANETS = [
    SUN, MOON, MERCURY, VENUS, MARS,
    JUPITER, SATURN, URANUS, NEPTUNE, PLUTO,
]

# Modern Western default — modern planets, lunar nodes, Chiron
LIST_TROPICAL_DEFAULT = LIST_MODERN_PLANETS + [
    NORTH_NODE, SOUTH_NODE, CHIRON,
]

# Vedic / sidereal default — seven traditional planets + Rahu, Ketu
# (No outer planets; classical Vedic doesn't use Uranus/Neptune/Pluto)
LIST_VEDIC_DEFAULT = [
    SUN, MOON, MERCURY, VENUS, MARS, JUPITER, SATURN,
    NORTH_NODE, SOUTH_NODE,
]

# The two luminaries
LIST_LIGHTS = [SUN, MOON]

# Personal planets — those with fast-moving cycles relevant to individual personality
LIST_PERSONAL_PLANETS = [SUN, MOON, MERCURY, VENUS, MARS]

# Social planets — generational but still personally felt
LIST_SOCIAL_PLANETS = [JUPITER, SATURN]

# Transpersonal / outer planets — generational, slow-moving
LIST_TRANSPERSONAL = [URANUS, NEPTUNE, PLUTO]

# Lunar nodes — mean nodes by default (the library's existing default)
LIST_LUNAR_NODES = [NORTH_NODE, SOUTH_NODE]
```

**Verification step:** before committing, confirm each constant referenced (`SUN`, `MOON`, ..., `CHIRON`, `NORTH_NODE`, `SOUTH_NODE`, `URANUS`, `NEPTUNE`, `PLUTO`) actually exists in `const.py`. If any are missing — particularly `CHIRON` or the outer planets — flag in PROJECT-LOG.md and either:
- Add the missing constant if it's just an oversight (some object IDs may exist as strings without named constants)
- Remove that constant from the list with a comment explaining why
- Note as a follow-up task

The library may not currently support all these objects in `Chart()` construction. That's fine — these lists are convenience groupings, not promises. A consumer who passes `LIST_TROPICAL_DEFAULT` to `Chart()` and gets an error about an unsupported object is getting the right error from the right layer; this task doesn't fix object support, only naming.

#### 2.2 Document the lists

Create `docs/OBJECT-LISTS.md`:

```markdown
# Object Lists in mayaastrolib

`mayaastrolib.const` provides several pre-defined object lists for common
use cases. Pass these to `Chart()` via the `IDs=` parameter to control
which objects are computed.

## Available lists

| Constant                | Description                                  |
|-------------------------|----------------------------------------------|
| `LIST_SEVEN_PLANETS`    | Traditional: Sun through Saturn              |
| `LIST_MODERN_PLANETS`   | Modern: Sun through Pluto                    |
| `LIST_TROPICAL_DEFAULT` | Modern + lunar nodes + Chiron                |
| `LIST_VEDIC_DEFAULT`    | Seven planets + Rahu + Ketu                  |
| `LIST_LIGHTS`           | Sun and Moon only                            |
| `LIST_PERSONAL_PLANETS` | Sun, Moon, Mercury, Venus, Mars              |
| `LIST_SOCIAL_PLANETS`   | Jupiter, Saturn                              |
| `LIST_TRANSPERSONAL`    | Uranus, Neptune, Pluto                       |
| `LIST_LUNAR_NODES`      | North Node and South Node                    |
| `LIST_OBJECTS`          | Everything including Pars Fortuna, Syzygy    |

## When to use which

**Modern Western charts.** Use `LIST_TROPICAL_DEFAULT`. This is what most
consumer-facing astrology software computes. Includes the outer planets
which are not part of the traditional system.

**Traditional / Hellenistic / Medieval.** Use `LIST_SEVEN_PLANETS`. Outer
planets and Chiron are anachronistic to these traditions.

**Vedic / sidereal (when Phase 2 ships).** Use `LIST_VEDIC_DEFAULT`. The
classical Vedic system uses the seven visible planets plus the lunar
nodes (Rahu/Ketu). Outer planets are sometimes added in modern Vedic
practice, but not by default.

**Comparative analyses.** `LIST_PERSONAL_PLANETS`, `LIST_SOCIAL_PLANETS`,
and `LIST_TRANSPERSONAL` are useful for filtering or grouping output
without manually maintaining sub-lists.

## Examples

```python
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib import const

date = Datetime("2015/03/13", "17:00", "+00:00")
pos = GeoPos("38n32", "8w54")

# Modern Western chart with outer planets
chart = Chart(date, pos, IDs=const.LIST_TROPICAL_DEFAULT)

# Traditional chart with only the seven planets
chart = Chart(date, pos, IDs=const.LIST_SEVEN_PLANETS)

# Just the lights
chart = Chart(date, pos, IDs=const.LIST_LIGHTS)
```

## Defining custom lists

The lists are plain Python lists. Combine and customise freely:

```python
my_list = const.LIST_MODERN_PLANETS + [const.PARS_FORTUNA]
```
```

### Part 3: Tests

Add `tests/test_aspect_api.py`:

```python
"""Tests for the API improvements added in Task 009."""

import unittest
import warnings

from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib import const
from mayaastrolib import aspects


class AspectNameTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)

    def test_aspect_has_name_property(self):
        sun = self.chart.get(const.SUN)
        moon = self.chart.get(const.MOON)
        asp = aspects.getAspect(sun, moon, const.MAJOR_ASPECTS)
        if asp is not None:
            self.assertIsInstance(asp.name, str)
            self.assertIn(asp.name, const.ASPECT_NAMES.values())

    def test_aspect_names_constant_exists(self):
        self.assertIn(0, const.ASPECT_NAMES)
        self.assertEqual(const.ASPECT_NAMES[0], "Conjunction")
        self.assertEqual(const.ASPECT_NAMES[120], "Trine")


class AspectObjectFidelityTests(unittest.TestCase):
    """Verify that Aspect preserves full Object access on .active/.passive
    (or via the new attribute, depending on the design choice made).
    """
    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)

    def test_can_access_movement_through_aspect(self):
        """The original bug: asp.active.movement returned a frozen string,
        not the actual planet's current movement state.
        """
        sun = self.chart.get(const.SUN)
        mars = self.chart.get(const.MARS)
        asp = aspects.getAspect(sun, mars, const.MAJOR_ASPECTS)
        if asp is not None:
            # Whichever attribute exposes the full Object — adapt to the
            # design choice made (asp.active or asp.activeObj)
            obj = getattr(asp, 'activeObj', asp.active)
            # Verify we can read .movement (the property from Task 006)
            self.assertIsNotNone(obj.movement)


class GetAspectReturnTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)

    def test_no_aspect_returns_none(self):
        """The new pythonic behaviour: None instead of a sentinel."""
        # Construct two objects we know don't aspect each other.
        # If no such pair exists in this chart, skip — but document.
        ...

    def test_existing_aspect_returns_aspect(self):
        sun = self.chart.get(const.SUN)
        moon = self.chart.get(const.MOON)
        asp = aspects.getAspect(sun, moon, const.MAJOR_ASPECTS)
        # Whether an aspect exists between Sun and Moon for this date is
        # determined by the chart, but a returned Aspect must have a valid
        # `name` and `type`.
        if asp is not None:
            self.assertIsInstance(asp.name, str)
            self.assertIn(asp.type, const.ASPECT_NAMES)


class DeprecatedSentinelTests(unittest.TestCase):
    def test_getAspectOrSentinel_warns(self):
        """The deprecated sentinel-returning function emits warnings."""
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        chart = Chart(date, pos)
        sun = chart.get(const.SUN)
        moon = chart.get(const.MOON)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            asp = aspects.getAspectOrSentinel(sun, moon, const.MAJOR_ASPECTS)
            self.assertTrue(
                any(issubclass(x.category, DeprecationWarning) for x in w)
            )


if __name__ == "__main__":
    unittest.main()
```

Add `tests/test_object_lists.py`:

```python
"""Tests for the standard object lists added in Task 009."""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos


class ObjectListConstantsTests(unittest.TestCase):
    def test_modern_planets_has_ten(self):
        self.assertEqual(len(const.LIST_MODERN_PLANETS), 10)
        self.assertIn(const.SUN, const.LIST_MODERN_PLANETS)
        self.assertIn(const.PLUTO, const.LIST_MODERN_PLANETS)

    def test_lights_has_two(self):
        self.assertEqual(set(const.LIST_LIGHTS), {const.SUN, const.MOON})

    def test_personal_planets_excludes_outer(self):
        self.assertNotIn(const.URANUS, const.LIST_PERSONAL_PLANETS)
        self.assertNotIn(const.NEPTUNE, const.LIST_PERSONAL_PLANETS)
        self.assertNotIn(const.PLUTO, const.LIST_PERSONAL_PLANETS)

    def test_transpersonal_is_only_outer(self):
        self.assertEqual(
            set(const.LIST_TRANSPERSONAL),
            {const.URANUS, const.NEPTUNE, const.PLUTO},
        )

    def test_vedic_default_excludes_outer_planets(self):
        for planet in [const.URANUS, const.NEPTUNE, const.PLUTO]:
            self.assertNotIn(planet, const.LIST_VEDIC_DEFAULT)

    def test_vedic_default_includes_nodes(self):
        self.assertIn(const.NORTH_NODE, const.LIST_VEDIC_DEFAULT)
        self.assertIn(const.SOUTH_NODE, const.LIST_VEDIC_DEFAULT)

    def test_lists_are_lists_not_tuples(self):
        # So consumers can do LIST_MODERN_PLANETS + [extra_object]
        self.assertIsInstance(const.LIST_MODERN_PLANETS, list)
        self.assertIsInstance(const.LIST_TROPICAL_DEFAULT, list)

    def test_ASPECT_NAMES_dict_exists(self):
        self.assertIsInstance(const.ASPECT_NAMES, dict)
        self.assertGreater(len(const.ASPECT_NAMES), 4)


class ChartConstructionWithListsTests(unittest.TestCase):
    """Smoke test: building a Chart with each list doesn't crash."""

    def setUp(self):
        self.date = Datetime("2015/03/13", "17:00", "+00:00")
        self.pos = GeoPos("38n32", "8w54")

    def test_chart_with_modern_planets(self):
        chart = Chart(self.date, self.pos, IDs=const.LIST_MODERN_PLANETS)
        self.assertIsNotNone(chart.get(const.SUN))

    def test_chart_with_lights(self):
        chart = Chart(self.date, self.pos, IDs=const.LIST_LIGHTS)
        self.assertIsNotNone(chart.get(const.SUN))
        self.assertIsNotNone(chart.get(const.MOON))


if __name__ == "__main__":
    unittest.main()
```

The smoke tests for Chart construction with each list MAY fail if the library doesn't currently support computing some objects (e.g. Chiron may not be in the ephemeris call). If a test fails:

1. Mark it `@unittest.expectedFailure` with a clear reason
2. Document in PROJECT-LOG.md what's missing
3. Add a follow-up to IDEAS.md if it's worth adding object support

Don't fix the underlying ephemeris in this task. Object support is a separate concern.

## Update CHANGELOG.md

Under `[Unreleased]`:

```markdown
### Added
- `Aspect.name` — human-readable aspect name (e.g. "Trine", "Square")
- `const.ASPECT_NAMES` — mapping of aspect angle integers to names
- Standard object lists in `const`:
  - `LIST_MODERN_PLANETS` — Sun through Pluto
  - `LIST_TROPICAL_DEFAULT` — modern planets + nodes + Chiron
  - `LIST_VEDIC_DEFAULT` — seven planets + Rahu + Ketu
  - `LIST_LIGHTS`, `LIST_PERSONAL_PLANETS`, `LIST_SOCIAL_PLANETS`
  - `LIST_TRANSPERSONAL`, `LIST_LUNAR_NODES`
- Documentation page `docs/OBJECT-LISTS.md`
- `getAspect()` now returns `None` when no aspect exists (Pythonic)

### Changed
- [Document the asp.active / asp.passive change here once decided]

### Deprecated
- `getAspectOrSentinel()` (or the old `getAspect()` semantic) — use
  `getAspect()` which returns None. Will be removed in 1.0.
```

## Update IDEAS.md

If anything in this task surfaced a bigger conversation (object support gaps, AspectObject semantics worth revisiting, etc.), add it to IDEAS.md.

## Out of scope

- Adding new ephemeris support for objects not currently computable
- Changing how Chart() handles unknown object IDs
- Type hints on the new APIs (Phase 1 follow-up)
- Documentation site setup (Phase 1 follow-up)
- Vedic-specific computation (Phase 2)

## Process

1. Branch:

   ```
   git checkout development
   git pull origin development
   git checkout -b task-009-aspect-api-and-lists
   ```

2. Suggested commit structure:
   - `feat: add ASPECT_NAMES mapping to const`
   - `feat: add Aspect.name property`
   - `feat: preserve full Object reference on Aspect`
   - `feat: getAspect returns None instead of sentinel`
   - `refactor: deprecate sentinel-returning getAspect with rename`
   - `feat: add standard object lists to const`
   - `docs: add OBJECT-LISTS.md`
   - `test: cover aspect API improvements and standard lists`
   - `docs: update CHANGELOG and IDEAS for Task 009`

3. Pre-completion checklist:
   - `ruff format --check .` passes
   - `ruff check .` passes
   - `mypy mayaastrolib/` — no new errors
   - `pytest -x` passes — all tests including new ones
   - The deprecation warnings from this task appear in pytest output where the old API is still used

4. PROJECT-LOG.md entry must include:
   - The decision made about Aspect.active / Aspect.passive (kept as AspectObject vs replaced with full Object) and reasoning
   - Any object constants that were missing from `const.py` and how they were resolved
   - Any list-with-Chart smoke tests that had to be xfailed and why
   - The grep output showing internal getAspect call sites that were updated

5. Push:

   ```
   git push -u origin task-009-aspect-api-and-lists
   ```

6. Verify CI green.

7. DO NOT merge. Leave for human review.

## Definition of done

- `Aspect.name` works and returns expected strings
- `const.ASPECT_NAMES` dict is exposed
- Full Object reference is accessible from an Aspect (whether via `.active`/`.passive` or `.activeObj`/`.passiveObj`)
- `getAspect()` returns `None` for no-aspect case
- `getAspectOrSentinel()` (or equivalent) emits DeprecationWarning
- All eight new list constants exist in `const.py`
- `docs/OBJECT-LISTS.md` exists
- All existing tests still pass
- New tests in `test_aspect_api.py` and `test_object_lists.py` pass
- CHANGELOG updated
- CI green

## If something goes wrong

Most likely failure: an existing recipe or test depends on `asp.active` being an `AspectObject` and breaks when the type changes. If this happens:

1. Decide: is the dependency real (uses an AspectObject-specific attribute) or incidental (just type-checks)?
2. If real, keep AspectObject behaviour on `.active` and add the full Object on `.activeObj`. This is the safer path.
3. If incidental, fix the test/recipe.

Second most likely: a list constant references a planet ID that doesn't exist (e.g. `CHIRON` is not defined in `const.py`). Search before referencing:

```bash
grep -n "^CHIRON\|^URANUS\|^NEPTUNE\|^PLUTO\|^NORTH_NODE\|^SOUTH_NODE" mayaastrolib/const.py
```

If a constant is missing, either add it (if it's an oversight) or remove that planet from the list (if it's not actually supported in the library). Document either choice in PROJECT-LOG.md.

If something fundamental breaks:

1. `git reset --hard development`
2. Failure report in PROJECT-LOG.md
3. Commit on `task-009-failed-attempt-1`
4. Push and stop

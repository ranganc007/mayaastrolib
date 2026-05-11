# Task 008: Dignities Thread-Safety and Parameter API

## Context

You are working in the `mayaastrolib` repository. Before doing anything:

1. Read `CLAUDE.md` in full.
2. Read `mayaastrolib/dignities/essential.py` end to end. Pay particular attention to:
   - Module-level constants `FACES`, `TERMS`, `TABLE`, `SCORES`
   - The `setFaces()` and `setTerms()` functions and their `global` declarations
   - Every function that uses these globals (most of them)
3. Read `mayaastrolib/dignities/tables.py` for the available variants.
4. Read `docs/PROJECT-LOG.md` for recent task entries.
5. Confirm Tasks 006 and 007 are merged to `development`. Run `git log --oneline development -10` and verify.

## Why this task exists

`mayaastrolib/dignities/essential.py` has module-level mutable state:

```python
FACES = tables.CHALDEAN_FACES
TERMS = tables.EGYPTIAN_TERMS

def setFaces(variant):
    global FACES
    FACES = variant

def setTerms(variant):
    global TERMS
    TERMS = variant
```

Every function in the module reads from these globals. Calling `setTerms(LILLY_TERMS)` once changes the answer of every subsequent dignity calculation across the entire process. Two charts in the same process cannot use different terms variants. Two threads computing dignities simultaneously can corrupt each other's results.

The demo webapp runs on mod_wsgi with `threads=2`. The bug is dormant only because both threads happen to want the same variant. Any real multi-tenant use of the library (a web service serving multiple users with different dignity preferences) would hit this immediately.

This task fixes it by passing variants as parameters with sensible defaults. The module-level state remains for backwards compatibility but is deprecated.

## Design decision (already made — do not relitigate)

**Approach: parameters now, `DignityConfig` class later if Phase 2 demands it.**

Two configuration knobs (`terms_variant` and `faces_variant`) is not enough complexity to warrant a config object. Add them as keyword-only parameters with the existing module-level globals as defaults. When Vedic work in Phase 2 adds ayanamsa/dasha system/etc. and the parameter list balloons past 4-5, that's when we introduce a config object. Not before.

The `setFaces()` / `setTerms()` module-level mutators stay (deprecated) for backwards compatibility. Internal library code switches to passing parameters. External callers using the deprecated mutators get a `DeprecationWarning`.

## Task scope

### 1. Audit which functions need the parameters

Read `essential.py` and list every function that currently reads `FACES` or `TERMS`. Expected list (verify):

- `term(sign, lon)` — reads TERMS
- `face(sign, lon)` — reads FACES
- `setFaces(variant)`, `setTerms(variant)` — write the globals (deprecated)
- `getInfo(ID, sign, lon)` — calls `term()` and `face()`
- `score(ID, sign, lon)` — calls `getInfo()`
- `isPeregrine(ID, sign, lon)` — calls multiple lookups
- `almutem(sign, lon)` — uses dignity tables
- `EssentialInfo` class — likely calls `term()` and `face()` indirectly

Document the list in PROJECT-LOG.md under "audit findings".

### 2. Add keyword-only parameters to all affected functions

Convert each function. Pattern:

```python
# Before
def term(sign, lon):
    for term_data in TERMS[sign]:
        if term_data[1] >= lon:
            return term_data[0]

# After
def term(sign, lon, *, terms_variant=None):
    """Return the term lord for a given sign and longitude.

    Args:
        sign: Sign constant from const.LIST_SIGNS.
        lon: Longitude within the sign (0–30).
        terms_variant: One of EGYPTIAN_TERMS, TETRABIBLOS_TERMS, LILLY_TERMS
            from mayaastrolib.dignities.tables. Defaults to the value set by
            setTerms() (or EGYPTIAN_TERMS if never set), but passing this
            parameter is preferred and thread-safe.

    Returns:
        The term lord (a planet ID string).
    """
    if terms_variant is None:
        terms_variant = TERMS  # falls back to module-level (deprecated path)
    for term_data in terms_variant[sign]:
        if term_data[1] >= lon:
            return term_data[0]
```

Apply the same pattern to all functions that need `terms_variant` or `faces_variant`. For functions that need both, both go in the signature.

The `*,` (keyword-only marker) is non-negotiable. When this becomes a `DignityConfig` object in Phase 2, callers using `terms_variant=X` keep working; callers using positional arguments would break.

### 3. Add the `score(obj)` overload for ergonomics

Per the audit, every caller of `score()` writes `score(p.id, p.sign, p.signlon)`. Add an overload that takes an Object directly:

```python
def score(obj_or_id, sign=None, lon=None, *, terms_variant=None, faces_variant=None):
    """Compute the essential dignity score.

    Two call styles:
        score(planet_object)            # preferred
        score(id, sign, lon)            # legacy

    The first form is more convenient when you have an Object. The second
    is supported for backwards compatibility.

    Args:
        obj_or_id: Either an Object instance, or a planet ID string.
        sign: Required if obj_or_id is a string. Sign constant.
        lon: Required if obj_or_id is a string. Longitude within sign.
        terms_variant: See `term()`.
        faces_variant: See `face()`.

    Returns:
        Integer score in [-10, +5].

    Raises:
        TypeError: if obj_or_id is a string but sign/lon are missing.
    """
    # Detect call style
    if hasattr(obj_or_id, 'id') and hasattr(obj_or_id, 'sign') and hasattr(obj_or_id, 'signlon'):
        # Object-style call
        ID = obj_or_id.id
        sign = obj_or_id.sign
        lon = obj_or_id.signlon
    else:
        # Legacy 3-arg call
        ID = obj_or_id
        if sign is None or lon is None:
            raise TypeError(
                "score(id, sign, lon) requires all three arguments. "
                "For convenience, score(obj) accepts an Object directly."
            )

    # ... existing logic, threading the variants through ...
```

Apply the same overload pattern to other dignity functions where it makes sense:
- `getInfo(ID, sign, lon)` → also accepts `getInfo(obj)`
- `isPeregrine(ID, sign, lon)` → also accepts `isPeregrine(obj)`

For functions where the obj-style call doesn't add value (e.g. `term(sign, lon)` doesn't need an object, just a position), don't force it.

### 4. Deprecate the module-level setters

Modify `setFaces()` and `setTerms()`:

```python
def setFaces(variant):
    """[DEPRECATED] Set the global faces variant.

    Module-level state is not thread-safe. Pass `faces_variant=...`
    to dignity functions instead. This function will be removed in
    version 1.0.
    """
    import warnings
    warnings.warn(
        "setFaces() mutates global state and is not thread-safe. "
        "Pass faces_variant=... to dignity functions instead. "
        "setFaces() will be removed in version 1.0.",
        DeprecationWarning,
        stacklevel=2,
    )
    global FACES
    FACES = variant
```

Same for `setTerms()`. Don't remove them — that breaks compatibility. Just warn.

### 5. Update internal call sites

Search for everywhere in `mayaastrolib/` that calls a dignity function with the old signature:

```bash
grep -rn "essential\." mayaastrolib/
grep -rn "from .* import .* essential" mayaastrolib/
```

Update each call site to either:
- Pass `terms_variant` / `faces_variant` explicitly if a specific variant is intended
- Use the new `score(obj)` style if the call has an Object handy

Internal library code should NOT call the deprecated `setFaces()` or `setTerms()`. If any internal code does, that's a bug to fix in this task.

### 6. Thread-safety test

Add `tests/test_dignities_thread_safety.py`:

```python
"""Verify dignity calculations are thread-safe when variants are passed
as parameters.

Regression test for the global-state bug fixed in Task 008.
"""

import threading
import unittest

from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib import const
from mayaastrolib.dignities import essential
from mayaastrolib.dignities.tables import (
    EGYPTIAN_TERMS,
    TETRABIBLOS_TERMS,
    LILLY_TERMS,
)


class DignityThreadSafetyTests(unittest.TestCase):

    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)
        self.sun = self.chart.get(const.SUN)

    def test_different_threads_different_variants(self):
        """Each thread uses a different terms variant simultaneously.
        
        Without the parameter API, this would corrupt results because
        all threads share the module-level TERMS global.
        """
        results = {}
        errors = []

        def compute_with_variant(variant_name, variant_value):
            try:
                # Run many iterations to maximize chance of interleaving
                scores = []
                for _ in range(100):
                    s = essential.score(self.sun, terms_variant=variant_value)
                    scores.append(s)
                # All scores in this thread should be identical
                results[variant_name] = scores
            except Exception as e:
                errors.append((variant_name, e))

        threads = [
            threading.Thread(
                target=compute_with_variant,
                args=("egyptian", EGYPTIAN_TERMS),
            ),
            threading.Thread(
                target=compute_with_variant,
                args=("tetrabiblos", TETRABIBLOS_TERMS),
            ),
            threading.Thread(
                target=compute_with_variant,
                args=("lilly", LILLY_TERMS),
            ),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])
        # Each thread's scores should be internally consistent
        for variant_name, scores in results.items():
            self.assertEqual(
                len(set(scores)),
                1,
                f"Thread '{variant_name}' got inconsistent results: "
                f"{set(scores)}",
            )


class ScoreOverloadTests(unittest.TestCase):

    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)
        self.sun = self.chart.get(const.SUN)

    def test_object_call_equals_legacy_call(self):
        """score(obj) == score(obj.id, obj.sign, obj.signlon)"""
        new_style = essential.score(self.sun)
        legacy = essential.score(self.sun.id, self.sun.sign, self.sun.signlon)
        self.assertEqual(new_style, legacy)

    def test_legacy_call_with_missing_args_raises(self):
        with self.assertRaises(TypeError):
            essential.score(const.SUN)  # missing sign, lon


class DeprecatedSettersTests(unittest.TestCase):

    def test_setFaces_emits_warning(self):
        import warnings
        from mayaastrolib.dignities.tables import TRIPLICITY_FACES
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            essential.setFaces(TRIPLICITY_FACES)
            self.assertTrue(
                any(issubclass(warning.category, DeprecationWarning)
                    for warning in w),
                "setFaces() should emit DeprecationWarning",
            )


if __name__ == "__main__":
    unittest.main()
```

### 7. Update CHANGELOG.md

Under `[Unreleased]`:

```markdown
### Added
- `terms_variant` and `faces_variant` keyword parameters on `dignities.essential` functions for thread-safe variant selection
- `score(obj)`, `getInfo(obj)`, `isPeregrine(obj)` overloads accepting Object instances directly

### Deprecated
- `dignities.essential.setFaces()` and `setTerms()`. Module-level mutable state is not thread-safe. Use the new keyword parameters instead. These setters will be removed in version 1.0.

### Fixed
- Dignity calculations are now thread-safe when variants are passed as parameters. Previously, two threads computing with different terms variants could corrupt each other's results via shared module-level state.
```

## Out of scope

- Adding more dignity systems (Vedic dignities, KP system, etc.) — Phase 2
- Building a `DignityConfig` class — defer until parameter list grows
- Renaming the module-level constants — out of scope
- The `accidental.py` module — has different patterns, separate task if needed

## Process

1. Branch:

   ```
   git checkout development
   git pull origin development
   git checkout -b task-008-dignities-thread-safety
   ```

2. Commits:
   - `refactor: add terms_variant/faces_variant params to dignities.essential`
   - `feat: add score(obj) overload accepting Object instances`
   - `feat: add getInfo(obj) and isPeregrine(obj) overloads`
   - `refactor: deprecate setFaces and setTerms with DeprecationWarning`
   - `refactor: update internal call sites to use parameter API`
   - `test: add thread-safety and overload tests for dignities`
   - `docs: update CHANGELOG for Task 008`

3. Pre-completion checklist:
   - `ruff format --check .` passes
   - `ruff check .` passes
   - `mypy mayaastrolib/` — no new errors
   - `pytest -x` passes — including the thread-safety test
   - Run the thread-safety test 5 times in a row — should pass every time

4. PROJECT-LOG.md entry must include:
   - The full audit list of functions modified
   - Any function where the overload pattern didn't fit (and why)
   - Output of running the thread-safety test 5 times (should be "5/5 passed")

5. Push:

   ```
   git push -u origin task-008-dignities-thread-safety
   ```

6. Verify CI green.

7. DO NOT merge. Leave for human review.

## Definition of done

- Every function in `dignities/essential.py` that reads `FACES` or `TERMS` accepts `*, terms_variant=None` and/or `*, faces_variant=None`
- `score(obj)`, `getInfo(obj)`, `isPeregrine(obj)` overloads work
- `setFaces()` and `setTerms()` emit DeprecationWarning but still function
- Thread-safety test passes 5 times in a row
- All existing tests still pass
- CHANGELOG updated
- CI green

## If something goes wrong

The most likely failure mode: the parameter migration breaks an internal call site that wasn't found by grep. The full test suite from Tasks 004a and 006 should catch most of these.

If a test fails after the migration:

1. Read the failing test carefully — does it expect the old or new behaviour?
2. Check whether the failure is in user code (test) or library code (call site missed in step 5)
3. Fix the call site, not the test

If the thread-safety test is flaky (passes sometimes, fails sometimes):

1. That's a real bug in the implementation — global state is leaking somewhere
2. Run the test in a tight loop to reproduce reliably
3. Find the leak (likely a function that doesn't honour the parameter and falls back to globals)

If the `score(obj)` detection logic has edge cases (e.g. someone passes a string that happens to have an `.id` attribute via some other mechanism):

1. Tighten the detection — check for all three attributes (`id`, `sign`, `signlon`)
2. If still ambiguous, document the rule in the docstring and trust the user

If you can't complete in reasonable time:

1. `git reset --hard development`
2. Detailed failure report in PROJECT-LOG.md
3. Commit on `task-008-failed-attempt-1`
4. Push and stop

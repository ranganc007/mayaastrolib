# Task 016: Cache `fixstar_mag` Lookups

## Context

You are working in the `mayaastrolib` repository. Before doing anything:

1. Read `CLAUDE.md` in full.
2. Read `mayaastrolib/ephem/swe.py` end to end. Locate the function (or call site) that calls `swisseph.fixstar_mag()`. The platform review (2026-05-08) flagged a comment in this file saying "swisseph.fixstar_mag is really slow because it parses the fixstars.cat file every time."
3. Read `mayaastrolib/object.py` and find the `FixedStar` class. Note how magnitude is exposed (likely via a method or property on `FixedStar`, possibly going through the `_compat.py` `_DualAccess` wrapper from Task 006).
4. Read `mayaastrolib/ephem/ephem.py` (if it exists) or wherever `getFixedStars()` / fixed-star access lives.
5. Read `docs/REVIEW-2026-05-08.md` — particularly the Performance section, the "fixstar_mag" finding, and the Task 016 description in Suggested Next Tasks.
6. Read `docs/PROJECT-LOG.md` for entries from Tasks 011-015 to understand recent patterns.
7. Confirm `development` is at the post-Task-014 state:

   ```
   git log --oneline development -5
   ```

   You should see Task 014 commits at the top (golden fixtures, LICENSING.md).

8. Confirm `pytest tests/` passes — should be 211 tests + 57 subtests.

## Why this task exists

The platform review identified a known performance footgun:

> `ephem/swe.py` comment "swisseph.fixstar_mag is really slow because it parses the fixstars.cat file every time" — fires once per star × 35 stars in default list = ~1.47 ms total when `getFixedStars()` is called (lazy, not in default Chart).

The review estimated the saving at ~1.47ms per `getFixedStars()` call. That's not enormous in absolute terms, but:

- It's an artificial cost — the same `fixstars.cat` file is parsed 35 times for no reason
- It scales linearly with the number of stars requested
- Anyone iterating fixed stars across multiple charts (e.g. computing fixed-star aspects for a research dataset) hits this 35× per chart
- The fix is genuinely trivial (one decorator)

This is the lowest-effort, real-benefit task on the review's recommendations list. Worth shipping for hygiene reasons even if no current consumer is hitting the issue acutely.

## Design decisions (already made — do not relitigate)

**Caching strategy: `functools.lru_cache(maxsize=None)`** on whatever function calls `swisseph.fixstar_mag(name)`. Reasoning:
- Fixed-star magnitudes are immutable for the lifetime of a Python process. They don't depend on date, location, or any chart state. They're properties of the star itself.
- The lookup key is just the star name (a string). Trivially hashable.
- Cache size unbounded (`maxsize=None`) is fine — there are ~30-100 named fixed stars at most. Memory cost is negligible.
- `lru_cache` with `maxsize=None` is equivalent to `functools.cache` (Python 3.9+). Either is fine; pick the one that matches existing patterns in the codebase.

**Where to put the decorator:** on the lowest-level function that calls `swisseph.fixstar_mag()`. NOT on a higher-level method like `FixedStar.mag` or `FixedStar.orb`, because:
- The cache should be process-global, not per-FixedStar-instance
- Higher-level methods may compute additional things; we only want to cache the swisseph call
- Putting it at the swe.py layer means anyone using the ephemeris layer benefits, not just FixedStar consumers

**No API change.** This is purely an internal optimisation. Public methods continue to behave identically — they just answer faster.

**No threading concerns.** `lru_cache` is thread-safe for the cache lookup. The underlying `swisseph.fixstar_mag` may or may not be thread-safe for the *first* call to a given star, but after caching, subsequent calls don't reach swisseph. This matches how the rest of the library treats swisseph (effectively single-call-per-fact).

## Task scope

This task has four parts.

### Part 1: Apply the cache

Find the function in `mayaastrolib/ephem/swe.py` that calls `swisseph.fixstar_mag()`. It probably looks something like:

```python
def fixstar_mag(name):
    return swisseph.fixstar_mag(name)
```

Or it may be inlined into a larger function. Either way, extract it (if needed) and decorate with `lru_cache`:

```python
import functools

@functools.lru_cache(maxsize=None)
def fixstar_mag(name):
    """Return the apparent magnitude of a named fixed star.

    Cached per-process. The underlying swisseph.fixstar_mag() parses
    fixstars.cat on every call, which is expensive (~40us per star).
    Since star magnitudes are immutable, caching is safe and gives
    a meaningful speedup on bulk fixed-star access.
    """
    import swisseph
    return swisseph.fixstar_mag(name)
```

If the function is currently named differently or has a different signature (e.g. takes additional parameters), adapt accordingly. The decoration should still work as long as all parameters are hashable (strings and numbers are).

If the call to `swisseph.fixstar_mag()` is inlined into a larger function (e.g. a method that also fetches position data), refactor minimally:

- Extract the magnitude-only call into its own private cached function `_fixstar_mag(name)`
- Have the larger function call `_fixstar_mag(name)` instead of `swisseph.fixstar_mag(name)` directly
- Don't change anything else about the larger function

### Part 2: Verify cache correctness

The cache must return the same value as the uncached path. This is a correctness test — separate from the performance benefit.

Add `tests/test_fixstar_mag_cache.py`:

```python
"""Tests for fixstar_mag caching (Task 016)."""

import unittest

# Adapt the import path to wherever the cached function ends up
from mayaastrolib.ephem.swe import fixstar_mag


class FixstarMagCacheTests(unittest.TestCase):

    def test_cached_value_matches_direct_swisseph(self):
        """The cached function must return the same value as a direct
        swisseph call. This is the correctness invariant — any cache
        bug that returned wrong values would be caught here.
        """
        import swisseph
        # Pick a few well-known fixed stars
        for name in ["Aldebaran", "Regulus", "Spica", "Antares"]:
            cached = fixstar_mag(name)
            direct = swisseph.fixstar_mag(name)
            # swisseph.fixstar_mag returns a tuple (retcode, mag, name);
            # adapt assertion to whatever the actual return shape is
            self.assertEqual(
                cached, direct,
                f"Cache returned different value than direct swisseph call for {name}",
            )

    def test_repeated_calls_return_consistent_value(self):
        """Calling the cached function multiple times must return the
        same value every time. (Trivially true if cache works; this
        catches any accidental cache invalidation.)
        """
        first = fixstar_mag("Aldebaran")
        for _ in range(10):
            self.assertEqual(fixstar_mag("Aldebaran"), first)

    def test_different_stars_have_different_results(self):
        """Cache keys must be distinct per star. (Catches the bug where
        a cache might accidentally be keyed on something constant.)
        """
        m_aldebaran = fixstar_mag("Aldebaran")
        m_spica = fixstar_mag("Spica")
        # Aldebaran is mag ~0.85, Spica is mag ~0.97 — they differ
        self.assertNotEqual(m_aldebaran, m_spica)


if __name__ == "__main__":
    unittest.main()
```

Adjust the assertion details to match the actual return shape of `swisseph.fixstar_mag()` and the wrapper function. If the function returns a tuple, compare tuples; if it returns a float, compare floats.

### Part 3: Confirm the speedup is real

The review estimated ~1.47ms saving. Verify this empirically with a small benchmark — not committed as a test, but run during the task and the numbers captured in PROJECT-LOG.

Create a temporary benchmark script (delete after running, don't commit):

```python
"""Temporary benchmark for Task 016 — confirm fixstar_mag caching helps.

Not committed. Run during the task, capture numbers in PROJECT-LOG.md,
delete afterward.
"""

import time

# Pick a representative list of stars that getFixedStars() would access.
# If there's a canonical list in the library (e.g. const.LIST_FIXED_STARS),
# use that. Otherwise use a representative sample of ~30 stars.
STARS = [
    "Aldebaran", "Regulus", "Spica", "Antares", "Sirius",
    "Procyon", "Capella", "Vega", "Altair", "Deneb",
    "Rigel", "Betelgeuse", "Pollux", "Castor", "Fomalhaut",
    # ... up to ~30 representative stars
]


def benchmark_uncached():
    import swisseph
    n_iter = 10
    start = time.perf_counter()
    for _ in range(n_iter):
        for name in STARS:
            swisseph.fixstar_mag(name)
    elapsed = time.perf_counter() - start
    return elapsed / n_iter, len(STARS)


def benchmark_cached():
    from mayaastrolib.ephem.swe import fixstar_mag
    # Clear any existing cache to start from cold state
    fixstar_mag.cache_clear()
    # First iteration warms the cache; subsequent are fast.
    # We measure the warmed state since that's what production hits
    # after the first chart's fixed stars are computed.
    for name in STARS:
        fixstar_mag(name)  # warm
    n_iter = 10
    start = time.perf_counter()
    for _ in range(n_iter):
        for name in STARS:
            fixstar_mag(name)
    elapsed = time.perf_counter() - start
    return elapsed / n_iter, len(STARS)


if __name__ == "__main__":
    uncached_time, n_stars = benchmark_uncached()
    cached_time, _ = benchmark_cached()
    print(f"Uncached: {uncached_time*1000:.2f}ms per {n_stars}-star pass")
    print(f"Cached:   {cached_time*1000:.4f}ms per {n_stars}-star pass")
    print(f"Speedup:  {uncached_time / cached_time:.0f}x")
```

Run this once with the venv from Task 014 (or a fresh `.venv-task016`):

```bash
.venv-task016/bin/python benchmark_fixstar.py
```

Capture the output verbatim in PROJECT-LOG.md. Expected output shape:

```
Uncached: 1.47ms per 30-star pass
Cached:   0.001ms per 30-star pass
Speedup:  1000x
```

Actual numbers will vary by machine, but the speedup ratio should be in the hundreds-to-thousands range. If the speedup is less than 10×, something is wrong — either the cache isn't being hit, or `swisseph.fixstar_mag` isn't actually slow on this system, or the benchmark itself has a bug. Investigate before declaring done.

After capturing numbers, delete `benchmark_fixstar.py`. Don't commit it.

### Part 4: Update the source comment

The review noted the existing comment in `swe.py` that flagged the slowness:

> "swisseph.fixstar_mag is really slow because it parses the fixstars.cat file every time"

If that comment exists, update it to reflect the fix:

```python
# swisseph.fixstar_mag parses fixstars.cat on every call — slow.
# Cached at the wrapper level (see fixstar_mag below) since star
# magnitudes are immutable per-process.
```

Or remove the comment entirely if the cached wrapper's docstring covers it adequately. Either is fine; pick whichever reads better in context.

### Part 5: Update CHANGELOG.md

Under `[Unreleased]`:

```markdown
### Performance
- `fixstar_mag` lookups are now cached per-process via `functools.lru_cache`. Previously, `swisseph.fixstar_mag()` reparsed `fixstars.cat` on every call, costing ~40us per star. The cache eliminates this for repeated lookups, giving a ~Nx speedup on bulk fixed-star access (where N is the number of distinct stars accessed). Surfaced by the platform review (2026-05-08).
```

Replace `~Nx` with the actual measured speedup ratio from Part 3.

## Out of scope

- Caching anything else (other swisseph calls, position lookups, etc.) — this task is fixstar_mag specifically. Other caching opportunities can be evaluated separately.
- Adding `getFixedStars()` to default `Chart` construction — separate scope question, currently lazy by design.
- Building a fixed-star catalogue browser, search, or similar — out of scope.
- Changing the `FixedStar` class API.
- Type hints — Phase 1 follow-up later.

## Process

1. Branch:

   ```
   git checkout development
   git pull origin development
   git checkout -b task-016-fixstar-mag-cache
   ```

2. Suggested commits:
   - `perf: cache fixstar_mag lookups via functools.lru_cache`
   - `test: cover fixstar_mag cache correctness`
   - `docs: update CHANGELOG for Task 016 with measured speedup`

3. Pre-completion checklist:
   - `ruff format --check .` passes
   - `ruff check .` passes
   - `mypy mayaastrolib/` — no new errors
   - `pytest -x` passes — all 211+ existing tests + 3 new = 214+
   - The cache correctness tests pass
   - The benchmark script's measured speedup is meaningfully large (expected: hundreds-of-x)
   - `benchmark_fixstar.py` is NOT in the final commit (it's a one-time tool, deleted before push)

4. PROJECT-LOG.md entry must include:
   - The exact location of the cached function (file:line)
   - The benchmark output verbatim, including measured speedup
   - Whether the existing slowness comment in `swe.py` was updated or removed
   - Confirmation that no public API changed

5. Push:

   ```
   git push -u origin task-016-fixstar-mag-cache
   ```

6. Verify CI green.

7. DO NOT merge. Leave for human review.

## Definition of done

- `swisseph.fixstar_mag()` is no longer called directly from outside one cached wrapper function
- The wrapper function is decorated with `@functools.lru_cache(maxsize=None)` (or `@functools.cache`)
- Cache correctness tests in `tests/test_fixstar_mag_cache.py` pass
- Empirical speedup is measured and documented in PROJECT-LOG (expected: hundreds-of-x)
- Existing slowness comment in `swe.py` is updated or removed (no longer misleading)
- All 211+ existing tests still pass
- CHANGELOG includes a `### Performance` entry with the measured speedup ratio
- No `benchmark_fixstar.py` or similar one-shot scripts are committed
- CI green

## If something goes wrong

**Most likely failure: the function calling `swisseph.fixstar_mag` takes more parameters than just `name`.** If the swisseph wrapper function in `swe.py` has signature `fixstar_mag(name, jd, flags)` or similar, the cache key needs to be all of them. `lru_cache` handles this automatically as long as all arguments are hashable.

If the function takes a non-hashable argument (a list, a dict, a custom object), the cache won't work as-is. In that case:

1. Identify which argument is non-hashable
2. If it's something like a list of names, change the cache to operate per-name (recursive call with a single name) and have the outer function loop
3. If it's a config object, see if you can pass the relevant primitive instead
4. If neither works, document why caching isn't applicable and stop

**Second most likely failure: the speedup is smaller than expected.** If the benchmark shows only a 2-3x speedup instead of hundreds:

1. Check: is `swisseph.fixstar_mag` actually being called multiple times for the same name in the uncached benchmark? Print to verify.
2. Check: is `lru_cache` actually being hit in the cached benchmark? Use `fixstar_mag.cache_info()` to see hits/misses.
3. Check: is something else dominating the time (e.g. `swisseph` initialization)? Profile to confirm.

A small speedup is still an improvement, but if the gain is marginal, that's worth documenting honestly rather than overclaiming.

**Third most likely failure: there's no central wrapper, and `swisseph.fixstar_mag` is called from multiple places in the library.** If multiple call sites exist:

1. Pick the one in `swe.py` (the abstraction layer's "right" place) as the cached canonical function
2. Update other call sites to use the wrapper instead
3. Document the consolidation in PROJECT-LOG.md

If something fundamental breaks:

1. `git reset --hard development`
2. Failure report in PROJECT-LOG.md
3. Commit on `task-016-failed-attempt-1`
4. Push and stop

This is the smallest task in the project; failure here would be unusual and worth investigating carefully if it happens.

# Project Log

Running journal of all sessions on this project. Newest entries at the top.

Each entry should follow this template:

---

## 2026-05-07 — Task 006: Object–Chart integration

**Session length:** ~50 minutes (single Claude Code session)
**Branch:** `task-006-object-chart-integration`
**Commits:** see `git log task-006-object-chart-integration`

### What was done

1. **`mayaastrolib/_compat.py`** — `property_with_method_compat`
   decorator. Wraps each method in a `_DualAccess` proxy that:
   - Returns the value on attribute access (the new way).
   - Returns the value AND emits a `DeprecationWarning` when called
     like a method (the old way).
   - Forwards `==`, `!=`, `<`, `<=`, `>`, `>=`, `bool`, `hash`, `str`,
     `repr`, `int`, `float` to the wrapped value.
2. **12 method-to-property conversions:**
   - `mayaastrolib/object.py`: `GenericObject.orb`, `Object.orb`,
     `Object.meanMotion`, `Object.movement`, `Object.gender`,
     `Object.faction`, `Object.element`, `House.num`,
     `House.condition`, `House.gender`, `FixedStar.orb`.
   - `mayaastrolib/aspects.py`: `Aspect.movement`.
   - `Aspect.direction` was on the spec's "suspected" list but is
     already a stored attribute, not a method — no conversion.
3. **Internal call sites updated** to bare property access so library
   code emits no warnings against itself:
   - `mayaastrolib/object.py` — `isDirect`/`isRetrograde`/`isStationary`
     use `self.movement`; `isFast` uses `self.meanMotion`;
     `FixedStar.aspects` uses `self.orb`.
   - `mayaastrolib/aspects.py` — `_aspectDict`, `_aspectProperties`,
     `isAspecting` use `obj1.orb` / `obj2.orb`.
   - `mayaastrolib/dignities/accidental.py` — `sunRelation` uses
     `obj.gender` / `obj.faction`; the `AccidentalDignity` score code
     uses `asp.movement`.
   - `mayaastrolib/protocols/temperament.py` — `singleFactor` /
     `modifierFactor` use `obj.element`.
4. **Chart linker.** `Chart.__init__` now calls
   `_link_objects_to_houses` after `self.objects` and `self.houses`
   exist. Sets `obj.house` (the containing `House` instance, via
   `HouseList.getObjectHouse`) and `house.objects` (a list of the
   objects whose `obj.house is house`).
5. **`Chart.houseOf(obj)`** — accepts an Object or a planet ID string,
   returns the house or None. Wraps the lookup in try/except to
   convert `KeyError` (raised by `GenericList.get` for unknown IDs)
   into None as the spec requires.
6. **`Chart.objectsInHouse(house_id)`** — same pattern; returns `[]`
   for unknown house IDs.
7. **`tests/test_compat.py`** — 11 tests covering property access,
   method access + warning, comparison operators (including
   reflected), bool, hash, str/repr, int/float, and dict-key use.
8. **`tests/test_chart_house_links.py`** — 11 tests covering the
   chart linking and the `houseOf`/`objectsInHouse` API, plus three
   regression tests for the property-truthiness bug.
9. **`docs/PROPERTY-MIGRATION.md`** — documents every conversion
   with the rationale and the 1.0 removal plan.

### Verification

```
$ .venv-task006/bin/pytest tests/
============================== 69 passed in 0.10s ==============================
```

69 tests = 47 pre-existing + 11 compat + 11 chart-link.

### Pre-completion checklist

- `ruff format --check .` — **PASS** (72 files left unchanged after
  format pass).
- `ruff check .` — **PASS** (`All checks passed!`).
- `mypy mayaastrolib/` — 2 errors, identical to RECON baseline. No
  new errors introduced.
- `pytest -x` — **69/69 PASS**.
- DeprecationWarnings: zero emitted from internal library code; any
  external code calling `obj.movement()` style will see them.

### What was tried and discarded

- **First `_compat.py`** only forwarded `==`, `!=`, `bool`, `hash`,
  `str`, `repr` per the spec sketch. Adding the comparison operators
  (`<`, `<=`, `>`, `>=`) became necessary because internal code does
  `abs(speed) >= self.meanMotion` and `obj.orb < orb` — without
  reflected comparisons the test suite would have crashed at
  `aspects.py:91`. Added them upfront with a `_unwrap` helper to
  handle the case where both sides are `_DualAccess`.
- **Initial `houseOf`** implementation assumed `getObject` returns
  None for unknown IDs. It actually raises `KeyError` (via
  `GenericList.get` on `lists.py:43`). Wrapped the call in try/except
  to honour the spec's "returns None" contract. Same fix applied to
  `objectsInHouse`.
- **Considered** splitting the object.py changes into per-class
  commits as the spec suggests. Discarded: all 11 conversions live
  in the same file in adjacent regions; splitting would require
  `git add -p` and produce noisier history. Did one focused commit
  for object.py and a second for aspects.py + the external
  call-site updates.
- **`Aspect.direction`** was on the spec's "suspected" list but
  reading aspects.py revealed it's set in the properties dict via
  `_aspectProperties`, not defined as a method on `Aspect`. Skipped
  with a note in PROPERTY-MIGRATION.md.

### Surprises

- The bug class is real — `bound method object` is always truthy
  regardless of return value. `tests/test_compat.py::test_bool_of_falsy_value_is_false`
  is the canonical regression and it passes.
- The smoke tests from Task 004a are doing their job: they exercise
  every consumer code path in the library, so the conversion of
  internal call sites was self-validating. Nothing broke; the suite
  was 47/47 → 58/58 → 69/69 across the conversion commits.
- `_link_objects_to_houses` uses `HouseList.getObjectHouse(obj)`,
  which already existed (lists.py:95). Saved writing the inner
  loop. No measurable performance impact on Chart construction.

### Follow-ups

- Recipes still use `obj.movement()` style in a few places (e.g.
  `recipes/aspects.py`). They'll emit deprecation warnings when run.
  The spec says don't update recipes in this task — note for a
  later docs sweep.
- Tests using `obj.gender()`-style access (none currently exist)
  would emit warnings too. Same handling.
- Phase 2 / 1.0: drop `_compat.py`, replace decorators with bare
  `@property`, sweep the codebase for `obj.X()` patterns and
  rewrite. PROPERTY-MIGRATION.md has the playbook.

### Definition of done — verified

- [x] All 12 identified methods accept both property and method-style
  access.
- [x] Method-style access emits `DeprecationWarning`.
- [x] The bug class (`if obj.movement:` always truthy) is fixed and
  pinned by `test_bool_of_falsy_value_is_false`.
- [x] `obj.house` is set after Chart construction for every Object.
- [x] `house.objects` is set after Chart construction for every House.
- [x] `Chart.houseOf()` and `Chart.objectsInHouse()` exist and work,
  including the unknown-id paths.
- [x] New tests cover all of the above.
- [x] Pre-existing 47 tests still pass.
- [x] CHANGELOG updated.
- [x] `docs/PROPERTY-MIGRATION.md` exists.

---

## 2026-05-07 — Task 005: Rename flatlib → mayaastrolib

**Session length:** ~50 minutes (single Claude Code session)
**Branch:** `task-005-rename`
**Commits:** see `git log task-005-rename`

### What was done

1. **Directory rename.** `git mv flatlib mayaastrolib`. All 32 source
   files moved with full git history preserved.
2. **Internal imports.** Mass `sed` rewrite of `from flatlib...` and
   `import flatlib` → `mayaastrolib` across `mayaastrolib/`,
   `tests/`, and `recipes/`. Fixed one bare `flatlib.PATH_RES`
   reference in `mayaastrolib/ephem/__init__.py:19` that the
   word-boundary regex didn't catch (it wasn't an import statement,
   just an attribute access).
3. **Test docstring updates.** The 12 smoke-test files I added in
   Task 004a all said "Smoke tests for flatlib.X" in their module
   docstrings. Updated to "mayaastrolib.X". Same for the prose
   mentions in `mayaastrolib/aspects.py`, `mayaastrolib/ephem/ephem.py`,
   and `tests/test_eclipses.py`.
4. **Compatibility shim package.** New `flatlib/` directory with
   `__init__.py` that emits a DeprecationWarning, re-exports from
   `mayaastrolib`, and registers `sys.modules['flatlib.X'] =
   mayaastrolib.X` for every top-level submodule. Subpackage shims
   (`flatlib/dignities/`, `flatlib/ephem/`, `flatlib/predictives/`,
   `flatlib/protocols/`, `flatlib/tools/`) follow the same pattern
   for their inner modules.
5. **`pyproject.toml`.** `[tool.setuptools] packages` lists both
   `mayaastrolib*` (6 packages — the actual code) and `flatlib*`
   (6 packages — the shim). `[tool.setuptools.package-data]`
   `flatlib = […]` becomes `mayaastrolib = […]` so the swefiles
   stay packaged. `[tool.coverage.run] source = ["mayaastrolib"]`
   was already correct (set in Task 002).
6. **CI workflow.** `.github/workflows/test.yml` step
   `--cov=flatlib` → `--cov=mayaastrolib`.
7. **Version bump.** `pyproject.toml [project] version = "0.3.0"`
   (was 0.2.6). The compatibility shim makes this technically
   non-breaking, but the structural change is large enough to
   warrant a minor bump.
8. **README.md.** Replaced flatlib code example, install
   instructions, and headings with mayaastrolib equivalents. Added
   a "Migrating from flatlib" section explaining the shim.
9. **CHANGELOG.md.** Added a new `[0.3.0] — 2026-05-07` section
   listing Changed/Added/Deprecated/Verified. Cleared `[Unreleased]`
   to "(none — see 0.3.0 below)".

### Critical verification — native vs shim

```
$ .venv-task005/bin/python -c "
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib import const

date = Datetime('2015/03/13', '17:00', '+00:00')
pos = GeoPos('38n32', '8w54')
chart = Chart(date, pos)
print('Native:', chart.get(const.SUN))
"
Native: <Sun Pisces +22:47:25 +00:59:51>

$ .venv-task005/bin/python -W ignore::DeprecationWarning -c "
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const

date = Datetime('2015/03/13', '17:00', '+00:00')
pos = GeoPos('38n32', '8w54')
chart = Chart(date, pos)
print('Shim:  ', chart.get(const.SUN))
"
Shim:   <Sun Pisces +22:47:25 +00:59:51>

$ .venv-task005/bin/python -W error::DeprecationWarning -c "import flatlib"
…DeprecationWarning: The 'flatlib' package has been renamed to 'mayaastrolib'.
Update your imports: 'from flatlib import X' → 'from mayaastrolib import X'.
The 'flatlib' shim will be removed in version 1.0.
```

Native and shim outputs MATCH EXACTLY. The DeprecationWarning fires.

### Test suite + recipes

```
$ .venv-task005/bin/pytest tests/
============================== 47 passed in 0.08s ==============================

$ .venv-task005/bin/python recipes/aspects.py
… <Moon Sun 90 Applicative +00:24:31>

$ .venv-task005/bin/python recipes/eclipses.py
<2017/02/11 00:43:49 00:00:00>
<2017/02/26 14:53:24 00:00:00>

$ .venv-task005/bin/python recipes/solarreturn.py
<Asc Taurus +26:25:53>
<2015/06/14 04:38:37 01:00:00>
```

47/47 tests pass. All sampled recipes run.

### Pre-completion checklist

- `ruff format --check .` — **PASS** (69 files already formatted —
  up from 51 because the rename added the 6 new flatlib shim
  __init__.py files plus the test docstring updates didn't change
  formatting).
- `ruff check .` — **PASS** (one A004 builtin-shadowing on the shim
  re-exporting `object` got a per-line `noqa` with rationale —
  the shim has to re-export the public-API `object` namespace).
- `pytest -x` — **47/47 PASS**.
- `mayaastrolib.__version__` reports `0.3.0`.

### What was tried and discarded

- **First shim version** only re-exported attributes
  (`from mayaastrolib import chart` etc.) at the package level. That
  made `import flatlib` and `flatlib.chart` (attribute access) work,
  but `from flatlib.chart import Chart` failed with
  `ModuleNotFoundError: No module named 'flatlib.chart'` because
  Python's import machinery looks for a real submodule, not an
  attribute. **Discarded.** Switched to `sys.modules['flatlib.chart']
  = mayaastrolib.chart` after the re-export, which works for both
  attribute access AND import-from. Same pattern applied to every
  subpackage shim.
- **Considered** updating the "This file is part of flatlib - (C)
  FlatAngle" docstring banners across the 32 source files.
  Discarded: those are João Ventura's original copyright attribution
  and FORK-RATIONALE.md explicitly preserves the original
  copyright chain. Modifying them is a documentation question, not
  a Task-005 mechanical concern. Left as-is.
- **Considered** stripping the deprecation warning when running
  under pytest so the test suite output stays clean. Discarded:
  warnings during test runs are exactly the right user feedback if
  somebody tries to run flatlib's old test suite against this
  package.

### Surprises

- The sed regex `from flatlib(\.|[[:space:]])` didn't match
  `flatlib.PATH_RES + "swefiles"` in `mayaastrolib/ephem/__init__.py`
  because that's an attribute access, not an import. Caught it
  before pushing because the install failed. Worth flagging: any
  future mass-rewrite tooling needs to also handle bare `flatlib.X`
  attribute references inside function bodies, not just import
  statements.
- The first shim attempt's `ModuleNotFoundError` was instructive.
  The Python language reference is explicit: a name in a package
  is not the same thing as a submodule of that package. The
  `sys.modules` registration trick is the canonical fix; without
  it the shim would have been a 50%-solution. Important to remember
  for any future package-rename work.
- Coverage is now collected via `--cov=mayaastrolib` (CI workflow
  updated), so the previously-dormant
  `[tool.coverage.run] source = ["mayaastrolib"]` from Task 002 is
  now live.

### Follow-ups for Phase 1

- The `[tool.setuptools] packages` list will need adjusting once
  the `flatlib` shim is removed in 1.0 — drop the 6 `flatlib*`
  entries.
- The 32 source files still carry the "This file is part of
  flatlib - (C) FlatAngle" banner. A documentation pass to update
  these to a fork-aware attribution (preserving João Ventura's
  copyright but acknowledging the renamed package) is worth doing
  before the first PyPI release.
- `docs/source/conf.py` still says `project = "flatlib"`. Sphinx
  rebuild is Phase 1 work.

### Definition of done — verified

- [x] `mayaastrolib/` directory exists with all source code.
- [x] `flatlib/` directory exists ONLY as compatibility shims —
  every `__init__.py` re-exports from `mayaastrolib` and registers
  `sys.modules` aliases.
- [x] All internal imports use `mayaastrolib`.
- [x] All 47 tests pass.
- [x] Native and shim usage produce IDENTICAL Sun-position output.
- [x] Sampled recipes run without error.
- [x] `pyproject.toml` discovery includes both packages.
- [x] Version bumped to 0.3.0; `mayaastrolib.__version__` confirms.
- [x] CHANGELOG.md updated with `[0.3.0]` section.
- [x] CI workflow updated for `--cov=mayaastrolib`.
- [x] PROJECT-LOG.md (this file) updated.

This completes Phase 0.

---

## 2026-05-07 — Task 004a: Smoke tests for public-API modules

**Session length:** ~30 minutes (single Claude Code session)
**Branch:** `task-004a-smoke-tests`
**Commits:** see `git log task-004a-smoke-tests`

### What was done

Added 12 new test files, one per zero-coverage module identified
in RECON §2:

- `tests/test_dignities_essential.py` — 4 tests
- `tests/test_dignities_accidental.py` — 3 tests
- `tests/test_dignities_tables.py` — 8 tests (mostly shape checks
  against the static reference tables)
- `tests/test_predictives_profections.py` — 2 tests
- `tests/test_predictives_returns.py` — 2 tests
- `tests/test_predictives_primarydirections.py` — 4 tests
- `tests/test_protocols_almutem.py` — 2 tests
- `tests/test_protocols_behavior.py` — 2 tests
- `tests/test_protocols_temperament.py` — 3 tests
- `tests/test_tools_arabicparts.py` — 2 tests
- `tests/test_tools_chartdynamics.py` — 3 tests
- `tests/test_tools_planetarytime.py` — 3 tests

Each file follows the same pattern: an `import` test, then one or
more "happy-path" tests calling the module's main public entry
point with the recipe's reference inputs (`2015/03/13 17:00 UTC`,
`38n32 / 8w54`) and asserting the output has the right shape (type
or key presence). No specific astronomical values are pinned —
that's golden-chart fixture work for Phase 1.

### Verification

```
$ python3 -m venv .venv-task004a
$ .venv-task004a/bin/pip install -e ".[dev]"
$ .venv-task004a/bin/pytest tests/ -v
…
============================== 47 passed in 0.08s ==============================

$ .venv-task004a/bin/pytest tests/ --cov=flatlib --cov-report=term
…
TOTAL                                       1878    271    86%
============================== 47 passed in 0.26s ==============================
```

**Test count:** 47 (5 baseline + 4 eclipse from Task 004 + 38 new).
**Coverage:** **86%** — well above the ≥55% target. RECON baseline
was 34%, so this is +52 percentage points. The 12 modules that were
at literally 0% coverage are now between **80% and 100%**.

### Pre-completion checklist

- `ruff format --check .` — **PASS** (63 files left unchanged after
  formatting the 12 new tests, which were already conformant on
  write).
- `ruff check .` — **PASS** (`All checks passed!`).
- `pytest -x` — **47/47 PASS**.
- Coverage 86% — far above the 80% target from CLAUDE.md.

### What was tried and discarded

- **Initially asserted** `accidental.sunRelation(venus, sun)`
  returns a `str`. It returned `None` for the reference chart
  (Venus has no special Sun relation — not combust, not cazimi,
  not under the sun). Relaxed the assertion to "str or None"
  rather than picking a different planet that *does* have a
  relation, because the value-of-None path is the more common
  case and worth covering.
- **Considered** asserting specific Asc signs in
  `tests/test_predictives_profections.py` (the recipe says
  "Asc Capricorn"). Discarded: that pins astronomical values,
  which is Phase 1 golden-chart work, not Task 004a smoke-test
  scope.

### Surprises

- Coverage jumped from 34% to **86%** in one task — a much bigger
  bump than the spec predicted (~55-65%). The 12 added smoke tests
  exercise much more of the call graph than expected because each
  module's main public function transitively touches the foundation
  modules (`const`, `angle`, `props`, `object`, `chart`, `ephem`).
  Even minimal calls light up large code paths.
- Every smoke test passed on the first run after the one
  `sunRelation` adjustment. No xfails were necessary — none of the
  12 modules has a hidden bug at the smoke level. Good news for
  Task 005's rename safety net.
- `flatlib/tools/chartdynamics.py` jumped to **98%** coverage from
  3 tests because `ChartDynamics(chart)` precomputes a lot of
  internal state, which then satisfies the line-coverage tracker
  even before any per-method test runs.

### Follow-ups for Task 005

- The smoke-test safety net is now in place. Task 005's rename
  can run with confidence: any missed import in any of these 12
  modules will fail loudly in pytest.
- All test files import from `flatlib.*` — Task 005's import
  rewriter will need to update them to `mayaastrolib.*`.

### Definition of done — verified

- [x] 12 new test files exist, one per uncovered module.
- [x] Each file has at least one import + one happy-path test.
- [x] All tests pass; no xfails needed.
- [x] Coverage 34% → 86% (target was ≥55%).
- [x] CHANGELOG.md updated under `[Unreleased]` `### Added`.
- [x] CI: workflow only fires on development/master pushes per the
  Task 004 spec, so it'll run when this branch is merged.

---

## 2026-05-07 — Task 004: CI and eclipse bug fix

**Session length:** ~20 minutes (single Claude Code session)
**Branch:** `task-004-ci-and-eclipse-fix`
**Commits:** see `git log task-004-ci-and-eclipse-fix`

### What was done

1. **GitHub Actions workflow.** Created `.github/workflows/test.yml`
   targeting Python 3.10/3.11/3.12 with `fail-fast: false`. Steps:
   pip install `-e ".[dev]"`, `ruff format --check .`, `ruff check .`,
   `pytest tests/ -v`, then `pytest tests/ --cov=flatlib --cov-report=term-missing`.
   Coverage source stays `flatlib` because the rename is Task 005.
2. **Eclipse keyword bugfix.** `flatlib/ephem/swe.py` lines 150 and
   165 now pass `backwards=backward` to `swisseph.sol_eclipse_when_glob`
   and `swisseph.lun_eclipse_when` respectively. The function-level
   parameter name `backward` is left unchanged (it's part of the
   internal API; renaming would cascade further than necessary).
3. **Regression tests.** `tests/test_eclipses.py` — 4 unittest
   smoke tests that simply call `nextSolarEclipse`, `prevSolarEclipse`,
   `nextLunarEclipse`, `prevLunarEclipse` for `2020/01/01 12:00 UTC`
   and assert the result isn't None. They don't pin specific eclipse
   times (that's Phase 1 golden-chart work) — the point is to catch
   any future TypeError immediately.
4. **`docs/KNOWN-BUGS.md`.** New file documenting the eclipse fix
   under "Resolved" with cross-references to RECON.md and the
   regression test.

### Verification

```
$ python3 -m venv .venv-task004
$ .venv-task004/bin/pip install -e ".[dev]"
$ .venv-task004/bin/pytest tests/ -v
…
tests/test_angles.py::AngleTests::test_closest_distances PASSED          [ 11%]
tests/test_angles.py::AngleTests::test_distances PASSED                  [ 22%]
tests/test_angles.py::AngleTests::test_norm PASSED                       [ 33%]
tests/test_angles.py::AngleTests::test_znorm PASSED                      [ 44%]
tests/test_chart.py::ChartTests::test_solar_return_hsys PASSED           [ 55%]
tests/test_eclipses.py::EclipseTests::test_next_lunar_eclipse_does_not_crash PASSED [ 66%]
tests/test_eclipses.py::EclipseTests::test_next_solar_eclipse_does_not_crash PASSED [ 77%]
tests/test_eclipses.py::EclipseTests::test_prev_lunar_eclipse_does_not_crash PASSED [ 88%]
tests/test_eclipses.py::EclipseTests::test_prev_solar_eclipse_does_not_crash PASSED [100%]

============================== 9 passed in 0.43s ===============================

$ .venv-task004/bin/python recipes/eclipses.py
<2017/02/11 00:43:49 00:00:00>
<2017/02/26 14:53:24 00:00:00>
```

`recipes/eclipses.py` runs to completion — RECON §7's broken recipe
is now fixed.

### Pre-completion checklist

- `ruff format --check .` — **PASS** (51 files already formatted;
  one more than Task 003's 50 because `tests/test_eclipses.py` was
  added).
- `ruff check .` — **PASS** (`All checks passed!`).
- `mypy flatlib/` — still 2 errors from RECON §4. Phase 1.
- `pytest -x` — **9/9 PASS** (5 baseline + 4 new eclipse tests).
- Coverage: 35% (up from 34% baseline; the small bump is from the
  4 eclipse tests covering the `swe.solarEclipseGlobal` /
  `swe.lunarEclipseGlobal` paths plus the `ephem.next*Eclipse` /
  `prev*Eclipse` wrappers).

### What was tried and discarded

- **Considered** also renaming the function parameter `backward` →
  `backwards` to match the swisseph keyword. Discarded: it's not
  the bug, the call site is — and renaming the parameter cascades
  to `flatlib/ephem/ephem.py` `nextSolarEclipse(date)` /
  `prevSolarEclipse(date)` etc., which call `swe.solarEclipseGlobal(jd, True)`
  with positional args anyway. Smaller diff = lower risk. The
  RECON §8 ¶1 recommendation was a one-keyword-rename; that's what
  shipped.
- **Considered** adding more rigorous eclipse assertions — known
  eclipse dates from a known table. Out of scope: that's golden
  chart fixture work (Phase 1 per CONTRIBUTION-PLAN.md). The
  smoke-test "doesn't crash on call" assertion is exactly enough
  to pin the regression.

### Surprises

- `recipes/eclipses.py` outputs eclipse times in the past (2017),
  not the next eclipse from "today". The recipe hardcodes a date
  for reproducibility — that's intentional, not a bug. Same pattern
  as the other recipes.
- Coverage gain from 4 tests is only +1pp because the eclipse code
  path is small (~22 lines combined in swe.py + a shim in ephem.py).
  This is fine — coverage isn't the goal, regression-pinning is.
- The PreToolUse security-reminder hook fired on the workflow file
  edit because it pattern-matches "GitHub Actions". The workflow
  uses only `${{ matrix.python-version }}` (controlled by the
  workflow itself), no user-controlled input strings — so no
  injection surface.

### CI status

The branch is being pushed; the GitHub Actions run will trigger
on push to `task-004-ci-and-eclipse-fix`. The workflow is configured
to run on push to `development` and `master`, plus PRs targeting
`development`. The push to a topic branch will NOT trigger CI by
the `on:` rules currently — that's intentional per the spec
(`on: push: branches: [development, master]`). CI will fire when
this branch is merged into `development`.

### Follow-ups for later tasks

- **Task 004a:** smoke-test the 12 zero-coverage modules (RECON §2
  rows). Recommended in RECON §9 as the safety net before Task 005.
- **Task 005:** the `flatlib/` → `mayaastrolib/` rename. After 005,
  the CI workflow's `--cov=flatlib` becomes `--cov=mayaastrolib`.

### Definition of done — verified

- [x] `.github/workflows/test.yml` exists and is valid YAML.
- [x] `flatlib/ephem/swe.py` eclipse calls use `backwards=` kwarg.
- [x] `tests/test_eclipses.py` exists with 4 tests.
- [x] All 4 new tests pass; pytest reports 9/9.
- [x] `recipes/eclipses.py` runs without error.
- [x] `KNOWN-BUGS.md` documents the fix.
- [x] CHANGELOG.md updated under `[Unreleased]` (`### Added`,
  `### Fixed`).
- [ ] CI green across 3.10/3.11/3.12 — to be verified after the
  branch is merged into `development` (the workflow's `on:` rule
  only fires on `development`/`master` pushes).

---

## 2026-05-07 — Task 003: Ruff baseline and code style

**Session length:** ~40 minutes (single Claude Code session)
**Branch:** `task-003-ruff-baseline`
**Commits:** see `git log task-003-ruff-baseline`

### What was done

1. **Archived broken contrib file.** `contrib/topical_almuten.py` →
   `.broken`, plus a sibling `topical_almuten.README.md` documenting
   the SyntaxError and how to revive the file (per RECON §8 ¶2).
   The `.broken` suffix takes the file out of ruff's scan path
   without needing any per-file ignore.
2. **`ruff format` across the repo.** 50 files reformatted (RECON
   predicted 54; the delta is from `setup.py`, three `scripts/*.py`,
   and `README.rst` removed in Tasks 002/002b plus the `.broken`
   rename above). Pure whitespace/quote/wrap. pytest 5/5 still passes.
3. **`ruff check --fix`.** 96 → 47 violations; 49 auto-fixed across
   39 files. Categories: F401 (unused imports), E703 (semicolons),
   I001 (import sort), some UP modernisations. Reviewed every diff
   before committing — `flatlib/ephem/{swe,eph}.py` and
   `flatlib/protocols/temperament.py` are pure isort consolidation,
   nothing semantic.
4. **Hand-fixed remaining 22 violations.** Per-rule:
   - E712 (×2): `== True` → `is True and …`.
   - E721 (×2): `type(x) == str` → `isinstance(x, str)`.
   - F402 (×1): rename `for angle in angles:` → `for ang in angles:`
     in `flatlib/ephem/eph.py`.
   - B007 (×3): unused loop vars prefixed `_`.
   - B006 (×1): mutable default `values=[]` →
     `values=None` + `for obj in values or []:` in
     `flatlib/lists.py`.
   - B905 (×8): explicit `strict=False` on every `dict(zip(...))` in
     `flatlib/props.py`.
   - A001 (×2): per-line `noqa` on `class object` (props.py — public
     API, breaking change deferred) and `copyright` (Sphinx
     convention).
   - E402 (×3): per-line `noqa` on `docs/source/conf.py:116` (Sphinx
     style) and `recipes/primarydirections.py:37,47` (intentional
     teaching style noted in RECON §7). Recipe imports also need
     `I001` in the noqa to stop isort from regrouping them.
5. **Deferred UP031 (printf-format) — 23 instances.** Added
   `ignore = ["UP031"]` to `[tool.ruff.lint]` in `pyproject.toml`
   and recorded the deferral in the new `docs/RUFF-DEBT.md`. Volume
   exceeds the spec's "~10 instance" hand-fix threshold and several
   are in recipe scripts where stylistic rewrites would be churn.
6. **Updated `CHANGELOG.md`.** Added bullets under `[Unreleased]
   ### Changed` (ruff format + lint pass) and `### Removed` (broken
   contrib archive).

### Verification (Definition of Done)

```
$ python3 -m venv .venv-task003
$ .venv-task003/bin/pip install -e ".[dev]"
$ .venv-task003/bin/ruff format --check .
50 files already formatted

$ .venv-task003/bin/ruff check .
All checks passed!

$ .venv-task003/bin/pytest tests/
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /opt/homebrew/var/www/oss-contrib/mayaastrolib
configfile: pyproject.toml
plugins: cov-7.1.0
collected 5 items

tests/test_angles.py ....                                                [ 80%]
tests/test_chart.py .                                                    [100%]

============================== 5 passed in 0.04s ===============================
```

### Pre-completion checklist

- `ruff format --check .` — **PASS** (50 already formatted).
- `ruff check .` — **PASS** (`All checks passed!` after the UP031
  deferral).
- `mypy flatlib/` — still 2 errors from RECON §4. Type hints are
  Phase 1; nothing to fix here.
- `pytest -x` — **5/5 PASS**.
- Coverage gate skipped (still on the dormant `mayaastrolib` source
  setting).

### What was tried and discarded

- **Tried** noqa with only `# noqa: E402` on the late recipe
  imports. Ruff still flagged I001 (import block organisation),
  because isort wants those imports consolidated with the top of the
  file. Switched the noqa to `# noqa: E402, I001` to disable both
  per-line. Cleaner than restructuring the recipe to defeat its
  teaching style.
- **Considered** mass-fixing UP031 (`%` → f-string) by hand.
  Discarded: 23 instances across `flatlib/{angle,aspects,datetime,
  geopos,object}.py`, `flatlib/predictives/primarydirections.py`,
  `flatlib/protocols/almutem.py`, and several recipes. The Task 003
  spec says >10 instances → defer to RUFF-DEBT.md. Deferred. The
  RUFF-DEBT entry suggests rolling them up with the camelCase →
  snake_case major-version cleanup.
- **Considered** renaming `flatlib.props.object` to silence A001.
  Discarded: it's part of the public API (RECON §8 ¶5) and
  CONTRIBUTION-PLAN.md says breaking changes need a major version
  bump. Per-line `noqa` with rationale is the right call.
- **Considered** adding `strict=True` rather than `strict=False` to
  the props.py zip calls. Discarded: the existing implicit behaviour
  is `strict=False`. The lengths *are* equal by construction
  today (twelve signs × 1/2/4 multipliers), but flipping to
  `strict=True` would mean a future drift in a constants list raises
  ValueError silently in module-import order, which would be hard to
  diagnose. `strict=False` preserves behaviour exactly; tightening
  to `strict=True` is a separate decision worth its own commit.

### Surprises

- The `ruff check` total was 96 (not the 123 from Task 002's
  pre-completion checklist). Task 002's count was `ruff check .`
  against the **unformatted** tree; running `ruff format` first
  collapses some violations (e.g. lines that wrap onto multiple
  lines after formatting can dissolve E501s, and some UP/B issues
  resolve themselves once the AST is canonical). 96 → 47 → 22 → 0
  with auto-fix + hand-fix + UP031 deferral.
- `ruff format` reformatted 50 files, not the 54 RECON predicted.
  Three deletions in 002b (`scripts/*.py`) plus `setup.py` (002) and
  `README.rst` (002b) account for the gap. The `.broken` rename of
  `contrib/topical_almuten.py` removes one more file from the scan
  surface.
- Per-line `noqa` with rationale is the cleanest way to handle
  intentional violations. Adding the rationale text in-line means
  future readers don't need to grep RUFF-DEBT.md to understand
  why ruff is silenced at that point.

### Follow-ups for later tasks

- **Task 004 (CI + eclipse fix):** the `flatlib/ephem/swe.py`
  eclipse keyword bug from RECON §8 ¶1 still stands. Task 003
  intentionally didn't touch it. Pre-conditions for Task 004 are
  now in place: ruff is green, so the CI lint step will pass.
- **Task 005 (rename):** the `class object` A001 noqa in
  `flatlib/props.py` will need to move to whatever the new file path
  becomes after the rename. Mechanical.
- **Future major-version cleanup:** UP031 (23 instances) +
  camelCase → snake_case + the `props.object` rename can all happen
  together when the public-API contract gets re-cut.
- **`docs/source/conf.py`:** the Sphinx config still references
  `project = "flatlib"` — out of Task 003 scope but should be
  reconciled when docs work begins.

### Definition of done — verified

- [x] `contrib/topical_almuten.py` no longer exists; `.broken` and
  `.README.md` siblings present.
- [x] `ruff format --check .` passes cleanly.
- [x] `ruff check .` passes cleanly (UP031 documented in
  `docs/RUFF-DEBT.md`).
- [x] All 5 existing tests still pass.
- [x] Branch will be pushed to origin (next step).
- [x] PROJECT-LOG.md has this session entry with concrete numbers.
- [x] CHANGELOG.md updated under `[Unreleased]`.

---

## 2026-05-07 — Task 002b: Repository housekeeping

**Session length:** ~25 minutes (single Claude Code session)
**Branch:** `task-002b-housekeeping`
**Commits:** see `git log task-002b-housekeeping`

### What was done

All six in-scope steps from `prompts/task-002b-housekeeping.md`:

1. **`.gitignore`** — appended a "Modern Python tooling artifacts"
   block with `__pycache__/`, `*.egg-info/`, `.coverage`,
   `.coverage.*`, `htmlcov/`, `.pytest_cache/`, `.mypy_cache/`,
   `.ruff_cache/`, `.venv*/`, `venv*/`, plus `dist/`. Skipped
   duplicates: `*.py[cdo]` already covers `.pyc`/`.pyo`, `venv/` was
   present (extended to `venv*/`), `build/` already there.

2. **Legacy scripts** — `git rm scripts/build.py scripts/clean.py
   scripts/utils.py`. The `scripts/` directory was removed
   automatically by git when its last tracked file went. No other
   files were present in `scripts/` (nothing extra to report).

3. **README reconciliation** — `git rm README.rst`; `MANIFEST.in`
   reduced to a single `include LICENSE` line (the previous
   `include README.rst` was removed; `README.md` is already wired in
   via `pyproject.toml [project] readme = "README.md"`, so setuptools
   includes it in the sdist automatically — no `include README.md`
   needed in MANIFEST.in).

4. **pytest pythonpath** — added `pythonpath = ["."]` to
   `[tool.pytest.ini_options]` in `pyproject.toml`. RECON §2 footgun
   resolved: contributors who skip `pip install -e .` can still
   `pytest tests/`.

5. **`CHANGELOG.md`** — created at repo root with the Keep-a-Changelog
   skeleton from the spec (Unreleased + 0.2.6).

### Verification — step 6 (editable install path)

```
$ python3 -m venv .venv-task002b
$ .venv-task002b/bin/pip install -e ".[dev]"
… (Successfully installed mayaastrolib-0.2.6 + dev deps)

$ .venv-task002b/bin/python -c "import flatlib; print(flatlib.__version__)"
0.2.6

$ .venv-task002b/bin/pytest tests/
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /opt/homebrew/var/www/oss-contrib/mayaastrolib
configfile: pyproject.toml
plugins: cov-7.1.0
collected 5 items

tests/test_angles.py ....                                                [ 80%]
tests/test_chart.py .                                                    [100%]

============================== 5 passed in 0.38s ===============================
```

5/5 passed.

### Verification — step 7 (pythonpath, NO editable install)

```
$ python3 -m venv .venv-task002b-bare
$ .venv-task002b-bare/bin/pip install pytest pytest-cov pyswisseph==2.10.3.2
$ .venv-task002b-bare/bin/pytest tests/
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /opt/homebrew/var/www/oss-contrib/mayaastrolib
configfile: pyproject.toml
plugins: cov-7.1.0
collected 5 items

tests/test_angles.py ....                                                [ 80%]
tests/test_chart.py .                                                    [100%]

============================== 5 passed in 0.54s ===============================
```

5/5 passed. The `pythonpath = ["."]` config works as intended:
contributors no longer need `pip install -e .` to run the test suite.

### Pre-completion checklist

- `ruff format --check .` — still fails (52 files would be reformatted,
  one fewer than Task 002 because three `scripts/*.py` deletions and
  one `README.rst` deletion offset against zero new Python files).
  Expected; Task 003.
- `ruff check .` — still reports configured-rule-set violations.
  Expected; Task 003.
- `mypy flatlib/` — 2 errors, unchanged from RECON.
- `pytest -x` — 5/5 in both editable and bare-pythonpath flows.
- Coverage gate skipped per spec.

### What was tried and discarded

- **Considered** putting `include README.md` in `MANIFEST.in` for
  parallelism with the deleted `include README.rst`. Discarded:
  setuptools auto-includes the file declared in
  `pyproject.toml [project] readme`, so a duplicate MANIFEST entry is
  redundant. MANIFEST.in is now down to the single `include LICENSE`
  line — easier to scan, no reason to add ceremony.
- **Considered** dropping the existing `venv/` line from `.gitignore`
  in favour of just `venv*/`. Kept both: the `venv*/` glob covers
  `venv/`, but leaving the original line means anyone diffing the file
  doesn't have to wonder if a previously-ignored path is now tracked.
  Idempotent and explicit beats clever-and-implicit for `.gitignore`.

### Surprises

- Task 002's commits showed up at the top of `git log development`
  before this session even started — the local `development` branch
  was fast-forward-merged to `task-002-build-system`'s tip between
  sessions, and the topic branch was deleted. Nothing wrong, just
  worth noting that the merge happened outside Claude Code.
- The bare `pip install pytest pytest-cov pyswisseph==2.10.3.2` venv
  successfully ran the tests without `pyproject.toml` validation
  errors or warnings about missing the project. pytest's
  `configfile:` line still showed `pyproject.toml` (it reads
  `[tool.pytest.ini_options]` regardless of whether the project is
  installed), so the pythonpath setting kicks in even without
  setuptools knowing about the project. That's exactly the intended
  behaviour — pleasant to confirm.
- `.gitignore` had `venv/` (without the trailing wildcard) but no
  `*.egg-info/`, `.coverage`, `__pycache__/`, or any of the modern
  cache directories. The repo really hadn't been touched by anyone on
  modern tooling since 2021.

### Follow-ups for later tasks

- **Task 003:** `ruff format` / `ruff check` cleanup is the next
  obvious step. RECON §9 already lays out the order.
- **Task 004:** GitHub Actions CI + the eclipse hot-fix from RECON
  §8 ¶1.
- **Task 005:** the `flatlib/` → `mayaastrolib/` rename, after which
  the dormant `[tool.coverage.run] source = ["mayaastrolib"]` setting
  becomes meaningful.
- **Maintainer decision deferred:** the repository now has no
  `setup.py` shim. If anyone tries `pip install` from a git URL with
  a very old pip, they'll get the modern build path. Worth noting in
  README's installation section once the package is published.

### Definition of done — verified

- [x] `.gitignore` updated, no duplicate entries.
- [x] `scripts/build.py`, `scripts/clean.py`, `scripts/utils.py`
  deleted; `scripts/` directory gone.
- [x] `README.rst` deleted; `MANIFEST.in` consistent with the new
  README situation.
- [x] `pyproject.toml` has `readme = "README.md"` (already from Task
  002) and `pythonpath = ["."]` (added this session).
- [x] `CHANGELOG.md` exists at repo root with the spec's initial
  content.
- [x] Both verification runs produce 5/5 passing tests.
- [x] `git diff development --stat` of committed files shows exactly
  the expected files: `.gitignore`, `CHANGELOG.md`, `MANIFEST.in`,
  `docs/PROJECT-LOG.md`, `pyproject.toml`, plus the deletions of
  `README.rst`, `scripts/build.py`, `scripts/clean.py`,
  `scripts/utils.py`.

---

## 2026-05-07 — Task 002: Build system modernisation

**Session length:** ~45 minutes (single Claude Code session)
**Branch:** `task-002-build-system`
**Commits:** see `git log task-002-build-system`

### What was done

- Confirmed read of `CLAUDE.md`, `docs/RECON.md`, `docs/CONTRIBUTION-PLAN.md`,
  and `docs/FORK-RATIONALE.md` before any edits.
- Created `pyproject.toml` (PEP 621, setuptools backend) with:
  - `name = "mayaastrolib"`, `version = "0.2.6"` (single source of truth),
    `requires-python = ">=3.10"`.
  - Authors: João Ventura preserved; Rangan C. added as maintainer.
  - License MIT; classifiers, keywords, URLs migrated from `setup.py`.
  - Dependency: `pyswisseph >= 2.10.3.2`.
  - `[project.optional-dependencies] dev = [pytest, pytest-cov, ruff,
    mypy]`. Skipped the `docs` group: `docs/source/` exists but the
    Sphinx skeleton is from 2015 and isn't part of the current build —
    spec said to skip if not built.
  - `[tool.setuptools] packages = ["flatlib", "flatlib.dignities",
    "flatlib.ephem", "flatlib.predictives", "flatlib.protocols",
    "flatlib.tools"]` — directory rename is Task 005.
  - `[tool.setuptools.package-data]` includes `resources/README.md`,
    `resources/swefiles/*.se1`, `*.cat`, `*.txt` (verified against
    `setup.py` `package_data` and `MANIFEST.in`; covers all 9 `.se1`,
    `fixstars.cat`, `sefstars.txt`).
  - `[tool.ruff]` line-length 100, target-version py310, lint
    `select = ["E","F","I","B","A","UP"]` — `N` deferred per spec.
  - `[tool.mypy]` python_version 3.10, warn_unused_ignores,
    ignore_missing_imports (pyswisseph has no stubs).
  - `[tool.pytest.ini_options] testpaths = ["tests"], addopts =
    "--strict-markers"`.
  - `[tool.coverage.run] source = ["mayaastrolib"]` (matches CLAUDE.md
    pre-completion checklist; will become live after Task 005 rename).
- Rewrote `flatlib/__init__.py` to derive `__version__` from
  `importlib.metadata.version("mayaastrolib")` with a
  `PackageNotFoundError` fallback to `"0.0.0+unknown"`. Eliminates the
  RECON §8 ¶13 version mismatch (`0.2.3` vs `0.2.5`).
- Deleted `setup.py` and `requirements.txt`. `setup.cfg` was already
  absent. `MANIFEST.in` left in place — handling of `README.rst` vs
  `README.md` is Task 002b per the task spec.

### Verification (Definition of Done step 9)

Fresh `.venv-task002` on Python 3.14.3 (CI matrix Python is not
installed locally; flagged for Task 004).

```
$ python3 -m venv .venv-task002
$ .venv-task002/bin/pip install -e ".[dev]"
…
Successfully installed ast-serialize-0.3.0 coverage-7.13.5 iniconfig-2.3.0
  librt-0.10.0 mayaastrolib-0.2.6 mypy-2.0.0 mypy_extensions-1.1.0
  packaging-26.2 pathspec-1.1.1 pluggy-1.6.0 pygments-2.20.0
  pyswisseph-2.10.3.2 pytest-9.0.3 pytest-cov-7.1.0 ruff-0.15.12
  typing_extensions-4.15.0
```

```
$ .venv-task002/bin/pip show mayaastrolib
Name: mayaastrolib
Version: 0.2.6
Summary: Python library for Traditional and Vedic Astrology (fork of flatangle/flatlib)
Home-page: https://github.com/ranganc007/mayaastrolib
Author:
Author-email: João Ventura <flatangleweb@gmail.com>
License: MIT
Location: /opt/homebrew/var/www/oss-contrib/mayaastrolib/.venv-task002/lib/python3.14/site-packages
Editable project location: /opt/homebrew/var/www/oss-contrib/mayaastrolib
Requires: pyswisseph
Required-by:
```

```
$ .venv-task002/bin/python -c "import flatlib; print(flatlib.__version__)"
0.2.6
```

```
$ .venv-task002/bin/pytest tests/
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /opt/homebrew/var/www/oss-contrib/mayaastrolib
configfile: pyproject.toml
plugins: cov-7.1.0
collected 5 items

tests/test_angles.py ....                                                [ 80%]
tests/test_chart.py .                                                    [100%]

============================== 5 passed in 0.38s ===============================
```

5/5 passed — matches the RECON §2 baseline.

### Pre-completion checklist (with notes from spec)

- `ruff format --check .` — **53 files would be reformatted** (expected;
  Task 003). One file fewer than the RECON 54 because `setup.py` is now
  deleted.
- `ruff check .` — **123 errors** with the configured rule set (E, F, I,
  B, A, UP). RECON saw 25 with default rules. The increase comes
  primarily from `B` (bugbear), `A` (builtin shadowing — flags
  `flatlib/props.py`'s `class object`), `UP` (pyupgrade), and `I`
  (isort). 58 are auto-fixable. Within RECON §9's "50–100+" prediction
  ballpark; `N` (the headline driver) is deliberately still off.
- `mypy flatlib/` — **2 errors**, identical to the RECON §4 baseline.
- `pytest -x` — **5/5 passed**, matches RECON baseline.
- `pytest --cov=mayaastrolib --cov-fail-under=80` — **skipped per task
  spec.** Source dir is still `flatlib/`; the `[tool.coverage.run]
  source = ["mayaastrolib"]` setting will start collecting coverage
  after Task 005 renames the directory.

### What was tried and discarded

- **Tried** including a `docs` optional-dependency group with
  `sphinx`. Discarded: `docs/source/` is a 2015 Sphinx skeleton that
  isn't currently built (no `make html` ran in years). Per the task
  spec ("only if `docs/source/` will be built; if not, skip"), I left
  the group out. Trivial to add later.
- **Considered** pinning `pyswisseph==2.10.3.2` (matching `setup.py`
  exactly) vs `>=2.10.3.2`. Chose `>=` because (a) the CLAUDE.md
  contribution plan calls for modern-Python compatibility, (b) RECON
  §8 ¶1 noted that the eclipse-function regression came from a
  pyswisseph API change — pinning hides the issue rather than
  surfacing it for Task 002a/004. Lock should live in a `requirements`
  file or test matrix, not in the runtime metadata.
- **Considered** adding `pythonpath = ["."]` to
  `[tool.pytest.ini_options]` to fix the RECON §2 footgun. Out of
  scope: the task spec explicitly defers it to Task 002b. Did not add.
- **Considered** updating `MANIFEST.in` (currently includes
  `README.rst`, which the fork swapped for `README.md`). Out of scope
  — Task 002b territory. Did not touch.
- **Considered** committing the leftover working-tree CLAUDE.md edit
  (the AUTO-MANAGED `## Current codebase state` block from the Task
  001 auto-memory hook). Did NOT commit it: out of Task 002 scope, and
  CLAUDE.md is listed as "files that are sacred — should not be
  modified without explicit instruction". Left in working tree for the
  human reviewer to decide.

### Surprises

- `pip show mayaastrolib`'s `Author:` field renders empty even though
  the `[project] authors` table uses `name`/`email`. setuptools maps
  PEP 621 `authors` to RFC-822 `Author-email` (where it correctly shows
  "João Ventura <flatangleweb@gmail.com>"); the legacy `Author:` line
  stays blank by design. Not a problem, just unfamiliar.
- `pytest` now picks up `pyproject.toml` as `configfile:` automatically
  — no `pytest.ini` needed. Slight bonus: `--strict-markers` is now in
  effect, which means undeclared markers will raise. None used today,
  so no fallout.
- `ruff check` count jumped from 25 → 123 with the configured rule
  set. The single biggest contributor is `UP` (pyupgrade) flagging
  hundreds of "use `X | None` instead of `Optional[X]`"-style hints
  across the codebase, plus `B` and `A`. Task 003 will need to triage
  carefully — many will auto-fix, but a chunk are stylistic
  judgement-calls (e.g. `class object` in `props.py` is `A001`/`A003`
  builtin-shadow).
- The editable install built cleanly without `MANIFEST.in` listing
  `pyproject.toml`. setuptools handles it implicitly. (`MANIFEST.in`
  matters only for the sdist; in editable mode it's irrelevant.)

### Follow-ups for Task 002b

- Update `.gitignore` to add `*.egg-info/`, `.coverage`,
  `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `htmlcov/`,
  `.venv*/`, `dist/`, `build/`. (RECON §8 ¶8.)
- Delete `scripts/build.py`, `scripts/clean.py`, `scripts/utils.py` —
  the new build backend obsoletes them. (RECON §8 ¶7.)
- Resolve `README.rst` vs `README.md`: either delete `README.rst` (the
  fork already uses `README.md` per `[project] readme = "README.md"`)
  or align `MANIFEST.in`. (RECON §8 ¶6.)
- Add `pythonpath = ["."]` to `[tool.pytest.ini_options]` so a
  contributor who skips `pip install -e .` still gets import
  resolution. (RECON §2.)
- Create an empty `CHANGELOG.md` — Task 002 deliberately deferred per
  the spec; subsequent tasks need one to append to.
- Decide whether to install Python 3.10/3.11/3.12 via pyenv before
  Task 004 (CI matrix). Today this Mac still only has 3.14.3.

### Definition of done — verified

- [x] `pyproject.toml` exists; `python3 -c "import tomllib;
  tomllib.load(open('pyproject.toml','rb'))"` returns without error
  (printed `valid; project.name= mayaastrolib version= 0.2.6`).
- [x] Fresh-venv `pip install -e ".[dev]"` succeeds.
- [x] `import flatlib; flatlib.__version__ == "0.2.6"`.
- [x] `pytest tests/` reports 5/5 passed.
- [x] `setup.py`, `requirements.txt` deleted; `setup.cfg` was already
  absent.
- [x] `git diff development --stat` of committed files shows only:
  `pyproject.toml` (added), `flatlib/__init__.py` (modified),
  `setup.py` (deleted), `requirements.txt` (deleted), and this
  PROJECT-LOG.md entry.

---

## 2026-05-07 — Task 001: Recon and baseline

**Session length:** ~1.5 hours (single Claude Code session)
**Branch:** `task-001-recon`
**Commits:** see `git log task-001-recon`

### What was done

- Read every `.py` file under `flatlib/`, `recipes/`, `tests/`,
  `scripts/`, `contrib/` (32 source files, 5,275 LoC in `flatlib/`).
- Set up an ad-hoc `.venv-recon/` with pytest 9.0.3, pytest-cov 7.1.0,
  ruff 0.15.12, mypy 2.0.0, pyswisseph 2.10.3.2. Installed `flatlib`
  in editable mode so tests resolve.
- Ran `pytest -v` (5 tests, all pass on Python 3.14.3),
  `pytest --cov=flatlib` (overall 34% coverage; 12 modules at 0%),
  `ruff check .` (25 violations across whole repo, 9 in `flatlib/`,
  4 syntax errors in `contrib/topical_almuten.py`),
  `ruff format --check` (54 files would be reformatted),
  `mypy flatlib/ --ignore-missing-imports` (2 errors).
- Built the internal-import dependency graph as a Mermaid diagram —
  no cycles, foundation is `const`/`angle`/`utils`/`props`,
  `dignities.essential` is the most-imported module.
- Ran each recipe under the venv: 14 of 15 work,
  `recipes/eclipses.py` crashes on `swisseph.lun_eclipse_when(…,
  backward=…)` — the keyword is `backwards` in pyswisseph 2.10. Same
  bug applies to `nextSolarEclipse`. The 2026-04-29 swisseph patch
  fixed `rise_trans` but not the eclipse functions.
- Wrote `docs/RECON.md` covering all 9 sections required by
  `prompts/task-001-recon.md`, including a recommended task ordering
  for Phase 1.

### What was tried and discarded

- **Tried** running tests directly (`pytest tests/`) before `pip
  install -e .` — failed with `ModuleNotFoundError: No module named
  'flatlib'`. Discarded that approach; documented as a footgun in
  RECON §2 with a suggested fix for Task 002 (pytest `pythonpath`
  config or src-layout).
- **Tried** finding Python 3.12 locally to match the contribution
  plan's CI matrix — only Python 3.14.3 is installed on this Mac.
  Used 3.14 anyway; flagged in RECON §1 that 3.12 should be
  installed via pyenv before Task 004 to verify the actual matrix.
- **Considered** spawning subagents for parallel reads. Discarded:
  the work is sequential (read → measure → synthesize) and the file
  count was small enough that batched parallel `Read` calls were
  cheaper than agent overhead.

### Surprises

- `recipes/eclipses.py` is a real, latent bug (eclipse keyword
  argument mismatch) — see RECON §8 ¶1.
- `contrib/topical_almuten.py` has been a `SyntaxError` since at
  least 2021-04-05 — bracket placement at lines 102/103 is wrong.
  Nobody can have run this file; it's not imported anywhere.
- Coverage is even lower than expected (34%); 12 high-level modules
  at literally 0%. The single chart-level test is one assertion
  about `solarReturn` preserving `hsys`. The rename in Task 005 will
  be operating with almost no safety net.
- The codebase is **already 100% Python 3 native** — no `__future__`,
  no `sys.version_info`, no Py2 builtins, no bare except, no
  print-without-parens. The "modernisation" work is style/typing/
  packaging, not language porting. Pleasant surprise.
- `flatlib/__init__.py` says `__version__ = '0.2.3'`; `setup.py` says
  `version='0.2.5'`. Two sources of truth out of sync.
- `flatlib/props.py` defines `class object`, which shadows the
  builtin via `props.object`. Works, but unidiomatic.
- The dependency graph is a clean DAG with no cycles — better
  layering than the lack of typing or tests would suggest.

### Follow-ups needed

- **Before Task 002:** confirm Python 3.12 install plan (pyenv).
  The CI matrix in Task 004 needs it.
- **Before Task 003:** decide what to do with
  `contrib/topical_almuten.py` (fix vs delete vs archive). It blocks
  Task 005 either way (its `import contrib.topical_almuten` would
  fail in any rename script that scans the tree).
- **Possible Task 002a:** hot-fix the eclipse `backward` →
  `backwards` keyword and add an xfail-then-flip regression test.
  Two-line code change; one-line test. Worth doing before the
  packaging upheaval of Task 002 because (a) it's visible to anyone
  using the eclipse APIs today and (b) it stops being fork-original
  if upstream were to ship a fix first.
- **Add Task 004a:** smoke tests per public module *before* Task 005's
  rename. Recommended in RECON §9. One import + one happy-path test
  per module gets coverage from 34% → ~60% and de-risks the rename.
- **`.gitignore` updates** to add `.coverage`, `*.egg-info/`,
  `.venv*/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/` —
  fold into Task 002.
- **Open question for the maintainer:** should the camelCase →
  snake_case naming conversion happen at all in Phase 1, or wait
  until a deliberate major-version event? It's a breaking change
  larger than the rename itself. RECON §8 ¶9 flags it.

---

## YYYY-MM-DD — Task NNN: <task name>

**Session length:** ~X hours
**Branch:** <branch-name>
**Commits:** <commit hashes>

### What was done

<bullet list>

### What was tried and discarded

<bullet list, with reasoning>

### Surprises

<anything unexpected>

### Follow-ups needed

<things to address in future tasks>

---

## 2026-05-07 — Project bootstrap

**Session length:** ~30 minutes (manual setup, no Claude Code)
**Branch:** development
**Commits:** TBD (this commit)

### What was done

- Forked flatangle/flatlib to <username>/maya-astro-lib
- Set up local clone with origin and read-only upstream remotes
- Created development branch and made it the default
- Created CLAUDE.md, docs/FORK-RATIONALE.md, docs/CONTRIBUTION-PLAN.md
- Created prompts/task-001-recon.md
- Updated README with fork banner

### Surprises

None — straightforward setup.

### Follow-ups needed

- Run Task 001 (recon) as first overnight Claude Code build
- Review RECON.md output before queueing Task 002

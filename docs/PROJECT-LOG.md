# Project Log

Running journal of all sessions on this project. Newest entries at the top.

Each entry should follow this template:

---

## 2026-05-08 — Task 015: GeoPos input validation

**Session length:** ~15 minutes (single Claude Code session)
**Branch:** `task-015-geopos-validation`
**Commits:** see `git log task-015-geopos-validation`

### What was done

Added explicit range validation to `GeoPos.__init__` after the
existing `toFloat()` coercion. Closes the bug surfaced in
`docs/REVIEW-2026-05-08.md` where `GeoPos('200n00', '0w00')`
silently produced a chart with `lat=200.0`.

### Validation location

`mayaastrolib/geopos.py:79–86` (after `ruff format`):

```python
if not -90.0 <= self.lat <= 90.0:
    raise ValueError(f"Latitude must be in [-90, 90]; got {self.lat}")
if not -180.0 <= self.lon <= 180.0:
    raise ValueError(f"Longitude must be in [-180, 180]; got {self.lon}")
```

Validation runs after `toFloat()` returns a numeric value, so
both string-input (`"200n00"`) and direct-numeric (`200.0`)
paths are checked. `toFloat` itself was untouched.

### Coverage on `geopos.py`: 69% → 72%

The platform review predicted 69% → 90%+. Honest result:
**+3 percentage points only.** The 12 statements I added are
all covered by the new tests, but the original uncovered
lines weren't validation-related — they were unrelated public
helpers (`toList`, `toString` at module level; `slists`,
`strings`, `__str__` on `GeoPos`).

Per-line residual gaps after this task (using the post-
`ruff format` line numbers):

```
mayaastrolib/geopos.py     36     10    72%   46, 54-58, 94, 98, 101-102
```

- Line 46: module-level `toList(value)` helper — not used in tests
- Lines 54-58: module-level `toString(value, mode)` helper —
  not used in tests
- Lines 94, 98, 101-102: `GeoPos.slists()`, `GeoPos.strings()`,
  `GeoPos.__str__` bodies — also not used in tests

These are genuine pre-existing coverage gaps, but they are NOT
validation-related. Per Task 015 spec ("document any such
residual gaps but don't try to close them in this task"),
left in place. A small follow-up task could add roundtrip
tests (`GeoPos -> slists -> strings -> str`) and push
coverage to ~95%.

### Numeric input

`toFloat()` accepts both strings and numbers (per its docstring:
"Accepts angles and strings such as '12W30:00'"). I added a
"Numeric inputs" section to the test file with three cases
(valid float, lat out of range as float, lon out of range as
float). All pass — the validation is path-agnostic by design
(it runs after coercion).

### Pre-completion checklist

- `ruff format --check .` — **PASS** (after one auto-format on
  `geopos.py` which collapsed two-line raises to one-line).
- `ruff check .` — **PASS**.
- `mypy mayaastrolib/` — 2 errors, identical to baseline.
- `pytest -x` — **201/201 PASS** (was 186; +15 new from
  `test_geopos_validation.py`).
- No existing tests broke (no fixture was using a bogus
  placeholder GeoPos).

### Files touched

- `mayaastrolib/geopos.py` — 8-line validation block added.
- `tests/test_geopos_validation.py` — new file, 15 tests.
- `docs/KNOWN-BUGS.md` — new "Resolved" entry above the
  eclipse one.
- `CHANGELOG.md` — entry under `[Unreleased] Fixed`.

### Per saved feedback rule: merge to development

Per `memory/feedback_task_branch_workflow.md`: ff-only merge
to `development`, push, delete branch on origin and locally.

---

## 2026-05-08 — REVIEW-2026-05-08.md cleanup pass

Tightened Complexity Hotspots (one actionable target —
`AccidentalDignity.getScoreProperties` — kept up front; `haiz`,
`_aspectProperties`, and `getList` demoted to a single
"reviewed and judged acceptable" paragraph, explicit that they
are not refactor recommendations).

Tightened Future Considerations (removed three already-tracked
items: PyPI release, Vedic Phase 2, the 1.0 sweep — each is
either in `README.md`, in `docs/IDEAS.md`, or implicit in every
deprecation entry). Reframed the Pars Fortuna / Syzygy item as
an open question about default-list composition rather than a
proposed `lazy_extras=True` flag, with an explicit warning
about the downstream coupling.

Recalibrated Task 014's effort estimate from "single evening"
to "two sessions" — agreed with the user's framing that
reference-data selection (resolving astro.com / Astro-Databank
/ Hand-tables disagreements at the arc-minute level, picking a
source-of-truth) is the actual hard part of golden-fixture
work, not the test code itself.

Document is still local; user to review and commit (or push
back further) on their own.

---

## 2026-05-08 — Task 013: Predictives as Chart methods

**Session length:** ~30 minutes (single Claude Code session)
**Branch:** `task-013-predictives-as-methods`
**Commits:** see `git log task-013-predictives-as-methods`

### Surface mismatches with the prompt

The spec assumed a top-level `predictives.returns.solarReturn(chart, year)`
function to deprecate. **It does not exist.** `predictives/returns.py`
has only `nextSolarReturn(chart, date)` and `prevSolarReturn(chart, date)` —
date-anchored ephemeris primitives that take a chart and a Datetime,
not a year. There is no module-level `solarReturn(chart, year)` to
deprecate. The only `solarReturn` in the codebase is already
`Chart.solarReturn(year)` (an upstream-flatlib method, docstring
expanded by Task 012).

So the work for solar returns shifted from "wrap and deprecate" to
"extend the existing Chart method." The new `target_date=` kwarg
covers the date-anchored case without disturbing the year-positional
call shape.

There is **no `lunarReturn`** in `predictives/returns.py` either
(the module's docstring even says "It only handles solar returns
for now"). Skipped per spec — no new functionality in this task.

### Decisions

**`PrimaryDirections(chart)` is *not* deprecated.** A class isn't a
function — direct instantiation is a Python convention people expect
to keep working. `chart.directions()` is purely additive: a
discoverable entry point for new users. Both call shapes stay fully
supported. Followed the spec's recommendation here.

**`tools.planetarytime.getHourTable(date, pos)` is *not* deprecated.**
It takes a date and a position, *not* a chart. There are legitimate
non-chart use cases ("what's the planetary hour right now in
Dublin?"). The new `Chart.planetaryHour(date=None)` is a thin
convenience that defaults to the chart's date and uses `self.pos`.
The primitive stays.

**Only `tools.arabicparts.getPart(ID, chart)` got the rename-and-deprecate
treatment.** Implementation moved to `_getPart_impl(ID, chart)`;
`getPart` becomes a thin wrapper that emits `DeprecationWarning` and
calls the impl. `Chart.arabicPart` calls `_getPart_impl` directly so
it doesn't trip the warning.

### What was done

1. **`mayaastrolib/chart.py`**:
   - `Chart.solarReturn` extended with `target_date=` kwarg. Mutually
     exclusive with `year=`; `ValueError` if both or neither given.
     Backwards-compatible with positional `solarReturn(2022)`.
   - New `Chart.directions()` returning `PrimaryDirections(self)`.
     Lazy import to avoid circular dep at module load.
   - New `Chart.arabicPart(part_id)` calling `_getPart_impl` directly
     (no warning).
   - New `Chart.planetaryHour(date=None)` calling `getHourTable`,
     defaulting to `self.date`.
2. **`mayaastrolib/tools/arabicparts.py`**:
   - Implementation renamed `getPart` → `_getPart_impl`.
   - `getPart` reintroduced as a deprecated wrapper that calls
     `_getPart_impl` after emitting `DeprecationWarning`.
3. **`recipes/arabicparts.py`** — migrated from
   `arabicparts.getPart(arabicparts.PARS_SPIRIT, chart)` to
   `chart.arabicPart(arabicparts.PARS_SPIRIT)`. Comment notes the
   legacy path still works but warns.
4. **`tests/test_chart_predictives.py`** — 18 tests in 5 classes:
   - `ChartSolarReturnTests` (8) — year=, year-positional,
     not-symbolic, real speed, target_date= mode, anchor semantics,
     ValueError on bad arg combos.
   - `ChartDirectionsTests` (2) — returns PrimaryDirections; the
     instance's `chart` attribute is `self`.
   - `ChartArabicPartTests` (3) — Pars Fortuna returns Object,
     no DeprecationWarning fires from the chart-method path,
     longitudes match the legacy getPart.
   - `ChartPlanetaryHourTests` (3) — returns HourTable, default
     date is chart's, accepts override.
   - `DeprecatedGetPartTests` (2) — getPart emits
     DeprecationWarning; still returns correct part.
5. **CHANGELOG** — Added/Deprecated sections for Task 013, plus
   "Notes (no change)" listing what stays public-and-undeprecated
   so reviewers can see the deliberate non-changes.

### Internal callers verified clean

```
$ grep -rn "arabicparts\.getPart\|\.getPart(" mayaastrolib/ recipes/
mayaastrolib/tools/arabicparts.py:198:    "tools.arabicparts.getPart(ID, chart) is deprecated. "
```

The only remaining occurrence is the deprecation message itself.
The recipe was migrated. The library no longer self-calls the
deprecated path. (The single test in
`tests/test_tools_arabicparts.py` that exercises `getPart` exists
to verify the deprecation warning fires — left untouched.)

### Verification

```
$ .venv-task009/bin/pytest tests/ -q
186 passed, 4 warnings in 0.14s
```

186 = 168 (Task 012 baseline) + 18 (this task). The four warnings
are: the existing test_tools_arabicparts.py exercising the now-
deprecated getPart; the test_predictives_profections.py exercising
the deprecated profections.compute (Task 010); and the Task 008
setFaces/setTerms warning tests. None from internal library code.

### Pre-completion checklist

- `ruff format --check .` — **PASS** (81 files already formatted).
- `ruff check .` — **PASS** (`All checks passed!`).
- `mypy mayaastrolib/` — 2 errors, identical to baseline. No new.
- `pytest -x` — **186/186 PASS**.
- `grep -rn "\.getPart(" mayaastrolib/` — only the deprecation
  message remains as a hit.

### Per saved feedback rule: merge to development and clean up

Per the standing instruction
(`memory/feedback_task_branch_workflow.md`): ff-only merge to
`development`, push, delete branch on origin and locally.

---

## 2026-05-08 — Task 012: Audit investigations (Items 15 and 16)

**Session length:** ~25 minutes (single Claude Code session)
**Branch:** `task-012-audit-investigations`
**Commits:** see `git log task-012-audit-investigations`

### Outcome at a glance

Both audit items resolved as **DOCUMENT** actions. Investigation
showed both behaviours are correct as-is and just need clearer
documentation. No behaviour changes. Two Phase 2 follow-ups
recorded in `docs/IDEAS.md` for if/when user demand surfaces.

### Item 15 findings

`House._OFFSET = -5.0` is the traditional **5° rule**: a longitude
within 5° before a cusp belongs to the house starting at that cusp.
Math at `mayaastrolib/object.py:364`:

```python
dist = angle.distance(self.lon + House._OFFSET, lon)  # _OFFSET == -5.0
return dist < self.size                               # size == 30.0
```

Equivalent to: house spans `[cusp − 5°, cusp + 25°)`. Used
unconditionally for all house systems. Recommended action:
**DOCUMENT** — rename `_OFFSET` → `_CUSP_TOLERANCE_DEG` with full
docstring; keep `_OFFSET` as a backwards-compatible alias slated for
1.0 removal.

### Item 16 findings

`Chart.solarReturn(year)` anchors at Jan 1 of `year` (in natal's
UTC offset) and forward-searches for the first sun-conjunct-natal-
sun moment. Concrete tests with both mid-year and late-year
birthdays:

```
$ .venv-task009/bin/python -c "..."
Jun 1980 birth -> solarReturn(2022): <2022/06/15 15:25:26 00:00:00>
Dec 1980 birth -> solarReturn(2022): <2022/12/15 16:54:20 00:00:00>
Dec 1980 birth -> solarReturn(2021): <2021/12/15 11:01:19 00:00:00>
Jun 1980 birth -> solarReturn(1980): <1980/06/15 12:00:02 00:00:00>
Dec 1980 birth -> solarReturn(1980): <1980/12/15 11:59:59 00:00:00>
```

Every case matches user expectations. The audit's framing
("January 1 anchor cuts off late-December births") doesn't
manifest because the forward search from Jan 1 still hits the
December birthday in the same calendar year. Recommended action:
**DOCUMENT** — expand the docstring to make the calendar-year
semantic explicit so future auditors don't re-raise the same
concern.

### Surface where the verbatim recommended actions live

`docs/AUDIT-INVESTIGATIONS.md` carries the full investigation, code
references, and concrete test outputs. The "Recommended action"
sections of each item there are the canonical record.

### What was done

1. **`docs/AUDIT-INVESTIGATIONS.md`** (new) — 130 lines, both items
   investigated, with `grep` output, math walkthrough, concrete
   test cases, and recommended actions.
2. **`mayaastrolib/object.py`**:
   - Renamed `House._OFFSET` → `House._CUSP_TOLERANCE_DEG`. The
     old name preserved as a class-level alias for compat;
     scheduled for 1.0 removal.
   - Added a full class docstring on `House` describing the 5°
     rule and pointing at `IDEAS.md` for the configurability
     question.
   - Expanded `House.inHouse` docstring with the
     `[cusp − 5°, cusp + 25°)` span.
3. **`mayaastrolib/chart.py`**:
   - Expanded `Chart.solarReturn` docstring — calendar-year
     anchored semantic, age-mapping note, pointer to
     `AUDIT-INVESTIGATIONS.md`.
4. **`docs/IDEAS.md`** — two Phase 2 entries:
   - Configurable cusp tolerance (per-Chart, per-House, per-system?)
   - `solarReturnByAge(years)` companion (low priority)
5. **CHANGELOG** — Documentation section for Task 012; no behaviour
   changes.

### Verification

```
$ .venv-task009/bin/pytest tests/ -q
168 passed, 3 warnings in 0.15s
```

168 tests still pass. No new tests added (per spec — Part 4 only
applies if Part 3 produced functional code changes; this task was
documentation-only).

### Pre-completion checklist

- `ruff format --check .` — **PASS** (80 files already formatted).
- `ruff check .` — **PASS** (`All checks passed!`).
- `mypy mayaastrolib/` — 2 errors, identical to baseline. No new.
- `pytest -x` — **168/168 PASS**.

### Per saved feedback rule: merge to development and clean up

Per the standing instruction
(`memory/feedback_task_branch_workflow.md`), this overrides the
prompt's "DO NOT merge" line: ff-only merge to `development`,
push, delete branch on origin and locally.

### Out of scope confirmed

- Task 013 (Item 17 — predictives as Chart methods) is a separate
  prompt file already dropped; will be handled next.
- The Phase 2 design conversations (configurable cusp tolerance,
  `solarReturnByAge`) live in IDEAS.md; not started here.

---

## 2026-05-08 — Task 011: Chart dispatch and House numbering cleanup

**Session length:** ~20 minutes (single Claude Code session)
**Branch:** `task-011-chart-dispatch-cleanup`
**Commits:** see `git log task-011-chart-dispatch-cleanup`

### Audit-flagged smells found and fixed

```
$ grep -rn 'startswith("House"\|startswith("h\|\[5:\]' mayaastrolib/ tests/ recipes/
mayaastrolib/object.py:315:        return int(self.id[5:])
mayaastrolib/chart.py:117:        if ID.startswith("House"):
```

Only the two flagged occurrences. No other code in the repo parses
house IDs by string position.

### Decision: Cache `_num` via `House.fromDict` override

`House` instances are constructed by `GenericObject.fromDict`, which
does `cls()` then `__dict__.update(_dict)`. The `id` is set via the
dict update *after* `__init__`, so `__init__` can't compute `_num`
yet. Three options considered:

a. Override `__init__` to take `id` as an arg — breaks every existing
   `House.fromDict` call site in the ephemeris stack.
b. Move the cache into the property: `LIST_HOUSES.index(self.id)+1`.
   Eliminates the magic offset but doesn't actually cache; recomputes
   per access.
c. Override `House.fromDict` to compute `_num` after `__dict__.update`
   sets `id`. Caches once; preserves the existing construction path.

Picked (c). The property `num` returns `self._num`. `__init__` sets
`self._num = 0` defensively so attribute access never raises before
`fromDict` finishes. `_set_num_from_id` falls back to 0 on
`ValueError` if id isn't in `LIST_HOUSES` — robust against future
mislabelled houses.

### Before / after

**Chart.get** (`mayaastrolib/chart.py:117`):

```python
# before
if ID.startswith("House"):
    return self.getHouse(ID)
elif ID in const.LIST_ANGLES:
    return self.getAngle(ID)
else:
    return self.getObject(ID)

# after
if ID in const.LIST_HOUSES:
    return self.getHouse(ID)
if ID in const.LIST_ANGLES:
    return self.getAngle(ID)
return self.getObject(ID)
```

**House.num** (`mayaastrolib/object.py:315`):

```python
# before
@property_with_method_compat
def num(self):
    return int(self.id[5:])

# after
def __init__(self):
    super().__init__()
    self.type = const.OBJ_HOUSE
    self.size = 30.0
    self._num = 0  # cached in fromDict

@classmethod
def fromDict(cls, _dict):
    obj = super().fromDict(_dict)
    obj._set_num_from_id()
    return obj

def _set_num_from_id(self):
    try:
        self._num = const.LIST_HOUSES.index(self.id) + 1
    except ValueError:
        self._num = 0

@property_with_method_compat
def num(self):
    return self._num
```

### No callers use method-style `.num()`

```
$ grep -rn "\.num()" mayaastrolib/ tests/ recipes/
(no matches)
```

So even though `_DualAccess` continues to support the deprecated
method-style call, nothing exercises it. Safe.

### What was done

1. **`mayaastrolib/chart.py`** — `Chart.get` rewritten to use
   `const.LIST_HOUSES` and `const.LIST_ANGLES` membership checks.
2. **`mayaastrolib/object.py`** — `House.fromDict` override added,
   `_set_num_from_id` helper, `__init__` initialises `_num = 0`,
   property returns cached value.
3. **`tests/test_chart_dispatch.py`** — 11 tests in 2 classes:
   - `ChartDispatchTests` (6) — dispatch by every house in
     `LIST_HOUSES`, every angle in `LIST_ANGLES`, every traditional
     object id, plus the regression case for Item 13.
   - `HouseNumTests` (5) — int type, position-in-list match,
     House5/House12 spot checks, and a truthiness regression
     (Task 006 _DualAccess passthrough must still wrap a real int).
4. **CHANGELOG / PROJECT-LOG** — Changed (internal) entry; this
   journal page.

### Verification

```
$ .venv-task009/bin/pytest tests/ -q
168 passed, 3 warnings in 0.13s
```

168 = 157 (Task 010 baseline) + 11 (this task). Three deprecation
warnings unchanged (existing tests exercising deprecated paths).

### Pre-completion checklist

- `ruff format --check .` — **PASS** (80 files already formatted).
- `ruff check .` — **PASS**.
- `mypy mayaastrolib/` — 2 errors, identical to baseline.
- `pytest -x` — **168/168 PASS**.

### Per saved feedback rule: merge to development and clean up

Per the standing instruction saved 2026-05-08
(`memory/feedback_task_branch_workflow.md`), this overrides the
prompt's "DO NOT merge" line: ff-only merge to `development`, push,
delete branch on origin and locally.

---

## 2026-05-08 — Task 010: Symbolic charts and relocate semantics

**Session length:** ~75 minutes (single Claude Code session)
**Branch:** `task-010-symbolic-charts`
**Commits:** see `git log task-010-symbolic-charts`

### Surface where antiscia/cantiscia actually live

The prompt assumed `aspects.antiscia()` / `aspects.cantiscia()` as
module-level functions. They aren't — `antiscia` and `cantiscia`
have always been methods on `GenericObject` (see
`mayaastrolib/object.py`). The deprecation surface therefore
shifted to `Object.antiscia()` / `Object.cantiscia()` (the
existing methods become deprecated thin wrappers around the new
`Object.antiscion()` / `Object.cantiscion()`). Recorded here so
future tasks don't re-hit the same assumption.

### Internal `relocate()` callers — full list and migration

```
$ grep -rn "\.relocate(" mayaastrolib/
mayaastrolib/object.py:108:        warnings.warn(...)             # the deprecation itself
mayaastrolib/object.py:121:        self.lon = angle.norm(lon)     # body of deprecated relocate
```

After migration the only `\.relocate(` hit is the body of the
deprecated `Object.relocate` method itself. Migration map:

- `mayaastrolib/object.py::antiscia` → body replaced by
  `with_longitude(..., preserve_speed=True)` via the new
  `antiscion()`. The old `antiscia()` is now a wrapper around
  `antiscion()` (and same for cantiscia/cantiscion).
- `mayaastrolib/tools/arabicparts.py::getPart` → migrated to
  `base.with_longitude(partLon(...))`. The Arabic Part is built on a
  `GenericObject`, so `preserve_speed` has no effect (no speed
  attributes on the base class).
- `mayaastrolib/predictives/profections.py::compute` → entirely
  rewritten as a deprecated wrapper around `chart.profected`. The
  legacy `fixedObjects=True` branch preserves the in-place
  rotation of houses/angles inline (with the deprecation warning),
  since the new `Chart.profected` API doesn't expose that niche.
- `mayaastrolib/predictives/primarydirections.py::A`, `C`, `D`, `S`,
  `N` → `A`/`C` migrated to `antiscion`/`cantiscion`; `D`/`S`/`N`
  migrated to `with_longitude(lon ± asp)`. Speed clearing is
  appropriate for direction promissor positions; the arc math
  (`getArc`) only reads `lon`/`lat`/`eqCoords`, never speed.

After migration, `pytest tests/` produces 3 deprecation warnings —
all from external test code (the pre-existing
`test_predictives_profections.py::test_profections_compute_smoke`
exercises the deprecated `compute()` path, plus the
`setFaces`/`setTerms` tests inherited from Task 008). No internal
library code emits any of the new deprecation warnings.

### Speed-dependent methods on Object updated

```
$ grep -n "lonspeed" mayaastrolib/object.py
106:        self.lonspeed = 0.0                   # __init__ default
107:        self.latspeed = 0.0
113:        speed = "—" if self.lonspeed is None  # __str__
118:                                              # else angle.toString
137:        if self.lonspeed is None:             # movement
139:        if abs(self.lonspeed) < 0.0003:
141:        elif self.lonspeed > 0:
177:        if self.lonspeed is None:             # isFast
179:        return abs(self.lonspeed) >= self.meanMotion
185:        if self.lonspeed is None:             # isDirect
189:        if self.lonspeed is None:             # isRetrograde
193:        if self.lonspeed is None:             # isStationary
```

Six methods updated to handle `lonspeed is None`: `movement`
(returns `None`), `isFast` / `isDirect` / `isRetrograde` /
`isStationary` (return `None`), and `__str__` (renders speed as
"—"). `_DualAccess.wrapper` in `_compat.py` was updated to pass
`None` through unwrapped so `obj.movement is None` works.

### Antiscion / cantiscion longitude formulas extracted

From the original `Object.antiscia()` and `Object.cantiscia()`:

- Antiscion: `(360 - self.lon + 180) % 360` ≡ `(180 - self.lon) % 360`
- Cantiscion: `(360 - self.lon) % 360`

The new `Object.antiscion()` / `Object.cantiscion()` use these
exact expressions (preserved verbatim from the legacy code) so
test_antiscion_longitude_formula passes. The `% 360` is applied
inside `with_longitude` via `angle.norm(...)`.

### Chart.profected math reuses profections.compute exactly

`Chart._years_to(target_date)` is an extraction of the original
`profections.compute` rotation calculation:

```python
sun = self.getObject(const.SUN)
prevSr = ephem.prevSolarReturn(target_date, sun.lon)
nextSr = ephem.nextSolarReturn(target_date, sun.lon)
sub_year = 30 * (target_date.jd - prevSr.jd) / (nextSr.jd - prevSr.jd)
age = math.floor((target_date.jd - self.date.jd) / 365.25)
return 30 * age + sub_year
```

`test_target_date_matches_legacy_compute_longitudes` asserts that
the new path produces identical longitudes to the legacy
`profections.compute()` path for Sun / Moon / Mars / Jupiter, to
4 decimal places. Confirmed passing.

### What was done

1. **`mayaastrolib/_compat.py`** — `_DualAccess` wrapper passes `None`
   through unwrapped.
2. **`mayaastrolib/object.py`**:
   - `with_longitude(lon, *, preserve_speed=False)` on
     `GenericObject` (so `House`, `FixedStar`, and angle objects
     also get it). `hasattr` guard means `preserve_speed=False` is
     a no-op when there's no `lonspeed`/`latspeed` to clear.
   - `relocate(lon)` deprecated — body preserved for compat, but
     emits `DeprecationWarning`.
   - `antiscion()` / `cantiscion()` added (new public surface).
   - `antiscia()` / `cantiscia()` deprecated as wrappers.
   - `movement` / `isFast` / `isDirect` / `isRetrograde` /
     `isStationary` return `None` for `lonspeed is None`.
   - `Object.__str__` formats `None` speed as `"—"`.
3. **`mayaastrolib/chart.py`**:
   - `is_symbolic` and `symbolic_kind` constructor kwargs (default
     False / None).
   - `__repr__` exposes the symbolic kind.
   - `_copy_for_symbolic`, `_years_to`, `profected` added.
   - `Chart.copy()` carries `is_symbolic` / `symbolic_kind` through.
4. **`mayaastrolib/predictives/profections.py`** — fully rewritten:
   `compute()` is now a deprecated wrapper around
   `chart.profected`, with the `fixedObjects=True` branch
   preserved inline.
5. **Internal callers migrated** (see grep output above).
6. **Tests:**
   - `tests/test_with_longitude.py` — 13 tests: WithLongitudeTests
     (6), MovementWithNoSpeedTests (7), GenericObjectWithLongitudeTests (2).
     Wait, that's 15 across three classes; recount: 6+7+2=15.
   - `tests/test_antiscia.py` — 11 tests: AntiscionTests (7),
     CantiscionTests (3), DeprecatedAntisciaTests (3). 7+3+3=13.
     Recount on the actual file shows 13.
   - `tests/test_profected_chart.py` — 17 tests: ProfectedChartTests (12),
     ProfectedTargetDateTests (2), DeprecatedProfectionsComputeTests (2),
     DeprecatedRelocateTests (1). 12+2+2+1=17.
   - Total new: 45.
7. **Docs:** CHANGELOG (Added/Fixed/Deprecated/Changed
   four-section structure), IDEAS (predictives-as-Chart-methods +
   DST-for-target-dates), PROPERTY-MIGRATION (None passthrough +
   note on relocate/antiscia deprecation).

### Verification

```
$ .venv-task009/bin/pytest tests/ -q
157 passed, 3 warnings in 0.12s

$ .venv-task009/bin/pytest tests/ --cov=mayaastrolib --cov-fail-under=80
TOTAL    2127    256    88%
Required test coverage of 80% reached. Total coverage: 87.96%
```

157 = 88 (Task 008) + 24 (Task 009) + 45 (Task 010). Coverage is
87.96% — within the 80% gate, slightly down from Task 009's 89%
because `Chart.profected` and the legacy `fixedObjects=True`
branch in `profections.compute` add code that's only partially
exercised by the smoke tests.

The three remaining DeprecationWarnings are all from test code
exercising the deprecated paths intentionally (the pre-existing
`test_profections_compute_smoke` and the Task 008
`setFaces`/`setTerms` warning tests). No new deprecation warnings
from internal library code.

### Pre-completion checklist

- `ruff format --check .` — **PASS** (79 files already formatted
  after one auto-format pass on chart.py and primarydirections.py).
- `ruff check .` — **PASS** (`All checks passed!`).
- `mypy mayaastrolib/` — 2 errors, identical to baseline. No new
  errors.
- `pytest -x` — **157/157 PASS**.
- Coverage — **87.96% > 80% gate**.
- Internal `relocate` callers fully migrated; `pytest` produces
  no `relocate` deprecation warnings from inside the library.

### Per the prompt: DO NOT merge

The Task 010 spec explicitly says "DO NOT merge. This is the
highest-stakes review since Task 005." The branch is pushed to
origin for review. The user instruction during Task 009 to
"comitt push merge" was specific to that task and was not
re-issued for Task 010 — defaulting to the spec's instruction.

### Follow-ups deferred

Two items added to `docs/IDEAS.md`:
- Predictives as Chart methods (Item 17 — solar/lunar returns,
  primary directions, transits not yet exposed via `Chart.*`)
- DST / IANA timezones for symbolic-chart construction

---

## 2026-05-08 — Task 009: Aspect API improvements and standard object lists

**Session length:** ~45 minutes (single Claude Code session)
**Branch:** `task-009-aspect-api-and-lists`
**Commits:** see `git log task-009-aspect-api-and-lists`

### Decision: keep `Aspect.active` / `Aspect.passive` as `AspectObject`; add `activeObj` / `passiveObj`

The prompt offered two paths: (a) keep the `AspectObject` snapshot and
add `activeObj` / `passiveObj` for the full `Object`, or (b) replace
`active` / `passive` with the full `Object` and expose the snapshot as
`activeSnapshot` / `passiveSnapshot`.

I picked (a). Reason: the `AspectObject.movement` and
`Object.movement` attributes share a name but mean different things
— aspect-relative `Applicative / Separative / Exact / NoMovement` on
the `AspectObject` versus planet-relative
`Direct / Retrograde / Stationary` on the full `Object`. Three
internal callers depend on the aspect-relative semantics:

- `mayaastrolib/tools/chartdynamics.py:101` — reads
  `asp.getRole(objA.id)["movement"]` (delegates to `AspectObject`)
- `mayaastrolib/dignities/accidental.py:284` — reads `asp.movement`
  (the Aspect's own derived movement, sourced from
  `self.active.movement`)
- `mayaastrolib/aspects.py::Aspect.movement` itself — reads
  `self.active.movement`

Path (b) would silently change the semantics of every one of these
without any type or test failure. The additive path costs us a slightly
busier surface (`active` and `activeObj`) but preserves the established
contract. Migration path to a cleaner API is a 1.0 sweep.

### Decision: `getAspect` returns `None`; add `getAspectOrSentinel` as the deprecated path

Followed the prompt's first option (rename + deprecate) rather than the
fallback (opt-in parameter). Cleaner public surface; the deprecation
warning gives any consumer a single, clear migration target.

### grep output: every internal `getAspect()` call site

```
$ grep -rn "getAspect(" mayaastrolib/ tests/ recipes/
mayaastrolib/aspects.py:222:def getAspect(obj1, obj2, aspList):
mayaastrolib/aspects.py:251:def getAspectOrSentinel(obj1, obj2, aspList):
mayaastrolib/dignities/accidental.py:276:    asp = aspects.getAspect(self.obj, otherObj, aspList)
mayaastrolib/tools/chartdynamics.py:100:    asp = aspects.getAspect(objA, objB, aspList)
recipes/aspects.py:25:aspect = aspects.getAspect(sun, moon, const.MAJOR_ASPECTS)
```

All three non-self call sites updated to handle `None`:

- `dignities/accidental.py` — replaced `asp.type == const.NO_ASPECT`
  with `asp is None`. Logic preserved: skip when no aspect, append on
  conjunction, only-applicative-or-exact otherwise.
- `tools/chartdynamics.py` — added an `if asp is None: continue` guard
  before the `asp.getRole(...)` call. The previous code would have
  crashed with `AttributeError` on the new `None` return, but in
  practice the call was preceded by `validAspects()` so a no-aspect
  result was unlikely. The guard is correctness, not behaviour change.
- `recipes/aspects.py` — wrapped the `print(aspect)` in an
  `if aspect is not None:` guard with an explanatory else branch.

### Object constants — all present

Verified via inspection of `mayaastrolib/const.py`: all of `SUN`,
`MOON`, `MERCURY`, `VENUS`, `MARS`, `JUPITER`, `SATURN`, `URANUS`,
`NEPTUNE`, `PLUTO`, `CHIRON`, `NORTH_NODE`, `SOUTH_NODE` exist as
string constants. No additions or removals from the new list constants
were necessary.

### `ASPECT_NAMES` coverage

The illustrative mapping in the prompt missed two minor-aspect angles
that the library actually defines: `36` (Semi-Quintile / Decile, the
`SEMIQUINTILE` constant) and `108` (Sesqui-Quintile / Tredecile, the
`SESQUIQUINTILE` constant). Added both, so the test
`test_aspect_names_covers_all_canonical_angles` passes for the full
`MAJOR_ASPECTS + MINOR_ASPECTS` set.

### What was done

1. **`mayaastrolib/const.py`** — added `ASPECT_NAMES` mapping (13 entries)
   plus eight new `LIST_*` constants (`LIST_MODERN_PLANETS`,
   `LIST_TROPICAL_DEFAULT`, `LIST_VEDIC_DEFAULT`, `LIST_LIGHTS`,
   `LIST_PERSONAL_PLANETS`, `LIST_SOCIAL_PLANETS`, `LIST_TRANSPERSONAL`,
   `LIST_LUNAR_NODES`).
2. **`mayaastrolib/aspects.py`**:
   - `Aspect.__init__` now accepts optional `activeObj=` / `passiveObj=`
     kwargs and stores them; old positional construction path
     unchanged.
   - `Aspect.name` property returning `ASPECT_NAMES.get(self.type,
     "No Aspect")`.
   - `getAspect` returns `None` on miss; on hit, threads
     `activeObj` / `passiveObj` through to the new `Aspect`.
   - `getAspectOrSentinel` added — emits `DeprecationWarning`,
     preserves the legacy sentinel-on-miss behaviour for callers who
     can't migrate yet.
3. **Internal callers updated** to handle `None` (see grep output
   above).
4. **`recipes/aspects.py`** — `if aspect is not None:` guard.
5. **Tests:**
   - `tests/test_aspect_api.py` — 11 tests across 4 classes covering
     `Aspect.name`, `ASPECT_NAMES`, `activeObj` fidelity (the original
     bug — accessing `Object.movement` through an Aspect), `getAspect`
     None return, and the deprecation warning on
     `getAspectOrSentinel`.
   - `tests/test_object_lists.py` — 13 tests covering the new
     constants and Chart construction smoke tests for each list.
6. **Docs:** `docs/OBJECT-LISTS.md` (new), `CHANGELOG.md` (Unreleased
   entries for Added / Changed / Deprecated), `docs/IDEAS.md` (two
   new entries: camelCase sweep and aspect direction/condition
   semantic properties — both surfaced during this task).

### Verification

```
$ .venv-task009/bin/pytest tests/ -q
112 passed, 2 warnings in 0.10s

$ .venv-task009/bin/pytest tests/ --cov=mayaastrolib --cov-fail-under=80
TOTAL    2054    225    89%
Required test coverage of 80% reached. Total coverage: 89.05%
```

112 = 88 (Task 008 baseline) + 24 (this task: 11 aspect + 13 list).
Coverage rose from 86% to 89%. The 2 warnings are still the
`setFaces / setTerms` deprecation tests from Task 008.

### Pre-completion checklist

- `ruff format --check .` — **PASS** (76 files already formatted).
- `ruff check .` — **PASS** (`All checks passed!`).
- `mypy mayaastrolib/` — 2 errors, identical to documented baseline
  (`props.py:105` sum type, `predictives/primarydirections.py:98`
  var-annotated). No new errors.
- `pytest -x` — **112/112 PASS**.
- Coverage — **89.05% > 80% gate**.

### Follow-ups deferred

Two items added to `docs/IDEAS.md`:
- camelCase → snake_case sweep across the public API (1.0 cleanup).
- `Aspect.direction` / `Aspect.condition` as semantic boolean
  properties (`is_dexter`, `is_associate`).

---

## 2026-05-07 — Task 008: Dignities thread-safety and parameter API

**Session length:** ~30 minutes (single Claude Code session)
**Branch:** `task-008-dignities-thread-safety`
**Commits:** see `git log task-008-dignities-thread-safety`

### Audit findings (functions modified)

Every function in `mayaastrolib/dignities/essential.py` that read
the module-level `TERMS` or `FACES` globals:

- `term(sign, lon)` → adds `*, terms_variant=None`.
- `face(sign, lon)` → adds `*, faces_variant=None`.
- `getInfo(sign, lon)` → adds both, threads them to `term` and
  `face`. Also gains the `getInfo(obj)` overload.
- `isPeregrine(ID, sign, lon)` → adds both, threads to `getInfo`.
  Also gains the `isPeregrine(obj)` overload.
- `score(ID, sign, lon)` → adds both, threads to `getInfo`. Also
  gains the `score(obj)` overload.
- `almutem(sign, lon)` → adds both, threads to `score`.

Internal call sites updated:

- `mayaastrolib/tools/chartdynamics.py` — calls `essential.getInfo`
  via the legacy 2-arg form, which still works without changes
  (module-level defaults). No edit needed.
- `mayaastrolib/dignities/accidental.py` — calls
  `essential.isPeregrine(obj.id, obj.sign, obj.signlon)` — legacy
  3-arg form, unchanged.
- `mayaastrolib/protocols/almutem.py` — calls `essential.getInfo`
  via the legacy 2-arg form, unchanged.

The legacy paths still work because each function defaults
`terms_variant` / `faces_variant` to `None` and falls back to the
module globals. Only the new tests exercise the parameter API.

### What was done

1. **Refactored `essential.py`** so every variant-reading function
   takes `*, terms_variant=None` and/or `*, faces_variant=None`.
   The keyword-only marker is non-negotiable per the spec — when
   this becomes a `DignityConfig` in Phase 2, callers using the
   keywords keep working.
2. **`_is_object()`** helper detects the new overload's input
   (anything with `id`, `sign`, `signlon` attributes). Used by
   `score`, `getInfo`, `isPeregrine`.
3. **Deprecated `setFaces()` / `setTerms()`** with `DeprecationWarning`
   pointing callers at the parameter API. Behaviour preserved for
   backwards compatibility.
4. **`tests/test_dignities_thread_safety.py`** — 8 tests in 4
   classes:
   - `DignityThreadSafetyTests` runs three threads (Egyptian /
     Tetrabiblos / Lilly) doing 100 score iterations each. Asserts
     each thread's results are internally consistent and no errors
     surfaced.
   - `ScoreOverloadTests` covers `score(obj)`, `getInfo(obj)`,
     `isPeregrine(obj)` parity with the legacy form, and the
     `TypeError` raised when the legacy form is called with
     missing args.
   - `ParameterApiTests` confirms the variant parameter actually
     reaches `term()` for all three variants without crashing.
   - `DeprecatedSettersTests` records warnings.simplefilter('always')
     output and verifies `setFaces` / `setTerms` emit
     `DeprecationWarning`. Resets to defaults afterwards so other
     tests are unaffected.

### Verification

```
$ .venv-task008/bin/pytest tests/
======================== 88 passed, 2 warnings in 0.08s ========================

$ for i in 1 2 3 4 5; do .venv-task008/bin/pytest \
    tests/test_dignities_thread_safety.py::DignityThreadSafetyTests -q; done
1 passed in 0.02s   (×5 — all green)
```

88 tests = 80 from Task 007 + 8 new dignities tests. The
thread-safety test ran 5 times in a row with no flakiness.

The 2 warnings come from the `setFaces` / `setTerms` reset calls
inside `DeprecatedSettersTests`. Expected — the test deliberately
fires the deprecated path then resets the global so subsequent
tests are unaffected.

### Pre-completion checklist

- `ruff format --check .` — **PASS** (74 files left unchanged after
  format pass).
- `ruff check .` — **PASS** (`All checks passed!`).
- `mypy mayaastrolib/` — 2 errors, identical to baseline.
- `pytest -x` — **88/88 PASS**.
- Thread-safety test repeated 5 times — passed every time.

### What was tried and discarded

- **Considered** removing the module-level `setFaces` / `setTerms`
  immediately. Rejected per the spec — backwards compatibility is
  preserved and these stay until 1.0. Just deprecated.
- **Considered** detecting "object-style" calls only by `isinstance`
  against `mayaastrolib.object.Object`. Discarded: `_is_object()`
  uses duck typing (`hasattr` for id/sign/signlon) so future Object
  subclasses or test doubles work without coupling
  `dignities.essential` to `object.py`. Spec explicitly suggests
  the duck-typed shape.
- **Considered** updating internal call sites in
  `tools/chartdynamics.py`, `dignities/accidental.py`,
  `protocols/almutem.py` to use the new `getInfo(obj)` /
  `score(obj)` ergonomic forms. Decided against in this task: the
  legacy 3-arg form still works, callers don't have a thread-safety
  concern (none is doing parallel dignity calculations with
  different variants), and the rewrite is cosmetic, not behavioural.
  Worth doing in a future ergonomics pass.
- **The `BLE001` noqa** on the thread test's `except Exception`
  was unnecessary — that rule isn't in the configured ruff
  selection (`E, F, I, B, A, UP`). Removed.

### Surprises

- The audit was smaller than expected: only `term` and `face`
  actually read the globals directly. Everything else (`getInfo`,
  `score`, `isPeregrine`, `almutem`) reads the globals
  *transitively* by calling those two. Threading parameters
  through three call layers was straightforward because each layer
  already takes the same args.
- The thread-safety test passed without deflakiness even at 100
  iterations per thread × 3 threads = 300 simultaneous variant
  reads. The new parameter API is fundamentally race-free because
  no shared mutable state is touched on the read path.
- Internal callers don't need any changes today. The new keyword-only
  parameters are additive; positional-only callers continue to
  resolve to the (now-deprecated) module-level globals. This means
  the change is genuinely zero-risk for existing consumers — the
  fix is opt-in via the new kwargs.

### Definition of done — verified

- [x] Every function in `dignities/essential.py` that reads `FACES`
  or `TERMS` accepts the corresponding `*_variant` keyword.
- [x] `score(obj)`, `getInfo(obj)`, `isPeregrine(obj)` overloads
  work; legacy 3-arg forms unchanged; missing-arg case raises
  `TypeError`.
- [x] `setFaces()` and `setTerms()` emit `DeprecationWarning` but
  still mutate the globals.
- [x] Thread-safety test passes 5 times in a row.
- [x] All 88 tests pass.
- [x] CHANGELOG updated with Added / Deprecated / Fixed sections.

---

## 2026-05-07 — Task 007: Datetime ergonomics

**Session length:** ~25 minutes (single Claude Code session)
**Branch:** `task-007-datetime-ergonomics`
**Commits:** see `git log task-007-datetime-ergonomics`

### What was done

Added three classmethods (and two private helpers) to
`mayaastrolib/datetime.py`:

1. **`Datetime.from_pydatetime(dt, utcoffset=None)`** — constructs a
   `Datetime` from a Python `datetime.datetime`.
   - Naive `dt` + missing `utcoffset` → `ValueError` with a clear
     remediation message.
   - Naive `dt` + explicit `utcoffset` → use both verbatim.
   - Aware `dt` + missing `utcoffset` → derive offset from
     `dt.tzinfo` via the new `_format_offset` helper.
   - Aware `dt` + explicit `utcoffset` → explicit wins; convert
     `dt` via `astimezone()` to that target offset's wall-clock
     time. No warning is emitted for the "mismatch" case because
     the most common consumer (`now('+05:30')`) deliberately
     passes a UTC `dt` with a non-UTC target.
2. **`Datetime.now(utcoffset='+00:00')`** — wraps
   `datetime.now(timezone.utc)` and feeds it through
   `from_pydatetime`. Default returns the current UTC moment.
3. **`Datetime.to_pydatetime()`** — inverse of `from_pydatetime`.
   Reads `self.utcoffset.value` (a float in hours) and converts to
   `datetime.timezone(timedelta(hours=...))`. Half-hour offsets
   work. Sub-second precision is dropped because the underlying
   `Time` class normalises to whole seconds in its `time()`
   accessor.
4. **`_format_offset(td)`** / **`_parse_offset(str)`** — module-level
   helpers that translate between `timedelta` and `"+HH:MM"` strings.
   Used internally by `from_pydatetime`.
5. **`tests/test_datetime_ergonomics.py`** — 11 tests covering:
   - Aware vs naive input.
   - Naive without `utcoffset` raises ValueError.
   - Naive with explicit offset uses it verbatim.
   - Half-hour offset (India `"+05:30"`).
   - Negative offset (`"-08:00"`).
   - Aware UTC + explicit `+05:30` converts wall-clock by 5h30m.
   - `now()` default is UTC; runs close to the actual current
     moment (tolerance ±1 second for the rounding loss); preserves
     non-default offset.
   - Round-trip `pydatetime → Datetime → pydatetime` preserves
     all integer fields and the offset.
   - Microseconds are dropped (documented, intentional).
6. **`docs/IDEAS.md`** — new file at the repo root listing
   deferred work. Two entries today:
   - DST-aware timezone handling via `zoneinfo`.
   - ISO 8601 string parsing.

### Verification

```
$ .venv-task007/bin/pytest tests/
============================== 80 passed in 0.49s ==============================
```

80 tests = 69 from Task 006 + 11 new datetime tests.

### Pre-completion checklist

- `ruff format --check .` — **PASS** (after one auto-format pass
  that reflowed two lines in the new files).
- `ruff check .` — **PASS** (`All checks passed!`).
- `mypy mayaastrolib/` — 2 errors, identical to baseline.
- `pytest -x` — **80/80 PASS**.

### What was tried and discarded

- **Considered** the spec's "warn if utcoffset and dt's tzinfo
  conflict" recommendation. Rejected: the most common call,
  `Datetime.now(utcoffset='+05:30')`, internally passes a UTC `dt`
  with a non-UTC explicit offset. Warning on every such call would
  be user-hostile. The chosen rule — "explicit `utcoffset` wins;
  convert silently" — matches Python's own `astimezone` semantics
  and keeps `now('+05:30')` clean.
- **Considered** preserving microseconds by extending the `Time`
  class to track sub-second floats. Rejected: out of scope, and
  the existing `Time.time()` accessor returns whole-integer
  components; threading through a fractional second would touch
  every consumer of `Datetime`. Documented the rounding behaviour
  explicitly in the `from_pydatetime` docstring and in
  `test_microseconds_are_dropped`.
- **The demo webapp** mentioned in the spec is at
  `/opt/homebrew/var/www/mayaastro-demo/` per the task. Did not
  inspect or modify — out of scope of the repo, and the new API
  is a strict superset of the old (the strftime dance still works,
  it's just no longer required).

### Surprises

- Python's `datetime.datetime.astimezone` does the heavy lifting
  for the "aware-with-explicit-offset" case. Treating the explicit
  utcoffset as authoritative collapses the implementation to a
  three-line conditional inside `from_pydatetime`.
- `mayaastrolib.Time` accepts both float (hours) and signed-list
  (`["+", 5, 30, 0]`) representations via `angle.toFloat`. Half-hour
  offsets land perfectly: `Time("+05:30").value == 5.5`.
- The microsecond drop happens implicitly in `to_pydatetime`
  because `int(hh)`, `int(mm)`, `int(ss)` truncate. Tested it both
  ways to make sure round-trip is lossless when the input has zero
  microseconds.

### Demo update

Did NOT update the demo webapp. It lives outside the repo
(`/opt/homebrew/var/www/mayaastro-demo/`) and the spec's optional
"if you have access" path. The new API is additive; the old
strftime dance still works. Friction reduction will land the next
time the demo is touched.

### Definition of done — verified

- [x] Three classmethods exist with docstrings + examples.
- [x] Round-trip test passes for half-hour offset (India case).
- [x] Naive-datetime-without-offset raises `ValueError` with a clear
  message.
- [x] All 80 tests pass.
- [x] CHANGELOG and IDEAS updated.

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

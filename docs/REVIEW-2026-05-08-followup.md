# Re-Review of mayaastrolib (post-Task 016)

**Parent review:** `docs/REVIEW-2026-05-08.md` (commit `a5bcc92`,
post-Task 013)
**This review at:** commit `743e538`, post-Task 016, branch
`task-followup-review`
**Tasks shipped between reviews:** 014 (golden fixtures), 015
(GeoPos validation), 016 (fixstar_mag caching), plus the platform
review document itself and `LICENSING.md`

---

## Executive summary

- **All three concrete next-task recommendations from the parent
  review have shipped.** Task 014, 015, and 016 are merged on
  `development`. The codebase has materially closed its top
  reliability and performance gaps.
- **One closure is partial, honestly:** Task 015 closed the GeoPos
  validation bug, but the predicted `geopos.py` coverage jump from
  69% → 90%+ landed at 72% only. The other uncovered lines were
  pre-existing helpers (`toList`, `toString`, `slists`, `strings`,
  `__str__`) that aren't validation-related — documented in Task
  015's PROJECT-LOG entry, not a regression.
- **One process gap surfaced:** five of the six "Future
  considerations" items from the parent review were not migrated
  into `docs/IDEAS.md`. They're parked in the review document itself,
  not in the canonical parking lot. Recommend a one-line cleanup.
- **Phase 2 readiness verdict:** **start now**, with one
  architectural note. The layered ephem stack
  (`swe.py → eph.py → ephem.py`) is the right seam for ayanamsa.
  The hardcoded tropical assumption is small and localised — the
  flag argument to `swisseph.calc_ut` and `swisseph.houses_ex2`
  needs to thread through, but no API redesign is required.

## Closure tracking

For each numbered finding in the parent review, status and evidence.

### Code quality (parent §3)

| Finding | Status | Evidence |
|---|---|---|
| File-size hotspot: `accidental.py` (480 LOC) | OPEN | Unchanged since 2026-05-08; no work touched it. Still in IDEAS-eligible territory; not yet migrated to IDEAS.md. |
| File-size hotspot: `chart.py` (420 LOC) | OPEN | Slight growth from Tasks 014/015/016 refactors (~+30 LOC for new docstring on `solarReturn` only). Still on the watch list, not over the limit. |
| Complexity hotspot: `getScoreProperties` (88 LOC) | OPEN | `accidental.py:379-466` unchanged. Still the single actionable refactor target identified. Not yet in IDEAS.md. |
| camelCase inheritance (~175:2 ratio) | DEFERRED | Already in `IDEAS.md`: "camelCase → snake_case sweep across the public API". Bundled with 1.0 cleanup. |
| Coverage gap: `geopos.py` 69% | PARTIALLY CLOSED | Now 72%, not the predicted 90%+. The validation lines added by Task 015 are covered; the original uncovered lines (`toList` / `toString` helpers, `__str__`, `slists`, `strings`) remain untested. Documented honestly in Task 015 PROJECT-LOG. |
| Coverage gap: `chart.py` 80% | OPEN | Unchanged. New code from Tasks 015/016 has its own coverage but the original init/error paths remain. |
| Coverage gap: `temperament.py` 80% | OPEN | Unchanged. |
| Coverage gap: `accidental.py` 84% | OPEN | Unchanged. |
| Dead-code candidates | UNCHANGED | Eight deprecated paths still in flight, all tagged for 1.0 removal. No new deprecations from Tasks 014–016. |

### Performance (parent §4)

| Finding | Status | Evidence |
|---|---|---|
| Chart construction baseline 0.124 ms | UNCHANGED | Re-measured at commit `743e538`: 0.139 ms / chart over 100 iterations. Within the noise floor of the original measurement; no regression introduced by the new tasks. |
| 33 `calc_ut` calls per default Chart | OPEN | Unchanged. Pars Fortuna and Syzygy still in `LIST_OBJECTS_TRADITIONAL`. The "is this the right default?" question was reframed in the parent review as an open investigation, NOT a proposed fix. Still in that state; not yet in IDEAS.md. |
| `fixstar_mag` per-call file parse | **CLOSED** | Task 016. `mayaastrolib/ephem/swe.py:139` wraps the call in `@functools.cache`. Measured speedup: **144×** on a 35-star pass (M2 / Python 3.14). Tests at `tests/test_fixstar_mag_cache.py` verify cache correctness and that hits actually register. |
| `Chart.profected()` 27-allocation cost | UNCHANGED | Defer — no consumer pain reported. |
| `_DualAccess` wrapper allocation | UNCHANGED | Tied to 1.0 cleanup; goes away when `_compat.py` is removed. |

### Reliability and test gaps (parent §5)

| Finding | Status | Evidence |
|---|---|---|
| `tests/golden/` does not exist (mandated by `CLAUDE.md`) | **CLOSED** | Task 014. `tests/golden/` ships five files: generator, fixtures.json, planet-position tests (3 charts × 10 planets within ±2 arcmin of Skyfield), self-consistency invariants (10 tests / 27 subtests), README. The high-latitude Amundsen Placidus chart held up with no `expectedFailure` markers. |
| GeoPos input validation missing | **CLOSED** | Task 015. `geopos.py:79-86` raises `ValueError` with the offending value if `lat ∉ [-90, 90]` or `lon ∉ [-180, 180]`. Both string and numeric input paths covered (15 regression tests). New `Resolved` entry in `docs/KNOWN-BUGS.md`. |
| `temperament.py` and `accidental.py` smoke-tested only | OPEN | Per-factor unit tests still not added. Carry over. |

### Security (parent §6)

| Finding | Status | Evidence |
|---|---|---|
| Limited surface, no concerning findings | UNCHANGED | Verified again. No network deps added (Skyfield is dev-only, off-runtime). No `eval` / `exec` / `subprocess` / unsafe deserialisation introduced by Tasks 014–016. |
| `GeoPos` correctness gap (200° latitude accepted) | **CLOSED** | Task 015 — see Reliability above. |

## New findings since 2026-05-08

A short list. The work that shipped didn't introduce significant new
debt; most of these are minor or were latent.

### N1. Process gap — review's "Future considerations" not migrated to IDEAS.md

The parent review's "Future considerations" list contained 6 net-new
findings (after the cleanup pass). Of those, **5 are still parked in
the review document only** and were never migrated to
`docs/IDEAS.md`:

- Type hints on the public API surface
- Split `dignities/accidental.py`
- Pars Fortuna and Syzygy in default object list (open question)
- `AccidentalDignity.getScoreProperties` rule extraction
- Per-factor unit tests for `temperament.py` and `accidental.py`

(One — `_DualAccess` removal in 1.0 — is implicitly covered by the
existing `camelCase → snake_case sweep` IDEAS entry.)

`IDEAS.md` is the canonical "deferred work" parking lot per project
convention. The review listing items but not migrating them means
those items are easier to lose track of. Suggest a single
documentation pass to migrate them. Mechanical, no judgment calls.

### N2. `swisseph.fixstar2_ut` may have a similar parsing cost — needs investigation, not action

`mayaastrolib/ephem/swe.py::sweFixedStar` calls
`swisseph.fixstar2_ut(star, jd)` on every fixed-star access. Like
`fixstar2_mag`, this likely parses `fixstars.cat` per call — but
unlike `fixstar2_mag`, the result depends on `jd` and so a naïve
`@functools.cache` keyed on `(star, jd)` only helps for repeated
queries at the *same* date. Caching the catalog-lookup portion
separately from the date-dependent precession/proper-motion
correction would help, but requires deeper pyswisseph internals
knowledge.

**In what scenario does this matter, and to whom?** Niche — only
hits consumers who call `getFixedStars()` once per chart in a
batch, and only past the per-star-mag savings already delivered by
Task 016. Defer; surface to IDEAS.md if anyone reports the cost.

### N3. `LIST_VEDIC_DEFAULT` currently produces tropical positions

The constant added in Task 009 selects the seven visible planets
plus Rahu/Ketu — but doesn't apply ayanamsa, so charts built with
`Chart(date, pos, IDs=const.LIST_VEDIC_DEFAULT)` today produce
tropical longitudes for those planets. The constant is honest —
it just specifies *which* planets — but a Vedic-curious user could
assume sidereal handling.

This is actually a correct *current* state given Phase 2 hasn't
shipped, but worth flagging in the Phase 2 readiness section
below as a documentation update opportunity (not a bug).

## Phase 2 readiness

Per-module assessment of how easily the codebase accommodates
sidereal / Vedic features. **Bottom line: ready to start.** No
breaking-API change required.

### Architectural seams that already help

- **`Chart.is_symbolic` / `symbolic_kind`** (Task 010) — generalised
  from "profection" but designed to extend. A sidereal natal chart
  isn't symbolic, but a Vedic *navamsa* (D9 divisional chart) is —
  the existing flag would carry naturally.
- **`Object.with_longitude(lon, *, preserve_speed=False)`**
  (Task 010) — exactly the right primitive for ayanamsa shifting.
  Apply ayanamsa at chart construction by computing
  `obj.with_longitude(obj.lon - ayanamsa_value, preserve_speed=True)`
  for each planet.
- **Layered ephem stack** (`swe.py` → `eph.py` → `ephem.py`) —
  ayanamsa belongs at `swe.py`. One module to touch.

### Tropical hardcoding is small and localised

`mayaastrolib/ephem/swe.py:69` calls
`swisseph.calc_ut(jd, sweObj)` with no flags — implicitly
`SEFLG_SWIEPH` only. Same shape at `:82` (`sweObjectLon`) and the
fixed-star / houses entry points. The Phase 2 work at the swe
layer is:

1. Add a module-level `SID_MODE` (default tropical / off)
2. Expose `swe.setSidMode(mode)` paralleling the existing
   `swe.setPath`
3. Have `sweObject` / `sweObjectLon` / `sweFixedStar` / `sweHouses`
   read `SID_MODE` and pass `SEFLG_SIDEREAL` when set
4. Call `swisseph.set_sid_mode(mode)` once when `setSidMode` is
   called

**Total surface change: ~20 LOC in `swe.py`** plus a Chart-level
`zodiac=` / `ayanamsa=` kwarg that threads through. Not a
redesign.

### Open question for Phase 2 design

Should sidereal mode be a **per-`Chart` parameter** (calling
`swisseph.set_sid_mode` per construction) or a **module-level
configuration** (called once at app startup)? The pyswisseph C
state is process-global, so per-chart mode-switching is fine for
single-threaded use but creates a thread-safety pitfall that's
similar to the `setTerms`/`setFaces` issue Task 008 fixed.

This is the actual architectural question to settle before
shipping any sidereal API. Not a blocker; just a decision the
Phase 2 spec needs to make explicitly.

### `LIST_VEDIC_DEFAULT` documentation

When sidereal lands, update `docs/OBJECT-LISTS.md` to clarify
that `LIST_VEDIC_DEFAULT` selects the *bodies* a Vedic chart
needs but doesn't itself trigger sidereal mode — that's a
separate `zodiac=` kwarg.

## Suggested next moves

Per the constraints (cap of 3, evidence-based, not duplicating
IDEAS):

### 1. Migrate parent-review's Future Considerations to IDEAS.md

**Why:** New finding N1 above. The five orphaned items are
non-trivial work that should be visible in the canonical parking
lot. Mechanical cleanup, ~10 minutes.

### 2. Phase 2 spike: ayanamsa at the swe layer

**Why:** The codebase is ready; the spike just needs to confirm
the per-Chart vs module-level decision (see Phase 2 readiness §3
above) before the sidereal API gets named. Small, focused, and
unblocks the headline goal.

### 3. (Optional, only if Phase 2 work isn't started immediately)
Doc-update on `LIST_VEDIC_DEFAULT`

**Why:** New finding N3. Until ayanamsa lands, the constant is
honest but easy to misread. A two-line note in
`docs/OBJECT-LISTS.md` removes the trap. Five-minute fix; only
worth doing if Phase 2 is more than a session away.

## Future considerations

Items surfaced by this re-review that aren't worth elevating but
should be visible:

- **`fixstar2_ut` per-call cost** (finding N2) — investigate if any
  consumer reports batch-fixed-star cost.
- **Per-factor unit tests for `temperament.py` and `accidental.py`**
  — carry over from parent review; small, low priority.
- **`AccidentalDignity.getScoreProperties` rule extraction** —
  carry over from parent review.

The remaining parent-review items (file-size watch, type hints,
splitting `accidental.py`) get migrated into IDEAS as part of
Suggested next move #1.

---

*Re-review at commit `743e538`. Generated locally; not committed at
write time. Any remaining open items are tracked either above or in
`docs/IDEAS.md` after suggested move #1 lands. The library has
materially improved since 2026-05-08 — closure rate on the parent
review's concrete tasks is 3/3.*

## Project Brief Delta — mayaastrolib

**Generated:** 2026-05-11
**Parent brief:** `docs/PROJECT-BRIEF-2026-05-08.md` (read that first; this is a 3-day delta, not a standalone)
**Branch at write time:** `task-followup-review` (post-Task 016)
**Commits since parent:** 21 (master last touched ≥3 days ago; recent work all on `development` + `task-followup-review`)

---

### What shipped since 2026-05-08

Three tasks, in order:

| Task | Headline | Public surface | Evidence |
|---|---|---|---|
| **014** Golden fixtures | Skyfield-anchored ±2′ planet-position tests for Einstein, Kahlo, Amundsen + self-consistency invariants (houses sum to 360°, profected charts have `None` speed, etc.). High-latitude Placidus chart held without `expectedFailure`. | None (test infra). `skyfield>=1.46` added to `[dev]` only. `LICENSING.md` at repo root. | `tests/golden/` (5 files); commits `bbcfd99 → e28bb07` |
| **015** GeoPos validation | `GeoPos.__init__` raises `ValueError` on lat ∉ [-90, 90] or lon ∉ [-180, 180] after `toFloat()` coercion. Closes the silent-bad-chart bug from the platform review. | Behaviour change: previously-silent bad input now raises. 15 regression tests. | `mayaastrolib/geopos.py:79-86`; `tests/test_geopos_validation.py`; commits `f21f9b4`, `fbab377` |
| **016** fixstar_mag cache | `swisseph.fixstar2_mag` lookups memoised at module level via `@functools.cache` on private `_fixstar_mag`. **144× measured speedup** on a 35-star pass. | None (internal wrapper). | `mayaastrolib/ephem/swe.py`; `tests/test_fixstar_mag_cache.py`; commits `96f3bce`, `57a5fc8` |

Plus: a written **re-review** (`docs/REVIEW-2026-05-08-followup.md`, commit `65c2472`) tracking closure of every parent-review finding and flagging new ones. Not yet committed to PROJECT-LOG beyond entry `4b185d3`.

### State changes against parent brief

The parent brief's "tech stack" and "architecture" sections still describe the codebase accurately. The only numbers that shifted:

| Metric | 2026-05-08 | 2026-05-11 | Source |
|---|---:|---:|---|
| Test files | 19 | **29** | `find tests -name 'test_*.py' \| wc -l` (+golden/ + 015 + 016) |
| Tests passing | 88 | **215** | Per CLAUDE.md "Current codebase state" |
| Coverage | ~88% | ~88% | Unchanged — new code is well-covered; the previously-uncovered helper paths in `geopos.py` (`toList`, `toString`, `__str__`) remain uncovered |
| `geopos.py` coverage | 69% | **72%** | Lower than the predicted 90%+ — Task 015 added validation paths but didn't backfill pre-existing helper coverage. Documented honestly in Task 015's PROJECT-LOG entry. |
| Open deprecation paths | 8 | 8 | Tasks 014–016 added none |
| Known bugs | 1 (GeoPos) | 0 | KNOWN-BUGS.md "Resolved" entry added |

### Parent brief's "Gaps & Risks" — closure status

| Parent gap | Status |
|---|---|
| (1) Vedic/sidereal unification not started | **Materially unchanged, but unblocked.** Re-review's Phase 2 readiness section concludes "start now, no API redesign required" — the tropical hardcoding lives in ~20 LOC at `mayaastrolib/ephem/swe.py:69-82` (no flag passed to `swisseph.calc_ut`). The Task 010 primitive `Object.with_longitude(lon, *, preserve_speed=True)` is exactly the right ayanamsa-shift primitive. The open architectural question is **per-Chart vs module-level sidereal mode** (pyswisseph C state is process-global → same thread-safety pitfall Task 008 fixed). Settle before naming the API. |
| (2) Type hints, mypy strictness, golden tests aspirational | **Half closed.** Golden tests now exist (`tests/golden/`, 10 test methods / 57 subtests). Type hints on the public API surface and mypy strictness are unchanged — still on the queue. |
| (3) PyPI release blocked on housekeeping | Unchanged. Same blockers (camelCase sweep, property-method shim removal, `pyproject.toml` author/maintainer identity for upload). The `0.4.0` release story is now stronger (golden tests + GeoPos validation + 144× fixed-star speedup + Datetime ergonomics + thread-safe dignities) but the cleanup work is still pending. |

### Parent brief's "Suggested next moves" — closure status

| Parent suggestion | Status |
|---|---|
| Sequence and start the sidereal/Vedic spike | **Open. Unblocked.** Closures (1)(2)(3) below removed the prerequisites. Phase 2 readiness analysis lives in `docs/REVIEW-2026-05-08-followup.md` §"Phase 2 readiness". |
| Stand up `tests/golden/` with 2–3 reference charts | **CLOSED** (Task 014). Three charts, ±2′ tolerance, Skyfield-anchored. |
| Add type hints to public API surface | **Open.** Untouched. |

### New findings (from the re-review, not parent brief)

1. **N1 — process gap: parent review's "Future considerations" not migrated to `docs/IDEAS.md`.** Five items (type hints, splitting `accidental.py`, Pars Fortuna / Syzygy default-list question, `getScoreProperties` rule extraction, per-factor unit tests for `temperament.py` / `accidental.py`) live only in `REVIEW-2026-05-08.md`. Mechanical cleanup, ~10 minutes; recommended.
2. **N2 — `swisseph.fixstar2_ut` may have a parallel parsing cost** to the one Task 016 just fixed for `fixstar2_mag`. The result depends on `jd`, so a naïve cache only helps repeated queries at the same date. Investigate if anyone reports batch-fixed-star cost. Defer.
3. **N3 — `LIST_VEDIC_DEFAULT` produces tropical positions today.** The constant is honest (it just names the bodies), but a Vedic-curious user could assume sidereal handling. Two-line note in `docs/OBJECT-LISTS.md` removes the trap. Only worth doing if Phase 2 is more than a session away.

### Suggested next moves (delta-only ranking)

Refreshed against the new state:

1. **Phase 2 spike — ayanamsa at the `swe.py` layer.** *Impact: high. Effort: medium.* The headline goal of the fork. Codebase is ready (3/3 parent closures + golden-test safety net). Settle the per-Chart-vs-module-level decision first; then a ~20 LOC change in `swe.py` plus a Chart `zodiac=` / `ayanamsa=` kwarg. The first Vedic golden chart (e.g. Lahiri-ayanamsa-shifted Krishnamurti or a published BV Raman example) is the natural anchor.
2. **Migrate review "Future considerations" into `docs/IDEAS.md`.** *Impact: low (process hygiene). Effort: trivial.* Finding N1. ~10 minutes. Worth doing before Phase 2 starts so the parking lot is canonical.
3. **Type hints on the public API surface** (`chart.py`, `object.py`, `datetime.py`, `geopos.py`, `aspects.py`). *Impact: medium. Effort: low.* Last remaining piece from the parent brief's #3 suggestion. Pre-PyPI hygiene; gives Claude-Code tool-call consumers an accurate API description. Defer behind Phase 2 only if Phase 2 starts immediately.

### What hasn't changed (re-confirmed)

- Engineering discipline still the standout. Three more tasks, three more journal entries, three more pre-completion checklist passes. Every commit lines up with a planned task.
- Security surface still clean. No new network deps (Skyfield is dev-only). No `eval`/`exec`/`subprocess` added.
- Performance baseline ~unchanged: 0.139 ms/chart at `743e538` vs 0.124 ms/chart at `a5bcc92` (within noise; no regression).
- Code-quality watch list unchanged: `dignities/accidental.py` (480 LOC, 47 methods, `getScoreProperties` at 88 LOC), `chart.py` (420 LOC + small growth from new methods).

---

*Delta only; parent brief at `docs/PROJECT-BRIEF-2026-05-08.md` is still the canonical full snapshot. Revisit both when Phase 2 lands or before a `0.4.0` PyPI tag, whichever comes first.*

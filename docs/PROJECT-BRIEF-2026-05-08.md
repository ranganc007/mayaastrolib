# Project Brief — mayaastrolib

**Generated:** 2026-05-08
**Audience:** engineer (default)
**Branch:** development
**Methodology:** 4-phase project comprehension (`~/.claude/skills/project-comprehension/SKILL.md`)

---

## Elevator pitch

`mayaastrolib` is a Python 3.10+ astrological calculation engine — a modernisation fork of the abandoned `flatangle/flatlib` — that pairs a Swiss-Ephemeris-backed pure-calculation core with a clean, typed, async-friendly API designed for web backends and AI tool calls. Its eventual differentiator is unifying Western (tropical) and Vedic (sidereal) astrology behind a single coherent API, consolidating work currently scattered across multiple half-finished forks.

## Tech stack

| Category          | Technology                | Version          | Purpose                                                        |
|-------------------|---------------------------|------------------|----------------------------------------------------------------|
| Language          | Python                    | 3.10–3.12 (CI)   | Runtime; local dev on 3.14.3                                   |
| Build backend     | setuptools + pyproject    | PEP 621          | Single source of truth for metadata, deps, tool config         |
| Ephemeris         | pyswisseph                | ≥2.10.3.2        | C bindings to Swiss Ephemeris — only runtime dep               |
| Lint/format       | ruff                      | (dev extras)     | line-length 100, rules E/F/I/B/A/UP, UP031 deferred            |
| Type checker      | mypy                      | (dev extras)     | `ignore_missing_imports`; warnings tolerated, errors not       |
| Tests             | pytest + pytest-cov       | (dev extras)     | 19 test files, 88 tests, target ≥80% coverage                  |
| CI                | GitHub Actions            | `test.yml`       | Matrix Python 3.10/3.11/3.12; ruff + pytest + coverage         |
| Compatibility     | `flatlib` shim package    | in-tree          | `import flatlib …` still works with `DeprecationWarning`       |

**Code size:** ~5,667 LoC in `mayaastrolib/` across 39 Python files (top-level + `dignities/`, `ephem/`, `predictives/`, `protocols/`, `tools/`).

## Architecture

Pure-calculation library, no network, no I/O outside the bundled ephemeris files in `mayaastrolib/resources/swefiles/`. Single dataflow:

```
User input ──► Datetime + GeoPos ──► Chart(date, pos, hsys=, IDs=)
                                         │
                                         ├─► ephem.ephem.getObjectList ─► ephem.eph.getObject ─► ephem.swe.sweObject ─► swisseph (C)
                                         └─► ephem.ephem.getHouses     ─► ephem.eph.getHouses  ─► ephem.swe.sweHouses
                                                                          │
                                                                          ▼
                                                  ObjectList / HouseList / GenericList
                                                                          │
                                                                          ▼
                                                  _link_objects_to_houses ─ stamps obj.house and house.objects
```

Layered ephemeris stack: `swe.py` (raw pyswisseph wrapper) → `eph.py` (mid-layer returning plain dicts) → `ephem.py` (façade returning typed flatlib objects, the layer `Chart` actually uses). This is the cleanest seam in the codebase and the natural insertion point for the upcoming sidereal/Vedic unification.

Downstream features (`dignities/`, `predictives/`, `protocols/`, `tools/`) all consume the `Chart` and the static tables in `props.py` and `dignities/tables.py`; they do not touch the ephemeris directly.

## Key components

| Module                                | Purpose                                                                                              | Notable files |
|---------------------------------------|------------------------------------------------------------------------------------------------------|---------------|
| Top-level (`chart`, `object`, `lists`, `datetime`, `geopos`, `angle`, `aspects`, `const`, `props`, `utils`) | Public-facing model: `Chart`, `Object/House/FixedStar`, `Datetime`, `GeoPos`, angle math, aspect computation, sign/planet constants. | `mayaastrolib/chart.py`, `mayaastrolib/object.py`, `mayaastrolib/datetime.py` |
| `mayaastrolib/_compat.py`             | `property_with_method_compat` decorator: lets newly-converted properties still respond to `obj.movement()` with a `DeprecationWarning`. Forwards `__eq__`, `__bool__`, `__lt__`, etc. so callsites need no edits. Slated for removal in 1.0. | `mayaastrolib/_compat.py` |
| `mayaastrolib/ephem/`                 | Swiss Ephemeris stack (4 layers). `swe.py` was patched in Task 004 to fix the `backward=` → `backwards=` keyword renamed by pyswisseph 2.x. | `ephem/swe.py`, `ephem/eph.py`, `ephem/ephem.py`, `ephem/tools.py` |
| `mayaastrolib/dignities/`             | Essential + accidental dignities and the static tables (Egyptian / Tetrabiblos / Lilly terms; Chaldean / Triplicity faces). Task 008 made `essential.py` thread-safe via `terms_variant`/`faces_variant` kwargs. | `dignities/essential.py`, `dignities/tables.py`, `dignities/accidental.py` |
| `mayaastrolib/predictives/`           | Solar returns, profections, primary directions (Ptolemy/Placidus semi-arc). | `predictives/returns.py`, `predictives/profections.py`, `predictives/primarydirections.py` |
| `mayaastrolib/protocols/`             | Interpretive protocols — almutem, behavior, temperament. Smoke-tested only.                          | `protocols/almutem.py`, `protocols/behavior.py`, `protocols/temperament.py` |
| `mayaastrolib/tools/`                 | Arabic parts, chart dynamics, planetary time. Smoke-tested only.                                     | `tools/arabicparts.py`, `tools/chartdynamics.py`, `tools/planetarytime.py` |
| `flatlib/__init__.py` (shim)          | Backwards-compatible alias package. Re-exports everything from `mayaastrolib` and stitches `sys.modules['flatlib.<sub>']` to the new submodules so both `import flatlib.X` and `from flatlib.X import Y` resolve. | `flatlib/__init__.py` |
| Tests (`tests/`)                      | 19 files, 88 passing, including a 3-thread parametric regression for dignities thread-safety and an eclipse keyword-arg regression. | `tests/test_dignities_thread_safety.py`, `tests/test_eclipses.py`, `tests/test_chart_house_links.py` |
| Docs                                  | `CONTRIBUTION-PLAN.md` (sequenced tasks 001–010 with definitions of done), `PROJECT-LOG.md` (running journal per task), `RECON.md` (Task 001 baseline), `KNOWN-BUGS.md`, `RUFF-DEBT.md`, `IDEAS.md`, `PROPERTY-MIGRATION.md`, `FORK-RATIONALE.md`. | `docs/` |
| CI                                    | `.github/workflows/test.yml` — matrix 3.10/3.11/3.12, runs `ruff format --check`, `ruff check`, `pytest`, then coverage report. | `.github/workflows/test.yml` |

## Strengths

1. **Engineering discipline is the headline strength.** The repo has a written contribution plan with numbered tasks (001–008 done, 009–010 staged), a per-task journal in `PROJECT-LOG.md`, a pre-completion checklist in `CLAUDE.md` (ruff + mypy + pytest + coverage + log + changelog), per-task venvs, and `IDEAS.md` to capture out-of-scope work without drifting. Every recent commit lines up with one of those tasks. This is rare for a 2-month-old fork of an abandoned project.

2. **Migration is treated as a first-class engineering problem, not a rename.** Two non-trivial migrations are live: (a) `flatlib/` → `mayaastrolib/` is shimmed via `sys.modules` aliases so both module-import and from-import paths work; (b) several methods (`Object.movement`, `House.num`, etc.) were converted to properties via `_compat.property_with_method_compat`, a custom dual-access wrapper that fixes a real bug (`if obj.movement:` was always truthy because the bound method had non-None identity) while keeping the legacy callsites green with a `DeprecationWarning`. Both have a documented 1.0 removal target. Evidence: `mayaastrolib/_compat.py:14-99`, `flatlib/__init__.py:42-58`, `docs/PROPERTY-MIGRATION.md`.

3. **Tests cover the real bugs that hid in the ancestor.** `tests/test_eclipses.py` is a regression for the pyswisseph 2.x keyword rename (`backward=` → `backwards=`). `tests/test_dignities_thread_safety.py` runs three threads with three different terms variants in parallel and asserts result-set determinism — a real concern given the pre-Task-008 module-level globals. `tests/test_chart_house_links.py` guards the property-truthiness fix. These aren't synthetic; they encode lessons learned.

## Gaps & risks

1. **Stated goal #2 (Vedic/sidereal unification) hasn't started yet.** Phase 0 (modernisation, tasks 001–005) plus a few ergonomics tasks (006–008) are in. The Phase-2 sidereal work — the actual differentiator from upstream — is unscoped beyond a one-line entry in `CONTRIBUTION-PLAN.md`. Risk: the project is currently a *better-maintained flatlib*, not yet *flatlib + Vedic*. Until a sidereal task is sequenced, the value proposition isn't materially different from upstream's revival.
   *Evidence:* `docs/CONTRIBUTION-PLAN.md` Phase 2 placeholder; no sidereal modules in `mayaastrolib/`.
   *Impact:* High for project goal; low for current users.

2. **Type hints, mypy strictness, and golden tests are still aspirational.** `CLAUDE.md` mandates type hints on new code and golden charts in `tests/golden/`, but: the live source files inspected here (`chart.py`, `object.py`, `datetime.py`, `dignities/essential.py`) carry no `sig`-style annotations, mypy runs with `ignore_missing_imports` and tolerates warnings, and `tests/golden/` does not exist on disk yet. The 88 passing tests are structural/smoke; there is no astronomical-correctness anchor.
   *Evidence:* `mayaastrolib/chart.py` (no annotations); `pyproject.toml:80-83` (mypy lax); `find tests -type d` shows no `golden/` directory.
   *Impact:* Medium. A future Vedic refactor without golden charts will be hard to verify safely.

3. **Public-API stability and a PyPI release are blocked on housekeeping.** `README.md` says "A PyPI release will follow once the API surface stabilises", and the codebase carries known stylistic debt slated for a "camelCase → snake_case major-version cleanup" (`docs/RUFF-DEBT.md`) plus the property/shim removals planned for 1.0. Until those land, downstream consumers (the sibling `mayaastro-demo` Flask app per the parent CLAUDE.md) are pinned to an editable install. The original-author email in `pyproject.toml` `authors = …` (preserved for copyright reasons) will also matter when uploading to PyPI — `maintainers` is correct but the upload identity needs review.
   *Evidence:* `README.md:42-43`; `docs/RUFF-DEBT.md:14-17`; `pyproject.toml:13-18`.
   *Impact:* Medium. Blocks adoption beyond the local workspace.

## Suggested next moves

Prioritised by impact / effort. The first recommendation is a leverage move (it unblocks Vedic work); the rest are smaller wins.

1. **Sequence and start the sidereal/Vedic spike.** *Impact: high. Effort: medium-high.* Pick one Vedic operation (e.g. Lahiri ayanamsa applied to planetary longitudes) and land it as Task 009 with a golden test sourced from a known Vedic chart. This converts the project's stated goal into a measurable inch of progress, anchors the eventual Phase-2 design, and forces an architectural decision (where does ayanamsa live — `Chart`, `Datetime`, or a per-call kwarg?) before the API surface is too set to change. The existing layered ephemeris (`swe → eph → ephem`) makes this less invasive than it sounds: the swap can be implemented at the `eph.getObject` layer.

2. **Stand up `tests/golden/` with 2–3 reference charts before any further feature work.** *Impact: high. Effort: low.* Pick public ephemeris reference points (astro.com, Astro-Databank), encode positions with the ±2 arc-min / ±5 arc-min tolerance specified in `CLAUDE.md`, and gate CI on them. This is a one-evening task that pays back permanently — every subsequent refactor (sidereal, type hints, ephem rewrite) is verified against astronomy rather than against itself.

3. **Add type hints to the public API surface (`chart.py`, `object.py`, `datetime.py`, `geopos.py`) in one task.** *Impact: medium. Effort: low.* These files account for most of the user-visible signatures. Adding `from __future__ import annotations` plus signatures (without flipping mypy to strict yet) gives IDE users and Claude Code tool-call consumers an accurate API description, satisfies the `CLAUDE.md` "type hints required on new code" rule for the next contributor, and produces a typed surface ready for a 0.4.0 PyPI release.

### Lower-priority but worth queueing

- **Cut a `0.4.0` PyPI release** once (1) and (3) land. The `flatlib` shim plus `Datetime` ergonomics plus thread-safe dignities is already a strong release-note story.
- **Convert at least one `recipes/*.py` script into a runnable example or doctest.** Recipes are the closest thing to user-facing docs; right now they're stale and untested.
- **Replace the `setFaces`/`setTerms` callsites in `recipes/` with the new kwarg API** before the 1.0 removal lands, so the deprecation warning doesn't surprise anyone reading the recipes.

---

*This brief is a snapshot at 2026-05-08. The codebase ships an excellent `PROJECT-LOG.md` for ongoing work — prefer that for week-to-week status; revisit this brief when Phase 2 (Vedic) starts or before a PyPI release.*

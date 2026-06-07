# Project Brief: mayaastrolib

**Generated:** 2026-06-06
**Focus:** all
**Audience:** engineer
**Supersedes:** `docs/PROJECT-BRIEF-2026-05-08.md` + `docs/PROJECT-BRIEF-2026-05-11-delta.md` (both now stale — they describe the codebase at Task 016 / 215 tests, before the entire Vedic subsystem landed). This is a full standalone refresh, not a delta.

> **Note on git dates:** `HEAD` is dated 2026-05-11, but the last brief was written *earlier that same day* at Task 016. Tasks 017–038 (the 12-module Vedic package + the public-API type-hint pass) were all committed afterward. So although `git log` shows no commits "since" the last brief by date, the content has roughly doubled (215 → 553 tests).

---

## Elevator Pitch

`mayaastrolib` is a typed, modern-Python (3.10+) fork of the abandoned `flatlib` that unifies Western/tropical and Vedic/sidereal astrology behind one Swiss-Ephemeris-backed calculation API. It targets developers embedding chart math in web apps, FastAPI services, and AI tooling — pure calculation, no UI, no interpretations, no network.

## Tech Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Language | Python | ≥3.10 (3.12 target; 3.14 local) | Typed, modern-Python library |
| Ephemeris | pyswisseph (Swiss Ephemeris) | ≥2.10.3.2 | The *only* runtime dependency — all astronomy |
| Packaging | setuptools + PEP 621 | `pyproject.toml` only | Single source of truth; no `setup.py`/`requirements.txt` |
| Formatter | ruff format | 0.15.x, line-length 100 | Style (clean) |
| Linter | ruff check | rules `E,F,I,B,A,UP` (UP031 deferred) | Lint (clean) |
| Type checker | mypy | `ignore_missing_imports` | 2-error baseline (both pre-existing) |
| Tests | pytest + pytest-cov | — | 553 tests, 51 files, 94.12% coverage |
| Golden tests | skyfield | ≥1.46 (dev-only) | Independent ±2′ astronomical anchor |
| CI | GitHub Actions | matrix 3.10/3.11/3.12 | format + lint + pytest + coverage gate |
| Version | — | 0.3.0 (Beta) | Pre-1.0; API still stabilising |

## Architecture

A three-layer calculation stack with a thin public object model on top, plus an optional Vedic extension package that reuses the same stack.

### Data Flow

```
User input                Calculation stack                 Public objects
──────────                ─────────────────                 ──────────────
Datetime(date,time,utc) ─┐
GeoPos(lat,lon) ─────────┤→ ephem/ephem.py (orchestration)
Chart(date,pos,**kw) ────┘    └→ ephem/eph.py (zodiac/ayanamsa logic)
                                   └→ ephem/swe.py (pyswisseph C bridge)
                                        └→ Swiss Ephemeris .se1 files
                              ↓
                        Chart.objects / .houses / .angles
                        (ObjectList / HouseList / GenericList)
                              ↓
                        chart.get(ID) → Object | House | angle
```

- **Entry:** `Chart.__init__` (`chart.py:39`) validates `zodiac`/`ayanamsa` against `const.LIST_*`, then calls `ephem.getObjectList` and `ephem.getHouses`, and finally `_link_objects_to_houses()` which stamps `obj.house` and `house.objects` (Task 006 property migration).
- **Zodiac switch:** a single kwarg (`zodiac=ZODIAC_SIDEREAL`, `ayanamsa=…`) threads down to `swe.py`, where sidereal calls take a different path (`_sidereal_calc_ut` / `_sidereal_houses_ex`, `swe.py:73-92`). Tropical is the default and unchanged.
- **Output:** charts expose lists; `chart.get(ID)` dispatches by `const.LIST_HOUSES`/`LIST_ANGLES` membership (not string-prefix matching — Task 011).

### Key Patterns

- **Process-global C state, lock-guarded.** pyswisseph's `set_sid_mode` mutates global state; the `(set_sid_mode, calc_ut)` pair is wrapped in `_SIDEREAL_CALC_LOCK` (`swe.py:70-92`) so concurrent sidereal computations for different ayanamsas can't interleave. Same class of thread-safety fix as Task 008's `dignities.essential`.
- **Symbolic vs real charts.** `Chart.profected()` returns a deep-copied chart with `is_symbolic=True` and `lonspeed=None` (so `isRetrograde()` etc. return `None` rather than lying); `Chart.solarReturn()` returns a *real* ephemeris chart. Clear separation at `chart.py:258-399`.
- **Immutable relocation.** `Object.with_longitude(lon, *, preserve_speed=False)` (Task 010) is the functional primitive underneath profections, antiscia, and the ayanamsa shift — no in-place `relocate()` in new code.
- **Optional, zero-cost Vedic.** `mayaastrolib/vedic/` is imported only on demand; Western-only users pay nothing (`vedic/__init__.py`).
- **flatlib compat shim.** `flatlib/` still exists, re-exporting `mayaastrolib` with a `DeprecationWarning`; slated for removal in 1.0.

## Key Components

### Core object model
- **Purpose:** Charts, objects, houses, angles, aspects, datetime, geoposition.
- **Key files:** `chart.py`, `object.py`, `aspects.py`, `datetime.py`, `geopos.py`, `angle.py`, `const.py`, `lists.py`, `_compat.py`.
- **Dependencies:** `ephem` layer.
- **Notes:** `geopos.py` + `datetime.py` are fully type-hinted (Tasks 037/038); `aspects.py`/`chart.py`/`object.py` deferred — their `__dict__.update` / `_compat`-decorated dynamic-attribute patterns surface ~30 mypy errors without a deliberate refactor.

### Ephemeris stack
- **Purpose:** Translate (date, position, zodiac, ayanamsa) into longitudes/speeds/houses.
- **Key files:** `ephem/ephem.py` (orchestration), `ephem/eph.py` (zodiac logic), `ephem/swe.py` (C bridge), `ephem/tools.py`.
- **Notes:** `swe.py` holds `SWE_OBJECTS`/`SWE_HOUSESYS` maps and the sidereal plumbing; `_fixstar_mag` is `@functools.cache`-memoised (Task 016, 144× speedup).

### Dignities / Protocols / Predictives / Tools
- **Purpose:** Essential + accidental dignity scoring, temperament/almuten protocols, solar returns / profections / primary directions, Arabic parts, planetary hours.
- **Key files:** `dignities/`, `protocols/`, `predictives/`, `tools/`.
- **Notes:** `dignities.essential` is the most-imported module (dep graph is a clean DAG). `accidental.py` 100% / `temperament.py` 99% covered after Task 033. `getScoreProperties` table-driven since Task 034.

### Vedic extension (`mayaastrolib/vedic/`)
- **Purpose:** The full Jyotisha layer — 12 modules, 3,603 LOC.
- **Key files:** `ayanamsa.py` (Lahiri/KP/Raman/Fagan-Bradley), `nakshatras.py`, `divisional.py` (all 16 BPHS vargas), `dasha.py` (Vimshottari MD/AD/Pratyantar), `ashtakavarga.py` (BAV/SAV + shodhana variants + kakshya), `sadesati.py`, `upagrahas.py`, `tajika.py` + `tajika_bala.py` + `tajika_aspects.py` (annual charts, Sahams, Harsha/Panchavargiya Bala, Ithasala/Isharafa/Nakta), `kp.py` (249-row sub-lord table, sub-sub-lord, horary, Ruling Planets), `yogas.py` (Pancha Mahapurusha + Raja/Dhana/Vipareeta/Neecha-Bhanga + lesser yogas + weighted strength).
- **Notes:** Encodes classical dignity tables *fresh* (not the Western `dignities/tables.py`). Each module tested independent of the ephemeris where possible.

### Tests
- **Purpose:** Two mandatory layers — structural (`tests/unit`-style `test_*.py`) and golden (`tests/golden/`).
- **Key files:** 48 `test_*.py` at `tests/` root + `tests/golden/` (Skyfield-anchored Einstein/Kahlo/Amundsen at ±2′, plus self-consistency invariants: houses sum to 360°, cusps ordered, profected charts have `None` speed).
- **Notes:** 553 tests + 87 subtests, all passing; 94.12% coverage against an 80% CI floor.

## Strengths

1. **Genuinely high test discipline for a solo astrology lib.** 553 tests / 51 files / **94.12%** coverage, *plus* an independent astronomical oracle: `tests/golden/` anchors positions against Skyfield (a different ephemeris) at ±2 arcmin. This is the rare astrology library whose correctness is verifiable, not asserted. `accidental.py` and `temperament.py` — historically smoke-only — are now 100%/99%.
2. **Clean, single-dependency, modern-packaging foundation.** One runtime dep (`pyswisseph`), `pyproject.toml` as the sole config source, ruff format/check both clean across 121 files, CI matrix on 3.10–3.12, dependency graph a cycle-free DAG. The fork actually delivered on its "modernise" goal: `setup.py`/`requirements.txt`/`README.rst` all deleted.
3. **Coherent tropical+sidereal unification.** The headline fork goal is real and shipped: one `Chart(zodiac=…, ayanamsa=…)` switch threads cleanly through a three-layer ephem stack, the process-global pyswisseph state is correctly lock-guarded (`swe.py:70-92`), and predictives (`solarReturn`/`profected`) were made zodiac-aware in Task 027 rather than left silently wrong on sidereal charts.

## Gaps & Risks

1. **Public-API type-hint pass is ~40% done and structurally blocked on the core classes.**
   - *Evidence:* `geopos.py`/`datetime.py` typed; `aspects.py`/`chart.py`/`object.py` deferred because `Aspect`/`AspectObject` use `self.__dict__.update(...)` and `Object`/`House` use `_compat`-decorated dynamic attributes — adding signatures surfaces ~30 mypy "no attribute" errors. The README and CLAUDE.md both list "type hints required" as a core principle, so the most-used classes being untyped is a credibility gap.
   - *Impact:* IDE autocomplete and downstream type-checking are weakest exactly where consumers touch the API most (`Chart`, `Object`). mypy can't be tightened past the 2-error baseline until this is done.
   - *Effort to fix:* medium — needs class-level attribute annotations + a small `Aspect.__init__` restructure, not a rewrite.
2. **No PyPI release; install is git-clone-only, and the API is explicitly still moving.**
   - *Evidence:* README: "A PyPI release will follow once the API surface stabilises." Version 0.3.0, Beta. Eight open deprecation paths slated for 1.0 removal (per CLAUDE.md).
   - *Impact:* Every consuming project (e.g. the sibling `mayaastro-demo` editable install) is pinned to a working tree, not a versioned artifact. No reproducible installs, no semver contract for external users yet.
   - *Effort to fix:* small-to-medium — packaging is ready; the blocker is a deliberate API-freeze decision, not tooling.
3. **The Vedic subsystem grew fast and carries documented simplifications that could read as "complete."**
   - *Evidence:* Yoga strength uses accidental-dignity weighting, *not* full six-fold Shadbala (`yogas.py`, Task 035); Panchavargiya Bala uses "simplified component scales" (`tajika_bala.py`, Task 029); `lord_of_year` is a heuristic tally, not the canonical Bala rule; Sahams cover 14 of ~50; KP horary lacks house cusps. All are honestly documented in CLAUDE.md/PROJECT-LOG, but a user reading the API surface alone wouldn't know.
   - *Impact:* Classical-accuracy expectations may be over-met in name, under-met in computation. Low *correctness* risk (it's documented), real *expectation* risk.
   - *Effort to fix:* large (full Shadbala is its own project) — better served by surfacing the simplifications in docstrings/`__doc__` than by implementing now.

## Suggested Next Moves

1. **Finish the public-API type-hint pass on `object.py`/`chart.py`/`aspects.py`.**
   - *Priority:* P1 · *Scope:* medium · *Evidence:* CLAUDE.md "Type-hint pass" note; mypy 2-error baseline can't tighten until done.
   - *Impact:* Closes the biggest stated-vs-actual gap; unlocks `--strict`-ish mypy and real IDE support on the classes consumers use most.
2. **Backfill the 2 standing mypy errors while in the type-hinting headspace.**
   - *Priority:* P2 · *Scope:* small · *Evidence:* `props.py:105` (sum over `list[list[str]]`) and `predictives/primarydirections.py:98` (`SIG_HOUSES` needs annotation) — both shown by `mypy mayaastrolib/`.
   - *Impact:* Gets the type checker to genuine zero, so CI can fail on *new* type errors instead of tolerating a baseline.
3. **Add a docstring "Accuracy / simplifications" note to each Vedic function that approximates a classical formula.**
   - *Priority:* P1 · *Scope:* small · *Evidence:* `yogas.yoga_strength_weighted`, `tajika_bala.panchavargiya_bala`, `tajika.lord_of_year`, `tajika.sahams` (14 of ~50).
   - *Impact:* Moves the honesty that currently lives in PROJECT-LOG into the API surface itself; prevents silent over-trust by API-only consumers. Quick win.
4. **Decide and document the API-freeze line for 1.0, then cut a PyPI 0.4.x.**
   - *Priority:* P2 · *Scope:* medium · *Evidence:* README PyPI deferral; 8 open deprecation paths in `_compat`/aspects/predictives.
   - *Impact:* Gives `mayaastro-demo` and any external user a versioned, reproducible install instead of an editable working tree.
5. **Surface the simplifications list (move 3) into `docs/IDEAS.md` follow-ups as tracked issues, not prose.**
   - *Priority:* P2 · *Scope:* small · *Evidence:* deferred items are currently scattered across PROJECT-LOG entries and CLAUDE.md state notes.
   - *Impact:* Turns "remaining open work" into a pickable backlog rather than tribal knowledge in CLAUDE.md.

## File Map

```
mayaastrolib/                 # repo root (editable install used by mayaastro-demo)
├── mayaastrolib/             # the package (~10.1k LOC)
│   ├── chart.py              # Chart class — entry point, zodiac switch, symbolic/SR charts
│   ├── object.py             # Object/House model (dynamic attrs via _compat — untyped)
│   ├── aspects.py            # Aspect model (__dict__.update — untyped)
│   ├── const.py              # all IDs, LIST_* canonical lists, zodiac/ayanamsa constants
│   ├── datetime.py geopos.py # typed (Tasks 037/038); GeoPos validates lat/lon ranges
│   ├── angle.py lists.py props.py utils.py _compat.py
│   ├── ephem/                # 3-layer stack: ephem.py → eph.py → swe.py (pyswisseph bridge)
│   ├── dignities/            # essential + accidental dignity (most-imported: dignities.essential)
│   ├── predictives/          # solar returns, profections, primary directions
│   ├── protocols/            # temperament, almuten
│   ├── tools/                # arabic parts, planetary time, chart dynamics
│   ├── vedic/                # 12 modules / 3,603 LOC — optional, zero-cost-when-unused
│   │   ├── ayanamsa.py nakshatras.py divisional.py dasha.py
│   │   ├── ashtakavarga.py sadesati.py upagrahas.py
│   │   ├── tajika.py tajika_bala.py tajika_aspects.py kp.py yogas.py
│   └── resources/swefiles/   # Swiss Ephemeris .se1 data
├── flatlib/                  # compat shim — re-exports w/ DeprecationWarning, removed in 1.0
├── tests/                    # 48 test_*.py + golden/ (Skyfield-anchored ±2′ + invariants)
├── docs/                     # CONTRIBUTION-PLAN, PROJECT-LOG, KNOWN-BUGS, REVIEW-*, briefs
├── contrib/ recipes/ prompts/
├── pyproject.toml            # single config source (build, ruff, mypy, pytest, coverage)
├── CLAUDE.md                 # standing session context — authoritative codebase state
├── CHANGELOG.md LICENSING.md README.md
```

## Stats

| Metric | Value |
|--------|-------|
| Python source files (pkg, excl. venvs) | 121 |
| Package LOC (`mayaastrolib/`) | ~10,138 |
| Vedic LOC (subset) | 3,603 (12 modules) |
| Test files | 51 (48 root + 3 golden) |
| Tests | 553 (+ 87 subtests), all passing |
| Coverage | 94.12% (CI floor 80%) |
| Runtime dependencies | 1 (pyswisseph) |
| mypy errors | 2 (pre-existing baseline) |
| ruff format / check | clean (121 files) |
| Version | 0.3.0 (Beta, pre-PyPI) |
| Open deprecation paths (→ 1.0) | 8 |
| Known open bugs | 0 |
| Contributor | solo (Rangan C.) |

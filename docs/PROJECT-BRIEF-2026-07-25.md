# Project Brief: mayaastrolib

**Generated:** 2026-07-25
**Focus:** all
**Audience:** engineer
**Branch:** `development` (== `origin/master`, nothing unpushed)
**Supersedes:** `docs/PROJECT-BRIEF-2026-06-06.md` (15 commits, 3 releases, and a PyPI
publication have landed since; a delta section is at the end)

---

## Elevator Pitch

`mayaastrolib` is a typed, dependency-light Python 3.10+ engine that computes both
Traditional/Western and Vedic (Jyotisha) astrology charts on the Swiss Ephemeris — a
modernised, heavily extended fork of the abandoned `flatangle/flatlib`. It targets
developers embedding chart calculation in web apps, APIs, and AI tooling, not end users
looking at chart wheels.

## Tech Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Language | Python | 3.10 min / 3.12 target | Library runtime; PEP 561 typed (`py.typed` shipped) |
| Ephemeris | `pyswisseph` | ≥2.10.3.2 | The **only** runtime dependency — C Swiss Ephemeris bridge |
| Packaging | setuptools + PEP 621 | `pyproject.toml` only | Single source of truth for build, ruff, mypy, pytest, coverage |
| Lint/format | ruff | line-length 100, `E,F,I,B,A,UP` | Clean across 130 files |
| Types | mypy | `python_version = 3.10` | **Zero errors** across 49 source files |
| Tests | pytest + pytest-cov | — | 664 tests + 230 subtests, 95% coverage, 2.5s wall |
| Independent oracle | Skyfield (dev-only) | ≥1.46 | Golden tests anchor positions against a *different* ephemeris |
| CI | GitHub Actions | 3 workflows | `test.yml` (3.10/3.11/3.12 matrix), `package.yml`, `publish.yml` |
| Distribution | PyPI | 0.5.0 | Published via OIDC Trusted Publishing — no stored token |

## Architecture

A layered pure-calculation library. No network, no I/O beyond reading bundled `.se1`
ephemeris files, no persistence, no UI. Everything is a function of
`(Datetime, GeoPos, options)`.

### Data Flow

```
Datetime + GeoPos + kwargs(hsys, zodiac, ayanamsa, IDs)
        │
        ▼
   Chart.__init__            mayaastrolib/chart.py:66
        │  builds objects / houses / angles, links objects→houses
        ▼
   ephem.ephem  ──▶  ephem.eph  ──▶  ephem.swe  ──▶  pyswisseph (C)
   (chart-level)     (typed dicts)   (raw bridge,     ▲
                                      lock-guarded)   │
                                                 _SWE_LOCK (RLock)
        │
        ├─▶ Western layer: aspects · dignities{essential,accidental} ·
        │                  protocols{temperament,almutem,behavior} ·
        │                  predictives{returns,profections,primarydirections} ·
        │                  tools{arabicparts,planetarytime,chartdynamics}
        │
        ├─▶ Vedic layer (sidereal): vedic/* — 14 modules, 4,341 LOC
        │
        ▼
   Chart.to_dict() / to_json()   ──▶  schema v1 JSON
        │
        ▼
   report.full_report()  /  aio.afull_report()   ← the "front door"
```

### Key Patterns

- **Three-layer ephemeris stack.** `ephem/ephem.py` (chart semantics) → `ephem/eph.py`
  (normalised dicts) → `ephem/swe.py` (the only file that touches `swisseph`). The
  zodiac/ayanamsa switch threads through all three as keyword arguments, so sidereal is
  a parameter rather than a fork of the code.
- **One global lock for a non-thread-safe C library.** `ephem/swe.py:70` defines a single
  module-level `threading.RLock` guarding *every* swisseph entry point. Reentrant because
  `sweFixedStar` nests `_fixstar_mag`. This is what makes the async helpers and thread-pool
  use safe (`docs/CONCURRENCY.md`).
- **Lazy top-level facade.** `mayaastrolib/__init__.py:21` uses module `__getattr__` so
  `import mayaastrolib` never imports swisseph — metadata-only and Western-only consumers
  pay no startup cost, while `mayaastrolib.full_report` still resolves.
- **Versioned serialization contract.** `Chart.to_dict()` emits `schema_version` +
  `meta`/`objects`/`houses`/`angles`/`aspects`, with `dignities=` and `vedic=` as opt-in
  blocks. Every model class (`Object`, `House`, `FixedStar`, `Aspect`) has its own
  `to_dict()`.
- **Deprecate, don't break.** 13 `DeprecationWarning` sites across 7 files
  (`_compat.py`, `object.py`, `aspects.py`, `tools/arabicparts.py`,
  `dignities/essential.py`, `predictives/profections.py`, `flatlib/__init__.py`) keep old
  call shapes alive; all are scheduled for removal at 1.0.
- **Immutability over mutation.** `Object.with_longitude()` replaced in-place
  `relocate()`; symbolic charts (`profected`, `solarReturn`) return new `Chart` objects
  tagged with `is_symbolic` / `symbolic_kind`.
- **Classical-simplification honesty.** Where a Vedic technique is approximated, the
  docstring says so in-line — 17 such notes across `shadbala.py`, `tajika_bala.py`,
  `tajika.py`, `kp.py`, `upagrahas.py`.

## Key Components

### `chart.py` — the entry point
- **Purpose:** `Chart` construction, object/house lookup and linking, serialization,
  and the symbolic-chart techniques (profections, solar returns, primary directions).
- **Key files:** `mayaastrolib/chart.py` (686 LOC, 30 public methods)
- **Dependencies:** `ephem`, `const`, `object`, `aspects`, `predictives`, lazily `vedic`
- **Notes:** Fully type-hinted as of 0.4.0. `to_dict()` at line 155 is now the widest
  public contract in the library.

### `ephem/` — the calculation bridge
- **Purpose:** Everything that talks to Swiss Ephemeris.
- **Key files:** `ephem/swe.py` (266), `ephem/eph.py` (168), `ephem/ephem.py` (212),
  `ephem/tools.py`
- **Notes:** `swe.py` is the single choke point for thread safety and for the
  `@functools.cache` fixed-star magnitude optimisation (144× on bulk star passes).

### `vedic/` — the Jyotisha subsystem (the fork's main addition)
- **Purpose:** Sidereal astrology behind one `Chart(zodiac=..., ayanamsa=...)` switch.
- **Key files:** 14 modules / 4,341 LOC — `yogas.py` (709), `shadbala.py` (645),
  `ashtakavarga.py` (455), `tajika.py` (410), `kp.py` (387), `divisional.py` (361),
  plus `tajika_aspects`, `tajika_bala`, `dasha`, `nakshatras`, `sadesati`, `upagrahas`,
  `ayanamsa`
- **Dependencies:** `chart`, `const`, `angle` — deliberately *not* the Western
  `dignities/tables.py` (Vedic dignity tables are encoded fresh)
- **Notes:** Zero cost when unused. Coverage here is excellent (98–99% on the big
  modules). Four ayanamsas: Lahiri, Krishnamurti/KP, Raman, Fagan-Bradley.

### `report.py` + `aio.py` — the consumption layer (new in 0.5.0)
- **Purpose:** One call from `Datetime` + `GeoPos` to a full serialized report;
  async wrappers so an event loop stays free.
- **Key files:** `mayaastrolib/report.py` (101), `mayaastrolib/aio.py` (64)
- **Notes:** `aio` is a thin `run_in_executor` shim, correct precisely *because* of
  `_SWE_LOCK`. This is the layer a FastAPI/MCP consumer should target.

### `tests/` — the load-bearing part
- **Purpose:** Structural tests (contracts) + golden tests (astronomical truth).
- **Key files:** 54 `tests/test_*.py`; `tests/golden/` with `fixtures.json` (7 reference
  charts), `test_planet_positions.py`, `test_vedic_positions.py`,
  `test_self_consistency.py`
- **Notes:** Golden fixtures are generated from Skyfield, an independent ephemeris, at
  ±2 arcmin. `test_concurrency.py` pins the 8-thread mixed tropical/sidereal result
  byte-for-byte against a serial reference.

### `flatlib/` — compatibility shim
- **Purpose:** `import flatlib` keeps working with a `DeprecationWarning`.
- **Key files:** 6 files. Removed at 1.0.

## Strengths

1. **Verification is genuinely independent, not self-referential.** The golden suite
   (`tests/golden/fixtures.json`, 7 charts spanning 1875–1961, both hemispheres, Pacific
   longitudes) is generated from **Skyfield**, a completely separate ephemeris
   implementation, and asserted at ±2 arc-minutes in both tropical and sidereal frames.
   For an AI-authored codebase — which the README states plainly at line 88 — this is the
   right load-bearing control, and it is actually in place rather than aspirational.
   Verified this session: `664 passed, 230 subtests, 95% coverage, 2.53s`.

2. **The engineering hygiene is real and currently green.** Verified this session, not
   taken from docs: `ruff format --check` → 130 files clean; `ruff check` → all passed;
   `mypy mayaastrolib/` → **zero** issues across 49 files (the 2-error baseline the
   previous brief flagged is gone). One runtime dependency. Three CI workflows, including
   `package.yml`, which installs the built wheel into a clean venv *outside the source
   tree* and computes a real Western + Vedic chart on every push — that check exists
   because it would have caught the 0.3.1 bug where the entire `vedic` package was
   silently dropped from wheels.

3. **Thread safety and async were solved at the right layer.** Rather than telling
   consumers "don't call this concurrently," `ephem/swe.py:70` serialises the whole C
   surface behind one RLock and `aio.py` offloads to a thread pool. The trade-off (a
   little parallelism for correctness) is documented in the code comment itself and in
   `docs/CONCURRENCY.md`, and `tests/test_concurrency.py` proves the 8-thread result is
   identical to serial. Most Swiss-Ephemeris wrappers never address this at all.

## Gaps & Risks

1. **The Vedic derived layer has no external oracle — only the positions do.**
   The golden tests validate planetary longitudes against Skyfield. But Shadbala
   (645 LOC), the yoga detector (709 LOC), Ashtakavarga, and the Tajika balas are
   validated only against the library's own expectations. Several are explicitly
   approximations — 17 in-code notes say so (`shadbala.py:43` "absolute totals
   approximate", `tajika_bala.py:183` "Panchavargiya Bala (simplified)",
   `tajika.py:268` "a crude 0–3 strength tally"). Coverage is 98–99% there, which
   measures *that the code runs*, not *that the astrology is right*.
   - *Impact:* A consumer reading `shadbala()` output as classical Virupas could be
     materially misled; the honesty currently lives in docstrings, not in the returned
     data.
   - *Effort to fix:* medium (pick 2–3 published reference charts per technique from
     a standard text and pin them, the way the Western side is pinned)

2. **`CLAUDE.md` — the standing session context — is ~3 releases stale.** It states
   "Version: 0.3.0", "553 tests", "94.12%", "mypy: 2 errors", "`vedic/` = 12 modules",
   "PyPI release … out of scope", and "Last updated by Task 038". Reality: 0.5.0,
   664 tests, 95%, mypy clean, 14 modules, published on PyPI, last task 047.
   - *Impact:* This is the highest-leverage stale file in the repo — every future AI
     session starts by reading it and will plan against facts that are two releases old
     (e.g. re-attempting the type-hint pass that 0.4.0 finished).
   - *Effort to fix:* small

3. **Momentum stopped dead after the 0.5.0 sprint, mid-1.0-runway.** 135 commits in the
   last 90 days, **0 in the last 30** — everything landed 2026-06-07/08 and nothing since.
   Meanwhile 13 deprecation paths are queued for removal at 1.0, the camelCase →
   snake_case sweep and the UP031 debt (`docs/RUFF-DEBT.md`) are both explicitly
   "bundle with the 1.0 cleanup", and no 1.0 API-freeze line has been drawn.
   - *Impact:* The library is now *published*, so every week at 0.5.0 adds external
     consumers who will feel the 1.0 breaking changes. The cost of the deferred cleanup
     rises monotonically from here.
   - *Effort to fix:* small to decide and document the freeze line; large to execute it

## Suggested Next Moves

1. **Refresh the "Current codebase state" block in `CLAUDE.md` to 0.5.0 reality.**
   - *Priority:* P0 · *Scope:* small
   - *Evidence:* `CLAUDE.md` says 0.3.0 / 553 tests / 94.12% / mypy 2 errors / 12 vedic
     modules / "PyPI out of scope"; actual is 0.5.0 / 664 / 95% / 0 / 14 / published.
   - *Impact:* Every subsequent session plans against true facts. Highest
     leverage-per-minute item in the repo.

2. **Pin 2–3 published reference values per approximated Vedic technique.**
   - *Priority:* P1 · *Scope:* medium
   - *Evidence:* `vedic/shadbala.py:43`, `vedic/tajika_bala.py:183,187,209`,
     `vedic/tajika.py:268,293`, `vedic/upagrahas.py:104`, `vedic/kp.py:349` — all
     self-declared approximations with no external anchor.
   - *Impact:* Extends the golden-test guarantee from "the positions are right" to
     "the interpretations are right", closing the one place where the project's own
     verification story does not reach.

3. **Draw and publish the 1.0 API-freeze line.**
   - *Priority:* P1 · *Scope:* small (decision) → large (execution)
   - *Evidence:* 13 `DeprecationWarning` sites across 7 modules; `docs/IDEAS.md`
     defers camelCase→snake_case, UP031, and the property/shim removals all to "a single
     1.0 cleanup task"; the package is live on PyPI at 0.5.0.
   - *Impact:* Gives external consumers a migration date instead of open-ended
     uncertainty, and converts three vague "someday" entries into one schedulable task.

4. **Emit the approximation caveats into the serialized output, not just docstrings.**
   - *Priority:* P1 · *Scope:* small
   - *Evidence:* `Chart.to_dict(vedic=True)` returns a Shadbala summary with no marker
     that its absolute Virupa totals are approximate (`vedic/shadbala.py:43`).
   - *Impact:* An API-only or LLM consumer never reads the docstring. A
     `"caveats": [...]` or `"precision": "approximate"` field carries the honesty across
     the JSON boundary — where it matters most for AI tooling, a stated project goal.

5. **Add `Datetime.from_zoneinfo(...)` / DST-aware construction.**
   - *Priority:* P2 · *Scope:* medium
   - *Evidence:* `docs/IDEAS.md` first entry, deferred since Task 007 (2026-05-07);
     `Datetime` still takes a fixed offset string like `"+05:30"`.
   - *Impact:* The single largest ergonomic gap for the stated consumer (web apps
     receiving a birth city + date). Today every caller must independently solve
     historical DST — the classic source of silently-wrong charts.

6. **Cover `predictives/profections.py` or finish deprecating it.**
   - *Priority:* P2 · *Scope:* small
   - *Evidence:* 31% coverage (26 statements, 18 uncovered) — by far the worst module in
     the package; it holds the deprecated `profections.compute()` superseded by
     `Chart.profected()` in Task 010.
   - *Impact:* Either the legacy path is tested or it is honestly on its way out; right
     now it is neither, and it drags the coverage floor.

7. **Delete the two stray duplicate prompt files.**
   - *Priority:* P2 · *Scope:* small
   - *Evidence:* `git status` shows untracked `prompts/task-002b-housekeeping (1).md`
     and `prompts/task-011-chart-dispatch-cleanup (1).md` — browser-download duplicates
     of tracked files.
   - *Impact:* Working tree returns to clean; trivial, but it is the only noise in an
     otherwise pristine repo state.

## File Map

```
mayaastrolib/                    # repo root; editable install backs mayaastro-demo
├── mayaastrolib/                # the package — 49 files, 11,408 LOC
│   ├── __init__.py              # lazy facade — import stays swisseph-free
│   ├── chart.py                 # Chart: construction, lookup, to_dict/to_json, SR/profections
│   ├── object.py aspects.py     # domain model — fully typed since 0.4.0
│   ├── const.py                 # all IDs, LIST_* canonical lists, zodiac/ayanamsa constants
│   ├── datetime.py geopos.py    # typed; GeoPos validates lat/lon ranges
│   ├── report.py                # full_report() facade — the front door        [0.5.0]
│   ├── aio.py                   # achart / afull_report — event-loop-safe      [0.5.0]
│   ├── angle.py lists.py props.py utils.py _compat.py
│   ├── ephem/                   # ephem.py → eph.py → swe.py (sole swisseph bridge, RLock)
│   ├── dignities/               # essential + accidental (essential = most-imported module)
│   ├── predictives/             # returns, profections (31% cov), primarydirections
│   ├── protocols/               # temperament (99%), almutem, behavior
│   ├── tools/                   # arabicparts, planetarytime, chartdynamics
│   ├── vedic/                   # 14 modules / 4,341 LOC — the fork's headline addition
│   │   ├── ayanamsa nakshatras divisional dasha ashtakavarga sadesati upagrahas
│   │   ├── yogas (709) shadbala (645) kp (387)
│   │   └── tajika tajika_bala tajika_aspects
│   ├── resources/swefiles/      # bundled Swiss Ephemeris .se1 data
│   └── py.typed                 # PEP 561 marker — downstream type checkers see our types
├── flatlib/                     # 6-file compat shim, DeprecationWarning, removed at 1.0
├── tests/                       # 54 test_*.py
│   └── golden/                  # 7 Skyfield-anchored charts + invariants + generator
├── docs/                        # 22 md — CONTRIBUTION-PLAN, PROJECT-LOG, CONCURRENCY,
│                                #   RELEASING, KNOWN-BUGS, IDEAS, RUFF-DEBT, briefs
├── prompts/                     # 40+ task specs — the AI build record
├── recipes/ contrib/            # 15 usage examples; 1 archived broken script
├── .github/workflows/           # test.yml · package.yml · publish.yml (OIDC)
├── pyproject.toml               # single config source
└── CLAUDE.md CHANGELOG.md LICENSING.md README.md
```

## Stats

| Metric | Value |
|--------|-------|
| Version | **0.5.0** — published on PyPI |
| Python source files (pkg) | 49 |
| Package LOC | 11,408 |
| Vedic LOC (subset) | 4,341 (14 modules) |
| Test files | 57 (54 root + 3 golden) |
| Tests | **664 + 230 subtests**, all passing (2.53s) |
| Coverage | **95%** (CI floor 80%) |
| Golden reference charts | 7 (Skyfield-anchored, ±2 arcmin) |
| Runtime dependencies | **1** (`pyswisseph`) |
| mypy errors | **0** (49 files) |
| ruff format / check | clean (130 files) |
| CI workflows | 3 |
| Open deprecation paths (→ 1.0) | 13 sites / 7 modules |
| TODO/FIXME/HACK in package | 0 |
| Known open bugs | 0 |
| Commits (30d) | **0** |
| Commits (90d) | 135 |
| Contributors | solo (Rangan C.) |

---

## Delta since `PROJECT-BRIEF-2026-06-06.md`

All 15 intervening commits landed on 2026-06-07/08; nothing since.

**All five prior "Next Moves" were completed:**

| Prior move | Status |
|---|---|
| 1. Finish type hints on `object.py`/`chart.py`/`aspects.py` | ✅ 0.4.0 — plus `py.typed` shipped |
| 2. Clear the 2 baseline mypy errors | ✅ 0.4.0 — mypy now fully clean |
| 3. Docstring "accuracy/simplifications" notes on Vedic approximations | ✅ 17 in-code notes |
| 4. Decide the 1.0 freeze line, cut a PyPI release | ⚠️ **half done** — 0.3.1→0.5.0 published via Trusted Publishing; the freeze line itself is still undrawn |
| 5. Move simplifications into a tracked backlog | ⚠️ partial — still prose in `IDEAS.md`/`PROJECT-LOG.md` |

**New since the last brief:**
- **0.5.0** — `mayaastrolib.aio` async helpers; `full_report` facade; `Chart.to_dict()`
  / `to_json()` schema v1; every swisseph entry point serialised behind one RLock.
- **0.4.0** — six-fold Shadbala; KP horary chart with 12 cusps; higher-order Tajika
  yogas (Kamboola, Gairi-Kamboola, Khallasara); golden charts 3 → 7; full public-API
  type hints; `package.yml` CI.
- **0.3.1/0.3.2** — fixed the packaging bug that shipped wheels **without the entire
  `vedic` package**; PyPI Trusted Publishing; on-disk API token removed.
- Tests 553 → 664; coverage 94.12% → 95%; vedic modules 12 → 14; mypy 2 → 0.

**Carried forward, still open:** the Vedic derived layer still has no external oracle
(prior brief did not raise this); the 1.0 API-freeze decision; DST/`zoneinfo` support.

# CLAUDE.md — maya-astro-lib

This file is the standing context for all Claude Code sessions in this
repository. Read it fully before making any change.

## Project identity

`mayaastrolib` is a Python library for astrological chart calculation,
forked from `flatangle/flatlib` (MIT, abandoned in practice as of 2024).

This fork exists to:
1. Modernise the codebase to current Python (3.10+) with type hints and
   modern packaging.
2. Unify Western (tropical) and Vedic (sidereal) astrology in a single
   library with a coherent API, consolidating the work of the various
   half-finished sidereal forks of flatlib.
3. Provide a clean, typed, async-friendly calculation engine suitable for
   use from web apps (Next.js, FastAPI) and AI tooling (Claude tool calls,
   MCP servers).

This fork does NOT exist to:
- Be a desktop chart-drawing application
- Provide AI-generated interpretations (that belongs in the consuming app)
- Compete with flatlib upstream — if upstream revives, we may contribute back

## Architectural constraints

- Python 3.10 minimum, 3.12 target. No Python 2 compatibility code.
- Type hints required on all new code. Existing code gets typed
  incrementally per the contribution plan.
- Public API stability: anything documented in README is considered public.
  Breaking changes require a major version bump and a CHANGELOG entry.
- Internal modules (anything starting with `_`) can change freely.
- Swiss Ephemeris is the calculation backend. Do not introduce alternative
  ephemeris libraries without explicit discussion.
- No network calls in the core library. Pure calculation only.

## Code style

- Formatter: `ruff format` (line length 100)
- Linter: `ruff check` with the rules in pyproject.toml — must pass
- Type checker: `mypy` — warnings tolerated, errors not
- Naming: PEP 8. Astrological terms keep their conventional capitalisation
  (e.g. `Sun`, `Moon`, `Ascendant`) when used as identifiers for objects,
  but lowercase in function names (`get_sun()`, not `get_Sun()`).
- Imports: stdlib, third-party, local — separated by blank lines
- Docstrings: Google style, required on all public functions and classes

## Testing requirements

Two layers, both mandatory:

1. **Structural tests** (`tests/unit/`) — verify code contracts.
   Every new function gets unit tests. Bug fixes get regression tests.

2. **Functional tests** (`tests/golden/`) — verify astronomical correctness.
   Reference charts with known positions sourced from Astro-Databank or
   astro.com. Tolerance: ±2 arc-minutes for planets, ±5 arc-minutes for
   house cusps. These tests survive any refactor.

Coverage target: 80% minimum, 90% goal. Enforced in CI.

## Pre-completion checklist

Before declaring any task complete, run in this order and confirm all pass:

1. `ruff format --check .`
2. `ruff check .`
3. `mypy mayaastrolib/`
4. `pytest -x` (stop on first failure)
5. `pytest --cov=mayaastrolib --cov-fail-under=80`
6. Update `docs/PROJECT-LOG.md` with: date, task ID, what was done,
   what was tried and discarded, surprises, follow-ups needed
7. Update `CHANGELOG.md` if the change is user-visible

If any step fails, fix before declaring done. Do NOT modify tests to make
them pass — modify the code. The only exception is when a test is
genuinely wrong, in which case explain in PROJECT-LOG.md and CHANGELOG.md.

## Working agreements with Claude Code

- One task per session. Don't combine tasks unless the spec says so.
- Read `docs/CONTRIBUTION-PLAN.md` for the current task. Don't pick
  arbitrary work.
- If a task is ambiguous, stop and ask in PROJECT-LOG.md rather than guess.
- Never push to `main`. All work happens on feature branches.
- Never push to the `upstream` remote. It is read-only.
- Commit messages: imperative mood, ~50 char subject, body explaining why.
  Reference task IDs from the contribution plan.

## Files that are sacred

These should not be modified without explicit instruction:
- `LICENSE` — preserves original copyright chain
- `docs/FORK-RATIONALE.md` — explains why this fork exists
- This file (`CLAUDE.md`)

<!-- AUTO-MANAGED: project-description -->
## Current codebase state

Last updated by Task v1.0-02 remove-deprecated-APIs (2026-07-25, branch `development`).

- **Package name:** `mayaastrolib/` — rename from `flatlib/` completed in Task 005. Canonical import: `from mayaastrolib import ...`. The `flatlib/` compatibility shim was **deleted in Task v1.0-03**; `import flatlib` now raises `ModuleNotFoundError`. `mayaastrolib` is the only top-level package built.
- **Version:** 0.5.0, published on PyPI (`pip install mayaastrolib`) — unified via `importlib.metadata.version("mayaastrolib")` in `pyproject.toml`. `development` currently carries unreleased **breaking** changes for 1.0.
- **pyproject.toml:** EXISTS — PEP 621, setuptools backend; single source of truth for version, ruff, mypy, pytest, and coverage config. `pythonpath = ["."]` set. UP031 in `[tool.ruff.lint] ignore`.
- **setup.py:** DELETED — build system is pyproject.toml only.
- **requirements.txt:** DELETED — runtime dep (`pyswisseph>=2.10.3.2`) and dev extras live in pyproject.toml `[dev]` extras.
- **README.rst:** DELETED — `README.md` is canonical.
- **scripts/:** DELETED — removed in Task 002.
- **contrib/topical_almuten.py:** ARCHIVED as `contrib/topical_almuten.py.broken` (SyntaxError since 2021, never importable); `topical_almuten.README.md` documents the revival path.
- **CI:** `.github/workflows/test.yml` EXISTS — GitHub Actions, matrix Python 3.10/3.11/3.12, runs ruff format check + ruff check + pytest + coverage against `mayaastrolib`.
- **Dev venv:** `python3 -m venv .venv-<taskname>` then `pip install -e ".[dev]"`. Named per-task (`.venv-task002` through `.venv-task009`; no `.venv-task010` — Tasks 010–013 reused `.venv-task009`; `.venv-task014` created fresh because skyfield needed installing; Tasks 014, 015, and 016 all reused `.venv-task014` — no `.venv-task015` or `.venv-task016` created); all ignored by `.gitignore`.
- **Python locally:** 3.14.3. CI targets 3.10–3.12.
- **Tests:** 57 test files, **655 tests + 230 subtests**, all passing. Coverage **95%** (`--cov=mayaastrolib --cov-fail-under=80`). `mayaastrolib/vedic/` = **14 modules**. **Type-hint pass: DONE** — `geopos`, `datetime`, `object`, `chart`, `aspects`, `_compat` all typed and the package ships `py.typed` (0.4.0 + Task v1.0-04; the `_compat` decorator is typed `Callable[[Any], _T] -> _T` so the 13 migrated properties expose real types downstream instead of `Any`). **Remaining genuine open work:** the rest of the ~50 Sahams + ~10 more Tajika yogas (source-variant); external reference values for the approximated Vedic techniques (Shadbala totals, Panchavargiya Bala, `lord_of_year`) — these are self-declared approximations with no independent oracle. Cross-repo oracle-parity tests are out of scope per the user.
- **Road to 1.0:** `prompts/v1.0-00-INDEX.md` is the ordered backlog. Done: **v1.0-01** (pinned `ruff==0.15.16` / `mypy==2.1.0`, hermetic fixed-star tests), **v1.0-01b** (per-thread swisseph ephemeris path — see below), **v1.0-02** (deprecated-API removal), **v1.0-03** (flatlib shim deleted), **v1.0-04** (finish type hints), **v1.0-05** (public API frozen — `__all__` on 25 modules + `docs/API-STABILITY.md`, enforced by `tests/test_public_api.py`). Note prompt **07** (six-fold Shadbala, KP horary cusps) was largely delivered by 0.4.0 — only 7b (the Saham/Tajika long tail) is genuinely open, and it is optional for 1.0.
- **Deprecations — REMOVED in 1.0 (Task v1.0-02):** `getAspectOrSentinel()`, `setTerms()`/`setFaces()`, `Object.relocate()`, `Object.antiscia()`/`cantiscia()`, `profections.compute()`, `tools.arabicparts.getPart()`, `House._OFFSET`. See CHANGELOG "Removed (BREAKING)" for replacements. **Still present:** the `_compat.py` property migration (`obj.movement` *and* `obj.movement()` both work) and the `flatlib/` shim — both slated for removal by later v1.0 tasks.
- **Threading:** every swisseph call goes through `ephem.swe._ephe_session()`, which takes the lock **and** re-applies the ephemeris path for the calling thread. Do not take `_SWE_LOCK` directly — the Linux wheels keep swisseph state thread-local, so a missed path re-apply silently downgrades results to the Moshier ephemeris. See `docs/CONCURRENCY.md`.
- **Public API:** a name is public iff it is in its module's `__all__`. `docs/API-STABILITY.md` is the contract (frozen surface, `vedic` fidelity tiering, not-public modules, post-1.0 deprecation policy). Top-level `Chart`/`Datetime`/`GeoPos`/`const`/`full_report` resolve **lazily** — do not convert to eager imports, `import mayaastrolib` must stay swisseph-free (pinned by `tests/test_public_api.py`).
- **Lint state:** `ruff format --check` PASSES. `ruff check` PASSES. UP031 deferred — see `docs/RUFF-DEBT.md`.
- **mypy:** clean — *Success: no issues found in 49 source files*.
- **Known bugs:** None open. Eclipse `backward=` kwarg bug fixed in Task 004 (see `docs/KNOWN-BUGS.md`).
- **Dep graph:** clean DAG, no cycles; `dignities.essential` is the most-imported module.
- **LICENSING.md:** EXISTS at repo root — documents MIT (mayaastrolib) + LGPL (pyswisseph) + GPL/commercial (Swiss Ephemeris) licensing situation.
- **Features completed (Tasks 004–016):**
  - Task 004: Eclipse `backward=` → `backwards=` fix in `ephem/swe.py`; regression test `tests/test_eclipses.py`; CI workflow established (`.github/workflows/test.yml`)
  - Task 004a: Smoke tests for 12 zero-coverage modules (dignities/predictives/protocols/tools); coverage 34% → 86%
  - Task 005: Package renamed `flatlib/` → `mayaastrolib/`; flatlib compat shim added
  - Task 006: `Chart.houseOf()`, `Chart.objectsInHouse()`, `Object.house`, `House.objects`; property migration via `mayaastrolib/_compat.py`; `docs/PROPERTY-MIGRATION.md`
  - Task 007: `Datetime.from_pydatetime()`, `Datetime.now()`, `Datetime.to_pydatetime()`; DST and ISO 8601 deferred to `docs/IDEAS.md`
  - Task 008: `dignities.essential` thread-safe via `terms_variant`/`faces_variant` kwargs; `setTerms()`/`setFaces()` deprecated
  - Task 009: `Aspect.name`, `Aspect.activeObj`/`passiveObj`; `getAspect()` returns `None` (was sentinel); `getAspectOrSentinel()` deprecated (removed in 1.0); `ASPECT_NAMES` dict and 8 standard list constants (`LIST_MODERN_PLANETS`, `LIST_TROPICAL_DEFAULT`, `LIST_VEDIC_DEFAULT`, `LIST_LIGHTS`, `LIST_PERSONAL_PLANETS`, `LIST_SOCIAL_PLANETS`, `LIST_TRANSPERSONAL`, `LIST_LUNAR_NODES`) added to `const.py`; `docs/OBJECT-LISTS.md`
  - Task 010: `Object.with_longitude(lon, *, preserve_speed=False)` — immutable replacement for in-place `relocate()`; `Object.antiscion()`/`cantiscion()` (new, preserve_speed=True); `Chart.profected(years=N)` / `Chart.profected(target_date=D)` returns symbolic chart; `Chart.is_symbolic` (bool) and `Chart.symbolic_kind` (str); speed-derived methods (`movement`, `isFast`, `isDirect`, `isRetrograde`, `isStationary`) return `None` when `lonspeed is None`; deprecated: `Object.relocate()`, `Object.antiscia()`/`cantiscia()`, `profections.compute()`; fixed: profected charts no longer carry stale natal retrograde state
  - Task 011: `Chart.get()` dispatches by `const.LIST_HOUSES` / `const.LIST_ANGLES` membership (no more `startswith("House")`); `House.num` cached on `self._num` at `fromDict` time (no more `int(self.id[5:])`); 11 new dispatch tests in `tests/test_chart_dispatch.py`; internal-only refactor, no public API changes
  - Task 012: Audit investigations (docs-only, no test-count change); Item 15: `House._OFFSET` confirmed as traditional 5° cusp-tolerance rule, renamed to `House._CUSP_TOLERANCE_DEG` with full docstring (old name kept as alias until 1.0); Item 16: `solarReturn(year)` semantics verified correct, docstring expanded; new `docs/AUDIT-INVESTIGATIONS.md`; configurable cusp tolerance and `solarReturnByAge()` deferred to `docs/IDEAS.md`
  - Task 013: `Chart.solarReturn()` extended with `target_date=` kwarg (`year=` still works); `Chart.directions()` returns `PrimaryDirections(self)` (class NOT deprecated); `Chart.arabicPart(part_id)` calls new private `_getPart_impl`; `Chart.planetaryHour(date=None)` wraps `getHourTable`, defaults to chart date; deprecated: `tools.arabicparts.getPart(ID, chart)`; 18 new tests added
  - Task 014: golden test fixtures (`tests/golden/`) — Skyfield-anchored planet-position tests for 3 reference charts (Einstein, Kahlo, Amundsen) at ±2 arcmin tolerance, plus self-consistency invariant suite (houses sum to 360°, cusps ordered, planets in valid ranges, profected charts symbolic); `skyfield>=1.46` added as dev-only dep; `LICENSING.md` clarifies the MIT + LGPL + GPL-Swiss-Eph commercial situation; 10 new test methods, 57 subtests; closes the headline reliability gap surfaced by the platform review
  - Task 015: `GeoPos.__init__` validates `lat ∈ [-90, 90]` and `lon ∈ [-180, 180]` after `toFloat()` coercion; raises `ValueError` with the offending value; closes the silent-bad-chart bug surfaced by the platform review (`docs/REVIEW-2026-05-08.md`); 15 regression tests in `tests/test_geopos_validation.py`; new entry in `docs/KNOWN-BUGS.md` "Resolved"
  - Task 016: `swisseph.fixstar2_mag` lookups cached per-process via `@functools.cache` on private `mayaastrolib.ephem.swe._fixstar_mag(star)` wrapper; 144x measured speedup on a 35-star pass (M2 / Python 3.14); no public API change; closes the only documented "really slow" path surfaced by the platform review; 4 cache-correctness regression tests in `tests/test_fixstar_mag_cache.py`
  - **Task 038: Public-API type hints (datetime.py).** `datetime.py` fully type-hinted (`from __future__ import annotations`; module-level `import datetime as _pydt`; `dateJDN`/`jdnDate`/offset helpers + the `Date`/`Time`/`Datetime` classes — attr annotations + all method signatures). No behaviour change; mypy at the 2-error baseline. `aspects.py`/`chart.py`/`object.py` deferred (the `__dict__.update` / `_compat` dynamic-attribute patterns make signature annotations surface ~30 mypy errors — needs a deliberate refactor, not a quick pass).
  - **Task 037: Public-API type hints (geopos.py).** `geopos.py` fully type-hinted (`from __future__ import annotations`; `toFloat`/`toList`/`toString` + the `GeoPos` class). No behaviour change; mypy still at the 2-error baseline. First slice of the public-API type-hint pass — `datetime.py`/`aspects.py`/`chart.py`/`object.py` remain.
  - **Task 036: Ashtakavarga shodhana variants.** `vedic/ashtakavarga.py` — `variant=` on `trikona_shodhana` (`subtract_min` / `zero_if_any_zero`) and `ekadhipatya_shodhana` (`default` / `zero_unoccupied`); `shodhita_sarvashtakavarga(..., trikona_variant=, ekadhipatya_variant=)` threads both through. `TRIKONA_VARIANTS`/`EKADHIPATYA_VARIANTS` constants; unknown → `ValueError`. 5 new tests.
  - **Task 035: Weighted yoga strength + yoga cancellations.** `vedic/yogas.py` — `yoga_strength_weighted(yoga, chart, ...)` (sum of the yoga planets' `AccidentalDignity.score()`; accidental dignity, not full Shadbala — documented). `detect_yogas_with_strength(chart, ayanamsa=..., weighted=False)` `weighted=` flag. Gaja-Kesari cancellation (Jupiter/Moon debilitated). Neecha-Bhanga also fires on navamsa-exaltation when `planet_lons` is passed; `_chart_signs` now returns the longitudes too. 6 new tests. Full six-fold Shadbala, combust/enemy-sign Gaja-Kesari cancellation deferred.
  - **Task 034: AccidentalDignity score-rule refactor.** `getScoreProperties` — the 15 simple "+N if flag else 0" rules now come from a `(key, flag, plus, otherwise)` table iterated once; the ~7 context-dependent rules (Sun-excluded light/no-under-sun/direction, 3-way haiz, feral↔void interaction, Moon-only via-combusta, orientality) stay inline. Behaviour identical (verified by `test_score_properties_regression` pinning the scores + the full Sun dict). Method ~88→~55 LOC; complexity down. Closes the platform-review hotspot.
  - **Task 033: Per-factor tests for smoke-only modules.** `tests/test_protocols_temperament_factors.py` + `tests/test_dignities_accidental_factors.py` exercise the temperament and accidental-dignity engines across several charts × the 7 classical planets. No production code changed. `accidental.py` 84%→100%, `temperament.py` 80%→99%; overall 92%→94%. Closes the platform-review "smoke-tested only" gap.
  - **Task 032: Lesser Vedic yogas + yoga strength.** `vedic/yogas.py` — `_detect_lesser` adds Amala (benefic in 10th from Lagna/Moon), Adhi (benefics in 6/7/8 from Moon), Lakshmi (9th lord dignified in kendra/trikona), Saraswati (J/V/M in good houses), Kahala (4th & 9th lords in mutual kendras), Vasumati (all benefics in upachayas), Sunapha/Anapha/Durudhara (around the Moon), Vesi/Vasi/Ubhayachari (around the Sun). `detect_yogas = _detect + _detect_extended + _detect_lesser`. `yoga_strength(yoga, planet_signs, asc_sign)` (+2 own/exalt, −2 debilitated, +1 kendra/trikona); `detect_yogas_with_strength(chart, ...)` sorts by descending strength. `UPACHAYA_HOUSES` constant; `_chart_signs` helper. 28 tests. Classical Shadbala-weighted strength + the long tail of yogas deferred.
  - **Task 031: Ashtakavarga prastara / shodhana / kakshya.** `vedic/ashtakavarga.py` — `bhinnashtakavarga_prastara(planet, signs)` (per-contributor 0/1 breakdown; sums to the BAV), `trikona_shodhana(bav)` (subtract the min from each of the 4 trine groups), `ekadhipatya_shodhana(bav, occupied_signs)` (co-rulership reduction over the 5 sign pairs — one common variant), `shodhita_sarvashtakavarga(planet_signs, lagna_sign)` (SAV after both reductions; ≪337), `kakshya_of(lon)` (8 kakshyas of 3°45', order Saturn/Jupiter/Mars/Sun/Venus/Mercury/Moon/Lagna), `kakshya_transit_active(prastara, transiting_lon)` → `(kakshya_lord, bool)`. Constants `TRIKONA_GROUPS`/`EKADHIPATYA_PAIRS`/`KAKSHYA_LORDS`. 35 tests.
  - **Task 030: KP sub-sub-lord / horary / Ruling Planets.** `vedic/kp.py` — `sub_sub_lord_at(lon)` and `sub_lord_at(lon, with_sub_sub=True)` (the 4th KP level: within a sub, 9 Vimshottari-proportional parts starting from the sub's lord). `prashna_to_longitude(n)` (horary number 1..249 → midpoint of the Nth KP segment; raises outside [1,249]). `kp_horary(n)` → `{prashna, lagna_longitude, lagna}` (lagna = the with-sub-sub chain). `ruling_planets(date, pos, ayanamsa=AYANAMSA_KRISHNAMURTI)` → `{day_lord, moon_sign_lord, moon_star_lord, moon_sub_lord, lagna_sign_lord, lagna_star_lord, lagna_sub_lord, all}` (civil-date weekday; KP ayanamsa). New `_vimshottari_sequence_from`/`_proportional_lord` helpers. 13 tests. Full horary chart with cusps deferred.
  - **Task 029: Tajika Harsha/Panchavargiya Bala + aspects.** `vedic/tajika_bala.py` — `harsha_bala(chart, ayanamsa=...)` (5-component 0/5 joy score, max 25: hemisphere/gender/dignity/own-decanate/joy-house), `panchavargiya_bala(chart, ayanamsa=...)` (Kshetra+Uchcha(0..20)+Hadda+Drekkana+Navamsa sum — **simplified component scales**, documented). `vedic/tajika_aspects.py` — `tajika_aspects(chart)` detects Ithasala (applying)/Isharafa (separating)/Nakta (translation of light) with deeptamsha orbs (Sun 15° … Saturn 9°; pair-orb = average); `TajikaAspect` frozen dataclass; needs real speeds (raises on symbolic charts). 16 tests. `lord_of_year` still uses its own heuristic; remaining 13 Tajika yogas + faithful Panchavargiya scales deferred.
  - **Task 028: Fuller Tajika Saham table.** `tajika.sahams()` returns 14 Sahams (was 4): Punya, Vidya, Yasas, Karma, Pitri, Matri, Bhratri, Putra, Kalatra, Jeeva, Vivaha, Vyapara, Roga, Bandhu. Data-driven `_SAHAM_FORMULAS` table (`name → (term_a, term_b, reversible)`; a term is a planet ID, `"Asc"`, or another Saham name). New `SAHAM_*` constants. Yasas references the chart's Punya Saham. Formulas follow Raman *Varshaphala*; still a curated subset of ~50, the rest a follow-up.
  - **Task 027: Zodiac-aware predictives.** `zodiac`/`ayanamsa` thread through `ephem/tools.solarReturnJD` → `eph`/`ephem` `nextSolarReturn`/`prevSolarReturn` (default tropical); `Chart.solarReturn` and `_years_to` pass `self.zodiac`/`self.ayanamsa`; the SR chart is built with the same. So `Chart.solarReturn()` / `Chart.profected(target_date=...)` now work correctly on sidereal charts (SR Sun returns to the natal *sidereal* Sun). `Chart.directions()` raises `NotImplementedError` on a sidereal chart (primary directions need equatorial coords; not a Vedic technique). Tropical behaviour unchanged. 11 tests.
  - **Task 024b: Tajika Muntha / Lord of Year / Sahams.** `vedic/tajika.py` extended with `muntha(natal_chart, target_year, ayanamsa=...)` (the progressed point — natal Lagna sign at birth, +1 sign/year; returns `{sign_idx, sign, lord}`), `lord_of_year_candidates(annual_chart, natal_chart, target_year, ...)` (the 5 Varsheshwara candidates as `(label, planet_id)` — Muntha lord, annual-Lagna lord, Sun-sign lord, natal-Lagna lord, Trirashi-pati), `lord_of_year(...)` (picks by a simple own/exalted/in-kendra tally — HEURISTIC, the canonical rule uses Panchavargiya Bala which is a follow-up), `sahams(annual_chart, ...)` (Punya/Vidya/Yasas/Karma — the unambiguous core; full ~50-Saham table deferred). 21 tests. Harsha/Panchavargiya Bala, Tajika aspects, the full Saham list deferred.
  - **Task 026b: Extended Vedic yogas.** `vedic/yogas.py` now also detects Raja (kendra lord conjunct distinct trikona lord), Dhana (two distinct wealth-house 2/5/9/11 lords conjunct), Vipareeta Raja (Harsha/Sarala/Vimala — 6th/8th/12th lord in a dusthana), Neecha Bhanga (debilitated planet cancelled by dispositor or would-be-exalted planet in a kendra), Kemadruma (no graha in 2nd/12th from Moon). New public helpers `sign_lord`, `house_lord`, `houses_ruled_by`; constants `TRIKONA_HOUSES`/`DUSTHANA_HOUSES`/`DHANA_HOUSES`. `detect_yogas = _detect + _detect_extended`. 17 new tests. Conjunction-only Raja/Dhana (no aspect/parivartana yet); 2 of the classical Neecha-Bhanga conditions; "2nd & 12th empty" Kemadruma. Yoga strength, lesser yogas deferred.
  - **Task 025: Vedic KP sub-lords.** `mayaastrolib/vedic/kp.py` — `kp_table()` returns the canonical **249-row** sub-lord table (`{start_lon, end_lon, sign, sign_lord, nakshatra, star_lord, sub_lord}`, tiling [0,360); 249 = 243 Star×Sub segments + the 6 sign boundaries 30/90/150/210/270/330 that bisect a sub-segment; import-time assert enforces). `sub_lord_at(sidereal_lon)` returns the chain `{longitude, sign, sign_lord, nakshatra, star_lord, pada, sub_lord}`. `kp_sublords(chart, ayanamsa=AYANAMSA_KRISHNAMURTI)` returns chains for the 7 planets + Asc (defaults to KP ayanamsa for tropical charts). `SIGN_LORDS` = traditional 7-planet rulerships. 14 unit tests. Sub-sub-lord, KP horary, Ruling Planets deferred.
  - **Task 017b: Additional ayanamsas.** `vedic/ayanamsa.py` now supports `lahiri`, `krishnamurti` (KP — swisseph's `SIDM_KRISHNAMURTI`, ~0.1° below Lahiri), `raman`, `fagan_bradley`. `const.AYANAMSA_KRISHNAMURTI`/`RAMAN`/`FAGAN_BRADLEY`; `LIST_AYANAMSAS` has all four. `ayanamsa.get(ayanamsa, date)` is the generic table-driven dispatcher; per-name functions are thin wrappers. `Chart(zodiac=ZODIAC_SIDEREAL, ayanamsa=...)` accepts any. 11 tests.
  - **Task 026: Vedic Yoga Detection.** `mayaastrolib/vedic/yogas.py` — `detect_yogas(chart, ayanamsa=...)` returns a list of `YogaResult(name, sanskrit, planets, description)`. Detects the 5 Pancha Mahapurusha (Ruchaka/Mars, Bhadra/Mercury, Hamsa/Jupiter, Malavya/Venus, Sasha/Saturn — planet in own/exaltation sign AND in a kendra), Gaja-Kesari (Jupiter 1/4/7/10 from Moon), Budha-Aditya (Mercury+Sun same sign), Chandra-Mangala (Moon+Mars same sign). Kendras are Whole-Sign (sign offset from Asc, ignoring `hsys`). Classical Vedic dignity tables encoded fresh (`OWN_SIGNS`/`EXALTATION_SIGN`/`DEBILITATION_SIGN`) — NOT the Western `dignities/tables.py`. Helpers: `is_in_own_or_exaltation`, `is_debilitated`, `house_from`. 23 unit tests; core logic tested independent of the ephemeris. Raja/Dhana/Vipareeta yogas, Neecha Bhanga, Kemadruma deferred.
  - **Task 024: Vedic Tajika (core slice).** `mayaastrolib/vedic/tajika.py` — `varshapravesh(natal_chart, target_year, ayanamsa=...)` returns the `Datetime` when the sidereal Sun returns to the natal sidereal Sun longitude (own sidereal search `sidereal_sun_return_jd`, NOT the tropical solar return — they diverge by up to ~a day over decades). `mudda_dasha(varshapravesh_date, ...)` returns 9 `DashaPeriod`s — the 365.25-day year split in Vimshottari proportions, starting from the varshapravesh-Moon's nakshatra lord. Reuses `dasha.DashaPeriod`/`VIMSHOTTARI_ORDER`/`VIMSHOTTARI_YEARS`. First Mudda period is full-length (year starts fresh at VP, no partial-before). `Chart.solarReturn` deliberately left tropical-only. 13 unit tests. Deferred to Task 024b: Varsheshwara, Harsha Bala, Panchavargiya Bala, the ~50 Sahams, Tajika aspects.
  - **Task 023: Vedic Upagrahas.** `mayaastrolib/vedic/upagrahas.py` — `sun_derived_upagrahas(sun_sidereal_lon)` returns the 5 Phaladeepika points (Dhuma = Sun+133°20', Vyatipata = 360−Dhuma, Parivesha = Vyatipata+180, Indrachapa = 360−Parivesha, Upaketu = Indrachapa+16°40'). `gulika_longitude(chart, ayanamsa=...)` = Gulika/Mandi via weekday-portion method (day/night span split into 8 parts ruled in weekday order; sidereal Asc at start of Saturn-ruled part; uses civil-date weekday — documented approximation). `upagrahas(chart, school="B", ayanamsa=...)` returns `{name: UpagrahaResult(name, sidereal_longitude, sign, deg_in_sign)}`; `school="B"` = 5 Sun-derived (default), `school="A"` adds Gulika. `WEEKDAY_LORDS` table (Sun=0..Sat=6). 17 unit tests. Other Kala-velas (Kala/Mrityu/Artha-prahara/Yamaghantaka) deferred.
  - **Task 022: Vedic Sade Sati.** `mayaastrolib/vedic/sadesati.py` — `sade_sati(natal_moon_sign, target, ayanamsa=...)` returns `SadeSatiPhase(active, phase, saturn_sign, natal_moon_sign, severity)`; phases `"rising"`/`"peak"`/`"setting"`/`"not-active"` (Saturn in 12th/1st/2nd from natal Moon; peak=janma shani=intense). `sade_sati_for_year(sign, year, ...)` checks July 1 noon UTC. `small_panoti(sign, target, ...)` returns `"ashtama_shani"` (Saturn 8th from Moon) / `"kantaka_shani"` (4th) / `None`. `saturn_sidereal_sign(target, ...)` → 0..11. `natal_moon_sign` accepts int or sign-name string; no GeoPos needed (Saturn longitude is location-independent). 22 unit tests. Day-precise ingress dates deferred.
  - **Task 021: Vedic Ashtakavarga.** `mayaastrolib/vedic/ashtakavarga.py` — BPHS Ch. 66 bindu system. `ASHTAKAVARGA_TABLES` holds the Prastara tables for all 7 planets (per-planet totals 48/49/39/54/56/52/39 → 337 SAV grand total, enforced by import-time asserts). `bhinnashtakavarga(planet, signs)` returns the 12-cell BAV histogram for one planet given the 8 contributor sign indices (7 planets + `ASCENDANT` literal key). `sarvashtakavarga(planet_signs, lagna_sign)` returns `{per_rasi, grand_total, by_planet}` with `grand_total` always 337. `ashtakavarga(chart, ayanamsa=...)` chart-level entry point; handles tropical-or-sidereal. 16 unit tests. Trikona/ekadhipatya shodhana and kakshya sub-divisions deferred.
  - **Task 020: Vimshottari Dasha.** `mayaastrolib/vedic/dasha.py` — `vimshottari(chart, target=None, ayanamsa=...)` returns full 120-year MD sequence plus optional MD/AD/Pratyantar active at target. `antardashas(md)` returns 9 ADs (starting with MD lord); `pratyantar_dashas(ad)` returns 9 Pratyantars. `DashaPeriod` and `VimshottariResult` are frozen dataclasses with `level=1/2/3` for MD/AD/Pratyantar. `VIMSHOTTARI_ORDER` = [Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury]. `VIMSHOTTARI_YEARS` totals 120; `DAYS_PER_VIMSHOTTARI_YEAR = 365.25` per BPHS / Muhurta Chintamani. First MD's `start` precedes `chart.date` (partial-remaining portion). Accepts both tropical and sidereal charts. 19 unit tests in `tests/test_vedic_dasha.py`.
  - **Task 019: Vedic divisional charts (Shodashavarga).** `mayaastrolib/vedic/divisional.py` — all 16 BPHS vargas as pure functions on sidereal longitude returning sign index 0-11: D1 rasi, D2 hora, D3 drekkana, D4 chaturthamsa, D7 saptamsa, D9 navamsa, D10 dasamsa, D12 dvadasamsa, D16 shodasamsa, D20 vimsamsa, D24 chaturvimsamsa, D27 bhamsa, D30 trimsamsa (unequal segments per BPHS 6.29-32), D40 khavedamsa, D45 akshavedamsa, D60 shastiamsa. `all_vargas(chart, ayanamsa=...)` chart-level entry point handles tropical-or-sidereal input. Internal `_segment(deg, n) = int(deg * n / 30)` avoids float-imprecision bug at boundaries. 25 unit tests in `tests/test_vedic_divisional.py`.
  - **Task 018: Vedic nakshatras.** `mayaastrolib/vedic/nakshatras.py` — `NAKSHATRA_NAMES` (27 Sanskrit names, BPHS order), `NAKSHATRA_LORDS` (Vimshottari cycle: Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury × 3), `Nakshatra` frozen dataclass (name, lord, pada 1-4, index 0-26), `of_longitude(sidereal_lon)`, `janma_nakshatra(chart, ayanamsa=...)` (accepts both tropical and sidereal charts), `tarabala(natal_nak, transit_nak)` (1..9 cycle position per Muhurta Chintamani 6.6). Each nakshatra spans 13°20'; each pada 3°20'. 17 unit tests in `tests/test_vedic_nakshatras.py`; tropical-and-sidereal chart inputs agree.
  - **Task 017: Vedic foundation.** New `mayaastrolib/vedic/` package; `vedic.ayanamsa.lahiri(date)`, `to_sidereal`, `to_tropical`, `get`. `Chart` accepts `zodiac=ZODIAC_TROPICAL|ZODIAC_SIDEREAL` and `ayanamsa=AYANAMSA_LAHIRI` kwargs (default tropical — zero behaviour change for existing callers). Sidereal mode threaded through three-layer ephem stack with lock-guarded `set_sid_mode + calc_ut` / `set_sid_mode + houses_ex` pairs in `ephem/swe.py`. Constants: `ZODIAC_*`, `AYANAMSA_LAHIRI`, `LIST_ZODIACS`, `LIST_AYANAMSAS`, plus Sanskrit aliases `RAHU = NORTH_NODE`, `KETU = SOUTH_NODE`. Golden tests at `tests/golden/test_vedic_positions.py` anchor Skyfield-tropical-minus-Lahiri-ayanamsa against `Chart(zodiac=ZODIAC_SIDEREAL)` at ±2 arcmin for Einstein/Kahlo/Amundsen. Solar returns / profections / directions are zodiac-naive under sidereal mode (deferred to Phase 2 follow-ups). Lahiri ayanamsa only; KP/Raman/Fagan-Bradley deferred.
<!-- END AUTO-MANAGED -->

## Goal anchor

When in doubt, the question to ask is: "does this serve the three goals
listed under Project Identity?" If not, it goes in `docs/IDEAS.md` for
later consideration, not into the current sprint.

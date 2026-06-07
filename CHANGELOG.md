# Changelog

All notable changes to this project will be documented in this file. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.3.2] — 2026-06-07

### Added
- **CI Trusted Publishing** (`.github/workflows/publish.yml`) — publishing to
  PyPI now happens automatically when a GitHub Release is published, via
  PyPI's OIDC Trusted Publishing (no API token stored anywhere). The build
  job validates with `twine check` and installs the built wheel into a clean
  venv to compute a Western + Vedic chart before publishing, so a broken
  wheel (e.g. the 0.3.1 dropped-`vedic` bug) can never be auto-released.
- `docs/RELEASING.md` documents the one-time PyPI trusted-publisher setup and
  the tag → release → auto-publish flow.

### Changed
- Richer `[project.urls]` (Repository, Documentation, Changelog, Issues) so
  the PyPI project page links back to the GitHub repo, docs, and changelog.

## [0.3.1] — 2026-06-07

### Fixed
- **Packaging: `mayaastrolib.vedic` was omitted from built wheels/sdists.**
  `pyproject.toml` used a hand-maintained `[tool.setuptools] packages = [...]`
  list that predated the Vedic subsystem (added in Task 017), so a real
  `pip install` shipped the library *without its entire Vedic engine* —
  any sidereal/Jyotisha call raised `ModuleNotFoundError: No module named
  'mayaastrolib.vedic'`. Editable installs (`pip install -e .`) masked it
  because they put the whole source tree on the path. Switched to
  setuptools auto-discovery (`[tool.setuptools.packages.find]`, include
  `mayaastrolib*` / `flatlib*`) so no subpackage can be silently dropped
  again. Caught by a clean-install end-to-end smoke test (Western chart +
  Vedic nakshatra) run against the built wheel.
- **Packaging: `MANIFEST.in`** expanded to ship the Swiss Ephemeris data
  (`*.se1`/`*.cat`/`*.txt`), README, CHANGELOG, and LICENSING in the sdist.

### Changed
- README documentation links made absolute so they render on PyPI.

## [0.3.0] — 2026-06-07

First release under the `mayaastrolib` name; first to ship the unified
Western + Vedic engine. See the per-task entries below for the full history.

### Changed (Docs — flatlib → mayaastrolib branding pass + enhancement showcase)
- `README.md` rewritten to lead with the value the fork adds over flatlib:
  a "What this fork adds" section covering the 12-module Vedic subsystem,
  the modernisation (Python 3.10+, type hints, `pyproject.toml`-only
  packaging, ruff/mypy/CI), the coverage jump (34% → 94% with
  Skyfield-anchored golden tests), and the API ergonomics/correctness fixes.
- The 32 inherited source-file headers now read "This file is part of
  mayaastrolib, a fork of flatlib - (C) FlatAngle" — accurate to the
  package name while preserving the original copyright/author attribution.
- `mayaastrolib/resources/README.md`, `docs/README.md`, and the inherited
  Sphinx tree under `docs/source/` (`conf.py`, `index.rst`, `faq.rst`,
  `installation.rst`, and the tutorial import/URL examples) updated from
  flatlib to mayaastrolib; installation docs updated for the 3.10+
  source-install reality and project metadata bumped to 0.3.0.
- `LICENSE`, `docs/FORK-RATIONALE.md`, `CLAUDE.md`, the `flatlib/`
  compatibility shim, and historical logs (CHANGELOG/PROJECT-LOG/prompts)
  intentionally left referencing flatlib — they document the copyright
  chain, the fork rationale, and project history.
- No code behaviour change; 553 tests pass, ruff/format clean, mypy at the
  2-error baseline.

### Changed (Task 038 — public-API type hints: datetime.py)
- `mayaastrolib/datetime.py` is now fully type-hinted (`from __future__
  import annotations`; `dateJDN`/`jdnDate`/`_format_offset`/
  `_parse_offset` and the `Date`/`Time`/`Datetime` classes — attribute
  annotations and all method signatures, including `from_pydatetime` /
  `now` / `to_pydatetime` / `fromJD` / `getUTC`). The module-level
  `import datetime as _pydt` replaces the per-function local imports.
  No behaviour change; mypy stays at the documented 2-error baseline.
- Note: `aspects.py`, `chart.py`, and `object.py` were attempted but
  *deferred* — they use `self.__dict__.update(...)` (Aspect /
  AspectObject) and the `_compat.property_with_method_compat` /
  `_DualAccess` machinery (Object / House), so adding signature
  annotations makes mypy start checking those method bodies and it then
  flags ~30 dynamically-set attributes (`.id`, `.type`, `.movement`,
  …). Typing those cleanly needs either class-level attribute
  annotations on the dynamic classes or a small restructure of the
  `__dict__.update` pattern — a deliberate change, not a quick pass —
  so it's left for a follow-up. `geopos.py` (Task 037) and
  `datetime.py` (this task) are the two clean ones; that's 2 of the 5
  public-API modules typed.

### Changed (Task 037 — public-API type hints: geopos.py)
- `mayaastrolib/geopos.py` is now fully type-hinted (`from __future__
  import annotations`; the `toFloat`/`toList`/`toString` conversion
  helpers and the `GeoPos` class — `lat`/`lon` attributes, `__init__`,
  `slists`, `strings`, `__str__`). No behaviour change; mypy stays at
  the documented 2-error baseline. First slice of the public-API
  type-hint pass — `datetime.py`, `aspects.py`, `chart.py`, and
  `object.py` are still to do (the latter two are the `_compat`-heavy
  ones and need care to avoid mypy noise).

### Added (Task 036 — Ashtakavarga shodhana variants)
- `trikona_shodhana(bav, variant="subtract_min")` — new `variant=`:
  `"subtract_min"` (default, unchanged) or `"zero_if_any_zero"` (the
  harsher rule some texts use — if any cell in a trine is 0, zero the
  whole trine).
- `ekadhipatya_shodhana(bav, occupied_signs, variant="default")` — new
  `variant=`: `"default"` (unchanged) or `"zero_unoccupied"` (when one
  sign of a co-ruled pair is occupied, the unoccupied one is always
  zeroed regardless of values).
- `shodhita_sarvashtakavarga(planet_signs, lagna_sign,
  trikona_variant=..., ekadhipatya_variant=...)` — passes the variants
  through. New `TRIKONA_VARIANTS` / `EKADHIPATYA_VARIANTS` constants;
  unknown variants raise `ValueError`.
- 5 new tests in `tests/test_vedic_ashtakavarga_shodhana.py`.

### Added / Changed (Task 035 — weighted yoga strength + yoga cancellations)
- `mayaastrolib.vedic.yogas.yoga_strength_weighted(yoga, chart, ...)` —
  a strength score for a yoga weighted by the *accidental dignity*
  (`AccidentalDignity.score()`) of its classical-planet members.
  Documented as accidental dignity, not a full six-fold Shadbala (the
  Cheshta/Naisargika balas aren't modelled).
- `detect_yogas_with_strength(chart, ayanamsa=..., weighted=False)` —
  new `weighted=` flag: `False` (default) uses the lightweight
  `yoga_strength`; `True` uses `yoga_strength_weighted`.
- **Gaja-Kesari cancellation** — the yoga is no longer emitted if
  Jupiter or the Moon is debilitated. (Combustion / enemy-sign also
  weaken it per some texts, but those need an orb / a friendship table
  that the sign-index data doesn't provide, so only the debilitation
  check is applied.)
- **Neecha-Bhanga refinement** — `_detect_extended` now also accepts
  `planet_lons=` (supplied by the chart-level `detect_yogas`); when
  present, Neecha-Bhanga also fires if the debilitated planet is
  exalted in its navamsa (D9), one of the classical cancellation
  conditions that sign data alone can't determine. `_chart_signs` now
  returns the sidereal longitudes alongside the sign indices.
- 6 new tests in `tests/test_vedic_yogas_lesser.py` (weighted strength,
  the `weighted=` flag, Gaja-Kesari cancellation, navamsa-exaltation
  Neecha-Bhanga). The existing yoga tests are unaffected.

### Changed (Task 034 — accidental-dignity score-rule refactor)
- `AccidentalDignity.getScoreProperties` rewritten: the 15 "+N if flag
  else 0" rules (peregrine excepted) now come from a single
  `(key, flag, plus, otherwise)` table iterated in one loop; the ~7
  context-dependent rules (Sun-excluded light/no-under-sun/direction,
  3-way haiz, the feral↔void interaction, Moon-only via-combusta,
  orientality's diurnal/nocturnal split) stay inline and clearly
  commented. **Behaviour is identical** — verified by a regression
  test that pins the score and the full Sun score-properties dict for a
  fixed chart. The method dropped from ~88 LOC of scattered assignments
  to ~55 with the rule values centralised; cyclomatic complexity down
  considerably. Closes the `getScoreProperties` complexity hotspot from
  the platform review.
- New `test_score_properties_regression` in
  `tests/test_dignities_accidental_factors.py` (the behaviour anchor).

### Added (Task 033 — per-factor tests for the smoke-only modules)
- `tests/test_protocols_temperament_factors.py` and
  `tests/test_dignities_accidental_factors.py` — exercise the
  temperament factor/modifier engine and the `AccidentalDignity`
  engine across several charts × the seven classical planets, asserting
  structural invariants (factor element keys, modifier shape,
  temperament/quality partitions, score-property dicts, active ⊆ all
  score properties, flag methods don't raise). No production code
  changed. `dignities/accidental.py` coverage 84% → **100%**;
  `protocols/temperament.py` 80% → **99%** (the one remaining line is
  the "skip a planet already counted in House 1" branch — needs a
  contrived chart and isn't worth chasing). Overall coverage 92% →
  **94%**. Closes the "smoke-tested only" gap flagged in the platform
  review.

### Added (Task 032 — lesser Vedic yogas + yoga strength scoring)
- `mayaastrolib/vedic/yogas.py` `detect_yogas` now also returns a set of
  **lesser yogas**: Amala (a benefic in the 10th from the Lagna/Moon),
  Adhi (benefics in the 6th/7th/8th from the Moon), Lakshmi (9th lord
  dignified in a kendra/trikona), Saraswati (Jupiter+Venus+Mercury all
  in kendras/trikonas/2nd), Kahala (4th and 9th lords in mutual
  kendras), Vasumati (all benefics in upachayas 3/6/10/11),
  Sunapha/Anapha/Durudhara (planets in the 2nd/12th from the Moon), and
  Vesi/Vasi/Ubhayachari (planets in the 2nd/12th from the Sun). Internal
  `_detect_lesser`.
- `yoga_strength(yoga, planet_signs, asc_sign)` → a small integer
  strength score: +2 if a yoga planet is in its own or exaltation sign,
  −2 if debilitated, +1 if in a kendra/trikona from the Lagna.
- `detect_yogas_with_strength(chart, ayanamsa=...)` → `(YogaResult,
  strength)` pairs sorted by descending strength. New `UPACHAYA_HOUSES`
  constant.
- 28 unit tests in `tests/test_vedic_yogas_lesser.py`; the integration
  test in `tests/test_vedic_yogas_extended.py` updated to include the
  new yoga names.
- Still deferred: a classical Shadbala-weighted yoga strength, finer
  Neecha-Bhanga conditions, Gaja-Kesari cancellation, and the long tail
  of named yogas.

### Added (Task 031 — Ashtakavarga prastara, shodhana, kakshya)
- `mayaastrolib/vedic/ashtakavarga.py` extended:
  - `bhinnashtakavarga_prastara(planet, signs)` — the per-contributor
    breakdown `{contributor: 12-cell list of 0/1}`; summing the eight
    rows reproduces `bhinnashtakavarga`.
  - `trikona_shodhana(bav)` — trine reduction: for each of the four
    trine groups, subtract the minimum of the three cells from all
    three. (Documented: this is the "subtract the min" form, not the
    harsher "zero the whole trine if any member is zero" variant.)
  - `ekadhipatya_shodhana(bav, occupied_signs)` — co-rulership
    reduction applied to the trikona-reduced BAV across the five
    co-rulership sign pairs. (One common variant; documented.)
  - `shodhita_sarvashtakavarga(planet_signs, lagna_sign)` — the SAV
    after trikona + ekadhipatya reduction of each BAV.
  - `kakshya_of(sidereal_lon)` — which of the 8 kakshyas (3°45' each,
    ruled in the fixed order Saturn/Jupiter/Mars/Sun/Venus/Mercury/
    Moon/Lagna) a longitude falls in.
  - `kakshya_transit_active(prastara, transiting_lon)` — for transit
    timing: returns `(kakshya_lord, active)` where `active` is True iff
    that kakshya's lord (as an Ashtakavarga contributor) places a bindu
    in the transited sign in the given prastara.
  - New constants `TRIKONA_GROUPS`, `EKADHIPATYA_PAIRS`,
    `KAKSHYA_LORDS`, `KAKSHYA_WIDTH_DEG`.
- 35 unit tests in `tests/test_vedic_ashtakavarga_shodhana.py`.

### Added (Task 030 — KP sub-sub-lord, horary, Ruling Planets)
- `mayaastrolib/vedic/kp.py` extended:
  - `sub_sub_lord_at(sidereal_lon)` and `sub_lord_at(..., with_sub_sub=
    True)` — the **4th level** of the KP hierarchy. Within a sub (whose
    width is proportional to its lord's Vimshottari years), the span is
    divided again into 9 parts proportional to the Vimshottari years,
    the sequence starting from the sub's own lord. New
    `_vimshottari_sequence_from` / `_proportional_lord` helpers (the
    sub-level lookup is now expressed in terms of the latter too).
  - `prashna_to_longitude(prashna_number)` — maps a horary number
    1..249 to the midpoint longitude of the corresponding 249-row KP
    segment; raises `ValueError` outside `[1, 249]`.
  - `kp_horary(prashna_number)` — returns `{prashna, lagna_longitude,
    lagna}` where `lagna` is the `sub_lord_at(..., with_sub_sub=True)`
    chain at that longitude. (A full horary chart with house cusps from
    a fixed Ascendant degree is a follow-up.)
  - `ruling_planets(date, pos, ayanamsa=AYANAMSA_KRISHNAMURTI)` — the
    KP Ruling Planets at a question moment: `day_lord` (weekday lord),
    `moon_sign_lord` / `moon_star_lord` / `moon_sub_lord`,
    `lagna_sign_lord` / `lagna_star_lord` / `lagna_sub_lord`, plus
    `"all"` (the distinct set). Uses the civil-date weekday (the true
    astrological day runs sunrise→sunrise — a documented approximation)
    and builds a chart under the KP ayanamsa.
- 13 unit tests in `tests/test_vedic_kp_extras.py`.
- Deferred: a full horary chart (house cusps from a fixed Asc), KP
  significators / cuspal interlinks.

### Added (Task 029 — Tajika Harsha/Panchavargiya Bala + aspects)
- `mayaastrolib/vedic/tajika_bala.py`:
  - `harsha_bala(chart, ayanamsa=...)` → the "joy strength": a
    five-component, 0-or-5-per-component score (max 25) per classical
    planet — hemisphere (diurnal planet above the horizon / nocturnal
    below), gender (masc planet in odd sign / fem in even / neutral
    always), dignity (own or exaltation sign), own decanate (D3 lord =
    the planet), and planetary joy (in its joy house). Returns
    `{planet: {"components": {...}, "total": int}}`.
  - `panchavargiya_bala(chart, ayanamsa=...)` → the "five-fold
    strength": Kshetra + Uchcha (exaltation-distance, 0..20) + Hadda
    (term) + Drekkana + Navamsa sub-balas, summed. **The component
    scales are a documented simplification** — good for relative
    comparison (e.g. picking the Lord of the Year by the canonical
    rule) but not a verified replica of any single text. `tajika.
    lord_of_year` keeps its own simpler heuristic; callers who want the
    Panchavargiya pick can compute it from this.
- `mayaastrolib/vedic/tajika_aspects.py`:
  - `tajika_aspects(chart)` → detects **Ithasala** (within combined
    deeptamsha orb of a Ptolemaic aspect, faster planet applying),
    **Isharafa** (within orb, faster planet separating), and **Nakta**
    (translation of light — a faster planet within orb of two slower
    planets that aren't within orb of each other). Returns a list of
    frozen `TajikaAspect(kind, planets, aspect_angle, orb, separation)`.
    Needs a real ephemeris chart (planets must have `lonspeed`) — a
    symbolic chart raises `ValueError`. Deeptamshas: Sun 15°, Moon 12°,
    Mars 8°, Mercury 7°, Jupiter 9°, Venus 7°, Saturn 9°; pair-orb =
    their average.
- 16 unit tests in `tests/test_vedic_tajika_bala.py` (Harsha component
  invariants, joy-house cross-check, Panchavargiya totals, the
  `_uchcha`/`_kshetra` helpers, Tajika-aspect shape/orb invariants,
  `_pair_orb`/`_closest_aspect`, symbolic-chart rejection).
- Still deferred: a fully reference-faithful Panchavargiya component
  scheme; the rest of the 16 Tajika yogas (Yamaya, Kambula,
  Gairi-Kambula, Khallasara, Rudda, …).

### Added (Task 028 — full(er) Tajika Saham table)
- `mayaastrolib.vedic.tajika.sahams()` now returns **14** Sahams (was
  4): Punya, Vidya, Yasas, Karma, Pitri, Matri, Bhratri, Putra,
  Kalatra, Jeeva, Vivaha, Vyapara, Roga, Bandhu. Refactored to a
  data-driven `_SAHAM_FORMULAS` table (`name → (term_a, term_b,
  reversible)`, where a term is a planet ID, the literal `"Asc"`, or
  another Saham name) — adding more is now one table row. New
  `SAHAM_*` constants exported for the new names.
- The Saham formulas vary across sources; these follow Tajika
  Neelakanthi as commonly reproduced (B.V. Raman, *Varshaphala*). This
  is still a curated subset of the ~50-Saham list — the remainder
  remains a follow-up. Yasas references the chart's Punya Saham (handled
  by ordering it last in the table).
- Tests in `tests/test_vedic_tajika_balas.py` updated: the 4-Saham
  check became a 14-Saham check, plus a `test_yasas_uses_punya_saham`
  verifying the Saham-references-Saham resolution.

### Changed (Task 027 — zodiac-aware predictives under sidereal mode)
- `Chart.solarReturn()` and `Chart.profected(target_date=...)` now work
  correctly on **sidereal** charts. Previously the solar-return search
  (`ephem.tools.solarReturnJD`) always compared against the *tropical*
  Sun while the natal-Sun longitude it was given was sidereal — a
  zodiac mismatch that produced a wrong return moment. `zodiac` and
  `ayanamsa` now thread through `tools.solarReturnJD` →
  `eph.nextSolarReturn`/`prevSolarReturn` → `ephem.nextSolarReturn`/
  `prevSolarReturn`, and `Chart` passes its own `zodiac`/`ayanamsa`.
  The returned solar-return chart is also built with the same
  `zodiac`/`ayanamsa` as the natal. Tropical charts are unaffected
  (the new args default to tropical).
- `Chart.profected()` already preserved the chart's `zodiac`/`ayanamsa`
  via `copy.deepcopy`; the `target_date=` path now uses the
  zodiac-correct solar-return interpolation too.
- `Chart.directions()` now **raises `NotImplementedError` on a sidereal
  chart** — primary directions are an equatorial-coordinate technique
  and the ecliptic-longitude conversion would carry the ayanamsa shift
  into the right-ascension values. (It's also not a Vedic technique.)
  Build the chart with the default zodiac for directions.
- 11 unit tests in `tests/test_sidereal_predictives.py` (sidereal SR
  returns to natal sidereal Sun; SR/profected inherit zodiac+ayanamsa;
  birth-year SR ≈ birth; tropical SR/profected/directions unchanged;
  sidereal `directions()` raises).

### Added (Task 024b — Tajika Muntha, Lord of Year, Sahams)
- `mayaastrolib/vedic/tajika.py` extended:
  - `muntha(natal_chart, target_year, ayanamsa=...)` → the Muntha (the
    progressed point that sits in the natal Lagna's sign at birth and
    advances one sign per year of life). Returns `{sign_idx, sign, lord}`.
  - `lord_of_year_candidates(annual_chart, natal_chart, target_year,
    ayanamsa=...)` → the 5 Varsheshwara candidates in traditional
    priority order (Muntha lord, annual-Lagna lord, Sun-sign lord,
    natal-Lagna lord, Trirashi-pati) as `(label, planet_id)` pairs.
  - `lord_of_year(...)` → picks the candidate with the highest simple
    own/exalted/in-a-kendra strength tally (ties → Muntha-first).
    **Heuristic** — the canonical rule uses Panchavargiya Bala, which
    is a follow-up.
  - `sahams(annual_chart, ayanamsa=...)` → the core Tajika Sahams as
    `{name: sidereal_longitude}` — **Punya** (Moon−Sun+Asc by day,
    reversed by night), **Vidya** (the reverse of Punya), **Yasas**
    (Jupiter−Punya+Asc by day, reversed by night), **Karma**
    (Mars−Sun+Asc by day, reversed by night). All normalised to
    `[0, 360)`.
  - `_trirashi_pati`, `SAHAM_PUNYA`/`SAHAM_VIDYA`/`SAHAM_YASAS`/
    `SAHAM_KARMA` constants exported.
- 21 new unit tests in `tests/test_vedic_tajika_balas.py` (Muntha
  advance per year, the 5-candidate list, Lord-of-Year ∈ candidates,
  the Trirashi-pati helper, the 4 Sahams, Punya/Vidya reversal,
  Punya-matches-formula, tropical-vs-sidereal-chart agreement).
- Still deferred (a further follow-up): the full ~50 Saham table,
  Harsha Bala, Panchavargiya Bala, and the Tajika aspects (ithasala,
  isharafa, etc.).

### Added (Task 026b — extended Vedic yogas)
- `mayaastrolib/vedic/yogas.py` now also detects, on top of the original
  8 (Pancha Mahapurusha + Gaja-Kesari + Budha-Aditya + Chandra-Mangala):
  - **Raja Yoga** — a kendra lord (1/4/7/10) conjunct a distinct trikona
    lord (1/5/9).
  - **Dhana Yoga** — two distinct wealth-house (2/5/9/11) lords conjunct.
  - **Vipareeta Raja Yoga** — Harsha (6th lord), Sarala (8th lord),
    Vimala (12th lord), each firing when that dusthana lord is itself
    in a dusthana (6/8/12).
  - **Neecha Bhanga Raja Yoga** — a debilitated planet whose
    debilitation is cancelled by the dispositor, or the would-be-exalted
    planet, being in a kendra from the Ascendant.
  - **Kemadruma Yoga** — no graha (among Mars/Mercury/Jupiter/Venus/
    Saturn) in the 2nd or 12th sign from the Moon.
- New public helpers: `sign_lord(sign_idx)`, `house_lord(house_num,
  asc_sign)`, `houses_ruled_by(planet, asc_sign)`. New constants:
  `TRIKONA_HOUSES`, `DUSTHANA_HOUSES`, `DHANA_HOUSES`.
- `detect_yogas` returns the union of the original and extended sets;
  internally `_detect` + `_detect_extended`, both pure functions over
  `(planet_signs, asc_sign)`.
- 17 new unit tests in `tests/test_vedic_yogas_extended.py` (the helpers
  + each new yoga's positive/negative cases + integration with a real
  chart + tropical-vs-sidereal agreement). Existing 23 yoga tests
  unaffected.
- Still deferred: yoga strength scoring, mutual-aspect/parivartana Raja
  Yogas, finer Neecha-Bhanga conditions, Gaja-Kesari cancellation, and
  the many named lesser yogas.

### Added (Task 025 — Vedic KP sub-lords)
- `mayaastrolib/vedic/kp.py` — the Krishnamurti Paddhati Star-Sub
  sub-lord system.
  - `kp_table()` → the canonical **249-row** sub-lord table. Each row
    is `{start_lon, end_lon, sign, sign_lord, nakshatra, star_lord,
    sub_lord}`; the rows tile `[0, 360)` with no gaps. (249 = the 243
    Star×Sub segments + the 6 sign boundaries — 30°/90°/150°/210°/270°
    /330° — that each bisect a sub-segment; an import-time assert
    enforces the count.)
  - `sub_lord_at(sidereal_lon)` → `{longitude, sign, sign_lord,
    nakshatra, star_lord, pada, sub_lord}` for any sidereal longitude.
  - `kp_sublords(chart, ayanamsa=AYANAMSA_KRISHNAMURTI)` → the chains
    for the 7 classical planets + the Ascendant. Defaults to the KP
    (Krishnamurti) ayanamsa for tropical charts; for KP-correct results
    build the chart with `ayanamsa=AYANAMSA_KRISHNAMURTI`.
  - `SIGN_LORDS` — the traditional 7-planet sign rulerships.
- 14 unit tests in `tests/test_vedic_kp.py`: the 249-row count, that
  the table tiles 360° contiguously, sign-lord consistency, the
  `sub_lord_at(0.0)` chain, the bisected-sub case at the 30° boundary,
  consistency with `nakshatras.of_longitude`, and the chart-level
  `kp_sublords` (sidereal vs tropical-with-KP-ayanamsa agreement).
- Deferred to a follow-up: sub-sub-lord (4th level), KP horary
  (prashna 1..249), Ruling Planets, KP significators / cuspal
  interlinks.

### Added (Task 017b — additional ayanamsas)
- `mayaastrolib/vedic/ayanamsa.py` now supports four ayanamsas, not
  just Lahiri: `lahiri`, `krishnamurti` (KP), `raman`, `fagan_bradley`
  (Western sidereal). New constants `AYANAMSA_KRISHNAMURTI`,
  `AYANAMSA_RAMAN`, `AYANAMSA_FAGAN_BRADLEY` added to `const`;
  `LIST_AYANAMSAS` extended to all four.
- `Chart(zodiac=ZODIAC_SIDEREAL, ayanamsa=...)` accepts any of them
  (the validation was already there; the list just got longer).
- `ayanamsa.get(ayanamsa, date)` is now a generic dispatcher backed by
  the `_AYANAMSA_TO_SWE_MODE` table; the per-name functions
  (`lahiri`/`krishnamurti`/`raman`/`fagan_bradley`) are thin wrappers.
  This collapses the old hardcoded Lahiri-only `get` into a clean
  table-driven form — all downstream consumers (`to_sidereal`,
  `to_tropical`, `_sidereal_calc_ut` in `ephem/swe.py`) work with any
  ayanamsa unchanged.
- 11 unit tests in `tests/test_vedic_ayanamsa_variants.py`.

### Added (Task 026 — Vedic Yoga Detection)
- `mayaastrolib/vedic/yogas.py` — named planetary-combination detection.
  - `detect_yogas(chart, ayanamsa=...)` → list of frozen
    `YogaResult(name, sanskrit, planets, description)`. Handles both
    tropical and sidereal charts.
  - Detects the 5 Pancha Mahapurusha yogas — **Ruchaka** (Mars),
    **Bhadra** (Mercury), **Hamsa** (Jupiter), **Malavya** (Venus),
    **Sasha** (Saturn): the planet in its own or exaltation sign *and*
    in a kendra — plus **Gaja-Kesari** (Jupiter 1st/4th/7th/10th from
    the Moon), **Budha-Aditya** (Mercury+Sun same sign), and
    **Chandra-Mangala** (Moon+Mars same sign).
  - Kendras are Whole-Sign: `(planet_sign − asc_sign) % 12 + 1 ∈
    {1, 4, 7, 10}`, regardless of the chart's `hsys` — the Vedic
    convention.
  - Classical Vedic dignity tables (`OWN_SIGNS`, `EXALTATION_SIGN`,
    `DEBILITATION_SIGN`) plus `is_in_own_or_exaltation`,
    `is_debilitated`, `house_from` helpers exported.
- 23 unit tests in `tests/test_vedic_yogas.py`: the dignity/house
  helpers, the core detection logic exercised directly over
  sign-index dicts (no ephemeris), each yoga's positive and negative
  cases, the kendra requirement, and the tropical-vs-sidereal-chart
  agreement.
- Deferred to a follow-up: Raja yogas (kendra-trikona lord
  conjunction/aspect), Dhana yogas, Vipareeta Raja yogas, Neecha
  Bhanga (debilitation cancellation), Kemadruma, and the various
  yoga-cancellation conditions.

### Added (Task 024 — Vedic Tajika: varshapravesh + Mudda dasha)
- `mayaastrolib/vedic/tajika.py` — the core Tajika annual-chart slice.
  - `varshapravesh(natal_chart, target_year, ayanamsa=...)` → the
    `Datetime` when the *sidereal* Sun returns to the natal sidereal
    Sun longitude in `target_year`. This is NOT the same as the
    tropical solar return — the ayanamsa drifts, so the two diverge by
    up to ~a day over decades — so it runs its own sidereal search
    (`sidereal_sun_return_jd`, the Newton-style loop from
    `ephem.tools.solarReturnJD` adapted to sidereal longitudes).
  - `mudda_dasha(varshapravesh_date, ayanamsa=...)` → the 9 Mudda
    (Varsha Vimshottari) periods: the 365.25-day year divided among the
    9 Vimshottari lords in the standard proportions, the sequence
    starting from the lord of the nakshatra the Moon occupies at the
    varshapravesh moment. Reuses `dasha.DashaPeriod` /
    `VIMSHOTTARI_ORDER` / `VIMSHOTTARI_YEARS`. Unlike the natal
    Vimshottari, the first Mudda period is full-length (the year starts
    fresh at varshapravesh).
- `Chart.solarReturn` is deliberately **left tropical-only** — the
  zodiac-aware refactor of the Hellenistic solar return is a separate
  decision (see Task 017's CHANGELOG note). Tajika sidesteps it with
  its own sidereal search.
- 13 unit tests in `tests/test_vedic_tajika.py`: sidereal-return
  convergence to ≤1″, birth-year varshapravesh ≈ birth moment,
  consecutive years ≈365.25 days apart, Sun-at-varshapravesh = natal
  sidereal Sun, tropical-natal-chart agreement, and the full Mudda
  dasha structure (9 periods, sum 365.25 days, lord order from the
  varshapravesh-Moon nakshatra, proportional durations, contiguous).
- Deferred to a follow-up (Task 024b): Varsheshwara (lord of year),
  Harsha Bala, Panchavargiya Bala, the ~50 Tajika Sahams, and the
  Tajika aspects (ithasala etc.).

### Added (Task 023 — Vedic Upagrahas)
- `mayaastrolib/vedic/upagrahas.py` — the "sub-planet" sensitive
  points.
  - `sun_derived_upagrahas(sun_sidereal_lon)` → the 5 Phaladeepika
    points (Dhuma = Sun+133°20', Vyatipata = 360°−Dhuma, Parivesha
    = Vyatipata+180°, Indrachapa = 360°−Parivesha, Upaketu =
    Indrachapa+16°40'). The chained relations hold: Dhuma+Vyatipata
    = 360°, Indrachapa+Parivesha = 360°.
  - `gulika_longitude(chart, ayanamsa=...)` → Gulika/Mandi via the
    weekday-portion ascendant method (School A): the day or night
    span is split into 8 parts ruled in weekday order; Gulika is the
    sidereal Ascendant at the start of the Saturn-ruled part. Uses
    the civil-date weekday (the true astrological day runs
    sunrise→sunrise — a documented approximation).
  - `upagrahas(chart, school="B", ayanamsa=...)` → dict of
    `UpagrahaResult(name, sidereal_longitude, sign, deg_in_sign)`.
    `school="B"` (default) = the 5 Sun-derived; `school="A"` adds
    Gulika.
- 17 unit tests in `tests/test_vedic_upagrahas.py` covering the
  School B formulas (including the chained-relation invariants),
  Gulika day-vs-night divergence, the Saturday-day Gulika ≈
  sunrise-ascendant check, the entry-point school selection, and
  result-field consistency.

### Added (Task 022 — Vedic Sade Sati)
- `mayaastrolib/vedic/sadesati.py` — the ~7.5-year Saturn-over-Moon
  transit phase detector.
  - `sade_sati(natal_moon_sign, target, ayanamsa=...)` → frozen
    `SadeSatiPhase(active, phase, saturn_sign, natal_moon_sign,
    severity)`. Phases: `"rising"` (Saturn 12th from Moon,
    moderate), `"peak"` (Saturn in Moon's sign / janma shani,
    intense), `"setting"` (Saturn 2nd from Moon, mild),
    `"not-active"`.
  - `sade_sati_for_year(natal_moon_sign, year, ayanamsa=...)` —
    checks the year's midpoint (July 1, 12:00 UTC).
  - `small_panoti(natal_moon_sign, target, ayanamsa=...)` →
    `"ashtama_shani"` (Saturn 8th from Moon), `"kantaka_shani"`
    (Saturn 4th from Moon), or `None`.
  - `saturn_sidereal_sign(target, ayanamsa=...)` — Saturn's
    sidereal sign index 0..11.
- `natal_moon_sign` accepts either a sign index (0..11) or a
  sign-name string. Saturn's geocentric longitude is
  location-independent at the day level, so no GeoPos is needed.
- 22 unit tests in `tests/test_vedic_sadesati.py` covering the
  phase logic directly (no ephemeris), sign normalisation, pinned
  Saturn sidereal positions (Aquarius mid-2024, Pisces mid-2025,
  Sagittarius 2020), all four phases, both panotis, and the
  int-vs-name input equivalence.

### Added (Task 021 — Vedic Ashtakavarga)
- `mayaastrolib/vedic/ashtakavarga.py` — the bindu (benefic-point)
  system per BPHS ch. 66.
  - `ASHTAKAVARGA_TABLES` — the canonical Prastara tables for all 7
    planets (per-planet totals Sun 48 / Moon 49 / Mars 39 /
    Mercury 54 / Jupiter 56 / Venus 52 / Saturn 39, summing to the
    337 SAV grand-total invariant; enforced by import-time asserts).
  - `bhinnashtakavarga(planet, signs)` — the 12-cell BAV histogram
    for one planet given the 8 contributor sign indices (7 planets +
    Ascendant). Sums to the planet's canonical total.
  - `sarvashtakavarga(planet_signs, lagna_sign)` — the SAV: per-sign
    sum of the 7 planetary BAVs. Returns `{per_rasi, grand_total,
    by_planet}`; `grand_total` is always 337.
  - `ashtakavarga(chart, ayanamsa=...)` — chart-level entry point;
    handles both tropical and sidereal charts.
- 16 unit tests in `tests/test_vedic_ashtakavarga.py` covering the
  table-total invariants, the BAV-is-a-fixed-histogram property
  (BAV rotates with positions, sums constant), a hand-computed
  micro case, and the SAV=337 invariant for arbitrary positions.

### Added (Task 020 — Vimshottari Dasha)
- `mayaastrolib/vedic/dasha.py` — Vimshottari Mahadasha computation.
  - `vimshottari(chart, target=None, ayanamsa=...)` — main entry
    point. Returns the full 120-year MD sequence plus, if target
    given, the MD/AD/Pratyantar active at that moment.
  - `antardashas(md)` — the 9 Antardashas within a Mahadasha.
  - `pratyantar_dashas(ad)` — the 9 Pratyantars within an
    Antardasha.
  - `DashaPeriod` and `VimshottariResult` are frozen dataclasses.
- `VIMSHOTTARI_YEARS` constants (Ketu 7 / Venus 20 / Sun 6 / Moon
  10 / Mars 7 / Rahu 18 / Jupiter 16 / Saturn 19 / Mercury 17 = 120)
  exposed for downstream use. `DAYS_PER_VIMSHOTTARI_YEAR = 365.25`
  per BPHS / Muhurta Chintamani convention.
- 19 unit tests in `tests/test_vedic_dasha.py` covering birth
  balance (boundary, midpoint), MD sequence (120-year span, lord
  order, durations), AD nesting (9 ADs sum to MD, Venus AD = 20/120
  of MD), Pratyantar nesting, current-period lookup
  (target-at-birth returns first MD; outside-range returns None),
  and the tropical-vs-sidereal-chart agreement invariant.

### Added (Task 019 — Vedic divisional charts / Shodashavarga)
- `mayaastrolib/vedic/divisional.py` — full BPHS Shodashavarga.
- 15 *computed* vargas + D1 (rasi convenience):
  - **D1** rasi, **D2** hora, **D3** drekkana, **D4** chaturthamsa,
    **D7** saptamsa, **D9** navamsa, **D10** dasamsa, **D12**
    dvadasamsa, **D16** shodasamsa, **D20** vimsamsa, **D24**
    chaturvimsamsa, **D27** bhamsa, **D30** trimsamsa (unequal
    segments), **D40** khavedamsa, **D45** akshavedamsa,
    **D60** shastiamsa.
- Each function takes a sidereal longitude and returns sign index
  0..11. Pure functions; no Chart, no Datetime, no Ayanamsa.
- `all_vargas(chart, ayanamsa=...)` — chart-level entry point
  returning `{varga_name: {planet_id: sign_idx}}`. Handles
  tropical-or-sidereal input.
- `VARGA_NAMES` and `SIGN_NAMES` constants exported for
  downstream display.
- Internal `_segment(deg, n)` helper uses `int(deg * n / 30)`
  rather than `int(deg // (30/n))` to avoid the float-imprecision
  bug at boundaries where `30/9 = 3.333...3335` makes
  `10.0 // 3.333... = 2` instead of the correct `3`.
- 25 unit tests in `tests/test_vedic_divisional.py` covering
  hora, drekkana, navamsa (full Aries progression + Taurus +
  Gemini starts), trimsamsa (both parities × all 5 segments),
  dvadasamsa, shastiamsa, and the chart-level `all_vargas`.

### Added (Task 018 — Vedic nakshatras)
- `mayaastrolib/vedic/nakshatras.py` — 27-nakshatra arithmetic.
  - `NAKSHATRA_NAMES` — canonical Sanskrit names in BPHS order
    (Ashwini, Bharani, …, Revati).
  - `NAKSHATRA_LORDS` — Vimshottari rulership cycle (Ketu, Venus,
    Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury × 3).
  - `of_longitude(sidereal_lon)` — sidereal-longitude →
    `Nakshatra`. Handles negative longitudes and >360° via modulo;
    raises `ValueError` on NaN/inf.
  - `janma_nakshatra(chart, ayanamsa=...)` — natal Moon's nakshatra.
    Accepts both tropical and sidereal charts; tropical input is
    shifted via `to_sidereal` before lookup.
  - `tarabala(natal_nak, transit_nak)` — 1..9 tara cycle position
    per Muhurta Chintamani 6.6.
- `Nakshatra` is a frozen dataclass — `name`, `lord`, `pada`, `index`.
- 17 unit tests in `tests/test_vedic_nakshatras.py` covering
  boundaries, padas, janma_nakshatra (tropical ↔ sidereal
  agreement), and tarabala.

### Added (Task 017 — Vedic foundation)
- New `mayaastrolib/vedic/` package — foundation for the Phase 2 Vedic
  Jyotisha extension. This task ships the foundation only; downstream
  modules (nakshatras, divisional charts, dasha, ...) follow in
  Tasks 018+.
- `mayaastrolib.vedic.ayanamsa.lahiri(date)` — Lahiri ayanamsa in
  degrees at a given date. Backed by
  `swisseph.get_ayanamsa_ut(SIDM_LAHIRI)`.
- `mayaastrolib.vedic.ayanamsa.to_sidereal(lon, date, ayanamsa=...)`
  and `to_tropical(lon, date, ayanamsa=...)` — longitude conversions.
- `mayaastrolib.vedic.ayanamsa.get(ayanamsa, date)` — dispatcher.
- `Chart` now accepts `zodiac=ZODIAC_TROPICAL|ZODIAC_SIDEREAL` and
  `ayanamsa=AYANAMSA_LAHIRI` kwargs. **Default is tropical — zero
  behaviour change for existing callers.** All 215 pre-Task-017 tests
  pass unchanged.
- New constants in `const`: `ZODIAC_TROPICAL`, `ZODIAC_SIDEREAL`,
  `AYANAMSA_LAHIRI`, `LIST_ZODIACS`, `LIST_AYANAMSAS`. Sanskrit
  aliases `RAHU = NORTH_NODE`, `KETU = SOUTH_NODE`.
- New tests: `tests/test_vedic_foundation.py` (23 tests) and
  `tests/golden/test_vedic_positions.py` (Skyfield-anchored sidereal
  positions for Einstein, Kahlo, Amundsen at ±2 arcmin tolerance).

### Architectural notes
- Sidereal mode is resolved at `Chart` construction. The
  `(set_sid_mode, calc_ut)` and `(set_sid_mode, houses_ex)` pairs are
  lock-guarded in `mayaastrolib/ephem/swe.py` (`_sidereal_calc_ut`,
  `_sidereal_houses_ex`) so concurrent sidereal chart construction
  with different ayanamsas is safe. Tropical charts bypass the lock
  entirely.
- Pars Fortuna and Syzygy under sidereal mode: PF is computed
  tropically (the diurnal check needs tropical Sun/MC for correct
  horizon math) and the resulting longitude is shifted via
  `to_sidereal`. The shift is mathematically equivalent to computing
  Asc+Moon−Sun directly in sidereal coordinates.
- Under sidereal mode, `Chart.solarReturn()`, `Chart.profected()`,
  and the predictives module are not yet zodiac-aware. Calling them
  on a sidereal chart will produce mixed-zodiac output. Phase 2
  follow-up tasks address these (see Task 024 for Tajika
  varshapravesh, which is the Vedic equivalent of solar returns).
- Additional ayanamsas (KP, Raman, Fagan-Bradley) deferred to a
  follow-up task. Lahiri only for now.

### Performance (Task 016 — fixstar_mag caching)
- `swisseph.fixstar2_mag` lookups are now cached per-process via
  `functools.cache` on a private `mayaastrolib.ephem.swe._fixstar_mag`
  wrapper. Previously, the underlying call reparsed `fixstars.cat`
  on every invocation. The cache is unbounded (~30–100 named stars
  at most; memory cost negligible) because magnitudes are
  immutable per-process.
  Measured speedup: **144×** on a 35-star pass (M2 / Python 3.14).
  Surfaced by the platform review (`docs/REVIEW-2026-05-08.md`).
- No public API change; `chart.getFixedStars()` /
  `chart.getFixedStar(name)` continue to behave identically.

### Added (Task 014 — golden test fixtures)
- Golden test suite at `tests/golden/`:
  - `test_planet_positions.py` — verifies mayaastrolib planet
    positions against frozen Skyfield references for three charts
    (Einstein, Kahlo, Amundsen). Tolerance ±2 arcminutes per
    `CLAUDE.md`. Closes the long-standing reliability gap
    surfaced by the platform review.
  - `test_self_consistency.py` — invariant tests for houses
    (sum to 360°, ordered cusps), planets (lon/signlon in range,
    obj.house set), aspects (orb non-negative, name in
    `ASPECT_NAMES.values()`), and symbolic charts (profected
    houses still span 360°, profected planets have None speed).
    Independent of any external reference.
  - `generate_fixtures.py` — Skyfield-based fixture generator,
    run manually by maintainers. Uses `de440s.bsp` (1849–2150)
    so all three charts are in range. Geocentric output to
    match Swiss Ephemeris.
  - `fixtures.json` — frozen reference data, committed.
  - `README.md` — methodology doc covering reference choice,
    LMT→UTC conversions, when to regenerate.
- `LICENSING.md` at repo root — clarifies the
  MIT-mayaastrolib + LGPL-pyswisseph + GPL/commercial-Swiss-Eph
  situation for users planning closed-source commercial use.
- `skyfield>=1.46` added to `[project.optional-dependencies] dev`
  — test infrastructure only, never installed for runtime.

### Fixed (Task 015 — GeoPos input validation)
- `GeoPos.__init__` now validates that latitude ∈ [-90, 90] and
  longitude ∈ [-180, 180], raising `ValueError` with the offending
  value if out of range. Previously, out-of-range coordinates
  (e.g. `GeoPos('200n00', '0w00')`) silently produced charts with
  mathematically nonsensical output. Surfaced by the platform
  review (`docs/REVIEW-2026-05-08.md`); regression tests in
  `tests/test_geopos_validation.py`.

### Added (Predictives as Chart methods — Task 013)
- `Chart.solarReturn(year=N)` extended to also accept
  `target_date=D` for "next solar return after this datetime"
  searches. Existing positional `solarReturn(2022)` calls keep
  working unchanged. Mutually exclusive args; `ValueError` if
  both or neither given.
- `Chart.directions()` — returns a
  :class:`mayaastrolib.predictives.primarydirections.PrimaryDirections`
  for this chart. Direct instantiation of the class remains
  supported and is *not* deprecated; this method is a
  discoverable Chart-level entry point. See PROJECT-LOG for the
  decision rationale.
- `Chart.arabicPart(part_id)` — convenience for
  :func:`mayaastrolib.tools.arabicparts.getPart`. Reads at the
  call site and shows up on `chart.` autocomplete.
- `Chart.planetaryHour(date=None)` — returns the planetary
  :class:`HourTable` for the chart's location at the given
  moment (defaults to the chart's date). Underlying
  :func:`getHourTable` remains available for date-and-position
  use without a chart.

### Deprecated
- `mayaastrolib.tools.arabicparts.getPart(ID, chart)` — use
  `chart.arabicPart(ID)` instead. Will be removed in 1.0.
  Implementation moved to private `_getPart_impl` so the chart
  method doesn't trip the warning. `recipes/arabicparts.py`
  updated to the new API.

### Notes (no change)
- `mayaastrolib.predictives.primarydirections.PrimaryDirections`
  remains a public class with no deprecation. Both
  `chart.directions()` and `PrimaryDirections(chart)` stay fully
  supported.
- `mayaastrolib.predictives.returns.nextSolarReturn` /
  `prevSolarReturn` remain undeprecated — they are useful
  primitives that take a chart + date pair and don't fit the
  "method on Chart" wrapper pattern as cleanly.
- `mayaastrolib.tools.planetarytime.getHourTable` /
  `getNow` / etc. remain undeprecated — they have legitimate
  date-and-position uses without requiring a chart.

### Documentation (Task 012 — audit investigations)
- `docs/AUDIT-INVESTIGATIONS.md` (new) — investigation findings for
  audit Items 15 (`House._OFFSET`) and 16 (`solarReturn(year)`
  semantics). Both items resolved as DOCUMENT actions; no behaviour
  change.
- `House._OFFSET` renamed to `House._CUSP_TOLERANCE_DEG` with a
  full docstring explaining the traditional **5° rule** (a longitude
  within 5° before a cusp belongs to the house starting at that
  cusp). The `_OFFSET` name is preserved as a backwards-compatible
  alias and slated for removal in 1.0. `House.inHouse` docstring
  expanded to make the `[cusp − 5°, cusp + 25°)` span explicit.
- `Chart.solarReturn(year)` docstring expanded — clarifies that
  the search anchors at January 1 of the target year and that the
  result is the calendar-year-anchored return, which equals the
  birthday-equivalent moment for any natal date. Concrete test
  cases preserved in `docs/AUDIT-INVESTIGATIONS.md`.
- `docs/IDEAS.md` records two Phase 2 follow-ups:
  configurable cusp tolerance, and a `solarReturnByAge(years)`
  companion. Both deferred — current behaviour is correct.

### Changed (internal — Task 011)
- `Chart.get(ID)` now dispatches by list membership against
  `const.LIST_HOUSES` and `const.LIST_ANGLES` rather than by
  string-prefix matching on `"House"`. No user-facing behaviour
  change; eliminates a brittleness if house IDs ever change format.
- `House.num` is now resolved from `const.LIST_HOUSES` once at
  construction (in `House.fromDict`) and cached on `self._num`,
  rather than parsed from `int(self.id[5:])` at access time.
  No user-facing behaviour change; eliminates the magic
  `len("House")` offset.

### Added (Symbolic charts and relocate semantics — Task 010)
- `Object.with_longitude(lon, *, preserve_speed=False)` — returns a new
  Object at the given longitude. By default clears `lonspeed` /
  `latspeed` to `None`, signalling that orbital dynamics are undefined
  for the new (symbolic) position. Pass `preserve_speed=True` when the
  new position meaningfully shares dynamics with the original (e.g.
  antiscia). Available on `GenericObject` (and therefore `Object`,
  `House`, `FixedStar`); `preserve_speed` is a no-op on classes
  without speed attributes.
- `Object.antiscion()` and `Object.cantiscion()` — return new objects
  representing the antiscion / contra-antiscion positions.
  Implemented as `with_longitude(..., preserve_speed=True)`.
- `Chart.profected(years=N)` and `Chart.profected(target_date=D)` —
  return a profected chart with `is_symbolic=True`,
  `symbolic_kind="profection"`, and properly cleared planet speeds.
  Mutually exclusive args; `ValueError` if both or neither given.
- `Chart.is_symbolic` (bool) and `Chart.symbolic_kind` (str) — flag
  whether a chart represents derived positions rather than
  computed-from-ephemeris ones. Default `False` / `None` for natal
  charts. `Chart.__repr__` surfaces the flag for visibility.
- `Object.movement`, `Object.isFast`, `Object.isDirect`,
  `Object.isRetrograde`, `Object.isStationary` now return `None` when
  `lonspeed is None` (symbolic positions). Previously they would
  return a bool computed from a stale or zero speed, masking the
  symbolic nature of the position.

### Fixed
- Profected charts no longer report stale natal speed / retrograde
  state. Previously `profections.compute()` rotated planet longitudes
  via in-place `relocate()` but left `lonspeed` / `latspeed`
  unchanged, so `isRetrograde()` on a profected chart returned the
  natal answer. The new `chart.profected()` correctly clears
  speed-derived attributes for symbolic positions, and
  `profections.compute()` now delegates to it (see Changed below).

### Deprecated
- `Object.relocate(lon)` — in-place mutation that leaves speeds
  stale. Use `obj.with_longitude(lon)` instead. Will be removed in
  version 1.0.
- `Object.antiscia()` and `Object.cantiscia()` — use
  `obj.antiscion()` / `obj.cantiscion()`. Will be removed in 1.0.
- `predictives.profections.compute(chart, date)` — use
  `chart.profected(target_date=date)`. Will be removed in 1.0.

### Changed (behaviour)
- `predictives.profections.compute(chart, date)` (the default
  `fixedObjects=False` path) now returns a chart with
  `is_symbolic=True` and cleared speeds, by delegating to
  `chart.profected(target_date=date)`. Callers that read
  `is_retrograde()` / `movement` from the result will now see `None`
  where they previously got the natal answer. This is the bug fix
  referenced under Fixed. The legacy `fixedObjects=True` branch is
  preserved for compatibility but emits the same deprecation warning.
- `_DualAccess` (the property/method compat wrapper from Task 006)
  passes `None` through unwrapped so `obj.movement is None` works.
  Tradeoff: calling `obj.movement()` on a symbolic object raises
  `TypeError` instead of emitting a `DeprecationWarning`. Symbolic
  objects are new in this task; no existing code does this.

### Added (Aspect API and standard lists — Task 009)
- `Aspect.name` — human-readable aspect name
  (e.g. `"Trine"`, `"Square"`, `"Sextile"`).
- `const.ASPECT_NAMES` — `dict[int, str]` mapping every canonical
  aspect angle (`MAJOR_ASPECTS + MINOR_ASPECTS`) to its name.
- `Aspect.activeObj` and `Aspect.passiveObj` — references to the
  original `Object` instances. Use these when you need per-planet
  properties (`movement`, `house`, `element`, etc.) from an Aspect.
  The legacy `Aspect.active` / `Aspect.passive` `AspectObject`
  snapshots are kept unchanged for backwards compatibility — note
  that `aspect.active.movement` is *aspect-relative*
  (Applicative / Separative / Exact), while
  `aspect.activeObj.movement` is *planet-relative*
  (Direct / Retrograde / Stationary). The two are distinct.
- Standard object lists in `mayaastrolib.const`:
  - `LIST_MODERN_PLANETS` — Sun through Pluto
  - `LIST_TROPICAL_DEFAULT` — modern planets + nodes + Chiron
  - `LIST_VEDIC_DEFAULT` — seven planets + Rahu + Ketu
  - `LIST_LIGHTS` — Sun, Moon
  - `LIST_PERSONAL_PLANETS` — Sun, Moon, Mercury, Venus, Mars
  - `LIST_SOCIAL_PLANETS` — Jupiter, Saturn
  - `LIST_TRANSPERSONAL` — Uranus, Neptune, Pluto
  - `LIST_LUNAR_NODES` — North Node, South Node
- Documentation page `docs/OBJECT-LISTS.md` describing the lists and
  guidance on when to use which.

### Changed
- `aspects.getAspect(obj1, obj2, aspList)` now returns `None` when no
  aspect exists within orb. Previously it returned a sentinel `Aspect`
  with `type == const.NO_ASPECT`. Internal call sites in
  `dignities/accidental.py`, `tools/chartdynamics.py`, and the
  `recipes/aspects.py` example were updated to handle `None`.

### Deprecated
- `aspects.getAspectOrSentinel()` — preserves the pre-Task-009
  sentinel-returning behaviour. Use `getAspect()` instead. Will be
  removed in version 1.0.

### Added
- `Chart.houseOf(obj)` returns the house containing an object. Accepts
  either an Object instance or a planet ID string.
- `Chart.objectsInHouse(house_id)` returns the list of objects in a
  named house.
- `Object.house` attribute, set on every Object during `Chart.__init__`.
- `House.objects` attribute, set on every House during `Chart.__init__`.
- Property-style access for `Object.movement`, `Object.gender`,
  `Object.faction`, `Object.element`, `Object.orb`, `Object.meanMotion`,
  `House.num`, `House.condition`, `House.gender`, `Aspect.movement`,
  `FixedStar.orb`, and `GenericObject.orb`. Implemented via the new
  `mayaastrolib._compat.property_with_method_compat` decorator, which
  emits a `DeprecationWarning` if the legacy method-style access is used.
- `docs/PROPERTY-MIGRATION.md` documents the migration and the 1.0
  removal plan.

### Deprecated
- Method-style access for the property-converted methods above
  (e.g. `obj.movement()`). Emits `DeprecationWarning`. Will be removed
  in version 1.0. Use `obj.movement` (no parens) instead.

### Fixed
- `if obj.movement:` (and similar truthiness checks on the converted
  getters) now reflects the actual value's truthiness instead of being
  unconditionally true because of the bound-method object's identity.

### Added (Datetime ergonomics)
- `Datetime.from_pydatetime(dt, utcoffset=None)` — construct from a
  Python `datetime.datetime`. Accepts naive (with explicit `utcoffset`)
  or timezone-aware. When both an aware `dt` and an explicit `utcoffset`
  are given, the explicit offset wins and `dt` is converted via
  `astimezone()` to that offset's wall-clock time.
- `Datetime.now(utcoffset='+00:00')` — current UTC moment expressed in
  the given offset. Does NOT handle DST; pass a fixed offset.
- `Datetime.to_pydatetime()` — convert to a timezone-aware
  `datetime.datetime`. Round-trips with `from_pydatetime` (whole
  seconds; sub-second precision is dropped, documented).

### Notes
- DST-aware timezone handling (e.g. via IANA names like
  `"Europe/Dublin"`) is deliberately deferred. See `docs/IDEAS.md`.

### Added (Dignities thread-safety + ergonomics)
- `terms_variant` and `faces_variant` keyword-only parameters on
  `dignities.essential` functions (`term`, `face`, `getInfo`,
  `isPeregrine`, `score`, `almutem`) for thread-safe variant
  selection. Defaults to the module-level globals (legacy path).
- `score(obj)`, `getInfo(obj)`, `isPeregrine(obj)` overloads
  accepting an Object instance directly. The legacy
  `(id, sign, lon)` form continues to work; missing args raise
  `TypeError` with a clear message.

### Deprecated
- `dignities.essential.setFaces()` and `setTerms()`. Module-level
  mutable state is not thread-safe. Use the new keyword parameters
  instead. These setters will be removed in version 1.0.

### Fixed
- Dignity calculations are now thread-safe when variants are passed
  as parameters. Previously, two threads computing with different
  terms variants could corrupt each other's results via shared
  module-level state.

## [0.3.0] — 2026-05-07

### Changed
- Renamed package from `flatlib` to `mayaastrolib`. The new canonical
  import is `from mayaastrolib import …`.

### Added
- Compatibility shim: `import flatlib` continues to work but emits a
  `DeprecationWarning`. Marked for removal in version 1.0.
- Compatibility shims for all subpackages: `flatlib.dignities`,
  `flatlib.ephem`, `flatlib.predictives`, `flatlib.protocols`,
  `flatlib.tools`, plus every leaf-module path
  (`flatlib.dignities.essential` etc.) via `sys.modules` aliases so
  both `import flatlib.X` and `from flatlib.X import Y` resolve.

### Deprecated
- The `flatlib` package name. Migrate to `mayaastrolib`. The shim
  will be removed in 1.0.

### Verified
- `pytest tests/` produces 47/47 passing both natively and via the
  shim.
- `chart.get(const.SUN)` returns identical positions
  (`<Sun Pisces +22:47:25 +00:59:51>`) when called via the new
  `mayaastrolib.*` paths and via the legacy `flatlib.*` paths.

### Changed
- Forked from flatangle/flatlib at upstream version 0.2.5
- Modernised build system: replaced setup.py with pyproject.toml
- Consolidated version source via importlib.metadata
- Configured ruff, mypy, pytest in pyproject.toml
- Set Python minimum version to 3.10
- Applied `ruff format` across the repo (50 files reformatted, no
  logic changes)
- Resolved ruff lint violations (auto-fixes plus hand-fixes for
  E712/E721/F402/B005/B006/B007/B905/A001/E402); deferred 23 UP031
  printf-format instances to docs/RUFF-DEBT.md

### Added
- GitHub Actions CI workflow (`.github/workflows/test.yml`) running
  ruff lint and pytest on Python 3.10/3.11/3.12
- Regression tests for eclipse functions (`tests/test_eclipses.py`)
- `docs/KNOWN-BUGS.md` documenting the eclipse fix
- Smoke tests for 12 previously zero-coverage modules: dignities
  (essential, accidental, tables), predictives (profections, returns,
  primarydirections), protocols (almutem, behavior, temperament),
  tools (arabicparts, chartdynamics, planetarytime). Coverage rose
  from 34% to 86%.

### Fixed
- Eclipse functions in `flatlib/ephem/swe.py` (`solarEclipseGlobal`,
  `lunarEclipseGlobal`) now pass `backwards=` instead of `backward=`
  to pyswisseph 2.x, which renamed the keyword. Previously
  `nextSolarEclipse` / `prevSolarEclipse` / `nextLunarEclipse` /
  `prevLunarEclipse` raised `TypeError` on every call. Same root
  cause as the upstream rise_trans patch (commit 856d26b on master)
  but for eclipse functions, which were missed at the time.

### Removed
- Legacy build scripts (scripts/build.py, scripts/clean.py, scripts/utils.py)
- Legacy packaging files (setup.py, setup.cfg, requirements.txt)
- README.rst (consolidated to README.md)
- Archived broken `contrib/topical_almuten.py` to
  `contrib/topical_almuten.py.broken` with a sibling README explaining
  the SyntaxError and how to revive the file later

## [0.2.6] - unreleased

Initial fork release. See [Unreleased] above.

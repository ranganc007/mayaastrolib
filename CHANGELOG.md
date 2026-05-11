# Changelog

All notable changes to this project will be documented in this file. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

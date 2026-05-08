# Changelog

All notable changes to this project will be documented in this file. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

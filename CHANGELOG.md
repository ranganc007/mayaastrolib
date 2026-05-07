# Changelog

All notable changes to this project will be documented in this file. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

(none — see 0.3.0 below)

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

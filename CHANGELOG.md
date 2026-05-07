# Changelog

All notable changes to this project will be documented in this file. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

### Removed
- Legacy build scripts (scripts/build.py, scripts/clean.py, scripts/utils.py)
- Legacy packaging files (setup.py, setup.cfg, requirements.txt)
- README.rst (consolidated to README.md)
- Archived broken `contrib/topical_almuten.py` to
  `contrib/topical_almuten.py.broken` with a sibling README explaining
  the SyntaxError and how to revive the file later

## [0.2.6] - unreleased

Initial fork release. See [Unreleased] above.

# Licensing

`mayaastrolib` itself is MIT-licensed (see `LICENSE`).

## Runtime dependencies and their licenses

`mayaastrolib` depends on `pyswisseph` at runtime. `pyswisseph` is a
Python wrapper around Swiss Ephemeris.

- **`pyswisseph`** itself is LGPL-licensed (the Python bindings).
- **Swiss Ephemeris** (the underlying C library and ephemeris data
  files) is dual-licensed:
  - **GPL v2+** for open-source projects, OR
  - **Commercial license** from Astrodienst (Switzerland) for
    closed-source commercial use. Pricing and terms:
    https://www.astro.com/swisseph/

### What this means for you

- **Using `mayaastrolib` for personal, research, or open-source
  projects:** comply with GPL on the Swiss Ephemeris portion, which
  is automatic for open-source / GPL-compatible projects.
- **Using `mayaastrolib` in a closed-source commercial product:**
  you must obtain a commercial Swiss Ephemeris license from
  Astrodienst. This is not unique to `mayaastrolib` — it applies to
  any astrology software that uses Swiss Ephemeris.

`mayaastrolib`'s MIT license is real, but it doesn't override the
licensing of its dependencies. The MIT license applies to the
astrology code in this repository; the GPL applies to the
ephemeris computation Swiss Ephemeris performs on your behalf.

## Development dependencies

These are NOT shipped to users; they are used only when developing
or testing `mayaastrolib`.

- **`skyfield`** (MIT) — used by
  `tests/golden/generate_fixtures.py` to generate independent
  astronomical reference data for golden tests. Not a runtime
  dependency.

## Future direction

If you require a license-clean astronomy backend for commercial
closed-source use, please file an issue. Building a pure-Python /
MIT astronomy backend (using e.g. VSOP87 or JPL DE-series via
Skyfield as runtime, not just dev) is a significant undertaking
but on the table for a future major version if there is real
demand.

# mayaastrolib

**A modern, typed, unified Western + Vedic astrology engine for Python 3.10+.**

[![PyPI](https://img.shields.io/pypi/v/mayaastrolib)](https://pypi.org/project/mayaastrolib/)
[![Python](https://img.shields.io/pypi/pyversions/mayaastrolib)](https://pypi.org/project/mayaastrolib/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/ranganc007/mayaastrolib/blob/master/LICENSE)

`mayaastrolib` is a Python library for Traditional (Hellenistic/Western) **and** Vedic
(Jyotisha) astrology, computed on the Swiss Ephemeris. It is a thoroughly modernised,
heavily extended fork of [`flatangle/flatlib`](https://github.com/flatangle/flatlib)
(MIT, unmaintained in practice since 2024).

> Original copyright © João Ventura, MIT licensed. Fork modifications © Rangan C., 2026.
> See [docs/FORK-RATIONALE.md](https://github.com/ranganc007/mayaastrolib/blob/master/docs/FORK-RATIONALE.md) for why this fork exists.

```python
from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos

date = Datetime('2015/03/13', '17:00', '+00:00')
pos = GeoPos('38n32', '8w54')
chart = Chart(date, pos)

sun = chart.get(const.SUN)
print(sun)
# <Sun Pisces +22:47:25 +00:59:51>
```

---

## What this fork adds over flatlib

`flatlib` is an excellent traditional-astrology core, but it stopped at Python-2-era
packaging, had no type hints, ~34% test coverage, and no sidereal/Vedic support.
`mayaastrolib` keeps the calculation core's correctness and rebuilds everything around it:

### 🪔 A Vedic (Jyotisha) subsystem — *new, ~4,500 LOC across 13 modules*

flatlib is tropical-only. `mayaastrolib` adds a full sidereal engine behind one switch
(`Chart(zodiac=const.ZODIAC_SIDEREAL, ayanamsa=const.AYANAMSA_LAHIRI)`):

| Module | What it computes |
|---|---|
| `vedic.ayanamsa` | Lahiri, Krishnamurti (KP), Raman, Fagan-Bradley |
| `vedic.nakshatras` | 27 nakshatras, lords, padas, tarabala |
| `vedic.divisional` | all 16 BPHS divisional charts (D1–D60 / Shodashavarga) |
| `vedic.dasha` | Vimshottari Mahadasha / Antardasha / Pratyantardasha |
| `vedic.ashtakavarga` | BAV/SAV (337-bindu system), prastara, trikona/ekadhipatya shodhana, kakshya |
| `vedic.yogas` | Pancha Mahapurusha, Raja, Dhana, Vipareeta, Neecha-Bhanga, Gaja-Kesari, lesser yogas + strength scoring |
| `vedic.sadesati` | Sade Sati phases + small-panoti (ashtama/kantaka shani) |
| `vedic.upagrahas` | Sun-derived upagrahas + Gulika/Mandi |
| `vedic.tajika` (+`_bala`, `_aspects`) | annual charts (Varshaphala), Mudda dasha, Sahams, Harsha/Panchavargiya Bala, Ithasala/Isharafa/Nakta |
| `vedic.kp` | Krishnamurti Paddhati — 249-row sub-lord table, sub-sub-lord, horary chart with cusps, Ruling Planets |
| `vedic.shadbala` | the six-fold planetary strength (Sthana, Dig, Kala, Cheshta, Naisargika, Drik) |

**On completeness:** the module list is broad, but some techniques ship a
*documented approximation* of the classical formula rather than a faithful
replica — notably the absolute Shadbala totals, `tajika_bala.panchavargiya_bala`,
`tajika.lord_of_year`, `upagrahas.gulika_longitude`, and the Saham table (14 of
roughly 50). Each says so in its own docstring, and
[docs/API-STABILITY.md](https://github.com/ranganc007/mayaastrolib/blob/master/docs/API-STABILITY.md)
tiers every `vedic` module by fidelity so you can tell at a glance which results
are determinate and which may be refined in a later release.

### ⚙️ Modern engineering — *the whole codebase brought to current standards*

- **Python 3.10+** baseline (3.12 target); all Python-2 compatibility code removed.
- **Type hints** across the public API, with a `py.typed` marker so downstream type checkers see them.
- **Modern packaging** — single `pyproject.toml` (PEP 621); `setup.py`, `requirements.txt`, and `README.rst` deleted.
- **ruff** format + lint and **mypy** (zero errors) in CI, both pinned for reproducibility.
- **CI** — GitHub Actions matrix on Python 3.10 / 3.11 / 3.12, plus a packaging job
  that installs the built wheel into a clean venv and computes a real chart.
- **An explicit, frozen public API** — see [docs/API-STABILITY.md](https://github.com/ranganc007/mayaastrolib/blob/master/docs/API-STABILITY.md).

### 🧪 Real correctness guarantees — *coverage 34% → 96%*

- **670+ tests**, all passing, **96% coverage** (80% CI floor).
- **Golden tests** anchor planet positions against [Skyfield](https://rhodesmill.org/skyfield/)
  — an *independent* ephemeris — at ±2 arc-minutes across 7 reference charts spanning
  1875–1961 and both hemispheres, in tropical *and* sidereal frames, plus
  astronomical-invariant suites (houses sum to 360°, cusps ordered, etc.).

### ✨ API ergonomics & correctness fixes

- `Chart.houseOf()`, `Chart.objectsInHouse()`, `Object.house`, `House.objects` (object↔house links).
- `Datetime.from_pydatetime()` / `.now()` / `.to_pydatetime()`.
- Immutable `Object.with_longitude()`, `Chart.profected()`, zodiac-aware `Chart.solarReturn()`.
- `GeoPos` now validates latitude/longitude ranges instead of silently producing a wrong chart.
- Thread-safe sidereal calculation (lock-guarded Swiss-Ephemeris global state).
- Eclipse-keyword bug fixed for pyswisseph 2.x; fixed-star magnitude lookups cached (144× speedup).

See [CHANGELOG.md](https://github.com/ranganc007/mayaastrolib/blob/master/CHANGELOG.md) for the full task-by-task history.

---

## Development & provenance

Most of the fork's commits — the entire Vedic subsystem, the modernisation, and the test
suite — were authored through **[Claude Code](https://claude.com/claude-code)** (Anthropic's
agentic CLI), with **minimal line-by-line human review** of individual diffs.

That makes the test discipline the load-bearing part of this project, by design — correctness
is *verified*, not taken on trust:

- **Structural tests** pin every public function's contract (670+ tests, 96% coverage).
- **Golden tests** anchor the astronomical output against [Skyfield](https://rhodesmill.org/skyfield/)
  — a completely independent ephemeris — at ±2 arc-minutes for known reference charts, so a
  wrong calculation fails CI rather than shipping silently.
- The library is **exercised in real applications** (the mayaastro.com lunar site and its
  local demo), which surfaces integration issues that unit tests don't.

In other words: the code is AI-generated, but the *behaviour* is held to an independent,
reproducible, real-world standard. Classical-technique simplifications (e.g. yoga strength
using accidental dignity rather than full Shadbala) are documented honestly in
[CHANGELOG.md](https://github.com/ranganc007/mayaastrolib/blob/master/CHANGELOG.md) and `docs/PROJECT-LOG.md` rather than hidden.

---

## API stability

From 1.0, a name is public **if and only if** it appears in its module's `__all__`.
[docs/API-STABILITY.md](https://github.com/ranganc007/mayaastrolib/blob/master/docs/API-STABILITY.md)
is the contract: it lists the frozen surface, tiers the `vedic` subsystem by fidelity
(exact vs documented-approximation), names the modules that are deliberately *not*
covered, and states the deprecation policy for breaking changes. It is enforced by
`tests/test_public_api.py`.

The everyday entry points are also available from the top level:

```python
from mayaastrolib import Chart, Datetime, GeoPos, const
```

These resolve lazily, so `import mayaastrolib` never loads Swiss Ephemeris or its
~6 MB of data — useful if you only need `const` or `__version__`.

## Documentation

Start here:

- **[docs/FAQ.md](https://github.com/ranganc007/mayaastrolib/blob/master/docs/FAQ.md)** — what the library is, what it computes, what it does **not** do, threading, accuracy, licensing.
- **[docs/HOW-IT-WORKS.md](https://github.com/ranganc007/mayaastrolib/blob/master/docs/HOW-IT-WORKS.md)** — the calculation pipeline, package layout, and gotchas.
- **[docs/BIRTH-CHART-PRIMER.md](https://github.com/ranganc007/mayaastrolib/blob/master/docs/BIRTH-CHART-PRIMER.md)** — how a birth chart is calculated and what the houses/planets traditionally mean.
- **[docs/FORK-RATIONALE.md](https://github.com/ranganc007/mayaastrolib/blob/master/docs/FORK-RATIONALE.md)** — why this fork exists.
- **[docs/KNOWN-BUGS.md](https://github.com/ranganc007/mayaastrolib/blob/master/docs/KNOWN-BUGS.md)** — tracked bugs and their fixes.

The original flatlib API documentation is largely still applicable — substitute `flatlib`
with `mayaastrolib` in import paths.

## Installation

`mayaastrolib` requires Python 3.10 or later:

```sh
pip install mayaastrolib
```

The only runtime dependency is `pyswisseph` (Swiss Ephemeris). To install from source
instead (e.g. for development), see the [Development](#development) section below.

### Migrating from flatlib

Rewrite `flatlib` imports to `mayaastrolib` — the module layout is otherwise unchanged:

```python
from flatlib import const              →  from mayaastrolib import const
from flatlib.chart import Chart        →  from mayaastrolib.chart import Chart
```

Versions 0.3.0–0.5.0 shipped a `flatlib` compatibility package that re-exported
`mayaastrolib` with a `DeprecationWarning`. **It was removed in 1.0** — `import flatlib`
now raises `ModuleNotFoundError`. Pin `mayaastrolib<1.0` if you need the shim while you
migrate.

## Development

```sh
git clone https://github.com/ranganc007/mayaastrolib.git
cd mayaastrolib
pip install -e ".[dev]"
pytest
ruff check . && ruff format --check . && mypy mayaastrolib/
```

## Licensing

`mayaastrolib` is MIT-licensed (preserving flatlib's original copyright chain). It depends on
`pyswisseph` (LGPL) and the Swiss Ephemeris data, which is GPL / commercial dual-licensed —
if you ship `mayaastrolib` in a closed-source product you must comply with the Swiss Ephemeris
GPL terms or hold a commercial Swiss Ephemeris licence. See [LICENSING.md](https://github.com/ranganc007/mayaastrolib/blob/master/LICENSING.md).

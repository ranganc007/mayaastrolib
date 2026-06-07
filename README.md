# mayaastrolib

**A modern, typed, unified Western + Vedic astrology engine for Python 3.10+.**

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

### 🪔 A complete Vedic (Jyotisha) subsystem — *new, ~3,600 LOC, 12 modules*

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
| `vedic.kp` | Krishnamurti Paddhati — 249-row sub-lord table, sub-sub-lord, horary, Ruling Planets |

### ⚙️ Modern engineering — *the whole codebase brought to current standards*

- **Python 3.10+** baseline (3.12 target); all Python-2 compatibility code removed.
- **Type hints** rolling out across the public API (`geopos`, `datetime` done; core classes in progress).
- **Modern packaging** — single `pyproject.toml` (PEP 621); `setup.py`, `requirements.txt`, and `README.rst` deleted.
- **ruff** format + lint (clean across 121 files) and **mypy** in CI.
- **CI** — GitHub Actions matrix on Python 3.10 / 3.11 / 3.12.

### 🧪 Real correctness guarantees — *coverage 34% → 94%*

- **553 tests** (+87 subtests), all passing, **94% coverage** (80% CI floor).
- **Golden tests** anchor planet positions against [Skyfield](https://rhodesmill.org/skyfield/)
  — an *independent* ephemeris — at ±2 arc-minutes for reference charts (Einstein, Kahlo, Amundsen),
  plus astronomical-invariant suites (houses sum to 360°, cusps ordered, etc.).

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

- **Structural tests** pin every public function's contract (553 tests, 94% coverage).
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

`mayaastrolib` requires Python 3.10 or later. Install from source:

```sh
git clone https://github.com/ranganc007/mayaastrolib.git
cd mayaastrolib
pip install -e .
```

The only runtime dependency is `pyswisseph` (Swiss Ephemeris). A PyPI release will follow
once the public API stabilises.

### Migrating from flatlib

`mayaastrolib` ships a compatibility shim: existing `import flatlib` and `from flatlib.x import Y`
calls keep working but emit a `DeprecationWarning`. Update imports to `mayaastrolib` at your
convenience; the shim is removed in version 1.0.

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

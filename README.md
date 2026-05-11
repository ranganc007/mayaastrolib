> **Note:** This is `mayaastrolib` — a fork of [flatangle/flatlib](https://github.com/flatangle/flatlib).
> The original `flatlib` is no longer actively maintained. This fork modernises the codebase
> (Python 3.10+, type hints, modern tooling) and unifies Western and Vedic astrology in a
> single library. See [docs/FORK-RATIONALE.md](docs/FORK-RATIONALE.md) for details.
>
> Original copyright João Ventura, MIT licensed. Fork modifications copyright Rangan C., 2026.

---

# mayaastrolib

`mayaastrolib` is a Python library for Traditional and Vedic Astrology, forked from `flatangle/flatlib`.

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

## Documentation

Fork-specific documentation (start here):

- **[docs/FAQ.md](docs/FAQ.md)** — plain-English Q&A: what the library is, what it computes, what it does **not** do, threading, accuracy, licensing.
- **[docs/HOW-IT-WORKS.md](docs/HOW-IT-WORKS.md)** — guided walkthrough from "what does this library do?" through the calculation pipeline to the package layout and gotchas.
- **[docs/BIRTH-CHART-PRIMER.md](docs/BIRTH-CHART-PRIMER.md)** — how a birth chart is calculated (six stages), what the twelve houses traditionally mean, and what each planet conventionally signifies in each house (a 10×12 reference grid).
- **[docs/PROPERTY-MIGRATION.md](docs/PROPERTY-MIGRATION.md)** — method-to-property API migration and 1.0 removal plan.
- **[docs/FORK-RATIONALE.md](docs/FORK-RATIONALE.md)** — why this fork exists.
- **[docs/KNOWN-BUGS.md](docs/KNOWN-BUGS.md)** — tracked bugs and fixes (e.g. pyswisseph 2.x eclipse keyword).

The original flatlib documentation at [http://flatlib.readthedocs.org/](http://flatlib.readthedocs.org/) is largely still applicable — substitute `flatlib` with `mayaastrolib` in import paths.

## Installation

`mayaastrolib` requires Python 3.10 or later. Install from source:

```sh
git clone https://github.com/ranganc007/mayaastrolib.git
cd mayaastrolib
pip install -e .
```

A PyPI release will follow once the API surface stabilises.

### Migrating from flatlib

`mayaastrolib` 0.3.0 ships a compatibility shim: existing `import flatlib` and `from flatlib.x import Y` calls continue to work but emit a `DeprecationWarning`. Update your imports to `mayaastrolib` at your convenience; the shim will be removed in version 1.0.

## Development

Clone the repository and install dev dependencies:

```sh
git clone https://github.com/ranganc007/mayaastrolib.git
cd mayaastrolib
pip install -e ".[dev]"
pytest tests/
```

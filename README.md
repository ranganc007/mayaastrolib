> **Note:** This is `mayaastrolib` — a fork of [flatangle/flatlib](https://github.com/flatangle/flatlib).
> The original `flatlib` is no longer actively maintained. This fork modernises the codebase
> (Python 3.10+, type hints, modern tooling) and unifies Western and Vedic astrology in a
> single library. See [docs/FORK-RATIONALE.md](docs/FORK-RATIONALE.md) for details.
>
> Original copyright João Ventura, MIT licensed. Fork modifications copyright Rangan C., 2026.

---

# flatlib

Flatlib is a python library for Traditional Astrology.

```python

>>> date = Datetime('2015/03/13', '17:00', '+00:00')
>>> pos = GeoPos('38n32', '8w54')
>>> chart = Chart(date, pos)

>>> sun = chart.get(const.SUN)
>>> print(sun)
<Sun Pisces +22:47:25 +00:59:51>

```

## Documentation

Flatlib's documentation is available at [http://flatlib.readthedocs.org/](http://flatlib.readthedocs.org/).


## Installation

Flatlib is a Python 3 package, make sure you have Python 3 installed on your system. 

You can install flatlib with `pip3 install flatlib` or download the latest stable version from [https://pypi.python.org/pypi/flatlib](https://pypi.python.org/pypi/flatlib) and install it with `python3 setup.py install`. 


## Development

You can clone this repository or download a zip file using the right side buttons. 
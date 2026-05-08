# Object Lists in mayaastrolib

`mayaastrolib.const` provides several pre-defined object lists for common
use cases. Pass these to `Chart()` via the `IDs=` parameter to control
which objects are computed.

## Available lists

| Constant                  | Description                                  |
|---------------------------|----------------------------------------------|
| `LIST_SEVEN_PLANETS`      | Traditional: Sun through Saturn              |
| `LIST_MODERN_PLANETS`     | Modern: Sun through Pluto                    |
| `LIST_TROPICAL_DEFAULT`   | Modern + lunar nodes + Chiron                |
| `LIST_VEDIC_DEFAULT`      | Seven planets + Rahu + Ketu                  |
| `LIST_LIGHTS`             | Sun and Moon only                            |
| `LIST_PERSONAL_PLANETS`   | Sun, Moon, Mercury, Venus, Mars              |
| `LIST_SOCIAL_PLANETS`     | Jupiter, Saturn                              |
| `LIST_TRANSPERSONAL`      | Uranus, Neptune, Pluto                       |
| `LIST_LUNAR_NODES`        | North Node and South Node                    |
| `LIST_OBJECTS_TRADITIONAL`| Library default — seven planets + nodes + Syzygy + Pars Fortuna |
| `LIST_OBJECTS`            | Everything including Pars Fortuna and Syzygy |

## When to use which

**Modern Western charts.** Use `LIST_TROPICAL_DEFAULT`. This is what most
consumer-facing astrology software computes. Includes the outer planets
(Uranus, Neptune, Pluto) plus the lunar nodes and Chiron. Outer planets
are not part of the traditional system but are core to modern Western
practice.

**Traditional / Hellenistic / Medieval.** Use `LIST_SEVEN_PLANETS`. Outer
planets and Chiron are anachronistic to these traditions. If you also
want Pars Fortuna and Syzygy (used in dignity and lot calculations),
use `LIST_OBJECTS_TRADITIONAL` — this is the library's default for
`Chart(date, pos)` with no `IDs=` argument.

**Vedic / sidereal (when Phase 2 ships).** Use `LIST_VEDIC_DEFAULT`. The
classical Vedic system uses the seven visible planets plus the lunar
nodes (Rahu / Ketu). Outer planets are sometimes added in modern Vedic
practice, but not by default. Note that as of 0.3.0 the library does not
yet apply ayanamsa — so positions returned for a Vedic-default chart are
still tropical. Sidereal computation is planned for Phase 2.

**Comparative analyses.** `LIST_PERSONAL_PLANETS`, `LIST_SOCIAL_PLANETS`,
and `LIST_TRANSPERSONAL` are useful for filtering or grouping output
without manually maintaining sub-lists. They overlap with
`LIST_MODERN_PLANETS` (their concatenation, plus the Moon, equals it).

## Examples

```python
from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos

date = Datetime("2015/03/13", "17:00", "+00:00")
pos = GeoPos("38n32", "8w54")

# Modern Western chart with outer planets, nodes, and Chiron
chart = Chart(date, pos, IDs=const.LIST_TROPICAL_DEFAULT)

# Traditional chart with only the seven visible planets
chart = Chart(date, pos, IDs=const.LIST_SEVEN_PLANETS)

# Just the lights
chart = Chart(date, pos, IDs=const.LIST_LIGHTS)

# Iterate the personal planets
for pid in const.LIST_PERSONAL_PLANETS:
    obj = chart.get(pid)
    print(obj.id, obj.sign, obj.signlon)
```

## Defining custom lists

The lists are plain Python `list` instances. Combine and customise freely:

```python
my_list = const.LIST_MODERN_PLANETS + [const.PARS_FORTUNA]
chart = Chart(date, pos, IDs=my_list)
```

## A note on object support

These lists are convenience groupings, not promises of computability.
Passing a list that contains an object the library does not currently
support will raise from the ephemeris layer — the right error from the
right layer. The current ephemeris computes everything in the lists
above, but the surface is intentionally permissive: as additional
objects (asteroids, lots) are added to the library, new lists will be
added here without breaking existing ones.

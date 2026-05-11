# How mayaastrolib works

A walkthrough from "what is this thing actually doing?" all the way down to the package layout. Reading this end to end takes about 15 minutes. The first three sections require no programming background. The rest assume you can read Python.

---

## Part 1 — The whole thing in one paragraph

You give the library a moment in time and a place on Earth. It asks the Swiss Ephemeris (an astronomy library) where every relevant celestial body was at that moment. It then runs a small pile of geometry to figure out which zodiac sign each body was in, which "house" of the local sky it was in, and which bodies were in significant angular relationships with each other. It packages all of that into a `Chart` object you can ask questions of. That is the entirety of what the library does at runtime.

## Part 2 — The four things in a chart

When astrologers talk about "a chart," they mean four lists, all measured in the same units (degrees of celestial longitude, 0° to 360° going around the zodiac):

**Objects.** The Sun, the Moon, the eight non-Earth planets, the lunar nodes (where the Moon's orbit crosses the Earth's orbital plane), Chiron, the Pars Fortuna (an algebraic point combining Sun, Moon, and Ascendant), and Syzygy (the previous Sun-Moon alignment). Each has a position on the zodiac wheel.

**Houses.** Twelve numbered slices of the local sky, anchored at the eastern horizon (1st house cusp = Ascendant). Different "house systems" divide up the rest of the sky differently — Placidus uses time arcs, Equal divides the ecliptic into twelve 30° wedges, Whole Sign uses the boundaries of the zodiac signs themselves. Each house has a starting cusp longitude and a sign.

**Angles.** The Ascendant (eastern horizon) and Midheaven (the point on the ecliptic directly south of the observer, where it crosses the local meridian). These are special because in many house systems the 1st house cusp equals the Ascendant and the 10th house cusp equals the Midheaven, but **not all of them do**, so the library carries angles separately as a safety. (In Equal house, for example, the 10th cusp is exactly 90° before the 1st, which is rarely the actual Midheaven.)

**Aspects.** Pairs of objects whose angular separation matches one of the canonical values (0°, 60°, 90°, 120°, 180°) within a tolerance called the "orb." Computed on demand, not stored.

These are the four things every astrology library deals with. mayaastrolib's job is to compute them correctly and hand them to you in a clean Python data structure.

## Part 3 — A worked example, narrated

Consider asking: "Where were the planets at 9:30pm Indian Standard Time on March 14, 1985, in Chennai (13°5′N, 80°16′E)?"

```python
from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos

date = Datetime("1985/03/14", "21:30", "+05:30")
pos = GeoPos("13n05", "80e16")
chart = Chart(date, pos, hsys=const.HOUSES_PLACIDUS)
```

Three lines of construction, executed in milliseconds. What the library actually did:

1. Parsed `"1985/03/14"` and `"21:30"` and the `+05:30` offset into a Julian Date — the astronomical clock that Swiss Ephemeris speaks. UTC offsets are subtracted; DST is **not** handled (you must pass a fixed offset).
2. Asked Swiss Ephemeris for the heliocentric and geocentric positions of every body in the default object list at that Julian Date.
3. Computed the Ascendant and Midheaven from the geographic position, the Earth's axial tilt at that moment, and the local sidereal time.
4. Computed the twelve house cusps under the chosen house system (Placidus, here — which involves dividing the diurnal and nocturnal arcs into thirds at the geographic latitude).
5. For each object, walked the houses to find which one contains it, and stamped `obj.house` on the object.
6. For each house, collected the objects whose `.house` points back at it, and stamped `house.objects` on the house.

After construction:

```python
sun = chart.get(const.SUN)        # an Object
sun.sign        # "Pisces"
sun.signlon     # 23.6131…  (degrees within Pisces)
sun.lon         # 353.6131…  (degrees on the full zodiac wheel)
sun.house       # House5
sun.house.id    # "House5"

moon = chart.get(const.MOON)
moon.house.id   # e.g. "House3"

# Aspects are computed on demand
from mayaastrolib import aspects
asp = aspects.getAspect(sun, moon, const.MAJOR_ASPECTS)
if asp is not None:                  # None means no aspect within orb
    asp.name         # "Trine", "Square", "Sextile", … (also const.ASPECT_NAMES[asp.type])
    asp.type         # 60, 90, 120, etc.
    asp.orb          # how far from exact, in degrees
    asp.movement     # *aspect-relative*: "Applicative" / "Separative" / "Exact"
    asp.activeObj    # the original Object instance that "starts" the aspect
    asp.passiveObj   # the original Object instance that "receives" it
    # Note: asp.activeObj.movement is *planet-relative* ("Direct"/"Retrograde"/"Stationary")
    # and is distinct from asp.movement above. The two answer different questions.
```

That is the whole user-visible surface of the library, give or take a dozen helper modules.

---

## Part 4 — The calculation pipeline (intermediate)

This section assumes you can read Python. It walks `Chart.__init__` end to end.

### Step 1: Resolve inputs to canonical forms

`Datetime` parses the human-readable date/time/UTC-offset triple and stores a Julian Date internally. `GeoPos` parses `"13n05"` into a signed decimal latitude. Both classes are tiny.

### Step 2: Get object positions from the ephemeris

`ephem.getObjectList(IDs, date, pos)` is the bridge to Swiss Ephemeris. For each ID in the requested list (default: traditional seven planets plus a handful of points), it asks `pyswisseph` for the body's geocentric ecliptic longitude, latitude, and longitude speed at the Julian Date. It returns a list of `Object` instances, each carrying:

- `id`, `sign`, `signlon` (degrees within the sign), `lon` (degrees on the full ecliptic), `lat`, `lonspeed`
- `isRetrograde()` (true when `lonspeed < 0`)
- Property accessors for `movement`, `gender`, `faction`, `element`, `orb`, `meanMotion`

### Step 3: Get houses and angles

`ephem.getHouses(date, pos, hsys)` calls `swe_houses_ex` from Swiss Ephemeris with the chosen house-system code. Swiss Ephemeris returns 12 cusp longitudes plus the Ascendant, Midheaven, ARMC (sidereal time), and a few derived angles. The library wraps these in `House` and `GenericObject` instances and returns them as a `HouseList` plus the angles list.

The house system codes are single ASCII letters internally (`'P'` = Placidus, `'E'` = Equal, `'W'` = Whole Sign, etc.), exposed as named constants in `const.py` so you write `const.HOUSES_PLACIDUS`.

### Step 4: Cross-link objects and houses

After step 3, you have a list of objects and a list of houses, but no relation between them. `Chart._link_objects_to_houses` fixes this:

```python
for obj in self.objects:
    obj.house = self.houses.getObjectHouse(obj)
for house in self.houses:
    house.objects = [o for o in self.objects if o.house is house]
```

`HouseList.getObjectHouse` walks the houses and returns the first one whose `inHouse(obj.lon)` test is true. This is O(12) per object, run once at construction. After this, `obj.house` is a free attribute lookup forever after.

### Step 5: Done

The `Chart` is now fully populated:

- `chart.objects` — list of `Object`
- `chart.houses` — `HouseList` of `House`
- `chart.angles` — list of `GenericObject` (Ascendant, Midheaven, etc.)
- `chart.date`, `chart.pos`, `chart.hsys` — the inputs, retained
- Plus convenience methods: `chart.get(id)`, `chart.getAngle(id)`, `chart.houseOf(obj)`, `chart.objectsInHouse(hid)`, `chart.isDiurnal()`, `chart.getMoonPhase()`, etc.
- **Predictive methods (Task 013)** — discoverable on the chart instead of scattered across modules:
  - `chart.solarReturn(year=N)` / `chart.solarReturn(target_date=D)` — the chart anchored at January 1 of `N`, or the next solar return on or after `D`. Mutually exclusive args.
  - `chart.profected(years=N)` / `chart.profected(target_date=D)` — annual-profection chart with `is_symbolic=True` and cleared planet speeds (Task 010).
  - `chart.directions()` — returns a `PrimaryDirections` object for symbolic-time progressions.
  - `chart.arabicPart(part_id)` — Arabic Part of the chart (e.g. `const.PARS_FORTUNA`). Replaces the deprecated `tools.arabicparts.getPart(id, chart)`.
  - `chart.planetaryHour(date=None)` — returns the planetary `HourTable` for the chart's location at the given moment (defaults to the chart's date).

Aspects, dignities, and most analyses are computed lazily on demand against this populated chart.

---

## Part 5 — Package layout (technical)

```
mayaastrolib/
├── __init__.py              # version, paths
├── _compat.py               # property_with_method_compat decorator
├── angle.py                 # angle arithmetic helpers (mod 360 etc.)
├── aspects.py               # getAspect, hasAspect, MAJOR_ASPECTS
├── chart.py                 # Chart class — the user-facing entrypoint
├── const.py                 # all named constants (signs, IDs, house systems, …)
├── datetime.py              # Datetime: human triple → Julian Date
├── geopos.py                # GeoPos: text lat/lon → signed decimals
├── lists.py                 # HouseList, ObjectList helpers
├── object.py                # Object, House, FixedStar, GenericObject
├── props.py                 # static lookups: sign rulers, exaltations, etc.
├── utils.py                 # internal helpers
├── resources/               # ephemeris files (Swiss Ephemeris data)
├── ephem/                   # bridge to pyswisseph; getObjectList, getHouses
├── dignities/               # essential.py, accidental.py, tables.py
├── predictives/             # profections, returns, primary directions
├── protocols/               # almutem, behavior, temperament
└── tools/                   # arabic parts, chart dynamics, planetary time
```

### The user-facing surface (what you import)

99% of consumers use just these:

```python
from mayaastrolib import const                      # named constants
from mayaastrolib.chart import Chart                # the chart class
from mayaastrolib.datetime import Datetime          # date/time wrapper
from mayaastrolib.geopos import GeoPos              # geographic position
from mayaastrolib import aspects                    # getAspect, MAJOR_ASPECTS
from mayaastrolib.dignities import essential        # score, getInfo, isPeregrine
```

### Layers below that

- **`ephem/`** — the only module that talks to `pyswisseph`. If you ever want to stub out the ephemeris (for tests, for an alternate astronomy backend), this is the seam.
- **`object.py`** — the data classes. Each class is dumb: positional state plus methods to compute derived properties (sign, signlon, retrograde, dignities). They're lightweight enough that copying a chart is fast.
- **`dignities/`, `predictives/`, `protocols/`, `tools/`** — analyses that take a chart and return something. None of them mutate the chart. These are where most domain-specific logic lives.

### Things to know about the data model

- **All longitudes are degrees on the ecliptic**, 0° to 360°, with 0° at the Aries equinox point (tropical) or at a fixed sidereal anchor (Vedic mode). Sign membership is just `int(lon // 30)`.
- **`Object.lon` is absolute, `Object.signlon` is relative to the start of its sign.** Both are kept; both are useful.
- **`Object.lonspeed` carries the apparent angular velocity in degrees per day.** Negative means retrograde from Earth's reference frame. This is how `isRetrograde` is implemented.
- **House membership is determined by longitude**, not by zodiacal sign. A house can span multiple signs; a sign can span multiple houses; they are orthogonal divisions of the same wheel.
- **Aspects compare two longitudes**, not two signs. A 90°-apart pair forms a square regardless of which signs they are in (though traditional astrology cares about the sign relationship as well).

---

## Part 6 — Conventions and gotchas

### Naming and access patterns

- **`obj.house` is an attribute** (set during `Chart.__init__`). Don't iterate the houses to find it — it's already there.
- **`House.num`, `House.condition`, `House.gender` are properties** as of `[Unreleased]`. The legacy method-style access (`h.num()`) still works and emits `DeprecationWarning`. See [PROPERTY-MIGRATION.md](PROPERTY-MIGRATION.md).
- **`Aspect.movement` is also a property.** Same deprecation note applies.
- **`dignities.essential.score(obj)` is the preferred form** — pass the Object directly. The legacy `(id, sign, lon)` three-scalar form still works.

### Threading

- `dignities.essential` historically had module-level mutable globals for `terms` and `faces` variants, set via `setTerms()` / `setFaces()`. **This was not thread-safe.** As of `[Unreleased]`, all `essential.*` functions accept `terms_variant=` and `faces_variant=` keyword-only parameters. Pass these per call instead of mutating the module globals; the setters are deprecated.
- The rest of the library is read-only after `Chart` construction. You can safely build many Charts in parallel from one process. Swiss Ephemeris itself is thread-safe for position queries.

### Time

- `Datetime` does **not** know about IANA timezones (`"Europe/Dublin"`, `"America/Los_Angeles"`). It takes a fixed UTC offset. If your input is a wall-clock time in a DST-observing zone, you must resolve the correct offset for that date yourself. See `IDEAS.md` for the deferred plan to add IANA support.
- `Datetime.now(utcoffset='+00:00')` returns the current UTC moment expressed at the given offset.
- `Datetime.from_pydatetime(dt, utcoffset=None)` and `to_pydatetime()` round-trip with Python's `datetime.datetime` (whole-second precision; sub-seconds are dropped).

### Calendars

- All dates are proleptic Gregorian. If you have a Julian-calendar source date (anything before 1582 in many sources), convert it before constructing `Datetime`.

### House systems

- `const.HOUSES_DEFAULT = HOUSES_ALCABITUS`. Common alternatives are Placidus (most popular in modern Western practice), Equal, and Whole Sign. Polar regions break Placidus and most other quadrant systems (cusps go undefined above ~66° latitude near solstices); use Whole Sign for those.

### Object lists

- The default object list passed to `Chart` is `const.LIST_OBJECTS_TRADITIONAL` — Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, plus the lunar nodes, Pars Fortuna, and Syzygy.
- For "modern" charts (Sun…Pluto), use `const.LIST_MODERN_PLANETS`. For modern + nodes + Chiron, use `const.LIST_TROPICAL_DEFAULT`. For Vedic charts (seven traditional + nodes, no outer planets), use `const.LIST_VEDIC_DEFAULT`. There are also useful subsets: `LIST_LIGHTS` (Sun, Moon), `LIST_PERSONAL_PLANETS` (Sun…Mars), `LIST_SOCIAL_PLANETS` (Jupiter, Saturn), `LIST_TRANSPERSONAL` (Uranus, Neptune, Pluto), `LIST_LUNAR_NODES` (North/South Node). See [`docs/OBJECT-LISTS.md`](OBJECT-LISTS.md) for guidance on when to use which.

### Symbolic charts (derived, not from ephemeris)

Some astrological techniques produce charts whose planet positions are *derived* from a natal chart rather than computed afresh from the ephemeris — for example, profected charts, charts at relocated longitudes, or antiscia. These positions are no longer "where the planet actually was at time T," so the orbital dynamics (`lonspeed`, `latspeed`) are undefined.

The library distinguishes these symbolic positions from real ones:

- **`Object.with_longitude(lon, *, preserve_speed=False)`** — returns a new Object at the given longitude. By default clears `lonspeed` / `latspeed` to `None`. Pass `preserve_speed=True` only when the new position meaningfully shares dynamics with the original (e.g. antiscia, where the speed is the same). Replaces the deprecated `Object.relocate(lon)`, which mutated in place and left stale speeds.
- **`Object.antiscion()` / `Object.cantiscion()`** — return new Objects at the antiscion (mirror across 0° Cancer / Capricorn axis) and contra-antiscion positions. Replace the deprecated `antiscia()` / `cantiscia()`.
- **`Chart.profected(years=N)` / `Chart.profected(target_date=D)`** — return a profected chart with `is_symbolic=True`, `symbolic_kind="profection"`, and properly cleared planet speeds. Replaces `predictives.profections.compute(chart, date)` (now a thin deprecated wrapper).
- **`Chart.is_symbolic`** (bool, default `False`) and **`Chart.symbolic_kind`** (str, e.g. `"profection"`) — flag whether the chart represents derived positions.

When `lonspeed is None` (a symbolic position), `obj.movement`, `isFast`, `isDirect`, `isRetrograde`, and `isStationary` return `None` rather than computing a misleading bool from a stale speed. This is the bug fix that originally motivated the redesign — `profections.compute` used to leave natal speeds intact, so `isRetrograde()` on a profected chart silently returned the natal answer.

---

## Part 7 — Where to read further

- **[FAQ.md](FAQ.md)** — the layman-friendly version of all of this.
- **[BIRTH-CHART-PRIMER.md](BIRTH-CHART-PRIMER.md)** — what the geometry *means* in traditional/modern astrology: the six calculation stages explained for non-coders, the twelve houses' domains, and the planet-in-house interpretive grid.
- **[FORK-RATIONALE.md](FORK-RATIONALE.md)** — why this fork exists and what it's doing differently from upstream.
- **[PROPERTY-MIGRATION.md](PROPERTY-MIGRATION.md)** — the API ergonomics changes (method → property) and the 1.0 removal plan.
- **[KNOWN-BUGS.md](KNOWN-BUGS.md)** — bugs we have either fixed or are tracking, including the pyswisseph 2.x eclipse keyword fix.
- **[IDEAS.md](IDEAS.md)** — deferred features (IANA timezones, etc.).
- **The flatlib readthedocs site** — [http://flatlib.readthedocs.org/](http://flatlib.readthedocs.org/) — most upstream documentation still applies if you substitute `flatlib` with `mayaastrolib` in import paths.
- **Swiss Ephemeris documentation** — [https://www.astro.com/swisseph/](https://www.astro.com/swisseph/) — for questions about the underlying astronomy library, accuracy bounds, ephemeris file licensing, and Julian Date conventions.

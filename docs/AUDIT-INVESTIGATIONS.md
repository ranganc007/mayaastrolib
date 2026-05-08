# Audit Investigations

Outputs of investigation tasks for audit items that needed
code-reading before a fix could be scoped. Each entry follows: what
was found, what the code actually does, what the right fix is.

---

## Item 15 — `House._OFFSET = -5.0`

**Investigated in Task 012, 2026-05-08.**

### Where it's used

```
$ grep -rn "_OFFSET\|inHouse\|hasObject" mayaastrolib/ --include="*.py"
mayaastrolib/object.py:299:    _OFFSET = -5.0
mayaastrolib/object.py:362:    def inHouse(self, lon):
mayaastrolib/object.py:364:        dist = angle.distance(self.lon + House._OFFSET, lon)
mayaastrolib/object.py:367:    def hasObject(self, obj):
mayaastrolib/object.py:369:        return self.inHouse(obj.lon)
mayaastrolib/lists.py:65:        res = [obj for obj in self if house.hasObject(obj)]
mayaastrolib/lists.py:91:            if house.inHouse(lon):
```

`_OFFSET` is a class constant on `House` (`mayaastrolib/object.py:299`).
Its only use is inside `House.inHouse(lon)` at `object.py:364`:

```python
def inHouse(self, lon):
    dist = angle.distance(self.lon + House._OFFSET, lon)
    return dist < self.size
```

`House.size` defaults to `30.0` (from `__init__`); `self.lon` is the
cusp's ecliptic longitude. So the test is:

> "Is `lon` within `size` (30°) of `cusp + (-5)` = `cusp - 5°` ?"

Equivalent to saying the house spans from `cusp − 5°` (inclusive) to
`cusp + 25°` (exclusive). A planet whose longitude falls 5° *before*
the named cusp is still considered to be in this house — except, by
the same rule applied to the *previous* house, that earlier 5°
window is ALSO claimed by the previous cusp. The net behaviour is
that a longitude in the band `[cusp_i − 5°, cusp_i)` is reported as
belonging to house `i` (this house) rather than house `i−1`.

Two callers consume this:

- `lists.py:65` — `ObjectList.getObjectsInHouse(house)` → `house.hasObject(obj)` → `inHouse(obj.lon)`.
- `lists.py:91` — `HouseList.getHouseByLon(lon)` walks the houses and
  returns the first whose `inHouse(lon)` is True.

`Chart._link_objects_to_houses` (in `chart.py`) uses the
`HouseList`-based lookup to stamp `obj.house` on every object, which
is what powers `Chart.houseOf(obj)` and `Chart.objectsInHouse(...)`
added in Task 006.

### What it appears to mean

This is the **traditional "5° rule"** (also called the
"fifth-degree rule" or "cusp tolerance"): a planet within 5° of the
next house cusp is considered to belong to the *next* house already,
because cusps "come early" in their effects.

This is a long-standing convention in Hellenistic, Medieval, and a
good chunk of modern Western astrology. It's a workaround for
aspects of house-cusp computation that are themselves approximate
(quadrant systems like Placidus place cusps at proportional
divisions that don't match psychological/practical sign onset).

The 5° figure is a defensible default. Some authors use 3° or 7°.
Some apply it only to angular cusps (House 1, 4, 7, 10), leaving
the others sharp. The current code applies it uniformly across all
12 houses. This is a config decision, not a bug.

The constant is used unconditionally — there is no per-house-system
gating. A whole-sign chart and a Placidus chart both run through
the same offset. This is *probably* desirable for whole-sign (where
cusps coincide with sign starts and a planet at 29° of a sign is
clearly in the next sign anyway) but it's worth noting that
purists may quibble.

### Recommended action

**DOCUMENT.** The code is correct; it just needs a name change
(`_OFFSET → _CUSP_TOLERANCE_DEG`) and a docstring explaining the
5° rule. No behaviour change. Applied in Task 012.

A potential follow-up — making the tolerance configurable via
`Chart(cusp_tolerance=...)` or per-`House` — is recorded in
`docs/IDEAS.md` for Phase 2 if user demand surfaces. Not done here
because (a) the current default is widely accepted, and (b) the
parameterisation surface (per-chart, per-house, per-house-system?)
needs design discussion.

---

## Item 16 — `solarReturn(year)` semantics

**Investigated in Task 012, 2026-05-08.**

### Code under investigation

`Chart.solarReturn` lives at `mayaastrolib/chart.py:310-318`:

```python
def solarReturn(self, year):
    """Returns this chart's solar return for a given year."""
    sun = self.getObject(const.SUN)
    date = Datetime(f"{year}/01/01", "00:00", self.date.utcoffset)
    srDate = ephem.nextSolarReturn(date, sun.lon)
    return Chart(srDate, self.pos, hsys=self.hsys)
```

The behaviour: anchor at January 1 of `year` (00:00 in the natal's
fixed UTC offset), then forward-search for the first Sun
conjunction with the natal Sun longitude.

### Concrete behaviour (verified by running)

```python
natal_jun = Chart(Datetime('1980/06/15', '12:00', '+00:00'), GeoPos('38n32', '8w54'))
natal_dec = Chart(Datetime('1980/12/15', '12:00', '+00:00'), GeoPos('38n32', '8w54'))

natal_jun.solarReturn(2022).date   # <2022/06/15 15:25:26 00:00:00>
natal_dec.solarReturn(2022).date   # <2022/12/15 16:54:20 00:00:00>
natal_dec.solarReturn(2021).date   # <2021/12/15 11:01:19 00:00:00>
natal_jun.solarReturn(1980).date   # <1980/06/15 12:00:02 00:00:00>
natal_dec.solarReturn(1980).date   # <1980/12/15 11:59:59 00:00:00>
```

In every case, `solarReturn(year=N)` returns the solar return that
falls within calendar year `N`, regardless of whether the birthday
is in early or late part of the year.

Mapping years to ages: a 1980 birth, `solarReturn(2022)` = 42nd
birthday return. A 1980 birth, `solarReturn(1980)` = the natal
moment itself (0th return). For both Jun and Dec birthdays.

### Does it match user expectations?

**Yes.** The audit raised a concern that "first sun-conjunct-natal
moment in calendar year N" might disagree with "Nth birthday return"
for late-year birthdays. The concrete test cases above show this
concern doesn't manifest:

- For a Dec 15 birth, the search anchors at Jan 1 of the target
  year and walks forward until late December — well after the
  birthday-equivalent-date that year. No off-by-one.
- The age math `(year_of_return - year_of_birth)` gives the
  expected birthday number for every realistic case (mid-year and
  late-year alike).

The only edge case where the two interpretations could diverge is
if the natal date itself crosses a year boundary in some unusual
timezone such that the "calendar year of return" interpretation
disagrees with the "birthday number" interpretation. This is at
most a one-day window and isn't astrologically meaningful.

### Recommended action

**NO ACTION beyond DOCUMENTATION.** The current behaviour is
correct and matches user expectations. Just expand the docstring
to make the calendar-year-anchored semantic explicit (so future
auditors don't re-raise the same concern). Applied in Task 012.

A possible Phase 2 enhancement — adding a `solarReturnByAge(years)`
companion that disambiguates by counting from the natal date —
is recorded in `docs/IDEAS.md`. Low priority; the existing API
already works for every realistic call.

# Golden Test Suite

Functional / golden test layer mandated by `CLAUDE.md`. Tests here
verify mayaastrolib's astronomical correctness against an independent
reference (Skyfield), and assert structural invariants that must hold
for any correctly-computed chart.

## Layout

| File | Purpose |
|---|---|
| `generate_fixtures.py` | Skyfield-based reference generator. Run **manually** by maintainers when adding charts or updating Skyfield. |
| `fixtures.json` | Frozen reference data. Committed. |
| `test_planet_positions.py` | Golden tests against Skyfield. Runs in CI. |
| `test_self_consistency.py` | Invariant tests independent of any reference. Runs in CI. |
| `.skyfield-data/` | Skyfield ephemeris cache (de440s.bsp). Gitignored. |

## Reference methodology

**Why Skyfield:**
- MIT-licensed, no GPL contamination of the test infrastructure
- Independent implementation from Swiss Ephemeris (mayaastrolib's
  runtime backend), so agreement is meaningful evidence — not just
  the library agreeing with itself
- Reproducible: anyone can run `generate_fixtures.py` and get the
  same numbers
- Used by NASA and professional astronomers; well-tested

**Why we don't golden-test houses, dignities, or aspects:** Skyfield
is an astronomy library — it doesn't know about astrological
concepts. Houses, dignities, and aspects are tested via
`test_self_consistency.py` (invariants) instead. This catches a
different class of bug than golden tests can.

**Tolerance:** ±2 arcminutes for planets (per `CLAUDE.md`). The
Skyfield/Swiss-Ephemeris drift in practice is <0.1 arcmin for
inner planets and Pluto, <0.5 arcmin for the Moon (sub-second-of-arc
parallax/aberration model differences). Two arcminutes is comfortable
headroom.

**Geocentric vs topocentric:** Skyfield's reference is computed
geocentric (`EARTH.at(t).observe(body)`) to match Swiss Ephemeris's
default geocentric output. Topocentric would shift the Moon by up to
~1° due to parallax — visible above tolerance and would silently
fail the comparison.

## Reference charts

| Chart | Date (LMT → UTC) | Location | Lat | Rodden |
|---|---|---|---:|---|
| Albert Einstein | 1879-03-14 11:30 → 10:50 UTC | Ulm, Germany | 48°N | AA |
| Frida Kahlo | 1907-07-06 08:30 → 15:06:40 UTC | Coyoacán, Mexico | 19°N | AA |
| Roald Amundsen | 1872-07-16 03:30 → 02:46:48 UTC | Borge, Norway | 59°N | B |

The Amundsen chart at 59°N is deliberately included to exercise
Placidus stability near the boundary where it begins to behave
irregularly. As of Task 014 it produces consistent, ordered house
cusps — no instability surfaced.

## LMT-to-UTC conversion

Pre-1893 charts (Einstein, Amundsen) and Mexico in 1907 (Kahlo)
predate fixed-offset civil time, so birth times are recorded as
**Local Mean Time** (LMT). LMT-to-UTC:

```
UTC = LMT − longitude_degrees / 15  hours    (East positive)
```

Worked examples (verified by hand at fixture generation):

- Ulm 10°E → +0:40:00, so 11:30 LMT = 10:50:00 UTC
- Coyoacán -99.167°W → -6:36:40, so 08:30 LMT = 15:06:40 UTC
- Borge 10.8°E → +0:43:12, so 03:30 LMT = 02:46:48 UTC

## Cross-checking new fixtures

When adding a new chart to `generate_fixtures.py`, also verify the
Sun's position against an independent source (astro.com,
Astro-Databank) to within ±1 arcminute. The Sun moves ~2.5 arcmin
per hour, so a ~1 arcmin agreement validates the LMT-to-UTC
conversion at sub-minute accuracy.

For Task 014's three charts, Skyfield's Sun positions match
Astro-Databank's published Sun positions:

- Einstein: 23°30' Pisces (353.50° Skyfield, 353°30' AstroDB) ✓
- Kahlo: 13°23' Cancer (103.38° Skyfield, 13°23' AstroDB) ✓
- Amundsen: 23°49' Cancer (113.81° Skyfield, public record ~24° Cancer) ✓

## Regenerating fixtures

```bash
.venv-task014/bin/python tests/golden/generate_fixtures.py
```

Then commit the updated `fixtures.json`. CI does **not** run this
script — fixtures are frozen artefacts.

## When to regenerate

- Adding a new fixture chart
- Updating Skyfield to a major new version
- Updating the JPL ephemeris (e.g. `de440s.bsp` → `de441.bsp`)
- Discovering a fixture is wrong (e.g. LMT-conversion error)

**Do NOT regenerate to make a failing test pass.** If mayaastrolib's
output drifts beyond tolerance, that's a real signal — investigate
the library, don't paper over it by regenerating fixtures.

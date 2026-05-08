# Known Bugs and Fixes

## Resolved

### `GeoPos` accepted out-of-range latitude / longitude

**Discovered:** 2026-05-08 platform review (see
`docs/REVIEW-2026-05-08.md` — Reliability and test gaps, item 2).
**Fixed:** Task 015.
**Affected:** `mayaastrolib/geopos.py::GeoPos.__init__`.

`GeoPos('200n00', '0w00')` returned an instance with `lat=200.0`
without raising. Any chart constructed with this `GeoPos` produced
mathematically nonsensical output that didn't visibly fail. The
library's defenses against bad input were accidental (`int()` cast
on garbage strings happens to raise; `swisseph.calc_ut` raises on
unknown bodies); range validation was missing.

After Task 015, `GeoPos.__init__` validates `lat ∈ [-90, 90]` and
`lon ∈ [-180, 180]` after float coercion, raising `ValueError` with
the offending value in the message. Boundaries are inclusive (poles
and antimeridian are valid).

Regression tests: `tests/test_geopos_validation.py` (15 cases
covering valid boundaries, out-of-range strings, just-past-boundary
inputs, and numeric input paths).

### Eclipse functions used wrong keyword argument

**Discovered:** Task 001 recon (see RECON.md §8 ¶1)
**Fixed:** Task 004 (`fix:` commit, this task)
**Affected:** `flatlib/ephem/swe.py` solarEclipseGlobal and lunarEclipseGlobal

`flatlib/ephem/swe.py` called pyswisseph eclipse functions with `backward=...`. In pyswisseph 2.x the keyword is `backwards`. Same root cause as the upstream rise_trans patch (commit 856d26b on master) but for eclipse functions, which were missed at the time.

Symptoms before fix: any call to `nextSolarEclipse`, `prevSolarEclipse`, `nextLunarEclipse`, or `prevLunarEclipse` raised `TypeError: ... got an unexpected keyword argument 'backward'`. The `recipes/eclipses.py` example was broken.

Regression test: `tests/test_eclipses.py`.

## Open

(none currently)

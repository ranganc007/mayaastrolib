# Known Bugs and Fixes

## Resolved

### Eclipse functions used wrong keyword argument

**Discovered:** Task 001 recon (see RECON.md §8 ¶1)
**Fixed:** Task 004 (`fix:` commit, this task)
**Affected:** `flatlib/ephem/swe.py` solarEclipseGlobal and lunarEclipseGlobal

`flatlib/ephem/swe.py` called pyswisseph eclipse functions with `backward=...`. In pyswisseph 2.x the keyword is `backwards`. Same root cause as the upstream rise_trans patch (commit 856d26b on master) but for eclipse functions, which were missed at the time.

Symptoms before fix: any call to `nextSolarEclipse`, `prevSolarEclipse`, `nextLunarEclipse`, or `prevLunarEclipse` raised `TypeError: ... got an unexpected keyword argument 'backward'`. The `recipes/eclipses.py` example was broken.

Regression test: `tests/test_eclipses.py`.

## Open

(none currently)

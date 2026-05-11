# Task 024: Vedic Tajika — Varshapravesh + Mudda Dasha

## Context

Read `CLAUDE.md`, the `vedic/tajika.py` section of
`docs/2026-05-11-vedic-extension-spec.md`, and confirm Tasks 017–023
merged. Read `mayaastrolib/ephem/tools.py` (`solarReturnJD` pattern),
`mayaastrolib/ephem/swe.py` (`sweObjectLon` now takes `zodiac`), and
`mayaastrolib/vedic/dasha.py` (the Vimshottari proportions and the
`DashaPeriod`/`_add_days` helpers — reuse them). Confirm `pytest tests/`
passes (~359 after Task 023).

## Why this task exists

Tajika ("Persian-derived" Vedic annual astrology) builds a chart for the
moment the Sun returns to its natal position each year (varshapravesh),
and reads it with its own techniques. The headline ones are the
varshapravesh chart itself and the Mudda dasha (Vimshottari proportions
compressed into the one year). This is MayaAstro's "free differentiator"
versus paid services.

## Scope decision (this task is a CORE slice)

This task ships **varshapravesh + Mudda dasha** only. Deferred to a
follow-up (024b): Lord-of-Year (Varsheshwara), Harsha Bala,
Panchavargiya Bala, and the ~50 Tajika Sahams. Those are large and
mostly orthogonal; better as their own task.

## Design decisions (already made)

- **Sidereal solar return.** Varshapravesh = the moment the *sidereal*
  Sun returns to the natal *sidereal* Sun longitude, in the target year.
  This is NOT the same as the tropical solar return — the ayanamsa
  drifts ~50″/yr, so over decades the two diverge by up to ~a day.
  Implement a dedicated search (same Newton-ish loop as
  `ephem.tools.solarReturnJD` but using `sweObjectLon(SUN, jd,
  zodiac=ZODIAC_SIDEREAL, ayanamsa=...)`). Do NOT touch
  `Chart.solarReturn` — that stays tropical-only for now (the
  zodiac-aware refactor of the Hellenistic solar return is a separate
  decision documented in Task 017's CHANGELOG).
- **`varshapravesh(natal_chart, target_year, ayanamsa=...)` returns a
  `Datetime`** (the return moment, in the natal chart's UTC offset).
  The caller can build a `Chart(that_datetime, natal.pos,
  zodiac=ZODIAC_SIDEREAL)` if they want the full annual chart.
- **Mudda dasha:** the 365.25-day year is divided among the 9
  Vimshottari lords in the standard proportions (Ketu 7 / Venus 20 /
  Sun 6 / Moon 10 / Mars 7 / Rahu 18 / Jupiter 16 / Saturn 19 /
  Mercury 17, summing to 120 → each gets `years/120 × 365.25` days).
  The sequence **starts from the lord of the nakshatra the Moon
  occupies at the varshapravesh moment** (the most common rule), then
  proceeds through the Vimshottari cycle. Reuse `dasha.DashaPeriod` and
  `dasha.VIMSHOTTARI_ORDER`/`VIMSHOTTARI_YEARS`. There is no
  partial-first-period here — the year starts fresh at varshapravesh,
  so the first Mudda period is the full duration of its lord.
- **`MEAN_MOTION_SUN`** (0.9833 °/day, already in `const.py`) is fine
  for the search step; the loop converges regardless.

## Task scope

`mayaastrolib/vedic/tajika.py`:

```python
def sidereal_sun_return_jd(start_jd, target_sidereal_lon, ayanamsa) -> float
def varshapravesh(natal_chart, target_year, ayanamsa=...) -> Datetime
def mudda_dasha(varshapravesh_date, ayanamsa=...) -> list[DashaPeriod]   # 9 periods, sum 365.25 days
```

`varshapravesh`: compute the natal sidereal Sun longitude from
`natal_chart` (if the chart is tropical, shift via `to_sidereal`), anchor
the search at Jan 1 of `target_year` (in `natal_chart.date.utcoffset`),
walk forward to the return.

`mudda_dasha`: build a temporary sidereal Moon position at the
varshapravesh moment via `sweObjectLon(MOON, vp.jd, zodiac=SIDEREAL,
ayanamsa)`, get its nakshatra lord via `nakshatras.of_longitude`, then
build the 9 `DashaPeriod`s (level=1) starting from that lord.

## Tests (`tests/test_vedic_tajika.py`)

- `sidereal_sun_return_jd` converges: pick a known sidereal Sun longitude
  and a start jd; the returned jd, fed back through `sweObjectLon(SUN,
  jd, SIDEREAL)`, should equal the target within ~0.0003° (one arc-sec,
  matching `ephem.tools.MAX_ERROR`).
- `varshapravesh`: for a natal chart, the varshapravesh of the **birth
  year** should be very close to the birth moment itself (within ~a day —
  the natal Sun is at its natal position at birth, by definition).
- `varshapravesh(year)` and `varshapravesh(year+1)` differ by ≈365.25
  days (±1 day).
- The sidereal Sun longitude at the varshapravesh moment equals the natal
  sidereal Sun longitude (within ~0.001°).
- `mudda_dasha`: returns 9 `DashaPeriod`s; durations sum to 365.25 days
  (±0.01); first period's lord matches the varshapravesh-Moon nakshatra
  lord; lords follow `VIMSHOTTARI_ORDER` cyclically from that start;
  each period's duration = `lord_years/120 × 365.25` days (±0.01).
- The first Mudda period starts exactly at the varshapravesh moment (no
  partial-before-start, unlike the natal Vimshottari).

## Out of scope (→ Task 024b)

- Varsheshwara (lord of year), Harsha Bala, Panchavargiya Bala, Sahams.
- The Tajika aspects (ithasala, isharafa, etc.) and Sahams-based timing.
- Day-precise dasha sub-levels within Mudda.

## Process

Branch `task-024-vedic-tajika`. Commits: `feat: add vedic.tajika
varshapravesh + Mudda dasha`, then `docs: update CHANGELOG, PROJECT-LOG,
CLAUDE.md for Task 024`. Pre-completion checklist: ruff format/check,
mypy (no new errors), pytest, coverage ≥80%. PROJECT-LOG must note: how
far the birth-year varshapravesh lands from the birth moment, and that
`Chart.solarReturn` was deliberately left tropical-only. Push, verify
CI, DO NOT merge.

## Definition of done

- `sidereal_sun_return_jd`, `varshapravesh`, `mudda_dasha` implemented.
- Sidereal return converges to ≤1″; birth-year varshapravesh ≈ birth.
- Mudda dasha: 9 periods, sum 365.25 days, correct lord order from the
  varshapravesh-Moon nakshatra lord.
- Tests pass; existing tests unaffected. Docs updated. CI green.

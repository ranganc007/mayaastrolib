# Task 022: Vedic Sade Sati

## Context

Read `CLAUDE.md`, the `vedic/sadesati.py` section of
`docs/2026-05-11-vedic-extension-spec.md`, and confirm Tasks 017–021 have
merged. Read `mayaastrolib/vedic/nakshatras.py` for the module style and
`mayaastrolib/ephem/swe.py` for `sweObjectLon`. Confirm `pytest tests/`
passes (~320 after Task 021).

## Why this task exists

Sade Sati ("seven and a half") is the ~7.5-year period when transiting
Saturn occupies the 12th, 1st (same as), and 2nd signs from the natal
Moon — each ~2.5-year leg called a dhaiyya. It's one of the most
commonly-requested Vedic timing facts.

## Design decisions (already made)

- **Phase taxonomy:** `"rising"` (Saturn 12th from natal Moon, first
  dhaiyya), `"peak"` (Saturn in the natal Moon's own sign, janma shani,
  most intense), `"setting"` (Saturn 2nd from natal Moon, last dhaiyya),
  `"not-active"` otherwise.
- **Severity:** `"intense"` for peak, `"moderate"` for rising,
  `"mild"` for setting, `"none"` otherwise. Traditional ranking.
- **Saturn's sign is location-independent** at the day granularity, so
  the API takes a natal Moon *sign index* and a target `Datetime` — no
  GeoPos needed. Saturn's sidereal longitude is computed via
  `swe.sweObjectLon(SATURN, target.jd)` then `to_sidereal`.
- **`SadeSatiPhase` is a frozen dataclass:** `active` (bool), `phase`
  (str), `saturn_sign` (sign name), `natal_moon_sign` (sign name),
  `severity` (str).
- **Also ship the "small panoti" / dhaiyya check** as a separate
  function: Ashtama Shani (Saturn 8th from Moon) and Kantaka /
  Ardhashtama Shani (Saturn 4th from Moon), each ~2.5 yr — return a
  string label or `None`.

## Task scope

`mayaastrolib/vedic/sadesati.py`:

```python
@dataclass(frozen=True)
class SadeSatiPhase:
    active: bool
    phase: str       # "rising" | "peak" | "setting" | "not-active"
    saturn_sign: str
    natal_moon_sign: str
    severity: str    # "intense" | "moderate" | "mild" | "none"

def saturn_sidereal_sign(target, ayanamsa=...) -> int   # 0..11
def sade_sati(natal_moon_sign, target, ayanamsa=...) -> SadeSatiPhase
def sade_sati_for_year(natal_moon_sign, year, ayanamsa=...) -> SadeSatiPhase  # checks mid-year
def small_panoti(natal_moon_sign, target, ayanamsa=...) -> str | None  # "ashtama_shani" | "kantaka_shani" | None
```

`natal_moon_sign` accepts either an int 0..11 or a sign-name string
(`const.ARIES`, …) — normalise internally. `sade_sati_for_year` checks
at July 1 noon UTC of the given year.

## Tests (`tests/test_vedic_sadesati.py`)

- Synthetic-position tests using a fixed natal Moon sign: pick dates
  where Saturn's known sidereal sign produces each phase. (Verify
  Saturn's sidereal sign at a couple of well-known dates first, then
  pin.)
- Phase logic unit-tested directly via a small internal helper that
  takes (saturn_sign, moon_sign) → phase — so we don't depend on
  ephemeris for the core logic test.
- `sade_sati` with Saturn far from the Moon → `not-active`, `severity
  == "none"`, `active == False`.
- `small_panoti`: Saturn 8th from Moon → `"ashtama_shani"`; 4th → 
  `"kantaka_shani"`; elsewhere → `None`.
- Sign-name and int inputs for `natal_moon_sign` produce the same result.

## Out of scope

- Day-precise Sade Sati start/end dates (requires Saturn ingress
  search) — a follow-up; this task is "what phase is active at moment T".
- Sade Sati remedial recommendations — presentational.

## Process

Branch `task-022-vedic-sadesati`. Commits: `feat: add vedic.sadesati`,
then `docs: update CHANGELOG, PROJECT-LOG, CLAUDE.md for Task 022`.
Pre-completion checklist: ruff format/check, mypy (no new errors),
pytest, coverage ≥80%. PROJECT-LOG must note the Saturn-sidereal-sign
value at the test dates. Push, verify CI, DO NOT merge.

## Definition of done

- `sade_sati`, `sade_sati_for_year`, `small_panoti` implemented.
- Phase logic and severity correct per the taxonomy above.
- Tests pass; existing tests unaffected. CHANGELOG/PROJECT-LOG/CLAUDE.md
  updated. CI green.

# Task 023: Vedic Upagrahas

## Context

Read `CLAUDE.md`, the `vedic/upagrahas.py` section of
`docs/2026-05-11-vedic-extension-spec.md`, and confirm Tasks 017–022 have
merged. Read `mayaastrolib/ephem/ephem.py` (`nextSunrise`, `nextSunset`,
`lastSunrise`) and `mayaastrolib/vedic/sadesati.py` for the module
style. Confirm `pytest tests/` passes (~342 after Task 022).

## Why this task exists

Upagrahas ("sub-planets") are sensitive points used in Vedic chart
analysis. Two computation schools:
- **School B** (Phaladeepika): the 5 Sun-longitude-derived points
  (Dhuma, Vyatipata, Parivesha, Indrachapa/Chapa, Upaketu). Pure
  arithmetic, no location.
- **School A** (B.V. Raman): Gulika/Mandi via the weekday-portion
  ascendant method. Needs date + lat/lng + sunrise/sunset.

## Design decisions (already made)

- **School B formulas** (from the Sun's *sidereal* longitude S):
  - Dhuma = S + 133°20'
  - Vyatipata = 360° − Dhuma
  - Parivesha = Vyatipata + 180°
  - Indrachapa (Chapa) = 360° − Parivesha
  - Upaketu = Chapa + 16°40'
  All normalised to [0, 360).
- **School A — Gulika:** divide the relevant span (sunrise→sunset for a
  day birth, sunset→next-sunrise for a night birth) into 8 equal parts.
  The parts are ruled in weekday order (Sun, Moon, Mars, Mercury,
  Jupiter, Venus, Saturn) starting — for a day birth — from the day's
  lord, and — for a night birth — from the lord of the 5th weekday
  (counting the day's lord as 1st). Gulika's longitude = the (sidereal)
  ascendant at the **start** of the Saturn-ruled part. Mandi is treated
  as a synonym of Gulika here.
- **Weekday is the civil-date weekday** (Sunday=0). The true astrological
  day runs sunrise→sunrise, so a pre-dawn birth is technically the
  previous weekday — document this approximation; don't fix it in this
  task.
- **`UpagrahaResult` is a frozen dataclass:** `name`, `sidereal_longitude`,
  `sign` (name), `deg_in_sign`.
- **`upagrahas(chart, school="B", ayanamsa=...)`** — `school="B"` returns
  the 5 Sun-derived; `school="A"` returns `{"Gulika": ...}` (and the
  Sun-derived ones too, since they're cheap). Default `"B"`.

## Task scope

`mayaastrolib/vedic/upagrahas.py`:

```python
@dataclass(frozen=True)
class UpagrahaResult:
    name: str
    sidereal_longitude: float
    sign: str
    deg_in_sign: float

WEEKDAY_LORDS = [SUN, MOON, MARS, MERCURY, JUPITER, VENUS, SATURN]  # idx 0=Sunday

def sun_derived_upagrahas(sun_sidereal_lon) -> dict[str, float]   # 5 longitudes
def gulika_longitude(chart, ayanamsa=...) -> float                # sidereal lon
def upagrahas(chart, school="B", ayanamsa=...) -> dict[str, UpagrahaResult]
```

## Tests (`tests/test_vedic_upagrahas.py`)

- School B formulas: hand-check each from a fixed Sun longitude
  (e.g. S=100° → Dhuma=233°20', Vyatipata=126°40', etc.). Verify the
  chained relations (Vyatipata + Dhuma = 360°; Chapa + Parivesha = 360°).
- All 5 longitudes in [0, 360).
- `gulika_longitude` returns a valid longitude for a known day and night
  birth; verify it differs between a day birth and a night birth at the
  same location.
- `upagrahas(chart, school="B")` returns 5 results; `school="A"` includes
  "Gulika".
- `UpagrahaResult.sign` and `deg_in_sign` are consistent with
  `sidereal_longitude`.
- Tropical-and-sidereal charts produce the same upagraha signs.

## Out of scope

- The "5 Kala-velas" weekday-portion points (Kala, Mrityu, Artha-prahara,
  Yamaghantaka, plus Gulika) as a full set — only Gulika is in scope here.
- Day-precise sunrise-day weekday correction — documented approximation.
- Mandi-vs-Gulika distinction (start vs midpoint vs end of Saturn part) —
  this task uses start-of-part for both.

## Process

Branch `task-023-vedic-upagrahas`. Commits: `feat: add vedic.upagrahas`,
then `docs: update CHANGELOG, PROJECT-LOG, CLAUDE.md for Task 023`.
Pre-completion checklist: ruff format/check, mypy (no new errors),
pytest, coverage ≥80%. Push, verify CI, DO NOT merge.

## Definition of done

- `sun_derived_upagrahas`, `gulika_longitude`, `upagrahas` implemented.
- School B formulas correct (chained relations hold).
- Gulika differs day-vs-night.
- Tests pass; existing tests unaffected. Docs updated. CI green.

# Task 021: Vedic Ashtakavarga (BAV + SAV)

## Context

Read `CLAUDE.md`, `docs/2026-05-11-vedic-extension-spec.md` (the
`vedic/ashtakavarga.py` section), and confirm Tasks 017–020 have merged
to `development`. Read `mayaastrolib/vedic/divisional.py` and
`mayaastrolib/vedic/nakshatras.py` for the established module style.
Confirm `pytest tests/` passes (~304 tests after Task 020).

## Why this task exists

Ashtakavarga is the bindu (benefic-point) system. Each of the 7 classical
planets gets a Bhinnashtakavarga (BAV) — a 12-cell array counting how
many points it receives in each sign, contributed by the positions of 8
bodies (7 planets + Ascendant). The Sarvashtakavarga (SAV) sums the 7
planetary BAVs per sign, canonically totalling 337. Used heavily in
transit timing and the per-month bindu rendering in yearly forecasts.

## Design decisions (already made)

- **8 contributors per BAV** (7 planets + Ascendant) — "ashta" = 8.
- **SAV = sum of the 7 planetary BAVs only** (not Lagna's). Canonical
  grand total = 337. This is the standard rule set.
- **Pure functions on sign indices.** `bhinnashtakavarga(planet,
  signs_dict)` takes the planet ID and a dict {body_id: sign_idx 0-11},
  returns a 12-cell list. `sarvashtakavarga(planet_signs, lagna_sign)`
  composes them. A chart-level `ashtakavarga(chart, ayanamsa=...)` wraps
  both, extracting sidereal signs from the chart.
- **BAV tables are data, not code.** Module-level dict of dicts. The
  canonical BPHS Ch. 66 tables (verify the per-planet totals: Sun 48,
  Moon 49, Mars 39, Mercury 54, Jupiter 56, Venus 52, Saturn 39 — these
  sum to 337).
- **House counting: house 1 = same sign as contributor.** So a bindu at
  "house h from contributor C" lands in sign `(c_sign + h - 1) % 12`.

## Task scope

`mayaastrolib/vedic/ashtakavarga.py`:

```python
ASHTAKAVARGA_TABLES = {
    const.SUN: {
        const.SUN: [1, 2, 4, 7, 8, 9, 10, 11],
        const.MOON: [3, 6, 10, 11],
        const.MARS: [1, 2, 4, 7, 8, 9, 10, 11],
        const.MERCURY: [3, 5, 6, 9, 10, 11, 12],
        const.JUPITER: [5, 6, 9, 11],
        const.VENUS: [6, 7, 12],
        const.SATURN: [1, 2, 4, 7, 8, 9, 10, 11],
        "Ascendant": [3, 4, 6, 10, 11, 12],
    },
    # ... Moon, Mars, Mercury, Jupiter, Venus, Saturn
}

ASHTAKAVARGA_CONTRIBUTORS = [SUN, MOON, MARS, MERCURY, JUPITER, VENUS, SATURN, "Ascendant"]
ASHTAKAVARGA_PLANETS = [SUN, MOON, MARS, MERCURY, JUPITER, VENUS, SATURN]

def bhinnashtakavarga(planet, signs) -> list[int]:  # 12 cells
def sarvashtakavarga(planet_signs, lagna_sign) -> dict  # {per_rasi, grand_total, by_planet}
def ashtakavarga(chart, ayanamsa=...) -> dict  # chart-level
```

Use the literal string `"Ascendant"` as the Lagna contributor key (it is
not a planet ID; `const.ASC` is the angle ID `"Asc"`, which would also
work — pick one and be consistent).

## Tests (`tests/test_vedic_ashtakavarga.py`)

- Each of the 7 BAV tables sums to its canonical total (48/49/39/54/56/52/39).
- The 7 totals sum to 337.
- `bhinnashtakavarga` returns a 12-cell list summing to the planet's total
  regardless of the input positions (a BAV is a histogram of a fixed
  number of bindus).
- A hand-computed micro case: all 8 bodies at sign 0 (Aries) — then for
  the Sun, sign `(0 + h - 1) % 12` for each `h` in the Sun's table, summed
  over all 8 contributors. Verify a couple of cells.
- `sarvashtakavarga` grand_total == 337 for any chart.
- `ashtakavarga(chart)` works on a sidereal chart; tropical-and-sidereal
  charts agree.

## Out of scope

- Trikona/Ekadhipatya shodhana (reduction techniques) — separate task.
- Kakshya (the 8 sub-divisions within a sign) — separate task.
- Bindu-based transit prediction logic — presentational, downstream.

## Process

Branch `task-021-vedic-ashtakavarga`. Commits: `feat: add
vedic.ashtakavarga with BAV/SAV tables`, then `docs: update CHANGELOG,
PROJECT-LOG, CLAUDE.md for Task 021`. Pre-completion checklist: ruff
format/check, mypy (no new errors), pytest, coverage ≥80%. PROJECT-LOG
entry must confirm the 337 invariant and cite the BPHS Ch. 66 table
source. Push, verify CI, DO NOT merge (the orchestrating session merges).

## Definition of done

- All 7 BAV tables present and summing correctly; SAV = 337.
- `bhinnashtakavarga`, `sarvashtakavarga`, `ashtakavarga` implemented.
- Tests pass; existing tests unaffected.
- CHANGELOG + PROJECT-LOG + CLAUDE.md updated. CI green.

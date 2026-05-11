# Task 026: Vedic Yoga Detection

## Context

Read `CLAUDE.md`, the `vedic/yogas.py` section of
`docs/2026-05-11-vedic-extension-spec.md`, and confirm Tasks 017–024
merged. Read `mayaastrolib/vedic/divisional.py` (sign-index helpers and
the tropical→sidereal pattern) and `mayaastrolib/const.py` (sign names).
Confirm `pytest tests/` passes (~372 after Task 024).

## Why this task exists

Yogas are the named planetary combinations that drive Vedic
interpretation. Detecting them programmatically (Ruchaka, Hamsa,
Gaja-Kesari, …) is the kind of feature that makes a chart library feel
complete. This task ships a focused, unambiguous set: the 5 Pancha
Mahapurusha yogas plus Gaja-Kesari, Budha-Aditya, and Chandra-Mangala.

## Design decisions (already made)

- **Whole-Sign kendras.** A planet is "in a kendra" iff its sign is the
  1st, 4th, 7th, or 10th from the Ascendant's sign — i.e. `(planet_sign
  − asc_sign) % 12 + 1 ∈ {1, 4, 7, 10}`. Use this regardless of the
  chart's `hsys`; Vedic yoga rules are Whole-Sign by convention. Document
  it. (Likewise "Jupiter in a kendra from the Moon" uses sign offsets.)
- **Vedic dignities** (own / exalted signs) are the classical ones —
  these are *not* the Western essential-dignity table. Encode them
  fresh in this module.
- **Scope = 8 yoga types:**
  - Pancha Mahapurusha: **Ruchaka** (Mars), **Bhadra** (Mercury),
    **Hamsa** (Jupiter), **Malavya** (Venus), **Sasha** (Saturn) — the
    planet in its own or exaltation sign *and* in a kendra.
  - **Gaja-Kesari** — Jupiter in the 1st/4th/7th/10th from the Moon.
  - **Budha-Aditya** (Nipuna) — Mercury and Sun in the same sign.
  - **Chandra-Mangala** — Moon and Mars in the same sign.
- **`YogaResult` is a frozen dataclass:** `name`, `sanskrit`,
  `planets` (tuple of planet IDs), `description`.
- **`detect_yogas(chart, ayanamsa=...)`** returns a list of `YogaResult`,
  possibly empty. Handles tropical-or-sidereal charts (tropical → shift
  to sidereal first).

## Task scope

`mayaastrolib/vedic/yogas.py`:

```python
@dataclass(frozen=True)
class YogaResult:
    name: str
    sanskrit: str
    planets: tuple
    description: str

OWN_SIGNS = {SUN: [LEO], MOON: [CANCER], MARS: [ARIES, SCORPIO],
             MERCURY: [GEMINI, VIRGO], JUPITER: [SAGITTARIUS, PISCES],
             VENUS: [TAURUS, LIBRA], SATURN: [CAPRICORN, AQUARIUS]}
EXALTATION_SIGN = {SUN: ARIES, MOON: TAURUS, MARS: CAPRICORN,
                   MERCURY: VIRGO, JUPITER: CANCER, VENUS: PISCES,
                   SATURN: LIBRA}
PANCHA_MAHAPURUSHA = {MARS: ("Ruchaka", ...), MERCURY: ("Bhadra", ...),
                      JUPITER: ("Hamsa", ...), VENUS: ("Malavya", ...),
                      SATURN: ("Sasha", ...)}
KENDRA_HOUSES = (1, 4, 7, 10)

def is_in_own_or_exaltation(planet, sign_idx) -> bool
def house_from(reference_sign, planet_sign) -> int   # 1..12, Whole-Sign
def detect_yogas(chart, ayanamsa=...) -> list[YogaResult]
```

## Tests (`tests/test_vedic_yogas.py`)

- `is_in_own_or_exaltation`: Mars in Aries → True; Mars in Capricorn
  (exalted) → True; Mars in Cancer (debilitated) → False; Mars in Leo →
  False.
- `house_from`: reference Aries (0), planet Aries (0) → 1; planet Cancer
  (3) → 4; planet Capricorn (9) → 10; planet Pisces (11) → 12.
- Construct synthetic charts (real `Chart` objects at chosen dates) that
  do/don't exhibit each yoga. To avoid hunting for the perfect date,
  also unit-test the *core logic* via small helpers that take
  (planet_signs dict, asc_sign) and return the yoga list — so the logic
  tests don't depend on the ephemeris.
- A no-yoga chart returns `[]` (or only the yogas it genuinely has).
- Budha-Aditya fires iff Sun and Mercury share a sign.
- Gaja-Kesari fires iff Jupiter is 1/4/7/10 from the Moon.
- `detect_yogas` works on a sidereal chart and (with ayanamsa) on the
  equivalent tropical chart, producing the same yoga set.

## Out of scope

- Raja yogas (kendra-trikona lord conjunction/aspect), Dhana yogas,
  Vipareeta Raja yogas, Neecha Bhanga, Kemadruma, Gaja-Kesari's
  cancellation conditions — a follow-up.
- Yoga "strength" scoring or remediation — presentational.

## Process

Branch `task-026-vedic-yogas`. Commits: `feat: add vedic.yogas`, then
`docs: update CHANGELOG, PROJECT-LOG, CLAUDE.md for Task 026`.
Pre-completion checklist: ruff format/check, mypy (no new errors),
pytest, coverage ≥80%. PROJECT-LOG must note the Whole-Sign-kendra
decision and which sample dates were used to exercise each yoga. Push,
verify CI, DO NOT merge.

## Definition of done

- `detect_yogas` implemented; the 8 yoga types detected correctly.
- Core logic unit-tested independent of the ephemeris.
- Tests pass; existing tests unaffected. Docs updated. CI green.

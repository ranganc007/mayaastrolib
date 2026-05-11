# mayaastrolib — Vedic Jyotisha Extension Spec

**Date:** 2026-05-11
**Target repo:** `https://github.com/ranganc007/mayaastrolib` (your MIT fork of flatlib)
**Local path:** `/opt/homebrew/var/www/oss-contrib/mayaastrolib/`
**Status:** spec — ready to plan
**Author:** drafted in the mayaastro repo to motivate execution; should be moved or copied to the mayaastrolib repo for implementation

---

## Context

mayaastrolib (= flatlib) is a Western/Hellenistic traditional-astrology library. It ships modules for:
- `predictives/`: primary directions, profections, solar/lunar returns
- `tools/`: Arabic parts, chart dynamics, planetary hours
- `dignities/`: essential + accidental, almutems, Egyptian Terms
- `ephem/`: Swiss Ephemeris bindings

It does **not** ship any Vedic Jyotisha tradition. The MayaAstro main repo therefore has 9+ Vedic compute modules with no parity oracle (Vimshottari dasha, divisional charts, Ashtakavarga, Tajika varshapravesh layer, Sade Sati, Mangal Dosha, Yogas, panchang, KP). The Vedic side ships unverified.

Since you own the MIT fork, the cleanest path is to **add Vedic Jyotisha modules to mayaastrolib** rather than introducing a third oracle library. Benefits:
- One Python venv for all parity (`.venv-oracle`)
- One license posture (MIT throughout)
- Each new mayaastrolib module unblocks a sibling MayaAstro parity test
- The fork becomes a useful open-source contribution in its own right (no Python lib today combines Hellenistic + Vedic in one MIT-licensed package — flatlib + vedicastro is the closest, but those are separate)

---

## Architecture decision

**Add a new top-level `vedic/` package** alongside `predictives/` and `tools/`:

```
mayaastrolib/mayaastrolib/
├── chart.py         (existing)
├── const.py         (existing — extend with Vedic constants)
├── dignities/       (existing)
├── ephem/           (existing)
├── predictives/     (existing — Western)
│   ├── primarydirections.py
│   ├── profections.py
│   └── returns.py
├── protocols/       (existing)
├── tools/           (existing)
│   └── arabicparts.py
└── vedic/           ← NEW
    ├── __init__.py
    ├── ayanamsa.py        # Lahiri + Krishnamurti + Raman
    ├── nakshatras.py       # 27-nakshatra arithmetic, lord, pada
    ├── divisional.py       # All 16 vargas (D1-D60)
    ├── dasha.py            # Vimshottari MD/AD/Pratyantar
    ├── ashtakavarga.py     # BAV + SAV bindu tables
    ├── sadesati.py         # Saturn-Moon phase detection
    ├── tajika.py           # Varshapravesh + Mudda Dasha + Sahams
    ├── upagrahas.py        # Mandi, Dhuma, etc.
    ├── kp.py               # Krishnamurti Paddhati 249 sub-lord table
    └── yogas.py            # Classical yoga detection (Raja, Dhana, etc.)
```

**Rationale:** keeps Vedic clearly separated from the Western tradition modules; users who only want Western imports never load Vedic code (and vice versa); the existing `chart.Chart` is reused as the input — no duplicate chart-building.

**Naming:** classes/functions use Sanskrit terms (`Vimshottari`, `Navamsa`, `Bhinnashtakavarga`) since that's the canonical vocabulary; English comments explain.

---

## Module list — priority + effort

Ordered by signal-to-effort. P0 = highest value (unblocks the most existing MayaAstro modules).

| Priority | Module | Effort | Unblocks parity for |
|---|---|---:|---|
| **P0** | `ayanamsa.py` | 0.5 day | All Vedic compute (foundation — every other module depends on it) |
| **P0** | `nakshatras.py` | 0.5 day | `src/data/nakshatras.ts`, panchang, dasha balance |
| **P0** | `divisional.py` | 1 day | `src/lib/karmic/divisional.ts` (D9/D12/D3) + `src/lib/karmic/vargas/` (D2/D7/D10/D16/D20/D24/D27/D30/D40/D45/D60) |
| **P0** | `dasha.py` | 1 day | `src/lib/dasha.ts` Vimshottari MD/AD + `src/lib/yearlyForecast/index.ts` mahadashaForYear |
| **P1** | `ashtakavarga.py` | 1.5 days | `src/lib/ashtakavarga.ts` BAV + SAV bindu tables |
| **P1** | `sadesati.py` | 0.5 day | `src/lib/sadeSati.ts` |
| **P1** | `upagrahas.py` | 0.5 day | `src/lib/upagrahas/compute.ts` (we already verified School B math; this would verify School A) |
| **P2** | `tajika.py` | 2 days | `src/lib/tajika/varshapravesh.ts` + the full Tajika Neelakanthi annual horoscope layer |
| **P2** | `kp.py` | 2 days | `src/lib/kp/advanced.ts` 249 sub-lord boundaries (we already cross-check vs RedAstrologer + Aryan Astrology references in `tests/kp249.test.ts`, but a programmatic oracle would catch any future drift) |
| **P3** | `yogas.py` | 2 days | `src/lib/yogas.ts` classical yoga detection (Raja, Dhana, Pancha-mahapurusha, etc.) |

**Total effort: ~11.5 days** to fully cover the Vedic side. P0 alone (3 days) unlocks parity for the most-used modules.

---

## Per-module API design

### `vedic/ayanamsa.py` (P0, 0.5 day)

```python
from mayaastrolib.datetime import Datetime

def lahiri(date: Datetime) -> float:
    """Lahiri ayanamsa in degrees at the given date.
    Per IAU 1976 + ICRF correction; matches Indian Astronomical Ephemeris."""

def krishnamurti(date: Datetime) -> float:
    """KP ayanamsa = Lahiri - 0.00375°. Matches K.S. Krishnamurti's original 1971 spec."""

def raman(date: Datetime) -> float:
    """B.V. Raman's ayanamsa. Slightly different epoch from Lahiri."""

def fagan_bradley(date: Datetime) -> float:
    """Western sidereal (Fagan-Bradley) — for comparison only, not used in Vedic."""

# Convert tropical longitude to sidereal under a chosen ayanamsa.
def to_sidereal(tropical_lon: float, date: Datetime, ayanamsa: str = "lahiri") -> float: ...
```

**Implementation notes:** Swiss Ephemeris already exposes `swe.set_sid_mode(swe.SIDM_LAHIRI)` and `swe.get_ayanamsa(jd)`. This module is mostly a thin wrapper.

**Parity test in MayaAstro:** new `tests/parity/ayanamsaParity.test.ts` against our `src/lib/vedic.ts` `lahiriAyanamsa()` at ±0.001° (tight — both should be using the same IAU formula).

### `vedic/nakshatras.py` (P0, 0.5 day)

```python
NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", ..., "Revati"  # all 27, in order
]

NAKSHATRA_LORDS = [  # Vimshottari rulership cycle
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", ...  # 27 entries
]

class Nakshatra:
    name: str
    lord: str
    pada: int  # 1..4

def of_longitude(sidereal_lon: float) -> Nakshatra:
    """Return the nakshatra at a sidereal longitude (0..360)."""

def janma_nakshatra(chart, ayanamsa: str = "lahiri") -> Nakshatra:
    """Return the natal Moon's nakshatra ('birth star')."""

def tarabala(natal_moon_nak: Nakshatra, transit_moon_nak: Nakshatra) -> int:
    """9-tara cycle position, 1..9. Per Muhurta Chintamani 6.6."""
```

**Parity test:** verify our `src/data/nakshatras.ts` `getNakshatra(lon)` produces the same name + pada as flatlib at 1000 random sidereal longitudes.

### `vedic/divisional.py` (P0, 1 day)

```python
def navamsa(sidereal_lon: float) -> int:
    """D9 sign index 0..11. BPHS ch. 6 śloka 6-9."""

def dvadasamsa(sidereal_lon: float) -> int:
    """D12 sign index. BPHS ch. 6."""

def drekkana(sidereal_lon: float) -> int:
    """D3 sign index. BPHS ch. 7."""

# ...then the 11 we shipped in src/lib/karmic/vargas/:
def hora(sidereal_lon: float) -> int: ...           # D2
def saptamsa(sidereal_lon: float) -> int: ...        # D7
def dasamsa(sidereal_lon: float) -> int: ...         # D10
def shodasamsa(sidereal_lon: float) -> int: ...      # D16
def vimsamsa(sidereal_lon: float) -> int: ...        # D20
def chaturvimsamsa(sidereal_lon: float) -> int: ...  # D24
def bhamsa(sidereal_lon: float) -> int: ...          # D27
def trimsamsa(sidereal_lon: float) -> int: ...       # D30 (special — 5 unequal segments)
def khavedamsa(sidereal_lon: float) -> int: ...      # D40
def akshavedamsa(sidereal_lon: float) -> int: ...    # D45
def shastiamsa(sidereal_lon: float) -> int: ...      # D60

def all_vargas(chart, ayanamsa: str = "lahiri") -> dict[str, dict[str, int]]:
    """Return {varga_name: {planet_name: sign_idx}} for all 15 Shodashavarga."""
```

**Parity test:** for our 2 reference charts × 9 grahas × 15 vargas = 270 sign assertions. Catches any off-by-one or modality-table typos.

### `vedic/dasha.py` (P0, 1 day)

```python
class DashaPeriod:
    lord: str
    start: Datetime
    end: Datetime

class VimshottariResult:
    janma_nakshatra: Nakshatra
    birth_balance: dict  # {lord, years_remaining}
    sequence: list[DashaPeriod]  # full 120-year MD sequence
    current_md: DashaPeriod
    current_ad: DashaPeriod

def vimshottari(chart, target: Datetime = None, ayanamsa: str = "lahiri") -> VimshottariResult:
    """Compute Vimshottari Mahadasha for a chart. If target given, returns
    the MD/AD active at that target date."""

def antardashas(md: DashaPeriod) -> list[DashaPeriod]:
    """Return the 9 antardashas of a Mahadasha."""

def pratyantar_dashas(ad: DashaPeriod) -> list[DashaPeriod]:
    """Return the 9 pratyantardashas of an antardasha."""
```

**Parity test:** for our 2 reference charts at 5 sample target dates each, verify our `computeDasha(birthDate, now)` returns the same `(currentMaha.planet, currentAntar.planet)` pair as flatlib at that target. 20 strict assertions.

### `vedic/ashtakavarga.py` (P1, 1.5 days)

```python
def bhinnashtakavarga(contributor: str, signs: dict[str, int]) -> list[int]:
    """7-row × 12-col Bhinnashtakavarga for one contributing planet.
    Per BPHS ch. 8 śloka 24-43. Returns 12-cell bindu array."""

def sarvashtakavarga(planet_signs: dict[str, int], lagna_sign: int) -> dict:
    """SAV grand total = sum of 7 BAVs. Returns {per_rasi: [12], grand_total: int, by_planet: {name: [12]}}.
    Canonical grand total = 337 for the standard rule set."""
```

**Parity test:** 2 charts × 7 BAVs × 12 cells = 168 strict bindu assertions. SAV grand total = 337 invariant. Catches any rule-table typo.

### `vedic/sadesati.py` (P1, 0.5 day)

```python
class SadeSatiPhase:
    active: bool
    phase: str  # "rising" | "peak" | "setting" | "not-active"
    saturn_sign: str  # the sign Saturn currently transits
    natal_moon_sign: str
    severity: str  # "mild" | "moderate" | "intense"

def sade_sati(natal_moon_sign: str, target: Datetime, ayanamsa: str = "lahiri") -> SadeSatiPhase: ...

def sade_sati_for_year(natal_moon_sign: str, year: int, ayanamsa: str = "lahiri") -> SadeSatiPhase: ...
```

**Parity test:** 2 charts × 5 sample years = 10 SadeSati phase assertions. Validates `src/lib/sadeSati.ts` against an independent Saturn transit.

### `vedic/upagrahas.py` (P1, 0.5 day)

```python
class UpagrahaResult:
    name: str  # "Mandi" | "Dhuma" | ...
    sidereal_longitude: float
    sign: str
    deg_in_sign: float

def upagrahas(chart, school: str = "B", ayanamsa: str = "lahiri") -> dict[str, UpagrahaResult]:
    """Return all 7 upagrahas. school = 'A' (B.V. Raman ascendant-at-segment-rising,
    requires lat/lng + sunrise/sunset) or 'B' (Phaladeepika simpler form)."""
```

**Parity test:** verifies our `src/lib/upagrahas/compute.ts` against a second source. Especially valuable for Mandi School A (currently shipped only as the Phaladeepika simplification).

### `vedic/tajika.py` (P2, 2 days)

```python
def varshapravesh(natal_chart, target_year: int, ayanamsa: str = "lahiri") -> Datetime:
    """Find the moment the SIDEREAL Sun returns to its natal sidereal position
    in the target year. Tajika annual chart timing."""

def mudda_dasha(varshapravesh: Datetime, ayanamsa: str = "lahiri") -> list[DashaPeriod]:
    """9 Mudda sub-periods within the year, summing to 365.25 days.
    Per Tajika Neelakanthi."""

def lord_of_year(annual_chart) -> str:
    """Tajika Varsheshwara — strongest of 5 candidates per Tajika Neelakanthi."""

def harsha_bala(annual_chart) -> dict[str, float]:
    """Per-planet Harsha Bala (joy) score. 5 components, max 65."""

def panchavargiya_bala(annual_chart) -> dict[str, dict]:
    """K/H/D/N/Trimshamsha components. Per BPHS 31.4-6 (Vedic carried into Tajika)."""

def sahams(annual_chart) -> dict[str, float]:
    """The 50+ Tajika Sahams (sensitive points). Returns {saham_name: longitude}."""
```

**Parity test:** unblocks the entire Tajika layer in MayaAstro. We currently cross-check Tajika math vs Clickastro reference in `tests/varshaphalRegression.test.ts` (5 charts) — having a programmatic oracle would let us add hundreds more reference charts cheaply.

### `vedic/kp.py` (P2, 2 days)

```python
def kp_249_table() -> list[dict]:
    """The full 249-row KP sub-lord table. Each row: {start_lon, end_lon, sign, sign_lord, star_lord, sub_lord}."""

def sub_lord_at(sidereal_lon: float) -> dict:
    """Return KP sub-lord chain (sign / star / sub / sub-sub) for a position."""

def horary(prashna_number: int, target: Datetime, lat: float, lng: float) -> Chart:
    """KP horary chart for a prashna (1..249) at a given moment."""

def ruling_planets(target: Datetime, lat: float, lng: float, ayanamsa: str = "krishnamurti") -> dict:
    """Ruling Planets at the moment of question — Lagna/Moon/Day-lord/Hour-lord/Asc-sub-lord."""
```

**Parity test:** rebuilds the kp249 cross-check programmatically (we currently have `tests/kp249.test.ts` with 33 hand-coded assertions; a flatlib-Vedic oracle would let us auto-test all 249 boundaries).

### `vedic/yogas.py` (P3, 2 days)

```python
class YogaResult:
    name: str
    sanskrit: str
    description: str
    citation: str  # BPHS / Phaladeepika / Saravali reference

def detect_yogas(chart, ayanamsa: str = "lahiri") -> list[YogaResult]:
    """Detect all classical yogas in the chart. Returns Pancha Mahapurusha
    (Ruchaka/Bhadra/Hamsa/Malavya/Sasha), Raja Yogas, Dhana Yogas,
    Vipareeta Raja Yogas, Gaja-Kesari, Lakshmi, Saraswati, Karma, Bhakti,
    Jnana, Daridra, Pravrajya/Sannyasa per BPHS ch. 78 + Phaladeepika ch. 6-7
    + Saravali ch. 33-35."""
```

**Parity test:** verifies `src/lib/yogas.ts` (currently 11 detectors). Catches any drift in the strict-config rules.

---

## Implementation order (dependency-aware)

```
P0 — Foundation (3 days):
  ayanamsa.py
  nakshatras.py
  divisional.py
  dasha.py

P1 — Predictive layer (2.5 days):
  ashtakavarga.py
  sadesati.py
  upagrahas.py

P2 — Specialized (4 days):
  tajika.py
  kp.py

P3 — Interpretation (2 days):
  yogas.py
```

After each P-tier, the corresponding parity tests in MayaAstro main repo can be added (described per-module above). Total: ~11.5 days dev + ~2 days parity tests = **~13.5 days** for full Vedic coverage.

---

## Testing strategy

For each new module in mayaastrolib:

1. **Unit tests** (in mayaastrolib repo) following the existing `tests/test_*.py` pattern — pure-Python assertions against published reference values from BPHS / Phaladeepika / Tajika Neelakanthi.

2. **Parity fixtures** (in MayaAstro main repo) — extend `scripts/oracle-fixtures.py` with one new mode per module:
   ```bash
   .venv-oracle/bin/python scripts/oracle-fixtures.py vimshottari > tests/parity/vimshottari-fixtures.json
   .venv-oracle/bin/python scripts/oracle-fixtures.py vargas > tests/parity/vargas-fixtures.json
   .venv-oracle/bin/python scripts/oracle-fixtures.py ashtakavarga > tests/parity/ashtakavarga-fixtures.json
   .venv-oracle/bin/python scripts/oracle-fixtures.py sadesati > tests/parity/sadesati-fixtures.json
   .venv-oracle/bin/python scripts/oracle-fixtures.py upagrahas > tests/parity/upagrahas-fixtures.json
   .venv-oracle/bin/python scripts/oracle-fixtures.py tajika > tests/parity/tajika-fixtures.json
   .venv-oracle/bin/python scripts/oracle-fixtures.py kp249 > tests/parity/kp249-fixtures.json
   .venv-oracle/bin/python scripts/oracle-fixtures.py yogas > tests/parity/yogas-fixtures.json
   ```

3. **Vitest parity tests** — one per module, follows the existing `tests/parity/*.test.ts` pattern.

---

## MayaAstro integration unblock

What ships from the main repo when each mayaastrolib module lands:

| When this lands in mayaastrolib... | ...this becomes parity-verified in MayaAstro |
|---|---|
| `vedic/ayanamsa` | `src/lib/vedic.ts` `lahiriAyanamsa()` |
| `vedic/nakshatras` | `src/data/nakshatras.ts` + `src/lib/panchang.ts` nakshatra arithmetic |
| `vedic/divisional` | All 15 vargas in `src/lib/karmic/{divisional,vargas}/` |
| `vedic/dasha` | `src/lib/dasha.ts` + `src/lib/yearlyForecast/index.ts` mahadashaForYear |
| `vedic/ashtakavarga` | `src/lib/ashtakavarga.ts` (foundation of the per-month bindu rendering in yearly PDFs) |
| `vedic/sadesati` | `src/lib/sadeSati.ts` |
| `vedic/upagrahas` | `src/lib/upagrahas/compute.ts` (validates Mandi School A) |
| `vedic/tajika` | `src/lib/tajika/varshapravesh.ts` + the entire Tajika annual layer (huge) |
| `vedic/kp` | `src/lib/kp/advanced.ts` + sub-lord chain |
| `vedic/yogas` | `src/lib/yogas.ts` 11 yoga detectors |

**Cumulative impact:** every single Vedic compute module in MayaAstro main repo would have a programmatic oracle. Currently zero of them do (we have one-off cross-checks against Clickastro PDFs, RedAstrologer references, etc.). This is the single biggest accuracy/regression-prevention investment available.

---

## Open-source value of the fork

This extension makes mayaastrolib **the only MIT-licensed Python library combining Hellenistic + Vedic Jyotisha in one package**. Today the closest options are:

- `flatlib` (MIT, Hellenistic only)
- `vedicastro` / `vedicastro-py` (MIT, Vedic only, less complete than spec'd above)
- Combine the two — separate venvs, separate APIs, separate maintenance

Shipping mayaastrolib with a `vedic/` package fills a real gap. Worth pushing the fork upstream as an open-source contribution.

---

## Recommended execution order

1. **Week 1**: P0 (ayanamsa + nakshatras + divisional + dasha). 4 days. Adds 4 parity tests in MayaAstro covering the most-used Vedic modules.

2. **Week 2**: P1 (ashtakavarga + sadesati + upagrahas). 2.5 days. Adds 3 more parity tests including the all-important Ashtakavarga rules.

3. **Week 3**: P2 (tajika + kp). 4 days. Closes the loop on the entire Tajika annual horoscope (your free differentiator vs Clickastro) and KP horary.

4. **Week 4**: P3 (yogas) + polish + push upstream. 2 days.

Total: ~3 calendar weeks for one focused developer. Or — given the pattern is now well-established — could be done in ~10 elapsed days via aggressive subagent parallelization (each module is independent of the others within a P-tier).

---

## Open questions (for you to decide)

1. **Push upstream to flatangle/flatlib?** Or keep as a private fork?
2. **Vedic class naming — Sanskrit (Navamsa) or English (NinthDivision)?** Current spec uses Sanskrit per Vedic convention. Some Western users may find that opaque.
3. **Multi-ayanamsa support — Lahiri only, or all four (Lahiri / KP / Raman / Fagan-Bradley)?** Spec defaults to Lahiri but exposes all four.
4. **Where does this spec live for execution — in mayaastrolib's `docs/` folder, or in mayaastro's `docs/specs/` (here) only?** Cleanest is to copy to mayaastrolib's `docs/`.
5. **Tradition variants — strict BPHS only, or include Saravali / Phaladeepika alternates?** Spec assumes BPHS as primary citation; can flag classical variants in module docstrings without forking the API.

Tell me which questions to answer and I'll write the implementation plan, or just say "go execute the spec" and I'll build the P0 modules + parity tests next.

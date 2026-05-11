# Task 019: Vedic Divisional Charts (Shodashavarga)

## Context

You are working in the `mayaastrolib` repository. Before doing anything:

1. Read `CLAUDE.md` in full.
2. Read `docs/2026-05-11-vedic-extension-spec.md` — particularly the `vedic/divisional.py` section. **The spec lists 16 vargas. This task ships the 15 standard Shodashavarga (BPHS) — D1 is the rasi chart itself and is just the sidereal sign, not a separate computation.**
3. Read `prompts/task-017-vedic-foundation.md` and `prompts/task-018-vedic-nakshatras.md` — confirm both have shipped.
4. Confirm Tasks 017 + 018 have merged to `development`. If not, STOP.
5. Read `mayaastrolib/vedic/ayanamsa.py` and `mayaastrolib/vedic/nakshatras.py` — note the import patterns, the use of `Datetime`, `const`, the dataclass result-type approach.
6. Confirm `pytest tests/` passes — expected ~245 tests after Tasks 017 + 018.

## Why this task exists

Divisional charts (vargas) are the heart of Vedic predictive analysis. D9 (navamsa) is used in marriage/spouse readings; D10 (dasamsa) for career; D12 (dvadasamsa) for parents; D60 (shastiamsa) for fine-grained karma. Every Vedic-astrology consumer eventually needs all 15.

This is the **largest of the P0 modules** by code volume (because each varga is a separate function) but each varga is small and isolated — no cross-dependencies between them.

## Design decisions (already made — do not relitigate)

- **Pure-function design.** Each varga function takes `sidereal_lon` (a float in degrees) and returns a sign index 0..11 (0 = Aries, 11 = Pisces). No Chart, no Datetime, no Ayanamsa — those concerns belong one level up in `all_vargas`.
- **Each function corresponds to one BPHS rule.** No clever generic-varga abstraction. The rules differ enough (especially D30, the Trimsamsa, which has *unequal* segments by sign parity) that abstraction obscures rather than simplifies. Three similar lines is better than a premature abstraction (per CLAUDE.md).
- **`all_vargas(chart, ayanamsa=...)` is the user-facing entry point.** Returns a nested dict. Most callers will use this and not the individual functions.
- **D1 (rasi) is the chart itself.** `all_vargas` returns it as `{"D1": {planet: sign_for_sidereal_longitude}}` — a thin convenience layer. The 15 *computed* vargas are D2/D3/D4/D7/D9/D10/D12/D16/D20/D24/D27/D30/D40/D45/D60.
- **Standard BPHS scheme for D9 and D10.** There are alternative schemes (Parashara vs Raman for D9; multiple D10 conventions). The spec calls for BPHS canonical; document this in docstrings and flag alternates as "see also" without implementing them in this task.
- **D30 special case is mandatory.** Trimsamsa has 5 unequal segments by sign-parity: odd signs use Mars 5° + Saturn 5° + Jupiter 8° + Mercury 7° + Venus 5°; even signs use Venus 5° + Mercury 7° + Jupiter 8° + Saturn 5° + Mars 5°. Per BPHS 6.29-32. The function signature is the same as the others; the implementation branches.

## Task scope

### Part 1: Module shell

Create `mayaastrolib/vedic/divisional.py`:

```python
"""Divisional charts (Shodashavarga) per BPHS ch. 6-7.

Each varga divides the 30° span of a sign into N equal (or in some cases
unequal) segments and maps each segment to a sign. The mapping is the
"divisional sign" of the planet for that varga.

References:
- BPHS ch. 6 (Shodashavarga definitions)
- BPHS ch. 7 (specific divisional rules and exceptions)
- Phaladeepika ch. 4 (cross-reference for D30 Trimsamsa)

Each function takes a *sidereal* longitude (0..360) and returns the
sign index (0=Aries .. 11=Pisces) the planet falls in for that varga.
Tropical longitudes will produce silently-wrong results — see
`all_vargas` for the chart-level entry point that handles ayanamsa.
"""

from mayaastrolib import const
from mayaastrolib.vedic import ayanamsa as _ay

# Sign indices, 0..11
ARIES = 0
TAURUS = 1
GEMINI = 2
CANCER = 3
LEO = 4
VIRGO = 5
LIBRA = 6
SCORPIO = 7
SAGITTARIUS = 8
CAPRICORN = 9
AQUARIUS = 10
PISCES = 11

SIGN_NAMES = [
    const.ARIES, const.TAURUS, const.GEMINI, const.CANCER,
    const.LEO, const.VIRGO, const.LIBRA, const.SCORPIO,
    const.SAGITTARIUS, const.CAPRICORN, const.AQUARIUS, const.PISCES,
]


def _sign_index(sid_lon: float) -> int:
    """Return sign index 0..11 for a sidereal longitude."""
    return int((sid_lon % 360.0) // 30.0)


def _deg_in_sign(sid_lon: float) -> float:
    """Return position within sign, 0..30."""
    return (sid_lon % 360.0) - _sign_index(sid_lon) * 30.0


def rasi(sid_lon: float) -> int:
    """D1 — the natal sidereal sign. Returns 0..11."""
    return _sign_index(sid_lon)


def hora(sid_lon: float) -> int:
    """D2 (Hora) — wealth indicator. BPHS 6.6.

    Odd signs: first 15° → Leo (Sun), last 15° → Cancer (Moon).
    Even signs: first 15° → Cancer (Moon), last 15° → Leo (Sun).
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    odd = sign % 2 == 0  # Aries=0 is odd by 1-indexed convention
    first_half = deg < 15.0
    if odd:
        return LEO if first_half else CANCER
    else:
        return CANCER if first_half else LEO


def drekkana(sid_lon: float) -> int:
    """D3 (Drekkana) — siblings, courage. BPHS 6.7.

    Each sign is divided into 3 parts of 10°. First → same sign;
    second → 5th from sign; third → 9th from sign.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    third = int(deg // 10.0)  # 0, 1, 2
    return (sign + third * 4) % 12


def chaturthamsa(sid_lon: float) -> int:
    """D4 (Chaturthamsa) — fortune, property. BPHS 6.8.

    Each sign divided into 4 parts of 7°30'. Counts start from the sign
    itself, then 4th, 7th, 10th house from it (kendras of natal sign).
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    quarter = int(deg // 7.5)  # 0..3
    return (sign + quarter * 3) % 12


def saptamsa(sid_lon: float) -> int:
    """D7 (Saptamsa) — children. BPHS 6.10.

    Each sign divided into 7 parts of 4°17'8.57". In odd signs, counts
    forward from the sign; in even signs, from the 7th sign.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = int(deg // (30.0 / 7.0))  # 0..6
    odd = sign % 2 == 0
    start = sign if odd else (sign + 6) % 12
    return (start + seg) % 12


def navamsa(sid_lon: float) -> int:
    """D9 (Navamsa) — spouse, dharma. BPHS 6.11-15.

    Each sign divided into 9 parts of 3°20'. The first navamsa of:
    - Movable signs (Aries, Cancer, Libra, Capricorn) → same sign
    - Fixed signs (Taurus, Leo, Scorpio, Aquarius) → 9th sign
    - Dual signs (Gemini, Virgo, Sagittarius, Pisces) → 5th sign
    Subsequent navamsas count forward.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = int(deg // (30.0 / 9.0))  # 0..8
    mod3 = sign % 3
    if mod3 == 0:        # Movable: Aries(0), Cancer(3), Libra(6), Capricorn(9)
        start = sign
    elif mod3 == 1:      # Fixed: Taurus(1), Leo(4), Scorpio(7), Aquarius(10)
        start = (sign + 8) % 12
    else:                # Dual: Gemini(2), Virgo(5), Sagittarius(8), Pisces(11)
        start = (sign + 4) % 12
    return (start + seg) % 12


def dasamsa(sid_lon: float) -> int:
    """D10 (Dasamsa) — career, social status. BPHS 6.16.

    Each sign divided into 10 parts of 3°. In odd signs counts forward
    from the sign; in even signs from the 9th sign.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = int(deg // 3.0)  # 0..9
    odd = sign % 2 == 0
    start = sign if odd else (sign + 8) % 12
    return (start + seg) % 12


def dvadasamsa(sid_lon: float) -> int:
    """D12 (Dvadasamsa) — parents, ancestors. BPHS 6.17.

    Each sign divided into 12 parts of 2°30'. Counts forward from the sign.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = int(deg // 2.5)  # 0..11
    return (sign + seg) % 12


def shodasamsa(sid_lon: float) -> int:
    """D16 (Shodasamsa) — vehicles, comforts. BPHS 6.18.

    Each sign divided into 16 parts of 1°52'30". In movable signs counts
    from Aries; in fixed from Leo; in dual from Sagittarius.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = int(deg // (30.0 / 16.0))  # 0..15
    mod3 = sign % 3
    if mod3 == 0:   start = ARIES
    elif mod3 == 1: start = LEO
    else:           start = SAGITTARIUS
    return (start + seg) % 12


def vimsamsa(sid_lon: float) -> int:
    """D20 (Vimsamsa) — spiritual practice. BPHS 6.19.

    Each sign divided into 20 parts of 1°30'. Movable: from Aries;
    Fixed: from Sagittarius; Dual: from Leo.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = int(deg // 1.5)  # 0..19
    mod3 = sign % 3
    if mod3 == 0:   start = ARIES
    elif mod3 == 1: start = SAGITTARIUS
    else:           start = LEO
    return (start + seg) % 12


def chaturvimsamsa(sid_lon: float) -> int:
    """D24 (Chaturvimsamsa) — education, learning. BPHS 6.20.

    Each sign divided into 24 parts of 1°15'. Odd signs from Leo;
    even from Cancer.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = int(deg // 1.25)  # 0..23
    odd = sign % 2 == 0
    start = LEO if odd else CANCER
    return (start + seg) % 12


def bhamsa(sid_lon: float) -> int:
    """D27 (Bhamsa / Saptavimsamsa) — strengths, weaknesses. BPHS 6.21.

    Each sign divided into 27 parts of 1°6'40". Fire signs from Aries;
    Earth from Cancer; Air from Libra; Water from Capricorn.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = int(deg // (30.0 / 27.0))  # 0..26
    mod4 = sign % 4
    starts = [ARIES, CANCER, LIBRA, CAPRICORN]
    return (starts[mod4] + seg) % 12


def trimsamsa(sid_lon: float) -> int:
    """D30 (Trimsamsa) — misfortunes, illness. BPHS 6.29-32.

    Unequal segments by sign parity:
    - Odd signs: 5° Mars, 5° Saturn, 8° Jupiter, 7° Mercury, 5° Venus
                 → Aries, Aquarius, Sagittarius, Gemini, Libra
    - Even signs: 5° Venus, 7° Mercury, 8° Jupiter, 5° Saturn, 5° Mars
                  → Taurus, Virgo, Pisces, Capricorn, Scorpio
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    odd = sign % 2 == 0
    if odd:
        cuts = [5.0, 10.0, 18.0, 25.0, 30.0]
        signs = [ARIES, AQUARIUS, SAGITTARIUS, GEMINI, LIBRA]
    else:
        cuts = [5.0, 12.0, 20.0, 25.0, 30.0]
        signs = [TAURUS, VIRGO, PISCES, CAPRICORN, SCORPIO]
    for i, c in enumerate(cuts):
        if deg < c:
            return signs[i]
    return signs[-1]  # exact 30° boundary case


def khavedamsa(sid_lon: float) -> int:
    """D40 (Khavedamsa) — maternal lineage. BPHS 6.22.

    Each sign divided into 40 parts of 45'. Odd signs from Aries;
    even from Libra.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = int(deg // 0.75)  # 0..39
    odd = sign % 2 == 0
    start = ARIES if odd else LIBRA
    return (start + seg) % 12


def akshavedamsa(sid_lon: float) -> int:
    """D45 (Akshavedamsa) — paternal lineage. BPHS 6.23.

    Each sign divided into 45 parts of 40'. Movable signs from Aries;
    fixed from Leo; dual from Sagittarius.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = int(deg // (30.0 / 45.0))  # 0..44
    mod3 = sign % 3
    if mod3 == 0:   start = ARIES
    elif mod3 == 1: start = LEO
    else:           start = SAGITTARIUS
    return (start + seg) % 12


def shastiamsa(sid_lon: float) -> int:
    """D60 (Shastiamsa) — overall karma, finest division. BPHS 6.24-28.

    Each sign divided into 60 parts of 30'. In odd signs counts forward
    from the sign; in even from the 12th from the sign (i.e. one back).
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = int(deg // 0.5)  # 0..59
    odd = sign % 2 == 0
    start = sign if odd else (sign + 11) % 12
    # Wraps multiple times — count seg signs forward from start.
    return (start + seg) % 12


# Names map for `all_vargas`
_VARGA_FUNCTIONS = {
    "D1": rasi,
    "D2": hora,
    "D3": drekkana,
    "D4": chaturthamsa,
    "D7": saptamsa,
    "D9": navamsa,
    "D10": dasamsa,
    "D12": dvadasamsa,
    "D16": shodasamsa,
    "D20": vimsamsa,
    "D24": chaturvimsamsa,
    "D27": bhamsa,
    "D30": trimsamsa,
    "D40": khavedamsa,
    "D45": akshavedamsa,
    "D60": shastiamsa,
}

VARGA_NAMES = list(_VARGA_FUNCTIONS.keys())


def all_vargas(chart, ayanamsa: str = const.AYANAMSA_LAHIRI) -> dict[str, dict[str, int]]:
    """Return {varga_name: {planet_id: sign_idx}} for the full Shodashavarga.

    Handles both tropical and sidereal charts — if `chart.zodiac` is
    tropical, applies the supplied ayanamsa before computing each varga.
    """
    # Resolve sidereal longitudes for all planets in the chart once
    if chart.zodiac == const.ZODIAC_SIDEREAL:
        sid_lons = {obj.id: obj.lon for obj in chart.objects}
    else:
        sid_lons = {
            obj.id: _ay.to_sidereal(obj.lon, chart.date, ayanamsa=ayanamsa)
            for obj in chart.objects
        }
    result = {}
    for varga_name, fn in _VARGA_FUNCTIONS.items():
        result[varga_name] = {
            planet_id: fn(lon) for planet_id, lon in sid_lons.items()
        }
    return result
```

### Part 2: Tests

Add `tests/test_vedic_divisional.py`. The crucial part is the reference values — encode published BPHS examples or values cross-checked against a known Vedic chart calculator.

```python
"""Tests for Vedic divisional charts — Task 019."""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import divisional as div


class SignIndexHelperTests(unittest.TestCase):

    def test_aries_zero_to_30(self):
        for lon in [0.0, 15.0, 29.99]:
            self.assertEqual(div._sign_index(lon), div.ARIES)

    def test_taurus_30_to_60(self):
        for lon in [30.0, 45.0, 59.99]:
            self.assertEqual(div._sign_index(lon), div.TAURUS)

    def test_pisces_wraps(self):
        self.assertEqual(div._sign_index(359.99), div.PISCES)
        self.assertEqual(div._sign_index(360.0), div.ARIES)


class HoraTests(unittest.TestCase):
    """D2 — odd signs split Leo/Cancer; even signs split Cancer/Leo."""

    def test_aries_first_half_is_leo(self):
        self.assertEqual(div.hora(7.0), div.LEO)

    def test_aries_second_half_is_cancer(self):
        self.assertEqual(div.hora(22.0), div.CANCER)

    def test_taurus_first_half_is_cancer(self):
        self.assertEqual(div.hora(37.0), div.CANCER)

    def test_taurus_second_half_is_leo(self):
        self.assertEqual(div.hora(52.0), div.LEO)


class DrekkanaTests(unittest.TestCase):
    """D3 — first 10° same sign, second 10° 5th sign, third 10° 9th sign."""

    def test_aries_first_drekkana(self):
        self.assertEqual(div.drekkana(5.0), div.ARIES)

    def test_aries_second_drekkana_is_leo(self):
        # 5th from Aries = Leo
        self.assertEqual(div.drekkana(15.0), div.LEO)

    def test_aries_third_drekkana_is_sagittarius(self):
        # 9th from Aries = Sagittarius
        self.assertEqual(div.drekkana(25.0), div.SAGITTARIUS)


class NavamsaTests(unittest.TestCase):
    """D9 — the most-used varga. Verify at every navamsa cusp of Aries."""

    def test_aries_navamsa_progression(self):
        # Aries is movable; D9 starts from Aries and counts forward by 1.
        cases = [
            (0.5, div.ARIES),       # navamsa 1
            (3.5, div.TAURUS),      # navamsa 2
            (6.7, div.GEMINI),      # navamsa 3
            (10.0, div.CANCER),     # navamsa 4
            (13.5, div.LEO),        # navamsa 5
            (16.7, div.VIRGO),      # navamsa 6
            (20.0, div.LIBRA),      # navamsa 7
            (23.5, div.SCORPIO),    # navamsa 8
            (27.0, div.SAGITTARIUS),# navamsa 9
        ]
        for lon, expected in cases:
            self.assertEqual(div.navamsa(lon), expected, f"lon={lon}")

    def test_taurus_navamsa_starts_from_capricorn(self):
        # Taurus is fixed; D9 starts from the 9th sign (Capricorn) and counts forward.
        self.assertEqual(div.navamsa(30.5), div.CAPRICORN)

    def test_gemini_navamsa_starts_from_libra(self):
        # Gemini is dual; D9 starts from the 5th sign (Libra) and counts forward.
        self.assertEqual(div.navamsa(60.5), div.LIBRA)


class TrimsamsaTests(unittest.TestCase):
    """D30 — the unequal-segment varga. Verify both parities."""

    def test_aries_odd_segments(self):
        # Odd sign: Mars(0-5), Saturn(5-10), Jupiter(10-18), Mercury(18-25), Venus(25-30)
        self.assertEqual(div.trimsamsa(2.5), div.ARIES)         # Mars
        self.assertEqual(div.trimsamsa(7.5), div.AQUARIUS)      # Saturn
        self.assertEqual(div.trimsamsa(14.0), div.SAGITTARIUS)  # Jupiter
        self.assertEqual(div.trimsamsa(22.0), div.GEMINI)       # Mercury
        self.assertEqual(div.trimsamsa(27.0), div.LIBRA)        # Venus

    def test_taurus_even_segments(self):
        # Even sign: Venus(0-5), Mercury(5-12), Jupiter(12-20), Saturn(20-25), Mars(25-30)
        self.assertEqual(div.trimsamsa(32.5), div.TAURUS)       # Venus
        self.assertEqual(div.trimsamsa(38.0), div.VIRGO)        # Mercury
        self.assertEqual(div.trimsamsa(45.0), div.PISCES)       # Jupiter
        self.assertEqual(div.trimsamsa(52.0), div.CAPRICORN)    # Saturn
        self.assertEqual(div.trimsamsa(57.0), div.SCORPIO)      # Mars


class AllVargasTests(unittest.TestCase):
    """End-to-end with a real chart — verifies the chart wiring."""

    def test_all_vargas_returns_all_16(self):
        date = Datetime("1947/08/15", "00:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        result = div.all_vargas(chart)
        self.assertEqual(set(result.keys()), set(div.VARGA_NAMES))

    def test_d1_matches_chart_sign(self):
        date = Datetime("2024/06/15", "12:00", "+00:00")
        pos = GeoPos("28n36", "77e12")
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        result = div.all_vargas(chart)
        # D1 of Sun should be the sign of Sun's sidereal longitude.
        sun_sign = int(chart.get(const.SUN).lon // 30) % 12
        self.assertEqual(result["D1"][const.SUN], sun_sign)

    def test_tropical_and_sidereal_chart_agree(self):
        """all_vargas(tropical, ayanamsa=lahiri) should equal
        all_vargas(sidereal). This validates the ayanamsa branching."""
        date = Datetime("2024/06/15", "12:00", "+00:00")
        pos = GeoPos("28n36", "77e12")
        tropical = Chart(date, pos)
        sidereal = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        r1 = div.all_vargas(tropical)
        r2 = div.all_vargas(sidereal)
        for varga in div.VARGA_NAMES:
            for planet in r1[varga]:
                self.assertEqual(
                    r1[varga][planet], r2[varga][planet],
                    f"{varga} disagreement for {planet}",
                )
```

### Part 3: Update CHANGELOG.md

```markdown
### Added (Task 019 — Vedic divisional charts)
- `mayaastrolib/vedic/divisional.py` — full Shodashavarga (16 vargas):
  D1, D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60.
- Each varga is a pure function on sidereal longitude.
- `all_vargas(chart, ayanamsa=...)` — chart-level entry point that
  handles tropical-or-sidereal input and returns a nested dict.
- BPHS canonical schemes for D9 and D10; D30 implements the unequal
  segment scheme per BPHS 6.29-32.
```

## Out of scope

- Alternative D9 schemes (Raman, KP) — flag in docstrings; not implemented
- Drekkana variants (Parashara vs Jagannath vs Somanath) — BPHS canonical only
- Higher vargas (D72, D108, D144) — not in the Shodashavarga; out of scope
- Bhavachalit / cuspal interpolation — separate concern
- Varga visualization / chart drawing — never in scope for the library
- Type hints — Phase 1 follow-up

## Process

1. Branch:

   ```
   git checkout development
   git pull origin development
   git checkout -b task-019-vedic-divisional
   ```

2. Suggested commits:
   - `feat: add vedic.divisional with 16 Shodashavarga functions`
   - `feat: add all_vargas chart-level convenience`
   - `test: cover hora, drekkana, navamsa, trimsamsa, and chart wiring`
   - `docs: update CHANGELOG and PROJECT-LOG for Task 019`

3. Pre-completion checklist:
   - `ruff format --check .` passes
   - `ruff check .` passes
   - `mypy mayaastrolib/` — no new errors
   - `pytest -x` passes
   - Each of D2/D3/D9/D30 has at least one boundary test that fails if the formula is off-by-one

4. PROJECT-LOG.md entry must include:
   - The chosen D9 scheme (BPHS canonical) and a note that Raman / KP alternates are deferred
   - The Trimsamsa cuts verified against BPHS 6.29-32 verbatim
   - A spot check: for a real Vedic chart (e.g. 1947-08-15 Delhi midnight Moon), all 15 vargas of the Moon, cross-checked against a published Vedic chart calculator if available

5. Push, verify CI green, DO NOT merge.

## Definition of done

- All 16 varga functions exist with the signatures shown
- `all_vargas` returns 16 entries
- Boundary tests pass for D2, D3, D9, D30 at minimum
- Tropical-input and sidereal-input produce identical varga assignments
- CHANGELOG + PROJECT-LOG entries
- CI green

## If something goes wrong

**Most likely: D9 or D30 off-by-one.** These are the two most-published vargas; their boundaries are pinned in countless reference texts. If your D9 doesn't say "Aries 0°-3°20' → Aries", "Aries 3°20'-6°40' → Taurus" you have a bug. The test `test_aries_navamsa_progression` will catch it.

**Second: D30 parity inverted.** "Odd signs" in BPHS means Aries=1st, so Aries (sign_index=0) is odd. Don't flip the parity check.

**Third: `chart.objects` doesn't return what you expect.** Inspect the actual attribute name — it might be `chart.objects.content`, or via iteration `for obj in chart`. Adapt; don't add a new property.

**Fourth: a varga test passes for sidereal-chart input but fails for tropical-chart input.** Means the ayanamsa branching in `all_vargas` is wrong. The tropical longitude minus ayanamsa should equal the sidereal longitude.

If something fundamental breaks:

1. `git reset --hard development`
2. Failure report in PROJECT-LOG.md
3. Commit on `task-019-failed-attempt-1`
4. Push and stop

Largest task in the chain by code volume; smallest by architectural risk. The functions are independent — if one is wrong, only its tests fail. Get them committed one at a time if the diff feels unwieldy.

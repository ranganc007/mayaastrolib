# Task 020: Vimshottari Dasha

## Context

You are working in the `mayaastrolib` repository. Before doing anything:

1. Read `CLAUDE.md` in full.
2. Read `docs/2026-05-11-vedic-extension-spec.md` — particularly the `vedic/dasha.py` section.
3. Read `prompts/task-017-vedic-foundation.md`, `prompts/task-018-vedic-nakshatras.md`, `prompts/task-019-vedic-divisional.md` — confirm all have shipped.
4. Confirm Tasks 017 + 018 + 019 have merged to `development`. If not, STOP.
5. Read `mayaastrolib/vedic/nakshatras.py` (Task 018) — this module's `Nakshatra`, `NAKSHATRA_LORDS`, and `janma_nakshatra` are the primitives Vimshottari builds on.
6. Read `mayaastrolib/datetime.py` — understand the `Datetime` constructor, `from_pydatetime`, `to_pydatetime`. Vimshottari arithmetic adds years/days to dates; we'll lean on `to_pydatetime` for that.
7. Read `mayaastrolib/predictives/` — note the existing pattern for predictive computations (`solarReturn`, `profections`, `primarydirections`). The Vimshottari dasha is morally a predictive but its API shape is dictated by Vedic convention, not Western. We're putting it in `vedic/` per the spec.
8. Confirm `pytest tests/` passes — expected ~270 tests after Tasks 017 + 018 + 019.

## Why this task exists

Vimshottari Mahadasha is the single most-used Vedic predictive technique. Every Vedic chart reading starts with "what dasha period is the native in?" — and the answer drives the rest of the interpretation. Without it, Vedic charts are inert.

This task ships the foundational MD + AD + Pratyantar levels (Mahadasha = major period, Antardasha = sub-period, Pratyantardasha = sub-sub-period). Sookshma and Prana (4th and 5th levels) are deferred — most consumers stop at Pratyantar.

## Design decisions (already made — do not relitigate)

- **120-year canonical cycle.** Vimshottari = 120 years total, distributed across the 9 nakshatra lords in fixed proportions:
  - Ketu: 7, Venus: 20, Sun: 6, Moon: 10, Mars: 7, Rahu: 18, Jupiter: 16, Saturn: 19, Mercury: 17.
  - These sum to 120. No alternates.
- **Birth balance** = the remaining portion of the dasha of the natal nakshatra's lord, proportional to how far the Moon is *into* the nakshatra.
- **All periods are nested in the same 9-lord order**: Ketu → Venus → Sun → Moon → Mars → Rahu → Jupiter → Saturn → Mercury → Ketu (wraps). Inside a Mahadasha of (e.g.) Venus, the Antardashas are Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury, Ketu (starting with the MD lord itself). Inside an Antardasha of (e.g.) Sun within Venus, the Pratyantars are Sun, Moon, ..., Venus (starting with the AD lord).
- **Period durations are products of proportions.** AD of lord X within MD of lord Y has duration `(years[X] / 120) * years[Y]`. Pratyantar similarly nested.
- **Year-as-time = 365.25 days.** Vimshottari traditional duration uses a tropical-year approximation. This matches BPHS and Phaladeepika canonical practice.
- **`vimshottari(chart, target=None, ayanamsa="lahiri")` is the main entry point.** With `target=None`, returns the full 120-year MD sequence anchored at the natal date. With `target=<Datetime>`, additionally fills in `current_md` and `current_ad` for the active periods at that target.
- **`Datetime` is the date type throughout.** Use existing `Datetime.to_pydatetime()` / `Datetime.from_pydatetime()` for arithmetic (delegate `timedelta` math to stdlib).

## Task scope

### Part 1: Module skeleton

Create `mayaastrolib/vedic/dasha.py`:

```python
"""Vimshottari Mahadasha — the 120-year nakshatra-based predictive cycle.

Vimshottari (lit. "120-yearly") assigns to each of 9 planetary lords a
fixed proportion of a 120-year life cycle, ordered by the Vimshottari
nakshatra lord sequence. Each Mahadasha is further subdivided into 9
Antardashas in the same order (starting with the MD lord itself), and
each Antardasha into 9 Pratyantardashas similarly.

References:
- BPHS ch. 46-51 (Vimshottari structure and rules)
- Phaladeepika ch. 19 (Antardasha effects, used downstream not here)
- Muhurta Chintamani for the 365.25-day year convention
"""

from __future__ import annotations

import datetime as _stdlib_dt
from dataclasses import dataclass

from mayaastrolib import const
from mayaastrolib.datetime import Datetime
from mayaastrolib.vedic import nakshatras as _nak

# Vimshottari ordering — must match nakshatras._VIMSHOTTARI_CYCLE
VIMSHOTTARI_ORDER = [
    const.KETU, const.VENUS, const.SUN, const.MOON, const.MARS,
    const.RAHU, const.JUPITER, const.SATURN, const.MERCURY,
]

VIMSHOTTARI_YEARS = {
    const.KETU: 7,
    const.VENUS: 20,
    const.SUN: 6,
    const.MOON: 10,
    const.MARS: 7,
    const.RAHU: 18,
    const.JUPITER: 16,
    const.SATURN: 19,
    const.MERCURY: 17,
}

VIMSHOTTARI_TOTAL_YEARS = 120
assert sum(VIMSHOTTARI_YEARS.values()) == VIMSHOTTARI_TOTAL_YEARS

# Traditional 365.25-day year.
DAYS_PER_VIMSHOTTARI_YEAR = 365.25


@dataclass(frozen=True)
class DashaPeriod:
    """One Mahadasha, Antardasha, or Pratyantardasha period.

    Attributes:
        lord: The ruling planet ID (const.KETU, const.VENUS, ...).
        start: Period start as a `Datetime`.
        end: Period end as a `Datetime`.
        level: 1=MD, 2=AD, 3=Pratyantar.
    """
    lord: str
    start: Datetime
    end: Datetime
    level: int


@dataclass(frozen=True)
class VimshottariResult:
    """The full result of a Vimshottari computation.

    Attributes:
        janma_nakshatra: The natal Moon's nakshatra.
        birth_balance_lord: The lord of the natal nakshatra (= MD-at-birth).
        birth_balance_years: Years remaining in the MD-at-birth at the
            moment of birth.
        sequence: The full 120-year MD sequence, in chronological order.
        current_md: The MD active at `target` (None if target not given).
        current_ad: The AD active at `target` (None if target not given).
        current_pratyantar: The Pratyantar active at `target` (None if
            target not given).
    """
    janma_nakshatra: _nak.Nakshatra
    birth_balance_lord: str
    birth_balance_years: float
    sequence: list[DashaPeriod]
    current_md: DashaPeriod | None = None
    current_ad: DashaPeriod | None = None
    current_pratyantar: DashaPeriod | None = None


def _add_days(dt: Datetime, days: float) -> Datetime:
    """Return `dt` shifted by `days` calendar days."""
    pydt = dt.to_pydatetime()
    shifted = pydt + _stdlib_dt.timedelta(days=days)
    return Datetime.from_pydatetime(shifted)


def _years_to_days(years: float) -> float:
    return years * DAYS_PER_VIMSHOTTARI_YEAR


def _next_lord(lord: str) -> str:
    idx = VIMSHOTTARI_ORDER.index(lord)
    return VIMSHOTTARI_ORDER[(idx + 1) % 9]


def _birth_balance(natal_nak: _nak.Nakshatra, natal_moon_lon: float) -> tuple[str, float]:
    """Return (lord, years_remaining) for the dasha-at-birth.

    The Moon at the start of the natal nakshatra (e.g. exactly 0° Ashwini)
    has the full Ketu MD ahead of it; deeper into the nakshatra means less
    remaining.
    """
    nak_start_lon = natal_nak.index * _nak.NAKSHATRA_SPAN_DEG
    deg_into_nak = (natal_moon_lon % 360.0) - nak_start_lon
    fraction_elapsed = deg_into_nak / _nak.NAKSHATRA_SPAN_DEG
    lord = natal_nak.lord
    full_years = VIMSHOTTARI_YEARS[lord]
    remaining_years = full_years * (1.0 - fraction_elapsed)
    return lord, remaining_years


def antardashas(md: DashaPeriod) -> list[DashaPeriod]:
    """The 9 Antardashas within a Mahadasha.

    Starts with the MD lord itself, then proceeds through the Vimshottari
    cycle. Duration of each AD = (lord_years / 120) * md_years.
    """
    md_duration_days = (md.end.to_pydatetime() - md.start.to_pydatetime()).total_seconds() / 86400.0
    md_years = md_duration_days / DAYS_PER_VIMSHOTTARI_YEAR
    result = []
    current_start = md.start
    md_idx = VIMSHOTTARI_ORDER.index(md.lord)
    for i in range(9):
        ad_lord = VIMSHOTTARI_ORDER[(md_idx + i) % 9]
        ad_years = (VIMSHOTTARI_YEARS[ad_lord] / 120.0) * md_years
        ad_days = ad_years * DAYS_PER_VIMSHOTTARI_YEAR
        ad_end = _add_days(current_start, ad_days)
        result.append(DashaPeriod(lord=ad_lord, start=current_start, end=ad_end, level=2))
        current_start = ad_end
    return result


def pratyantar_dashas(ad: DashaPeriod) -> list[DashaPeriod]:
    """The 9 Pratyantardashas within an Antardasha. Same nesting rule."""
    ad_duration_days = (ad.end.to_pydatetime() - ad.start.to_pydatetime()).total_seconds() / 86400.0
    ad_years = ad_duration_days / DAYS_PER_VIMSHOTTARI_YEAR
    result = []
    current_start = ad.start
    ad_idx = VIMSHOTTARI_ORDER.index(ad.lord)
    for i in range(9):
        pr_lord = VIMSHOTTARI_ORDER[(ad_idx + i) % 9]
        pr_years = (VIMSHOTTARI_YEARS[pr_lord] / 120.0) * ad_years
        pr_days = pr_years * DAYS_PER_VIMSHOTTARI_YEAR
        pr_end = _add_days(current_start, pr_days)
        result.append(DashaPeriod(lord=pr_lord, start=current_start, end=pr_end, level=3))
        current_start = pr_end
    return result


def _build_md_sequence(birth: Datetime, balance_lord: str, balance_years: float) -> list[DashaPeriod]:
    """Build the full 120-year MD sequence anchored at the natal date.

    The first MD is the dasha-at-birth's remaining portion (started before
    birth, ending balance_years later). Each subsequent MD is the full
    duration of the next lord in the cycle.
    """
    sequence = []
    # First MD — partial, ending balance_years after birth.
    first_end = _add_days(birth, _years_to_days(balance_years))
    first_start = _add_days(first_end, -_years_to_days(VIMSHOTTARI_YEARS[balance_lord]))
    sequence.append(DashaPeriod(lord=balance_lord, start=first_start, end=first_end, level=1))

    # Subsequent MDs — each lord's full duration.
    current_start = first_end
    current_lord = _next_lord(balance_lord)
    while current_start.to_pydatetime() < (
        birth.to_pydatetime() + _stdlib_dt.timedelta(days=_years_to_days(120))
    ):
        full_days = _years_to_days(VIMSHOTTARI_YEARS[current_lord])
        end = _add_days(current_start, full_days)
        sequence.append(DashaPeriod(lord=current_lord, start=current_start, end=end, level=1))
        current_start = end
        current_lord = _next_lord(current_lord)
    return sequence


def _find_active(periods: list[DashaPeriod], target: Datetime) -> DashaPeriod | None:
    """Return the period containing `target`, or None if outside the range."""
    t = target.to_pydatetime()
    for p in periods:
        if p.start.to_pydatetime() <= t < p.end.to_pydatetime():
            return p
    return None


def vimshottari(chart, target: Datetime | None = None, ayanamsa: str = const.AYANAMSA_LAHIRI) -> VimshottariResult:
    """Compute the Vimshottari Mahadasha for a chart.

    Args:
        chart: The natal `Chart`.
        target: If given, returns the MD/AD/Pratyantar active at this
            target moment. If None, only the full MD sequence is computed.
        ayanamsa: Used only if `chart.zodiac == ZODIAC_TROPICAL`.

    Returns:
        A `VimshottariResult` containing the natal nakshatra, the
        dasha-at-birth balance, the full 120-year MD sequence, and
        (if target given) the MD/AD/Pratyantar active at the target.
    """
    natal_nak = _nak.janma_nakshatra(chart, ayanamsa=ayanamsa)
    moon = chart.get(const.MOON)
    if chart.zodiac == const.ZODIAC_SIDEREAL:
        moon_lon = moon.lon
    else:
        from mayaastrolib.vedic.ayanamsa import to_sidereal
        moon_lon = to_sidereal(moon.lon, chart.date, ayanamsa=ayanamsa)
    balance_lord, balance_years = _birth_balance(natal_nak, moon_lon)

    sequence = _build_md_sequence(chart.date, balance_lord, balance_years)

    current_md = current_ad = current_pratyantar = None
    if target is not None:
        current_md = _find_active(sequence, target)
        if current_md is not None:
            ads = antardashas(current_md)
            current_ad = _find_active(ads, target)
            if current_ad is not None:
                prs = pratyantar_dashas(current_ad)
                current_pratyantar = _find_active(prs, target)

    return VimshottariResult(
        janma_nakshatra=natal_nak,
        birth_balance_lord=balance_lord,
        birth_balance_years=balance_years,
        sequence=sequence,
        current_md=current_md,
        current_ad=current_ad,
        current_pratyantar=current_pratyantar,
    )
```

### Part 2: Tests

Add `tests/test_vedic_dasha.py`:

```python
"""Tests for Vimshottari dasha — Task 020."""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import dasha
from mayaastrolib.vedic import nakshatras as nak


class BirthBalanceTests(unittest.TestCase):

    def test_moon_at_start_of_nakshatra_has_full_remaining(self):
        # Ashwini starts at 0°; Moon at 0° has the full Ketu MD ahead.
        ashwini = nak.of_longitude(0.0)
        lord, remaining = dasha._birth_balance(ashwini, 0.0)
        self.assertEqual(lord, const.KETU)
        self.assertAlmostEqual(remaining, 7.0, places=4)

    def test_moon_at_end_of_nakshatra_has_zero_remaining(self):
        # End of Ashwini = 13°20'.
        ashwini = nak.of_longitude(0.0)
        _, remaining = dasha._birth_balance(ashwini, 13.0 + 20.0 / 60.0)
        self.assertAlmostEqual(remaining, 0.0, places=2)

    def test_moon_at_midpoint_has_half_remaining(self):
        ashwini = nak.of_longitude(0.0)
        _, remaining = dasha._birth_balance(ashwini, (13.0 + 20.0/60.0) / 2.0)
        self.assertAlmostEqual(remaining, 3.5, places=2)


class VimshottariStructureTests(unittest.TestCase):

    def setUp(self):
        self.date = Datetime("1980/01/01", "12:00", "+05:30")
        self.pos = GeoPos("28n36", "77e12")
        self.chart = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)

    def test_sequence_length_covers_120_years(self):
        result = dasha.vimshottari(self.chart)
        first_start = result.sequence[0].start.to_pydatetime()
        last_end = result.sequence[-1].end.to_pydatetime()
        total_days = (last_end - first_start).total_seconds() / 86400.0
        # Should cover at least 120 years, may slightly exceed due to wrapping.
        self.assertGreaterEqual(total_days, 120 * 365.25 - 1)

    def test_md_sequence_follows_vimshottari_order(self):
        result = dasha.vimshottari(self.chart)
        # Starting from the birth-balance lord, each subsequent MD is the
        # next lord in the cycle.
        for i in range(len(result.sequence) - 1):
            lord_i = result.sequence[i].lord
            lord_next = result.sequence[i + 1].lord
            expected_next = dasha._next_lord(lord_i)
            self.assertEqual(lord_next, expected_next, f"MD {i} → {i+1} broken")

    def test_md_durations_match_table(self):
        result = dasha.vimshottari(self.chart)
        # Skip the first (partial) and last (may be truncated) — middle MDs
        # should each be the full duration of their lord.
        for md in result.sequence[1:-1]:
            actual_days = (md.end.to_pydatetime() - md.start.to_pydatetime()).total_seconds() / 86400.0
            expected_days = dasha.VIMSHOTTARI_YEARS[md.lord] * dasha.DAYS_PER_VIMSHOTTARI_YEAR
            self.assertAlmostEqual(actual_days, expected_days, delta=1.0)


class AntardashaTests(unittest.TestCase):

    def setUp(self):
        # Build a 20-year Venus MD starting at a known date for testing.
        start = Datetime("2000/01/01", "00:00", "+00:00")
        end_pydt = start.to_pydatetime() + __import__("datetime").timedelta(
            days=20 * dasha.DAYS_PER_VIMSHOTTARI_YEAR
        )
        end = Datetime.from_pydatetime(end_pydt)
        self.venus_md = dasha.DashaPeriod(
            lord=const.VENUS, start=start, end=end, level=1,
        )

    def test_nine_antardashas(self):
        ads = dasha.antardashas(self.venus_md)
        self.assertEqual(len(ads), 9)

    def test_first_antardasha_is_md_lord(self):
        ads = dasha.antardashas(self.venus_md)
        self.assertEqual(ads[0].lord, const.VENUS)

    def test_antardasha_sequence(self):
        ads = dasha.antardashas(self.venus_md)
        expected_order = [
            const.VENUS, const.SUN, const.MOON, const.MARS, const.RAHU,
            const.JUPITER, const.SATURN, const.MERCURY, const.KETU,
        ]
        self.assertEqual([a.lord for a in ads], expected_order)

    def test_antardasha_durations_sum_to_md(self):
        ads = dasha.antardashas(self.venus_md)
        md_days = (self.venus_md.end.to_pydatetime() - self.venus_md.start.to_pydatetime()).total_seconds() / 86400.0
        ad_days_total = sum(
            (a.end.to_pydatetime() - a.start.to_pydatetime()).total_seconds() / 86400.0
            for a in ads
        )
        self.assertAlmostEqual(ad_days_total, md_days, delta=0.01)

    def test_venus_ad_within_venus_md_is_20_over_120_of_total(self):
        ads = dasha.antardashas(self.venus_md)
        venus_ad = ads[0]
        ad_days = (venus_ad.end.to_pydatetime() - venus_ad.start.to_pydatetime()).total_seconds() / 86400.0
        expected_days = (20.0 / 120.0) * 20.0 * dasha.DAYS_PER_VIMSHOTTARI_YEAR
        self.assertAlmostEqual(ad_days, expected_days, delta=0.01)


class CurrentPeriodTests(unittest.TestCase):
    """Verify the active-period lookup against published references."""

    def test_current_md_for_known_chart(self):
        """For a chart with a well-known natal nakshatra, verify the active
        MD at a specific date matches the published Vimshottari calculation."""
        # Reference: published natal chart of an arbitrary public figure
        # whose Vimshottari is widely calculated (e.g. a chart used in
        # parity tests in the MayaAstro sibling repo).
        # Replace with a chart whose canonical Vimshottari you can cite.
        date = Datetime("1947/08/15", "00:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        target = Datetime("2024/06/01", "12:00", "+00:00")
        result = dasha.vimshottari(chart, target=target)
        self.assertIsNotNone(result.current_md)
        self.assertIsNotNone(result.current_ad)
        self.assertIsNotNone(result.current_pratyantar)
        # The MD lord at 2024-06-01 for this natal chart can be cross-checked
        # against any Vimshottari calculator. Fill in the expected lord here
        # after running once to bootstrap; on re-runs this becomes a regression.
        # self.assertEqual(result.current_md.lord, const.<EXPECTED>)


class TargetOutsideSequenceTests(unittest.TestCase):

    def test_target_before_birth_returns_none(self):
        date = Datetime("1980/01/01", "12:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        before = Datetime("1900/01/01", "00:00", "+00:00")
        result = dasha.vimshottari(chart, target=before)
        self.assertIsNone(result.current_md)

    def test_target_after_120_years_returns_none(self):
        date = Datetime("1980/01/01", "12:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        after = Datetime("2200/01/01", "00:00", "+00:00")
        result = dasha.vimshottari(chart, target=after)
        self.assertIsNone(result.current_md)
```

The `test_current_md_for_known_chart` test ships with a commented-out assertion. On first run, capture the actual `current_md.lord` and uncomment the assertion in a follow-up commit. This is the regression-anchor pattern.

### Part 3: Update CHANGELOG.md

```markdown
### Added (Task 020 — Vimshottari Dasha)
- `mayaastrolib/vedic/dasha.py` — Vimshottari Mahadasha computation.
  - `vimshottari(chart, target=None, ayanamsa=...)` — main entry point.
    Returns the full 120-year MD sequence plus, if target given, the
    MD/AD/Pratyantar active at that moment.
  - `antardashas(md)` — the 9 Antardashas within a Mahadasha.
  - `pratyantar_dashas(ad)` — the 9 Pratyantars within an Antardasha.
  - `DashaPeriod` and `VimshottariResult` are frozen dataclasses.
- `VIMSHOTTARI_YEARS` constants (Ketu 7 / Venus 20 / Sun 6 / Moon 10 /
  Mars 7 / Rahu 18 / Jupiter 16 / Saturn 19 / Mercury 17 = 120) exposed
  for downstream use.
```

## Out of scope

- Sookshma (4th level) and Prana (5th level) — defer until requested.
  Same nesting rule; trivial to add but unused by most readers.
- Char Dasha, Yogini Dasha, other dasha systems — separate tasks if requested.
- Dasha interpretation / effects rules — presentational, downstream.
- Year-as-365.2422 days (sidereal year) instead of 365.25 — would be a
  separate task with its own justification.
- Type hints on the public API (Phase 1 follow-up).

## Process

1. Branch:

   ```
   git checkout development
   git pull origin development
   git checkout -b task-020-vedic-dasha
   ```

2. Suggested commits:
   - `feat: add vedic.dasha with Vimshottari MD/AD/Pratyantar`
   - `test: cover birth balance, MD sequence, AD nesting`
   - `docs: update CHANGELOG and PROJECT-LOG for Task 020`

3. Pre-completion checklist:
   - `ruff format --check .` passes
   - `ruff check .` passes
   - `mypy mayaastrolib/` — no new errors
   - `pytest -x` passes
   - Sum of all MD durations is exactly 120 years (within 1 day)
   - Sum of all AD durations within one MD is exactly that MD's duration

4. PROJECT-LOG.md entry must include:
   - The chosen reference chart for `test_current_md_for_known_chart` and the captured `current_md.lord` value (which becomes the regression assertion in a follow-up)
   - Verification that the first MD's `start` precedes `birth.date` (it's the *remaining* portion of a dasha that started before birth) — this is non-obvious and worth flagging in the journal

5. Push, verify CI green, DO NOT merge.

## Definition of done

- `mayaastrolib/vedic/dasha.py` exists with the API above
- Birth balance formula correct (sum-to-full-period when Moon at start of nakshatra; sum-to-zero at end)
- MD sequence covers exactly 120 years from the first MD's start
- AD durations within an MD sum to the MD duration
- Pratyantar durations within an AD sum to the AD duration
- Target-outside-range returns None gracefully
- CHANGELOG entry; PROJECT-LOG entry
- CI green

## If something goes wrong

**Most likely: the birth balance is off because Moon's longitude is being read tropically.** Verify by hand: for a Moon at 5° sidereal Aries (5° into Ashwini = 5/13.333 = 0.375 fraction), the Ketu balance should be 7 × (1 - 0.375) = 4.375 years. If your function returns the right answer for sidereal-chart input but the wrong answer for tropical-chart input, the ayanamsa branching at the top of `vimshottari()` is wrong.

**Second: `Datetime.to_pydatetime()` doesn't accept a chart's stored date directly.** It may need an intermediate step or a different method name (`asdatetime()`, `to_python()`, ...). Inspect `mayaastrolib/datetime.py` first.

**Third: `Datetime.from_pydatetime` doesn't handle timezone-aware vs naive correctly.** If you build a naive `pydatetime + timedelta`, the resulting `Datetime` may have no UTC offset and downstream behaviour will diverge. Round-trip via `to_pydatetime()` to preserve the timezone, do the timedelta, and pass back.

**Fourth: floating-point accumulation drift.** Summing 120 years' worth of AD-day differences via repeated `_add_days(..., float)` accumulates error. The current implementation uses chronological start-to-end-of-period, with each end computed from a fresh `start + duration` — this is robust. Resist the urge to "optimize" by accumulating durations; the small per-period cost is worth the numerical stability.

**Fifth: `chart.date` is the natal date; `vimshottari(chart)` returns a sequence anchored at that date, but the FIRST MD's `start` is before `chart.date`.** This is correct — the first MD is the partial-remaining portion of a dasha that began before birth. A test that asserts `result.sequence[0].start >= chart.date` would be wrong; it should assert `result.sequence[0].end >= chart.date >= result.sequence[0].start`.

If something fundamental breaks:

1. `git reset --hard development`
2. Failure report in PROJECT-LOG.md
3. Commit on `task-020-failed-attempt-1`
4. Push and stop

This is the most complex task in the P0 chain. Birth balance arithmetic, sequence anchoring, and target lookup all interact. If anything feels off, write the failure report — the Vedic predictive interpretation literally hinges on getting this right.

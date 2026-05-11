"""Vimshottari Mahadasha — the 120-year nakshatra-based predictive cycle.

Vimshottari (lit. "120-yearly") assigns to each of 9 planetary lords a
fixed proportion of a 120-year life cycle, ordered by the Vimshottari
nakshatra lord sequence. Each Mahadasha is further subdivided into 9
Antardashas in the same order (starting with the MD lord itself), and
each Antardasha into 9 Pratyantardashas similarly.

References:
- BPHS ch. 46-51 (Vimshottari structure and rules)
- Phaladeepika ch. 19 (Antardasha effects — used downstream, not here)
- Muhurta Chintamani for the 365.25-day year convention
"""

from __future__ import annotations

import datetime as _stdlib_dt
from dataclasses import dataclass, field

from mayaastrolib import const
from mayaastrolib.datetime import Datetime
from mayaastrolib.vedic import nakshatras as _nak

# Vimshottari ordering — must match nakshatras._VIMSHOTTARI_CYCLE.
VIMSHOTTARI_ORDER = [
    const.KETU,
    const.VENUS,
    const.SUN,
    const.MOON,
    const.MARS,
    const.RAHU,
    const.JUPITER,
    const.SATURN,
    const.MERCURY,
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

# Traditional 365.25-day year per BPHS / Muhurta Chintamani convention.
DAYS_PER_VIMSHOTTARI_YEAR = 365.25


@dataclass(frozen=True)
class DashaPeriod:
    """One Mahadasha, Antardasha, or Pratyantardasha period.

    Attributes:
        lord: The ruling planet ID (``const.KETU``, ``const.VENUS``, ...).
        start: Period start as a :class:`Datetime`.
        end: Period end as a :class:`Datetime`.
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
            The first MD's ``start`` precedes ``chart.date`` — it's the
            partial-remaining portion of a dasha that began before birth.
        current_md: The MD active at ``target`` (None if target not given
            or outside the 120-year range).
        current_ad: The AD active at ``target`` (None otherwise).
        current_pratyantar: The Pratyantar active at ``target`` (None
            otherwise).
    """

    janma_nakshatra: _nak.Nakshatra
    birth_balance_lord: str
    birth_balance_years: float
    sequence: list = field(default_factory=list)
    current_md: DashaPeriod | None = None
    current_ad: DashaPeriod | None = None
    current_pratyantar: DashaPeriod | None = None


def _add_days(dt, days):
    """Return ``dt`` shifted by ``days`` calendar days."""
    pydt = dt.to_pydatetime()
    shifted = pydt + _stdlib_dt.timedelta(days=days)
    return Datetime.from_pydatetime(shifted)


def _years_to_days(years):
    return years * DAYS_PER_VIMSHOTTARI_YEAR


def _next_lord(lord):
    idx = VIMSHOTTARI_ORDER.index(lord)
    return VIMSHOTTARI_ORDER[(idx + 1) % 9]


def _birth_balance(natal_nak, natal_moon_lon):
    """Return ``(lord, years_remaining)`` for the dasha-at-birth.

    The Moon at the start of the natal nakshatra (e.g. exactly 0°
    Ashwini) has the full Ketu MD ahead of it; deeper into the
    nakshatra means less remaining.
    """
    nak_start_lon = natal_nak.index * _nak.NAKSHATRA_SPAN_DEG
    deg_into_nak = (natal_moon_lon % 360.0) - nak_start_lon
    fraction_elapsed = deg_into_nak / _nak.NAKSHATRA_SPAN_DEG
    lord = natal_nak.lord
    full_years = VIMSHOTTARI_YEARS[lord]
    remaining_years = full_years * (1.0 - fraction_elapsed)
    return lord, remaining_years


def antardashas(md):
    """The 9 Antardashas within a Mahadasha.

    Starts with the MD lord itself, then proceeds through the Vimshottari
    cycle. Duration of each AD = ``(lord_years / 120) * md_years``.
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


def pratyantar_dashas(ad):
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


def _build_md_sequence(birth, balance_lord, balance_years):
    """Build the full 120-year MD sequence anchored at the natal date.

    The first MD is the dasha-at-birth's remaining portion (started
    before birth, ending ``balance_years`` later). Each subsequent MD is
    the full duration of the next lord in the cycle.
    """
    sequence = []
    # First MD — partial, ending balance_years after birth.
    first_end = _add_days(birth, _years_to_days(balance_years))
    first_start = _add_days(first_end, -_years_to_days(VIMSHOTTARI_YEARS[balance_lord]))
    sequence.append(DashaPeriod(lord=balance_lord, start=first_start, end=first_end, level=1))

    # Subsequent MDs — each lord's full duration.
    current_start = first_end
    current_lord = _next_lord(balance_lord)
    birth_pydt = birth.to_pydatetime()
    cycle_end = birth_pydt + _stdlib_dt.timedelta(days=_years_to_days(120))
    while current_start.to_pydatetime() < cycle_end:
        full_days = _years_to_days(VIMSHOTTARI_YEARS[current_lord])
        end = _add_days(current_start, full_days)
        sequence.append(DashaPeriod(lord=current_lord, start=current_start, end=end, level=1))
        current_start = end
        current_lord = _next_lord(current_lord)
    return sequence


def _find_active(periods, target):
    """Return the period containing ``target``, or None if outside range."""
    t = target.to_pydatetime()
    for p in periods:
        if p.start.to_pydatetime() <= t < p.end.to_pydatetime():
            return p
    return None


def vimshottari(chart, target=None, ayanamsa=const.AYANAMSA_LAHIRI):
    """Compute the Vimshottari Mahadasha for a chart.

    Args:
        chart: The natal :class:`Chart`.
        target: If given, returns the MD/AD/Pratyantar active at this
            target moment. If None, only the full MD sequence is computed.
        ayanamsa: Used only if ``chart.zodiac == ZODIAC_TROPICAL``.

    Returns:
        A :class:`VimshottariResult` containing the natal nakshatra, the
        dasha-at-birth balance, the full 120-year MD sequence, and
        (if target given) the MD/AD/Pratyantar active at the target.
    """
    natal_nak = _nak.janma_nakshatra(chart, ayanamsa=ayanamsa)
    moon = chart.getObject(const.MOON)
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

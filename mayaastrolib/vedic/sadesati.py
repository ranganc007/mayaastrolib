"""Sade Sati — the ~7.5-year Saturn-over-natal-Moon transit period.

Sade Sati ("seven and a half") runs while transiting Saturn occupies the
12th, 1st (the natal Moon's own sign), and 2nd signs from the natal Moon
— each ~2.5-year leg called a *dhaiyya*. The middle leg (Saturn in the
Moon's own sign, "janma shani") is traditionally the most intense.

Two related lesser transits ("small panoti"):
- Ashtama Shani — Saturn in the 8th from the natal Moon (~2.5 yr).
- Kantaka / Ardhashtama Shani — Saturn in the 4th from the natal Moon.

Saturn's geocentric longitude is location-independent at the day
granularity, so these functions take a natal Moon *sign index* and a
target :class:`Datetime` — no GeoPos required.

References:
- Phaladeepika ch. 26 (Sade Sati and the dhaiyyas)
- BPHS ch. 81 (Saturn transit effects)
"""

from dataclasses import dataclass

import swisseph

from mayaastrolib import const
from mayaastrolib.vedic import ayanamsa as _ay

# Phase labels.
PHASE_RISING = "rising"  # Saturn 12th from natal Moon
PHASE_PEAK = "peak"  # Saturn in natal Moon's own sign (janma shani)
PHASE_SETTING = "setting"  # Saturn 2nd from natal Moon
PHASE_NONE = "not-active"

# Severity labels, by phase.
_SEVERITY = {
    PHASE_PEAK: "intense",
    PHASE_RISING: "moderate",
    PHASE_SETTING: "mild",
    PHASE_NONE: "none",
}

_SWE_SATURN = 6  # pyswisseph body id for Saturn

# Map from "houses-of-difference" (Saturn sign minus Moon sign, mod 12)
# to phase. House 12 from the Moon = diff 11; house 1 = diff 0; house 2 = diff 1.
_DIFF_TO_PHASE = {11: PHASE_RISING, 0: PHASE_PEAK, 1: PHASE_SETTING}

# Small-panoti diffs: 8th from Moon = diff 7; 4th from Moon = diff 3.
_DIFF_TO_PANOTI = {7: "ashtama_shani", 3: "kantaka_shani"}


@dataclass(frozen=True)
class SadeSatiPhase:
    """The Sade Sati state at a particular moment.

    Attributes:
        active: True if Saturn is in the 12th, 1st, or 2nd from the
            natal Moon.
        phase: One of ``"rising"``, ``"peak"``, ``"setting"``,
            ``"not-active"``.
        saturn_sign: The sign name Saturn currently transits (sidereal).
        natal_moon_sign: The natal Moon's sign name (sidereal).
        severity: ``"intense"`` (peak), ``"moderate"`` (rising),
            ``"mild"`` (setting), or ``"none"``.
    """

    active: bool
    phase: str
    saturn_sign: str
    natal_moon_sign: str
    severity: str


def _normalise_sign(sign):
    """Accept a sign index (0..11) or a sign-name string; return the index."""
    if isinstance(sign, str):
        if sign not in const.LIST_SIGNS:
            raise ValueError(f"Unknown sign name {sign!r}; expected one of {const.LIST_SIGNS}")
        return const.LIST_SIGNS.index(sign)
    return int(sign) % 12


def _phase_for_diff(saturn_sign, moon_sign):
    """Return the Sade Sati phase given Saturn's and the Moon's sign indices."""
    diff = (saturn_sign - moon_sign) % 12
    return _DIFF_TO_PHASE.get(diff, PHASE_NONE)


def saturn_sidereal_sign(target, ayanamsa=const.AYANAMSA_LAHIRI):
    """Return Saturn's sidereal sign index (0..11) at the target Datetime."""
    sweList, _flg = swisseph.calc_ut(target.jd, _SWE_SATURN)
    saturn_trop = sweList[0]
    saturn_sid = _ay.to_sidereal(saturn_trop, target, ayanamsa=ayanamsa)
    return int((saturn_sid % 360.0) // 30.0)


def sade_sati(natal_moon_sign, target, ayanamsa=const.AYANAMSA_LAHIRI):
    """Return the Sade Sati phase active at ``target``.

    Args:
        natal_moon_sign: Sign index 0..11 or sign-name string for the
            natal Moon (sidereal).
        target: A :class:`Datetime`.
        ayanamsa: One of ``const.LIST_AYANAMSAS``.

    Returns:
        A :class:`SadeSatiPhase`.
    """
    moon_idx = _normalise_sign(natal_moon_sign)
    saturn_idx = saturn_sidereal_sign(target, ayanamsa=ayanamsa)
    phase = _phase_for_diff(saturn_idx, moon_idx)
    return SadeSatiPhase(
        active=phase != PHASE_NONE,
        phase=phase,
        saturn_sign=const.LIST_SIGNS[saturn_idx],
        natal_moon_sign=const.LIST_SIGNS[moon_idx],
        severity=_SEVERITY[phase],
    )


def sade_sati_for_year(natal_moon_sign, year, ayanamsa=const.AYANAMSA_LAHIRI):
    """Return the Sade Sati phase at mid-year (July 1, 12:00 UTC) of ``year``.

    Convenience for "is this person in Sade Sati during <year>" — uses
    the year's midpoint as a representative sample. For day-precise
    boundaries, query :func:`sade_sati` directly.
    """
    from mayaastrolib.datetime import Datetime

    mid = Datetime(f"{year}/07/01", "12:00", "+00:00")
    return sade_sati(natal_moon_sign, mid, ayanamsa=ayanamsa)


def small_panoti(natal_moon_sign, target, ayanamsa=const.AYANAMSA_LAHIRI):
    """Return the small-panoti label active at ``target``, or ``None``.

    Returns ``"ashtama_shani"`` if Saturn is in the 8th from the natal
    Moon, ``"kantaka_shani"`` if in the 4th, else ``None``. These do not
    overlap Sade Sati (8th and 4th are not 12th/1st/2nd).
    """
    moon_idx = _normalise_sign(natal_moon_sign)
    saturn_idx = saturn_sidereal_sign(target, ayanamsa=ayanamsa)
    diff = (saturn_idx - moon_idx) % 12
    return _DIFF_TO_PANOTI.get(diff)

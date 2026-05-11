"""Tajika — Vedic annual ("Persian-derived") astrology.

This module ships the core slice: the *varshapravesh* (the moment the
sidereal Sun returns to its natal sidereal position in a target year)
and the *Mudda dasha* (the Vimshottari proportions compressed into that
one year). The Lord-of-Year, Harsha Bala, Panchavargiya Bala, and the
~50 Tajika Sahams are deferred to a follow-up.

References:
- Tajika Neelakanthi (the canonical Tajika text)
- BPHS ch. 31 (Panchavargiya Bala — carried into Tajika; not in this slice)
"""

from mayaastrolib import const
from mayaastrolib.datetime import Datetime
from mayaastrolib.ephem.tools import MAX_ERROR
from mayaastrolib.vedic import ayanamsa as _ay
from mayaastrolib.vedic import nakshatras as _nak
from mayaastrolib.vedic.dasha import (
    DAYS_PER_VIMSHOTTARI_YEAR,
    VIMSHOTTARI_ORDER,
    VIMSHOTTARI_YEARS,
    DashaPeriod,
    _add_days,
)

_SWE_SUN = 0
_SWE_MOON = 1

# A Tajika year is one tropical year of the Sun's return; we use the same
# 365.25-day convention as the Vimshottari/Mudda arithmetic.
TAJIKA_YEAR_DAYS = DAYS_PER_VIMSHOTTARI_YEAR


def _sidereal_lon(swe_body, jd, ayanamsa):
    """Return the sidereal longitude of a swisseph body at ``jd``."""
    from mayaastrolib.ephem.swe import _sidereal_calc_ut

    sweList, _flg = _sidereal_calc_ut(jd, swe_body, ayanamsa)
    return sweList[0] % 360.0


def _closest_distance(a, b):
    """Signed shortest angular distance from ``a`` to ``b`` in (-180, 180]."""
    d = (b - a) % 360.0
    return d - 360.0 if d > 180.0 else d


def sidereal_sun_return_jd(start_jd, target_sidereal_lon, ayanamsa=const.AYANAMSA_LAHIRI):
    """Find the JD at or after ``start_jd`` when the sidereal Sun is at
    ``target_sidereal_lon``.

    Newton-style iteration on the Sun's mean motion, identical in shape
    to :func:`mayaastrolib.ephem.tools.solarReturnJD` but using sidereal
    longitudes.
    """
    jd = start_jd
    sun = _sidereal_lon(_SWE_SUN, jd, ayanamsa)
    # Walk forward to the first occurrence at/after start_jd.
    dist = (target_sidereal_lon - sun) % 360.0
    while abs(dist) > MAX_ERROR:
        jd = jd + dist / const.MEAN_MOTION_SUN
        sun = _sidereal_lon(_SWE_SUN, jd, ayanamsa)
        dist = _closest_distance(sun, target_sidereal_lon)
    return jd


def _natal_sidereal_sun_lon(natal_chart, ayanamsa):
    sun = natal_chart.getObject(const.SUN)
    if natal_chart.zodiac == const.ZODIAC_SIDEREAL:
        return sun.lon % 360.0
    return _ay.to_sidereal(sun.lon, natal_chart.date, ayanamsa=ayanamsa) % 360.0


def varshapravesh(natal_chart, target_year, ayanamsa=const.AYANAMSA_LAHIRI):
    """Return the varshapravesh :class:`Datetime` for ``target_year``.

    The varshapravesh is the moment in ``target_year`` when the sidereal
    Sun returns to the natal chart's sidereal Sun longitude.

    Args:
        natal_chart: The natal :class:`Chart` (tropical or sidereal).
        target_year: The civil year to compute the annual chart for.
        ayanamsa: One of ``const.LIST_AYANAMSAS``.

    Returns:
        A :class:`Datetime` in the natal chart's UTC offset.
    """
    target_lon = _natal_sidereal_sun_lon(natal_chart, ayanamsa)
    anchor = Datetime(f"{target_year}/01/01", "00:00", natal_chart.date.utcoffset)
    jd = sidereal_sun_return_jd(anchor.jd, target_lon, ayanamsa=ayanamsa)
    return Datetime.fromJD(jd, natal_chart.date.utcoffset)


def mudda_dasha(varshapravesh_date, ayanamsa=const.AYANAMSA_LAHIRI):
    """Return the 9 Mudda (Varsha Vimshottari) dasha periods for the year.

    The 365.25-day year is divided among the 9 Vimshottari lords in the
    standard proportions, the sequence starting from the lord of the
    nakshatra the Moon occupies at ``varshapravesh_date`` and proceeding
    through the Vimshottari cycle.

    Args:
        varshapravesh_date: The varshapravesh :class:`Datetime` (e.g.
            from :func:`varshapravesh`).
        ayanamsa: One of ``const.LIST_AYANAMSAS``.

    Returns:
        A list of 9 :class:`mayaastrolib.vedic.dasha.DashaPeriod` (level
        1), chronological, durations summing to 365.25 days.
    """
    moon_sid_lon = _sidereal_lon(_SWE_MOON, varshapravesh_date.jd, ayanamsa)
    start_lord = _nak.of_longitude(moon_sid_lon).lord
    start_idx = VIMSHOTTARI_ORDER.index(start_lord)

    periods = []
    current_start = varshapravesh_date
    for i in range(9):
        lord = VIMSHOTTARI_ORDER[(start_idx + i) % 9]
        days = (VIMSHOTTARI_YEARS[lord] / 120.0) * TAJIKA_YEAR_DAYS
        end = _add_days(current_start, days)
        periods.append(DashaPeriod(lord=lord, start=current_start, end=end, level=1))
        current_start = end
    return periods

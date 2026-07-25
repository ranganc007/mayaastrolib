"""Ayanamsa computation — the offset between tropical and sidereal zodiacs.

The ayanamsa is a slowly-varying angle (~50 arcseconds/year) measuring
precession of the equinoxes since the canonical epoch of each tradition.

Supported:
- **Lahiri** — the standard for Indian Vedic astrology; the Indian
  Astronomical Ephemeris uses it.
- **Krishnamurti** — the KP system's ayanamsa (K.S. Krishnamurti's own
  value; ~0.1° smaller than Lahiri).
- **Raman** — B.V. Raman's ayanamsa.
- **Fagan-Bradley** — the Western sidereal standard (not used in Vedic;
  provided for comparison and Western-sidereal consumers).

References:
- Indian Astronomical Ephemeris (Lahiri canonical implementation)
- pyswisseph ``swe.get_ayanamsa_ut(jd)`` with ``set_sid_mode``
- IAU 1976 nutation/precession model
"""

import threading

import swisseph

from mayaastrolib import const

__all__ = [
    "get",
    "lahiri",
    "krishnamurti",
    "raman",
    "fagan_bradley",
    "to_sidereal",
    "to_tropical",
]

# Map our string constants to pyswisseph integer mode IDs.
_AYANAMSA_TO_SWE_MODE = {
    const.AYANAMSA_LAHIRI: swisseph.SIDM_LAHIRI,
    const.AYANAMSA_KRISHNAMURTI: swisseph.SIDM_KRISHNAMURTI,
    const.AYANAMSA_RAMAN: swisseph.SIDM_RAMAN,
    const.AYANAMSA_FAGAN_BRADLEY: swisseph.SIDM_FAGAN_BRADLEY,
}

# Lock guarding ``swisseph.set_sid_mode`` + ``swisseph.get_ayanamsa_ut``,
# which both manipulate process-global pyswisseph state.
_AYANAMSA_LOCK = threading.Lock()


def _swe_mode_for(ayanamsa):
    """Return the pyswisseph integer mode constant for a named ayanamsa.

    Raises:
        ValueError: if ``ayanamsa`` is not in ``const.LIST_AYANAMSAS``.
    """
    if ayanamsa not in _AYANAMSA_TO_SWE_MODE:
        raise ValueError(f"Unknown ayanamsa {ayanamsa!r}; supported: {const.LIST_AYANAMSAS}")
    return _AYANAMSA_TO_SWE_MODE[ayanamsa]


def get(ayanamsa, date):
    """Return the named ayanamsa in degrees at the UT-based ``date``.

    Args:
        ayanamsa: One of ``const.LIST_AYANAMSAS``.
        date: A :class:`~mayaastrolib.datetime.Datetime`.

    Returns:
        The ayanamsa value at ``date.jd`` in decimal degrees. Positive
        means sidereal longitude < tropical longitude.
    """
    with _AYANAMSA_LOCK:
        swisseph.set_sid_mode(_swe_mode_for(ayanamsa))
        return swisseph.get_ayanamsa_ut(date.jd)


def lahiri(date):
    """Lahiri ayanamsa in degrees at ``date``.

    Named for N. C. Lahiri, who chaired the 1955 Indian Calendar Reform
    Committee; the canonical sidereal offset of the Indian Astronomical
    Ephemeris.

    Example:
        >>> from mayaastrolib.datetime import Datetime
        >>> from mayaastrolib.vedic.ayanamsa import lahiri
        >>> lahiri(Datetime("2000/01/01", "12:00", "+00:00"))  # ~23.857
    """
    return get(const.AYANAMSA_LAHIRI, date)


def krishnamurti(date):
    """Krishnamurti (KP) ayanamsa in degrees at ``date``.

    Used by the Krishnamurti Paddhati system; ~0.1° smaller than Lahiri.
    """
    return get(const.AYANAMSA_KRISHNAMURTI, date)


def raman(date):
    """B.V. Raman's ayanamsa in degrees at ``date``."""
    return get(const.AYANAMSA_RAMAN, date)


def fagan_bradley(date):
    """Fagan-Bradley (Western sidereal) ayanamsa in degrees at ``date``."""
    return get(const.AYANAMSA_FAGAN_BRADLEY, date)


def to_sidereal(tropical_lon, date, ayanamsa=const.AYANAMSA_LAHIRI):
    """Convert a tropical longitude to sidereal under the given ayanamsa.

    Args:
        tropical_lon: Tropical longitude in degrees.
        date: The moment at which to compute the ayanamsa offset.
        ayanamsa: One of ``const.LIST_AYANAMSAS``. Defaults to Lahiri.

    Returns:
        Sidereal longitude in degrees, normalised to ``[0, 360)``.
    """
    offset = get(ayanamsa, date)
    return (tropical_lon - offset) % 360.0


def to_tropical(sidereal_lon, date, ayanamsa=const.AYANAMSA_LAHIRI):
    """Convert a sidereal longitude back to tropical under the given ayanamsa."""
    offset = get(ayanamsa, date)
    return (sidereal_lon + offset) % 360.0

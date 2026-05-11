"""Ayanamsa computation — the offset between tropical and sidereal zodiacs.

The ayanamsa is a slowly-varying angle (~50 arcseconds/year) measuring
precession of the equinoxes since the canonical epoch of each tradition.
Lahiri ayanamsa is the standard for Indian Vedic astrology; the Indian
Astronomical Ephemeris uses it.

References:
- Indian Astronomical Ephemeris (Lahiri canonical implementation)
- pyswisseph ``swe.get_ayanamsa_ut(jd)`` (Lahiri at IAU 1976 precision)
- IAU 1976 nutation/precession model
"""

import threading

import swisseph

from mayaastrolib import const

# Map our string constants to pyswisseph integer mode IDs.
_AYANAMSA_TO_SWE_MODE = {
    const.AYANAMSA_LAHIRI: swisseph.SIDM_LAHIRI,
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


def lahiri(date):
    """Lahiri ayanamsa in degrees at the given UT-based ``date``.

    The Lahiri ayanamsa (named for N. C. Lahiri, who chaired the 1955
    Indian Calendar Reform Committee) is the canonical sidereal offset
    used by the Indian Astronomical Ephemeris. Returns degrees;
    positive means sidereal longitude < tropical longitude.

    Args:
        date: A :class:`~mayaastrolib.datetime.Datetime`.

    Returns:
        Ayanamsa value at ``date.jd`` in decimal degrees.

    Example:
        >>> from mayaastrolib.datetime import Datetime
        >>> from mayaastrolib.vedic.ayanamsa import lahiri
        >>> lahiri(Datetime("2000/01/01", "12:00", "+00:00"))  # ~23.857
    """
    with _AYANAMSA_LOCK:
        swisseph.set_sid_mode(_swe_mode_for(const.AYANAMSA_LAHIRI))
        return swisseph.get_ayanamsa_ut(date.jd)


def get(ayanamsa, date):
    """Return the named ayanamsa in degrees at ``date``.

    Dispatch helper that resolves a string ayanamsa name to the
    corresponding implementation. Currently only Lahiri is supported;
    additional ayanamsas (KP, Raman, Fagan-Bradley) follow in Task 017b.
    """
    if ayanamsa == const.AYANAMSA_LAHIRI:
        return lahiri(date)
    raise ValueError(f"Unknown ayanamsa {ayanamsa!r}; supported: {const.LIST_AYANAMSAS}")


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

"""
This file is part of mayaastrolib, a fork of flatlib - (C) FlatAngle
Author: João Ventura (flatangleweb@gmail.com)


This module implements a simple interface with the C
Swiss Ephemeris using the pyswisseph library.

The pyswisseph library must be already installed and
accessible.

"""

import functools
import threading

import swisseph

from mayaastrolib import angle, const

# Map objects
SWE_OBJECTS = {
    const.SUN: 0,
    const.MOON: 1,
    const.MERCURY: 2,
    const.VENUS: 3,
    const.MARS: 4,
    const.JUPITER: 5,
    const.SATURN: 6,
    const.URANUS: 7,
    const.NEPTUNE: 8,
    const.PLUTO: 9,
    const.CHIRON: 15,
    const.NORTH_NODE: 10,
}

# Map house systems
SWE_HOUSESYS = {
    const.HOUSES_PLACIDUS: b"P",
    const.HOUSES_KOCH: b"K",
    const.HOUSES_PORPHYRIUS: b"O",
    const.HOUSES_REGIOMONTANUS: b"R",
    const.HOUSES_CAMPANUS: b"C",
    const.HOUSES_EQUAL: b"A",
    const.HOUSES_EQUAL_2: b"E",
    const.HOUSES_VEHLOW_EQUAL: b"V",
    const.HOUSES_WHOLE_SIGN: b"W",
    const.HOUSES_MERIDIAN: b"X",
    const.HOUSES_AZIMUTHAL: b"H",
    const.HOUSES_POLICH_PAGE: b"T",
    const.HOUSES_ALCABITUS: b"B",
    const.HOUSES_MORINUS: b"M",
}


# ==== Internal functions ==== #


# pyswisseph wraps the Swiss Ephemeris C library, which is NOT fully
# thread-safe: ``set_sid_mode`` mutates process-global state, and the
# library keeps internal static buffers/caches across calls. This single
# reentrant lock serialises EVERY swisseph entry point, so the engine is
# safe to drive from a thread pool (e.g. FastAPI under load via the async
# helpers in ``mayaastrolib.aio``). It is an RLock because a few helpers
# nest swisseph calls (e.g. ``sweFixedStar`` → ``_fixstar_mag``).
#
# swisseph calls are fast (µs–ms), so serialising them trades a little
# parallelism for correctness; the async helpers keep the event loop free
# regardless. See docs/CONCURRENCY.md.
_SWE_LOCK = threading.RLock()


def setPath(path):
    """Sets the path for the swe files."""
    with _SWE_LOCK:
        swisseph.set_ephe_path(path)


# === Sidereal mode plumbing (Task 017) === #


def _sidereal_calc_ut(jd, sweObj, ayanamsa):
    """Thread-safe sidereal :func:`swisseph.calc_ut` call.

    Resolves the ayanamsa name lazily to avoid an import cycle with
    :mod:`mayaastrolib.vedic.ayanamsa`.
    """
    from mayaastrolib.vedic.ayanamsa import _swe_mode_for

    with _SWE_LOCK:
        swisseph.set_sid_mode(_swe_mode_for(ayanamsa))
        return swisseph.calc_ut(jd, sweObj, swisseph.FLG_SIDEREAL)


def _sidereal_houses_ex(jd, lat, lon, hsys, ayanamsa):
    """Thread-safe sidereal :func:`swisseph.houses_ex` call."""
    from mayaastrolib.vedic.ayanamsa import _swe_mode_for

    with _SWE_LOCK:
        swisseph.set_sid_mode(_swe_mode_for(ayanamsa))
        return swisseph.houses_ex(jd, lat, lon, hsys, swisseph.FLG_SIDEREAL)


# === Object functions === #


def sweObject(obj, jd, zodiac=const.ZODIAC_TROPICAL, ayanamsa=const.AYANAMSA_LAHIRI):
    """Returns an object from the Ephemeris.

    Args:
        obj: Object ID (e.g. ``const.SUN``).
        jd: Julian Day (UT).
        zodiac: ``const.ZODIAC_TROPICAL`` (default) or
            ``const.ZODIAC_SIDEREAL``.
        ayanamsa: Used only when ``zodiac == ZODIAC_SIDEREAL``.
    """
    sweObj = SWE_OBJECTS[obj]
    with _SWE_LOCK:
        if zodiac == const.ZODIAC_SIDEREAL:
            sweList, flg = _sidereal_calc_ut(jd, sweObj, ayanamsa)
        else:
            sweList, flg = swisseph.calc_ut(jd, sweObj)
    return {
        "id": obj,
        "lon": sweList[0],
        "lat": sweList[1],
        "lonspeed": sweList[3],
        "latspeed": sweList[4],
    }


def sweObjectLon(obj, jd, zodiac=const.ZODIAC_TROPICAL, ayanamsa=const.AYANAMSA_LAHIRI):
    """Returns the longitude of an object.

    See :func:`sweObject` for ``zodiac``/``ayanamsa`` semantics.
    """
    sweObj = SWE_OBJECTS[obj]
    with _SWE_LOCK:
        if zodiac == const.ZODIAC_SIDEREAL:
            sweList, flg = _sidereal_calc_ut(jd, sweObj, ayanamsa)
        else:
            sweList, flg = swisseph.calc_ut(jd, sweObj)
    return sweList[0]


def sweNextTransit(obj, jd, lat, lon, flag):
    """Returns the julian date of the next transit of
    an object. The flag should be 'RISE' or 'SET'.

    """
    sweObj = SWE_OBJECTS[obj]
    flag = swisseph.CALC_RISE if flag == "RISE" else swisseph.CALC_SET
    with _SWE_LOCK:
        trans = swisseph.rise_trans(jd, sweObj, flag, (lon, lat, 0))
    return trans[1][0]


# === Houses and angles === #


def sweHouses(jd, lat, lon, hsys, zodiac=const.ZODIAC_TROPICAL, ayanamsa=const.AYANAMSA_LAHIRI):
    """Returns lists of houses and angles.

    See :func:`sweObject` for ``zodiac``/``ayanamsa`` semantics.
    """
    hsys_b = SWE_HOUSESYS[hsys]
    with _SWE_LOCK:
        if zodiac == const.ZODIAC_SIDEREAL:
            hlist, ascmc = _sidereal_houses_ex(jd, lat, lon, hsys_b, ayanamsa)
        else:
            hlist, ascmc = swisseph.houses(jd, lat, lon, hsys_b)
    # Add first house to the end of 'hlist' so that we
    # can compute house sizes with an iterator
    hlist += (hlist[0],)
    houses = [
        {
            "id": const.LIST_HOUSES[i],
            "lon": hlist[i],
            "size": angle.distance(hlist[i], hlist[i + 1]),
        }
        for i in range(12)
    ]
    angles = [
        {"id": const.ASC, "lon": ascmc[0]},
        {"id": const.MC, "lon": ascmc[1]},
        {"id": const.DESC, "lon": angle.norm(ascmc[0] + 180)},
        {"id": const.IC, "lon": angle.norm(ascmc[1] + 180)},
    ]
    return (houses, angles)


def sweHousesLon(jd, lat, lon, hsys, zodiac=const.ZODIAC_TROPICAL, ayanamsa=const.AYANAMSA_LAHIRI):
    """Returns lists with house and angle longitudes."""
    hsys_b = SWE_HOUSESYS[hsys]
    with _SWE_LOCK:
        if zodiac == const.ZODIAC_SIDEREAL:
            hlist, ascmc = _sidereal_houses_ex(jd, lat, lon, hsys_b, ayanamsa)
        else:
            hlist, ascmc = swisseph.houses(jd, lat, lon, hsys_b)
    angles = [ascmc[0], ascmc[1], angle.norm(ascmc[0] + 180), angle.norm(ascmc[1] + 180)]
    return (hlist, angles)


# === Fixed stars === #

# `swisseph.fixstar2_mag` parses fixstars.cat on every call — slow
# (~40us per call on this machine). Cached per-process at the
# wrapper layer below, since star magnitudes are immutable.


@functools.cache
def _fixstar_mag(star):
    """Return the cached apparent-magnitude tuple for a fixed star.

    Wraps :func:`swisseph.fixstar2_mag`. The underlying call reparses
    ``fixstars.cat`` every invocation, which is expensive when
    iterating over the default fixed-star list. Star magnitudes are
    process-immutable, so the LRU cache (unbounded; ~30–100 named
    stars at most) is safe and gives a hundreds-of-x speedup on
    bulk access.
    """
    with _SWE_LOCK:
        return swisseph.fixstar2_mag(star)


def sweFixedStar(star, jd):
    """Returns a fixed star from the Ephemeris."""
    with _SWE_LOCK:
        sweList, stnam, flg = swisseph.fixstar2_ut(star, jd)
    mag = _fixstar_mag(star)
    return {"id": star, "mag": mag, "lon": sweList[0], "lat": sweList[1]}


# === Eclipses === #


def solarEclipseGlobal(jd, backward):
    """Returns the jd details of previous or next global solar eclipse."""

    with _SWE_LOCK:
        sweList = swisseph.sol_eclipse_when_glob(jd, backwards=backward)
    return {
        "maximum": sweList[1][0],
        "begin": sweList[1][2],
        "end": sweList[1][3],
        "totality_begin": sweList[1][4],
        "totality_end": sweList[1][5],
        "center_line_begin": sweList[1][6],
        "center_line_end": sweList[1][7],
    }


def lunarEclipseGlobal(jd, backward):
    """Returns the jd details of previous or next global lunar eclipse."""

    with _SWE_LOCK:
        sweList = swisseph.lun_eclipse_when(jd, backwards=backward)
    return {
        "maximum": sweList[1][0],
        "partial_begin": sweList[1][2],
        "partial_end": sweList[1][3],
        "totality_begin": sweList[1][4],
        "totality_end": sweList[1][5],
        "penumbral_begin": sweList[1][6],
        "penumbral_end": sweList[1][7],
    }

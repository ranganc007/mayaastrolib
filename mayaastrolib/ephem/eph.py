"""
This file is part of flatlib - (C) FlatAngle
Author: João Ventura (flatangleweb@gmail.com)


This module implements functions for retrieving
astronomical and astrological data from an ephemeris.

It is as middle layer between the Swiss Ephemeris
and user software. Objects are treated as python
dicts and jd/lat/lon as float.

"""

from mayaastrolib import angle, const

from . import swe, tools

# === Objects === #


def _shift_to_sidereal(lon_value, jd, ayanamsa):
    """Convert a tropical longitude to sidereal for the given Julian day.

    Used by the PF/Syzygy paths, which compute against tropical Sun/Moon
    and then shift the result. Avoids cycles by importing lazily.
    """
    from mayaastrolib.datetime import Datetime
    from mayaastrolib.vedic.ayanamsa import to_sidereal

    date_proxy = Datetime.fromJD(jd, "+00:00")
    return to_sidereal(lon_value, date_proxy, ayanamsa=ayanamsa)


def getObject(
    ID,
    jd,
    lat,
    lon,
    zodiac=const.ZODIAC_TROPICAL,
    ayanamsa=const.AYANAMSA_LAHIRI,
):
    """Returns an object for a specific date and location.

    Args:
        ID: Object ID.
        jd: Julian Day (UT).
        lat: Geographic latitude.
        lon: Geographic longitude.
        zodiac: ``const.ZODIAC_TROPICAL`` (default) or ``const.ZODIAC_SIDEREAL``.
        ayanamsa: Used only when ``zodiac == ZODIAC_SIDEREAL``.
    """
    if ID == const.SOUTH_NODE:
        obj = swe.sweObject(const.NORTH_NODE, jd, zodiac=zodiac, ayanamsa=ayanamsa)
        obj.update({"id": const.SOUTH_NODE, "lon": angle.norm(obj["lon"] + 180)})
    elif ID == const.PARS_FORTUNA:
        # Pars Fortuna's diurnal check needs tropical Sun/MC for correct
        # horizon math. The formula (Asc + Moon - Sun) is offset-invariant,
        # so we compute tropical then shift the result if needed.
        pflon = tools.pfLon(jd, lat, lon)
        if zodiac == const.ZODIAC_SIDEREAL:
            pflon = _shift_to_sidereal(pflon, jd, ayanamsa)
        obj = {"id": ID, "lon": pflon, "lat": 0, "lonspeed": 0, "latspeed": 0}
    elif ID == const.SYZYGY:
        # Syzygy is a JD-finding iteration; once found, Moon at that
        # moment is computed in the target zodiac directly.
        szjd = tools.syzygyJD(jd)
        obj = swe.sweObject(const.MOON, szjd, zodiac=zodiac, ayanamsa=ayanamsa)
        obj["id"] = const.SYZYGY
    else:
        obj = swe.sweObject(ID, jd, zodiac=zodiac, ayanamsa=ayanamsa)

    _signInfo(obj)
    return obj


# === Houses === #


def getHouses(
    jd,
    lat,
    lon,
    hsys,
    zodiac=const.ZODIAC_TROPICAL,
    ayanamsa=const.AYANAMSA_LAHIRI,
):
    """Returns lists of houses and angles."""
    houses, angles = swe.sweHouses(
        jd,
        lat,
        lon,
        hsys,
        zodiac=zodiac,
        ayanamsa=ayanamsa,
    )
    for house in houses:
        _signInfo(house)
    for ang in angles:
        _signInfo(ang)
    return (houses, angles)


# === Fixed stars === #


def getFixedStar(ID, jd):
    """Returns a fixed star."""
    star = swe.sweFixedStar(ID, jd)
    _signInfo(star)
    return star


# === Solar returns === #


def nextSolarReturn(jd, lon):
    """Return the JD of the next solar return."""
    return tools.solarReturnJD(jd, lon, True)


def prevSolarReturn(jd, lon):
    """Returns the JD of the previous solar return."""
    return tools.solarReturnJD(jd, lon, False)


# === Sunrise and sunsets === #


def nextSunrise(jd, lat, lon):
    """Returns the JD of the next sunrise."""
    return swe.sweNextTransit(const.SUN, jd, lat, lon, "RISE")


def nextSunset(jd, lat, lon):
    """Returns the JD of the next sunset."""
    return swe.sweNextTransit(const.SUN, jd, lat, lon, "SET")


def lastSunrise(jd, lat, lon):
    """Returns the JD of the last sunrise."""
    return nextSunrise(jd - 1.0, lat, lon)


def lastSunset(jd, lat, lon):
    """Returns the JD of the last sunset."""
    return nextSunset(jd - 1.0, lat, lon)


# === Stations === #


def nextStation(ID, jd):
    """Returns the aproximate jd of the next station."""
    return tools.nextStationJD(ID, jd)


# === Other functions === #


def _signInfo(obj):
    """Appends the sign id and longitude to an object."""
    lon = obj["lon"]
    obj.update({"sign": const.LIST_SIGNS[int(lon / 30)], "signlon": lon % 30})

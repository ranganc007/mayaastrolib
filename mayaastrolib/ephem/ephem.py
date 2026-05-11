"""
This file is part of flatlib - (C) FlatAngle
Author: João Ventura (flatangleweb@gmail.com)


This module implements functions which are useful
for mayaastrolib. Basically, it converts internal objects
and lists from the ephemeris to mayaastrolib.objects and
mayaastrolib.lists.

Flatlib users will want to use this module for
accessing the ephemeris.

"""

from mayaastrolib import const
from mayaastrolib.datetime import Datetime
from mayaastrolib.lists import FixedStarList, GenericList, HouseList, ObjectList
from mayaastrolib.object import FixedStar, GenericObject, House, Object

from . import eph, swe

# === Objects === #


def getObject(
    ID,
    date,
    pos,
    zodiac=const.ZODIAC_TROPICAL,
    ayanamsa=const.AYANAMSA_LAHIRI,
):
    """Returns an ephemeris object.

    See :func:`mayaastrolib.ephem.eph.getObject` for ``zodiac``/``ayanamsa``
    semantics.
    """
    obj = eph.getObject(
        ID,
        date.jd,
        pos.lat,
        pos.lon,
        zodiac=zodiac,
        ayanamsa=ayanamsa,
    )
    return Object.fromDict(obj)


def getObjectList(
    IDs,
    date,
    pos,
    zodiac=const.ZODIAC_TROPICAL,
    ayanamsa=const.AYANAMSA_LAHIRI,
):
    """Returns a list of objects."""
    objList = [getObject(ID, date, pos, zodiac=zodiac, ayanamsa=ayanamsa) for ID in IDs]
    return ObjectList(objList)


# === Houses and angles === #


def getHouses(
    date,
    pos,
    hsys,
    zodiac=const.ZODIAC_TROPICAL,
    ayanamsa=const.AYANAMSA_LAHIRI,
):
    """Returns the lists of houses and angles.

    Since houses and angles are computed at the
    same time, this function should be fast.

    See :func:`mayaastrolib.ephem.eph.getObject` for ``zodiac``/``ayanamsa``
    semantics.
    """
    houses, angles = eph.getHouses(
        date.jd,
        pos.lat,
        pos.lon,
        hsys,
        zodiac=zodiac,
        ayanamsa=ayanamsa,
    )
    hList = [House.fromDict(house) for house in houses]
    aList = [GenericObject.fromDict(angle) for angle in angles]
    return (HouseList(hList), GenericList(aList))


def getHouseList(date, pos, hsys):
    """Returns a list of houses."""
    return getHouses(date, pos, hsys)["houses"]


def getAngleList(date, pos, hsys):
    """Returns a list of angles (Asc, MC..)"""
    return getHouses(date, pos, hsys)["angles"]


# === Fixed stars === #


def getFixedStar(ID, date):
    """Returns a fixed star from the ephemeris."""
    star = eph.getFixedStar(ID, date.jd)
    return FixedStar.fromDict(star)


def getFixedStarList(IDs, date):
    """Returns a list of fixed stars."""
    starList = [getFixedStar(ID, date) for ID in IDs]
    return FixedStarList(starList)


# === Solar returns === #


def nextSolarReturn(date, lon, zodiac=const.ZODIAC_TROPICAL, ayanamsa=const.AYANAMSA_LAHIRI):
    """Returns the next date when the sun is at longitude 'lon'.

    See :func:`mayaastrolib.ephem.tools.solarReturnJD` for the
    ``zodiac``/``ayanamsa`` semantics.
    """
    jd = eph.nextSolarReturn(date.jd, lon, zodiac=zodiac, ayanamsa=ayanamsa)
    return Datetime.fromJD(jd, date.utcoffset)


def prevSolarReturn(date, lon, zodiac=const.ZODIAC_TROPICAL, ayanamsa=const.AYANAMSA_LAHIRI):
    """Returns the previous date when the sun is at longitude 'lon'."""
    jd = eph.prevSolarReturn(date.jd, lon, zodiac=zodiac, ayanamsa=ayanamsa)
    return Datetime.fromJD(jd, date.utcoffset)


# === Sunrise and sunsets === #


def nextSunrise(date, pos):
    """Returns the date of the next sunrise."""
    jd = eph.nextSunrise(date.jd, pos.lat, pos.lon)
    return Datetime.fromJD(jd, date.utcoffset)


def nextSunset(date, pos):
    """Returns the date of the next sunset."""
    jd = eph.nextSunset(date.jd, pos.lat, pos.lon)
    return Datetime.fromJD(jd, date.utcoffset)


def lastSunrise(date, pos):
    """Returns the date of the last sunrise."""
    jd = eph.lastSunrise(date.jd, pos.lat, pos.lon)
    return Datetime.fromJD(jd, date.utcoffset)


def lastSunset(date, pos):
    """Returns the date of the last sunset."""
    jd = eph.lastSunset(date.jd, pos.lat, pos.lon)
    return Datetime.fromJD(jd, date.utcoffset)


# === Station === #


def nextStation(ID, date):
    """Returns the aproximate date of the next station."""
    jd = eph.nextStation(ID, date.jd)
    return Datetime.fromJD(jd, date.utcoffset)


# === Eclipses === #


def prevSolarEclipse(date):
    """Returns the Datetime of the maximum phase of the
    previous global solar eclipse.

    """

    eclipse = swe.solarEclipseGlobal(date.jd, backward=True)
    return Datetime.fromJD(eclipse["maximum"], date.utcoffset)


def nextSolarEclipse(date):
    """Returns the Datetime of the maximum phase of the
    next global solar eclipse.

    """

    eclipse = swe.solarEclipseGlobal(date.jd, backward=False)
    return Datetime.fromJD(eclipse["maximum"], date.utcoffset)


def prevLunarEclipse(date):
    """Returns the Datetime of the maximum phase of the
    previous global lunar eclipse.

    """

    eclipse = swe.lunarEclipseGlobal(date.jd, backward=True)
    return Datetime.fromJD(eclipse["maximum"], date.utcoffset)


def nextLunarEclipse(date):
    """Returns the Datetime of the maximum phase of the
    next global lunar eclipse.

    """

    eclipse = swe.lunarEclipseGlobal(date.jd, backward=False)
    return Datetime.fromJD(eclipse["maximum"], date.utcoffset)

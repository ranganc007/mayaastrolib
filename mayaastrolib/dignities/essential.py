"""
This file is part of mayaastrolib, a fork of flatlib - (C) FlatAngle
Author: João Ventura (flatangleweb@gmail.com)


This module provides useful functions for handling
essential dignities. It provides easy access to an
essential dignity table, functions for retrieving
information from the table and to compute scores and
almutems.

Most functions accept ``terms_variant`` and ``faces_variant`` as
keyword-only parameters. Pass these for thread-safe variant
selection. The module-level globals (``TERMS``, ``FACES``) remain as
the defaults when no variant is passed; the ``setTerms`` / ``setFaces``
mutators that used to rebind them were removed in 1.0 because mutating
process-global state is not thread-safe.

The convenience functions ``score(obj)``, ``getInfo(obj)``, and
``isPeregrine(obj)`` accept an Object instance directly to spare
callers the ``obj.id, obj.sign, obj.signlon`` boilerplate.

"""

from mayaastrolib import const

from . import tables

# Face variants
CHALDEAN_FACES = "Chaldean Faces"
TRIPLICITY_FACES = "Triplicity Faces"

# Term variants
EGYPTIAN_TERMS = "Egyptian Terms"
TETRABIBLOS_TERMS = "Tetrabiblos Terms"
LILLY_TERMS = "Lilly Terms"

# Module-level defaults, used when no *_variant argument is passed.
FACES = tables.CHALDEAN_FACES
TERMS = tables.EGYPTIAN_TERMS
TABLE = tables.ESSENTIAL_DIGNITIES


# === Table properties === #


def ruler(sign):
    """Returns the ruler of the sign."""
    return TABLE[sign]["ruler"]


def exalt(sign):
    """Returns the exaltation."""
    return TABLE[sign]["exalt"][0]


def exaltDeg(sign):
    """Returns the exaltation degree."""
    return TABLE[sign]["exalt"][1]


def dayTrip(sign):
    """Returns the diurnal triplicity."""
    return TABLE[sign]["trip"][0]


def nightTrip(sign):
    """Returns the nocturnal triplicity."""
    return TABLE[sign]["trip"][1]


def partTrip(sign):
    """Returns the participant triplicity."""
    return TABLE[sign]["trip"][2]


def exile(sign):
    """Returns the exile."""
    return TABLE[sign]["exile"]


def fall(sign):
    """Returns the fall."""
    return TABLE[sign]["fall"][0]


def fallDeg(sign):
    """Returns the fall degree."""
    return TABLE[sign]["fall"][1]


def term(sign, lon, *, terms_variant=None):
    """Return the term lord for a given sign and longitude.

    Args:
        sign: Sign constant from const.LIST_SIGNS.
        lon: Longitude within the sign (0-30).
        terms_variant: One of EGYPTIAN_TERMS, TETRABIBLOS_TERMS,
            LILLY_TERMS table dicts (from
            ``mayaastrolib.dignities.tables``). Defaults to the module-level
            ``TERMS`` (``EGYPTIAN_TERMS``); passing this parameter is
            preferred and thread-safe.

    Returns:
        The term lord (a planet ID string).
    """
    if terms_variant is None:
        terms_variant = TERMS
    for ID, a, b in terms_variant[sign]:
        if a <= lon < b:
            return ID
    return None


def face(sign, lon, *, faces_variant=None):
    """Return the face lord for a given sign and longitude.

    Args:
        sign: Sign constant.
        lon: Longitude within the sign (0-30).
        faces_variant: One of CHALDEAN_FACES, TRIPLICITY_FACES table
            dicts (from ``mayaastrolib.dignities.tables``). Defaults to the
            module-level ``FACES`` (``CHALDEAN_FACES``); passing this
            parameter is preferred and thread-safe.

    Returns:
        The face lord (a planet ID string).
    """
    if faces_variant is None:
        faces_variant = FACES
    faces = faces_variant[sign]
    if lon < 10:
        return faces[0]
    elif lon < 20:
        return faces[1]
    else:
        return faces[2]


# === Complex properties === #


def _is_object(o):
    """Return True if ``o`` looks like an Object (has id/sign/signlon)."""
    return hasattr(o, "id") and hasattr(o, "sign") and hasattr(o, "signlon")


def getInfo(obj_or_sign, lon=None, *, terms_variant=None, faces_variant=None):
    """Return the complete essential dignities for a position.

    Two call styles:

        getInfo(planet_object)            # preferred
        getInfo(sign, lon)                # legacy

    Args:
        obj_or_sign: Either an Object instance (sign and signlon are
            read from it), or a sign constant.
        lon: Required when ``obj_or_sign`` is a sign string. Longitude
            within the sign (0-30).
        terms_variant: See ``term()``.
        faces_variant: See ``face()``.

    Returns:
        Dict with keys ``ruler``, ``exalt``, ``dayTrip``,
        ``nightTrip``, ``partTrip``, ``term``, ``face``, ``exile``,
        ``fall``.

    Raises:
        TypeError: when called as ``getInfo(sign)`` with no ``lon``.
    """
    if _is_object(obj_or_sign):
        sign = obj_or_sign.sign
        lon = obj_or_sign.signlon
    else:
        sign = obj_or_sign
        if lon is None:
            raise TypeError(
                "getInfo(sign, lon) requires a longitude. "
                "For convenience, getInfo(obj) accepts an Object directly."
            )
    return {
        "ruler": ruler(sign),
        "exalt": exalt(sign),
        "dayTrip": dayTrip(sign),
        "nightTrip": nightTrip(sign),
        "partTrip": partTrip(sign),
        "term": term(sign, lon, terms_variant=terms_variant),
        "face": face(sign, lon, faces_variant=faces_variant),
        "exile": exile(sign),
        "fall": fall(sign),
    }


def isPeregrine(
    obj_or_id,
    sign=None,
    lon=None,
    *,
    terms_variant=None,
    faces_variant=None,
):
    """Return True if the planet is peregrine at the given position.

    Two call styles:

        isPeregrine(planet_object)
        isPeregrine(planet_id, sign, lon)

    Args:
        obj_or_id: Either an Object or a planet ID string.
        sign, lon: Required when ``obj_or_id`` is a string.
        terms_variant, faces_variant: See ``term()`` / ``face()``.

    Raises:
        TypeError: if ``obj_or_id`` is a string and sign/lon are missing.
    """
    if _is_object(obj_or_id):
        ID = obj_or_id.id
        sign = obj_or_id.sign
        lon = obj_or_id.signlon
    else:
        ID = obj_or_id
        if sign is None or lon is None:
            raise TypeError(
                "isPeregrine(id, sign, lon) requires all three arguments. "
                "For convenience, isPeregrine(obj) accepts an Object directly."
            )
    info = getInfo(
        sign,
        lon,
        terms_variant=terms_variant,
        faces_variant=faces_variant,
    )
    for dign, objID in info.items():
        if dign not in ["exile", "fall"] and ID == objID:
            return False
    return True


# === Scores === #

SCORES = {
    "ruler": 5,
    "exalt": 4,
    "dayTrip": 3,
    "nightTrip": 3,
    "partTrip": 3,
    "term": 2,
    "face": 1,
    "fall": -4,
    "exile": -5,
}


def score(
    obj_or_id,
    sign=None,
    lon=None,
    *,
    terms_variant=None,
    faces_variant=None,
):
    """Compute the essential dignity score for a planet at a position.

    Two call styles:

        score(planet_object)            # preferred
        score(id, sign, lon)            # legacy

    Args:
        obj_or_id: Either an Object instance, or a planet ID string.
        sign: Required if ``obj_or_id`` is a string. Sign constant.
        lon: Required if ``obj_or_id`` is a string. Longitude within
            sign.
        terms_variant: See ``term()``.
        faces_variant: See ``face()``.

    Returns:
        Integer score in [-10, +5].

    Raises:
        TypeError: if ``obj_or_id`` is a string but sign/lon are
            missing.
    """
    if _is_object(obj_or_id):
        ID = obj_or_id.id
        sign = obj_or_id.sign
        lon = obj_or_id.signlon
    else:
        ID = obj_or_id
        if sign is None or lon is None:
            raise TypeError(
                "score(id, sign, lon) requires all three arguments. "
                "For convenience, score(obj) accepts an Object directly."
            )
    info = getInfo(
        sign,
        lon,
        terms_variant=terms_variant,
        faces_variant=faces_variant,
    )
    dignities = [dign for (dign, objID) in info.items() if objID == ID]
    return sum([SCORES[dign] for dign in dignities])


def almutem(sign, lon, *, terms_variant=None, faces_variant=None):
    """Return the almutem (highest-scoring planet) for a position."""
    planets = const.LIST_SEVEN_PLANETS
    res = [None, 0]
    for ID in planets:
        sc = score(
            ID,
            sign,
            lon,
            terms_variant=terms_variant,
            faces_variant=faces_variant,
        )
        if sc > res[1]:
            res = [ID, sc]
    return res[0]


# ----------------------- #
#   EssentialInfo Class   #
# ----------------------- #


class EssentialInfo:
    """This class represents the Essential dignities
    information for a given object.

    """

    def __init__(self, obj):
        self.obj = obj
        # Include info in instance properties
        info = getInfo(obj.sign, obj.signlon)
        self.__dict__.update(info)
        # Add score and almutem
        self.score = score(obj.id, obj.sign, obj.signlon)
        self.almutem = almutem(obj.sign, obj.signlon)

    def getInfo(self):
        """Returns the essential dignities for this object."""
        return getInfo(self.obj.sign, self.obj.signlon)

    def getDignities(self):
        """Returns the dignities belonging to this object."""
        info = self.getInfo()
        dignities = [dign for (dign, objID) in info.items() if objID == self.obj.id]
        return dignities

    def isPeregrine(self):
        """Returns if this object is peregrine."""
        return isPeregrine(self.obj.id, self.obj.sign, self.obj.signlon)

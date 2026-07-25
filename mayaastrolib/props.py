"""
This file is part of mayaastrolib, a fork of flatlib - (C) FlatAngle
Author: João Ventura (flatangleweb@gmail.com)


This module defines some properties of Traditional Astrology core
elements.

It defines qualities of temperaments, orbs and genders of planets,
if a house is cardinal, angular or succedent, among others.

To keep things simple, properties are divided in types, such as
base properties, planet properties, house properties, etc. Each
property type is defined as a lowercased python class so that we
can mimic different namespaces in a single python module.

"""

from . import const

__all__ = [
    "base",
    "sign",
    "object",
    "house",
    "aspect",
    "fixedStar",
    "houseSystem",
]

# ------------------- #
#   Base Properties   #
# ------------------- #


class base:
    """Base qualities shared across the system.

    Namespace for the elemental, temperament, and gender/faction tables
    that the sign, object and house namespaces build on.
    """

    # The four elements
    elements = [const.FIRE, const.EARTH, const.AIR, const.WATER]

    # The four temperaments
    temperaments = [const.CHOLERIC, const.MELANCHOLIC, const.SANGUINE, const.PHLEGMATIC]

    # Genders
    genders = [const.MASCULINE, const.FEMININE]

    # Factions
    factions = [const.DIURNAL, const.NOCTURNAL]

    # Sun seasons
    sunseasons = [const.SPRING, const.SUMMER, const.AUTUMN, const.WINTER]

    # Element to Temperament
    elementTemperament = {
        const.FIRE: const.CHOLERIC,
        const.EARTH: const.MELANCHOLIC,
        const.AIR: const.SANGUINE,
        const.WATER: const.PHLEGMATIC,
    }

    # Temperament to Element
    temperamentElement = {
        const.CHOLERIC: const.FIRE,
        const.MELANCHOLIC: const.EARTH,
        const.SANGUINE: const.AIR,
        const.PHLEGMATIC: const.WATER,
    }

    # Qualities of elements
    elementQuality = {
        const.FIRE: [const.HOT, const.DRY],
        const.EARTH: [const.COLD, const.DRY],
        const.AIR: [const.HOT, const.HUMID],
        const.WATER: [const.COLD, const.HUMID],
    }

    # Qualities of temperaments
    temperamentQuality = {
        const.CHOLERIC: [const.HOT, const.DRY],
        const.MELANCHOLIC: [const.COLD, const.DRY],
        const.SANGUINE: [const.HOT, const.HUMID],
        const.PHLEGMATIC: [const.COLD, const.HUMID],
    }

    # Moon Phase Elements
    moonphaseElement = {
        const.MOON_FIRST_QUARTER: const.AIR,
        const.MOON_SECOND_QUARTER: const.FIRE,
        const.MOON_THIRD_QUARTER: const.EARTH,
        const.MOON_LAST_QUARTER: const.WATER,
    }

    # Sun Season Elements
    sunseasonElement = {
        const.SPRING: const.AIR,
        const.SUMMER: const.FIRE,
        const.AUTUMN: const.EARTH,
        const.WINTER: const.WATER,
    }


# ------------------- #
#   Sign Properties   #
# ------------------- #


class sign:
    """Properties of the twelve zodiac signs.

    Element, quality (cardinal/fixed/mutable), gender, faction, ruler and
    the seasonal/temperament associations for each sign.
    """

    _signs = const.LIST_SIGNS

    # Modes
    _modes = [const.CARDINAL, const.FIXED, const.MUTABLE]
    mode = dict(zip(_signs, _modes * 4, strict=False))

    # Sun Season — each season repeated 3× (one per sign in the season)
    _sunseasons = [s for season in base.sunseasons for s in [season] * 3]
    sunseason = dict(zip(_signs, _sunseasons, strict=False))

    # Simple properties
    gender = dict(zip(_signs, base.genders * 6, strict=False))
    faction = dict(zip(_signs, base.factions * 6, strict=False))
    element = dict(zip(_signs, base.elements * 3, strict=False))
    temperament = dict(zip(_signs, base.temperaments * 3, strict=False))

    # Fertilities
    fertility = {
        const.ARIES: const.SIGN_MODERATELY_STERILE,
        const.TAURUS: const.SIGN_MODERATELY_FERTILE,
        const.GEMINI: const.SIGN_STERILE,
        const.CANCER: const.SIGN_FERTILE,
        const.LEO: const.SIGN_STERILE,
        const.VIRGO: const.SIGN_STERILE,
        const.LIBRA: const.SIGN_MODERATELY_FERTILE,
        const.SCORPIO: const.SIGN_FERTILE,
        const.SAGITTARIUS: const.SIGN_MODERATELY_FERTILE,
        const.CAPRICORN: const.SIGN_MODERATELY_STERILE,
        const.AQUARIUS: const.SIGN_MODERATELY_STERILE,
        const.PISCES: const.SIGN_FERTILE,
    }

    # Sign number
    number = dict((sign, i + 1) for (i, sign) in enumerate(_signs))

    # Sign figure properties
    figureBestial = [const.ARIES, const.TAURUS, const.LEO, const.SAGITTARIUS, const.CAPRICORN]

    figureHuman = [const.GEMINI, const.VIRGO, const.LIBRA, const.AQUARIUS]

    figureWild = [const.LEO]


# --------------------- #
#   Object Properties   #
# --------------------- #


class object:  # noqa: A001 — public API; renaming is a breaking change deferred to a future major version
    """Properties of the planets and other chart objects.

    Orbs, mean daily motion, gender, faction, element and temperament per
    object ID, plus the sect and joy tables used by the dignity engines.
    """

    # Mean daily motions
    meanMotion = {
        const.NO_PLANET: 0,
        const.SUN: 0.9833,
        const.MOON: 13.1833,
        const.MERCURY: 0.9833,
        const.VENUS: 0.9833,
        const.MARS: 0.5166,
        const.JUPITER: 0.0833,
        const.SATURN: 0.0333,
        const.URANUS: 0.001,
        const.NEPTUNE: 0.0001,
        const.PLUTO: 0.00001,
        const.CHIRON: 0.00001,
        const.NORTH_NODE: 13.1833,
        const.SOUTH_NODE: 13.1833,
        const.SYZYGY: 0.0,
    }

    # Object orbs
    orb = {
        const.NO_PLANET: 0,
        const.SUN: 15,
        const.MOON: 12,
        const.MERCURY: 7,
        const.VENUS: 7,
        const.MARS: 8,
        const.JUPITER: 9,
        const.SATURN: 9,
        const.URANUS: 5,
        const.NEPTUNE: 5,
        const.PLUTO: 5,
        const.CHIRON: 5,
        const.NORTH_NODE: 12,
        const.SOUTH_NODE: 12,
        const.SYZYGY: 0,
        const.PARS_FORTUNA: 0,
    }

    # Planet elements
    element = {
        const.SATURN: const.EARTH,
        const.JUPITER: const.AIR,
        const.MARS: const.FIRE,
        const.SUN: const.FIRE,
        const.VENUS: const.AIR,
        const.MERCURY: const.EARTH,
        const.MOON: const.WATER,
    }

    # Planet temperaments
    temperament = {
        const.SATURN: const.MELANCHOLIC,
        const.JUPITER: const.SANGUINE,
        const.MARS: const.CHOLERIC,
        const.SUN: const.CHOLERIC,
        const.VENUS: const.SANGUINE,
        const.MERCURY: const.MELANCHOLIC,
        const.MOON: const.PHLEGMATIC,
    }

    # Planet genders
    gender = {
        const.SATURN: const.MASCULINE,
        const.JUPITER: const.MASCULINE,
        const.MARS: const.MASCULINE,
        const.SUN: const.MASCULINE,
        const.VENUS: const.FEMININE,
        const.MERCURY: const.NEUTRAL,
        const.MOON: const.FEMININE,
    }

    # Planet factions
    faction = {
        const.SATURN: const.DIURNAL,
        const.JUPITER: const.DIURNAL,
        const.MARS: const.NOCTURNAL,
        const.SUN: const.DIURNAL,
        const.VENUS: const.NOCTURNAL,
        const.MERCURY: const.NEUTRAL,
        const.MOON: const.NOCTURNAL,
    }

    # Sign joy of planets
    signJoy = {
        const.SATURN: const.AQUARIUS,
        const.JUPITER: const.SAGITTARIUS,
        const.MARS: const.SCORPIO,
        const.SUN: const.LEO,
        const.VENUS: const.TAURUS,
        const.MERCURY: const.VIRGO,
        const.MOON: const.CANCER,
    }

    # House joy of planets
    houseJoy = {
        const.SATURN: const.HOUSE12,
        const.JUPITER: const.HOUSE11,
        const.MARS: const.HOUSE6,
        const.SUN: const.HOUSE9,
        const.VENUS: const.HOUSE5,
        const.MERCURY: const.HOUSE1,
        const.MOON: const.HOUSE3,
    }


# -------------------- #
#   House Properties   #
# -------------------- #


class house:
    """Properties of the twelve houses.

    Condition (angular/succedent/cadent), gender, and the above/below the
    horizon grouping.
    """

    _houses = const.LIST_HOUSES

    # House conditions
    _conditions = [const.ANGULAR, const.SUCCEDENT, const.CADENT]
    condition = dict(zip(_houses, _conditions * 4, strict=False))

    # House genders
    gender = dict(zip(_houses, base.genders * 4, strict=False))

    # Houses above and below horizon
    aboveHorizon = [
        const.HOUSE7,
        const.HOUSE8,
        const.HOUSE9,
        const.HOUSE10,
        const.HOUSE11,
        const.HOUSE12,
    ]

    belowHorizon = [
        const.HOUSE1,
        const.HOUSE2,
        const.HOUSE3,
        const.HOUSE4,
        const.HOUSE5,
        const.HOUSE6,
    ]


# --------------------- #
#   Aspect Properties   #
# --------------------- #


class aspect:
    """Properties of the aspects.

    Which aspects are major, minor or all, and the per-aspect metadata used
    when computing an :class:`~mayaastrolib.aspects.Aspect`.
    """

    # Names
    name = {
        # Major Aspects
        const.NO_ASPECT: "None",
        const.CONJUNCTION: "Conjunction",
        const.SEXTILE: "Sextile",
        const.SQUARE: "Square",
        const.TRINE: "Trine",
        const.OPPOSITION: "Opposition",
        # Minor Aspects
        const.SEMISEXTILE: "Semisextile",
        const.SEMIQUINTILE: "Semiquintile",
        const.SEMISQUARE: "Semisquare",
        const.QUINTILE: "Quintile",
        const.SESQUIQUINTILE: "Sesquiquintile",
        const.SESQUISQUARE: "Sesquisquare",
        const.BIQUINTILE: "Biquintile",
        const.QUINCUNX: "Quincunx",
    }


# ------------------------- #
#   Fixed Star Properties   #
# ------------------------- #


class fixedStar:
    """Properties of the fixed stars.

    The magnitude-to-orb mapping used to size a fixed star's orb.
    """

    pass


# ------------------------- #
#   House Sys. Properties   #
# ------------------------- #


class houseSystem:
    """Properties of the supported house systems.

    Groups the house-system constants (Placidus, Koch, Whole Sign, ...) by
    the characteristics that affect chart construction.
    """

    pass

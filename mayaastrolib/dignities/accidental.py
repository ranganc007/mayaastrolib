"""
This file is part of mayaastrolib, a fork of flatlib - (C) FlatAngle
Author: João Ventura (flatangleweb@gmail.com)


This module implements some utility functions for
handling the accidental dignities of an Astrology
Chart.

"""

from copy import copy

from mayaastrolib import angle, aspects, const, props
from mayaastrolib.dignities import essential
from mayaastrolib.tools.chartdynamics import ChartDynamics

# Relations with Sun
COMBUST = "Combust"
CAZIMI = "Cazimi"
UNDER_SUN = "Under the Sun"

# Light
LIGHT_AUGMENTING = "Augmenting Light"
LIGHT_DIMINISHING = "Diminishing Light"

# Orientality
ORIENTAL = "Oriental"
OCCIDENTAL = "Occidental"

# Haiz
HAIZ = "Haiz"
CHAIZ = "Contra-Haiz"


# === Base functions === #


def sunRelation(obj, sun):
    """Returns an object's relation with the sun."""
    if obj.id == const.SUN:
        return None
    dist = abs(angle.closestdistance(sun.lon, obj.lon))
    if dist < 0.2833:
        return CAZIMI
    elif dist < 8.0:
        return COMBUST
    elif dist < 16.0:
        return UNDER_SUN
    else:
        return None


def light(obj, sun):
    """Returns if an object is augmenting or diminishing light."""
    dist = angle.distance(sun.lon, obj.lon)
    faster = sun if sun.lonspeed > obj.lonspeed else obj
    if faster == sun:
        return LIGHT_DIMINISHING if dist < 180 else LIGHT_AUGMENTING
    else:
        return LIGHT_AUGMENTING if dist < 180 else LIGHT_DIMINISHING


def orientality(obj, sun):
    """Returns if an object is oriental or
    occidental to the sun.

    """
    dist = angle.distance(sun.lon, obj.lon)
    return OCCIDENTAL if dist < 180 else ORIENTAL


def viaCombusta(obj):
    """Returns if an object is in the Via Combusta."""
    return 195 < obj.lon < 225


def haiz(obj, chart):
    """Returns if an object is in Haiz."""
    objGender = obj.gender
    objFaction = obj.faction

    if obj.id == const.MERCURY:
        # Gender and faction of mercury depends on orientality
        sun = chart.getObject(const.SUN)
        orientalityM = orientality(obj, sun)
        if orientalityM == ORIENTAL:
            objGender = const.MASCULINE
            objFaction = const.DIURNAL
        else:
            objGender = const.FEMININE
            objFaction = const.NOCTURNAL

    # Object gender match sign gender?
    signGender = props.sign.gender[obj.sign]
    genderConformity = objGender == signGender

    # Match faction
    factionConformity = False
    diurnalChart = chart.isDiurnal()

    if obj.id == const.SUN and not diurnalChart:
        # Sun is in conformity only when above horizon
        factionConformity = False
    else:
        # Get list of houses in the chart's diurnal faction
        if diurnalChart:
            diurnalFaction = props.house.aboveHorizon
            nocturnalFaction = props.house.belowHorizon
        else:
            diurnalFaction = props.house.belowHorizon
            nocturnalFaction = props.house.aboveHorizon

        # Get the object's house and match factions
        objHouse = chart.houses.getObjectHouse(obj)
        if (
            objFaction == const.DIURNAL
            and objHouse.id in diurnalFaction
            or objFaction == const.NOCTURNAL
            and objHouse.id in nocturnalFaction
        ):
            factionConformity = True

    # Match things
    if genderConformity and factionConformity:
        return HAIZ
    elif not genderConformity and not factionConformity:
        return CHAIZ
    else:
        return None


# ---------------------------- #
#   Accidental Dignity Class   #
# ---------------------------- #

# House scores
HOUSE_SCORES = {
    const.HOUSE1: 5,
    const.HOUSE2: 3,
    const.HOUSE3: 1,
    const.HOUSE4: 4,
    const.HOUSE5: 3,
    const.HOUSE6: -3,
    const.HOUSE7: 4,
    const.HOUSE8: -4,
    const.HOUSE9: 2,
    const.HOUSE10: 5,
    const.HOUSE11: 4,
    const.HOUSE12: -5,
}


class AccidentalDignity:
    """This class provides methods to access the
    accidental dignities of an object in a Chart.

    """

    def __init__(self, obj, chart):
        self.obj = obj
        self.chart = chart
        self.dyn = ChartDynamics(chart)
        self.scoreProperties = None

    # === Houses === #

    def house(self):
        """Returns the object's house."""
        house = self.chart.houses.getObjectHouse(self.obj)
        return house

    def houseScore(self):
        """Returns the score of the object's house."""
        house = self.house()
        return HOUSE_SCORES[house.id]

    # === Relation with Sun === #

    def sunRelation(self):
        """Returns the relation of the object with the sun."""
        sun = self.chart.getObject(const.SUN)
        return sunRelation(self.obj, sun)

    def isCazimi(self):
        return self.sunRelation() == CAZIMI

    def isUnderSun(self):
        return self.sunRelation() == UNDER_SUN

    def isCombust(self):
        return self.sunRelation() == COMBUST

    def light(self):
        """Returns if object is augmenting or diminishing its
        light.

        """
        sun = self.chart.getObject(const.SUN)
        return light(self.obj, sun)

    def isAugmentingLight(self):
        return self.light() == LIGHT_AUGMENTING

    def orientality(self):
        """Returns the orientality of the object."""
        sun = self.chart.getObject(const.SUN)
        return orientality(self.obj, sun)

    def isOriental(self):
        return self.orientality() == ORIENTAL

    # === Joys === #

    def inHouseJoy(self):
        """Returns if the object is in its house of joy."""
        house = self.house()
        return props.object.houseJoy[self.obj.id] == house.id

    def inSignJoy(self):
        """Returns if the object is in its sign of joy."""
        return props.object.signJoy[self.obj.id] == self.obj.sign

    # === Mutual Receptions === #

    def reMutualReceptions(self):
        """Returns all mutual receptions with the object
        and other planets, indexed by planet ID.
        It only includes ruler and exaltation receptions.

        """
        planets = copy(const.LIST_SEVEN_PLANETS)
        planets.remove(self.obj.id)
        mrs = {}
        for ID in planets:
            mr = self.dyn.reMutualReceptions(self.obj.id, ID)
            if mr:
                mrs[ID] = mr
        return mrs

    def eqMutualReceptions(self):
        """Returns a list with mutual receptions with the
        object and other planets, when the reception is the
        same for both (both ruler or both exaltation).

        It basically return a list with every ruler-ruler and
        exalt-exalt mutual receptions

        """
        mrs = self.reMutualReceptions()
        res = []
        for _ID, receptions in mrs.items():
            for pair in receptions:
                if pair[0] == pair[1]:
                    res.append(pair[0])
        return res

    # === Aspects to benefics and malefics === #

    def __aspectLists(self, IDs, aspList):
        """Returns a list with the aspects that the object
        makes to the objects in IDs. It considers only
        conjunctions and other exact/applicative aspects
        if in aspList.

        """
        res = []

        for otherID in IDs:
            # Ignore same
            if otherID == self.obj.id:
                continue

            # Get aspects to the other object
            otherObj = self.chart.getObject(otherID)
            asp = aspects.getAspect(self.obj, otherObj, aspList)

            if asp is None:
                continue
            elif asp.type == const.CONJUNCTION:
                res.append(asp.type)
            else:
                # Only exact or applicative aspects
                movement = asp.movement
                if movement in [const.EXACT, const.APPLICATIVE]:
                    res.append(asp.type)

        return res

    def aspectBenefics(self):
        """Returns a list with the good aspects the object
        makes to the benefics.

        """
        benefics = [const.VENUS, const.JUPITER]
        return self.__aspectLists(benefics, aspList=[0, 60, 120])

    def aspectMalefics(self):
        """Returns a list with the bad aspects the object
        makes to the malefics.

        """
        malefics = [const.MARS, const.SATURN]
        return self.__aspectLists(malefics, aspList=[0, 90, 180])

    # == Application and Separation from benefics and malefics == #

    def __sepApp(self, IDs, aspList):
        """Returns true if the object last and next movement are
        separations and applications to objects in list IDs.
        It only considers aspects in aspList.

        This function is static since it does not test if the next
        application will be indeed perfected. It considers only
        a snapshot of the chart and not its astronomical movement.

        """
        sep, app = self.dyn.immediateAspects(self.obj.id, aspList)
        if sep is None or app is None:
            return False
        else:
            sepCondition = sep["id"] in IDs
            appCondition = app["id"] in IDs
            return sepCondition is True and appCondition is True

    def isAuxilied(self):
        """Returns if the object is separating and applying to
        a benefic considering good aspects.

        """
        benefics = [const.VENUS, const.JUPITER]
        return self.__sepApp(benefics, aspList=[0, 60, 120])

    def isSurrounded(self):
        """Returns if the object is separating and applying to
        a malefic considering bad aspects.

        """
        malefics = [const.MARS, const.SATURN]
        return self.__sepApp(malefics, aspList=[0, 90, 180])

    # === Aspects to Moon Nodes === #

    def isConjNorthNode(self):
        """Returns if object is conjunct north node."""
        node = self.chart.getObject(const.NORTH_NODE)
        return aspects.hasAspect(self.obj, node, aspList=[0])

    def isConjSouthNode(self):
        """Returns if object is conjunct south node."""
        node = self.chart.getObject(const.SOUTH_NODE)
        return aspects.hasAspect(self.obj, node, aspList=[0])

    # === Void of Course, Feral and Haiz === #

    def isVoc(self):
        """Return if the object is Void of Course."""
        return self.dyn.isVOC(self.obj.id)

    def isFeral(self):
        """Returns true if the object does not have any
        aspects.

        """
        planets = copy(const.LIST_SEVEN_PLANETS)
        planets.remove(self.obj.id)
        for otherID in planets:
            otherObj = self.chart.getObject(otherID)
            if aspects.hasAspect(self.obj, otherObj, const.MAJOR_ASPECTS):
                return False
        return True

    def haiz(self):
        """Returns the object haiz."""
        return haiz(self.obj, self.chart)

    # === Scores === #

    def getScoreProperties(self):
        """Returns the accidental dignity score of the object as a dict.

        The bulk of the rules are "+N if flag else 0" (or 0/−M), driven
        by the table below; the handful that need context (the Sun is
        excluded, a 3-way split, two interacting flags) are handled
        inline after the loop.
        """
        obj = self.obj
        score = {}

        # Peregrine, mutual receptions, house.
        score["peregrine"] = -5 if essential.isPeregrine(obj.id, obj.sign, obj.signlon) else 0
        mr = self.eqMutualReceptions()
        score["mr_ruler"] = +5 if "ruler" in mr else 0
        score["mr_exalt"] = +4 if "exalt" in mr else 0
        score["house"] = self.houseScore()

        # Simple flag rules: (key, flag, plus_if_true, value_if_false).
        aspBen = self.aspectBenefics()
        aspMal = self.aspectMalefics()
        simple_rules = (
            ("joy_sign", self.inSignJoy(), +3, 0),
            ("joy_house", self.inHouseJoy(), +2, 0),
            ("cazimi", self.isCazimi(), +5, 0),
            ("combust", self.isCombust(), -6, 0),
            ("under_sun", self.isUnderSun(), -4, 0),
            ("north_node", self.isConjNorthNode(), -3, 0),
            ("south_node", self.isConjSouthNode(), -5, 0),
            ("benefic_asp0", const.CONJUNCTION in aspBen, +5, 0),
            ("benefic_asp120", const.TRINE in aspBen, +4, 0),
            ("benefic_asp60", const.SEXTILE in aspBen, +3, 0),
            ("malefic_asp0", const.CONJUNCTION in aspMal, -5, 0),
            ("malefic_asp180", const.OPPOSITION in aspMal, -4, 0),
            ("malefic_asp90", const.SQUARE in aspMal, -3, 0),
            ("auxilied", self.isAuxilied(), +5, 0),
            ("surround", self.isSurrounded(), -5, 0),
        )
        for key, flag, plus, otherwise in simple_rules:
            score[key] = plus if flag else otherwise

        # Context-dependent rules.

        # Not "under the sun beams" — only meaningful for non-Sun bodies.
        score["no_under_sun"] = +5 if (obj.id != const.SUN and not self.sunRelation()) else 0

        # Light — the Sun has no "light" of its own.
        if obj.id == const.SUN:
            score["light"] = 0
        else:
            score["light"] = +1 if self.isAugmentingLight() else -1

        # Orientality — diurnal planets favour the east, nocturnal the west.
        if obj.id in (const.SATURN, const.JUPITER, const.MARS):
            score["orientality"] = +2 if self.isOriental() else -2
        elif obj.id in (const.VENUS, const.MERCURY, const.MOON):
            score["orientality"] = -2 if self.isOriental() else +2
        else:
            score["orientality"] = 0

        # Direction and speed — the luminaries are never retrograde.
        if obj.id in (const.SUN, const.MOON):
            score["direction"] = 0
        else:
            score["direction"] = +4 if obj.isDirect() else -5
        score["speed"] = +2 if obj.isFast() else -2

        # Feral and void — "void of course" only counts if not also feral.
        score["feral"] = -3 if self.isFeral() else 0
        score["void"] = -2 if (self.isVoc() and score["feral"] == 0) else 0

        # Haiz — three-way (haiz / contra-haiz / neither).
        haiz = self.haiz()
        score["haiz"] = +3 if haiz == HAIZ else (-2 if haiz == CHAIZ else 0)

        # Moon in the Via Combusta.
        score["viacombusta"] = -2 if (obj.id == const.MOON and viaCombusta(obj)) else 0

        return score

    def getActiveProperties(self):
        """Returns the non-zero accidental dignities."""
        score = self.getScoreProperties()
        return {key: value for (key, value) in score.items() if value != 0}

    def score(self):
        """Returns the sum of the accidental dignities
        score.

        """
        if not self.scoreProperties:
            self.scoreProperties = self.getScoreProperties()
        return sum(self.scoreProperties.values())

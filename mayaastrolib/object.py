"""
This file is part of flatlib - (C) FlatAngle
Author: João Ventura (flatangleweb@gmail.com)


This module implements classes to represent
Astrology objects, such as planets, Houses
and Fixed-Stars.

"""

import warnings

from . import angle, const, props, utils
from ._compat import property_with_method_compat

# ------------------ #
#   Generic Object   #
# ------------------ #


class GenericObject:
    """This class represents a generic object and
    includes properties which are common to all
    objects on a chart.

    """

    def __init__(self):
        self.id = const.NO_PLANET
        self.type = const.OBJ_GENERIC
        self.lon = 0.0
        self.lat = 0.0
        self.sign = const.ARIES
        self.signlon = 0.0

    @classmethod
    def fromDict(cls, _dict):
        """Builds instance from dictionary of properties."""
        obj = cls()
        obj.__dict__.update(_dict)
        return obj

    def copy(self):
        """Returns a deep copy of this object."""
        return self.fromDict(self.__dict__)

    def __str__(self):
        return "<%s %s %s>" % (self.id, self.sign, angle.toString(self.signlon))

    # === Properties === #

    @property_with_method_compat
    def orb(self):
        """Returns the orb of this object."""
        return -1.0

    def isPlanet(self):
        """Returns if this object is a planet."""
        return self.type == const.OBJ_PLANET

    def eqCoords(self, zerolat=False):
        """Returns the Equatorial Coordinates of this object.
        Receives a boolean parameter to consider a zero latitude.

        """
        lat = 0.0 if zerolat else self.lat
        return utils.eqCoords(self.lon, lat)

    # === Functions === #

    def with_longitude(self, lon, *, preserve_speed=False):
        """Return a new object instance at the given longitude.

        This is a coordinate transform — it does NOT recompute orbital
        state from ephemeris.

        On :class:`Object` subclasses (which carry ``lonspeed`` /
        ``latspeed``), the default behaviour clears those speeds to
        ``None``, signalling that orbital dynamics are undefined for the
        new position. Methods that depend on speed
        (``movement`` / ``isRetrograde`` / ``isFast``) return ``None``
        for such objects. Pass ``preserve_speed=True`` when the new
        position meaningfully shares dynamics with the original — for
        example, antiscia, where the reflected point moves with the
        original planet.

        On :class:`GenericObject`, :class:`House`, and :class:`FixedStar`
        (no speed attributes), ``preserve_speed`` has no effect.

        Args:
            lon: New longitude in degrees. Normalised to [0, 360).
            preserve_speed: If True, keep original ``lonspeed`` /
                ``latspeed``. Defaults to False.

        Returns:
            A new instance of the same class. The original is not
            modified.
        """
        new = self.copy()
        new.lon = angle.norm(lon)
        new.signlon = new.lon % 30
        new.sign = const.LIST_SIGNS[int(new.lon / 30.0)]
        if not preserve_speed:
            if hasattr(new, "lonspeed"):
                new.lonspeed = None
            if hasattr(new, "latspeed"):
                new.latspeed = None
        return new

    def relocate(self, lon):
        """[DEPRECATED] In-place relocate. Use ``with_longitude(lon)`` instead.

        ``relocate()`` mutates ``lon`` / ``signlon`` / ``sign`` but
        leaves any ``lonspeed`` / ``latspeed`` attributes stale, which
        causes downstream code to read the original object's speed
        even though the new position is symbolic. For antiscia, use
        :meth:`antiscion` / :meth:`cantiscion`. For arbitrary
        repositioning, use :meth:`with_longitude`. Will be removed in
        version 1.0.
        """
        warnings.warn(
            "Object.relocate(lon) mutates in place and leaves speed "
            "attributes stale, which causes is_retrograde() and movement "
            "to return wrong answers. Use obj.with_longitude(lon) for a "
            "new Object, or obj.antiscion() / obj.cantiscion() for "
            "reflection. Will be removed in version 1.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.lon = angle.norm(lon)
        self.signlon = self.lon % 30
        self.sign = const.LIST_SIGNS[int(self.lon / 30.0)]

    def antiscion(self):
        """Return the antiscion of this object — a new instance reflected
        across the 0° Cancer / 0° Capricorn axis.

        Antiscia preserve dynamics: the reflected point moves with the
        original planet. The returned object has the same speed
        attributes as ``self``.
        """
        new = self.with_longitude(360 - self.lon + 180, preserve_speed=True)
        new.type = const.OBJ_GENERIC
        return new

    def cantiscion(self):
        """Return the contra-antiscion of this object — a new instance
        reflected across the 0° Aries / 0° Libra axis.

        See :meth:`antiscion` for semantics. Cantiscia preserve dynamics.
        """
        new = self.with_longitude(360 - self.lon, preserve_speed=True)
        new.type = const.OBJ_GENERIC
        return new

    def antiscia(self):
        """[DEPRECATED] Use :meth:`antiscion` instead.

        Returns the same antiscion object. Will be removed in 1.0.
        """
        warnings.warn(
            "Object.antiscia() is deprecated. Use obj.antiscion() instead. "
            "Will be removed in version 1.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.antiscion()

    def cantiscia(self):
        """[DEPRECATED] Use :meth:`cantiscion` instead.

        Returns the same cantiscion object. Will be removed in 1.0.
        """
        warnings.warn(
            "Object.cantiscia() is deprecated. Use obj.cantiscion() instead. "
            "Will be removed in version 1.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.cantiscion()


# -------------------- #
#   Astrology Object   #
# -------------------- #


class Object(GenericObject):
    """This class represents an Astrology object, such
    as the sun or the moon, and includes properties and
    functions which are common for all objects.

    """

    def __init__(self):
        super().__init__()
        self.type = const.OBJ_PLANET
        self.lonspeed = 0.0
        self.latspeed = 0.0

    def __str__(self):
        string = super().__str__()[:-1]
        speed = "—" if self.lonspeed is None else angle.toString(self.lonspeed)
        return "%s %s>" % (string, speed)

    # === Properties === #

    @property_with_method_compat
    def orb(self):
        """Returns the orb of this object."""
        return props.object.orb[self.id]

    @property_with_method_compat
    def meanMotion(self):
        """Returns the mean daily motion of this object."""
        return props.object.meanMotion[self.id]

    @property_with_method_compat
    def movement(self):
        """Returns if this object is direct, retrograde or stationary.

        Returns ``None`` for symbolic positions where ``lonspeed`` is
        undefined (e.g. profected planets — see
        :meth:`mayaastrolib.chart.Chart.profected`). The
        ``property_with_method_compat`` wrapper passes ``None`` through
        unwrapped so ``obj.movement is None`` works.
        """
        if self.lonspeed is None:
            return None
        if abs(self.lonspeed) < 0.0003:
            return const.STATIONARY
        elif self.lonspeed > 0:
            return const.DIRECT
        else:
            return const.RETROGRADE

    @property_with_method_compat
    def gender(self):
        """Returns the gender of this object."""
        return props.object.gender[self.id]

    @property_with_method_compat
    def faction(self):
        """Returns the faction of this object."""
        return props.object.faction[self.id]

    @property_with_method_compat
    def element(self):
        """Returns the element of this object."""
        return props.object.element[self.id]

    # === Functions === #

    def isDirect(self):
        """Returns if this object is in direct motion, or ``None`` for
        symbolic positions with undefined speed.
        """
        if self.lonspeed is None:
            return None
        return self.movement == const.DIRECT

    def isRetrograde(self):
        """Returns if this object is in retrograde motion, or ``None``
        for symbolic positions with undefined speed.
        """
        if self.lonspeed is None:
            return None
        return self.movement == const.RETROGRADE

    def isStationary(self):
        """Returns if this object is stationary, or ``None`` for
        symbolic positions with undefined speed.
        """
        if self.lonspeed is None:
            return None
        return self.movement == const.STATIONARY

    def isFast(self):
        """Returns if this object is in fast motion.

        Returns ``None`` for symbolic positions where ``lonspeed`` is
        undefined.
        """
        if self.lonspeed is None:
            return None
        return abs(self.lonspeed) >= self.meanMotion


# ------------------ #
#     House Cusp     #
# ------------------ #


class House(GenericObject):
    """A house cusp.

    The class implements the traditional **5° rule** in
    :meth:`inHouse` and :meth:`hasObject`: a longitude within 5°
    *before* a cusp is considered to belong to the house starting
    *at* that cusp, not the previous house. This is a long-standing
    convention in Hellenistic, Medieval, and modern Western
    astrology — the rationale being that house influences "come
    early" relative to their nominal cusps.

    See :data:`_CUSP_TOLERANCE_DEG`. Configurability is recorded as
    a Phase 2 IDEA in `docs/IDEAS.md` (`Item 15`); the 5° default
    is hard-coded for now because the design surface (per-chart,
    per-house, per-house-system?) is not yet settled.
    """

    # Degrees a longitude may precede a cusp and still count as
    # belonging to the house starting at that cusp. See class
    # docstring. Negative because the math in `inHouse` adds it to
    # `self.lon` to shift the comparison anchor 5° earlier.
    _CUSP_TOLERANCE_DEG = -5.0
    # Backwards-compatible alias kept for any external caller that
    # learned the old name. Slated for removal in 1.0.
    _OFFSET = _CUSP_TOLERANCE_DEG

    def __init__(self):
        super().__init__()
        self.type = const.OBJ_HOUSE
        self.size = 30.0
        # Cached at construction in fromDict() via _set_num_from_id().
        # Initialised to 0 so attribute access never raises before id is set.
        self._num = 0

    @classmethod
    def fromDict(cls, _dict):
        """Build a House and cache its number from the id."""
        obj = super().fromDict(_dict)
        obj._set_num_from_id()
        return obj

    def _set_num_from_id(self):
        """Resolve self._num via list lookup so we don't parse the id string.

        Falls back to 0 if the id isn't a recognised house — defensive
        against future id-format changes or mislabelled houses.
        """
        try:
            self._num = const.LIST_HOUSES.index(self.id) + 1
        except ValueError:
            self._num = 0

    def __str__(self):
        string = super().__str__()[:-1]
        return "%s %s>" % (string, self.size)

    # === Properties === #

    @property_with_method_compat
    def num(self):
        """Returns the number of this house [1..12].

        Resolved via :data:`mayaastrolib.const.LIST_HOUSES` once at
        construction (see :meth:`fromDict`) and cached on
        ``self._num``. No string parsing at access time.
        """
        return self._num

    @property_with_method_compat
    def condition(self):
        """Returns the condition of this house.
        The house can be angular, succedent or cadent.

        """
        return props.house.condition[self.id]

    @property_with_method_compat
    def gender(self):
        """Returns the gender of this house."""
        return props.house.gender[self.id]

    # === Functions === #

    def isAboveHorizon(self):
        """Returns true if this house is above horizon."""
        return self.id in props.house.aboveHorizon

    def inHouse(self, lon):
        """Return True if the longitude ``lon`` falls inside this house.

        The house is taken to span ``[cusp − 5°, cusp + 25°)`` — i.e.
        it includes the 5° band immediately before its named cusp,
        per the traditional 5° rule. See the class docstring.
        """
        dist = angle.distance(self.lon + House._CUSP_TOLERANCE_DEG, lon)
        return dist < self.size

    def hasObject(self, obj):
        """Returns true if an object is in this house."""
        return self.inHouse(obj.lon)


# ------------------ #
#     Fixed Star     #
# ------------------ #


class FixedStar(GenericObject):
    """This class represents a generic fixed star."""

    def __init__(self):
        super().__init__()
        self.type = const.OBJ_FIXED_STAR
        self.mag = 0.0

    def __str__(self):
        string = super().__str__()[:-1]
        return "%s %s>" % (string, self.mag)

    # === Properties === #

    # Map magnitudes to orbs
    _ORBS = [[2, 7.5], [3, 5.5], [4, 3.5], [5, 1.5]]

    @property_with_method_compat
    def orb(self):
        """Returns the orb of this fixed star."""
        for mag, orb in FixedStar._ORBS:
            if self.mag < mag:
                return orb
        return 0.5

    # === Functions === #

    def aspects(self, obj):
        """Returns true if this star aspects another object.
        Fixed stars only aspect by conjunctions.

        """
        dist = angle.closestdistance(self.lon, obj.lon)
        return abs(dist) < self.orb

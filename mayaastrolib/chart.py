"""
This file is part of flatlib - (C) FlatAngle
Author: João Ventura (flatangleweb@gmail.com)


This module implements a class to represent an
astrology Chart. It provides methods to handle
the chart, as well as three relevant properties:

- objects: a list with the chart's objects
- houses: a list with the chart's houses
- angles: a list with the chart's angles

Since houses 1 and 10 may not match the Asc and
MC in some house systems, the Chart class
includes the list of angles. The angles should be
used when you want to deal with angle's longitudes.

There are also methods to access fixed stars.

"""

import copy as _copy
import math

from . import angle, const, utils
from .datetime import Datetime
from .ephem import ephem
from .lists import GenericList, HouseList, ObjectList

# ------------------ #
#    Chart Class     #
# ------------------ #


class Chart:
    """This class represents an astrology chart."""

    def __init__(self, date, pos, **kwargs):
        """Creates an astrology chart for a given
        date and location.

        Optional arguments are:
        - hsys: house system
        - IDs: list of objects to include
        - is_symbolic: True if this chart represents derived/symbolic
          positions (e.g. profections). Default False.
        - symbolic_kind: a string identifying the kind of symbolic
          chart, e.g. ``"profection"``. Default None. Only meaningful
          when ``is_symbolic=True``.

        """
        # Handle optional arguments
        hsys = kwargs.get("hsys", const.HOUSES_DEFAULT)
        IDs = kwargs.get("IDs", const.LIST_OBJECTS_TRADITIONAL)

        self.date = date
        self.pos = pos
        self.hsys = hsys
        self.is_symbolic = kwargs.get("is_symbolic", False)
        self.symbolic_kind = kwargs.get("symbolic_kind", None)
        self.objects = ephem.getObjectList(IDs, date, pos)
        self.houses, self.angles = ephem.getHouses(date, pos, hsys)
        self._link_objects_to_houses()

    def __repr__(self):
        if self.is_symbolic:
            return f"<{type(self).__name__} ({self.symbolic_kind}) {self.date}>"
        return f"<{type(self).__name__} {self.date}>"

    def _link_objects_to_houses(self):
        """Stamp `obj.house` on every Object and `house.objects` on every House.

        Uses HouseList.getObjectHouse, which iterates the houses and returns
        the first whose `inHouse(obj.lon)` is true. Defensive fallback to
        None if no house matches (shouldn't happen in normal house systems
        but allows for fixed-stars or angle objects whose membership is not
        meaningful).
        """
        for obj in self.objects:
            obj.house = self.houses.getObjectHouse(obj)
        for house in self.houses:
            house.objects = [o for o in self.objects if o.house is house]

    def copy(self):
        """Returns a deep copy of this chart."""
        chart = Chart.__new__(Chart)
        chart.date = self.date
        chart.pos = self.pos
        chart.hsys = self.hsys
        chart.is_symbolic = getattr(self, "is_symbolic", False)
        chart.symbolic_kind = getattr(self, "symbolic_kind", None)
        chart.objects = self.objects.copy()
        chart.houses = self.houses.copy()
        chart.angles = self.angles.copy()
        return chart

    # === Properties === #

    def getObject(self, ID):
        """Returns an object from the chart."""
        return self.objects.get(ID)

    def getHouse(self, ID):
        """Returns an house from the chart."""
        return self.houses.get(ID)

    def getAngle(self, ID):
        """Returns an angle from the chart."""
        return self.angles.get(ID)

    def get(self, ID):
        """Returns an object, house or angle
        from the chart.

        """
        if ID.startswith("House"):
            return self.getHouse(ID)
        elif ID in const.LIST_ANGLES:
            return self.getAngle(ID)
        else:
            return self.getObject(ID)

    def houseOf(self, obj):
        """Return the House containing obj, or None if obj is not in any house.

        Equivalent to ``obj.house``, provided for callers who have the chart
        but only the object's id.

        Args:
            obj: An Object instance, or a planet ID string (e.g. const.SUN).

        Returns:
            The House instance, or None.
        """
        if isinstance(obj, str):
            try:
                obj = self.getObject(obj)
            except KeyError:
                return None
            if obj is None:
                return None
        return getattr(obj, "house", None)

    def objectsInHouse(self, house_id):
        """Return the list of Objects in the named house.

        Args:
            house_id: A house ID string (e.g. const.HOUSE5).

        Returns:
            List of Object instances, possibly empty.
        """
        try:
            house = self.getHouse(house_id)
        except KeyError:
            return []
        if house is None:
            return []
        return list(house.objects)

    # === Fixed stars === #

    # The computation of fixed stars is inefficient,
    # so the access must be made directly to the
    # ephemeris only when needed.

    def getFixedStar(self, ID):
        """Returns a fixed star from the ephemeris."""
        return ephem.getFixedStar(ID, self.date)

    def getFixedStars(self):
        """Returns a list with all fixed stars."""
        IDs = const.LIST_FIXED_STARS
        return ephem.getFixedStarList(IDs, self.date)

    # === Houses and angles === #

    def isHouse1Asc(self):
        """Returns true if House1 is the same as the Asc."""
        house1 = self.getHouse(const.HOUSE1)
        asc = self.getAngle(const.ASC)
        dist = angle.closestdistance(house1.lon, asc.lon)
        return abs(dist) < 0.0003  # 1 arc-second

    def isHouse10MC(self):
        """Returns true if House10 is the same as the MC."""
        house10 = self.getHouse(const.HOUSE10)
        mc = self.getAngle(const.MC)
        dist = angle.closestdistance(house10.lon, mc.lon)
        return abs(dist) < 0.0003  # 1 arc-second

    # === Other properties === #

    def isDiurnal(self):
        """Returns true if this chart is diurnal."""
        sun = self.getObject(const.SUN)
        mc = self.getAngle(const.MC)

        # Get ecliptical positions and check if the
        # sun is above the horizon.
        lat = self.pos.lat
        sunRA, sunDecl = utils.eqCoords(sun.lon, sun.lat)
        mcRA, mcDecl = utils.eqCoords(mc.lon, 0)
        return utils.isAboveHorizon(sunRA, sunDecl, mcRA, lat)

    def getMoonPhase(self):
        """Returns the phase of the moon."""
        sun = self.getObject(const.SUN)
        moon = self.getObject(const.MOON)
        dist = angle.distance(sun.lon, moon.lon)
        if dist < 90:
            return const.MOON_FIRST_QUARTER
        elif dist < 180:
            return const.MOON_SECOND_QUARTER
        elif dist < 270:
            return const.MOON_THIRD_QUARTER
        else:
            return const.MOON_LAST_QUARTER

    # === Symbolic charts === #

    def _copy_for_symbolic(self, symbolic_kind):
        """Return a deep-copied chart with the symbolic flag set.

        Internal helper for :meth:`profected` and any future symbolic
        derivatives. Uses ``copy.deepcopy`` so callers can mutate the
        returned chart's objects/houses/angles without aliasing into
        the natal.
        """
        new = _copy.deepcopy(self)
        new.is_symbolic = True
        new.symbolic_kind = symbolic_kind
        return new

    def _years_to(self, target_date):
        """Return the rotation angle (degrees) for a profection from
        ``self.date`` to ``target_date``.

        Combines integer years (30° each) with the fractional sub-year
        rotation, mirroring the existing
        :func:`mayaastrolib.predictives.profections.compute` math so
        that ``Chart.profected(target_date=...)`` produces identical
        longitudes to the legacy API.
        """
        sun = self.getObject(const.SUN)
        prevSr = ephem.prevSolarReturn(target_date, sun.lon)
        nextSr = ephem.nextSolarReturn(target_date, sun.lon)
        sub_year = 30 * (target_date.jd - prevSr.jd) / (nextSr.jd - prevSr.jd)
        age = math.floor((target_date.jd - self.date.jd) / 365.25)
        return 30 * age + sub_year

    def profected(self, years=None, target_date=None):
        """Return a profected chart — natal positions rotated forward by
        one sign per year of age.

        Profections are a symbolic predictive technique. The returned
        chart's planetary positions do NOT represent where the planets
        actually are at the target date — they are natal positions
        rotated by N×30°. Therefore, dynamics-derived attributes like
        ``obj.movement`` and ``obj.isRetrograde()`` return ``None`` for
        the profected chart's planets.

        Args:
            years: Age in whole or fractional years. The profected chart
                rotates by ``years × 30°`` modulo 360. Mutually
                exclusive with ``target_date``.
            target_date: A :class:`Datetime`. The rotation is derived
                using the same math as
                :func:`mayaastrolib.predictives.profections.compute`,
                including the sub-year solar-return interpolation.
                Mutually exclusive with ``years``.

        Returns:
            A new :class:`Chart` with ``is_symbolic=True`` and
            ``symbolic_kind="profection"``. Planet ``lonspeed`` and
            ``latspeed`` are ``None``.

        Raises:
            ValueError: if both ``years`` and ``target_date`` are
                provided, or neither is.
        """
        if (years is None) == (target_date is None):
            raise ValueError(
                "Pass exactly one of years= or target_date=",
            )
        if target_date is not None:
            rotation = self._years_to(target_date)
        else:
            rotation = (years % 12) * 30

        new = self._copy_for_symbolic(symbolic_kind="profection")
        new.objects = ObjectList([obj.with_longitude(obj.lon + rotation) for obj in new.objects])
        new.houses = HouseList([house.with_longitude(house.lon + rotation) for house in new.houses])
        new.angles = GenericList([a.with_longitude(a.lon + rotation) for a in new.angles])
        new._link_objects_to_houses()
        return new

    # === Solar returns === #

    def solarReturn(self, year):
        """Returns this chart's solar return for a
        given year.

        """
        sun = self.getObject(const.SUN)
        date = Datetime(f"{year}/01/01", "00:00", self.date.utcoffset)
        srDate = ephem.nextSolarReturn(date, sun.lon)
        return Chart(srDate, self.pos, hsys=self.hsys)

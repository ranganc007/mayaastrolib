"""
This file is part of mayaastrolib, a fork of flatlib - (C) FlatAngle
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

from __future__ import annotations

import copy as _copy
import math
from typing import TYPE_CHECKING, Any

from . import angle, const, utils
from .datetime import Datetime
from .ephem import ephem
from .lists import GenericList, HouseList, ObjectList

if TYPE_CHECKING:
    from .geopos import GeoPos
    from .object import FixedStar, GenericObject, House, Object
    from .predictives.primarydirections import PrimaryDirections
    from .tools.planetarytime import HourTable

# ------------------ #
#    Chart Class     #
# ------------------ #


class Chart:
    """This class represents an astrology chart."""

    date: Datetime
    pos: GeoPos
    hsys: str
    zodiac: str
    ayanamsa: str
    is_symbolic: bool
    symbolic_kind: str | None
    objects: ObjectList
    houses: HouseList
    angles: GenericList

    def __init__(self, date: Datetime, pos: GeoPos, **kwargs: Any) -> None:
        """Creates an astrology chart for a given
        date and location.

        Optional arguments are:
        - hsys: house system
        - IDs: list of objects to include
        - zodiac: ``const.ZODIAC_TROPICAL`` (default) or
          ``const.ZODIAC_SIDEREAL``. When sidereal, longitudes are
          shifted by the chosen ayanamsa.
        - ayanamsa: One of ``const.LIST_AYANAMSAS``. Used only when
          ``zodiac=ZODIAC_SIDEREAL``. Default ``AYANAMSA_LAHIRI``.
        - is_symbolic: True if this chart represents derived/symbolic
          positions (e.g. profections). Default False.
        - symbolic_kind: a string identifying the kind of symbolic
          chart, e.g. ``"profection"``. Default None. Only meaningful
          when ``is_symbolic=True``.

        """
        # Handle optional arguments
        hsys = kwargs.get("hsys", const.HOUSES_DEFAULT)
        IDs = kwargs.get("IDs", const.LIST_OBJECTS_TRADITIONAL)
        zodiac = kwargs.get("zodiac", const.ZODIAC_TROPICAL)
        ayanamsa = kwargs.get("ayanamsa", const.AYANAMSA_LAHIRI)

        if zodiac not in const.LIST_ZODIACS:
            raise ValueError(f"Unknown zodiac {zodiac!r}; supported: {const.LIST_ZODIACS}")
        if ayanamsa not in const.LIST_AYANAMSAS:
            raise ValueError(f"Unknown ayanamsa {ayanamsa!r}; supported: {const.LIST_AYANAMSAS}")

        self.date = date
        self.pos = pos
        self.hsys = hsys
        self.zodiac = zodiac
        self.ayanamsa = ayanamsa
        self.is_symbolic = kwargs.get("is_symbolic", False)
        self.symbolic_kind = kwargs.get("symbolic_kind", None)
        self.objects = ephem.getObjectList(
            IDs,
            date,
            pos,
            zodiac=zodiac,
            ayanamsa=ayanamsa,
        )
        self.houses, self.angles = ephem.getHouses(
            date,
            pos,
            hsys,
            zodiac=zodiac,
            ayanamsa=ayanamsa,
        )
        self._link_objects_to_houses()

    def __repr__(self) -> str:
        if self.is_symbolic:
            return f"<{type(self).__name__} ({self.symbolic_kind}) {self.date}>"
        return f"<{type(self).__name__} {self.date}>"

    def _link_objects_to_houses(self) -> None:
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

    def copy(self) -> Chart:
        """Returns a deep copy of this chart."""
        chart = Chart.__new__(Chart)
        chart.date = self.date
        chart.pos = self.pos
        chart.hsys = self.hsys
        chart.zodiac = getattr(self, "zodiac", const.ZODIAC_TROPICAL)
        chart.ayanamsa = getattr(self, "ayanamsa", const.AYANAMSA_LAHIRI)
        chart.is_symbolic = getattr(self, "is_symbolic", False)
        chart.symbolic_kind = getattr(self, "symbolic_kind", None)
        chart.objects = self.objects.copy()
        chart.houses = self.houses.copy()
        chart.angles = self.angles.copy()
        return chart

    # === Properties === #

    def getObject(self, ID: str) -> Object:
        """Returns an object from the chart."""
        return self.objects.get(ID)

    def getHouse(self, ID: str) -> House:
        """Returns an house from the chart."""
        return self.houses.get(ID)

    def getAngle(self, ID: str) -> GenericObject:
        """Returns an angle from the chart."""
        return self.angles.get(ID)

    def get(self, ID: str) -> GenericObject:
        """Return the object, house, or angle with the given ID.

        Dispatches by list membership against the canonical lists in
        :mod:`mayaastrolib.const` rather than by string-prefix matching,
        so future ID format changes (e.g. ``"House1"`` → ``"H1"``) only
        require updating the list, not the dispatch.

        Args:
            ID: An ID string from ``const.LIST_HOUSES``,
                ``const.LIST_ANGLES``, or any object ID.

        Returns:
            The matching House, angle, or Object.
        """
        if ID in const.LIST_HOUSES:
            return self.getHouse(ID)
        if ID in const.LIST_ANGLES:
            return self.getAngle(ID)
        return self.getObject(ID)

    def houseOf(self, obj: GenericObject | str) -> House | None:
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

    def objectsInHouse(self, house_id: str) -> list[Object]:
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

    def getFixedStar(self, ID: str) -> FixedStar:
        """Returns a fixed star from the ephemeris."""
        return ephem.getFixedStar(ID, self.date)

    def getFixedStars(self) -> Any:
        """Returns a list with all fixed stars."""
        IDs = const.LIST_FIXED_STARS
        return ephem.getFixedStarList(IDs, self.date)

    # === Houses and angles === #

    def isHouse1Asc(self) -> bool:
        """Returns true if House1 is the same as the Asc."""
        house1 = self.getHouse(const.HOUSE1)
        asc = self.getAngle(const.ASC)
        dist = angle.closestdistance(house1.lon, asc.lon)
        return abs(dist) < 0.0003  # 1 arc-second

    def isHouse10MC(self) -> bool:
        """Returns true if House10 is the same as the MC."""
        house10 = self.getHouse(const.HOUSE10)
        mc = self.getAngle(const.MC)
        dist = angle.closestdistance(house10.lon, mc.lon)
        return abs(dist) < 0.0003  # 1 arc-second

    # === Other properties === #

    def isDiurnal(self) -> bool:
        """Returns true if this chart is diurnal."""
        sun = self.getObject(const.SUN)
        mc = self.getAngle(const.MC)

        # Get ecliptical positions and check if the
        # sun is above the horizon.
        lat = self.pos.lat
        sunRA, sunDecl = utils.eqCoords(sun.lon, sun.lat)
        mcRA, mcDecl = utils.eqCoords(mc.lon, 0)
        return utils.isAboveHorizon(sunRA, sunDecl, mcRA, lat)

    def getMoonPhase(self) -> str:
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

    def _copy_for_symbolic(self, symbolic_kind: str) -> Chart:
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

    def _years_to(self, target_date: Datetime) -> float:
        """Return the rotation angle (degrees) for a profection from
        ``self.date`` to ``target_date``.

        Combines integer years (30° each) with the fractional sub-year
        rotation, mirroring the existing
        :func:`mayaastrolib.predictives.profections.compute` math so
        that ``Chart.profected(target_date=...)`` produces identical
        longitudes to the legacy API.
        """
        sun = self.getObject(const.SUN)
        prevSr = ephem.prevSolarReturn(
            target_date,
            sun.lon,
            zodiac=self.zodiac,
            ayanamsa=self.ayanamsa,
        )
        nextSr = ephem.nextSolarReturn(
            target_date,
            sun.lon,
            zodiac=self.zodiac,
            ayanamsa=self.ayanamsa,
        )
        sub_year = 30 * (target_date.jd - prevSr.jd) / (nextSr.jd - prevSr.jd)
        age = math.floor((target_date.jd - self.date.jd) / 365.25)
        return 30 * age + sub_year

    def profected(self, years: float | None = None, target_date: Datetime | None = None) -> Chart:
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
            assert years is not None  # guaranteed by the exactly-one check above
            rotation = (years % 12) * 30

        new = self._copy_for_symbolic(symbolic_kind="profection")
        new.objects = ObjectList([obj.with_longitude(obj.lon + rotation) for obj in new.objects])
        new.houses = HouseList([house.with_longitude(house.lon + rotation) for house in new.houses])
        new.angles = GenericList([a.with_longitude(a.lon + rotation) for a in new.angles])
        new._link_objects_to_houses()
        return new

    # === Solar returns === #

    def solarReturn(self, year: int | None = None, target_date: Datetime | None = None) -> Chart:
        """Return this chart's solar return for a calendar year or near a date.

        A solar return is a real chart computed from ephemeris for the
        moment the Sun returns to its natal longitude. Unlike a profected
        chart it is *not* symbolic — the planets carry real speeds and
        dynamics.

        Two modes, mutually exclusive:

        - ``year=N``: anchors at January 1, 00:00 of ``year`` (in this
          chart's UTC offset) and walks forward to the first Sun
          conjunction. Each calendar year contains exactly one such
          moment, so this is equivalent to "the birthday-equivalent
          moment in ``year``" for any natal date. Verified concretely
          in ``docs/AUDIT-INVESTIGATIONS.md`` (Item 16).
        - ``target_date=D``: walks forward from ``D`` to the next Sun
          conjunction. Useful when you want the SR active at a known
          moment without computing the year yourself.

        Args:
            year: The calendar year in which the solar return falls.
            target_date: A :class:`Datetime` to search forward from.

        Returns:
            A new :class:`Chart` for the SR moment.
            ``is_symbolic`` is ``False``.

        Raises:
            ValueError: if both ``year`` and ``target_date`` are passed,
                or neither.
        """
        if (year is None) == (target_date is None):
            raise ValueError("Pass exactly one of year= or target_date=")
        sun = self.getObject(const.SUN)
        if year is not None:
            anchor = Datetime(f"{year}/01/01", "00:00", self.date.utcoffset)
        else:
            assert target_date is not None  # guaranteed by the exactly-one check above
            anchor = target_date
        srDate = ephem.nextSolarReturn(
            anchor,
            sun.lon,
            zodiac=self.zodiac,
            ayanamsa=self.ayanamsa,
        )
        return Chart(
            srDate,
            self.pos,
            hsys=self.hsys,
            zodiac=self.zodiac,
            ayanamsa=self.ayanamsa,
        )

    # === Other predictives and tools (Task 013) === #

    def directions(self) -> PrimaryDirections:
        """Return a :class:`PrimaryDirections` instance for this chart.

        Primary directions are a symbolic predictive technique mapping
        natal angular relationships forward through time via the
        semi-arc method. The returned object exposes methods for
        computing specific directions and timing tables.

        Direct instantiation via
        :class:`mayaastrolib.predictives.primarydirections.PrimaryDirections`
        remains supported and is *not* deprecated; this method is
        purely a discoverable Chart-level entry point. Use whichever
        reads better at the call site.

        Returns:
            A :class:`PrimaryDirections` instance.

        Raises:
            NotImplementedError: if this chart is sidereal. Primary
                directions are an equatorial-coordinate technique and
                the conversion goes through ecliptic longitude; on a
                sidereal chart the longitudes carry the ayanamsa shift,
                which would corrupt the right-ascension values. Build
                the chart with the default (tropical) zodiac for
                directions. (Primary directions are also not a Vedic
                technique, so this is rarely wanted on a sidereal chart.)
        """
        if self.zodiac == const.ZODIAC_SIDEREAL:
            raise NotImplementedError(
                "Primary directions require tropical (equatorial-derived) "
                "coordinates; this chart is sidereal. Rebuild it with the "
                "default zodiac to use directions()."
            )
        from .predictives.primarydirections import PrimaryDirections

        return PrimaryDirections(self)

    def arabicPart(self, part_id: str) -> GenericObject:
        """Compute an Arabic part (lot) for this chart.

        Args:
            part_id: A part constant from
                :mod:`mayaastrolib.tools.arabicparts` (for example,
                :data:`PARS_FORTUNA`, :data:`PARS_SPIRIT`).

        Returns:
            A :class:`GenericObject` placed at the part's longitude
            with type ``OBJ_ARABIC_PART``.

        Example:
            >>> from mayaastrolib.tools import arabicparts
            >>> fortuna = chart.arabicPart(arabicparts.PARS_FORTUNA)
        """
        from .tools.arabicparts import _getPart_impl

        return _getPart_impl(part_id, self)

    def planetaryHour(self, date: Datetime | None = None) -> HourTable:
        """Return the planetary :class:`HourTable` for this chart.

        Convenience wrapper around
        :func:`mayaastrolib.tools.planetarytime.getHourTable`. The
        underlying function takes a date and a position; this method
        defaults to this chart's date and uses ``self.pos``.

        Args:
            date: A :class:`Datetime`. Defaults to the chart's own date.

        Returns:
            An :class:`HourTable` instance covering the diurnal and
            nocturnal hour sequences for the requested moment.

        Note:
            ``getHourTable(date, pos)`` is *not* deprecated — it
            remains useful for date+location queries that don't need
            a chart (e.g. "what's the planetary hour right now in
            Dublin").
        """
        from .tools.planetarytime import getHourTable

        if date is None:
            date = self.date
        return getHourTable(date, self.pos)

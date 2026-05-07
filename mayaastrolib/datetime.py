"""
This file is part of flatlib - (C) FlatAngle
Author: João Ventura (flatangleweb@gmail.com)


This module provides functions and classes for handling
dates and times.

The classes implemented in this file are <Date>, <Time>
and <Datetime>. Since time is similar to angles (same
string separators and base 60), the <Time> class uses
angular functions for internal conversions.

"""

from . import angle

# Calendar types
GREGORIAN = 0
JULIAN = 1


# === Julian Day Number conversions === #


def dateJDN(year, month, day, calendar):
    """Converts date to Julian Day Number."""
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    if calendar == GREGORIAN:
        return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    else:
        return day + (153 * m + 2) // 5 + 365 * y + y // 4 - 32083


def jdnDate(jdn):
    """Converts Julian Day Number to Gregorian date."""
    a = jdn + 32044
    b = (4 * a + 3) // 146097
    c = a - (146097 * b) // 4
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153
    day = e + 1 - (153 * m + 2) // 5
    month = m + 3 - 12 * (m // 10)
    year = 100 * b + d - 4800 + m // 10
    return [year, month, day]


# === UTC offset string helpers (used by Datetime.from_pydatetime / now) === #


def _format_offset(td):
    """Format a ``datetime.timedelta`` as ``"+HH:MM"`` / ``"-HH:MM"``.

    Used to derive the offset string from an aware datetime's tzinfo.
    """
    total_seconds = int(td.total_seconds())
    sign = "+" if total_seconds >= 0 else "-"
    total_seconds = abs(total_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{sign}{hours:02d}:{minutes:02d}"


def _parse_offset(offset_str):
    """Parse ``"+05:30"`` / ``"-08:00"`` into a ``datetime.timedelta``.

    Used when ``Datetime.from_pydatetime`` is asked to convert an aware
    datetime to a different target offset.
    """
    import datetime as _pydt

    if not offset_str or len(offset_str) < 6 or offset_str[0] not in "+-":
        raise ValueError(
            f"Invalid utcoffset format: {offset_str!r} (expected '+HH:MM' or '-HH:MM')"
        )
    sign = 1 if offset_str[0] == "+" else -1
    hours = int(offset_str[1:3])
    minutes = int(offset_str[4:6])
    return _pydt.timedelta(hours=sign * hours, minutes=sign * minutes)


# ------------------ #
#     Date Class     #
# ------------------ #


class Date:
    """This class represents a calendar date. It is
    internally represented by a JDN integer.

    Objects of this class can be instantiated with
    dates of type string, list and int (jdn).
    String and date lists are like 'yyyy/mm/dd'.

    """

    # Calendar types
    GREGORIAN = GREGORIAN
    JULIAN = JULIAN

    def __init__(self, value, calendar=GREGORIAN):
        if isinstance(value, str):
            # Assume string date such as "2015/03/29"
            value = [int(v) for v in value.split("/")]
            value = dateJDN(value[0], value[1], value[2], calendar)
        elif isinstance(value, list):
            # Assume list date such as [2015,03,29]
            value = dateJDN(value[0], value[1], value[2], calendar)
        self.jdn = int(value)

    def dayofweek(self):
        """Returns the day of week starting on Sunday as zero."""
        return (self.jdn + 1) % 7

    def date(self):
        """Returns date as list [yyyy,mm,dd]."""
        return jdnDate(self.jdn)

    def toList(self):
        """Returns date as signed list."""
        date = self.date()
        sign = "+" if date[0] >= 0 else "-"
        date[0] = abs(date[0])
        return list(sign) + date

    def toString(self):
        """Returns date as string."""
        slist = self.toList()
        sign = "" if slist[0] == "+" else "-"
        string = "/".join(["%02d" % v for v in slist[1:]])
        return sign + string

    def __str__(self):
        return "<%s>" % self.toString()


# ------------------ #
#     Time Class     #
# ------------------ #


class Time:
    """This class represents a time in the library.
    A time from this class can have negative values.

    Objects of this class can be instantiated with
    strings, signed lists or float values.
    String and time lists are like 'hh:mm:ss.'

    """

    def __init__(self, value):
        self.value = angle.toFloat(value)

    def getUTC(self, utcoffset):
        """Returns a new Time object set to UTC given
        an offset Time object.

        """
        newTime = (self.value - utcoffset.value) % 24
        return Time(newTime)

    def time(self):
        """Returns time as list [hh,mm,ss]."""
        slist = self.toList()
        if slist[0] == "-":
            slist[1] *= -1
            # We must do a trick if we want to
            # make negative zeros explicit
            if slist[1] == -0:
                slist[1] = -0.0
        return slist[1:]

    def toList(self):
        """Returns time as signed list."""
        slist = angle.toList(self.value)
        # Keep hours in 0..23
        slist[1] = slist[1] % 24
        return slist

    def toString(self):
        """Returns time as string."""
        slist = self.toList()
        string = angle.slistStr(slist)
        return string if slist[0] == "-" else string[1:]

    def __str__(self):
        return "<%s>" % self.toString()


# ------------------ #
#   Datetime Class   #
# ------------------ #


class Datetime:
    """This class represents a specific moment in time given by
    a date, a time and an UTC Offset. The UTC Offset is zero
    by default (UTC+0) although an offset can be given.

    """

    # Calendar types
    GREGORIAN = GREGORIAN
    JULIAN = JULIAN

    def __init__(self, date, time=0, utcoffset=0, calendar=GREGORIAN):
        # Prepare the variables
        if isinstance(date, Date):
            self.date = date
        else:
            self.date = Date(date, calendar)

        if isinstance(time, Time):
            self.time = time
        else:
            self.time = Time(time)

        if isinstance(utcoffset, Time):
            self.utcoffset = utcoffset
        else:
            self.utcoffset = Time(utcoffset)

        # Compute jd
        self.jd = self.date.jdn + self.time.value / 24.0 - self.utcoffset.value / 24.0 - 0.5

    @staticmethod
    def fromJD(jd, utcoffset):
        """Builds a Datetime object given a jd and utc offset."""
        if not isinstance(utcoffset, Time):
            utcoffset = Time(utcoffset)
        localJD = jd + utcoffset.value / 24.0
        date = Date(round(localJD))
        time = Time((localJD + 0.5 - date.jdn) * 24)
        return Datetime(date, time, utcoffset)

    @classmethod
    def from_pydatetime(cls, dt, utcoffset=None):
        """Construct a Datetime from a Python ``datetime.datetime``.

        Args:
            dt: A ``datetime.datetime`` instance. May be naive or
                timezone-aware.
            utcoffset: UTC offset string like ``"+05:30"`` or ``"-08:00"``.
                Required if ``dt`` is naive (no tzinfo). If ``dt`` is
                aware AND ``utcoffset`` is None, the offset is derived
                from ``dt.tzinfo``. If ``dt`` is aware AND ``utcoffset``
                is given, ``utcoffset`` wins: ``dt`` is converted to that
                offset's wall-clock time.

        Returns:
            A new Datetime instance. Sub-second precision is rounded to
            whole seconds — the underlying Time class does not preserve
            microseconds.

        Raises:
            ValueError: if ``dt`` is naive and ``utcoffset`` is not given.

        Example:
            >>> import datetime as pydt
            >>> now = pydt.datetime.now(pydt.timezone.utc)
            >>> mdate = Datetime.from_pydatetime(now)
        """
        import datetime as _pydt

        if dt.tzinfo is None:
            if utcoffset is None:
                raise ValueError(
                    "Datetime.from_pydatetime requires utcoffset for a "
                    "naive datetime (no tzinfo). Pass utcoffset='+00:00' "
                    "for UTC, or the local offset string."
                )
            target_offset_str = utcoffset
            target_dt = dt
        else:
            if utcoffset is None:
                target_offset_str = _format_offset(dt.utcoffset())
                target_dt = dt
            else:
                # Explicit utcoffset wins. Convert the aware dt to that
                # offset's wall-clock time so the resulting Datetime
                # represents the same instant in the requested zone.
                target_offset_str = utcoffset
                target_offset = _parse_offset(utcoffset)
                target_dt = dt.astimezone(_pydt.timezone(target_offset))

        date_str = "%04d/%02d/%02d" % (target_dt.year, target_dt.month, target_dt.day)
        time_str = "%02d:%02d:%02d" % (target_dt.hour, target_dt.minute, target_dt.second)
        return cls(date_str, time_str, target_offset_str)

    @classmethod
    def now(cls, utcoffset="+00:00"):
        """Return a Datetime representing the current moment.

        Args:
            utcoffset: UTC offset for the returned Datetime. Defaults to
                UTC. The underlying time is always the current wall-clock
                UTC moment; the offset controls how the wall-clock fields
                are formatted. To get a chart for "right now in Dublin",
                pass ``utcoffset="+01:00"`` (BST) or ``"+00:00"`` (GMT)
                depending on current DST state — this method does not
                handle DST.

        Returns:
            A Datetime for the current UTC moment, expressed in the given
            offset.

        Example:
            >>> mdate = Datetime.now()                  # UTC
            >>> mdate = Datetime.now(utcoffset='-05:00') # US Eastern (no DST awareness)
        """
        import datetime as _pydt

        return cls.from_pydatetime(
            _pydt.datetime.now(_pydt.timezone.utc),
            utcoffset=utcoffset,
        )

    def to_pydatetime(self):
        """Convert to a Python ``datetime.datetime`` with timezone info.

        Returns:
            A timezone-aware ``datetime.datetime`` in the offset originally
            specified at construction time. Sub-second precision is not
            preserved (see ``from_pydatetime``).

        Example:
            >>> mdate = Datetime("2015/03/13", "17:00", "+00:00")
            >>> py = mdate.to_pydatetime()
            >>> py.tzinfo.utcoffset(py)  # timedelta(0)
        """
        import datetime as _pydt

        year, month, day = jdnDate(self.date.jdn)
        hh, mm, ss = self.time.time()
        # self.time.time() can return floats (e.g. for fractional seconds);
        # cast to int because pydatetime requires int components.
        tz = _pydt.timezone(_pydt.timedelta(hours=self.utcoffset.value))
        return _pydt.datetime(year, month, day, int(hh), int(mm), int(ss), tzinfo=tz)

    def getUTC(self):
        """Returns this Datetime localized for UTC."""
        timeUTC = self.time.getUTC(self.utcoffset)
        dateUTC = Date(round(self.jd))
        return Datetime(dateUTC, timeUTC)

    def __str__(self):
        return "<%s %s %s>" % (
            self.date.toString(),
            self.time.toString(),
            self.utcoffset.toString(),
        )

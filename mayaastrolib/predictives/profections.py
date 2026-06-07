"""
This file is part of mayaastrolib, a fork of flatlib - (C) FlatAngle
Author: João Ventura (flatangleweb@gmail.com)


This module provides functions for handling profections.

The preferred entry point is :meth:`mayaastrolib.chart.Chart.profected`,
which returns a properly symbolic chart whose planet ``lonspeed`` /
``latspeed`` are cleared. The :func:`compute` function below is kept as
a deprecated wrapper for the legacy API.
"""

import math
import warnings

from mayaastrolib import const
from mayaastrolib.ephem import ephem


def compute(chart, date, fixedObjects=False):
    """[DEPRECATED] Return a profection chart for a given date.

    Use :meth:`mayaastrolib.chart.Chart.profected` instead, which
    returns a symbolic chart with ``is_symbolic=True`` and properly
    cleared planet speeds. ``compute`` will be removed in version 1.0.

    Args:
        chart: The natal chart.
        date: Target Datetime.
        fixedObjects: If True, keep the natal object positions (rotate
            only houses and angles). Niche legacy behaviour, not
            available on the new ``Chart.profected`` API.

    Returns:
        For ``fixedObjects=False`` (default): identical to
        ``chart.profected(target_date=date)`` — a symbolic chart.

        For ``fixedObjects=True``: the legacy in-place mutation result
        — natal object positions, profected houses/angles, no
        ``is_symbolic`` flag. Consumers needing this combination will
        have to inline the math after the 1.0 removal.
    """
    warnings.warn(
        "predictives.profections.compute() is deprecated. "
        "Use chart.profected(target_date=date) instead, which returns "
        "a symbolic chart with cleared planet speeds. "
        "Will be removed in version 1.0.",
        DeprecationWarning,
        stacklevel=2,
    )

    if not fixedObjects:
        return chart.profected(target_date=date)

    # Legacy fixedObjects=True behaviour preserved verbatim. Houses and
    # angles rotate; natal objects stay put. Not exposed on the new
    # Chart.profected API.
    sun = chart.getObject(const.SUN)
    prevSr = ephem.prevSolarReturn(date, sun.lon)
    nextSr = ephem.nextSolarReturn(date, sun.lon)
    rotation = 30 * (date.jd - prevSr.jd) / (nextSr.jd - prevSr.jd)
    age = math.floor((date.jd - chart.date.jd) / 365.25)
    rotation = 30 * age + rotation

    pChart = chart.copy()
    for house in pChart.houses:
        # Local in-place rotate kept here on purpose: deprecated wrapper
        # only, and the houses are GenericObject (no speed concept).
        new_lon = (house.lon + rotation) % 360
        house.lon = new_lon
        house.signlon = new_lon % 30
        house.sign = const.LIST_SIGNS[int(new_lon / 30.0)]
    for ang in pChart.angles:
        new_lon = (ang.lon + rotation) % 360
        ang.lon = new_lon
        ang.signlon = new_lon % 30
        ang.sign = const.LIST_SIGNS[int(new_lon / 30.0)]

    return pChart

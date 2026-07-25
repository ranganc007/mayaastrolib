"""High-level facade — one call from a date + place to a full chart report.

This is the front door for web apps and AI tooling: instead of learning
the 13-module calculation API, a consumer calls :func:`full_report` and
gets back a single JSON-serialisable dict combining the Western chart
(objects, houses, angles, aspects, dignities) and — for sidereal charts,
or on request — the Vedic layer (nakshatras, dasha, yogas, Shadbala).

The dict is exactly the v1 serialization schema produced by
:meth:`mayaastrolib.chart.Chart.to_dict`; see that method for the shape.

Example:
    >>> from mayaastrolib.datetime import Datetime
    >>> from mayaastrolib.geopos import GeoPos
    >>> from mayaastrolib.report import full_report
    >>> report = full_report(
    ...     Datetime("1990/06/15", "14:30", "+05:30"),
    ...     GeoPos("28n36", "77e12"),
    ... )
    >>> report["meta"]["zodiac"], len(report["objects"])
    ('Tropical', 11)
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from . import const
from .chart import Chart

__all__ = [
    "full_report",
    "full_report_json",
]

if TYPE_CHECKING:
    from .datetime import Datetime
    from .geopos import GeoPos


def full_report(
    date: Datetime,
    pos: GeoPos,
    *,
    hsys: str = const.HOUSES_DEFAULT,
    IDs: list[str] | None = None,
    zodiac: str = const.ZODIAC_TROPICAL,
    ayanamsa: str = const.AYANAMSA_LAHIRI,
    aspects: bool = True,
    dignities: bool = True,
    vedic: bool | str = "auto",
) -> dict[str, Any]:
    """Build a chart for ``date`` / ``pos`` and return its full report dict.

    A convenience wrapper around :class:`~mayaastrolib.chart.Chart` +
    :meth:`Chart.to_dict`. Defaults to a *comprehensive* report
    (aspects + dignities); the Vedic block is included automatically for
    sidereal charts.

    Args:
        date: A :class:`~mayaastrolib.datetime.Datetime`.
        pos: A :class:`~mayaastrolib.geopos.GeoPos`.
        hsys: House system. Default :data:`const.HOUSES_DEFAULT`.
        IDs: Objects to include. Default
            :data:`const.LIST_OBJECTS_TRADITIONAL`.
        zodiac: ``const.ZODIAC_TROPICAL`` (default) or
            ``const.ZODIAC_SIDEREAL``.
        ayanamsa: Used only when sidereal. Default Lahiri.
        aspects: Include the aspects list. Default True.
        dignities: Include per-planet essential dignities. Default True.
        vedic: ``"auto"`` (default) includes the Vedic block iff the chart
            is sidereal; ``True`` forces it on (computed via internal
            sidereal conversion even for a tropical chart); ``False``
            omits it.

    Returns:
        The v1 serialization dict (see :meth:`Chart.to_dict`).
    """
    chart = Chart(
        date,
        pos,
        hsys=hsys,
        zodiac=zodiac,
        ayanamsa=ayanamsa,
        IDs=IDs if IDs is not None else const.LIST_OBJECTS_TRADITIONAL,
    )
    if vedic == "auto":
        include_vedic = zodiac == const.ZODIAC_SIDEREAL
    else:
        include_vedic = bool(vedic)
    return chart.to_dict(aspects=aspects, dignities=dignities, vedic=include_vedic)


def full_report_json(
    date: Datetime,
    pos: GeoPos,
    *,
    indent: int | None = None,
    **kwargs: Any,
) -> str:
    """Like :func:`full_report` but returns a JSON string. ``indent`` is
    forwarded to :func:`json.dumps`; other keyword arguments pass through
    to :func:`full_report`."""
    return json.dumps(full_report(date, pos, **kwargs), indent=indent)

"""Async helpers for non-blocking chart computation.

The calculation engine is synchronous and CPU-bound (it calls into the
Swiss Ephemeris C library). In an async server — FastAPI, an MCP server,
an AI agent loop — running it directly on the event loop would block every
other coroutine for the duration of the computation.

These helpers run the synchronous work in a thread-pool executor via
:meth:`asyncio.loop.run_in_executor`, so the event loop stays responsive.
Concurrency is safe because every Swiss Ephemeris entry point is serialised
behind a single reentrant lock (see ``mayaastrolib.ephem.swe._SWE_LOCK``);
the executor threads contend on that lock but never corrupt each other's
results. See ``docs/CONCURRENCY.md``.

Example:
    >>> import asyncio
    >>> from mayaastrolib.datetime import Datetime
    >>> from mayaastrolib.geopos import GeoPos
    >>> from mayaastrolib.aio import afull_report
    >>> async def main():
    ...     return await afull_report(
    ...         Datetime("1990/06/15", "14:30", "+05:30"), GeoPos("28n36", "77e12")
    ...     )
    >>> report = asyncio.run(main())  # doctest: +SKIP
"""

from __future__ import annotations

import asyncio
import functools
from typing import TYPE_CHECKING, Any

from . import report as _report
from .chart import Chart

if TYPE_CHECKING:
    from .datetime import Datetime
    from .geopos import GeoPos


async def _run(func: Any, *args: Any, **kwargs: Any) -> Any:
    """Run a blocking callable in the default thread-pool executor."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))


async def achart(date: Datetime, pos: GeoPos, **kwargs: Any) -> Chart:
    """Construct a :class:`~mayaastrolib.chart.Chart` off the event loop.

    Accepts the same keyword arguments as :class:`Chart`.
    """
    return await _run(Chart, date, pos, **kwargs)


async def afull_report(date: Datetime, pos: GeoPos, **kwargs: Any) -> dict[str, Any]:
    """Compute :func:`mayaastrolib.report.full_report` off the event loop."""
    return await _run(_report.full_report, date, pos, **kwargs)


async def afull_report_json(date: Datetime, pos: GeoPos, **kwargs: Any) -> str:
    """Compute :func:`mayaastrolib.report.full_report_json` off the event
    loop."""
    return await _run(_report.full_report_json, date, pos, **kwargs)

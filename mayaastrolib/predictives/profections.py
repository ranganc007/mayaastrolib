"""
This file is part of mayaastrolib, a fork of flatlib - (C) FlatAngle
Author: João Ventura (flatangleweb@gmail.com)


Profections.

The entry point is :meth:`mayaastrolib.chart.Chart.profected`, which returns
a properly symbolic chart whose planet ``lonspeed`` / ``latspeed`` are
cleared::

    pchart = chart.profected(target_date=date)   # or: chart.profected(years=N)

This module previously exposed ``compute(chart, date, fixedObjects=False)``.
It was deprecated in favour of ``Chart.profected`` and removed in 1.0: it
mutated houses and angles in place and left planet speeds stale, so
``movement`` / ``isRetrograde`` on a profected chart reported the *natal*
planet's dynamics.

``compute(..., fixedObjects=True)`` — natal object positions with only houses
and angles rotated — has no direct replacement. It was a niche legacy mode and
is deliberately not exposed on :meth:`Chart.profected`; callers who need it
must inline the rotation themselves.

The module is intentionally left in place (rather than deleted) so that
``mayaastrolib.predictives.profections`` remains importable for the 1.0 cycle.
"""

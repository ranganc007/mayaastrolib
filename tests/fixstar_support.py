"""Shared guard for tests that need the Swiss Ephemeris fixed-star catalogue.

Fixed-star lookups read two data files from the ephemeris path:
``sefstars.txt`` (positions, via ``swisseph.fixstar2_ut``) and
``fixstars.cat`` (magnitudes, via ``swisseph.fixstar2_mag``). Both *are*
vendored in ``mayaastrolib/resources/swefiles/`` and shipped as package data,
and ``mayaastrolib.ephem`` points swisseph at them on import — so in a normal
checkout or wheel install these tests run for real.

They can still be genuinely unavailable: a consumer or CI job may repoint the
ephemeris path via :func:`mayaastrolib.ephem.setPath`, or install from a source
tree stripped of package data. swisseph then raises
``swisseph.Error: could not find star name ...``, which reads like a code bug
when it is purely environmental.

Tests that need the catalogue decorate with :data:`requires_fixstar_data` so
they skip honestly in that case. The guard only skips on genuine absence — when
the data is present the tests run and assert exactly as before.
"""

import functools
import unittest


@functools.cache
def fixstar_data_available() -> bool:
    """Return True if a real fixed-star lookup succeeds in this environment.

    Probes the full path (position *and* magnitude, i.e. both data files) with
    one guarded lookup and caches the answer for the session.
    """
    from mayaastrolib import const
    from mayaastrolib.ephem import swe

    try:
        swe.sweFixedStar(const.STAR_ALGOL, 2451545.0)  # J2000.0
    except Exception:
        return False
    return True


requires_fixstar_data = unittest.skipUnless(
    fixstar_data_available(),
    "Swiss Ephemeris fixed-star catalogue (sefstars.txt / fixstars.cat) not "
    "available on the ephemeris path",
)

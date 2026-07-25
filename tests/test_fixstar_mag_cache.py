"""Tests for fixstar_mag caching (Task 016).

The platform review (`docs/REVIEW-2026-05-08.md`) flagged
``swisseph.fixstar2_mag`` as the only documented "really slow" path
in the codebase — it reparses ``fixstars.cat`` on every call.
Task 016 wraps it in :func:`mayaastrolib.ephem.swe._fixstar_mag` with
:func:`functools.lru_cache`, since star magnitudes are immutable
per-process.

These tests verify the cache returns the same value as a direct
swisseph call (correctness) and is keyed per-star (no accidental
collisions). The empirical speedup is captured separately in
``docs/PROJECT-LOG.md`` from a one-time benchmark; not asserted here
because absolute timings are machine-dependent.
"""

from __future__ import annotations

import unittest

# tests/ is not a package; pytest puts it on sys.path (importmode=prepend).
from fixstar_support import requires_fixstar_data

import mayaastrolib.ephem  # noqa: F401 — import side-effect: sets swisseph ephe path
from mayaastrolib.ephem.swe import _fixstar_mag


@requires_fixstar_data
class FixstarMagCacheTests(unittest.TestCase):
    def test_cached_value_matches_direct_swisseph(self):
        """The cached function must return the same value as a direct
        swisseph call. Any cache bug returning wrong values would be
        caught here.
        """
        import swisseph

        for name in ["Aldebaran", "Regulus", "Spica", "Antares"]:
            cached = _fixstar_mag(name)
            direct = swisseph.fixstar2_mag(name)
            self.assertEqual(
                cached,
                direct,
                f"cache returned {cached!r} but direct call returned {direct!r} for {name}",
            )

    def test_repeated_calls_return_consistent_value(self):
        """Calling the cached function multiple times returns the same
        value every time (catches accidental cache invalidation).
        """
        first = _fixstar_mag("Aldebaran")
        for _ in range(10):
            self.assertEqual(_fixstar_mag("Aldebaran"), first)

    def test_different_stars_have_different_results(self):
        """Cache keys must be distinct per star (catches accidentally
        keying on something constant).
        """
        m_aldebaran = _fixstar_mag("Aldebaran")
        m_spica = _fixstar_mag("Spica")
        # Aldebaran is mag ~0.86, Spica is mag ~0.97 — distinct tuples
        self.assertNotEqual(m_aldebaran, m_spica)

    def test_cache_actually_caches(self):
        """After warming, repeated calls must register as cache hits
        rather than misses.
        """
        _fixstar_mag.cache_clear()
        # First call: miss
        _fixstar_mag("Aldebaran")
        info_after_first = _fixstar_mag.cache_info()
        self.assertEqual(info_after_first.misses, 1)
        # Second call: hit
        _fixstar_mag("Aldebaran")
        info_after_second = _fixstar_mag.cache_info()
        self.assertEqual(info_after_second.hits, 1)
        self.assertEqual(info_after_second.misses, 1)


if __name__ == "__main__":
    unittest.main()

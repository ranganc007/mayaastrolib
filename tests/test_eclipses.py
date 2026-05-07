"""Regression tests for eclipse calculations.

Catches the pyswisseph keyword argument bug found during fork recon
(see RECON.md §8 ¶1 and KNOWN-BUGS.md). Once the bug is fixed in
flatlib/ephem/swe.py, these tests pin the behaviour so any future
regression will fail loudly in CI.
"""

import unittest

from flatlib.datetime import Datetime
from flatlib.ephem import ephem


class EclipseTests(unittest.TestCase):
    """Smoke tests — verify eclipse functions return without crashing."""

    def setUp(self):
        # Reference date: 2020-01-01 12:00 UTC. Arbitrary but fixed.
        self.date = Datetime("2020/01/01", "12:00", "+00:00")

    def test_next_solar_eclipse_does_not_crash(self):
        """nextSolarEclipse must not raise TypeError on keyword args."""
        result = ephem.nextSolarEclipse(self.date)
        self.assertIsNotNone(result)

    def test_prev_solar_eclipse_does_not_crash(self):
        """prevSolarEclipse must not raise TypeError on keyword args."""
        result = ephem.prevSolarEclipse(self.date)
        self.assertIsNotNone(result)

    def test_next_lunar_eclipse_does_not_crash(self):
        """nextLunarEclipse must not raise TypeError on keyword args."""
        result = ephem.nextLunarEclipse(self.date)
        self.assertIsNotNone(result)

    def test_prev_lunar_eclipse_does_not_crash(self):
        """prevLunarEclipse must not raise TypeError on keyword args."""
        result = ephem.prevLunarEclipse(self.date)
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()

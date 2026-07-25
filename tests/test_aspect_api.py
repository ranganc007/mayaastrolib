"""Tests for the Aspect API improvements added in Task 009.

Covers:
- ``Aspect.name`` property and ``const.ASPECT_NAMES`` mapping
- ``Aspect.activeObj`` / ``passiveObj`` references to the original Object
- ``getAspect`` returning ``None`` instead of a sentinel
"""

import unittest

from mayaastrolib import aspects, const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos


def _chart():
    """The library's canonical README sample chart."""
    date = Datetime("2015/03/13", "17:00", "+00:00")
    pos = GeoPos("38n32", "8w54")
    return Chart(date, pos)


class AspectNameTests(unittest.TestCase):
    def test_aspect_names_constant_exists(self):
        self.assertIsInstance(const.ASPECT_NAMES, dict)
        self.assertEqual(const.ASPECT_NAMES[0], "Conjunction")
        self.assertEqual(const.ASPECT_NAMES[60], "Sextile")
        self.assertEqual(const.ASPECT_NAMES[90], "Square")
        self.assertEqual(const.ASPECT_NAMES[120], "Trine")
        self.assertEqual(const.ASPECT_NAMES[180], "Opposition")

    def test_aspect_names_covers_all_canonical_angles(self):
        for angle in const.MAJOR_ASPECTS + const.MINOR_ASPECTS:
            self.assertIn(angle, const.ASPECT_NAMES)

    def test_aspect_has_name_property(self):
        chart = _chart()
        sun = chart.get(const.SUN)
        moon = chart.get(const.MOON)
        asp = aspects.getAspect(sun, moon, const.MAJOR_ASPECTS)
        self.assertIsNotNone(asp, "Sun-Moon aspect expected for sample chart")
        self.assertIsInstance(asp.name, str)
        self.assertIn(asp.name, const.ASPECT_NAMES.values())
        # Sample chart has Sun-Moon Square per recipes/aspects.py
        self.assertEqual(asp.name, const.ASPECT_NAMES[asp.type])

    def test_no_aspect_name_for_no_aspect_type(self):
        """``Aspect.name`` still degrades gracefully for NO_ASPECT.

        Before 1.0 such an Aspect came from ``getAspectOrSentinel()``. That
        constructor is gone, so build one directly from a properties dict —
        the ``name`` lookup is what is under test, not how it was produced.
        """
        chart = _chart()
        sun = chart.get(const.SUN)
        moon = chart.get(const.MOON)
        asp = aspects.Aspect(
            {
                "type": const.NO_ASPECT,
                "orb": 0,
                "direction": const.DEXTER,
                "condition": const.ASSOCIATE,
                "active": {"id": sun.id, "inOrb": False, "movement": const.EXACT},
                "passive": {"id": moon.id, "inOrb": False, "movement": const.EXACT},
            }
        )
        self.assertEqual(asp.type, const.NO_ASPECT)
        self.assertEqual(asp.name, "No Aspect")


class AspectObjectFidelityTests(unittest.TestCase):
    """Verify that activeObj / passiveObj expose the original Object."""

    def test_activeObj_is_full_object_with_movement(self):
        chart = _chart()
        sun = chart.get(const.SUN)
        moon = chart.get(const.MOON)
        asp = aspects.getAspect(sun, moon, const.MAJOR_ASPECTS)
        self.assertIsNotNone(asp)
        # The full Object's movement is Direct/Retrograde/Stationary
        # (NOT the aspect-relative Applicative/Separative/Exact carried by
        # asp.active.movement). This is the bug Task 009 fixes.
        self.assertIn(
            asp.activeObj.movement,
            [const.DIRECT, const.RETROGRADE, const.STATIONARY],
        )

    def test_active_snapshot_still_has_aspect_movement(self):
        """The legacy AspectObject snapshot continues to carry the
        aspect-relative movement string for backwards compatibility.
        """
        chart = _chart()
        sun = chart.get(const.SUN)
        moon = chart.get(const.MOON)
        asp = aspects.getAspect(sun, moon, const.MAJOR_ASPECTS)
        self.assertIsNotNone(asp)
        self.assertIn(
            asp.active.movement,
            [const.APPLICATIVE, const.SEPARATIVE, const.EXACT, const.NO_MOVEMENT],
        )

    def test_activeObj_identity_matches_input(self):
        """activeObj is the very Object instance that was the active end."""
        chart = _chart()
        sun = chart.get(const.SUN)
        moon = chart.get(const.MOON)
        asp = aspects.getAspect(sun, moon, const.MAJOR_ASPECTS)
        self.assertIsNotNone(asp)
        self.assertIn(asp.activeObj, (sun, moon))
        self.assertIn(asp.passiveObj, (sun, moon))
        self.assertIsNot(asp.activeObj, asp.passiveObj)


class GetAspectReturnTests(unittest.TestCase):
    def test_no_aspect_returns_none(self):
        """Asking for an empty aspect list always yields None."""
        chart = _chart()
        sun = chart.get(const.SUN)
        moon = chart.get(const.MOON)
        asp = aspects.getAspect(sun, moon, [])
        self.assertIsNone(asp)

    def test_existing_aspect_returns_aspect(self):
        chart = _chart()
        sun = chart.get(const.SUN)
        moon = chart.get(const.MOON)
        asp = aspects.getAspect(sun, moon, const.MAJOR_ASPECTS)
        self.assertIsNotNone(asp)
        self.assertIn(asp.type, const.ASPECT_NAMES)


if __name__ == "__main__":
    unittest.main()

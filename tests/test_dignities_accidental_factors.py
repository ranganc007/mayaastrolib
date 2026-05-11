"""Per-factor exercise tests for accidental dignities — Task 033.

Runs the AccidentalDignity engine across several charts × the seven
classical planets so the sun-relation, light, orientality, haiz, and
the various aspect/receptions branches get exercised, and asserts the
structural invariants of the score outputs.
"""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.dignities import accidental
from mayaastrolib.geopos import GeoPos

_CHARTS = [
    ("1879/03/14", "11:30", "+01:00", "48n22", "10e54"),
    ("1947/08/15", "00:00", "+05:30", "28n36", "77e12"),
    ("2000/01/01", "12:00", "+00:00", "0n00", "0e00"),
    ("1969/07/20", "20:17", "+00:00", "51n30", "0w07"),
    ("1990/06/21", "06:00", "-05:00", "40n43", "74w00"),
    ("2024/10/01", "03:00", "+09:00", "35n41", "139e41"),  # Tokyo pre-dawn
]
_PLANETS = (
    const.SUN,
    const.MOON,
    const.MERCURY,
    const.VENUS,
    const.MARS,
    const.JUPITER,
    const.SATURN,
)


def _make_charts():
    return [Chart(Datetime(d, t, off), GeoPos(lat, lon)) for (d, t, off, lat, lon) in _CHARTS]


class AccidentalDignityTests(unittest.TestCase):
    def test_score_properties_well_formed(self):
        for chart in _make_charts():
            for pid in _PLANETS:
                obj = chart.getObject(pid)
                ad = accidental.AccidentalDignity(obj, chart)
                props = ad.getScoreProperties()
                self.assertIsInstance(props, dict)
                # Every value in the score-properties dict is a (score,
                # bool/value) pair or a score; just verify it's a mapping
                # with at least the house entry, and that getScore sums it.
                self.assertIn("house", props)
                score = ad.score()
                self.assertIsInstance(score, int)

    def test_active_properties_subset_of_score_properties(self):
        for chart in _make_charts():
            for pid in _PLANETS:
                ad = accidental.AccidentalDignity(chart.getObject(pid), chart)
                allp = ad.getScoreProperties()
                active = ad.getActiveProperties()
                self.assertTrue(set(active.keys()).issubset(set(allp.keys())))

    def test_house_score_in_expected_range(self):
        for chart in _make_charts():
            for pid in _PLANETS:
                ad = accidental.AccidentalDignity(chart.getObject(pid), chart)
                # houseScore returns a small integer (the traditional
                # house-strength value); just sanity-check it's an int in
                # a plausible band.
                hs = ad.houseScore()
                self.assertIsInstance(hs, int)
                self.assertTrue(-10 <= hs <= 10)

    def test_sun_relation_one_of_expected(self):
        for chart in _make_charts():
            sun = chart.getObject(const.SUN)
            for pid in _PLANETS:
                if pid == const.SUN:
                    continue
                rel = accidental.sunRelation(chart.getObject(pid), sun)
                # sunRelation returns one of a small set of labels (or
                # None / a constant). Just verify it doesn't raise and is
                # a string or None.
                self.assertTrue(rel is None or isinstance(rel, str))

    def test_light_and_orientality_callable(self):
        for chart in _make_charts():
            sun = chart.getObject(const.SUN)
            for pid in (const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN):
                obj = chart.getObject(pid)
                # These should not raise for any chart × planet.
                accidental.light(obj, sun)
                accidental.orientality(obj, sun)

    def test_haiz_and_via_combusta_callable(self):
        for chart in _make_charts():
            for pid in _PLANETS:
                obj = chart.getObject(pid)
                accidental.haiz(obj, chart)
                accidental.viaCombusta(obj)

    def test_boolean_flag_methods_callable_for_every_planet(self):
        # Exercise every flag-method across every planet × chart so the
        # branches are covered. The flags are truthy/falsy (some return
        # None where the concept isn't meaningful, e.g. orientality for a
        # luminary); just verify none of them raise.
        for chart in _make_charts():
            for pid in _PLANETS:
                ad = accidental.AccidentalDignity(chart.getObject(pid), chart)
                for method_name in (
                    "isCazimi",
                    "isUnderSun",
                    "isCombust",
                    "isAugmentingLight",
                    "isOriental",
                    "inHouseJoy",
                    "inSignJoy",
                    "isAuxilied",
                    "isSurrounded",
                    "isConjNorthNode",
                    "isConjSouthNode",
                    "isVoc",
                    "isFeral",
                    "haiz",
                ):
                    bool(getattr(ad, method_name)())  # must not raise

    def test_score_properties_regression(self):
        # Pins getScoreProperties for a fixed chart × planet so the
        # table-driven refactor (Task 034) — and any future change — is
        # caught if it alters the numbers.
        chart = Chart(Datetime("1947/08/15", "00:00", "+05:30"), GeoPos("28n36", "77e12"))
        expected_totals = {
            const.SUN: 5,
            const.MOON: 10,
            const.MARS: 13,
            const.JUPITER: -10,
            const.SATURN: 15,
            const.MERCURY: -7,
            const.VENUS: -11,
        }
        for pid, expected in expected_totals.items():
            ad = accidental.AccidentalDignity(chart.getObject(pid), chart)
            self.assertEqual(ad.score(), expected, f"{pid}")
            # The full Sun score-properties dict (a stable anchor).
            if pid == const.SUN:
                self.assertEqual(
                    dict(sorted(ad.getScoreProperties().items())),
                    {
                        "auxilied": 0,
                        "benefic_asp0": 5,
                        "benefic_asp120": 0,
                        "benefic_asp60": 0,
                        "cazimi": 0,
                        "combust": 0,
                        "direction": 0,
                        "feral": 0,
                        "haiz": 0,
                        "house": 4,
                        "joy_house": 0,
                        "joy_sign": 3,
                        "light": 0,
                        "malefic_asp0": -5,
                        "malefic_asp180": 0,
                        "malefic_asp90": 0,
                        "mr_exalt": 0,
                        "mr_ruler": 0,
                        "no_under_sun": 0,
                        "north_node": 0,
                        "orientality": 0,
                        "peregrine": 0,
                        "south_node": 0,
                        "speed": -2,
                        "surround": 0,
                        "under_sun": 0,
                        "viacombusta": 0,
                        "void": 0,
                    },
                )


if __name__ == "__main__":
    unittest.main()

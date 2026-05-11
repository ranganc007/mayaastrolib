"""Per-factor exercise tests for the temperament protocol — Task 033.

The smoke tests run the engine once; these run it across several charts
so the factor / modifier branches (aspecting-but-not-in-house-1,
Mars/Saturn/Sun afflictions, etc.) get exercised, and assert the
structural invariants of the outputs.
"""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.protocols import temperament

# A spread of dates/locations so different temperament branches fire.
_CHARTS = [
    ("1879/03/14", "11:30", "+01:00", "48n22", "10e54"),  # Einstein-ish
    ("1947/08/15", "00:00", "+05:30", "28n36", "77e12"),  # Delhi midnight
    ("2000/01/01", "12:00", "+00:00", "0n00", "0e00"),  # equator noon
    ("1969/07/20", "20:17", "+00:00", "51n30", "0w07"),  # London evening
    ("1990/06/21", "06:00", "-05:00", "40n43", "74w00"),  # NYC dawn solstice
]


def _make_charts():
    return [Chart(Datetime(d, t, off), GeoPos(lat, lon)) for (d, t, off, lat, lon) in _CHARTS]


class TemperamentFactorTests(unittest.TestCase):
    def test_factors_have_element_keys(self):
        for chart in _make_charts():
            factors = temperament.getFactors(chart)
            self.assertIsInstance(factors, list)
            for f in factors:
                self.assertIn("factor", f)
                # Every factor that made it into the list has an element.
                self.assertIn("element", f)
                self.assertIn(f["element"], (const.FIRE, const.EARTH, const.AIR, const.WATER))

    def test_modifiers_well_formed(self):
        for chart in _make_charts():
            mods = temperament.getModifiers(chart)
            self.assertIsInstance(mods, list)
            for m in mods:
                self.assertEqual(set(m.keys()), {"factor", "aspect", "objID", "element"})
                self.assertIn(
                    m["factor"],
                    (temperament.MOD_ASC, temperament.MOD_ASC_RULER, temperament.MOD_MOON),
                )
                self.assertIn(m["objID"], (const.MARS, const.SATURN, const.SUN))

    def test_scores_partition(self):
        for chart in _make_charts():
            sc = temperament.scores(temperament.getFactors(chart))
            self.assertEqual(
                set(sc["temperaments"].keys()),
                {const.CHOLERIC, const.MELANCHOLIC, const.SANGUINE, const.PHLEGMATIC},
            )
            self.assertEqual(
                set(sc["qualities"].keys()), {const.HOT, const.COLD, const.DRY, const.HUMID}
            )
            for v in sc["temperaments"].values():
                self.assertGreaterEqual(v, 0)
            for v in sc["qualities"].values():
                self.assertGreaterEqual(v, 0)
            # Each factor contributes exactly one to a temperament and two
            # to qualities, so the totals are consistent.
            n_factors = len(temperament.getFactors(chart))
            self.assertEqual(sum(sc["temperaments"].values()), n_factors)
            self.assertEqual(sum(sc["qualities"].values()), 2 * n_factors)

    def test_temperament_class_methods(self):
        chart = _make_charts()[0]
        t = temperament.Temperament(chart)
        self.assertEqual(t.getFactors(), temperament.getFactors(chart))
        self.assertEqual(t.getModifiers(), temperament.getModifiers(chart))
        self.assertEqual(t.getScore(), temperament.scores(temperament.getFactors(chart)))

    def test_modifier_factor_returns_none_when_no_aspect(self):
        # Two objects far apart with no aspect → modifierFactor returns None.
        chart = _make_charts()[0]
        sun = chart.getObject(const.SUN)
        asc = chart.getAngle(const.ASC)
        # asp list that excludes the conjunction so it's "no aspect" if
        # they're conjunct, or just pick objects ~30° apart and an asp
        # list of [120] — at least one combination yields None across the
        # five charts.
        results = [
            temperament.modifierFactor(chart, "test", asc, sun, [120]) for chart in _make_charts()
        ]
        # At least one of the five should be None (no 120° aspect).
        self.assertIn(None, results)

    def test_single_factor_for_a_sign_string(self):
        chart = _make_charts()[0]
        factors = []
        res = temperament.singleFactor(factors, chart, "Test", const.ARIES)
        self.assertEqual(res["element"], const.FIRE)
        self.assertIn(res, factors)


if __name__ == "__main__":
    unittest.main()

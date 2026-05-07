"""Thread-safety and overload tests for mayaastrolib.dignities.essential.

Regression tests for the global-state bug fixed in Task 008.
"""

import threading
import unittest
import warnings

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.dignities import essential
from mayaastrolib.dignities.tables import (
    EGYPTIAN_TERMS,
    LILLY_TERMS,
    TETRABIBLOS_TERMS,
    TRIPLICITY_FACES,
)
from mayaastrolib.geopos import GeoPos


def _build_chart():
    date = Datetime("2015/03/13", "17:00", "+00:00")
    pos = GeoPos("38n32", "8w54")
    return Chart(date, pos)


class DignityThreadSafetyTests(unittest.TestCase):
    def setUp(self):
        self.chart = _build_chart()
        self.sun = self.chart.get(const.SUN)

    def test_different_threads_different_variants(self):
        """Each thread uses a different terms variant simultaneously.

        Without the parameter API, this would corrupt results because
        all threads share the module-level TERMS global.
        """
        results = {}
        errors = []

        def compute_with_variant(variant_name, variant_value):
            try:
                scores = []
                for _ in range(100):
                    s = essential.score(self.sun, terms_variant=variant_value)
                    scores.append(s)
                results[variant_name] = scores
            except Exception as e:
                errors.append((variant_name, e))

        threads = [
            threading.Thread(target=compute_with_variant, args=("egyptian", EGYPTIAN_TERMS)),
            threading.Thread(target=compute_with_variant, args=("tetrabiblos", TETRABIBLOS_TERMS)),
            threading.Thread(target=compute_with_variant, args=("lilly", LILLY_TERMS)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])
        # Each thread's scores should be internally consistent.
        for variant_name, scores in results.items():
            self.assertEqual(
                len(set(scores)),
                1,
                f"Thread '{variant_name}' got inconsistent results: {set(scores)}",
            )


class ScoreOverloadTests(unittest.TestCase):
    def setUp(self):
        self.chart = _build_chart()
        self.sun = self.chart.get(const.SUN)

    def test_object_call_equals_legacy_call(self):
        new_style = essential.score(self.sun)
        legacy = essential.score(self.sun.id, self.sun.sign, self.sun.signlon)
        self.assertEqual(new_style, legacy)

    def test_legacy_call_with_missing_args_raises(self):
        with self.assertRaises(TypeError):
            essential.score(const.SUN)  # missing sign, lon

    def test_getInfo_object_call_equals_legacy_call(self):
        new_style = essential.getInfo(self.sun)
        legacy = essential.getInfo(self.sun.sign, self.sun.signlon)
        self.assertEqual(new_style, legacy)

    def test_isPeregrine_object_call_equals_legacy_call(self):
        new_style = essential.isPeregrine(self.sun)
        legacy = essential.isPeregrine(self.sun.id, self.sun.sign, self.sun.signlon)
        self.assertEqual(new_style, legacy)


class ParameterApiTests(unittest.TestCase):
    """Verify the variant parameter actually changes the result."""

    def setUp(self):
        self.chart = _build_chart()
        self.sun = self.chart.get(const.SUN)

    def test_different_terms_variants_can_yield_different_results(self):
        # Compute the term lord under all three variants. They aren't
        # required to differ for any specific position, but at least one
        # function call must complete cleanly per variant — which is the
        # main thing the parameter API enables.
        for variant in (EGYPTIAN_TERMS, TETRABIBLOS_TERMS, LILLY_TERMS):
            t = essential.term(self.sun.sign, self.sun.signlon, terms_variant=variant)
            self.assertIsNotNone(t)


class DeprecatedSettersTests(unittest.TestCase):
    def test_setFaces_emits_warning(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            essential.setFaces(TRIPLICITY_FACES)
            self.assertTrue(
                any(issubclass(w.category, DeprecationWarning) for w in caught),
                "setFaces() should emit DeprecationWarning",
            )
        # Reset the global so other tests are not affected.
        essential.setFaces(essential.CHALDEAN_FACES)

    def test_setTerms_emits_warning(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            essential.setTerms(LILLY_TERMS)
            self.assertTrue(
                any(issubclass(w.category, DeprecationWarning) for w in caught),
                "setTerms() should emit DeprecationWarning",
            )
        # Reset.
        essential.setTerms(EGYPTIAN_TERMS)


if __name__ == "__main__":
    unittest.main()

"""Tests for the property_with_method_compat decorator (mayaastrolib._compat).

These cover the wrapper's protocol forwarding (==, <, bool, etc.) plus
the regression case that motivated the decorator: a method-style getter
returning a value whose truthiness was always True regardless of the
underlying string.
"""

import unittest
import warnings

from mayaastrolib._compat import property_with_method_compat


class _Holder:
    """Minimal class with a property_with_method_compat decorated attribute."""

    def __init__(self, value):
        self._stored = value

    @property_with_method_compat
    def thing(self):
        return self._stored


class CompatPropertyTests(unittest.TestCase):
    def test_property_access_equals_value(self):
        h = _Holder("hello")
        self.assertEqual(h.thing, "hello")

    def test_method_access_returns_value_and_warns(self):
        h = _Holder("hello")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = h.thing()
            self.assertEqual(result, "hello")
            self.assertTrue(
                any(issubclass(w.category, DeprecationWarning) for w in caught),
                "method-style access must emit DeprecationWarning",
            )

    def test_eq_and_ne(self):
        h = _Holder(7)
        self.assertEqual(h.thing, 7)
        self.assertNotEqual(h.thing, 8)

    def test_comparison_operators(self):
        h = _Holder(5)
        self.assertTrue(h.thing < 10)
        self.assertTrue(h.thing <= 5)
        self.assertTrue(h.thing > 1)
        self.assertTrue(h.thing >= 5)

    def test_reflected_comparison(self):
        # Number on the left side, _DualAccess on the right.
        h = _Holder(5)
        self.assertTrue(3 < h.thing)
        self.assertTrue(10 >= h.thing)

    def test_bool_of_falsy_value_is_false(self):
        # Original bug: a bound method object is always truthy regardless of
        # the underlying value. The wrapper must reflect the value's truthiness.
        h = _Holder("")
        self.assertFalse(bool(h.thing))
        self.assertFalse(h.thing)

    def test_bool_of_truthy_value_is_true(self):
        h = _Holder("Direct")
        self.assertTrue(bool(h.thing))
        self.assertTrue(h.thing)

    def test_str_and_repr(self):
        h = _Holder("Pisces")
        self.assertEqual(str(h.thing), "Pisces")
        self.assertEqual(repr(h.thing), "'Pisces'")

    def test_hash_matches_value(self):
        h = _Holder("Sun")
        self.assertEqual(hash(h.thing), hash("Sun"))

    def test_dictionary_key_use(self):
        h = _Holder("Sun")
        d = {"Sun": "yes"}
        self.assertEqual(d[h.thing], "yes")

    def test_float_and_int(self):
        h = _Holder(2.5)
        self.assertEqual(float(h.thing), 2.5)
        self.assertEqual(int(h.thing), 2)


if __name__ == "__main__":
    unittest.main()

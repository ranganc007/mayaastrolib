"""Smoke tests for mayaastrolib.dignities.tables.

The module is mostly static reference data; tests assert the
expected constants exist with sensible shapes.
"""

import unittest

from mayaastrolib.dignities import tables


class TablesTests(unittest.TestCase):
    def test_module_imports(self):
        self.assertIsNotNone(tables)

    def test_sign_list_has_twelve_signs(self):
        self.assertEqual(len(tables.SIGN_LIST), 12)

    def test_chaldean_faces_keyed_by_sign(self):
        self.assertEqual(len(tables.CHALDEAN_FACES), 12)

    def test_triplicity_faces_keyed_by_sign(self):
        self.assertEqual(len(tables.TRIPLICITY_FACES), 12)

    def test_egyptian_terms_keyed_by_sign(self):
        self.assertEqual(len(tables.EGYPTIAN_TERMS), 12)

    def test_tetrabiblos_terms_keyed_by_sign(self):
        self.assertEqual(len(tables.TETRABIBLOS_TERMS), 12)

    def test_lilly_terms_keyed_by_sign(self):
        self.assertEqual(len(tables.LILLY_TERMS), 12)

    def test_essential_dignities_keyed_by_sign(self):
        self.assertEqual(len(tables.ESSENTIAL_DIGNITIES), 12)


if __name__ == "__main__":
    unittest.main()

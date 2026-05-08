"""Tests for GeoPos input validation (Task 015).

Closes the bug surfaced in `docs/REVIEW-2026-05-08.md`: out-of-range
latitudes (e.g. ``GeoPos('200n00', '0w00')``) used to be silently
accepted, producing mathematically nonsensical charts. After Task 015,
construction raises ``ValueError`` with the offending value in the
message.
"""

import unittest

from mayaastrolib.geopos import GeoPos


class GeoPosValidationTests(unittest.TestCase):
    # ---------------------------------------------------------------- #
    # Valid inputs continue to work                                    #
    # ---------------------------------------------------------------- #

    def test_valid_string_lat_lon(self):
        pos = GeoPos("38n32", "8w54")
        self.assertAlmostEqual(pos.lat, 38.5333, places=2)
        self.assertAlmostEqual(pos.lon, -8.9, places=1)

    def test_valid_equator_prime_meridian(self):
        pos = GeoPos("0n00", "0e00")
        self.assertEqual(pos.lat, 0.0)
        self.assertEqual(pos.lon, 0.0)

    def test_valid_north_pole(self):
        pos = GeoPos("90n00", "0e00")
        self.assertEqual(pos.lat, 90.0)

    def test_valid_south_pole(self):
        pos = GeoPos("90s00", "0e00")
        self.assertEqual(pos.lat, -90.0)

    def test_valid_antimeridian_east(self):
        pos = GeoPos("0n00", "180e00")
        self.assertEqual(pos.lon, 180.0)

    def test_valid_antimeridian_west(self):
        pos = GeoPos("0n00", "180w00")
        self.assertEqual(pos.lon, -180.0)

    # ---------------------------------------------------------------- #
    # Out-of-range string inputs raise ValueError                      #
    # ---------------------------------------------------------------- #

    def test_latitude_above_90_raises(self):
        with self.assertRaises(ValueError) as ctx:
            GeoPos("200n00", "0w00")
        self.assertIn("200", str(ctx.exception))
        self.assertIn("Latitude", str(ctx.exception))

    def test_latitude_below_neg_90_raises(self):
        with self.assertRaises(ValueError) as ctx:
            GeoPos("100s00", "0w00")
        self.assertIn("-100", str(ctx.exception))

    def test_longitude_above_180_raises(self):
        with self.assertRaises(ValueError) as ctx:
            GeoPos("0n00", "200e00")
        self.assertIn("200", str(ctx.exception))
        self.assertIn("Longitude", str(ctx.exception))

    def test_longitude_below_neg_180_raises(self):
        with self.assertRaises(ValueError) as ctx:
            GeoPos("0n00", "200w00")
        self.assertIn("-200", str(ctx.exception))

    # ---------------------------------------------------------------- #
    # Boundary checks: ±90 / ±180 valid; one minute past not           #
    # ---------------------------------------------------------------- #

    def test_latitude_just_above_90_raises(self):
        with self.assertRaises(ValueError):
            GeoPos("90n01", "0w00")

    def test_longitude_just_above_180_raises(self):
        with self.assertRaises(ValueError):
            GeoPos("0n00", "180e01")

    # ---------------------------------------------------------------- #
    # Numeric inputs — toFloat() accepts floats too, so the path also  #
    # needs validation.                                                #
    # ---------------------------------------------------------------- #

    def test_valid_float_inputs(self):
        pos = GeoPos(38.5333, -8.9)
        self.assertAlmostEqual(pos.lat, 38.5333, places=4)
        self.assertAlmostEqual(pos.lon, -8.9, places=4)

    def test_float_lat_out_of_range_raises(self):
        with self.assertRaises(ValueError) as ctx:
            GeoPos(200.0, 0.0)
        self.assertIn("200", str(ctx.exception))

    def test_float_lon_out_of_range_raises(self):
        with self.assertRaises(ValueError) as ctx:
            GeoPos(0.0, -250.0)
        self.assertIn("-250", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

"""Tests for Vedic nakshatra arithmetic — Task 018."""

import unittest

from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.vedic import nakshatras as nak


class NakshatraBoundaryTests(unittest.TestCase):
    """Each nakshatra starts at a known sidereal longitude."""

    def test_zero_degrees_is_ashwini_pada_1(self):
        n = nak.of_longitude(0.0)
        self.assertEqual(n.name, "Ashwini")
        self.assertEqual(n.lord, const.KETU)
        self.assertEqual(n.pada, 1)
        self.assertEqual(n.index, 0)

    def test_13_20_is_bharani_pada_1(self):
        # End of Ashwini = start of Bharani at exactly 13°20'.
        n = nak.of_longitude(13.0 + 20.0 / 60.0)
        self.assertEqual(n.name, "Bharani")
        self.assertEqual(n.lord, const.VENUS)
        self.assertEqual(n.pada, 1)

    def test_just_before_bharani_is_ashwini_pada_4(self):
        # 13°19' is still in Ashwini's last pada.
        n = nak.of_longitude(13.0 + 19.0 / 60.0)
        self.assertEqual(n.name, "Ashwini")
        self.assertEqual(n.pada, 4)

    def test_360_wraps_to_ashwini(self):
        n = nak.of_longitude(360.0)
        self.assertEqual(n.name, "Ashwini")

    def test_negative_longitude_wraps(self):
        # -1° should map to ~359° → Revati.
        n = nak.of_longitude(-1.0)
        self.assertEqual(n.name, "Revati")

    def test_nan_raises(self):
        with self.assertRaises(ValueError):
            nak.of_longitude(float("nan"))

    def test_inf_raises(self):
        with self.assertRaises(ValueError):
            nak.of_longitude(float("inf"))

    def test_all_27_nakshatras_have_correct_lords(self):
        """Spot-check the Vimshottari lord at each segment matches the cycle."""
        expected = [
            (0, const.KETU),
            (1, const.VENUS),
            (2, const.SUN),
            (3, const.MOON),
            (4, const.MARS),
            (5, const.RAHU),
            (6, const.JUPITER),
            (7, const.SATURN),
            (8, const.MERCURY),
            (9, const.KETU),  # cycle repeats
            (18, const.KETU),  # third cycle
            (26, const.MERCURY),  # last nakshatra
        ]
        for idx, lord in expected:
            mid_lon = (idx + 0.5) * nak.NAKSHATRA_SPAN_DEG
            n = nak.of_longitude(mid_lon)
            self.assertEqual(n.lord, lord, f"Nakshatra {idx} ({n.name})")


class NakshatraPadaTests(unittest.TestCase):
    """4 padas per nakshatra of 3°20' each."""

    def test_pada_at_each_quarter_in_ashwini(self):
        # Ashwini starts at 0°. Padas: 1@0-3°20', 2@3°20-6°40', 3@6°40-10°, 4@10°-13°20'.
        cases = [
            (0.5, 1),
            (3.0, 1),
            (3.5, 2),
            (6.0, 2),
            (7.0, 3),
            (9.0, 3),
            (10.5, 4),
            (13.0, 4),
        ]
        for lon, expected_pada in cases:
            n = nak.of_longitude(lon)
            self.assertEqual(n.pada, expected_pada, f"lon={lon}")

    def test_padas_repeat_in_each_nakshatra(self):
        # Bharani's pada 1 starts at 13°20'.
        b1 = nak.of_longitude(13.0 + 20.0 / 60.0 + 0.1)
        self.assertEqual(b1.name, "Bharani")
        self.assertEqual(b1.pada, 1)


class JanmaNakshatraTests(unittest.TestCase):
    """Birth-star computation against a real chart."""

    def test_natal_moon_nakshatra_sidereal_chart(self):
        date = Datetime("1947/08/15", "00:00", "+05:30")
        pos = GeoPos("28n36", "77e12")  # Delhi
        chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        n = nak.janma_nakshatra(chart)
        # Internal consistency: the Moon's sidereal lon should map to
        # the returned nakshatra.
        moon_lon = chart.getObject(const.MOON).lon
        self.assertEqual(n, nak.of_longitude(moon_lon))

    def test_natal_moon_nakshatra_tropical_with_ayanamsa(self):
        date = Datetime("1947/08/15", "00:00", "+05:30")
        pos = GeoPos("28n36", "77e12")
        tropical_chart = Chart(date, pos)
        sidereal_chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL)
        # The natal nakshatra should be the same whether we ask via a
        # tropical chart (with ayanamsa applied) or via a sidereal chart.
        n_from_tropical = nak.janma_nakshatra(tropical_chart)
        n_from_sidereal = nak.janma_nakshatra(sidereal_chart)
        self.assertEqual(n_from_tropical.name, n_from_sidereal.name)
        self.assertEqual(n_from_tropical.pada, n_from_sidereal.pada)


class TarabalaTests(unittest.TestCase):
    def test_self_to_self_is_1(self):
        ashwini = nak.of_longitude(0.0)
        self.assertEqual(nak.tarabala(ashwini, ashwini), 1)

    def test_natal_to_next_is_2(self):
        natal = nak.of_longitude(0.0)  # Ashwini
        transit = nak.of_longitude(15.0)  # Bharani
        self.assertEqual(nak.tarabala(natal, transit), 2)

    def test_natal_to_9_forward_is_9(self):
        natal = nak.of_longitude(0.0)
        transit = nak.of_longitude(8 * nak.NAKSHATRA_SPAN_DEG + 1.0)  # Ashlesha
        self.assertEqual(nak.tarabala(natal, transit), 9)

    def test_natal_to_10_forward_wraps_to_1(self):
        natal = nak.of_longitude(0.0)
        transit = nak.of_longitude(9 * nak.NAKSHATRA_SPAN_DEG + 1.0)  # Magha
        self.assertEqual(nak.tarabala(natal, transit), 1)


class FrozenDataclassTests(unittest.TestCase):
    def test_nakshatra_is_frozen(self):
        # `frozen=True` dataclasses raise `dataclasses.FrozenInstanceError`
        # (a subclass of AttributeError) on attribute assignment.
        n = nak.of_longitude(0.0)
        with self.assertRaises(AttributeError):
            n.name = "Bharani"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()

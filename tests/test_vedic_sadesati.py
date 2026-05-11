"""Tests for Vedic Sade Sati — Task 022."""

import unittest

from mayaastrolib import const
from mayaastrolib.datetime import Datetime
from mayaastrolib.vedic import sadesati as ss


class PhaseLogicTests(unittest.TestCase):
    """The core phase mapping, tested directly without the ephemeris."""

    def test_saturn_in_moon_sign_is_peak(self):
        # diff 0 → peak.
        self.assertEqual(ss._phase_for_diff(5, 5), ss.PHASE_PEAK)

    def test_saturn_12th_from_moon_is_rising(self):
        # Saturn in the 12th from Moon → diff (saturn - moon) % 12 == 11.
        # If Moon at sign 5, the 12th-from is sign 4.
        self.assertEqual(ss._phase_for_diff(4, 5), ss.PHASE_RISING)

    def test_saturn_2nd_from_moon_is_setting(self):
        # 2nd-from-Moon → diff == 1. Moon at 5 → 2nd-from is sign 6.
        self.assertEqual(ss._phase_for_diff(6, 5), ss.PHASE_SETTING)

    def test_saturn_far_from_moon_is_not_active(self):
        # Moon at 5, Saturn at 0 → diff 7 → not active.
        self.assertEqual(ss._phase_for_diff(0, 5), ss.PHASE_NONE)

    def test_wraparound_rising(self):
        # Moon at Aries (0), 12th-from is Pisces (11). Saturn at 11 → rising.
        self.assertEqual(ss._phase_for_diff(11, 0), ss.PHASE_RISING)


class SignNormalisationTests(unittest.TestCase):
    def test_int_passthrough(self):
        self.assertEqual(ss._normalise_sign(5), 5)

    def test_int_wraps(self):
        self.assertEqual(ss._normalise_sign(14), 2)

    def test_sign_name(self):
        self.assertEqual(ss._normalise_sign(const.ARIES), 0)
        self.assertEqual(ss._normalise_sign(const.PISCES), 11)

    def test_unknown_sign_name_raises(self):
        with self.assertRaises(ValueError):
            ss._normalise_sign("Ophiuchus")


class SaturnSiderealSignTests(unittest.TestCase):
    """Pinned values — Saturn's sidereal sign at known dates (Lahiri)."""

    def test_saturn_2024_06_is_aquarius(self):
        d = Datetime("2024/06/01", "12:00", "+00:00")
        self.assertEqual(ss.saturn_sidereal_sign(d), const.LIST_SIGNS.index(const.AQUARIUS))

    def test_saturn_2025_06_is_pisces(self):
        d = Datetime("2025/06/01", "12:00", "+00:00")
        self.assertEqual(ss.saturn_sidereal_sign(d), const.LIST_SIGNS.index(const.PISCES))

    def test_saturn_2020_01_is_sagittarius(self):
        d = Datetime("2020/01/01", "12:00", "+00:00")
        self.assertEqual(ss.saturn_sidereal_sign(d), const.LIST_SIGNS.index(const.SAGITTARIUS))


class SadeSatiTests(unittest.TestCase):
    """End-to-end with pinned Saturn positions."""

    def test_peak_when_saturn_in_moon_sign(self):
        # Saturn in Aquarius (2024-06-01); natal Moon in Aquarius → peak.
        d = Datetime("2024/06/01", "12:00", "+00:00")
        result = ss.sade_sati(const.AQUARIUS, d)
        self.assertTrue(result.active)
        self.assertEqual(result.phase, ss.PHASE_PEAK)
        self.assertEqual(result.severity, "intense")
        self.assertEqual(result.saturn_sign, const.AQUARIUS)
        self.assertEqual(result.natal_moon_sign, const.AQUARIUS)

    def test_rising_when_saturn_12th_from_moon(self):
        # Saturn in Pisces (2025-06-01); natal Moon in Aries → Saturn is
        # in the 12th from Moon → rising.
        d = Datetime("2025/06/01", "12:00", "+00:00")
        result = ss.sade_sati(const.ARIES, d)
        self.assertTrue(result.active)
        self.assertEqual(result.phase, ss.PHASE_RISING)
        self.assertEqual(result.severity, "moderate")

    def test_setting_when_saturn_2nd_from_moon(self):
        # Saturn in Aquarius (2024-06-01); natal Moon in Capricorn →
        # Saturn is in the 2nd from Moon → setting.
        d = Datetime("2024/06/01", "12:00", "+00:00")
        result = ss.sade_sati(const.CAPRICORN, d)
        self.assertTrue(result.active)
        self.assertEqual(result.phase, ss.PHASE_SETTING)
        self.assertEqual(result.severity, "mild")

    def test_not_active_when_saturn_far_from_moon(self):
        # Saturn in Aquarius (2024-06-01); natal Moon in Leo → diff 6 → none.
        d = Datetime("2024/06/01", "12:00", "+00:00")
        result = ss.sade_sati(const.LEO, d)
        self.assertFalse(result.active)
        self.assertEqual(result.phase, ss.PHASE_NONE)
        self.assertEqual(result.severity, "none")

    def test_int_and_sign_name_inputs_agree(self):
        d = Datetime("2024/06/01", "12:00", "+00:00")
        by_name = ss.sade_sati(const.AQUARIUS, d)
        by_idx = ss.sade_sati(const.LIST_SIGNS.index(const.AQUARIUS), d)
        self.assertEqual(by_name, by_idx)


class SadeSatiForYearTests(unittest.TestCase):
    def test_for_year_uses_mid_year(self):
        # July 1, 2024 → Saturn in Aquarius; natal Moon Aquarius → peak.
        result = ss.sade_sati_for_year(const.AQUARIUS, 2024)
        self.assertEqual(result.phase, ss.PHASE_PEAK)


class SmallPanotiTests(unittest.TestCase):
    def test_ashtama_shani(self):
        # Saturn in Aquarius (sign 10) on 2024-06-01. 8th-from-Moon means
        # diff 7 → Moon at (10 - 7) % 12 = 3 = Cancer.
        d = Datetime("2024/06/01", "12:00", "+00:00")
        self.assertEqual(ss.small_panoti(const.CANCER, d), "ashtama_shani")

    def test_kantaka_shani(self):
        # diff 3 → Moon at (10 - 3) % 12 = 7 = Scorpio.
        d = Datetime("2024/06/01", "12:00", "+00:00")
        self.assertEqual(ss.small_panoti(const.SCORPIO, d), "kantaka_shani")

    def test_none_when_not_in_a_panoti(self):
        d = Datetime("2024/06/01", "12:00", "+00:00")
        # Moon in Aquarius → diff 0 → that's Sade Sati peak, not a panoti.
        self.assertIsNone(ss.small_panoti(const.AQUARIUS, d))


class FrozenDataclassTests(unittest.TestCase):
    def test_phase_is_frozen(self):
        d = Datetime("2024/06/01", "12:00", "+00:00")
        result = ss.sade_sati(const.LEO, d)
        with self.assertRaises(AttributeError):
            result.phase = "peak"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()

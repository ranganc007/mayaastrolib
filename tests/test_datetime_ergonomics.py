"""Tests for Datetime classmethods added in Task 007."""

import datetime as pydt
import unittest

from mayaastrolib.datetime import Datetime


class FromPyDatetimeTests(unittest.TestCase):
    def test_aware_datetime_uses_its_own_offset(self):
        dt = pydt.datetime(2015, 3, 13, 17, 0, tzinfo=pydt.timezone.utc)
        mdate = Datetime.from_pydatetime(dt)
        self.assertEqual(mdate.date.toString(), "2015/03/13")
        self.assertEqual(mdate.time.toString(), "17:00:00")
        self.assertEqual(mdate.utcoffset.toString(), "00:00:00")

    def test_naive_datetime_requires_explicit_offset(self):
        dt = pydt.datetime(2015, 3, 13, 17, 0)
        with self.assertRaises(ValueError):
            Datetime.from_pydatetime(dt)

    def test_naive_datetime_with_offset(self):
        dt = pydt.datetime(2015, 3, 13, 17, 0)
        mdate = Datetime.from_pydatetime(dt, utcoffset="+00:00")
        self.assertEqual(mdate.date.toString(), "2015/03/13")
        self.assertEqual(mdate.time.toString(), "17:00:00")

    def test_offset_with_minutes(self):
        # India is +05:30 — half-hour offsets must work.
        dt = pydt.datetime(2015, 3, 13, 17, 0)
        mdate = Datetime.from_pydatetime(dt, utcoffset="+05:30")
        self.assertEqual(mdate.utcoffset.toString(), "05:30:00")

    def test_negative_offset(self):
        dt = pydt.datetime(2015, 3, 13, 17, 0)
        mdate = Datetime.from_pydatetime(dt, utcoffset="-08:00")
        # Time class formats negative offsets with leading minus
        self.assertTrue(mdate.utcoffset.toString().startswith("-08"))

    def test_aware_datetime_with_explicit_offset_converts(self):
        # dt is in UTC; we ask for the same instant expressed in +05:30.
        # The wall-clock time should advance by 5h30m.
        dt = pydt.datetime(2015, 3, 13, 12, 0, tzinfo=pydt.timezone.utc)
        mdate = Datetime.from_pydatetime(dt, utcoffset="+05:30")
        self.assertEqual(mdate.date.toString(), "2015/03/13")
        self.assertEqual(mdate.time.toString(), "17:30:00")
        self.assertEqual(mdate.utcoffset.toString(), "05:30:00")


class NowTests(unittest.TestCase):
    def test_now_default_is_utc(self):
        mdate = Datetime.now()
        self.assertEqual(mdate.utcoffset.toString(), "00:00:00")

    def test_now_returns_datetime_close_to_actual_now(self):
        before = pydt.datetime.now(pydt.timezone.utc)
        mdate = Datetime.now()
        after = pydt.datetime.now(pydt.timezone.utc)

        py_mdate = mdate.to_pydatetime()
        # Allow for the second-rounding loss in either direction.
        self.assertLessEqual(before - pydt.timedelta(seconds=1), py_mdate)
        self.assertLessEqual(py_mdate, after + pydt.timedelta(seconds=1))

    def test_now_with_offset_preserves_offset(self):
        mdate = Datetime.now(utcoffset="+05:30")
        self.assertEqual(mdate.utcoffset.toString(), "05:30:00")


class RoundTripTests(unittest.TestCase):
    def test_from_pydatetime_to_pydatetime_roundtrip(self):
        original = pydt.datetime(
            2015,
            3,
            13,
            17,
            30,
            45,
            tzinfo=pydt.timezone(pydt.timedelta(hours=5, minutes=30)),
        )
        mdate = Datetime.from_pydatetime(original)
        result = mdate.to_pydatetime()

        self.assertEqual(original.year, result.year)
        self.assertEqual(original.month, result.month)
        self.assertEqual(original.day, result.day)
        self.assertEqual(original.hour, result.hour)
        self.assertEqual(original.minute, result.minute)
        self.assertEqual(original.second, result.second)
        self.assertEqual(original.utcoffset(), result.utcoffset())

    def test_microseconds_are_dropped(self):
        # Documented behaviour: from_pydatetime rounds to whole seconds.
        original = pydt.datetime(2015, 3, 13, 17, 30, 45, 999_999, tzinfo=pydt.timezone.utc)
        mdate = Datetime.from_pydatetime(original)
        result = mdate.to_pydatetime()
        self.assertEqual(result.microsecond, 0)


if __name__ == "__main__":
    unittest.main()

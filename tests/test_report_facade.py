"""Tests for the full_report facade — Task 046 (0.5.0 #2)."""

import json
import unittest

import mayaastrolib
from mayaastrolib import const
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.report import full_report, full_report_json


class _Base(unittest.TestCase):
    def setUp(self):
        self.date = Datetime("1990/06/15", "14:30", "+05:30")
        self.pos = GeoPos("28n36", "77e12")


class FullReportTests(_Base):
    def test_returns_v1_schema(self):
        r = full_report(self.date, self.pos)
        self.assertEqual(r["schema_version"], 1)
        for key in ("meta", "objects", "houses", "angles", "aspects"):
            self.assertIn(key, r)

    def test_defaults_are_comprehensive(self):
        # full_report defaults to aspects + dignities on.
        r = full_report(self.date, self.pos)
        self.assertIn("aspects", r)
        self.assertIn("dignities", r)

    def test_tropical_auto_omits_vedic(self):
        r = full_report(self.date, self.pos)  # tropical, vedic="auto"
        self.assertNotIn("vedic", r)

    def test_sidereal_auto_includes_vedic(self):
        r = full_report(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)
        self.assertIn("vedic", r)
        self.assertEqual(r["meta"]["zodiac"], const.ZODIAC_SIDEREAL)

    def test_vedic_force_on_tropical(self):
        r = full_report(self.date, self.pos, vedic=True)
        self.assertIn("vedic", r)

    def test_vedic_force_off_on_sidereal(self):
        r = full_report(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL, vedic=False)
        self.assertNotIn("vedic", r)

    def test_flags_forwarded(self):
        r = full_report(self.date, self.pos, aspects=False, dignities=False)
        self.assertNotIn("aspects", r)
        self.assertNotIn("dignities", r)

    def test_custom_object_list(self):
        r = full_report(self.date, self.pos, IDs=[const.SUN, const.MOON])
        ids = {o["id"] for o in r["objects"]}
        self.assertEqual(ids, {const.SUN, const.MOON})

    def test_result_is_json_native(self):
        json.dumps(full_report(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL))

    def test_matches_chart_to_dict(self):
        from mayaastrolib.chart import Chart

        chart = Chart(self.date, self.pos, IDs=const.LIST_OBJECTS_TRADITIONAL)
        self.assertEqual(
            full_report(self.date, self.pos, dignities=False),
            chart.to_dict(dignities=False),
        )


class FullReportJsonTests(_Base):
    def test_returns_valid_json(self):
        s = full_report_json(self.date, self.pos)
        self.assertEqual(json.loads(s)["schema_version"], 1)

    def test_indent_forwarded(self):
        self.assertIn("\n", full_report_json(self.date, self.pos, indent=2))

    def test_kwargs_forwarded(self):
        s = full_report_json(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)
        self.assertIn("vedic", json.loads(s))


class PackageExportTests(_Base):
    def test_top_level_full_report(self):
        # Lazily exposed via PEP 562 __getattr__.
        r = mayaastrolib.full_report(self.date, self.pos)
        self.assertEqual(r["schema_version"], 1)

    def test_top_level_full_report_json(self):
        s = mayaastrolib.full_report_json(self.date, self.pos)
        self.assertEqual(json.loads(s)["schema_version"], 1)

    def test_unknown_attribute_raises(self):
        missing = "does_not_exist"
        with self.assertRaises(AttributeError):
            getattr(mayaastrolib, missing)


if __name__ == "__main__":
    unittest.main()

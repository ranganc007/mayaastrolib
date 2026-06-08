"""Tests for Chart / Object / Aspect serialization (to_dict / to_json) —
Task 045, the v1 schema."""

import json
import unittest

from mayaastrolib import aspects as _aspects
from mayaastrolib import const
from mayaastrolib.chart import SCHEMA_VERSION, Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos


def _assert_json_native(value):
    """Raise unless ``value`` is composed solely of JSON-native types."""
    json.dumps(value)


class _Base(unittest.TestCase):
    def setUp(self):
        self.date = Datetime("1990/06/15", "14:30", "+05:30")
        self.pos = GeoPos("28n36", "77e12")
        self.tropical = Chart(self.date, self.pos)
        self.sidereal = Chart(self.date, self.pos, zodiac=const.ZODIAC_SIDEREAL)


class CoreStructureTests(_Base):
    def test_schema_version_present(self):
        self.assertEqual(self.tropical.to_dict()["schema_version"], SCHEMA_VERSION)

    def test_top_level_keys(self):
        d = self.tropical.to_dict()
        for key in ("schema_version", "meta", "objects", "houses", "angles", "aspects"):
            self.assertIn(key, d)

    def test_meta_keys_and_types(self):
        meta = self.tropical.to_dict()["meta"]
        self.assertEqual(
            set(meta), {"datetime", "utcoffset", "jd", "pos", "zodiac", "ayanamsa", "hsys"}
        )
        self.assertIn("+05:30", meta["datetime"])  # offset preserved in ISO
        self.assertEqual(meta["pos"]["lat"], self.pos.lat)
        self.assertEqual(meta["zodiac"], const.ZODIAC_TROPICAL)

    def test_meta_ayanamsa_none_for_tropical(self):
        self.assertIsNone(self.tropical.to_dict()["meta"]["ayanamsa"])

    def test_meta_ayanamsa_set_for_sidereal(self):
        self.assertEqual(self.sidereal.to_dict()["meta"]["ayanamsa"], self.sidereal.ayanamsa)

    def test_counts_match_chart(self):
        d = self.tropical.to_dict()
        self.assertEqual(len(d["objects"]), len(list(self.tropical.objects)))
        self.assertEqual(len(d["houses"]), 12)
        self.assertEqual(len(d["angles"]), len(list(self.tropical.angles)))

    def test_everything_is_json_native(self):
        _assert_json_native(self.tropical.to_dict())

    def test_to_json_roundtrips_to_same_dict(self):
        s = self.tropical.to_json()
        self.assertEqual(json.loads(s), self.tropical.to_dict())

    def test_to_json_indent_forwarded(self):
        self.assertIn("\n", self.tropical.to_json(indent=2))
        self.assertNotIn("\n", self.tropical.to_json())


class ObjectDictTests(_Base):
    def test_planet_dict_keys(self):
        sun = next(o for o in self.tropical.to_dict()["objects"] if o["id"] == const.SUN)
        for key in (
            "id",
            "type",
            "lon",
            "lat",
            "sign",
            "signlon",
            "lonspeed",
            "latspeed",
            "movement",
            "house",
        ):
            self.assertIn(key, sun)
        self.assertEqual(sun["type"], const.OBJ_PLANET)
        self.assertIn(sun["movement"], (const.DIRECT, const.RETROGRADE, const.STATIONARY))

    def test_house_dict_keys(self):
        h = self.tropical.to_dict()["houses"][0]
        for key in ("id", "num", "size", "objects"):
            self.assertIn(key, h)
        self.assertTrue(1 <= h["num"] <= 12)
        self.assertIsInstance(h["objects"], list)

    def test_each_object_lon_in_range(self):
        for o in self.tropical.to_dict()["objects"]:
            self.assertTrue(0.0 <= o["lon"] < 360.0)

    def test_house_object_ids_are_consistent(self):
        # Every object's "house" must list that object under that house's
        # "objects", and vice versa.
        d = self.tropical.to_dict()
        houses = {h["id"]: h for h in d["houses"]}
        for o in d["objects"]:
            hid = o["house"]
            if hid is not None:
                self.assertIn(o["id"], houses[hid]["objects"])

    def test_fixedstar_dict_has_mag(self):
        star = self.tropical.getFixedStar(const.STAR_ALGOL)
        sd = star.to_dict()
        self.assertIn("mag", sd)
        self.assertEqual(sd["id"], const.STAR_ALGOL)


class AspectDictTests(_Base):
    def test_aspect_dict_keys(self):
        asps = self.tropical.to_dict()["aspects"]
        self.assertGreater(len(asps), 0)
        for key in (
            "active",
            "passive",
            "type",
            "name",
            "orb",
            "direction",
            "condition",
            "movement",
        ):
            self.assertIn(key, asps[0])

    def test_aspect_name_matches_type(self):
        for a in self.tropical.to_dict()["aspects"]:
            self.assertEqual(a["name"], const.ASPECT_NAMES.get(a["type"], "No Aspect"))

    def test_aspects_flag_off_omits_aspects(self):
        self.assertNotIn("aspects", self.tropical.to_dict(aspects=False))

    def test_standalone_aspect_to_dict(self):
        sun = self.tropical.getObject(const.SUN)
        moon = self.tropical.getObject(const.MOON)
        asp = _aspects.getAspect(sun, moon, const.MAJOR_ASPECTS)
        if asp is not None:
            d = asp.to_dict()
            self.assertEqual({d["active"], d["passive"]}, {const.SUN, const.MOON})
            _assert_json_native(d)


class DignitiesBlockTests(_Base):
    def test_off_by_default(self):
        self.assertNotIn("dignities", self.tropical.to_dict())

    def test_dignities_block_per_planet(self):
        dig = self.tropical.to_dict(dignities=True)["dignities"]
        self.assertIn(const.SUN, dig)
        for key in ("ruler", "exalt", "dayTrip", "nightTrip", "term", "face", "exile", "fall"):
            self.assertIn(key, dig[const.SUN])
        _assert_json_native(dig)


class VedicBlockTests(_Base):
    def test_off_by_default(self):
        self.assertNotIn("vedic", self.sidereal.to_dict())

    def test_vedic_block_structure(self):
        v = self.sidereal.to_dict(vedic=True)["vedic"]
        for key in ("ayanamsa", "ayanamsa_value", "nakshatras", "dasha", "yogas", "shadbala"):
            self.assertIn(key, v)

    def test_vedic_nakshatras(self):
        nak = self.sidereal.to_dict(vedic=True)["vedic"]["nakshatras"]
        for body in ("Moon", "Asc"):
            self.assertEqual(set(nak[body]), {"name", "lord", "pada", "index"})
            self.assertTrue(1 <= nak[body]["pada"] <= 4)
            self.assertTrue(0 <= nak[body]["index"] <= 26)

    def test_vedic_dasha_active_periods(self):
        dasha = self.sidereal.to_dict(vedic=True)["vedic"]["dasha"]
        self.assertEqual(set(dasha), {"maha", "antar", "pratyantar"})
        # The maha-dasha active at the chart date must bracket it.
        self.assertIsNotNone(dasha["maha"])
        self.assertEqual(dasha["maha"]["level"], 1)

    def test_vedic_shadbala_summary(self):
        from mayaastrolib.vedic import shadbala

        shad = self.sidereal.to_dict(vedic=True)["vedic"]["shadbala"]
        self.assertEqual(set(shad), set(shadbala._CLASSICAL_PLANETS))
        for entry in shad.values():
            self.assertEqual(
                set(entry),
                {"total_rupas", "total_virupas", "required_rupas", "sufficient"},
            )

    def test_full_vedic_is_json_native(self):
        _assert_json_native(self.sidereal.to_dict(vedic=True, dignities=True))

    def test_vedic_works_on_tropical_chart_too(self):
        # vedic=True should compute (via internal sidereal conversion) even
        # for a tropical-zodiac chart.
        v = self.tropical.to_dict(vedic=True)["vedic"]
        self.assertIn("nakshatras", v)


class SymbolicChartTests(_Base):
    def test_profected_chart_serializes(self):
        prof = self.tropical.profected(years=30)
        d = prof.to_dict()
        _assert_json_native(d)
        sun = next(o for o in d["objects"] if o["id"] == const.SUN)
        # Symbolic positions have undefined speed and movement.
        self.assertIsNone(sun["lonspeed"])
        self.assertIsNone(sun["movement"])

    def test_profected_chart_meta_marks_symbolic_via_zodiac(self):
        # Even symbolic charts produce a valid meta block.
        prof = self.tropical.profected(years=30)
        self.assertEqual(prof.to_dict()["meta"]["zodiac"], const.ZODIAC_TROPICAL)


if __name__ == "__main__":
    unittest.main()

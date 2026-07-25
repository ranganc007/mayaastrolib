"""Public-API surface tests — Task v1.0-05.

These make `docs/API-STABILITY.md` binding rather than aspirational. They
fail if the declared surface and the real one drift apart, which is the
failure mode the 1.0 stability contract exists to prevent.
"""

from __future__ import annotations

import importlib
import subprocess
import sys
import unittest

import mayaastrolib

# Modules that declare a frozen public surface. Keep in sync with
# docs/API-STABILITY.md.
CORE_MODULES = [
    "mayaastrolib.aio",
    "mayaastrolib.angle",
    "mayaastrolib.aspects",
    "mayaastrolib.chart",
    "mayaastrolib.const",
    "mayaastrolib.datetime",
    "mayaastrolib.geopos",
    "mayaastrolib.lists",
    "mayaastrolib.object",
    "mayaastrolib.props",
    "mayaastrolib.report",
    "mayaastrolib.utils",
]

VEDIC_MODULES = [
    f"mayaastrolib.vedic.{name}"
    for name in (
        "ashtakavarga",
        "ayanamsa",
        "dasha",
        "divisional",
        "kp",
        "nakshatras",
        "sadesati",
        "shadbala",
        "tajika",
        "tajika_aspects",
        "tajika_bala",
        "upagrahas",
        "yogas",
    )
]

ALL_MODULES = CORE_MODULES + VEDIC_MODULES

# The frozen top-level surface, per docs/API-STABILITY.md.
TOP_LEVEL_SURFACE = {
    "__version__",
    "PATH_LIB",
    "PATH_RES",
    "Chart",
    "Datetime",
    "GeoPos",
    "const",
    "full_report",
    "full_report_json",
}

# Modules deliberately NOT part of the contract (API-STABILITY.md "Not public").
INTERNAL_MODULES = [
    "mayaastrolib.ephem.swe",
    "mayaastrolib.dignities.essential",
    "mayaastrolib.predictives.returns",
    "mayaastrolib.protocols.temperament",
    "mayaastrolib.tools.arabicparts",
]


class AllDeclaredTests(unittest.TestCase):
    def test_every_public_module_declares_all(self):
        for name in ALL_MODULES:
            with self.subTest(module=name):
                mod = importlib.import_module(name)
                self.assertTrue(
                    hasattr(mod, "__all__"),
                    f"{name} is public but does not declare __all__",
                )

    def test_every_name_in_all_exists(self):
        for name in ALL_MODULES:
            mod = importlib.import_module(name)
            for symbol in mod.__all__:
                with self.subTest(module=name, symbol=symbol):
                    self.assertTrue(
                        hasattr(mod, symbol),
                        f"{name}.__all__ lists {symbol!r}, which does not exist",
                    )

    def test_all_entries_are_unique_strings(self):
        for name in ALL_MODULES:
            mod = importlib.import_module(name)
            with self.subTest(module=name):
                self.assertTrue(all(isinstance(s, str) for s in mod.__all__))
                self.assertEqual(
                    len(mod.__all__),
                    len(set(mod.__all__)),
                    f"{name}.__all__ has duplicate entries",
                )

    def test_star_import_yields_only_declared_names(self):
        # `from mayaastrolib.chart import *` must import exactly __all__.
        namespace: dict[str, object] = {}
        exec("from mayaastrolib.chart import *", namespace)  # noqa: S102
        imported = {k for k in namespace if not k.startswith("__")}
        self.assertEqual(imported, set(mayaastrolib.chart.__all__))


class TopLevelSurfaceTests(unittest.TestCase):
    def test_top_level_all_matches_the_document(self):
        self.assertEqual(set(mayaastrolib.__all__), TOP_LEVEL_SURFACE)

    def test_every_top_level_name_resolves(self):
        for symbol in mayaastrolib.__all__:
            with self.subTest(symbol=symbol):
                self.assertIsNotNone(getattr(mayaastrolib, symbol))

    def test_dir_exposes_the_surface(self):
        self.assertTrue(TOP_LEVEL_SURFACE.issubset(set(dir(mayaastrolib))))

    def test_unknown_attribute_raises_attribute_error(self):
        with self.assertRaises(AttributeError):
            getattr(mayaastrolib, "definitely_not_a_real_name")  # noqa: B009

    def test_lazy_export_is_cached_after_first_access(self):
        # __getattr__ writes the resolved value into globals(), so a second
        # access must return the identical object.
        self.assertIs(mayaastrolib.Chart, mayaastrolib.Chart)

    def test_internal_modules_declare_no_public_surface(self):
        # These are reachable but explicitly outside the contract. If one
        # grows an __all__, it is being promoted — update API-STABILITY.md.
        for name in INTERNAL_MODULES:
            with self.subTest(module=name):
                mod = importlib.import_module(name)
                self.assertFalse(
                    hasattr(mod, "__all__"),
                    f"{name} declares __all__ but API-STABILITY.md lists it as internal",
                )


class LazyImportTests(unittest.TestCase):
    def test_importing_the_package_does_not_load_swisseph(self):
        """`import mayaastrolib` must not pull in the calculation stack.

        Run in a subprocess because this process has already imported
        swisseph via the other tests. This property is part of the contract:
        metadata-only and const-only consumers pay no startup cost.
        """
        code = "import sys, mayaastrolib; print('swisseph' in sys.modules)"
        out = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True, check=True
        )
        self.assertEqual(out.stdout.strip(), "False")

    def test_touching_chart_does_load_swisseph(self):
        # The mirror of the above: the laziness is real, not an accident of
        # swisseph never being needed.
        code = "import sys, mayaastrolib; mayaastrolib.Chart; print('swisseph' in sys.modules)"
        out = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True, check=True
        )
        self.assertEqual(out.stdout.strip(), "True")


class ReadmeQuickStartTests(unittest.TestCase):
    """Pins the exact snippet the README shows a new user."""

    def test_readme_quick_start_runs(self):
        from mayaastrolib import const
        from mayaastrolib.chart import Chart
        from mayaastrolib.datetime import Datetime
        from mayaastrolib.geopos import GeoPos

        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        chart = Chart(date, pos)

        sun = chart.get(const.SUN)
        self.assertEqual(sun.id, const.SUN)
        self.assertEqual(str(sun), "<Sun Pisces +22:47:25 +00:59:51>")

    def test_quick_start_also_works_off_the_top_level(self):
        # The convenience form promised by API-STABILITY.md.
        from mayaastrolib import Chart, Datetime, GeoPos, const

        chart = Chart(Datetime("2015/03/13", "17:00", "+00:00"), GeoPos("38n32", "8w54"))
        self.assertEqual(chart.get(const.SUN).sign, const.PISCES)

    def test_full_report_facade_is_reachable_from_top_level(self):
        report = mayaastrolib.full_report(
            mayaastrolib.Datetime("2015/03/13", "17:00", "+00:00"),
            mayaastrolib.GeoPos("38n32", "8w54"),
        )
        self.assertEqual(report["schema_version"], mayaastrolib.chart.SCHEMA_VERSION)


if __name__ == "__main__":
    unittest.main()

"""
This file is part of mayaastrolib, a fork of flatlib - (C) FlatAngle
Author: João Ventura (flatangleweb@gmail.com)

"""

import os as _os
from importlib.metadata import PackageNotFoundError as _PackageNotFoundError
from importlib.metadata import version as _pkg_version

try:
    __version__ = _pkg_version("mayaastrolib")
except _PackageNotFoundError:
    __version__ = "0.0.0+unknown"

# Library and resource paths
PATH_LIB = _os.path.dirname(__file__) + _os.sep
PATH_RES = PATH_LIB + "resources" + _os.sep


# The frozen public surface of the top-level package. See
# docs/API-STABILITY.md — everything here is covered by the 1.0 stability
# contract. Names are resolved lazily by __getattr__ below.
__all__ = [
    # Metadata
    "__version__",
    "PATH_LIB",
    "PATH_RES",
    # Everyday entry points
    "Chart",
    "Datetime",
    "GeoPos",
    "const",
    # High-level facade
    "full_report",
    "full_report_json",
]

# name -> (submodule, attribute). A None attribute means "the submodule
# itself". Every entry is deferred so that `import mayaastrolib` does not
# pull in the calculation stack — and therefore does not load swisseph or
# the ~6 MB of ephemeris data. Consumers who only need the version, the
# resource paths, or the constants pay nothing for the rest.
_LAZY_EXPORTS = {
    "Chart": ("chart", "Chart"),
    "Datetime": ("datetime", "Datetime"),
    "GeoPos": ("geopos", "GeoPos"),
    "const": ("const", None),
    "full_report": ("report", "full_report"),
    "full_report_json": ("report", "full_report_json"),
}


def __getattr__(name):
    """Resolve the public top-level names on first access (PEP 562).

    Keeping these lazy is deliberate: ``import mayaastrolib`` must stay
    swisseph-free, so the everyday entry points cannot be eagerly imported
    here. See ``_LAZY_EXPORTS`` and ``docs/API-STABILITY.md``.
    """
    try:
        module_name, attr = _LAZY_EXPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None

    import importlib

    module = importlib.import_module(f".{module_name}", __name__)
    value = module if attr is None else getattr(module, attr)
    globals()[name] = value  # cache: __getattr__ is not consulted again
    return value


def __dir__():
    """Make the lazy exports discoverable to ``dir()`` and tab-completion."""
    return sorted(set(globals()) | set(__all__))

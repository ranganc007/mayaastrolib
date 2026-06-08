"""
This file is part of mayaastrolib, a fork of flatlib - (C) FlatAngle
Author: João Ventura (flatangleweb@gmail.com)

"""

import os
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

try:
    __version__ = _pkg_version("mayaastrolib")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

# Library and resource paths
PATH_LIB = os.path.dirname(__file__) + os.sep
PATH_RES = PATH_LIB + "resources" + os.sep


def __getattr__(name):
    """Lazily expose the high-level facade at the package top level.

    ``mayaastrolib.full_report`` / ``full_report_json`` resolve on first
    access without importing the (swisseph-loading) calculation stack at
    ``import mayaastrolib`` time — so Western-only and metadata-only users
    pay no startup cost.
    """
    if name in ("full_report", "full_report_json"):
        from . import report

        return getattr(report, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

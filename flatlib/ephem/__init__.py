"""Compatibility shim — see flatlib/__init__.py for the deprecation notice."""

import sys

from mayaastrolib.ephem import *  # noqa: F401, F403
from mayaastrolib.ephem import eph, ephem, swe, tools  # noqa: F401

sys.modules["flatlib.ephem.eph"] = eph
sys.modules["flatlib.ephem.ephem"] = ephem
sys.modules["flatlib.ephem.swe"] = swe
sys.modules["flatlib.ephem.tools"] = tools

"""Compatibility shim — see flatlib/__init__.py for the deprecation notice."""

import sys

from mayaastrolib.dignities import *  # noqa: F401, F403
from mayaastrolib.dignities import accidental, essential, tables  # noqa: F401

sys.modules["flatlib.dignities.essential"] = essential
sys.modules["flatlib.dignities.accidental"] = accidental
sys.modules["flatlib.dignities.tables"] = tables

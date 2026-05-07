"""Compatibility shim — see flatlib/__init__.py for the deprecation notice."""

import sys

from mayaastrolib.protocols import *  # noqa: F401, F403
from mayaastrolib.protocols import almutem, behavior, temperament  # noqa: F401

sys.modules["flatlib.protocols.almutem"] = almutem
sys.modules["flatlib.protocols.behavior"] = behavior
sys.modules["flatlib.protocols.temperament"] = temperament

"""Compatibility shim — see flatlib/__init__.py for the deprecation notice."""

import sys

from mayaastrolib.predictives import *  # noqa: F401, F403
from mayaastrolib.predictives import primarydirections, profections, returns  # noqa: F401

sys.modules["flatlib.predictives.primarydirections"] = primarydirections
sys.modules["flatlib.predictives.profections"] = profections
sys.modules["flatlib.predictives.returns"] = returns

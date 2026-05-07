"""Compatibility shim — see flatlib/__init__.py for the deprecation notice."""

import sys

from mayaastrolib.tools import *  # noqa: F401, F403
from mayaastrolib.tools import arabicparts, chartdynamics, planetarytime  # noqa: F401

sys.modules["flatlib.tools.arabicparts"] = arabicparts
sys.modules["flatlib.tools.chartdynamics"] = chartdynamics
sys.modules["flatlib.tools.planetarytime"] = planetarytime

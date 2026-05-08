"""
Author: João Ventura <flatangleweb@gmail.com>


This recipe shows sample code for computing
arabic parts.

"""

from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.tools import arabicparts

# Build a chart for a date and location
date = Datetime("2015/03/13", "17:00", "+00:00")
pos = GeoPos("38n32", "8w54")
chart = Chart(date, pos)

# Retrieve the Pars Spirit via the discoverable Chart method (Task 013).
# The legacy `arabicparts.getPart(arabicparts.PARS_SPIRIT, chart)` still
# works but emits a DeprecationWarning and will be removed in 1.0.
parsSpirit = chart.arabicPart(arabicparts.PARS_SPIRIT)
print(parsSpirit)  # <Pars Spirit Sagittarius +03:52:01>

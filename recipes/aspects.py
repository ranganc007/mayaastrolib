"""
Author: João Ventura <flatangleweb@gmail.com>


This recipe shows sample code for handling
aspects.

"""

from mayaastrolib import aspects, const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos

# Build a chart for a date and location
date = Datetime("2015/03/13", "17:00", "+00:00")
pos = GeoPos("38n32", "8w54")
chart = Chart(date, pos)

# Retrieve the Sun and Moon
sun = chart.get(const.SUN)
moon = chart.get(const.MOON)

# Get the aspect — returns None if no major aspect exists within orb
aspect = aspects.getAspect(sun, moon, const.MAJOR_ASPECTS)
if aspect is not None:
    print(aspect)  # <Moon Sun 90 Applicative +00:24:30>
else:
    print("No major aspect between Sun and Moon")

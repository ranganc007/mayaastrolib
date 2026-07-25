mayaastrolib documentation
==========================

mayaastrolib is a Python 3.10+ library for Traditional (Western) and Vedic astrology,
computed on the Swiss Ephemeris. It is a modernised, extended fork of flatlib.::

    >>> date = Datetime('2015/03/13', '17:00', '+00:00')
    >>> pos = GeoPos('38n32', '8w54')
    >>> chart = Chart(date, pos)

    >>> sun = chart.get(const.SUN)
    >>> print(sun)
    <Sun Pisces +22:47:25 +00:59:51>

For a sidereal (Vedic) chart, pass a zodiac and ayanamsa::

    >>> from mayaastrolib import const
    >>> chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL, ayanamsa=const.AYANAMSA_LAHIRI)


Contents
--------

.. toctree::
   :maxdepth: 2

   installation
   tutorials/index
   api/index
   faq

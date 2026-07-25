"""Nakshatra (lunar mansion) arithmetic for Vedic Jyotisha.

The 27 nakshatras divide the sidereal zodiac into equal 13°20' segments.
Each nakshatra has:

- A name (Sanskrit)
- A ruling planet ("lord") in the Vimshottari Mahadasha cycle
- 4 padas (quarters), each 3°20'

References:
- Brihat Parashara Hora Shastra (BPHS) ch. 3, 9
- Muhurta Chintamani (for tarabala)
"""

from dataclasses import dataclass

from mayaastrolib import const
from mayaastrolib.vedic import ayanamsa as _ay

__all__ = [
    "NAKSHATRA_NAMES",
    "NAKSHATRA_LORDS",
    "NAKSHATRA_SPAN_DEG",
    "PADA_SPAN_DEG",
    "Nakshatra",
    "of_longitude",
    "janma_nakshatra",
    "tarabala",
]

NAKSHATRA_NAMES = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishtha",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]

# Vimshottari rulership cycle — 9 lords, repeats 3 times across 27 nakshatras.
_VIMSHOTTARI_CYCLE = [
    const.KETU,
    const.VENUS,
    const.SUN,
    const.MOON,
    const.MARS,
    const.RAHU,
    const.JUPITER,
    const.SATURN,
    const.MERCURY,
]
NAKSHATRA_LORDS = _VIMSHOTTARI_CYCLE * 3

assert len(NAKSHATRA_NAMES) == 27
assert len(NAKSHATRA_LORDS) == 27

# Each nakshatra spans 13°20' = 360/27 degrees.
NAKSHATRA_SPAN_DEG = 360.0 / 27.0
# Each pada spans 3°20' = 13°20' / 4.
PADA_SPAN_DEG = NAKSHATRA_SPAN_DEG / 4.0


@dataclass(frozen=True)
class Nakshatra:
    """A nakshatra at a particular sidereal longitude.

    Attributes:
        name: The Sanskrit name, e.g. "Ashwini".
        lord: The Vimshottari ruling planet ID, e.g. ``const.KETU``.
        pada: Quarter index, 1..4.
        index: Zero-based index into ``NAKSHATRA_NAMES``, 0..26.
    """

    name: str
    lord: str
    pada: int
    index: int


def of_longitude(sidereal_lon):
    """Return the nakshatra at the given sidereal longitude.

    The longitude is reduced modulo 360 — callers needn't normalise first.

    Raises:
        ValueError: if ``sidereal_lon`` is non-finite (NaN or infinity).
    """
    # NaN and inf both fail this finite-check via subtraction trick.
    if sidereal_lon != sidereal_lon or (
        sidereal_lon == sidereal_lon and (sidereal_lon - sidereal_lon != 0)
    ):
        raise ValueError(f"sidereal_lon must be finite; got {sidereal_lon!r}")
    lon = sidereal_lon % 360.0
    idx = int(lon // NAKSHATRA_SPAN_DEG)
    # Pada is 1-indexed
    within = lon - idx * NAKSHATRA_SPAN_DEG
    pada = int(within // PADA_SPAN_DEG) + 1
    return Nakshatra(
        name=NAKSHATRA_NAMES[idx],
        lord=NAKSHATRA_LORDS[idx],
        pada=pada,
        index=idx,
    )


def janma_nakshatra(chart, ayanamsa=const.AYANAMSA_LAHIRI):
    """Return the natal Moon's nakshatra ("birth star").

    If ``chart.zodiac == ZODIAC_SIDEREAL``, reads the Moon's sidereal
    longitude directly. If ``chart.zodiac == ZODIAC_TROPICAL``, applies
    :func:`mayaastrolib.vedic.ayanamsa.to_sidereal` with the supplied
    ``ayanamsa`` (default Lahiri) before computing the nakshatra.

    Args:
        chart: A :class:`mayaastrolib.chart.Chart`.
        ayanamsa: Used only when the chart is tropical; ignored otherwise.
    """
    moon = chart.getObject(const.MOON)
    if chart.zodiac == const.ZODIAC_SIDEREAL:
        sid_lon = moon.lon
    else:
        sid_lon = _ay.to_sidereal(moon.lon, chart.date, ayanamsa=ayanamsa)
    return of_longitude(sid_lon)


def tarabala(natal_moon_nak, transit_moon_nak):
    """9-tara cycle position, 1..9.

    Counts nakshatras from the natal Moon's nakshatra to the transit
    Moon's nakshatra (inclusive forward), modulo 9. Per Muhurta
    Chintamani 6.6.

    The 1..9 numeric result maps to the qualitative names (Janma,
    Sampat, Vipat, Kshema, Pratyak, Sadhana, Naidhana, Mitra, Param
    Mitra), but the label-to-meaning mapping is presentational and
    lives downstream.
    """
    forward = (transit_moon_nak.index - natal_moon_nak.index) % 27
    return (forward % 9) + 1

"""Vedic yoga detection — named planetary combinations.

This module ships a focused, unambiguous set: the 5 Pancha Mahapurusha
yogas plus Gaja-Kesari, Budha-Aditya, and Chandra-Mangala. Raja/Dhana
yogas, Neecha Bhanga, Kemadruma, and the various cancellation conditions
are deferred to a follow-up.

Kendras (angular houses) are computed Whole-Sign: a planet is "in a
kendra" iff its sign is the 1st, 4th, 7th, or 10th from the Ascendant's
sign. This is the Vedic convention regardless of the chart's house
system.

References:
- BPHS ch. 75-78 (Mahapurusha and other yogas)
- Phaladeepika ch. 6-7
- Saravali ch. 33-35
"""

from dataclasses import dataclass

from mayaastrolib import const
from mayaastrolib.vedic import ayanamsa as _ay

# Sign indices, 0..11.
_ARIES, _TAURUS, _GEMINI, _CANCER = 0, 1, 2, 3
_LEO, _VIRGO, _LIBRA, _SCORPIO = 4, 5, 6, 7
_SAGITTARIUS, _CAPRICORN, _AQUARIUS, _PISCES = 8, 9, 10, 11

# Classical Vedic dignities.
OWN_SIGNS = {
    const.SUN: [_LEO],
    const.MOON: [_CANCER],
    const.MARS: [_ARIES, _SCORPIO],
    const.MERCURY: [_GEMINI, _VIRGO],
    const.JUPITER: [_SAGITTARIUS, _PISCES],
    const.VENUS: [_TAURUS, _LIBRA],
    const.SATURN: [_CAPRICORN, _AQUARIUS],
}
EXALTATION_SIGN = {
    const.SUN: _ARIES,
    const.MOON: _TAURUS,
    const.MARS: _CAPRICORN,
    const.MERCURY: _VIRGO,
    const.JUPITER: _CANCER,
    const.VENUS: _PISCES,
    const.SATURN: _LIBRA,
}
DEBILITATION_SIGN = {
    const.SUN: _LIBRA,
    const.MOON: _SCORPIO,
    const.MARS: _CANCER,
    const.MERCURY: _PISCES,
    const.JUPITER: _CAPRICORN,
    const.VENUS: _VIRGO,
    const.SATURN: _ARIES,
}

# Pancha Mahapurusha: planet → (sanskrit name, short description).
PANCHA_MAHAPURUSHA = {
    const.MARS: ("Ruchaka", "Mars strong in a kendra — courage, leadership, vigour."),
    const.MERCURY: (
        "Bhadra",
        "Mercury strong in a kendra — intellect, eloquence, business acumen.",
    ),
    const.JUPITER: ("Hamsa", "Jupiter strong in a kendra — wisdom, ethics, respected position."),
    const.VENUS: ("Malavya", "Venus strong in a kendra — beauty, comfort, artistic refinement."),
    const.SATURN: (
        "Sasha",
        "Saturn strong in a kendra — authority, discipline, command over others.",
    ),
}

KENDRA_HOUSES = (1, 4, 7, 10)


@dataclass(frozen=True)
class YogaResult:
    """A detected yoga.

    Attributes:
        name: English/common name (e.g. "Hamsa Yoga", "Gaja-Kesari Yoga").
        sanskrit: The Sanskrit name (e.g. "Hamsa").
        planets: Tuple of the planet IDs involved.
        description: One-line description of the yoga's significance.
    """

    name: str
    sanskrit: str
    planets: tuple
    description: str


def is_in_own_or_exaltation(planet, sign_idx):
    """True if ``planet`` is in one of its own signs or its exaltation sign."""
    sign_idx = sign_idx % 12
    return sign_idx in OWN_SIGNS.get(planet, []) or EXALTATION_SIGN.get(planet) == sign_idx


def is_debilitated(planet, sign_idx):
    """True if ``planet`` is in its debilitation sign."""
    return DEBILITATION_SIGN.get(planet) == (sign_idx % 12)


def house_from(reference_sign, planet_sign):
    """Return the Whole-Sign house number (1..12) of ``planet_sign`` counted
    from ``reference_sign`` (which is house 1)."""
    return (planet_sign - reference_sign) % 12 + 1


def _detect(planet_signs, asc_sign):
    """Core yoga detection over sign indices.

    Args:
        planet_signs: Mapping of planet ID → sign index (0..11). Must
            include the 7 classical planets.
        asc_sign: The Ascendant's sign index.

    Returns:
        A list of :class:`YogaResult`.
    """
    results = []

    # --- Pancha Mahapurusha ---
    for planet, (sanskrit, desc) in PANCHA_MAHAPURUSHA.items():
        sign = planet_signs.get(planet)
        if sign is None:
            continue
        if is_in_own_or_exaltation(planet, sign) and house_from(asc_sign, sign) in KENDRA_HOUSES:
            results.append(
                YogaResult(
                    name=f"{sanskrit} Yoga",
                    sanskrit=sanskrit,
                    planets=(planet,),
                    description=desc,
                )
            )

    # --- Gaja-Kesari: Jupiter in a kendra from the Moon ---
    moon_sign = planet_signs.get(const.MOON)
    jup_sign = planet_signs.get(const.JUPITER)
    if moon_sign is not None and jup_sign is not None:
        if house_from(moon_sign, jup_sign) in KENDRA_HOUSES:
            results.append(
                YogaResult(
                    name="Gaja-Kesari Yoga",
                    sanskrit="Gaja-Kesari",
                    planets=(const.JUPITER, const.MOON),
                    description="Jupiter in a kendra from the Moon — fame, intelligence.",
                )
            )

    # --- Budha-Aditya (Nipuna): Mercury conjunct Sun (same sign) ---
    sun_sign = planet_signs.get(const.SUN)
    mer_sign = planet_signs.get(const.MERCURY)
    if sun_sign is not None and mer_sign is not None and sun_sign == mer_sign:
        results.append(
            YogaResult(
                name="Budha-Aditya Yoga",
                sanskrit="Budha-Aditya",
                planets=(const.MERCURY, const.SUN),
                description="Mercury conjunct the Sun — sharp intellect, learning, administration.",
            )
        )

    # --- Chandra-Mangala: Moon conjunct Mars (same sign) ---
    mars_sign = planet_signs.get(const.MARS)
    if moon_sign is not None and mars_sign is not None and moon_sign == mars_sign:
        results.append(
            YogaResult(
                name="Chandra-Mangala Yoga",
                sanskrit="Chandra-Mangala",
                planets=(const.MOON, const.MARS),
                description="Moon conjunct Mars — drive, wealth through enterprise.",
            )
        )

    return results


_CLASSICAL_PLANETS = (
    const.SUN,
    const.MOON,
    const.MARS,
    const.MERCURY,
    const.JUPITER,
    const.VENUS,
    const.SATURN,
)


def detect_yogas(chart, ayanamsa=const.AYANAMSA_LAHIRI):
    """Detect the supported yogas in a chart.

    Args:
        chart: A :class:`Chart`. Tropical or sidereal — a tropical chart
            is shifted to sidereal via ``ayanamsa`` before sign extraction.
        ayanamsa: One of ``const.LIST_AYANAMSAS``.

    Returns:
        A list of :class:`YogaResult`, possibly empty.
    """

    def sid_sign(obj):
        if chart.zodiac == const.ZODIAC_SIDEREAL:
            lon = obj.lon
        else:
            lon = _ay.to_sidereal(obj.lon, chart.date, ayanamsa=ayanamsa)
        return int((lon % 360.0) // 30.0)

    planet_signs = {p: sid_sign(chart.getObject(p)) for p in _CLASSICAL_PLANETS}
    asc_sign = sid_sign(chart.getAngle(const.ASC))
    return _detect(planet_signs, asc_sign)

"""Vedic yoga detection — named planetary combinations.

Detects:

- The 5 **Pancha Mahapurusha** yogas (Ruchaka/Mars, Bhadra/Mercury,
  Hamsa/Jupiter, Malavya/Venus, Sasha/Saturn) — the planet in its own
  or exaltation sign and in a kendra.
- **Gaja-Kesari** (Jupiter 1st/4th/7th/10th from the Moon),
  **Budha-Aditya** (Mercury+Sun same sign), **Chandra-Mangala**
  (Moon+Mars same sign).
- **Raja Yoga** — a kendra lord conjunct a distinct trikona lord.
- **Dhana Yoga** — two distinct wealth-house (2/5/9/11) lords conjunct.
- **Vipareeta Raja Yoga** — Harsha (6th lord), Sarala (8th lord), or
  Vimala (12th lord) when that dusthana lord is itself in a dusthana
  (6/8/12).
- **Neecha Bhanga Raja Yoga** — a debilitated planet whose debilitation
  is cancelled (dispositor or the would-be-exalted planet in a kendra).
- **Kemadruma Yoga** — no graha in the 2nd or 12th sign from the Moon.

Houses are computed Whole-Sign (sign offset from the Ascendant's sign),
the Vedic convention, regardless of the chart's house system.

Still deferred: yoga *strength* scoring, finer Neecha-Bhanga conditions
(navamsa exaltation, dispositor-aspect), Gaja-Kesari cancellation, and
the dozens of named lesser yogas (Lakshmi, Saraswati, Gaja, etc.).

References:
- BPHS ch. 75-78 (Mahapurusha, Raja, Dhana, Vipareeta, Neecha Bhanga)
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
TRIKONA_HOUSES = (1, 5, 9)
DUSTHANA_HOUSES = (6, 8, 12)
DHANA_HOUSES = (2, 5, 9, 11)  # houses of wealth/gain

# Sign → ruling planet, 0-indexed (the traditional 7-planet rulerships).
_SIGN_LORD = [
    const.MARS,  # Aries
    const.VENUS,  # Taurus
    const.MERCURY,  # Gemini
    const.MOON,  # Cancer
    const.SUN,  # Leo
    const.MERCURY,  # Virgo
    const.VENUS,  # Libra
    const.MARS,  # Scorpio
    const.JUPITER,  # Sagittarius
    const.SATURN,  # Capricorn
    const.SATURN,  # Aquarius
    const.JUPITER,  # Pisces
]

# Sign → the planet that is exalted in it (inverse of EXALTATION_SIGN).
_EXALTED_IN = {sign: planet for planet, sign in EXALTATION_SIGN.items()}


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


def sign_lord(sign_idx):
    """Return the ruling planet of a sign (0=Aries .. 11=Pisces)."""
    return _SIGN_LORD[sign_idx % 12]


def house_lord(house_num, asc_sign):
    """Return the lord of the ``house_num``-th Whole-Sign house from the
    Ascendant at ``asc_sign``."""
    sign_of_house = (asc_sign + house_num - 1) % 12
    return _SIGN_LORD[sign_of_house]


def houses_ruled_by(planet, asc_sign):
    """Return the list of Whole-Sign house numbers (1..12) that ``planet``
    rules in a chart with the given Ascendant sign."""
    return [h for h in range(1, 13) if house_lord(h, asc_sign) == planet]


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


# Planets that "count" for the Kemadruma check (the nodes and the
# luminaries' co-presence rules vary; the classical Kemadruma counts the
# five non-luminary grahas in the 2nd/12th from the Moon).
_KEMADRUMA_PLANETS = (const.MARS, const.MERCURY, const.JUPITER, const.VENUS, const.SATURN)


def _detect_extended(planet_signs, asc_sign):
    """Detect the extended yoga set — Raja, Dhana, Vipareeta Raja, Neecha
    Bhanga, Kemadruma — over sign indices.

    Args:
        planet_signs: Mapping of planet ID → sign index (0..11) for the
            7 classical planets.
        asc_sign: The Ascendant's sign index.

    Returns:
        A list of :class:`YogaResult`.
    """
    results = []

    # Map each planet to the house it occupies (Whole-Sign).
    house_of = {p: house_from(asc_sign, s) for p, s in planet_signs.items()}

    # --- Raja Yoga: a kendra lord conjunct a (distinct) trikona lord ---
    kendra_lords = {house_lord(h, asc_sign) for h in KENDRA_HOUSES}
    trikona_lords = {house_lord(h, asc_sign) for h in TRIKONA_HOUSES}
    raja_pairs = set()
    for p1 in kendra_lords:
        for p2 in trikona_lords:
            if p1 == p2:
                continue
            if planet_signs.get(p1) is not None and planet_signs[p1] == planet_signs.get(p2):
                raja_pairs.add(frozenset((p1, p2)))
    for pair in raja_pairs:
        a, b = sorted(pair)
        results.append(
            YogaResult(
                name="Raja Yoga",
                sanskrit="Raja",
                planets=(a, b),
                description="A kendra lord conjunct a trikona lord — power, status, success.",
            )
        )

    # --- Dhana Yoga: two distinct wealth-house lords conjunct ---
    dhana_lords = {house_lord(h, asc_sign): h for h in DHANA_HOUSES}
    dhana_pairs = set()
    dl = list(dhana_lords)
    for i in range(len(dl)):
        for j in range(i + 1, len(dl)):
            p1, p2 = dl[i], dl[j]
            if planet_signs.get(p1) is not None and planet_signs[p1] == planet_signs.get(p2):
                dhana_pairs.add(frozenset((p1, p2)))
    for pair in dhana_pairs:
        a, b = sorted(pair)
        results.append(
            YogaResult(
                name="Dhana Yoga",
                sanskrit="Dhana",
                planets=(a, b),
                description="Wealth-house lords conjunct — gains, prosperity.",
            )
        )

    # --- Vipareeta Raja Yoga: a dusthana lord placed in a dusthana ---
    _VIPAREETA_NAMES = {6: "Harsha", 8: "Sarala", 12: "Vimala"}
    for ruled_house, name in _VIPAREETA_NAMES.items():
        lord = house_lord(ruled_house, asc_sign)
        if house_of.get(lord) in DUSTHANA_HOUSES:
            results.append(
                YogaResult(
                    name=f"{name} Yoga (Vipareeta Raja)",
                    sanskrit=name,
                    planets=(lord,),
                    description=f"{ruled_house}th lord in a dusthana — adversity turned advantage.",
                )
            )

    # --- Neecha Bhanga: a debilitated planet's debilitation cancelled ---
    for planet, sign in planet_signs.items():
        if not is_debilitated(planet, sign):
            continue
        dispositor = sign_lord(sign)  # lord of the debilitation sign
        exalted_planet = _EXALTED_IN.get(sign)
        cancelled = False
        reasons = []
        if house_of.get(dispositor) in KENDRA_HOUSES:
            cancelled = True
            reasons.append("dispositor in a kendra")
        if exalted_planet is not None and house_of.get(exalted_planet) in KENDRA_HOUSES:
            cancelled = True
            reasons.append(f"{exalted_planet} (exalted there) in a kendra")
        if cancelled:
            results.append(
                YogaResult(
                    name="Neecha Bhanga Raja Yoga",
                    sanskrit="Neecha Bhanga",
                    planets=(planet,),
                    description=f"{planet} debilitated but cancelled ({'; '.join(reasons)}).",
                )
            )

    # --- Kemadruma: 2nd and 12th from the Moon both empty of grahas ---
    moon_sign = planet_signs.get(const.MOON)
    if moon_sign is not None:
        second_from_moon = (moon_sign + 1) % 12
        twelfth_from_moon = (moon_sign - 1) % 12
        occupied = any(
            planet_signs.get(p) in (second_from_moon, twelfth_from_moon) for p in _KEMADRUMA_PLANETS
        )
        if not occupied:
            results.append(
                YogaResult(
                    name="Kemadruma Yoga",
                    sanskrit="Kemadruma",
                    planets=(const.MOON,),
                    description="No graha in the 2nd or 12th from the Moon — isolation, struggle.",
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
    return _detect(planet_signs, asc_sign) + _detect_extended(planet_signs, asc_sign)

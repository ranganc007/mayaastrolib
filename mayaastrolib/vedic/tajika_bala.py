"""Tajika strength measures — Harsha Bala and Panchavargiya Bala.

**Harsha Bala** ("joy strength") is a five-component, 0-or-5-per-component
score (max 25) used in Tajika annual analysis:

1. Hemisphere — diurnal planets (Sun, Mercury, Jupiter, Saturn) above
   the horizon (houses 7-12), nocturnal planets (Moon, Mars, Venus)
   below it (houses 1-6).
2. Gender — masculine planets (Sun, Mars, Jupiter) in odd (masculine)
   signs; feminine planets (Moon, Venus) in even (feminine) signs;
   neutral planets (Mercury, Saturn) always.
3. Dignity — in own or exaltation sign.
4. Own decanate — the drekkana (D3) sign of the planet's position is
   one of the planet's own signs.
5. Planetary joy — in its joy house (Sun 9, Moon 3, Mars 6, Mercury 1,
   Jupiter 11, Venus 5, Saturn 12).

**Panchavargiya Bala** ("five-fold strength") sums five sub-balas. The
component *scales* vary substantially across sources; this module uses
a documented simplified scheme (see `_kshetra` etc.) good for relative
comparison — it is NOT a verified replica of any one text. Used here to
let callers do the canonical Lord-of-Year pick if they prefer it over
`tajika.lord_of_year`'s heuristic.

Houses are computed Whole-Sign from the chart's Ascendant sign.

References:
- Tajika Neelakanthi ch. 9 (Harsha Bala), ch. 11 (Panchavargiya Bala)
- BPHS ch. 27, 31 (Shadbala / Panchavargiya — carried into Tajika)
"""

from mayaastrolib import const
from mayaastrolib.vedic import ayanamsa as _ay
from mayaastrolib.vedic import divisional as _div

__all__ = [
    "harsha_bala",
    "panchavargiya_bala",
]

_CLASSICAL_PLANETS = (
    const.SUN,
    const.MOON,
    const.MARS,
    const.MERCURY,
    const.JUPITER,
    const.VENUS,
    const.SATURN,
)

# Diurnal / nocturnal classification for the hemisphere component.
_DIURNAL_PLANETS = {const.SUN, const.MERCURY, const.JUPITER, const.SATURN}
_NOCTURNAL_PLANETS = {const.MOON, const.MARS, const.VENUS}

# Planetary genders for the gender component (Mercury and Saturn are
# treated as neutral — they score the gender point unconditionally).
_MASCULINE = {const.SUN, const.MARS, const.JUPITER}
_FEMININE = {const.MOON, const.VENUS}

# Own / exaltation / debilitation signs (0-indexed).
_OWN_SIGNS = {
    const.SUN: [4],
    const.MOON: [3],
    const.MARS: [0, 7],
    const.MERCURY: [2, 5],
    const.JUPITER: [8, 11],
    const.VENUS: [1, 6],
    const.SATURN: [9, 10],
}
_EXALTATION_DEG = {  # sign_idx, deg-within-sign of the exaltation point
    const.SUN: (0, 10.0),
    const.MOON: (1, 3.0),
    const.MARS: (9, 28.0),
    const.MERCURY: (5, 15.0),
    const.JUPITER: (3, 5.0),
    const.VENUS: (11, 27.0),
    const.SATURN: (6, 20.0),
}
_EXALT_SIGN = {p: s for p, (s, _d) in _EXALTATION_DEG.items()}

# Planetary joy houses (1..12), the classical joys.
_JOY_HOUSE = {
    const.SUN: 9,
    const.MOON: 3,
    const.MARS: 6,
    const.MERCURY: 1,
    const.JUPITER: 11,
    const.VENUS: 5,
    const.SATURN: 12,
}

# Traditional 7-planet sign rulerships, 0-indexed.
_SIGN_LORDS = [
    const.MARS,
    const.VENUS,
    const.MERCURY,
    const.MOON,
    const.SUN,
    const.MERCURY,
    const.VENUS,
    const.MARS,
    const.JUPITER,
    const.SATURN,
    const.SATURN,
    const.JUPITER,
]


def _sid_lon(chart, getter, ayanamsa):
    obj = getter()
    if chart.zodiac == const.ZODIAC_SIDEREAL:
        return obj.lon % 360.0
    return _ay.to_sidereal(obj.lon, chart.date, ayanamsa=ayanamsa)


def _planet_data(chart, ayanamsa):
    """Return per-planet (sidereal_lon, sign_idx, deg_in_sign, whole_sign_house)."""
    asc_lon = _sid_lon(chart, lambda: chart.getAngle(const.ASC), ayanamsa)
    asc_sign = int(asc_lon // 30.0)
    data = {}
    for p in _CLASSICAL_PLANETS:
        lon = _sid_lon(chart, lambda p=p: chart.getObject(p), ayanamsa)
        sign = int(lon // 30.0)
        deg = lon - sign * 30.0
        house = (sign - asc_sign) % 12 + 1
        data[p] = (lon, sign, deg, house)
    return data


# --- Harsha Bala --- #


def _harsha_components(planet, sign, deg, house, is_diurnal_chart):
    """Return the 5 Harsha-Bala components (each 0 or 5) for one planet."""
    c = {}
    # 1. Hemisphere (houses 7-12 = above the horizon).
    above = house in (7, 8, 9, 10, 11, 12)
    if planet in _DIURNAL_PLANETS:
        c["hemisphere"] = 5 if above else 0
    elif planet in _NOCTURNAL_PLANETS:
        c["hemisphere"] = 0 if above else 5
    else:  # shouldn't happen — every classical planet is in one set
        c["hemisphere"] = 0
    # 2. Gender (odd sign idx = masculine sign).
    odd_sign = sign % 2 == 0
    if planet in _MASCULINE:
        c["gender"] = 5 if odd_sign else 0
    elif planet in _FEMININE:
        c["gender"] = 0 if odd_sign else 5
    else:
        c["gender"] = 5  # neutral planets always score
    # 3. Dignity (own or exaltation sign).
    c["dignity"] = (
        5 if (sign in _OWN_SIGNS.get(planet, []) or _EXALT_SIGN.get(planet) == sign) else 0
    )
    # 4. Own decanate.
    lon = sign * 30.0 + deg
    d3_sign = _div.drekkana(lon)
    c["decanate"] = 5 if _SIGN_LORDS[d3_sign] == planet else 0
    # 5. Planetary joy.
    c["joy"] = 5 if _JOY_HOUSE.get(planet) == house else 0
    return c


def harsha_bala(chart, ayanamsa=const.AYANAMSA_LAHIRI):
    """Return the Harsha Bala for each classical planet.

    Args:
        chart: A :class:`Chart` (typically an annual / varshapravesh
            chart). Tropical or sidereal.
        ayanamsa: Used only when the chart is tropical.

    Returns:
        Dict ``{planet_id: {"components": {hemisphere, gender, dignity,
        decanate, joy}, "total": int}}``. Each component is 0 or 5;
        total ∈ [0, 25].
    """
    is_diurnal = chart.isDiurnal()
    data = _planet_data(chart, ayanamsa)
    result = {}
    for p in _CLASSICAL_PLANETS:
        _lon, sign, deg, house = data[p]
        comps = _harsha_components(p, sign, deg, house, is_diurnal)
        result[p] = {"components": comps, "total": sum(comps.values())}
    return result


# --- Panchavargiya Bala (simplified) --- #


def _kshetra(planet, sign):
    """Kshetra (sign) bala — simplified: own/exalted 30, debilitated 0,
    neutral 15."""
    if sign in _OWN_SIGNS.get(planet, []) or _EXALT_SIGN.get(planet) == sign:
        return 30.0
    # Debilitation = the sign opposite the exaltation sign.
    debil_sign = (_EXALT_SIGN.get(planet, 0) + 6) % 12
    if planet in _EXALT_SIGN and sign == debil_sign:
        return 0.0
    return 15.0


def _uchcha(planet, sign, deg):
    """Uchcha (exaltation) bala on a 0..20 scale — 20 at the exaltation
    point, 0 at the debilitation point, linear in between."""
    ex_sign, ex_deg = _EXALTATION_DEG[planet]
    ex_lon = ex_sign * 30.0 + ex_deg
    p_lon = sign * 30.0 + deg
    sep = abs(((p_lon - ex_lon + 180.0) % 360.0) - 180.0)  # 0..180
    return (180.0 - sep) / 180.0 * 20.0


def _hadda(planet, sign):
    """Hadda (term) bala — simplified: 15 if in its own sign (a proxy for
    "in its own term"), else 3.75. (A faithful version would use the
    Egyptian-terms table in dignities/tables.py.)"""
    return 15.0 if sign in _OWN_SIGNS.get(planet, []) else 3.75


def _drekkana_bala(planet, lon):
    """Drekkana bala — 10 if the D3 sign's lord is the planet, else 2."""
    return 10.0 if _SIGN_LORDS[_div.drekkana(lon)] == planet else 2.0


def _navamsa_bala(planet, lon):
    """Navamsa bala — 5 if the D9 sign's lord is the planet, else 1."""
    return 5.0 if _SIGN_LORDS[_div.navamsa(lon)] == planet else 1.0


def panchavargiya_bala(chart, ayanamsa=const.AYANAMSA_LAHIRI):
    """Return the (simplified) Panchavargiya Bala for each classical planet.

    Sums five sub-balas: Kshetra (sign), Uchcha (exaltation distance),
    Hadda (term), Drekkana, Navamsa. The component scales here are a
    documented simplification — see the module docstring — suitable for
    relative comparison (e.g. picking the Lord of the Year) but not a
    verified replica of any single text.

    Returns:
        Dict ``{planet_id: {"components": {kshetra, uchcha, hadda,
        drekkana, navamsa}, "total": float}}``.
    """
    data = _planet_data(chart, ayanamsa)
    result = {}
    for p in _CLASSICAL_PLANETS:
        lon, sign, deg, _house = data[p]
        comps = {
            "kshetra": _kshetra(p, sign),
            "uchcha": _uchcha(p, sign, deg),
            "hadda": _hadda(p, sign),
            "drekkana": _drekkana_bala(p, lon),
            "navamsa": _navamsa_bala(p, lon),
        }
        result[p] = {"components": comps, "total": sum(comps.values())}
    return result

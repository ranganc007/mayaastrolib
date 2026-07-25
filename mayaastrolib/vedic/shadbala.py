"""Shadbala — the classical six-fold strength of the planets (BPHS ch. 27).

Shadbala ("six strengths") scores each of the seven classical planets on
six independent axes and sums them. Strength is measured in **Virupas**
(1 Rupa = 60 Virupas). The six balas are:

1. **Sthana Bala** (positional) — Uchcha (exaltation distance),
   Saptavargaja (dignity across 7 divisional charts via 5-fold compound
   friendship), Oja-Yugma (odd/even rasi + navamsa), Kendradi (angular /
   succedent / cadent), and Drekkana (decanate by gender).
2. **Dig Bala** (directional) — strength by proximity to the planet's
   preferred angle (Sun/Mars → MC, Jupiter/Mercury → Asc, Moon/Venus →
   IC, Saturn → Desc).
3. **Kala Bala** (temporal) — Nathonnatha (day/night), Paksha (lunar
   phase), Tribhaga, Vara (weekday lord), Hora (planetary-hour lord), and
   Ayana (declination). See the *Simplifications* note below.
4. **Cheshta Bala** (motional) — from planetary motion; Sun's Cheshta is
   its Ayana bala, Moon's is its Paksha bala (the classical substitution).
5. **Naisargika Bala** (natural) — a fixed per-planet constant.
6. **Drik Bala** (aspectual) — net benefic-minus-malefic aspect on the
   planet.

The total is compared against per-planet **required minimums**
(``REQUIRED_RUPAS``) to judge whether a planet is "strong enough".

Simplifications (documented, in the spirit of this package's other bala
modules — see ``tajika_bala.panchavargiya_bala``):

- **Kala Bala** omits *Abda* (year-lord) and *Masa* (month-lord), which
  need almanac-level solar-year / lunar-month commencement data, and
  *Yuddha* (planetary war), whose adjustment rule varies by source and
  only fires for sub-1° conjunctions of the star planets. The Kala total
  is therefore slightly below the theoretical maximum.
- **Nathonnatha / Tribhaga** use local clock time with a fixed
  6:00/18:00 sunrise/sunset rather than true oblique-ascension day length.
- **Saptavargaja** treats Moolatrikona by sign in every varga.
- **Cheshta** (for Mars..Saturn) maps motional state (retrograde / speed
  vs. mean) to the eight avasthas rather than computing the exact
  seeghra-kendra arc.
- **Drik** uses sign-based Parashari full aspects (graha drishti) rather
  than the degree-graded Sripati drishti table.

These make the absolute totals approximate, but the **relative** ordering
and the strong/weak verdict track the classical method closely.

References:
- BPHS ch. 27 (Shadbala), ch. 3-7 (divisional dignities, friendships)
- B.V. Raman, *Graha and Bhava Balas*
"""

from __future__ import annotations

from typing import Any

from mayaastrolib import const
from mayaastrolib import utils as _utils
from mayaastrolib.vedic import ayanamsa as _ay
from mayaastrolib.vedic import divisional as _div

__all__ = [
    "REQUIRED_RUPAS",
    "shadbala",
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

# Traditional 7-planet sign rulerships, 0-indexed (Aries..Pisces).
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

# Own signs (0-indexed) and the exaltation point (sign_idx, deg-in-sign).
_OWN_SIGNS = {
    const.SUN: [4],
    const.MOON: [3],
    const.MARS: [0, 7],
    const.MERCURY: [2, 5],
    const.JUPITER: [8, 11],
    const.VENUS: [1, 6],
    const.SATURN: [9, 10],
}
_EXALTATION_DEG = {
    const.SUN: (0, 10.0),
    const.MOON: (1, 3.0),
    const.MARS: (9, 28.0),
    const.MERCURY: (5, 15.0),
    const.JUPITER: (3, 5.0),
    const.VENUS: (11, 27.0),
    const.SATURN: (6, 20.0),
}
# Moolatrikona sign per planet (0-indexed).
_MOOLATRIKONA_SIGN = {
    const.SUN: 4,
    const.MOON: 1,
    const.MARS: 0,
    const.MERCURY: 5,
    const.JUPITER: 8,
    const.VENUS: 6,
    const.SATURN: 10,
}

# Natural (Naisargika) friendships. Anything not listed is neutral.
_NATURAL_FRIENDS = {
    const.SUN: {const.MOON, const.MARS, const.JUPITER},
    const.MOON: {const.SUN, const.MERCURY},
    const.MARS: {const.SUN, const.MOON, const.JUPITER},
    const.MERCURY: {const.SUN, const.VENUS},
    const.JUPITER: {const.SUN, const.MOON, const.MARS},
    const.VENUS: {const.MERCURY, const.SATURN},
    const.SATURN: {const.MERCURY, const.VENUS},
}
_NATURAL_ENEMIES = {
    const.SUN: {const.VENUS, const.SATURN},
    const.MOON: set(),
    const.MARS: {const.MERCURY},
    const.MERCURY: {const.MOON},
    const.JUPITER: {const.MERCURY, const.VENUS},
    const.VENUS: {const.SUN, const.MOON},
    const.SATURN: {const.SUN, const.MOON, const.MARS},
}

# Naisargika Bala (natural strength), virupas. Exact = rank/7 * 60 with
# Saturn=1 .. Sun=7, so the values are stored as fractions for precision.
_NAISARGIKA_RANK = {
    const.SATURN: 1,
    const.MARS: 2,
    const.MERCURY: 3,
    const.JUPITER: 4,
    const.VENUS: 5,
    const.MOON: 6,
    const.SUN: 7,
}

# Day-strong vs night-strong (Nathonnatha). Mercury scores fully always.
_DAY_STRONG = {const.SUN, const.JUPITER, const.VENUS}
_NIGHT_STRONG = {const.MOON, const.MARS, const.SATURN}

# Benefic / malefic for Paksha and Drik bala (Mercury and Moon treated as
# benefic here — a documented simplification; truly both are conditional).
_BENEFICS = {const.JUPITER, const.VENUS, const.MERCURY, const.MOON}
_MALEFICS = {const.SUN, const.MARS, const.SATURN}

# Dig Bala: the angle of *maximum* strength for each planet, expressed as
# the whole-circle longitude key 'asc' / 'mc' / 'desc' / 'ic'. The point
# of *weakness* is the opposite cusp.
_DIG_STRONG_ANGLE = {
    const.SUN: "mc",
    const.MARS: "mc",
    const.JUPITER: "asc",
    const.MERCURY: "asc",
    const.MOON: "ic",
    const.VENUS: "ic",
    const.SATURN: "desc",
}

# Gender groups for Drekkana bala. Hermaphrodite planets win in the 2nd
# decanate, masculine in the 1st, feminine in the 3rd.
_MASCULINE = {const.SUN, const.JUPITER, const.MARS}
_FEMININE = {const.MOON, const.VENUS}
_HERMAPHRODITE = {const.MERCURY, const.SATURN}

# Required minimum Shadbala per planet, in Rupas (BPHS). A planet meeting
# its minimum is considered to have sufficient strength.
REQUIRED_RUPAS = {
    const.SUN: 6.5,
    const.MOON: 6.0,
    const.MARS: 5.0,
    const.MERCURY: 7.0,
    const.JUPITER: 6.5,
    const.VENUS: 5.5,
    const.SATURN: 5.0,
}

# Mean daily motion (degrees/day), geocentric — reused for Cheshta.
_MEAN_MOTION = {
    const.SUN: 0.9856,
    const.MOON: 13.176,
    const.MARS: 0.524,
    const.MERCURY: 1.383,
    const.JUPITER: 0.083,
    const.VENUS: 1.602,
    const.SATURN: 0.034,
}

# Saptavargaja dignity → virupas.
_SAPTA_MT = 45.0
_SAPTA_OWN = 30.0
_SAPTA_GREAT_FRIEND = 22.5
_SAPTA_FRIEND = 15.0
_SAPTA_NEUTRAL = 7.5
_SAPTA_ENEMY = 3.75
_SAPTA_GREAT_ENEMY = 1.875

# The 7 vargas of the Saptavarga, as (name, divisional-fn).
_SAPTAVARGA = (
    ("rasi", _div.rasi),
    ("hora", _div.hora),
    ("drekkana", _div.drekkana),
    ("saptamsa", _div.saptamsa),
    ("navamsa", _div.navamsa),
    ("dvadasamsa", _div.dvadasamsa),
    ("trimsamsa", _div.trimsamsa),
)


# ----------------------------------------------------------------------- #
#   Chart access helpers (mirror tajika_bala)                             #
# ----------------------------------------------------------------------- #


def _sidereal_of(native: float, chart: Any, ayanamsa: str) -> float:
    """Sidereal longitude of a chart-native object longitude."""
    if chart.zodiac == const.ZODIAC_SIDEREAL:
        return native % 360.0
    return _ay.to_sidereal(native, chart.date, ayanamsa=ayanamsa)


def _gather(chart: Any, ayanamsa: str) -> dict[str, dict[str, Any]]:
    """Collect per-planet data needed across the six balas.

    Tracks three longitudes per planet because the balas need different
    frames:

    - ``sid`` (sidereal) — for sign/dignity/divisional/aspect work.
    - ``native`` (the chart's own frame) — for Dig Bala, which is a
      planet-to-cusp arc; a shared ayanamsa cancels, so planet and cusps
      just have to be in the *same* frame.
    - declination — derived from the *true tropical* longitude (the
      celestial equator is tropical), never the sidereal value.
    """
    asc_obj = chart.getAngle(const.ASC)
    asc_sign = int(_sidereal_of(asc_obj.lon, chart, ayanamsa) // 30.0)
    data: dict[str, dict[str, Any]] = {}
    for p in _CLASSICAL_PLANETS:
        obj = chart.getObject(p)
        native = obj.lon % 360.0
        if chart.zodiac == const.ZODIAC_SIDEREAL:
            sid = native
            trop = _ay.to_tropical(native, chart.date, ayanamsa=ayanamsa)
        else:
            sid = _ay.to_sidereal(native, chart.date, ayanamsa=ayanamsa)
            trop = native
        sign = int(sid // 30.0)
        _ra, decl = _utils.eqCoords(trop, obj.lat)
        data[p] = {
            "sid": sid,
            "native": native,
            "sign": sign,
            "deg": sid - sign * 30.0,
            "house": (sign - asc_sign) % 12 + 1,
            "decl": decl,
            "speed": obj.lonspeed,
            "retro": obj.isRetrograde(),
        }
    return data


# ----------------------------------------------------------------------- #
#   1. Sthana Bala (positional)                                           #
# ----------------------------------------------------------------------- #


def _uchcha_bala(planet: str, sid_lon: float) -> float:
    """Exaltation strength: arc from the debilitation point / 3, 0..60."""
    ex_sign, ex_deg = _EXALTATION_DEG[planet]
    debil_lon = ((ex_sign * 30.0 + ex_deg) + 180.0) % 360.0
    arc = abs(((sid_lon - debil_lon + 180.0) % 360.0) - 180.0)  # 0..180
    return arc / 3.0


def _compound_relation(planet: str, other: str, planet_sign: int, other_sign: int) -> str:
    """5-fold compound friendship of ``planet`` toward ``other``.

    Natural friendship combined with temporal (Tatkalika) friendship:
    a planet in the 2/3/4/10/11/12 sign from another is its temporal
    friend, otherwise its temporal enemy.
    """
    house = (other_sign - planet_sign) % 12 + 1
    temp_friend = house in (2, 3, 4, 10, 11, 12)
    if other in _NATURAL_FRIENDS[planet]:
        nat = "friend"
    elif other in _NATURAL_ENEMIES[planet]:
        nat = "enemy"
    else:
        nat = "neutral"
    if nat == "friend":
        return "great_friend" if temp_friend else "neutral"
    if nat == "enemy":
        return "neutral" if temp_friend else "great_enemy"
    return "friend" if temp_friend else "enemy"


def _saptavargaja_bala(planet: str, sid_lon: float, planet_signs: dict[str, int]) -> float:
    """Dignity strength summed across the seven vargas."""
    total = 0.0
    for _name, fn in _SAPTAVARGA:
        varga_sign = fn(sid_lon)
        lord = _SIGN_LORDS[varga_sign]
        if lord == planet:
            total += _SAPTA_MT if varga_sign == _MOOLATRIKONA_SIGN[planet] else _SAPTA_OWN
            continue
        rel = _compound_relation(planet, lord, planet_signs[planet], planet_signs[lord])
        total += {
            "great_friend": _SAPTA_GREAT_FRIEND,
            "friend": _SAPTA_FRIEND,
            "neutral": _SAPTA_NEUTRAL,
            "enemy": _SAPTA_ENEMY,
            "great_enemy": _SAPTA_GREAT_ENEMY,
        }[rel]
    return total


def _oja_yugma_bala(planet: str, sid_lon: float) -> float:
    """Odd/even strength in rasi (D1) and navamsa (D9): up to 15 each."""
    # Moon and Venus gain in even (yugma) signs; the rest in odd (oja).
    wants_even = planet in (const.MOON, const.VENUS)
    bala = 0.0
    for sign in (_div.rasi(sid_lon), _div.navamsa(sid_lon)):
        is_even = sign % 2 == 1  # 0-indexed: idx 1 = Taurus = 2nd = even
        if is_even == wants_even:
            bala += 15.0
    return bala


def _kendradi_bala(house: int) -> float:
    """Angular 60, succedent 30, cadent 15 (whole-sign house from Asc)."""
    if house in (1, 4, 7, 10):
        return 60.0
    if house in (2, 5, 8, 11):
        return 30.0
    return 15.0


def _drekkana_bala(planet: str, sid_lon: float) -> float:
    """15 virupas when the planet's gender matches its decanate, else 0."""
    third = int((sid_lon % 30.0) // 10.0)  # 0, 1 or 2
    if planet in _MASCULINE:
        return 15.0 if third == 0 else 0.0
    if planet in _FEMININE:
        return 15.0 if third == 2 else 0.0
    return 15.0 if third == 1 else 0.0  # hermaphrodite


def _sthana_bala(planet: str, d: dict[str, Any], planet_signs: dict[str, int]) -> dict[str, Any]:
    comps = {
        "uchcha": _uchcha_bala(planet, d["sid"]),
        "saptavargaja": _saptavargaja_bala(planet, d["sid"], planet_signs),
        "oja_yugma": _oja_yugma_bala(planet, d["sid"]),
        "kendradi": _kendradi_bala(d["house"]),
        "drekkana": _drekkana_bala(planet, d["sid"]),
    }
    return {"components": comps, "total": sum(comps.values())}


# ----------------------------------------------------------------------- #
#   2. Dig Bala (directional)                                             #
# ----------------------------------------------------------------------- #


def _dig_bala(planet: str, trop_lon: float, angles: dict[str, float]) -> float:
    """Directional strength: arc from the weak cusp / 3 (0..60).

    Uses tropical longitudes throughout — Dig Bala is the arc between the
    planet and a cusp, so a shared ayanamsa cancels.
    """
    strong = _DIG_STRONG_ANGLE[planet]
    opposite = {"mc": "ic", "ic": "mc", "asc": "desc", "desc": "asc"}[strong]
    weak_lon = angles[opposite]
    arc = abs(((trop_lon - weak_lon + 180.0) % 360.0) - 180.0)  # 0..180
    return arc / 3.0


# ----------------------------------------------------------------------- #
#   3. Kala Bala (temporal)                                               #
# ----------------------------------------------------------------------- #


def _nathonnatha_bala(planet: str, hour: float) -> float:
    """Day/night strength, graded by nearness to noon / midnight."""
    if planet == const.MERCURY:
        return 60.0
    nearness_noon = 1.0 - abs(hour - 12.0) / 12.0
    if planet in _DAY_STRONG:
        return nearness_noon * 60.0
    return (1.0 - nearness_noon) * 60.0  # night-strong


def _paksha_bala(planet: str, sun_sid: float, moon_sid: float) -> float:
    """Lunar-phase strength. Benefics gain toward full moon, malefics
    toward new moon. The Moon's own paksha bala is doubled."""
    kendra = abs(((moon_sid - sun_sid + 180.0) % 360.0) - 180.0)  # 0..180
    benefic_share = kendra / 180.0 * 60.0
    bala = benefic_share if planet in _BENEFICS else 60.0 - benefic_share
    if planet == const.MOON:
        bala *= 2.0
    return bala


def _tribhaga_bala(planet: str, hour: float, is_day: bool) -> float:
    """Strength to the ruler of the current third of day/night (Jupiter
    always). Fixed 6:00 sunrise / 18:00 sunset is a documented proxy."""
    if planet == const.JUPITER:
        return 60.0
    if is_day:
        # 06-10 Mercury, 10-14 Sun, 14-18 Saturn
        third = min(int((hour - 6.0) // 4.0), 2)
        ruler = (const.MERCURY, const.SUN, const.SATURN)[max(third, 0)]
    else:
        # 18-22 Moon, 22-02 Venus, 02-06 Mars
        night_hour = (hour - 18.0) % 24.0
        third = min(int(night_hour // 4.0), 2)
        ruler = (const.MOON, const.VENUS, const.MARS)[max(third, 0)]
    return 60.0 if planet == ruler else 0.0


def _vara_bala(planet: str, weekday_lord: str) -> float:
    """45 virupas to the lord of the weekday."""
    return 45.0 if planet == weekday_lord else 0.0


# Chaldean (descending) order used to step planetary hours.
_HORA_ORDER = (
    const.SATURN,
    const.JUPITER,
    const.MARS,
    const.SUN,
    const.VENUS,
    const.MERCURY,
    const.MOON,
)


def _hora_lord(weekday_lord: str, hour: float) -> str:
    """Lord of the planetary hour. Hour 0 (from a 6:00 sunrise) is ruled
    by the weekday lord; subsequent horas step in Chaldean order."""
    hours_since_sunrise = int((hour - 6.0) % 24.0)
    start = _HORA_ORDER.index(weekday_lord)
    return _HORA_ORDER[(start + hours_since_sunrise) % 7]


def _hora_bala(planet: str, weekday_lord: str, hour: float) -> float:
    return 60.0 if planet == _hora_lord(weekday_lord, hour) else 0.0


def _ayana_bala(planet: str, decl: float) -> float:
    """Declination strength. North-declination-favouring planets gain with
    positive declination; Moon and Saturn favour the south. The Sun's
    ayana bala is doubled. Result clamped to [0, 60] (×2 for the Sun)."""
    south_favouring = planet in (const.MOON, const.SATURN)
    effective = -decl if south_favouring else decl
    bala = (24.0 + effective) / 48.0 * 60.0
    bala = max(0.0, min(60.0, bala))
    if planet == const.SUN:
        bala *= 2.0
    return bala


def _kala_bala(
    planet: str,
    d: dict[str, Any],
    hour: float,
    is_day: bool,
    weekday_lord: str,
    sun_sid: float,
    moon_sid: float,
) -> dict[str, Any]:
    comps = {
        "nathonnatha": _nathonnatha_bala(planet, hour),
        "paksha": _paksha_bala(planet, sun_sid, moon_sid),
        "tribhaga": _tribhaga_bala(planet, hour, is_day),
        "vara": _vara_bala(planet, weekday_lord),
        "hora": _hora_bala(planet, weekday_lord, hour),
        "ayana": _ayana_bala(planet, d["decl"]),
    }
    return {"components": comps, "total": sum(comps.values())}


# ----------------------------------------------------------------------- #
#   4. Cheshta Bala (motional)                                            #
# ----------------------------------------------------------------------- #


def _cheshta_bala(planet: str, d: dict[str, Any], ayana: float, paksha: float) -> float:
    """Motional strength.

    Sun's Cheshta is its Ayana bala; Moon's is its Paksha bala (classical
    substitution). For Mars..Saturn, motional state is mapped to the eight
    avasthas (documented approximation of the seeghra-kendra method).
    """
    if planet == const.SUN:
        return ayana
    if planet == const.MOON:
        return paksha
    if d["retro"]:
        return 60.0  # Vakra — maximum cheshta
    speed = d["speed"]
    if speed is None:
        return 30.0  # undefined motion → neutral (Sama)
    mean = _MEAN_MOTION[planet]
    r = abs(speed) / mean if mean else 1.0
    if r < 0.05:
        return 15.0  # Vikala / Manda (near-stationary, slow)
    if r < 0.5:
        return 15.0  # Manda (slow)
    if r < 1.0:
        return 30.0  # Sama (mean)
    if r < 1.5:
        return 45.0  # Chara (swift)
    return 30.0  # Atichara (very swift)


# ----------------------------------------------------------------------- #
#   5. Naisargika Bala (natural)                                          #
# ----------------------------------------------------------------------- #


def _naisargika_bala(planet: str) -> float:
    return _NAISARGIKA_RANK[planet] / 7.0 * 60.0


# ----------------------------------------------------------------------- #
#   6. Drik Bala (aspectual)                                              #
# ----------------------------------------------------------------------- #


def _casts_full_aspect(aspecting: str, from_sign: int, to_sign: int) -> bool:
    """Parashari graha drishti: every planet aspects the 7th; Mars the
    4th & 8th, Jupiter the 5th & 9th, Saturn the 3rd & 10th, additionally."""
    house = (to_sign - from_sign) % 12 + 1
    if house == 7:
        return True
    if aspecting == const.MARS:
        return house in (4, 8)
    if aspecting == const.JUPITER:
        return house in (5, 9)
    if aspecting == const.SATURN:
        return house in (3, 10)
    return False


def _drik_bala(planet: str, planet_signs: dict[str, int]) -> float:
    """Net benefic-minus-malefic full aspect on the planet, / 4."""
    target_sign = planet_signs[planet]
    net = 0.0
    for other in _CLASSICAL_PLANETS:
        if other == planet:
            continue
        if _casts_full_aspect(other, planet_signs[other], target_sign):
            net += 60.0 if other in _BENEFICS else -60.0
    return net / 4.0


# ----------------------------------------------------------------------- #
#   Public entry point                                                    #
# ----------------------------------------------------------------------- #


def shadbala(chart: Any, ayanamsa: str = const.AYANAMSA_LAHIRI) -> dict[str, dict[str, Any]]:
    """Compute the six-fold Shadbala for the seven classical planets.

    Args:
        chart: A :class:`~mayaastrolib.chart.Chart`, tropical or sidereal.
            Must carry real planetary speeds (not a symbolic/profected
            chart) for Cheshta Bala.
        ayanamsa: Used only when ``chart`` is tropical.

    Returns:
        ``{planet_id: entry}`` where each ``entry`` has keys:

        - ``sthana`` / ``kala``: ``{"components": {...}, "total": float}``
        - ``dig`` / ``cheshta`` / ``naisargika`` / ``drik``: ``float``
        - ``total_virupas`` / ``total_rupas``: the summed strength
        - ``required_rupas``: the BPHS minimum for this planet
        - ``sufficient``: ``total_rupas >= required_rupas``

        All sub-strengths are in Virupas (60 Virupas = 1 Rupa).
    """
    data = _gather(chart, ayanamsa)
    planet_signs = {p: data[p]["sign"] for p in _CLASSICAL_PLANETS}

    asc_obj = chart.getAngle(const.ASC)
    mc_obj = chart.getAngle(const.MC)
    angles = {
        "asc": asc_obj.lon % 360.0,
        "mc": mc_obj.lon % 360.0,
        "desc": (asc_obj.lon + 180.0) % 360.0,
        "ic": (mc_obj.lon + 180.0) % 360.0,
    }

    hour = float(chart.date.time.value) % 24.0
    is_day = chart.isDiurnal()
    weekday_lord = _weekday_lord(chart.date)
    sun_sid = data[const.SUN]["sid"]
    moon_sid = data[const.MOON]["sid"]

    result: dict[str, dict[str, Any]] = {}
    for p in _CLASSICAL_PLANETS:
        d = data[p]
        sthana = _sthana_bala(p, d, planet_signs)
        dig = _dig_bala(p, d["native"], angles)
        kala = _kala_bala(p, d, hour, is_day, weekday_lord, sun_sid, moon_sid)
        cheshta = _cheshta_bala(p, d, kala["components"]["ayana"], kala["components"]["paksha"])
        naisargika = _naisargika_bala(p)
        drik = _drik_bala(p, planet_signs)

        total_v = sthana["total"] + dig + kala["total"] + cheshta + naisargika + drik
        result[p] = {
            "sthana": sthana,
            "dig": dig,
            "kala": kala,
            "cheshta": cheshta,
            "naisargika": naisargika,
            "drik": drik,
            "total_virupas": total_v,
            "total_rupas": total_v / 60.0,
            "required_rupas": REQUIRED_RUPAS[p],
            "sufficient": total_v / 60.0 >= REQUIRED_RUPAS[p],
        }
    return result


def _weekday_lord(date: Any) -> str:
    """Lord of the civil weekday (Sun=0..Sat=6). Documented approximation:
    the astrological day runs sunrise→sunrise, so a pre-dawn birth belongs
    to the previous weekday; this uses the civil date."""
    # WEEKDAY_LORDS is ordered Sun..Sat; Python weekday() is Mon=0..Sun=6.
    from mayaastrolib.vedic.upagrahas import WEEKDAY_LORDS

    pydt = date.to_pydatetime()
    idx = (pydt.weekday() + 1) % 7
    return WEEKDAY_LORDS[idx]

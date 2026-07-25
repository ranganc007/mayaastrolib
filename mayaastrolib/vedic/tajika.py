"""Tajika — Vedic annual ("Persian-derived") astrology.

Ships: the *varshapravesh* (the moment the sidereal Sun returns to its
natal sidereal position in a target year), the *Mudda dasha* (the
Vimshottari proportions compressed into that one year), the *Muntha*
(the progressed point that advances one sign per year of life), the
*Lord of the Year* (Varsheshwara — chosen from 5 candidates), and a
curated set of 14 *Tajika Sahams* (sensitive points — Punya, Vidya,
Yasas, Karma, Pitri, Matri, Bhratri, Putra, Kalatra, Jeeva, Vivaha,
Vyapara, Roga, Bandhu).

Deferred to a follow-up: the rest of the ~50-Saham list, Harsha Bala,
Panchavargiya Bala (so Lord-of-Year here uses a simple strength
heuristic, not the canonical Panchavargiya tally), and the Tajika
aspects (ithasala, isharafa, etc.).

References:
- Tajika Neelakanthi (the canonical Tajika text)
- B.V. Raman, *Varshaphala* (Saham formulas as commonly reproduced)
- BPHS ch. 31 (Panchavargiya Bala — carried into Tajika; not yet here)
"""

from mayaastrolib import const
from mayaastrolib.datetime import Datetime
from mayaastrolib.ephem.tools import MAX_ERROR
from mayaastrolib.vedic import ayanamsa as _ay
from mayaastrolib.vedic import nakshatras as _nak
from mayaastrolib.vedic.dasha import (
    DAYS_PER_VIMSHOTTARI_YEAR,
    VIMSHOTTARI_ORDER,
    VIMSHOTTARI_YEARS,
    DashaPeriod,
    _add_days,
)

__all__ = [
    "TAJIKA_YEAR_DAYS",
    "sidereal_sun_return_jd",
    "varshapravesh",
    "mudda_dasha",
    "muntha",
    "lord_of_year_candidates",
    "lord_of_year",
    "SAHAM_PUNYA",
    "SAHAM_VIDYA",
    "SAHAM_YASAS",
    "SAHAM_KARMA",
    "SAHAM_PITRI",
    "SAHAM_MATRI",
    "SAHAM_BHRATRI",
    "SAHAM_PUTRA",
    "SAHAM_KALATRA",
    "SAHAM_JEEVA",
    "SAHAM_VIVAHA",
    "SAHAM_VYAPARA",
    "SAHAM_ROGA",
    "SAHAM_BANDHU",
    "sahams",
]

_SWE_SUN = 0
_SWE_MOON = 1

# A Tajika year is one tropical year of the Sun's return; we use the same
# 365.25-day convention as the Vimshottari/Mudda arithmetic.
TAJIKA_YEAR_DAYS = DAYS_PER_VIMSHOTTARI_YEAR

# Traditional 7-planet sign rulerships, 0-indexed (Aries .. Pisces).
# (Kept local rather than shared — it's a 12-element table; see
# vedic/kp.py and vedic/yogas.py for the other copies.)
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
# Classical Vedic dignities (for the Lord-of-Year strength heuristic).
_OWN_SIGNS = {
    const.SUN: [4],
    const.MOON: [3],
    const.MARS: [0, 7],
    const.MERCURY: [2, 5],
    const.JUPITER: [8, 11],
    const.VENUS: [1, 6],
    const.SATURN: [9, 10],
}
_EXALTATION_SIGN = {
    const.SUN: 0,
    const.MOON: 1,
    const.MARS: 9,
    const.MERCURY: 5,
    const.JUPITER: 3,
    const.VENUS: 11,
    const.SATURN: 6,
}
_KENDRA_HOUSES = (1, 4, 7, 10)


def _sidereal_lon(swe_body, jd, ayanamsa):
    """Return the sidereal longitude of a swisseph body at ``jd``."""
    from mayaastrolib.ephem.swe import _sidereal_calc_ut

    sweList, _flg = _sidereal_calc_ut(jd, swe_body, ayanamsa)
    return sweList[0] % 360.0


def _closest_distance(a, b):
    """Signed shortest angular distance from ``a`` to ``b`` in (-180, 180]."""
    d = (b - a) % 360.0
    return d - 360.0 if d > 180.0 else d


def sidereal_sun_return_jd(start_jd, target_sidereal_lon, ayanamsa=const.AYANAMSA_LAHIRI):
    """Find the JD at or after ``start_jd`` when the sidereal Sun is at
    ``target_sidereal_lon``.

    Newton-style iteration on the Sun's mean motion, identical in shape
    to :func:`mayaastrolib.ephem.tools.solarReturnJD` but using sidereal
    longitudes.
    """
    jd = start_jd
    sun = _sidereal_lon(_SWE_SUN, jd, ayanamsa)
    # Walk forward to the first occurrence at/after start_jd.
    dist = (target_sidereal_lon - sun) % 360.0
    while abs(dist) > MAX_ERROR:
        jd = jd + dist / const.MEAN_MOTION_SUN
        sun = _sidereal_lon(_SWE_SUN, jd, ayanamsa)
        dist = _closest_distance(sun, target_sidereal_lon)
    return jd


def _natal_sidereal_sun_lon(natal_chart, ayanamsa):
    sun = natal_chart.getObject(const.SUN)
    if natal_chart.zodiac == const.ZODIAC_SIDEREAL:
        return sun.lon % 360.0
    return _ay.to_sidereal(sun.lon, natal_chart.date, ayanamsa=ayanamsa) % 360.0


def varshapravesh(natal_chart, target_year, ayanamsa=const.AYANAMSA_LAHIRI):
    """Return the varshapravesh :class:`Datetime` for ``target_year``.

    The varshapravesh is the moment in ``target_year`` when the sidereal
    Sun returns to the natal chart's sidereal Sun longitude.

    Args:
        natal_chart: The natal :class:`Chart` (tropical or sidereal).
        target_year: The civil year to compute the annual chart for.
        ayanamsa: One of ``const.LIST_AYANAMSAS``.

    Returns:
        A :class:`Datetime` in the natal chart's UTC offset.
    """
    target_lon = _natal_sidereal_sun_lon(natal_chart, ayanamsa)
    anchor = Datetime(f"{target_year}/01/01", "00:00", natal_chart.date.utcoffset)
    jd = sidereal_sun_return_jd(anchor.jd, target_lon, ayanamsa=ayanamsa)
    return Datetime.fromJD(jd, natal_chart.date.utcoffset)


def mudda_dasha(varshapravesh_date, ayanamsa=const.AYANAMSA_LAHIRI):
    """Return the 9 Mudda (Varsha Vimshottari) dasha periods for the year.

    The 365.25-day year is divided among the 9 Vimshottari lords in the
    standard proportions, the sequence starting from the lord of the
    nakshatra the Moon occupies at ``varshapravesh_date`` and proceeding
    through the Vimshottari cycle.

    Args:
        varshapravesh_date: The varshapravesh :class:`Datetime` (e.g.
            from :func:`varshapravesh`).
        ayanamsa: One of ``const.LIST_AYANAMSAS``.

    Returns:
        A list of 9 :class:`mayaastrolib.vedic.dasha.DashaPeriod` (level
        1), chronological, durations summing to 365.25 days.
    """
    moon_sid_lon = _sidereal_lon(_SWE_MOON, varshapravesh_date.jd, ayanamsa)
    start_lord = _nak.of_longitude(moon_sid_lon).lord
    start_idx = VIMSHOTTARI_ORDER.index(start_lord)

    periods = []
    current_start = varshapravesh_date
    for i in range(9):
        lord = VIMSHOTTARI_ORDER[(start_idx + i) % 9]
        days = (VIMSHOTTARI_YEARS[lord] / 120.0) * TAJIKA_YEAR_DAYS
        end = _add_days(current_start, days)
        periods.append(DashaPeriod(lord=lord, start=current_start, end=end, level=1))
        current_start = end
    return periods


# --- Muntha, Lord of Year, Sahams (Task 024b) --- #


def _sign_of(lon):
    return int((lon % 360.0) // 30.0)


def _sidereal_asc_sign(chart, ayanamsa):
    asc = chart.getAngle(const.ASC)
    if chart.zodiac == const.ZODIAC_SIDEREAL:
        return _sign_of(asc.lon)
    return _sign_of(_ay.to_sidereal(asc.lon, chart.date, ayanamsa=ayanamsa))


def _sidereal_planet_sign(chart, planet_id, ayanamsa):
    obj = chart.getObject(planet_id)
    if chart.zodiac == const.ZODIAC_SIDEREAL:
        return _sign_of(obj.lon)
    return _sign_of(_ay.to_sidereal(obj.lon, chart.date, ayanamsa=ayanamsa))


def _sidereal_lon_of_object(chart, getter, ayanamsa):
    obj = getter()
    if chart.zodiac == const.ZODIAC_SIDEREAL:
        return obj.lon % 360.0
    return _ay.to_sidereal(obj.lon, chart.date, ayanamsa=ayanamsa)


def muntha(natal_chart, target_year, ayanamsa=const.AYANAMSA_LAHIRI):
    """Return the Muntha for ``target_year``.

    The Muntha is a progressed point: it occupies the natal Lagna's sign
    at birth and advances one sign per completed year of life. For
    ``target_year`` (a civil year), the age used is ``target_year −
    birth_year``.

    Returns:
        Dict ``{sign_idx, sign, lord}`` — the Muntha's sidereal sign
        index (0..11), sign name, and ruling planet.
    """
    natal_lagna_sign = _sidereal_asc_sign(natal_chart, ayanamsa)
    birth_year = natal_chart.date.to_pydatetime().year
    age = target_year - birth_year
    sign_idx = (natal_lagna_sign + age) % 12
    return {
        "sign_idx": sign_idx,
        "sign": const.LIST_SIGNS[sign_idx],
        "lord": _SIGN_LORDS[sign_idx],
    }


def _trirashi_pati(annual_lagna_lon, is_diurnal):
    """Return the Trirashi-pati: the lord of the relevant third of the
    annual Lagna's sign.

    Each sign is split into three 10° parts. By day: 1st part → the
    sign's own lord, 2nd → the 5th sign's lord, 3rd → the 9th sign's
    lord. By night the order of the three is reversed.
    """
    sign_idx = _sign_of(annual_lagna_lon)
    deg = (annual_lagna_lon % 360.0) - sign_idx * 30.0
    part = int(deg // 10.0)  # 0, 1, 2
    offsets_day = [0, 4, 8]  # same sign, 5th, 9th
    offsets = offsets_day if is_diurnal else list(reversed(offsets_day))
    return _SIGN_LORDS[(sign_idx + offsets[part]) % 12]


def lord_of_year_candidates(annual_chart, natal_chart, target_year, ayanamsa=const.AYANAMSA_LAHIRI):
    """Return the five Varsheshwara (Lord-of-Year) candidates.

    Returns:
        A list of ``(label, planet_id)`` pairs in the traditional
        priority order: Muntha lord, annual-Lagna lord, Sun-sign lord
        (the sign the Sun occupies at varshapravesh), natal-Lagna lord,
        Trirashi-pati.
    """
    m = muntha(natal_chart, target_year, ayanamsa=ayanamsa)
    annual_lagna_lon = _sidereal_lon_of_object(
        annual_chart, lambda: annual_chart.getAngle(const.ASC), ayanamsa
    )
    annual_lagna_lord = _SIGN_LORDS[_sign_of(annual_lagna_lon)]
    sun_sign_lord = _SIGN_LORDS[_sidereal_planet_sign(annual_chart, const.SUN, ayanamsa)]
    natal_lagna_lord = _SIGN_LORDS[_sidereal_asc_sign(natal_chart, ayanamsa)]
    trirashi = _trirashi_pati(annual_lagna_lon, annual_chart.isDiurnal())
    return [
        ("muntha", m["lord"]),
        ("annual_lagna", annual_lagna_lord),
        ("sun_sign", sun_sign_lord),
        ("natal_lagna", natal_lagna_lord),
        ("trirashi", trirashi),
    ]


def _simple_strength(planet, annual_chart, annual_lagna_sign, ayanamsa):
    """A crude 0–3 strength tally for the Lord-of-Year heuristic:
    +1 if the planet is in its own sign, +1 if exalted, +1 if in a
    kendra from the annual Lagna. (The canonical Tajika rule uses
    Panchavargiya Bala — see the module docstring.)"""
    sign = _sidereal_planet_sign(annual_chart, planet, ayanamsa)
    score = 0
    if sign in _OWN_SIGNS.get(planet, []):
        score += 1
    if _EXALTATION_SIGN.get(planet) == sign:
        score += 1
    house = (sign - annual_lagna_sign) % 12 + 1
    if house in _KENDRA_HOUSES:
        score += 1
    return score


def lord_of_year(annual_chart, natal_chart, target_year, ayanamsa=const.AYANAMSA_LAHIRI):
    """Return the Lord of the Year (Varsheshwara) as ``(label, planet_id)``.

    Picks the candidate with the highest simple strength tally
    (own-sign / exalted / in-a-kendra in the annual chart), ties broken
    by the traditional candidate priority (Muntha lord first).

    NOTE: the canonical Tajika rule picks the strongest candidate by
    *Panchavargiya Bala* — a five-component strength sum not yet
    implemented. This is a documented heuristic stand-in.
    """
    candidates = lord_of_year_candidates(annual_chart, natal_chart, target_year, ayanamsa=ayanamsa)
    annual_lagna_sign = _sidereal_asc_sign(annual_chart, ayanamsa)
    best = None
    best_score = -1
    for label, planet in candidates:
        s = _simple_strength(planet, annual_chart, annual_lagna_sign, ayanamsa)
        if s > best_score:
            best_score = s
            best = (label, planet)
    return best


# --- Sahams (sensitive points) --- #

# Saham names (subset of the Tajika Neelakanthi list).
SAHAM_PUNYA = "Punya"  # virtue / merit
SAHAM_VIDYA = "Vidya"  # learning  (= Punya reversed)
SAHAM_YASAS = "Yasas"  # fame / glory
SAHAM_KARMA = "Karma"  # work / vocation
SAHAM_PITRI = "Pitri"  # father
SAHAM_MATRI = "Matri"  # mother
SAHAM_BHRATRI = "Bhratri"  # siblings
SAHAM_PUTRA = "Putra"  # children
SAHAM_KALATRA = "Kalatra"  # spouse
SAHAM_JEEVA = "Jeeva"  # livelihood
SAHAM_VIVAHA = "Vivaha"  # marriage
SAHAM_VYAPARA = "Vyapara"  # business / trade
SAHAM_ROGA = "Roga"  # illness
SAHAM_BANDHU = "Bandhu"  # relatives / kin

# Each entry: name -> (term_a, term_b, term_c, reversible).
#
# Day formula in all cases: ``term_a - term_b + term_c``. A "reversible"
# Saham swaps term_a and term_b for a nocturnal chart; term_c never moves.
# Most Sahams use the Lagna as term_c, but a few classical formulas add a
# planet instead (Gaurava adds the Sun, Jadya adds Mercury, Bandhana adds
# the Moon), which is why the third term is explicit rather than assumed.
#
# Each term is one of:
#   * a planet ID          -> its sidereal longitude in the annual chart
#   * "Asc"                -> the annual Lagna
#   * "LagnaLord"          -> the sidereal longitude of the Lagna sign's lord
#   * a SAHAM_* name       -> that Saham's longitude (it must be defined
#                             earlier in this dict)
#
# SOURCING: Saham formulas vary materially across sources. These 14 follow
# Tajika Neelakanthi as commonly reproduced (e.g. in B.V. Raman,
# *Varshaphala*).
#
# The classical list runs to roughly 50. Extending this table is deliberately
# NOT a from-memory exercise: an attempt to add ten more (Task v1.0-07b)
# produced three that were algebraically identical to entries already here
# (Paradara == Kalatra, Santapa == Roga, and Gaurava == Yasas on a diurnal
# chart), which is what a mis-remembered formula looks like. Adding the
# remainder needs a text to check against, and each new entry must clear the
# collision test in tests/test_vedic_tajika.py.
#
# The engine below is ready for them: it supports an explicit third term
# (several classical formulas add a planet rather than the Lagna) and the
# "LagnaLord" term, so a sourced addition is data entry, not code.
_SAHAM_FORMULAS = {
    SAHAM_PUNYA: (const.MOON, const.SUN, "Asc", True),
    SAHAM_VIDYA: (const.SUN, const.MOON, "Asc", True),
    SAHAM_KARMA: (const.MARS, const.SUN, "Asc", True),
    SAHAM_PITRI: (const.SUN, const.SATURN, "Asc", True),
    SAHAM_MATRI: (const.MOON, const.VENUS, "Asc", True),
    SAHAM_BHRATRI: (const.JUPITER, const.SATURN, "Asc", True),
    SAHAM_PUTRA: (const.JUPITER, const.MOON, "Asc", True),
    SAHAM_KALATRA: (const.VENUS, const.SUN, "Asc", True),
    SAHAM_JEEVA: (const.SATURN, const.JUPITER, "Asc", True),
    SAHAM_VIVAHA: (const.VENUS, const.SATURN, "Asc", True),
    SAHAM_VYAPARA: (const.MERCURY, const.SUN, "Asc", True),
    SAHAM_ROGA: (const.SATURN, const.MOON, "Asc", True),
    SAHAM_BANDHU: (const.MERCURY, const.MOON, "Asc", True),
    # Yasas references the Punya Saham, so it comes last.
    SAHAM_YASAS: (const.JUPITER, SAHAM_PUNYA, "Asc", True),
}

# Bodies whose sidereal longitudes the Saham formulas may reference.
_SAHAM_BODIES = (
    const.SUN,
    const.MOON,
    const.MARS,
    const.MERCURY,
    const.JUPITER,
    const.VENUS,
    const.SATURN,
)


def sahams(annual_chart, ayanamsa=const.AYANAMSA_LAHIRI):
    """Return the Tajika Sahams (sensitive points) for an annual chart.

    Args:
        annual_chart: A :class:`Chart` built at the varshapravesh moment
            (tropical or sidereal).
        ayanamsa: Used only when the chart is tropical.

    Returns:
        Dict ``{saham_name: sidereal_longitude}`` — Punya, Vidya, Yasas,
        Karma, Pitri, Matri, Bhratri, Putra, Kalatra, Jeeva, Vivaha,
        Vyapara, Roga, Bandhu — all normalised to ``[0, 360)``. For a
        diurnal chart the standard day formulas are used; for a
        nocturnal chart the two non-Lagna terms are swapped (the
        reversible-Saham rule).

    The Saham formulas vary across sources; these follow Tajika
    Neelakanthi as commonly reproduced. This is a curated subset of the
    ~50-Saham list — the remainder is a follow-up.
    """

    def sid(getter):
        return _sidereal_lon_of_object(annual_chart, getter, ayanamsa)

    asc = sid(lambda: annual_chart.getAngle(const.ASC))
    body_lons = {p: sid(lambda p=p: annual_chart.getObject(p)) for p in _SAHAM_BODIES}
    diurnal = annual_chart.isDiurnal()

    def _term(t, computed):
        if t == "Asc":
            return asc
        if t == "LagnaLord":
            lord = _SIGN_LORDS[int(asc // 30)]
            if lord not in body_lons:
                raise ValueError(f"Lagna lord {lord!r} is not among the Saham bodies")
            return body_lons[lord]
        if t in body_lons:
            return body_lons[t]
        if t in computed:
            return computed[t]
        raise ValueError(f"Unresolvable Saham term {t!r}")

    computed = {}
    for name, (a, b, c, reversible) in _SAHAM_FORMULAS.items():
        va = _term(a, computed)
        vb = _term(b, computed)
        vc = _term(c, computed)
        if reversible and not diurnal:
            va, vb = vb, va
        computed[name] = (va - vb + vc) % 360.0
    return computed

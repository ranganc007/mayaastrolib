"""Ashtakavarga — the bindu (benefic-point) system. BPHS ch. 66.

Each of the 7 classical planets gets a Bhinnashtakavarga (BAV): a 12-cell
array counting how many "benefic points" it receives in each sign,
contributed by the positions of 8 bodies (the 7 planets + the
Ascendant — hence "ashta", eight). The Sarvashtakavarga (SAV) sums the
7 planetary BAVs per sign; the grand total is canonically 337.

House counting convention: "house h from contributor C" means the sign
``(c_sign + h - 1) % 12`` — house 1 is C's own sign.

References:
- Brihat Parashara Hora Shastra (BPHS) ch. 66 (Prastara Ashtakavarga)
- Phaladeepika ch. 19 (cross-reference)
"""

from mayaastrolib import const
from mayaastrolib.vedic import ayanamsa as _ay

# The Lagna contributor key — not a planet ID.
ASCENDANT = "Ascendant"

# Contributors that supply bindus to every BAV.
ASHTAKAVARGA_CONTRIBUTORS = [
    const.SUN,
    const.MOON,
    const.MARS,
    const.MERCURY,
    const.JUPITER,
    const.VENUS,
    const.SATURN,
    ASCENDANT,
]

# Planets whose BAVs are summed into the SAV (Ascendant's own BAV is not).
ASHTAKAVARGA_PLANETS = [
    const.SUN,
    const.MOON,
    const.MARS,
    const.MERCURY,
    const.JUPITER,
    const.VENUS,
    const.SATURN,
]

# Canonical BPHS Ch. 66 Prastara tables: for each planet whose BAV is
# being built, the houses (counted from each contributor) that receive a
# bindu. Per-planet totals: Sun 48, Moon 49, Mars 39, Mercury 54,
# Jupiter 56, Venus 52, Saturn 39 — these sum to 337 (the SAV grand
# total invariant).
ASHTAKAVARGA_TABLES = {
    const.SUN: {
        const.SUN: [1, 2, 4, 7, 8, 9, 10, 11],
        const.MOON: [3, 6, 10, 11],
        const.MARS: [1, 2, 4, 7, 8, 9, 10, 11],
        const.MERCURY: [3, 5, 6, 9, 10, 11, 12],
        const.JUPITER: [5, 6, 9, 11],
        const.VENUS: [6, 7, 12],
        const.SATURN: [1, 2, 4, 7, 8, 9, 10, 11],
        ASCENDANT: [3, 4, 6, 10, 11, 12],
    },
    const.MOON: {
        const.SUN: [3, 6, 7, 8, 10, 11],
        const.MOON: [1, 3, 6, 7, 10, 11],
        const.MARS: [2, 3, 5, 6, 9, 10, 11],
        const.MERCURY: [1, 3, 4, 5, 7, 8, 10, 11],
        const.JUPITER: [1, 4, 7, 8, 10, 11, 12],
        const.VENUS: [3, 4, 5, 7, 9, 10, 11],
        const.SATURN: [3, 5, 6, 11],
        ASCENDANT: [3, 6, 10, 11],
    },
    const.MARS: {
        const.SUN: [3, 5, 6, 10, 11],
        const.MOON: [3, 6, 11],
        const.MARS: [1, 2, 4, 7, 8, 10, 11],
        const.MERCURY: [3, 5, 6, 11],
        const.JUPITER: [6, 10, 11, 12],
        const.VENUS: [6, 8, 11, 12],
        const.SATURN: [1, 4, 7, 8, 9, 10, 11],
        ASCENDANT: [1, 3, 6, 10, 11],
    },
    const.MERCURY: {
        const.SUN: [5, 6, 9, 11, 12],
        const.MOON: [2, 4, 6, 8, 10, 11],
        const.MARS: [1, 2, 4, 7, 8, 9, 10, 11],
        const.MERCURY: [1, 3, 5, 6, 9, 10, 11, 12],
        const.JUPITER: [6, 8, 11, 12],
        const.VENUS: [1, 2, 3, 4, 5, 8, 9, 11],
        const.SATURN: [1, 2, 4, 7, 8, 9, 10, 11],
        ASCENDANT: [1, 2, 4, 6, 8, 10, 11],
    },
    const.JUPITER: {
        const.SUN: [1, 2, 3, 4, 7, 8, 9, 10, 11],
        const.MOON: [2, 5, 7, 9, 11],
        const.MARS: [1, 2, 4, 7, 8, 10, 11],
        const.MERCURY: [1, 2, 4, 5, 6, 9, 10, 11],
        const.JUPITER: [1, 2, 3, 4, 7, 8, 10, 11],
        const.VENUS: [2, 5, 6, 9, 10, 11],
        const.SATURN: [3, 5, 6, 12],
        ASCENDANT: [1, 2, 4, 5, 6, 7, 9, 10, 11],
    },
    const.VENUS: {
        const.SUN: [8, 11, 12],
        const.MOON: [1, 2, 3, 4, 5, 8, 9, 11, 12],
        const.MARS: [3, 5, 6, 9, 11, 12],
        const.MERCURY: [3, 5, 6, 9, 11],
        const.JUPITER: [5, 8, 9, 10, 11],
        const.VENUS: [1, 2, 3, 4, 5, 8, 9, 10, 11],
        const.SATURN: [3, 4, 5, 8, 9, 10, 11],
        ASCENDANT: [1, 2, 3, 4, 5, 8, 9, 11],
    },
    const.SATURN: {
        const.SUN: [1, 2, 4, 7, 8, 10, 11],
        const.MOON: [3, 6, 11],
        const.MARS: [3, 5, 6, 10, 11, 12],
        const.MERCURY: [6, 8, 9, 10, 11, 12],
        const.JUPITER: [5, 6, 11, 12],
        const.VENUS: [6, 11, 12],
        const.SATURN: [3, 5, 6, 11],
        ASCENDANT: [1, 3, 4, 6, 10, 11],
    },
}

# Sanity invariants — enforced at import time so a typo can't ship.
_PLANET_TOTALS = {
    p: sum(len(v) for v in ASHTAKAVARGA_TABLES[p].values()) for p in ASHTAKAVARGA_PLANETS
}
assert _PLANET_TOTALS == {
    const.SUN: 48,
    const.MOON: 49,
    const.MARS: 39,
    const.MERCURY: 54,
    const.JUPITER: 56,
    const.VENUS: 52,
    const.SATURN: 39,
}, _PLANET_TOTALS
assert sum(_PLANET_TOTALS.values()) == 337


def _sign_of(lon):
    """Return sign index 0..11 for a longitude."""
    return int((lon % 360.0) // 30.0)


def bhinnashtakavarga(planet, signs):
    """Return the 12-cell Bhinnashtakavarga for ``planet``.

    Args:
        planet: One of ``ASHTAKAVARGA_PLANETS``.
        signs: Mapping of body ID → sign index (0..11) for the 8
            contributors. Must include all of ``ASHTAKAVARGA_CONTRIBUTORS``
            (use the literal ``ASCENDANT`` key for the rising sign).

    Returns:
        A 12-element list; index 0 = Aries, …, 11 = Pisces. The list
        sums to the planet's canonical total (Sun 48, Moon 49, …).
    """
    if planet not in ASHTAKAVARGA_TABLES:
        raise ValueError(
            f"{planet!r} has no Ashtakavarga table; expected one of {ASHTAKAVARGA_PLANETS}"
        )
    bav = [0] * 12
    table = ASHTAKAVARGA_TABLES[planet]
    for contributor in ASHTAKAVARGA_CONTRIBUTORS:
        if contributor not in signs:
            raise ValueError(f"signs is missing contributor {contributor!r}")
        c_sign = signs[contributor] % 12
        for house in table[contributor]:
            target_sign = (c_sign + house - 1) % 12
            bav[target_sign] += 1
    return bav


def sarvashtakavarga(planet_signs, lagna_sign):
    """Return the Sarvashtakavarga — the per-sign sum of the 7 planetary BAVs.

    Args:
        planet_signs: Mapping of planet ID → sign index for the 7
            classical planets.
        lagna_sign: Sign index of the Ascendant.

    Returns:
        Dict with keys:
        - ``"per_rasi"``: 12-element list, the SAV bindu count per sign.
        - ``"grand_total"``: int — sum of per_rasi. Canonically 337.
        - ``"by_planet"``: dict {planet_id: 12-element BAV list}.
    """
    signs = dict(planet_signs)
    signs[ASCENDANT] = lagna_sign % 12
    by_planet = {p: bhinnashtakavarga(p, signs) for p in ASHTAKAVARGA_PLANETS}
    per_rasi = [sum(by_planet[p][i] for p in ASHTAKAVARGA_PLANETS) for i in range(12)]
    return {
        "per_rasi": per_rasi,
        "grand_total": sum(per_rasi),
        "by_planet": by_planet,
    }


def ashtakavarga(chart, ayanamsa=const.AYANAMSA_LAHIRI):
    """Compute the full Ashtakavarga (BAV + SAV) for a chart.

    Handles both tropical and sidereal charts — tropical input is
    shifted to sidereal via the supplied ayanamsa before sign extraction.

    Returns:
        The same dict shape as :func:`sarvashtakavarga`.
    """
    if chart.zodiac == const.ZODIAC_SIDEREAL:

        def sid_lon(obj):
            return obj.lon
    else:

        def sid_lon(obj):
            return _ay.to_sidereal(obj.lon, chart.date, ayanamsa=ayanamsa)

    planet_signs = {}
    for p in ASHTAKAVARGA_PLANETS:
        planet_signs[p] = _sign_of(sid_lon(chart.getObject(p)))
    asc = chart.getAngle(const.ASC)
    lagna_sign = _sign_of(sid_lon(asc))
    return sarvashtakavarga(planet_signs, lagna_sign)

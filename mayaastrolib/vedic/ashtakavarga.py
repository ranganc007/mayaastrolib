"""Ashtakavarga — the bindu (benefic-point) system. BPHS ch. 66, 8.

Each of the 7 classical planets gets a Bhinnashtakavarga (BAV): a 12-cell
array counting how many "benefic points" it receives in each sign,
contributed by the positions of 8 bodies (the 7 planets + the
Ascendant — hence "ashta", eight). The Sarvashtakavarga (SAV) sums the
7 planetary BAVs per sign; the grand total is canonically 337.

This module also provides:
- the *prastara* (per-contributor breakdown) — `bhinnashtakavarga_prastara`;
- the *shodhana* reductions — `trikona_shodhana` (by trine),
  `ekadhipatya_shodhana` (by co-rulership), and `shodhita_sarvashtakavarga`
  (the SAV after both);
- *kakshya* — `kakshya_of` (which of the 8 sub-divisions of a sign a
  longitude is in) and `kakshya_transit_active` (transit timing).

House counting convention: "house h from contributor C" means the sign
``(c_sign + h - 1) % 12`` — house 1 is C's own sign.

References:
- Brihat Parashara Hora Shastra (BPHS) ch. 66 (Prastara), ch. 8
  (Shodhana, Kakshya)
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


# --- Prastara (per-contributor breakdown) --- #


def bhinnashtakavarga_prastara(planet, signs):
    """Return the per-contributor Bhinnashtakavarga ("prastara") for ``planet``.

    Like :func:`bhinnashtakavarga` but instead of summing, returns the
    breakdown: ``{contributor_id: 12-cell list}`` where each cell is 0
    or 1 (the bindu that contributor places in that sign for this
    planet). Summing the eight 12-cell lists element-wise reproduces
    :func:`bhinnashtakavarga`.
    """
    if planet not in ASHTAKAVARGA_TABLES:
        raise ValueError(
            f"{planet!r} has no Ashtakavarga table; expected one of {ASHTAKAVARGA_PLANETS}"
        )
    table = ASHTAKAVARGA_TABLES[planet]
    prastara = {}
    for contributor in ASHTAKAVARGA_CONTRIBUTORS:
        if contributor not in signs:
            raise ValueError(f"signs is missing contributor {contributor!r}")
        c_sign = signs[contributor] % 12
        row = [0] * 12
        for house in table[contributor]:
            row[(c_sign + house - 1) % 12] = 1
        prastara[contributor] = row
    return prastara


# --- Shodhana (reduction) --- #

# The four trine ("trikona") groups of sign indices.
TRIKONA_GROUPS = ([0, 4, 8], [1, 5, 9], [2, 6, 10], [3, 7, 11])

# The five co-rulership ("ekadhipatya") sign pairs (signs sharing a
# planet-lord). Cancer (Moon) and Leo (Sun) are single-rulership — no pair.
EKADHIPATYA_PAIRS = (
    (0, 7),  # Aries / Scorpio — Mars
    (1, 6),  # Taurus / Libra — Venus
    (2, 5),  # Gemini / Virgo — Mercury
    (8, 11),  # Sagittarius / Pisces — Jupiter
    (9, 10),  # Capricorn / Aquarius — Saturn
)


def trikona_shodhana(bav):
    """Apply trikona (trine) reduction to a 12-cell BAV.

    For each of the four trine groups, the minimum of the three cells is
    subtracted from all three. (If the minimum is zero the trine is
    unchanged. Some texts use a harsher rule — "if any trine member is
    zero, zero the whole trine" — which is *not* what this implements.)

    Returns a new 12-cell list; the input is not modified.
    """
    result = list(bav)
    for group in TRIKONA_GROUPS:
        m = min(result[i] for i in group)
        for i in group:
            result[i] -= m
    return result


def ekadhipatya_shodhana(bav, occupied_signs):
    """Apply ekadhipatya (co-rulership) reduction to a 12-cell BAV.

    For each of the five co-rulership sign pairs ``(a, b)``, using
    whether each sign is *occupied* (has a planet of the natal chart in
    it):

    - both occupied → unchanged;
    - neither occupied → if the two cells differ, both become the
      smaller; if equal, both become 0;
    - one occupied, one not → the unoccupied cell becomes 0 if the
      occupied cell's value is greater-or-equal, otherwise both become
      the smaller value.

    (Ekadhipatya rules vary across sources — this is one common variant.
    Apply *after* :func:`trikona_shodhana`.)

    Args:
        bav: A 12-cell list (typically already trikona-reduced).
        occupied_signs: An iterable of sign indices that contain a
            planet in the chart.

    Returns a new 12-cell list; the input is not modified.
    """
    result = list(bav)
    occ = set(occupied_signs)
    for a, b in EKADHIPATYA_PAIRS:
        va, vb = result[a], result[b]
        a_occ, b_occ = a in occ, b in occ
        if a_occ and b_occ:
            continue
        if not a_occ and not b_occ:
            if va == vb:
                result[a] = result[b] = 0
            else:
                lo = min(va, vb)
                result[a] = result[b] = lo
        else:
            # Exactly one occupied.
            occ_val = va if a_occ else vb
            unocc_idx = b if a_occ else a
            unocc_val = vb if a_occ else va
            if occ_val >= unocc_val:
                result[unocc_idx] = 0
            else:
                result[a] = result[b] = min(va, vb)
    return result


def shodhita_sarvashtakavarga(planet_signs, lagna_sign):
    """Return the SAV after trikona + ekadhipatya reduction of each BAV.

    Args:
        planet_signs: Mapping of planet ID → sign index for the 7
            classical planets.
        lagna_sign: Sign index of the Ascendant.

    Returns:
        Dict with keys ``"per_rasi"`` (12-cell list, the reduced SAV),
        ``"grand_total"`` (its sum — typically much less than 337), and
        ``"by_planet"`` (dict ``{planet_id: reduced 12-cell BAV}``).
    """
    signs = dict(planet_signs)
    signs[ASCENDANT] = lagna_sign % 12
    occupied = set(planet_signs.values())  # signs occupied by a planet
    by_planet = {}
    for p in ASHTAKAVARGA_PLANETS:
        bav = bhinnashtakavarga(p, signs)
        reduced = ekadhipatya_shodhana(trikona_shodhana(bav), occupied)
        by_planet[p] = reduced
    per_rasi = [sum(by_planet[p][i] for p in ASHTAKAVARGA_PLANETS) for i in range(12)]
    return {
        "per_rasi": per_rasi,
        "grand_total": sum(per_rasi),
        "by_planet": by_planet,
    }


# --- Kakshya --- #

# The 8 kakshya lords, in order from 0° to 30° within a sign
# (each kakshya is 3°45').
KAKSHYA_LORDS = (
    const.SATURN,
    const.JUPITER,
    const.MARS,
    const.SUN,
    const.VENUS,
    const.MERCURY,
    const.MOON,
    ASCENDANT,
)
KAKSHYA_WIDTH_DEG = 30.0 / 8.0  # 3°45'


def kakshya_of(sidereal_lon):
    """Return the kakshya lord for a sidereal longitude.

    Each sign's 30° is split into 8 kakshyas of 3°45' each, ruled in the
    fixed order Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon,
    Ascendant (Lagna) from 0° to 30°.
    """
    deg = (sidereal_lon % 360.0) % 30.0
    idx = int(deg / KAKSHYA_WIDTH_DEG)
    if idx > 7:
        idx = 7
    return KAKSHYA_LORDS[idx]


def kakshya_transit_active(prastara, transiting_lon):
    """Return whether the transiting planet's current kakshya is "active".

    A transit through a sign is judged auspicious for the kakshya whose
    lord (as an Ashtakavarga *contributor*) places a bindu in that sign
    in the relevant prastara. This returns ``(kakshya_lord, active)``
    where ``active`` is ``True`` iff that contributor's row of
    ``prastara`` has a 1 in the transited sign.

    Args:
        prastara: A ``{contributor_id: 12-cell list}`` mapping, e.g.
            from :func:`bhinnashtakavarga_prastara`.
        transiting_lon: The transiting planet's sidereal longitude.

    Returns:
        ``(kakshya_lord, bool)``.
    """
    sign = _sign_of(transiting_lon)
    lord = kakshya_of(transiting_lon)
    row = prastara.get(lord)
    active = bool(row[sign]) if row is not None else False
    return lord, active

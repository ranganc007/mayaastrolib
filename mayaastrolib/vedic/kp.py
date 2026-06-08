"""Krishnamurti Paddhati (KP) — the Star-Sub sub-lord system.

The KP zodiac divides each of the 27 nakshatras (13°20') into 9 "subs"
with widths proportional to the Vimshottari dasha years
(Ketu 7, Venus 20, Sun 6, Moon 10, Mars 7, Rahu 18, Jupiter 16,
Saturn 19, Mercury 17 — total 120), the sub sequence starting from the
nakshatra's own lord and cycling through the Vimshottari order. That's
27 × 9 = 243 Star-Sub segments.

The canonical "249" sub-lord table additionally splits at the 12 sign
boundaries. Six of those coincide with nakshatra/sub boundaries; the
other six (30°, 90°, 150°, 210°, 270°, 330°) each fall strictly inside
a sub-segment and bisect it. 243 + 6 = 249 rows.

References:
- K.S. Krishnamurti, *Krishnamurti Padhdhati* (the six "Readers")
- Standard KP "249" sub-lord tables (reproduced in countless KP texts)
"""

from mayaastrolib import const
from mayaastrolib.vedic import ayanamsa as _ay
from mayaastrolib.vedic import nakshatras as _nak
from mayaastrolib.vedic.dasha import VIMSHOTTARI_ORDER, VIMSHOTTARI_YEARS

# Traditional 7-planet sign rulerships. Index 0 = Aries .. 11 = Pisces.
SIGN_LORDS = [
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

_SEG = _nak.NAKSHATRA_SPAN_DEG  # 13°20' per nakshatra
_EPS = 1e-6  # degrees, for dedup of change points


def _sub_sequence_for_nakshatra(nak_idx):
    """Return the 9 sub-lord IDs of nakshatra ``nak_idx`` in order.

    The sequence starts with the nakshatra's own lord and proceeds
    through the Vimshottari cycle.
    """
    lord = _nak.NAKSHATRA_LORDS[nak_idx]
    start = VIMSHOTTARI_ORDER.index(lord)
    return [VIMSHOTTARI_ORDER[(start + i) % 9] for i in range(9)]


def _vimshottari_sequence_from(lord):
    """Return the 9-lord Vimshottari cycle starting from ``lord``."""
    start = VIMSHOTTARI_ORDER.index(lord)
    return [VIMSHOTTARI_ORDER[(start + i) % 9] for i in range(9)]


def _proportional_lord(fraction, seq):
    """Given a fraction 0..1 of a span and a 9-lord sequence with widths
    proportional to the Vimshottari years, return the lord whose
    sub-span contains ``fraction``."""
    cum = 0.0
    for lord in seq:
        cum += VIMSHOTTARI_YEARS[lord] / 120.0
        if fraction < cum - _EPS / _SEG:
            return lord
    return seq[-1]


def _sub_lord(sidereal_lon):
    """Return the KP sub-lord ID at ``sidereal_lon``."""
    lon = sidereal_lon % 360.0
    nak_idx = int(lon // _SEG)
    pos_in_nak = (lon - nak_idx * _SEG) / _SEG  # fraction 0..1
    return _proportional_lord(pos_in_nak, _sub_sequence_for_nakshatra(nak_idx))


def _sub_sub_lord(sidereal_lon):
    """Return the KP sub-sub-lord ID (the 4th level) at ``sidereal_lon``.

    Within a sub (whose width is proportional to its lord's Vimshottari
    years), the 30° is divided again into 9 parts proportional to the
    Vimshottari years, the sequence starting from the sub's own lord.
    """
    lon = sidereal_lon % 360.0
    nak_idx = int(lon // _SEG)
    pos_in_nak = (lon - nak_idx * _SEG) / _SEG  # fraction 0..1 of the nakshatra
    sub_seq = _sub_sequence_for_nakshatra(nak_idx)
    # Walk the subs to find which one we're in and our fraction within it.
    cum = 0.0
    for sub_lord in sub_seq:
        width = VIMSHOTTARI_YEARS[sub_lord] / 120.0
        if pos_in_nak < cum + width - _EPS / _SEG:
            frac_in_sub = (pos_in_nak - cum) / width if width > 0 else 0.0
            return _proportional_lord(frac_in_sub, _vimshottari_sequence_from(sub_lord))
        cum += width
    # Boundary: last sub, last sub-sub.
    return _vimshottari_sequence_from(sub_seq[-1])[-1]


def sub_lord_at(sidereal_lon, with_sub_sub=False):
    """Return the full KP chain at ``sidereal_lon``.

    Args:
        sidereal_lon: A sidereal ecliptic longitude in degrees. For
            KP-correct results compute it under the Krishnamurti
            ayanamsa.
        with_sub_sub: If True, the result also includes ``sub_sub_lord``
            (the 4th level).

    Returns:
        Dict with keys ``longitude`` (normalised), ``sign``,
        ``sign_lord``, ``nakshatra``, ``star_lord``, ``pada``,
        ``sub_lord`` — and ``sub_sub_lord`` when ``with_sub_sub=True``.
    """
    lon = sidereal_lon % 360.0
    sign_idx = int(lon // 30.0)
    nak = _nak.of_longitude(lon)
    chain = {
        "longitude": lon,
        "sign": const.LIST_SIGNS[sign_idx],
        "sign_lord": SIGN_LORDS[sign_idx],
        "nakshatra": nak.name,
        "star_lord": nak.lord,
        "pada": nak.pada,
        "sub_lord": _sub_lord(lon),
    }
    if with_sub_sub:
        chain["sub_sub_lord"] = _sub_sub_lord(lon)
    return chain


def sub_sub_lord_at(sidereal_lon):
    """Return just the KP sub-sub-lord ID (the 4th level) at ``sidereal_lon``."""
    return _sub_sub_lord(sidereal_lon)


def _build_kp_table():
    """Build the 249-row KP sub-lord table.

    Collects the union of the 243 sub-segment end longitudes and the 12
    sign boundaries, dedups within ``_EPS``, sorts, and tags each
    consecutive (wrapping) interval by its midpoint.
    """
    points = []
    # Sub-segment ends — collect the end of each of the 27×9 subs.
    for nak_idx in range(27):
        nak_start = nak_idx * _SEG
        cum = 0.0
        for sub_lord in _sub_sequence_for_nakshatra(nak_idx):
            cum += VIMSHOTTARI_YEARS[sub_lord] / 120.0
            points.append((nak_start + cum * _SEG) % 360.0)
    # Sign boundaries.
    points.extend(j * 30.0 for j in range(12))
    # Dedup within epsilon.
    points.sort()
    deduped = []
    for p in points:
        if not deduped or abs(p - deduped[-1]) > _EPS:
            deduped.append(p)
    # 0.0 may appear at both ends after the modulo; ensure it's once.
    if deduped and abs(deduped[0]) <= _EPS and abs(deduped[-1] - 360.0) <= _EPS:
        deduped.pop()  # drop the 360.0 duplicate of 0.0
    rows = []
    n = len(deduped)
    for i in range(n):
        start = deduped[i]
        end = deduped[(i + 1) % n]
        if end <= start + _EPS:
            end += 360.0
        mid = ((start + end) / 2.0) % 360.0
        sign_idx = int(mid // 30.0)
        nak = _nak.of_longitude(mid)
        rows.append(
            {
                "start_lon": start % 360.0,
                "end_lon": end % 360.0,
                "sign": const.LIST_SIGNS[sign_idx],
                "sign_lord": SIGN_LORDS[sign_idx],
                "nakshatra": nak.name,
                "star_lord": nak.lord,
                "sub_lord": _sub_lord(mid),
            }
        )
    return rows


_KP_TABLE = _build_kp_table()
assert len(_KP_TABLE) == 249, f"KP table has {len(_KP_TABLE)} rows, expected 249"


def kp_table():
    """Return the 249-row KP sub-lord table.

    Each row is a dict ``{start_lon, end_lon, sign, sign_lord,
    nakshatra, star_lord, sub_lord}``. The rows tile ``[0, 360)`` with
    no gaps or overlaps. The list is built once at import; callers
    should treat it as read-only.
    """
    return _KP_TABLE


_CLASSICAL_PLANETS = (
    const.SUN,
    const.MOON,
    const.MARS,
    const.MERCURY,
    const.JUPITER,
    const.VENUS,
    const.SATURN,
)


def kp_sublords(chart, ayanamsa=const.AYANAMSA_KRISHNAMURTI):
    """Return the KP sub-lord chains for a chart's planets and Ascendant.

    Args:
        chart: A :class:`Chart`. If sidereal, its positions are used
            as-is — for KP-correct results, build it with
            ``ayanamsa=AYANAMSA_KRISHNAMURTI``. If tropical, positions
            are shifted to sidereal via ``ayanamsa`` (default the KP
            ayanamsa).
        ayanamsa: Used only when ``chart.zodiac == ZODIAC_TROPICAL``.

    Returns:
        Dict ``{body_id: <sub_lord_at dict>}`` for the 7 classical
        planets plus ``const.ASC``.
    """

    def sid_lon(obj):
        if chart.zodiac == const.ZODIAC_SIDEREAL:
            return obj.lon
        return _ay.to_sidereal(obj.lon, chart.date, ayanamsa=ayanamsa)

    result = {p: sub_lord_at(sid_lon(chart.getObject(p))) for p in _CLASSICAL_PLANETS}
    result[const.ASC] = sub_lord_at(sid_lon(chart.getAngle(const.ASC)))
    return result


# --- KP horary --- #

# Weekday lords, Sunday=0 .. Saturday=6.
_WEEKDAY_LORDS = [
    const.SUN,
    const.MOON,
    const.MARS,
    const.MERCURY,
    const.JUPITER,
    const.VENUS,
    const.SATURN,
]


def prashna_to_longitude(prashna_number):
    """Return the sidereal longitude (the midpoint of the corresponding
    249-row KP segment) for a horary *prashna* number 1..249.

    Args:
        prashna_number: An integer in ``[1, 249]``.

    Returns:
        The midpoint longitude of the ``prashna_number``-th row of
        :func:`kp_table` (1-indexed), in degrees.

    Raises:
        ValueError: if ``prashna_number`` is outside ``[1, 249]``.
    """
    if not (1 <= prashna_number <= 249):
        raise ValueError(f"prashna_number must be in [1, 249]; got {prashna_number}")
    row = _KP_TABLE[prashna_number - 1]
    start, end = row["start_lon"], row["end_lon"]
    if end <= start:
        end += 360.0
    return ((start + end) / 2.0) % 360.0


def kp_horary(prashna_number):
    """Return the KP horary Ascendant chain for a *prashna* number.

    The querent's number 1..249 selects one of the 249 KP segments; the
    horary Ascendant is taken at the midpoint of that segment. (This
    returns the Lagna's sub-lord chain — building a full horary chart
    with house cusps from a fixed Ascendant degree is a follow-up.)

    Returns:
        Dict ``{"prashna": int, "lagna_longitude": float, "lagna":
        <sub_lord_at dict including sub_sub_lord>}``.
    """
    lon = prashna_to_longitude(prashna_number)
    return {
        "prashna": prashna_number,
        "lagna_longitude": lon,
        "lagna": sub_lord_at(lon, with_sub_sub=True),
    }


def kp_horary_chart(prashna_number):
    """Return a full KP horary chart — 12 house cusps with sub-lord chains.

    The querent's number 1..249 fixes the horary Ascendant (the midpoint
    of the corresponding KP segment). The remaining cusps are placed
    **equal-house** — each 30° from the Ascendant — and every cusp is
    resolved to its full KP chain (sign / star / sub / sub-sub lord).

    Why equal house: the 249-number method supplies only an Ascendant
    *degree*, not a birth time or latitude, so the Placidus intermediate
    cusps KP normally uses are undetermined from the number alone. Equal
    houses are the deterministic, number-only choice. When you do have the
    question's time and place, cast a sidereal ``Chart`` (Krishnamurti
    ayanamsa) and pass it to :func:`kp_sublords` for true Placidus cusps.

    Args:
        prashna_number: An integer in ``[1, 249]``.

    Returns:
        Dict ``{"prashna": int, "lagna_longitude": float, "houses":
        [chain_1, ..., chain_12]}`` where each ``chain_i`` is the
        :func:`sub_lord_at` result (with sub-sub-lord) for cusp ``i``,
        carrying an extra ``"cusp"`` key (1..12).

    Raises:
        ValueError: if ``prashna_number`` is outside ``[1, 249]``.
    """
    asc_lon = prashna_to_longitude(prashna_number)
    houses = []
    for cusp in range(1, 13):
        cusp_lon = (asc_lon + (cusp - 1) * 30.0) % 360.0
        chain = sub_lord_at(cusp_lon, with_sub_sub=True)
        chain["cusp"] = cusp
        houses.append(chain)
    return {
        "prashna": prashna_number,
        "lagna_longitude": asc_lon,
        "houses": houses,
    }


def ruling_planets(date, pos, ayanamsa=const.AYANAMSA_KRISHNAMURTI):
    """Return the KP Ruling Planets at the moment of a question.

    The Ruling Planets are: the day-of-week lord, the Moon's sign lord
    and star (nakshatra) lord, the Ascendant's sign lord and star lord,
    plus the Moon's and Ascendant's KP sub-lords. (The weekday used is
    the civil-date weekday — the true astrological day runs
    sunrise→sunrise, a documented approximation.)

    Args:
        date: A :class:`~mayaastrolib.datetime.Datetime` — the question
            moment.
        pos: A :class:`~mayaastrolib.geopos.GeoPos` — the question
            location (needed for the Ascendant).
        ayanamsa: The sidereal ayanamsa to use; defaults to the KP
            (Krishnamurti) ayanamsa.

    Returns:
        Dict with keys ``day_lord``, ``moon_sign_lord``,
        ``moon_star_lord``, ``moon_sub_lord``, ``lagna_sign_lord``,
        ``lagna_star_lord``, ``lagna_sub_lord``, plus a ``set`` of all
        the distinct ruling-planet IDs under ``"all"``.
    """
    from mayaastrolib.chart import Chart

    chart = Chart(date, pos, zodiac=const.ZODIAC_SIDEREAL, ayanamsa=ayanamsa)
    moon_lon = chart.getObject(const.MOON).lon % 360.0
    asc_lon = chart.getAngle(const.ASC).lon % 360.0
    moon_chain = sub_lord_at(moon_lon)
    lagna_chain = sub_lord_at(asc_lon)

    pydt = date.to_pydatetime()
    weekday = (pydt.weekday() + 1) % 7  # Python Mon=0..Sun=6 → astro Sun=0..Sat=6
    day_lord = _WEEKDAY_LORDS[weekday]

    rp = {
        "day_lord": day_lord,
        "moon_sign_lord": moon_chain["sign_lord"],
        "moon_star_lord": moon_chain["star_lord"],
        "moon_sub_lord": moon_chain["sub_lord"],
        "lagna_sign_lord": lagna_chain["sign_lord"],
        "lagna_star_lord": lagna_chain["star_lord"],
        "lagna_sub_lord": lagna_chain["sub_lord"],
    }
    rp["all"] = set(rp.values())
    return rp

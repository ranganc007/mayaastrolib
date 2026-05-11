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


def _sub_lord(sidereal_lon):
    """Return the KP sub-lord ID at ``sidereal_lon``."""
    lon = sidereal_lon % 360.0
    nak_idx = int(lon // _SEG)
    pos_in_nak = (lon - nak_idx * _SEG) / _SEG  # fraction 0..1
    cum = 0.0
    seq = _sub_sequence_for_nakshatra(nak_idx)
    for sub_lord in seq:
        cum += VIMSHOTTARI_YEARS[sub_lord] / 120.0
        # Use a small epsilon so a longitude exactly at a sub boundary
        # belongs to the *next* sub (consistent with [start, end) rows).
        if pos_in_nak < cum - _EPS / _SEG:
            return sub_lord
    return seq[-1]


def sub_lord_at(sidereal_lon):
    """Return the full KP chain at ``sidereal_lon``.

    Args:
        sidereal_lon: A sidereal ecliptic longitude in degrees. For
            KP-correct results compute it under the Krishnamurti
            ayanamsa.

    Returns:
        Dict with keys ``longitude`` (normalised), ``sign``,
        ``sign_lord``, ``nakshatra``, ``star_lord``, ``pada``,
        ``sub_lord``.
    """
    lon = sidereal_lon % 360.0
    sign_idx = int(lon // 30.0)
    nak = _nak.of_longitude(lon)
    return {
        "longitude": lon,
        "sign": const.LIST_SIGNS[sign_idx],
        "sign_lord": SIGN_LORDS[sign_idx],
        "nakshatra": nak.name,
        "star_lord": nak.lord,
        "pada": nak.pada,
        "sub_lord": _sub_lord(lon),
    }


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

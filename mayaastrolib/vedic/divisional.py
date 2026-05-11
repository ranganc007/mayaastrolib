"""Divisional charts (Shodashavarga) per BPHS ch. 6-7.

Each varga divides the 30° span of a sign into N equal (or in some cases
unequal) segments and maps each segment to a sign. The mapping is the
"divisional sign" of the planet for that varga.

References:
- BPHS ch. 6 (Shodashavarga definitions)
- BPHS ch. 7 (specific divisional rules and exceptions)
- Phaladeepika ch. 4 (cross-reference for D30 Trimsamsa)

Each function takes a *sidereal* longitude (0..360) and returns the sign
index (0=Aries .. 11=Pisces) the planet falls in for that varga.
Tropical longitudes will produce silently-wrong results — see
:func:`all_vargas` for the chart-level entry point that handles
ayanamsa.
"""

from mayaastrolib import const
from mayaastrolib.vedic import ayanamsa as _ay

# Sign indices, 0..11
ARIES = 0
TAURUS = 1
GEMINI = 2
CANCER = 3
LEO = 4
VIRGO = 5
LIBRA = 6
SCORPIO = 7
SAGITTARIUS = 8
CAPRICORN = 9
AQUARIUS = 10
PISCES = 11

SIGN_NAMES = [
    const.ARIES,
    const.TAURUS,
    const.GEMINI,
    const.CANCER,
    const.LEO,
    const.VIRGO,
    const.LIBRA,
    const.SCORPIO,
    const.SAGITTARIUS,
    const.CAPRICORN,
    const.AQUARIUS,
    const.PISCES,
]


def _sign_index(sid_lon):
    """Return sign index 0..11 for a sidereal longitude."""
    return int((sid_lon % 360.0) // 30.0)


def _deg_in_sign(sid_lon):
    """Return position within sign, 0..30."""
    return (sid_lon % 360.0) - _sign_index(sid_lon) * 30.0


def _segment(deg, n_segments):
    """Return segment index 0..(n_segments-1) for a position within a 30° sign.

    Uses ``int(deg * n / 30)`` rather than ``int(deg // (30/n))`` to avoid
    the float-imprecision bug where ``30/9 = 3.333...3335`` makes
    ``deg=10.0 // 3.333... = 2`` instead of the correct ``3``.
    """
    if deg >= 30.0:
        return n_segments - 1
    return int(deg * n_segments / 30.0)


def rasi(sid_lon):
    """D1 — the natal sidereal sign. Returns 0..11."""
    return _sign_index(sid_lon)


def hora(sid_lon):
    """D2 (Hora) — wealth indicator. BPHS 6.6.

    Odd signs: first 15° → Leo (Sun), last 15° → Cancer (Moon).
    Even signs: first 15° → Cancer (Moon), last 15° → Leo (Sun).

    "Odd" here means the 1-indexed sign number is odd (Aries=1, Gemini=3,
    Leo=5, …); in 0-indexed terms that's sign_index ∈ {0, 2, 4, 6, 8, 10}.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    odd = sign % 2 == 0
    first_half = deg < 15.0
    if odd:
        return LEO if first_half else CANCER
    else:
        return CANCER if first_half else LEO


def drekkana(sid_lon):
    """D3 (Drekkana) — siblings, courage. BPHS 6.7.

    Each sign is divided into 3 parts of 10°. First → same sign;
    second → 5th from sign; third → 9th from sign.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    third = int(deg // 10.0)  # 0, 1, 2
    return (sign + third * 4) % 12


def chaturthamsa(sid_lon):
    """D4 (Chaturthamsa) — fortune, property. BPHS 6.8.

    Each sign divided into 4 parts of 7°30'. Counts start from the sign
    itself, then 4th, 7th, 10th house from it (kendras of natal sign).
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    quarter = int(deg // 7.5)  # 0..3
    return (sign + quarter * 3) % 12


def saptamsa(sid_lon):
    """D7 (Saptamsa) — children. BPHS 6.10.

    Each sign divided into 7 parts of 4°17'8.57". In odd signs, counts
    forward from the sign; in even signs, from the 7th sign.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = _segment(deg, 7)
    odd = sign % 2 == 0
    start = sign if odd else (sign + 6) % 12
    return (start + seg) % 12


def navamsa(sid_lon):
    """D9 (Navamsa) — spouse, dharma. BPHS 6.11-15.

    Each sign divided into 9 parts of 3°20'. The first navamsa of:

    - Movable signs (Aries, Cancer, Libra, Capricorn) → same sign
    - Fixed signs (Taurus, Leo, Scorpio, Aquarius) → 9th sign
    - Dual signs (Gemini, Virgo, Sagittarius, Pisces) → 5th sign

    Subsequent navamsas count forward.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = _segment(deg, 9)
    mod3 = sign % 3
    if mod3 == 0:  # Movable: Aries(0), Cancer(3), Libra(6), Capricorn(9)
        start = sign
    elif mod3 == 1:  # Fixed: Taurus(1), Leo(4), Scorpio(7), Aquarius(10)
        start = (sign + 8) % 12
    else:  # Dual: Gemini(2), Virgo(5), Sagittarius(8), Pisces(11)
        start = (sign + 4) % 12
    return (start + seg) % 12


def dasamsa(sid_lon):
    """D10 (Dasamsa) — career, social status. BPHS 6.16.

    Each sign divided into 10 parts of 3°. In odd signs counts forward
    from the sign; in even signs from the 9th sign.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = _segment(deg, 10)
    odd = sign % 2 == 0
    start = sign if odd else (sign + 8) % 12
    return (start + seg) % 12


def dvadasamsa(sid_lon):
    """D12 (Dvadasamsa) — parents, ancestors. BPHS 6.17.

    Each sign divided into 12 parts of 2°30'. Counts forward from the sign.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = _segment(deg, 12)
    return (sign + seg) % 12


def shodasamsa(sid_lon):
    """D16 (Shodasamsa) — vehicles, comforts. BPHS 6.18.

    Each sign divided into 16 parts of 1°52'30". In movable signs counts
    from Aries; in fixed from Leo; in dual from Sagittarius.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = _segment(deg, 16)
    mod3 = sign % 3
    if mod3 == 0:
        start = ARIES
    elif mod3 == 1:
        start = LEO
    else:
        start = SAGITTARIUS
    return (start + seg) % 12


def vimsamsa(sid_lon):
    """D20 (Vimsamsa) — spiritual practice. BPHS 6.19.

    Each sign divided into 20 parts of 1°30'. Movable: from Aries;
    Fixed: from Sagittarius; Dual: from Leo.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = int(deg // 1.5)  # 0..19
    mod3 = sign % 3
    if mod3 == 0:
        start = ARIES
    elif mod3 == 1:
        start = SAGITTARIUS
    else:
        start = LEO
    return (start + seg) % 12


def chaturvimsamsa(sid_lon):
    """D24 (Chaturvimsamsa) — education, learning. BPHS 6.20.

    Each sign divided into 24 parts of 1°15'. Odd signs from Leo;
    even from Cancer.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = int(deg // 1.25)  # 0..23
    odd = sign % 2 == 0
    start = LEO if odd else CANCER
    return (start + seg) % 12


def bhamsa(sid_lon):
    """D27 (Bhamsa / Saptavimsamsa) — strengths, weaknesses. BPHS 6.21.

    Each sign divided into 27 parts of 1°6'40". Fire signs from Aries;
    Earth from Cancer; Air from Libra; Water from Capricorn.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = _segment(deg, 27)
    mod4 = sign % 4
    starts = [ARIES, CANCER, LIBRA, CAPRICORN]
    return (starts[mod4] + seg) % 12


def trimsamsa(sid_lon):
    """D30 (Trimsamsa) — misfortunes, illness. BPHS 6.29-32.

    Unequal segments by sign parity:

    - Odd signs: 5° Mars, 5° Saturn, 8° Jupiter, 7° Mercury, 5° Venus
      → Aries, Aquarius, Sagittarius, Gemini, Libra
    - Even signs: 5° Venus, 7° Mercury, 8° Jupiter, 5° Saturn, 5° Mars
      → Taurus, Virgo, Pisces, Capricorn, Scorpio
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    odd = sign % 2 == 0
    if odd:
        cuts = [5.0, 10.0, 18.0, 25.0, 30.0]
        signs = [ARIES, AQUARIUS, SAGITTARIUS, GEMINI, LIBRA]
    else:
        cuts = [5.0, 12.0, 20.0, 25.0, 30.0]
        signs = [TAURUS, VIRGO, PISCES, CAPRICORN, SCORPIO]
    for i, c in enumerate(cuts):
        if deg < c:
            return signs[i]
    return signs[-1]  # exact 30° boundary case


def khavedamsa(sid_lon):
    """D40 (Khavedamsa) — maternal lineage. BPHS 6.22.

    Each sign divided into 40 parts of 45'. Odd signs from Aries;
    even from Libra.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = int(deg // 0.75)  # 0..39
    odd = sign % 2 == 0
    start = ARIES if odd else LIBRA
    return (start + seg) % 12


def akshavedamsa(sid_lon):
    """D45 (Akshavedamsa) — paternal lineage. BPHS 6.23.

    Each sign divided into 45 parts of 40'. Movable signs from Aries;
    fixed from Leo; dual from Sagittarius.
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = _segment(deg, 45)
    mod3 = sign % 3
    if mod3 == 0:
        start = ARIES
    elif mod3 == 1:
        start = LEO
    else:
        start = SAGITTARIUS
    return (start + seg) % 12


def shastiamsa(sid_lon):
    """D60 (Shastiamsa) — overall karma, finest division. BPHS 6.24-28.

    Each sign divided into 60 parts of 30'. In odd signs counts forward
    from the sign; in even from the 12th from the sign (i.e. one back).
    """
    sign = _sign_index(sid_lon)
    deg = _deg_in_sign(sid_lon)
    seg = int(deg // 0.5)  # 0..59
    odd = sign % 2 == 0
    start = sign if odd else (sign + 11) % 12
    return (start + seg) % 12


# Names map for `all_vargas`
_VARGA_FUNCTIONS = {
    "D1": rasi,
    "D2": hora,
    "D3": drekkana,
    "D4": chaturthamsa,
    "D7": saptamsa,
    "D9": navamsa,
    "D10": dasamsa,
    "D12": dvadasamsa,
    "D16": shodasamsa,
    "D20": vimsamsa,
    "D24": chaturvimsamsa,
    "D27": bhamsa,
    "D30": trimsamsa,
    "D40": khavedamsa,
    "D45": akshavedamsa,
    "D60": shastiamsa,
}

VARGA_NAMES = list(_VARGA_FUNCTIONS.keys())


def all_vargas(chart, ayanamsa=const.AYANAMSA_LAHIRI):
    """Return ``{varga_name: {planet_id: sign_idx}}`` for the full Shodashavarga.

    Handles both tropical and sidereal charts — if ``chart.zodiac`` is
    tropical, applies the supplied ayanamsa before computing each varga.
    """
    if chart.zodiac == const.ZODIAC_SIDEREAL:
        sid_lons = {obj.id: obj.lon for obj in chart.objects}
    else:
        sid_lons = {
            obj.id: _ay.to_sidereal(obj.lon, chart.date, ayanamsa=ayanamsa) for obj in chart.objects
        }
    result = {}
    for varga_name, fn in _VARGA_FUNCTIONS.items():
        result[varga_name] = {planet_id: fn(lon) for planet_id, lon in sid_lons.items()}
    return result

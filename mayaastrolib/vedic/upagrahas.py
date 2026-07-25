"""Upagrahas — the "sub-planets" or sensitive points of Vedic astrology.

Two computation schools are supported:

- **School B** (Phaladeepika): the 5 Sun-longitude-derived points —
  Dhuma, Vyatipata, Parivesha, Indrachapa (Chapa), Upaketu. Pure
  arithmetic; no location needed.
- **School A** (B.V. Raman): Gulika / Mandi via the weekday-portion
  ascendant method — divide the day (or night) into 8 parts, find the
  Saturn-ruled part, take the sidereal ascendant at its start.

References:
- Phaladeepika ch. 3 (the 5 Sun-derived upagrahas)
- B.V. Raman, *A Manual of Hindu Astrology* (Gulika / Mandi method)
- BPHS ch. 4 (Kala-velas)
"""

from dataclasses import dataclass

from mayaastrolib import const
from mayaastrolib.ephem import ephem as _ephem
from mayaastrolib.ephem import swe as _swe
from mayaastrolib.vedic import ayanamsa as _ay

__all__ = [
    "WEEKDAY_LORDS",
    "DHUMA",
    "VYATIPATA",
    "PARIVESHA",
    "INDRACHAPA",
    "UPAKETU",
    "GULIKA",
    "UpagrahaResult",
    "sun_derived_upagrahas",
    "gulika_longitude",
    "upagrahas",
]

# Weekday lords in weekday order. Index 0 = Sunday, 6 = Saturday.
WEEKDAY_LORDS = [
    const.SUN,
    const.MOON,
    const.MARS,
    const.MERCURY,
    const.JUPITER,
    const.VENUS,
    const.SATURN,
]

# Sun-derived upagraha names.
DHUMA = "Dhuma"
VYATIPATA = "Vyatipata"
PARIVESHA = "Parivesha"
INDRACHAPA = "Indrachapa"
UPAKETU = "Upaketu"
GULIKA = "Gulika"


@dataclass(frozen=True)
class UpagrahaResult:
    """One upagraha at a particular moment.

    Attributes:
        name: The upagraha's name.
        sidereal_longitude: Ecliptic longitude in the sidereal zodiac,
            0..360.
        sign: The sign name the upagraha falls in.
        deg_in_sign: Position within the sign, 0..30.
    """

    name: str
    sidereal_longitude: float
    sign: str
    deg_in_sign: float


def _make_result(name, sidereal_lon):
    lon = sidereal_lon % 360.0
    sign_idx = int(lon // 30.0)
    return UpagrahaResult(
        name=name,
        sidereal_longitude=lon,
        sign=const.LIST_SIGNS[sign_idx],
        deg_in_sign=lon - sign_idx * 30.0,
    )


def sun_derived_upagrahas(sun_sidereal_lon):
    """Return the 5 Sun-derived upagraha longitudes (School B / Phaladeepika).

    Args:
        sun_sidereal_lon: The Sun's sidereal longitude in degrees.

    Returns:
        Dict {name: longitude} for Dhuma, Vyatipata, Parivesha,
        Indrachapa, Upaketu — all normalised to [0, 360).
    """
    s = sun_sidereal_lon % 360.0
    dhuma = (s + 133.0 + 20.0 / 60.0) % 360.0  # Sun + 133°20'
    vyatipata = (360.0 - dhuma) % 360.0
    parivesha = (vyatipata + 180.0) % 360.0
    indrachapa = (360.0 - parivesha) % 360.0
    upaketu = (indrachapa + 16.0 + 40.0 / 60.0) % 360.0  # Chapa + 16°40'
    return {
        DHUMA: dhuma,
        VYATIPATA: vyatipata,
        PARIVESHA: parivesha,
        INDRACHAPA: indrachapa,
        UPAKETU: upaketu,
    }


def _astro_weekday(date):
    """Return the civil-date weekday with Sunday=0..Saturday=6.

    NOTE: the true astrological day runs sunrise→sunrise, so a pre-dawn
    birth technically belongs to the previous weekday. This uses the
    civil date — a documented approximation.
    """
    pydt = date.to_pydatetime()
    return (pydt.weekday() + 1) % 7  # Python: Mon=0..Sun=6 → astro: Sun=0..Sat=6


def gulika_longitude(chart, ayanamsa=const.AYANAMSA_LAHIRI):
    """Return Gulika's (Mandi's) sidereal longitude for ``chart``.

    Uses the weekday-portion method (School A): the day (sunrise→sunset)
    or night (sunset→next sunrise) is split into 8 equal parts, ruled in
    weekday order starting — for a day birth — from the day's lord, or —
    for a night birth — from the lord of the 5th weekday counting the
    day's lord as 1st. Gulika's longitude is the sidereal ascendant at
    the *start* of the Saturn-ruled part.
    """
    date = chart.date
    pos = chart.pos

    next_sunrise = _ephem.nextSunrise(date, pos)
    next_sunset = _ephem.nextSunset(date, pos)
    # If the next sunset comes before the next sunrise, the next event is a
    # sunset → we are currently in daytime. Otherwise it is night.
    is_daytime = next_sunset.jd < next_sunrise.jd

    weekday = _astro_weekday(date)  # 0=Sunday

    if is_daytime:
        span_start_jd = _ephem.lastSunrise(date, pos).jd
        span_end_jd = next_sunset.jd
        first_lord_index = weekday
    else:
        span_start_jd = _ephem.lastSunset(date, pos).jd
        span_end_jd = next_sunrise.jd
        # Night sequence starts at the lord of the 5th weekday (1-indexed),
        # which is the day-lord index + 4 (0-indexed).
        first_lord_index = (weekday + 4) % 7

    span_len = span_end_jd - span_start_jd
    part_len = span_len / 8.0

    # Which of the 8 parts (0..6, since part 7 is unruled) is ruled by Saturn?
    saturn_part = None
    for part in range(7):
        if WEEKDAY_LORDS[(first_lord_index + part) % 7] == const.SATURN:
            saturn_part = part
            break
    # Saturn always appears among the first 7 parts, so saturn_part is set.

    gulika_jd = span_start_jd + saturn_part * part_len
    _hlist, angles = _swe.sweHousesLon(
        gulika_jd,
        pos.lat,
        pos.lon,
        const.HOUSES_DEFAULT,
        zodiac=const.ZODIAC_SIDEREAL,
        ayanamsa=ayanamsa,
    )
    return angles[0] % 360.0  # the sidereal Ascendant


def upagrahas(chart, school="B", ayanamsa=const.AYANAMSA_LAHIRI):
    """Compute the upagrahas for a chart.

    Args:
        chart: A :class:`Chart`. May be tropical or sidereal — the Sun's
            longitude is shifted to sidereal via ``ayanamsa`` when the
            chart is tropical.
        school: ``"B"`` (default) returns the 5 Sun-derived upagrahas;
            ``"A"`` returns those plus Gulika (the weekday-portion
            point, which needs the chart's date and location).
        ayanamsa: One of ``const.LIST_AYANAMSAS``.

    Returns:
        Dict {name: :class:`UpagrahaResult`}.
    """
    if school not in ("A", "B"):
        raise ValueError(f"school must be 'A' or 'B'; got {school!r}")

    sun_obj = chart.getObject(const.SUN)
    if chart.zodiac == const.ZODIAC_SIDEREAL:
        sun_sid = sun_obj.lon
    else:
        sun_sid = _ay.to_sidereal(sun_obj.lon, chart.date, ayanamsa=ayanamsa)

    result = {name: _make_result(name, lon) for name, lon in sun_derived_upagrahas(sun_sid).items()}
    if school == "A":
        result[GULIKA] = _make_result(GULIKA, gulika_longitude(chart, ayanamsa=ayanamsa))
    return result

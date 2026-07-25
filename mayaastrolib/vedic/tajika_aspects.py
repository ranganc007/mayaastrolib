"""Tajika planetary aspects — Ithasala, Isharafa, and Nakta.

Tajika treats only the Ptolemaic aspects (conjunction 0°, sextile 60°,
square 90°, trine 120°, opposition 180°) and judges them by *application*
vs *separation*:

- **Ithasala** (इत्थशाल, "perfect aspect") — two planets are within their
  combined orb of an exact aspect *and the faster planet is applying* to
  the slower (their longitudinal separation from exactness is shrinking).
- **Isharafa** (इशराफ, "separating aspect") — within orb but the faster
  planet has *already passed* exactness and is separating.
- **Nakta** (नक्त, "translation of light") — two planets are NOT within
  orb of each other, but a third (faster-moving) planet is within orb of
  *both* and is positioned between them, carrying the light from one to
  the other.

Orbs are the *deeptamsha* values — half the orb is contributed by each
planet, so the pair-orb is the average of the two deeptamshas. Standard
deeptamshas: Sun 15°, Moon 12°, Mars 8°, Mercury 7°, Jupiter 9°,
Venus 7°, Saturn 9°.

These functions need planetary speeds (`obj.lonspeed`), so they only
work on a real ephemeris chart (a varshapravesh / annual chart), not a
symbolic one — a symbolic chart's planets have `lonspeed is None`.

References:

- Tajika Neelakanthi ch. 4-5 (the 16 Tajika yogas; Ithasala, Isharafa,
  Nakta, Yamaya, Kambula, ...)
- B.V. Raman, *Varshaphala* (orb / deeptamsha tables)
"""

from dataclasses import dataclass

from mayaastrolib import const

__all__ = [
    "DEEPTAMSHA",
    "ASPECT_ANGLES",
    "ITHASALA",
    "ISHARAFA",
    "NAKTA",
    "KAMBOOLA",
    "GAIRI_KAMBOOLA",
    "KHALLASARA",
    "TajikaAspect",
    "tajika_aspects",
    "tajika_yogas",
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

# Deeptamsha (orb) for each planet, in degrees.
DEEPTAMSHA = {
    const.SUN: 15.0,
    const.MOON: 12.0,
    const.MARS: 8.0,
    const.MERCURY: 7.0,
    const.JUPITER: 9.0,
    const.VENUS: 7.0,
    const.SATURN: 9.0,
}

# The Ptolemaic aspect angles Tajika recognises.
ASPECT_ANGLES = (0.0, 60.0, 90.0, 120.0, 180.0)

ITHASALA = "Ithasala"
ISHARAFA = "Isharafa"
NAKTA = "Nakta"

KAMBOOLA = "Kamboola"
GAIRI_KAMBOOLA = "Gairi-Kamboola"
KHALLASARA = "Khallasara"


@dataclass(frozen=True)
class TajikaAspect:
    """A detected Tajika aspect.

    Attributes:
        kind: ``"Ithasala"``, ``"Isharafa"``, or ``"Nakta"``.
        planets: The planet IDs involved. For Ithasala/Isharafa, a
            2-tuple ``(faster, slower)``. For Nakta, a 3-tuple
            ``(translator, planet_a, planet_b)``.
        aspect_angle: The exact-aspect angle (0/60/90/120/180).
        orb: The combined orb used (average of the relevant deeptamshas).
        separation: For Ithasala/Isharafa, the current distance (deg)
            from exactness. For Nakta, ``None``.
    """

    kind: str
    planets: tuple
    aspect_angle: float
    orb: float
    separation: float | None = None


def _norm360(x):
    return x % 360.0


def _angular_sep(a, b):
    """Smallest separation between two longitudes, 0..180."""
    d = abs(_norm360(a) - _norm360(b))
    return min(d, 360.0 - d)


def _closest_aspect(lon_a, lon_b):
    """Return ``(aspect_angle, distance_from_exact)`` for the Ptolemaic
    aspect the two longitudes are nearest to forming."""
    sep = _angular_sep(lon_a, lon_b)
    best_angle = min(ASPECT_ANGLES, key=lambda ang: abs(sep - ang))
    return best_angle, abs(sep - best_angle)


def _pair_orb(p1, p2):
    return (DEEPTAMSHA[p1] + DEEPTAMSHA[p2]) / 2.0


def _has_speeds(chart):
    """True if the chart's planets carry real longitudinal speeds."""
    obj = chart.getObject(const.SUN)
    return getattr(obj, "lonspeed", None) is not None


def _planet_state(chart):
    """Return ``{planet: (lon, lonspeed)}`` for the classical planets."""
    state = {}
    for p in _CLASSICAL_PLANETS:
        obj = chart.getObject(p)
        state[p] = (obj.lon % 360.0, obj.lonspeed)
    return state


def _applying(lon_fast, spd_fast, lon_slow, spd_slow, aspect_angle):
    """True if the faster planet is *applying* to (closing on) the exact
    aspect with the slower planet.

    We look at whether the signed separation-from-exactness is moving
    toward zero over a tiny time step.
    """

    def sep_from_exact(lf, ls):
        s = _angular_sep(lf, ls)
        return s - aspect_angle

    now = sep_from_exact(lon_fast, lon_slow)
    dt = 1.0 / 24.0  # one hour
    later = sep_from_exact(lon_fast + spd_fast * dt, lon_slow + spd_slow * dt)
    return abs(later) < abs(now)


def tajika_aspects(chart):
    """Detect Ithasala, Isharafa, and Nakta in a chart.

    Args:
        chart: A real ephemeris :class:`Chart` (e.g. an annual /
            varshapravesh chart). The planets must carry speeds —
            a symbolic chart raises :class:`ValueError`.

    Returns:
        A list of :class:`TajikaAspect`, possibly empty.
    """
    if not _has_speeds(chart):
        raise ValueError(
            "tajika_aspects requires a real ephemeris chart (planets must "
            "have lonspeed); this chart's planets have no speed."
        )
    state = _planet_state(chart)
    planets = list(_CLASSICAL_PLANETS)
    results = []

    # --- Ithasala / Isharafa: pairwise ---
    in_orb_pairs = []  # remember which pairs are within orb (for Nakta)
    for i in range(len(planets)):
        for j in range(i + 1, len(planets)):
            p1, p2 = planets[i], planets[j]
            lon1, spd1 = state[p1]
            lon2, spd2 = state[p2]
            angle, dist = _closest_aspect(lon1, lon2)
            orb = _pair_orb(p1, p2)
            if dist > orb:
                continue
            in_orb_pairs.append((p1, p2))
            # Faster planet = larger |speed|.
            if abs(spd1) >= abs(spd2):
                fast, lon_f, spd_f, slow, lon_s, spd_s = p1, lon1, spd1, p2, lon2, spd2
            else:
                fast, lon_f, spd_f, slow, lon_s, spd_s = p2, lon2, spd2, p1, lon1, spd1
            if _applying(lon_f, spd_f, lon_s, spd_s, angle):
                results.append(TajikaAspect(ITHASALA, (fast, slow), angle, orb, dist))
            else:
                results.append(TajikaAspect(ISHARAFA, (fast, slow), angle, orb, dist))

    # --- Nakta: a fast planet within orb of two slower planets that are
    #     NOT within orb of each other. ---
    in_orb_set = {frozenset(pair) for pair in in_orb_pairs}
    for translator in planets:
        t_lon, t_spd = state[translator]
        # Candidate "endpoints": planets within orb of the translator,
        # slower than it.
        partners = []
        for p in planets:
            if p == translator:
                continue
            p_lon, p_spd = state[p]
            if abs(p_spd) >= abs(t_spd):
                continue
            _angle, dist = _closest_aspect(t_lon, p_lon)
            if dist <= _pair_orb(translator, p):
                partners.append(p)
        for a_i in range(len(partners)):
            for b_i in range(a_i + 1, len(partners)):
                a, b = partners[a_i], partners[b_i]
                # The two endpoints must NOT already be within orb of
                # each other (else it's a direct Ithasala/Isharafa).
                if frozenset((a, b)) in in_orb_set:
                    continue
                results.append(TajikaAspect(NAKTA, (translator, a, b), 0.0, _pair_orb(a, b), None))
    return results


def tajika_yogas(chart):
    """Detect the Moon-centred and chart-level Tajika yogas that derive
    from the Ithasala/Isharafa analysis.

    Three higher-order yogas are reported, all built on
    :func:`tajika_aspects`:

    - **Kamboola** — the Moon is in an *Ithasala* (applying aspect) with
      another planet. An auspicious yoga: the year's matters fructify.
      (Classically Kamboola is graded full / half / quarter by the Moon's
      angularity and is keyed to the Lord of the Year; this reports the
      core condition — the Moon forming an Ithasala.)
    - **Gairi-Kamboola** — the Moon is in an *Isharafa* (separating
      aspect) and forms no Ithasala. The weakening counterpart of
      Kamboola.
    - **Khallasara** — *no* Ithasala exists anywhere in the chart: the
      promise of the year is "void", lacking a perfected aspect to carry
      it. A chart-level condition.

    Args:
        chart: A real ephemeris :class:`Chart` (planets must carry
            speeds); a symbolic chart raises :class:`ValueError`.

    Returns:
        Dict with keys ``kamboola`` (bool), ``kamboola_aspects`` (the
        Moon Ithasalas), ``gairi_kamboola`` (bool),
        ``gairi_kamboola_aspects`` (the Moon Isharafas), and
        ``khallasara`` (bool).

    Note:
        The names and finer grading of the Tajika yogas vary across
        sources (Tajika Neelakanthi, Raman's *Varshaphala*); the
        conditions encoded here are the commonly reproduced core.
    """
    aspects = tajika_aspects(chart)
    moon_ithasala = [a for a in aspects if a.kind == ITHASALA and const.MOON in a.planets]
    moon_isharafa = [a for a in aspects if a.kind == ISHARAFA and const.MOON in a.planets]
    any_ithasala = any(a.kind == ITHASALA for a in aspects)
    return {
        KAMBOOLA: bool(moon_ithasala),
        "kamboola_aspects": moon_ithasala,
        GAIRI_KAMBOOLA: bool(moon_isharafa) and not moon_ithasala,
        "gairi_kamboola_aspects": moon_isharafa,
        KHALLASARA: not any_ithasala,
    }

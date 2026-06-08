"""Generate golden-test fixtures using Skyfield.

Run manually by maintainers when fixtures need updating. Not invoked
by CI or pytest — fixture data is committed as JSON.

Skyfield (MIT, pure Python, NASA JPL ephemeris) is used as the
reference implementation. mayaastrolib's output is later compared
against this reference in
:mod:`tests.golden.test_planet_positions`.

Usage:
    .venv-task014/bin/python tests/golden/generate_fixtures.py

Output:
    tests/golden/fixtures.json
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from skyfield.api import Loader
from skyfield.framelib import ecliptic_frame

# Skyfield ephemeris cache directory — gitignored. First run downloads
# de440s.bsp (~17 MB); subsequent runs use the cache.
DATA_DIR = Path(__file__).parent / ".skyfield-data"
DATA_DIR.mkdir(exist_ok=True)
load = Loader(str(DATA_DIR))

ts = load.timescale()
eph = load("de440s.bsp")

EARTH = eph["earth"]
PLANETS = {
    "Sun": eph["sun"],
    "Moon": eph["moon"],
    "Mercury": eph["mercury"],
    "Venus": eph["venus"],
    # de440s.bsp only ships barycenters for Mars and the outer planets.
    # Barycenter ≠ planet for the gas giants (offset is real because of
    # massive moons), but the difference projected on the geocentric
    # ecliptic at AU distances is well below an arcminute, comfortably
    # inside the ±2′ tolerance.
    "Mars": eph["mars barycenter"],
    "Jupiter": eph["jupiter barycenter"],
    "Saturn": eph["saturn barycenter"],
    "Uranus": eph["uranus barycenter"],
    "Neptune": eph["neptune barycenter"],
    "Pluto": eph["pluto barycenter"],
}

# Reference charts. UTC times derived by hand from LMT using
# UTC = LMT - longitude_degrees / 15 hours (East positive).
# Verified during Task 014 — see PROJECT-LOG entry.
CHARTS = [
    {
        "name": "Albert Einstein",
        "date_utc": "1879-03-14T10:50:00",
        # 11:30 LMT at Ulm (10.0°E) → 11:30 - 0:40 = 10:50 UTC
        "location": {"lat": 48.4, "lon": 10.0, "elevation_m": 478},
        "rodden_rating": "AA",
        "source": "Astro-Databank",
    },
    {
        "name": "Frida Kahlo",
        "date_utc": "1907-07-06T15:06:40",
        # 08:30 LMT at Coyoacán (-99.167°W = -6:36:40 from UTC)
        # → 08:30 + 6:36:40 = 15:06:40 UTC
        "location": {"lat": 19.333, "lon": -99.167, "elevation_m": 2240},
        "rodden_rating": "AA",
        "source": "Astro-Databank",
    },
    {
        "name": "Roald Amundsen",
        "date_utc": "1872-07-16T02:46:48",
        # 03:30 LMT at Borge (10.8°E = +0:43:12 from UTC)
        # → 03:30 - 0:43:12 = 02:46:48 UTC
        "location": {"lat": 59.383, "lon": 10.8, "elevation_m": 5},
        "rodden_rating": "B",
        "source": "Public biographical record",
    },
    {
        "name": "Carl Jung",
        "date_utc": "1875-07-26T18:54:44",
        # 19:32 LMT at Kesswil (9.3174°E = +0:37:16 from UTC)
        # → 19:32:00 - 0:37:16 = 18:54:44 UTC
        "location": {"lat": 47.5996, "lon": 9.3174, "elevation_m": 400},
        "rodden_rating": "AA",
        "source": "Astro-Databank",
    },
    {
        "name": "Marilyn Monroe",
        "date_utc": "1926-06-01T17:30:00",
        # 09:30 PST at Los Angeles (PST = UTC-8; no US DST in 1926)
        # → 09:30 + 8:00 = 17:30 UTC
        "location": {"lat": 34.0522, "lon": -118.2437, "elevation_m": 89},
        "rodden_rating": "AA",
        "source": "Astro-Databank",
    },
    {
        "name": "Diana Spencer",
        "date_utc": "1961-07-01T18:45:00",
        # 19:45 BST at Sandringham (BST = UTC+1 in summer 1961)
        # → 19:45 - 1:00 = 18:45 UTC
        "location": {"lat": 52.8309, "lon": 0.5125, "elevation_m": 20},
        "rodden_rating": "AA",
        "source": "Astro-Databank",
    },
    {
        "name": "Barack Obama",
        "date_utc": "1961-08-05T05:24:00",
        # 19:24 HST at Honolulu (HST = UTC-10) on 1961-08-04
        # → 19:24 + 10:00 = 05:24 UTC the next day
        "location": {"lat": 21.3069, "lon": -157.8583, "elevation_m": 6},
        "rodden_rating": "AA",
        "source": "Birth certificate (Astro-Databank)",
    },
]


def compute_chart(chart: dict) -> dict[str, float]:
    """Return Skyfield's geocentric apparent ecliptic longitudes.

    Maps each PLANETS key to its ecliptic longitude in degrees [0, 360).

    **Geocentric, not topocentric.** mayaastrolib's Swiss Ephemeris
    backend returns geocentric positions by default; matching that is
    necessary for tolerance comparison. The difference matters only
    for the Moon (parallax up to ~1°); for Mars and outward it's
    sub-arcsecond. Surface location is not used here — it stays in
    the fixture for the self-consistency suite to consume when it
    builds mayaastrolib charts (which need lat/lon for houses).
    """
    iso = chart["date_utc"]
    dt = datetime.fromisoformat(iso).replace(tzinfo=None)
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

    out: dict[str, float] = {}
    for name, body in PLANETS.items():
        astrometric = EARTH.at(t).observe(body)
        # Apparent ecliptic-of-date coordinates (matches Swiss Eph
        # convention: tropical, mean ecliptic of date).
        lat_, lon, _distance = astrometric.apparent().frame_latlon(ecliptic_frame)
        out[name] = float(lon.degrees) % 360.0

    return out


def main() -> None:
    fixtures = []
    for chart in CHARTS:
        positions = compute_chart(chart)
        fixtures.append(
            {
                "name": chart["name"],
                "date_utc": chart["date_utc"],
                "location": chart["location"],
                "rodden_rating": chart["rodden_rating"],
                "source": chart["source"],
                "expected_positions": positions,
                "tolerance_arcmin": 2.0,
                "generated_by": "skyfield (de440s.bsp)",
            }
        )

    out_path = Path(__file__).parent / "fixtures.json"
    with open(out_path, "w") as f:
        json.dump(fixtures, f, indent=2)
    print(f"Wrote {len(fixtures)} fixtures to {out_path}")


if __name__ == "__main__":
    main()

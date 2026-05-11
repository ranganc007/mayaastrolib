# Task 025: Vedic KP — Sub-Lord Table

## Context

Read `CLAUDE.md`, the `vedic/kp.py` section of
`docs/2026-05-11-vedic-extension-spec.md`, and confirm Tasks 017–026
merged. Read `mayaastrolib/vedic/nakshatras.py` (`NAKSHATRA_LORDS`,
`NAKSHATRA_SPAN_DEG`, `of_longitude`) and `mayaastrolib/vedic/dasha.py`
(`VIMSHOTTARI_ORDER`, `VIMSHOTTARI_YEARS`). Confirm `pytest tests/`
passes (~406 after Task 017b).

## Why "249"

The KP zodiac is divided by Star (nakshatra) and Sub. Each of the 27
nakshatras (13°20') is split into 9 "subs" with widths proportional to
the Vimshottari dasha years (Ketu 7, Venus 20, Sun 6, Moon 10, Mars 7,
Rahu 18, Jupiter 16, Saturn 19, Mercury 17 — total 120), the sub
sequence starting from the nakshatra's own lord and cycling through the
Vimshottari order. That's 27 × 9 = **243** Star-Sub segments.

The canonical "**249**" table additionally splits at the 12 sign
boundaries. 6 of those (0°, 60°, 120°, 180°, 240°, 300°) coincide with
existing nakshatra/sub boundaries; the other **6** (30°, 90°, 150°,
210°, 270°, 330°) each fall strictly *inside* a sub-segment and bisect
it — specifically the Rahu-sub of a Sun-ruled nakshatra (for the
30°-type) or the Moon-sub of a Jupiter-ruled nakshatra (for the
90°-type). 243 + 6 = **249** rows. The implementation should produce
exactly 249 segments; assert this at module load.

## Design decisions (already made)

- **Sign rulerships** are the traditional 7-planet ones: Aries→Mars,
  Taurus→Venus, Gemini→Mercury, Cancer→Moon, Leo→Sun, Virgo→Mercury,
  Libra→Venus, Scorpio→Mars, Sagittarius→Jupiter, Capricorn→Saturn,
  Aquarius→Saturn, Pisces→Jupiter. (No Uranus/Neptune/Pluto.)
- **`sub_lord_at(sidereal_lon)`** returns a dict:
  `{longitude, sign, sign_lord, nakshatra, star_lord, pada, sub_lord}`.
  Pure function on a sidereal longitude.
- **`kp_table()`** returns the 249-row list; each row is a dict
  `{start_lon, end_lon, sign, sign_lord, nakshatra, star_lord,
  sub_lord}`. Built once and cached at module level.
- **`kp_sublords(chart, ayanamsa=AYANAMSA_KRISHNAMURTI)`** returns
  `{body_id: <sub_lord_at dict>}` for the 7 classical planets + the
  Ascendant. Defaults to the KP (Krishnamurti) ayanamsa — used only
  when the chart is tropical; if the chart is sidereal its positions
  are used as-is (build it with `ayanamsa=AYANAMSA_KRISHNAMURTI` for
  KP-correct results, and the docstring should say so).
- **Sub-sub-lord (the 4th level)** is out of scope — `sub_lord_at`
  stops at the sub. A follow-up can add it (same proportional split,
  one level deeper).

## Task scope

`mayaastrolib/vedic/kp.py`:

```python
SIGN_LORDS = [...]                       # idx 0=Aries .. 11=Pisces

def _sub_lord(sidereal_lon) -> str        # the sub-lord ID
def sub_lord_at(sidereal_lon) -> dict     # full chain
def kp_table() -> list[dict]              # 249 rows, cached
def kp_sublords(chart, ayanamsa=AYANAMSA_KRISHNAMURTI) -> dict
```

The table is built by collecting the union of (a) the 243 sub-segment
end longitudes, (b) the 12 sign boundaries, deduping within ~1e-6°,
sorting, and tagging each consecutive (wrapping) interval by its
midpoint. Assert `len(kp_table()) == 249` at module load.

## Tests (`tests/test_vedic_kp.py`)

- `len(kp_table()) == 249`.
- Every row's `[start_lon, end_lon)` is non-empty and the rows tile
  [0, 360) with no gaps/overlaps; the per-row span sums to 360°.
- Each row's `sign_lord` matches `SIGN_LORDS[int(start_lon // 30)]`
  (using a point strictly inside the row to avoid boundary ambiguity).
- `sub_lord_at(0.0)` → Ashwini, star_lord Ketu, sub_lord Ketu (the
  first sub of Ashwini is Ketu's, since Ashwini's lord is Ketu and the
  sub sequence starts with the nakshatra's lord), sign Aries,
  sign_lord Mars, pada 1.
- The first sub of Ashwini ends at `7/120 × 13°20' = 0.7778°` →
  `sub_lord_at(0.5)` is still Ketu-sub; `sub_lord_at(0.9)` is the
  next sub (Venus, since Ashwini's sub order is Ketu, Venus, Sun, …).
- The 30° sign boundary bisects a sub: `sub_lord_at(29.9)` and
  `sub_lord_at(30.1)` have the *same* sub_lord (it's one sub split by
  the sign boundary) but *different* sign / sign_lord.
- `sub_lord_at` is consistent with `nakshatras.of_longitude` for the
  star and pada.
- `kp_sublords(chart)` returns chains for the 7 planets + Asc; works on
  a sidereal chart (built with KP ayanamsa) and the equivalent tropical
  chart with `ayanamsa=AYANAMSA_KRISHNAMURTI`.

## Out of scope

- Sub-sub-lord (4th level), KP horary (prashna 1..249), Ruling Planets,
  KP significators / cuspal interlinks — follow-ups.

## Process

Branch `task-025-vedic-kp`. Commits: `feat: add vedic.kp sub-lord
table`, then `docs: update CHANGELOG, PROJECT-LOG, CLAUDE.md for Task
025`. Pre-completion checklist: ruff format/check, mypy (no new errors),
pytest, coverage ≥80%. PROJECT-LOG must record the 243→249 derivation
and that the table-length assert is enforced at import. Push, verify
CI, DO NOT merge.

## Definition of done

- `kp_table()` returns exactly 249 rows that tile [0, 360).
- `sub_lord_at` returns the correct sign/sign_lord/nakshatra/star_lord/
  pada/sub_lord chain; consistent with `nakshatras.of_longitude`.
- `kp_sublords` works on tropical and sidereal charts.
- Tests pass; existing tests unaffected. Docs updated. CI green.

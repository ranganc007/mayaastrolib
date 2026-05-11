# Task 026b: Extended Vedic Yogas

Follow-up to Task 026. Adds Raja, Dhana, Vipareeta Raja, Neecha Bhanga,
and Kemadruma detection to `mayaastrolib/vedic/yogas.py`.

## Design decisions (already made)

- **Whole-Sign houses** throughout — `house_lord(h, asc_sign) =
  SIGN_LORD[(asc_sign + h - 1) % 12]`. New public helpers: `sign_lord`,
  `house_lord`, `houses_ruled_by`.
- **Raja Yoga** — a kendra lord (lord of houses 1/4/7/10) conjunct a
  *distinct* trikona lord (lord of houses 1/5/9), i.e. in the same
  sign. (Mutual aspect and parivartana are deferred.)
- **Dhana Yoga** — two *distinct* wealth-house lords (houses 2/5/9/11)
  conjunct.
- **Vipareeta Raja** — Harsha (6th lord), Sarala (8th lord), Vimala
  (12th lord), each fires when that dusthana lord is itself placed in a
  dusthana (house 6/8/12).
- **Neecha Bhanga** — a debilitated planet whose debilitation is
  cancelled by *either* (a) the dispositor (lord of the debilitation
  sign) being in a kendra from the Ascendant, or (b) the planet that is
  exalted in that sign being in a kendra. (Finer conditions — navamsa
  exaltation, dispositor aspecting — deferred.)
- **Kemadruma** — no graha among {Mars, Mercury, Jupiter, Venus,
  Saturn} in the 2nd or 12th sign from the Moon. (The Sun, nodes are
  not counted; the "no planet conjunct/kendra from Moon" extra clauses
  are deferred.)
- `detect_yogas` now returns the union of the original 8 and these new
  ones. The internal split is `_detect` (original) + `_detect_extended`
  (new), both pure functions over `(planet_signs, asc_sign)`.

## Tests (`tests/test_vedic_yogas_extended.py`)

- The house helpers (`house_lord`, `houses_ruled_by`, `sign_lord`,
  `_EXALTED_IN` inverse).
- Each new yoga: a synthetic `(planet_signs, asc_sign)` that does fire
  it and one that doesn't.
- The Kemadruma "Sun-flanking-the-Moon doesn't block it" case.
- `detect_yogas` on a real chart returns only supported sanskrit names;
  tropical and sidereal charts agree.

## Out of scope

Yoga strength scoring; mutual-aspect/parivartana Raja Yogas; finer
Neecha-Bhanga conditions; Gaja-Kesari cancellation; the dozens of named
lesser yogas (Lakshmi, Saraswati, Gaja, Amala, Adhi, etc.).

# API Stability

This document is the **single source of truth** for what `mayaastrolib`
considers public. From 1.0 onward it is a contract, not a description.

Before 1.0 the public surface was defined implicitly — "whatever the README
happens to mention". That is not something a consumer can rely on and not
something a maintainer can check. Task v1.0-05 made it explicit.

## The rule

A name is **public** if and only if it appears in its module's `__all__`.

Two corollaries:

- A leading underscore (`_ephe_session`, `_getPart_impl`, `mayaastrolib/_compat.py`)
  always means internal. These can change or disappear in any release,
  including a patch.
- **No underscore does not imply public.** A module-level name absent from
  `__all__` is internal-by-convention even if it looks importable. `__all__`
  is the boundary; the underscore is just an extra hint.

`from mayaastrolib.chart import *` therefore imports exactly the supported
surface, and `dir(mayaastrolib)` lists exactly the supported top level.

## The frozen surface

### Top level — `mayaastrolib`

| Name | Kind |
|---|---|
| `__version__`, `PATH_LIB`, `PATH_RES` | metadata |
| `Chart`, `Datetime`, `GeoPos`, `const` | everyday entry points |
| `full_report`, `full_report_json` | high-level facade |

These are resolved **lazily** (PEP 562 `__getattr__`). This is deliberate and
is itself part of the contract: `import mayaastrolib` must not import
swisseph or the ~6 MB of ephemeris data. Code that only needs the version,
the resource paths, or `const` pays nothing for the calculation stack. Do not
convert these to eager imports.

### Core modules

| Module | Public names |
|---|---|
| `chart` | `Chart`, `SCHEMA_VERSION` |
| `object` | `GenericObject`, `Object`, `House`, `FixedStar` |
| `aspects` | `Aspect`, `AspectObject`, `getAspect`, `hasAspect`, `isAspecting`, `aspectType`, `MAX_MINOR_ASP_ORB`, `MAX_EXACT_ORB` |
| `datetime` | `Datetime`, `Date`, `Time`, `dateJDN`, `jdnDate`, `GREGORIAN`, `JULIAN` |
| `geopos` | `GeoPos`, `toFloat`, `toList`, `toString`, `LAT`, `LON`, `SIGN`, `CHAR` |
| `const` | all 200 module-level constants (computed, so it cannot drift) |
| `angle` | the 13 angle helpers (`norm`, `distance`, `closestdistance`, …) |
| `lists` | `GenericList`, `ObjectList`, `HouseList`, `FixedStarList` |
| `utils` | `ascdiff`, `dnarcs`, `isAboveHorizon`, `eqCoords` |
| `props` | `base`, `sign`, `object`, `house`, `aspect`, `fixedStar`, `houseSystem` |
| `report` | `full_report`, `full_report_json` |
| `aio` | `achart`, `afull_report`, `afull_report_json` |

### `mayaastrolib.vedic` — public, tiered

Every `vedic` module declares `__all__` and is public. But the subsystem is
**tiered by fidelity**, because some of it implements a classical technique
exactly and some of it ships a documented approximation. The tier affects
what stability means for the *values*, never for the *signature*:

| Tier | Modules | Guarantee |
|---|---|---|
| **Exact** — determinate arithmetic on a longitude, no interpretive choice | `ayanamsa`, `nakshatras`, `divisional`, `ashtakavarga`, `kp`, `dasha`, `sadesati` | Signatures **and values** are stable. A value change is a bug fix and gets a CHANGELOG entry. |
| **Approximate** — a documented stand-in for a classical formula, or a rule with genuine source variance | `shadbala`, `tajika`, `tajika_bala`, `tajika_aspects`, `upagrahas`, `yogas` | Signatures are stable under the same policy as everything else. **Values may be refined in a minor release** as approximations are replaced with the classical computation, with a CHANGELOG entry. |

Every approximate function says so in its own docstring. Do not pin exact
numeric assertions against a Tier-2 output without reading it — see
`shadbala.py`'s module docstring, `tajika_bala.panchavargiya_bala`,
`tajika.lord_of_year`, and `upagrahas.gulika_longitude`.

### Not public

`mayaastrolib.ephem` (`ephem`, `eph`, `swe`, `tools`), `dignities`,
`predictives`, `protocols`, and `tools` do not declare `__all__` and are
**not** covered by the stability contract. They are reachable and are used
internally, but their shape may change in a minor release. The supported way
to reach that functionality is through `Chart`:

| Instead of | Use |
|---|---|
| `predictives.profections` | `Chart.profected()` |
| `predictives.returns` | `Chart.solarReturn()` |
| `predictives.primarydirections` | `Chart.directions()` |
| `tools.arabicparts` | `Chart.arabicPart()` |
| `tools.planetarytime` | `Chart.planetaryHour()` |
| `ephem.swe` | `Chart(...)` |

`dignities.essential` / `dignities.accidental` and `protocols.*` have no
`Chart` equivalent yet. They are usable, but treat them as provisional and
say so if you depend on them — promoting them is a candidate for 1.1.

## Changing the API after 1.0

`mayaastrolib` follows semantic versioning. For anything in the frozen
surface above:

1. **Patch** (1.0.x) — bug fixes only. No signature changes. A corrected
   calculation is allowed and must appear in the CHANGELOG under `Fixed`.
2. **Minor** (1.x.0) — additions only: new modules, new functions, new
   keyword arguments **with defaults that preserve existing behaviour**.
   Tier-2 `vedic` value refinements land here.
3. **Major** (2.0.0) — the only place a public name may be removed or change
   meaning.

Removal requires all three of:

- a **deprecation window of at least one minor release**, during which the
  old name still works and emits a `DeprecationWarning` naming the version
  that will remove it and the replacement to use;
- a `CHANGELOG.md` entry under **`Removed (BREAKING)`** giving the exact
  replacement — see the 1.0 entry for the format;
- a major version bump.

The 1.0 release itself is the precedent: `getAspectOrSentinel`,
`setTerms`/`setFaces`, `Object.relocate`, `Object.antiscia`/`cantiscia`,
`profections.compute`, `arabicparts.getPart`, `House._OFFSET`, and the whole
`flatlib` compatibility package were each deprecated with a warning naming
1.0, then removed in 1.0, each with its replacement recorded.

## Known wrinkles

Recorded here rather than fixed, because v1.0-05 declares the surface and
does not rename anything in it.

- **camelCase.** Much of the surface is camelCase (`getAspect`, `houseOf`,
  `isDirect`, `arabicPart`) inherited from flatlib, against PEP 8. Renaming
  is tracked in `docs/IDEAS.md` and would be a 2.0 change under the policy
  above.
- **`property_with_method_compat`.** `obj.movement` and `obj.movement()`
  both work. Only property access is type-annotated; the call form is
  deprecated and slated for removal with `_compat.py`. See
  `docs/PROPERTY-MIGRATION.md`.
- **`Aspect.exists()` / `const.NO_ASPECT`** are near-vestigial now that
  `getAspect()` returns `None` and the sentinel constructor is gone. Public,
  but no library code produces a `NO_ASPECT` Aspect.
- **`mayaastrolib.predictives.profections`** is an empty module — its only
  function was removed in 1.0. Deleting it entirely is a candidate for 1.1.

## Enforcement

`tests/test_public_api.py` pins all of this:

- every name in every `__all__` actually exists on its module;
- the top-level surface matches this document exactly;
- `import mayaastrolib` stays swisseph-free;
- the README quick-start runs end to end.

# Ideas (Deferred Work)

This file collects work that surfaced during a task but doesn't belong in the current sprint. Add an entry when you discover something worth doing later. Remove entries when they get scheduled into a real task.

## DST-aware timezone handling for Datetime

**Status:** Deferred. Likely a future task.

Currently `Datetime` takes a fixed UTC offset string (`"+05:30"`). For locations with daylight saving, consumers must know the correct offset for the chart's date.

A future task should add `Datetime.from_zoneinfo("Europe/Dublin", date, time)` using the stdlib `zoneinfo` module. Decisions to make:

- Add a `tzdata` dependency, or rely on the system tzdb?
- Store the IANA name in `Datetime`, or convert to fixed offset at construction?
- Backwards compatibility for the existing offset-string API?

The core cost is the change in mental model: today the library treats UTC offset as just a number. With IANA timezones it would treat timezone as a real first-class concept (with rules for ambiguous/missing local times during DST transitions).

Surfaced during Task 007 (datetime ergonomics), 2026-05-07.

## ISO 8601 string parsing for Datetime

**Status:** Deferred. Add when friction surfaces.

`Datetime.from_iso("2015-03-13T17:00+00:00")` would be useful for JSON-driven webapps and API consumers. Lower priority than `from_pydatetime` because most callers already have a `datetime.datetime`.

Surfaced during Task 007.

## camelCase → snake_case sweep across the public API

**Status:** Deferred. Bundle with the 1.0 cleanup.

The public API still uses camelCase (`getAspect`, `getRole`, `houseOf`,
`isDirect`, `isPlanet`, etc.) inherited from upstream flatlib. PEP 8
prefers snake_case. A sweeping rename is too disruptive to ship as a
patch — it touches every recipe, test, and downstream consumer.

Plan: combine with the property/shim removals already scheduled for 1.0
and the UP031 percent-format sweep. Land all three as a single
"camelCase → snake_case + property cleanup" task so consumers only need
to migrate once.

Surfaced during Task 009 (aspect API improvements), 2026-05-08.

## Aspect direction / orientation as semantic properties

**Status:** Deferred.

`Aspect.direction` is a string (`"Dexter"` / `"Sinister"`) and
`Aspect.condition` is a string (`"Associate"` / `"Dissociate"`). These
could become property-decorated booleans (`aspect.is_dexter`,
`aspect.is_associate`) for ergonomic checks, parallel to
`Object.is_direct()`. Low priority; consumers can equality-check the
string today.

Surfaced during Task 009.

## Predictives as Chart methods (audit Item 17)

**Status:** Partially addressed in Task 010.

Task 010 added `Chart.profected()` as a method-style entry point.
Other predictives — solar / lunar returns, primary directions, transits
— remain as top-level functions in their own modules
(`predictives.returns`, `predictives.primarydirections`).

Future work should consider adding:
- `Chart.solarReturn(year)` — already exists but its semantic
  question (calendar year vs. Nth birthday) is open (see audit
  Item 16).
- `Chart.lunarReturn(date)` — for lunar returns. Not yet
  implemented in `predictives.returns` either.
- `Chart.directions(target_date)` — primary directions wrapper.

These each have their own design questions — solar return semantics,
whether they're symbolic charts (directions yes, returns no),
how they compose with `is_symbolic` / `symbolic_kind`. Defer until
Phase 2 design conversation.

Surfaced during Task 010 (symbolic charts and relocate semantics),
2026-05-08.

## DST / IANA timezones for symbolic-chart construction

**Status:** Deferred. Likely Phase 2.

`Chart.profected(target_date=...)` accepts a `Datetime` with a fixed
UTC offset. For long timespans crossing DST boundaries, computing the
"target_date 30 years from natal in the same wall-clock timezone"
requires IANA tz support, which Task 007 documented as deferred.

Surfaced during Task 010.

## Configurable cusp tolerance (audit Item 15)

**Status:** Investigated in Task 012, deferred for design.
**See:** `docs/AUDIT-INVESTIGATIONS.md` Item 15 for findings.

The 5° cusp tolerance hard-coded as `House._CUSP_TOLERANCE_DEG`
(formerly `_OFFSET = -5.0`) is a defensible default but some
authors prefer 3° or 7°, and some apply the rule only to angular
cusps rather than to all 12. Making it configurable is reasonable
future work, but the design surface is open: per-`Chart`,
per-`House`, per-house-system? Not enough user demand right now to
pick. Defer until Phase 2 or until a consumer asks.

Surfaced during Task 012, 2026-05-08.

## solarReturnByAge companion (audit Item 16)

**Status:** Investigated in Task 012, deferred — low priority.
**See:** `docs/AUDIT-INVESTIGATIONS.md` Item 16 for findings.

`Chart.solarReturn(year)` works correctly for every realistic case
(verified by concrete tests). A `solarReturnByAge(years)` companion
that disambiguates by counting forward from the natal date would
be a small ergonomic addition but isn't required — the existing
API already gives the right answer when consumers map age to year
themselves.

Surfaced during Task 012, 2026-05-08.

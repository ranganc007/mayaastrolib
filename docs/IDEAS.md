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

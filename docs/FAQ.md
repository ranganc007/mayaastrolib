# mayaastrolib — Frequently Asked Questions

A plain-English Q&A about what this library is, what it does, and what it does not do. For a guided walkthrough of the internals, see [HOW-IT-WORKS.md](HOW-IT-WORKS.md).

## The basics

### What is mayaastrolib?

A Python library that takes a moment in time and a place on Earth and tells you where every planet was in the sky at that moment, which zodiac sign each was in, which "house" each was in relative to that location, and which planets were in meaningful angular relationships with each other. It is the computational engine behind the kind of birth chart an astrologer would draw on paper.

### Do I have to believe in astrology to use this library?

No. The library is a **computational** tool. It tells you where the planets actually were — that part is astronomy, and it's accurate. What you do with that information (cast a horoscope, build a meditation app, study historical correlations, render a pretty diagram, train an LLM) is your concern. The library does not produce interpretations and explicitly will not tell you what your Saturn return "means."

### Is this a website? An app?

It is a Python library — a piece of code other programs import. There is no UI. If you want a website, you write one (the [mayaastro-demo](../../mayaastro-demo) repo is a small Flask example that consumes this library). If you want an app, you build one. mayaastrolib gives you the numbers; presentation is up to you.

### What does it actually compute, in one sentence?

Given a UTC moment and a latitude/longitude, it returns a `Chart` object containing the positions of celestial bodies (Sun through Pluto, plus the lunar nodes, Chiron, and a few traditional points), the boundaries of the twelve astrological houses for that location, the angular relationships between bodies, and a basket of derived qualities (dignities, retrogradation, day/night designation, lunar phase, etc.).

### What inputs do I need?

Three things:

1. **Date and time** in `YYYY/MM/DD HH:MM` form, with the UTC offset (e.g. `+05:30`, `-08:00`).
2. **Location** as latitude/longitude in the library's text form (e.g. `13n05` = 13°5′ North, `80e16` = 80°16′ East).
3. **House system** — optional, defaults to Alcabitus. Other choices include Placidus, Equal, Whole Sign, Koch, Regiomontanus, Porphyrius, Campanus, Meridian, Morinus, etc. (See `const.HOUSES_*`.)

### Will it tell me my future?

No. It will tell you what the sky looked like at any past, present, or future moment to high precision. Whether that has predictive value is a question outside the library's scope.

## Concepts (for the curious layperson)

### What is a "chart"?

A snapshot of the sky as seen from a specific point on Earth at a specific moment, with all the moving parts labelled. Think of it as a freeze-frame map of where the Sun, Moon, and planets were against the background of the zodiac at the instant you were born — or at any other instant you ask about.

### What are "houses"?

Twelve slices of the sky-as-seen-from-your-location, oriented around the horizon and the meridian. Where the planets are absolutely (which constellation they're in) is one thing — what part of *your local sky* they're in is another. Houses encode the second.

A planet rising in the east at the moment of computation is "in the first house"; one directly overhead is "in the tenth"; one setting in the west is "in the seventh"; one straight below your feet on the other side of Earth is "in the fourth." There are several mathematical conventions for dividing up the rest (see "house system" above).

### What are "aspects"?

Angular distances between two planets that astrologers consider meaningful. The library reports the five "major" aspects:

| Aspect | Angle | Plain English |
|---|---|---|
| Conjunction | 0° | They're in the same place |
| Sextile | 60° | They're a sixth of the sky apart |
| Square | 90° | They're a quarter of the sky apart |
| Trine | 120° | They're a third of the sky apart |
| Opposition | 180° | They're directly across from each other |

### What are "dignities"?

A scoring system from traditional Western astrology that quantifies how "comfortable" or "well-placed" each planet is in its current sign. The library ships the standard tables (rulership, exaltation, triplicity, terms, faces) and lets you compute scores like "Mars in Aries scores +5 because Aries is its rulership."

### What is "Vedic" vs "Western"?

Two astrological traditions, distinguished mainly by which zodiac they use:

- **Western (tropical)** — zodiac is anchored to the seasons (the Sun enters Aries at the spring equinox).
- **Vedic (sidereal)** — zodiac is anchored to the actual constellation positions in the sky, which drift relative to the seasons by ~50 arcseconds per year.

mayaastrolib supports both. The fork's stated goal (see [FORK-RATIONALE.md](FORK-RATIONALE.md)) is to unify the two coherently in one library, which is why it's not just the upstream `flatlib`.

## Practical questions

### Is the math correct?

Yes, to the precision of [Swiss Ephemeris](https://www.astro.com/swisseph/), which is the gold-standard astronomical engine used by professional astronomy software. mayaastrolib does not compute orbits itself — it asks `pyswisseph` (a binding to the C library) for planet positions and then does the astrological geometry on top.

### How accurate is it?

For dates between roughly 13201 BCE and 17191 CE, planet positions are accurate to better than 0.01 arcsecond — far finer than astrological convention requires. House cusps and angles inherit the precision of the Earth-orientation model used; for any reasonable era, the error is below 1 arcsecond.

### How fast is it?

Building one `Chart` runs in single-digit milliseconds on a modern laptop, dominated by the Swiss Ephemeris call. Rendering a single chart in a web request is essentially free. Bulk computations (many thousands of charts) are also feasible — see the thread-safety note below.

### Can I use it from a web server / async code / multiple threads?

Yes. As of `[Unreleased]`, dignity calculations are thread-safe when you pass `terms_variant=` and `faces_variant=` as keyword arguments instead of relying on the legacy module-level mutable globals. See [PROPERTY-MIGRATION.md](PROPERTY-MIGRATION.md) for related API changes. There is no I/O in the hot path beyond the one-time loading of ephemeris files at module import.

### What about timezones with daylight saving time?

mayaastrolib's `Datetime` takes a fixed UTC offset, not an IANA zone like `Europe/Dublin`. If your input is "March 13, 2015, 5pm Europe/Dublin," you must resolve that to either `+00:00` (UTC, winter) or `+01:00` (BST, summer) yourself before constructing the `Datetime`. See `docs/IDEAS.md` for the deferred plan to add IANA zone support.

### Does it work for events before the year 1 CE?

Yes — Swiss Ephemeris covers ~13,000 BCE forward. Note that calendar conventions changed (Julian vs Gregorian) and the library uses proleptic Gregorian dates throughout, which is correct for astronomy but may need conversion if your historical source uses Julian dates.

### Can I use this commercially?

mayaastrolib itself is MIT-licensed and free for commercial use. **However**, it depends on `pyswisseph`, which links to Swiss Ephemeris — that is dual-licensed under either GPL or the Swiss Ephemeris Professional License. Commercial users must comply with one of those for the ephemeris dependency. mayaastrolib does not change this constraint; it is inherited from upstream `flatlib`.

### How is this different from the original flatlib?

`flatlib` is the upstream by João Ventura, MIT-licensed, no longer actively maintained as of mid-2020. mayaastrolib is a fork that:

1. Modernises packaging (Python 3.10+, `pyproject.toml`, ruff/mypy in CI)
2. Unifies Western (tropical) and Vedic (sidereal) astrology in one coherent API
3. Fixes pyswisseph 2.x compatibility (eclipse functions had a silently broken kwarg)
4. Adds property-style ergonomics (e.g. `obj.house` instead of an O(12) probe)
5. Ships type hints throughout

A `flatlib` compatibility shim is included; existing code that imports `flatlib` continues to work with a `DeprecationWarning`.

### Where does the name come from?

Personal. "Maya" carries a meaning to the maintainer; "astrolib" describes what it does. The package was renamed from `flatlib` in version 0.3.0.

## Things this library does NOT do

- **It does not interpret charts.** No "Saturn in your seventh house means…" text. That is the consumer's responsibility — including any app that wants to ship interpretations.
- **It does not do election or horary work for you.** It computes what you need to *do* election or horary; the questions and rules are yours.
- **It does not draw chart wheels.** No SVG/PNG rendering. Build that on top, or pipe the data to a charting library.
- **It does not handle natural-language times** like "next full moon" or "the moment of my birth." You must convert to UTC offset yourself.
- **It does not implement astrology systems we have not coded.** Mayan astrology, Chinese astrology, Hellenistic-only ruling, evolutionary astrology: out of scope at present. Issues and PRs welcome.

## Where to go next

- **A working example** — see [`mayaastro-demo`](../../mayaastro-demo), a small Flask app that consumes this library to render birth charts and live transits.
- **The technical walkthrough** — [HOW-IT-WORKS.md](HOW-IT-WORKS.md) walks the calculation pipeline from time-and-place inputs to a fully-populated `Chart` object.
- **What a chart actually means** — [BIRTH-CHART-PRIMER.md](BIRTH-CHART-PRIMER.md) covers how a birth chart is calculated (six stages), what each of the twelve houses traditionally signifies, and how each planet is conventionally read in each house. This is *educational reference content*; the library still does not produce interpretations.
- **Why this fork exists** — [FORK-RATIONALE.md](FORK-RATIONALE.md).
- **Migrating from flatlib** — see the README's "Migrating from flatlib" section.
- **The original docs** — [http://flatlib.readthedocs.org/](http://flatlib.readthedocs.org/) is largely still applicable; substitute `flatlib` with `mayaastrolib` in import paths.

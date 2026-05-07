# Fork Rationale

## What this is

`mayaastrolib` is a fork of [flatangle/flatlib](https://github.com/flatangle/flatlib),
originally created by João Ventura. The original is MIT licensed and that
license is preserved here, with the original copyright intact and an
additional copyright line for fork modifications.

## Why we forked

The upstream `flatlib` repository, while functional, has shown signs of
inactive maintenance:

- Open issues from 2020 with no maintainer response
- Multiple parallel forks (`flatlib_sidereal`, `flatlib_vedic`,
  `gognjen/flatlib`, `skunal-maker/flatlib_vedic`) addressing real gaps,
  none merged back
- No releases addressing Python 3.10+ deprecations
- No type hints, no modern tooling, `setup.py`-era packaging

Rather than wait indefinitely for upstream merges, this fork takes the
codebase forward independently.

## What we're doing differently

1. **Modernisation.** Python 3.10+, full type hints, pyproject.toml,
   ruff/mypy in CI, pytest with coverage gates.

2. **Unified Vedic + Western.** First-class support for both tropical
   (Western) and sidereal (Vedic) calculations with a coherent API,
   consolidating what is currently scattered across multiple unmaintained
   forks.

3. **Modern application fit.** Clean async-friendly APIs, typed return
   structures suitable for serialisation to JSON, designed for use from
   web backends and AI tool calls.

## What we're not doing

- Reimplementing Swiss Ephemeris (we depend on `pyswisseph`)
- Providing astrological interpretations (that's the consumer's concern)
- Adding a GUI

## Relationship to upstream

The `upstream` git remote points to `flatangle/flatlib` and is read-only.
We will cherry-pick bug fixes from upstream if they appear. If upstream
becomes actively maintained again, we will evaluate contributing
non-fork-specific improvements back.

## Licensing

MIT, same as upstream. Original copyright (João Ventura, 2014-) is
preserved. Fork modifications copyright (Rangan C., 2026-) added.

Note that `mayaastrolib` depends on Swiss Ephemeris (via `pyswisseph`),
which is dual-licensed GPL / Swiss Ephemeris Professional License. Users
deploying this library in commercial contexts must comply with one of
those licenses for the ephemeris dependency. This is unchanged from
upstream flatlib.

## Acknowledgements

Deep thanks to João Ventura for creating flatlib and releasing it under
MIT. Without that foundation this work would not be possible. Thanks
also to the maintainers of the various sidereal/Vedic flatlib forks
whose work informs the unification effort here.

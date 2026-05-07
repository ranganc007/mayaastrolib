# CLAUDE.md — maya-astro-lib

This file is the standing context for all Claude Code sessions in this
repository. Read it fully before making any change.

## Project identity

`mayaastrolib` is a Python library for astrological chart calculation,
forked from `flatangle/flatlib` (MIT, abandoned in practice as of 2024).

This fork exists to:
1. Modernise the codebase to current Python (3.10+) with type hints and
   modern packaging.
2. Unify Western (tropical) and Vedic (sidereal) astrology in a single
   library with a coherent API, consolidating the work of the various
   half-finished sidereal forks of flatlib.
3. Provide a clean, typed, async-friendly calculation engine suitable for
   use from web apps (Next.js, FastAPI) and AI tooling (Claude tool calls,
   MCP servers).

This fork does NOT exist to:
- Be a desktop chart-drawing application
- Provide AI-generated interpretations (that belongs in the consuming app)
- Compete with flatlib upstream — if upstream revives, we may contribute back

## Architectural constraints

- Python 3.10 minimum, 3.12 target. No Python 2 compatibility code.
- Type hints required on all new code. Existing code gets typed
  incrementally per the contribution plan.
- Public API stability: anything documented in README is considered public.
  Breaking changes require a major version bump and a CHANGELOG entry.
- Internal modules (anything starting with `_`) can change freely.
- Swiss Ephemeris is the calculation backend. Do not introduce alternative
  ephemeris libraries without explicit discussion.
- No network calls in the core library. Pure calculation only.

## Code style

- Formatter: `ruff format` (line length 100)
- Linter: `ruff check` with the rules in pyproject.toml — must pass
- Type checker: `mypy` — warnings tolerated, errors not
- Naming: PEP 8. Astrological terms keep their conventional capitalisation
  (e.g. `Sun`, `Moon`, `Ascendant`) when used as identifiers for objects,
  but lowercase in function names (`get_sun()`, not `get_Sun()`).
- Imports: stdlib, third-party, local — separated by blank lines
- Docstrings: Google style, required on all public functions and classes

## Testing requirements

Two layers, both mandatory:

1. **Structural tests** (`tests/unit/`) — verify code contracts.
   Every new function gets unit tests. Bug fixes get regression tests.

2. **Functional tests** (`tests/golden/`) — verify astronomical correctness.
   Reference charts with known positions sourced from Astro-Databank or
   astro.com. Tolerance: ±2 arc-minutes for planets, ±5 arc-minutes for
   house cusps. These tests survive any refactor.

Coverage target: 80% minimum, 90% goal. Enforced in CI.

## Pre-completion checklist

Before declaring any task complete, run in this order and confirm all pass:

1. `ruff format --check .`
2. `ruff check .`
3. `mypy mayaastrolib/`
4. `pytest -x` (stop on first failure)
5. `pytest --cov=mayaastrolib --cov-fail-under=80`
6. Update `docs/PROJECT-LOG.md` with: date, task ID, what was done,
   what was tried and discarded, surprises, follow-ups needed
7. Update `CHANGELOG.md` if the change is user-visible

If any step fails, fix before declaring done. Do NOT modify tests to make
them pass — modify the code. The only exception is when a test is
genuinely wrong, in which case explain in PROJECT-LOG.md and CHANGELOG.md.

## Working agreements with Claude Code

- One task per session. Don't combine tasks unless the spec says so.
- Read `docs/CONTRIBUTION-PLAN.md` for the current task. Don't pick
  arbitrary work.
- If a task is ambiguous, stop and ask in PROJECT-LOG.md rather than guess.
- Never push to `main`. All work happens on feature branches.
- Never push to the `upstream` remote. It is read-only.
- Commit messages: imperative mood, ~50 char subject, body explaining why.
  Reference task IDs from the contribution plan.

## Files that are sacred

These should not be modified without explicit instruction:
- `LICENSE` — preserves original copyright chain
- `docs/FORK-RATIONALE.md` — explains why this fork exists
- This file (`CLAUDE.md`)

## Goal anchor

When in doubt, the question to ask is: "does this serve the three goals
listed under Project Identity?" If not, it goes in `docs/IDEAS.md` for
later consideration, not into the current sprint.

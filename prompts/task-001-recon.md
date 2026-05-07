# Task 001: Recon and Baseline

## Context

You are working in the `maya-astro-lib` repository, a fork of
`flatangle/flatlib`. Read `CLAUDE.md` and `docs/FORK-RATIONALE.md`
before starting. Read `docs/CONTRIBUTION-PLAN.md` for full task scope.

## Your job for this session

Produce `docs/RECON.md` — a comprehensive baseline analysis of the
inherited codebase. NO code changes in this session. Pure analysis.

## Required sections in RECON.md

### 1. Module inventory

For each `.py` file in `flatlib/` (the source directory, not yet
renamed), document:
- Path
- Purpose (one sentence)
- Public API (classes and functions not prefixed with `_`)
- Key dependencies (internal imports, external imports)
- Line count
- Last commit date and message (use `git log -1 --format='%ai %s' <file>`)

Present as a table.

### 2. Test suite baseline

Run `pytest -v` and capture results.
- Total tests
- Passing
- Failing (list with file:test name and brief failure reason)
- Errors (list with file:test name and brief error reason)
- Skipped
- Coverage: run `pytest --cov=flatlib --cov-report=term-missing` and
  report overall percentage and per-module breakdown

### 3. Lint baseline

Run `ruff check .` and report:
- Total violations
- Top 10 violation codes by frequency
- Files with the most violations (top 5)

Run `ruff format --check .` and report how many files would be
reformatted.

### 4. Type baseline

Run `mypy flatlib/ --ignore-missing-imports` and report:
- Total errors
- Top 5 error categories

### 5. Python compatibility

Search the codebase for patterns that indicate version-specific code:
- `from __future__ import` statements
- `sys.version_info` checks
- Use of `typing.Dict`, `typing.List`, etc. (deprecated in 3.9+)
- Use of `Optional[X]` rather than `X | None` (style, not breaking)
- Any `except` without exception type
- `print` statements without parens (would be Python 2)
- `unicode`, `basestring`, `xrange` (Python 2)

### 6. Internal module dependency graph

For each internal module, list which other internal modules it imports.
Present as a Mermaid diagram in the markdown.

### 7. Recipes review

For each file in `recipes/`, document what it demonstrates and whether
it still runs on current Python. Don't fix breakage — just note it.

### 8. Surprises and concerns

A free-form section. Anything you noticed that doesn't fit elsewhere:
- Code that looks suspicious
- Comments hinting at known bugs
- Design decisions that look questionable in 2026
- Missing things you'd expect to find (e.g. no LICENSE header on files)

### 9. Recommended task ordering for Phase 1

Given what you found, recommend an ordering for tasks 002-005 (which
are in CONTRIBUTION-PLAN.md). Specifically:
- Are there any blockers between tasks?
- Is the planned order still sensible given findings?
- Any tasks that should be split or merged?
- Any new tasks to add?

## Process

1. Start by reading every file in `flatlib/` — understand before
   analysing.
2. Work in the `development` branch (already created).
3. Do not make any code changes. The only file you create is
   `docs/RECON.md`.
4. Append a session summary to `docs/PROJECT-LOG.md` covering:
   what you did, how long it took, what surprised you, what you'd
   want clarified before Task 002.
5. Run the pre-completion checklist from CLAUDE.md (skipping the
   coverage gate, which doesn't apply to a recon task).
6. Commit on a branch named `task-001-recon` with message
   `docs: add baseline recon (task 001)`.

## What "done" looks like

In the morning, when I review, I should be able to read RECON.md and
have a complete mental model of: what code exists, what state it's in,
what's working, what's broken, and what to tackle first. If I have to
go look at the code to answer a basic question about state, the recon
isn't done.

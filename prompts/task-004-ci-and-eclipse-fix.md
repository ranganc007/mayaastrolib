# Task 004: CI and Eclipse Bug Fix

## Context

You are working in the `mayaastrolib` repository. Before doing anything:

1. Read `CLAUDE.md` in full.
2. Read `docs/RECON.md` — specifically §8 ¶1 (the eclipse bug) and §9 (Task 004 recommendations).
3. Read `docs/PROJECT-LOG.md` for entries from Tasks 002, 002b, and 003.
4. Confirm Task 003 has been merged to `development`:

   ```
   git log --oneline development -5
   ```

   You should see at the top:
   - `style: hand-fix remaining ruff violations` (or similar from Task 003)
   - The earlier `style:` and `chore:` commits from Task 003
   - Earlier `chore:` and `build:` commits from Task 002b and Task 002

   If the Task 003 `style:` commits are not present, STOP. Append a note to PROJECT-LOG.md and exit.

## Task scope

This task does three things:

1. Set up GitHub Actions CI to run tests on Python 3.10, 3.11, and 3.12
2. Fix the latent eclipse bug discovered by the recon (§8 ¶1)
3. Add a regression test for the eclipse bug

In scope:

### 1. Create GitHub Actions workflow

Create `.github/workflows/test.yml` (the directory may not exist — create it):

```yaml
name: Tests

on:
  push:
    branches: [development, master]
  pull_request:
    branches: [development]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip

      - name: Install package and dev dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e ".[dev]"

      - name: Lint with ruff
        run: |
          ruff format --check .
          ruff check .

      - name: Run tests
        run: pytest tests/ -v

      - name: Run tests with coverage
        run: pytest tests/ --cov=flatlib --cov-report=term-missing
```

Note: the coverage source is `flatlib` not `mayaastrolib` because the directory rename hasn't happened yet (Task 005).

### 2. Fix the eclipse bug

Per recon §8 ¶1, `flatlib/ephem/swe.py` has two function calls using the wrong keyword argument. In pyswisseph 2.x the keyword is `backwards`, not `backward`. The functions affected:

- `solarEclipseGlobal`
- `lunarEclipseGlobal`

Find both calls and change `backward=...` to `backwards=...`. The swisseph functions involved are likely `swe.sol_eclipse_when_glob()` and `swe.lun_eclipse_when()` — verify by reading the file.

This is a literal find-and-replace of one keyword argument name. No other logic should change.

### 3. Add regression test for eclipses

Create `tests/test_eclipses.py` with at least these tests:

```python
"""Regression tests for eclipse calculations.

Catches the pyswisseph keyword argument bug found during fork recon
(see RECON.md §8 ¶1 and KNOWN-BUGS.md). Once the bug is fixed in
flatlib/ephem/swe.py, these tests pin the behaviour so any future
regression will fail loudly in CI.
"""

import unittest

from flatlib.datetime import Datetime
from flatlib.ephem import ephem


class EclipseTests(unittest.TestCase):
    """Smoke tests — verify eclipse functions return without crashing."""

    def setUp(self):
        # Reference date: 2020-01-01 12:00 UTC. Arbitrary but fixed.
        self.date = Datetime("2020/01/01", "12:00", "+00:00")

    def test_next_solar_eclipse_does_not_crash(self):
        """nextSolarEclipse must not raise TypeError on keyword args."""
        result = ephem.nextSolarEclipse(self.date)
        self.assertIsNotNone(result)

    def test_prev_solar_eclipse_does_not_crash(self):
        """prevSolarEclipse must not raise TypeError on keyword args."""
        result = ephem.prevSolarEclipse(self.date)
        self.assertIsNotNone(result)

    def test_next_lunar_eclipse_does_not_crash(self):
        """nextLunarEclipse must not raise TypeError on keyword args."""
        result = ephem.nextLunarEclipse(self.date)
        self.assertIsNotNone(result)

    def test_prev_lunar_eclipse_does_not_crash(self):
        """prevLunarEclipse must not raise TypeError on keyword args."""
        result = ephem.prevLunarEclipse(self.date)
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
```

Verify the test file matches the project's existing test style (`tests/test_angles.py` and `tests/test_chart.py` use `unittest.TestCase`). Adjust if those files use a different pattern.

### 4. Verify the fix and tests work

Run locally first before pushing:

```
python3 -m venv .venv-task004
.venv-task004/bin/pip install -e ".[dev]"
.venv-task004/bin/pytest tests/ -v
```

Should show 9 tests passing (5 original + 4 eclipse tests). Capture output.

Then specifically run the eclipse recipe to confirm the user-visible bug is gone:

```
.venv-task004/bin/python recipes/eclipses.py
```

Should run to completion without TypeError. Capture output.

### 5. Create KNOWN-BUGS.md

New file at repo root or in `docs/`. Document the eclipse bug and its resolution:

```markdown
# Known Bugs and Fixes

## Resolved

### Eclipse functions used wrong keyword argument

**Discovered:** Task 001 recon (see RECON.md §8 ¶1)
**Fixed:** Task 004 (`fix:` commit, this task)
**Affected:** `flatlib/ephem/swe.py` solarEclipseGlobal and lunarEclipseGlobal

`flatlib/ephem/swe.py` called pyswisseph eclipse functions with `backward=...`. In pyswisseph 2.x the keyword is `backwards`. Same root cause as the upstream rise_trans patch (commit 856d26b on master) but for eclipse functions, which were missed at the time.

Symptoms before fix: any call to `nextSolarEclipse`, `prevSolarEclipse`, `nextLunarEclipse`, or `prevLunarEclipse` raised `TypeError: ... got an unexpected keyword argument 'backward'`. The `recipes/eclipses.py` example was broken.

Regression test: `tests/test_eclipses.py`.

## Open

(none currently)
```

### 6. Verify CI is green

Push the branch and watch the GitHub Actions run. The workflow should complete green across all three Python versions.

If the workflow fails, debug. Common failure modes:
- Python 3.10 not finding a feature: indicates accidentally using newer syntax
- pyswisseph install failing: may need a different version constraint
- ruff failing in CI but passing locally: indicates `ruff` version mismatch — pin it

Iterate until CI is green. Each iteration is a new commit on the branch.

## Out of scope

- Smoke tests for other untested modules — that's Task 004a
- Renaming the source directory — that's Task 005
- Adding type hints — Phase 1
- Coverage gating in CI — too few tests to be meaningful yet

## Process

1. Create branch:

   ```
   git checkout development
   git pull origin development
   git checkout -b task-004-ci-and-eclipse-fix
   ```

2. Suggested commits, in order:
   - `ci: add GitHub Actions workflow for Python 3.10/3.11/3.12`
   - `fix: correct pyswisseph eclipse keyword (backward → backwards)`
   - `test: add regression tests for eclipse functions`
   - `docs: add KNOWN-BUGS.md documenting eclipse fix`
   - Plus any iteration commits to get CI green (squash-merge optional)

3. Update `CHANGELOG.md` `[Unreleased]` section. Add `### Fixed` subsection mentioning the eclipse fix. Add `### Added` subsection mentioning CI workflow and regression tests.

4. Pre-completion checklist:
   - `ruff format --check .` passes
   - `ruff check .` passes
   - `mypy flatlib/` — same warnings as before, no new ones
   - `pytest -x` passes (now 9/9)
   - Coverage will be slightly higher; capture the new percentage in the log

5. Append PROJECT-LOG.md entry covering all six steps, with the verification command outputs and the URL of the GitHub Actions workflow run.

6. Push:

   ```
   git push -u origin task-004-ci-and-eclipse-fix
   ```

7. Watch CI run. Iterate until green. Once green, DO NOT merge. Leave for human review.

## Definition of done

- `.github/workflows/test.yml` exists and is valid
- CI runs green across Python 3.10, 3.11, 3.12 — verified by a green check on the GitHub PR view
- `flatlib/ephem/swe.py` eclipse calls use the correct keyword
- `tests/test_eclipses.py` exists with 4+ tests, all passing
- `recipes/eclipses.py` runs without error
- `KNOWN-BUGS.md` documents the fix
- All 9 tests pass locally
- Branch pushed
- PROJECT-LOG.md updated
- CHANGELOG.md updated

## If something goes wrong

If the eclipse fix doesn't work — the keyword change isn't enough, or pyswisseph 2.10.3.2 has a different API entirely:

1. Read the pyswisseph source/docs to understand the actual signature
2. Document findings in PROJECT-LOG.md
3. If the fix becomes more than a 5-line change, stop and surface it for review rather than expanding scope mid-task

If CI keeps failing for an unclear reason after 3+ iterations:

1. Reset the branch to `development`
2. Document each iteration's failure in PROJECT-LOG.md
3. Commit the log on `task-004-failed-attempt-1`
4. Push and stop

A clean failure with diagnosis notes is better than a broken main-line.

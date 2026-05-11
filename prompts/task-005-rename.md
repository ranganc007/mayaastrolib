# Task 005: Rename flatlib → mayaastrolib

## Context

You are working in the `mayaastrolib` repository. Before doing anything:

1. Read `CLAUDE.md` in full.
2. Read `docs/RECON.md` — specifically §1 (module inventory) and §6 (dependency graph). The dependency graph is critical for understanding the import-update scope.
3. Read `docs/PROJECT-LOG.md` for entries from Tasks 002, 002b, 003, 004, 004a.
4. Read `docs/CONTRIBUTION-PLAN.md` for the original Task 005 spec.
5. Confirm Task 004a has been merged to `development`:

   ```
   git log --oneline development -10
   ```

   You should see the smoke test commits from Task 004a.

   If Task 004a is not merged, STOP. Append a note to PROJECT-LOG.md and exit.

   ALSO confirm: `pytest tests/` should produce ≥33 tests passing on `development`. If it doesn't, the safety net isn't in place. Stop and report.

## Why this is the highest-risk task in Phase 0

This task touches every Python file. A single missed import becomes a runtime error in user code. The smoke tests from Task 004a are your safety net — if any test fails post-rename, you have a missed import.

The compatibility shim (step 3 below) means existing users doing `import flatlib` continue to work, with a deprecation warning. This is critical: it means people who pip-installed the fork as a flatlib drop-in don't have their code break overnight.

## Task scope

### 1. Rename the source directory

```
git mv flatlib mayaastrolib
```

`git mv` preserves history. After this, the directory is `mayaastrolib/` instead of `flatlib/`.

Subdirectories rename automatically:
- `mayaastrolib/dignities/`
- `mayaastrolib/ephem/`
- `mayaastrolib/predictives/`
- `mayaastrolib/protocols/`
- `mayaastrolib/tools/`
- `mayaastrolib/resources/`

### 2. Update every internal import

Every file that imports from `flatlib` needs updating to import from `mayaastrolib` instead.

Find them:

```
grep -r "from flatlib" --include="*.py" -l
grep -r "import flatlib" --include="*.py" -l
```

Update each. Patterns to handle:

```python
# Before                              # After
from flatlib import const             from mayaastrolib import const
from flatlib.chart import Chart       from mayaastrolib.chart import Chart
from flatlib.dignities import essential   from mayaastrolib.dignities import essential
import flatlib                        import mayaastrolib
import flatlib.const as const         import mayaastrolib.const as const
```

Files to update include:
- All `.py` files inside `mayaastrolib/` (the renamed source)
- `tests/*.py` (all test files)
- `recipes/*.py` (the example scripts)
- Any other Python file in the repo

The `contrib/topical_almuten.py.broken` file is intentionally not parseable so leave it alone — its imports stay as-is. Same for the `topical_almuten.README.md`.

Also check non-Python files:
- `pyproject.toml` — the `[tool.setuptools] packages` list needs updating from `flatlib*` to `mayaastrolib*`
- `pyproject.toml` — the `[tool.setuptools.package-data]` section's `flatlib = [...]` becomes `mayaastrolib = [...]`
- `pyproject.toml` — `[tool.coverage.run] source` was already set to `mayaastrolib` in Task 002, verify
- `.github/workflows/test.yml` — coverage source `flatlib` → `mayaastrolib`
- README.md — any code examples

### 3. Add the compatibility shim

Create a new top-level package `flatlib/` with just an `__init__.py`:

```python
"""Compatibility shim — flatlib has been renamed to mayaastrolib.

This module re-exports everything from `mayaastrolib` and emits a
DeprecationWarning. Marked for removal in version 1.0.

Update your imports:
    from flatlib import const     →  from mayaastrolib import const
    from flatlib.chart import Chart  →  from mayaastrolib.chart import Chart
"""

import warnings

warnings.warn(
    "The 'flatlib' package has been renamed to 'mayaastrolib'. "
    "Update your imports: 'from flatlib import X' → 'from mayaastrolib import X'. "
    "The 'flatlib' shim will be removed in version 1.0.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from mayaastrolib at the package level
from mayaastrolib import *  # noqa: F401, F403, E402

# Make submodules importable through the shim too
from mayaastrolib import (  # noqa: F401, E402
    aspects,
    angle,
    chart,
    const,
    datetime,
    geopos,
    lists,
    object,
    props,
    utils,
)
```

You'll likely also need shims for the subpackages so `from flatlib.dignities import essential` keeps working. Create:

- `flatlib/dignities/__init__.py` — re-exports from `mayaastrolib.dignities`
- `flatlib/ephem/__init__.py`
- `flatlib/predictives/__init__.py`
- `flatlib/protocols/__init__.py`
- `flatlib/tools/__init__.py`

Each subpackage `__init__.py` should be minimal:

```python
"""Compatibility shim — see flatlib/__init__.py for the deprecation notice."""
from mayaastrolib.<subpackage> import *  # noqa: F401, F403
```

Update `pyproject.toml` `[tool.setuptools] packages` to include both the new `mayaastrolib*` packages AND the old `flatlib*` shim packages. Both need to be installed for the shim to work.

### 4. Update version

Bump version to `0.3.0` in `pyproject.toml`. This is a substantial enough change to warrant a minor bump even though there's a compatibility shim. Update CHANGELOG.md.

### 5. Verify everything works

This is the critical verification. Use a fresh venv:

```
python3 -m venv .venv-task005
.venv-task005/bin/pip install -e ".[dev]"

# Native usage (the new way)
.venv-task005/bin/python -c "
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib import const

date = Datetime('2015/03/13', '17:00', '+00:00')
pos = GeoPos('38n32', '8w54')
chart = Chart(date, pos)
print('Native:', chart.get(const.SUN))
"

# Shim usage (the old way must still work, with warning)
.venv-task005/bin/python -W error::DeprecationWarning -c "
import flatlib
" 2>&1 | head -5  # expect DeprecationWarning to fire

# Shim should still produce correct results when the warning is non-fatal
.venv-task005/bin/python -W ignore::DeprecationWarning -c "
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const

date = Datetime('2015/03/13', '17:00', '+00:00')
pos = GeoPos('38n32', '8w54')
chart = Chart(date, pos)
print('Shim:', chart.get(const.SUN))
"

# The two outputs above must produce IDENTICAL Sun position values

# Run the full test suite
.venv-task005/bin/pytest tests/ -v

# Run the recipes to make sure they still work
.venv-task005/bin/python recipes/aspects.py
.venv-task005/bin/python recipes/eclipses.py
.venv-task005/bin/python recipes/solarreturn.py
```

Capture all of this output in the session log. The "Native" and "Shim" Sun position outputs MUST match exactly. If they don't, the shim is broken.

If any recipe fails, an import update was missed.

If any test fails, the safety net caught a problem — diagnose before proceeding.

### 6. Update documentation

- README.md: update install instructions, code examples, project name references. Keep the fork banner.
- docs/source/* (if Sphinx exists): update any module references
- recipes/: each recipe should now import from `mayaastrolib`, not `flatlib`. Add a comment at the top of each recipe noting the new import style.

### 7. Update CHANGELOG.md

Under `[Unreleased]`:

```markdown
## [0.3.0] — 2026-MM-DD

### Changed
- Renamed package from `flatlib` to `mayaastrolib`. The new canonical import is `from mayaastrolib import …`.

### Added
- Compatibility shim: `import flatlib` continues to work but emits a DeprecationWarning. Marked for removal in version 1.0.
- Compatibility shims for all subpackages: `flatlib.dignities`, `flatlib.ephem`, `flatlib.predictives`, `flatlib.protocols`, `flatlib.tools`.

### Deprecated
- The `flatlib` package name. Migrate to `mayaastrolib`. The shim will be removed in 1.0.
```

## Out of scope

- Renaming functions, classes, or constants inside the codebase (camelCase → snake_case is deferred to Phase 2 per IDEAS.md)
- Adding type hints
- New tests beyond what's needed to verify the rename
- New functionality

## Process

1. Create branch:

   ```
   git checkout development
   git pull origin development
   git checkout -b task-005-rename
   ```

2. Suggested commits, in order (helps review immensely):
   - `refactor: rename flatlib package to mayaastrolib (git mv only)` — just the directory rename, before any import updates. Tests will be broken at this commit, that's expected and recoverable.
   - `refactor: update internal imports flatlib → mayaastrolib`
   - `refactor: update tests and recipes to import from mayaastrolib`
   - `feat: add flatlib compatibility shim with DeprecationWarning`
   - `build: update pyproject.toml package discovery for rename`
   - `ci: update CI coverage source to mayaastrolib`
   - `docs: update README and recipes for renamed package`
   - `chore: bump version to 0.3.0`

3. Pre-completion checklist:
   - `ruff format --check .` passes
   - `ruff check .` passes
   - `mypy mayaastrolib/` runs (errors expected, that's Phase 1)
   - `pytest -x` passes — ALL tests, including smoke tests from Task 004a
   - The native vs shim Sun-position comparison from step 5 produces matching output

4. PROJECT-LOG.md entry must include:
   - The native vs shim verification output
   - The full pytest output showing all tests passing
   - Number of files modified (likely 30+)
   - Any imports that needed special handling (relative imports, dynamic imports, etc.)

5. Push:

   ```
   git push -u origin task-005-rename
   ```

6. Watch CI run. It must pass on all three Python versions.

7. DO NOT merge. This is the most consequential review of Phase 0.

## Definition of done

- `mayaastrolib/` directory exists with all the source code
- Old `flatlib/` directory exists ONLY as compatibility shims (each `__init__.py` re-exports from `mayaastrolib`)
- All internal imports use `mayaastrolib`
- All tests pass — ≥33 tests, all green
- Native and shim usage produce identical results
- All recipes run without error
- pyproject.toml package discovery includes both `mayaastrolib*` and `flatlib*`
- Version bumped to 0.3.0
- CHANGELOG.md updated with [0.3.0] section
- CI green on the branch
- PROJECT-LOG.md updated with verification outputs

## If something goes wrong

The compatibility shim has subtle failure modes. If the shim doesn't quite work — typical failures: `from flatlib.chart import Chart` working but `from flatlib import chart` failing, or vice versa — diagnose by:

1. Print `flatlib.__path__` and `mayaastrolib.__path__` and check they match expectations
2. Try the imports manually in a Python REPL
3. Check that `pyproject.toml` includes BOTH packages in the discovery list

If a test fails post-rename, the most likely cause is a missed import. Run:

```
grep -r "flatlib" mayaastrolib/ tests/ recipes/ --include="*.py"
```

Anything that comes up is a missed update.

If you hit something fundamental and can't fix in 30 minutes:

1. `git reset --hard development`
2. Detailed failure report in PROJECT-LOG.md
3. Commit on `task-005-failed-attempt-1`
4. Push and stop

The rename is high-stakes enough that a clean failure with diagnosis notes is unambiguously better than pushing a half-working state. Phase 0 isn't "done" until Task 005 lands cleanly — there's no shame in attempting it twice.

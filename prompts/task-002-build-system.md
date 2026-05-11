# Task 002: Build System Modernisation

## Context

You are working in the `mayaastrolib` repository (a fork of `flatangle/flatlib`). Before doing anything else:

1. Read `CLAUDE.md` in full — these are the standing rules.
2. Read `docs/RECON.md` in full — this is the baseline analysis from Task 001. Pay particular attention to §8 (surprises) and §9 (recommended task ordering).
3. Read `docs/CONTRIBUTION-PLAN.md` for Task 002's full scope.
4. Read `docs/FORK-RATIONALE.md` for project intent.

Confirm in your session log that you have read these files before proceeding.

## Task scope

This task modernises the Python build system. It does NOT do housekeeping (gitignore, scripts/ deletion, README.rst handling, pythonpath config) — those are Task 002b.

In scope:

1. Create `pyproject.toml` using PEP 621 metadata format with the setuptools backend.

2. Migrate metadata from `setup.py`:
   - name: `mayaastrolib` (NOT flatlib)
   - version: read from a single source — see step 7
   - description, authors (preserve João Ventura as original author, add Rangan C. as fork maintainer)
   - license: MIT
   - classifiers, keywords, URLs
   - Set `requires-python = ">=3.10"`

3. In `pyproject.toml`, add `[project.optional-dependencies]`:
   - `dev`: pytest, pytest-cov, ruff, mypy
   - `docs`: sphinx (only if `docs/source/` will be built; if not, skip this group)

4. Configure tooling in `pyproject.toml`:
   - `[tool.ruff]`: line-length = 100, target-version = "py310"
   - `[tool.ruff.lint]`: select = ["E", "F", "I", "B", "A", "UP"] — DO NOT include "N" (PEP 8 naming) yet. The recon flagged that enabling N would explode violations because of the codebase's camelCase API. Defer N to a future task.
   - `[tool.mypy]`: python_version = "3.10", warn_unused_ignores = true, ignore_missing_imports = true (because pyswisseph has no stubs). Do NOT enable strict mode.
   - `[tool.pytest.ini_options]`: testpaths = ["tests"], addopts = "--strict-markers"
   - `[tool.coverage.run]`: source = ["mayaastrolib"]

5. Specify the package discovery section so `mayaastrolib` is found. The source directory is still named `flatlib/` (rename happens in Task 005). Use:

   ```
   [tool.setuptools]
   packages = ["flatlib", "flatlib.dignities", "flatlib.ephem", "flatlib.predictives", "flatlib.protocols", "flatlib.tools"]
   ```

   AND add `[tool.setuptools.package-data]` entries for the `flatlib/resources/swefiles/*.se1`, `*.cat`, and `*.txt` files. Verify against the existing `setup.py` `package_data` and `MANIFEST.in` to make sure no resources are dropped.

6. Specify dependencies: `pyswisseph >= 2.10.3.2`. Match what's in `setup.py` and `requirements.txt`.

7. Single source of truth for version: put the version in `pyproject.toml` `[project] version = "0.2.6"` (one minor bump from upstream's 0.2.5 to mark the fork). Then in `flatlib/__init__.py`, replace the hardcoded `__version__ = '0.2.3'` with a lookup via `importlib.metadata.version("mayaastrolib")`. Wrap that in a try/except for `PackageNotFoundError` and fall back to "0.0.0+unknown" so the package still imports if not installed.

8. Delete `setup.py`, `setup.cfg` (if present), and `requirements.txt`. These are now redundant.

9. Verify the install works in a fresh venv. Use a separate venv name like `.venv-task002` so it doesn't conflict with `.venv-recon`. Run:

   ```
   python3 -m venv .venv-task002
   .venv-task002/bin/pip install -e ".[dev]"
   .venv-task002/bin/pip show mayaastrolib
   .venv-task002/bin/python -c "import flatlib; print(flatlib.__version__)"
   .venv-task002/bin/pytest tests/
   ```

   The pytest run should produce 5 passed (same as recon baseline). Capture all four outputs in the session log.

## Out of scope (do NOT do these in this task)

- Updating `.gitignore` (Task 002b)
- Deleting `scripts/` (Task 002b)
- Handling `README.rst` vs `README.md` or `MANIFEST.in` (Task 002b)
- Adding `pythonpath` to pytest config (Task 002b)
- Creating `CHANGELOG.md` (Task 002b)
- Running `ruff check --fix` or `ruff format` (Task 003)
- Renaming the source directory (Task 005)

If you discover something in scope of those tasks during this work, note it in the session log under "follow-ups for Task 002b" and move on.

## Process

1. Create a new branch from `development`:

   ```
   git checkout development
   git pull origin development
   git checkout -b task-002-build-system
   ```

2. Do the work above. Suggested final commit structure (3 commits):
   - `build: add pyproject.toml with PEP 621 metadata`
   - `build: consolidate version source via importlib.metadata`
   - `build: remove setup.py, setup.cfg, requirements.txt`

3. Run the pre-completion checklist from CLAUDE.md, with these notes:
   - `ruff format --check` will fail because Task 003 hasn't run. That's expected — note it in the log but don't fix.
   - `ruff check` will report violations. That's expected — note it.
   - `mypy mayaastrolib/` won't work (the directory is still `flatlib/`). Run `mypy flatlib/` instead.
   - `pytest -x` should pass with 5/5 (matching recon baseline).
   - Coverage gate doesn't apply yet — skip the `--cov-fail-under=80` step.

4. Append a session entry to `docs/PROJECT-LOG.md` using the template already in that file. Cover:
   - What was done (brief bullets)
   - The four verification command outputs from step 9 above
   - Anything tried and discarded with reasoning
   - Surprises
   - Follow-ups for Task 002b (if any)

5. Push the branch:

   ```
   git push -u origin task-002-build-system
   ```

6. DO NOT merge to development. Leave the branch for human review.

## Definition of done

- `pyproject.toml` exists and is syntactically valid (verify with `python3 -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"`)
- Fresh venv install via `pip install -e ".[dev]"` succeeds
- `import flatlib` works and `flatlib.__version__` returns "0.2.6"
- `pytest tests/` passes 5/5
- `setup.py`, `setup.cfg`, `requirements.txt` are deleted
- Branch `task-002-build-system` is pushed to origin
- `docs/PROJECT-LOG.md` has an entry for this session
- No files outside scope have been modified (verify with `git diff development --stat` showing only the expected files)

## If something goes wrong

If you cannot complete the task — for example, if the package discovery configuration breaks the install in a way you can't diagnose — DO NOT push broken state to origin. Instead:

1. Reset the branch to `development`'s HEAD: `git reset --hard development`
2. Append a detailed failure report to `docs/PROJECT-LOG.md` covering what you tried, what failed, what you suspect is wrong
3. Commit the log entry on a new branch `task-002-failed-attempt-1` and push that
4. Stop work — do not proceed to Task 002b

A clean failure with good notes is better than a half-broken push.

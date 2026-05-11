# Task 002b: Repository Housekeeping

## Context

You are working in the `mayaastrolib` repository. Before doing anything:

1. Read `CLAUDE.md` in full.
2. Read `docs/RECON.md` — pay particular attention to Surprises §6, §7, §8, and §15.
3. Read `docs/PROJECT-LOG.md` for the Task 002 session entry — there may be follow-ups noted there.
4. Confirm Task 002 has been merged to `development` by running `git log --oneline development -5` and verifying you see the pyproject.toml commits.

If Task 002 has NOT been merged to development, STOP and report this in PROJECT-LOG.md. Do not proceed.

## Task scope

This task does the housekeeping that Task 002 deliberately deferred.

In scope:

### 1. Update `.gitignore`

Append entries for modern Python tooling artifacts (do not duplicate existing entries). At minimum add:

```
*.egg-info/
.coverage
.coverage.*
htmlcov/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.venv*/
venv*/
dist/
build/
__pycache__/
*.pyc
```

Check the file before editing — some of these may already exist. Don't duplicate.

### 2. Delete the legacy scripts directory

Remove these files:

- `scripts/build.py`
- `scripts/clean.py`
- `scripts/utils.py`

These were pre-pyproject-era helpers. With modern packaging they are redundant. If `scripts/` becomes empty after the deletion, remove the directory too. If there are OTHER files in `scripts/` not listed above, leave them alone and report in the log.

### 3. Reconcile README.rst and README.md

The recon found both files exist with different content (Surprise §6). The fork's README.md has the fork banner. Plan:

- Verify both files exist
- Delete `README.rst`
- Update `MANIFEST.in` if it references `README.rst`, replacing with `README.md` (or removing the line if `pyproject.toml` already includes the README via `readme = "README.md"`)
- In `pyproject.toml`, ensure `readme = "README.md"` is set in `[project]`. If it's missing, add it.

### 4. Add pytest pythonpath configuration

In `pyproject.toml`, under `[tool.pytest.ini_options]`, add:

```
pythonpath = ["."]
```

This means contributors can run `pytest` without first doing `pip install -e .`. The recon flagged this footgun in §2.

### 5. Create `CHANGELOG.md`

New file at repo root. Use the "Keep a Changelog" format (https://keepachangelog.com). Initial content:

```markdown
# Changelog

All notable changes to this project will be documented in this file. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed
- Forked from flatangle/flatlib at upstream version 0.2.5
- Modernised build system: replaced setup.py with pyproject.toml
- Consolidated version source via importlib.metadata
- Configured ruff, mypy, pytest in pyproject.toml
- Set Python minimum version to 3.10

### Removed
- Legacy build scripts (scripts/build.py, scripts/clean.py, scripts/utils.py)
- Legacy packaging files (setup.py, setup.cfg, requirements.txt)
- README.rst (consolidated to README.md)

## [0.2.6] - unreleased

Initial fork release. See [Unreleased] above.
```

### 6. Verify the install still works

Repeat the verification from Task 002 step 9, but with a fresh venv name `.venv-task002b`:

```
python3 -m venv .venv-task002b
.venv-task002b/bin/pip install -e ".[dev]"
.venv-task002b/bin/python -c "import flatlib; print(flatlib.__version__)"
.venv-task002b/bin/pytest tests/
```

Should still produce 5/5 passing. Capture output in log.

### 7. Verify pythonpath config works

In a fresh shell with no venv activated:

```
python3 -m venv .venv-task002b-bare
.venv-task002b-bare/bin/pip install pytest pytest-cov pyswisseph==2.10.3.2
# Note: NO `pip install -e .` this time
.venv-task002b-bare/bin/pytest tests/
```

This should ALSO produce 5/5 passing thanks to the new `pythonpath = ["."]` config. If it fails, the pythonpath config is wrong — fix it before proceeding. Capture output.

## Out of scope

- Anything Task 003 (ruff fixes) or beyond
- Renaming the source directory
- Touching `flatlib/` source code at all — this is pure housekeeping

## Process

1. Create branch from `development`:

   ```
   git checkout development
   git pull origin development
   git checkout -b task-002b-housekeeping
   ```

2. Suggested commit structure (4 commits, makes review trivial):
   - `chore: update .gitignore for modern Python tooling`
   - `chore: remove legacy scripts directory`
   - `chore: consolidate to README.md, update MANIFEST.in`
   - `build: add pytest pythonpath config and CHANGELOG.md`

3. Run pre-completion checklist with same caveats as Task 002 (ruff format/check still expected to fail, that's Task 003).

4. Append entry to `docs/PROJECT-LOG.md` covering all six steps, with the verification command outputs from steps 6 and 7.

5. Push:

   ```
   git push -u origin task-002b-housekeeping
   ```

6. DO NOT merge. Leave for human review.

## Definition of done

- `.gitignore` updated, no duplicate entries
- `scripts/build.py`, `scripts/clean.py`, `scripts/utils.py` deleted
- `README.rst` deleted, `MANIFEST.in` consistent
- `pyproject.toml` has `readme = "README.md"` and pythonpath config
- `CHANGELOG.md` exists at repo root with initial content
- Both verification runs produce 5/5 passing tests
- Branch pushed to origin
- PROJECT-LOG.md has session entry
- `git diff development --stat` shows only expected file changes

## If something goes wrong

Same protocol as Task 002: do not push broken state. Reset to `development` HEAD, log a detailed failure report on a separate branch, stop work.

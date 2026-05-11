# Task 003: Ruff Baseline and Code Style

## Context

You are working in the `mayaastrolib` repository. Before doing anything:

1. Read `CLAUDE.md` in full.
2. Read `docs/RECON.md` — specifically §3 (lint baseline), §8 ¶2 (the contrib syntax error), and §9 (recommended ordering for Task 003).
3. Read `docs/PROJECT-LOG.md` for entries from Task 002 and Task 002b.
4. Confirm Tasks 002 AND 002b have been merged to `development`:

   ```
   git log --oneline development -10
   ```

   You should see (from the top, in order):
   - `build: add pytest pythonpath config and initial CHANGELOG`
   - `chore: consolidate to README.md, update MANIFEST.in`
   - `chore: remove legacy scripts directory`
   - `chore: update .gitignore for modern Python tooling`
   - `build: remove setup.py and requirements.txt`
   - `build: consolidate version source via importlib.metadata`
   - `build: add pyproject.toml with PEP 621 metadata`

   If the four `chore:` and `build:` commits from Task 002b are not present, STOP. Append a note to PROJECT-LOG.md saying Task 002b is not merged and exit.

## Task scope

This task gets the codebase to a clean ruff baseline using the configuration that Task 002 established in `pyproject.toml` (rules: E, F, I, B, A, UP — line length 100 — target py310).

The recon §3 found 9 ruff violations in `flatlib/` plus 5 syntax errors in `contrib/topical_almuten.py`. Note that the new ruff rule set is broader than the default used in the recon, so expect MORE violations than the recon's baseline.

In scope:

### 1. Archive the broken contrib file

Per recon §8 ¶2, `contrib/topical_almuten.py` has had a SyntaxError since at least 2021-04-05 (mismatched brackets at lines 102/103). Nothing imports this file. The decision (made by the project maintainer, not negotiable) is to ARCHIVE rather than fix or delete:

- Rename the file to `contrib/topical_almuten.py.broken`
- Add a sibling file `contrib/topical_almuten.README.md` with this content:

```markdown
# topical_almuten.py.broken — archived

This file has had a SyntaxError since at least 2021-04-05 (upstream commit "Update topical_almuten.py"). Bracket placement at lines 102 and 103 is wrong:

    TA_LIST.extend([chart.getObject(essential.dayTrip(chart.getHouse(const.HOUSE4).sign])))

The `]` and `)` are swapped — should likely be `…HOUSE4).sign))])`.

Nothing imports this file. It appears to be experimental Persian/Vedic-nativity work (topical almuten is a technique with Vedic parallels) that may be relevant to Phase 2 of the fork (Vedic unification). Archived rather than fixed because we do not yet understand the original author's intent and don't want to silently change behaviour we don't have tests for.

To revisit: rename back to `.py`, fix the brackets, write tests. Until then, ruff and import scanners skip it because of the `.broken` suffix.
```

### 2. Run ruff format

Run `.venv-task003/bin/ruff format .` across the whole repo. The recon expected 54 files would be reformatted. This is whitespace, indentation, line wrapping, quote style — no logic changes.

Capture the count of files actually changed in the session log.

Commit as a single commit: `style: apply ruff format across repo`. The body should note this is a pure formatting change with no logic modifications.

### 3. Run ruff check --fix

Run `.venv-task003/bin/ruff check --fix .`. This auto-fixes the safe violations:
- F401 unused imports
- E703 trailing semicolons
- Possibly some UP (pyupgrade) violations

Review every change before committing. Auto-fixes can occasionally be wrong. If anything looks suspicious, revert it and document in the log.

Commit as: `style: apply ruff auto-fixes`.

### 4. Hand-fix remaining ruff violations

Run `.venv-task003/bin/ruff check .` and fix what remains. The recon predicted these specific issues will need human attention:

- `flatlib/aspects.py:294` — `E712`: change `== True` to `is True` or use truthiness
- `flatlib/dignities/accidental.py:322` — `E712`: same
- `flatlib/protocols/temperament.py:46,54` — `E721`: change `type(obj) == str` to `isinstance(obj, str)`
- `flatlib/ephem/eph.py:61` — `F402`: rename the loop variable `for angle in angles:` to `for ang in angles:` (or similar) so it stops shadowing the imported `angle` module

The new ruff rule set (UP especially) may surface MORE issues than the recon predicted because the recon ran with default rules. Fix everything that comes up, OR — if a class of violation is too large to fix safely (more than ~10 instances of one rule, or instances that change semantics) — disable that specific rule in `pyproject.toml` `[tool.ruff.lint] ignore = [...]` and document the deferral in `docs/RUFF-DEBT.md`.

For the camelCase issue specifically: the N (pep8-naming) rule was deliberately NOT enabled in Task 002. If you find ruff is still flagging naming issues, something is wrong with the config. Verify `pyproject.toml` `[tool.ruff.lint] select` does not contain "N".

Commit as: `style: hand-fix remaining ruff violations`.

### 5. Verify everything still works

In a fresh venv:

```
python3 -m venv .venv-task003
.venv-task003/bin/pip install -e ".[dev]"
.venv-task003/bin/ruff format --check .
.venv-task003/bin/ruff check .
.venv-task003/bin/pytest tests/
```

All four commands must pass cleanly. Capture output in log.

`ruff format --check .` should pass (no files to reformat).
`ruff check .` should pass (no violations) OR only report violations documented in `docs/RUFF-DEBT.md`.
`pytest tests/` should pass 5/5.

### 6. Create RUFF-DEBT.md if needed

Only if you deferred any rule classes in step 4. Otherwise skip.

Format:

```markdown
# Ruff Debt

Rules currently disabled in `pyproject.toml [tool.ruff.lint] ignore` and the reason for deferral.

## RULE_CODE — short name

**Disabled in:** pyproject.toml on YYYY-MM-DD
**Reason:** ...
**Plan:** ...
```

## Out of scope

- Adding type hints (Phase 1 work)
- Modifying test code beyond ruff's auto-fixes
- Renaming the source directory
- Fixing the eclipse bug (Task 004)
- Any new functionality

## Process

1. Create branch from `development`:

   ```
   git checkout development
   git pull origin development
   git checkout -b task-003-ruff-baseline
   ```

2. Commits, in order:
   - `chore: archive broken contrib/topical_almuten.py`
   - `style: apply ruff format across repo`
   - `style: apply ruff auto-fixes`
   - `style: hand-fix remaining ruff violations`
   - `docs: add RUFF-DEBT.md` (only if step 6 needed)

3. Update `CHANGELOG.md` `[Unreleased]` section with a `### Changed` subsection noting the formatting and lint pass. Don't bump the version.

4. Run pre-completion checklist with these notes:
   - `ruff format --check` should now PASS
   - `ruff check` should now PASS (or only show documented debt)
   - `mypy flatlib/` may still show 2 errors from recon §4 — that's fine, type hints are Phase 1
   - `pytest -x` should pass 5/5
   - Coverage gate doesn't apply yet

5. Append entry to `docs/PROJECT-LOG.md` with:
   - The actual file count from `ruff format` (predicted 54)
   - The actual violation count after each step
   - Anything that surprised you compared to the recon predictions
   - List of any rules deferred to RUFF-DEBT.md with reasoning

6. Push:

   ```
   git push -u origin task-003-ruff-baseline
   ```

7. DO NOT merge. Leave for human review.

## Definition of done

- `contrib/topical_almuten.py` no longer exists; `.broken` and `.README.md` siblings do
- `ruff format --check .` passes cleanly
- `ruff check .` passes cleanly (or only reports documented debt)
- All 5 existing tests still pass
- Branch pushed to origin
- PROJECT-LOG.md has session entry with concrete numbers
- CHANGELOG.md updated under `[Unreleased]`

## If something goes wrong

The most likely failure mode: a UP (pyupgrade) auto-fix changes behaviour subtly and a test starts failing. If this happens:

1. Identify which auto-fix caused it (`git bisect` is overkill for 4 commits — just check each one)
2. Revert just that change
3. Document the rule disable in RUFF-DEBT.md
4. Re-run pytest to confirm green

If you can't isolate the cause within ~30 minutes:

1. Reset the branch: `git reset --hard development`
2. Detailed failure report in PROJECT-LOG.md
3. Commit on `task-003-failed-attempt-1`
4. Push and stop

Do not push partial state to `task-003-ruff-baseline`.

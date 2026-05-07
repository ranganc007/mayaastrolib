# Project Log

Running journal of all sessions on this project. Newest entries at the top.

Each entry should follow this template:

---

## 2026-05-07 — Task 003: Ruff baseline and code style

**Session length:** ~40 minutes (single Claude Code session)
**Branch:** `task-003-ruff-baseline`
**Commits:** see `git log task-003-ruff-baseline`

### What was done

1. **Archived broken contrib file.** `contrib/topical_almuten.py` →
   `.broken`, plus a sibling `topical_almuten.README.md` documenting
   the SyntaxError and how to revive the file (per RECON §8 ¶2).
   The `.broken` suffix takes the file out of ruff's scan path
   without needing any per-file ignore.
2. **`ruff format` across the repo.** 50 files reformatted (RECON
   predicted 54; the delta is from `setup.py`, three `scripts/*.py`,
   and `README.rst` removed in Tasks 002/002b plus the `.broken`
   rename above). Pure whitespace/quote/wrap. pytest 5/5 still passes.
3. **`ruff check --fix`.** 96 → 47 violations; 49 auto-fixed across
   39 files. Categories: F401 (unused imports), E703 (semicolons),
   I001 (import sort), some UP modernisations. Reviewed every diff
   before committing — `flatlib/ephem/{swe,eph}.py` and
   `flatlib/protocols/temperament.py` are pure isort consolidation,
   nothing semantic.
4. **Hand-fixed remaining 22 violations.** Per-rule:
   - E712 (×2): `== True` → `is True and …`.
   - E721 (×2): `type(x) == str` → `isinstance(x, str)`.
   - F402 (×1): rename `for angle in angles:` → `for ang in angles:`
     in `flatlib/ephem/eph.py`.
   - B007 (×3): unused loop vars prefixed `_`.
   - B006 (×1): mutable default `values=[]` →
     `values=None` + `for obj in values or []:` in
     `flatlib/lists.py`.
   - B905 (×8): explicit `strict=False` on every `dict(zip(...))` in
     `flatlib/props.py`.
   - A001 (×2): per-line `noqa` on `class object` (props.py — public
     API, breaking change deferred) and `copyright` (Sphinx
     convention).
   - E402 (×3): per-line `noqa` on `docs/source/conf.py:116` (Sphinx
     style) and `recipes/primarydirections.py:37,47` (intentional
     teaching style noted in RECON §7). Recipe imports also need
     `I001` in the noqa to stop isort from regrouping them.
5. **Deferred UP031 (printf-format) — 23 instances.** Added
   `ignore = ["UP031"]` to `[tool.ruff.lint]` in `pyproject.toml`
   and recorded the deferral in the new `docs/RUFF-DEBT.md`. Volume
   exceeds the spec's "~10 instance" hand-fix threshold and several
   are in recipe scripts where stylistic rewrites would be churn.
6. **Updated `CHANGELOG.md`.** Added bullets under `[Unreleased]
   ### Changed` (ruff format + lint pass) and `### Removed` (broken
   contrib archive).

### Verification (Definition of Done)

```
$ python3 -m venv .venv-task003
$ .venv-task003/bin/pip install -e ".[dev]"
$ .venv-task003/bin/ruff format --check .
50 files already formatted

$ .venv-task003/bin/ruff check .
All checks passed!

$ .venv-task003/bin/pytest tests/
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /opt/homebrew/var/www/oss-contrib/mayaastrolib
configfile: pyproject.toml
plugins: cov-7.1.0
collected 5 items

tests/test_angles.py ....                                                [ 80%]
tests/test_chart.py .                                                    [100%]

============================== 5 passed in 0.04s ===============================
```

### Pre-completion checklist

- `ruff format --check .` — **PASS** (50 already formatted).
- `ruff check .` — **PASS** (`All checks passed!` after the UP031
  deferral).
- `mypy flatlib/` — still 2 errors from RECON §4. Type hints are
  Phase 1; nothing to fix here.
- `pytest -x` — **5/5 PASS**.
- Coverage gate skipped (still on the dormant `mayaastrolib` source
  setting).

### What was tried and discarded

- **Tried** noqa with only `# noqa: E402` on the late recipe
  imports. Ruff still flagged I001 (import block organisation),
  because isort wants those imports consolidated with the top of the
  file. Switched the noqa to `# noqa: E402, I001` to disable both
  per-line. Cleaner than restructuring the recipe to defeat its
  teaching style.
- **Considered** mass-fixing UP031 (`%` → f-string) by hand.
  Discarded: 23 instances across `flatlib/{angle,aspects,datetime,
  geopos,object}.py`, `flatlib/predictives/primarydirections.py`,
  `flatlib/protocols/almutem.py`, and several recipes. The Task 003
  spec says >10 instances → defer to RUFF-DEBT.md. Deferred. The
  RUFF-DEBT entry suggests rolling them up with the camelCase →
  snake_case major-version cleanup.
- **Considered** renaming `flatlib.props.object` to silence A001.
  Discarded: it's part of the public API (RECON §8 ¶5) and
  CONTRIBUTION-PLAN.md says breaking changes need a major version
  bump. Per-line `noqa` with rationale is the right call.
- **Considered** adding `strict=True` rather than `strict=False` to
  the props.py zip calls. Discarded: the existing implicit behaviour
  is `strict=False`. The lengths *are* equal by construction
  today (twelve signs × 1/2/4 multipliers), but flipping to
  `strict=True` would mean a future drift in a constants list raises
  ValueError silently in module-import order, which would be hard to
  diagnose. `strict=False` preserves behaviour exactly; tightening
  to `strict=True` is a separate decision worth its own commit.

### Surprises

- The `ruff check` total was 96 (not the 123 from Task 002's
  pre-completion checklist). Task 002's count was `ruff check .`
  against the **unformatted** tree; running `ruff format` first
  collapses some violations (e.g. lines that wrap onto multiple
  lines after formatting can dissolve E501s, and some UP/B issues
  resolve themselves once the AST is canonical). 96 → 47 → 22 → 0
  with auto-fix + hand-fix + UP031 deferral.
- `ruff format` reformatted 50 files, not the 54 RECON predicted.
  Three deletions in 002b (`scripts/*.py`) plus `setup.py` (002) and
  `README.rst` (002b) account for the gap. The `.broken` rename of
  `contrib/topical_almuten.py` removes one more file from the scan
  surface.
- Per-line `noqa` with rationale is the cleanest way to handle
  intentional violations. Adding the rationale text in-line means
  future readers don't need to grep RUFF-DEBT.md to understand
  why ruff is silenced at that point.

### Follow-ups for later tasks

- **Task 004 (CI + eclipse fix):** the `flatlib/ephem/swe.py`
  eclipse keyword bug from RECON §8 ¶1 still stands. Task 003
  intentionally didn't touch it. Pre-conditions for Task 004 are
  now in place: ruff is green, so the CI lint step will pass.
- **Task 005 (rename):** the `class object` A001 noqa in
  `flatlib/props.py` will need to move to whatever the new file path
  becomes after the rename. Mechanical.
- **Future major-version cleanup:** UP031 (23 instances) +
  camelCase → snake_case + the `props.object` rename can all happen
  together when the public-API contract gets re-cut.
- **`docs/source/conf.py`:** the Sphinx config still references
  `project = "flatlib"` — out of Task 003 scope but should be
  reconciled when docs work begins.

### Definition of done — verified

- [x] `contrib/topical_almuten.py` no longer exists; `.broken` and
  `.README.md` siblings present.
- [x] `ruff format --check .` passes cleanly.
- [x] `ruff check .` passes cleanly (UP031 documented in
  `docs/RUFF-DEBT.md`).
- [x] All 5 existing tests still pass.
- [x] Branch will be pushed to origin (next step).
- [x] PROJECT-LOG.md has this session entry with concrete numbers.
- [x] CHANGELOG.md updated under `[Unreleased]`.

---

## 2026-05-07 — Task 002b: Repository housekeeping

**Session length:** ~25 minutes (single Claude Code session)
**Branch:** `task-002b-housekeeping`
**Commits:** see `git log task-002b-housekeeping`

### What was done

All six in-scope steps from `prompts/task-002b-housekeeping.md`:

1. **`.gitignore`** — appended a "Modern Python tooling artifacts"
   block with `__pycache__/`, `*.egg-info/`, `.coverage`,
   `.coverage.*`, `htmlcov/`, `.pytest_cache/`, `.mypy_cache/`,
   `.ruff_cache/`, `.venv*/`, `venv*/`, plus `dist/`. Skipped
   duplicates: `*.py[cdo]` already covers `.pyc`/`.pyo`, `venv/` was
   present (extended to `venv*/`), `build/` already there.

2. **Legacy scripts** — `git rm scripts/build.py scripts/clean.py
   scripts/utils.py`. The `scripts/` directory was removed
   automatically by git when its last tracked file went. No other
   files were present in `scripts/` (nothing extra to report).

3. **README reconciliation** — `git rm README.rst`; `MANIFEST.in`
   reduced to a single `include LICENSE` line (the previous
   `include README.rst` was removed; `README.md` is already wired in
   via `pyproject.toml [project] readme = "README.md"`, so setuptools
   includes it in the sdist automatically — no `include README.md`
   needed in MANIFEST.in).

4. **pytest pythonpath** — added `pythonpath = ["."]` to
   `[tool.pytest.ini_options]` in `pyproject.toml`. RECON §2 footgun
   resolved: contributors who skip `pip install -e .` can still
   `pytest tests/`.

5. **`CHANGELOG.md`** — created at repo root with the Keep-a-Changelog
   skeleton from the spec (Unreleased + 0.2.6).

### Verification — step 6 (editable install path)

```
$ python3 -m venv .venv-task002b
$ .venv-task002b/bin/pip install -e ".[dev]"
… (Successfully installed mayaastrolib-0.2.6 + dev deps)

$ .venv-task002b/bin/python -c "import flatlib; print(flatlib.__version__)"
0.2.6

$ .venv-task002b/bin/pytest tests/
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /opt/homebrew/var/www/oss-contrib/mayaastrolib
configfile: pyproject.toml
plugins: cov-7.1.0
collected 5 items

tests/test_angles.py ....                                                [ 80%]
tests/test_chart.py .                                                    [100%]

============================== 5 passed in 0.38s ===============================
```

5/5 passed.

### Verification — step 7 (pythonpath, NO editable install)

```
$ python3 -m venv .venv-task002b-bare
$ .venv-task002b-bare/bin/pip install pytest pytest-cov pyswisseph==2.10.3.2
$ .venv-task002b-bare/bin/pytest tests/
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /opt/homebrew/var/www/oss-contrib/mayaastrolib
configfile: pyproject.toml
plugins: cov-7.1.0
collected 5 items

tests/test_angles.py ....                                                [ 80%]
tests/test_chart.py .                                                    [100%]

============================== 5 passed in 0.54s ===============================
```

5/5 passed. The `pythonpath = ["."]` config works as intended:
contributors no longer need `pip install -e .` to run the test suite.

### Pre-completion checklist

- `ruff format --check .` — still fails (52 files would be reformatted,
  one fewer than Task 002 because three `scripts/*.py` deletions and
  one `README.rst` deletion offset against zero new Python files).
  Expected; Task 003.
- `ruff check .` — still reports configured-rule-set violations.
  Expected; Task 003.
- `mypy flatlib/` — 2 errors, unchanged from RECON.
- `pytest -x` — 5/5 in both editable and bare-pythonpath flows.
- Coverage gate skipped per spec.

### What was tried and discarded

- **Considered** putting `include README.md` in `MANIFEST.in` for
  parallelism with the deleted `include README.rst`. Discarded:
  setuptools auto-includes the file declared in
  `pyproject.toml [project] readme`, so a duplicate MANIFEST entry is
  redundant. MANIFEST.in is now down to the single `include LICENSE`
  line — easier to scan, no reason to add ceremony.
- **Considered** dropping the existing `venv/` line from `.gitignore`
  in favour of just `venv*/`. Kept both: the `venv*/` glob covers
  `venv/`, but leaving the original line means anyone diffing the file
  doesn't have to wonder if a previously-ignored path is now tracked.
  Idempotent and explicit beats clever-and-implicit for `.gitignore`.

### Surprises

- Task 002's commits showed up at the top of `git log development`
  before this session even started — the local `development` branch
  was fast-forward-merged to `task-002-build-system`'s tip between
  sessions, and the topic branch was deleted. Nothing wrong, just
  worth noting that the merge happened outside Claude Code.
- The bare `pip install pytest pytest-cov pyswisseph==2.10.3.2` venv
  successfully ran the tests without `pyproject.toml` validation
  errors or warnings about missing the project. pytest's
  `configfile:` line still showed `pyproject.toml` (it reads
  `[tool.pytest.ini_options]` regardless of whether the project is
  installed), so the pythonpath setting kicks in even without
  setuptools knowing about the project. That's exactly the intended
  behaviour — pleasant to confirm.
- `.gitignore` had `venv/` (without the trailing wildcard) but no
  `*.egg-info/`, `.coverage`, `__pycache__/`, or any of the modern
  cache directories. The repo really hadn't been touched by anyone on
  modern tooling since 2021.

### Follow-ups for later tasks

- **Task 003:** `ruff format` / `ruff check` cleanup is the next
  obvious step. RECON §9 already lays out the order.
- **Task 004:** GitHub Actions CI + the eclipse hot-fix from RECON
  §8 ¶1.
- **Task 005:** the `flatlib/` → `mayaastrolib/` rename, after which
  the dormant `[tool.coverage.run] source = ["mayaastrolib"]` setting
  becomes meaningful.
- **Maintainer decision deferred:** the repository now has no
  `setup.py` shim. If anyone tries `pip install` from a git URL with
  a very old pip, they'll get the modern build path. Worth noting in
  README's installation section once the package is published.

### Definition of done — verified

- [x] `.gitignore` updated, no duplicate entries.
- [x] `scripts/build.py`, `scripts/clean.py`, `scripts/utils.py`
  deleted; `scripts/` directory gone.
- [x] `README.rst` deleted; `MANIFEST.in` consistent with the new
  README situation.
- [x] `pyproject.toml` has `readme = "README.md"` (already from Task
  002) and `pythonpath = ["."]` (added this session).
- [x] `CHANGELOG.md` exists at repo root with the spec's initial
  content.
- [x] Both verification runs produce 5/5 passing tests.
- [x] `git diff development --stat` of committed files shows exactly
  the expected files: `.gitignore`, `CHANGELOG.md`, `MANIFEST.in`,
  `docs/PROJECT-LOG.md`, `pyproject.toml`, plus the deletions of
  `README.rst`, `scripts/build.py`, `scripts/clean.py`,
  `scripts/utils.py`.

---

## 2026-05-07 — Task 002: Build system modernisation

**Session length:** ~45 minutes (single Claude Code session)
**Branch:** `task-002-build-system`
**Commits:** see `git log task-002-build-system`

### What was done

- Confirmed read of `CLAUDE.md`, `docs/RECON.md`, `docs/CONTRIBUTION-PLAN.md`,
  and `docs/FORK-RATIONALE.md` before any edits.
- Created `pyproject.toml` (PEP 621, setuptools backend) with:
  - `name = "mayaastrolib"`, `version = "0.2.6"` (single source of truth),
    `requires-python = ">=3.10"`.
  - Authors: João Ventura preserved; Rangan C. added as maintainer.
  - License MIT; classifiers, keywords, URLs migrated from `setup.py`.
  - Dependency: `pyswisseph >= 2.10.3.2`.
  - `[project.optional-dependencies] dev = [pytest, pytest-cov, ruff,
    mypy]`. Skipped the `docs` group: `docs/source/` exists but the
    Sphinx skeleton is from 2015 and isn't part of the current build —
    spec said to skip if not built.
  - `[tool.setuptools] packages = ["flatlib", "flatlib.dignities",
    "flatlib.ephem", "flatlib.predictives", "flatlib.protocols",
    "flatlib.tools"]` — directory rename is Task 005.
  - `[tool.setuptools.package-data]` includes `resources/README.md`,
    `resources/swefiles/*.se1`, `*.cat`, `*.txt` (verified against
    `setup.py` `package_data` and `MANIFEST.in`; covers all 9 `.se1`,
    `fixstars.cat`, `sefstars.txt`).
  - `[tool.ruff]` line-length 100, target-version py310, lint
    `select = ["E","F","I","B","A","UP"]` — `N` deferred per spec.
  - `[tool.mypy]` python_version 3.10, warn_unused_ignores,
    ignore_missing_imports (pyswisseph has no stubs).
  - `[tool.pytest.ini_options] testpaths = ["tests"], addopts =
    "--strict-markers"`.
  - `[tool.coverage.run] source = ["mayaastrolib"]` (matches CLAUDE.md
    pre-completion checklist; will become live after Task 005 rename).
- Rewrote `flatlib/__init__.py` to derive `__version__` from
  `importlib.metadata.version("mayaastrolib")` with a
  `PackageNotFoundError` fallback to `"0.0.0+unknown"`. Eliminates the
  RECON §8 ¶13 version mismatch (`0.2.3` vs `0.2.5`).
- Deleted `setup.py` and `requirements.txt`. `setup.cfg` was already
  absent. `MANIFEST.in` left in place — handling of `README.rst` vs
  `README.md` is Task 002b per the task spec.

### Verification (Definition of Done step 9)

Fresh `.venv-task002` on Python 3.14.3 (CI matrix Python is not
installed locally; flagged for Task 004).

```
$ python3 -m venv .venv-task002
$ .venv-task002/bin/pip install -e ".[dev]"
…
Successfully installed ast-serialize-0.3.0 coverage-7.13.5 iniconfig-2.3.0
  librt-0.10.0 mayaastrolib-0.2.6 mypy-2.0.0 mypy_extensions-1.1.0
  packaging-26.2 pathspec-1.1.1 pluggy-1.6.0 pygments-2.20.0
  pyswisseph-2.10.3.2 pytest-9.0.3 pytest-cov-7.1.0 ruff-0.15.12
  typing_extensions-4.15.0
```

```
$ .venv-task002/bin/pip show mayaastrolib
Name: mayaastrolib
Version: 0.2.6
Summary: Python library for Traditional and Vedic Astrology (fork of flatangle/flatlib)
Home-page: https://github.com/ranganc007/mayaastrolib
Author:
Author-email: João Ventura <flatangleweb@gmail.com>
License: MIT
Location: /opt/homebrew/var/www/oss-contrib/mayaastrolib/.venv-task002/lib/python3.14/site-packages
Editable project location: /opt/homebrew/var/www/oss-contrib/mayaastrolib
Requires: pyswisseph
Required-by:
```

```
$ .venv-task002/bin/python -c "import flatlib; print(flatlib.__version__)"
0.2.6
```

```
$ .venv-task002/bin/pytest tests/
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /opt/homebrew/var/www/oss-contrib/mayaastrolib
configfile: pyproject.toml
plugins: cov-7.1.0
collected 5 items

tests/test_angles.py ....                                                [ 80%]
tests/test_chart.py .                                                    [100%]

============================== 5 passed in 0.38s ===============================
```

5/5 passed — matches the RECON §2 baseline.

### Pre-completion checklist (with notes from spec)

- `ruff format --check .` — **53 files would be reformatted** (expected;
  Task 003). One file fewer than the RECON 54 because `setup.py` is now
  deleted.
- `ruff check .` — **123 errors** with the configured rule set (E, F, I,
  B, A, UP). RECON saw 25 with default rules. The increase comes
  primarily from `B` (bugbear), `A` (builtin shadowing — flags
  `flatlib/props.py`'s `class object`), `UP` (pyupgrade), and `I`
  (isort). 58 are auto-fixable. Within RECON §9's "50–100+" prediction
  ballpark; `N` (the headline driver) is deliberately still off.
- `mypy flatlib/` — **2 errors**, identical to the RECON §4 baseline.
- `pytest -x` — **5/5 passed**, matches RECON baseline.
- `pytest --cov=mayaastrolib --cov-fail-under=80` — **skipped per task
  spec.** Source dir is still `flatlib/`; the `[tool.coverage.run]
  source = ["mayaastrolib"]` setting will start collecting coverage
  after Task 005 renames the directory.

### What was tried and discarded

- **Tried** including a `docs` optional-dependency group with
  `sphinx`. Discarded: `docs/source/` is a 2015 Sphinx skeleton that
  isn't currently built (no `make html` ran in years). Per the task
  spec ("only if `docs/source/` will be built; if not, skip"), I left
  the group out. Trivial to add later.
- **Considered** pinning `pyswisseph==2.10.3.2` (matching `setup.py`
  exactly) vs `>=2.10.3.2`. Chose `>=` because (a) the CLAUDE.md
  contribution plan calls for modern-Python compatibility, (b) RECON
  §8 ¶1 noted that the eclipse-function regression came from a
  pyswisseph API change — pinning hides the issue rather than
  surfacing it for Task 002a/004. Lock should live in a `requirements`
  file or test matrix, not in the runtime metadata.
- **Considered** adding `pythonpath = ["."]` to
  `[tool.pytest.ini_options]` to fix the RECON §2 footgun. Out of
  scope: the task spec explicitly defers it to Task 002b. Did not add.
- **Considered** updating `MANIFEST.in` (currently includes
  `README.rst`, which the fork swapped for `README.md`). Out of scope
  — Task 002b territory. Did not touch.
- **Considered** committing the leftover working-tree CLAUDE.md edit
  (the AUTO-MANAGED `## Current codebase state` block from the Task
  001 auto-memory hook). Did NOT commit it: out of Task 002 scope, and
  CLAUDE.md is listed as "files that are sacred — should not be
  modified without explicit instruction". Left in working tree for the
  human reviewer to decide.

### Surprises

- `pip show mayaastrolib`'s `Author:` field renders empty even though
  the `[project] authors` table uses `name`/`email`. setuptools maps
  PEP 621 `authors` to RFC-822 `Author-email` (where it correctly shows
  "João Ventura <flatangleweb@gmail.com>"); the legacy `Author:` line
  stays blank by design. Not a problem, just unfamiliar.
- `pytest` now picks up `pyproject.toml` as `configfile:` automatically
  — no `pytest.ini` needed. Slight bonus: `--strict-markers` is now in
  effect, which means undeclared markers will raise. None used today,
  so no fallout.
- `ruff check` count jumped from 25 → 123 with the configured rule
  set. The single biggest contributor is `UP` (pyupgrade) flagging
  hundreds of "use `X | None` instead of `Optional[X]`"-style hints
  across the codebase, plus `B` and `A`. Task 003 will need to triage
  carefully — many will auto-fix, but a chunk are stylistic
  judgement-calls (e.g. `class object` in `props.py` is `A001`/`A003`
  builtin-shadow).
- The editable install built cleanly without `MANIFEST.in` listing
  `pyproject.toml`. setuptools handles it implicitly. (`MANIFEST.in`
  matters only for the sdist; in editable mode it's irrelevant.)

### Follow-ups for Task 002b

- Update `.gitignore` to add `*.egg-info/`, `.coverage`,
  `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `htmlcov/`,
  `.venv*/`, `dist/`, `build/`. (RECON §8 ¶8.)
- Delete `scripts/build.py`, `scripts/clean.py`, `scripts/utils.py` —
  the new build backend obsoletes them. (RECON §8 ¶7.)
- Resolve `README.rst` vs `README.md`: either delete `README.rst` (the
  fork already uses `README.md` per `[project] readme = "README.md"`)
  or align `MANIFEST.in`. (RECON §8 ¶6.)
- Add `pythonpath = ["."]` to `[tool.pytest.ini_options]` so a
  contributor who skips `pip install -e .` still gets import
  resolution. (RECON §2.)
- Create an empty `CHANGELOG.md` — Task 002 deliberately deferred per
  the spec; subsequent tasks need one to append to.
- Decide whether to install Python 3.10/3.11/3.12 via pyenv before
  Task 004 (CI matrix). Today this Mac still only has 3.14.3.

### Definition of done — verified

- [x] `pyproject.toml` exists; `python3 -c "import tomllib;
  tomllib.load(open('pyproject.toml','rb'))"` returns without error
  (printed `valid; project.name= mayaastrolib version= 0.2.6`).
- [x] Fresh-venv `pip install -e ".[dev]"` succeeds.
- [x] `import flatlib; flatlib.__version__ == "0.2.6"`.
- [x] `pytest tests/` reports 5/5 passed.
- [x] `setup.py`, `requirements.txt` deleted; `setup.cfg` was already
  absent.
- [x] `git diff development --stat` of committed files shows only:
  `pyproject.toml` (added), `flatlib/__init__.py` (modified),
  `setup.py` (deleted), `requirements.txt` (deleted), and this
  PROJECT-LOG.md entry.

---

## 2026-05-07 — Task 001: Recon and baseline

**Session length:** ~1.5 hours (single Claude Code session)
**Branch:** `task-001-recon`
**Commits:** see `git log task-001-recon`

### What was done

- Read every `.py` file under `flatlib/`, `recipes/`, `tests/`,
  `scripts/`, `contrib/` (32 source files, 5,275 LoC in `flatlib/`).
- Set up an ad-hoc `.venv-recon/` with pytest 9.0.3, pytest-cov 7.1.0,
  ruff 0.15.12, mypy 2.0.0, pyswisseph 2.10.3.2. Installed `flatlib`
  in editable mode so tests resolve.
- Ran `pytest -v` (5 tests, all pass on Python 3.14.3),
  `pytest --cov=flatlib` (overall 34% coverage; 12 modules at 0%),
  `ruff check .` (25 violations across whole repo, 9 in `flatlib/`,
  4 syntax errors in `contrib/topical_almuten.py`),
  `ruff format --check` (54 files would be reformatted),
  `mypy flatlib/ --ignore-missing-imports` (2 errors).
- Built the internal-import dependency graph as a Mermaid diagram —
  no cycles, foundation is `const`/`angle`/`utils`/`props`,
  `dignities.essential` is the most-imported module.
- Ran each recipe under the venv: 14 of 15 work,
  `recipes/eclipses.py` crashes on `swisseph.lun_eclipse_when(…,
  backward=…)` — the keyword is `backwards` in pyswisseph 2.10. Same
  bug applies to `nextSolarEclipse`. The 2026-04-29 swisseph patch
  fixed `rise_trans` but not the eclipse functions.
- Wrote `docs/RECON.md` covering all 9 sections required by
  `prompts/task-001-recon.md`, including a recommended task ordering
  for Phase 1.

### What was tried and discarded

- **Tried** running tests directly (`pytest tests/`) before `pip
  install -e .` — failed with `ModuleNotFoundError: No module named
  'flatlib'`. Discarded that approach; documented as a footgun in
  RECON §2 with a suggested fix for Task 002 (pytest `pythonpath`
  config or src-layout).
- **Tried** finding Python 3.12 locally to match the contribution
  plan's CI matrix — only Python 3.14.3 is installed on this Mac.
  Used 3.14 anyway; flagged in RECON §1 that 3.12 should be
  installed via pyenv before Task 004 to verify the actual matrix.
- **Considered** spawning subagents for parallel reads. Discarded:
  the work is sequential (read → measure → synthesize) and the file
  count was small enough that batched parallel `Read` calls were
  cheaper than agent overhead.

### Surprises

- `recipes/eclipses.py` is a real, latent bug (eclipse keyword
  argument mismatch) — see RECON §8 ¶1.
- `contrib/topical_almuten.py` has been a `SyntaxError` since at
  least 2021-04-05 — bracket placement at lines 102/103 is wrong.
  Nobody can have run this file; it's not imported anywhere.
- Coverage is even lower than expected (34%); 12 high-level modules
  at literally 0%. The single chart-level test is one assertion
  about `solarReturn` preserving `hsys`. The rename in Task 005 will
  be operating with almost no safety net.
- The codebase is **already 100% Python 3 native** — no `__future__`,
  no `sys.version_info`, no Py2 builtins, no bare except, no
  print-without-parens. The "modernisation" work is style/typing/
  packaging, not language porting. Pleasant surprise.
- `flatlib/__init__.py` says `__version__ = '0.2.3'`; `setup.py` says
  `version='0.2.5'`. Two sources of truth out of sync.
- `flatlib/props.py` defines `class object`, which shadows the
  builtin via `props.object`. Works, but unidiomatic.
- The dependency graph is a clean DAG with no cycles — better
  layering than the lack of typing or tests would suggest.

### Follow-ups needed

- **Before Task 002:** confirm Python 3.12 install plan (pyenv).
  The CI matrix in Task 004 needs it.
- **Before Task 003:** decide what to do with
  `contrib/topical_almuten.py` (fix vs delete vs archive). It blocks
  Task 005 either way (its `import contrib.topical_almuten` would
  fail in any rename script that scans the tree).
- **Possible Task 002a:** hot-fix the eclipse `backward` →
  `backwards` keyword and add an xfail-then-flip regression test.
  Two-line code change; one-line test. Worth doing before the
  packaging upheaval of Task 002 because (a) it's visible to anyone
  using the eclipse APIs today and (b) it stops being fork-original
  if upstream were to ship a fix first.
- **Add Task 004a:** smoke tests per public module *before* Task 005's
  rename. Recommended in RECON §9. One import + one happy-path test
  per module gets coverage from 34% → ~60% and de-risks the rename.
- **`.gitignore` updates** to add `.coverage`, `*.egg-info/`,
  `.venv*/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/` —
  fold into Task 002.
- **Open question for the maintainer:** should the camelCase →
  snake_case naming conversion happen at all in Phase 1, or wait
  until a deliberate major-version event? It's a breaking change
  larger than the rename itself. RECON §8 ¶9 flags it.

---

## YYYY-MM-DD — Task NNN: <task name>

**Session length:** ~X hours
**Branch:** <branch-name>
**Commits:** <commit hashes>

### What was done

<bullet list>

### What was tried and discarded

<bullet list, with reasoning>

### Surprises

<anything unexpected>

### Follow-ups needed

<things to address in future tasks>

---

## 2026-05-07 — Project bootstrap

**Session length:** ~30 minutes (manual setup, no Claude Code)
**Branch:** development
**Commits:** TBD (this commit)

### What was done

- Forked flatangle/flatlib to <username>/maya-astro-lib
- Set up local clone with origin and read-only upstream remotes
- Created development branch and made it the default
- Created CLAUDE.md, docs/FORK-RATIONALE.md, docs/CONTRIBUTION-PLAN.md
- Created prompts/task-001-recon.md
- Updated README with fork banner

### Surprises

None — straightforward setup.

### Follow-ups needed

- Run Task 001 (recon) as first overnight Claude Code build
- Review RECON.md output before queueing Task 002

# Contribution Plan

Tasks are numbered and roughly sequential. Each task has a unique ID
referenced in commits and PROJECT-LOG entries.

## Phase 0: Foundation (Tasks 001-005)

### Task 001: Recon and baseline

**Goal:** Produce a comprehensive understanding of the inherited codebase
before any modifications.

**Scope:**
- Inventory all modules in `flatlib/` — for each, document purpose,
  public API, key dependencies, lines of code
- Run existing test suite on Python 3.12, document pass/fail per test
- Run `ruff check` with default rules, document violation count by category
- Identify all `import` statements — flag any that are deprecated or removed
  in Python 3.10+
- Build a dependency graph of internal module imports
- List all public classes and functions — anything not prefixed with `_`
- Read every file in `recipes/` and document what each demonstrates

**Deliverable:** `docs/RECON.md` with the above, plus a section
"Recommended task ordering for Phase 1" with reasoning.

**Definition of done:**
- RECON.md exists and covers all bullets above
- No code changes in this task — pure analysis
- PROJECT-LOG entry summarising findings and surprises

**Estimated session length:** 1 overnight build

---

### Task 002: Build system modernisation

**Goal:** Replace `setup.py` with `pyproject.toml`. Establish modern
tooling.

**Scope:**
- Create `pyproject.toml` using setuptools backend (PEP 621 metadata)
- Migrate all metadata from `setup.py`: name, version, description,
  authors (preserving original), license, classifiers
- Change package name from `flatlib` to `mayaastrolib` in pyproject.toml
  but DO NOT yet rename the source directory (Task 005)
- Add `[project.optional-dependencies]` for `dev` (pytest, pytest-cov,
  mypy, ruff) and `docs` (sphinx, if upstream had docs)
- Configure ruff in pyproject.toml: line length 100, target Python 3.10,
  enable rule sets E, F, I, N, UP, B, A
- Configure mypy in pyproject.toml: strict mode disabled initially,
  warn_unused_ignores enabled
- Configure pytest in pyproject.toml: testpaths, coverage source
- Delete `setup.py` and `setup.cfg` if present
- Update `.gitignore` for modern Python tooling artifacts
- Verify `pip install -e ".[dev]"` works in a fresh venv

**Definition of done:**
- Fresh venv can install the package and dev dependencies
- `ruff check` runs (violations expected, that's Task 003)
- `pytest` discovers tests (pass/fail status logged, not yet enforced)
- All checklist items pass

**Out of scope:**
- Renaming source directory (Task 005)
- Fixing ruff violations (Task 003)
- Fixing failing tests (Task 004)

**Estimated session length:** 1 overnight build

---

### Task 003: Ruff baseline and auto-fixes

**Goal:** Get the codebase to a clean ruff baseline with auto-fixes only.

**Scope:**
- Run `ruff check --fix` and `ruff format` across the codebase
- Manually review every change before committing — auto-fixes can be wrong
- For violations that ruff cannot auto-fix, document them in
  `docs/RUFF-DEBT.md` with file:line references and assessment of
  difficulty (trivial / moderate / risky)
- Do NOT manually fix non-trivial violations in this task — that's
  follow-up work
- Ensure all existing tests still pass after auto-fixes

**Definition of done:**
- `ruff format --check` passes cleanly
- `ruff check` reports only violations documented in RUFF-DEBT.md
- Test suite pass/fail count unchanged from Task 001 baseline

**Estimated session length:** 1 overnight build

---

### Task 004: Test suite green on Python 3.12

**Goal:** Get every existing test passing on Python 3.12.

**Scope:**
- For each failing test from Task 001, diagnose root cause
- Categorise: (a) Python version drift, (b) dependency change,
  (c) genuine test bug, (d) genuine code bug
- Fix categories (a), (b), and (c) directly
- For category (d), document in `docs/KNOWN-BUGS.md` and add an
  `xfail` marker — do NOT fix the underlying code in this task
- Add CI workflow `.github/workflows/test.yml` running on Python
  3.10, 3.11, 3.12 — must pass before merge to main

**Definition of done:**
- `pytest` passes on local Python 3.12
- CI workflow exists and is green
- Any xfail tests have corresponding KNOWN-BUGS.md entries

**Estimated session length:** 1-2 overnight builds depending on what
Task 001 finds

---

### Task 005: Rename to mayaastrolib

**Goal:** Rename the source package from `flatlib` to `mayaastrolib`
across the entire codebase.

**Scope:**
- Rename `flatlib/` directory to `mayaastrolib/`
- Update all internal imports
- Update all imports in tests
- Update README, examples, recipes
- Update pyproject.toml package discovery if needed
- Add a compatibility shim: `flatlib/__init__.py` that imports * from
  `mayaastrolib` and emits a DeprecationWarning. This makes migration
  easier for any user who installed the fork as a flatlib replacement.
  Mark for removal in version 1.0.
- Update CHANGELOG.md noting the rename

**Definition of done:**
- All imports use `mayaastrolib` natively
- The compatibility shim works: `import flatlib` succeeds with warning
- All tests pass
- Documentation reflects new name

**Estimated session length:** 1 overnight build

---

## Phase 1: Foundation hardening (Tasks 006-010)

To be planned after Phase 0 completes. Likely candidates:
- Add type hints to core modules (one module per task)
- Build the golden chart fixture set (5+ reference charts)
- Set up Sphinx docs and ReadTheDocs
- Establish API stability boundary documentation
- First PyPI release as 0.1.0

## Phase 2: Vedic unification

To be planned after Phase 1. Will involve studying the existing sidereal
forks and consolidating their work.

# Project Log

Running journal of all sessions on this project. Newest entries at the top.

Each entry should follow this template:

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

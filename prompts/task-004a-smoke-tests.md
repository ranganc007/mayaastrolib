# Task 004a: Smoke Tests for Public-API Modules

## Context

You are working in the `mayaastrolib` repository. Before doing anything:

1. Read `CLAUDE.md` in full.
2. Read `docs/RECON.md` — specifically §1 (module inventory), §2 (test coverage), and §9 (this task is recommended in the "Tasks I'd consider adding" subsection).
3. Read `docs/PROJECT-LOG.md` for entries from Tasks 002, 002b, 003, 004.
4. Confirm Task 004 has been merged to `development`:

   ```
   git log --oneline development -5
   ```

   You should see Task 004's commits at the top:
   - The CI workflow, eclipse fix, eclipse tests, KNOWN-BUGS

   If Task 004's commits are not present, STOP. Append a note to PROJECT-LOG.md and exit.

## Why this task exists

The recon found that 12 high-level modules are at literally 0% test coverage:
- `flatlib/dignities/accidental.py`
- `flatlib/dignities/essential.py`
- `flatlib/dignities/tables.py`
- `flatlib/predictives/primarydirections.py`
- `flatlib/predictives/profections.py`
- `flatlib/predictives/returns.py`
- `flatlib/protocols/almutem.py`
- `flatlib/protocols/behavior.py`
- `flatlib/protocols/temperament.py`
- `flatlib/tools/arabicparts.py`
- `flatlib/tools/chartdynamics.py`
- `flatlib/tools/planetarytime.py`

Task 005 (rename `flatlib` → `mayaastrolib`) will touch every import in every file. Renaming with no test safety net is risky. This task adds enough coverage to catch the obvious failure modes before the rename.

The goal is NOT comprehensive coverage. Goal: each module has at least one test that imports it and exercises its main public function. Coverage target: get from current ~34% to ~60%.

## Task scope

For each of the 12 modules listed above, add tests in a new file `tests/test_<module>.py`. Each test file should:

1. **Import test:** assert the module imports without error
2. **Happy-path test:** call the main public function with valid inputs and assert the output has the expected shape (type, length, presence of expected keys/attributes)

Reference the recipes in `recipes/` for known-good usage patterns. The recipes were validated in the recon to mostly run on Python 3.14, so they're a reliable source of valid inputs.

Do NOT assert specific astronomical values. That's golden-chart-fixture work for Phase 1. The point here is "the function returns *something*, and it has the *right shape*", not "the value is correct to N arcminutes".

### Per-module guidance

For each module, here's the suggested test pattern. Adapt as needed based on what the module actually exports.

#### `tests/test_dignities_essential.py`

```python
import unittest
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const
from flatlib.dignities import essential


class EssentialDignityTests(unittest.TestCase):
    def setUp(self):
        date = Datetime("2015/03/13", "17:00", "+00:00")
        pos = GeoPos("38n32", "8w54")
        self.chart = Chart(date, pos)
        self.sun = self.chart.get(const.SUN)

    def test_module_imports(self):
        self.assertIsNotNone(essential)

    def test_score_returns_int(self):
        score = essential.score(self.sun)
        self.assertIsInstance(score, int)

    def test_get_info_returns_essential_info(self):
        info = essential.getInfo(self.sun.id, self.sun.signlon)
        # EssentialInfo has 'ruler', 'exalt', 'triplicity', etc.
        self.assertIsNotNone(info)
```

#### `tests/test_dignities_accidental.py`

Reference: `recipes/accidentaldignities.py`. Test that `AccidentalDignity(chart, planet)` returns an object with the documented properties.

#### `tests/test_dignities_tables.py`

Tables module is mostly static data. Test that the constants exist and have the expected types (lists/dicts with non-zero length).

#### `tests/test_predictives_profections.py`

Reference: `recipes/profections.py`. Test that `compute(chart, years)` returns a chart-like object.

#### `tests/test_predictives_returns.py`

Reference: `recipes/solarreturn.py`. Test that `nextSolarReturn(chart, date)` returns a Chart.

#### `tests/test_predictives_primarydirections.py`

Reference: `recipes/primarydirections.py`. Test that `PrimaryDirections(chart)` constructs and `PDTable` returns a list-like.

#### `tests/test_protocols_almutem.py`

Reference: `recipes/almutem.py`. Test that `compute(chart)` returns a dict/object with planet keys.

#### `tests/test_protocols_behavior.py`

Reference: `recipes/behavior.py`. Test that `compute(chart)` returns without crashing.

#### `tests/test_protocols_temperament.py`

Reference: `recipes/temperament.py`. Test that `Temperament(chart)` constructs and has score-like attributes.

#### `tests/test_tools_arabicparts.py`

Reference: `recipes/arabicparts.py`. Test that `getPart(PARS_FORTUNA, chart)` returns a GenericObject.

#### `tests/test_tools_chartdynamics.py`

Reference: `recipes/chartdynamics.py`. Test that `ChartDynamics(chart)` constructs and exposes documented methods.

#### `tests/test_tools_planetarytime.py`

Reference: `recipes/planetarytime.py`. Test that `getHourTable(date, pos)` returns an HourTable.

## Special handling

Some recipes pass complete arguments. Some need additional inputs the recipe doesn't show. Use the recon's RECON.md §1 module inventory to identify what each public function expects.

If a public function genuinely cannot be tested without significant setup (e.g. requires a specific kind of chart or pre-computed state), write the import-only test and document in the test file's docstring why happy-path testing was deferred. Note this in the session log.

If a test reveals a genuine bug — i.e. the function crashes or returns nonsense — DO NOT fix the bug in this task. Mark the test as `@unittest.expectedFailure` or use `pytest.mark.xfail` with a clear reason, document in `KNOWN-BUGS.md`, and move on. Bug fixes are separate tasks.

## Verification

```
python3 -m venv .venv-task004a
.venv-task004a/bin/pip install -e ".[dev]"
.venv-task004a/bin/pytest tests/ -v
.venv-task004a/bin/pytest tests/ --cov=flatlib --cov-report=term-missing
```

Expected: ~33 tests passing (9 from before + ~24 new), coverage at ~55-65%.

If coverage didn't improve much, the smoke tests aren't actually exercising the modules. Investigate.

## Out of scope

- Bug fixes (mark as xfail, defer)
- Adding new functionality
- Type hints (Phase 1)
- Renaming (Task 005)
- Golden-chart correctness tests (Phase 1)

## Process

1. Create branch:

   ```
   git checkout development
   git pull origin development
   git checkout -b task-004a-smoke-tests
   ```

2. Commit per module so review is easy. Suggested commits:
   - `test: add smoke tests for dignities modules`
   - `test: add smoke tests for predictives modules`
   - `test: add smoke tests for protocols modules`
   - `test: add smoke tests for tools modules`
   - `docs: update KNOWN-BUGS.md with any new xfails`

3. Update `CHANGELOG.md` `[Unreleased]` `### Added` section noting the smoke test coverage.

4. Pre-completion checklist:
   - `ruff format --check .` passes (test files must be formatted)
   - `ruff check .` passes
   - `pytest -x` passes (33+ tests, all green or properly xfailed)
   - Coverage report shows substantial improvement from baseline

5. PROJECT-LOG.md entry must include:
   - Final test count
   - Final coverage percentage with comparison to baseline (34%)
   - List of any xfails added with KNOWN-BUGS.md references
   - List of any modules where happy-path testing was skipped, with reasons

6. Push:

   ```
   git push -u origin task-004a-smoke-tests
   ```

7. Verify CI is green on the new branch. The CI workflow from Task 004 runs on push.

8. DO NOT merge. Leave for human review.

## Definition of done

- 12 new test files exist, one per uncovered module
- Each test file has at minimum: 1 import test + 1 happy-path test (or 1 import test + xfail with documentation)
- All tests pass OR are properly marked xfail
- Coverage improved from ~34% to ≥55%
- CI green on the branch
- PROJECT-LOG.md updated with concrete numbers
- CHANGELOG.md updated

## If something goes wrong

If multiple modules turn out to be hard to smoke-test (e.g. require extensive fixture setup):

1. Do as many as you can with high confidence
2. For the rest, write only the import test and document in PROJECT-LOG.md why the happy-path test was deferred
3. Don't fake it — empty test functions or trivially-passing assertions do more harm than good

If a smoke test reveals widespread bugs in an uncovered module (more than 2 tests xfail per module):

1. Stop adding tests to that module
2. Document the discovery in PROJECT-LOG.md and KNOWN-BUGS.md
3. Surface for human review before continuing — this might warrant a dedicated bug-fix task before Task 005 proceeds

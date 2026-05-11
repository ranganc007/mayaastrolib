# Task 012: Investigate Items 15 and 16

## Context

You are working in the `mayaastrolib` repository. Before doing anything:

1. Read `CLAUDE.md` in full.
2. Read `mayaastrolib/object.py` end to end. Pay particular attention to:
   - The `House` class
   - Any class-level constant like `_OFFSET` or similar magic numbers
   - The `inHouse()` and `hasObject()` methods
3. Read `mayaastrolib/predictives/returns.py` end to end. Look at `solarReturn()` (and `lunarReturn()` if present). Understand what `year` means as an argument.
4. Read `docs/PROJECT-LOG.md` for entries from Tasks 006-011.
5. Read `docs/IDEAS.md` to understand the deferral pattern (where audit items get parked when they need design rather than mechanical fixes).
6. Confirm Task 011 is on `development`:

   ```
   git log --oneline development -5
   ```

   Should show Task 011 commits (chart dispatch and house num cleanup).

## Why this task exists

Two audit items need investigation before they can be fixed:

**Item 15 — `House._OFFSET = -5.0` magic number.**

There's a class constant in `House` controlling some offset behaviour. The audit notes "no comment beyond 'traditional house offset'", and that it affects `inHouse()` and `hasObject()`. Without understanding what this constant *means* astrologically, we can't decide whether the fix is:
- Document it (it's correct as-is, just undocumented)
- Make it configurable (it's a defensible default but should be a parameter)
- Remove it (it's wrong code from the upstream)
- Leave alone with a TODO for Phase 2 (it's complex enough to deserve its own task)

**Item 16 — `solarReturn(year)` semantics.**

The audit notes: "Solar return for year N" should arguably mean "Nth birthday return" but currently means "first sun-conjunct-natal-sun moment in calendar year N". The two interpretations differ depending on whether the person's birthday falls before or after January 1.

The audit may be slightly wrong about how this manifests. The actual code might already do what consumers expect, or might differ subtly. Need to read it before pronouncing a fix.

## Task scope

This task is **investigation-first**. The output is a document, not necessarily code changes. If — and only if — the findings produce an unambiguous fix that's small and uncontroversial, also apply that fix. Otherwise defer to IDEAS.md and stop.

### Part 1: Investigate Item 15 (`House._OFFSET`)

Read every reference to the offset in the codebase:

```bash
grep -rn "_OFFSET\|inHouse\|hasObject" mayaastrolib/ --include="*.py"
```

Trace the math. Specifically answer:

1. **What is the literal value?** (Likely `-5.0` per audit, but verify.)
2. **Where is it used?** Likely in `inHouse(lon)` checking whether a longitude falls in a house's span.
3. **What does the math look like?** Pseudocode: how does the offset transform the comparison? E.g. is it shifting the house cusp boundaries by 5°? Is it widening the house's lower or upper bound?
4. **What astrological convention does this implement?** Two strong candidates:
   - **Traditional rule:** "A planet within 5° of the next house cusp counts as being in that next house." (Common in Hellenistic and Medieval astrology.)
   - **Whole-sign vs Placidus boundary handling:** Adjusting where house boundaries fall relative to cusps in different house systems.
   If it's neither of those, what is it?
5. **Is the value used unconditionally, or only with certain house systems?** If the latter, that's a strong clue about its meaning.

Document findings in a new file `docs/AUDIT-INVESTIGATIONS.md`:

```markdown
# Audit Investigations

Outputs of investigation tasks for audit items that needed code-reading
before a fix could be scoped. Each entry follows: what was found, what
the code actually does, what the right fix is.

---

## Item 15 — House._OFFSET = -5.0

**Investigated in Task 012.**

### Where it's used

[file:line references and pseudocode of the math]

### What it appears to mean

[best understanding after reading the code]

### Recommended action

One of:
- **DOCUMENT.** The code is correct; it just needs a docstring and named
  constant explaining the convention. Apply in this task.
- **PARAMETERISE.** The value is a defensible default but should be
  configurable. Add a parameter to Chart() or House().
- **DEFERRED.** Meaning unclear, fix unclear, more research needed.
  Tracked in IDEAS.md.
```

### Part 2: Investigate Item 16 (`solarReturn(year)`)

Read `mayaastrolib/predictives/returns.py` and trace exactly what `solarReturn(year=N)` does. Specifically answer:

1. **What is `year` in the signature?** A calendar year (2025) or an age (42)? The audit assumes calendar year.
2. **What is the search starting point?** January 1 of year N? Birthday in year N? Some other anchor?
3. **What is the search direction?** Forward only? Forward-or-backward?
4. **What happens at year-boundary edge cases?** If someone is born December 30, 1980 and asks for `solarReturn(year=2022)`:
   - Does it return the late-December 2021 event (the 2021-2022 transition)?
   - The late-December 2022 event (the 2022-2023 transition)?
   - Something else?
5. **Is the existing behaviour actually wrong?** The audit's reading is one interpretation. Read the docstring (if any) and any tests. The behaviour might be defensible-as-is, or might match user expectations in most realistic cases.

Test it concretely. Pick a date with known characteristics:

```python
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.predictives import returns

# Person born June 15, 1980 (mid-year birthday — easy case)
natal = Chart(
    Datetime("1980/06/15", "12:00", "+00:00"),
    GeoPos("38n32", "8w54"),
)
sr_2022 = returns.solarReturn(natal, 2022)
print("June 1980 birth, year 2022 returns:", sr_2022.date)
# Expected: late June 2022 (around the 42nd birthday)

# Person born December 15, 1980 (late-year birthday — edge case)
natal_dec = Chart(
    Datetime("1980/12/15", "12:00", "+00:00"),
    GeoPos("38n32", "8w54"),
)
sr_dec_2022 = returns.solarReturn(natal_dec, 2022)
print("Dec 1980 birth, year 2022 returns:", sr_dec_2022.date)
# Audit's claim: this returns Dec 2022 (which IS the 42nd birthday — math aligns)
# Or possibly: this returns Dec 2021 (which would be the 41st birthday — bug)
```

Run this manually or as a temporary script. Capture the actual outputs.

Document findings in `docs/AUDIT-INVESTIGATIONS.md`:

```markdown
## Item 16 — solarReturn(year) semantics

**Investigated in Task 012.**

### Current behaviour (verified by running)

[exact behaviour with concrete date examples]

### Does it match user expectations?

[honest assessment — yes / no / mostly / depends]

### Recommended action

One of:
- **NO ACTION.** Behaviour is fine; the audit's concern doesn't manifest
  in practice. Document the semantics clearly in the docstring.
- **DOCUMENT WITH WARNING.** Behaviour is defensible but surprising in
  edge cases. Add a docstring explaining and a code example.
- **ADD ALTERNATE API.** Add `solarReturnByAge(years_after_birth=N)` or
  `solarReturn(birthday_number=N)` to disambiguate, keeping the existing
  function unchanged.
- **DEFERRED.** Behaviour is wrong but the right semantic is unclear
  enough to need its own task. Track in IDEAS.md.
```

### Part 3: Apply unambiguous fixes only

After both investigations are documented, decide what to fix in this task vs defer.

**Fix in this task if:**
- The recommended action is "DOCUMENT" or "DOCUMENT WITH WARNING" (pure docstring/comment additions)
- The recommended action is "PARAMETERISE" AND the parameter has an obvious sensible default AND the change is < 30 lines
- The recommended action is "ADD ALTERNATE API" AND the new function is < 50 lines AND doesn't require design decisions

**Defer to IDEAS.md if:**
- The investigation surfaced ambiguity that needs human design input
- The fix would require changing multiple files or affect public API
- The findings contradict the audit's framing in unexpected ways (warrants discussion before code)

If deferring, write to `docs/IDEAS.md`:

```markdown
## Item 15 / Item 16 — [investigated, deferred]

**Status:** Investigated in Task 012, deferred for design.
**See:** `docs/AUDIT-INVESTIGATIONS.md` for findings.

[2-3 sentences summarising what's open]
```

If fixing, do the minimal change. Don't expand scope. The point is to close the audit cleanly, not to redesign anything.

### Part 4: Tests (only if Part 3 produced code changes)

If Part 3 added documentation only: no tests needed.
If Part 3 parameterised something: add a test verifying the parameter works and the default is unchanged.
If Part 3 added a new API: test the new API; verify the old one is unchanged.

## Out of scope

- Changing `inHouse()` / `hasObject()` math itself (that would be a behaviour change requiring its own task)
- Changing solar return search algorithm (same)
- Item 17 (predictives as chart methods — Task 013)
- Any new functionality

## Process

1. Branch:

   ```
   git checkout development
   git pull origin development
   git checkout -b task-012-audit-investigations
   ```

2. Suggested commits:
   - `docs: add AUDIT-INVESTIGATIONS.md with Item 15 findings`
   - `docs: add Item 16 findings to AUDIT-INVESTIGATIONS.md`
   - One of:
     - `docs: document House._OFFSET in code` (DOCUMENT outcome)
     - `feat: parameterise [whatever] in House` (PARAMETERISE outcome)
     - `feat: add solarReturnByAge alongside solarReturn` (ADD ALTERNATE API outcome)
     - `docs: defer Items 15 and 16 to IDEAS.md` (DEFER outcome)
   - `test: cover [new behaviour]` (only if Part 3 produced code changes)
   - `docs: update CHANGELOG and IDEAS for Task 012`

3. Pre-completion checklist:
   - `ruff format --check .` passes
   - `ruff check .` passes
   - `mypy mayaastrolib/` — no new errors
   - `pytest -x` passes — all tests still green

4. PROJECT-LOG.md entry must include:
   - Verbatim copy of the recommended action for each item
   - The actual concrete output from running the solar return test cases (Part 2 step 5)
   - Whether anything was fixed in this task or deferred
   - If deferred, brief note on what design questions are open

5. Push:

   ```
   git push -u origin task-012-audit-investigations
   ```

6. Verify CI green.

7. DO NOT merge. Leave for human review.

## Definition of done

- `docs/AUDIT-INVESTIGATIONS.md` exists and covers both Item 15 and Item 16
- For each item, the investigation is concrete (file:line refs, real output, real test cases)
- A clear recommended action is stated for each item
- If the action was "fix": the fix is applied, tested, and minimal in scope
- If the action was "defer": IDEAS.md has an entry tracking the open question
- All existing tests still pass
- CI green

## If something goes wrong

The most likely failure mode here is over-reach. Investigation tasks tempt you (or Claude Code) to "while we're in there, also fix..." Resist this. The point is to investigate and document, then apply only the minimum unambiguous fix.

If the investigation reveals something genuinely concerning — e.g. the `_OFFSET` math is actually wrong, not just undocumented — STOP. Document the finding loudly in PROJECT-LOG.md and IDEAS.md. Do not "just fix it" mid-task. That's a separate task with its own design conversation.

If the investigation can't reach a conclusion (the code is too tangled, the references are too sparse, the math is over your head), that's also a valid outcome. Document what you tried, what you couldn't determine, and defer.

A good investigation that defers cleanly is far more valuable than a hasty fix that creates regressions.

If something fundamental breaks during the optional fix phase:

1. `git reset --hard development`
2. The investigation document survives in your local clone — you can re-commit just the docs as a separate branch
3. Failure report in PROJECT-LOG.md
4. Push the docs-only commit and stop

The investigation findings are valuable on their own, even without a fix.

# Re-Review of mayaastrolib (post-Task 016)

## Context

The platform review at `docs/REVIEW-2026-05-08.md` was conducted at commit `a5bcc92` (post-Task 013). Since then, five things have shipped:

- Task 014: Golden test fixtures (Skyfield-anchored) and self-consistency suite
- Task 015: GeoPos input validation
- Task 016: fixstar_mag caching
- The platform review document itself (with cleanup pass)
- LICENSING.md at repo root

This task produces a fresh review of the codebase at its current state, primarily to confirm that the previous review's findings have actually been closed (and to surface any new findings introduced since).

The user is preparing to start Phase 2 (Vedic / sidereal work) and wants a clear, current picture of the codebase before that starts. Phase 2 will introduce significant new design surface, so going in with a clean slate matters.

## Why this isn't just "run review-full again"

Two reasons this is structured as a re-review rather than a from-scratch audit:

1. **Closure tracking is the primary value.** The previous review made specific claims ("GeoPos doesn't validate input", "tests/golden/ doesn't exist", "fixstar_mag is slow"). Each one can be checked yes/no. A fresh review that ignores the previous one would re-discover some of these and miss the closure narrative entirely.

2. **The previous review was good.** Its calibration was about right — actionable findings, honest deferrals, no alarmism. We don't need to throw it out and start over; we need to update it for the current state.

So this task **builds on** the previous review rather than replacing it. The output is a new document that references the old one explicitly.

## Task scope

### Part 1: Read the previous review carefully

Before any new analysis:

1. Read `docs/REVIEW-2026-05-08.md` end to end. Note specifically:
   - Each finding's specific claim (with file:line references)
   - The recommended actions
   - The "Suggested Next Tasks" list (014, 015, 016)
   - The "Future considerations" list (deferred items)
2. Read `docs/AUDIT-INVESTIGATIONS.md` — context on Items 15 and 16 from the deeper audit, which were deferred.
3. Read `docs/IDEAS.md` end to end — explicit deferral parking lot.
4. Read `docs/PROJECT-LOG.md` entries for Tasks 014-016. Confirm the work that shipped matches what the review proposed.

### Part 2: Closure tracking

For every numbered finding in the previous review, produce a status: **Closed**, **Deferred (intentionally)**, **Open (still pending)**, or **Wrong (review was inaccurate)**.

Specifically check:

**Code quality findings (was previous Section 3):**
- File-size hotspots (accidental.py, chart.py, object.py): unchanged or addressed?
- Complexity hotspot `getScoreProperties`: still 88 LOC sequential dict assembly?
- camelCase inheritance: still ~175:2 ratio? Still tracked in IDEAS.md as 1.0 sweep?
- Coverage gaps: did Task 015 close the geopos.py gap as predicted (69% → 90%+)?
- Dead-code candidates: still all deprecated paths slated for 1.0 removal?

**Performance findings (was previous Section 4):**
- Chart construction baseline (~0.124ms): re-measure on current code, has it drifted?
- 33 calc_ut calls in default Chart (Pars Fortuna + Syzygy overhead): unchanged?
- fixstar_mag inefficiency: closed by Task 016?
- profections.compute allocation: unchanged?
- _DualAccess wrapper allocation: unchanged?

**Reliability/test findings (was previous Section 5):**
- tests/golden/ existence: closed by Task 014?
- GeoPos validation: closed by Task 015?
- Coverage on chart.py / temperament.py / accidental.py: shifted?

**Security findings (was previous Section 6):**
- GeoPos input validation: closed?
- Datetime parsing: still relies on stdlib failure paths?
- Chart constructor: still no semantic checks?

For each, produce a short status line. Example:

```
Item: "GeoPos accepts out-of-range latitudes silently" (was Sec 5, line 142)
Status: CLOSED — Task 015. Verified at geopos.py:34-42 with raise ValueError
        when lat ∉ [-90, 90] or lon ∉ [-180, 180]. Tests at
        tests/test_geopos_validation.py cover boundaries and out-of-range cases.
```

If the closure is genuine but partial (e.g. validation added but only for one input format), say so explicitly. Don't claim closure that isn't there.

### Part 3: New findings since 2026-05-08

After closure tracking, do a fresh pass for findings that didn't exist or weren't surfaced last time. Specifically check:

**Has the recent work introduced new debt?**
- Task 014 added Skyfield as a dev dep — any complications? Is `tests/golden/` properly isolated from CI?
- Task 014 added LICENSING.md — does it accurately reflect current state?
- Task 015 GeoPos validation — does it correctly handle all input formats `GeoPos.__init__` accepts? Numeric lat/lon as well as string?
- Task 016 fixstar_mag cache — does the cache cover all call sites? Any other functions in `swe.py` with the same per-call-parsing pattern?

**Has Phase 2 readiness changed?**
- Are there clear architectural seams where ayanamsa would be added?
- Does `LIST_VEDIC_DEFAULT` (added in Task 009) currently produce sensible output, or is it placeholder?
- Are there places in the code where "tropical" is hardcoded as an assumption?

**Anything else found by fresh inspection?**

Use the same review-full skill if it adds value. Don't run skills that won't help. Trust your own grep-and-read judgment for closure tracking; reach for skills for fresh-finding work.

### Part 4: Compare to Phase 2 readiness

This is the part that's specific to "we're about to start Phase 2."

For each major area mayaastrolib has work in (Chart, Object, Aspect, predictives, dignities, ephem layer), assess:

**Phase 2 readiness:**
- Is the API surface stable enough that adding sidereal mode won't require breaking changes?
- Are there decisions made in earlier tasks (e.g. symbolic chart machinery from Task 010) that constrain Phase 2 design space, helpfully or unhelpfully?
- Where would ayanamsa actually plug in? Is the seam obvious or requires invention?

This isn't asking "is Phase 2 designed yet" (it isn't, deliberately). It's asking "if we started Phase 2 design tomorrow, what would the codebase already constrain or enable?"

### Part 5: Produce the output document

Write `docs/REVIEW-2026-05-08-followup.md`. Filename intentionally short and dated, references the parent review.

Structure:

```markdown
# Re-Review of mayaastrolib (post-Task 016)

**Parent review:** `docs/REVIEW-2026-05-08.md` (commit a5bcc92, post-Task 013)
**This review at:** [current commit hash]
**Tasks shipped between reviews:** 014, 015, 016

## Executive summary

[2-4 bullets: what closed, what's still open, what's new, Phase 2 readiness verdict]

## Closure tracking

[Each previous finding with status — CLOSED / DEFERRED / OPEN / WRONG — with file:line evidence]

## New findings since 2026-05-08

[Anything surfaced by fresh inspection that wasn't in the previous review.
If nothing new, say so explicitly.]

## Phase 2 readiness

[Per-module assessment: how easily does this codebase accommodate the
addition of sidereal/Vedic features?]

## Suggested next moves

[At most 3 concrete suggestions. Could be:
- "Phase 2 can start" (with caveats)
- "These N items should close before Phase 2"
- "Reconsider X based on what's been learned"
Anything beyond 3 goes to a "Future considerations" section.]
```

Aim for 200-350 lines. Shorter than the original review because closure tracking is mechanical and shouldn't require commentary, and because new findings should be sparse if the work has been good.

## Process

1. **Branch:**

   ```
   git checkout development
   git pull origin development
   git checkout -b task-followup-review
   ```

   (Note: this isn't a numbered task in the contribution plan — it's a meta-review like the original. No `task-NNN` prefix.)

2. **No code changes.** Pure analysis and documentation.

3. **Suggested commits:**
   - `docs: add re-review post-Task 016 with closure tracking`
   - `docs: update PROJECT-LOG with re-review entry`

4. **Verification:**
   - `wc -l docs/REVIEW-2026-05-08-followup.md` — should be 200-350 lines
   - Spot-check 3-5 file:line references to confirm they resolve
   - No tests/lint apply to docs

5. **Append a brief PROJECT-LOG.md entry:**

   > **2026-MM-DD — Re-review (post-Task 016)**
   >
   > Closure-tracking review against `docs/REVIEW-2026-05-08.md`. Confirmed [N] findings closed, [M] deferred (in IDEAS.md), [K] still pending. Surfaced [J] new findings (or none). Phase 2 readiness verdict: [start now / address these first / reconsider].

6. **Push:**

   ```
   git push -u origin task-followup-review
   ```

7. **DO NOT merge automatically.** Surface to user for review. Reviews are documents the user wants to read before they land.

## Constraints

These are explicit instructions to constrain the review:

1. **"Suggested next moves" caps at 3 items.** Anything beyond that goes to "Future considerations" or to IDEAS.md if not already there. The previous review proved this constraint produces actionable output; preserve it.

2. **Coverage findings must distinguish active code from deprecated-pending-1.0 code.** Same convention as the previous review's Class A vs Class B split.

3. **Performance findings (if any) must answer: "in what scenario does this matter, and to whom?"** Same convention as the previous review.

4. **Closure claims must be evidence-based.** "GeoPos validation closed" needs a file:line reference and a brief note about what was actually verified, not just "Task 015 ran."

5. **Don't recommend tasks that are already in IDEAS.md.** If the right next move is "do the IDEAS.md item X," say so but don't elevate it to a "Suggested next move" — it's already parked.

6. **If everything is closed and nothing new is found, say so plainly.** Don't pad. A 150-line "all clear" review is more valuable than a 400-line review that invents work to recommend.

## Out of scope

- Code changes
- New numbered tasks (suggestions in the review become candidate tasks; the user decides whether to draft prompts)
- Re-investigating Items 15/16 (already documented in `AUDIT-INVESTIGATIONS.md`)
- Vedic-specific design (that's the Phase 2 planning conversation, separate)

## If something goes wrong

Most likely failure: the closure tracking surfaces a finding that the user thought was closed but actually wasn't. (Example: "Task 015 added GeoPos validation but only for string inputs; numeric lat/lon still unchecked.")

If this happens:

1. Document the partial closure honestly in the review
2. Add to IDEAS.md or recommend as a follow-up task — but don't draft the task in this review document
3. Don't try to fix it in this task; this is review-only

If the closure tracking surfaces that the platform review itself was wrong about something (e.g. "fixstar_mag isn't actually slow on Apple Silicon"), document the disagreement honestly. Reviews aren't sacred; updating them with new evidence is correct.

If the analysis runs long (>400 lines), that's a signal to trim rather than to commit a long document. Reviews lose value when they're tedious.

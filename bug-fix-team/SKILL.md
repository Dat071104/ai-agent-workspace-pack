---
name: bug-fix-team
description: Use this when the user reports a bug or failed behavior. Verify first with a failing test, reason across multiple root-cause hypotheses and fix directions for non-obvious bugs, then recommend one minimal fix before editing. Fast path for obvious bugs. Can run parallel bug_hunter subagents for hard bugs.
---

# Skill: Bug-Fix Team

## Purpose

Verify reported issues before changing code. Fix only the minimal affected zone after confirmation.

## Workflow

1. Re-anchor: restate the original goal/task in one line before touching code.
   Check for divergence with the base branch (`git fetch` then compare) and warn
   if the working tree is behind. Read the bug report.
2. Read relevant context and implementation logs.
3. Reproduce as a **failing test first** when the repo has a test harness: the
   test is both the evidence and the regression guard. Record its failing output
   as the "before" evidence. Without a harness, record the exact repro command
   and its output.
4. Classify the issue:
   - real bug,
   - misunderstanding,
   - expected behavior,
   - feature request,
   - flaky environment.
5. Triage size. Choose one path and say which and why in the output. Judge it
   from steps 3-4 and the suspect code:
   - **Obvious**: reproduced, one cause at one site, with evidence on `exact`
     graph edges (confirm in step 6) or direct code reading. Fast path: one
     hypothesis, one fix direction. Skip the templates in steps 7-9. Still
     confirm before editing.
   - **Medium**: steps 7-11, in-chat multi-hypothesis reasoning.
   - **Hard/ambiguous**: steps 7-11, then the parallel `bug_hunter` offer at step 12.
6. Map the affected zone. Do not start by grepping the tree. The symptom is
   usually reported at one symbol while the fault lives at another, so work the
   call graph rather than the filenames:

   ```bash
   python _agent_ops/tools/explore.py --root . --symbol <symbol from the report>
   python _agent_ops/tools/explore.py --root . --path <entry point> <suspect symbol>
   python _agent_ops/tools/explore.py --root . --impact <symbol you intend to change>
   ```

   `--symbol` returns definitions, callers, callees, and the path from an entry
   point. `--path` shows how control actually reaches the failing code -- the
   middleware or hook sitting on that path is frequently the real cause and
   never appears in a grep for the symptom. Read `_agent_ops/REPO_MAP.md` for
   modules and routes if you need orientation first.

   **Read the provenance tag on every edge.** `exact` is resolved; `heuristic`
   is inferred from a unique name; `ambiguous` means several definitions share
   the name and you must confirm which one runs; `weak` is regex-extracted
   JS/TS. Never build a root-cause argument on an `ambiguous` or `weak` edge
   without opening the file.

   If the index is missing or stale, rebuild it:
   `python _agent_ops/tools/build_code_index.py --root .`

   When `--impact` finds no test, its "Candidate tests (text match, unverified)"
   list is a set of leads to open, not call edges.

   Fallback without Python: grep for the seed symbol, then follow its importers
   one hop out by hand. Either way, state which files are in the zone before
   proposing a fix, and treat an edit to a hot symbol as cross-module until
   proven otherwise.
7. Root-cause hypotheses (Medium/Hard only; Obvious states its one cause and
   evidence instead): generate 2-4 candidate root causes. For each, record
   evidence for, evidence against, confidence (low/med/high), and the cheapest
   way to disprove it. Use `ROOT_CAUSE_HYPOTHESES_TEMPLATE.md`. Check
   `_agent_ops/CURRENT_TASK.md` -> "Ruled Out / Already Tried" first, and record
   each hypothesis there as it is disproved, so no session re-tests a dead end.
8. Rank hypotheses and pick the most-supported one. State explicitly when the
   evidence is mixed instead of forcing a single answer.
9. Fix directions (Medium/Hard only): for the leading hypothesis, propose 2-3 fix approaches. Score
   each by blast radius, risk, effort, reversibility, and test cost. Use
   `FIX_DIRECTIONS_TEMPLATE.md`.
10. Recommend ONE minimal fix. Medium/Hard: keep 1-2 fallbacks documented.
    Obvious: the fix with its evidence, no fallbacks.
11. Impact analysis for the recommended direction. Get the blast radius and the
    tests to run from the graph rather than guessing:
    `python _agent_ops/tools/explore.py --root . --impact <symbol being changed>`.
    Treat its output as the MINIMUM blast radius: dynamic dispatch, DI wiring,
    reflection, and runtime registries are invisible to a static index.
12. Hard gate (Hard/ambiguous only, per step 5): OFFER parallel-subagent mode
    where each `bug_hunter` subagent probes one fix direction in isolation, then
    results are merged. Warn about the extra token cost FIRST. Run only if the
    user confirms.
13. Ask for confirmation before editing. Let the user pick which direction to take.
    Obvious fixes still need this confirmation.
14. After confirmation, fix only the affected zone. Before editing, list every
    caller with `python _agent_ops/tools/explore.py --root . --impact <symbol>`.
    Fix the root cause once in the shared code; never patch one caller while the
    shared function stays broken. Apply `build-team/PONYTAIL_RULES.md` (level
    `full`) and add a `shortcut: <limit>, <when to upgrade>` comment when the fix
    has a known ceiling. Only call symbols verified to exist (Correctness Guards).
15. Test. The failing test from step 3 now passes (without a harness, the
    recorded repro command now succeeds). Run the tests `explore.py --impact` lists for
    the touched symbols. Obvious: the Quick Self-Check in
    `build-team/PONYTAIL_RULES.md`. Medium/Hard: `build-team/SELF_REVIEW_CHECKLIST.md`
    limited to Bug / Risk / Scale / Missing test. If either changed source, re-run the
    relevant checks. Re-check that the fix still serves the original goal from
    step 1, and that it did not push the affected module toward a new failure
    (under-edit). Report `git diff HEAD --shortstat -- <task files>` plus the
    count of new files.
16. Update the implementation log and `_agent_ops/CURRENT_TASK.md` (`## Status`,
    files touched, ruled out). In a managed session, append/write them (ops
    writes are already authorized by `@start-here`); outside one, ask first.
    Then draft the Closure Receipt with
    `python _agent_ops/tools/closure_check.py --root . --compact` (keeps the
    receipt short on an Obvious fix). Compact only folds rows proven updated;
    resolve every `decide`/`unverified`/`MISSING` row, and note that exit 0 does
    not mean the obligations are met.
17. Commit only if user allowed it.

## When to Use

- User reports a bug.
- Audit found a defect.
- Tests fail.
- Behavior may differ from expected behavior.

## When Not to Use

- Feature requests without a defect.
- Broad cleanup.
- Audit-only work.
- Refactors disguised as fixes.

## Expected Output Contract

- Bug classification, evidence, affected zone.
- Medium/Hard: ranked root-cause hypotheses with confidence, 2-3 scored fix
  directions, 1-2 fallbacks. Obvious: one hypothesis and one fix, with evidence.
- Recommended minimal fix and its impact analysis.
- Triage path (Obvious / Medium / Hard) and why; if Hard, a token-cost warning
  before offering parallel-subagent mode.
- Risks and rollback notes.
- Confirmation question (Medium/Hard: which direction to take).
- Failing-test evidence: the "before" failing output and the "after" passing output
  (or the repro command's before/after output when there is no harness).
- After fixing: files changed, diff stat (step 15), tests run and results.
- Closure Receipt per `_agent_ops/SESSION_PROTOCOL.md`, after applying its
  prompt-independent durable-record triggers.
- Final line: what was skipped or not checked, and any remaining risk.

## Safety Rules

- Never use `git add .`.
- Do not fix before confirmation unless autonomous fixing was explicitly confirmed.
- No broad refactor.
- Keep changes minimal.
- Do not commit or push unless user allowed it.
- Always warn about token cost before spawning parallel `bug_hunter` subagents,
  and spawn them only after the user confirms.
- Medium/Hard only: reason across multiple hypotheses, but still commit to ONE
  recommended fix. Obvious uses one hypothesis.
  Do not implement several fix directions at once.

## Correctness Guards

- Anti-drift: keep the original goal in view; if a fix drifts from it, stop and
  flag before continuing.
- Anti-hallucination: only reference functions, APIs, imports, and config keys
  that are verified to exist. When unsure, verify or ask; do not guess a name.
- Merge safety: check divergence with the base branch before editing; warn if
  behind so the fix does not land on stale code.
- Honesty: do not report a fix as done or tests as passed unless they ran.


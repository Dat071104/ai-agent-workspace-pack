---
name: bug-fix-team
description: Use this when the user reports a bug or failed behavior. Verify first, classify bug vs misunderstanding vs expected behavior vs feature request, then propose a minimal fix before editing.
---

# Skill: Bug-Fix Team

## Purpose

Verify reported issues before changing code. Fix only the minimal affected zone after confirmation.

## Workflow

1. Re-anchor: restate the original goal/task in one line before touching code.
   Check for divergence with the base branch (`git fetch` then compare) and warn
   if the working tree is behind. Read the bug report.
2. Read relevant context and implementation logs.
3. Reproduce or inspect.
4. Classify the issue:
   - real bug,
   - misunderstanding,
   - expected behavior,
   - feature request,
   - flaky environment.
5. Map the affected zone. Do not start by grepping the tree. The symptom is
   usually reported at one symbol while the fault lives at another, so work the
   call graph rather than the filenames:

   ```bash
   python scripts/explore.py --root . --symbol <symbol from the report>
   python scripts/explore.py --root . --path <entry point> <suspect symbol>
   python scripts/explore.py --root . --impact <symbol you intend to change>
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
   `python scripts/build_code_index.py --root .`

   Fallback without Python: grep for the seed symbol, then follow its importers
   one hop out by hand. Either way, state which files are in the zone before
   proposing a fix, and treat an edit to a hot symbol as cross-module until
   proven otherwise.
6. Root-cause hypotheses: generate 2-4 candidate root causes. For each, record
   evidence for, evidence against, confidence (low/med/high), and the cheapest
   way to disprove it. Use `ROOT_CAUSE_HYPOTHESES_TEMPLATE.md`. Check
   `_agent_ops/CURRENT_TASK.md` -> "Ruled Out / Already Tried" first, and record
   each hypothesis there as it is disproved. This is what stops a later session
   -- or this one after a context compaction -- from re-testing a known dead end.
7. Rank hypotheses and pick the most-supported one. State explicitly when the
   evidence is mixed instead of forcing a single answer.
8. Fix directions: for the leading hypothesis, propose 2-3 fix approaches. Score
   each by blast radius, risk, effort, reversibility, and test cost. Use
   `FIX_DIRECTIONS_TEMPLATE.md`.
9. Recommend ONE minimal fix and keep 1-2 fallbacks documented.
10. Impact analysis for the recommended direction. Get the blast radius and the
    tests to run from the graph rather than guessing:
    `python scripts/explore.py --root . --impact <symbol being changed>`.
    Treat its output as the MINIMUM blast radius: dynamic dispatch, DI wiring,
    reflection, and runtime registries are invisible to a static index.
11. Complexity gate: classify the bug as Medium (single-agent) or Hard/ambiguous.
    - Medium: proceed with in-chat multi-hypothesis reasoning.
    - Hard/ambiguous: OFFER parallel-subagent mode where each `bug_hunter`
      subagent probes one fix direction in isolation, then results are merged.
      Warn about the extra token cost FIRST. Run only if the user confirms.
12. Ask for confirmation before editing. Let the user pick which direction to take.
13. After confirmation, fix only the affected zone. Before calling any function,
    API, import, or config key, confirm it actually exists in the codebase or a
    real dependency. If unverified, say so and check; never invent a symbol.
14. Test. Re-check that the fix still serves the original goal from step 1, and
    that it did not push the affected module toward a new failure (under-edit).
15. Update implementation log after permission.
16. Commit only if user allowed it.

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

- Bug classification.
- Evidence.
- Affected zone.
- Ranked root-cause hypotheses with confidence.
- 2-3 scored fix directions.
- Recommended minimal fix plus 1-2 fallbacks.
- Impact analysis for the recommended direction.
- Complexity gate result (Medium vs Hard) and, if Hard, a token-cost warning
  before offering parallel-subagent mode.
- Risks and rollback notes.
- Confirmation question (including which direction to take).
- After fixing: files changed, tests, results, remaining risks.
- Closure Receipt per `_agent_ops/SESSION_PROTOCOL.md`.

## Safety Rules

- Never use `git add .`.
- Do not fix before confirmation unless autonomous fixing was explicitly confirmed.
- No broad refactor.
- Keep changes minimal.
- Do not commit or push unless user allowed it.
- Always warn about token cost before spawning parallel `bug_hunter` subagents,
  and spawn them only after the user confirms.
- Reason across multiple hypotheses, but still commit to ONE recommended fix.
  Do not implement several fix directions at once.

## Correctness Guards

- Anti-drift: keep the original goal in view; if a fix drifts from it, stop and
  flag before continuing.
- Anti-hallucination: only reference functions, APIs, imports, and config keys
  that are verified to exist. When unsure, verify or ask; do not guess a name.
- Merge safety: check divergence with the base branch before editing; warn if
  behind so the fix does not land on stale code.
- Honesty: do not report a fix as done or tests as passed unless they ran.


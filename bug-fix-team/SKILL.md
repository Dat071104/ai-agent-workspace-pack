---
name: bug-fix-team
description: Use this when the user reports a bug or failed behavior. Verify first, classify bug vs misunderstanding vs expected behavior vs feature request, then propose a minimal fix before editing.
---

# Skill: Bug-Fix Team

## Purpose

Verify reported issues before changing code. Fix only the minimal affected zone after confirmation.

## Workflow

1. Read the bug report.
2. Read relevant context and implementation logs.
3. Reproduce or inspect.
4. Classify the issue:
   - real bug,
   - misunderstanding,
   - expected behavior,
   - feature request,
   - flaky environment.
5. Map the affected zone.
6. Root-cause hypotheses: generate 2-4 candidate root causes. For each, record
   evidence for, evidence against, confidence (low/med/high), and the cheapest
   way to disprove it. Use `ROOT_CAUSE_HYPOTHESES_TEMPLATE.md`.
7. Rank hypotheses and pick the most-supported one. State explicitly when the
   evidence is mixed instead of forcing a single answer.
8. Fix directions: for the leading hypothesis, propose 2-3 fix approaches. Score
   each by blast radius, risk, effort, reversibility, and test cost. Use
   `FIX_DIRECTIONS_TEMPLATE.md`.
9. Recommend ONE minimal fix and keep 1-2 fallbacks documented.
10. Impact analysis for the recommended direction.
11. Complexity gate: classify the bug as Medium (single-agent) or Hard/ambiguous.
    - Medium: proceed with in-chat multi-hypothesis reasoning.
    - Hard/ambiguous: OFFER parallel-subagent mode where each `bug_hunter`
      subagent probes one fix direction in isolation, then results are merged.
      Warn about the extra token cost FIRST. Run only if the user confirms.
12. Ask for confirmation before editing. Let the user pick which direction to take.
13. After confirmation, fix only the affected zone.
14. Test.
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


---
name: clean-code-team
description: Use this only for high-risk cleanup or refactoring. Requires warning, clean git state, recovery branch/tag, audit first, batch plan, one batch at a time, tests after each batch, and confirmation before continuing.
---

# Skill: Clean-Code Team

## Purpose

Handle cleanup and refactoring with strict safeguards. Clean-code is always Very Heavy.

## Very Heavy Warning

Before starting, warn the user:

- high token cost,
- high reasoning cost,
- should use the strongest available model,
- can break working code,
- requires clean git state,
- requires a recovery branch or tag,
- must audit first,
- must clean one batch at a time.

## Workflow

1. Warn user and classify the task as Very Heavy.
2. Check git state.
3. Require clean git state or ask user how to proceed.
4. Recommend recovery branch or tag.
5. Build a dependency and behavior map based on imports, routes, tests, scripts, runtime flows, and logs.
6. Identify cleanup candidates.
7. Classify risk and value.
8. Propose a batch cleanup plan.
9. Ask for confirmation.
10. Clean one batch only.
11. Test after the batch.
12. Update implementation log after permission.
13. Commit batch only if user allowed it.
14. Ask whether to continue before the next batch.

## When to Use

- Removing duplication.
- Improving structure.
- Reducing dead code.
- Refactoring confusing modules.
- Preparing code for long-term maintenance.

## When Not to Use

- Dirty git state without explicit user direction.
- Missing tests for critical behavior.
- Urgent bug fix.
- User has not confirmed cleanup risk.

## Expected Output Contract

- Very Heavy warning.
- Git state.
- Recovery recommendation.
- Dependency and behavior map summary.
- Cleanup candidates.
- Batch plan.
- Confirmation question.
- After each batch: files changed, tests, results, rollback notes, continue question.

## Safety Rules

- Never use `git add .`.
- Do not run on dirty git state without explicit user direction.
- Do not combine unrelated cleanup batches.
- Do not claim a perfect full in-memory graph.
- Do not commit or push unless user allowed it.

## Refactor Guards

- Dependency drift: do not add, remove, or upgrade a package as part of cleanup
  unless the batch explicitly requires it. If it does, state the package,
  version change, reason, and expected lockfile change, and confirm first.
- Prefer improving structure over adding code. If a batch only adds a new layer
  without reducing duplication or complexity, reconsider it.
- Do not copy-paste an existing pattern to "clean up"; extract or reuse instead.
- Anti-hallucination: only reference symbols and modules verified to exist.
- Keep public behavior identical unless the batch is explicitly a behavior change
  the user approved.


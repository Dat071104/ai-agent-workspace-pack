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
6. Prepare impact analysis.
7. Propose the minimal fix.
8. Ask for confirmation before editing.
9. After confirmation, fix only the affected zone.
10. Test.
11. Update implementation log after permission.
12. Commit only if user allowed it.

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
- Impact analysis.
- Minimal fix proposal.
- Risks and rollback notes.
- Confirmation question.
- After fixing: files changed, tests, results, remaining risks.

## Safety Rules

- Never use `git add .`.
- Do not fix before confirmation unless autonomous fixing was explicitly confirmed.
- No broad refactor.
- Keep changes minimal.
- Do not commit or push unless user allowed it.


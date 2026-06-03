---
name: tester-team
description: Use this for full audits, scoped audits, UX/performance audits, and production-readiness checks. This team tests and reports only; it does not fix by default.
---

# Skill: Tester Team

## Purpose

Audit and test like a QA/product team without modifying files by default.

## First Question

Always ask which audit mode the user wants:

- Full audit.
- Scoped audit.
- Production-readiness audit.
- UX/performance-only audit.

Warn that full audits and production-readiness audits can be Heavy or Very Heavy.

## Workflow

1. Confirm audit mode and scope.
2. Check token/risk level.
3. Read project context, implementation logs, decision logs, risk register, and roadmap as needed.
4. Inspect relevant files and tests.
5. Run safe tests and read-only checks when appropriate.
6. Report findings in chat first.
7. Do not fix unless the user switches to `bug-fix-team/`.

## When to Use

- Full project audit.
- Scoped feature or phase audit.
- Production-readiness review.
- UX/performance-only audit.
- Regression investigation without code changes.

## When Not to Use

- Fixing bugs.
- Refactoring.
- Creating major structure.

## Expected Output Contract

- Audit mode and scope.
- Token/risk warning.
- Commands run.
- Findings ordered by severity.
- Evidence and reproduction notes.
- UX/performance/integration/repo hygiene notes.
- Test gaps.
- Recommended next workflow.

## Safety Rules

- Never use `git add .`.
- Do not modify files by default.
- Do not commit or push.
- Be explicit about tests not run.


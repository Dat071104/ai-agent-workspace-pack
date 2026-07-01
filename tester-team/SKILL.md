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
4. Detect the test harness (see below). Report what exists vs what is missing.
5. Inspect relevant files and tests.
6. Propose exact test commands with token/time estimates; run them only after
   the user approves. Prefer the narrowest scope first.
7. Report findings in chat first. Do not claim tests passed unless they ran.
8. Do not fix unless the user switches to `bug-fix-team/`.

## Test Harness Detection

Detect available test tooling by reading `package.json`, `pyproject.toml`,
lockfiles, and config files. Look for: playwright, jest, vitest, cypress,
pytest, go test, and build scripts. See `TEST_HARNESS_MATRIX.md` for the
detect/run command map.

Rules:

- Report what EXISTS vs what is MISSING. Do NOT install anything.
- Propose exact commands (for example `npx playwright test <spec>`), estimate
  token/time, and mark E2E runs as Heavy.
- Run tests only after the user approves. Prefer one spec or one project first,
  then broaden.
- For end-to-end runs, use `E2E_PLAYWRIGHT_PROMPT.md`.

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

## Security & Observability Audit

Report only; do not fix. Route real defects to `bug-fix-team/`.

Security checks (flag by severity, do not exploit):

- Hardcoded secrets, tokens, or credentials in code or config.
- Unsanitized input reaching SQL (string-concatenated queries vs parameterized),
  shell/command execution, or file paths.
- Missing authentication/authorization on sensitive routes or actions.
- Unsafe deserialization, SSRF-prone requests, or overly broad CORS.

Observability checks (report gaps):

- Failure paths (catch blocks, error returns, external calls) without a log or
  metric at the failure point.
- No structured way to trace a request/operation end to end.
- Silent failures that would be invisible in production.

## Expected Output Contract

- Audit mode and scope.
- Token/risk warning.
- Commands run.
- Findings ordered by severity.
- Evidence and reproduction notes.
- Security findings (secrets, injection, authz gaps) with severity.
- Observability gaps (missing logs/metrics on failure paths).
- UX/performance/integration/repo hygiene notes.
- Test gaps.
- Recommended next workflow.

## Safety Rules

- Never use `git add .`.
- Do not modify files by default.
- Do not commit or push.
- Do not install dependencies or test tooling.
- Do not run Heavy or E2E test commands without explicit approval.
- Be explicit about tests not run.


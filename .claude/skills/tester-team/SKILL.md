---
name: tester-team
description: Use this for full audits, scoped audits, UX/performance audits, and production-readiness checks. Can detect and run the project's real test harness (Playwright, Jest, Vitest, pytest) after approval. Reports only; does not fix by default.
---

# Tester Team (adapter)

This is a Claude Code adapter. The source of truth is `tester-team/SKILL.md` at
the repo root. Read that file and its references, then follow it exactly.

References: `tester-team/TEST_HARNESS_MATRIX.md`,
`tester-team/E2E_PLAYWRIGHT_PROMPT.md`, `tester-team/FULL_AUDIT_PROMPT.md`,
`tester-team/SCOPED_AUDIT_PROMPT.md`. For parallel audits, the `tester` and
`repo_hygiene_reviewer` subagents are available.

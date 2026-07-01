# Tester Team

Use `tester-team/` for audit and testing only. It reports issues and does not fix them by default.

Default first question:

- Full audit from project start to current phase?
- Scoped audit of a feature, folder, or phase?
- Production readiness audit?
- UX/performance-only audit?

It can detect the project's real test harness (Playwright, Jest, Vitest,
Cypress, pytest, go test) and propose exact scoped commands, but it never
installs tooling and runs tests only after approval.

Vietnamese note: Team nay chi kiem thu va audit. Khong sua code neu nguoi dung
chua chuyen sang bug-fix-team. No co the do harness test that (vd Playwright/npx)
va de xuat lenh, nhung chay chi khi duoc duyet, khong tu cai.

Files:

- `SKILL.md`
- `FULL_AUDIT_PROMPT.md`
- `SCOPED_AUDIT_PROMPT.md`
- `TEST_HARNESS_MATRIX.md`
- `E2E_PLAYWRIGHT_PROMPT.md`
- `UX_AUDIT_CHECKLIST.md`
- `PERFORMANCE_AUDIT_CHECKLIST.md`
- `PRODUCTION_READINESS_MATRIX.md`

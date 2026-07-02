# Full Audit Prompt

```text
You are using tester-team for a full audit.

Ask first:
Do you want a full audit, scoped audit, production-readiness audit, or UX/performance-only audit?

If full audit is confirmed:
1. Check git status.
2. Read the target project's own README.md (not this pack's), plus AGENTS.md, context cards, implementation log, decision log, risk register, and roadmap.
3. Inspect architecture, main user flows, tests, docs, configuration, and repo hygiene.
4. Run safe tests and build checks if available.
5. Audit functionality, UX, accessibility basics, performance, integration, runnability, observability, docs, and public repo cleanliness.

Rules:
- Do not fix.
- Do not modify files.
- Never use git add .
- Do not commit or push.

Report:
- Severity-ranked findings.
- Evidence.
- Reproduction steps.
- Test commands and results.
- Unknowns and test gaps.
- Recommended next workflow.
```

# Scoped Audit Prompt

```text
You are using tester-team for a scoped audit.

Scope:
<feature, folder, phase, bug area, or user flow>

Steps:
1. Check git status.
2. Read relevant context and logs.
3. Inspect only files needed for the scope.
4. Run targeted tests or manual checks.
5. Check integration boundaries and regressions near the scope.

Rules:
- Do not fix.
- Do not modify files.
- Never use git add .
- Do not commit or push.

Report:
- Scope audited.
- Findings by severity.
- Evidence and file/line references.
- Commands run.
- Residual risks.
```


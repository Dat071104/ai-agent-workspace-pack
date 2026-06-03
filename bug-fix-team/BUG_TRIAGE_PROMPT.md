# Bug Triage Prompt

```text
You are using bug-fix-team for bug triage.

Bug report:
<paste report>

Repo path:
<absolute repo path>

Steps:
1. Check git status.
2. Read project context, implementation log, decision log, and risk register.
3. Inspect relevant files and tests.
4. Try to reproduce or reason from code and logs.
5. Classify the report:
   - real bug,
   - misunderstanding,
   - expected behavior,
   - feature request,
   - flaky environment.

Rules:
- Do not fix yet.
- Never use git add .
- Ask before destructive actions.

Report:
- Classification.
- Evidence.
- Reproduction steps or inspection notes.
- Affected area.
- Recommended next action.
```


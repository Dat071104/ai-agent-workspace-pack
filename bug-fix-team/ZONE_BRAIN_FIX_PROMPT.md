# Zone-Brain Fix Prompt

```text
You are using bug-fix-team for affected-zone fixing.

Confirmed bug:
<bug summary>

Affected zone:
<files/modules/APIs/contracts>

Steps:
1. Re-check git status.
2. Map directly affected files.
3. Map adjacent files that may regress.
4. Identify tests needed before and after.
5. Propose the smallest fix.
6. Ask user confirmation before editing.
7. After confirmation, edit only the affected zone.
8. Run targeted tests.
9. Update implementation log.

Git:
- Never use git add .
- Stage explicit files only if user allowed committing.
- Commit only if user allowed it.
```


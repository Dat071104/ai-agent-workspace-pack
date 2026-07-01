# Zone-Brain Fix Prompt

```text
You are using bug-fix-team for affected-zone fixing with multi-direction reasoning.

Confirmed bug:
<bug summary>

Affected zone:
<files/modules/APIs/contracts>

Steps:
1. Re-check git status.
2. Map directly affected files.
3. Map adjacent files that may regress.
4. Root-cause hypotheses: generate 2-4 candidates with evidence and confidence
   (use ROOT_CAUSE_HYPOTHESES_TEMPLATE.md). Rank them; say if evidence is mixed.
5. Fix directions: for the leading hypothesis propose 2-3 approaches scored by
   blast radius, risk, effort, reversibility, and test cost
   (use FIX_DIRECTIONS_TEMPLATE.md). Recommend one, keep fallbacks.
6. Identify tests needed before and after.
7. Complexity gate: if the bug is Hard/ambiguous, offer parallel bug_hunter mode
   and warn about token cost before running it.
8. Ask user confirmation before editing. Let the user pick the direction.
9. After confirmation, edit only the affected zone using the chosen direction.
10. Run targeted tests.
11. Update implementation log.

Git:
- Never use git add .
- Stage explicit files only if user allowed committing.
- Commit only if user allowed it.
```

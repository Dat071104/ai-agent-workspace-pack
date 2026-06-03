# Clean-Code Audit Prompt

```text
You are using clean-code-team for audit only.

Warning:
Clean-code work is high cost and high risk. Audit first. Do not change files.

Repo path:
<absolute repo path>

Steps:
1. Check git status.
2. Read context, logs, tests, and architecture docs.
3. Build a dependency map from imports and call boundaries where practical.
4. Identify duplication, dead code, unclear boundaries, risky abstractions, large files, and inconsistent patterns.
5. Classify cleanup candidates by risk and value.

Rules:
- Do not modify files.
- Never use git add .
- Do not commit or push.

Report:
- Cleanup candidates.
- Risk classification.
- Suggested batches.
- Tests needed per batch.
- Recovery recommendation.
```


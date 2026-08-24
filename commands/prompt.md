# Prompt Command

```text
Use prompting-team.
Read `_agent_ops/SESSION_BRIEF.md`, `_agent_ops/OPERATING_RULES.md`, and `_agent_ops/CURRENT_TASK.md` (if a task is in progress) first. Use `_agent_ops/REPO_MAP.md` to locate code before grepping the repo,
then only the project context and implementation evidence needed for this goal.
Create a strong copy-paste prompt for this goal: <goal>.
Use prompting-team/PROMPT_READINESS_GATE.md first for large prompts.
Capability-detect real child agents. If unavailable, default to stricter scope,
exact context-read order, stop/confirm gates, and sequential team roles when useful.
Include repo path placeholder, scope, non-goals, Session Receipt, initial inspection,
phase gates, tests, repo hygiene, root-owned `_agent_ops/` closure updates, no git
add ., commit/push rules, final report format, and honesty rules.
Show expected output before finalizing.
Do not write prompt files unless I explicitly confirm.
Expected output: full prompt plus prompt review checklist result.
```

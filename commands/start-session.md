# Start Session Command

```text
Read only AGENTS.md and START_HERE.md first. Read TEAM_ROUTER.md for routing. Do not read README.md unless the user asks about the workspace pack itself. This starts one managed session: check git status, ensure `_agent_ops/` exists without overwriting files, then read only `_agent_ops/SESSION_BRIEF.md` and `_agent_ops/OPERATING_RULES.md`. This permission applies only inside `_agent_ops/`.
Do not read every team folder yet.

User request:
<paste request>

Your job:
1. Route the request using TEAM_ROUTER.md or the README routing table.
2. Recommend the best team and explain why.
3. Ask clarifying questions if context is missing.
4. Classify token/risk level: Light, Medium, Heavy, or Very Heavy.
5. Show the expected output before doing the work.
6. Suggest optional teams/skills only if useful.
7. Print a compact Session Receipt: understood goal, non-goals, context read,
   missing context, recommended mode, and the one confirmation needed.
8. Recommend `solo`, `auto`, `parallel`, or `sequential`; spawn only when two
   independent bounded workstreams and native support exist, after a token-cost
   warning. Otherwise use sequential role checks when useful.
9. Before meaningful completion, update the smallest applicable `_agent_ops/`
   records. Root owns this; subagents never write `_agent_ops/`.
10. Wait for confirmation before source/config/git/external/destructive changes.

Rules:
- Chat first, files later.
- Never use git add .
- Ask before destructive or dangerous actions.
- Keep the report concise and honest.
```

# Harness Prompt

```text
You are using prompting-team to design or evaluate a harness.

Goal:
<tool-calling, test, eval, or prompt harness goal>

Repo path:
<absolute repo path>

Inputs:
<data, tasks, tools, fixtures, or evaluation cases>

Target agent profile:
- Target agent/harness: <Codex / Claude Code / DeepSeek / Gemini / Cursor / other>.
- If native spawning is unavailable, or the target is weaker/less suited to the
  task: define a smaller deterministic harness first, require explicit context
  reads, and add stop gates before adding dependencies or broad coverage.
- If extra teams are useful, list them in order. Capability-detect child agents;
  if unavailable, they run sequentially in one session.

Required behavior:
- Define success criteria.
- Define failure cases.
- Include setup and teardown.
- Prefer deterministic checks when possible.
- Record all commands and outputs needed to reproduce.

Initial inspection:
1. Read the target project's own AGENTS.md or always-on rules.
2. Read `_agent_ops/SESSION_BRIEF.md` and `_agent_ops/OPERATING_RULES.md` first.
3. Read only relevant project context, log evidence, roadmap, and selected team
   SKILL.md files.
4. Inspect existing tests or harness utilities.
5. Identify external dependencies and whether they are available.
6. Report the exact files read and proposed harness boundary before editing.

Safety:
- Never use git add .
- Do not run destructive commands.
- Do not send private data to external services.
- Ask before adding dependencies.

Output:
- Harness design.
- Files to create or change.
- Test plan.
- Risk notes.
- Final report format.
```

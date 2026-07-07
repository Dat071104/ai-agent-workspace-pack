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
- If target is DeepSeek, Gemini, Cursor, another prompt-based harness, or a
  weaker/less-suited model: define a smaller deterministic harness first, require
  explicit context reads, and add stop gates before adding dependencies or broad
  coverage.
- If extra teams are useful, list them in order. On prompt-based harnesses, they
  run sequentially in one session.

Required behavior:
- Define success criteria.
- Define failure cases.
- Include setup and teardown.
- Prefer deterministic checks when possible.
- Record all commands and outputs needed to reproduce.

Initial inspection:
1. Read the target project's own AGENTS.md or always-on rules.
2. Read project context card, implementation log, phase roadmap, and selected
   team SKILL.md files if relevant.
3. Inspect existing tests or harness utilities.
4. Identify external dependencies and whether they are available.
5. Report the exact files read and proposed harness boundary before editing.

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

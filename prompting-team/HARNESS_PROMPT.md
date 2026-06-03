# Harness Prompt

```text
You are using prompting-team to design or evaluate a harness.

Goal:
<tool-calling, test, eval, or prompt harness goal>

Repo path:
<absolute repo path>

Inputs:
<data, tasks, tools, fixtures, or evaluation cases>

Required behavior:
- Define success criteria.
- Define failure cases.
- Include setup and teardown.
- Prefer deterministic checks when possible.
- Record all commands and outputs needed to reproduce.

Initial inspection:
1. Read context and logs.
2. Inspect existing tests or harness utilities.
3. Identify external dependencies and whether they are available.

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


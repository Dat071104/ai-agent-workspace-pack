# AGENTS.md

This repo is a reusable AI-agent operating kit for coding projects.

For broad requests, read `START_HERE.md`, `TEAM_ROUTER.md`, and `README.md` first. Do not load every team folder. Route the task, recommend the best team, explain why, classify token/risk level, and ask whether to proceed.

Use `core-context/` templates for project memory. Use the relevant team folder only when needed.

Behavior rules:

- Chat first, files later.
- Say what you understood and what context is missing.
- Ask clarifying questions when needed.
- Show options, risks, expected output, and next step.
- Ask before writing or modifying files unless autonomous mode was explicitly confirmed.
- Use `prompting-team/PROMPT_READINESS_GATE.md` before large prompts.
- Warn when work is Heavy or Very Heavy.
- Suggest extra teams/skills only when useful; do not force them.

Safety rules:

- Never use `git add .`.
- Stage explicit files only.
- Ask before destructive or dangerous actions.
- Check git status before and after changes when working in a git repo.
- Update implementation logs in target projects after permission.
- Keep public repositories clean: no secrets, private logs, generated artifacts, datasets, model files, or local-only files.
- Prefer Vietnamese if the user writes Vietnamese.
- Keep reports concise and honest. Do not claim tests passed unless they were run.


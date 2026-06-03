# Core Context / Bo nho du an

The `core-context/` folder contains templates for the project memory layer. Copy these files into a target project, usually under `_agent_ops/`, so AI agents can understand the current state without re-discovering everything each session.

Vietnamese note: Thu muc nay dung de tao bo nho du an: context, log, quyet dinh, rui ro, roadmap va quy tac van hanh.

## Recommended Files in a Target Project

- `PROJECT_CONTEXT_CARD.md`
- `SESSION_BRIEF.md`
- `IMPLEMENTATION_LOG.md`
- `DECISION_LOG.md`
- `RISK_REGISTER.md`
- `PHASE_ROADMAP.md`
- `OPERATING_RULES.md`
- `phase_context_cards/`

## Session Brief

`SESSION_BRIEF.template.md` is a compact file for starting an AI-agent session without loading many docs. Use it to tell the agent:

- current goal,
- active task,
- files allowed to read first,
- files not to edit without confirmation,
- preferred team,
- expected output,
- risk/token level.

This reduces token load and helps the agent avoid reading every folder.

## Rules

- Keep logs append-only.
- Keep entries factual and dated.
- Do not include secrets or private data.
- Update context before handoff.
- Never stage files with `git add .`; stage explicit files only.


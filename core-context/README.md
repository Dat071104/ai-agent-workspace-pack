# Core Context / Bo nho du an

The `core-context/` folder contains templates for the project memory layer. Copy these files into a target project, usually under `_agent_ops/`, so AI agents can understand the current state without re-discovering everything each session.

Vietnamese note: Thu muc nay dung de tao bo nho du an: context, log, quyet dinh, rui ro, roadmap va quy tac van hanh.

## Recommended Files in a Target Project

- `INDEX.md` -- router for the folder itself; read it when unsure what to open
- `PROJECT_CONTEXT_CARD.md`
- `SESSION_BRIEF.md`
- `CURRENT_TASK.md` -- task-level working memory
- `REPO_MAP.md` -- generated code map, not a template
- `SESSION_PROTOCOL.md`
- `IMPLEMENTATION_LOG.md`
- `LOG_SUMMARY.md` -- generated
- `HANDOFF.md` -- written by `handoff-team/` when a session hands off
- `DECISION_LOG.md`
- `RISK_REGISTER.md`
- `PHASE_ROADMAP.md`
- `OPERATING_RULES.md`
- `phase_context_cards/`
- `archive/` -- rotated log entries

`scripts/init_project_ops.py` creates all of these, generates `REPO_MAP.md`, and
writes an `_agent_ops/.gitignore` implementing the hybrid tracking policy below.

For a starter context card pre-filled from repo inspection (stack, branch,
commit) instead of the blank template:

```bash
python _agent_ops/tools/generate_context_card.py --root . --name "<project>" --output _agent_ops/PROJECT_CONTEXT_CARD.md
```

It leaves `<fill in ...>` markers where a human must decide. Those are blanks to
ask about, not facts to infer -- `scripts/session_start.py` counts them and says
so.

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

## Managed Session Protocol

`SESSION_PROTOCOL.template.md` defines the lifecycle for a managed session:
minimal first reads, advisor-style Session Receipt, mode selection, subagent
ownership, and the closure gate for factual context updates. The root agent
owns `_agent_ops/`; subagents never update it. Read it when initializing a
target project or changing session behavior, not on every ordinary task.

## Current Task and Repo Map

`CURRENT_TASK.template.md` is task-level working memory: files touched, dead ends
already ruled out, open questions, next step. It is overwritten, never appended,
and it is what survives a mid-task context compaction. The Session Brief cannot
do this job -- it is scoped to the session, not the task.

`REPO_MAP.md` is generated, not copied from a template:

```bash
python _agent_ops/tools/generate_repo_map.py --root . --output _agent_ops/REPO_MAP.md --force
```

It gives a module table, the highest fan-in files (widest blast radius), and
entry points in one capped Tier-1 read, so an agent locating code does not have
to grep the whole repository. For the affected zone of one specific change, drill
down with `scripts/scan_deps.py --seed "<keyword>" --hops 2`.

## Git Tracking (hybrid policy)

Durable project memory is tracked so it survives a clone -- including the
implementation log and its archive, which are the project's real work history.
Only machine-local scratch and derived files stay untracked: `SESSION_BRIEF.md`
and `CURRENT_TASK.md` change every session, and `LOG_SUMMARY.md` is regenerated
from the log.

| Tracked | Ignored |
| --- | --- |
| `INDEX.md`, `OPERATING_RULES.md`, `SESSION_PROTOCOL.md`, `PROJECT_CONTEXT_CARD.md`, `REPO_MAP.md`, `HANDOFF.md`, `IMPLEMENTATION_LOG.md`, `archive/`, `DECISION_LOG.md`, `RISK_REGISTER.md`, `PHASE_ROADMAP.md`, `phase_context_cards/` | `SESSION_BRIEF.md`, `CURRENT_TASK.md`, `LOG_SUMMARY.md` |

Tracked files are readable by anyone with repository access. Keep secrets,
private data, and unverified claims out of all of them.

## Rules

- Keep logs append-only; rotate rather than delete (see `SESSION_PROTOCOL.md`).
- Keep entries factual and dated.
- Do not include secrets or private data.
- Update context before handoff, and print the Closure Receipt.
- Never stage files with `git add .`; stage explicit files only.

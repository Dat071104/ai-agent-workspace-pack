# Next Session Context Template

Two uses, same content:

1. Paste the block below into a new agent session, or
2. write it to `_agent_ops/HANDOFF.md` (tracked) so the next session finds it
   automatically. Start that file with the two fields below so
   `scripts/session_start.py` can classify it:

```markdown
## Status

open

## Date

YYYY-MM-DD
```

Set `Status` to `consumed` once a session has absorbed the handoff, so it is not
replayed. Because `CURRENT_TASK.md` is not tracked, copy its dead ends and open
questions into the handoff or they will not survive a machine swap.

```text
Project:
<project name>

Current state:
<short summary>

Read first:
- AGENTS.md
- _agent_ops/INDEX.md
- _agent_ops/REPO_MAP.md (before grepping for code)
- _agent_ops/PROJECT_CONTEXT_CARD.md
- _agent_ops/LOG_SUMMARY.md, then IMPLEMENTATION_LOG.md if needed

Already ruled out (do not retry):
<dead ends from CURRENT_TASK.md, with evidence>

Open questions awaiting the user:
<questions>

Last completed:
<last completed task>

Next task:
<next task>

Known risks:
<risks>

Rules:
- Never use git add .
- Check git status before and after changes.
- Update implementation log.
- Commit only if I explicitly allow it.
```


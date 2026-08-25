---
name: handoff-team
description: Use this for session handoffs, final reports, continuity summaries, next-session prompts, and milestone delivery notes. Do not use for code changes or bug fixing.
---

# Skill: Handoff Team

## Name

Handoff Team

## Description

Creates complete or compact handoff artifacts for continuity across sessions, agents, milestones, or final delivery.

## When to Use

- End of session.
- Before changing agents.
- Before release.
- After major phase completion.
- For portfolio/demo final reports.

## When Not to Use

- Direct code implementation.
- Bug fixing.
- Cleanup or refactoring.
- Audit-only work without a handoff need.

## Workflow

1. Read project context and logs, cheapest first: `_agent_ops/SESSION_BRIEF.md`,
   `_agent_ops/CURRENT_TASK.md` (unfinished work, dead ends, open questions),
   and `_agent_ops/LOG_SUMMARY.md` before the full implementation log. Rotate
   the log first if it has grown past its retention window:
   `python _agent_ops/tools/summarize_implementation_log.py --log _agent_ops/IMPLEMENTATION_LOG.md --rotate --keep 10 --output _agent_ops/LOG_SUMMARY.md --force`
2. Check git state and recent commit if available.
3. Summarize architecture and current status.
4. List what was built and files touched.
5. Record run/test commands.
6. Capture known issues and risks.
7. Provide next steps and next-session prompt.
8. Write the handoff to `_agent_ops/HANDOFF.md` using
   `NEXT_SESSION_CONTEXT_TEMPLATE.md` as its shape, with `Status: open` at the
   top. That file is TRACKED, so a session on another machine or a fresh clone
   picks it up. `scripts/session_start.py` detects it and tells the next agent
   to read it first -- the user does not have to paste anything or explain that
   this is a continuation.
   Fold in what `CURRENT_TASK.md` holds (dead ends already ruled out, open
   questions) because that file is NOT tracked and will not travel.
   Keep it short and free of secrets: on a public repo it is public.

## Output Format

- Executive summary.
- Repo state.
- Architecture.
- Work completed.
- How to run/test.
- Known issues.
- Next steps, including anything still listed in CURRENT_TASK.md as ruled out or
  awaiting an answer, so the next session does not rediscover it.
- Suggested next prompt.
- Closure Receipt per `_agent_ops/SESSION_PROTOCOL.md`.

## Safety Rules

- Never use `git add .`.
- Do not modify code unless asked.
- Do not commit or push unless user allowed it.
- Do not include secrets or private data.

# Session Brief / Tom tat phien lam viec

Use this compact file as the hot context at the start of every managed
AI-agent session. Keep it short (normally one or two pages). It points the
agent to only the first files it needs; do not duplicate full logs here.

## Original Goal (do not lose)

`<the one-line goal for this work; re-read before each step to prevent drift>`

The agent should re-anchor to this line before each edit. If the current work
drifts from it, stop and flag instead of continuing.

## Project / User Goal

`<what the user wants to accomplish>`

## Current State

`<current project state or milestone>`

## Session Receipt

- Managed session: `yes / no`
- Harness and native child-agent capability: `<known / unknown / unavailable>`
- Context read at session start: `<paths>`
- Important context missing: `<none or paths/questions>`
- Current work mode: `<solo / auto / parallel / sequential>`

## Active Task

`<what this session should do>`

## Constraints

- `<time, budget, stack, safety, platform, or scope constraint>`

## Non-Goals / Do Not Infer

- `<work that is explicitly out of scope or requires user confirmation>`

## Files Allowed to Read First

- `AGENTS.md`
- `_agent_ops/OPERATING_RULES.md`
- `_agent_ops/CURRENT_TASK.md` (when a task is already in progress)
- `_agent_ops/REPO_MAP.md` (before grepping the repository for code)
- `<specific context/log/team files only when needed>`

See `_agent_ops/INDEX.md` for the full read order and cost of each file.

## Files Not to Edit Without Confirmation

- `<file or folder>`

## Preferred Team

`<advisor-team / analyze-team / prompting-team / tester-team / bug-fix-team / clean-code-team / repo-hygiene-team / handoff-team / unsure>`

## Expected Output

`<chat report, options table, prompt, audit report, bug triage, handoff, etc.>`

## Risk / Token Level

`Light / Medium / Heavy / Very Heavy`

## Last Verified Commit

`<short SHA of HEAD when this brief was last confirmed against the code>`

Update this whenever the brief is refreshed. `scripts/session_start.py` diffs it
against HEAD to report exactly what changed since this memory was written, so a
stale value is what stops the agent from acting on an outdated mental model.

## Last Updated

`YYYY-MM-DD`

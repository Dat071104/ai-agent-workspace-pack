# Agent Ops Index / Muc luc bo nho

Router for this folder. Read this first when you do not know which memory file
you need. Load files in tier order and stop as soon as you can act -- reading
everything here defeats the purpose of the folder.

## Read Order

| Tier | File | Read when | Cost |
| --- | --- | --- | --- |
| 0 | `SESSION_BRIEF.md` | Every managed session. Goal, constraints, current state. | Light |
| 0 | `OPERATING_RULES.md` | Every managed session. Behavior and safety rules. | Light |
| 0 | `CURRENT_TASK.md` | A task is already in progress. Files touched, dead ends, next step. | Light |
| 0 | `HANDOFF.md` | **A previous session handed off.** Read it before anything else when its Status is `open`. | Light |
| 1 | `REPO_MAP.md` | You need to locate code or judge blast radius. **Read before grepping the repo.** | Light |
| 1 | `code_index.json` | Never read directly -- it is machine-sized. Query it with `scripts/explore.py`. | n/a |
| 1 | `LOG_SUMMARY.md` | You need recent history without the full log. | Light |
| 2 | `PROJECT_CONTEXT_CARD.md` | Durable project facts: stack, architecture, business rules, run/test commands. | Medium |
| 2 | `PHASE_ROADMAP.md` | Planning or checking phase order and gates. | Medium |
| 2 | `DECISION_LOG.md` | A past trade-off is relevant to the current choice. | Medium |
| 2 | `RISK_REGISTER.md` | Assessing or adding risk. | Medium |
| 3 | `IMPLEMENTATION_LOG.md` | `LOG_SUMMARY.md` was not enough. Append-only history; tracked, so it survives a clone. | Heavy |
| 3 | `phase_context_cards/` | Working inside one specific phase. | Medium |
| 3 | `archive/` | Investigating something older than the retained log window. | Heavy |
| ref | `SESSION_PROTOCOL.md` | Changing session behavior, or unsure about the closure gate. | Medium |

## Write Triggers

| Event | Update |
| --- | --- |
| Each meaningful step in a task | `CURRENT_TASK.md` |
| Every managed session | `SESSION_BRIEF.md` (state, next step, `Last Verified Commit`) |
| Real implementation, test, or audit evidence | append `IMPLEMENTATION_LOG.md` |
| Durable project or milestone state changed | `PROJECT_CONTEXT_CARD.md` |
| Decision with material trade-offs | `DECISION_LOG.md` |
| New or changed material risk | `RISK_REGISTER.md` |
| Code files moved or added | rebuild `code_index.json`, then regenerate `REPO_MAP.md` |
| Ending a session that another session will continue | `HANDOFF.md` via `handoff-team/` |
| Absorbing a handoff at session start | set `HANDOFF.md` Status to `consumed` |

The root agent owns every file here. Subagents never write to this folder.
Before reporting a task complete, print the Closure Receipt defined in
`SESSION_PROTOCOL.md`.

## Git Tracking (hybrid policy)

Enforced by `_agent_ops/.gitignore`.

| Tracked -- durable memory, should survive a clone | Ignored -- session scratch, machine-local |
| --- | --- |
| `INDEX.md`, `OPERATING_RULES.md`, `SESSION_PROTOCOL.md`, `PROJECT_CONTEXT_CARD.md`, `REPO_MAP.md`, `HANDOFF.md`, `IMPLEMENTATION_LOG.md`, `archive/`, `DECISION_LOG.md`, `RISK_REGISTER.md`, `PHASE_ROADMAP.md`, `phase_context_cards/` | `SESSION_BRIEF.md`, `CURRENT_TASK.md`, `LOG_SUMMARY.md` |

Tracked files are visible to anyone who can read the repository. Never put
secrets, private data, or unverified claims in any file here.

## Helper Scripts

```bash
python scripts/session_start.py --root .                     # read-only session checks
python scripts/generate_repo_map.py --root . \
    --output _agent_ops/REPO_MAP.md --force                  # refresh the code map
python scripts/build_code_index.py --root .                  # rebuild the symbol graph
python scripts/explore.py --symbol <name>                    # callers, callees, flow
python scripts/explore.py --impact <name>                    # blast radius + tests
python scripts/scan_deps.py --root . --seed "<keyword>" --hops 2   # file-level zone
python scripts/summarize_implementation_log.py \
    --log _agent_ops/IMPLEMENTATION_LOG.md --rotate --keep 10 \
    --output _agent_ops/LOG_SUMMARY.md --force               # summarize + archive
```

If Python is unavailable, every one of these has a manual fallback described in
`SESSION_PROTOCOL.md`.

## Last Updated

`YYYY-MM-DD`

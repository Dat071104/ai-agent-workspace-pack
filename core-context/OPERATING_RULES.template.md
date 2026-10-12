# Operating Rules / Quy tac van hanh

Read at the start of every managed session, so it stays short. Universal rules are
NOT repeated here -- a copy drifts from the original:

- `AGENTS.md` (always loaded): behavior and safety rules, advisor persona, coding
  standard, subagent gating, managed-session and Closure Receipt requirements.
- `_agent_ops/SESSION_PROTOCOL.md`: session start, work modes, subagent contract,
  closure gate, Closure Receipt format, commit-time repo-map gate, log rotation.
- `_agent_ops/INDEX.md`: what to read when.

Put only this project's own rules below. If a rule here conflicts with
`AGENTS.md`, the stricter one wins; ask the user when unclear.

## Pointers (do not expand)

- Session start and hot context: `SESSION_PROTOCOL.md` > Session Start.
- Locate code with `_agent_ops/REPO_MAP.md` before grepping.
- Re-anchor to the Session Brief's goal, non-goals, and constraints before an
  edit, scope expansion, or final conclusion.
- A task prompt controls the requested work, not durable recordkeeping. Classify
  actual work under `SESSION_PROTOCOL.md` and print the Closure Receipt; an
  omitted filename is never a valid not-needed reason.
- Authorized commit with staged project code: `SESSION_PROTOCOL.md` > Commit-Time
  Repo Map Gate (`refresh_repo_map.py --stage`; never `--no-verify`).

## Testing

- Run the smallest meaningful test first; add broader tests when touching shared
  behavior.
- Record commands and results in the implementation log.
- Project test command: `<fill in>`

## Commit Rules

- Commit only when the user allowed it, after validation passes, with a clear
  message. Push only when requested.

## Safety

- Ask before major structure creation unless the user explicitly requested
  autonomous execution.
- For high-risk cleanup, use `clean-code-team/`.

## Project-Specific Rules

- `<language, style, naming, or framework conventions>`
- `<zones not to edit without confirmation>`
- `<other house rules; delete this section if none>`

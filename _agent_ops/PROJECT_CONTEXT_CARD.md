# Project Context Card / The ngu canh du an

## Project Name

`ai-agent-workspace-pack`

## One-Paragraph Summary

English: `A reusable, cross-harness operating kit that provides agent routing, managed project context, and deterministic repository tools for coding projects.`

Vietnamese: `Bo cong cu van hanh tai su dung cho AI coding agent, phuc vu viec route team, luu ngu canh va kiem tra repository an toan.`

## Current Phase / State

`Bridge v1.1 implemented and locally validated; namespaced embedded layout remains a planned v2 migration.`

Update this section when a durable phase or gate becomes accepted, rejected, or
blocked, even when the task prompt only names task-level files. Put detailed
commands and raw outcomes in IMPLEMENTATION_LOG.md; keep this card to the
current durable state.

## Tech Stack

- Language: Python, Markdown
- Framework: stdlib command-line tools and portable instruction templates
- Runtime: Python 3
- Database: none
- Test tools: unittest (`python -B tests/test_workspace_tools.py`)

## Architecture

`Root instructions route work to one team; scripts initialize _agent_ops and generate deterministic code-navigation artifacts; core-context supplies durable templates. The init script owns managed bridge changes, while host-owned AGENTS.md text outside bridge markers remains untouched.`

See `_agent_ops/REPO_MAP.md` for the generated module table, hot files, and
entry points. Describe here only what a scanner cannot infer: intent,
boundaries, and the reasons behind the structure.

## Business Rules & Acceptance Criteria

`Embedded installation must never overwrite host instructions and must make @start-here discoverable after an explicit bridge install.`

- Rule: `Bridge ownership is marker-bounded.` -> Accept when: `install/check lifecycle tests preserve host text and report structural status.`

Note: if this section is empty, the agent must ask before implementing logic, to
avoid code that is syntactically right but semantically wrong.

## Key Decisions

- `Use a managed AGENTS bridge v1.1 before any layout migration, because it fixes the current discoverability gap without changing existing embedded paths.`

## Current Branch / Commit

- Branch: `main`
- Commit: `27e5e7c` at validation start; bridge commit pending.

## How to Run

```bash
python scripts/init_project_ops.py --target <project>
```

## How to Test

```bash
python -B tests/test_workspace_tools.py
```

## Known Risks

- Flat embedded layout can still collide with host directories; defer namespace migration to a separately tested v2 change.

## Next Step

`Commit the verified bridge v1.1 change; later design and test .ai-agent-workspace-pack/ as a compatible v2 layout.`

## Do Not Do

- Do not overwrite host-owned AGENTS.md text or infer natural-language policy conflicts.
- Do not overwrite host harness configuration during the future migration.

## Last Verified Commit

`27e5e7c`

## Last Updated

`2026-08-27`

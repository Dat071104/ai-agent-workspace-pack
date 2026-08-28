# Project Context Card / The ngu canh du an

## Project Name

`ai-agent-workspace-pack`

## One-Paragraph Summary

English: `A reusable, cross-harness operating kit that provides agent routing, managed project context, and deterministic repository tools for coding projects.`

Vietnamese: `Bo cong cu van hanh tai su dung cho AI coding agent, phuc vu viec route team, luu ngu canh va kiem tra repository an toan.`

## Current Phase / State

`Namespaced embedded-pack v2 is feature-complete locally and validated. embed_pack.py materializes a clean ai-agent-workspace-pack/ directory with fresh nested project operations, the root AGENTS.md begins with a preserving bridge, and generated root pointers under .codex/agents/, .claude/agents/, and .claude/skills/ restore the four subagents and nine team skills that root-only harness discovery would otherwise lose. The symbol index now excludes a nested pack, matching REPO_MAP.md. Copying the pack folder into a project and running its own bootstrap command now selects the namespaced layout automatically. Released at ad6f01c on origin/main. TASK-0004 then closed the two carried-over defects: a repository with no commits is reported as a repository, and the ambiguous root-level pack exclusion was removed in favour of migration, restoring this pack's own repo map to 13 indexed files.`

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

`Root instructions route work to one team; scripts initialize project operations and generate deterministic code-navigation artifacts; core-context supplies durable templates. The init script owns both the legacy marker bridge and the namespaced first-line bridge, while host-owned AGENTS.md text remains untouched after that first line.`

See `_agent_ops/REPO_MAP.md` for the generated module table, hot files, and
entry points. Describe here only what a scanner cannot infer: intent,
boundaries, and the reasons behind the structure.

## Business Rules & Acceptance Criteria

`Embedded installation must preserve host instructions and make the copied pack discoverable without spreading its folders into the application root.`

- Rule: `Namespaced bridge ownership is first-line bounded.` -> Accept when: `install/check lifecycle tests preserve host text exactly after the link and report structural status.`
- Rule: `Nested ops are operational.` -> Accept when: `session-start, code-map refresh, and pre-commit staging work from ai-agent-workspace-pack/_agent_ops/.`

Note: if this section is empty, the agent must ask before implementing logic, to
avoid code that is syntactically right but semantically wrong.

## Key Decisions

- `Use a namespaced embedded layout for new copies while retaining the legacy flat bridge for compatibility.`

## Current Branch / Commit

- Branch: `main`
- Commit: `403e7a4` namespaced embedded v2 local release; push remains unrequested.

## How to Run

```bash
python D:\path\to\ai-agent-workspace-pack\scripts\embed_pack.py --target .
```

## How to Test

```bash
python -B tests/test_workspace_tools.py
```

## Known Risks

- Root harness entry files are still required for automatic discovery, but pack folders and ops state no longer collide with host directories.

## Next Step

`Push the verified v2 pack change only when authorized.`

## Do Not Do

- Do not overwrite host-owned AGENTS.md text or infer natural-language policy conflicts.
- Do not overwrite host harness configuration during an embedded install.

## Last Verified Commit

`403e7a4`

## Last Updated

`2026-08-28`

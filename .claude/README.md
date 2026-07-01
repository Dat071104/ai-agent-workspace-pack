# Claude Code Adapter

Auto-discovery layer for Claude Code. These files are thin adapters; the team
folders at the repo root are the single source of truth.

- `agents/` — four real subagents: `tester`, `bug_hunter`, `bug_fixer`,
  `repo_hygiene_reviewer`. Each points back to its team `SKILL.md`.
- `skills/<team>/SKILL.md` — pointer skills so Claude Code can discover each team
  by metadata. They redirect to `<team>/SKILL.md` at the root.

Do not duplicate workflow content here. When a team's process changes, edit the
root team folder only.

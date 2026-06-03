# Commands

Short copy-paste prompts for common AI-agent workflows.

Use these when you want to start a new agent session without reading many files. Paste the command into Codex, Cursor, Claude Code, Windsurf, or another coding agent, then replace the placeholders.

Vietnamese note: Day la cac prompt ngan de copy vao agent. Nen bat dau bang `start-session.md` neu chua biet dung team nao.

## Recommended First Command

Start with `start-session.md` for broad or unclear requests. It tells the agent to read only the short entry docs, route the task, warn about token/risk, and wait before writing files.

## Command Selection

| Command | Use when | Team |
| --- | --- | --- |
| `start-session.md` | Starting a new broad session | Router first |
| `route-task.md` | Choosing the right team | Router first |
| `analyze.md` | Idea, architecture, roadmap, options | `analyze-team/` |
| `prompt.md` | Create a phase, audit, harness, or handoff prompt | `prompting-team/` |
| `test-full.md` | Full project audit | `tester-team/` |
| `test-scoped.md` | Scoped feature/folder/phase audit | `tester-team/` |
| `fix-bug.md` | Verify and plan a bug fix | `bug-fix-team/` |
| `clean-code.md` | High-risk cleanup audit and batch plan | `clean-code-team/` |
| `handoff.md` | End-session or next-session report | `handoff-team/` |
| `release-check.md` | Public repo and release readiness | `repo-hygiene-team/`, `tester-team/` |

## Rules Shared by Commands

- Chat first, files later.
- Do not read every team folder.
- Never use `git add .`.
- Warn before Heavy or Very Heavy work.
- Ask before file writes, commits, pushes, destructive actions, or broad changes.


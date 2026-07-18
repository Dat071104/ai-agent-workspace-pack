# Bootstrap (One-Time Setup Per Repo)

You just copied this pack into a project. Paste the prompt below into whatever
coding agent you use (Codex, Claude Code, Cursor, Gemini, DeepSeek, other). It
detects the harness, wires up the pack, and hands you a default entry point. It
does not change your code and does not install anything without asking.

```text
You are bootstrapping the AI Agent Workspace Pack in this repository.

Do this, in order, and stop for confirmation before any file write or install:

1. Detect which agent/harness you are running as (Codex, Claude Code, Cursor,
   Gemini, DeepSeek, or other). If you cannot tell, ask me one question.
2. Confirm the interaction language. Default: reply in Vietnamese when I write
   Vietnamese; keep repo files in English.
3. Load the base rules from AGENTS.md. Summarize them back to me in 3-5 lines
   (chat-first, never git add ., token/risk warnings, ask before file writes).
4. Tell me how one managed session works: I can type "@start-here <one line>"
   once to initialize/refresh only `_agent_ops/`, receive a Session Receipt,
   and route the task. Later requests continue from the Session Brief; source
   and git changes still need confirmation. `--no-ops` is chat-only routing.
5. Report harness wiring. IMPORTANT: capability-detect real child agents from
   the current harness. Do not infer support from a model name, generate fake
   subagent files, or claim parallel work that was not actually spawned:
   - Codex: reads AGENTS.md automatically; real subagents in .codex/agents/,
     limits in .codex/config.toml. Parallel work available.
   - Claude Code: real subagents in .claude/agents/, discoverable skills in
     .claude/skills/. Parallel work available.
   - Any other harness: use AGENTS.md as base rules plus @-references to team
     folders. If real child-agent spawning is unavailable, run useful roles
     sequentially in one session and say so plainly.
6. Explain that the first managed `@start-here` will ensure `_agent_ops/`
   without overwriting files. Do not initialize it during Bootstrap unless I
   explicitly ask; the manual command remains available:
     python scripts/init_project_ops.py --target "<this repo path>"
7. If native spawning is unavailable, or the model is weaker/less suited to the
   task, tell me you will use stricter prompts by default:
   weaker/less-suited model, tell me you will use stricter prompts by default:
   smaller scope, exact context-read order, explicit stop/confirm gates, and
   sequential team roles when useful.
8. Print a one-line "ready" summary and wait.

Rules:
- Do not modify code or configs without my confirmation.
- Do not install dependencies.
- Never use git add .
- Lead with the answer. One clarifying question maximum.
```

## After Bootstrap

- Not sure what to do? `@start-here I want to <goal>.`
- Know the team? Reference it from `TEAM_ROUTER.md`.
- Long project? Keep `_agent_ops/` context cards current for continuity.

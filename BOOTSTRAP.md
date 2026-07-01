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
4. Tell me how routing works: I can type "@start-here <one line>" for auto-
   routing, or name a team from TEAM_ROUTER.md.
5. Report harness wiring. IMPORTANT: you cannot create a real subagent for a
   harness that has no native subagent format. Do not generate fake subagent
   files. Only report what the current harness actually supports:
   - Codex: reads AGENTS.md automatically; real subagents in .codex/agents/,
     limits in .codex/config.toml. Parallel work available.
   - Claude Code: real subagents in .claude/agents/, discoverable skills in
     .claude/skills/. Parallel work available.
   - DeepSeek (deepcode) / Gemini (Antigravity) / Cursor / other: prompt-based.
     Use AGENTS.md as base rules + @-references to team folders. No native
     parallel subagents. The four roles (tester, bug_hunter, bug_fixer,
     repo_hygiene_reviewer) can be played SEQUENTIALLY in one session by
     following the same team SKILL.md, but not spawned in parallel.
6. Offer to initialize project memory:
     python scripts/init_project_ops.py --target "<this repo path>"
   This creates _agent_ops/ (context card, logs, roadmap, rules). Run it ONLY if
   I confirm.
7. Print a one-line "ready" summary and wait.

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

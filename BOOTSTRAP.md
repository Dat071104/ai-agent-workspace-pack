# Bootstrap (One-Time Setup Per Repo)

## Install / Cai dat

Run from your project root. Either way the pack ends up in ONE folder,
`<project>/ai-agent-workspace-pack/`, with the project memory in
`ai-agent-workspace-pack/_agent_ops/`.

**A. Recommended: install from a source pack** (a clone or download kept anywhere
outside your project):

```bash
python <path-to-pack>/scripts/embed_pack.py --target .
```

It copies only the shipped pack files (an allowlist, Git-tracked only when the
source is its own repository; never `.env`, virtualenvs, `tests/`, `examples/`, or
the source pack's own `_agent_ops/`), writes `PACK_VERSION` and
`PACK_MANIFEST.json`, creates fresh project memory, adds a marked block to your
root `AGENTS.md` (every line of yours is kept), and writes the root `CLAUDE.md`
and `GEMINI.md` adapters (only if absent) and the `.claude/` / `.codex/` pointer
files.

**B. Copy-paste**: copy the pack folder to `<project>/ai-agent-workspace-pack/`,
then from the project root:

```bash
python ai-agent-workspace-pack/scripts/embed_pack.py --target .
```

Run from inside the copy, `embed_pack.py` installs **in place**: it copies
nothing, finishes the install (manifest, memory, `AGENTS.md` block, adapters) and
reports files it did not treat as pack content (for example `tests/`, `examples/`)
without deleting them. Do not copy the source pack's `_agent_ops/` along: it is
that pack's own memory, not yours.

**C. If it prints `BLOCKED` (exit 3)**: the `_agent_ops/` it found is not proven
to be this project's (typically copied along with the folder, or installed
before ownership stamps existed). Nothing was written.
Run one of the commands it prints, from the project root:

```bash
python ai-agent-workspace-pack/scripts/init_project_ops.py --target . --embedded-folder ai-agent-workspace-pack --reset-memory
python ai-agent-workspace-pack/scripts/init_project_ops.py --target . --embedded-folder ai-agent-workspace-pack --claim-memory
```

`--reset-memory` backs up every memory file to `_agent_ops/backups/<timestamp>/`
(gitignored, never deleted) and starts from fresh templates. `--claim-memory` keeps
the records and makes them this project's (for example after a Git history
rewrite changed the root commit). `--claim-memory` is also the one-time step
for a pre-stamp install. A folder of untouched templates needs no flag.
Nothing is lost either way (reset backs up first); choose deliberately.

Afterwards commit `ai-agent-workspace-pack/_agent_ops/OPS_OWNER.json`: it is what
lets a clone of your repository keep its memory and a copy elsewhere be refused.
Update later with `embed_pack.py --target . --update` (see `README.md`).
Flat install with no folder (`python scripts/init_project_ops.py --target .`) and
runtime-only mode are described in `README.md`.

## Bootstrap prompt

You just installed this pack into a project. Paste the prompt below into whatever
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
     python ai-agent-workspace-pack/scripts/init_project_ops.py --target .
   Say what that creates: session memory, plus a generated `REPO_MAP.md` (the
   code map read instead of grepping the repo), a `CURRENT_TASK.md` working
   memory that survives context compaction, an `_agent_ops/.gitignore` that
   tracks durable memory while keeping session scratch local, a copy of the
   tools in `_agent_ops/tools/` so this repo runs them with no pack present,
   and an `AGENTS.md` at the repo root if it does not already have one.
   Also report whether Python is available here. If it is, the deterministic
   session checks run as `python _agent_ops/tools/session_start.py --root .`
   once `_agent_ops/` exists (`python scripts/session_start.py --root .` from
   inside the pack before that; for a namespaced install the tools live at
   `ai-agent-workspace-pack/_agent_ops/tools/`); if not, say that the manual fallback in
   `SESSION_PROTOCOL.md` will be used instead.
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

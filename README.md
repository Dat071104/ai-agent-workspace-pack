# AI Agent Workspace Pack

Reusable operating kit for AI-assisted software projects.

This repository helps coding agents such as Codex, Cursor, Claude Code, Windsurf, and similar tools plan, prompt, test, fix, clean up, and hand off coding projects with safer defaults and better continuity.

Vietnamese note: Day la bo cong cu dung lai cho cac du an code voi AI agent. Neu ban viet tieng Viet, agent nen tra loi bang tieng Viet.

## Use This First

Most users should start with `START_HERE.md` or this README. You do not need to read every folder. The pack is designed for progressive disclosure: load a short entry file first, then only load the team folder that matches your task.

Recommended first prompt:

```text
@start-here I want to [describe goal].
Route me to the right team, ask clarifying questions, and do not write files until I confirm.
```

If you only want to chat with an agent, say that clearly:

```text
I only want a chat report. Do not create or modify files.
```

## What This Repo Is

`ai-agent-workspace-pack` is a public-friendly support layer for coding projects. It is not a framework, not a CLI package, and not tied to one product. It gives users a repeatable way to:

- store project memory,
- plan implementation phases,
- create high-quality prompts,
- audit and test work,
- triage bugs before fixing,
- run risky cleanup with safeguards,
- keep repositories clean for public release,
- hand off work between AI-agent sessions.

## Who It Is For

- Developers using Codex as the main coding agent.
- Users working with Cursor, Claude Code, Windsurf, or similar tools.
- Non-technical users and early students who want clearer AI help.
- Public repo maintainers who want reusable AI-agent rules without private logs.

## How the Agent Should Behave

1. Route the task first.
2. Ask questions if context is missing.
3. Show options, risks, and expected output.
4. Recommend a path.
5. Ask before writing or modifying files.
6. Update logs only after permission.
7. Keep reports concise and honest.

## Chat-First, File-Later Rule

For analysis, planning, prompting, audit, bug triage, and clean-code:

1. Answer in chat first.
2. Say what was understood.
3. Say what context is missing.
4. Ask clarifying questions when needed.
5. Show options and risks.
6. Show expected output.
7. Ask user confirmation before writing or modifying files.

Only write files when the user explicitly allows it or the confirmed mode is autonomous.

## Team Router Overview

Use `TEAM_ROUTER.md` before reading long team folders.

| User intent | Recommended team | Token/risk | Writes files by default? |
| --- | --- | --- | --- |
| Overview: what to improve next, priorities, ROI | `advisor-team/` | Medium | No |
| Idea, architecture, options, roadmap | `analyze-team/` | Medium | No |
| Create prompt, harness, phase prompt | `prompting-team/` | Medium to Very Heavy | No |
| Test, audit, QA, production readiness | `tester-team/` | Medium to Very Heavy | No |
| Bug report or suspected broken behavior | `bug-fix-team/` | Medium | No |
| Cleanup, refactor, messy repo | `clean-code-team/` | Very Heavy | No |
| Git safety, public repo, release | `repo-hygiene-team/` | Light to Medium | No |
| Handoff, report, continue later | `handoff-team/` | Light to Medium | No |

Router-first rule: do not read every team folder. Route the request, explain why, and ask whether to proceed.

## Quickest Way to Use This Pack

1. Attach or reference `START_HERE.md`.
2. Describe your goal in plain language.
3. Ask the agent to route the task.
4. Confirm the recommended team.
5. Let the agent produce a chat report first.
6. Approve file writes only when you are ready.

## Recommended Startup Prompt

Use the `@start-here` auto-router (see `commands/start-here.md`). It reads only
the short entry files, so the agent stays light on context. This README is a
human guide; you do not need to attach it.

```text
@start-here I want to build a web app.
Route me to the right team, ask clarifying questions, classify token/risk level, and do not write files until I confirm.
```

## For Non-Technical Users

You do not need exact technical terms. Say what you want to build, what problem it solves, who will use it, and what you are worried about.

Good first request:

```text
I want to build a small app for tracking personal expenses. I am not sure what tech stack to use. Please give me 3 options and recommend one. Do not create files yet.
```

The teams help like this:

- `advisor-team/` acts like a senior mentor: what to improve first and how hard it is.
- `analyze-team/` turns ideas into options and a plan.
- `prompting-team/` creates strong prompts for Codex or another agent.
- `tester-team/` checks the result like a QA/product team.
- `bug-fix-team/` verifies bugs safely before changing code.

The agent should avoid jargon, explain expected results, give A/B/C choices, and warn before expensive or risky actions.

## For Advanced Users

- Use `commands/` directly for common workflows.
- Reference a specific team folder when you already know what you need.
- Use `scripts/init_project_ops.py` to create project memory.
- Use `scripts/scan_deps.py` for lightweight affected-area scanning.
- Use `scripts/check_repo_hygiene.py` before release.
- Use autonomous mode only after explicit confirmation.

## Folder Overview

| Folder/File | Purpose |
| --- | --- |
| `START_HERE.md` | Short user-first entry guide. |
| `BOOTSTRAP.md` | One-time per-repo setup prompt (detects harness). |
| `TEAM_ROUTER.md` | Routing table for choosing the right team. |
| `AGENTS.md` | Short always-on agent rules + subagent + persona. |
| `.claude/` | Claude Code adapter: subagents + discoverable skills. |
| `.codex/` | Codex adapter: subagents + fan-out limits. |
| `core-context/` | Project memory templates. |
| `advisor-team/` | Senior-advisor overview: prioritize improvements by value, estimate difficulty. |
| `analyze-team/` | Clarification, options, architecture, roadmap. |
| `prompting-team/` | Prompt and harness creation. |
| `tester-team/` | Audit and testing only. |
| `bug-fix-team/` | Bug verification and minimal fix planning. |
| `clean-code-team/` | High-risk cleanup workflow. |
| `repo-hygiene-team/` | Git safety, public repo, release checks. |
| `handoff-team/` | Continuity and final reports. |
| `commands/` | Short copy-paste prompts. |
| `harness/` | Matrices and checklists. |
| `scripts/` | Lightweight Python helpers. |
| `examples/` | Generic public-safe examples. |

## Initialize a Target Project

Run:

```bash
python scripts/init_project_ops.py --target "D:\MyProject"
```

Optional custom folder:

```bash
python scripts/init_project_ops.py --target "D:\MyProject" --ops-folder "_project_memory"
```

This creates project memory files such as `PROJECT_CONTEXT_CARD.md`, `IMPLEMENTATION_LOG.md`, `DECISION_LOG.md`, `RISK_REGISTER.md`, `PHASE_ROADMAP.md`, and `OPERATING_RULES.md`.

Existing files are not overwritten unless `--force` is passed.

## Prompt Readiness Gate

Before generating a large Codex, Cursor, Claude Code, Windsurf, or autonomous execution prompt, use `prompting-team/PROMPT_READINESS_GATE.md`.

Check:

- Is context enough?
- Is the project context card available?
- Is the implementation log available?
- Is expected output defined?
- Are test and audit gates included?
- Is git safety included?
- Is token/risk level acceptable?
- Should another team be used first?
- Does the user need to confirm before autonomous work?

## Token and Risk Levels

Use `harness/TOKEN_RISK_MATRIX.md`.

| Level | Typical work |
| --- | --- |
| Light | Route task, short handoff, simple hygiene check. |
| Medium | Analysis, scoped prompt, bug triage, scoped audit. |
| Heavy | Multi-phase prompt, broad audit, production-readiness review. |
| Very Heavy | Clean-code, full codebase audit, multi-phase autonomous execution prompt. |

Very Heavy work should use the strongest available model and explicit confirmation.

## Skill Suggestion Philosophy

Agents may suggest skills or teams, but must not force them.

Example:

```text
This task may benefit from tester-team after Phase 2 because integration risk is high. Use tester-team now? yes/no.
```

## Modes

| Mode | Behavior |
| --- | --- |
| Safe mode | Read and report only. No file changes. |
| Confirm-to-act mode | Inspect and propose, then ask before file changes. |
| Autonomous mode | Edit/test/commit only after explicit user confirmation. |

## Git Safety Rules

- Never use `git add .`.
- Run `git status --short` before and after changes when in a git repo.
- Stage explicit files only.
- Do not commit secrets, local logs, generated artifacts, databases, model files, or private data.
- Commit only after validation passes and only if the user allowed it.
- Push only when the user requested it and the remote/branch are clear.

## Implementation Log Philosophy

Implementation logs are append-only. They should capture what changed, why, files touched, tests run, results, bugs found, fixes applied, commit hash, remaining risks, and next step.

Vietnamese note: Log giup phien lam viec sau hieu trang thai that cua du an.

## Phase and Part Consistency Audits

After every 2-3 phases, after a major part, or before a critical milestone, consider:

- consistency audit across completed parts,
- integration audit,
- production-readiness audit.

These audits are suggested, not forced.

## How to Avoid Reading Too Many Files

1. Start with `START_HERE.md`, `AGENTS.md`, and this README.
2. Use `TEAM_ROUTER.md`.
3. Load only the selected team folder.
4. Use `core-context/SESSION_BRIEF.template.md` in target projects to summarize the session.
5. Ask for a chat report before file changes.

## Failure-Mode Guards (Embedded Per Team)

To keep global context light, guards against common agent failure modes live
inside the team `SKILL.md` that needs them, not in a single always-loaded file.
They only load when you enter that team:

- `bug-fix-team/`: re-anchor to the original goal (anti-drift), verify a symbol
  exists before calling it (anti-hallucination), and check base-branch
  divergence before editing (merge safety).
- `tester-team/`: security audit (secrets, injection, authz) and observability
  gaps (missing logs/metrics on failure paths), report-only.
- `clean-code-team/`: dependency-drift guard and a "improve structure, do not
  copy-paste" rule.
- `core-context/`: `PROJECT_CONTEXT_CARD` carries business rules and acceptance
  criteria (anti "compiles but wrong"); `SESSION_BRIEF` pins the original goal.

This is deliberate: one prompt per team means each guard is present exactly when
relevant and absent when not.

## Use with Codex

Place `AGENTS.md` at the repository root. In a new session, reference `START_HERE.md` and ask Codex to route the request before loading team folders. For long projects, initialize `_agent_ops/` and keep context cards current.

## Use with Cursor, Claude Code, or Windsurf

Use `AGENTS.md` as the always-on instruction source if supported. Otherwise paste `commands/start-session.md` or `commands/route-task.md`. Keep project memory in `_agent_ops/` so different agents can share context.

See **Per-Harness Setup** below for exact per-tool invocation, including DeepSeek
(deepcode) and Gemini (Antigravity), plus copy-paste examples.

## Per-Harness Setup

This pack is portable. The **team folders are the single source of truth**;
`AGENTS.md` is the shared base rules every harness reads. Each harness gets a
thin adapter (or just `@`-references) that points back to the team folders.

### What "subagent" means here (read this first)

A **real subagent** is a separate process the harness spawns and can run in
**parallel**. This is a harness feature, not a prompt trick. Only **Codex** and
**Claude Code** have a native subagent format in this pack. For every other tool,
"subagent" is only a **role played sequentially** by one agent in one session —
same SKILL, no parallelism. No prompt (including `@start-here`) can generate a
real subagent for a tool that lacks the native format.

### Capability matrix

| Harness | Base rules | How to invoke a team | Real parallel subagents? | Discovery |
| --- | --- | --- | --- | --- |
| **Codex** | `AGENTS.md` (auto) | `@bug-fix-team/SKILL.md` or a `.codex` subagent | Yes (`.codex/agents/*.toml`, capped by `.codex/config.toml`) | Automatic |
| **Claude Code** | `AGENTS.md` | Skill is discoverable, or spawn a `.claude` subagent | Yes (`.claude/agents/*.md`) | `.claude/skills/` |
| **DeepSeek (deepcode CLI)** | `AGENTS.md` | `@tester-team/SKILL.md` (paste reference) | No — sequential role-play only | Manual `@`-reference |
| **Gemini (Antigravity)** | `AGENTS.md` | `@tester-team/SKILL.md` (paste reference) | No — sequential role-play only | Manual `@`-reference |
| **Cursor / Windsurf / other** | `AGENTS.md` | `@<team>/SKILL.md` (paste reference) | No — sequential role-play only | Manual `@`-reference |

The four roles are: `tester` and `repo_hygiene_reviewer` (read-only),
`bug_hunter` (read-only, probes one fix direction), `bug_fixer` (write, applies a
confirmed fix). On Codex/Claude they run in parallel after a token warning; on
prompt-based tools they run one after another in the same chat.

For DeepSeek, Gemini, Cursor, other prompt-based harnesses, or a model you know
is weaker or less suited to the task, use the stricter prompt profile from
`prompting-team/`: smaller scope, explicit context-read order, concrete
stop/confirm gates, and ordered team chains when useful. This costs more prompt
text and more checkpoints, but reduces missed context and scope drift.

### New repo, any harness

Run `BOOTSTRAP.md` once: paste its prompt into your agent. It detects the harness,
summarizes the rules, tells you exactly how to invoke teams there, and offers to
initialize `_agent_ops/`. It will **not** fabricate subagent files for a tool that
has no native format. Then, when unsure which team to use, type
`@start-here <one line>` and the agent routes you and suggests the exact
`@reference` for your harness.

### Copy-paste per harness

**Codex** — `AGENTS.md` is read automatically. Route, then invoke by reference or subagent:
```text
@start-here I need to audit this repo before release.
```
Parallel audit (Codex spawns real subagents; approve after the token warning):
```text
Run the tester and repo_hygiene_reviewer subagents in parallel on this repo,
then merge into one prioritized list. Do not edit files.
```
If your Codex build lacks TOML subagents: delete `.codex/agents/`, keep
`.codex/config.toml`, and invoke the roles by prompt instead.

**Claude Code** — skills in `.claude/skills/` are discoverable; subagents in `.claude/agents/`:
```text
@start-here I found a bug where login sometimes returns 500.
```
Spawn a subagent explicitly when you want isolation/parallelism:
```text
Use the bug_hunter subagents to probe each fix direction in parallel, then have
one bug_fixer apply the confirmed fix after I approve.
```

**DeepSeek (deepcode CLI)** — no native subagents. Load base rules, then reference the team:
```text
@AGENTS.md
@tester-team/SKILL.md
Audit the auth module. Report findings by severity. Do not edit files.
Use stricter scope: read AGENTS.md, project context card, implementation log,
then only auth-related source/tests/config. Play tester and repo_hygiene_reviewer
roles sequentially (no parallelism here). Stop before expanding scope.
```

**Gemini (Antigravity)** — same pattern; `AGENTS.md` as base, `@`-reference the team:
```text
@AGENTS.md
@bug-fix-team/SKILL.md
Verify this bug first, give me 2-3 fix directions with trade-offs, recommend one.
Use stricter scope: read AGENTS.md, project context card, implementation log, and
only the files needed to reproduce the bug. Do not edit until I confirm.
```

**Cursor / Windsurf / other** — set `AGENTS.md` as the always-on rules if
supported, otherwise paste `commands/start-session.md`. Invoke teams with
`@<team>/SKILL.md`. Keep project memory in `_agent_ops/` so tools share context.

## Pros and Cons

| Pros | Cons |
| --- | --- |
| Reusable workflow across projects. | Not a magic production guarantee. |
| Safer AI coding defaults. | Can still be token-heavy. |
| Better continuity across sessions. | Requires user discipline. |
| Phase and audit discipline. | Clean-code mode is risky. |
| Useful for non-technical users. | Scripts are lightweight, not full language-server tools. |
| Helps reduce forgotten context. | Prompts need adaptation per project. |
| Supports multiple agents. | Too many rules can slow small tasks. |

## Common Mistakes

- Loading every team folder at session start.
- Asking for clean-code before creating a recovery point.
- Letting bug-fix work start before verifying the bug.
- Running full audits when a scoped audit is enough.
- Forgetting to update implementation logs.
- Using `git add .`.

## When Not to Use This Pack

- Tiny one-off tasks where a direct answer is enough.
- Projects where no AI-agent workflow is needed.
- Repositories with sensitive data unless you first remove or protect that data.
- Emergency production fixes where the process overhead would slow a known safe fix.

## What This Pack Does Not Do

- It does not replace human review.
- It does not guarantee bug-free code.
- It does not enforce policy through a full CLI package.
- It does not include private project logs.
- It does not install external dependencies.
- It does not automatically push or publish code.

## Suggested Public Repo Usage

- Keep this pack generic.
- Do not add private implementation logs.
- Keep examples neutral and concise.
- Prefer Markdown templates and small scripts.
- Add CI later only when the repo stabilizes.

## v1.1 Refinement Notes

v1.1 improves the user and agent experience without adding many folders. It adds a user-first entry guide, a team router, session-start commands, prompt readiness gate, session brief template, and token/risk matrix. It also reinforces progressive disclosure, chat-first/file-later behavior, non-technical user support, and clean-code safeguards.

## Roadmap

- Add script unit tests.
- Add more realistic examples.
- Add optional CI for structure and script checks.
- Done: Codex/Claude Code adapter files and real subagents (`.codex/`, `.claude/`).
- Add optional packaging or plugin/marketplace distribution if real use justifies it.
- Add prompt quality benchmarks and examples.

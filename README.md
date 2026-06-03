# AI Agent Workspace Pack

Reusable operating kit for AI-assisted software projects.

This repository helps coding agents such as Codex, Cursor, Claude Code, Windsurf, and similar tools plan, prompt, test, fix, clean up, and hand off coding projects with safer defaults and better continuity.

Vietnamese note: Day la bo cong cu dung lai cho cac du an code voi AI agent. Neu ban viet tieng Viet, agent nen tra loi bang tieng Viet.

## Use This First

Most users should start with `START_HERE.md` or this README. You do not need to read every folder. The pack is designed for progressive disclosure: load a short entry file first, then only load the team folder that matches your task.

Recommended first prompt:

```text
@START_HERE.md
I want to [describe goal].
Please route me to the right team, ask clarifying questions, and do not write files until I confirm.
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

```text
@README.md
@AGENTS.md
@START_HERE.md

I want to build a web app.
Please route me to the right team, ask clarifying questions, classify token/risk level, and do not write files until I confirm.
```

## For Non-Technical Users

You do not need exact technical terms. Say what you want to build, what problem it solves, who will use it, and what you are worried about.

Good first request:

```text
I want to build a small app for tracking personal expenses. I am not sure what tech stack to use. Please give me 3 options and recommend one. Do not create files yet.
```

The teams help like this:

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
| `TEAM_ROUTER.md` | Routing table for choosing the right team. |
| `AGENTS.md` | Short always-on agent rules. |
| `core-context/` | Project memory templates. |
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

## Use with Codex

Place `AGENTS.md` at the repository root. In a new session, reference `START_HERE.md` and ask Codex to route the request before loading team folders. For long projects, initialize `_agent_ops/` and keep context cards current.

## Use with Cursor, Claude Code, or Windsurf

Use `AGENTS.md` as the always-on instruction source if supported. Otherwise paste `commands/start-session.md` or `commands/route-task.md`. Keep project memory in `_agent_ops/` so different agents can share context.

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
- Add Cursor/Claude/Windsurf-specific adapter files.
- Add optional packaging or installer if real use justifies it.
- Add prompt quality benchmarks and examples.


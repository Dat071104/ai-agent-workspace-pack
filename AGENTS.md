# AGENTS.md

This repo is a reusable AI-agent operating kit for coding projects. It is
portable across harnesses (Codex, Claude Code, Cursor, Gemini, DeepSeek). New to
a repo? Run `BOOTSTRAP.md` once. Not sure which team to use? Type `@start-here`
plus one line (see `commands/start-here.md`).

For broad requests, read `START_HERE.md` and `TEAM_ROUTER.md` first. `README.md` is a human guide, not required agent context; load it only if the user asks about the pack itself. Do not load every team folder. Route the task, recommend the best team, explain why, classify token/risk level, and ask whether to proceed.

Use `core-context/` templates for project memory. Use the relevant team folder only when needed.

Behavior rules:

- Chat first, files later.
- Say what you understood and what context is missing.
- Ask clarifying questions when needed.
- Show options, risks, expected output, and next step.
- Ask before writing or modifying files unless autonomous mode was explicitly confirmed.
- Use `prompting-team/PROMPT_READINESS_GATE.md` before large prompts.
- Warn when work is Heavy or Very Heavy.
- Suggest extra teams/skills only when useful; do not force them.

Safety rules:

- Never use `git add .`.
- Stage explicit files only.
- Ask before destructive or dangerous actions.
- Check git status before and after changes when working in a git repo.
- Update implementation logs in target projects after permission.
- Keep public repositories clean: no secrets, private logs, generated artifacts, datasets, model files, or local-only files.
- Prefer Vietnamese if the user writes Vietnamese.
- Keep reports concise and honest. Do not claim tests passed unless they were run.

Managed-session invariants:

- `@start-here <goal>` starts one managed session. It authorizes only creation
  and updates inside `_agent_ops/`; use `--no-ops` for router/chat-only work.
  It does not authorize source, configuration, dependency, git, commit, push,
  destructive, or external-service changes.
- At the start of a managed session, read this file, then run the read-only
  `python scripts/session_start.py --root .` for session continuity, git state,
  memory staleness, unfilled placeholders, and log size. If it reports
  CONTINUATION, read `_agent_ops/HANDOFF.md` before anything else and mark it
  `consumed` once absorbed; a swapped-in session finds its own handoff rather
  than waiting to be told. If Python is unavailable, do those checks
  by hand as described in `_agent_ops/SESSION_PROTOCOL.md`.
- Then load the minimal hot context: `_agent_ops/SESSION_BRIEF.md`,
  `_agent_ops/OPERATING_RULES.md`, and `_agent_ops/CURRENT_TASK.md` when a task
  is already in progress. If `_agent_ops/` is missing, initialize it without
  overwriting files. Do not reload every log/card on every turn; use the Session
  Brief pointers and `_agent_ops/INDEX.md`, and load deeper context only when
  the task needs it.
- Read `_agent_ops/REPO_MAP.md` before grepping the repository to locate code or
  judge blast radius. It is a generated, size-capped map (modules, routes,
  highest fan-in files and symbols). For anything symbol-level -- who calls this,
  how does control reach it, what breaks if I change it -- query the graph
  instead of grepping:
  `python scripts/explore.py --symbol <name>`, `--path <a> <b>`, `--impact <name>`.
  Every edge carries a provenance tag: `exact`, `heuristic`, `ambiguous`, `weak`.
  Treat `ambiguous` and `weak` as leads to verify by reading code, never as fact.
  Static analysis cannot see dynamic dispatch, DI wiring, reflection, or runtime
  registries, so an impact result is the MINIMUM blast radius, never the maximum.
- Keep `_agent_ops/CURRENT_TASK.md` current *during* a task, not only at the
  end: files touched, approaches ruled out with their evidence, next step. It is
  what survives a mid-task context compaction and stops the agent from retrying
  a dead end.
- Before an edit, scope expansion, or final conclusion, re-anchor to the
  Session Brief's original goal and constraints. Before a meaningful completion
  report, the root agent updates the smallest applicable `_agent_ops/` records
  and prints the **Closure Receipt**: one row per ops file, each resolved as
  updated-with-what or not-needed-with-why. Omitting a row silently is a
  protocol violation. Read `_agent_ops/SESSION_PROTOCOL.md` for the
  authoritative lifecycle and the receipt format.

Subagent policy:

- Real subagents exist for four roles: `tester` and `repo_hygiene_reviewer`
  (read-only), `bug_hunter` (read-only, probes one fix direction), and
  `bug_fixer` (workspace-write, applies the confirmed fix).
- Use `auto` as the default work mode. Spawn subagents only when at least two
  independent workstreams have bounded paths and no shared write target, real
  child-agent spawning is available, and the user confirms after a token-cost
  warning. Otherwise use a solo or sequential role-check path and say which.
- Treat a clear request to use/spawn subagents as `auto` with a
  **subagent-preferred** intent; do not make the user repeat it as `@work`.
  This includes contextual equivalents such as "spawn/use subagents", "delegate
  to child agents", "gọi/dùng/chia agent con", or "làm/chạy song song bằng
  agents". A mere mention or discussion of subagents is not a trigger.
- For that intent, first report the eligible recommendation: `parallel` when
  native spawning and independent scopes exist; `sequential` when work depends
  on itself or spawning is unavailable; `solo` when extra roles add no value.
  Explain the reason, token cost, and next confirmation rather than silently
  spawning or pretending that sequential work is parallel.
- Large audit: run `tester` + `repo_hygiene_reviewer` in parallel, then merge.
- Hard bug: run several `bug_hunter` in parallel to probe fix directions, then a
  single `bug_fixer` after confirmation.
- The root agent owns user communication, git, `_agent_ops/`, evidence merging,
  and all final decisions. Subagents receive a compact task capsule and do not
  write `_agent_ops/`; source changes use one serialized writer lane.
- Adapters: `.codex/agents/*.toml` for Codex, `.claude/agents/*.md` for Claude
  Code. They point back to the team folders; the team `SKILL.md` files are the
  single source of truth.

Coding standard (always on, applies to every team that writes code):

- One responsibility per change: a function/file/commit does one thing. Do not
  fold unrelated concerns into the same edit.
- No overlapping side effects: do not have two code paths write the same
  state/file without a clear, single owner. This is the main cause of "fixing
  one bug creates another" -- avoid it up front, not after the fact.
- Keep blast radius isolated: prefer changes containable to one module/zone.
  If a change must cross boundaries, say so explicitly before editing.
- Reuse existing logic instead of duplicating it; check for an existing
  function/util first. For deeper cleanup, use `clean-code-team/`.

Advisor persona (how to communicate):

- Be a principled, high-signal advisor. Lead with the answer, then the reasoning.
- Hold positions supported by evidence. Update on better data or reasoning, not
  on repetition or pressure. Frame pushback as "the data shows X", not "I think".
- For any recommendation, surface benefits, costs, risks, and time horizon.
- Distinguish "I don't know", "I'm uncertain", "evidence is mixed", and "best
  estimate". Do not fill gaps with plausible guesses.
- Before acting on ambiguous or high-stakes input, ask the single most important
  clarifying question. One question, not five.
- No filler. Professional disagreement is not hostility; stay collaborative.

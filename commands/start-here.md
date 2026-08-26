# Start-Here Command (Advanced Auto-Router)

Use this once at the beginning of a session. `@start-here` creates or refreshes
only `_agent_ops/` memory, establishes a compact Session Receipt, then routes
the task. Later requests continue from that state; they do not need another
`@start-here`. Add `--no-ops` for chat-only/router-only work.

```text
@start-here [--no-ops] <one-line description of your goal>

You are the auto-router for this workspace pack.

Read only AGENTS.md, TEAM_ROUTER.md, and START_HERE.md first. Do not load every
team folder. Unless `--no-ops` was supplied, treat this as a state machine:

- If `_agent_ops/` is missing and `scripts/init_project_ops.py` exists, run
  `python scripts/init_project_ops.py --target .` immediately. Do not ask first:
  `@start-here` already authorizes these `_agent_ops/` writes.
- The bootstrap is complete only after the new `SESSION_BRIEF.md` and
  `CURRENT_TASK.md` are filled from the user's goal, and one factual bootstrap
  entry is appended to `IMPLEMENTATION_LOG.md`. It also generates `REPO_MAP.md`
  and the symbol index.
- "Do everything" or "initialize everything" means this complete bootstrap
  only. It NEVER authorizes source, configuration, dependency, git, commit,
  push, destructive, or external-service changes.

Then run the deterministic checks:

  python _agent_ops/tools/session_start.py --root .

That is read-only and reports git state, what changed since the memory was last
verified, whether REPO_MAP.md is stale, unfilled template placeholders, and
whether the implementation log needs rotating. If Python is unavailable, do it
by hand instead: `git status --short`, `git rev-parse --short HEAD`, compare
HEAD to the `Last Verified Commit` in SESSION_BRIEF.md, run
`git log --oneline <sha>..HEAD`, and skim SESSION_BRIEF.md / CURRENT_TASK.md for
unfilled `<placeholder>` text.

Then read only `_agent_ops/SESSION_BRIEF.md`, `_agent_ops/OPERATING_RULES.md`,
and `_agent_ops/CURRENT_TASK.md` if a task is already in progress. Do not load
the whole implementation log, decision log, risk register, or every phase card
unless the active task needs it. To locate code, read `_agent_ops/REPO_MAP.md`
before grepping the repository.

Do this:
0. Check Session Continuity FIRST. If the checks report CONTINUATION, a previous
   session left `_agent_ops/HANDOFF.md`. Read it before routing or touching
   code, say in one line that you are continuing that work and what its next
   step was, and set its `Status` to `consumed` once absorbed. Do not make me
   explain that this is a continuation -- find it yourself.
1. Print a compact Session Receipt: understood goal/non-goals, context read,
   important context missing, and the scope of managed-session permission
   (only `_agent_ops/`; never source or git). Surface anything the
   deterministic checks flagged: stale memory, a stale repo map, or unfilled
   placeholders. Placeholders are blanks to ask about, not facts to infer.
2. Classify the intent and pick the best team from TEAM_ROUTER.md. If the goal
   needs several teams, propose a short ordered chain (for example:
   advisor-team -> analyze-team -> prompting-team -> tester-team). Do not run the
   whole chain automatically; recommend it and let me approve step by step.
   If the request is vague ("make this better", "what should I improve"), route
   to advisor-team first for an overview and priorities. A request to add new
   behavior ("add X", "build X", "implement X") routes to build-team; a request
   about something broken routes to bug-fix-team.
3. State the recommended team (or ordered chain) in one line, and why in one line.
4. Tell me the exact way to invoke that team on MY harness (detect it; if unsure,
   ask once):
   - Codex: reference the team, e.g. "@bug-fix-team/SKILL.md", or invoke the
     matching .codex subagent for parallel work.
   - Claude Code: the team is a discoverable skill; you may also spawn the
     matching .claude subagent.
   - Any other harness: capability-detect real child-agent spawning. If it is
     unavailable, suggest the exact @reference to paste and use sequential
     role-play without claiming parallelism.
5. Classify token/risk (Light / Medium / Heavy / Very Heavy) and warn if the
   work is Heavy or Very Heavy, per harness/TOKEN_RISK_MATRIX.md.
6. If the target harness has no native spawning, or the model is
   weaker/less-suited, use `sequential`: select exactly one team, bound work to
   one phase/module/bug direction/audit slice, name the exact context files to
   read, and stop for one explicit confirmation before any source-changing work.
   Do not propose a chain unless the selected team proves it is needed.
7. Recommend `solo`, `auto`, `parallel`, or `sequential`. Parallel is eligible
   only for at least two independent bounded workstreams with no shared write
   target. State benefit, token cost, and risk. Ask before costly fan-out.
   If my request explicitly says to spawn/use subagents or an equivalent (for
   example "gọi agent con" or "làm song song bằng agents"), route it internally
   as `auto --prefer-subagents` and lead me to the eligible recommendation; do
   not require me to repeat a command or assume I authorized blind fan-out.
8. Ask the SINGLE most important clarifying question or confirmation only if it
   materially changes scope, risk, or cost. Do not invent missing requirements.
9. Show the expected output before starting. Continue advisor behavior after
   routing: explain recommendation, options, and trade-offs rather than acting
   as an autonomous guesser.
10. During a multi-step task, keep `_agent_ops/CURRENT_TASK.md` current: files
    touched, approaches ruled out with evidence, open questions, next step.
    Update it as you go, not only at the end -- it is what survives if the
    conversation context is compacted.
11. Before a meaningful completion report, let the root classify actual work
    under SESSION_PROTOCOL.md, not the prompt's file list. Write every
    triggered durable record first: the implementation log for
    implementation/test/audit/gate/verification evidence, the project context
    card for durable state, and the decision log for material trade-offs. Then
    print the Closure Receipt: one row per ops file, each resolved as
    updated-with-what or not-needed-with-a-missing-trigger. Do not stage,
    commit, or push them automatically.

Rules:
- Chat first, files later.
- One clarifying question maximum, not five.
- Never use git add .
- For an authorized source commit, stage source after tests, then run
  _agent_ops/tools/refresh_repo_map.py with --stage and review the map before
  commit. Do not use --no-verify.
- Do not install dependencies.
- Do not run Heavy or E2E commands without approval.
- Do not claim a subagent was spawned on a harness that has no native subagents.
- Root owns `_agent_ops/`, git, evidence merging, and user communication.
- Subagents receive only a bounded context capsule and never write `_agent_ops/`.
- Keep it concise and honest. Lead with the routing decision.
```

## Behavior Summary

- One line in, a managed Session Receipt and routed answer out.
- Deterministic checks come from `scripts/session_start.py`, not from the model
  remembering to run them; a manual fallback exists when Python is unavailable.
- Single team when one fits; an ordered multi-team chain when the goal needs it.
- Vague goals go to advisor-team first for overview and priorities.
- Picks up an open handoff by itself, without the user mentioning it.
- Always shows token/risk before heavy work.
- At most one clarifying question.
- Locates code via `_agent_ops/REPO_MAP.md` before grepping the repository.
- Writes only `_agent_ops/` during a managed start; never writes source, runs a
  whole chain, or runs heavy commands without confirmation.
- Ends meaningful work with a Closure Receipt.

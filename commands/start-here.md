# Start-Here Command (Advanced Auto-Router)

Use this once at the beginning of a session. `@start-here` creates or refreshes
only `_agent_ops/` memory, establishes a compact Session Receipt, then routes
the task. Later requests continue from that state; they do not need another
`@start-here`. Add `--no-ops` for chat-only/router-only work.

```text
@start-here [--no-ops] <one-line description of your goal>

You are the auto-router for this workspace pack.

Read only AGENTS.md, TEAM_ROUTER.md, and START_HERE.md first. Do not load every
team folder. Unless `--no-ops` was supplied, check git status, ensure
`_agent_ops/` exists without overwriting files, then read only
`_agent_ops/SESSION_BRIEF.md` and `_agent_ops/OPERATING_RULES.md`. Do not load
the whole implementation log, decision log, risk register, or every phase card
unless the active task needs it.

Do this:
1. Print a compact Session Receipt: understood goal/non-goals, context read,
   important context missing, and the scope of managed-session permission
   (only `_agent_ops/`; never source or git).
2. Classify the intent and pick the best team from TEAM_ROUTER.md. If the goal
   needs several teams, propose a short ordered chain (for example:
   advisor-team -> analyze-team -> prompting-team -> tester-team). Do not run the
   whole chain automatically; recommend it and let me approve step by step.
   If the request is vague ("make this better", "what should I improve"), route
   to advisor-team first for an overview and priorities.
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
6. If the target harness is DeepSeek, Gemini, Cursor, other prompt-based, or a
   weaker/less-suited model, recommend stricter scope by default: one phase,
   one module, one bug direction, or one audit slice; name the exact context
   files to read before work begins; and propose an ordered team chain only when
   it improves quality.
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
10. Before a meaningful completion report, let the root update the smallest
    applicable `_agent_ops/` records under `SESSION_PROTOCOL.md`. Do not stage,
    commit, or push them automatically.

Rules:
- Chat first, files later.
- One clarifying question maximum, not five.
- Never use git add .
- Do not install dependencies.
- Do not run Heavy or E2E commands without approval.
- Do not claim a subagent was spawned on a harness that has no native subagents.
- Root owns `_agent_ops/`, git, evidence merging, and user communication.
- Subagents receive only a bounded context capsule and never write `_agent_ops/`.
- Keep it concise and honest. Lead with the routing decision.
```

## Behavior Summary

- One line in, a managed Session Receipt and routed answer out.
- Single team when one fits; an ordered multi-team chain when the goal needs it.
- Vague goals go to advisor-team first for overview and priorities.
- Always shows token/risk before heavy work.
- At most one clarifying question.
- Writes only `_agent_ops/` during a managed start; never writes source, runs a
  whole chain, or runs heavy commands without confirmation.

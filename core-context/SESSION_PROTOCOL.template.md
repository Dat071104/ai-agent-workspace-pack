# Managed Session Protocol / Giao thuc phien quan ly

Use this file as the durable operating contract for one target repository. It
keeps the agent anchored without requiring it to load every context file on
every turn.

## Scope of Managed Session Permission

Starting a session with `@start-here` authorizes only the creation and updates
of files inside `_agent_ops/`. It does **not** authorize source, configuration,
dependency, git, commit, push, destructive, or external-service changes. Those
still require the normal confirmation rules.

Use `@start-here --no-ops <goal>` for a chat-only/router-only session that must
not create or update `_agent_ops/`.

## Session Start: Root Agent Only

1. Read the target repository's `AGENTS.md` or equivalent always-on rules.
2. Check git status without changing it.
3. Ensure `_agent_ops/` exists. If it is absent and managed-session permission
   applies, initialize it with the workspace-pack helper without overwriting
   existing files.
4. Read only `_agent_ops/SESSION_BRIEF.md` and
   `_agent_ops/OPERATING_RULES.md` first. Read the project context card, phase
   cards, decision log, risk register, or implementation log only when the
   active task needs them.
5. Return a compact **Session Receipt** before substantive work:
   - understood goal and non-goals;
   - context read and important context missing;
   - recommended team and token/risk level;
   - proposed work mode (`solo`, `auto`, `parallel`, or `sequential`);
   - the one clarification or confirmation needed, if any.

The root agent must re-anchor to the Original Goal and Constraints in
`SESSION_BRIEF.md` before an edit, a scope expansion, or a final conclusion.
If they conflict with the current request, stop and ask the user rather than
silently choosing a new direction.

## Work Modes

| Mode | Use when | Behavior |
| --- | --- | --- |
| `solo` | One small, contained task | Root completes it directly. |
| `auto` | Default | Root chooses the least costly useful mode after inspection. |
| `parallel` | At least two independent, read-only workstreams and real child-agent spawning is available | Root spawns 2-4 bounded agents, then merges their evidence. |
| `sequential` | Workstreams depend on each other or native spawning is unavailable | Root runs the same role checks in order in one session. Do not claim parallel execution. |

Do not spawn merely because a request contains two checklist items. A workstream
is independent only when it has a distinct question, bounded paths, and no
shared write target. Native support is capability-detected from the current
harness; model or product names alone are not proof.

When a user clearly asks to use/spawn subagents, the root internally routes the
request as `@work auto --prefer-subagents`; do not ask them to repeat a command.
Recognize contextual equivalents such as "spawn/use subagents", "delegate to
child agents", "gọi/dùng/chia agent con", or "làm/chạy song song bằng agents".
Do not trigger from a mere mention or a general discussion of subagents. First
recommend `parallel`, `sequential`, or `solo` with the reason and cost; actual
fan-out still follows the confirmation rule above.

## Subagent Contract

The root agent owns planning, user communication, git, external side effects,
context updates, evidence synthesis, and the final recommendation. It sends
each subagent a compact context capsule:

- goal, non-goals, and relevant `AGENTS.md` constraints;
- one assigned question plus allowed paths;
- exact `_agent_ops/` files to read, if any;
- expected evidence and stop condition;
- no writes to `_agent_ops/`, no commit, push, or destructive action.

Default to read-only subagents. Do not run concurrent writers in one workspace.
After evidence is merged, use one writer lane for source changes. The root must
warn about token cost and ask before a costly fan-out unless the user has
explicitly approved autonomous parallel work for the current task.

## Context Update / Closure Gate: Root Agent Only

Before reporting a meaningful task as complete, update the smallest applicable
set of `_agent_ops/` files:

| Change | Required record |
| --- | --- |
| Every managed session | `SESSION_BRIEF.md`: active state, next step, timestamp |
| Meaningful implementation, test, or audit evidence | append to `IMPLEMENTATION_LOG.md` |
| Durable project/milestone state changed | `PROJECT_CONTEXT_CARD.md` |
| Decision with material trade-offs | `DECISION_LOG.md` |
| New or changed material risk | `RISK_REGISTER.md` |

Do not update every file mechanically. Keep the implementation log factual and
append-only; never put secrets, private data, or unverified claims in any ops
file. Context updates are never staged, committed, or pushed automatically.

## User-Advisor Contract

The agent remains an advisor, not an autonomous guesser. It must explain what
it understood, identify missing context, recommend the least risky useful path,
and ask one focused question when an answer would materially change scope,
risk, or cost. It should suggest a work mode and explain its benefit/cost; the
user may accept, change, or decline that suggestion.

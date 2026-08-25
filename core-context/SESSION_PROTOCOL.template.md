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
2. Run the deterministic checks. Prefer the script; it is read-only:

   ```bash
   python _agent_ops/tools/session_start.py --root .
   ```

   It reports git state, what changed since the memory was last verified,
   whether `REPO_MAP.md` is stale, unfilled template placeholders, and whether
   the implementation log needs rotating.

   **Fallback when Python is unavailable** -- do these by hand:
   `git status --short`; `git rev-parse --short HEAD`; compare HEAD against the
   `Last Verified Commit` in `SESSION_BRIEF.md` and run
   `git log --oneline <sha>..HEAD`; skim `SESSION_BRIEF.md` and
   `CURRENT_TASK.md` for `<placeholder>` text still unfilled.
3. Ensure `_agent_ops/` exists. If it is absent and managed-session permission
   applies, initialize it with the workspace-pack helper without overwriting
   existing files.
4. Read only `_agent_ops/SESSION_BRIEF.md`, `_agent_ops/OPERATING_RULES.md`,
   and -- if a task is already in progress -- `_agent_ops/CURRENT_TASK.md`.
   Read `_agent_ops/REPO_MAP.md` before grepping the repository for code. Read
   the project context card, phase cards, decision log, risk register, or
   implementation log only when the active task needs them. `_agent_ops/INDEX.md`
   lists the full read order.
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

## Working Memory During a Task: `CURRENT_TASK.md`

`SESSION_BRIEF.md` is session-level. `CURRENT_TASK.md` is task-level, and it is
what survives when the conversation context is compacted mid-task. Overwrite it;
never append.

Update it after each meaningful step, not only at the end:

| Event | What to record |
| --- | --- |
| A file was edited | add it to Files Touched So Far |
| A hypothesis or approach was disproved | add it to Ruled Out / Already Tried, with the evidence |
| The user answered a question | remove it from Open Questions and record the answer's effect |
| The next action changed | rewrite Next Concrete Step |

The **Ruled Out** section carries the most weight. After a context compaction an
agent will otherwise retry an approach that was already disproved, spending
tokens to rediscover a known dead end.

## Context Update / Closure Gate: Root Agent Only

Before reporting a meaningful task as complete, update the smallest applicable
set of `_agent_ops/` files:

| Change | Required record |
| --- | --- |
| Each meaningful step within a task | `CURRENT_TASK.md`: files touched, dead ends, next step |
| Every managed session | `SESSION_BRIEF.md`: active state, next step, `Last Verified Commit` |
| Meaningful implementation, test, or audit evidence | append to `IMPLEMENTATION_LOG.md` |
| Durable project/milestone state changed | `PROJECT_CONTEXT_CARD.md` |
| Decision with material trade-offs | `DECISION_LOG.md` |
| New or changed material risk | `RISK_REGISTER.md` |
| Code files added, moved, or removed | regenerate `REPO_MAP.md` |

Do not update every file mechanically. Keep the implementation log factual and
append-only; never put secrets, private data, or unverified claims in any ops
file. Context updates are never staged, committed, or pushed automatically.

### Closure Receipt (required output)

A prose reminder to "update the smallest applicable set" is easy to skip. So the
gate is an output contract instead: print this block before any meaningful
completion report.

```text
Closure Receipt
- CURRENT_TASK.md      : updated (files touched, next step) | not needed (<why>)
- IMPLEMENTATION_LOG.md: appended <date>/<task>             | not needed (<why>)
- SESSION_BRIEF.md     : state + Last Verified Commit -> <sha> | not needed (<why>)
- PROJECT_CONTEXT_CARD : updated (<what>)                   | not needed (<why>)
- DECISION_LOG.md      : DEC-00NN added                     | not needed (<why>)
- RISK_REGISTER.md     : RISK-00NN added/changed            | not needed (<why>)
- REPO_MAP.md          : regenerated                        | not needed (<why>)
```

Rules:

- Every row must resolve to either *updated, with what changed* or *not needed,
  with the reason*. Silently omitting a row is a protocol violation.
- "not needed" is a legitimate answer for most rows on most tasks. The point is
  a deliberate decision on each, not a mechanical update of all.
- The receipt states what was actually written. Do not list a file as updated
  before writing it.
- Routing, questions, and read-only reports do not need a receipt. Anything that
  changed code, produced test/audit evidence, or settled a decision does.

## Log Rotation

`IMPLEMENTATION_LOG.md` is append-only and would otherwise grow without bound --
turning the folder that exists to save context into a context cost of its own.

- Keep the newest 10 entries in the active log.
- Older entries move to `_agent_ops/archive/IMPLEMENTATION_LOG_<YYYY-MM>.md`.
- `_agent_ops/LOG_SUMMARY.md` becomes the Tier-1 read; the full log drops to
  Tier 3.

```bash
python _agent_ops/tools/summarize_implementation_log.py \
    --log _agent_ops/IMPLEMENTATION_LOG.md \
    --rotate --keep 10 --output _agent_ops/LOG_SUMMARY.md --force
```

**Fallback when Python is unavailable:** cut the oldest entries out of the log by
hand into the archive file, keeping the log's title and entry template at the
top. Never delete entries; archiving is a move, not a cleanup.

## User-Advisor Contract

The agent remains an advisor, not an autonomous guesser. It must explain what
it understood, identify missing context, recommend the least risky useful path,
and ask one focused question when an answer would materially change scope,
risk, or cost. It should suggest a work mode and explain its benefit/cost; the
user may accept, change, or decline that suggestion.

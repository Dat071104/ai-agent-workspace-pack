# Current Task / Cong viec dang lam

Working memory for ONE task. **Overwrite this file; never append to it.** Keep it
under ~60 lines so updating it stays cheap enough to do often.

`SESSION_BRIEF.md` is session-level. This file is task-level: it is what survives
when the conversation context is compacted mid-task. Update it after each
meaningful step -- a file edited, a hypothesis ruled out, a user answer received
-- not only at the end.

When the task finishes, classify the work under SESSION_PROTOCOL.md and fold
every triggered durable fact into the implementation log, project context card,
and/or decision log. Prompt omission is never a reason to skip a triggered
record. Set Status to `complete` only after writing the records and Closure
Receipt; overwrite this file when the next task begins.

## Task ID / Started

`TASK-0001` / `YYYY-MM-DD`

## Status

`idle`

One of `in-progress`, `blocked` (waiting on a user answer), `complete`, `idle`.
`session_start.py` reads this line. Without it a finished task looks live,
because its Next Concrete Step is still written down.

## Original Goal

`<copy verbatim from SESSION_BRIEF.md -- re-read before each edit to prevent drift>`

If the work no longer serves this line, stop and flag it instead of continuing.

## Non-Goals

- `<explicitly out of scope for THIS task>`

## Files Touched So Far

| File | What changed | Reverted? |
| --- | --- | --- |
| `<path>` | `<one line>` | no |

## Ruled Out / Already Tried

The highest-value section. After a context compaction the agent tends to retry a
hypothesis that was already disproved. Record every dead end with its evidence.

| Tried | Why it was rejected | Evidence |
| --- | --- | --- |
| `<hypothesis, approach, or fix direction>` | `<reason>` | `<command output, file, or user answer>` |

## Open Questions Awaiting User

- `<question the task is blocked on -- do not guess an answer>`

Write `None` when there is nothing to ask.

## Standing Permissions / Notes

Constraints and authorizations that persist but are not questions, for example
"commit/push needs explicit authorization per slice set". They never block the
task, so they do not belong under Open Questions.

- `<none, or a standing permission/constraint>`

## Next Concrete Step

`<the single next action, specific enough to execute without re-deriving context>`

## Last Verified Commit

`<short SHA of HEAD when this file was last updated>`

## Closure Gate (before final report)

- [ ] Classified actual work against SESSION_PROTOCOL.md; prompt file lists did
      not narrow the record triggers.
- [ ] Wrote every triggered durable record, or recorded the absent trigger in
      the Closure Receipt.
- [ ] Printed the Closure Receipt after the writes, never as a plan to write
      later.
- [ ] If committing staged project code, refreshed the code index and Repo Map
      after tests; only REPO_MAP.md was auto-staged by the refresh helper.

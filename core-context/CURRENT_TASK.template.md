# Current Task / Cong viec dang lam

Working memory for ONE task. **Overwrite this file; never append to it.** Keep it
under ~60 lines so updating it stays cheap enough to do often.

`SESSION_BRIEF.md` is session-level. This file is task-level: it is what survives
when the conversation context is compacted mid-task. Update it after each
meaningful step -- a file edited, a hypothesis ruled out, a user answer received
-- not only at the end.

When the task finishes, fold the durable facts into `IMPLEMENTATION_LOG.md` and
reset this file for the next task.

## Task ID / Started

`TASK-0001` / `YYYY-MM-DD`

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

## Next Concrete Step

`<the single next action, specific enough to execute without re-deriving context>`

## Last Verified Commit

`<short SHA of HEAD when this file was last updated>`

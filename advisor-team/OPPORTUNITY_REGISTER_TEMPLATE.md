# Opportunity / Improvement Register Template

A value-first, ranked list of what could be improved. Fill the table, then rank
by ROI. This is a report, not a commitment to build.

## Project

`<project name and one-line goal>`

## Register

| # | Opportunity (function / module / flow) | Type | User / Business value | Effort | Risk | Evidence | Confidence | ROI verdict | Horizon | Owning team | Recommend now? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 |  | code / product / delivery / lean | High / Med / Low | S / M / L / XL | Low / Med / High | `path:line`, log entry, or measurement; else `needs data` | high / med / low | Quick win / Big bet / Fill-in / Money pit | Now / Next / Later | analyze / bug-fix / tester / clean-code / prompting / repo-hygiene | Yes / Later / No |
| 2 |  |  |  |  |  |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |  |  |  |  |  |

- Value = impact on users or the business, not code elegance.
- Effort = size from `EFFORT_COMPLEXITY_RUBRIC.md`. For `lean` rows, write the
  size as negative lines, e.g. `S (-120 lines)`.
- Evidence is mandatory. A row with no citation says `needs data` and cannot be
  `Now`.
- Confidence: `high` = read in code or measured; `med` = one inference from
  evidence; `low` = assumption. Ranking discounts `low` (see SKILL.md step 5).
- ROI verdict pairs value with effort (see the rubric's quadrant note).
- Horizon: Now = S/M, high confidence, unblocked. Next = waits on a Now item or
  on data. Later = L/XL or blocked by an open risk.
- Owning team = who should actually execute if approved.

## Top Picks (1-3)

1. `<opportunity>` -- why now, in one line (value vs effort).
2. `<opportunity>` -- why now.
3. `<opportunity>` -- why now.

The single next step is a Next Step Card (`NEXT_STEP_CARD_TEMPLATE.md`), built
from pick 1.

## Deliberately Deferred

- `<opportunity>` -- reason it is not worth doing now.

## Notes

- Mark each value/effort cell as `known`, `estimate`, or `needs data`.
- Re-check effort against real code before committing to any item.

# Fix Directions Template

Use this after ranking root-cause hypotheses. For the leading hypothesis,
propose 2-3 fix approaches and score them. Recommend exactly one, but keep
fallbacks documented so the user can choose.

## Leading Hypothesis

`<H# and one-line root cause>`

## Fix Directions

| # | Direction (summary) | Blast radius | Risk | Effort | Reversibility | Test cost | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D1 |  | Local / Module / Cross-cutting | Low / Med / High | Low / Med / High | Easy / Hard | Low / Med / High | Recommended / Fallback / Rejected |
| D2 |  | Local / Module / Cross-cutting | Low / Med / High | Low / Med / High | Easy / Hard | Low / Med / High | Recommended / Fallback / Rejected |
| D3 |  | Local / Module / Cross-cutting | Low / Med / High | Low / Med / High | Easy / Hard | Low / Med / High | Recommended / Fallback / Rejected |

## Recommendation

- Recommended direction: `<D#>`
- Why: `<concise rationale tied to blast radius, risk, reversibility>`
- Fallback 1: `<D#>` — use if `<condition>`.
- Fallback 2: `<D#>` — use if `<condition>`.

## Complexity Gate

- Classification: `Medium` (single-agent reasoning) / `Hard or ambiguous`
- If `Hard or ambiguous`: parallel-subagent mode is available. Each `bug_hunter`
  probes one direction in isolation, then results are merged into this table.
  This costs extra tokens. Confirm before running.

## Confirmation

Pick one before I edit anything:

- Proceed with the recommended direction.
- Choose a fallback direction instead.
- Run parallel `bug_hunter` mode first (extra token cost).
- Stop and keep this as a report only.

I will not use `git add .`. I will commit only if explicitly allowed.

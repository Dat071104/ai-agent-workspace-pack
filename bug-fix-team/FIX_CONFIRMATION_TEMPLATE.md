# Fix Confirmation Template

## Confirmed Issue

`<classification and summary>`

## Leading Root Cause

`<H# and one-line root cause; note if evidence is mixed>`

## Fix Directions Considered

| # | Direction | Verdict |
| --- | --- | --- |
| D1 |  | Recommended / Fallback / Rejected |
| D2 |  | Recommended / Fallback / Rejected |
| D3 |  | Recommended / Fallback / Rejected |

## Recommended Minimal Fix

`<recommended direction summary>`

## Fallbacks

- `<D#>` — use if `<condition>`.

## Affected Zone

- `<file/module>`

## Risks

- `<risk>`

## Tests

- `<test command>`

## Confirmation Needed

Please confirm before I patch:

- Proceed with the recommended direction.
- Choose a fallback direction instead.
- Run parallel `bug_hunter` mode first (extra token cost; only for Hard bugs).
- Adjust the fix plan.
- Stop and keep this as a report only.

I will not use `git add .`. I will commit only if explicitly allowed.

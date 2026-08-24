# Slice Plan Template

A slice is the smallest change that leaves the codebase working and verifiable.
Implement one slice, verify it, report, then ask before the next.

Splitting is not busywork: it keeps the blast radius reviewable and gives a
clean rollback point when a later slice turns out to be wrong.

## Slices

| # | Slice | Files | Depends on | Verifiable by | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | `<smallest working increment>` | `<paths>` | - | `<test/command>` | Planned |
| 2 | `<next>` | `<paths>` | 1 | `<test/command>` | Planned |

## Rules

- One responsibility per slice. Do not fold unrelated concerns together.
- No two slices write the same state without one clear owner.
- A slice that only adds a layer without reducing duplication or delivering
  behavior should be reconsidered.
- After each slice: files changed, tests run, real results, remaining work, and
  a confirmation question before continuing.

## Per-Slice Report

### Slice `<n>`: `<name>`

- Files changed: `<paths>`
- Reused: `<what existing code was used instead of new code>`
- Tests run: `<command>`
- Results: `<real output; do not claim a pass that did not run>`
- Not yet implemented: `<what remains>`
- Risks introduced: `<risk or none>`
- Continue to slice `<n+1>`? `<question>`

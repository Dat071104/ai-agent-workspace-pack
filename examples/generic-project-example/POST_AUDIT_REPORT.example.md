# Post Audit Report Example

## Scope

Scoped audit of ticket list filters and export flow.

## Findings

### High

None.

### Medium

- Empty state does not explain that active filters may hide tickets.

### Low

- Export button remains enabled when no tickets match.

## Commands Run

```bash
npm test -- ticket-filter
```

## Result

Tests passed. Manual UX review found two usability issues.

## Recommended Next Workflow

Use bug-fix-team for the empty-state issue if accepted as a bug.


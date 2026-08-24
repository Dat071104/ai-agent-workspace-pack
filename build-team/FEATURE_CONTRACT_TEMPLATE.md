# Feature Contract Template

Fill this in BEFORE writing code. If the Business Rules section cannot be
completed from `_agent_ops/PROJECT_CONTEXT_CARD.md` or the user, stop and ask.
An unanswered rule here becomes a silent wrong assumption in the code.

## Feature

`<one line: what behavior will exist that does not exist now>`

## Out of Scope

- `<what this feature explicitly does not do>`

## Business Rules & Acceptance Criteria

| Rule | Accept when (observable) |
| --- | --- |
| `<rule>` | `<criterion an outsider could verify>` |

Source of these rules: `<context card / user / ticket>`. If any row was inferred
rather than stated, mark it and confirm before implementing.

## Interface Contract

- Signature / endpoint / command: `<exact shape>`
- Inputs: `<types, required vs optional, validation>`
- Outputs: `<success shape>`
- Error cases: `<condition -> behavior>`
- Side effects: `<state written, and which code path owns it>`

## Placement

- Owning module (from `_agent_ops/REPO_MAP.md`): `<module>`
- Why this module owns the concern: `<one line>`
- Touches a hot file? `<yes/no; if yes, treat as cross-module>`

## Reuse

| Existing thing to reuse | Path |
| --- | --- |
| `<function/util/pattern>` | `<path>` |

Genuinely new code: `<what has no existing equivalent, and why>`

## Impact

- Files to create: `<paths>`
- Files to modify: `<paths>`
- Cross-boundary effects: `<none, or describe>`
- Rollback: `<how to undo this slice>`

## Verification

- Narrowest meaningful test: `<command>`
- Wider check if needed: `<command or tester-team scope>`

# Decision Log / Nhat ky quyet dinh

## Decision Entry

### Decision ID

`DEC-0001`

### Date

`2026-08-27`

### Context

`An embedded pack beside an existing host AGENTS.md was undiscoverable because the installer correctly preserved the host file.`

### Options

| Option | Description | Pros | Cons |
| --- | --- | --- | --- |
| A | Add a managed, explicit bridge to an existing AGENTS.md | Fixes discoverability without changing host text outside markers | Leaves flat-layout collisions for a later migration |
| B | Immediately move the entire pack under a namespace | Addresses all root path collisions | Broad migration with many path and adapter changes |

### Decision

`Choose A for v1.1; retain flat embedded compatibility and defer namespaced .ai-agent-workspace-pack/ layout to v2.`

### Rationale

`The bridge is small, marker-bounded, idempotent, and directly fixes the reported failure. A full layout move would expand scope beyond the immediate verified need.`

### Consequences

- Existing host instructions remain intact by default; users opt in with --install-agents-bridge.
- The check command reports only structural bridge states and does not attempt semantic policy analysis.

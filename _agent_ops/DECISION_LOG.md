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

---

## Decision Entry

### Decision ID

`DEC-0002`

### Date

`2026-08-28`

### Context

`A user needs the full pack embedded in an application without flattening scripts, teams, adapters, and project state into the application root.`

### Options

| Option | Description | Pros | Cons |
| --- | --- | --- | --- |
| A | Keep the flat embedded layout | No migration work | Collides with host paths and looks like a copied clone |
| B | Copy the pack under ai-agent-workspace-pack/ with a first-line root bridge | One contained folder; preserves host AGENTS.md; supports nested runtime tools | Three lightweight root harness entry files can still be needed for auto-discovery |

### Decision

`Choose B for the new namespaced embedded mode; keep the existing flat bridge as legacy compatibility.`

### Rationale

`The first root line is sufficient to route to the pack while preserving all host rules below it. Making the ops folder nested prevents the same collision from reappearing as _agent_ops/.`

### Consequences

- `--embedded-folder ai-agent-workspace-pack` is explicit and validates the copied-pack signature before writing.
- `embed_pack.py` excludes source `.git/` and source `_agent_ops/`, then initializes fresh target state.
- Runtime tools derive their nested ops location; the pre-commit hook stages only the nested map.
- Scanners skip a namespaced child only when all pack markers are present.

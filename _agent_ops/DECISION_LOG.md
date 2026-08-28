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

---

## Decision Entry

### Decision ID

`DEC-0003`

### Date

`2026-08-28`

### Context

`The namespaced layout removed the pack's four subagents and nine team skills, because Codex and Claude Code auto-discover agents and skills only at the repository root.`

### Options

| Option | Description | Pros | Cons |
| --- | --- | --- | --- |
| A | Revert to the flat layout | Discovery works | Reintroduces collisions with the host's scripts/, tests/, README.md, LICENSE, .gitignore |
| B | Accept the loss | Nothing to build | AGENTS.md promises subagents that cannot be discovered |
| C | Generate small marked pointers at the root that resolve into the pack folder | Discovery works with 2 hidden root directories; no workflow content duplicated | Pointers are generated, so a pack update requires re-running the installer |

### Decision

`Choose C. Only the discovery surface lives at the root; every workflow file stays inside the pack folder.`

### Rationale

`The flat layout's cost was collision with host-owned paths, not the presence of .claude/ and .codex/ -- projects using these harnesses have them anyway. Pointers carry no workflow content, so the team SKILL.md files remain the single source of truth.`

### Consequences

- A pointer is marked `AI_AGENT_WORKSPACE_PACK:ADAPTER v1`; a re-run updates a marked file and never a same-named host file.
- Pack-relative paths inside pointers are rewritten path-leading only, which keeps re-runs idempotent and leaves prose untouched.
- `--no-root-adapters` opts out, at the cost of discovery.
- Editing a pointer by hand is wrong: change the team file in the pack and re-run the installer.

---

## Decision Entry

### Decision ID

`DEC-0004`

### Date

`2026-08-28`

### Context

`The exclusion that keeps a workspace pack out of a project's code graph could not distinguish a flat install from the pack's own source checkout: both carry the same marker files at the root.`

### Options

| Option | Description | Pros | Cons |
| --- | --- | --- | --- |
| A | Keep the heuristic | No work | Guesses; already wrong on this repository, whose own map reported 1 file |
| B | Record the layout at install time in `<ops>/pack_install.json` and read it back | Keeps flat installs supported | Adds a state file plus a fallback branch, to maintain a mode being retired |
| C | Remove the root-level exclusion and migrate flat installs | Deletes code; ambiguity disappears with the case; fixes the pack's own map | A flat install indexes pack scripts until migrated |

### Decision

`Choose C. Only a pack in its own subdirectory is excluded, which is unambiguous by construction. scripts/migrate_pack.py converts existing flat installs.`

### Rationale

`The information needed -- is this pack the product or the infrastructure? -- does not exist in the files, so no heuristic can be correct. Option B would encode the answer, but only to keep alive a layout already replaced by the namespaced one.`

### Consequences

- `build_code_index` and `scan_deps` share one `should_skip_path`, so the map and the index cannot drift apart again.
- The pack's own repo map is useful again: 13 files with real fan-in.
- Migration is a dry run by default, moves rather than deletes, and refuses a dirty or non-Git worktree.

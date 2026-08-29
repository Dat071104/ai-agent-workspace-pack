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

---

## Decision Entry

### Decision ID

`DEC-0005`

### Date

`2026-08-28`

### Context

`An installed pack cannot pull fixes from the source pack, and nothing recorded which revision a project was running.`

### Options

| Option | Description | Pros | Cons |
| --- | --- | --- | --- |
| A | Git submodule or clone per project | Real upstream, real version | Reintroduces the clone the namespaced design rejected; a submodule is one more thing to explain and to break |
| B | Hand-bumped semantic version in the pack | Readable | Goes stale the moment someone forgets to bump it |
| C | `--update` plus a stamp taken from the source Git revision | No manual step to forget; honest about a dirty source; the update is a reviewable diff | The stamp is meaningful only against the source pack |

### Decision

`Choose C. The revision is derived, never typed, and a project reports it every session.`

### Rationale

`The stamp exists to answer "which pack is this project running", which is answerable locally. "Is it behind" needs a source pack present, so session_start reports the version rather than claiming staleness it cannot verify.`

### Consequences

- `_agent_ops/` is excluded from the refresh, so project memory survives an update.
- Files the current revision no longer ships are removed, so a renamed pack file does not linger in an older install.
- An update refuses a dirty or non-Git worktree unless `--allow-dirty`, keeping it revertible.
- An install made before this change reports `version unknown` rather than pretending to be current.

---

## Decision Entry

### Decision ID

`DEC-0006`

### Date

`2026-08-29`

### Context

`The root AGENTS.md bridge was a bare "@ai-agent-workspace-pack/AGENTS.md" line, and the generated CLAUDE.md / GEMINI.md imported the pack directly. Both were treated as contracts; neither is one. Codex concatenates AGENTS.md and expands no @path, so the bridge reached it as decoration. And a project whose real governance lives in its own AGENTS.md had those rules preserved on disk but absent from Claude's and Gemini's context.`

### Options

| Option | Description | Pros | Cons |
| --- | --- | --- | --- |
| A | Keep the `@path` bridge and rely on the model opening the path it read | No change | Behavior, not a contract; silently correct on some runs and silently wrong on others |
| B | Managed prose block in the root AGENTS.md, and harness memory files that import the root first and the pack second | One canonical entry point every harness resolves identically; host rules always precede pack workflow | Claude and Gemini need two import lines instead of one |
| C | Duplicate the pack's instructions into the root AGENTS.md | Guaranteed in context | Two copies that drift; defeats the point of the namespaced layout |

### Decision

`Choose B. The root AGENTS.md is the single canonical entry point; the pack is reached from it.`

### Rationale

`A rule that is on disk but not in context is not a rule. The only text every harness is guaranteed to receive identically is the literal content of the file it auto-discovers, so the instruction lives there as prose. The @path imports remain, but as an optimization for the harnesses that expand them, never as the mechanism the design depends on.`

### Consequences

- The managed block is versioned (`v2`). A v1 block or the v1 bare link line is replaced in place, so an older install upgrades without a second bridge appearing.
- Refreshing an existing bridge no longer requires `--install-agents-bridge`: it regenerates pack-owned text. Installing a bridge where none exists still requires the flag, because that adds text to a host file.
- `CLAUDE.md` / `GEMINI.md` carry two import lines in a namespaced install, host file first.

---

## Decision Entry

### Decision ID

`DEC-0007`

### Date

`2026-08-29`

### Context

`source_state.CODE_SUFFIXES listed .go, .rs, .java, .rb, .php and .cs as project code; scan_deps -- the scanner that builds the graph -- parses only Python and JS/TS. A Go repository was told its graph was stale on every commit, the rebuild ignored every changed file, and the next session was told the same thing.`

### Options

| Option | Description | Pros | Cons |
| --- | --- | --- | --- |
| A | Write parsers for Go, Rust and Java | Widest coverage | Large, and each parser is a new source of wrong `exact` edges |
| B | One suffix list, owned by `source_state.py`, narrowed to what the scanner parses | Freshness can never disagree with indexing | The graph stays Python + JS/TS, and the README has to say so |

### Decision

`Choose B, and state the language boundary in the README rather than implying uniform support.`

### Rationale

`A staleness warning that no rebuild can clear is worse than no warning: it trains the reader to ignore the one signal that is supposed to mean something. The memory, protocol, hygiene and git layers really are language-agnostic; only the code graph is not, and saying which is which costs one paragraph.`

### Consequences

- `source_state.py` owns `CODE_SUFFIXES`, `EMBEDDED_PACK_MARKERS` and `looks_like_pack`; `scan_deps.py` imports them.
- A nested pack is detected by signature rather than by the hardcoded folder name, so renaming the install folder no longer turns pack internals back into project source.
- `--ops-folder` now requires the leaf name `_agent_ops`, the one name every tool skips.

---

## Decision Entry

### Decision ID

`DEC-0008`

### Date

`2026-08-29`

### Context

`--folder accepted any relative path, so a pack could be installed at tools/my-pack/. The scanner detects a pack among the root's immediate children and freshness reads only the first path component, so neither saw it: a scratch install produced 15 indexed files, 14 of them the pack's own scripts and 1 the actual application. migrate_pack.py validated nothing at all, so --folder ../escape moved the pack out of the project.`

### Options

| Option | Description | Pros | Cons |
| --- | --- | --- | --- |
| A | Make the scanner search for a pack at any depth | `--folder` stays free-form | Walks the whole tree to answer "is this infrastructure"; a vendored copy of the pack inside a dependency would start excluding real project code |
| B | Require the pack folder to be one directory directly under the project root | Detection stays a single `iterdir()`; the rule is checked once, where the pack is placed | `--folder tools/my-pack` is no longer accepted |

### Decision

`Choose B. Depth one is the precondition the existing detection was already written against; enforce it instead of re-deriving it in every scanner.`

### Rationale

`The permissive path was never a supported layout, only an unvalidated one -- it silently produced a code graph about the pack rather than about the project, which is a wrong answer rather than an error. Option A would make an inexpensive check expensive and would create a new false-positive class.`

### Consequences

- `source_state.pack_folder()` is the one validator; `embed_pack.py`, `migrate_pack.py` and `init_project_ops.py --embedded-folder` all use it.
- `--ops-folder` keeps `relative_folder()`: a nested ops path such as `ai-agent-workspace-pack/_agent_ops` is legitimate, and its leaf name is separately enforced.
- `migrate_pack.py` can no longer move a pack outside `--target`.

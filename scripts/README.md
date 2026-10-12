# Scripts

Lightweight Python helpers for initializing project memory, generating the repo
map, running session-start checks, scanning dependencies, checking repo hygiene,
generating starter context cards, and summarizing/rotating implementation logs.

All scripts use the Python standard library only.

`embed_pack.py` is the portable installation entry point: it copies this pack
into `<target>/ai-agent-workspace-pack/`, then initializes fresh nested
operations, a preserving root `AGENTS.md` bridge, and the root `.codex/` and
`.claude/` pointer files the harnesses need to discover the subagents and team
skills. It is not copied into runtime tools because it requires the full source
pack.

- **Shipping set.** What is copied is decided in one place (`pack_manifest.py`):
  an allowlist of pack entries (root documents, `*-team/`, `commands/`,
  `core-context/`, `harness/`, `scripts/`, `.claude/` and `.codex/` adapter
  sources), narrowed to Git-tracked files when the source is its own repository.
  Never shipped: `.env` files, virtualenvs and other local state, `tests/`,
  `examples/`, and the source's `_agent_ops/`. New pack files must be `git add`-ed
  (staged) to ship; no commit is needed. Before writing anything, the installer
  refuses if a file the pack needs to run is missing from the shipping set, and
  names each one; other untracked files are reported as skipped.
- **In place.** Run from a pack already copied to `<target>/<folder>/`
  (`python ai-agent-workspace-pack/scripts/embed_pack.py --target .`), it copies
  nothing: it writes `PACK_VERSION` and `PACK_MANIFEST.json`, runs init, and lists
  files outside the shipping set (for example `tests/`) as left untouched. A
  source nested inside the destination, or the reverse, is refused.
- **Records.** Every install writes `<folder>/PACK_VERSION` (reported by
  `session_start.py`) and `<folder>/PACK_MANIFEST.json` (sha256 of each shipped
  file), the ownership proof `--update` relies on.
- **`--update`** refreshes an installed pack and never touches `_agent_ops/`
  records. A shipped file the host edited is saved to
  `<folder>/.update-backup/<YYYYmmdd-HHMMSS>[-N]/` (a new folder per update,
  git-ignored by the pack's `.gitignore`) and then overwritten; a file no longer
  shipped is removed only if provably unmodified; unknown files are never
  touched. It passes `--policy-history <source>` to init so unedited generated
  policy from an older revision can be recognized and refreshed. It refuses on a
  dirty or non-Git worktree without `--allow-dirty`.

`migrate_pack.py` moves an older flat install into the namespaced folder. It is
a dry run by default, moves rather than deletes, and refuses to touch a dirty or
non-Git worktree without `--allow-dirty`. A file moves only with content proof
(bytes equal the source file, or a version it held in the source's history); any
name-only collision is a conflict and nothing is moved.

`init_project_ops.py` copies the runtime scripts (the `RUNTIME_TOOLS` list in it) into
the target project as `_agent_ops/tools/`. Inside a project, run them as
`python _agent_ops/tools/<script> ...`; the `python scripts/<script> ...` form
below is for working on the pack itself. Install/ownership tooling
(`init_project_ops.py`, `ops_gate.py`, `ops_policy.py`, `embed_pack.py`,
`migrate_pack.py`, `pack_*.py`) does not travel -- it needs `core-context/` or the
full source pack.

These are the deterministic half of a managed session. Running them keeps the
model from having to remember mechanical bookkeeping, which matters most on
weaker or prompt-only harnesses. Every one of them has a manual fallback
described in `core-context/SESSION_PROTOCOL.template.md`; the pack still works
without Python.

## Commands

```bash
# One-time per repo: create _agent_ops/, copy the tools in, build the code
# index, generate REPO_MAP.md, write the hybrid _agent_ops/.gitignore, and add
# an AGENTS.md if the project has none. Never overwrites without --force.
python scripts/init_project_ops.py --target "D:\MyProject"
#   --no-tools      do not copy the tools into <target>/_agent_ops/tools/
#   --embedded-folder ai-agent-workspace-pack
#                   keep project operations inside a copied pack folder and
#                   use a managed root AGENTS.md block pointing at it
#   --no-agents-md  do not create AGENTS.md at the target root
#   --install-agents-bridge  explicitly add/update the managed bridge in an
#                       existing embedded project's AGENTS.md
#   --check-agents-bridge    read-only bridge health check
#   --no-index      skip code_index.json    --no-repo-map  skip REPO_MAP.md
#   --force         regenerate derived files (code index, repo map); never
#                   overwrites memory records, host-owned adapters, or edited
#                   policy files (tools/ are always refreshed)
#   --reset-memory  memory not proven this project's (foreign, unverifiable,
#                   damaged stamp, or unstamped): back up EVERY
#                   file to <ops>/backups/<timestamp>/ (gitignored), then fresh
#                   templates
#   --claim-memory  adopt the existing memory as this project's and stamp it
#   --policy-history <source-pack-checkout>
#                   recognize an unedited SESSION_PROTOCOL/OPERATING_RULES/INDEX
#                   from an older revision and refresh it
#   --install-repo-map-hook  opt in to a managed pre-commit map refresh hook

# When init finds memory that is not provably this project's -- including any
# unstamped memory that has real records -- it exits 3 and writes nothing; it
# prints the --reset-memory / --claim-memory commands. embed_pack.py and
# migrate_pack.py accept the same two flags and pass them to init; embed_pack.py
# asks the same question before it writes anything.

# Start of every managed session. Read-only: git state, what changed since the
# memory was last verified, repo-map staleness, unfilled placeholders, log size.
python scripts/session_start.py --root .

# The codegraph-lite read: modules, highest fan-in files, entry points. Capped.
# Regenerate whenever code files are added, moved, or removed.
python scripts/generate_repo_map.py --root . --output _agent_ops/REPO_MAP.md --force

# Symbol-level graph: classes, functions, methods, routes, and the CALLS /
# IMPORTS / EXTENDS edges between them. Rebuild when code changes.
python scripts/build_code_index.py --root .

# Before an authorized commit containing staged project code: rebuild the index
# and map once for the Git index, then stage only the map. The helper refuses
# when unstaged or untracked code would make the map disagree with the commit.
python scripts/refresh_repo_map.py --root . --stage

# The one query tool. Structural retrieval instead of grep -> read -> grep.
python scripts/explore.py --symbol charge          # definitions, callers, callees, flow
python scripts/explore.py --path checkout charge   # how control reaches a symbol
python scripts/explore.py --impact getUser         # blast radius + tests to run
#   (when no test is in the graph: "Candidate tests" = text-match leads, not edges)
python scripts/explore.py --file src/auth.py       # what a file holds, who imports it
python scripts/explore.py --entrypoints            # routes + unreferenced symbols

# File-level drill-down when the symbol graph is not needed.
python scripts/scan_deps.py --root . --seed "auth,login,session" --hops 2 --output markdown

# Before release, and to enforce the hybrid _agent_ops/ tracking policy.
python scripts/check_repo_hygiene.py --root .

# Starter context card from light repo inspection.
python scripts/generate_context_card.py --root . --name "Project Alpha"

# Summarize the log; --rotate archives older entries so the log stays cheap.
python scripts/summarize_implementation_log.py --log "_agent_ops/IMPLEMENTATION_LOG.md"
python scripts/summarize_implementation_log.py --log "_agent_ops/IMPLEMENTATION_LOG.md" \
    --rotate --keep 10 --output "_agent_ops/LOG_SUMMARY.md" --force
```

## Module Map (internals of install, ownership and policy)

Split along one responsibility each. `ops_identity.py`, `session_state.py` and
`source_state.py` ship into `_agent_ops/tools/` (session_start.py imports them);
the rest stay in the pack (init, install and update need the full source pack).

| Module | Role |
| --- | --- |
| `ops_identity.py` | Whose `_agent_ops/` memory is this: states OWNED / UNBOUND / FOREIGN / UNVERIFIABLE / LEGACY / NEW from `OPS_OWNER.json` and the Git root commit(s). Read-only; strict stamp schema (a damaged stamp is unverifiable, never bindable). |
| `session_state.py` | Parses what the ops records say (sections, placeholders, task `## Status`, open questions); `session_start.py` prints. |
| `ops_gate.py` | init's ownership gate: refuse (exit 3), `--reset-memory` with a sha256-verified backup, `--claim-memory`, templates-only detection; the only stamp writer; `preflight_refusal` lets embed ask before writing. |
| `ops_policy.py` | Tracks generated policy files in `OPS_POLICY.json`; refreshes one only when provably unedited, keeps and reports customized ones. |
| `pack_manifest.py` | The shipping set (allowlist + Git-tracked) and `PACK_MANIFEST.json` (path to sha256). |
| `pack_ownership.py` | Proof a host file is the pack's: manifest hash, else `PACK_VERSION` revision blob, else any historical blob. |
| `pack_sync.py` | Writes/refreshes the shipping set in a host folder: backups to `.update-backup/`, proven-only removals. |
| `source_state.py` | Shared Git-index helpers (repo-map freshness, clean-worktree and pack-folder checks). |

## Which Script Answers Which Question

| Question | Script |
| --- | --- |
| What state is this session starting from? | `session_start.py` |
| Where does the code live? What is central? | `generate_repo_map.py` |
| Who calls this function? What does it call? | `explore.py --symbol` |
| How does a request actually reach this code? | `explore.py --path` |
| What breaks if I change this, and which tests cover it? | `explore.py --impact` |
| What routes exist? What looks unreferenced? | `explore.py --entrypoints` |
| Which files does *this* change touch? | `scan_deps.py` |
| Is my memory stale relative to the code? | `session_start.py` |
| Is the log getting expensive to read? | `summarize_implementation_log.py --rotate` |
| Which ops records does this work still owe before closure? | `closure_check.py` (`--compact` folds proven rows; `--strict` exits 2 on MISSING) |
| Whose `_agent_ops/` memory is this? | `session_start.py` (ownership verdict) |
| Is this repo safe to make public? | `check_repo_hygiene.py` |

## Safety

- Scripts are cross-platform.
- Scripts print clear output.
- Scripts do not modify code unexpectedly.
- `session_start.py` is strictly read-only.
- `init_project_ops.py` will not overwrite existing files unless `--force` is passed.
- `summarize_implementation_log.py --rotate` rewrites the log in place. It writes
  and verifies the archive first, and aborts without touching the log if any
  entry failed to reach it. Archiving is a move, never a delete.
- `check_repo_hygiene.py` exits 1 on forbidden tracked files or `_agent_ops/`
  policy violations, so it can gate a release step.
- `build_code_index.py` writes `_agent_ops/code_index.json`, which is gitignored:
  it is a derived artifact, can reach tens of MB on a large repository, and would
  conflict on every merge. `REPO_MAP.md` is the small tracked view of it.

## Reading the code graph honestly

Every edge carries a provenance tag. Consumers must surface it:

| Tag | Meaning |
| --- | --- |
| `exact` | Resolved through the file's own imports or local scope. |
| `heuristic` | The name is unique repo-wide, so the target is inferred. |
| `ambiguous` | Several definitions share the name; all candidates are kept. |
| `weak` | Regex-extracted JS/TS, because no JS parser ships with Python. |

`exact` never applies to an attribute call (`obj.save()`): the indexer does not
resolve the receiver's type, so a name match against a same-file or
same-import definition is a lead, not a proof. Attribute calls resolve to at
most `heuristic` (the name is unique repo-wide) or `ambiguous` (several
definitions share it) -- direct calls (`save()`, `imported_fn()`) are the only
ones that can earn `exact`.

Python is parsed with `ast`, so its symbols and local calls are trustworthy.
JS/TS is regex-only. Nothing here sees dynamic dispatch, DI wiring, reflection,
or runtime registries, so:

- an `--impact` result is the MINIMUM blast radius, never the maximum;
- `--impact` groups its transitively affected symbols by the WORST edge
  confidence on the path back to the target, not just hop count: "Confirmed
  impact" is exact-only, "Probable impact" includes a heuristic edge, and
  "Uncertain leads" includes an ambiguous or weak one -- an exact-looking hop
  downstream of a weak one is still a weak lead;
- "nothing calls this" in `--entrypoints` is a CANDIDATE for dead code, never a
  verdict -- confirm by search and by running the tests before deleting.

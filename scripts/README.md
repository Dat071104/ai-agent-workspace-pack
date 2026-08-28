# Scripts

Lightweight Python helpers for initializing project memory, generating the repo
map, running session-start checks, scanning dependencies, checking repo hygiene,
generating starter context cards, and summarizing/rotating implementation logs.

All scripts use the Python standard library only.

`embed_pack.py` is the portable installation entry point: it copies this pack
into `<target>/ai-agent-workspace-pack/` without `.git/` or the source pack's
project-specific `_agent_ops/`, then initializes fresh nested operations and a
preserving root `AGENTS.md` bridge. It is not copied into runtime tools because
it requires the full source pack.

`init_project_ops.py` copies every other script here into the target project as
`_agent_ops/tools/`. Inside a project, run them as
`python _agent_ops/tools/<script> ...`; the `python scripts/<script> ...` form
below is for working on the pack itself. Only `init_project_ops.py` does not
travel -- it needs `core-context/`.

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
#                   use a first-line root AGENTS.md bridge to it
#   --no-agents-md  do not create AGENTS.md at the target root
#   --install-agents-bridge  explicitly add/update the managed bridge in an
#                       existing embedded project's AGENTS.md
#   --check-agents-bridge    read-only bridge health check
#   --no-index      skip code_index.json    --no-repo-map  skip REPO_MAP.md
#   --force         overwrite memory files (tools/ are always refreshed)
#   --install-repo-map-hook  opt in to a managed pre-commit map refresh hook

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

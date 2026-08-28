# Repo Map / Ban do ma nguon

Generated file. Do not hand-edit; regenerate with
`python scripts/generate_repo_map.py --root . --output _agent_ops/REPO_MAP.md --force`.

Read this BEFORE grepping the repository. It answers "where does the code
live" and "what breaks if I touch this" in one Tier-1 read.

## Last Verified Commit

`f0fa45e`

## Indexed Source Fingerprint

`sha256:13:34ab8a8aee8ed57acd78a9860a4b17513b464721b26b10c11ec1985da7b25e03`

## Snapshot

- Branch: `main`
- Generated: `2026-08-28`
- Code files indexed: 1
- Stack: Unknown

## Modules

`Inbound` counts imports coming from OUTSIDE the module: higher means more
code depends on it, so changes there travel further.

| Module | Files | Inbound | Entry points |
| --- | --- | --- | --- |
| `tests` | 1 | 0 | - |

## Hot Files (widest blast radius)

Ranked by fan-in. Treat an edit here as cross-module until proven otherwise.

| File | Imported by | Imports |
| --- | --- | --- |
| _no local import edges resolved_ | | |

## Symbol Graph

170 symbols, 328 edges (exact 183, heuristic 145, ambiguous 0, weak 0).

### Most-called symbols

| Symbol | Called by | Where |
| --- | --- | --- |
| `read_text` | 38 | `scripts/session_start.py:80` |
| `WorkspaceToolsGoldenTests.write` | 25 | `tests/test_workspace_tools.py:34` |
| `WorkspaceToolsGoldenTests.init_project` | 20 | `tests/test_workspace_tools.py:53` |
| `WorkspaceToolsGoldenTests.run_tool` | 14 | `tests/test_workspace_tools.py:40` |
| `run` | 13 | `scripts/refresh_repo_map.py:25` |
| `git_value` | 6 | `scripts/generate_context_card.py:12` |
| `Graph.label` | 5 | `scripts/explore.py:100` |
| `write_if_absent` | 5 | `scripts/init_project_ops.py:127` |
| `tool_prefix` | 5 | `scripts/scan_deps.py:63` |
| `resolve_ops_dir` | 5 | `scripts/source_state.py:52` |
| `WorkspaceToolsGoldenTests.make_source_fixture` | 5 | `tests/test_workspace_tools.py:56` |
| `Graph.find` | 4 | `scripts/explore.py:83` |

Query it instead of grepping:

```bash
python scripts/explore.py --root . --symbol <name>    # callers, callees, flow
python scripts/explore.py --root . --impact <name>    # blast radius + tests
python scripts/explore.py --root . --path <a> <b>     # how a reaches b
```

## Entry Points

- None detected by filename convention. Confirm manually.

## Oversized Files

Files past 400 lines. Long files are where agents lose the thread and
where unrelated responsibilities collect. Split along a responsibility
boundary before adding to one of these.

| File | Lines |
| --- | --- |
| `tests/test_workspace_tools.py` | 832 |

## Isolated Files

1 file(s) have no resolved local imports in either direction.
They are listed only on demand -- enumerating them here would recreate the
context bloat this map exists to prevent.

## Drill Down

This map is deliberately shallow. For the affected zone of a specific change:

```bash
python scripts/scan_deps.py --root . --seed "<keyword>" --hops 2 --output markdown
```

## Limits

- Covers `.py`, `.js`, `.jsx`, `.ts`, `.tsx` only.
- Relative imports resolve exactly. Absolute Python imports and JS path
  aliases are inferred by probing parent directories, so they can be wrong;
  package imports (`react`, `numpy`) are not followed at all.
- Dynamic imports, DI wiring, and runtime registries are invisible here.
  Verify before claiming a file is unused.

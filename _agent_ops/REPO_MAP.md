# Repo Map / Ban do ma nguon

Generated file. Do not hand-edit; regenerate with
`python _agent_ops/tools/generate_repo_map.py --root . --output _agent_ops/REPO_MAP.md --force`.

Read this BEFORE grepping the repository. It answers "where does the code
live" and "what breaks if I touch this" in one Tier-1 read.

## Last Verified Commit

`27e5e7c`

## Indexed Source Fingerprint

`sha256:12:d977bddae0fd2ec8f3d28f4268ac9f67ebface458d581998f8d374bb6d5b16bd`

## Snapshot

- Branch: `main`
- Generated: `2026-08-27`
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

131 symbols, 242 edges (exact 196, heuristic 46, ambiguous 0, weak 0).

### Most-called symbols

| Symbol | Called by | Where |
| --- | --- | --- |
| `read_text` | 21 | `scripts/session_start.py:83` |
| `run` | 11 | `scripts/refresh_repo_map.py:25` |
| `WorkspaceToolsGoldenTests.init_project` | 11 | `tests/test_workspace_tools.py:52` |
| `WorkspaceToolsGoldenTests.write` | 11 | `tests/test_workspace_tools.py:33` |
| `WorkspaceToolsGoldenTests.run_tool` | 7 | `tests/test_workspace_tools.py:39` |
| `git_value` | 6 | `scripts/generate_context_card.py:12` |
| `Graph.label` | 5 | `scripts/explore.py:97` |
| `tool_prefix` | 5 | `scripts/scan_deps.py:63` |
| `WorkspaceToolsGoldenTests.make_source_fixture` | 5 | `tests/test_workspace_tools.py:55` |
| `Graph.find` | 3 | `scripts/explore.py:80` |
| `write_if_absent` | 3 | `scripts/init_project_ops.py:99` |
| `build_graph` | 3 | `scripts/scan_deps.py:267` |

Query it instead of grepping:

```bash
python _agent_ops/tools/explore.py --root . --symbol <name>    # callers, callees, flow
python _agent_ops/tools/explore.py --root . --impact <name>    # blast radius + tests
python _agent_ops/tools/explore.py --root . --path <a> <b>     # how a reaches b
```

## Entry Points

- None detected by filename convention. Confirm manually.

## Isolated Files

1 file(s) have no resolved local imports in either direction.
They are listed only on demand -- enumerating them here would recreate the
context bloat this map exists to prevent.

## Drill Down

This map is deliberately shallow. For the affected zone of a specific change:

```bash
python _agent_ops/tools/scan_deps.py --root . --seed "<keyword>" --hops 2 --output markdown
```

## Limits

- Covers `.py`, `.js`, `.jsx`, `.ts`, `.tsx` only.
- Relative imports resolve exactly. Absolute Python imports and JS path
  aliases are inferred by probing parent directories, so they can be wrong;
  package imports (`react`, `numpy`) are not followed at all.
- Dynamic imports, DI wiring, and runtime registries are invisible here.
  Verify before claiming a file is unused.

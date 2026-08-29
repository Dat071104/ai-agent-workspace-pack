# Repo Map / Ban do ma nguon

Generated file. Do not hand-edit; regenerate with
`python scripts/generate_repo_map.py --root . --output _agent_ops/REPO_MAP.md --force`.

Read this BEFORE grepping the repository. It answers "where does the code
live" and "what breaks if I touch this" in one Tier-1 read.

## Last Verified Commit

`b3fe982`

## Indexed Source Fingerprint

`sha256:14:18d9436f9dff41cd58a87f933de888ebe99b409723063b1de2564117a94a795f`

## Snapshot

- Branch: `main`
- Generated: `2026-08-29`
- Code files indexed: 14
- Stack: Unknown

## Modules

`Inbound` counts imports coming from OUTSIDE the module: higher means more
code depends on it, so changes there travel further.

| Module | Files | Inbound | Entry points |
| --- | --- | --- | --- |
| `scripts` | 13 | 0 | - |
| `tests` | 1 | 0 | - |

## Hot Files (widest blast radius)

Ranked by fan-in. Treat an edit here as cross-module until proven otherwise.

| File | Imported by | Imports |
| --- | --- | --- |
| `scripts/source_state.py` | 10 | 0 |
| `scripts/scan_deps.py` | 5 | 1 |
| `scripts/generate_context_card.py` | 3 | 0 |
| `scripts/build_code_index.py` | 1 | 3 |
| `scripts/generate_repo_map.py` | 1 | 3 |
| `scripts/summarize_implementation_log.py` | 1 | 0 |

## Symbol Graph

197 symbols, 396 edges (exact 201, heuristic 193, ambiguous 2, weak 0).

### Most-called symbols

| Symbol | Called by | Where |
| --- | --- | --- |
| `read_text` | 42 | `scripts/session_start.py:79` |
| `WorkspaceToolsGoldenTests.write` | 36 | `tests/test_workspace_tools.py:42` |
| `WorkspaceToolsGoldenTests.init_project` | 26 | `tests/test_workspace_tools.py:61` |
| `WorkspaceToolsGoldenTests.run_tool` | 24 | `tests/test_workspace_tools.py:48` |
| `run` | 18 | `scripts/refresh_repo_map.py:25` |
| `WorkspaceToolsGoldenTests.assert_root_bridge` | 7 | `tests/test_workspace_tools.py:96` |
| `git_value` | 6 | `scripts/generate_context_card.py:12` |
| `Graph.label` | 5 | `scripts/explore.py:100` |
| `tool_prefix` | 5 | `scripts/scan_deps.py:50` |
| `resolve_ops_dir` | 5 | `scripts/source_state.py:84` |
| `WorkspaceToolsGoldenTests.make_source_fixture` | 5 | `tests/test_workspace_tools.py:64` |
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
| `tests/test_workspace_tools.py` | 1225 |
| `scripts/init_project_ops.py` | 1018 |
| `scripts/session_start.py` | 613 |
| `scripts/scan_deps.py` | 525 |
| `scripts/build_code_index.py` | 497 |
| `scripts/explore.py` | 427 |
| `scripts/generate_repo_map.py` | 421 |

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

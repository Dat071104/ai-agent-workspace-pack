# Repo Map / Ban do ma nguon

Generated file. Do not hand-edit; regenerate with
`python scripts/generate_repo_map.py --root . --output _agent_ops/REPO_MAP.md --force`.

Read this BEFORE grepping the repository. It answers "where does the code
live" and "what breaks if I touch this" in one Tier-1 read.

## Last Verified Commit

`714ce2e`

## Indexed Source Fingerprint

`sha256:18:4836c4110c993b1a8d51c5326ad1a0c84965add453134614c89ea6b2842faff7`

## Snapshot

- Branch: `main`
- Generated: `2026-10-11`
- Code files indexed: 18
- Stack: Unknown

## Modules

`Inbound` counts imports coming from OUTSIDE the module: higher means more
code depends on it, so changes there travel further.

| Module | Files | Inbound | Entry points |
| --- | --- | --- | --- |
| `scripts` | 15 | 0 | - |
| `tests` | 3 | 0 | - |

## Hot Files (widest blast radius)

Ranked by fan-in. Treat an edit here as cross-module until proven otherwise.

| File | Imported by | Imports |
| --- | --- | --- |
| `scripts/source_state.py` | 11 | 0 |
| `scripts/scan_deps.py` | 5 | 2 |
| `scripts/generate_context_card.py` | 3 | 0 |
| `scripts/extract_java_csharp.py` | 2 | 0 |
| `scripts/build_code_index.py` | 1 | 4 |
| `scripts/generate_repo_map.py` | 1 | 3 |
| `scripts/session_start.py` | 1 | 4 |
| `scripts/summarize_implementation_log.py` | 1 | 0 |

## Symbol Graph

271 symbols, 687 edges (exact 233, heuristic 202, ambiguous 252, weak 0).

### Most-called symbols

| Symbol | Called by | Where |
| --- | --- | --- |
| `ClosureCheckTests.write` | 59 | `tests/test_closure_check.py:35` |
| `JavaCSharpGraphTests.write` | 59 | `tests/test_java_csharp.py:117` |
| `WorkspaceToolsGoldenTests.write` | 59 | `tests/test_workspace_tools.py:42` |
| `read_text` | 47 | `scripts/session_start.py:79` |
| `WorkspaceToolsGoldenTests.init_project` | 26 | `tests/test_workspace_tools.py:61` |
| `WorkspaceToolsGoldenTests.run_tool` | 24 | `tests/test_workspace_tools.py:48` |
| `Scanner.run` | 23 | `scripts/extract_java_csharp.py:230` |
| `run` | 23 | `scripts/refresh_repo_map.py:25` |
| `git` | 10 | `scripts/closure_check.py:35` |
| `ClosureCheckTests.run_check` | 10 | `tests/test_closure_check.py:40` |
| `ClosureCheckTests.row` | 8 | `tests/test_closure_check.py:47` |
| `build_index` | 7 | `scripts/build_code_index.py:294` |

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
| `scripts/init_project_ops.py` | 1020 |
| `scripts/session_start.py` | 613 |
| `scripts/scan_deps.py` | 534 |
| `scripts/build_code_index.py` | 506 |
| `scripts/explore.py` | 427 |
| `scripts/generate_repo_map.py` | 427 |
| `scripts/extract_java_csharp.py` | 400 |

## Isolated Files

3 file(s) have no resolved local imports in either direction.
They are listed only on demand -- enumerating them here would recreate the
context bloat this map exists to prevent.

## Drill Down

This map is deliberately shallow. For the affected zone of a specific change:

```bash
python scripts/scan_deps.py --root . --seed "<keyword>" --hops 2 --output markdown
```

## Limits

- Covers `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.java`, `.cs` only. Java and C#
  are regex-extracted (not parsed): their calls are always `weak`, and C#
  has no file import edges because `using` names namespaces, not files.
- Relative imports resolve exactly. Absolute Python imports and JS path
  aliases are inferred by probing parent directories, so they can be wrong;
  package imports (`react`, `numpy`) are not followed at all.
- Dynamic imports, DI wiring, and runtime registries are invisible here.
  Verify before claiming a file is unused.

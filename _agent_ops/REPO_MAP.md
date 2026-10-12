# Repo Map / Ban do ma nguon

Generated file. Do not hand-edit; regenerate with
`python _agent_ops/tools/generate_repo_map.py --root . --output _agent_ops/REPO_MAP.md --force`.

Read this BEFORE grepping the repository. It answers "where does the code
live" and "what breaks if I touch this" in one Tier-1 read.

## Last Verified Commit

`a67f0d2`

## Indexed Source Fingerprint

`sha256:33:b8dbca4b323ac797224a4e8b443fed058c56777f20847c8538b96553f0797746`

## Snapshot

- Branch: `main`
- Generated: `2026-10-12`
- Code files indexed: 33
- Stack: Unknown

## Modules

`Inbound` counts imports coming from OUTSIDE the module: higher means more
code depends on it, so changes there travel further.

| Module | Files | Inbound | Entry points |
| --- | --- | --- | --- |
| `scripts` | 22 | 0 | - |
| `tests` | 11 | 0 | - |

## Hot Files (widest blast radius)

Ranked by fan-in. Treat an edit here as cross-module until proven otherwise.

| File | Imported by | Imports |
| --- | --- | --- |
| `scripts/source_state.py` | 13 | 0 |
| `scripts/scan_deps.py` | 5 | 2 |
| `scripts/pack_manifest.py` | 4 | 0 |
| `scripts/generate_context_card.py` | 3 | 0 |
| `scripts/ops_gate.py` | 3 | 3 |
| `scripts/ops_identity.py` | 3 | 1 |
| `scripts/extract_java_csharp.py` | 2 | 0 |
| `scripts/ops_policy.py` | 2 | 1 |
| `scripts/pack_ownership.py` | 2 | 1 |
| `scripts/pack_sync.py` | 2 | 2 |
| `tests/test_ops_ownership.py` | 2 | 0 |
| `tests/test_shipping.py` | 2 | 0 |
| `scripts/build_code_index.py` | 1 | 4 |
| `scripts/generate_repo_map.py` | 1 | 3 |
| `scripts/session_start.py` | 1 | 6 |

## Symbol Graph

617 symbols, 1383 edges (exact 569, heuristic 550, ambiguous 264, weak 0).

### Most-called symbols

| Symbol | Called by | Where |
| --- | --- | --- |
| `read_text` | 97 | `scripts/session_start.py:101` |
| `run` | 46 | `tests/test_ops_ownership.py:35` |
| `Scanner.run` | 37 | `scripts/extract_java_csharp.py:230` |
| `run` | 37 | `scripts/refresh_repo_map.py:25` |
| `write` | 37 | `tests/test_ops_ownership.py:49` |
| `OpsCase.init` | 29 | `tests/test_ops_ownership.py:106` |
| `git` | 29 | `tests/test_ops_ownership.py:43` |
| `WorkspaceToolsGoldenTests.init_project` | 26 | `tests/test_workspace_tools.py:62` |
| `ShippingBase.make_source` | 25 | `tests/test_shipping.py:64` |
| `WorkspaceToolsGoldenTests.run_tool` | 24 | `tests/test_workspace_tools.py:49` |
| `git` | 21 | `scripts/closure_check.py:43` |
| `OpsCase.session` | 19 | `tests/test_ops_ownership.py:109` |

Query it instead of grepping:

```bash
python _agent_ops/tools/explore.py --root . --symbol <name>    # callers, callees, flow
python _agent_ops/tools/explore.py --root . --impact <name>    # blast radius + tests
python _agent_ops/tools/explore.py --root . --path <a> <b>     # how a reaches b
```

## Entry Points

- None detected by filename convention. Confirm manually.

## Oversized Files

Files past 400 lines. Long files are where agents lose the thread and
where unrelated responsibilities collect. Split along a responsibility
boundary before adding to one of these.

| File | Lines |
| --- | --- |
| `tests/test_workspace_tools.py` | 1233 |
| `scripts/init_project_ops.py` | 1128 |
| `tests/test_ops_ownership.py` | 748 |
| `scripts/session_start.py` | 592 |
| `tests/test_ops_ownership_round2.py` | 584 |
| `scripts/scan_deps.py` | 534 |
| `scripts/build_code_index.py` | 506 |
| `scripts/explore.py` | 459 |
| `scripts/generate_repo_map.py` | 427 |
| `scripts/ops_gate.py` | 424 |

## Isolated Files

5 file(s) have no resolved local imports in either direction.
They are listed only on demand -- enumerating them here would recreate the
context bloat this map exists to prevent.

## Drill Down

This map is deliberately shallow. For the affected zone of a specific change:

```bash
python _agent_ops/tools/scan_deps.py --root . --seed "<keyword>" --hops 2 --output markdown
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

# Repo Map / Ban do ma nguon

Generated file. Do not hand-edit; regenerate with
`python scripts/generate_repo_map.py --root . --output _agent_ops/REPO_MAP.md --force`.

Read this BEFORE grepping the repository. It answers "where does the code
live" and "what breaks if I touch this" in one Tier-1 read.

## Last Verified Commit

`5648e9b`

## Indexed Source Fingerprint

`sha256:37:5023c11ca76641da0101ae3086aff133d58c552ed934841cf13ddd716ceab36a`

## Snapshot

- Branch: `main`
- Generated: `2026-10-20`
- Code files indexed: 37
- Stack: Unknown

## Modules

`Inbound` counts imports coming from OUTSIDE the module: higher means more
code depends on it, so changes there travel further.

| Module | Files | Inbound | Entry points |
| --- | --- | --- | --- |
| `scripts` | 22 | 0 | - |
| `tests` | 15 | 0 | - |

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
| `tests/test_shipping.py` | 3 | 0 |
| `scripts/extract_java_csharp.py` | 2 | 0 |
| `scripts/ops_policy.py` | 2 | 1 |
| `scripts/pack_ownership.py` | 2 | 1 |
| `scripts/pack_sync.py` | 2 | 2 |
| `tests/test_ops_ownership.py` | 2 | 0 |
| `scripts/build_code_index.py` | 1 | 4 |
| `scripts/generate_repo_map.py` | 1 | 3 |
| `scripts/session_start.py` | 1 | 6 |

## Symbol Graph

693 symbols, 1514 edges (exact 438, heuristic 756, ambiguous 320, weak 0).

### Most-called symbols

| Symbol | Called by | Where |
| --- | --- | --- |
| `read_text` | 98 | `scripts/session_start.py:101` |
| `run` | 49 | `tests/test_ops_ownership.py:35` |
| `Scanner.run` | 40 | `scripts/extract_java_csharp.py:235` |
| `run` | 40 | `scripts/refresh_repo_map.py:25` |
| `write` | 37 | `tests/test_ops_ownership.py:49` |
| `OpsCase.init` | 29 | `tests/test_ops_ownership.py:106` |
| `git` | 29 | `tests/test_ops_ownership.py:43` |
| `ShippingBase.make_source` | 26 | `tests/test_shipping.py:64` |
| `WorkspaceToolsGoldenTests.init_project` | 26 | `tests/test_workspace_tools.py:63` |
| `WorkspaceToolsGoldenTests.run_tool` | 24 | `tests/test_workspace_tools.py:50` |
| `git` | 21 | `scripts/closure_check.py:43` |
| `OpsCase.session` | 19 | `tests/test_ops_ownership.py:109` |

Query it instead of grepping:

```bash
python scripts/explore.py --root . --symbol <name>    # callers, callees, flow
python scripts/explore.py --root . --impact <name>    # blast radius + tests (ambiguous: use Cls.method)
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
| `tests/test_workspace_tools.py` | 1234 |
| `scripts/init_project_ops.py` | 1128 |
| `tests/test_ops_ownership.py` | 748 |
| `scripts/build_code_index.py` | 595 |
| `scripts/session_start.py` | 592 |
| `tests/test_ops_ownership_round2.py` | 584 |
| `scripts/scan_deps.py` | 534 |
| `scripts/explore.py` | 476 |
| `scripts/generate_repo_map.py` | 427 |
| `scripts/ops_gate.py` | 424 |

## Isolated Files

8 file(s) have no resolved local imports in either direction.
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

# Implementation Log / Nhat ky trien khai

Append-only. Add a new entry for each meaningful task or phase that produces
implementation, test, audit, gate, or verification evidence -- including a
negative result that changes the next action. A prompt need not name this file
for the entry to be required.

## Entry Template

### Date

`YYYY-MM-DD`

### Task ID

`TASK-0001` or `not assigned`

### Phase / Task

`<phase or task name>`

### Files Touched

- `<file path>`

### What Changed / Evidence Produced

- `<change, or evidence produced; say "no source change" for an audit-only task>`

### Why

`<reason>`

### Tests Run

```bash
<command>
```

### Results

`<pass/fail and evidence>`

### Bugs Found

- `<bug or none>`

### Root Cause

`<root cause if known>`

### Fix Applied

`<fix or none>`

### Git Commit

`<hash or not committed>`

### Push Result

`<pushed/not pushed/not applicable>`

### Remaining Risks

- `<risk>`

### Next Step

`<next concrete task>`

### Date

`2026-08-27`

### Task ID

`TASK-0001`

### Phase / Task

`Managed AGENTS bridge v1.1`

### Files Touched

- `AGENTS.md`
- `scripts/{embed_pack,init_project_ops}.py`
- `tests/test_workspace_tools.py`
- `README.md`
- `scripts/README.md`
- `_agent_ops/PROJECT_CONTEXT_CARD.md`
- `_agent_ops/DECISION_LOG.md`
- `_agent_ops/RISK_REGISTER.md`

### What Changed / Evidence Produced

- Added explicit `--install-agents-bridge` and read-only `--check-agents-bridge` behavior.
- Bridge installation updates only a marker-bounded block, preserving host AGENTS content.
- Added golden coverage for generated embedded instructions, missing, installed, outdated, and corrupt bridge states.

### Why

`Existing host AGENTS.md files otherwise prevent reliable discovery of @start-here routing in an embedded pack.`

### Tests Run

```bash
python -B tests/test_workspace_tools.py
python scripts/init_project_ops.py --target . --check-agents-bridge
python scripts/check_repo_hygiene.py --root .
```

### Results

`12/12 golden tests passed; the pack bridge reported INSTALLED; hygiene found no forbidden tracked files or generated/private artifacts.`

### Bugs Found

- `Existing host AGENTS.md was preserved but had no pack routing entry point.`

### Root Cause

`The installer intentionally skipped an existing AGENTS.md without providing an opt-in integration path.`

### Fix Applied

`Implemented a marker-bounded, explicit bridge install/check lifecycle; documented the deferred namespaced migration.`

### Git Commit

`Pending at time of evidence record.`

### Push Result

`Not requested.`

### Remaining Risks

- `Flat embedded layout collision risk remains until v2.`

### Next Step

`Refresh the repository map after staging, review staged changes, and commit the verified v1.1 patch.`

### Date

`2026-08-27`

### Task ID

`TASK-0002`

### Phase / Task

`README bridge quick note and publication`

### Files Touched

- `README.md`
- `_agent_ops/PROJECT_CONTEXT_CARD.md`
- `_agent_ops/IMPLEMENTATION_LOG.md`

### What Changed / Evidence Produced

- Added a top-of-README quick note showing the one-time bridge install for existing AGENTS.md and the read-only check command.

### Why

`The detailed bridge section was below the install explanation; users need the operational distinction immediately.`

### Tests Run

```bash
python scripts/init_project_ops.py --target . --check-agents-bridge
python scripts/check_repo_hygiene.py --root .
```

### Results

`Pending final validation and push.`

### Bugs Found

- `None.`

### Root Cause

`Not applicable; this is a documentation discoverability improvement.`

### Fix Applied

`Added a concise quick-start note above the README problem statement.`

### Git Commit

`Pending.`

### Push Result

`Pending user-authorized push.`

### Remaining Risks

- `Flat embedded layout collision risk remains until v2.`

### Next Step

`Validate, commit, push origin/main, and verify the remote SHA.`

---

### Date

`2026-08-28`

### Task ID

`TASK-0002`

### Phase / Task

`Namespaced embedded-pack v2`

### Files Touched

- `scripts/init_project_ops.py`
- `scripts/{source_state,session_start,refresh_repo_map,build_code_index,explore,generate_repo_map,scan_deps,check_repo_hygiene}.py`
- `tests/test_workspace_tools.py`
- `README.md`, `scripts/README.md`, `AGENTS.md`, `START_HERE.md`, `TEAM_ROUTER.md`
- `_agent_ops/{REPO_MAP,PROJECT_CONTEXT_CARD,DECISION_LOG,RISK_REGISTER,SESSION_BRIEF,CURRENT_TASK}.md`

### What Changed / Evidence Produced

- Added `embed_pack.py`, a no-clone materializer that excludes source `.git/` and source `_agent_ops/` before it initializes the copied pack.
- Added `--embedded-folder ai-agent-workspace-pack`: ops state and runtime tools now live under the copied pack, not the application root.
- The namespaced bridge is the literal first line of root `AGENTS.md`; every pre-existing host instruction follows unchanged. Empty host files receive only that link.
- Runtime map/index/explore/session/hygiene/commit-refresh paths resolve the nested ops folder, and project code scanners exclude only a child with the complete pack signature.

### Why

`A flat copied pack collides with host paths and makes an embedded project look like a clone of the pack instead of an application.`

### Tests Run

```bash
python -B -m unittest tests.test_workspace_tools -v
python scripts/check_repo_hygiene.py --root .
git diff --check
```

### Results

`23 golden tests passed. Hygiene passed with zero generated/private artifacts. git diff --check passed.`

### Bugs Found

- `scripts/__pycache__/` was created by an explicit compile check and removed before final hygiene.

### Root Cause

`The compile command writes bytecode by design; runtime tools and tests themselves suppress bytecode.`

### Fix Applied

`Removed only the verified generated scripts/__pycache__/ directory; no project file was deleted.`

### Git Commit

`403e7a4 (feat: add namespaced embedded pack install).`

### Push Result

`Not requested.`

### Remaining Risks

- `The three root harness entry files remain necessary for automatic discovery; all pack content and ops state are namespaced.`

### Next Step

`User may run embed_pack.py from a local source pack to materialize a clean namespaced copy in a target project; push only if authorized.`

---

## Entry

### Date

`2026-08-28`

### Task ID

`TASK-0003`

### Phase / Task

`Restore harness discovery in the namespaced embedded layout and stop the symbol index from indexing a nested pack.`

### Files Touched

| File | Change |
| --- | --- |
| `scripts/init_project_ops.py` | added the root harness adapter installer, its `--no-root-adapters` opt-out, pack-relative path rewriting, and the ownership marker |
| `scripts/build_code_index.py` | excluded a nested workspace pack from the symbol index, matching the dependency scan |
| `scripts/session_start.py` | removed a duplicated Durable Recordkeeping Gate block |
| `tests/test_workspace_tools.py` | two contracts: root adapters (rewrite, marker, idempotence, host-owned protection, opt-out) and nested-pack index exclusion |
| `AGENTS.md`, `README.md`, `scripts/README.md` | documented the root adapters and the generated-pointer rule |

### What Changed / Evidence Produced

- A namespaced install now writes 17 root pointer files: `.codex/agents/*.toml` (4), `.claude/agents/*.md` (4), `.claude/skills/*/SKILL.md` (9). Verified in a scratch project: `ROOT ADAPTERS: 17 written, 0 unchanged`.
- Every pack-relative path inside a pointer is rewritten to the pack folder. Verified: `Follow ai-agent-workspace-pack/tester-team/SKILL.md.` in the Codex TOML; `` `ai-agent-workspace-pack/_agent_ops/REPO_MAP.md` `` in the Claude agent.
- Re-running is idempotent (`0 written, 16 unchanged`) with zero double prefixes across all 17 files; a host-owned `.claude/agents/tester.md` was reported as `SKIP host-owned adapter` and left byte-identical.
- The symbol index in a scratch project dropped from 14 files (13 of them pack scripts) to 1: `['src/index.js']`. `explore.py --symbol read_text` now returns no match instead of pack internals; `--symbol boot` resolves to `src/index.js:1`.
- `session_start.py` prints the Durable Recordkeeping Gate once (was twice).

### Why

`Codex reads .codex/agents and Claude Code reads .claude/agents and .claude/skills at the repository root only. The namespaced layout put both inside the pack folder, so the four subagents and nine team skills silently disappeared -- a capability the flat layout provided. Separately, REPO_MAP.md excluded a nested pack while the index did not, so the map reported the project's real file count while the symbol graph and explore answered with pack internals.`

### Tests Run

```bash
python -B -m unittest tests.test_workspace_tools
python -B scripts/check_repo_hygiene.py --root .
git diff --check
```

### Results

`25 golden tests passed (23 existing plus 2 new). Hygiene passed: 161 tracked files, zero forbidden or generated artifacts. git diff --check passed.`

### Bugs Found

- `session_start.py` reported a fresh repository with no commits as "not a git repository", because `is_git` is derived from `rev-parse HEAD`.

### Root Cause

`Root adapters: the namespaced move was made without accounting for harness discovery being root-only. Index pollution: build_code_index.iter_code_files filtered on SKIP_DIRS alone and never used the nested-pack exclusion added to scan_deps. Duplicate gate: a copy-paste block introduced in cf42265.`

### Fix Applied

`Generated marked root pointers with rewritten paths; switched the index to the nested-pack exclusion while keeping a pack checkout able to index itself; deleted the duplicated block. The empty-repository mislabel was left unfixed and reported -- it is a separate concern from this change.`

### Git Commit

`ad6f01c (feat(embed): restore harness discovery in the namespaced layout).`

### Push Result

`Not requested.`

### Remaining Risks

- `Flat (legacy) embedded roots still index their own pack scripts, because a flat pack and a pack checkout are indistinguishable by markers.`
- `Codex subagent discovery from .codex/agents was verified by file placement, not by a Codex run.`

### Next Step

`User to run embed_pack.py against the application repo, or authorize a local commit of these changes.`

---

## Entry

### Date

`2026-08-28`

### Task ID

`TASK-0003`

### Phase / Task

`Make the pack's own documented bootstrap produce the namespaced layout after a plain folder copy.`

### Files Touched

| File | Change |
| --- | --- |
| `scripts/init_project_ops.py` | `detect_embedded_folder()`; auto-selects namespaced mode when the pack lives inside the target; bridge warning now prints the exact fix command |
| `AGENTS.md`, `commands/start-here.md` | bootstrap instructions state the through-the-folder command and that the bridge edit needs consent |
| `tests/test_workspace_tools.py` | contract for copy-then-bootstrap, including the explicit `--ops-folder` override |

### What Changed / Evidence Produced

- Reproduced the defect: after copying the pack folder into a project, `python ai-agent-workspace-pack/scripts/init_project_ops.py --target .` created `_agent_ops/` at the APPLICATION ROOT, wrote no root adapters, and left no bridge.
- After the fix the same command prints `EMBEDDED FOLDER: auto-detected ai-agent-workspace-pack`, puts ops at `ai-agent-workspace-pack/_agent_ops`, writes `ROOT ADAPTERS: 17 written`, and leaves a host `AGENTS.md` byte-identical.
- The missing-bridge warning now prints the command that fixes it, and running that command yields `AGENTS BRIDGE: INSTALLED (namespaced bridge prepended; host text preserved)` with the host lines intact below.
- `--ops-folder _agent_ops` still overrides detection, so the legacy flat layout stays reachable.

### Why

`The bootstrap instruction the pack ships -- `init_project_ops.py --target .` -- is what an agent runs on `@start-here`. Resolved through a copied pack folder it silently produced the flat layout, so the pack's own documented path defeated the namespaced design and dropped the root adapters.`

### Tests Run

```bash
python -B -m unittest tests.test_workspace_tools
python -B scripts/check_repo_hygiene.py --root .
git diff --check
```

### Results

`26 golden tests passed. Hygiene passed. git diff --check passed.`

### Bugs Found

- The documented bootstrap command produced a root `_agent_ops/` and no adapters after a manual folder copy.

### Root Cause

`init_project_ops.py entered namespaced mode only on an explicit --embedded-folder, which no bootstrap instruction passed.`

### Fix Applied

`Detect that the running script's pack root is inside --target and default to that folder, unless --embedded-folder or --ops-folder was given explicitly.`

### Git Commit

`ad6f01c (feat(embed): restore harness discovery in the namespaced layout).`

### Push Result

`Not requested.`

### Remaining Risks

- `Prepending the root AGENTS.md bridge still requires an explicit flag by design, so an install left at the warning stage is inert until the user consents.`

### Next Step

`Await authorization to commit.`

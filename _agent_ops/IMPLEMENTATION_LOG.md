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

---

## Entry

### Date

`2026-08-28`

### Task ID

`TASK-0004`

### Phase / Task

`Close the two carried-over defects: the ambiguous flat-embedded exclusion and the unborn-repository mislabel.`

### Files Touched

| File | Change |
| --- | --- |
| `scripts/session_start.py` | split `is_git` from `has_commits`; report a repository with no commits as a repository |
| `scripts/scan_deps.py` | removed the root-level pack exclusion; `is_embedded_pack` -> `looks_like_pack`; `should_skip_path` is now the single skip rule |
| `scripts/build_code_index.py` | deleted its private walk; it calls `scan_deps.iter_code_files` |
| `scripts/migrate_pack.py` | new: moves a flat install into the namespaced folder, dry run by default |
| `tests/test_workspace_tools.py` | 5 contracts added; the flat-pack fixture now asserts the opposite behaviour |
| `README.md`, `scripts/README.md` | documented the migration |

### What Changed / Evidence Produced

- Unborn repository: `session_start.py` now prints `HEAD: none yet`, lists `A  src/app.py`, and says `no commits yet, so there is nothing to verify memory against` instead of `not a git repository`. Because `ls-files --stage` works without a commit, the fingerprint path also works: after rebuilding, it reports `Current with the staged source index`.
- Flat exclusion removed: this pack's own `REPO_MAP.md` went from `Code files indexed: 1` with an empty hot-files table to 13 files with real fan-in (`scripts/source_state.py` imported by 6).
- One walk: `build_code_index` no longer carries its own copy; the golden test asserts the index file list EQUALS the dependency scan's, rather than checking each separately.
- Migration verified on a fixture where `scripts/` holds both the pack's tools and an application file: 133 pack files moved, `scripts/my_app_deploy.js` and `src/app.py` stayed at the root, `_agent_ops/` moved with its content, 139 renames in `git status`, and the rebuilt index lists only the application's two files.

### Why

`RISK-0004 could not be fixed by a better heuristic: a flat install and the pack's own checkout are identical by signature, so the rule was guessing -- and it guessed wrong on this repository, silently reducing its own map to one file. Removing the case removes the ambiguity. RISK on session_start was one variable answering two questions, which cost a new project every staleness check on the session that builds its map.`

### Tests Run

```bash
python -B -m unittest tests.test_workspace_tools
python -B scripts/check_repo_hygiene.py --root .
git diff --check
```

### Results

`30 golden tests passed (26 before this task). Hygiene passed. git diff --check passed.`

### Bugs Found

- The first migration run left `code_index.json` and `REPO_MAP.md` describing the flat layout, because `init_project_ops` skips existing files without `--force` and `--force` would have overwritten project memory.

### Root Cause

`Derived artifacts moved along with project memory but were not invalidated.`

### Fix Applied

`migrate_pack.py deletes exactly those two derived files after the move so initialization rebuilds them; nothing else in _agent_ops is touched.`

### Git Commit

`9b31b28, aa10911, e80c7bf, 58ba5bf.`

### Push Result

`Pushed to origin/main.`

### Remaining Risks

- `A flat install that is never migrated keeps indexing the pack's scripts; that is now a documented state with a tool, not a silent heuristic.`
- `migrate_pack.py leaves LICENSE, .gitignore and README.md at the root for manual review, since ownership cannot be determined.`

### Next Step

`Optional: run migrate_pack.py against the application repo once its path is known.`

---

## Entry

### Date

`2026-08-28`

### Task ID

`TASK-0005`

### Phase / Task

`Give a copied pack an update path and a revision stamp.`

### Files Touched

| File | Change |
| --- | --- |
| `scripts/embed_pack.py` | `--update` refreshes an installed pack in place; both modes write `PACK_VERSION` |
| `scripts/source_state.py` | `worktree_is_clean` moved here and shared |
| `scripts/migrate_pack.py` | uses the shared helper instead of its own copy |
| `scripts/session_start.py` | reports the installed pack revision, and its absence |
| `tests/test_workspace_tools.py` | 2 contracts added (32 total) |
| `README.md`, `scripts/README.md`, `AGENTS.md` | documented the update path |

### What Changed / Evidence Produced

- Reproduced the gap: `embed_pack.py` on an existing install errored with `Destination already exists`, re-running `init_project_ops.py` refreshed only `_agent_ops/tools/` and the 17 adapters, and no file anywhere recorded a pack revision.
- Verified an update on a fixture aged deliberately -- an outdated `tester-team/SKILL.md`, a `scripts/removed_in_new_version.py` that a later revision would not ship, a `PROJECT_CONTEXT_CARD.md` marker, and a `deadbee` stamp: `139 files written`, `stale files removed: 1`, `version: deadbee -> dd81340-dirty`, the team file restored byte-for-byte, and `MY PROJECT MEMORY` still present.
- `git status` in the target showed 1 deletion and 2 modifications -- a reviewable diff, not an opaque overwrite.
- `session_start.py` prints ``Workspace pack: `ai-agent-workspace-pack` at version `dd81340-dirty` ``, and with the stamp removed prints `version unknown (no PACK_VERSION)` plus the command that fixes it.

### Why

`A pack copied into a project has no upstream. Without an update path every fix made here stayed live in earlier copies; without a stamp no project could say which revision it ran, so the drift was invisible rather than merely inconvenient. This is the gap that matters most for a repository whose purpose is reuse.`

### Tests Run

```bash
python -B -m unittest tests.test_workspace_tools
python -B scripts/check_repo_hygiene.py --root .
git diff --check
```

### Results

`32 golden tests passed. Hygiene passed. git diff --check passed.`

### Bugs Found

- None beyond the gap itself.

### Root Cause

`embed_pack.py only ever handled first installation, and nothing recorded provenance.`

### Fix Applied

`--update overwrites shipped content, removes files no longer shipped, leaves _agent_ops/ alone, and refuses an unrevertible worktree. PACK_VERSION records revision, date, and the revision replaced.`

### Git Commit

`2762542.`

### Push Result

`Pushed to origin/main.`

### Remaining Risks

- `The stamp names a source revision; a project cannot tell it is behind without a source pack to compare against. session_start reports, it does not claim staleness it cannot verify.`
- `An update overwrites hand-edits made inside the pack folder. That folder is pack-owned by design, and the refusal on a dirty worktree keeps the change revertible.`

### Next Step

`Use it on a real project; revisit only when a second project makes a sharper need visible.`

---

## Entry

### Date

`2026-08-29`

### Task ID

`TASK-0006`

### Scope

`Make the root AGENTS.md the one canonical entry point every harness resolves, and stop three copies of "what is project code" from disagreeing.`

### Files Changed

| File | Change |
| --- | --- |
| `scripts/init_project_ops.py` | bridge v2: one `agents_bridge()` for both layouts, prose instead of an `@path`; legacy v1 block and v1 link line replaced in place; `CLAUDE.md`/`GEMINI.md` import the root `AGENTS.md` first and the pack second; `--ops-folder` leaf name enforced |
| `scripts/source_state.py` | owns `CODE_SUFFIXES` (Python + JS/TS only), `EMBEDDED_PACK_MARKERS`, `looks_like_pack`; nested pack detected by signature, not by name |
| `scripts/scan_deps.py` | imports those definitions; `iter_code_files` prunes skipped directories with `os.walk` instead of filtering a full `rglob` |
| `scripts/session_start.py` | removed a third, unused `CODE_SUFFIXES` copy |
| `scripts/embed_pack.py`, `scripts/migrate_pack.py` | take `looks_like_pack` from its owner |
| `_agent_ops/tools/*.py` | refreshed from `scripts/`; the tracked copies had drifted from canonical |
| `tests/test_workspace_tools.py` | 5 contracts added (37 total) |
| `README.md`, `AGENTS.md`, `scripts/README.md` | describe the block bridge and the language boundary |

### Why

`Two of these were contract bugs, not polish. The bridge was a link only some harnesses expand, so whether the pack was read at all depended on model behavior; and the generated harness files imported the pack instead of the host's own AGENTS.md, so a project's governance could be preserved on disk and still never reach the model. The third was a self-inflicted blind spot: this repository was running its own stale tracked copies of the runtime tools, so a fix in scripts/ looked verified while the sessions kept executing the old build.`

### Tests Run

```bash
python -B -m unittest discover -s tests -q
python -B scripts/check_repo_hygiene.py --root .
python -B scripts/embed_pack.py --target <scratch project>
python -B <scratch>/ai-agent-workspace-pack/scripts/init_project_ops.py --target <scratch v1 install>
```

### Results

`37 golden tests passed (32 before, 5 added). Hygiene passed after removing tests/__pycache__. A scratch fresh install produced the v2 block above preserved host text, with CLAUDE.md/GEMINI.md importing the root first. A scratch project holding the v1 bare link line was upgraded in place: link removed, block installed, host text intact.`

### Bugs Found

- Root `AGENTS.md` bridge was an `@path` line; Codex expands none, so the pack was not reliably read.
- `CLAUDE.md` / `GEMINI.md` imported the pack directly, bypassing host governance.
- 8 of 10 tracked `_agent_ops/tools/*.py` differed from `scripts/`; this repo was dogfooding a build it never shipped.
- `source_state` and `scan_deps` disagreed on project-code suffixes, leaving a Go/Rust/Java repo permanently stale.
- `--ops-folder` accepted a name no scanner skips, which would index the agent's own tooling as project source.

### Root Cause

`Each piece was verified against the filesystem shape it produced rather than against the context a harness actually receives, and "project code" was defined independently in three files.`

### Fix Applied

`One versioned managed block, one canonical entry point per harness, one suffix list, one pack-signature check, and a test that fails when the tracked runtime copies drift from scripts/.`

### Git Commit

`21a08a8`

### Push Result

`Pushed to origin/main (72bfb85..21a08a8).`

### Remaining Risks

- `Codex's lack of @path expansion in AGENTS.md was established from the loader's documented behavior, not from a Codex run in this session. The v2 block is correct either way -- prose is read whether or not an import would also have worked -- so the fix does not depend on that claim.`
- `RISK-0007: no test drives a real harness. The suite asserts the bytes each harness would load, which is one level closer to the truth than the previous filesystem-shape assertions, but still not an end-to-end harness run.`

### Next Step

`Use the pack on a real project. The entry-point invariant is closed; further work should come from use, not speculation.`

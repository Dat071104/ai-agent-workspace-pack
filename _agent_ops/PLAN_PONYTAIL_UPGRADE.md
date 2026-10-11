# PLAN -- TASK-0009: Ponytail integration + plan / bug-fix / ops / codegraph upgrade

Status: `executed 2026-10-11 (S4-S8 per Revision; S2/S3 deferred); uncommitted`; originally -- written 2026-10-11 by the coordinator session
(Opus 5.5) at HEAD `714ce2e`. Executed by a later session (Sonnet 5.5 / Haiku 5.5).

## Revision 2026-10-11 (user direction, overrides the sections below)

- The codegraph is considered complete. **S2 (speed) and S3 (`--changed`) are
  dropped** and move to Deferred; only S8 (Java + C#) touches the graph.
- Wherever a slice says `explore.py --changed`, use instead:
  `git diff --name-only` / `git diff -U0` to find touched symbols, then
  `python _agent_ops/tools/explore.py --root . --impact <symbol>` per symbol.
- S8 no longer depends on S3 (no `end` lines needed).
- Usage is unchanged: `@start-here` + a one-line goal; no new mandatory reads.
- Executed by parallel Sonnet/Haiku subagents in isolated worktrees with
  disjoint write sets; the root merges, syncs `_agent_ops/tools/`, edits
  `RUNTIME_TOOLS`, and owns `_agent_ops/`.

## 0. How to execute this plan (read first)

1. Start with `@start-here continue TASK-0009 from _agent_ops/PLAN_PONYTAIL_UPGRADE.md`.
   `session_start.py` reports CONTINUATION; read `_agent_ops/HANDOFF.md`, mark it
   `consumed`, then read this file. Do not reload every team folder.
2. Work on a branch: `git switch -c feat/task-0009-ponytail-upgrade`.
3. **One slice per turn, in the order of section 4.** After each slice: run its
   acceptance commands, update `_agent_ops/CURRENT_TASK.md` (files touched, ruled
   out, next step), append one `IMPLEMENTATION_LOG.md` entry, report, then STOP and
   ask before the next slice. Never run two slices in one writer turn.
4. Model per slice is given in the table. A `Sonnet` slice changes Python and its
   tests; do not hand it to Haiku. `Haiku` slices are Markdown-only with exact specs.
5. Global rules (from `AGENTS.md`, restated because they gate every slice):
   - stdlib only, no new dependency; no file grows past ~400 lines (the ones
     already past it -- `init_project_ops.py`, `session_start.py`, `scan_deps.py`,
     `build_code_index.py`, `explore.py`, `generate_repo_map.py` -- get at most a
     few lines of wiring; new logic goes in a new module named by responsibility);
   - never `git add .`; no commit/push without the user's explicit OK; for an
     authorized commit run `refresh_repo_map.py --stage` after tests;
   - after touching any file in `scripts/` that is in `RUNTIME_TOOLS`, copy it to
     `_agent_ops/tools/` (test `test_this_pack_runs_the_runtime_tools_it_ships`);
   - do not claim a test passed unless it ran; paste the real result line.
6. Test commands used throughout:
   ```bash
   python -B -m unittest discover -s tests -q
   python -B scripts/check_repo_hygiene.py --root .
   ```
   Baseline at `714ce2e`: 40 tests pass (per TASK-0008 log).

## 1. Goal, non-goals, constraints

**Goal.** Make the pack produce big-corp-grade changes -- minimal diff, no
speculative code, fast tooling on large repos -- by (a) vendoring the ponytail
"smallest complete change" discipline into build-team and bug-fix-team,
(b) making advisor/analyze end in one evidence-backed, paste-ready next step,
(c) speeding up and extending the lite codegraph, and (d) making the ops closure
gate deterministic instead of memory-driven.

**Non-goals.**
- No ponytail plugin install, hooks, statusline, env-var level config, gain
  scoreboard or help card (they belong to the plugin, not to an embedded pack).
- No tree-sitter / SQLite / multiprocessing, no Go/Kotlin/Rust parsers.
- No rewrite of existing workflows: edit by insertion, keep every step number
  readers already use where possible.
- No change to embed/update/migrate/bridge behavior (TASK-0006..0008 invariants).

**Constraints.**
- Preserve every string the golden tests assert (grep `assertIn(` before editing
  any template or `AGENTS.md`).
- `source_state.CODE_SUFFIXES` stays the single suffix owner (DEC-0007 consequence).
- Embedded mode must keep working: new team files must be reachable through the
  root `.claude/skills/` pointers, which are generated from the pack's
  `.claude/skills/` (see `adapter_sources()` in `scripts/init_project_ops.py`).

## 2. Evidence baseline (measured 2026-10-11, this session)

| Measurement | Value | How |
| --- | --- | --- |
| Hot context at a managed start | ~66 KB (~16-17k tokens) before any work | `wc -c` on AGENTS.md, START_HERE.md, TEAM_ROUTER.md, commands/start-here.md, SESSION_BRIEF, OPERATING_RULES, CURRENT_TASK, SESSION_PROTOCOL, REPO_MAP |
| Index build, Django (3,044 .py files) | 9.1 s, full rebuild every time | `build_code_index.py` on a depth-1 clone |
| Repo map, Django | 7.3 s -- re-walks and re-resolves every import via `scan_deps.build_graph()` although the index already holds the IMPORTS edges | `generate_repo_map.py` |
| Commit-time `refresh_repo_map.py` | ~16 s on Django-size repo (both of the above) | sum |
| Index size / query | 27 MB JSON; `explore.py --impact` 0.3 s | fine, no action |
| Edge provenance, Django | 95,312 edges: ambiguous 42%, heuristic 40%, exact 17%, weak 1% | index JSON |
| Symbols carry an end line? | No -- only `line` | `build_code_index.py` L171-277 |
| Files walked via | `os.walk` + `SKIP_DIRS`; `.gitignore` not honored | `scan_deps.iter_code_files` |
| Languages in graph | `.py .js .jsx .ts .tsx` only | `source_state.CODE_SUFFIXES` |
| bug-fix-team cost floor | every bug pays 2-4 hypotheses + 2-3 scored directions, even a one-line obvious bug | `bug-fix-team/SKILL.md` steps 6-9 |
| build-team cost floor | 12 steps + contract + slice plan for any size | `build-team/SKILL.md` |
| Closure Receipt | 7 rows, written from model memory, no tool checks it | `SESSION_PROTOCOL.md` |

Upstream ponytail: `https://github.com/dietrichgebert/ponytail`, commit
`9b58c1ffb790c075ca32e70a89cf1d80588f4abf` (2026-10-10), **MIT** (c) 2026
DietrichGebert. Files to read: `skills/ponytail/SKILL.md`,
`skills/ponytail-review/SKILL.md`, `skills/ponytail-audit/SKILL.md` (section 2
"Lean" only), `skills/ponytail-debt/SKILL.md`, `LICENSE`. Clone it into the
session scratchpad (never into this repo):
`git clone https://github.com/dietrichgebert/ponytail <scratchpad>/ponytail && git -C <scratchpad>/ponytail checkout 9b58c1f`.

## 3. Decisions already taken (user, 2026-10-11)

- **DEC-0009** -- add Java and C# to the codegraph as regex extractors whose call
  edges are `weak`; partially supersedes DEC-0007 option B.
- **DEC-0010** -- vendor + adapt ponytail into build-team (bug-fix reuses it),
  default level `full`, MIT attribution; no plugin dependency.
- Plan lives in `_agent_ops/` with a `HANDOFF.md` so a new session picks it up.

## 4. Slice order

| # | Slice | Model | Risk | Depends on |
| --- | --- | --- | --- | --- |
| S1 | Branch + read decisions | Haiku | Light | - |
| S2 | Codegraph speed: git file list, incremental cache, map reuses index | Sonnet | Medium | S1 |
| S3 | `explore.py --changed` (diff -> symbols -> callers -> tests) | Sonnet | Medium | S2 |
| S4 | Ponytail into build-team | Haiku (Sonnet if Haiku drifts) | Light | S3 |
| S5 | bug-fix-team: fast path, failing test first, root-cause-once | Haiku | Light | S4 |
| S6 | advisor + analyze: evidence intake, Next Step Card | Haiku | Light | S4 |
| S7 | Deterministic closure check + compact receipt | Sonnet | Medium | S3 |
| S8 | Java + C# extractors | Sonnet | Medium | S2, S3 |
| S9 | Release verification, embed smoke test, records | Sonnet | Medium | all |

Why this order: S3 must exist before S4-S5 reference `--changed` (otherwise the
docs name a command that does not exist -- the anti-hallucination rule). S2 makes
S3's "rebuild before mapping the diff" cheap. S8 goes late because it touches the
suffix invariant that S2/S3 tests rely on.

---

## S1 -- Branch + read decisions (Haiku)

- `git status --short` must be clean; `git switch -c feat/task-0009-ponytail-upgrade`.
- Read DEC-0009 and DEC-0010 in `_agent_ops/DECISION_LOG.md`.
- Rewrite `CURRENT_TASK.md` Next Concrete Step to S2. No other change.
- Acceptance: branch exists; tree clean except `_agent_ops/`.

## S2 -- Codegraph speed (Sonnet)

**Why.** 16 s per commit hook on a Django-size repo is friction a big-corp dev
will disable; ignored build output (venvs, generated code) bloats the graph.

**2a. File list from git.** `scripts/scan_deps.py::iter_code_files`
- When `root` is inside a git work tree, list with
  `git ls-files -z --cached --others --exclude-standard`, keep entries whose
  suffix is wanted, that exist on disk, and that pass `should_skip_path()` (nested
  pack rule stays). Fall back to the current `os.walk` when git is absent/fails.
- Keep the signature and return type. Untracked-but-not-ignored code must still be
  listed (`test_working_tree_code_makes_index_stale` relies on it).

**2b. Incremental extraction cache.** `scripts/build_code_index.py::build_index`
- Before extracting, verify the per-file extractors are pure per-file (read
  `extract_python(root, path, rel)`: if it reads other files, the cache key must
  include them -- record what you found in CURRENT_TASK).
- Cache file `<ops dir>/code_index.cache.json`:
  `{"extractor_version": N, "files": {rel: {"sha1": <hash of bytes>, "data": <per_file dict>}}}`.
  Re-extract only when the hash or `EXTRACTOR_VERSION` differs; drop vanished
  paths; write compact JSON atomically (temp file + replace).
- Summary/`--quiet` output gains `parsed M, reused N`. Add `--no-cache`.
- The cache is a generated artifact: add `code_index.cache.json` wherever
  `code_index.json` is ignored (`init_project_ops.py` ~L61 and ~L83 ops ignore
  list) and confirm `check_repo_hygiene.py` does not flag it.

**2c. Repo map reuses the index.** `scripts/generate_repo_map.py` (L406 calls
`build_graph(root)`)
- When `code_index.json` exists and its `index_source_fingerprint` equals
  `index_source_fingerprint(root)`, derive the file graph from its `IMPORTS`
  edges; otherwise keep calling `build_graph`. Put the converter in a small
  function; do not duplicate the resolver.

**Tests (add to `tests/test_workspace_tools.py`, or a new
`tests/test_codegraph_speed.py` -- the existing file is 1,225 lines, so prefer the
new file and reuse its fixture helpers by import).**
- second build after editing one file reports `parsed 1`;
- bumping `EXTRACTOR_VERSION` re-parses everything;
- an ignored directory (`.gitignore`) containing `.py` is not indexed;
- repo map Modules + Hot Files sections are identical via index path and
  `build_graph` path on the same fixture.

**Acceptance.** All tests pass. Re-run the Django benchmark (clone depth 1 into
scratchpad): warm rebuild after touching one file < 3 s (baseline 9.1 s);
`refresh_repo_map.py`-equivalent (index + map) < 5 s (baseline ~16 s). Record the
numbers in IMPLEMENTATION_LOG. If a target is missed, report the real number --
do not tune the benchmark.

## S3 -- `explore.py --changed` (Sonnet)

**Why.** Every downstream rule ("grep every caller before you fix", "self-review
your diff", "which tests to run") needs diff -> symbols -> callers. Today the
agent greps by hand, which is what ponytail-review does and what this graph exists
to replace.

**3a. End lines.** Add `end` to every symbol: Python `node.end_lineno`; JS (and
later Java/C#) = next symbol's start - 1 in the same file, else EOF -- mark the
approximation in the module docstring. Bump the index `"version"` to 2 and
`EXTRACTOR_VERSION`. `explore.py` keeps loading a v1 index for the other
commands; `--changed` on v1 says "rebuild the index" and exits 1.

**3b. New module `scripts/explore_changed.py`** (boundary: "map a git diff onto
the symbol graph"; `explore.py` is already 427 lines, so it only gets the flag and
a dispatch line, importing the new module lazily inside `main()` to avoid a cycle).
- `changed_ranges(root, base)` -- parse `git diff -U0 --no-color <base>` (default
  base `HEAD`: staged + unstaged vs HEAD; `--base origin/main` for a branch);
  `@@ -a,b +c,d @@` gives new-side ranges; a pure deletion maps to line `c`.
- If the index is stale for the working tree (reuse the staleness check
  `session_start.py` already uses -- do not write a second one), rebuild it first
  through `build_code_index.build_index` + the S2 cache, then map ranges.
- Output, capped like the other renderers (`MAX_LIST`):
  1. **Changed symbols** -- `kind name  file:start-end`;
  2. **Callers to re-check** -- reuse the impact traversal (depth default 2),
     grouped by worst edge confidence, `ambiguous`/`weak` labelled "verify";
  3. **Tests to run** -- reuse `TEST_HINTS` logic from `render_impact`;
  4. **Changed files with no indexed symbol** (config, SQL, templates) -- listed
     so the reviewer still opens them;
  5. **Removed definitions** -- names matched by `def|class|function` on removed
     lines, with `git grep -n <name>` as the follow-up (the index no longer has them).
- Footer: "minimum blast radius; dynamic dispatch/DI/reflection are invisible".
- Add `explore_changed.py` to `RUNTIME_TOOLS` in `init_project_ops.py`; copy to
  `_agent_ops/tools/`.

**Tests.** Fixture repo with a function + caller + test file: edit the function
body -> `--changed` lists the function, the caller, and the test; delete a
function -> listed under Removed; edit a `.json` -> listed under no-symbol files;
`--base` with a commit range works.

**Acceptance.** Tests pass; `python scripts/explore.py --root . --changed` on this
repo prints sane output for the S3 diff itself (paste it in the log).

## S4 -- Ponytail into build-team (Haiku; docs only)

**New files**
1. `build-team/PONYTAIL_RULES.md` (target <= 90 lines). Header:
   "Adapted from ponytail (MIT, (c) 2026 DietrichGebert), upstream commit 9b58c1f.
   See THIRD_PARTY_NOTICES.md." Content, adapted from `skills/ponytail/SKILL.md`:
   - *Before you write* -> scope list: callers, tests, fixtures, config, exports,
     data that could be destroyed or exposed. Tell the agent to get callers from
     `explore.py --impact <symbol>` instead of grepping.
   - *The smallest complete change* ladder, rungs 1-6, verbatim in meaning.
   - The bullet rules (lazy about the solution, never about the change; no
     speculative abstraction/config/wrapper; deletion beats addition; keep the
     codebase's structure; shortest working diff once scope is known; comment only
     the why; bug fix = fix root cause once in shared code; moved code keeps its
     validation; equal size -> pick the edge-case-correct one; non-trivial logic
     leaves one test or assert self-check).
   - `shortcut: <the limit>, <when to upgrade>` comment convention, and the debt
     ledger command (from ponytail-debt):
     `git grep -nE '(#|//|/[*]) ?(shortcut|ponytail):'` -- a marker with no
     upgrade trigger is tagged `no-trigger`.
   - *Never cut* list, verbatim in meaning.
   - Levels table `lite | full | ultra`, **default `full`**; the user selects
     another level per task by writing "ponytail lite" or "ponytail ultra" in the
     request. No env var, no config file, no "stop ponytail" session toggle.
   - **Diff hygiene (pack addition, label it as such):** do not reformat,
     re-order imports, or rename on lines the change does not need; follow the
     repo's formatter/linter config rather than personal style; one concern per
     diff; report `git diff --shortstat` with every slice.
   - Reply ending: one or two lines -- what was skipped or not checked, and any
     risk the user must know.
2. `build-team/SELF_REVIEW_CHECKLIST.md` (target <= 80 lines), adapted from
   `skills/ponytail-review/SKILL.md` sections 2-4: input is
   `explore.py --changed` + `git diff`; order correct, safe, holds under load,
   tested, fast, lean; "no concrete case, no finding"; `shortcut:` markers are
   decisions, not findings; output groups Must fix / Should fix / Nice to have,
   numbered, each finding with What this is / Problem / Fix / If we skip it;
   `Verdict:` and `Lean: -N lines possible.`
3. `THIRD_PARTY_NOTICES.md` at the repo root: name, URL, commit, and the full MIT
   license text copied from upstream `LICENSE`, plus which pack files are derived.

**Edits to `build-team/SKILL.md`** (insert; keep the file <= ~150 lines; reference
the new files instead of pasting their content):
- Step 1: add **size the change** with the S/M/L vocabulary from
  `advisor-team/EFFORT_COMPLEXITY_RUBRIC.md`. **S** = one file, no new public
  interface, no business rule: skip FEATURE_CONTRACT/SLICE_PLAN and give a
  5-line inline plan (goal, file, ladder rung, test, risk) plus one confirmation.
  M/L keep the current flow.
- Step 4 becomes "Reuse scan + smallest complete change": apply
  `PONYTAIL_RULES.md`, state the rung chosen and what was skipped by design.
- Step 6: add the ponytail scope list to the impact statement.
- New step between 9 and 10: **Self-review** -- run
  `python _agent_ops/tools/explore.py --root . --changed`, apply
  `SELF_REVIEW_CHECKLIST.md`, fix every Must-fix before reporting.
- Step 11: report adds `git diff --shortstat`, rung, self-review verdict, and the
  ponytail reply ending.
- Expected Output Contract + Correctness Guards: add "Lean guard: no code nobody
  asked for; every `shortcut:` names its ceiling and trigger."
- Renumber carefully; grep other files for "build-team ... step N" references.

**Template edits.** `FEATURE_CONTRACT_TEMPLATE.md`: new section *Smallest
Complete Change* (rung chosen 1-6, skipped by design, shortcuts with ceiling).
`SLICE_PLAN_TEMPLATE.md`: column `Diff budget (+/-)`; per-slice report lines
`Diff: <shortstat>` and `Self-review verdict:`.

**Adapters.** `.claude/skills/build-team/SKILL.md` References line: add the two
new files and the `--changed` command. `.claude/agents/bug_fixer.md` and
`.codex/agents/bug_fixer.toml`: one line "Apply build-team/PONYTAIL_RULES.md at
level full; end with what was skipped and any risk." `build-team/README.md`: one line.

**Acceptance.** Every command named in the new docs exists (`--changed`, the
grep); no file > 400 lines; `grep -n "PONYTAIL_RULES" -r .` shows SKILL.md,
adapter, bug_fixer pointers; tests + hygiene pass.

## S5 -- bug-fix-team (Haiku; docs only)

Edits to `bug-fix-team/SKILL.md`:
- Step 3: **reproduce as a failing test first** when the repo has a harness; the
  test is both the evidence and the regression guard. Otherwise record the exact
  repro command.
- New step after classification: **triage size**.
  - *Obvious* -- reproduced, one cause at one site, evidence on `exact` edges:
    fast path = one hypothesis, one fix direction, no templates, still confirm
    before editing.
  - *Medium* -- current steps 6-10.
  - *Hard/ambiguous* -- current parallel `bug_hunter` offer.
  State which path was used and why in the output.
- Fix step: "list every caller with `explore.py --impact`, then fix the root cause
  once in the shared code; never patch one caller while the shared function stays
  broken" + apply `build-team/PONYTAIL_RULES.md` (level full) + `shortcut:` comment
  when the fix has a known ceiling.
- Test step: failing test now passes; run the tests `explore.py --changed` lists;
  run `build-team/SELF_REVIEW_CHECKLIST.md` limited to Bug / Risk / Scale /
  Missing test.
- Step 15 wording conflict: "In a managed session, append the implementation log
  (ops writes are already authorized); outside one, ask first."
- Align the frontmatter `description` with `.claude/skills/bug-fix-team/SKILL.md`
  (the adapter mentions parallel `bug_hunter`; the source does not).
- Output contract adds: path used (Obvious/Medium/Hard), failing-test evidence,
  `git diff --shortstat`.

Acceptance: file stays <= ~160 lines; tests + hygiene pass.

## S6 -- advisor + analyze (Haiku; docs only)

**New `advisor-team/NEXT_STEP_CARD_TEMPLATE.md`** (shared by both teams):

```text
Next Step Card
- Do:            <one action, one sentence>
- Why now:       <value, with the evidence reference>
- Team / mode:   <team> / <solo | sequential | parallel>
- Paste to start: <exact invocation for this harness>
- Done when:     <observable check or command>
- Size / token:  <S|M|L|XL> / <Light|Medium|Heavy|Very Heavy>
- Stop and ask if: <condition that changes scope or risk>
- Not now:       <top deferred item + reason>
```

**`advisor-team/SKILL.md`**
- Replace *Context Intake* with **Evidence intake, deterministic first**:
  `session_start.py` output; REPO_MAP Hot Files + Oversized Files;
  `explore.py --entrypoints`; the `shortcut:` debt ledger grep (count, and
  `no-trigger` markers); open rows in `RISK_REGISTER.md`; Remaining Risks + Next
  Step of the last 3 `IMPLEMENTATION_LOG.md` entries (or `LOG_SUMMARY.md`);
  CURRENT_TASK Ruled Out. Every opportunity cites evidence (path:line, log entry,
  measurement) or is marked `needs data`.
- Add a **Lean lens** (from ponytail-audit "Lean"): delete / reuse / stdlib /
  yagni / merge / split, sized as negative lines.
- Workflow step 5: rank by value / effort discounted by confidence; tag horizon
  Now / Next / Later.
- Output ends with exactly **one Next Step Card** plus at most two one-line
  alternates.
- `OPPORTUNITY_REGISTER_TEMPLATE.md`: add columns Evidence, Confidence, Horizon.

**`analyze-team/SKILL.md`**
- Chat-first list: before options, state **decision criteria with weights**.
- Options must include **Option 0: do nothing / smallest version** (ponytail rung 1).
- Per option add **reversibility** (two-way / one-way door), a one-line
  **pre-mortem** ("this fails when ..."), and the cost to verify it.
- Output adds **Handoff to build-team**: prefilled Feature Contract fields
  (feature, out of scope, rules known vs unknown, owning module from REPO_MAP,
  first slice), then the Next Step Card.
- `OPTIONS_DEBATE_TEMPLATE.md`: criteria/weights table on top; columns
  Reversibility, Pre-mortem, Size.

Adapters: update References lines in `.claude/skills/advisor-team/SKILL.md` and
`.claude/skills/analyze-team/SKILL.md`. Acceptance: tests + hygiene pass; both
SKILL files stay <= ~100 lines.

## S7 -- Deterministic closure check + compact receipt (Sonnet)

**Why.** The receipt is the most-skipped step for smaller models; the pack's own
philosophy is "deterministic checks come from scripts, not model memory".

- New `scripts/closure_check.py` (read-only, <= ~150 lines; reuse
  `source_state.code_change_sets` / `resolve_ops_dir` and session_start's section
  parsing by import -- do not copy them).
  - Inputs: `--root`, optional `--since <sha>` (default: SESSION_BRIEF
    `Last Verified Commit`), `--strict`.
  - Detects: project code changed since `<sha>` (committed + working tree);
    which `_agent_ops/*.md` changed (working tree vs HEAD and since `<sha>`).
  - Prints a Closure Receipt draft: changed ops file -> `updated (detected)`;
    triggered but untouched -> `MISSING: <trigger> but <file> untouched` (e.g. code
    changed, IMPLEMENTATION_LOG.md untouched; code changed, REPO_MAP.md stale);
    everything else -> `decide: not needed (<missing trigger>)` for the model to fill.
  - Exit 0; with `--strict` exit 2 when any MISSING row exists.
  - Add to `RUNTIME_TOOLS`; copy to `_agent_ops/tools/`.
- `core-context/SESSION_PROTOCOL.template.md` and `_agent_ops/SESSION_PROTOCOL.md`:
  "run `closure_check.py` before printing the receipt"; allow the **compact
  form**: updated rows one per line; not-needed rows may share one line when they
  share the same missing trigger, e.g.
  `- DECISION_LOG, RISK_REGISTER, PROJECT_CONTEXT_CARD: not needed (no trade-off, no new risk, no milestone)`.
  Every ops file must still appear by name. Keep every asserted string intact.
- Mirror the one-line instruction in `commands/start-here.md` step 11 and
  `commands/work.md` step 8.
- Tests: code change + untouched log -> MISSING row; log updated -> updated row;
  `--strict` exit code.

## S8 -- Java + C# extractors (Sonnet)

- `source_state.CODE_SUFFIXES` += `.java`, `.cs` (single owner; the suffix
  equality test must still pass). `scan_deps.SKIP_DIRS` += `obj`, `.gradle` only
  (`bin`/`out` are ambiguous in other stacks; S2's git listing already drops
  ignored build output).
- New module `scripts/extract_java_csharp.py`: `extract_java(path, rel)` and
  `extract_csharp(path, rel)` returning the same per-file shape as `extract_js`
  (`symbols` with `line` and `end`, `imports`, `raw_calls`).
  - Symbols: class / interface / enum / record; methods = modifier list + return
    type + `name(`; drop keywords (`if for while switch catch return new throw
    using lock`) from methods and calls.
  - Routes: Spring `@(Get|Post|Put|Delete|Patch|Request)Mapping("...")`
    (also `value=`/`path=`); ASP.NET `[Http(Get|Post|Put|Delete|Patch)("...")]`,
    `[Route("...")]`. Bases: `extends X implements Y`; `: Base, IFoo`.
  - Java imports: derive the source root from the file's own `package` line,
    resolve `import a.b.C;` to `<source root>/a/b/C.java`; exists -> `heuristic`.
    Skip static and wildcard imports. C# `using` names namespaces, not files ->
    no IMPORTS edges; say so in Limits.
- `build_code_index.py`: dispatch by suffix to the new extractors; `lang` =
  `java` / `csharp`; CALLS for every non-Python language stay `weak`
  (`weak = data["lang"] != "python"`). `scan_deps.resolve_import`: delegate
  `.java` to the new resolver (wiring only).
- `generate_repo_map.py`: entry points also by `Program.cs`, `*Application.java`,
  `*Controller.java|.cs`; update the Limits text. README: update the language
  boundary paragraph. Add a consequence note under DEC-0007 pointing to DEC-0009.
- Tests: Java fixture (controller -> service, import resolution, Spring route) and
  C# fixture (controller, `[HttpGet]` route, method call) -> `--symbol`,
  `--impact`, `--entrypoints`, `--changed` behave; Java/C# edges never `exact`.
- Optional smoke: depth-1 clone of `spring-projects/spring-petclinic` and
  `dotnet-architecture/eShopOnWeb` into scratchpad -> index builds, report counts.

## S9 -- Release verification (Sonnet)

1. Sync `_agent_ops/tools/` from `scripts/` for every `RUNTIME_TOOLS` entry.
2. Full tests + hygiene; confirm REPO_MAP Oversized Files did not gain a file.
3. Embed smoke: make a tiny git project in scratchpad with one Python file and
   one test, `python scripts/embed_pack.py --target <it>`, then from it run
   `session_start.py`, `explore.py --changed`, `closure_check.py`; confirm
   `.claude/skills/build-team` pointer lists PONYTAIL_RULES and the checklist.
4. One line each in `README.md` (what's new + language boundary), `TEAM_ROUTER.md`
   build/bug-fix rows ("ponytail full by default"), `START_HERE.md` if it lists
   team capabilities.
5. Records: IMPLEMENTATION_LOG (one entry per slice is already done; add the
   release entry), PROJECT_CONTEXT_CARD milestone, RISK_REGISTER (see section 6),
   SESSION_BRIEF state + Last Verified Commit, CURRENT_TASK reset, Closure Receipt
   (generated by `closure_check.py`).
6. Ask the user before commit. If authorized: stage explicit files, run
   `python scripts/refresh_repo_map.py --root . --stage`, commit without
   `--no-verify`. Push only on a separate explicit OK.

## 5. Deferred (with reason)

| Item | Why not now |
| --- | --- |
| Slim `AGENTS.md` (13.9 KB) and the duplicated start-here text | Biggest token win (~25-30% of the 66 KB hot context) but many strings are asserted by golden tests and copied into generated bridges. Separate task after S7, with a before/after byte table. |
| ponytail-gain, ponytail-help, hooks, statusline, env config | Plugin features; no value inside an embedded pack. |
| ponytail-audit as a command | tester-team owns audits. Optional follow-up: add its "Lean" category to `harness/AUDIT_CHECKLIST.md` (~6 lines). |
| Reduce `ambiguous` edges (42% on Django) | Needs receiver-type inference; a separate design question. |
| Multiprocessing / SQLite / tree-sitter | S2 cache should remove most of the cost; measure first. |
| Go / Kotlin | Not requested; same pattern as S8 if needed. |

## 6. Risks to record

- **Vendored-rule drift:** ponytail upstream changes; pin is commit 9b58c1f.
  Re-sync is a manual decision, recorded in THIRD_PARTY_NOTICES.md.
- **Regex extractors (Java/C#) mis-attribute calls** -- mitigated by `weak` on
  every call edge and the existing "verify weak/ambiguous" rule.
- **Cache staleness bug** would silently serve old symbols -- mitigated by content
  hash keys, `EXTRACTOR_VERSION`, `--no-cache`, and the parsed/reused counter.
- **`--changed` line drift** when the index predates the working tree --
  mitigated by rebuild-if-stale before mapping.
- **Over-minimal changes** (ponytail cutting what was needed) -- mitigated by the
  vendored "never cut" list and "lazy about the solution, never about the change".

## 7. Definition of done

- S1-S9 each logged with real test output; all tests + hygiene pass.
- Django benchmark numbers recorded (target: warm rebuild < 3 s, index + map < 5 s).
- build-team and bug-fix-team apply ponytail `full` by default and end with
  skipped/risk lines; advisor/analyze end with one Next Step Card.
- `closure_check.py` produces the receipt draft in an embedded install.
- No commit or push happened without the user's explicit OK.

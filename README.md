# AI Agent Workspace Pack

A drop-in operating kit that gives coding agents — Claude Code, Codex, Cursor,
Gemini, Windsurf — **memory, a code map, and safe defaults** in any repository.

No dependencies. No cloud. Python standard library only. Everything stays local.

> **Tiếng Việt:** Đây là bộ công cụ dùng lại cho mọi dự án code với AI agent.
> Bạn có thể mô tả bằng tiếng Việt bình thường — agent sẽ trả lời tiếng Việt,
> hỏi lại khi thiếu thông tin, và luôn xin xác nhận trước khi sửa file.

> **Embedded pack một thư mục:** dùng `scripts/embed_pack.py` để copy sạch pack
> vào repo (không clone, không mang `_agent_ops` của source). Root `AGENTS.md`
> sẽ bắt đầu bằng link tới pack và giữ nguyên host instructions.

---

## The problem this solves

Drop an agent into a real repository and this happens every session:

```
You:   Login returns 500 when the token refreshes.
Agent: grep "refresh" → 200 hits
       read authController.ts
       grep tokenService
       read tokenService.ts
       read userRepository.ts
       ... 20 tool calls later, still looking
```

The agent is **rediscovering the same repository topology every single time**,
then forgetting it when the session ends.

This pack fixes three things:

| Problem | Fix |
| --- | --- |
| Agent re-explores the repo every session | A pre-built **code graph** it can query |
| Agent forgets what it already tried | **Task memory** that survives context compaction |
| Agent's notes die with the session | **Handoff** the next session picks up by itself |

---

## Install

```bash
# 1. Clone this pack anywhere -- it does not need to live inside your project
git clone https://github.com/Dat071104/ai-agent-workspace-pack.git
cd ai-agent-workspace-pack

# 2. Install into your project (one time, per repo)
python scripts/init_project_ops.py --target "D:\MyProject"

# 3. From then on, work from your project. The pack is no longer needed.
cd "D:\MyProject"
python _agent_ops/tools/session_start.py --root .
```

Step 2 puts four things in your project:

| What | Where | Why |
| --- | --- | --- |
| Memory files | `_agent_ops/*.md` | Brief, task state, decisions, risks, log |
| Code graph | `_agent_ops/REPO_MAP.md` + `code_index.json` | Locate code without grepping |
| The tools themselves | `_agent_ops/tools/` | So the project runs on its own |
| Agent instructions | `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` at your project root | Codex/Cursor/Windsurf auto-load `AGENTS.md`; Claude Code and Gemini CLI don't -- `CLAUDE.md`/`GEMINI.md` are thin adapters that `@`-import it |

`AGENTS.md` is the single canonical entry point. The generated `CLAUDE.md` and
`GEMINI.md` adapters import it first, so a rule you write there is in context
whichever of those tools the session runs under. A `CLAUDE.md` or `GEMINI.md`
your project already had is host-owned: it is preserved untouched, and the
installer warns rather than editing it if it does not import `AGENTS.md`.

It never replaces host-owned instruction content. `CLAUDE.md` and `GEMINI.md`
are written only if your project does not already have one. An existing
`AGENTS.md` keeps every line you wrote; the only thing the installer may add or
refresh there is the marked workspace-pack bridge block.

### Namespaced embedded pack: one copied folder

When the full pack should travel with a project, materialize a clean directory
(not a Git clone or submodule) from a local source-pack checkout:

```bash
python D:\path\to\ai-agent-workspace-pack\scripts\embed_pack.py --target .
```

This creates `ai-agent-workspace-pack/`, excluding the source `.git/` and its
project-specific `_agent_ops/`, then creates fresh project state inside the new
folder. It keeps team instructions, scripts, templates, phase cards, and the
project `_agent_ops/` state under that one folder. The only root-level integration files
are the lightweight harness entry points.

#### One canonical entry point, three harnesses

Your `AGENTS.md` stays the root of the tree. The installer prepends a managed
block to it -- plain text between `AI_AGENT_WORKSPACE_PACK` markers -- naming
where the pack is and what to read for `@start-here`. Every line you already
wrote follows it unchanged.

```text
your-project/
  AGENTS.md          <- your rules + the managed pack block   (Codex reads this)
  CLAUDE.md          <- @AGENTS.md, then @ai-agent-workspace-pack/AGENTS.md
  GEMINI.md          <- @./AGENTS.md, then @./ai-agent-workspace-pack/AGENTS.md
  ai-agent-workspace-pack/
```

Two properties are load-bearing, and earlier revisions of this pack got both
wrong:

- **The block is prose, not an `@import`.** Claude Code and Gemini CLI expand
  `@path` inside their own memory files. Codex concatenates `AGENTS.md` and
  resolves nothing, so a bare `@ai-agent-workspace-pack/AGENTS.md` line reached
  it as decoration -- the model might open that path, or might not. Prose is a
  contract; a link only some harnesses follow is not.
- **`CLAUDE.md` and `GEMINI.md` import your `AGENTS.md` first.** They used to
  import the pack directly, which meant a project whose real governance lived in
  its own `AGENTS.md` had those rules on disk and absent from the model's
  context. Host rules now reach every harness before any pack workflow does.

An install made before this change is upgraded in place the next time the
installer runs: the old link line is removed, the managed block replaces it, and
your own text is preserved.

#### Updating an installed pack

A copied pack has no upstream to pull from, so a fix made in the source pack
stays live in every project that copied an earlier revision. Refresh one with:

```bash
python D:\path\to\ai-agent-workspace-pack\scripts\embed_pack.py --target . --update
```

That overwrites pack content, removes files the current revision no longer
ships, and **never touches `_agent_ops/`** -- your project memory, logs and
decisions survive. It refuses on a dirty worktree, or outside Git, unless you
pass `--allow-dirty`, so the change is always reviewable as a diff.

Every install writes `<folder>/PACK_VERSION` recording the source revision and
install date, and an update records the revision it replaced. `session_start.py`
prints that version each session, so a project can always say which pack it is
running -- and says so explicitly when the stamp is missing.

#### Migrating an older flat install

A pack unpacked directly into an application root can be moved into the
namespaced layout without losing project memory:

```bash
python D:\path\to\ai-agent-workspace-pack\scripts\migrate_pack.py --target .
```

That prints the plan and changes nothing. Add `--apply` to perform it. Nothing
is deleted: every pack file is *moved*, so `git status` shows renames and
`git checkout` reverts the whole thing. `--apply` refuses on a dirty worktree,
or outside Git, unless you pass `--allow-dirty`.

Files are matched by their path inside the source pack, never by directory name.
A flat install merged the pack's `scripts/*.py` into the application's own
`scripts/`, so moving that directory wholesale would carry application code with
it. `LICENSE`, `.gitignore`, and `README.md` are never moved -- at the root they
are as likely to be the application's as the pack's, so review those three by
hand. `_agent_ops/` moves into the pack folder with its history intact;
`REPO_MAP.md` and `code_index.json` are rebuilt, because they described the old
layout.

#### Root harness adapters

Codex discovers subagents in `.codex/agents/` at the repository root, and Claude
Code discovers `.claude/agents/` and `.claude/skills/` there. Neither looks
inside a subdirectory, so the install also writes those pointer files at the
root: four subagents (`tester`, `bug_hunter`, `bug_fixer`,
`repo_hygiene_reviewer`) for both harnesses, plus the nine team skills for
Claude Code. Each pointer carries an `AI_AGENT_WORKSPACE_PACK:ADAPTER` marker
and resolves every path into the pack folder.

That marker is the ownership rule: a re-run updates a marked file and never
touches a same-named host file, which is reported as
`SKIP host-owned adapter`. Workflow content is never duplicated at the root --
the pointers name the team files inside the pack folder. Skip them with
`--no-root-adapters`, at the cost of losing subagent and skill discovery.

Check the bridge without writing:

```bash
python ai-agent-workspace-pack/scripts/init_project_ops.py --target . --embedded-folder ai-agent-workspace-pack --check-agents-bridge
```

### Existing flat `AGENTS.md`: install a managed bridge explicitly

An embedded pack beside an existing `AGENTS.md` is not automatically discoverable:
the host instructions remain the entry point. Preserve those instructions, then
install the small pack-owned bridge once:

```bash
python scripts/init_project_ops.py --target "D:\MyProject" --install-agents-bridge
```

The bridge is idempotent and changes only the text between its managed markers.
It routes `@start-here` to `START_HERE.md` and `TEAM_ROUTER.md`, while keeping
host rules in force and limiting the pack's automatic writes to `_agent_ops/`.
Check it without writing anything:

```bash
python scripts/init_project_ops.py --target "D:\MyProject" --check-agents-bridge
```

The check reports `INSTALLED`, `MISSING`, `OUTDATED`, or `CORRUPT`; only
structural marker problems block installation. It does not attempt to infer
policy conflicts from natural-language project rules.

**The tools are copied on purpose.** Cloning the pack "next to" a project used
to leave that project unable to run anything: `python scripts/session_start.py`
only works from inside the pack. Now every command runs from your project root,
and a teammate who clones your project gets working tooling without ever hearing
about this pack. Re-run step 2 any time to refresh the copies (`_agent_ops/tools/`
is always overwritten; your memory files are not).

### Choose one installation mode

- **Namespaced embedded pack (recommended):** run `embed_pack.py` from a local
  source pack to create `ai-agent-workspace-pack/`. The pack and its
  `_agent_ops/` state stay contained; root `AGENTS.md` gains only a marked
  bridge block and keeps every host instruction around it. The pack folder is
  one directory directly under the project root -- nested deeper it is no
  longer recognized as a pack, and its own files get indexed as your code.
- **Flat embedded pack (legacy compatibility):** copy this whole pack into the
  project root before initialization. `AGENTS.md`, `START_HERE.md`,
  `TEAM_ROUTER.md`, and the team folders stay available, but this can collide
  with host paths such as `scripts/`, `.codex/`, and `.claude/`.
- **Runtime-only:** keep the pack elsewhere and run step 2 above. The target
  gets `_agent_ops/` and its tools, but no team folders; its generated
  `AGENTS.md` says so rather than pretending named-team routing is available.

Do not mix the descriptions: embedded mode is the complete operating kit;
runtime-only mode is the self-contained tooling and memory layer.

---

## Daily use: one command

```text
@start-here I want to <your goal in one line>
```

That is the whole interface. The agent then:

1. runs read-only checks (git state, stale memory, unfinished work)
2. picks up a handoff automatically if a previous session left one
3. routes you to the right team and says why
4. warns you if the work is expensive
5. asks **at most one** question
6. waits for your OK before touching any file

You never need to remember a second command. Just talk normally after that.

---

## "I want to..." → what to type

| I want to | Type this | Team |
| --- | --- | --- |
| Not sure what I need | `@start-here <goal>` | auto-router |
| Know what to improve next | `@start-here what should I improve?` | `advisor-team` |
| Compare approaches before building | `@start-here compare 3 ways to do X` | `analyze-team` |
| **Build a new feature** | `@start-here add feature X` | `build-team` |
| **Fix a bug** | `@start-here bug: login returns 500` | `bug-fix-team` |
| Test / audit my project | `@start-here audit this before release` | `tester-team` |
| Clean up messy code | `@start-here my repo is messy` | `clean-code-team` |
| Check it is safe to make public | `@start-here release check` | `repo-hygiene-team` |
| Stop for today, continue later | `@start-here wrap up this session` | `handoff-team` |
| Write a prompt for another agent | `@start-here make me a phase prompt` | `prompting-team` |
| Just chat, change nothing | `@start-here --no-ops <question>` | router only |

**Non-technical?** Write plainly: *"I want an app to track my expenses, I do not
know what to use."* The agent gives A/B/C options, recommends one, explains the
cost, and never edits anything without asking.

---

## The code graph (the big one)

Instead of grepping, the agent **queries a pre-built map of your code**.

```bash
python _agent_ops/tools/build_code_index.py --root .    # build once, rebuild when code changes
```

Then:

```bash
python _agent_ops/tools/explore.py --symbol charge          # who calls it, what it calls
python _agent_ops/tools/explore.py --path checkout charge   # how control actually gets there
python _agent_ops/tools/explore.py --impact getUser         # what breaks + which tests to run
python _agent_ops/tools/explore.py --entrypoints            # all routes, and unused-looking code
python _agent_ops/tools/explore.py --file src/auth.py       # what is inside, who imports it
```

### Why this matters

Take a real bug: *"payment sometimes charges twice."*

Grep for `"charged twice"` finds nothing. Grep for `charge` finds the function
but not the reason. The graph shows the **path**:

```
POST /checkout
  → RetryMiddleware.handle     ← the actual bug lives here
    → PaymentService.process
      → StripeGateway.charge   ← where the symptom appears
```

The middleware never appears in a search for the symptom, but it is right there
on the call path. **Where a bug shows up is rarely where it lives.**

### Every relationship tells you how sure it is

| Tag | Meaning | Trust it? |
| --- | --- | --- |
| `exact` | Resolved through real imports/scope | Yes |
| `heuristic` | Name is unique in the repo, so inferred | Probably |
| `ambiguous` | Several functions share this name | **Open the file and check** |
| `weak` | Regex-extracted JS/TS | **Verify before relying on it** |

This is deliberate. A static analyzer **cannot** see dynamic dispatch, DI
wiring, reflection, or runtime registries. So:

- `--impact` gives the **minimum** blast radius, never the maximum
- "nothing calls this" is a **candidate** for dead code, never a verdict

Python is parsed with a real AST parser and is accurate. JS/TS uses regex
(no JS parser ships with Python) and is always marked `weak`.

**Language support is not uniform across the pack.** Memory, the session
protocol, the hygiene checks and the git safety rules are language-agnostic and
work in any repository. The code graph -- `REPO_MAP.md`, `code_index.json` and
`explore.py` -- indexes **Python and JS/TS only**. In a Go or Rust repository
everything else still works; you simply get no symbol graph, and the tools will
not claim one is stale.

---

## Project memory: `_agent_ops/`

Three layers, each with a different lifetime:

| Layer | File | Holds | Lifetime |
| --- | --- | --- | --- |
| **Code** | `REPO_MAP.md` | Modules, routes, most-called symbols | Rebuild when files move |
| **Task** | `CURRENT_TASK.md` | Files touched, **dead ends**, next step | Overwritten each task |
| **Project** | `PROJECT_CONTEXT_CARD.md`, `DECISION_LOG.md`, `RISK_REGISTER.md` | Durable facts and decisions | Grows with the project |

`CURRENT_TASK.md` is the one that matters most. Its **"Ruled Out / Already
Tried"** section is what stops an agent from re-testing a hypothesis it already
disproved after its context gets compacted.

The task prompt controls what the agent is asked to deliver; it does not waive
durable project memory. Real implementation, test, audit, gate, or verification
evidence belongs in the implementation log even if the prompt never names that
file. A durable phase/milestone result belongs on the project context card, and
a material trade-off belongs in the decision log.

### What gets committed, and what does not

`init_project_ops.py` writes an `_agent_ops/.gitignore` for you:

| Committed (survives a clone) | Local only |
| --- | --- |
| `REPO_MAP.md`, `IMPLEMENTATION_LOG.md`, `archive/`, `HANDOFF.md`, `PROJECT_CONTEXT_CARD.md`, `DECISION_LOG.md`, `RISK_REGISTER.md`, `PHASE_ROADMAP.md`, `OPERATING_RULES.md`, `SESSION_PROTOCOL.md`, `INDEX.md` | `SESSION_BRIEF.md`, `CURRENT_TASK.md`, `LOG_SUMMARY.md`, `code_index.json` |

Project history is shared; per-machine scratch and rebuildable artifacts are not.

> On a **public** repo the committed files are public. Keep secrets, customer
> names, and internal URLs out of the implementation log and handoff.
> `python _agent_ops/tools/check_repo_hygiene.py --root .` fails if a local-only file
> gets tracked by mistake.

### Source commits keep the map current

For an authorized commit containing project-code changes, stage the intended
source files after tests, then run the repo-map refresh helper with --stage.
It rebuilds the ignored code index and tracked Repo Map once, stages only the
map, and refuses to proceed when unstaged or untracked code would make the map
describe a different state than the commit. A project can opt in to the managed
pre-commit hook during initialization to enforce this map-refresh gate.

### The log never gets huge

An append-only log becomes a context problem of its own. So it rotates:

```bash
python _agent_ops/tools/summarize_implementation_log.py --log _agent_ops/IMPLEMENTATION_LOG.md \
    --rotate --keep 10 --output _agent_ops/LOG_SUMMARY.md --force
```

- `LOG_SUMMARY.md` — what the agent reads first
- `IMPLEMENTATION_LOG.md` — newest 10 entries
- `archive/` — everything older

The archive is written and verified **before** the log is rewritten, so nothing
can be lost. Rotation is a move, never a delete. The session-start check tells
you when it is time.

---

## Stopping and continuing later

End of session:

```text
@start-here wrap up this session
```

`handoff-team` writes `_agent_ops/HANDOFF.md` — which **is committed**, so it
travels with the repo.

Next session, on any machine, in any agent:

```text
@start-here
```

The agent sees the handoff by itself and says:

```
## Session Continuity
- CONTINUATION. A previous session left a handoff.
- READ _agent_ops/HANDOFF.md FIRST, before routing or touching code.
```

You do not have to explain that this is a continuation, and you do not paste
anything. The handoff carries the dead ends and open questions forward.

Four verdicts: `CONTINUATION` · `TASK IN PROGRESS` · `SESSION ESTABLISHED` · `FRESH`.

---

## The nine teams

Each team is one file the agent loads **only when needed** — that is how context
stays small.

| Team | Use it for | Writes code? |
| --- | --- | --- |
| `advisor-team` | What to improve next, priorities, ROI | No |
| `analyze-team` | Ideas, architecture options, roadmap | No |
| `build-team` | **Implementing new features** | Yes |
| `bug-fix-team` | Verify a bug, then fix it minimally | Yes |
| `tester-team` | Audits, QA, production readiness | No |
| `clean-code-team` | Refactoring and cleanup (high risk) | Yes |
| `repo-hygiene-team` | Git safety, public-repo readiness | No |
| `handoff-team` | Session handoff, final reports | No |
| `prompting-team` | Prompts for other agents | No |

Two teams have safety gates worth knowing about:

- **`build-team`** stops and asks if your acceptance criteria are missing.
  Code that compiles but encodes a *guessed* business rule is the most expensive
  kind of wrong — it passes review and fails in production.
- **`clean-code-team`** requires a clean git state and a recovery branch, works
  one batch at a time, and tests after each.

---

## Scripts

All standard-library Python, cross-platform, no install. After step 2 of the
install they live in your project at `_agent_ops/tools/`, so run them from your
project root: `python _agent_ops/tools/<script> ...`. Only `init_project_ops.py`
stays in the pack -- it needs the pack's templates.

| Question | Command |
| --- | --- |
| Set up a project | `init_project_ops.py --target <path>` |
| What state am I starting from? | `session_start.py --root .` *(read-only)* |
| Build/refresh the code graph | `build_code_index.py --root .` |
| Who calls this? How do I get here? | `explore.py --symbol` / `--path` |
| What breaks if I change this? | `explore.py --impact` |
| Refresh the human-readable map | `generate_repo_map.py --root . --output _agent_ops/REPO_MAP.md --force` |
| Which files does this change touch? | `scan_deps.py --seed "<keyword>" --hops 2` |
| Is this repo safe to publish? | `check_repo_hygiene.py --root .` |
| Shrink the log | `summarize_implementation_log.py --rotate` |

**No Python?** Everything still works. Every script has a manual fallback
written out in `core-context/SESSION_PROTOCOL.template.md`.

---

## Setting up your agent

The install writes `AGENTS.md` at your repo root for you, plus thin
`CLAUDE.md`/`GEMINI.md` adapters that `@`-import it for the two tools that
don't read `AGENTS.md` on their own. It already points at `_agent_ops/` and
the tools. Then run `BOOTSTRAP.md` once if you also want the team folders
wired up.

| Tool | Base rules | Invoke a team | Real parallel subagents |
| --- | --- | --- | --- |
| **Codex** | `AGENTS.md` (auto) | `@bug-fix-team/SKILL.md` | Yes — `.codex/agents/` |
| **Claude Code** | `AGENTS.md` (via `CLAUDE.md` import) | Teams are discoverable skills | Yes — `.claude/agents/` |
| **Cursor / Windsurf** | `AGENTS.md` (auto) | `@<team>/SKILL.md` | Detected at runtime; falls back to sequential |
| **Gemini / DeepSeek** | `AGENTS.md` (via `GEMINI.md` import, or Gemini's `context.fileName` setting) | `@<team>/SKILL.md` | Detected at runtime; falls back to sequential |

There are four real subagents: `tester` and `repo_hygiene_reviewer` (read-only),
`bug_hunter` (read-only, probes one theory), `bug_fixer` (applies a confirmed fix).

**The agent will never claim it spawned subagents when it did not.** If your tool
cannot spawn them, it runs the same roles one after another and tells you so.

Just say what you want — *"use subagents to audit this"*, *"gọi agent con kiểm
tra giúp"* — and the agent recommends `parallel`, `sequential`, or `solo` with
the cost, then waits for your OK.

---

## Safety

These are always on, in every team:

- Never `git add .` — explicit files only
- Never commit or push unless you asked
- Never install dependencies
- Never claim a test passed unless it actually ran
- Ask before anything destructive
- `@start-here` may only write inside `_agent_ops/` — never your source or git

Before a task is reported done, the agent prints a **Closure Receipt**: one line
per memory file, each saying what was updated or why it was not needed. The
not-needed reason must identify the absent trigger; "the prompt did not name
this file" is invalid. Silently skipping a line is a protocol violation.

---

## What this does *not* do

Being straight with you:

- **It does not make the model smarter.** Hard problems stay hard. It stops the
  model wasting effort re-learning what it already knew.
- **The code graph only sees static structure** in `.py`, `.js`, `.jsx`, `.ts`,
  `.tsx`. Dynamic dispatch, DI, reflection, and route registries are invisible.
  Never conclude "this file is dead" from the graph alone.
- **The Closure Receipt is a contract, not a daemon.** The requirement is
  repeated in the always-on agent rules, generated target instructions,
  templates, and commands, and a golden test guards that propagation. It still
  requires the agent to follow instructions and human review for material work.
- **Rebuilds are manual.** The session check reminds you; it does not watch files.
- **Small repos do not need this.** Under ~20 files the overhead outweighs the
  benefit — use `--no-ops`.
- It does not replace human review, guarantee correctness, or push your code.

---

## Common mistakes

| Mistake | Do instead |
| --- | --- |
| Loading every team folder at once | Let `@start-here` route you to one |
| Refactoring before a recovery point | Let `clean-code-team` create one first |
| Fixing a bug before reproducing it | Let `bug-fix-team` verify first |
| Full audit when a scoped one works | Ask for a scoped audit |
| Grepping a repo you already indexed | `explore.py --symbol <name>` |
| Letting one file grow past ~400 lines | Check **Oversized Files** in `REPO_MAP.md`, split by responsibility |
| Hand-editing `_agent_ops/tools/` | Fix the pack and re-run the install |
| Trusting an `ambiguous` edge | Open the file and confirm |

---

## Repository layout

```
START_HERE.md        Entry guide for humans
AGENTS.md            Always-on rules every agent reads
BOOTSTRAP.md         One-time setup prompt
TEAM_ROUTER.md       Which team for which task

<name>-team/         Nine teams, one SKILL.md each
core-context/        Templates copied into your project's _agent_ops/
commands/            Copy-paste prompts
harness/             Checklists and risk matrices
scripts/             Python helpers (stdlib only); copied into each project
examples/            Neutral, public-safe examples

.claude/  .codex/    Thin adapters — the team folders are the source of truth
```

---

## License

MIT. Use it, fork it, adapt it.

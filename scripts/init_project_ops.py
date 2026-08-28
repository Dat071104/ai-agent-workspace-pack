#!/usr/bin/env python3
"""Initialize an AI-agent project operations folder in a target project."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Running a tool must never leave __pycache__ inside someone else's repository.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))


TEMPLATE_MAP = {
    "INDEX.template.md": "INDEX.md",
    "PROJECT_CONTEXT_CARD.template.md": "PROJECT_CONTEXT_CARD.md",
    "SESSION_PROTOCOL.template.md": "SESSION_PROTOCOL.md",
    "SESSION_BRIEF.template.md": "SESSION_BRIEF.md",
    "CURRENT_TASK.template.md": "CURRENT_TASK.md",
    "IMPLEMENTATION_LOG.template.md": "IMPLEMENTATION_LOG.md",
    "DECISION_LOG.template.md": "DECISION_LOG.md",
    "RISK_REGISTER.template.md": "RISK_REGISTER.md",
    "PHASE_ROADMAP.template.md": "PHASE_ROADMAP.md",
    "OPERATING_RULES.template.md": "OPERATING_RULES.md",
}

# Tools copied into <ops>/tools/ so the target project can run them without the
# pack being present. Installing the pack "next to" a project used to leave the
# project unable to run any of this: `python scripts/session_start.py` only
# works from inside the pack. These are stdlib-only and cross-import each other,
# so they are copied as a set. init_project_ops.py itself is NOT copied -- it
# needs the pack's core-context/ templates, which do not travel with it.
RUNTIME_TOOLS = [
    "scan_deps.py",
    "generate_context_card.py",
    "source_state.py",
    "generate_repo_map.py",
    "build_code_index.py",
    "refresh_repo_map.py",
    "explore.py",
    "session_start.py",
    "summarize_implementation_log.py",
    "check_repo_hygiene.py",
]

# Hybrid git policy: durable project memory is tracked so it survives a clone;
# session-scoped scratch stays local so it never noises up a diff or leaks
# working notes into a public repository.
SESSION_SCOPED = [
    "SESSION_BRIEF.md",
    "CURRENT_TASK.md",
    "LOG_SUMMARY.md",
    "code_index.json",
]

OPS_GITIGNORE = """# Hybrid policy for _agent_ops/ (see INDEX.md).
#
# Ignored below: session-scoped scratch and derived files. SESSION_BRIEF and
# CURRENT_TASK are machine-local working notes that change every session;
# LOG_SUMMARY is regenerated from the log, so tracking it would only create
# merge noise.
#
# Everything else in this folder IS tracked on purpose: the context card, repo
# map, implementation log and its archive, handoff, decisions, risks, roadmap,
# and operating rules are durable project memory that must survive a clone.
# Never put secrets or private data in tracked files.

SESSION_BRIEF.md
CURRENT_TASK.md
LOG_SUMMARY.md

# Derived build artifact: rebuilt from source by build_code_index.py, can reach
# tens of MB on a large repo, and would conflict on every merge. REPO_MAP.md is
# the small human-readable view of it and IS tracked.
code_index.json

# Bytecode from running tools/. The tools themselves ARE tracked on purpose: a
# teammate who clones this project then has working tooling without the pack.
__pycache__/
"""


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def relative_folder(value: str, option: str) -> Path:
    """Validate a target-relative layout path before any writes occur."""

    folder = Path(value.replace("\\", "/"))
    if not value or folder.is_absolute() or any(part == ".." for part in folder.parts) or str(folder) in {"", "."}:
        raise ValueError(f"{option} must be a non-empty path inside --target")
    return folder


def detect_embedded_folder(target: Path) -> Path | None:
    """Return the pack's folder when this pack was copied INTO the target.

    The bootstrap instructions name `init_project_ops.py --target .`, which a
    namespaced install resolves to `<folder>/scripts/init_project_ops.py`.
    Without this detection that command created `_agent_ops/` at the application
    root and skipped the root adapters -- reproducing the flat layout the
    namespaced mode exists to avoid, from the pack's own documented command.
    """

    try:
        relative = repo_root().relative_to(target)
    except ValueError:
        return None
    return Path(relative.as_posix()) if relative.parts else None


def copy_template(source: Path, destination: Path, force: bool, ops_relative: str) -> str:
    if destination.exists() and not force:
        return f"SKIP existing: {destination}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = source.read_text(encoding="utf-8")
    destination.write_text(content.replace("_agent_ops", ops_relative), encoding="utf-8")
    return f"WRITE: {destination}"


def write_if_absent(destination: Path, content: str, force: bool) -> str:
    if destination.exists() and not force:
        return f"SKIP existing: {destination}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return f"WRITE: {destination}"


TOOLS_README = """# Tools

Copies of the workspace-pack scripts, so this project can run them without the
pack being installed. Do not hand-edit: re-running `init_project_ops.py`
overwrites this folder. Fix the pack instead.

Run every tool from the project root:

```bash
python _agent_ops/tools/session_start.py --root .
python _agent_ops/tools/explore.py --symbol <name>

python _agent_ops/tools/refresh_repo_map.py --root . --stage
```

For an authorized source commit, run the refresh helper after staging source and
tests. It rebuilds the index and Repo Map once, then stages only REPO_MAP.md.
"""

TARGET_AGENTS_MD = """# AGENTS.md

Agent instructions for this project. Generated by the AI agent workspace pack.
Edit it freely -- it is never overwritten once it exists.

<!-- PACK_MODE -->

## Start Every Session Here

```bash
python _agent_ops/tools/session_start.py --root .
```

Read-only. It prints session continuity, the git delta since memory was last
verified, stale memory, unfilled placeholders, and log size. If it reports
CONTINUATION, read `_agent_ops/HANDOFF.md` before anything else.

Then load only `_agent_ops/SESSION_BRIEF.md`, `_agent_ops/OPERATING_RULES.md`,
and `_agent_ops/CURRENT_TASK.md` when a task is already in progress.
`_agent_ops/INDEX.md` is the read-order router for the rest of that folder. Do
not load every file in it on every turn.

## Locate Code Without Grepping

Read `_agent_ops/REPO_MAP.md` first: modules, routes, and the files with the
widest blast radius, in one size-capped read. For symbol-level questions, query
the code graph instead of grepping:

```bash
python _agent_ops/tools/explore.py --symbol <name>   # definitions, callers, callees
python _agent_ops/tools/explore.py --path <a> <b>    # how control reaches a symbol
python _agent_ops/tools/explore.py --impact <name>   # blast radius + tests to run
python _agent_ops/tools/explore.py --entrypoints     # routes and unreferenced symbols
```

Every edge carries a provenance tag: `exact`, `heuristic`, `ambiguous`, `weak`.
Treat the last three as leads to confirm by reading code, never as fact. Static
analysis cannot see dynamic dispatch, DI wiring, reflection, or runtime
registries, so an impact result is the MINIMUM blast radius, never the maximum.

Rebuild both after significant code changes:

```bash
python _agent_ops/tools/build_code_index.py --root . --output _agent_ops/code_index.json --force
python _agent_ops/tools/generate_repo_map.py --root . --output _agent_ops/REPO_MAP.md --force
```

## How To Work

- Lead with the answer, then the reasoning. No preamble, no filler.
- Say what you understood and what context is missing. Ask at most one
  clarifying question before acting on ambiguous input.
- Ask before writing or modifying files unless autonomous mode was confirmed.
- Never use `git add .`; stage explicit files only. Ask before destructive
  actions. Never commit secrets, datasets, model files, or local logs.
- Keep `_agent_ops/CURRENT_TASK.md` current DURING a task, not only at the end:
  files touched, approaches ruled out with their evidence, next step. That file
  is what survives a mid-task context compaction.
- A task prompt defines deliverable scope, not durable recordkeeping. Before a
  completion report, classify the work actually performed under the session
  protocol; a filename omitted from the prompt never makes a triggered record
  not needed.
- Append the implementation log for implementation, test, audit, gate, or
  verification evidence. Update the project context card for durable
  phase/milestone state and the decision log for material trade-offs. Write
  these records before printing the Closure Receipt; an explicit user opt-out
  must be reported as a constraint, not as not needed.
- Before a local commit that includes staged project code, run the repo-map
  refresh helper with --stage after tests and before git commit. It rebuilds the
  symbol index and REPO_MAP.md once, then stages only REPO_MAP.md. If the
  managed pre-commit hook is installed, it enforces the repo-map safety gate and
  blocks an index/worktree mismatch.

## Coding Standard

- One responsibility per change. A function, a file, a commit does one thing.
- No overlapping side effects: two code paths must not write the same state
  without one clear owner. That is the main cause of "fixing one bug creates
  another".
- Keep files small enough to reason about. Split a file before it passes ~400
  lines and a function before ~50. Split along a responsibility boundary and
  name the boundary you used; never split by line count alone.
- Reuse existing logic instead of duplicating it. Look for an existing helper
  before writing a new one.
"""

EMBEDDED_MODE = """## Pack Mode: Embedded

This repository contains the full workspace pack (`TEAM_ROUTER.md` is present).
Treat `@start-here` as a literal session marker. The managed bridge below is
the project entry point for routing it safely.

<!-- AI_AGENT_WORKSPACE_PACK:BEGIN v1 -->
## AI Agent Workspace Pack

Instructions outside this managed block remain authoritative. This block is an
approved, narrowly scoped amendment for the workflow below.

When a user message starts with `@start-here`, read `START_HERE.md` and
`TEAM_ROUTER.md`, then load only the selected team's `SKILL.md`.

Pack instructions may add workflow but must not weaken existing project rules.
`@start-here` authorizes only `_agent_ops/` writes defined by the pack; source,
configuration, dependencies, git, destructive actions, and external services
remain governed by the project's existing rules.
<!-- AI_AGENT_WORKSPACE_PACK:END v1 -->

If `_agent_ops/` is missing, bootstrap it with
`python scripts/init_project_ops.py --target .`; that creates only agent-ops
state, never source or git changes. After bootstrap, use the local tools under
`_agent_ops/tools/` for deterministic checks and graph queries.
"""

RUNTIME_ONLY_MODE = """## Pack Mode: Runtime-only

No `TEAM_ROUTER.md` was present when this file was generated. Use the local
`_agent_ops/` records and tools normally, but do not claim that named pack teams
or `@start-here` routing instructions are available unless the user supplies an
embedded pack or an explicit team playbook.
"""

AGENTS_BRIDGE_BEGIN = "<!-- AI_AGENT_WORKSPACE_PACK:BEGIN v1 -->"
AGENTS_BRIDGE_END = "<!-- AI_AGENT_WORKSPACE_PACK:END v1 -->"
AGENTS_BRIDGE_PREFIX = "<!-- AI_AGENT_WORKSPACE_PACK:"
AGENTS_BRIDGE = """<!-- AI_AGENT_WORKSPACE_PACK:BEGIN v1 -->
## AI Agent Workspace Pack

Instructions outside this managed block remain authoritative. This block is an
approved, narrowly scoped amendment for the workflow below.

When a user message starts with `@start-here`, read `START_HERE.md` and
`TEAM_ROUTER.md`, then load only the selected team's `SKILL.md`.

Pack instructions may add workflow but must not weaken existing project rules.
`@start-here` authorizes only `_agent_ops/` writes defined by the pack; source,
configuration, dependencies, git, destructive actions, and external services
remain governed by the project's existing rules.
<!-- AI_AGENT_WORKSPACE_PACK:END v1 -->"""


def write_tools(ops_dir: Path, ops_relative: str) -> list[str]:
    """Copy the runtime tools into the project so it stops depending on the pack.

    Refreshed on every init even without --force: these are pack-owned derived
    copies, and a stale copy that silently disagrees with the pack is worse than
    a noisy overwrite. Nothing the user authored lives in this folder.
    """
    source_dir = Path(__file__).resolve().parent
    tools_dir = ops_dir / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    results: list[str] = []
    for name in RUNTIME_TOOLS:
        source = source_dir / name
        if not source.exists():
            results.append(f"WARN missing tool: {source}")
            continue
        destination = tools_dir / name
        action = "UPDATE" if destination.exists() else "WRITE"
        shutil.copyfile(source, destination)
        results.append(f"{action}: {destination}")
    results.append(write_if_absent(tools_dir / "README.md", TOOLS_README.replace("_agent_ops", ops_relative), True))
    return results


REPO_MAP_HOOK_MARKER = "# AI_AGENT_OPS_REPO_MAP_PRE_COMMIT v1"
REPO_MAP_HOOK = """#!/bin/sh
# AI_AGENT_OPS_REPO_MAP_PRE_COMMIT v1
set -eu

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
TOOL="$ROOT/_agent_ops/tools/refresh_repo_map.py"
if [ ! -f "$TOOL" ]; then
  echo "BLOCKED: missing _agent_ops/tools/refresh_repo_map.py" >&2
  exit 2
fi

if python -c "import sys" >/dev/null 2>&1; then
  exec python "$TOOL" --root "$ROOT" --stage
fi
if python3 -c "import sys" >/dev/null 2>&1; then
  exec python3 "$TOOL" --root "$ROOT" --stage
fi
if py -3 -c "import sys" >/dev/null 2>&1; then
  exec py -3 "$TOOL" --root "$ROOT" --stage
fi
echo "BLOCKED: no working Python interpreter found for repo-map hook" >&2
exit 2
"""


def install_repo_map_hook(target: Path, ops_relative: str) -> str:
    """Install only the pack-managed pre-commit hook; preserve any user hook."""

    result = subprocess.run(
        ["git", "rev-parse", "--git-path", "hooks/pre-commit"],
        cwd=str(target),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return "SKIP repo-map hook: target is not a Git repository."

    hook_path = Path(result.stdout.strip())
    if not hook_path.is_absolute():
        hook_path = target / hook_path
    if hook_path.exists():
        existing = hook_path.read_text(encoding="utf-8", errors="ignore")
        if REPO_MAP_HOOK_MARKER not in existing:
            return f"WARN existing pre-commit hook preserved: {hook_path}"
        action = "UPDATE"
    else:
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        action = "WRITE"

    with hook_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(REPO_MAP_HOOK.replace("_agent_ops", ops_relative))
    if os.name != "nt":
        hook_path.chmod(hook_path.stat().st_mode | 0o100)
    return f"{action}: managed repo-map pre-commit hook: {hook_path}"


def target_agents_content(target: Path, ops_relative: str) -> str:
    """One generated entry point, accurate for embedded and runtime-only installs."""
    mode = EMBEDDED_MODE if (target / "TEAM_ROUTER.md").is_file() else RUNTIME_ONLY_MODE
    return TARGET_AGENTS_MD.replace("<!-- PACK_MODE -->", mode.rstrip()).replace("_agent_ops", ops_relative)


def write_target_agents_md(target: Path, ops_relative: str) -> str:
    """Drop an AGENTS.md at the project root if it has none.

    Codex, Cursor, and Windsurf auto-discover AGENTS.md; Claude Code and Gemini
    CLI do not (they default to CLAUDE.md / GEMINI.md respectively), so
    write_target_claude_md()/write_target_gemini_md() below give those two a
    thin adapter that imports this file instead of duplicating it. Without any
    of this, everything installed under _agent_ops/ is invisible unless the
    user remembers to point at it every session. Never overwritten: a project
    that already has one has already made this decision.
    """
    destination = target / "AGENTS.md"
    return write_if_absent(destination, target_agents_content(target, ops_relative), False)


def claude_md_adapter(import_line: str) -> str:
    return f"""{import_line}

Claude Code reads `CLAUDE.md`, not `AGENTS.md`. The import above pulls in
this project's canonical agent instructions so they are not duplicated
across two files. Add Claude-specific instructions below this line.
"""


def gemini_md_adapter(import_line: str) -> str:
    return f"""{import_line}

Gemini CLI defaults to `GEMINI.md`. The import above pulls in this project's
canonical agent instructions so they are not duplicated across two files.
Add Gemini-specific instructions below this line.
"""


def write_target_claude_md(target: Path, import_line: str = "@AGENTS.md") -> str:
    """Drop a thin CLAUDE.md at the project root if it has none.

    Claude Code's own docs recommend exactly this pattern for an AGENTS.md
    that other tools also read: `@AGENTS.md` as an import, expanded into
    context at session start. Never overwritten: a project with its own
    CLAUDE.md has already made that decision.
    """
    return write_if_absent(target / "CLAUDE.md", claude_md_adapter(import_line), False)


def write_target_gemini_md(target: Path, import_line: str = "@./AGENTS.md") -> str:
    """Drop a thin GEMINI.md at the project root if it has none.

    Gemini CLI's `@path` import requires a leading `./` for a same-directory
    file, unlike Claude Code's `@AGENTS.md`. Never overwritten: a project
    with its own GEMINI.md has already made that decision.
    """
    return write_if_absent(target / "GEMINI.md", gemini_md_adapter(import_line), False)


def imports_agents_md(destination: Path, import_line: str) -> bool:
    """True if an existing CLAUDE.md/GEMINI.md already imports AGENTS.md.

    A host-owned file is never modified (see write_target_claude_md/
    write_target_gemini_md), so its bootstrap step can only warn, not fix,
    the case where that file predates this pack and has no import -- the same
    discoverability gap AGENTS.md itself had before those adapters existed,
    one level deeper.
    """
    try:
        return import_line in destination.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False


def agents_bridge_status(target: Path) -> tuple[str, str]:
    """Return a structural status for the optional host-owned AGENTS bridge."""
    destination = target / "AGENTS.md"
    if not destination.exists():
        return "MISSING", "AGENTS.md does not exist"
    try:
        content = destination.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return "CORRUPT", f"cannot read AGENTS.md safely: {error}"

    begins = content.count(AGENTS_BRIDGE_BEGIN)
    ends = content.count(AGENTS_BRIDGE_END)
    any_marker = AGENTS_BRIDGE_PREFIX in content
    if begins == 0 and ends == 0:
        if any_marker:
            return "CORRUPT", "unsupported bridge marker or version"
        return "MISSING", "no managed bridge block"
    if begins != 1 or ends != 1:
        return "CORRUPT", "expected exactly one BEGIN and one END marker"

    start = content.index(AGENTS_BRIDGE_BEGIN)
    end_start = content.index(AGENTS_BRIDGE_END)
    if end_start < start:
        return "CORRUPT", "END marker appears before BEGIN marker"
    end = end_start + len(AGENTS_BRIDGE_END)
    if content[start:end] == AGENTS_BRIDGE:
        return "INSTALLED", "managed bridge v1"
    return "OUTDATED", "managed block differs from bridge v1"


def install_agents_bridge(target: Path) -> str:
    """Append or update only the pack-owned bridge block in AGENTS.md."""
    destination = target / "AGENTS.md"
    status, detail = agents_bridge_status(target)
    if status == "CORRUPT":
        return f"AGENTS BRIDGE: CORRUPT ({detail}); not modified"
    if status == "INSTALLED":
        return "AGENTS BRIDGE: INSTALLED (managed bridge v1; unchanged)"
    if status == "MISSING":
        content = destination.read_text(encoding="utf-8")
        separator = "" if content.endswith("\n") else "\n"
        destination.write_text(content + separator + "\n" + AGENTS_BRIDGE + "\n", encoding="utf-8")
        return "AGENTS BRIDGE: INSTALLED (managed bridge v1 appended)"

    content = destination.read_text(encoding="utf-8")
    start = content.index(AGENTS_BRIDGE_BEGIN)
    end = content.index(AGENTS_BRIDGE_END, start) + len(AGENTS_BRIDGE_END)
    destination.write_text(content[:start] + AGENTS_BRIDGE + content[end:], encoding="utf-8")
    return "AGENTS BRIDGE: INSTALLED (managed bridge v1 updated)"


def namespaced_bridge_line(embedded_folder: Path) -> str:
    """The root entry point for one copied pack directory."""

    return f"@{embedded_folder.as_posix()}/AGENTS.md"


def namespaced_agents_bridge_status(target: Path, embedded_folder: Path) -> tuple[str, str]:
    """Check whether the pack link is literally the first AGENTS.md line."""

    destination = target / "AGENTS.md"
    if not destination.exists():
        return "MISSING", "AGENTS.md does not exist"
    try:
        lines = destination.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        return "CORRUPT", f"cannot read AGENTS.md safely: {error}"
    expected = namespaced_bridge_line(embedded_folder)
    if lines and lines[0] == expected:
        return "INSTALLED", "namespaced bridge is first line"
    if expected in lines:
        return "OUTDATED", "namespaced bridge is not the first line"
    return "MISSING", "no namespaced bridge line"


def install_namespaced_agents_bridge(target: Path, embedded_folder: Path) -> str:
    """Prepend the pack link while preserving every host-owned AGENTS.md line."""

    destination = target / "AGENTS.md"
    status, detail = namespaced_agents_bridge_status(target, embedded_folder)
    if status == "CORRUPT":
        return f"AGENTS BRIDGE: CORRUPT ({detail}); not modified"
    if status == "INSTALLED":
        return "AGENTS BRIDGE: INSTALLED (namespaced bridge unchanged)"

    expected = namespaced_bridge_line(embedded_folder)
    content = destination.read_text(encoding="utf-8") if destination.exists() else ""
    # An earlier install may have left its exact bridge line below host rules.
    # Remove only that unambiguous pack-owned line, never surrounding text.
    remaining = [line for line in content.splitlines(keepends=True) if line.rstrip("\r\n") != expected]
    suffix = "".join(remaining)
    destination.write_text(expected + "\n" + suffix, encoding="utf-8")
    action = "created" if not content else "prepended"
    return f"AGENTS BRIDGE: INSTALLED (namespaced bridge {action}; host text preserved)"


# --------------------------------------------------------------------------- #
# Root harness adapters
#
# Codex discovers subagents in `.codex/agents/` at the repository root, and
# Claude Code discovers `.claude/agents/` and `.claude/skills/` there. A
# namespaced install puts the pack -- and therefore those folders -- one level
# down, which silently dropped the four subagents and the nine team skills the
# flat layout provided. Copying the pack back to the root would undo the point
# of the namespaced layout, so only these small pointer files live at the root;
# every workflow they name stays inside the pack folder.
# --------------------------------------------------------------------------- #

ADAPTER_MARKER = "AI_AGENT_WORKSPACE_PACK:ADAPTER v1"
ADAPTER_NOTE = "generated pointer into the pack folder; edit the pack, not this file."
# Directories only. A host `.codex/config.toml` or `.claude/settings.json` is
# host policy: never generated, never overwritten.
ADAPTER_SOURCES = (".codex/agents", ".claude/agents", ".claude/skills")
# Pack-relative paths named inside the adapters. They must resolve from the
# project root once the adapter lives there. `_agent_ops` is included because a
# namespaced install keeps project memory inside the pack folder too.
ADAPTER_PATH_ROOTS = (
    "_agent_ops",
    "advisor-team",
    "analyze-team",
    "bug-fix-team",
    "build-team",
    "clean-code-team",
    "commands",
    "core-context",
    "examples",
    "handoff-team",
    "harness",
    "prompting-team",
    "repo-hygiene-team",
    "scripts",
    "tester-team",
)
# Path-leading occurrences only: `tester-team/SKILL.md` is rewritten, while
# `ai-agent-workspace-pack/tester-team/SKILL.md` and prose such as "the
# tester-team folder" are left alone. That also makes a re-run idempotent.
ADAPTER_PATH_RE = re.compile(
    r"(?<![\w./-])(" + "|".join(re.escape(name) for name in ADAPTER_PATH_ROOTS) + r")/"
)


def adapter_sources(pack_root: Path) -> list[Path]:
    """Every pointer file shipped by the pack, in a stable order."""

    found: list[Path] = []
    for entry in ADAPTER_SOURCES:
        source = pack_root / entry
        if source.is_dir():
            found += sorted(path for path in source.rglob("*") if path.is_file())
    return found


def rewrite_adapter_paths(text: str, prefix: str) -> str:
    """Make pack-relative paths resolve from the project root."""

    return ADAPTER_PATH_RE.sub(lambda match: prefix + match.group(1) + "/", text)


def stamp_adapter(text: str, suffix: str) -> str:
    """Mark a file as pack-owned so a re-run updates it but never a host file."""

    if suffix == ".toml":
        return "# " + ADAPTER_MARKER + " -- " + ADAPTER_NOTE + "\n" + text
    comment = "<!-- " + ADAPTER_MARKER + " -- " + ADAPTER_NOTE + " -->"
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for position in range(1, len(lines)):
            if lines[position].strip() == "---":
                body = lines[: position + 1] + ["", comment] + lines[position + 1 :]
                return "\n".join(body) + "\n"
    return comment + "\n\n" + text


def install_root_adapters(
    target: Path, pack_root: Path, embedded_folder: Path, force: bool
) -> list[str]:
    """Install root pointers for the harnesses that only auto-discover at the root."""

    sources = adapter_sources(pack_root)
    if not sources:
        return [
            "WARN no harness adapters found in " + str(pack_root)
            + "; subagents and team skills stay undiscovered."
        ]

    prefix = embedded_folder.as_posix() + "/"
    written = 0
    unchanged = 0
    messages: list[str] = []
    for source in sources:
        destination = target / source.relative_to(pack_root)
        content = stamp_adapter(
            rewrite_adapter_paths(source.read_text(encoding="utf-8"), prefix), source.suffix
        )
        if destination.exists():
            existing = destination.read_text(encoding="utf-8", errors="ignore")
            if ADAPTER_MARKER not in existing and not force:
                messages.append("SKIP host-owned adapter (not overwritten): " + str(destination))
                continue
            if existing == content:
                unchanged += 1
                continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        written += 1

    messages.append(
        "ROOT ADAPTERS: {written} written, {unchanged} unchanged -- subagents and team "
        "skills resolve into {prefix}".format(written=written, unchanged=unchanged, prefix=prefix)
    )
    return messages


def write_code_index(target: Path, ops_dir: Path, force: bool) -> str:
    """Build the symbol-level index that scripts/explore.py queries."""
    destination = ops_dir / "code_index.json"
    if destination.exists() and not force:
        return f"SKIP existing: {destination}"
    try:
        import json  # noqa: PLC0415

        from build_code_index import build_index  # noqa: PLC0415

        index = build_index(target)
        destination.write_text(json.dumps(index, separators=(",", ":")), encoding="utf-8")
        return (
            f"WRITE: {destination} "
            f"({len(index['symbols'])} symbols, {len(index['edges'])} edges)"
        )
    except Exception as error:  # noqa: BLE001 - report, do not abort init
        return (
            f"WARN could not build {destination}: {error}"
            "\n"
            "     Run scripts/build_code_index.py manually if you want "
            "symbol-level exploration."
        )


def write_repo_map(target: Path, ops_dir: Path, force: bool) -> str:
    """Generate the codegraph-lite map. Never fatal: the pack must stay usable
    on repos where this scan cannot run."""
    destination = ops_dir / "REPO_MAP.md"
    if destination.exists() and not force:
        return f"SKIP existing: {destination}"
    try:
        from generate_repo_map import render_map  # noqa: PLC0415
        from scan_deps import build_graph  # noqa: PLC0415

        graph = build_graph(target)
        destination.write_text(
            render_map(target, graph, 25, 15, ops_dir / "code_index.json", destination), encoding="utf-8"
        )
        return f"WRITE: {destination} ({len(graph)} code files indexed)"
    except Exception as error:  # noqa: BLE001 - report, do not abort init
        return (
            f"WARN could not generate {destination}: {error}\n"
            "     Run scripts/generate_repo_map.py manually, or describe the "
            "layout in PROJECT_CONTEXT_CARD.md."
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create project memory files in a target project."
    )
    parser.add_argument("--target", required=True, help="Target project directory.")
    parser.add_argument(
        "--ops-folder",
        default=None,
        help="Operations folder inside the target (default: _agent_ops, or <embedded-folder>/_agent_ops).",
    )
    parser.add_argument(
        "--embedded-folder",
        default=None,
        help=(
            "Copied workspace-pack folder inside the target, for example ai-agent-workspace-pack. "
            "Keeps project operations inside that folder and installs its root AGENTS.md bridge."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing ops files.",
    )
    parser.add_argument(
        "--no-repo-map",
        action="store_true",
        help="Skip generating REPO_MAP.md (useful for very large repositories).",
    )
    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Skip building code_index.json (the symbol-level graph).",
    )
    parser.add_argument(
        "--no-tools",
        action="store_true",
        help="Do not copy the runtime tools into <ops>/tools/.",
    )
    parser.add_argument(
        "--install-repo-map-hook",
        action="store_true",
        help=(
            "Install the managed pre-commit hook that refreshes and explicitly stages "
            "REPO_MAP.md for staged project-code commits. Never overwrites another hook."
        ),
    )
    parser.add_argument(
        "--no-agents-md",
        action="store_true",
        help="Do not create AGENTS.md at the project root when it is missing.",
    )
    parser.add_argument(
        "--install-agents-bridge",
        action="store_true",
        help=(
            "Explicitly install the workspace-pack bridge in an existing AGENTS.md. "
            "For --embedded-folder it becomes the first line and preserves all host text."
        ),
    )
    parser.add_argument(
        "--check-agents-bridge",
        action="store_true",
        help="Read-only bridge check; exits nonzero unless the managed bridge is installed.",
    )
    parser.add_argument(
        "--no-root-adapters",
        action="store_true",
        help=(
            "Do not install the root .claude/ and .codex/ pointer files. Without them "
            "Codex and Claude Code cannot discover the pack's subagents or team skills."
        ),
    )
    args = parser.parse_args()
    if args.install_repo_map_hook and args.no_tools:
        parser.error("--install-repo-map-hook requires the runtime tools.")
    if args.install_agents_bridge and args.no_agents_md:
        parser.error("--install-agents-bridge cannot be combined with --no-agents-md.")
    if args.install_agents_bridge and args.check_agents_bridge:
        parser.error("Choose either --install-agents-bridge or --check-agents-bridge.")

    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        parser.error(f"Target does not exist: {target}")
    if not target.is_dir():
        parser.error(f"Target is not a directory: {target}")

    try:
        embedded_folder = relative_folder(args.embedded_folder, "--embedded-folder") if args.embedded_folder else None
        ops_relative_path = relative_folder(args.ops_folder, "--ops-folder") if args.ops_folder else None
    except ValueError as error:
        parser.error(str(error))
    if embedded_folder is None and ops_relative_path is None:
        detected = detect_embedded_folder(target)
        if detected is not None:
            embedded_folder = detected
            print(
                "EMBEDDED FOLDER: auto-detected "
                + detected.as_posix()
                + " (this pack lives inside the target; keeping operations there)"
            )
    if embedded_folder:
        embedded_root = target / embedded_folder
        if not (embedded_root / "TEAM_ROUTER.md").is_file():
            parser.error(f"--embedded-folder is not a copied workspace pack: {embedded_root}")
        if ops_relative_path is None:
            ops_relative_path = embedded_folder / "_agent_ops"
    else:
        ops_relative_path = ops_relative_path or Path("_agent_ops")
    ops_relative = ops_relative_path.as_posix()
    flat_embedded = (target / "TEAM_ROUTER.md").is_file()
    if args.check_agents_bridge:
        status, detail = (
            namespaced_agents_bridge_status(target, embedded_folder)
            if embedded_folder
            else agents_bridge_status(target)
        )
        print(f"AGENTS BRIDGE: {status} ({detail})")
        return 0 if status == "INSTALLED" else 1
    if args.install_agents_bridge and not (embedded_folder or flat_embedded):
        parser.error("--install-agents-bridge requires a copied workspace pack.")

    templates_dir = repo_root() / "core-context"
    if not templates_dir.exists():
        parser.error(f"Cannot find template directory: {templates_dir}")

    ops_dir = target / ops_relative_path
    ops_dir.mkdir(parents=True, exist_ok=True)

    print(f"Target: {target}")
    print(f"Ops folder: {ops_dir}")

    for template_name, output_name in TEMPLATE_MAP.items():
        source = templates_dir / template_name
        if not source.exists():
            print(f"WARN missing template: {source}")
            continue
        print(copy_template(source, ops_dir / output_name, args.force, ops_relative))

    phase_dir = ops_dir / "phase_context_cards"
    phase_dir.mkdir(exist_ok=True)
    print(
        write_if_absent(
            phase_dir / "README.md",
            "# Phase Context Cards\n\n"
            "Store one phase context card per completed or active phase.\n\n"
            "Suggested name: `PHASE_001_<short-name>.md`.\n",
            args.force,
        )
    )

    archive_dir = ops_dir / "archive"
    archive_dir.mkdir(exist_ok=True)
    print(
        write_if_absent(
            archive_dir / "README.md",
            "# Archive\n\n"
            "Rotated implementation-log entries land here so the active log stays\n"
            "small enough to read cheaply. Read these only when investigating\n"
            "something older than the retained window.\n",
            args.force,
        )
    )

    print(write_if_absent(ops_dir / ".gitignore", OPS_GITIGNORE.replace("_agent_ops", ops_relative), args.force))

    if args.no_tools:
        print(f"SKIP tools (--no-tools): {ops_dir / 'tools'}")
    else:
        for line in write_tools(ops_dir, ops_relative):
            print(line)
    if args.install_repo_map_hook:
        print(install_repo_map_hook(target, ops_relative))

    # Index BEFORE map, not after: the map reads code_index.json to fill in its
    # Symbol Graph section, so building it second made a fresh install report
    # "Symbol Graph: Not built" even though the index landed moments later.
    if args.no_index:
        print(f"SKIP code index (--no-index): {ops_dir / 'code_index.json'}")
    else:
        print(write_code_index(target, ops_dir, args.force))
    if args.no_repo_map:
        print(f"SKIP repo map (--no-repo-map): {ops_dir / 'REPO_MAP.md'}")
    else:
        print(write_repo_map(target, ops_dir, args.force))

    agents_existed = (target / "AGENTS.md").exists()
    if args.no_agents_md:
        print(f"SKIP AGENTS.md (--no-agents-md): {target / 'AGENTS.md'}")
    elif embedded_folder:
        if agents_existed and not args.install_agents_bridge:
            status, detail = namespaced_agents_bridge_status(target, embedded_folder)
            if status == "MISSING":
                print(
                    "WARN copied pack detected but the namespaced AGENTS.md bridge is missing, "
                    "so no harness will read the pack. Prepend it without touching your own text:\n"
                    "         python " + embedded_folder.as_posix() + "/scripts/init_project_ops.py "
                    "--target . --install-agents-bridge"
                )
            else:
                print(f"AGENTS BRIDGE: {status} ({detail})")
        else:
            print(install_namespaced_agents_bridge(target, embedded_folder))

        claude_import = f"@{embedded_folder.as_posix()}/AGENTS.md"
        gemini_import = f"@./{embedded_folder.as_posix()}/AGENTS.md"
        claude_destination = target / "CLAUDE.md"
        claude_existed = claude_destination.exists()
        print(write_target_claude_md(target, claude_import))
        if claude_existed and not imports_agents_md(claude_destination, claude_import):
            print(
                "WARN existing CLAUDE.md does not import the copied pack, so Claude Code "
                "may never see its agent instructions. Add this line:\n"
                f"         {claude_import}"
            )

        gemini_destination = target / "GEMINI.md"
        gemini_existed = gemini_destination.exists()
        print(write_target_gemini_md(target, gemini_import))
        if gemini_existed and not imports_agents_md(gemini_destination, gemini_import):
            print(
                "WARN existing GEMINI.md does not import the copied pack, so Gemini CLI "
                "may never see its agent instructions. Add this line:\n"
                f"         {gemini_import}"
            )

        if args.no_root_adapters:
            print("SKIP root harness adapters (--no-root-adapters): subagents and team skills stay undiscovered.")
        else:
            for line in install_root_adapters(target, embedded_root, embedded_folder, args.force):
                print(line)
    else:
        print(write_target_agents_md(target, ops_relative))
        if args.install_agents_bridge:
            print(install_agents_bridge(target))
        elif flat_embedded and agents_existed:
            status, detail = agents_bridge_status(target)
            if status == "MISSING":
                print(
                    "WARN embedded pack detected but AGENTS bridge is missing. "
                    "Re-run with --install-agents-bridge to add the managed bridge."
                )
            else:
                print(f"AGENTS BRIDGE: {status} ({detail})")

        claude_destination = target / "CLAUDE.md"
        claude_existed = claude_destination.exists()
        print(write_target_claude_md(target))
        if claude_existed and not imports_agents_md(claude_destination, "@AGENTS.md"):
            print(
                "WARN existing CLAUDE.md does not import AGENTS.md, so Claude Code "
                "may never see this project's agent instructions. Add this line:\n"
                "         @AGENTS.md"
            )

        gemini_destination = target / "GEMINI.md"
        gemini_existed = gemini_destination.exists()
        print(write_target_gemini_md(target))
        if gemini_existed and not imports_agents_md(gemini_destination, "@./AGENTS.md"):
            print(
                "WARN existing GEMINI.md does not import AGENTS.md, so Gemini CLI "
                "may never see this project's agent instructions. Add this line:\n"
                "         @./AGENTS.md"
            )

    print("")
    print("Done. Existing files were preserved unless --force was used.")
    print(f"Session-scoped files are gitignored by {ops_relative}/.gitignore:")
    print("  " + ", ".join(SESSION_SCOPED))
    print(f"Everything else in {ops_relative}/ is tracked on purpose.")
    print("")
    print("Next steps, run from inside the project (no pack needed):")
    print(f"  cd {target}")
    print(f"  python {ops_relative}/tools/session_start.py --root .")
    print(f"  python {ops_relative}/tools/explore.py --symbol <name>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

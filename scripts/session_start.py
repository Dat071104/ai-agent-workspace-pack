#!/usr/bin/env python3
"""Print a deterministic session header for a managed AI-agent session.

Read-only. Writes nothing, stages nothing, runs no test or build command.

Purpose: move the bookkeeping half of `commands/start-here.md` out of the model.
Weaker models then only have to route the task, not also remember to check git
state, detect stale memory, and notice unfilled template placeholders.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Running a tool must never leave __pycache__ inside someone else's repository.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_context_card import git_value  # noqa: E402
from scan_deps import tool_prefix  # noqa: E402
from summarize_implementation_log import split_entries  # noqa: E402


PLACEHOLDER_RES = [
    re.compile(r"`<[^`\n]*>`"),
    re.compile(r"<fill in [^>\n]*>"),
]
ROTATE_THRESHOLD = 12
CODE_SUFFIXES = (".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".rb", ".php", ".cs")


def is_project_code(path: str) -> bool:
    """A changed file that should make the code map look stale.

    Excludes the agent's own folder: `_agent_ops/tools/` holds copies of these
    very scripts, and counting them made a fresh install report nine changed
    "code files" the moment the ops folder was committed.
    """
    cleaned = path.strip().replace("\\", "/")
    if cleaned.startswith("_agent_ops/") or "/_agent_ops/" in cleaned:
        return False
    return cleaned.endswith(CODE_SUFFIXES)


def git_changed_paths(root: Path, args: list[str]) -> set[str]:
    """Normalized paths from one git listing command, or an empty set on failure."""
    output = git_value(root, args)
    if output == "not available":
        return set()
    return {line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()}


def working_tree_code_files(root: Path) -> list[str]:
    """Project code changed outside HEAD, including staged and untracked files.

    A map or index stamped at HEAD is not fresh when a task has edited source
    without committing it. `_agent_ops/tools/` remains excluded through
    `is_project_code`, so copying the runtime cannot make every session stale.
    """
    paths: set[str] = set()
    for args in (
        ["diff", "--name-only"],
        ["diff", "--cached", "--name-only"],
        ["ls-files", "--others", "--exclude-standard"],
    ):
        paths.update(git_changed_paths(root, args))
    return sorted(path for path in paths if is_project_code(path))


def code_files_since(root: Path, stamp: str) -> list[str]:
    """Committed and working-tree project code newer than a map/index stamp."""
    committed = git_changed_paths(root, ["diff", "--name-only", f"{stamp}..HEAD"])
    combined = {path for path in committed if is_project_code(path)}
    combined.update(working_tree_code_files(root))
    return sorted(combined)


def read_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def section_body(text: str, heading: str) -> str:
    """Return the body under a `## Heading` up to the next heading of any level."""
    lines = text.splitlines()
    wanted = heading.strip().lower()
    collected: list[str] = []
    capture = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            if capture:
                break
            title = stripped.lstrip("#").strip().lower()
            # Prefix match so decorated headings still resolve, e.g.
            # "## Original Goal (do not lose)".
            capture = title == wanted or title.startswith(wanted)
            continue
        if capture:
            collected.append(line)
    return "\n".join(collected).strip()


def first_value(text: str, heading: str) -> str:
    body = section_body(text, heading)
    for line in body.splitlines():
        if line.strip():
            return line.strip().strip("`").strip()
    return ""


def count_placeholders(text: str) -> int:
    return sum(len(pattern.findall(text)) for pattern in PLACEHOLDER_RES)


def is_placeholder_only(line: str) -> bool:
    """True when a bullet is still the unfilled template text, not real content."""
    body = line.lstrip("-*").strip().strip("`").strip()
    return not body or (body.startswith("<") and body.endswith(">"))


def real_items(body: str) -> list[str]:
    """Filled-in entries from a section, whether it uses bullets or a table.

    Templates in this pack use both shapes, and every row still holding its
    `<placeholder>` text is dropped so a fresh template reports zero.
    """
    items: list[str] = []
    for raw in body.splitlines():
        line = raw.strip()
        if line.startswith(("-", "*")) and not line.startswith("---"):
            if not is_placeholder_only(line):
                items.append(line)
        elif line.startswith("|"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if not cells or all(set(cell) <= {"-", ":", ""} for cell in cells):
                continue  # separator row
            first = cells[0].strip("`").strip()
            if not first or first.startswith("<") or first.lower() in {"tried", "file", "risk"}:
                continue  # header row or unfilled placeholder row
            items.append("- " + " | ".join(cell for cell in cells if cell))
    return items


def commit_exists(root: Path, sha: str) -> bool:
    if not sha or sha.startswith("<"):
        return False
    # `rev-parse --verify` echoes the resolved SHA, so a successful check yields
    # non-empty stdout. `cat-file -e` succeeds silently and would be read as a
    # failure by git_value().
    return git_value(root, ["rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}"]) != "not available"


def has_real_content(text: str, headings: tuple[str, ...]) -> bool:
    """True when at least one of the named sections is filled in, not template text.

    Sections come in two shapes. For tables and bullet lists, `real_items` already
    drops header and placeholder rows. For a plain prose section, take the first
    line -- but never a table header row, which is boilerplate that would
    otherwise read as real content and make an untouched template look live.
    """
    for heading in headings:
        if real_items(section_body(text, heading)):
            return True
        value = first_value(text, heading)
        if value and not value.startswith(("<", "|")):
            return True
    return False


def continuity_block(brief: str, task: str, handoff: str) -> list[str]:
    """Answer the first question a swapped-in agent has: am I continuing someone?

    A new session should not have to be told by the user that a handoff exists.
    This looks for one and says so before anything else runs.
    """
    out = ["## Session Continuity", ""]
    status = first_value(handoff, "Status").lower() if handoff else ""
    task_live = has_real_content(task, ("Next Concrete Step", "Files Touched So Far"))
    brief_live = has_real_content(brief, ("Original Goal", "Active Task"))

    if handoff and status != "consumed":
        written = first_value(handoff, "Date")
        out += [
            "- **CONTINUATION.** A previous session left a handoff.",
            "- READ `_agent_ops/HANDOFF.md` FIRST, before routing or touching code.",
            f"- Handoff status: `{status or 'open'}`"
            + (f", written {written}" if written else ""),
            "- After absorbing it, set its Status to `consumed` so the next session",
            "  does not replay it.",
        ]
    elif task_live:
        out += [
            "- **TASK IN PROGRESS.** No open handoff, but `CURRENT_TASK.md` has live state.",
            "- Resume from its Next Concrete Step; honour its Ruled Out list.",
        ]
    elif brief_live:
        out += [
            "- **SESSION ESTABLISHED.** A brief exists; no task is mid-flight.",
            "- Start the next task from the brief's Active Task.",
        ]
    else:
        out += [
            "- **FRESH.** No handoff, no live task, no filled-in brief.",
            "- Treat this as a new session: establish the goal with the user first.",
        ]
    if handoff and status == "consumed":
        out.append("- An older handoff exists but is already marked consumed.")
    out.append("")
    return out


def render(root: Path, ops: Path, log_keep: int) -> str:
    tools = tool_prefix(root)
    brief_path = ops / "SESSION_BRIEF.md"
    task_path = ops / "CURRENT_TASK.md"
    card_path = ops / "PROJECT_CONTEXT_CARD.md"
    map_path = ops / "REPO_MAP.md"
    log_path = ops / "IMPLEMENTATION_LOG.md"
    handoff_path = ops / "HANDOFF.md"

    brief = read_text(brief_path)
    task = read_text(task_path)
    card = read_text(card_path)
    repo_map = read_text(map_path)
    log = read_text(log_path)
    handoff = read_text(handoff_path)

    head = git_value(root, ["rev-parse", "--short", "HEAD"])
    branch = git_value(root, ["branch", "--show-current"])
    status = git_value(root, ["status", "--short"])
    is_git = head != "not available"
    worktree_code = working_tree_code_files(root) if is_git else []

    out: list[str] = ["# Session Start (deterministic checks)", ""]

    out += ["## Repository", ""]
    if is_git:
        dirty = [line for line in status.splitlines() if line.strip()] if status != "not available" else []
        out += [
            f"- Root: `{root}`",
            f"- Branch: `{branch}`",
            f"- HEAD: `{head}`",
            f"- Uncommitted changes: {len(dirty)} file(s)",
        ]
        for line in dirty[:15]:
            out.append(f"    {line}")
        if len(dirty) > 15:
            out.append(f"    ... {len(dirty) - 15} more")
    else:
        out.append(f"- Root: `{root}` (not a git repository -- no delta or staleness checks)")
    out.append("")

    if not ops.exists():
        out += [
            "## Agent Ops",
            "",
            f"`{ops}` does not exist. Initialize it before a managed session:",
            "",
            "```bash",
            f'python <pack>/scripts/init_project_ops.py --target "{root}"',
            "```",
            "",
            "That one script lives in the workspace pack, not in the project: it",
            "needs the pack's core-context/ templates. It copies the rest of the",
            "tools into `_agent_ops/tools/`, and everything after it runs from the",
            "project with no pack present.",
            "",
        ]
        return "\n".join(out).rstrip() + "\n"

    out += continuity_block(brief, task, handoff)

    out += ["## Memory Freshness", ""]
    verified = first_value(brief, "Last Verified Commit")
    if not is_git:
        out.append("- Skipped: not a git repository.")
    elif not commit_exists(root, verified):
        out.append(
            "- SESSION_BRIEF has no usable `Last Verified Commit`. Treat project "
            "memory as UNVERIFIED against the current tree."
        )
    elif verified.startswith(head) or head.startswith(verified):
        if worktree_code:
            out.append(
                f"- SESSION_BRIEF matches HEAD (`{head}`), but {len(worktree_code)} "
                "uncommitted code file(s) make its behavioral memory stale."
            )
        else:
            out.append(f"- SESSION_BRIEF is current with HEAD (`{head}`).")
    else:
        delta = git_value(root, ["log", "--oneline", f"{verified}..HEAD"])
        commits = [line for line in delta.splitlines() if line.strip()] if delta != "not available" else []
        files = git_changed_paths(root, ["diff", "--name-only", f"{verified}..HEAD"])
        changed = sorted(files)
        code = code_files_since(root, verified)
        other = [line for line in changed if line not in code]
        out += [
            f"- SESSION_BRIEF was verified at `{verified}`; HEAD is `{head}`.",
            f"- {len(commits)} commit(s), {len(changed)} file(s) changed since then.",
        ]
        for line in commits[:10]:
            out.append(f"    {line}")
        if len(commits) > 10:
            out.append(f"    ... {len(commits) - 10} more")
        # Code changes are what invalidate a stale mental model; ops and doc
        # churn is expected noise, so it is counted rather than listed.
        out.append(f"- Code files changed ({len(code)}):")
        for line in code[:15]:
            out.append(f"    ~ {line}")
        if len(code) > 15:
            out.append(f"    ~ ... {len(code) - 15} more")
        if not code:
            out.append("    (none -- memory about code behavior is likely still valid)")
        if other:
            out.append(f"- Other files changed: {len(other)} (docs, config, _agent_ops)")
        out.append("- Re-read the affected memory before acting on it.")
    out.append("")

    out += ["## Repo Map", ""]
    if not repo_map:
        out += [
            "- `REPO_MAP.md` is missing. Generate it before grepping the repository:",
            "",
            "```bash",
            f"python {tools}/generate_repo_map.py --root . --output _agent_ops/REPO_MAP.md --force",
            "```",
        ]
    else:
        map_sha = first_value(repo_map, "Last Verified Commit")
        if not is_git or not commit_exists(root, map_sha):
            out.append("- Present; freshness unknown (no usable commit stamp).")
        elif map_sha.startswith(head) or head.startswith(map_sha):
            if worktree_code:
                out += [
                    f"- STALE: {len(worktree_code)} uncommitted code file(s) changed after `{map_sha}`.",
                    "  Regenerate with `--force` before trusting the module table.",
                ]
            else:
                out.append(f"- Current with HEAD (`{head}`).")
        else:
            code_files = code_files_since(root, map_sha)
            if code_files:
                out += [
                    f"- STALE: {len(code_files)} code file(s) changed since `{map_sha}`.",
                    "  Regenerate with `--force` before trusting the module table.",
                ]
            else:
                out.append(f"- Built at `{map_sha}`; no code files changed since. Still usable.")
    out.append("")

    out += ["## Symbol Index", ""]
    index_path = ops / "code_index.json"
    if not index_path.exists():
        out += [
            "- Not built. Without it there is no symbol-level exploration, so code",
            "  questions fall back to grepping. Build it once:",
            "",
            "```bash",
            f"python {tools}/build_code_index.py --root .",
            "```",
        ]
    else:
        try:
            index = json.loads(index_path.read_text(encoding="utf-8", errors="ignore"))
        except ValueError:
            index = {}
        index_sha = str(index.get("commit", ""))
        counts = f"{len(index.get('symbols', {}))} symbols, {len(index.get('edges', []))} edges"
        if not is_git or not commit_exists(root, index_sha):
            out.append(f"- Present ({counts}); freshness unknown.")
        elif index_sha.startswith(head) or head.startswith(index_sha):
            if worktree_code:
                out += [
                    f"- STALE: {len(worktree_code)} uncommitted code file(s) changed after `{index_sha}`.",
                    "  Rebuild before trusting call paths:",
                    f"  `python {tools}/build_code_index.py --root .`",
                ]
            else:
                out.append(f"- Current with HEAD ({counts}).")
        else:
            code_files = code_files_since(root, index_sha)
            if code_files:
                out += [
                    f"- STALE: {len(code_files)} code file(s) changed since `{index_sha}`.",
                    "  Rebuild before trusting call paths:",
                    f"  `python {tools}/build_code_index.py --root .`",
                ]
            else:
                out.append(f"- Built at `{index_sha}`; no code changed since ({counts}).")
        out.append(f"- Query it with `python {tools}/explore.py --symbol <name>` before grepping.")
    out.append("")

    out += ["## Session Brief", ""]
    if not brief:
        out.append("- Missing. Cannot anchor the session goal -- ask the user for it.")
    else:
        for heading in ("Original Goal", "Active Task", "Current State"):
            value = first_value(brief, heading)
            out.append(f"- {heading}: {value or '(empty)'}")
        constraints = real_items(section_body(brief, "Constraints"))
        if constraints:
            out.append("- Constraints:")
            for line in constraints[:8]:
                out.append(f"    {line}")
        else:
            out.append("- Constraints: none recorded (still unfilled template text).")
    out.append("")

    out += ["## Current Task", ""]
    if not task:
        out.append("- No `CURRENT_TASK.md`. Create one when a multi-step task begins.")
    else:
        for heading in ("Original Goal", "Next Concrete Step"):
            value = first_value(task, heading)
            out.append(f"- {heading}: {value or '(empty)'}")
        entries = real_items(section_body(task, "Ruled Out / Already Tried"))
        out.append(f"- Ruled out so far: {len(entries)} item(s) -- do not retry these.")
        for line in entries[:8]:
            out.append(f"    {line}")
        pending = real_items(section_body(task, "Open Questions Awaiting User"))
        if pending:
            out.append(f"- BLOCKED on {len(pending)} unanswered question(s):")
            for line in pending[:5]:
                out.append(f"    {line}")
    out.append("")

    out += ["## Unfilled Placeholders", ""]
    total = 0
    for label, text in (("SESSION_BRIEF.md", brief), ("PROJECT_CONTEXT_CARD.md", card), ("CURRENT_TASK.md", task)):
        if not text:
            continue
        count = count_placeholders(text)
        total += count
        out.append(f"- {label}: {count}")
    if total:
        out.append(
            "- These are template blanks, not facts. Ask the user rather than "
            "inferring values for them."
        )
    else:
        out.append("- None detected.")
    out.append("")

    out += ["## Implementation Log", ""]
    if not log:
        out.append("- Missing or empty.")
    else:
        entries = split_entries(log)
        out.append(f"- {len(entries)} entry/entries, {len(log.splitlines())} lines.")
        if len(entries) > log_keep:
            out += [
                f"- Over the rotation threshold ({log_keep}). Rotate before it becomes a context cost:",
                "",
                "```bash",
                f"python {tools}/summarize_implementation_log.py --log _agent_ops/IMPLEMENTATION_LOG.md \\",
                f"    --rotate --keep {log_keep} --output _agent_ops/LOG_SUMMARY.md --force",
                "```",
            ]
        else:
            out.append("- Under the rotation threshold. Read `LOG_SUMMARY.md` first if present.")
    out.append("")

    out += [
        "## Reminder",
        "",
        "This output covers the mechanical checks only. Still owed to the user:",
        "the Session Receipt, the routing decision, the token/risk level, and at",
        "most one clarifying question. If Session Continuity says CONTINUATION,",
        "read the handoff before any of that. Managed-session permission covers",
        "`_agent_ops/` only -- never source, config, or git.",
        "",
    ]
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print deterministic managed-session start checks. Read-only."
    )
    parser.add_argument("--root", default=".", help="Target project root.")
    parser.add_argument("--ops-folder", default="_agent_ops", help="Ops folder name.")
    parser.add_argument(
        "--log-keep",
        type=int,
        default=ROTATE_THRESHOLD,
        help="Entry count above which log rotation is suggested.",
    )
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        parser.error(f"Root must be an existing directory: {root}")

    print(render(root, root / args.ops_folder, max(args.log_keep, 1)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

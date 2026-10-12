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
import sys
from pathlib import Path

# Running a tool must never leave __pycache__ inside someone else's repository.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_context_card import git_value  # noqa: E402
from ops_identity import (  # noqa: E402
    FOREIGN,
    LEGACY,
    OWNED,
    UNBOUND,
    UNVERIFIABLE,
    Verdict,
    assess,
    init_command_hint,
    owner_summary,
    reason_lines,
)
from scan_deps import tool_prefix  # noqa: E402
from session_state import (  # noqa: E402,F401  (closure_check imports first_value from here)
    continuity_block,
    count_placeholders,
    first_value,
    has_real_content,
    is_placeholder_only,
    open_questions,
    real_items,
    section_body,
    task_status,
)
from source_state import (  # noqa: E402
    index_source_fingerprint,
    is_project_code as source_is_project_code,
    resolve_ops_dir,
)
from summarize_implementation_log import split_entries  # noqa: E402


ROTATE_THRESHOLD = 12


def is_project_code(path: str, root: Path | None = None) -> bool:
    """A changed file that should make the code map look stale.

    Excludes the agent's own folder: `_agent_ops/tools/` holds copies of these
    very scripts, and counting them made a fresh install report nine changed
    "code files" the moment the ops folder was committed.
    """
    return source_is_project_code(path, root)


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
    return sorted(path for path in paths if is_project_code(path, root))


def code_files_since(root: Path, stamp: str) -> list[str]:
    """Committed and working-tree project code newer than a map/index stamp."""
    committed = git_changed_paths(root, ["diff", "--name-only", f"{stamp}..HEAD"])
    combined = {path for path in committed if is_project_code(path, root)}
    combined.update(working_tree_code_files(root))
    return sorted(combined)


def read_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def commit_exists(root: Path, sha: str) -> bool:
    if not sha or sha.startswith("<"):
        return False
    # `rev-parse --verify` echoes the resolved SHA, so a successful check yields
    # non-empty stdout. `cat-file -e` succeeds silently and would be read as a
    # failure by git_value().
    return git_value(root, ["rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}"]) != "not available"


def pack_stamp(ops: Path) -> str:
    """Revision of the workspace pack this project runs, when it is namespaced.

    A project that cannot name its pack revision cannot tell whether a bug fixed
    upstream is still live in its own copy.
    """

    stamp = ops.parent / "PACK_VERSION"
    if not stamp.is_file():
        return ""
    for line in stamp.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("version:"):
            return line.split(":", 1)[1].strip()
    return ""


def unproven_section(verdict: Verdict, root: Path, ops: Path) -> list[str]:
    """Memory whose owner is not established: none of it is to be read as fact.

    FOREIGN, UNVERIFIABLE (including an unreadable or incomplete stamp) and
    LEGACY (no stamp) all stop here, differing only in wording. A swapped-in
    agent that resumed another project's "task in progress" -- or one nobody can
    vouch for -- would act on rules and decisions that were never this project's.
    The caller prints nothing from the records after this block.
    """

    reset = init_command_hint(root, ops, "--reset-memory")
    claim = init_command_hint(root, ops, "--claim-memory")
    plain = init_command_hint(root, ops, "").strip()
    headline = {
        FOREIGN: "This ops folder does not belong to this repository.",
        UNVERIFIABLE: "**UNVERIFIED.** This memory's owner cannot be established from this checkout.",
        LEGACY: "**UNSTAMPED (legacy).** Memory exists but has no ownership stamp, so its owner is unproven"
        + (" and it looks like the workspace pack's own memory." if verdict.suspect else "."),
    }[verdict.state]
    out = [
        f"## !! {'FOREIGN' if verdict.foreign_like else 'UNVERIFIED'} PROJECT MEMORY -- DO NOT RESUME !!",
        "",
        f"- {headline}",
        *reason_lines(verdict),
        "- Do NOT resume its task, brief, handoff or context card, and do not treat its decisions,",
        "  risks, Repo Map or rules as this project's. The sections that read them are skipped below.",
        "- Ask the user which they want, then run one (nothing is lost: --reset-memory backs up every file first):",
        f"    {reset}   # back up every file under the ops folder's backups/, start from fresh templates",
        f"    {claim}   # these records ARE this project's (for example after a git history rewrite)",
    ]
    if verdict.state == LEGACY:
        out.append(f"- If every record is still an untouched template, `{plain}` stamps the folder with no flag.")
    return out + [""]


def ownership_section(verdict: Verdict, root: Path, ops: Path) -> list[str]:
    """Whose memory this is, stated before any of it is believed."""

    if verdict.unproven:
        return unproven_section(verdict, root, ops)
    if verdict.state == OWNED:
        lines = [f"- Owned by this project ({owner_summary(verdict.stamp)})."]
    elif verdict.state == UNBOUND:
        lines = [
            "- Owned by this project, but its stamp was made before the first commit, so it names no root commit.",
            f"- Bind it once history exists: `{init_command_hint(root, ops, '').strip()}`",
        ]
    else:
        lines = ["- No project memory recorded yet."]
    return ["## Memory Ownership", "", *lines, ""]


def current_task_section(task: str) -> list[str]:
    """The task record, read through its declared Status.

    A completed task still has a "Next Concrete Step" and open-looking sections;
    printing them as live instructions sent the next session back into finished
    work. Only a task that is not done keeps its dead-end list and blockers.
    """

    out = ["## Current Task", ""]
    if not task:
        return out + ["- No `CURRENT_TASK.md`. Create one when a multi-step task begins.", ""]
    state = task_status(task)
    out.append(
        f"- Status: {state}"
        if state
        else "- Status: not recorded (file predates the Status field) -- treat its state as unverified."
    )
    out.append(f"- Original Goal: {first_value(task, 'Original Goal') or '(empty)'}")
    pending = open_questions(task)
    if state in ("complete", "idle"):
        out.append(f"- Task is {state}: its Next Concrete Step and Ruled Out list are history, not instructions.")
        if pending:
            out.append(f"- {len(pending)} open question(s) are still listed on a {state} task; likely stale.")
        return out + [""]
    out.append(f"- Next Concrete Step: {first_value(task, 'Next Concrete Step') or '(empty)'}")
    entries = real_items(section_body(task, "Ruled Out / Already Tried"))
    out.append(f"- Ruled out so far: {len(entries)} item(s) -- do not retry these.")
    out += [f"    {line}" for line in entries[:8]]
    if pending:
        out.append(f"- BLOCKED on {len(pending)} unanswered question(s):")
        out += [f"    {line}" for line in pending[:5]]
    return out + [""]


def render(root: Path, ops: Path, log_keep: int) -> str:
    tools = tool_prefix(root)
    try:
        ops_reference = ops.relative_to(root).as_posix()
    except ValueError:
        ops_reference = str(ops)
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
    # Two different questions, and they were conflated. `rev-parse HEAD` fails
    # in a repository whose first commit does not exist yet, so a brand-new
    # project was reported as "not a git repository" and silently lost its file
    # listing, its source fingerprint, and every staleness check on the one
    # session where the map is built.
    is_git = git_value(root, ["rev-parse", "--is-inside-work-tree"]) == "true"
    has_commits = is_git and head != "not available"
    change_sets = (
        {
            "unstaged": {
                path for path in git_changed_paths(root, ["diff", "--name-only"]) if is_project_code(path, root)
            },
            "staged": {
                path
                for path in git_changed_paths(root, ["diff", "--cached", "--name-only"])
                if is_project_code(path, root)
            },
            "untracked": {
                path
                for path in git_changed_paths(root, ["ls-files", "--others", "--exclude-standard"])
                if is_project_code(path, root)
            },
        }
        if is_git
        else {"unstaged": set(), "staged": set(), "untracked": set()}
    )
    worktree_code = sorted(change_sets["unstaged"] | change_sets["staged"] | change_sets["untracked"])
    source_fingerprint = index_source_fingerprint(root) if is_git else ""

    out: list[str] = ["# Session Start (deterministic checks)", ""]

    out += ["## Repository", ""]
    if is_git:
        dirty = [line for line in status.splitlines() if line.strip()] if status != "not available" else []
        out += [
            f"- Root: `{root}`",
            f"- Branch: `{branch}`",
            f"- HEAD: `{head}`" if has_commits else "- HEAD: none yet (no commits in this repository)",
            f"- Uncommitted changes: {len(dirty)} file(s)",
        ]
        for line in dirty[:15]:
            out.append(f"    {line}")
        if len(dirty) > 15:
            out.append(f"    ... {len(dirty) - 15} more")
    else:
        out.append(f"- Root: `{root}` (not a git repository -- no delta or staleness checks)")
    if ops_reference.endswith("/_agent_ops"):
        installed = pack_stamp(ops)
        pack_folder = ops_reference[: -len("/_agent_ops")]
        out.append(
            f"- Workspace pack: `{pack_folder}` at version `{installed}`"
            if installed
            else f"- Workspace pack: `{pack_folder}`, version unknown (no PACK_VERSION). "
            "Refresh it with `embed_pack.py --target . --update` from a source pack."
        )
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
            f"tools into `{ops_reference}/tools/`, and everything after it runs from the",
            "project with no pack present.",
            "",
        ]
        return "\n".join(out).rstrip() + "\n"

    verdict = assess(root, ops)
    out += ownership_section(verdict, root, ops)
    if verdict.unproven:
        # Every section below reads memory nobody has vouched for; "TASK IN
        # PROGRESS" and "Resume from its Next Concrete Step" under an UNVERIFIED
        # banner would contradict it. Read-only: the user picks the init flag.
        return "\n".join(out).rstrip() + "\n"

    out += continuity_block(brief, task, handoff)

    out += ["## Memory Freshness", ""]
    verified = first_value(brief, "Last Verified Commit")
    if not is_git:
        out.append("- Skipped: not a git repository.")
    elif not has_commits:
        out.append("- Skipped: no commits yet, so there is nothing to verify memory against.")
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
            f"python {tools}/generate_repo_map.py --root . --output {ops_reference}/REPO_MAP.md --force",
            "```",
        ]
    else:
        map_sha = first_value(repo_map, "Last Verified Commit")
        map_fingerprint = first_value(repo_map, "Indexed Source Fingerprint")
        if map_fingerprint and map_fingerprint != "not available" and source_fingerprint:
            if map_fingerprint != source_fingerprint:
                out += [
                    "- STALE: the indexed source fingerprint differs from REPO_MAP.md.",
                    "  Regenerate with --force before trusting the module table.",
                ]
            elif change_sets["unstaged"] or change_sets["untracked"]:
                outside_index = change_sets["unstaged"] | change_sets["untracked"]
                out += [
                    f"- STALE: {len(outside_index)} code file(s) changed outside the Git index.",
                    "  Regenerate after staging, or keep the map out of this pending source state.",
                ]
            elif change_sets["staged"]:
                out.append("- Current with the staged source index; ready for the pending commit.")
            else:
                out.append(
                    f"- Current with indexed source state at HEAD ({head})."
                    if has_commits
                    else "- Current with the staged source index; no commits yet."
                )
        elif not has_commits or not commit_exists(root, map_sha):
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
        index_fingerprint = str(index.get("index_source_fingerprint", ""))
        counts = f"{len(index.get('symbols', {}))} symbols, {len(index.get('edges', []))} edges"
        if index_fingerprint and source_fingerprint:
            if index_fingerprint != source_fingerprint:
                out += [
                    "- STALE: the indexed source fingerprint differs from code_index.json.",
                    "  Rebuild before trusting call paths:",
                    f"  `python {tools}/build_code_index.py --root .`",
                ]
            elif change_sets["unstaged"] or change_sets["untracked"]:
                outside_index = change_sets["unstaged"] | change_sets["untracked"]
                out += [
                    f"- STALE: {len(outside_index)} code file(s) changed outside the Git index.",
                    "  Rebuild after staging before trusting call paths.",
                ]
            elif change_sets["staged"]:
                out.append(f"- Current with the staged source index ({counts}); commit pending.")
            else:
                out.append(f"- Current with indexed source state ({counts}).")
        elif not has_commits or not commit_exists(root, index_sha):
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

    out += current_task_section(task)

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
                f"python {tools}/summarize_implementation_log.py --log {ops_reference}/IMPLEMENTATION_LOG.md \\",
                f"    --rotate --keep {log_keep} --output {ops_reference}/LOG_SUMMARY.md --force",
                "```",
            ]
        else:
            out.append("- Under the rotation threshold. Read `LOG_SUMMARY.md` first if present.")
    out.append("")

    out += [
        "## Durable Recordkeeping Gate",
        "",
        "Before a meaningful completion report, classify the work actually done,",
        "not the task prompt's file list. Implementation, test, audit, gate, or",
        "verification evidence requires an implementation-log entry; durable",
        "phase/milestone state requires a project-context update; material",
        "trade-offs require a decision entry. Write triggered records before the",
        "Closure Receipt. A missing filename is never a not-needed reason.",
        "For an authorized source commit, stage source after tests, then run the",
        "repo-map refresh helper with --stage before git commit. Do not bypass an",
        "installed managed hook with --no-verify.",
        "",
    ]

    out += [
        "## Reminder",
        "",
        "This output covers the mechanical checks only. Still owed to the user:",
        "the Session Receipt, the routing decision, the token/risk level, and at",
        "most one clarifying question. If Session Continuity says CONTINUATION,",
        "read the handoff before any of that. Managed-session permission covers",
        f"`{ops_reference}/` only -- never source, config, or git.",
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

    print(render(root, resolve_ops_dir(root, args.ops_folder), max(args.log_keep, 1)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Read-only draft of the Closure Receipt (see SESSION_PROTOCOL.md).

Detects project code changed since `Last Verified Commit` and which `_agent_ops/`
records were touched, then prints one receipt row per ops file. Rows it can
prove are filled in; rows that need judgment say `decide:`. Advisory only: the
receipt is still the agent's statement of what it actually wrote. Writes nothing.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from session_start import first_value, read_text  # noqa: E402
from source_state import code_change_sets, git_changed_paths, is_project_code, resolve_ops_dir  # noqa: E402

# Receipt order -> hint shown on a `decide:` row (names the trigger to look for).
RECORDS = {
    "CURRENT_TASK.md": "not needed (no task state to keep) | updated (files touched, next step)",
    "IMPLEMENTATION_LOG.md": "not needed (no implementation/test/audit/verification evidence)",
    "SESSION_BRIEF.md": "not needed (no state or commit change) | Last Verified Commit -> <sha>",
    "PROJECT_CONTEXT_CARD.md": "not needed (no milestone or durable state change)",
    "DECISION_LOG.md": "not needed (no trade-off) | DEC-00NN added",
    "RISK_REGISTER.md": "not needed (no new risk) | RISK-00NN added/changed",
    "REPO_MAP.md": "not needed (no code change) | regenerate via refresh_repo_map.py --stage",
}


def git(root: Path, *args: str) -> tuple[int, str]:
    result = subprocess.run(["git", *args], cwd=str(root), text=True, capture_output=True, check=False)
    return result.returncode, result.stdout.strip()


def resolve_since(root: Path, wanted: str) -> str:
    """A verifiable commit id: the requested one if it exists, otherwise HEAD."""
    token = wanted.split()[0] if wanted.split() else ""
    if token:
        code, out = git(root, "rev-parse", "--verify", "--quiet", f"{token}^{{commit}}")
        if code == 0 and out:
            return out
    return git(root, "rev-parse", "HEAD")[1]


def ops_change(root: Path, rel: str, since: str, since_time: int) -> str:
    """How an ops file changed: 'git', 'untracked', 'mtime', or '' when untouched/absent."""
    if git_changed_paths(root, ["diff", "--name-only", "--relative", f"{since}..HEAD", "--", rel]):
        return "git"
    status = git(root, "status", "--porcelain", "--", rel)[1]
    if status:  # `??` is a file git has never seen: it cannot prove this task's record
        return "untracked" if status.startswith("??") else "git"
    path = root / rel
    if path.is_file() and git(root, "check-ignore", "-q", rel)[0] == 0 and int(path.stat().st_mtime) > since_time:
        return "mtime"
    return ""


def record_row(name: str, change: str, present: bool, code: set, committed: set, since: str) -> str:
    """One receipt cell. Required records (log, brief) are judged before 'file absent'."""
    required = name in ("IMPLEMENTATION_LOG.md", "SESSION_BRIEF.md")
    if code and required and not present:
        return f"MISSING: project code changed ({len(code)} files) but {name} is absent"
    if change == "untracked" and code and name == "IMPLEMENTATION_LOG.md":
        return f"MISSING: project code changed ({len(code)} files) (log untracked: commit the ops folder or confirm)"
    if change == "untracked":
        return "decide: ops file is untracked/new; confirm it holds this task's record"
    if change == "mtime":  # a timestamp proves a write, not that the write records this task
        return f"unverified: modified after {since[:12]} (mtime only, gitignored) -- confirm it records this task"
    if change:
        return "updated (detected)"
    if not present:
        return "decide: file absent from the ops folder"
    if code and name == "IMPLEMENTATION_LOG.md":
        return f"MISSING: project code changed ({len(code)} files) but log untouched"
    if code and name == "SESSION_BRIEF.md":
        return "MISSING: project code changed but SESSION_BRIEF.md untouched"
    if committed and name == "REPO_MAP.md":
        return "MISSING: project code committed but REPO_MAP.md not regenerated"
    if code and name == "REPO_MAP.md":
        return "decide: code uncommitted -> regenerate via refresh_repo_map.py --stage at commit"
    return "decide: " + RECORDS[name]


def build_rows(root: Path, ops: Path, since: str) -> tuple[list[str], str]:
    sets = code_change_sets(root)
    committed = {p for p in git_changed_paths(root, ["diff", "--name-only", f"{since}..HEAD"]) if is_project_code(p, root)}
    working = set().union(*sets.values())
    code = committed | working
    code_time = git(root, "show", "-s", "--format=%ct", since)[1]
    since_time = int(code_time) if code_time.isdigit() else 0
    ops_rel = ops.relative_to(root).as_posix() if ops.is_relative_to(root) else ops.as_posix()
    rows = []
    for name in RECORDS:
        change = ops_change(root, f"{ops_rel}/{name}", since, since_time)
        cell = record_row(name, change, (ops / name).is_file(), code, committed, since)
        rows.append(f"- {name:<23}: {cell}")
    header = f"since {since[:12]} | code changed: {len(committed)} committed, {len(working)} uncommitted"
    return rows, header


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--since", default="", help="base commit (default: Last Verified Commit, else HEAD)")
    parser.add_argument("--strict", action="store_true", help="exit 2 when any row is MISSING")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    ops = resolve_ops_dir(root)
    if not ops.is_dir() or git(root, "rev-parse", "--git-dir")[0] != 0:
        print(f"closure_check: needs a git repo with an ops folder under {root}", file=sys.stderr)
        return 1
    wanted = args.since or first_value(read_text(ops / "SESSION_BRIEF.md"), "Last Verified Commit")
    rows, header = build_rows(root, ops, resolve_since(root, wanted))
    print("Closure Receipt (draft from closure_check.py -- fill every \"decide\" row)")
    print(header)
    print("\n".join(rows))
    return 2 if args.strict and any(": MISSING" in row for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())

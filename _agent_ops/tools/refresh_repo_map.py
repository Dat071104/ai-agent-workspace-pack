#!/usr/bin/env python3
"""Refresh code-navigation artifacts for a pending source commit.

This helper is intentionally commit-aware rather than a filesystem watcher.
It rebuilds once only when staged project code exists, rejects unstaged or
untracked code that would make the generated map disagree with the commit, and
stages only the generated REPO_MAP.md when requested.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


sys.dont_write_bytecode = True
TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))

from source_state import code_change_sets, git_changed_paths, resolve_ops_dir  # noqa: E402


def run(command: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def print_result(result: subprocess.CompletedProcess[str]) -> None:
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh code index and REPO_MAP.md for staged project-code changes."
    )
    parser.add_argument("--root", default=".", help="Git project root.")
    parser.add_argument(
        "--stage",
        action="store_true",
        help="Stage only the active ops folder's REPO_MAP.md after a successful refresh.",
    )
    parser.add_argument("--ops-folder", default="_agent_ops", help="Project operations folder.")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        parser.error(f"Root must be an existing directory: {root}")
    if run(["git", "rev-parse", "--is-inside-work-tree"], root).returncode != 0:
        print("BLOCKED: repo-map commit refresh requires a Git work tree.", file=sys.stderr)
        return 2

    changes = code_change_sets(root)
    staged = sorted(changes["staged"])
    if not staged:
        print("SKIP: no staged project-code changes; REPO_MAP.md remains valid for this commit.")
        return 0

    unmerged = sorted(git_changed_paths(root, ["diff", "--name-only", "--diff-filter=U"]))
    outside_index = sorted(changes["unstaged"] | changes["untracked"])
    if unmerged or outside_index:
        print(
            "BLOCKED: staged code cannot be mapped safely while source differs outside the Git index.",
            file=sys.stderr,
        )
        for path in unmerged:
            print(f"  unmerged: {path}", file=sys.stderr)
        for path in outside_index:
            print(f"  outside-index code: {path}", file=sys.stderr)
        print(
            "Stage or remove those code changes, then retry the commit. No map was written.",
            file=sys.stderr,
        )
        return 2

    ops_dir = resolve_ops_dir(root, args.ops_folder)
    map_path = ops_dir / "REPO_MAP.md"
    index_path = ops_dir / "code_index.json"
    required_tools = (TOOLS_DIR / "build_code_index.py", TOOLS_DIR / "generate_repo_map.py")
    if not ops_dir.is_dir() or not all(path.is_file() for path in required_tools):
        print(
            "BLOCKED: agent-ops tools are incomplete. Initialize or refresh agent ops before committing code.",
            file=sys.stderr,
        )
        return 2

    index_result = run(
        [
            sys.executable,
            "-B",
            str(TOOLS_DIR / "build_code_index.py"),
            "--root",
            str(root),
            "--output",
            str(index_path),
            "--quiet",
        ],
        root,
    )
    if index_result.returncode != 0:
        print("BLOCKED: code index refresh failed; commit stopped.", file=sys.stderr)
        print_result(index_result)
        return index_result.returncode or 1

    map_result = run(
        [
            sys.executable,
            "-B",
            str(TOOLS_DIR / "generate_repo_map.py"),
            "--root",
            str(root),
            "--output",
            str(map_path),
            "--index",
            str(index_path),
            "--force",
        ],
        root,
    )
    if map_result.returncode != 0:
        print("BLOCKED: REPO_MAP.md refresh failed; commit stopped.", file=sys.stderr)
        print_result(map_result)
        return map_result.returncode or 1

    if args.stage:
        map_relative = map_path.relative_to(root).as_posix()
        stage_result = run(["git", "add", "--", map_relative], root)
        if stage_result.returncode != 0:
            print("BLOCKED: generated REPO_MAP.md could not be staged; commit stopped.", file=sys.stderr)
            print_result(stage_result)
            return stage_result.returncode or 1

    print(f"UPDATED: code index + {map_path.relative_to(root).as_posix()} for {len(staged)} staged code file(s).")
    if args.stage:
        print(f"STAGED: {map_path.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

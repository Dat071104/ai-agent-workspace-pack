#!/usr/bin/env python3
"""Shared Git-index source-state helpers for repo-map freshness.

The map and symbol index are generated from the working tree, but a pre-commit
refresh must describe the staged source that will enter the commit.  A compact
fingerprint of Git's index makes that state verifiable after the commit, when
the commit hash itself was not knowable while the pre-commit hook ran.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


CODE_SUFFIXES = (
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".rb",
    ".php",
    ".cs",
)


def normalize_path(path: str) -> str:
    return path.strip().replace("\\", "/")


def is_project_code(path: str) -> bool:
    """True when a changed path should invalidate code-navigation artifacts."""

    cleaned = normalize_path(path)
    if cleaned.startswith("_agent_ops/") or "/_agent_ops/" in cleaned:
        return False
    return cleaned.endswith(CODE_SUFFIXES)


def git_changed_paths(root: Path, args: list[str]) -> set[str]:
    """Normalized paths from one Git listing command, or an empty set on error."""

    result = subprocess.run(
        ["git", *args],
        cwd=str(root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return set()
    return {normalize_path(line) for line in result.stdout.splitlines() if line.strip()}


def code_change_sets(root: Path) -> dict[str, set[str]]:
    """Project-code changes separated by their Git state."""

    return {
        "unstaged": {
            path for path in git_changed_paths(root, ["diff", "--name-only"]) if is_project_code(path)
        },
        "staged": {
            path
            for path in git_changed_paths(root, ["diff", "--cached", "--name-only"])
            if is_project_code(path)
        },
        "untracked": {
            path
            for path in git_changed_paths(root, ["ls-files", "--others", "--exclude-standard"])
            if is_project_code(path)
        },
    }


def index_source_fingerprint(root: Path) -> str:
    """Stable fingerprint of stage-0 project-code blobs in Git's index.

    Empty means the source state cannot be trusted, for example outside a Git
    repository or during an unresolved merge.  The staged blob IDs avoid reading
    every source file at every session start.
    """

    result = subprocess.run(
        ["git", "ls-files", "--stage", "-z"],
        cwd=str(root),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return ""

    entries: list[tuple[str, str]] = []
    for record in result.stdout.split(b"\0"):
        if not record or b"\t" not in record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        fields = metadata.split()
        if len(fields) != 3:
            continue
        _, raw_blob, raw_stage = fields
        path = normalize_path(raw_path.decode("utf-8", errors="surrogateescape"))
        if not is_project_code(path):
            continue
        if raw_stage != b"0":
            return ""
        entries.append((path, raw_blob.decode("ascii", errors="ignore")))

    digest = hashlib.sha256()
    for path, blob in sorted(entries):
        digest.update(path.encode("utf-8", errors="surrogateescape"))
        digest.update(b"\0")
        digest.update(blob.encode("ascii"))
        digest.update(b"\n")
    return f"sha256:{len(entries)}:{digest.hexdigest()}"

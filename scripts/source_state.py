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
DEFAULT_OPS_FOLDER = "_agent_ops"
NAMESPACED_PACK_FOLDER = "ai-agent-workspace-pack"
EMBEDDED_PACK_MARKERS = ("TEAM_ROUTER.md", "core-context", "scripts/init_project_ops.py")


def normalize_path(path: str) -> str:
    return path.strip().replace("\\", "/")


def is_project_code(path: str, root: Path | None = None) -> bool:
    """True when a changed path should invalidate code-navigation artifacts."""

    cleaned = normalize_path(path)
    if cleaned.startswith(f"{DEFAULT_OPS_FOLDER}/") or f"/{DEFAULT_OPS_FOLDER}/" in cleaned:
        return False
    if root and cleaned.startswith(f"{NAMESPACED_PACK_FOLDER}/"):
        pack_root = root / NAMESPACED_PACK_FOLDER
        if all((pack_root / marker).exists() for marker in EMBEDDED_PACK_MARKERS):
            return False
    return cleaned.endswith(CODE_SUFFIXES)


def resolve_ops_dir(root: Path, ops_folder: str = DEFAULT_OPS_FOLDER) -> Path:
    """Locate project operations, including a copied namespaced pack.

    A runtime tool lives at ``<ops>/tools/``. When the caller uses the normal
    default but the root has no ``_agent_ops/``, that location is the only
    safe, unambiguous fallback for an embedded installation.
    """

    requested = root / ops_folder
    if ops_folder != DEFAULT_OPS_FOLDER or requested.exists():
        return requested
    installed = Path(__file__).resolve().parent.parent
    try:
        installed.relative_to(root)
    except ValueError:
        return requested
    return installed if installed.name == DEFAULT_OPS_FOLDER else requested


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
        if not is_project_code(path, root):
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


def worktree_is_clean(root: Path) -> bool | None:
    """True/False inside a Git repository, None when there is no repository.

    A tool that overwrites or moves files in someone else's project uses this to
    refuse when the change would not be revertible.
    """

    inside = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=str(root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return None
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return status.returncode == 0 and not status.stdout.strip()

#!/usr/bin/env python3
"""The single definition of what a pack install ships, and the record of it.

Install, `--update` and migrate all answer "which files are the pack's?" from
here. Before this module each answered it by copying everything that was not on
a short denylist, so a developer's local `.env`, virtualenv or editor state in
the source checkout landed inside every host project.

Two layers, both required:

* an allowlist of top-level pack entries -- anything new at the top of the
  source checkout is NOT shipped until someone decides it should be;
* inside the allowlist, only Git-tracked files when the source is a Git
  repository, so ignored or untracked local files never travel. Without Git the
  allowlist is combined with an explicit denylist of known local-state names.

`PACK_MANIFEST.json` records what an install wrote (path -> sha256). It is the
proof of ownership that lets a later `--update` remove a file the pack no longer
ships without ever guessing from a file name.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


sys.dont_write_bytecode = True

MANIFEST_FILE = "PACK_MANIFEST.json"
STAMP_FILE = "PACK_VERSION"
MANIFEST_SCHEMA = 1

# Shipped, and why each one:
#   root documents   -- the agent entry points, router and human guide
#   *-team/          -- the nine team playbooks the router dispatches to
#   commands/        -- the `@command` definitions START_HERE.md points at
#   core-context/    -- templates init_project_ops.py reads to build _agent_ops/
#   harness/         -- checklists/matrices the teams cite
#   scripts/         -- init_project_ops.py and the runtime tools it copies
#   .claude/.codex   -- ONLY the adapter sources init installs at the host root
#                       (not settings.local.json, worktrees or other local state)
SHIPPED_ROOT_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "BOOTSTRAP.md",
    "START_HERE.md",
    "TEAM_ROUTER.md",
    "README.md",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    # Scoped to the pack folder it sits in; keeps tool bytecode out of commits.
    ".gitignore",
)
SHIPPED_TREES = (
    "advisor-team",
    "analyze-team",
    "bug-fix-team",
    "build-team",
    "clean-code-team",
    "handoff-team",
    "prompting-team",
    "repo-hygiene-team",
    "tester-team",
    "commands",
    "core-context",
    "harness",
    "scripts",
    ".claude/README.md",
    ".claude/agents",
    ".claude/skills",
    ".codex/config.toml",
    ".codex/agents",
)
# Deliberately NOT shipped: `tests/` (a host's `pytest` would collect the pack's
# own suite), `examples/` (illustrations, never read at runtime -- the only
# mention is a directory listing in README.md), `_agent_ops/` (the SOURCE's
# working memory, never a host's starting memory).
NOT_SHIPPED_TOP_LEVEL = ("tests", "examples", "_agent_ops")

DENIED_DIRS = {
    ".git", "_agent_ops", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".tox", ".venv", "venv", "node_modules", ".idea", ".vscode", ".update-backup",
    "worktrees",  # .claude/worktrees: other checkouts of this very repository
}
DENIED_PATTERNS = (
    "*.pyc", "*.pyo", "*.pem", "*.key", "*.crt", "*.p12", "*.pfx", "*.log", "*.sqlite",
    "*.sqlite3", "*.db", "*.swp", "*~", ".DS_Store", "Thumbs.db", "desktop.ini",
    "settings.local.json", STAMP_FILE, MANIFEST_FILE,
)
# `.env.example` documents variables and is meant to be shared; every other
# dotenv file may hold real values.
DOTENV_SAFE = {".env.example", ".env.sample", ".env.template"}

_MANAGED_BLOCK = re.compile(
    r"<!-- AI_AGENT_WORKSPACE_PACK:BEGIN (v\d+) -->.*?<!-- AI_AGENT_WORKSPACE_PACK:END \1 -->",
    re.DOTALL,
)


def is_denied(rel: str) -> bool:
    """True for local state that must never ship, whatever tracks it."""

    parts = rel.split("/")
    # Every component, the last one too: in a git worktree or submodule `.git`
    # is a FILE pointing at the real repository, and shipping it would make the
    # host's pack folder an alias of the source's repository.
    if any(part.lower() in DENIED_DIRS for part in parts):
        return True
    name = parts[-1]
    lowered = name.lower()
    if lowered.startswith(".env") and lowered not in DOTENV_SAFE:
        return True
    return any(fnmatch.fnmatchcase(lowered, pattern.lower()) for pattern in DENIED_PATTERNS)


def is_allowlisted(rel: str) -> bool:
    return rel in SHIPPED_ROOT_FILES or any(
        rel == entry or rel.startswith(entry + "/") for entry in SHIPPED_TREES
    )


def _same_path(left: str | Path, right: str | Path) -> bool:
    try:
        return os.path.samefile(left, right)
    except OSError:
        return False


def _git(source: Path, args: list[str], *, text: bool = False):
    """Run git in `source`; None when git cannot run or exits non-zero.

    A failure is never reported as empty output: callers treat "git said there
    is nothing" and "git could not answer" differently.
    """

    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(source),
            text=text,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return None
    return result.stdout if result.returncode == 0 else None


def _git_lines(source: Path, args: list[str]) -> list[str] | None:
    output = _git(source, [*args, "-z"])
    if output is None:
        return None
    return [raw.decode("utf-8", errors="surrogateescape") for raw in output.split(b"\0") if raw]


def is_git_root(source: Path) -> bool:
    """True only when `source` IS a repository's top level.

    A pack copied into a host project sits inside the HOST's repository: there
    `git ls-files` describes the host, and `rev-parse HEAD` would stamp the
    host's commit as the pack's revision.
    """

    top = _git(source, ["rev-parse", "--show-toplevel"], text=True)
    return bool(top and top.strip()) and _same_path(top.strip(), source)


def git_tracked(source: Path) -> set[str] | None:
    """Paths in the index of a source that is its own repository, else None.

    The two empty answers differ: an empty `set()` means Git is usable and
    tracks nothing (so nothing ships by the tracked rule), while None means there
    is no repository of the source's own to ask, so the denylist fallback applies.
    """

    if not is_git_root(source):
        return None
    names = _git_lines(source, ["ls-files"])
    if names is None:
        return None
    return {name.replace("\\", "/") for name in names}


def _walk(source: Path) -> set[str]:
    found: set[str] = set()
    for current, dirs, files in os.walk(source):
        # Prune denied directories instead of listing a whole virtualenv.
        dirs[:] = [name for name in dirs if name.lower() not in DENIED_DIRS]
        for name in files:
            found.add((Path(current) / name).relative_to(source).as_posix())
    return found


def local_tree_files(source: Path) -> set[str]:
    """Every non-denied file on disk, tracked or not.

    Migrate uses this wider net: a flat install may hold a file the source has
    only just added, and content proof (not membership here) decides ownership.
    """

    return {rel for rel in _walk(source) if not is_denied(rel)}


def repo_files(source: Path) -> set[str]:
    """Every file the pack's source owns: tracked when Git is usable, else the tree
    minus local-state names. Wider than what ships (it includes tests/examples),
    which is what migrate needs to recognise a legacy flat install."""

    tracked = git_tracked(source)
    candidates = tracked if tracked is not None else _walk(source)
    return {rel for rel in candidates if not is_denied(rel) and (source / rel).is_file()}


def shipping_set(source: Path) -> set[str]:
    """The files an install or update writes into a host, as posix paths."""

    return {rel for rel in repo_files(source) if is_allowlisted(rel)}


def unshipped_untracked(source: Path) -> list[str]:
    """Untracked, non-ignored files inside the allowlist: silently skipped by the
    Git rule, so a new pack file somebody forgot to `git add` must be surfaced."""

    if git_tracked(source) is None:
        return []
    names = _git_lines(source, ["ls-files", "--others", "--exclude-standard"]) or []
    return sorted(
        rel for rel in (name.replace("\\", "/") for name in names)
        if is_allowlisted(rel) and not is_denied(rel)
    )


def strip_managed_blocks(text: str) -> str:
    """Remove generated `AI_AGENT_WORKSPACE_PACK` blocks, keeping every other byte.

    The pack's own AGENTS.md used to carry a block saying "this repository is
    the workspace pack itself". Inside a host that sentence is false and is
    imported by the host's CLAUDE.md every session.
    """

    newline = "\r\n" if "\r\n" in text else "\n"
    while True:
        match = _MANAGED_BLOCK.search(text)
        if not match:
            return text
        before = text[: match.start()].rstrip("\r\n")
        after = text[match.end():].lstrip("\r\n")
        if before and after:
            text = before + newline + newline + after
        elif before:
            text = before + newline
        else:
            text = after


def shipped_bytes(source: Path, rel: str) -> bytes:
    """What the host receives for `rel`: the source bytes, bar the AGENTS.md block."""

    data = (source / rel).read_bytes()
    if rel == "AGENTS.md":
        data = strip_managed_blocks(data.decode("utf-8")).encode("utf-8")
    return data


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_manifest(pack_dir: Path) -> dict[str, str] | None:
    """path -> sha256 of an earlier install, or None when absent or unreadable."""

    path = pack_dir / MANIFEST_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("schema") != MANIFEST_SCHEMA:
        return None
    files = data.get("files")
    if not isinstance(files, dict):
        return None
    return {str(key): str(value) for key, value in files.items()}


def write_manifest(pack_dir: Path, version: str, rels: set[str]) -> None:
    """Record the content now on disk for `rels` (what this install owns).

    Hashed from disk, not from the source: after a copy they are identical, and
    for an in-place install the disk is the only truth. No timestamp, so a
    re-run on an unchanged pack rewrites byte-identical content.
    """

    files = {rel: sha256_file(pack_dir / rel) for rel in sorted(rels) if (pack_dir / rel).is_file()}
    payload = {"schema": MANIFEST_SCHEMA, "pack_version": version, "files": files}
    (pack_dir / MANIFEST_FILE).write_text(
        json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )

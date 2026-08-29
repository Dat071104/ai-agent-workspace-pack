#!/usr/bin/env python3
"""Move a flat workspace-pack install into one namespaced folder.

A flat install unpacked the pack's files directly into the application root,
where they mix with the application's own `scripts/`, `tests/`, and harness
folders. Nothing here deletes anything: every pack file is MOVED into
`<folder>/`, so `git status` shows renames and the whole operation is revertible
with `git checkout`.

Files are matched by their path inside this source pack, never by directory
name. A flat install merged the pack's `scripts/*.py` into the application's own
`scripts/`; moving that whole directory would take the application's code with
it, which is exactly the damage the namespaced layout exists to prevent.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from source_state import looks_like_pack  # noqa: E402
from source_state import worktree_is_clean  # noqa: E402


DEFAULT_FOLDER = "ai-agent-workspace-pack"
EXCLUDED_NAMES = {".git", "_agent_ops", "__pycache__", ".pytest_cache"}
# Entry points and host-shared names are decided by init_project_ops after the
# move, or left alone. `LICENSE`, `.gitignore`, and `README.md` are as likely to
# belong to the application as to the pack, and guessing wrong loses host files.
ROOT_ENTRY_POINTS = {"AGENTS.md", "CLAUDE.md", "GEMINI.md"}
NEVER_MOVED = {"LICENSE", ".gitignore", "README.md"} | ROOT_ENTRY_POINTS
FLAT_BRIDGE_BEGIN = "<!-- AI_AGENT_WORKSPACE_PACK:BEGIN v1 -->"
FLAT_BRIDGE_END = "<!-- AI_AGENT_WORKSPACE_PACK:END v1 -->"


def pack_relative_files(source: Path) -> list[Path]:
    """Every file this pack owns, as paths relative to the pack root."""

    found: list[Path] = []
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        if any(part in EXCLUDED_NAMES for part in relative.parts) or path.suffix == ".pyc":
            continue
        if len(relative.parts) == 1 and relative.name in NEVER_MOVED:
            continue
        found.append(relative)
    return sorted(found)


def strip_flat_bridge(text: str) -> str:
    """Remove the flat managed block, keeping every host-owned line."""

    if FLAT_BRIDGE_BEGIN not in text or FLAT_BRIDGE_END not in text:
        return text
    start = text.index(FLAT_BRIDGE_BEGIN)
    end = text.index(FLAT_BRIDGE_END, start) + len(FLAT_BRIDGE_END)
    return (text[:start].rstrip("\n") + "\n" + text[end:].lstrip("\n")).lstrip("\n")


def plan_moves(target: Path, source: Path, destination: Path) -> list[Path]:
    """Pack-owned files that actually exist in the target, in move order."""

    return [relative for relative in pack_relative_files(source) if (target / relative).is_file()]


def prune_empty_dirs(target: Path, moved: list[Path]) -> list[Path]:
    """Remove directories emptied by the move, deepest first. Never removes files."""

    candidates = {target / relative.parent for relative in moved if relative.parent != Path(".")}
    removed: list[Path] = []
    for directory in sorted(candidates, key=lambda path: len(path.parts), reverse=True):
        while directory != target and directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
            removed.append(directory)
            directory = directory.parent
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Move a flat workspace-pack install into one namespaced folder."
    )
    parser.add_argument("--target", required=True, help="Project directory holding the flat install.")
    parser.add_argument("--folder", default=DEFAULT_FOLDER, help="Destination folder inside the project.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Perform the move. Without it this prints the plan and changes nothing.",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Proceed even though the target worktree has uncommitted changes.",
    )
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.is_dir():
        parser.error(f"Target must be an existing directory: {target}")
    source = Path(__file__).resolve().parents[1]
    if target == source:
        parser.error("Refusing to migrate this pack's own source checkout.")
    if not looks_like_pack(target):
        parser.error(f"No flat workspace-pack install found at {target}")

    destination = target / args.folder
    if destination.exists():
        parser.error(f"Destination already exists; not merged into: {destination}")

    moves = plan_moves(target, source, destination)
    ops = target / "_agent_ops"
    agents = target / "AGENTS.md"
    strips_bridge = agents.is_file() and FLAT_BRIDGE_BEGIN in agents.read_text(encoding="utf-8", errors="ignore")

    print(f"Target: {target}")
    print(f"Destination: {destination}")
    print(f"Pack files to move: {len(moves)}")
    for relative in moves[:20]:
        print(f"  {relative.as_posix()} -> {args.folder}/{relative.as_posix()}")
    if len(moves) > 20:
        print(f"  ... {len(moves) - 20} more")
    print(f"Project memory: {'_agent_ops/ -> ' + args.folder + '/_agent_ops/' if ops.is_dir() else 'none found'}")
    print(f"Root AGENTS.md: {'managed flat block removed, host text kept' if strips_bridge else 'left as is'}")
    print("Derived artifacts rebuilt after the move: code_index.json, REPO_MAP.md")
    print("Never moved (host-shared or regenerated): " + ", ".join(sorted(NEVER_MOVED)))

    if not args.apply:
        print("\nDRY RUN. Nothing was changed. Re-run with --apply to perform the move.")
        return 0

    clean = worktree_is_clean(target)
    if clean is None and not args.allow_dirty:
        parser.error(
            "Target is not a Git repository, so this move would not be revertible. "
            "Commit it to Git first, or pass --allow-dirty to accept that risk."
        )
    if clean is False and not args.allow_dirty:
        parser.error(
            "Target worktree has uncommitted changes. Commit or stash them first so this "
            "move is revertible, or pass --allow-dirty."
        )

    destination.mkdir(parents=True)
    for relative in moves:
        new_path = destination / relative
        new_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(target / relative), str(new_path))
    if ops.is_dir():
        shutil.move(str(ops), str(destination / "_agent_ops"))
        # Both describe the OLD layout and are derived, so they are rebuilt by the
        # initialization below. Leaving them would keep the pack's own scripts in
        # the project's graph -- the exact defect this migration removes. Nothing
        # else in project memory is touched.
        for derived in ("code_index.json", "REPO_MAP.md"):
            stale = destination / "_agent_ops" / derived
            if stale.is_file():
                stale.unlink()
                print(f"REBUILD PENDING: {derived} (described the flat layout)")
    for removed in prune_empty_dirs(target, moves):
        print(f"REMOVED empty directory: {removed}")
    if strips_bridge:
        agents.write_text(strip_flat_bridge(agents.read_text(encoding="utf-8")), encoding="utf-8")
        print(f"UPDATED: {agents} (managed flat block removed)")
    # The pack root file the new bridge points at must exist even when the flat
    # install's AGENTS.md was host-owned and therefore stayed at the root.
    if not (destination / "AGENTS.md").is_file():
        shutil.copy2(source / "AGENTS.md", destination / "AGENTS.md")
        print(f"WRITE: {destination / 'AGENTS.md'} (canonical pack instructions)")

    print(f"MOVED: {len(moves)} pack file(s) into {destination}")
    initialize = subprocess.run(
        [
            sys.executable,
            "-B",
            str(destination / "scripts" / "init_project_ops.py"),
            "--target",
            str(target),
            "--embedded-folder",
            Path(args.folder).as_posix(),
            "--install-agents-bridge",
        ],
        cwd=str(target),
        text=True,
        check=False,
    )
    if initialize.returncode != 0:
        print(
            "BLOCKED: files were moved but initialization failed. Nothing was deleted; "
            "`git status` shows the renames and `git checkout` reverts them.",
            file=sys.stderr,
        )
        return initialize.returncode or 1
    print("MIGRATED. Review `git status`: every change is a rename plus the new root entry points.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

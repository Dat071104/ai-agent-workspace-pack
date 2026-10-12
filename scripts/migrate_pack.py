#!/usr/bin/env python3
"""Move a flat workspace-pack install into one namespaced folder.

A flat install unpacked the pack's files directly into the application root,
where they mix with the application's own `scripts/`, `tests/`, and harness
folders. Nothing here deletes anything: every pack file is MOVED into
`<folder>/`, so `git status` shows renames and the whole operation is revertible
with `git checkout`.

A file moves only with PROOF it is the pack's: its bytes equal this source
pack's file, or (when the source is a Git repository) a version that path held
at some revision of the source's history. A path that merely matches a pack
file's name -- an application's own `scripts/shared.py` -- is a conflict, and any
conflict stops the whole migration before the first move.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pack_manifest import local_tree_files, shipped_bytes, write_manifest  # noqa: E402
from pack_ownership import history_blobs, matches_history  # noqa: E402
from pack_sync import classify_overlap  # noqa: E402
from source_state import looks_like_pack, pack_folder  # noqa: E402
from source_state import worktree_is_clean  # noqa: E402
from ops_gate import REFUSED_EXIT  # noqa: E402


DEFAULT_FOLDER = "ai-agent-workspace-pack"
# Entry points and host-shared names are decided by init_project_ops after the
# move, or left alone. `LICENSE`, `.gitignore`, and `README.md` are as likely to
# belong to the application as to the pack, and guessing wrong loses host files.
ROOT_ENTRY_POINTS = {"AGENTS.md", "CLAUDE.md", "GEMINI.md"}
NEVER_MOVED = {"LICENSE", ".gitignore", "README.md"} | ROOT_ENTRY_POINTS
FLAT_BRIDGE_BEGIN = "<!-- AI_AGENT_WORKSPACE_PACK:BEGIN v1 -->"
FLAT_BRIDGE_END = "<!-- AI_AGENT_WORKSPACE_PACK:END v1 -->"


def strip_flat_bridge(text: str) -> str:
    """Remove the flat managed block, keeping every host-owned line."""

    if FLAT_BRIDGE_BEGIN not in text or FLAT_BRIDGE_END not in text:
        return text
    start = text.index(FLAT_BRIDGE_BEGIN)
    end = text.index(FLAT_BRIDGE_END, start) + len(FLAT_BRIDGE_END)
    return (text[:start].rstrip("\n") + "\n" + text[end:].lstrip("\n")).lstrip("\n")


def _lf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def plan_moves(target: Path, source: Path) -> tuple[list[str], list[str]]:
    """Split target files that share a pack path into (proven-pack, conflicts).

    Candidates are the source pack's files, tests/ and examples/ included: a
    flat install of an older revision unpacked those too, and they are exactly
    what pollutes the host root. Both lists are sorted, posix paths.
    """

    history: dict[str, set[str]] | None = None
    moves: list[str] = []
    conflicts: list[str] = []
    for rel in sorted(local_tree_files(source)):
        if "/" not in rel and rel in NEVER_MOVED:
            continue
        host_file = target / rel
        if not host_file.is_file():
            continue
        data = host_file.read_bytes()
        if _lf(data) == _lf((source / rel).read_bytes()):
            moves.append(rel)
            continue
        if history is None:
            history = history_blobs(source)
        (moves if matches_history(data, rel, history) else conflicts).append(rel)
    return moves, conflicts


def prune_empty_dirs(target: Path, moved: list[str]) -> list[Path]:
    """Remove directories emptied by the move, deepest first. Never removes files."""

    candidates = {(target / rel).parent for rel in moved if "/" in rel}
    removed: list[Path] = []
    for directory in sorted(candidates, key=lambda path: len(path.parts), reverse=True):
        while directory != target and directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
            removed.append(directory)
            directory = directory.parent
    return removed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Move a flat workspace-pack install into one namespaced folder."
    )
    parser.add_argument("--target", required=True, help="Project directory holding the flat install.")
    parser.add_argument(
        "--folder",
        default=DEFAULT_FOLDER,
        help="Destination folder name, directly under the project root.",
    )
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
    memory = parser.add_mutually_exclusive_group()
    memory.add_argument("--claim-memory", action="store_true",
                        help="Passed to init: adopt the moved memory (an install from before ownership stamps).")
    memory.add_argument("--reset-memory", action="store_true",
                        help="Passed to init: back up the moved memory completely, then start fresh.")
    return parser


def print_plan(target: Path, folder: Path, moves: list[str], conflicts: list[str],
               strips_bridge: bool) -> None:
    ops = target / "_agent_ops"
    print(f"Target: {target}")
    print(f"Destination: {target / folder}")
    print(f"Pack files to move (content proven to be the pack's): {len(moves)}")
    for rel in moves[:20]:
        print(f"  {rel} -> {folder.as_posix()}/{rel}")
    if len(moves) > 20:
        print(f"  ... {len(moves) - 20} more")
    print(f"Project memory: {'_agent_ops/ -> ' + folder.as_posix() + '/_agent_ops/' if ops.is_dir() else 'none found'}")
    print(f"Root AGENTS.md: {'managed flat block removed, host text kept' if strips_bridge else 'left as is'}")
    print("Derived artifacts rebuilt after the move: code_index.json, REPO_MAP.md")
    print("Never moved (host-shared or regenerated): " + ", ".join(sorted(NEVER_MOVED)))
    if conflicts:
        print(f"\nCONFLICTS ({len(conflicts)}): same path as a pack file, but different content:")
        for rel in conflicts:
            print(f"  {rel}")


def move_files(target: Path, destination: Path, moves: list[str]) -> None:
    destination.mkdir(parents=True)
    for rel in moves:
        new_path = destination / rel
        new_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(target / rel), str(new_path))


def move_ops(target: Path, destination: Path) -> None:
    ops = target / "_agent_ops"
    if not ops.is_dir():
        return
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


def ensure_pack_agents(source: Path, destination: Path) -> bool:
    """The pack root file the new bridge points at must exist even when the flat
    install's AGENTS.md was host-owned and therefore stayed at the root."""

    path = destination / "AGENTS.md"
    if path.is_file():
        return False
    path.write_bytes(shipped_bytes(source, "AGENTS.md"))
    print(f"WRITE: {path} (canonical pack instructions)")
    return True


def initialize(destination: Path, target: Path, folder: Path, memory_flag: str = "") -> int:
    return subprocess.run(
        [
            sys.executable,
            "-B",
            str(destination / "scripts" / "init_project_ops.py"),
            "--target",
            str(target),
            "--embedded-folder",
            folder.as_posix(),
            "--install-agents-bridge",
            *([memory_flag] if memory_flag else []),
        ],
        cwd=str(target),
        text=True,
        check=False,
    ).returncode


def apply_migration(source: Path, target: Path, folder: Path, moves: list[str],
                    strips_bridge: bool, memory_flag: str = "") -> int:
    destination = target / folder
    agents = target / "AGENTS.md"
    move_files(target, destination, moves)
    move_ops(target, destination)
    for removed in prune_empty_dirs(target, moves):
        print(f"REMOVED empty directory: {removed}")
    if strips_bridge:
        agents.write_text(strip_flat_bridge(agents.read_text(encoding="utf-8")), encoding="utf-8")
        print(f"UPDATED: {agents} (managed flat block removed)")
    owned = set(moves) | ({"AGENTS.md"} if ensure_pack_agents(source, destination) else set())
    # The moved files are proven pack content; recording them lets a later
    # `embed_pack.py --update` retire the ones this revision no longer ships.
    write_manifest(destination, "migrated", owned)

    print(f"MOVED: {len(moves)} pack file(s) into {destination}")
    code = initialize(destination, target, folder, memory_flag)
    if code == REFUSED_EXIT:
        print(
            "BLOCKED: files were moved, but init needs an ownership choice for the moved memory "
            "(see above). Re-run init with the printed --claim-memory or --reset-memory and "
            "--install-agents-bridge; nothing was deleted.",
            file=sys.stderr,
        )
        return code
    if code != 0:
        print(
            "BLOCKED: files were moved but initialization failed. Nothing was deleted; "
            "`git status` shows the renames and `git checkout` reverts them.",
            file=sys.stderr,
        )
        return 1
    print("MIGRATED. Review `git status`: every change is a rename plus the new root entry points.")
    print("Next: run `embed_pack.py --target . --update` from a current pack to refresh the moved files.")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    target = Path(args.target).expanduser().resolve()
    if not target.is_dir():
        parser.error(f"Target must be an existing directory: {target}")
    # This was unvalidated: `--folder ../elsewhere` moved the pack out of the
    # project entirely, and an absolute path ignored --target altogether.
    try:
        folder = pack_folder(args.folder)
    except ValueError as error:
        parser.error(str(error))
    source = Path(__file__).resolve().parents[1]
    if target == source:
        parser.error("Refusing to migrate this pack's own source checkout.")
    if not looks_like_pack(target):
        parser.error(f"No flat workspace-pack install found at {target}")
    destination = target / folder
    if destination.exists():
        parser.error(f"Destination already exists; not merged into: {destination}")
    if classify_overlap(source, destination) != "none":
        parser.error(f"The source pack {source} overlaps the destination {destination}.")

    moves, conflicts = plan_moves(target, source)
    agents = target / "AGENTS.md"
    strips_bridge = agents.is_file() and FLAT_BRIDGE_BEGIN in agents.read_text(encoding="utf-8", errors="ignore")
    print_plan(target, folder, moves, conflicts, strips_bridge)
    if conflicts:
        print(
            "\nREFUSED: nothing was moved. Rename, move or reconcile the conflicting host files "
            "(or restore them to the pack's content), then re-run.",
            file=sys.stderr,
        )
        return 1
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
    flag = "--reset-memory" if args.reset_memory else "--claim-memory" if args.claim_memory else ""
    return apply_migration(source, target, folder, moves, strips_bridge, flag)


if __name__ == "__main__":
    raise SystemExit(main())

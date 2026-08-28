#!/usr/bin/env python3
"""Materialize a clean, namespaced copy of this workspace pack in a project.

This is intentionally a copy operation, not a Git clone or submodule. The
source pack's own ``_agent_ops/`` is project-specific working memory and must
never become the target project's starting memory.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


sys.dont_write_bytecode = True
DEFAULT_FOLDER = "ai-agent-workspace-pack"
EXCLUDED_NAMES = {".git", "_agent_ops", "__pycache__", ".pytest_cache"}


def safe_folder(value: str) -> Path:
    folder = Path(value.replace("\\", "/"))
    if not value or folder.is_absolute() or any(part == ".." for part in folder.parts) or str(folder) in {"", "."}:
        raise ValueError("--folder must be a non-empty path inside --target")
    return folder


def ignore_source_state(directory: str, names: list[str]) -> set[str]:
    """Exclude source checkout state while retaining every pack instruction."""

    del directory
    return {name for name in names if name in EXCLUDED_NAMES or name.endswith(".pyc")}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copy this pack into a project without Git metadata or source _agent_ops state."
    )
    parser.add_argument("--target", required=True, help="Target project directory.")
    parser.add_argument("--folder", default=DEFAULT_FOLDER, help="Pack folder inside the target project.")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.exists() or not target.is_dir():
        parser.error(f"Target must be an existing directory: {target}")
    try:
        folder = safe_folder(args.folder)
    except ValueError as error:
        parser.error(str(error))

    source = Path(__file__).resolve().parents[1]
    destination = target / folder
    if destination.exists():
        parser.error(f"Destination already exists; not overwritten: {destination}")

    shutil.copytree(source, destination, ignore=ignore_source_state)
    initialize = subprocess.run(
        [
            sys.executable,
            "-B",
            str(destination / "scripts" / "init_project_ops.py"),
            "--target",
            str(target),
            "--embedded-folder",
            folder.as_posix(),
            "--install-agents-bridge",
        ],
        cwd=str(target),
        text=True,
        check=False,
    )
    if initialize.returncode != 0:
        print(
            "BLOCKED: copied pack remains at " + str(destination) + "; initialization failed without removing it.",
            file=sys.stderr,
        )
        return initialize.returncode or 1

    print(f"EMBEDDED PACK: {destination}")
    print("Source .git and source _agent_ops were excluded; a fresh nested ops folder was initialized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

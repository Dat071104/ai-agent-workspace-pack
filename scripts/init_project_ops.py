#!/usr/bin/env python3
"""Initialize an AI-agent project operations folder in a target project."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


TEMPLATE_MAP = {
    "INDEX.template.md": "INDEX.md",
    "PROJECT_CONTEXT_CARD.template.md": "PROJECT_CONTEXT_CARD.md",
    "SESSION_PROTOCOL.template.md": "SESSION_PROTOCOL.md",
    "SESSION_BRIEF.template.md": "SESSION_BRIEF.md",
    "CURRENT_TASK.template.md": "CURRENT_TASK.md",
    "IMPLEMENTATION_LOG.template.md": "IMPLEMENTATION_LOG.md",
    "DECISION_LOG.template.md": "DECISION_LOG.md",
    "RISK_REGISTER.template.md": "RISK_REGISTER.md",
    "PHASE_ROADMAP.template.md": "PHASE_ROADMAP.md",
    "OPERATING_RULES.template.md": "OPERATING_RULES.md",
}

# Hybrid git policy: durable project memory is tracked so it survives a clone;
# session-scoped scratch stays local so it never noises up a diff or leaks
# working notes into a public repository.
SESSION_SCOPED = [
    "SESSION_BRIEF.md",
    "CURRENT_TASK.md",
    "LOG_SUMMARY.md",
    "code_index.json",
]

OPS_GITIGNORE = """# Hybrid policy for _agent_ops/ (see INDEX.md).
#
# Ignored below: session-scoped scratch and derived files. SESSION_BRIEF and
# CURRENT_TASK are machine-local working notes that change every session;
# LOG_SUMMARY is regenerated from the log, so tracking it would only create
# merge noise.
#
# Everything else in this folder IS tracked on purpose: the context card, repo
# map, implementation log and its archive, handoff, decisions, risks, roadmap,
# and operating rules are durable project memory that must survive a clone.
# Never put secrets or private data in tracked files.

SESSION_BRIEF.md
CURRENT_TASK.md
LOG_SUMMARY.md

# Derived build artifact: rebuilt from source by build_code_index.py, can reach
# tens of MB on a large repo, and would conflict on every merge. REPO_MAP.md is
# the small human-readable view of it and IS tracked.
code_index.json
"""


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def copy_template(source: Path, destination: Path, force: bool) -> str:
    if destination.exists() and not force:
        return f"SKIP existing: {destination}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    return f"WRITE: {destination}"


def write_if_absent(destination: Path, content: str, force: bool) -> str:
    if destination.exists() and not force:
        return f"SKIP existing: {destination}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return f"WRITE: {destination}"


def write_code_index(target: Path, ops_dir: Path, force: bool) -> str:
    """Build the symbol-level index that scripts/explore.py queries."""
    destination = ops_dir / "code_index.json"
    if destination.exists() and not force:
        return f"SKIP existing: {destination}"
    try:
        import json  # noqa: PLC0415

        from build_code_index import build_index  # noqa: PLC0415

        index = build_index(target)
        destination.write_text(json.dumps(index, separators=(",", ":")), encoding="utf-8")
        return (
            f"WRITE: {destination} "
            f"({len(index['symbols'])} symbols, {len(index['edges'])} edges)"
        )
    except Exception as error:  # noqa: BLE001 - report, do not abort init
        return (
            f"WARN could not build {destination}: {error}"
            "\n"
            "     Run scripts/build_code_index.py manually if you want "
            "symbol-level exploration."
        )


def write_repo_map(target: Path, ops_dir: Path, force: bool) -> str:
    """Generate the codegraph-lite map. Never fatal: the pack must stay usable
    on repos where this scan cannot run."""
    destination = ops_dir / "REPO_MAP.md"
    if destination.exists() and not force:
        return f"SKIP existing: {destination}"
    try:
        from generate_repo_map import render_map  # noqa: PLC0415
        from scan_deps import build_graph  # noqa: PLC0415

        graph = build_graph(target)
        destination.write_text(render_map(target, graph, 25, 15), encoding="utf-8")
        return f"WRITE: {destination} ({len(graph)} code files indexed)"
    except Exception as error:  # noqa: BLE001 - report, do not abort init
        return (
            f"WARN could not generate {destination}: {error}\n"
            "     Run scripts/generate_repo_map.py manually, or describe the "
            "layout in PROJECT_CONTEXT_CARD.md."
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create _agent_ops/ project memory files in a target project."
    )
    parser.add_argument("--target", required=True, help="Target project directory.")
    parser.add_argument(
        "--ops-folder",
        default="_agent_ops",
        help="Operations folder name to create inside the target project.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing ops files.",
    )
    parser.add_argument(
        "--no-repo-map",
        action="store_true",
        help="Skip generating REPO_MAP.md (useful for very large repositories).",
    )
    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Skip building code_index.json (the symbol-level graph).",
    )
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        parser.error(f"Target does not exist: {target}")
    if not target.is_dir():
        parser.error(f"Target is not a directory: {target}")

    templates_dir = repo_root() / "core-context"
    if not templates_dir.exists():
        parser.error(f"Cannot find template directory: {templates_dir}")

    ops_dir = target / args.ops_folder
    ops_dir.mkdir(parents=True, exist_ok=True)

    print(f"Target: {target}")
    print(f"Ops folder: {ops_dir}")

    for template_name, output_name in TEMPLATE_MAP.items():
        source = templates_dir / template_name
        if not source.exists():
            print(f"WARN missing template: {source}")
            continue
        print(copy_template(source, ops_dir / output_name, args.force))

    phase_dir = ops_dir / "phase_context_cards"
    phase_dir.mkdir(exist_ok=True)
    print(
        write_if_absent(
            phase_dir / "README.md",
            "# Phase Context Cards\n\n"
            "Store one phase context card per completed or active phase.\n\n"
            "Suggested name: `PHASE_001_<short-name>.md`.\n",
            args.force,
        )
    )

    archive_dir = ops_dir / "archive"
    archive_dir.mkdir(exist_ok=True)
    print(
        write_if_absent(
            archive_dir / "README.md",
            "# Archive\n\n"
            "Rotated implementation-log entries land here so the active log stays\n"
            "small enough to read cheaply. Read these only when investigating\n"
            "something older than the retained window.\n",
            args.force,
        )
    )

    print(write_if_absent(ops_dir / ".gitignore", OPS_GITIGNORE, args.force))

    if args.no_repo_map:
        print(f"SKIP repo map (--no-repo-map): {ops_dir / 'REPO_MAP.md'}")
    else:
        print(write_repo_map(target, ops_dir, args.force))
    if args.no_index:
        print(f"SKIP code index (--no-index): {ops_dir / 'code_index.json'}")
    else:
        print(write_code_index(target, ops_dir, args.force))

    print("")
    print("Done. Existing files were preserved unless --force was used.")
    print("Session-scoped files are gitignored by _agent_ops/.gitignore:")
    print("  " + ", ".join(SESSION_SCOPED))
    print("Everything else in _agent_ops/ is tracked on purpose. Next step:")
    print(f'  python scripts/session_start.py --root "{target}"')
    print("Explore code structurally instead of grepping:")
    print(f'  python scripts/explore.py --root "{target}" --symbol <name>')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Initialize an AI-agent project operations folder in a target project."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


TEMPLATE_MAP = {
    "PROJECT_CONTEXT_CARD.template.md": "PROJECT_CONTEXT_CARD.md",
    "SESSION_BRIEF.template.md": "SESSION_BRIEF.md",
    "IMPLEMENTATION_LOG.template.md": "IMPLEMENTATION_LOG.md",
    "DECISION_LOG.template.md": "DECISION_LOG.md",
    "RISK_REGISTER.template.md": "RISK_REGISTER.md",
    "PHASE_ROADMAP.template.md": "PHASE_ROADMAP.md",
    "OPERATING_RULES.template.md": "OPERATING_RULES.md",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def copy_template(source: Path, destination: Path, force: bool) -> str:
    if destination.exists() and not force:
        return f"SKIP existing: {destination}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    return f"WRITE: {destination}"


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
    readme = phase_dir / "README.md"
    if readme.exists() and not args.force:
        print(f"SKIP existing: {readme}")
    else:
        readme.write_text(
            "# Phase Context Cards\n\n"
            "Store one phase context card per completed or active phase.\n\n"
            "Suggested name: `PHASE_001_<short-name>.md`.\n",
            encoding="utf-8",
        )
        print(f"WRITE: {readme}")

    print("Done. Existing files were preserved unless --force was used.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

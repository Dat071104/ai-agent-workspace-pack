#!/usr/bin/env python3
"""Generate a starter project context card from CLI args and light repo inspection."""

from __future__ import annotations

import argparse
import subprocess
from datetime import date
from pathlib import Path


def git_value(root: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return "not available"
    return result.stdout.strip() or "not available"


def detect_stack(root: Path) -> list[str]:
    stack: list[str] = []
    if (root / "package.json").exists():
        stack.append("JavaScript/TypeScript")
    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists():
        stack.append("Python")
    if (root / "go.mod").exists():
        stack.append("Go")
    if (root / "Cargo.toml").exists():
        stack.append("Rust")
    if (root / "pom.xml").exists() or (root / "build.gradle").exists():
        stack.append("Java")
    return stack or ["Unknown"]


def render_card(args: argparse.Namespace, root: Path) -> str:
    branch = git_value(root, ["branch", "--show-current"])
    commit = git_value(root, ["rev-parse", "--short", "HEAD"])
    stack = ", ".join(detect_stack(root))
    summary = args.summary or "Starter context card generated from repo inspection. Update this summary manually."
    run_command = args.run or "<fill in run command>"
    test_command = args.test or "<fill in test command>"
    return f"""# Project Context Card

## Project Name

{args.name}

## One-Paragraph Summary

{summary}

## Current Phase / State

{args.phase}

## Tech Stack

{stack}

## Architecture

<fill in main modules, services, data flow, and boundaries>

## Key Decisions

- <fill in decision and reason>

## Current Branch / Commit

- Branch: {branch}
- Commit: {commit}

## How to Run

```bash
{run_command}
```

## How to Test

```bash
{test_command}
```

## Known Risks

- <fill in known risk>

## Next Step

{args.next_step}

## Do Not Do

- Do not commit secrets, private data, generated artifacts, or local logs.
- Never use git add .

## Last Updated

{date.today().isoformat()}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a starter PROJECT_CONTEXT_CARD.md.")
    parser.add_argument("--root", default=".", help="Project root to inspect.")
    parser.add_argument("--name", default="Unnamed Project", help="Project name.")
    parser.add_argument("--summary", default="", help="One-paragraph project summary.")
    parser.add_argument("--phase", default="Initial context setup", help="Current phase or state.")
    parser.add_argument("--run", default="", help="Run command.")
    parser.add_argument("--test", default="", help="Test command.")
    parser.add_argument("--next-step", default="<fill in next step>", help="Next step.")
    parser.add_argument("--output", default="", help="Optional file path to write. Prints to stdout if omitted.")
    parser.add_argument("--force", action="store_true", help="Overwrite output file if it exists.")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        parser.error(f"Root must be an existing directory: {root}")

    card = render_card(args, root)
    if args.output:
        output = Path(args.output).expanduser().resolve()
        if output.exists() and not args.force:
            parser.error(f"Output exists. Use --force to overwrite: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(card, encoding="utf-8")
        print(f"Wrote: {output}")
    else:
        print(card)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


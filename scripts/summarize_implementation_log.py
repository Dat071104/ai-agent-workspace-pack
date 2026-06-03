#!/usr/bin/env python3
"""Summarize an append-only implementation log into a compact current-state report."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


HEADING_RE = re.compile(r"^(#{2,4})\s+(.+)$")
DATE_HEADING_RE = re.compile(r"^##\s+\d{4}-\d{2}-\d{2}(?:\b|$)")
ENTRY_HEADING_RE = re.compile(r"^##\s+Entry(?:\s*[:#-]|\s+\d|\s*$)", re.IGNORECASE)
DATE_LINE_RE = re.compile(r"^Date:\s*\S+", re.IGNORECASE)


def split_entries(text: str) -> list[str]:
    lines = text.splitlines()
    entries: list[list[str]] = []
    current: list[str] | None = None
    for line in lines:
        is_entry_start = bool(
            DATE_HEADING_RE.match(line)
            or ENTRY_HEADING_RE.match(line)
            or DATE_LINE_RE.match(line)
        )
        if is_entry_start:
            if current:
                entries.append(current)
            current = [line]
        elif current is not None:
            current.append(line)
    if current:
        entries.append(current)
    return ["\n".join(entry).strip() for entry in entries if "\n".join(entry).strip()]


def entry_title(entry: str, fallback_index: int) -> str:
    for line in entry.splitlines():
        if line.strip():
            if DATE_LINE_RE.match(line):
                return line.strip()
            return line.lstrip("#").strip()
    return f"Entry {fallback_index}"


def extract_section(entry: str, names: list[str]) -> str:
    lines = entry.splitlines()
    capture = False
    collected: list[str] = []
    wanted = [name.lower() for name in names]
    for line in lines:
        heading = HEADING_RE.match(line)
        if heading:
            title = heading.group(2).strip().lower()
            if any(name in title for name in wanted):
                capture = True
                continue
            if capture:
                break
        elif capture:
            collected.append(line)
    return "\n".join(line for line in collected if line.strip()).strip()


def render_summary(log_path: Path, entries: list[str], recent: list[str]) -> str:
    lines = [
        "# Implementation Log Summary",
        "",
        f"Source: {log_path}",
        f"Entries detected: {len(entries)}",
        f"Recent entries summarized: {len(recent)}",
        "",
    ]
    if not entries:
        lines.extend(
            [
                "No real log entries detected.",
                "",
                "Expected entry boundaries: `## YYYY-MM-DD`, `## Entry`, or `Date: YYYY-MM-DD`.",
                "",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    start_index = len(entries) - len(recent) + 1
    for offset, entry in enumerate(recent):
        title = entry_title(entry, start_index + offset)
        changed = extract_section(entry, ["what changed", "files touched"])
        tests = extract_section(entry, ["tests run", "results"])
        risks = extract_section(entry, ["remaining risks", "next step"])
        lines.append(f"## {title}")
        lines.append("")
        if changed:
            lines.append("### Change")
            lines.append(changed)
            lines.append("")
        if tests:
            lines.append("### Tests / Results")
            lines.append(tests)
            lines.append("")
        if risks:
            lines.append("### Risks / Next")
            lines.append(risks)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize an implementation log.")
    parser.add_argument("--log", required=True, help="Path to IMPLEMENTATION_LOG.md.")
    parser.add_argument("--last", type=int, default=5, help="Number of recent entries to summarize.")
    parser.add_argument("--output", default="", help="Optional output markdown file.")
    parser.add_argument("--force", action="store_true", help="Overwrite output file if it exists.")
    args = parser.parse_args()

    log_path = Path(args.log).expanduser().resolve()
    if not log_path.exists() or not log_path.is_file():
        parser.error(f"Log file does not exist: {log_path}")

    text = log_path.read_text(encoding="utf-8", errors="ignore")
    entries = split_entries(text)
    recent = entries[-max(args.last, 1):]

    summary = render_summary(log_path, entries, recent)
    if args.output:
        output = Path(args.output).expanduser().resolve()
        if output.exists() and not args.force:
            parser.error(f"Output exists. Use --force to overwrite: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(summary, encoding="utf-8")
        print(f"Wrote: {output}")
    else:
        print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

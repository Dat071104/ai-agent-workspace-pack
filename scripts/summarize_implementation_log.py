#!/usr/bin/env python3
"""Summarize an append-only implementation log into a compact current-state report."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path


HEADING_RE = re.compile(r"^(#{2,4})\s+(.+)$")
DATE_HEADING_RE = re.compile(r"^##\s+\d{4}-\d{2}-\d{2}(?:\b|$)")
ENTRY_HEADING_RE = re.compile(r"^##\s+Entry(?:\s*[:#-]|\s+\d|\s*$)", re.IGNORECASE)
DATE_LINE_RE = re.compile(r"^Date:\s*\S+", re.IGNORECASE)


def split_log(text: str) -> tuple[str, list[str]]:
    """Split a log into its preamble and its entries.

    The preamble is whatever precedes the first entry -- title, usage notes, the
    entry template. Rotation must preserve it, so it is returned separately
    rather than discarded.
    """
    lines = text.splitlines()
    preamble: list[str] = []
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
        else:
            preamble.append(line)
    if current:
        entries.append(current)
    return (
        "\n".join(preamble).strip(),
        ["\n".join(entry).strip() for entry in entries if "\n".join(entry).strip()],
    )


def split_entries(text: str) -> list[str]:
    return split_log(text)[1]


def rotate_log(log_path: Path, keep: int, archive_dir: Path) -> str:
    """Move all but the newest `keep` entries into a dated archive file.

    The active log is what agents read every session; unbounded growth turns the
    context-saving folder into a context cost. The archive is written and
    verified before the log is rewritten, so no entry can be lost.
    """
    text = log_path.read_text(encoding="utf-8", errors="ignore")
    preamble, entries = split_log(text)
    if len(entries) <= keep:
        return f"No rotation needed: {len(entries)} entry/entries, keep={keep}."

    moved = entries[:-keep]
    kept = entries[-keep:]
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / f"IMPLEMENTATION_LOG_{date.today():%Y-%m}.md"

    if archive_path.exists():
        existing = archive_path.read_text(encoding="utf-8", errors="ignore").rstrip()
    else:
        existing = (
            f"# Implementation Log Archive {date.today():%Y-%m}\n\n"
            f"Rotated out of `{log_path.name}`. Append-only; read only when the\n"
            "retained window and the summary are not enough."
        )
    archive_path.write_text(
        existing + "\n\n" + "\n\n".join(moved) + "\n", encoding="utf-8"
    )

    written = archive_path.read_text(encoding="utf-8", errors="ignore")
    missing = [entry for entry in moved if entry.splitlines()[0] not in written]
    if missing:
        return (
            f"ABORTED: {len(missing)} entry/entries did not reach {archive_path}. "
            f"{log_path} was left untouched."
        )

    head = (preamble + "\n\n") if preamble else ""
    log_path.write_text(head + "\n\n".join(kept) + "\n", encoding="utf-8")
    return (
        f"Rotated {len(moved)} entry/entries into {archive_path}; "
        f"{len(kept)} kept in {log_path}."
    )


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
    parser.add_argument(
        "--rotate",
        action="store_true",
        help="Move entries older than --keep into the archive folder. Modifies the log.",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=10,
        help="Entries to retain in the active log when rotating.",
    )
    parser.add_argument(
        "--archive-dir",
        default="",
        help="Archive folder. Defaults to an 'archive' folder beside the log.",
    )
    args = parser.parse_args()

    log_path = Path(args.log).expanduser().resolve()
    if not log_path.exists() or not log_path.is_file():
        parser.error(f"Log file does not exist: {log_path}")

    if args.rotate:
        archive_dir = (
            Path(args.archive_dir).expanduser().resolve()
            if args.archive_dir
            else log_path.parent / "archive"
        )
        print(rotate_log(log_path, max(args.keep, 1), archive_dir))

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

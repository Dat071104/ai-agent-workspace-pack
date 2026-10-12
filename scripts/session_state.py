#!/usr/bin/env python3
"""Read the state of a task out of the ops markdown records.

Split out of session_start.py along one boundary: parsing what the records
SAY (sections, placeholders, task status, open questions) versus gathering what
the repository IS (git state, freshness) and printing it. session_start prints;
this module decides what the records mean, so the rule for "is a task mid-flight"
lives in one place and can be tested without a git repository.
"""

from __future__ import annotations

import re
import sys

# Running a tool must never leave __pycache__ inside someone else's repository.
sys.dont_write_bytecode = True

PLACEHOLDER_RES = [
    re.compile(r"`<[^`\n]*>`"),
    re.compile(r"<fill in [^>\n]*>"),
]

# `CURRENT_TASK.md` `## Status`. The first word decides; anything after it is
# the author's note. Synonyms are accepted because the value is written by
# models that will not all copy the template's exact spelling.
TASK_STATES = ("in-progress", "blocked", "complete", "idle")
_STATUS_ALIASES = (
    ("in-progress", re.compile(r"^(in[- ]progress|active|wip)\b")),
    ("blocked", re.compile(r"^(blocked|waiting)\b")),
    ("complete", re.compile(r"^(complete|completed|done|finished)\b")),
    ("idle", re.compile(r"^(idle|none|no task)\b")),
)
# A line under "Open Questions" that says there are none is not a question.
_NO_QUESTION_RE = re.compile(r"^(none|n/a|nil|no open question|no question|nothing)\b", re.IGNORECASE)


def section_body(text: str, heading: str) -> str:
    """Return the body under a `## Heading` up to the next heading of any level."""
    lines = text.splitlines()
    wanted = heading.strip().lower()
    collected: list[str] = []
    capture = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            if capture:
                break
            title = stripped.lstrip("#").strip().lower()
            # Prefix match so decorated headings still resolve, e.g.
            # "## Original Goal (do not lose)".
            capture = title == wanted or title.startswith(wanted)
            continue
        if capture:
            collected.append(line)
    return "\n".join(collected).strip()


def first_value(text: str, heading: str) -> str:
    body = section_body(text, heading)
    for line in body.splitlines():
        if line.strip():
            return line.strip().strip("`").strip()
    return ""


def count_placeholders(text: str) -> int:
    return sum(len(pattern.findall(text)) for pattern in PLACEHOLDER_RES)


def is_placeholder_only(line: str) -> bool:
    """True when a bullet is still the unfilled template text, not real content."""
    body = line.lstrip("-*").strip().strip("`").strip()
    return not body or (body.startswith("<") and body.endswith(">"))


def real_items(body: str) -> list[str]:
    """Filled-in entries from a section, whether it uses bullets or a table.

    Templates in this pack use both shapes, and every row still holding its
    `<placeholder>` text is dropped so a fresh template reports zero.
    """
    items: list[str] = []
    for raw in body.splitlines():
        line = raw.strip()
        if line.startswith(("-", "*")) and not line.startswith("---"):
            if not is_placeholder_only(line):
                items.append(line)
        elif line.startswith("|"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if not cells or all(set(cell) <= {"-", ":", ""} for cell in cells):
                continue  # separator row
            first = cells[0].strip("`").strip()
            if not first or first.startswith("<") or first.lower() in {"tried", "file", "risk"}:
                continue  # header row or unfilled placeholder row
            items.append("- " + " | ".join(cell for cell in cells if cell))
    return items


def has_real_content(text: str, headings: tuple[str, ...]) -> bool:
    """True when at least one of the named sections is filled in, not template text.

    Sections come in two shapes. For tables and bullet lists, `real_items` already
    drops header and placeholder rows. For a plain prose section, take the first
    line -- but never a table header row, which is boilerplate that would
    otherwise read as real content and make an untouched template look live.
    """
    for heading in headings:
        if real_items(section_body(text, heading)):
            return True
        value = first_value(text, heading)
        if value and not value.startswith(("<", "|")):
            return True
    return False


def task_status(task: str) -> str | None:
    """The declared state of the task, or None when the file does not say.

    None covers a file written before the field existed, an unfilled template
    line listing the choices (`a | b | c`), and any value that is not a state.
    The caller must treat None as unknown, never as "in progress".
    """

    value = first_value(task, "Status").lower().strip("*_ ") if task else ""
    if not value or "|" in value or value.startswith("<"):
        return None
    for state, pattern in _STATUS_ALIASES:
        if pattern.match(value):
            return state
    return None


def open_questions(task: str) -> list[str]:
    """Questions the task is blocked on. "None..." and notes are not questions.

    Standing permissions live in their own section; a legacy file that put
    "None. Commit/push still needs authorization" here is still read as having
    no question, because the line begins with the answer.
    """

    questions = []
    for item in real_items(section_body(task, "Open Questions Awaiting User")):
        text = item.lstrip("-*").strip().strip("`").strip()
        if text and not _NO_QUESTION_RE.match(text):
            questions.append(item)
    return questions


def task_has_live_state(task: str) -> bool:
    return has_real_content(task, ("Next Concrete Step", "Files Touched So Far"))


def _handoff_lines(handoff: str, status: str) -> list[str]:
    written = first_value(handoff, "Date")
    return [
        "- **CONTINUATION.** A previous session left a handoff.",
        "- READ `_agent_ops/HANDOFF.md` FIRST, before routing or touching code.",
        f"- Handoff status: `{status or 'open'}`" + (f", written {written}" if written else ""),
        "- After absorbing it, set its Status to `consumed` so the next session",
        "  does not replay it.",
    ]


def _task_lines(task: str, state: str | None, live: bool) -> list[str]:
    """Continuity for the CURRENT_TASK.md alone; empty when it says nothing live."""

    if state == "in-progress":
        return [
            "- **TASK IN PROGRESS.** `CURRENT_TASK.md` Status is `in-progress`.",
            "- Resume from its Next Concrete Step; honour its Ruled Out list.",
        ]
    if state == "blocked":
        waiting = open_questions(task)
        return [
            "- **TASK BLOCKED.** `CURRENT_TASK.md` Status is `blocked`.",
            f"- Waiting on {len(waiting)} user question(s); do not guess the answers."
            if waiting
            else "- No question is recorded under Open Questions; find out what it is blocked on.",
        ]
    if state is None and live:
        return [
            "- **TASK STATE UNVERIFIED.** `CURRENT_TASK.md` has content but no `Status`",
            "  (written before status was tracked), so it may be mid-flight or long finished.",
            "- Check the implementation log or ask the user before resuming it; then set its Status.",
        ]
    return []


def continuity_block(brief: str, task: str, handoff: str) -> list[str]:
    """Answer the first question a swapped-in agent has: am I continuing someone?

    A new session should not have to be told by the user that a handoff exists.
    This looks for one and says so before anything else runs. A finished task is
    NOT a task in progress: only an explicit Status says so, because "the file
    has a next step in it" is true of a completed task too.
    """
    out = ["## Session Continuity", ""]
    status = first_value(handoff, "Status").lower() if handoff else ""
    state = task_status(task)
    task_lines = _task_lines(task, state, task_has_live_state(task))
    brief_live = has_real_content(brief, ("Original Goal", "Active Task"))

    if handoff and status != "consumed":
        out += _handoff_lines(handoff, status)
    elif task_lines:
        out += task_lines
    elif brief_live:
        out += ["- **SESSION ESTABLISHED.** A brief exists; no task is mid-flight."]
        if state == "complete":
            out.append("- `CURRENT_TASK.md` marks the last task `complete`; overwrite it when the next begins.")
        out.append("- Start the next task from the brief's Active Task.")
    else:
        out += [
            "- **FRESH.** No handoff, no live task, no filled-in brief.",
            "- Treat this as a new session: establish the goal with the user first.",
        ]
    if handoff and status == "consumed":
        out.append("- An older handoff exists but is already marked consumed.")
    out.append("")
    return out

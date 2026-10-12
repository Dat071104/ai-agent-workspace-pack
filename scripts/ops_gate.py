#!/usr/bin/env python3
"""init's ownership gate: decide what to do with memory it may not own.

`ops_identity` says whose memory this is; this module acts on that answer, and
is the only writer of the ownership stamp. Nothing is deleted without a
verified backup, and nothing is written when the gate refuses -- a refusal that
had already touched the folder would be a second problem on top of the first.

The rule it enforces: ownership must be PROVEN. Memory that cannot be proven
this project's (foreign, unverifiable, damaged stamp, or no stamp at all) is
refused until a person picks `--claim-memory` or `--reset-memory`; the gate never
trusts it automatically and never deletes it unbacked.

Not copied into projects: it needs init's flags, and runtime tools never decide
ownership, they only report it.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import sys
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable

# Running a tool must never leave __pycache__ inside someone else's repository.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import ops_identity as identity  # noqa: E402
from ops_identity import Verdict  # noqa: E402
from ops_policy import digest, render  # noqa: E402
from source_state import DEFAULT_OPS_FOLDER, looks_like_pack  # noqa: E402


# Inside the ops folder on purpose: every scanner skips that folder by name, so a
# copy of someone else's source files can never be indexed as this project's
# code, and one .gitignore line keeps it out of the host's history.
BACKUP_DIR = "backups"
# init exits with this when it will not touch memory it cannot prove is the
# project's. Distinct from argparse's 2 so a wrapper can tell "bad flags" from
# "needs a decision".
REFUSED_EXIT = 3
# Resets that land in the same second still get distinct folders (-2, -3, ...).
BACKUP_SLOTS = 1000
# Everything init or a tool it runs generates. None of it is a record a person
# wrote, so an ops folder holding only these and untouched templates has no
# memory to protect. Paths are relative to the ops folder.
SKELETON_FILES = frozenset({
    ".gitignore", "OPS_POLICY.json", "REPO_MAP.md", "code_index.json", "INDEX.md", "SESSION_PROTOCOL.md",
    "OPERATING_RULES.md", "archive/README.md", "phase_context_cards/README.md",
})
SKELETON_DIRS = frozenset({"tools", "__pycache__", BACKUP_DIR})


@dataclass
class Gate:
    ok: bool = True
    lines: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    backup: Path | None = None


def is_pack_source(target: Path, pack_root: Path) -> bool:
    """True when `target` is the pack's own checkout, running its own init.

    Its memory is the pack's by definition, so the gate stamps it instead of
    questioning it. A flat install (pack files unpacked at a project root)
    satisfies the same test and cannot be told apart from the source; that
    layout is deprecated, and its stamp is simply written as pack-owned.
    """

    return target.resolve() == pack_root.resolve() and looks_like_pack(target)


def command_for(target: Path, script: Path, passthrough: list[str]) -> Callable[[str], str]:
    """Builds the exact init command a user can paste, for a given flag."""

    try:
        shown = script.resolve().relative_to(target.resolve()).as_posix()
        where = f'python {shown} --target .'
    except ValueError:
        where = f'python "{script.resolve()}" --target "{target}"'
    extra = "".join(f" {item}" for item in passthrough)
    return lambda flag: f"{where}{extra} {flag}"


def new_stamp(git: identity.GitIdentity, how: str, origin: str, previous: dict | None = None) -> dict:
    """A fresh identity. Only a whole, non-shallow history may be recorded.

    Must stay in step with `ops_identity.stamp_problem`: it rejects any stamp
    that differs from what this writes, so a field added here needs a schema bump.
    """

    stamp = {
        "schema": identity.SCHEMA,
        "project_id": uuid.uuid4().hex,
        "root_commits": list(git.roots[: identity.MAX_STORED_ROOTS]) if git.state == "commits" else [],
        "origin": origin,
        "established": date.today().isoformat(),
        "established_by": how,
    }
    if previous and isinstance(previous.get("project_id"), str):
        stamp["previous_project_id"] = previous["project_id"]
    return stamp


def bound_stamp(stamp: dict, git: identity.GitIdentity) -> dict:
    """The same project, now tied to the root commit(s) it did not yet have."""

    bound = dict(stamp)
    bound["root_commits"] = list(git.roots[: identity.MAX_STORED_ROOTS])
    bound["bound"] = date.today().isoformat()
    return bound


def write_stamp(ops: Path, stamp: dict) -> Path:
    """Write the stamp whole or not at all.

    `os.replace` of a temp file means a crash cannot leave a half-written stamp
    (which now reads as damage) and a symlink at the path is replaced, not
    followed to overwrite whatever it points at.
    """

    ops.mkdir(parents=True, exist_ok=True)
    path = ops / identity.OWNER_FILE
    scratch = path.with_name(path.name + ".tmp")
    scratch.write_text(json.dumps(stamp, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(scratch, path)
    return path


def _tag(path: Path) -> str:
    """What one entry IS, so a copy is compared by content rather than by size.

    A symlink is read with `readlink`, never followed: following it would hash
    something outside the folder, and the backup must reproduce the link itself.
    """

    if path.is_symlink():
        return "link:" + os.readlink(path)
    if path.is_dir():
        return "dir"
    if not stat.S_ISREG(path.lstat().st_mode):
        return "special"
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            hasher.update(block)
    return "sha256:" + hasher.hexdigest()


def _entry_tags(root: Path, skip_backups: bool) -> dict[str, str]:
    found: dict[str, str] = {}
    for current, dirs, files in os.walk(root):  # followlinks=False: a linked directory is listed, not entered
        here = Path(current)
        if skip_backups and here == root:
            dirs[:] = [name for name in dirs if name != BACKUP_DIR]
        for name in (*dirs, *files):
            path = here / name
            found[path.relative_to(root).as_posix()] = _tag(path)
    return found


def _new_backup_folder(parent: Path) -> Path:
    """Create, never reuse, `parent/<UTC time>[-N]`.

    `mkdir` without `exist_ok` is the claim: if another reset made the folder
    first it raises and the next suffix is tried. Checking `exists()` first would
    leave a gap in which two resets share one folder.
    """

    clock = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    parent.mkdir(parents=True, exist_ok=True)
    for number in range(1, BACKUP_SLOTS + 1):
        folder = parent / (clock if number == 1 else f"{clock}-{number}")
        try:
            folder.mkdir()
        except FileExistsError:
            continue
        return folder
    raise OSError(f"no free backup folder for {clock} under {parent}")


def _copy_ops(ops: Path, destination: Path) -> None:
    """The copy step alone, so verification is independent of it."""

    def skip(directory: str, names: list[str]) -> set[str]:
        return {BACKUP_DIR} & set(names) if Path(directory) == ops else set()

    shutil.copytree(ops, destination, ignore=skip, symlinks=True, dirs_exist_ok=True)


def _verify_copy(ops: Path, destination: Path) -> int:
    """Raise unless `destination` reproduces `ops` entry for entry; else the file count."""

    original, copied = _entry_tags(ops, True), _entry_tags(destination, False)
    if original != copied:  # missing, extra and altered entries all land here
        bad = sorted(name for name in original.keys() | copied.keys() if original.get(name) != copied.get(name))
        raise OSError(f"the copy does not match the original ({len(bad)} entries, first: {', '.join(bad[:3])})")
    return sum(1 for tag in original.values() if tag != "dir")


def backup_ops(ops: Path) -> tuple[Path, int]:
    """Copy every file under `ops` (except earlier backups) to a new folder.

    Complete on purpose -- handoff, archive, roadmap, phase cards, plans,
    scratch, the index and the old stamp -- because a backup that omits the one
    file you later need is worse than none. Verified by content hash (symlinks by
    target) before the caller removes anything. A failed copy is renamed
    `.INCOMPLETE`, so no folder that looks like a backup is not one.
    """

    destination = _new_backup_folder(ops / BACKUP_DIR)
    try:
        _copy_ops(ops, destination)
        return destination, _verify_copy(ops, destination)
    except OSError as error:  # shutil.Error is an OSError
        try:
            destination.rename(destination.with_name(destination.name + ".INCOMPLETE"))
        except OSError:
            pass
        raise OSError(f"{error}; a partial copy under {ops / BACKUP_DIR} is marked .INCOMPLETE") from error


def _remove(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        for child in path.iterdir():
            _remove(child)
        path.rmdir()
        return
    try:
        path.unlink()
    except PermissionError:
        os.chmod(path, stat.S_IWRITE)  # git marks some copied files read-only on Windows
        path.unlink()


def clear_ops(ops: Path) -> None:
    """Remove everything but earlier backups, so no stale record survives."""

    for child in sorted(ops.iterdir()):
        if child.name != BACKUP_DIR:
            _remove(child)


def _is_untouched_record(path: Path, rel: str, templates: Path, ops_relative: str) -> bool:
    """True when this memory record still equals the template init renders for it."""

    if rel not in identity.MEMORY_RECORDS:
        return False
    template = templates / (rel[: -len(".md")] + ".template.md")  # HANDOFF.md has none: always authored
    try:
        written = path.read_text(encoding="utf-8")
        expected = render(template.read_text(encoding="utf-8"), ops_relative)
    except (OSError, ValueError):
        return False
    return digest(written) == digest(expected)


def holds_only_templates(ops: Path, templates: Path, ops_relative: str) -> bool:
    """True when nothing under `ops` was written by a person, so there is no memory to guard.

    Every memory record must still equal its template rendering (line endings
    ignored, via the policy refresh's `digest`) and every other file must be
    generated skeleton. Anything else -- an edited record, a handoff, an archived
    log, a linked or unknown file -- is memory. The errors are asymmetric on
    purpose: a wrong "untouched" adopts another project's records unasked, a
    wrong "touched" costs one flag. So a record left from an OLDER template
    revision is "touched" too, and asks once.
    """

    for current, dirs, files in os.walk(ops):
        here = Path(current)
        if here == ops:
            dirs[:] = [name for name in dirs if name not in SKELETON_DIRS]
        if any((here / name).is_symlink() for name in dirs):
            return False
        for name in files:
            path = here / name
            rel = path.relative_to(ops).as_posix()
            if path.is_symlink():
                return False
            if rel not in SKELETON_FILES and not _is_untouched_record(path, rel, templates, ops_relative):
                return False
    return True


def _stamped(ops: Path, stamp: dict, message: str) -> Gate:
    write_stamp(ops, stamp)
    roots = identity.stamp_roots(stamp)
    where = (
        "root commit " + ", ".join(identity.short(root) for root in roots[:3])
        if roots
        else "not bound to a root commit yet (no commits to bind to)"
    )
    return Gate(lines=[f"OWNERSHIP: {message} -- project {stamp['project_id'][:8]}, {where}"])


def _refusal(verdict: Verdict, ops: Path, command: Callable[[str], str]) -> Gate:
    legacy = verdict.state == identity.LEGACY
    if legacy:
        what = (
            "looks like the workspace pack's own memory"
            if verdict.suspect
            else f"has no {identity.OWNER_FILE}, so nothing proves it is this project's"
        )
    else:
        what = "does not belong to this repository" if verdict.foreign_like else "cannot be verified as this repository's"
    errors = [
        f"BLOCKED: {ops} holds project memory that {what}.",
        *["  " + line for line in identity.reason_lines(verdict)],
        "  Nothing was written. Resuming it would present another project's task, decisions and",
        "  rules as this project's.",
        "  Choose one (nothing is lost: --reset-memory backs up every file first):",
        f"    {command('--reset-memory')}",
        f"      back up every file under {ops / BACKUP_DIR / '<timestamp>'}, then start from fresh templates",
        f"    {command('--claim-memory')}",
        "      keep these records and make them this project's (for example after a git history rewrite)",
    ]
    if legacy:
        errors.append(
            f"  This is a one-time step: either choice writes {identity.OWNER_FILE} (commit it), and this"
            " project's memory is then recognized with no flag."
        )
    return Gate(ok=False, errors=errors)


def _reset(verdict: Verdict, ops: Path, origin: str) -> Gate:
    try:
        destination, count = backup_ops(ops)
    except OSError as error:
        return Gate(ok=False, errors=[f"BLOCKED: could not back up {ops}: {error}", "  Nothing was removed."])
    clear_ops(ops)
    stamp = new_stamp(verdict.git, "reset-memory", origin, previous=verdict.stamp)
    gate = _stamped(ops, stamp, "RESET -- fresh memory")
    gate.lines.insert(0, f"RESET MEMORY: backed up {count} file(s) to {destination}; the originals were then removed.")
    gate.lines.append(f"  The backup is kept (gitignored, never deleted, not indexed as code): {destination}")
    gate.backup = destination
    return gate


def apply_ownership(
    target: Path,
    ops: Path,
    *,
    claim: bool,
    reset: bool,
    pack_source: bool,
    command: Callable[[str], str],
    templates: Path | None = None,
    ops_relative: str = DEFAULT_OPS_FOLDER,
) -> Gate:
    """Decide and perform what init does about the memory already in `ops`.

    Without a flag init proceeds only on proof: no memory yet (NEW), a matching
    stamp (OWNED/UNBOUND), the pack's own checkout, or unstamped files that are
    all untouched templates (`templates` is the pack's `core-context/`; omitted,
    that case cannot be shown and falls through to refusal).
    """

    verdict = identity.assess(target, ops)
    git, state = verdict.git, verdict.state
    origin = "pack-source" if pack_source else "project"

    if state == identity.NEW:
        return _stamped(ops, new_stamp(git, "init", origin), "stamped new memory")
    if state in (identity.OWNED, identity.UNBOUND):
        return _keep_owned(verdict, ops, claim, reset)
    if reset:
        return _reset(verdict, ops, origin)
    if claim or pack_source:
        how = "claim-memory" if claim else "pack-source"
        stamp = new_stamp(git, how, origin, previous=verdict.stamp)
        return _stamped(ops, stamp, f"CLAIMED existing memory ({how})")
    if not _needs_choice(verdict, ops, templates, ops_relative):
        return _stamped(ops, new_stamp(git, "init", origin), "stamped a folder of untouched templates (no memory in it)")
    return _refusal(verdict, ops, command)


def _needs_choice(verdict: Verdict, ops: Path, templates: Path | None, ops_relative: str) -> bool:
    """Unproven memory needs --claim-memory or --reset-memory, unless it holds no memory at all."""

    if not verdict.unproven:
        return False
    untouched = verdict.state == identity.LEGACY and templates is not None
    return not (untouched and holds_only_templates(ops, templates, ops_relative))


def preflight_refusal(target: Path, ops: Path, *, templates: Path, ops_relative: str,
                      command: Callable[[str], str]) -> Gate | None:
    """The refusal init would print without a memory flag, decided without writing anything.

    Lets a caller such as `embed_pack.py --update` stop before it changes the
    pack, instead of refreshing it and only then learning init will refuse.
    """

    verdict = identity.assess(target, ops)
    return _refusal(verdict, ops, command) if _needs_choice(verdict, ops, templates, ops_relative) else None


def _keep_owned(verdict: Verdict, ops: Path, claim: bool, reset: bool) -> Gate:
    """OWNED or UNBOUND memory: keep it, binding an unbound stamp once history exists."""

    notes = []
    if reset or claim:
        flag = "--reset-memory" if reset else "--claim-memory"
        notes.append(
            f"{flag}: nothing done -- this memory already belongs to this project "
            "(a repeated flag must never wipe or rewrite memory built since)."
        )
    if verdict.state == identity.UNBOUND and verdict.git.state == "commits":
        gate = _stamped(ops, bound_stamp(verdict.stamp or {}, verdict.git), "BOUND to this repository's history")
    else:
        detail = "unbound until the first commit exists" if verdict.state == identity.UNBOUND else "owned by this project"
        gate = Gate(lines=[f"OWNERSHIP: {verdict.state} ({detail}; {identity.owner_summary(verdict.stamp)})"])
    gate.lines += notes
    return gate

#!/usr/bin/env python3
"""Write the shipping set into a host's pack folder, and refresh it later.

Before either, `missing_required` proves the set is complete: a pack missing a
module its own initializer imports must be refused, not half-installed.

Ownership rules, applied identically to install and update:

* A file is removed only with proof it is an unmodified pack file (see
  pack_ownership). A modified one is kept and reported; a file no record
  mentions is never touched.
* A shipped file the host edited is overwritten, because an update that leaves
  half the tools stale is worse than none -- but the host's version is first
  copied to `.update-backup/<timestamp>/<path>` so no edit is ever lost.
* `_agent_ops/` (project memory), PACK_VERSION, the manifest and the backup
  folder are never candidates for either action.
"""

from __future__ import annotations

import ast
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pack_manifest import MANIFEST_FILE, STAMP_FILE, git_tracked, is_denied  # noqa: E402
from pack_manifest import shipped_bytes, shipping_set  # noqa: E402
from pack_manifest import strip_managed_blocks, write_manifest  # noqa: E402
from pack_ownership import Baseline, load_baseline  # noqa: E402

BACKUP_DIR = ".update-backup"
RESERVED_TOP = {"_agent_ops", BACKUP_DIR, ".git"}
RESERVED_FILES = {STAMP_FILE, MANIFEST_FILE}


@dataclass
class SyncReport:
    written: int = 0
    unchanged: int = 0
    backed_up: list[str] = field(default_factory=list)
    backup_dir: Path | None = None
    removed: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    unproven: list[str] = field(default_factory=list)
    baseline: str = ""


def is_reserved(rel: str) -> bool:
    parts = rel.split("/")
    return (
        parts[0] in RESERVED_TOP
        or rel in RESERVED_FILES
        or "__pycache__" in parts
        or rel.endswith((".pyc", ".pyo"))
    )


def _inside(child: Path, parent: Path) -> bool:
    try:
        Path(os.path.normcase(child)).relative_to(os.path.normcase(parent))
    except ValueError:
        return False
    return True


def classify_overlap(source: Path, destination: Path) -> str:
    """How the source pack and the install destination relate on disk.

    `same` is a legitimate in-place install (the pack was copied into the host
    by hand); either nesting is an error, checked BEFORE any file is written.
    """

    source, destination = source.resolve(), destination.resolve()
    if _inside(source, destination) and _inside(destination, source):
        return "same"
    if _inside(destination, source):
        return "destination-inside-source"
    if _inside(source, destination):
        return "source-inside-destination"
    return "none"


# The installer's own entry points: what a host runs (`init_project_ops.py`) and
# what ships next to it. Everything else the pack needs at runtime is DERIVED from
# these by following their imports, so a new helper module cannot be forgotten.
ROOT_SCRIPTS = ("init_project_ops.py", "embed_pack.py", "migrate_pack.py")
# Files `looks_like_pack` and the agent entry chain need beyond scripts/templates.
REQUIRED_FILES = ("TEAM_ROUTER.md", "AGENTS.md")
# The one list init copies tools from; named so a tool missing from DISK is caught.
TOOL_LIST_NAME = "RUNTIME_TOOLS"
_SCRIPT_NAME = re.compile(r"\w+\.py")
_TEMPLATE_NAME = re.compile(r"[\w.-]+\.template\.md")
# Python before 3.10 has no list of stdlib modules: there only imports that find
# a sibling script on disk are followed.
_STDLIB = getattr(sys, "stdlib_module_names", None)


@dataclass
class ScriptRefs:
    modules: set[str] = field(default_factory=set)    # imported top-level names
    strings: set[str] = field(default_factory=set)    # every string constant
    declared: set[str] = field(default_factory=set)   # entries of TOOL_LIST_NAME


def _script_refs(path: Path) -> ScriptRefs:
    """What one script imports and names.

    Function-level imports are included (init imports its indexers lazily), and
    so are string constants: init reads its `TEMPLATE_MAP` templates by name, not
    by import.
    """

    refs = ScriptRefs()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, ValueError):
        return refs
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            refs.modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            refs.modules.add(node.module.split(".")[0])
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            refs.strings.add(node.value)
        elif isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == TOOL_LIST_NAME for target in node.targets
        ):
            refs.declared.update(
                item.value for item in ast.walk(node.value)
                if isinstance(item, ast.Constant) and isinstance(item.value, str)
            )
    return refs


def _next_scripts(refs: ScriptRefs, present: set[str]) -> list[str]:
    """Scripts a script depends on: local imports, declared tools, named siblings.

    A non-stdlib import with no file on disk is still a dependency (the pack is
    stdlib-only, so it can only be a sibling script that went missing).
    """

    names = [
        f"{module}.py" for module in refs.modules
        if f"{module}.py" in present or (_STDLIB is not None and module not in _STDLIB)
    ]
    names += [text for text in refs.declared if _SCRIPT_NAME.fullmatch(text)]
    names += [text for text in refs.strings if _SCRIPT_NAME.fullmatch(text) and text in present]
    return names


def required_files(source: Path) -> set[str]:
    """Files the pack cannot run without, as posix paths.

    Derived, not listed: the closure of `scripts/*.py` reachable from ROOT_SCRIPTS
    by import, by init's tool list, or by naming a sibling script, plus every
    `*.template.md` those scripts name under `core-context/`. A hand-kept list
    goes stale the day a script gains an import; the closure cannot.
    """

    present = {path.name for path in (source / "scripts").glob("*.py")}
    scripts: set[str] = set()
    templates: set[str] = set()
    queue = list(ROOT_SCRIPTS)
    while queue:
        name = queue.pop()
        if name in scripts:
            continue
        scripts.add(name)
        refs = _script_refs(source / "scripts" / name)
        queue += _next_scripts(refs, present)
        templates.update(text for text in refs.strings if _TEMPLATE_NAME.fullmatch(text))
    return (
        set(REQUIRED_FILES)
        | {f"scripts/{name}" for name in scripts}
        | {f"core-context/{name}" for name in templates}
    )


def missing_required(source: Path) -> dict[str, str]:
    """Required files the shipping set would leave out, each with the reason."""

    shipped = shipping_set(source)
    tracked = git_tracked(source)
    missing: dict[str, str] = {}
    for rel in sorted(required_files(source) - shipped):
        if not (source / rel).is_file():
            missing[rel] = "absent from the source checkout"
        elif is_denied(rel):
            missing[rel] = "excluded as local state"
        elif tracked is not None and rel not in tracked:
            missing[rel] = f"untracked: git add {rel} (staging is enough, no commit needed)"
        else:
            missing[rel] = "not in the shipping set"
    return missing


def materialize(source: Path, rel: str, target: Path) -> None:
    """Write one shipped file, keeping timestamps and mode where it is a plain copy."""

    target.parent.mkdir(parents=True, exist_ok=True)
    data = shipped_bytes(source, rel)
    if data == (source / rel).read_bytes():
        shutil.copy2(source / rel, target)
        return
    target.write_bytes(data)
    shutil.copymode(source / rel, target)


def install_pack(source: Path, destination: Path, version: str) -> int:
    """Fresh install: write every shipped file, then record what was written."""

    shipped = shipping_set(source)
    for rel in sorted(shipped):
        materialize(source, rel, destination / rel)
    write_manifest(destination, version, shipped)
    return len(shipped)


def strip_in_place(pack_dir: Path) -> bool:
    """In-place install: drop a generated self-bridge block from the pack's AGENTS.md."""

    agents = pack_dir / "AGENTS.md"
    if not agents.is_file():
        return False
    text = agents.read_text(encoding="utf-8")
    stripped = strip_managed_blocks(text)
    if stripped == text:
        return False
    agents.write_bytes(stripped.encode("utf-8"))
    return True


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def new_backup_root(destination: Path) -> Path:
    """A backup folder no earlier update owns.

    `mkdir` without `exist_ok` is the claim: two updates in the same second get
    `<stamp>` and `<stamp>-1` instead of the second silently overwriting the
    first one's saved edits. Being exclusive to this run, nothing in it can
    already exist, so a backup file is never overwritten either.
    """

    parent = destination / BACKUP_DIR
    parent.mkdir(parents=True, exist_ok=True)
    stamp = _timestamp()
    for attempt in range(10_000):
        root = parent / (stamp if attempt == 0 else f"{stamp}-{attempt}")
        try:
            root.mkdir()
        except FileExistsError:
            continue
        return root
    raise OSError(f"cannot allocate a backup folder under {parent}")


def _backup(destination: Path, backup_root: Path, rel: str) -> None:
    saved = backup_root / rel
    saved.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(destination / rel, saved)


def _refresh_shipped(source: Path, destination: Path, shipped: set[str],
                     baseline: Baseline, report: SyncReport) -> None:
    for rel in sorted(shipped):
        target = destination / rel
        new = shipped_bytes(source, rel)
        if target.is_file():
            current = target.read_bytes()
            if current == new:
                report.unchanged += 1
                continue
            if not baseline.unmodified(rel, current):
                if report.backup_dir is None:
                    report.backup_dir = new_backup_root(destination)
                _backup(destination, report.backup_dir, rel)
                report.backed_up.append(rel)
        materialize(source, rel, target)
        report.written += 1


def _walk_destination(destination: Path) -> list[str]:
    found: list[str] = []
    for current, dirs, files in os.walk(destination):
        dirs[:] = [name for name in dirs if name not in RESERVED_TOP and name != "__pycache__"]
        for name in files:
            rel = (Path(current) / name).relative_to(destination).as_posix()
            if not is_reserved(rel):
                found.append(rel)
    return sorted(found)


def _stale_candidates(destination: Path, shipped: set[str], baseline: Baseline) -> list[str]:
    """Files an earlier install may have written that this revision no longer ships."""

    if baseline.kind == "none":
        return []
    known = baseline.known_paths()
    return [rel for rel in _walk_destination(destination) if rel in known and rel not in shipped]


def _remove_stale(destination: Path, shipped: set[str], baseline: Baseline,
                  report: SyncReport) -> None:
    removed_dirs: set[Path] = set()
    for rel in _stale_candidates(destination, shipped, baseline):
        path = destination / rel
        if baseline.unmodified(rel, path.read_bytes()):
            path.unlink()
            report.removed.append(rel)
            removed_dirs.add(path.parent)
        else:
            report.conflicts.append(rel)
    if baseline.kind == "none":
        report.unproven = [rel for rel in _walk_destination(destination) if rel not in shipped]
    for directory in sorted(removed_dirs, key=lambda item: len(item.parts), reverse=True):
        while directory != destination and directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
            directory = directory.parent


def update_pack(source: Path, destination: Path, version: str, previous: str) -> SyncReport:
    """Refresh a pack folder to the source's shipping set under the ownership rules.

    Returns what was written, backed up, removed and left alone. Conflicts (a
    modified file the pack no longer ships) are dropped from the new manifest:
    the host edited them, so after this report they are the host's.
    """

    report = SyncReport()
    shipped = shipping_set(source)
    baseline = load_baseline(destination, source, previous)
    report.baseline = baseline.label
    _refresh_shipped(source, destination, shipped, baseline, report)
    _remove_stale(destination, shipped, baseline, report)
    write_manifest(destination, version, shipped)
    return report

#!/usr/bin/env python3
"""Who owns a project's `_agent_ops/` memory.

Memory is only true for the project that wrote it. Copying a repository -- or a
pack that ships its own memory -- drops one project's task, decisions and rules
into another, and every later session then resumes them as fact. This module is
the one place that answers "is this memory ours?": init refuses or repairs on
the answer, session_start reports it, and neither re-derives it.

Identity is the git ROOT commit(s) plus a generated project id, recorded in a
tracked `OPS_OWNER.json`. Not the absolute path (differs on every machine) and
not HEAD (differs on every commit). A clone shares its root commits, so a valid
clone keeps its memory with no manual step.

States:

  NEW           no memory yet
  OWNED         the stamp's root commit(s) intersect this checkout's
  UNBOUND       a VALID stamp that recorded no root commit (made before the
                first commit); the next init binds it
  FOREIGN       the stamp is bound, this checkout has history, no intersection
  UNVERIFIABLE  ownership cannot be shown: the stamp is bound but this checkout
                cannot show its history (no git, no commits, shallow clone), or
                the stamp is unreadable, incomplete or from a newer schema
  LEGACY        memory exists with no stamp (installed before stamps existed)

Only NEW, OWNED and UNBOUND are PROVEN (`Verdict.unproven` is False). Everything
else must be confirmed by a person before any record is read as this project's.

Read-only. The stamp is written by `ops_gate`, the one writer.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

# Running a tool must never leave __pycache__ inside someone else's repository.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from source_state import DEFAULT_OPS_FOLDER, looks_like_pack  # noqa: E402


OWNER_FILE = "OPS_OWNER.json"
SCHEMA = 1
MAX_STORED_ROOTS = 64
# A real stamp is a few hundred bytes (64 roots at most ~4 KB); a larger file is
# not one, and refusing it up front keeps a hostile file from reaching the parser.
MAX_STAMP_BYTES = 16_384
ORIGINS = ("project", "pack-source")
# Exactly what `ops_gate.new_stamp` always writes. A stamp missing any of these,
# or carrying anything else, is damaged or foreign-made, so it is never bound.
STAMP_FIELDS = ("schema", "project_id", "root_commits", "origin", "established", "established_by")
OPTIONAL_STAMP_FIELDS = ("previous_project_id", "bound")

NEW, OWNED, UNBOUND = "NEW", "OWNED", "UNBOUND"
FOREIGN, UNVERIFIABLE, LEGACY = "FOREIGN", "UNVERIFIABLE", "LEGACY"

# Records only a project writes about itself. Their presence is what makes a
# folder "memory" rather than an empty skeleton of templates and tools.
MEMORY_RECORDS = (
    "PROJECT_CONTEXT_CARD.md",
    "SESSION_BRIEF.md",
    "CURRENT_TASK.md",
    "IMPLEMENTATION_LOG.md",
    "DECISION_LOG.md",
    "RISK_REGISTER.md",
    "PHASE_ROADMAP.md",
    "HANDOFF.md",
)
# Pack-generated policy reads the same in every project, so it carries no
# evidence about whose memory this is and is skipped when looking for any.
GENERATED_POLICY = ("INDEX.md", "SESSION_PROTOCOL.md", "OPERATING_RULES.md", "README.md")
# Rebuilt from source by a script, so its presence says nothing about memory.
DERIVED_RECORDS = ("REPO_MAP.md",)

# Tokens that appear in memory only when the work was ON the pack: they name its
# own build scripts, code identifiers and test files. A project that merely USES
# the pack names its folder, `@start-here`, a team, `init_project_ops.py` or
# `TEAM_ROUTER.md` all the time -- those are deliberately absent, because
# counting them would turn every honest embedded install into a "foreign" one.
PACK_DEV_SIGNATURES = (
    "embed_pack.py",
    "migrate_pack.py",
    "RUNTIME_TOOLS",
    "TEMPLATE_MAP",
    "ADAPTER_MARKER",
    "AGENTS_BRIDGE_BEGIN",
    "BRIDGE_VERSION",
    "test_workspace_tools",
    "test_closure_check",
    "test_java_csharp",
)
# One stray mention (a bootstrap log line saying "ran embed_pack.py") is normal;
# three distinct pack-internal names is a record of developing the pack.
PACK_EVIDENCE_THRESHOLD = 3
RECORD_READ_LIMIT = 1_000_000
RECORD_FILE_LIMIT = 80
# A stamp is read from a file anyone can edit and its values become git
# arguments, so only a full commit hash is ever passed on. `fullmatch`, not `$`:
# `$` also accepts a trailing newline, which would reach git as part of the hash.
_SHA_RE = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
_ID_RE = re.compile(r"[0-9a-f]{32}")
_DAY_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


@dataclass(frozen=True)
class GitIdentity:
    """What this checkout can say about its own history."""

    state: str  # "commits" | "no-commits" | "no-git" | "shallow"
    roots: tuple[str, ...] = ()


@dataclass(frozen=True)
class Verdict:
    state: str
    detail: str
    git: GitIdentity
    stamp: dict | None = None
    evidence: tuple[str, ...] = ()
    suspect: bool = False  # LEGACY memory that looks like the pack's own

    @property
    def foreign_like(self) -> bool:
        """Memory worded as another project's: stamped for another repository, or
        unstamped and describing the workspace pack itself."""

        return self.state == FOREIGN or (self.state == LEGACY and self.suspect)

    @property
    def unproven(self) -> bool:
        """Ownership not established: nothing here may be resumed as this project's.

        False only for NEW (nothing to trust), OWNED (root commit matches) and
        UNBOUND (a valid stamp init wrote in this repository before its first
        commit). Absence of a foreign signature is not proof, so UNVERIFIABLE
        and LEGACY memory is unproven however innocent it looks.
        """

        return self.state not in (NEW, OWNED, UNBOUND)


def run_git(root: Path, *args: str) -> str | None:
    """Stdout of one git command, or None on any failure (including no git)."""

    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def git_identity(root: Path, owned: tuple[str, ...] = ()) -> GitIdentity:
    """Root commits of this checkout, or why none can be read.

    `owned` are the stamp's roots. Asking git whether one is an ancestor of HEAD
    answers "same project?" without walking the whole history, which on a very
    large repository is the difference between milliseconds and seconds on every
    session start; only a miss pays for the full enumeration.

    `--branches` joins HEAD so a checkout on an orphan branch still sees the
    project's real root; a false "foreign" stops work, a false "owned" needs a
    pathological merge. A shallow clone's boundary commits look like roots but
    are not, so it reports as shallow and is never compared as if it were whole.
    """

    if run_git(root, "rev-parse", "--is-inside-work-tree") != "true":
        return GitIdentity("no-git")
    if not run_git(root, "rev-parse", "--verify", "--quiet", "HEAD"):
        return GitIdentity("no-commits")
    for sha in owned:
        if run_git(root, "merge-base", "--is-ancestor", sha, "HEAD") is not None:
            return GitIdentity("commits", (sha,))
    roots = tuple(sorted(set((run_git(root, "rev-list", "--max-parents=0", "HEAD", "--branches") or "").split())))
    shallow = run_git(root, "rev-parse", "--is-shallow-repository") == "true"
    return GitIdentity("shallow" if shallow else "commits", roots)


def _is_id(value: object) -> bool:
    return isinstance(value, str) and _ID_RE.fullmatch(value) is not None


def _is_day(value: object) -> bool:
    if not isinstance(value, str) or _DAY_RE.fullmatch(value) is None:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _is_roots(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) <= MAX_STORED_ROOTS
        and all(isinstance(item, str) and _SHA_RE.fullmatch(item) for item in value)
    )


def stamp_problem(data: object) -> str | None:
    """Why `data` is not a stamp this pack writes, or None when it is one.

    Strict on purpose: a partial stamp such as `{}` has no root commit, which
    would read as "made before the first commit" and let init bind it to
    whatever repository it was copied into. The reason names fields, never their
    values -- the file is untrusted and this text reaches an agent's context.
    """

    if not isinstance(data, dict):
        return "it is not a JSON object"
    if "schema" in data and (type(data["schema"]) is not int or data["schema"] != SCHEMA):
        return f"unsupported schema (this tool reads schema {SCHEMA}; a newer pack may have written it)"
    missing = [key for key in STAMP_FIELDS if key not in data]
    if missing:
        return "missing " + ", ".join(missing)
    unknown = [key for key in data if key not in STAMP_FIELDS + OPTIONAL_STAMP_FIELDS]
    if unknown:
        return f"{len(unknown)} unknown field(s)"
    by = data["established_by"]
    checks = {
        "project_id": _is_id(data["project_id"]),
        "root_commits": _is_roots(data["root_commits"]),
        "origin": data["origin"] in ORIGINS,
        "established": _is_day(data["established"]),
        "established_by": isinstance(by, str) and 0 < len(by) <= 40,
        "previous_project_id": "previous_project_id" not in data or _is_id(data["previous_project_id"]),
        "bound": "bound" not in data or _is_day(data["bound"]),
    }
    bad = [name for name, ok in checks.items() if not ok]
    return "invalid " + ", ".join(bad) if bad else None


def _corrupt(why: str) -> dict:
    return {"corrupt": True, "why": why}


def read_stamp(ops: Path) -> dict | None:
    """The ownership stamp: None when absent, `{"corrupt": True, "why": ...}` when unusable."""

    path = ops / OWNER_FILE
    if not (path.exists() or path.is_symlink()):
        return None
    if path.is_symlink() or not path.is_file():
        return _corrupt("it is not a regular file")  # a link could point at someone else's stamp
    try:
        if path.stat().st_size > MAX_STAMP_BYTES:
            return _corrupt("it is too large to be a stamp")
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError):
        return _corrupt("it is not readable JSON")
    problem = stamp_problem(data)
    return _corrupt(problem) if problem else data


def stamp_roots(stamp: dict) -> tuple[str, ...]:
    roots = stamp.get("root_commits")
    if not isinstance(roots, list):
        return ()
    return tuple(item for item in roots if isinstance(item, str) and _SHA_RE.fullmatch(item))


def has_memory(ops: Path) -> bool:
    """True when anything a project wrote about itself is under `ops`.

    Not only the named records: a folder holding just an archived log or a phase
    card is still somebody's memory, and calling it NEW would let init adopt it
    without being asked. Pack-generated policy and the derived repo map are not.
    """

    if any((ops / name).is_file() for name in MEMORY_RECORDS):
        return True
    return any(path.name not in DERIVED_RECORDS for path in authored_records(ops))


def authored_records(ops: Path) -> list[Path]:
    """Markdown a project wrote itself: not generated policy, tools or backups."""

    found: list[Path] = []
    for folder in (ops, ops / "archive", ops / "phase_context_cards"):
        if folder.is_dir():
            found += [p for p in sorted(folder.glob("*.md")) if p.is_file() and p.name not in GENERATED_POLICY]
    return found[:RECORD_FILE_LIMIT]


def legacy_pack_evidence(ops: Path) -> tuple[str, ...]:
    """Pack-internal names found in project-authored records, with where.

    Evidence, not proof: it only decides whether an UNSTAMPED memory is refused
    like a foreign one. See `assess`.
    """

    found: dict[str, str] = {}
    for path in authored_records(ops):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")[:RECORD_READ_LIMIT]
        except OSError:
            continue
        for token in PACK_DEV_SIGNATURES:
            if token not in found and token in text:
                found[token] = path.name
    return tuple(f"{token} (in {name})" for token, name in found.items())


def assess(root: Path, ops: Path) -> Verdict:
    """Classify the memory under `ops` for the project checked out at `root`.

    LEGACY memory (no stamp) is unproven, however ordinary it looks. An earlier
    design claimed it unless it mentioned the pack's own internals, but absence
    of that signature proves nothing: another project's records carry none, and
    claiming them is exactly the cross-project leak the stamp exists to stop.
    The pack-internal evidence is kept only to say more in the message
    (`suspect`); init and session_start both require a person to choose.
    """

    stamp = read_stamp(ops)
    git = git_identity(root, stamp_roots(stamp) if stamp else ())
    if stamp is None:
        if not has_memory(ops):
            return Verdict(NEW, "no project memory yet", git)
        evidence = legacy_pack_evidence(ops)
        suspect = len(evidence) >= PACK_EVIDENCE_THRESHOLD and not looks_like_pack(root)
        detail = f"memory exists but {OWNER_FILE} does not (installed before ownership stamps)"
        return Verdict(LEGACY, detail, git, evidence=evidence, suspect=suspect)
    if stamp.get("corrupt"):
        return Verdict(UNVERIFIABLE, f"{OWNER_FILE} is unusable: {stamp.get('why', 'unreadable')}", git, stamp=stamp)
    return compare(stamp, git, root)


def compare(stamp: dict, git: GitIdentity, root: Path) -> Verdict:
    owned = set(stamp_roots(stamp))
    if owned & set(git.roots):
        return Verdict(OWNED, "root commit matches the ownership stamp", git, stamp=stamp)
    if not owned:
        return Verdict(UNBOUND, "stamp was made before the first commit", git, stamp=stamp)
    if git.state == "commits":
        return Verdict(FOREIGN, "stamp root commit(s) are not in this repository's history", git, stamp=stamp)
    reasons = {
        "no-git": "this directory is not a git repository",
        "no-commits": "this repository has no commits yet",
        "shallow": "this is a shallow clone, so its root commits are unknown (`git fetch --unshallow` can settle it)",
    }
    # A bound stamp from the pack's own source is never this project's, whatever
    # git can or cannot show: only a pack checkout legitimately holds it.
    if stamp.get("origin") == "pack-source" and not looks_like_pack(root):
        return Verdict(FOREIGN, "stamped by the workspace pack's own source repository", git, stamp=stamp)
    return Verdict(UNVERIFIABLE, reasons.get(git.state, "history unreadable"), git, stamp=stamp)


def short(sha: str) -> str:
    return sha[:10]


def owner_summary(stamp: dict | None) -> str:
    if not stamp or stamp.get("corrupt"):
        return "unknown owner"
    roots = ", ".join(short(r) for r in stamp_roots(stamp)[:3]) or "none recorded"
    return f"project {str(stamp.get('project_id', '?'))[:8]}, root commit {roots}"


def host_summary(git: GitIdentity) -> str:
    if git.state in ("commits", "shallow") and git.roots:
        return "root commit " + ", ".join(short(r) for r in git.roots[:3])
    return {"no-git": "not a git repository", "no-commits": "no commits yet"}.get(git.state, "history unknown")


def reason_lines(verdict: Verdict) -> list[str]:
    """Why a verdict is not OWNED, in terms a reader can check."""

    lines = [f"- {verdict.detail}."]
    if verdict.stamp and not verdict.stamp.get("corrupt"):
        lines.append(f"- Memory belongs to: {owner_summary(verdict.stamp)}.")
        lines.append(f"- This repository: {host_summary(verdict.git)}.")
    if verdict.evidence:
        lines.append("- Pack-internal names found in its records: " + "; ".join(verdict.evidence[:6]) + ".")
    return lines


def init_command_hint(root: Path, ops: Path, flag: str) -> str:
    """The init command a runtime tool can name, given only where ops lives.

    init_project_ops.py is not copied into a project (it needs the pack's
    templates), so a runtime tool can only name the pack by its install folder.
    """

    try:
        reference = ops.relative_to(root).as_posix()
    except ValueError:
        reference = ""
    suffix = "/" + DEFAULT_OPS_FOLDER
    folder = reference[: -len(suffix)] if reference.endswith(suffix) else ""
    if folder and looks_like_pack(root / folder):
        return f"python {folder}/scripts/init_project_ops.py --target . {flag}"
    if reference == DEFAULT_OPS_FOLDER and looks_like_pack(root):
        return f"python scripts/init_project_ops.py --target . {flag}"  # inside the pack itself
    extra = "" if reference in ("", DEFAULT_OPS_FOLDER) else f" --ops-folder {reference}"
    return f"python <pack>/scripts/init_project_ops.py --target .{extra} {flag}"

#!/usr/bin/env python3
"""Keep pack-generated policy current without overwriting project customization.

SESSION_PROTOCOL.md, OPERATING_RULES.md and INDEX.md are rendered from the
pack's templates, then live in the project. init used to keep them forever, so a
policy fix in the pack never reached a project that already had them. They are
also the files a project is most likely to have edited. Both facts are true, so
init needs to know which of the two a given file is -- and it records that at
generation time instead of guessing later.

`OPS_POLICY.json` maps each generated file to the hash of the text init wrote.
A file that still matches its recorded hash is the pack's, and is refreshed.
One that differs is the project's, and is kept and reported. A file with no
record (installed before this existed) is refreshed only when its text is
provably something the pack generated; otherwise it is kept. Ownership that
cannot be proven is never overwritten.

Not copied into projects; init and `embed_pack.py --update` call it.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# Running a tool must never leave __pycache__ inside someone else's repository.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ops_identity import run_git  # noqa: E402

POLICY_FILE = "OPS_POLICY.json"
POLICY_TEMPLATES = {
    "INDEX.template.md": "INDEX.md",
    "SESSION_PROTOCOL.template.md": "SESSION_PROTOCOL.md",
    "OPERATING_RULES.template.md": "OPERATING_RULES.md",
}
TEMPLATE_DIR_IN_PACK = "core-context"
HISTORY_LIMIT = 300


@dataclass(frozen=True)
class PolicyResult:
    """What happened to one generated file. `action` is one of WRITE, REFRESH,
    CURRENT, RECORD, KEEP-CUSTOMIZED, KEEP-UNPROVEN, WARN."""

    name: str
    action: str
    message: str


def render(template_text: str, ops_relative: str) -> str:
    """The text init writes for a template. One definition, so a hash recorded
    at generation time and a rendering computed later can never disagree."""

    return template_text.replace("_agent_ops", ops_relative)


def digest(text: str) -> str:
    """Hash that ignores line-ending style: a checkout with autocrlf rewrites
    every line ending, and that must not make an untouched file look edited."""

    return "sha256:" + hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def read_manifest(ops: Path) -> dict[str, str]:
    path = ops / POLICY_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    files = data.get("generated") if isinstance(data, dict) else None
    if not isinstance(files, dict):
        return {}
    return {name: value for name, value in files.items() if isinstance(name, str) and isinstance(value, str)}


def write_manifest(ops: Path, entries: dict[str, str]) -> None:
    body = json.dumps({"schema": 1, "generated": entries}, indent=2, sort_keys=True) + "\n"
    path = ops / POLICY_FILE
    # Rewritten only on change, so a no-op re-init leaves no diff in a tracked file.
    if path.is_file() and path.read_text(encoding="utf-8", errors="ignore").replace("\r\n", "\n") == body:
        return
    path.write_text(body, encoding="utf-8")


def _template_blobs(history_root: Path, template: str) -> list[bytes]:
    """Every committed version of one template, via a single git process."""

    path = f"{TEMPLATE_DIR_IN_PACK}/{template}"
    try:
        log = subprocess.run(
            ["git", "log", "--format=%H", f"-n{HISTORY_LIMIT}", "--", path],
            cwd=str(history_root), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
        )
        if log.returncode != 0 or not log.stdout.split():
            return []
        spec = "".join(f"{sha.decode()}:{path}\n" for sha in log.stdout.split()).encode()
        batch = subprocess.run(
            ["git", "cat-file", "--batch"],
            cwd=str(history_root), input=spec, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
        )
    except OSError:
        return []
    data, position, blobs = batch.stdout, 0, []
    while position < len(data):
        end = data.find(b"\n", position)
        if end < 0:
            break
        header = data[position:end].split()
        position = end + 1
        if len(header) == 3 and header[1] == b"blob":
            size = int(header[2])
            blobs.append(data[position : position + size])
            position += size + 1  # the object body is followed by one newline
    return blobs


def historical_digests(history_root: Path, template: str, ops_relative: str) -> set[str]:
    """Hashes of every rendering this template ever produced in `history_root`.

    A project that predates the manifest has no record of what init wrote. If
    its file equals ANY past rendering it was never edited, and refreshing it
    destroys nothing. `history_root` must be a git checkout of the pack itself.
    """

    return {
        digest(render(blob.decode("utf-8", errors="ignore"), ops_relative))
        for blob in _template_blobs(history_root, template)
    }


def policy_history_root(explicit: str | None, pack_root: Path) -> Path | None:
    """Checkout whose history identifies earlier policy renderings, if any.

    Only a pack that is its own repository qualifies. An embedded copy has no
    history of its own, and the host repository above it is not the pack's
    history -- consulting it would let a host's own commits vouch for a file.
    """

    if explicit:
        return Path(explicit).expanduser().resolve()
    top = run_git(pack_root, "rev-parse", "--show-toplevel")
    return pack_root if top and Path(top).resolve() == pack_root.resolve() else None


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def refresh_generated_policy(
    ops_dir: Path,
    templates_dir: Path,
    ops_relative: str,
    *,
    history_root: Path | None = None,
) -> list[PolicyResult]:
    """Create or refresh the pack-generated policy files under `ops_dir`.

    Public entry point (init calls it on every run; `embed_pack.py --update` may
    call it with the source pack as `history_root`).

      ops_dir        the project's `_agent_ops` folder; must exist
      templates_dir  the pack's `core-context/` folder
      ops_relative   how templates spell the ops folder, for example
                     `ai-agent-workspace-pack/_agent_ops` (the text that
                     replaces `_agent_ops` inside every rendered template)
      history_root   a git checkout of the pack, used only to recognize an
                     unrecorded legacy file as an earlier rendering; None skips
                     that and keeps such files

    Returns one PolicyResult per generated file. Writes only files whose
    ownership it can prove, and rewrites `OPS_POLICY.json` only on change.
    """

    entries = read_manifest(ops_dir)
    results: list[PolicyResult] = []
    for template_name, output_name in POLICY_TEMPLATES.items():
        template = templates_dir / template_name
        if not template.is_file():
            results.append(PolicyResult(output_name, "WARN", f"WARN missing template: {template}"))
            continue
        destination = ops_dir / output_name
        rendered = render(_read(template), ops_relative)
        result = _refresh_one(destination, rendered, entries, template_name, ops_relative, history_root)
        results.append(result)
    write_manifest(ops_dir, entries)
    return results


def _refresh_one(
    destination: Path,
    rendered: str,
    entries: dict[str, str],
    template_name: str,
    ops_relative: str,
    history_root: Path | None,
) -> PolicyResult:
    name, wanted = destination.name, digest(rendered)

    def replace(action: str, message: str) -> PolicyResult:
        destination.write_text(rendered, encoding="utf-8")
        entries[name] = wanted
        return PolicyResult(name, action, message)

    if not destination.exists():
        return replace("WRITE", f"WRITE: {destination}")
    current, recorded = digest(_read(destination)), entries.get(name)
    if current == wanted:
        entries[name] = wanted
        note = "already current" if recorded == wanted else "already current; recorded as pack-generated"
        return PolicyResult(name, "CURRENT" if recorded == wanted else "RECORD", f"SKIP existing: {destination} ({note})")
    if recorded is not None:
        if current == recorded:
            return replace("REFRESH", f"REFRESH policy: {destination} (unedited since init wrote it; now the current template)")
        return PolicyResult(
            name, "KEEP-CUSTOMIZED",
            f"KEEP customized, not refreshed: {destination} (differs from what init generated; "
            "delete it and re-run init to regenerate it from the current template)",
        )
    if history_root is not None and current in historical_digests(history_root, template_name, ops_relative):
        return replace("REFRESH", f"REFRESH policy: {destination} (matched an earlier pack rendering; now the current template)")
    return PolicyResult(
        name, "KEEP-UNPROVEN",
        f"KEEP unproven, not refreshed: {destination} (no record of what generated it and it matches no known "
        "rendering; delete it and re-run init to regenerate it)",
    )


def ensure_ignored(gitignore: Path, entries: tuple[str, ...]) -> list[str]:
    """Add missing patterns to an existing ops `.gitignore`, never removing a line.

    The file is written once at install, so a pattern added to the pack's list
    (the backup folder) would otherwise never reach an existing project -- and
    the first reset there would put a full copy of its old memory in `git status`.
    """

    present = {line.strip() for line in gitignore.read_text(encoding="utf-8", errors="ignore").splitlines()}
    missing = [entry for entry in entries if entry not in present]
    if not missing:
        return []
    text = gitignore.read_text(encoding="utf-8", errors="ignore")
    separator = "" if text.endswith("\n") or not text else "\n"
    gitignore.write_text(text + separator + "\n".join(missing) + "\n", encoding="utf-8")
    return [f"UPDATE: {gitignore} (added {', '.join(missing)})"]

#!/usr/bin/env python3
"""Proof that a file in a host project is the pack's, not merely named like it.

A path match proves nothing: a host's own `scripts/shared.py` can collide with
a pack file. Ownership is established only by content:

* an install manifest (path -> sha256 of what the install wrote), or
* for installs that predate the manifest, the Git blob the source repository
  holds for that path at the revision recorded in `PACK_VERSION`, or
* for a flat install of unknown age, the blob at ANY revision of the source
  history.

Blob ids are computed here rather than asked of Git per file, and a CRLF
rendering of a blob is accepted too: Windows checkouts with autocrlf store LF in
the index and write CRLF to disk, so the bytes in a host differ from the blob
while being the same file.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pack_manifest import is_git_root, read_manifest, sha256_bytes  # noqa: E402


def blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def content_ids(data: bytes) -> set[str]:
    """Blob ids a Git checkout could have produced these bytes from."""

    return {blob_id(data), blob_id(data.replace(b"\r\n", b"\n"))}


def _git_bytes(source: Path, args: list[str]) -> bytes | None:
    result = subprocess.run(
        ["git", *args],
        cwd=str(source),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def resolve_revision(source: Path, version: str) -> str | None:
    """A commit id for a `PACK_VERSION` value like `abc1234` or `abc1234-dirty`."""

    revision = version.removesuffix("-dirty").strip()
    if not revision or revision == "unknown" or not is_git_root(source):
        return None
    out = _git_bytes(source, ["rev-parse", "--verify", "--quiet", f"{revision}^{{commit}}"])
    return out.decode().strip() if out else None


def revision_blobs(source: Path, revision: str) -> dict[str, str]:
    """path -> blob id for every file in one commit."""

    out = _git_bytes(source, ["ls-tree", "-r", "-z", revision]) or b""
    blobs: dict[str, str] = {}
    for record in out.split(b"\0"):
        meta, _, raw_path = record.partition(b"\t")
        fields = meta.split()
        if len(fields) == 3 and fields[1] == b"blob":
            blobs[raw_path.decode("utf-8", errors="surrogateescape")] = fields[2].decode()
    return blobs


def history_blobs(source: Path) -> dict[str, set[str]]:
    """path -> every blob id that path has held in any commit of any branch."""

    if not is_git_root(source):
        return {}
    out = _git_bytes(
        source, ["log", "--all", "--no-renames", "--raw", "--no-abbrev", "--format=", "-z"]
    ) or b""
    tokens = out.split(b"\0")
    found: dict[str, set[str]] = {}
    position = 0
    while position < len(tokens):
        token = tokens[position]
        if token.startswith(b":") and position + 1 < len(tokens):
            fields = token.split()
            if len(fields) >= 5 and not fields[4].startswith(b"D"):
                path = tokens[position + 1].decode("utf-8", errors="surrogateescape")
                found.setdefault(path, set()).add(fields[3].decode())
            position += 2
        else:
            position += 1
    return found


def matches_history(data: bytes, rel: str, history: dict[str, set[str]]) -> bool:
    return bool(content_ids(data) & history.get(rel, set()))


class Baseline:
    """What a pack folder looked like when the pack last wrote it.

    `unmodified(rel, data)` is True only with positive proof; both "the host
    edited it" and "no record exists" answer False, because the caller must
    treat them the same way: never delete, and back up before overwriting.
    """

    def __init__(self, kind: str, hashes: dict[str, str] | None = None,
                 blobs: dict[str, str] | None = None, label: str = "") -> None:
        self.kind = kind  # "manifest" | "revision" | "none"
        self.label = label
        self._hashes = hashes or {}
        self._blobs = blobs or {}

    def known_paths(self) -> set[str]:
        return set(self._hashes) if self.kind == "manifest" else set(self._blobs)

    def unmodified(self, rel: str, data: bytes) -> bool:
        if self.kind == "manifest":
            return self._hashes.get(rel) == sha256_bytes(data)
        if self.kind == "revision":
            return self._blobs.get(rel) in content_ids(data)
        return False


def load_baseline(pack_dir: Path, source: Path, stamped_version: str) -> Baseline:
    """Best available proof for an installed pack folder: manifest, else revision."""

    manifest = read_manifest(pack_dir)
    if manifest is not None:
        return Baseline("manifest", hashes=manifest, label="install manifest")
    revision = resolve_revision(source, stamped_version)
    if revision:
        return Baseline("revision", blobs=revision_blobs(source, revision),
                        label=f"PACK_VERSION revision {revision[:10]}")
    return Baseline("none", label="no manifest and no usable PACK_VERSION revision")

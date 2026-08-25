#!/usr/bin/env python3
"""Basic dependency scanner for Python and JavaScript/TypeScript projects."""

from __future__ import annotations

import argparse
import ast
import json
import re
from collections import deque
from pathlib import Path


CODE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx"}
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "site-packages",
    # The agent's own memory folder. It holds a copy of these very tools, and
    # indexing them would put the tooling at the top of the project's own hot
    # files. A non-default --ops-folder name is not skipped automatically.
    "_agent_ops",
}
# A manually embedded workspace pack is infrastructure, not the target
# project's application. Without this exclusion, its own `scripts/*.py` crowd
# the map and graph of a small project. Detect the complete pack signature
# first; never skip a generic directory such as `scripts/` by name alone.
EMBEDDED_PACK_MARKERS = (
    "TEAM_ROUTER.md",
    "core-context",
    "scripts/init_project_ops.py",
)
EMBEDDED_PACK_DIRS = {
    ".claude",
    ".codex",
    "advisor-team",
    "analyze-team",
    "bug-fix-team",
    "build-team",
    "clean-code-team",
    "commands",
    "core-context",
    "examples",
    "handoff-team",
    "harness",
    "prompting-team",
    "repo-hygiene-team",
    "scripts",
    "tester-team",
}
JS_IMPORT_RE = re.compile(
    r"""(?:from\s+["']([^"']+)["']|import\s*\(?\s*["']([^"']+)["']|require\(\s*["']([^"']+)["']\s*\))"""
)


def tool_prefix(root: Path) -> str:
    """Path to invoke these tools with, as seen from `root`.

    They run both from the pack (`scripts/`) and from the copy installed inside
    a project (`_agent_ops/tools/`). A hard-coded `scripts/` in printed advice
    sends the reader of an installed project to a folder that is not there.
    """
    here = Path(__file__).resolve().parent
    try:
        return here.relative_to(root).as_posix()
    except ValueError:
        pass
    # Generated from the pack against a project that has the tools installed:
    # print the path the reader of THAT project can actually run.
    installed = root / "_agent_ops" / "tools"
    if (installed / Path(__file__).name).exists():
        return "_agent_ops/tools"
    return "scripts"


def is_embedded_pack(root: Path) -> bool:
    """True only when this root contains a complete manually embedded pack."""
    return all((root / marker).exists() for marker in EMBEDDED_PACK_MARKERS)


def should_skip_path(root: Path, path: Path, embedded_pack: bool) -> bool:
    """Keep project code, excluding generic artifacts and detected pack internals."""
    try:
        rel_parts = path.relative_to(root).parts
    except ValueError:
        return True
    if any(part in SKIP_DIRS for part in rel_parts):
        return True
    return bool(embedded_pack and rel_parts and rel_parts[0] in EMBEDDED_PACK_DIRS)


def iter_code_files(root: Path) -> list[Path]:
    files: list[Path] = []
    embedded_pack = is_embedded_pack(root)
    for path in root.rglob("*"):
        if should_skip_path(root, path, embedded_pack):
            continue
        if path.is_file() and path.suffix in CODE_SUFFIXES:
            files.append(path)
    return files


def py_imports(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return []
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = "." * node.level + (node.module or "")
            imports.append(base)
    return imports


def js_imports(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    imports: list[str] = []
    for match in JS_IMPORT_RE.finditer(text):
        imports.append(next(group for group in match.groups() if group))
    return imports


def imports_for(path: Path) -> list[str]:
    if path.suffix == ".py":
        return py_imports(path)
    return js_imports(path)


PY_SUFFIXES = [".py"]


def _first_existing(root: Path, candidates: list[Path]) -> Path | None:
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            try:
                candidate.relative_to(root)
            except ValueError:
                return None
            return candidate
    return None


def import_bases(root: Path, source: Path) -> list[Path]:
    """Directories that could act as the import root for an absolute import.

    A repo's modules are almost never importable from the repository root alone.
    A flat `scripts/` folder imports its siblings, a `src/` layout imports from
    `src/`, and a monorepo package imports from its own package root. Rather
    than guess which layout this is, walk every ancestor of the source file,
    nearest first, and stop at the repository root. Nearest-first matters: it
    prefers the sibling module over a same-named file higher up the tree.
    """
    bases: list[Path] = []
    current = source.parent
    while True:
        bases.append(current)
        if current == root or current.parent == current:
            break
        current = current.parent
        try:
            current.relative_to(root)
        except ValueError:
            break
    if root not in bases:
        bases.append(root)
    return bases


def resolve_python_import(root: Path, source: Path, import_name: str) -> tuple[Path | None, str]:
    """Resolve a Python import, which is a dotted module name, not a path.

    `from ..models.user import User` arrives here as `..models.user`. Treating
    that as a filesystem path (as the generic branch does) never matches, so
    Python fan-in silently came out empty before this existed.

    A relative import names its own base directory, so a hit is `exact`. An
    absolute import (`from scan_deps import ...`, `from app.models import ...`)
    depends on what is on `sys.path` at runtime, which static analysis cannot
    know; a hit there is a `heuristic` lead, not a proof.
    """
    level = len(import_name) - len(import_name.lstrip("."))
    remainder = import_name[level:]
    parts = [part for part in remainder.split(".") if part]

    if level:
        base = source.parent
        for _ in range(level - 1):
            base = base.parent
        bases, confidence = [base], "exact"
    else:
        if not parts:
            return None, "exact"
        bases, confidence = import_bases(root, source), "heuristic"

    for base in bases:
        if not parts:
            hit = _first_existing(root, [base / "__init__.py"])
        else:
            target = base.joinpath(*parts)
            hit = _first_existing(
                root,
                [target.with_suffix(suffix) for suffix in PY_SUFFIXES] + [target / "__init__.py"],
            )
        if hit is not None:
            return hit, confidence
    return None, confidence


JS_SUFFIXES = [".py", ".js", ".jsx", ".ts", ".tsx"]


def resolve_js_import(root: Path, source: Path, import_name: str) -> tuple[Path | None, str]:
    """Resolve a JS/TS specifier.

    `./x` and `/x` are paths, so a hit is `exact`. A bare specifier containing a
    slash (`components/Button`) is usually a `baseUrl`/`paths` alias, which is
    configured outside the source file; probing ancestors finds it but the hit is
    a `heuristic`. A single-word specifier (`react`, `fs`) is a package name and
    is never probed -- that is where false edges would come from.
    """
    if import_name.startswith((".", "/")):
        if import_name.startswith("/"):
            candidate_base = (root / import_name.lstrip("/")).resolve()
        else:
            candidate_base = (source.parent / import_name).resolve()
        candidates = [candidate_base]
        candidates += [candidate_base.with_suffix(suffix) for suffix in JS_SUFFIXES]
        candidates += [candidate_base / f"index{suffix}" for suffix in JS_SUFFIXES]
        return _first_existing(root, candidates), "exact"

    if "/" not in import_name or import_name.startswith("@"):
        return None, "exact"

    for base in import_bases(root, source):
        candidate_base = base / import_name
        candidates = [candidate_base]
        candidates += [candidate_base.with_suffix(suffix) for suffix in JS_SUFFIXES]
        candidates += [candidate_base / f"index{suffix}" for suffix in JS_SUFFIXES]
        hit = _first_existing(root, candidates)
        if hit is not None:
            return hit, "heuristic"
    return None, "heuristic"


def resolve_import(root: Path, source: Path, import_name: str) -> tuple[Path | None, str]:
    """Resolve one import to a file in this repo, with a provenance tag."""
    if source.suffix == ".py":
        return resolve_python_import(root, source, import_name)
    return resolve_js_import(root, source, import_name)


def resolve_relative_import(root: Path, source: Path, import_name: str) -> Path | None:
    """Path-only view of `resolve_import`, kept for callers that ignore provenance."""
    return resolve_import(root, source, import_name)[0]


def build_graph(root: Path) -> dict[str, dict[str, list[str]]]:
    graph: dict[str, dict[str, list[str]]] = {}
    files = iter_code_files(root)
    for path in files:
        rel = path.relative_to(root).as_posix()
        imports = imports_for(path)
        resolved: list[str] = []
        for item in imports:
            target = resolve_relative_import(root, path, item)
            if target:
                resolved.append(target.relative_to(root).as_posix())
        graph[rel] = {"imports": imports, "resolved": sorted(set(resolved))}
    return graph


def reverse_edges(graph: dict[str, dict[str, list[str]]]) -> dict[str, set[str]]:
    reverse: dict[str, set[str]] = {node: set() for node in graph}
    for source, data in graph.items():
        for target in data["resolved"]:
            reverse.setdefault(target, set()).add(source)
    return reverse


def find_seed_nodes(graph: dict[str, dict[str, list[str]]], seeds: list[str]) -> set[str]:
    if not seeds:
        return set(graph)
    lowered = [seed.lower() for seed in seeds]
    matches: set[str] = set()
    for file_name, data in graph.items():
        haystack = " ".join([file_name] + data["imports"]).lower()
        if any(seed in haystack for seed in lowered):
            matches.add(file_name)
    return matches


def expand(graph: dict[str, dict[str, list[str]]], seeds: set[str], hops: int) -> set[str]:
    reverse = reverse_edges(graph)
    seen = set(seeds)
    queue: deque[tuple[str, int]] = deque((node, 0) for node in seeds)
    while queue:
        node, depth = queue.popleft()
        if depth >= hops:
            continue
        neighbors = set(graph.get(node, {}).get("resolved", [])) | reverse.get(node, set())
        for neighbor in neighbors:
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append((neighbor, depth + 1))
    return seen


def markdown_report(graph: dict[str, dict[str, list[str]]], affected: set[str], seeds: set[str]) -> str:
    lines = ["# Dependency Scan", "", f"Seed files: {len(seeds)}", f"Affected files: {len(affected)}", ""]
    for file_name in sorted(affected):
        marker = "seed" if file_name in seeds else "affected"
        imports = graph[file_name]["imports"]
        resolved = graph[file_name]["resolved"]
        lines.append(f"## {file_name} ({marker})")
        lines.append("")
        lines.append("Imports: " + (", ".join(imports) if imports else "none"))
        lines.append("Resolved local deps: " + (", ".join(resolved) if resolved else "none"))
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan simple Python and JS/TS imports.")
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument("--seed", default="", help="Comma-separated keywords to seed affected files.")
    parser.add_argument("--hops", type=int, default=1, help="Dependency hops to include.")
    parser.add_argument("--output", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        parser.error(f"Root must be an existing directory: {root}")

    seeds = [item.strip() for item in args.seed.split(",") if item.strip()]
    graph = build_graph(root)
    seed_nodes = find_seed_nodes(graph, seeds)
    affected = expand(graph, seed_nodes, max(args.hops, 0))

    if args.output == "json":
        print(json.dumps({"root": str(root), "seeds": sorted(seed_nodes), "affected": sorted(affected), "graph": graph}, indent=2))
    else:
        print(markdown_report(graph, affected, seed_nodes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


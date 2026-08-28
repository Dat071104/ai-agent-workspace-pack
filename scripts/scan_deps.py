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
# A workspace pack copied INTO a project is infrastructure, not that project's
# application, so its code is excluded from the project's map and graph.
#
# Only a pack in its own subdirectory is excluded. Excluding one at the root was
# tried and removed: a project with the pack unpacked at its root and the pack's
# own source checkout have identical signatures, so the rule could not tell
# "infrastructure" from "the product". It silently reduced the pack's own repo
# map to a single file. Ambiguity here is worse than the pollution it prevented.
EMBEDDED_PACK_MARKERS = (
    "TEAM_ROUTER.md",
    "core-context",
    "scripts/init_project_ops.py",
)
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


def looks_like_pack(directory: Path) -> bool:
    """True only for a directory holding the complete workspace-pack signature."""
    return all((directory / marker).exists() for marker in EMBEDDED_PACK_MARKERS)


def namespaced_pack_dirs(root: Path) -> set[str]:
    """Top-level copied packs to exclude from a host project's code graph."""

    try:
        children = [child for child in root.iterdir() if child.is_dir()]
    except OSError:
        return set()
    return {child.name for child in children if looks_like_pack(child)}


def should_skip_path(root: Path, path: Path, nested_packs: set[str]) -> bool:
    """Keep project code, excluding generic artifacts and a nested pack.

    The single skip rule for this repository. The map and the symbol index both
    call it, because two independent copies of it once disagreed: REPO_MAP.md
    reported the project's real file count while the graph answered with pack
    internals.
    """
    try:
        rel_parts = path.relative_to(root).parts
    except ValueError:
        return True
    if any(part in SKIP_DIRS for part in rel_parts):
        return True
    return bool(rel_parts and rel_parts[0] in nested_packs)


def iter_code_files(root: Path, suffixes: frozenset[str] | set[str] | None = None) -> list[Path]:
    """Project code files. `suffixes` lets a caller narrow the set, never widen it."""
    wanted = CODE_SUFFIXES if suffixes is None else (set(suffixes) & CODE_SUFFIXES)
    files: list[Path] = []
    nested_packs = namespaced_pack_dirs(root)
    for path in root.rglob("*"):
        if should_skip_path(root, path, nested_packs):
            continue
        if path.is_file() and path.suffix in wanted:
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


def _strip_jsonc(text: str) -> str:
    """Strip `//` and `/* */` comments so stdlib `json` can read tsconfig.json.

    tsconfig/jsconfig files are JSONC (comments, trailing commas allowed), not
    strict JSON. This is a lexer, not a JSON parser, so it tracks string
    literals only well enough to avoid stripping `//` inside one.
    """
    out: list[str] = []
    in_string = False
    in_line_comment = False
    in_block_comment = False
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if in_line_comment:
            if c == "\n":
                in_line_comment = False
                out.append(c)
            i += 1
            continue
        if in_block_comment:
            if c == "*" and nxt == "/":
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue
        if in_string:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(nxt)
                i += 2
                continue
            if c == '"':
                in_string = False
            i += 1
            continue
        if c == '"':
            in_string = True
            out.append(c)
            i += 1
            continue
        if c == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue
        if c == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue
        out.append(c)
        i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def _load_ts_config(config_path: Path, _depth: int = 0) -> dict | None:
    """Load one tsconfig/jsconfig, following a single-level `extends` chain."""
    if _depth > 5:
        return None
    try:
        text = config_path.read_text(encoding="utf-8", errors="ignore")
        data = json.loads(_strip_jsonc(text))
    except (OSError, ValueError):
        return None
    options = dict(data.get("compilerOptions") or {})
    extends = data.get("extends")
    if isinstance(extends, str):
        parent_path = (config_path.parent / extends).resolve()
        if parent_path.suffix != ".json":
            parent_path = parent_path.with_name(parent_path.name + ".json")
        parent = _load_ts_config(parent_path, _depth + 1) if parent_path.exists() else None
        if parent:
            merged = dict(parent.get("compilerOptions") or {})
            merged.update(options)
            options = merged
    return {"compilerOptions": options, "config_dir": config_path.parent}


_TS_CONFIG_CACHE: dict[Path, dict | None] = {}


def find_ts_config(root: Path, source: Path) -> dict | None:
    """Nearest tsconfig.json/jsconfig.json walking up from `source` to `root`."""
    current = source.parent
    while True:
        for name in ("tsconfig.json", "jsconfig.json"):
            candidate = current / name
            if candidate not in _TS_CONFIG_CACHE:
                _TS_CONFIG_CACHE[candidate] = _load_ts_config(candidate) if candidate.exists() else None
            if _TS_CONFIG_CACHE[candidate] is not None:
                return _TS_CONFIG_CACHE[candidate]
        if current == root or current.parent == current:
            return None
        current = current.parent
        try:
            current.relative_to(root)
        except ValueError:
            return None


def ts_path_candidates(import_name: str, config: dict) -> list[Path]:
    """Resolve `import_name` through `compilerOptions.paths` / `baseUrl`.

    `paths` patterns end in `*` for prefix matches (`"@/*": ["./src/*"]`); an
    exact-key entry has no wildcard. Falls back to a bare `baseUrl` join when
    nothing in `paths` matches, since that alone makes `components/Button`
    resolvable without an entry in `paths`.
    """
    options = config["compilerOptions"]
    config_dir = config["config_dir"]
    paths = options.get("paths") or {}
    candidates: list[Path] = []
    for pattern, targets in paths.items():
        if not isinstance(targets, list):
            continue
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            if not import_name.startswith(prefix):
                continue
            suffix = import_name[len(prefix):]
            for target in targets:
                resolved = target[:-1] + suffix if target.endswith("*") else target
                candidates.append((config_dir / resolved).resolve())
        elif pattern == import_name:
            for target in targets:
                candidates.append((config_dir / target).resolve())
    if not candidates:
        base_url = options.get("baseUrl")
        if base_url:
            candidates.append((config_dir / base_url / import_name).resolve())
    return candidates


def resolve_js_import(root: Path, source: Path, import_name: str) -> tuple[Path | None, str]:
    """Resolve a JS/TS specifier.

    `./x` and `/x` are paths, so a hit is `exact`. A bare specifier containing a
    slash (`components/Button`, `@/components/Button`) is either a
    `tsconfig`/`jsconfig` `baseUrl`/`paths` alias or a scoped package; the
    nearest tsconfig/jsconfig is tried first, then ancestor-directory probing
    for the non-`@` case. Either hit is a `heuristic`, since both depend on
    config this function cannot fully verify. A single-word specifier
    (`react`, `fs`) is a package name and is never probed -- that is where
    false edges would come from.
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

    if "/" not in import_name:
        return None, "exact"

    config = find_ts_config(root, source)
    if config is not None:
        for candidate_base in ts_path_candidates(import_name, config):
            candidates = [candidate_base]
            candidates += [candidate_base.with_suffix(suffix) for suffix in JS_SUFFIXES]
            candidates += [candidate_base / f"index{suffix}" for suffix in JS_SUFFIXES]
            hit = _first_existing(root, candidates)
            if hit is not None:
                return hit, "heuristic"

    if import_name.startswith("@"):
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

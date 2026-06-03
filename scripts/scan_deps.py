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
}
JS_IMPORT_RE = re.compile(
    r"""(?:from\s+["']([^"']+)["']|import\s*\(?\s*["']([^"']+)["']|require\(\s*["']([^"']+)["']\s*\))"""
)


def iter_code_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
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


def resolve_relative_import(root: Path, source: Path, import_name: str) -> Path | None:
    if not import_name.startswith((".", "/")):
        return None
    base = source.parent
    candidate_base = (base / import_name).resolve() if not import_name.startswith("/") else (root / import_name.lstrip("/")).resolve()
    suffixes = [".py", ".js", ".jsx", ".ts", ".tsx"]
    candidates = [candidate_base] + [candidate_base.with_suffix(suffix) for suffix in suffixes]
    candidates += [candidate_base / f"index{suffix}" for suffix in suffixes]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            try:
                candidate.relative_to(root)
            except ValueError:
                return None
            return candidate
    return None


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


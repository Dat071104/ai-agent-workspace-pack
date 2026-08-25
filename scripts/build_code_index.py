#!/usr/bin/env python3
"""Build a symbol-level code index: the codegraph-lite kernel.

`scan_deps.py` answers "which FILE imports which file". That is too coarse for
bug work, where the observed location and the fault location are usually
different symbols in different files. This builds the finer graph:

    nodes  -- files, classes, functions, methods, routes
    edges  -- DEFINES, IMPORTS, CALLS, EXTENDS

Every edge carries a `conf` (provenance), because a static index cannot honestly
claim to resolve dynamic dispatch:

    exact      resolved through the file's own imports or its local scope
    heuristic  the name is unique across the repo, so the target is inferred
    ambiguous  several definitions share the name; all candidates are kept
    weak       extracted by regex (JS/TS), not by a real parser

Consumers must surface `conf`. An edge is a lead, not a proof.

Standard library only: Python is parsed with `ast`; JS/TS falls back to regex
because no JS parser ships with Python. Output is JSON rather than SQLite so the
index stays greppable, diffable, and does not trip the pack's own hygiene rules
about tracked `*.db` files.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

# Running a tool must never leave __pycache__ inside someone else's repository.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_context_card import git_value  # noqa: E402
from scan_deps import SKIP_DIRS, resolve_import  # noqa: E402


PY_SUFFIXES = {".py"}
JS_SUFFIXES = {".js", ".jsx", ".ts", ".tsx"}
CODE_SUFFIXES = PY_SUFFIXES | JS_SUFFIXES

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "route"}

# Beyond this many candidates an edge stops being a lead and becomes noise.
# Base names like `Exception` or method names like `run` match hundreds of
# definitions; emitting one edge per candidate explodes the index and tells the
# agent nothing it can act on.
AMBIGUITY_CAP = 4

# Calls to these resolve nowhere useful and would only add noise.
CALL_NOISE = {
    "print", "len", "str", "int", "float", "bool", "list", "dict", "set", "tuple",
    "range", "enumerate", "zip", "map", "filter", "sorted", "sum", "min", "max",
    "open", "isinstance", "getattr", "setattr", "hasattr", "super", "type",
    "append", "extend", "add", "update", "get", "keys", "values", "items",
    "join", "split", "strip", "format", "replace", "startswith", "endswith",
    "console", "log", "require", "then", "catch", "push", "toString", "JSON",
}

JS_FUNC_RE = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)",
    re.M,
)
JS_ARROW_RE = re.compile(
    r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(",
    re.M,
)
JS_CLASS_RE = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?class\s+([A-Za-z_$][\w$]*)"
    r"(?:\s+extends\s+([A-Za-z_$][\w$.]*))?",
    re.M,
)
JS_METHOD_RE = re.compile(r"^\s{2,}(?:async\s+)?([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{", re.M)
JS_CALL_RE = re.compile(r"\b([A-Za-z_$][\w$]*)\s*\(")
JS_ROUTE_RE = re.compile(
    r"\b(?:app|router|api)\.(get|post|put|patch|delete|use)\s*\(\s*[\"'`]([^\"'`]+)",
)


def iter_code_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix in CODE_SUFFIXES:
            files.append(path)
    return files


def sym_id(rel: str, qualname: str) -> str:
    return f"{rel}::{qualname}"


# --------------------------------------------------------------------------- #
# Python extraction (real AST -- these symbols and local calls are trustworthy)
# --------------------------------------------------------------------------- #

def route_from_decorator(node: ast.AST) -> str | None:
    """Recognize `@app.post("/login")` style routes so HTTP entry points appear."""
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return None
    method = node.func.attr.lower()
    if method not in HTTP_METHODS:
        return None
    for arg in node.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            verb = "ANY" if method == "route" else method.upper()
            return f"{verb} {arg.value}"
    return None


def call_name(node: ast.Call) -> tuple[str, bool] | None:
    """Return (name, is_attribute). Attribute calls cannot be typed statically."""
    func = node.func
    if isinstance(func, ast.Name):
        return func.id, False
    if isinstance(func, ast.Attribute):
        return func.attr, True
    return None


def extract_python(root: Path, path: Path, rel: str) -> dict:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except (SyntaxError, ValueError):
        return {"symbols": {}, "raw_calls": [], "imports": [], "import_names": {}}

    symbols: dict[str, dict] = {}
    raw_calls: list[dict] = []
    imports: list[str] = []
    import_names: dict[str, str] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            imports.append(module)
            for alias in node.names:
                import_names[alias.asname or alias.name] = module

    def record_calls(body: list[ast.AST], owner: str) -> None:
        """Collect calls made directly by `owner`, not by functions nested in it."""
        for statement in body:
            for node in ast.walk(statement):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue
                if isinstance(node, ast.Call):
                    found = call_name(node)
                    if found and found[0] not in CALL_NOISE:
                        raw_calls.append(
                            {
                                "from": owner,
                                "name": found[0],
                                "attr": found[1],
                                "line": getattr(node, "lineno", 0),
                            }
                        )

    def visit(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                qual = f"{prefix}{child.name}"
                bases = [
                    base.id if isinstance(base, ast.Name)
                    else base.attr if isinstance(base, ast.Attribute)
                    else ""
                    for base in child.bases
                ]
                symbols[qual] = {
                    "kind": "class",
                    "name": child.name,
                    "line": child.lineno,
                    "bases": [b for b in bases if b],
                }
                visit(child, f"{qual}.")
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qual = f"{prefix}{child.name}"
                route = None
                for decorator in child.decorator_list:
                    route = route or route_from_decorator(decorator)
                symbols[qual] = {
                    "kind": "method" if prefix else "function",
                    "name": child.name,
                    "line": child.lineno,
                    "bases": [],
                }
                if route:
                    symbols[qual]["route"] = route
                record_calls(child.body, qual)
                visit(child, f"{qual}.")

    visit(tree, "")
    # Module-level statements belong to the file itself.
    module_body = [
        n for n in tree.body
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    record_calls(module_body, "<module>")

    return {
        "symbols": symbols,
        "raw_calls": raw_calls,
        "imports": imports,
        "import_names": import_names,
    }


# --------------------------------------------------------------------------- #
# JS/TS extraction (regex -- deliberately marked weak)
# --------------------------------------------------------------------------- #

def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def extract_js(path: Path, rel: str) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    symbols: dict[str, dict] = {}
    raw_calls: list[dict] = []

    for match in JS_CLASS_RE.finditer(text):
        name = match.group(1)
        symbols[name] = {
            "kind": "class",
            "name": name,
            "line": line_of(text, match.start()),
            "bases": [match.group(2)] if match.group(2) else [],
        }
    for regex in (JS_FUNC_RE, JS_ARROW_RE):
        for match in regex.finditer(text):
            name = match.group(1)
            symbols.setdefault(
                name,
                {"kind": "function", "name": name, "line": line_of(text, match.start()), "bases": []},
            )
    for match in JS_METHOD_RE.finditer(text):
        name = match.group(1)
        if name in {"if", "for", "while", "switch", "catch", "function", "return"}:
            continue
        symbols.setdefault(
            name,
            {"kind": "method", "name": name, "line": line_of(text, match.start()), "bases": []},
        )
    for match in JS_ROUTE_RE.finditer(text):
        verb, route_path = match.group(1).upper(), match.group(2)
        key = f"<route {verb} {route_path}>"
        symbols[key] = {
            "kind": "route",
            "name": key,
            "line": line_of(text, match.start()),
            "bases": [],
            "route": f"{verb} {route_path}",
        }

    # Without scope analysis, attribute every call to the file. Coarse but honest.
    for match in JS_CALL_RE.finditer(text):
        name = match.group(1)
        if name in CALL_NOISE or name in {"if", "for", "while", "switch", "catch", "function", "return", "typeof"}:
            continue
        raw_calls.append(
            {"from": "<module>", "name": name, "attr": False, "line": line_of(text, match.start())}
        )

    imports = []
    for match in re.finditer(r"""from\s+["']([^"']+)["']|require\(\s*["']([^"']+)["']""", text):
        imports.append(match.group(1) or match.group(2))

    return {"symbols": symbols, "raw_calls": raw_calls, "imports": imports, "import_names": {}}


# --------------------------------------------------------------------------- #
# Index assembly
# --------------------------------------------------------------------------- #

def build_index(root: Path, max_files: int = 0) -> dict:
    files = iter_code_files(root)
    if max_files:
        files = files[:max_files]

    per_file: dict[str, dict] = {}
    for path in files:
        rel = path.relative_to(root).as_posix()
        if path.suffix in PY_SUFFIXES:
            per_file[rel] = extract_python(root, path, rel)
            per_file[rel]["lang"] = "python"
        else:
            per_file[rel] = extract_js(path, rel)
            per_file[rel]["lang"] = "js"

    symbols: dict[str, dict] = {}
    by_name: dict[str, list[str]] = defaultdict(list)
    for rel, data in per_file.items():
        for qual, info in data["symbols"].items():
            ident = sym_id(rel, qual)
            symbols[ident] = {
                "file": rel,
                "qualname": qual,
                "lang": data["lang"],
                **info,
            }
            by_name[info["name"]].append(ident)

    edges: list[dict] = []

    # IMPORTS: file -> file, reusing the resolver that scan_deps already has.
    # The resolver reports its own provenance: a relative import names its base
    # directory (exact), while an absolute one depends on runtime sys.path and is
    # only inferred (heuristic).
    import_targets: dict[str, set[str]] = defaultdict(set)
    import_conf: dict[tuple[str, str], str] = {}
    for rel, data in per_file.items():
        source = root / rel
        for name in data["imports"]:
            target, conf = resolve_import(root, source, name)
            if target:
                target_rel = target.relative_to(root).as_posix()
                if target_rel != rel:
                    import_targets[rel].add(target_rel)
                    key = (rel, target_rel)
                    if import_conf.get(key) != "exact":
                        import_conf[key] = conf
    for rel, targets in import_targets.items():
        for target in sorted(targets):
            edges.append(
                {
                    "from": rel,
                    "to": target,
                    "kind": "IMPORTS",
                    "conf": import_conf.get((rel, target), "heuristic"),
                }
            )

    # EXTENDS: class -> base class.
    for ident, info in symbols.items():
        for base in info.get("bases", []):
            candidates = [c for c in by_name.get(base, []) if symbols[c]["kind"] == "class"]
            same_file = [c for c in candidates if symbols[c]["file"] == info["file"]]
            if same_file:
                edges.append({"from": ident, "to": same_file[0], "kind": "EXTENDS", "conf": "exact"})
            elif len(candidates) == 1:
                edges.append(
                    {"from": ident, "to": candidates[0], "kind": "EXTENDS", "conf": "heuristic"}
                )
            elif 1 < len(candidates) <= AMBIGUITY_CAP:
                for candidate in candidates:
                    edges.append(
                        {"from": ident, "to": candidate, "kind": "EXTENDS", "conf": "ambiguous"}
                    )

    # CALLS: resolve each raw call name to one or more definitions.
    for rel, data in per_file.items():
        weak = data["lang"] == "js"
        local = {
            info["name"]: sym_id(rel, qual)
            for qual, info in data["symbols"].items()
        }
        imported_files = import_targets.get(rel, set())
        seen: set[tuple[str, str]] = set()

        for call in data["raw_calls"]:
            source_id = sym_id(rel, call["from"]) if call["from"] != "<module>" else rel
            name = call["name"]
            candidates = by_name.get(name)
            if not candidates:
                continue

            same_file = [c for c in candidates if symbols[c]["file"] == rel]
            from_import = [c for c in candidates if symbols[c]["file"] in imported_files]

            if weak:
                chosen, conf = (from_import or same_file or candidates), "weak"
            elif not call["attr"] and name in local and same_file:
                chosen, conf = same_file[:1], "exact"
            elif from_import:
                chosen, conf = from_import, "exact" if len(from_import) == 1 else "ambiguous"
            elif same_file:
                chosen, conf = same_file[:1], "exact"
            elif len(candidates) == 1:
                # Unique name repo-wide: likely right, but nothing proved it.
                chosen, conf = candidates, "heuristic"
            else:
                # Classic dynamic dispatch: obj.save() with many save() defs.
                chosen, conf = candidates, "ambiguous"

            if len(chosen) > AMBIGUITY_CAP:
                continue  # too ambiguous to be a lead
            for target in chosen:
                if target == source_id:
                    continue
                key = (source_id, target)
                if key in seen:
                    continue
                seen.add(key)
                edges.append(
                    {
                        "from": source_id,
                        "to": target,
                        "kind": "CALLS",
                        "conf": conf,
                        "line": call["line"],
                    }
                )

    # `bases` was consumed into EXTENDS edges and `name` is the last dotted
    # segment of `qualname`; dropping both keeps the on-disk index materially
    # smaller without losing anything a consumer needs.
    lean = {
        ident: {k: v for k, v in info.items() if k not in {"bases", "name"}}
        for ident, info in symbols.items()
    }
    return {
        "version": 1,
        "generated": date.today().isoformat(),
        "commit": git_value(root, ["rev-parse", "--short", "HEAD"]),
        "root": str(root),
        "files": {
            rel: {"lang": data["lang"], "symbols": len(data["symbols"])}
            for rel, data in per_file.items()
        },
        "symbols": lean,
        "edges": edges,
    }


def summarize(index: dict) -> str:
    kinds: dict[str, int] = defaultdict(int)
    for edge in index["edges"]:
        kinds[f"{edge['kind']}/{edge['conf']}"] += 1
    lines = [
        f"Files indexed : {len(index['files'])}",
        f"Symbols       : {len(index['symbols'])}",
        f"Edges         : {len(index['edges'])}",
    ]
    for key in sorted(kinds):
        lines.append(f"  {key:<22} {kinds[key]}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the symbol-level code index used by scripts/explore.py."
    )
    parser.add_argument("--root", default=".", help="Repository root to index.")
    parser.add_argument(
        "--output",
        default="_agent_ops/code_index.json",
        help="Index output path.",
    )
    parser.add_argument("--max-files", type=int, default=0, help="Cap files indexed (0 = all).")
    parser.add_argument("--quiet", action="store_true", help="Only print the output path.")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        parser.error(f"Root must be an existing directory: {root}")

    index = build_index(root, args.max_files)
    output = Path(args.output)
    if not output.is_absolute():
        output = root / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(index, separators=(",", ":")), encoding="utf-8")

    if not args.quiet:
        print(summarize(index))
    print(f"Wrote: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

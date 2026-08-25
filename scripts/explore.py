#!/usr/bin/env python3
"""Structural retrieval over the code index: one tool, connected context.

This is the query side of the codegraph-lite kernel. It replaces the
grep -> read -> grep -> read loop that an agent otherwise runs to rediscover a
repository's topology on every session.

Deliberately ONE command with modes rather than a family of narrow tools: an
agent picks the wrong tool far more often than it picks the wrong flag, and the
useful answer is almost always "the connected subgraph", not a single lookup.

    explore.py --symbol charge          definitions, callers, callees, source
    explore.py --path checkout charge   how control actually reaches a symbol
    explore.py --impact getUser         blast radius + which tests to run
    explore.py --file src/auth.py       what a file holds and who depends on it
    explore.py --entrypoints            routes and unreferenced entry symbols

Every relationship prints its provenance. `ambiguous` and `weak` are leads to
verify by reading code, never facts to act on.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict, deque
from pathlib import Path

# Running a tool must never leave __pycache__ inside someone else's repository.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from scan_deps import tool_prefix  # noqa: E402


CONF_NOTE = {
    "exact": "",
    "heuristic": " (name unique repo-wide; inferred)",
    "ambiguous": " (several definitions share this name -- verify which one runs)",
    "weak": " (regex-extracted JS/TS; low confidence)",
}
TEST_HINTS = ("test", "spec", "__tests__")
MAX_LIST = 25


def load_index(path: Path, root: Path) -> dict:
    if not path.exists():
        sys.exit(
            f"No index at {path}\n"
            "Build it first:\n"
            f"  python {tool_prefix(root)}/build_code_index.py --root . "
            "--output _agent_ops/code_index.json"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def symbol_name(info: dict) -> str:
    """Short name. The index stores only `qualname`; the name is its last segment."""
    return info.get("name") or info["qualname"].rsplit(".", 1)[-1]


class Graph:
    def __init__(self, index: dict) -> None:
        self.index = index
        self.symbols: dict[str, dict] = index["symbols"]
        self.out: dict[str, list[dict]] = defaultdict(list)
        self.into: dict[str, list[dict]] = defaultdict(list)
        self.imports_in: dict[str, set[str]] = defaultdict(set)
        for edge in index["edges"]:
            if edge["kind"] == "CALLS":
                self.out[edge["from"]].append(edge)
                self.into[edge["to"]].append(edge)
            elif edge["kind"] == "IMPORTS":
                self.imports_in[edge["to"]].add(edge["from"])
            elif edge["kind"] == "EXTENDS":
                self.out[edge["from"]].append(edge)
                self.into[edge["to"]].append(edge)

    def find(self, query: str) -> list[str]:
        """Match a symbol by exact name, qualname, id, then loose substring."""
        query_l = query.lower()
        exact = [i for i, s in self.symbols.items() if symbol_name(s).lower() == query_l]
        if exact:
            return exact
        qual = [i for i, s in self.symbols.items() if s["qualname"].lower() == query_l]
        if qual:
            return qual
        ident = [i for i in self.symbols if i.lower() == query_l]
        if ident:
            return ident
        return [
            i for i, s in self.symbols.items()
            if query_l in s["qualname"].lower() or query_l in i.lower()
        ]

    def label(self, ident: str) -> str:
        info = self.symbols.get(ident)
        if not info:
            return f"{ident} (file)"
        route = f"  [{info['route']}]" if info.get("route") else ""
        return f"{info['file']}:{info['line']}  {info['kind']:<8} {info['qualname']}{route}"

    def callers_transitive(self, start: str, depth: int) -> dict[str, int]:
        seen = {start: 0}
        queue = deque([(start, 0)])
        while queue:
            node, level = queue.popleft()
            if level >= depth:
                continue
            for edge in self.into.get(node, []):
                if edge["from"] not in seen:
                    seen[edge["from"]] = level + 1
                    queue.append((edge["from"], level + 1))
        seen.pop(start, None)
        return seen

    def entry_points(self) -> list[str]:
        routed = [i for i, s in self.symbols.items() if s.get("route")]
        named = [
            i for i, s in self.symbols.items()
            if symbol_name(s) in {"main", "handler", "run", "start"} and i not in routed
        ]
        unreferenced = [
            i for i, s in self.symbols.items()
            if not self.into.get(i) and s["kind"] in {"function", "method"}
        ]
        return routed + named + [i for i in unreferenced if i not in routed and i not in named]

    def path_to(self, target: str, sources: list[str], max_depth: int = 12) -> list[list[dict]]:
        """Shortest call path from each plausible source down to the target."""
        paths: list[list[dict]] = []
        for source in sources:
            prev: dict[str, dict] = {}
            seen = {source}
            queue = deque([(source, 0)])
            hit = False
            while queue and not hit:
                node, depth = queue.popleft()
                if depth >= max_depth:
                    continue
                for edge in self.out.get(node, []):
                    nxt = edge["to"]
                    if nxt in seen:
                        continue
                    seen.add(nxt)
                    prev[nxt] = edge
                    if nxt == target:
                        hit = True
                        break
                    queue.append((nxt, depth + 1))
            if hit:
                chain: list[dict] = []
                cursor = target
                while cursor in prev:
                    edge = prev[cursor]
                    chain.append(edge)
                    cursor = edge["from"]
                paths.append(list(reversed(chain)))
        paths.sort(key=len)
        return paths


def source_snippet(root: Path, info: dict, lines: int) -> list[str]:
    path = root / info["file"]
    if not path.exists() or lines <= 0:
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []
    start = max(info["line"] - 1, 0)
    return [f"    {n + 1:>4}| {text[n]}" for n in range(start, min(start + lines, len(text)))]


def render_symbol(graph: Graph, root: Path, query: str, snippet_lines: int) -> list[str]:
    matches = graph.find(query)
    if not matches:
        return [f"No symbol matches `{query}`. Try a partial name, or index first."]

    out = [f"# Explore: {query}", ""]
    if len(matches) > 1:
        out += [
            f"## Definitions ({len(matches)}) -- static analysis cannot pick one",
            "",
        ]
    else:
        out += ["## Definition", ""]
    for ident in matches[:MAX_LIST]:
        out.append(f"- {graph.label(ident)}")
    if len(matches) > MAX_LIST:
        out.append(f"- ... {len(matches) - MAX_LIST} more")
    out.append("")

    primary = matches[0]
    if snippet_lines and len(matches) == 1:
        body = source_snippet(root, graph.symbols[primary], snippet_lines)
        if body:
            out += ["## Source", "", *body, ""]

    for ident in matches[:3]:
        info = graph.symbols[ident]
        header = info["qualname"] if len(matches) > 1 else "This symbol"
        callers = graph.into.get(ident, [])
        callees = graph.out.get(ident, [])

        out.append(f"## {header}: called by ({len(callers)})")
        out.append("")
        if callers:
            for edge in callers[:MAX_LIST]:
                note = CONF_NOTE.get(edge["conf"], "")
                out.append(f"- [{edge['conf']}] {graph.label(edge['from'])}{note}")
            if len(callers) > MAX_LIST:
                out.append(f"- ... {len(callers) - MAX_LIST} more")
        else:
            out.append("- nothing calls it in the index (entry point, dead, or dynamically dispatched)")
        out.append("")

        out.append(f"## {header}: calls out ({len(callees)})")
        out.append("")
        if callees:
            for edge in callees[:MAX_LIST]:
                out.append(f"- [{edge['conf']}] {edge['kind']} -> {graph.label(edge['to'])}")
            if len(callees) > MAX_LIST:
                out.append(f"- ... {len(callees) - MAX_LIST} more")
        else:
            out.append("- none recorded")
        out.append("")

    flows = graph.path_to(primary, graph.entry_points())
    if flows:
        out += ["## Reached from an entry point", ""]
        for chain in flows[:3]:
            out.append(f"- {graph.label(chain[0]['from'])}")
            for depth, edge in enumerate(chain, start=1):
                out.append(f"  {'  ' * depth}-> [{edge['conf']}] {graph.label(edge['to'])}")
            out.append("")
    return out


def render_impact(graph: Graph, query: str, depth: int) -> list[str]:
    matches = graph.find(query)
    if not matches:
        return [f"No symbol matches `{query}`."]
    target = matches[0]
    out = [f"# Impact: {graph.symbols[target]['qualname']}", ""]
    if len(matches) > 1:
        out += [
            f"NOTE: {len(matches)} definitions share this name; showing the first.",
            "Blast radius for the others may differ.",
            "",
        ]
    dependents = graph.callers_transitive(target, depth)
    if not dependents:
        out += ["Nothing in the index reaches this symbol.", ""]
    else:
        out += [f"## Transitively affected ({len(dependents)}, depth {depth})", ""]
        for ident, level in sorted(dependents.items(), key=lambda kv: (kv[1], kv[0]))[:MAX_LIST]:
            out.append(f"- hop {level}: {graph.label(ident)}")
        if len(dependents) > MAX_LIST:
            out.append(f"- ... {len(dependents) - MAX_LIST} more")
        out.append("")

    files = {graph.symbols[i]["file"] for i in dependents if i in graph.symbols}
    files.add(graph.symbols[target]["file"])
    tests = sorted(f for f in files if any(hint in f.lower() for hint in TEST_HINTS))
    out += ["## Tests to run", ""]
    if tests:
        out += [f"- {f}" for f in tests]
    else:
        out.append("- No test file in the affected set. Either coverage is missing here,")
        out.append("  or the tests reach this code dynamically and the index cannot see it.")
    out += [
        "",
        "## Caution",
        "",
        "Static edges miss dynamic dispatch, DI wiring, reflection, and runtime",
        "registries. Treat this as the minimum blast radius, never the maximum.",
        "",
    ]
    return out


def render_file(graph: Graph, query: str) -> list[str]:
    rel = query.replace("\\", "/")
    files = [f for f in graph.index["files"] if f == rel or f.endswith("/" + rel) or rel in f]
    if not files:
        return [f"No indexed file matches `{query}`."]
    out: list[str] = []
    for path in files[:3]:
        symbols = [i for i, s in graph.symbols.items() if s["file"] == path]
        importers = sorted(graph.imports_in.get(path, set()))
        out += [f"# File: {path}", "", f"## Symbols ({len(symbols)})", ""]
        for ident in sorted(symbols, key=lambda i: graph.symbols[i]["line"])[:MAX_LIST]:
            out.append(f"- {graph.label(ident)}")
        if len(symbols) > MAX_LIST:
            out.append(f"- ... {len(symbols) - MAX_LIST} more")
        out += ["", f"## Imported by ({len(importers)})", ""]
        out += [f"- {f}" for f in importers[:MAX_LIST]] or ["- nothing imports it"]
        out.append("")
    return out


def render_path(graph: Graph, source: str, target: str) -> list[str]:
    sources = graph.find(source)
    targets = graph.find(target)
    if not sources:
        return [f"No symbol matches `{source}`."]
    if not targets:
        return [f"No symbol matches `{target}`."]
    out = [f"# Path: {source} -> {target}", ""]
    found = False
    for goal in targets[:3]:
        for chain in graph.path_to(goal, sources)[:2]:
            found = True
            out.append(f"- {graph.label(chain[0]['from'])}")
            for depth, edge in enumerate(chain, start=1):
                out.append(f"  {'  ' * depth}-> [{edge['conf']}] {graph.label(edge['to'])}")
            out.append("")
    if not found:
        out += [
            "No call path found in the index.",
            "",
            "That is not proof there is none: the connection may run through dynamic",
            "dispatch, an event bus, DI, or a framework hook the static index misses.",
            "",
        ]
    return out


def render_entrypoints(graph: Graph) -> list[str]:
    routed = [i for i, s in graph.symbols.items() if s.get("route")]
    out = ["# Entry Points", "", f"## Routes ({len(routed)})", ""]
    out += [f"- {graph.label(i)}" for i in routed[:MAX_LIST]] or ["- none detected"]
    unreferenced = [
        i for i, s in graph.symbols.items()
        if not graph.into.get(i) and s["kind"] in {"function", "method"} and i not in routed
    ]
    out += ["", f"## Nothing calls these ({len(unreferenced)})", ""]
    for ident in unreferenced[:MAX_LIST]:
        out.append(f"- {graph.label(ident)}")
    if len(unreferenced) > MAX_LIST:
        out.append(f"- ... {len(unreferenced) - MAX_LIST} more")
    out += [
        "",
        "Unreferenced does NOT mean dead. Entry points, CLI hooks, framework",
        "callbacks, tests, and dynamically dispatched methods all land here.",
        "",
    ]
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Structural retrieval over _agent_ops/code_index.json."
    )
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--index", default="_agent_ops/code_index.json", help="Index path.")
    parser.add_argument("--symbol", help="Definitions, callers, callees, and flow for a symbol.")
    parser.add_argument("--impact", help="Blast radius and tests to run for a symbol.")
    parser.add_argument("--file", dest="file_query", help="What a file holds and who imports it.")
    parser.add_argument("--path", nargs=2, metavar=("FROM", "TO"), help="Call path between symbols.")
    parser.add_argument("--entrypoints", action="store_true", help="Routes and unreferenced symbols.")
    parser.add_argument("--depth", type=int, default=4, help="Impact traversal depth.")
    parser.add_argument("--source-lines", type=int, default=12, help="Source lines to show (0 = none).")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    index_path = Path(args.index)
    if not index_path.is_absolute():
        index_path = root / index_path
    graph = Graph(load_index(index_path, root))

    if args.symbol:
        lines = render_symbol(graph, root, args.symbol, args.source_lines)
    elif args.impact:
        lines = render_impact(graph, args.impact, max(args.depth, 1))
    elif args.file_query:
        lines = render_file(graph, args.file_query)
    elif args.path:
        lines = render_path(graph, args.path[0], args.path[1])
    elif args.entrypoints:
        lines = render_entrypoints(graph)
    else:
        parser.error("Pick one: --symbol, --impact, --file, --path, or --entrypoints")

    stamp = graph.index.get("commit", "unknown")
    print("\n".join(lines).rstrip())
    print(f"\n---\nIndex built at commit `{stamp}` ({graph.index.get('generated')}). "
          f"Rebuild after code changes: python {tool_prefix(root)}/build_code_index.py --root .")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

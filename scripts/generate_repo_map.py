#!/usr/bin/env python3
"""Generate a compact, size-capped repo map for AI agents.

This is the "codegraph lite" read: one Tier-1 file that answers "where does the
code live" and "what has the widest blast radius" without the agent grepping the
whole repository.

Reuses the existing graph builder in `scan_deps.py` and the stack/git helpers in
`generate_context_card.py` instead of duplicating that logic.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

# Running a tool must never leave __pycache__ inside someone else's repository.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_context_card import detect_stack, git_value  # noqa: E402
from scan_deps import build_graph, reverse_edges, tool_prefix  # noqa: E402


ENTRY_STEMS = {"main", "index", "app", "cli", "__main__", "server", "start"}
ROOT_MODULE = "(repo root)"


def module_key(rel_path: str, depth: int) -> str:
    parts = rel_path.split("/")
    if len(parts) <= depth:
        return "/".join(parts[:-1]) or ROOT_MODULE
    return "/".join(parts[:depth])


def choose_depth(paths: list[str], max_depth: int = 3) -> int:
    """Pick the grouping depth that actually separates the codebase.

    A `src/`-rooted layout collapses to a single module at depth 1, which makes
    the module table useless. Descend until the grouping is informative.
    """
    if not paths:
        return 1
    chosen = 1
    for depth in range(1, max_depth + 1):
        chosen = depth
        keys = [module_key(path, depth) for path in paths]
        distinct = set(keys)
        largest = max(keys.count(key) for key in distinct)
        if len(distinct) >= 2 and largest <= 0.6 * len(paths):
            break
    return chosen


def is_entry_point(rel_path: str) -> bool:
    return Path(rel_path).stem in ENTRY_STEMS


def collect_modules(
    graph: dict[str, dict[str, list[str]]],
    reverse: dict[str, set[str]],
    depth: int,
) -> list[dict[str, object]]:
    """Group files by module and measure cross-module inbound edges."""
    files_by_module: dict[str, list[str]] = defaultdict(list)
    for rel_path in graph:
        files_by_module[module_key(rel_path, depth)].append(rel_path)

    inbound_by_module: dict[str, int] = defaultdict(int)
    for source, data in graph.items():
        source_module = module_key(source, depth)
        for target in data["resolved"]:
            target_module = module_key(target, depth)
            if target_module != source_module:
                inbound_by_module[target_module] += 1

    modules: list[dict[str, object]] = []
    for module, files in files_by_module.items():
        entries = sorted(path for path in files if is_entry_point(path))
        modules.append(
            {
                "name": module,
                "files": len(files),
                "entries": entries,
                "inbound": inbound_by_module.get(module, 0),
                # Local fan-in helps rank modules that nothing imports across
                # boundaries but that are still internally central.
                "internal": sum(len(reverse.get(path, set())) for path in files),
            }
        )
    modules.sort(key=lambda item: (-int(item["inbound"]), -int(item["files"]), str(item["name"])))
    return modules


def hot_files(
    graph: dict[str, dict[str, list[str]]],
    reverse: dict[str, set[str]],
    limit: int,
) -> list[tuple[str, int, int]]:
    """Files with the highest fan-in: changing them has the widest blast radius."""
    ranked = [
        (rel_path, len(reverse.get(rel_path, set())), len(graph[rel_path]["resolved"]))
        for rel_path in graph
    ]
    ranked = [item for item in ranked if item[1] > 0]
    ranked.sort(key=lambda item: (-item[1], item[0]))
    return ranked[:limit]


def count_isolated(
    graph: dict[str, dict[str, list[str]]],
    reverse: dict[str, set[str]],
) -> int:
    return sum(
        1
        for rel_path, data in graph.items()
        if not data["resolved"] and not reverse.get(rel_path)
    )


def symbol_section(root: Path) -> list[str]:
    """Symbol-level highlights, when the code index has been built.

    File fan-in says which file is central. It cannot say which FUNCTION is, and
    that is the level bugs actually live at. This stays optional so the map still
    works on a repo that was never indexed.
    """
    tools = tool_prefix(root)
    index_path = root / "_agent_ops" / "code_index.json"
    if not index_path.exists():
        return [
            "## Symbol Graph",
            "",
            "Not built. For symbol-level callers, call paths, and blast radius:",
            "",
            "```bash",
            f"python {tools}/build_code_index.py --root .",
            f"python {tools}/explore.py --root . --symbol <name>",
            "```",
            "",
        ]
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []

    symbols = index.get("symbols", {})
    fan_in: dict[str, int] = defaultdict(int)
    conf_counts: dict[str, int] = defaultdict(int)
    for edge in index.get("edges", []):
        conf_counts[edge.get("conf", "?")] += 1
        if edge.get("kind") == "CALLS":
            fan_in[edge["to"]] += 1

    routes = [
        (info.get("route", ""), info["file"], info["line"], info["qualname"])
        for info in symbols.values()
        if info.get("route")
    ]
    hot = sorted(
        ((ident, count) for ident, count in fan_in.items() if ident in symbols),
        key=lambda kv: (-kv[1], kv[0]),
    )[:12]

    out = [
        "## Symbol Graph",
        "",
        f"{len(symbols)} symbols, {len(index.get('edges', []))} edges "
        f"(exact {conf_counts.get('exact', 0)}, heuristic {conf_counts.get('heuristic', 0)}, "
        f"ambiguous {conf_counts.get('ambiguous', 0)}, weak {conf_counts.get('weak', 0)}).",
        "",
    ]
    if routes:
        out += ["### Routes", ""]
        for route, file_name, line, qual in sorted(routes)[:15]:
            out.append(f"- `{route}` -> `{file_name}:{line}` {qual}")
        if len(routes) > 15:
            out.append(f"- _... {len(routes) - 15} more_")
        out.append("")
    if hot:
        out += [
            "### Most-called symbols",
            "",
            "| Symbol | Called by | Where |",
            "| --- | --- | --- |",
        ]
        for ident, count in hot:
            info = symbols[ident]
            out.append(f"| `{info['qualname']}` | {count} | `{info['file']}:{info['line']}` |")
        out.append("")
    out += [
        "Query it instead of grepping:",
        "",
        "```bash",
        f"python {tools}/explore.py --root . --symbol <name>    # callers, callees, flow",
        f"python {tools}/explore.py --root . --impact <name>    # blast radius + tests",
        f"python {tools}/explore.py --root . --path <a> <b>     # how a reaches b",
        "```",
        "",
    ]
    return out


def long_files(root: Path, graph: dict[str, dict[str, list[str]]], limit: int, threshold: int) -> list[tuple[str, int]]:
    """Files big enough that an agent will struggle to hold them in context.

    Agents left alone tend to grow one file until it is thousands of lines. This
    is the factual list that makes "split this" a specific instruction instead of
    a slogan.
    """
    sized: list[tuple[str, int]] = []
    for rel in graph:
        try:
            count = sum(1 for _ in (root / rel).open(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
        if count >= threshold:
            sized.append((rel, count))
    sized.sort(key=lambda item: -item[1])
    return sized[:limit]


def render_map(
    root: Path,
    graph: dict[str, dict[str, list[str]]],
    max_modules: int,
    max_hot: int,
) -> str:
    reverse = reverse_edges(graph)
    depth = choose_depth(sorted(graph))
    modules = collect_modules(graph, reverse, depth)
    hot = hot_files(graph, reverse, max_hot)
    entries = sorted(path for path in graph if is_entry_point(path))
    tools = tool_prefix(root)
    commit = git_value(root, ["rev-parse", "--short", "HEAD"])
    branch = git_value(root, ["branch", "--show-current"])

    lines = [
        "# Repo Map / Ban do ma nguon",
        "",
        "Generated file. Do not hand-edit; regenerate with",
        f"`python {tools}/generate_repo_map.py --root . --output _agent_ops/REPO_MAP.md --force`.",
        "",
        "Read this BEFORE grepping the repository. It answers \"where does the code",
        "live\" and \"what breaks if I touch this\" in one Tier-1 read.",
        "",
        "## Last Verified Commit",
        "",
        f"`{commit}`",
        "",
        "## Snapshot",
        "",
        f"- Branch: `{branch}`",
        f"- Generated: `{date.today().isoformat()}`",
        f"- Code files indexed: {len(graph)}",
        f"- Stack: {', '.join(detect_stack(root))}",
        "",
    ]

    if not graph:
        lines += [
            "## Modules",
            "",
            "No Python or JS/TS files were found. This map covers only those",
            "languages; describe other stacks manually in `PROJECT_CONTEXT_CARD.md`.",
            "",
        ]
        return "\n".join(lines).rstrip() + "\n"

    shown = modules[:max_modules]
    lines += [
        "## Modules",
        "",
        "`Inbound` counts imports coming from OUTSIDE the module: higher means more",
        "code depends on it, so changes there travel further.",
        "",
        "| Module | Files | Inbound | Entry points |",
        "| --- | --- | --- | --- |",
    ]
    for module in shown:
        entry_cell = ", ".join(f"`{path}`" for path in list(module["entries"])[:3]) or "-"
        lines.append(
            f"| `{module['name']}` | {module['files']} | {module['inbound']} | {entry_cell} |"
        )
    if len(modules) > max_modules:
        hidden = len(modules) - max_modules
        lines.append(f"| _... {hidden} more modules not listed (cap {max_modules})_ | | | |")
    lines.append("")

    lines += [
        "## Hot Files (widest blast radius)",
        "",
        "Ranked by fan-in. Treat an edit here as cross-module until proven otherwise.",
        "",
        "| File | Imported by | Imports |",
        "| --- | --- | --- |",
    ]
    if hot:
        for rel_path, fan_in, fan_out in hot:
            lines.append(f"| `{rel_path}` | {fan_in} | {fan_out} |")
    else:
        lines.append("| _no local import edges resolved_ | | |")
    lines.append("")

    lines += symbol_section(root)

    lines += ["## Entry Points", ""]
    if entries:
        lines += [f"- `{path}`" for path in entries[:20]]
        if len(entries) > 20:
            lines.append(f"- _... {len(entries) - 20} more_")
    else:
        lines.append("- None detected by filename convention. Confirm manually.")
    lines.append("")

    oversized = long_files(root, graph, 10, 400)
    if oversized:
        lines += [
            "## Oversized Files",
            "",
            "Files past 400 lines. Long files are where agents lose the thread and",
            "where unrelated responsibilities collect. Split along a responsibility",
            "boundary before adding to one of these.",
            "",
            "| File | Lines |",
            "| --- | --- |",
        ]
        lines += [f"| `{rel}` | {count} |" for rel, count in oversized]
        lines.append("")

    isolated = count_isolated(graph, reverse)
    lines += [
        "## Isolated Files",
        "",
        f"{isolated} file(s) have no resolved local imports in either direction.",
        "They are listed only on demand -- enumerating them here would recreate the",
        "context bloat this map exists to prevent.",
        "",
        "## Drill Down",
        "",
        "This map is deliberately shallow. For the affected zone of a specific change:",
        "",
        "```bash",
        f"python {tools}/scan_deps.py --root . --seed \"<keyword>\" --hops 2 --output markdown",
        "```",
        "",
        "## Limits",
        "",
        "- Covers `.py`, `.js`, `.jsx`, `.ts`, `.tsx` only.",
        "- Relative imports resolve exactly. Absolute Python imports and JS path",
        "  aliases are inferred by probing parent directories, so they can be wrong;",
        "  package imports (`react`, `numpy`) are not followed at all.",
        "- Dynamic imports, DI wiring, and runtime registries are invisible here.",
        "  Verify before claiming a file is unused.",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a size-capped REPO_MAP.md for AI-agent context."
    )
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument("--output", default="", help="Output file. Prints to stdout if omitted.")
    parser.add_argument("--max-modules", type=int, default=25, help="Maximum modules listed.")
    parser.add_argument("--max-hot", type=int, default=15, help="Maximum hot files listed.")
    parser.add_argument("--force", action="store_true", help="Overwrite output file if it exists.")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        parser.error(f"Root must be an existing directory: {root}")

    graph = build_graph(root)
    report = render_map(root, graph, max(args.max_modules, 1), max(args.max_hot, 1))

    if args.output:
        output = Path(args.output).expanduser().resolve()
        if output.exists() and not args.force:
            parser.error(f"Output exists. Use --force to overwrite: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")
        print(f"Wrote: {output} ({len(report.splitlines())} lines, {len(graph)} files indexed)")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Measure what a harness reads per scenario in a host with the pack embedded.

Not a test (no `test_` prefix) and not shipped: `tests/` stays in the source
repo. Characters are exact; tokens are a chars/4 ESTIMATE -- no Claude
tokenizer is available offline, and an exact count needs the count_tokens API.

    python -B tests/measure_context.py <host_root> [pack_folder]

Build the host with `scripts/embed_pack.py --target <host_root>` on a fresh
`git init` repo, from each revision you want to compare. Scenario contents
below are the measurement's input: change them only together with a recorded
before/after pair, or the numbers stop being comparable.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ALWAYS = ["CLAUDE.md", "AGENTS.md", "{P}/AGENTS.md"]
ROUTE = ["{P}/START_HERE.md", "{P}/TEAM_ROUTER.md"]
HOT = ["{OPS}/SESSION_BRIEF.md", "{OPS}/OPERATING_RULES.md"]
BUILD_S = [".claude/skills/build-team/SKILL.md", "{P}/build-team/SKILL.md", "{P}/build-team/PONYTAIL_RULES.md"]
CLOSE = ["{OPS}/SESSION_PROTOCOL.md"]
SESSION_START = "<session_start>"

SCENARIOS = {
    "quick question": ALWAYS,
    "new S task (@start-here, build S)": ALWAYS + ROUTE + [SESSION_START] + HOT
    + ["{OPS}/CURRENT_TASK.md", "{OPS}/REPO_MAP.md"] + BUILD_S + CLOSE,
    "continuation (handoff, build S)": ALWAYS + [SESSION_START, "{OPS}/HANDOFF.md"] + HOT
    + ["{OPS}/CURRENT_TASK.md"] + BUILD_S + CLOSE,
}


def size(host: Path, item: str, ops: str) -> int:
    if item == SESSION_START:
        tool = host / ops / "tools" / "session_start.py"
        out = subprocess.run(
            [sys.executable, "-B", str(tool), "--root", "."],
            cwd=host, capture_output=True, text=True, encoding="utf-8", check=False,
        )
        return len(out.stdout)
    path = host / item
    return len(path.read_text(encoding="utf-8")) if path.exists() else 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    host = Path(sys.argv[1]).resolve()
    pack = sys.argv[2] if len(sys.argv) > 2 else "ai-agent-workspace-pack"
    ops = f"{pack}/_agent_ops"
    cache: dict[str, int] = {}
    for name, items in SCENARIOS.items():
        rows = []
        for raw in items:
            item = raw.format(P=pack, OPS=ops)
            if item not in cache:
                cache[item] = size(host, item, ops)
            rows.append((item, cache[item]))
        total = sum(n for _, n in rows)
        print(f"## {name}: {total} chars ~{total // 4} tok (chars/4 estimate)")
        for item, n in rows:
            print(f"   {n:>6}  {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Next Step Card Template

Shared by `advisor-team/` and `analyze-team/`. A card names ONE action, not a
menu. Every field cites evidence (`path:line`, a log entry, or a measurement),
and "Paste to start" is the exact text to run in the named harness. Use the
invocation form from `commands/*.md`. Nothing is written by filling in a card.

```text
Next Step Card
- Do:              <one action, one sentence>
- Why now:         <value, with the evidence reference>
- Team / mode:     <team> / <solo | sequential | parallel>
- Paste to start:  <exact invocation for this harness>
- Done when:       <observable check or command>
- Size / token:    <S|M|L|XL> / <Light|Medium|Heavy|Very Heavy>
- Stop and ask if: <condition that changes scope or risk>
- Not now:         <top deferred item + reason>
```

## Filled Example

Illustrative card built from the pack's own `_agent_ops/REPO_MAP.md`
(Oversized Files lists `scripts/explore.py` at 427 lines, past the 400-line
limit in `AGENTS.md`).

```text
Next Step Card
- Do:              Move the --path search out of scripts/explore.py into its own module, as clean-code batch 1 with no behavior change.
- Why now:         scripts/explore.py is 427 lines (REPO_MAP.md, Oversized Files, known). The path-search boundary is estimate: confirm it with explore.py --file before cutting.
- Team / mode:     clean-code-team / sequential
- Paste to start:  Use clean-code-team. Batch 1 only: move the --path search out of scripts/explore.py into its own module, no behavior change. Warn me about cost first, check git state, audit, and wait for my confirmation before any cleanup.
- Done when:       python -B -m unittest discover -s tests -q prints OK and scripts/explore.py is under 400 lines (wc -l).
- Size / token:    S / Medium
- Stop and ask if: python _agent_ops/tools/explore.py --root . --impact <path-search symbol> shows callers outside explore.py (the change then crosses a module boundary).
- Not now:         Splitting scripts/init_project_ops.py (1000+ lines) -- more callers, needs its own plan after this batch proves the pattern.
```

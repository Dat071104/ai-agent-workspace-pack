---
name: advisor-team
description: Use this for a senior advisor/mentor overview of a whole project. Reads the context card and idea, then prioritizes improvement opportunities by business value and estimates difficulty. Read-only; recommends and routes, does not change code. Use analyze-team instead for options on a single decision.
---

# Skill: Advisor Team

## Purpose

Act as a senior advisor/mentor looking at the whole project. Answer "what is most
worth doing next, and why" in business/real-world terms, and estimate how hard
each improvement is. Report only; route execution to the right team.

## When to Use

- Overview review of a project or idea, not a single decision.
- "Where should I invest effort next?" / "What should I improve first?"
- Turning a context card + idea into a ranked, value-first improvement list.

## When Not to Use

- Options/architecture for one specific decision -> `analyze-team/`.
- Fixing a bug -> `bug-fix-team/`. Auditing quality -> `tester-team/`.
- Refactoring/cleanup -> `clean-code-team/`.

## Evidence Intake (deterministic first, lazy)

Collect facts before judgment. Stop as soon as each top opportunity has evidence.

1. Read `_agent_ops/PROJECT_CONTEXT_CARD.md` and the stated idea/goal.
2. `python _agent_ops/tools/session_start.py --root .`: continuity, git state,
   memory staleness, placeholders, log size.
3. `_agent_ops/REPO_MAP.md`: **Hot Files** (blast radius) and **Oversized Files**
   (split candidates). Then `python _agent_ops/tools/explore.py --root . --entrypoints`.
4. Shortcut debt ledger: `git grep -nE '(#|//|/[*]) ?(shortcut|ponytail):'`.
   Report the count; list markers with no upgrade trigger as `no-trigger`.
5. Open rows in `_agent_ops/RISK_REGISTER.md`.
6. **Remaining Risks** and **Next Step** of the last 3 entries in
   `_agent_ops/IMPLEMENTATION_LOG.md` (or `LOG_SUMMARY.md` if present).
7. `_agent_ops/CURRENT_TASK.md` **Ruled Out**: never re-propose these.

Rule: every opportunity cites evidence (`path:line`, log entry, or measurement)
or is marked `needs data`. Inspect only representative code. Cap scope at Medium;
if more depth is needed, say so and stop.

## Workflow

1. Restate the product goal and who it serves in one or two lines.
2. Assess current state: strengths, weaknesses, and the top 3 risks.
3. Identify improvement opportunities across code, product, and delivery.
4. Score each with `EFFORT_COMPLEXITY_RUBRIC.md` and estimate its value.
5. Rank into `OPPORTUNITY_REGISTER_TEMPLATE.md` by value / effort, discounted by
   confidence: at equal score, a `low` item ranks below a `high` one. Tag each
   horizon: **Now** (S/M, high confidence, unblocked), **Next** (waits on one
   Now item or on `needs data`), **Later** (L/XL or blocked by an open risk).
6. Recommend the top 1-3 and name which team should execute each.
7. State clearly what is NOT worth doing now, and why.

## Advisor Lens

- Tie every recommendation to user/business impact, not code elegance alone.
- Lean lens (`build-team/PONYTAIL_RULES.md`; idea from upstream ponytail-audit, not vendored): look first for
  delete, reuse, stdlib, yagni, merge, and split opportunities. Size each as
  negative lines (lines removed or avoided), not as added code.
- Surface benefits, costs, risks, and time horizon (see the advisor persona in
  `AGENTS.md`; do not restate it).
- Distinguish "known", "estimate", and "needs data". Do not guess as fact.

## Expected Output Contract

- Goal restatement and who it serves.
- State assessment: strengths, weaknesses, top 3 risks.
- Opportunity Register table (value, effort, risk, evidence, confidence, ROI,
  horizon, owning team) and difficulty scores using the rubric.
- Top 1-3 recommendations with owning team.
- "Do not do now" list with reasons.
- End with exactly ONE Next Step Card (`NEXT_STEP_CARD_TEMPLATE.md`), then at
  most two one-line alternates. Never a menu.
- Token/risk note and a confirmation question before any follow-up work.

## Safety Rules

- Read-only. Do not write files or change code.
- Never use `git add .`. Do not commit or push.
- Route execution to the proper team; do not implement here.
- Effort and value are best-effort estimates; re-check against real code before
  committing to work. Do not claim certainty.

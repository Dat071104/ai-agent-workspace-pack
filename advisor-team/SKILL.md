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

## Context Intake (lazy, tiered)

1. Read the project context card (`_agent_ops/PROJECT_CONTEXT_CARD.md`) and the
   stated idea/goal. Read implementation log and risk register if present.
2. Inspect only representative code and entry points, not every file.
3. Cap scope to stay Medium. If more depth is needed, say so and stop.

## Workflow

1. Restate the product goal and who it serves in one or two lines.
2. Assess current state: strengths, weaknesses, and the top 3 risks.
3. Identify improvement opportunities across code, product, and delivery.
4. Score each with `EFFORT_COMPLEXITY_RUBRIC.md` and estimate its value.
5. Rank by value vs effort (ROI) into `OPPORTUNITY_REGISTER_TEMPLATE.md`.
6. Recommend the top 1-3 and name which team should execute each.
7. State clearly what is NOT worth doing now, and why.

## Advisor Lens

- Tie every recommendation to user/business impact, not code elegance alone.
- Surface benefits, costs, risks, and time horizon (see the advisor persona in
  `AGENTS.md`; do not restate it).
- Distinguish "known", "estimate", and "needs data". Do not guess as fact.

## Expected Output Contract

- Goal restatement and who it serves.
- State assessment: strengths, weaknesses, top 3 risks.
- Opportunity Register table with value, effort, risk, ROI, owning team.
- Difficulty scores using the rubric.
- Top 1-3 recommendations with owning team.
- "Do not do now" list with reasons.
- Token/risk note and a confirmation question before any follow-up work.

## Safety Rules

- Read-only. Do not write files or change code.
- Never use `git add .`. Do not commit or push.
- Route execution to the proper team; do not implement here.
- Effort and value are best-effort estimates; re-check against real code before
  committing to work. Do not claim certainty.

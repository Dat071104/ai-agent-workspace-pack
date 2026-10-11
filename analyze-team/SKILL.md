---
name: analyze-team
description: Use this when the user wants to analyze a new project idea, compare architecture options, decide a roadmap, or clarify scope before writing files. Do not use for bug fixing, audit-only work, or code cleanup.
---

# Skill: Analyze Team

## Purpose

Analyze requests before implementation. Turn vague goals into clear options, risks, and a recommended next step.

## Chat-First Behavior

Always answer in chat first:

1. Say what you understood.
2. Say what context is missing.
3. Ask clarifying questions when needed.
4. State decision criteria with weights (summing to 100) before any option
   exists, so the options are judged by what matters, not by how they were framed.
5. Create Option 0 plus 2-3 options (3-4 total).
6. Compare pros, cons, risks, effort, and tests, scoring each option against the
   weighted criteria.
7. Recommend one option.
8. Ask for confirmation before creating context cards, roadmaps, rules, or files.

## Option Rules

- **Option 0: do nothing / smallest version.** Apply rung 1 of
  `build-team/PONYTAIL_RULES.md` ("Does it need to exist? skip what nobody
  asked for"). If Option 0 wins, say so; it is a valid recommendation.
- Per option, state:
  - **Reversibility:** two-way door (cheap to undo) or one-way door (data,
    schema, public contract, or external effect).
  - **Pre-mortem:** one line, "this fails when ...".
  - **Cost to verify:** the narrowest command or check that would prove it works.
  - **Size:** S / M / L / XL.

## When to Use

- New project idea.
- Architecture or roadmap question.
- Ambiguous requirements.
- Major folder/file structure decision.
- Context card, roadmap, or operating rule planning.

## When Not to Use

- Straightforward implementation already confirmed by the user.
- Bug verification or fixing.
- Audit-only work.
- Refactoring or cleanup.

## Non-Technical User Mode

If the user seems non-technical:

- Avoid jargon.
- Give A/B/C choices.
- Recommend one option.
- Explain expected results.
- Provide exact next commands when useful.
- Warn before expensive or risky actions.

## Expected Output Contract

- Short summary of the request.
- Missing context or clarifying questions.
- Criteria and weights table, then the option table (Option 0 included, with
  reversibility, pre-mortem, and size).
- Recommendation.
- Handoff to build-team, when the recommendation is a build: prefilled
  `build-team/FEATURE_CONTRACT_TEMPLATE.md` fields for feature, out of scope,
  business rules known vs unknown (unknown ones flagged for confirmation), owning
  module (from `_agent_ops/REPO_MAP.md`), and first slice. If Option 0 wins, name
  the next team instead.
- Then ONE Next Step Card (`advisor-team/NEXT_STEP_CARD_TEMPLATE.md`).
- Token/risk level.
- Expected output if the user proceeds.
- Confirmation question.

## Safety Rules

- Never use `git add .`.
- Ask before destructive actions.
- Ask before creating major structure or context cards.
- Do not include secrets or private data.
- Update implementation logs in target projects only after permission.


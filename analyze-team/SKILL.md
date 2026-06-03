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
4. Create 2-4 options.
5. Compare pros, cons, risks, effort, and tests.
6. Recommend one option.
7. Ask for confirmation before creating context cards, roadmaps, rules, or files.

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
- 2-4 option table.
- Recommendation.
- Token/risk level.
- Expected output if the user proceeds.
- Confirmation question.

## Safety Rules

- Never use `git add .`.
- Ask before destructive actions.
- Ask before creating major structure or context cards.
- Do not include secrets or private data.
- Update implementation logs in target projects only after permission.


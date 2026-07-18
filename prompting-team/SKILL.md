---
name: prompting-team
description: Use this when the user wants a strong Codex, Cursor, Claude Code, Windsurf, phase, audit, harness, bug-fix, production-readiness, or handoff prompt. Use the readiness gate before large prompts.
---

# Skill: Prompting Team

## Purpose

Create robust prompts and harness instructions that are scoped, testable, safe, and honest.

## Readiness Gate

Before creating a major prompt, use `PROMPT_READINESS_GATE.md`.

Check:

- context sufficiency,
- project context card,
- implementation log,
- expected output,
- phase/part scope,
- test gates,
- audit gates,
- repo hygiene,
- git safety,
- token/risk level,
- whether another team should be used first,
- whether user confirmation is needed before autonomous work,
- the session receipt, closure gate, and whether native child agents are truly
  available for the requested work mode.

## Workflow

1. Read only relevant context and logs.
2. Identify target agent, managed-session state, and work mode.
3. Classify token/risk level.
4. Run the prompt readiness gate for large prompts.
5. Define goal, scope, non-goals, repo path, constraints, and expected output.
6. Include initial inspection, phase gates, tests, audit, repo hygiene, implementation log, commit/push rules, and honesty rules.
7. Show a prompt preview in chat.
8. Suggest optional teams/skills only when useful.
9. Ask before writing prompt files.

## Target-Agent Hardening

When the target is DeepSeek, Gemini, Cursor, another prompt-based harness, or a
model the user identifies as weaker or less suited to the task, default to a
stricter prompt profile:

- Narrow the scope to one phase, module, bug, or audit slice when possible.
- Spell out the exact context-intake order: base rules, project context card,
  implementation log, selected team `SKILL.md`, then only task-relevant files.
- Add explicit checkpoints: report what was read before editing, stop if required
  context is missing, and confirm before crossing scope.
- Prefer an ordered team chain when it improves quality, for example
  `advisor-team -> analyze-team -> prompting-team -> tester-team`.
- Capability-detect real child agents from the current harness rather than
  inferring capability from a model name. When native spawning is unavailable,
  describe these as sequential roles in one session, not parallel subagents.

Use the normal prompt profile for strong/native-agent harnesses, but still keep
scope, gates, tests, and honesty rules explicit.

## When to Use

- Phase-by-phase implementation prompts.
- Audit prompts.
- Bug-fix prompts after triage.
- Handoff prompts.
- Production-readiness prompts.
- Tool/test/eval harness prompts.

## When Not to Use

- Direct code implementation.
- Bug fixing without verification.
- Clean-code execution without `clean-code-team/`.

## Expected Output Contract

- Prompt title and intended use.
- Token/risk level.
- Missing context.
- Expected output.
- Full copy-paste prompt preview.
- Optional team suggestions.
- Confirmation question before file writes.

## Safety Rules

- Every prompt must say: never use `git add .`.
- Prompts must require explicit staging.
- Prompts must ask before destructive actions.
- Prompts must require honest test reporting.
- Prompts must keep public repos clean.

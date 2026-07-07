# Prompt Readiness Gate

Use this gate before creating a large Codex, Cursor, Claude Code, Windsurf, or autonomous execution prompt.

## Context Sufficiency

- [ ] User goal is clear.
- [ ] Target repo path is known.
- [ ] Project context card is available, or missing context is listed.
- [ ] Implementation log is available, or missing history is listed.
- [ ] Relevant phase/part scope is defined.
- [ ] Non-goals are defined.

## Expected Output

- [ ] Expected deliverable is defined.
- [ ] Final report format is defined.
- [ ] User-facing behavior or acceptance criteria are defined.
- [ ] The prompt says what to do if blocked.

## Gates

- [ ] Test gates are included.
- [ ] Audit gates are included when needed.
- [ ] Repo hygiene checks are included.
- [ ] Implementation log update is included.
- [ ] Git safety is included, including never use `git add .`.

## Token and Risk

- [ ] Task is classified as Light, Medium, Heavy, or Very Heavy.
- [ ] Very Heavy work includes a warning.
- [ ] Clean-code work is routed to `clean-code-team/`.
- [ ] Full audit or production readiness work is routed to `tester-team/`.

## Target Agent / Harness

- [ ] Target agent and harness are identified, or missing.
- [ ] If target is DeepSeek, Gemini, Cursor, other prompt-based harness, or a
      weaker/less-suited model, the prompt uses stricter scope.
- [ ] The prompt names the exact context-intake order and required files to read.
- [ ] Any extra teams are listed as an ordered sequence with stop/confirm gates.
- [ ] Prompt-based harnesses are told to run roles sequentially, not as parallel
      subagents.

## Optional Skills / Teams

- [ ] Another team should be suggested only if useful.
- [ ] Suggestions are optional, not forced.

## Confirmation Rule

- [ ] User must confirm before writing prompt files.
- [ ] User must confirm before autonomous execution.
- [ ] User must confirm before commits, pushes, destructive actions, or broad changes.

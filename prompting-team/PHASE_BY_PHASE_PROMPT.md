# Phase-by-Phase Implementation Prompt

```text
You are using prompting-team output for phase-by-phase implementation.

Goal:
<goal>

Repo path:
<absolute repo path>

Scope:
<files, features, or modules in scope>

Non-goals:
<what must not be changed>

Target agent profile:
- Target agent/harness: <Codex / Claude Code / DeepSeek / Gemini / Cursor / other>.
- If target is DeepSeek, Gemini, Cursor, another prompt-based harness, or a
  weaker/less-suited model: keep scope to one phase or module, make every
  context-read step explicit, and stop for confirmation before expanding scope.
- If extra teams are useful, run them as an ordered sequence with checkpoints.
  On prompt-based harnesses these are sequential roles, not parallel subagents.

Initial inspection:
1. Check git status.
2. Read the target project's own AGENTS.md or always-on rules.
3. Read the project context card, implementation log, phase roadmap, decision log,
   and risk register if present.
4. Read the selected team SKILL.md only if it is needed for this task.
5. Inspect only task-relevant source, tests, configuration, and docs before
   editing.
6. Report the exact files read and the intended edit boundary before changing
   files.

Execution:
1. Create a short phase plan.
2. Work one phase at a time.
3. Before each phase, state files likely to change.
4. After each phase, run the smallest meaningful test.
5. Update implementation log with files touched, changes, why, tests, results, risks, and next step.

Phase gates:
- Acceptance criteria are met.
- Tests or manual checks are recorded.
- No unrelated refactors.
- Repo hygiene remains clean.

Git safety:
- Never use git add .
- Stage explicit files only if the user allowed committing.
- Commit only after validation passes and only if the user allowed it.
- Push only if explicitly requested.

Final report:
- What changed.
- Files touched.
- Tests run and results.
- Known risks.
- Git status.
- Next recommended step.

Honesty:
Do not claim tests passed unless actually run. If blocked, report the blocker and the exact next needed input.
```

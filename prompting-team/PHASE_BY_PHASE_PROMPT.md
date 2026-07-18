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
- If native spawning is unavailable, or the target is weaker/less suited to the
  task: keep scope to one phase or module, make every context-read step
  explicit, and stop for confirmation before expanding scope.
- If extra teams are useful, run them as an ordered sequence with checkpoints.
  Capability-detect child agents; if unavailable, these are sequential roles,
  not claimed parallel subagents.

Initial inspection:
1. Check git status.
2. Read the target project's own AGENTS.md or always-on rules.
3. Read `_agent_ops/SESSION_BRIEF.md` and `_agent_ops/OPERATING_RULES.md` first.
4. Use their pointers to read only the relevant project card, current phase card,
   log entries, decisions, roadmap, or risks.
5. Read the selected team SKILL.md only if it is needed for this task.
6. Inspect only task-relevant source, tests, configuration, and docs before
   editing.
7. Report the exact files read and the intended edit boundary before changing
   files.

Execution:
1. Create a short phase plan.
2. Work one phase at a time.
3. Before each phase, state files likely to change.
4. After each phase, run the smallest meaningful test.
5. Root updates the smallest applicable `_agent_ops/` records: Session Brief
   always; append implementation evidence; change project/decision/risk records
   only when durable state, a material decision, or a material risk changed.

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

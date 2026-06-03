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

Initial inspection:
1. Check git status.
2. Read README.md, AGENTS.md, and project context files.
3. Read IMPLEMENTATION_LOG.md and PHASE_ROADMAP.md if present.
4. Inspect only relevant files before editing.

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


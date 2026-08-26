# Build Command

Use this to implement a new feature in an existing codebase. For a bug, use
`fix-bug.md`. For restructuring without new behavior, use `clean-code.md`.

```text
@build-team implement: <feature in one line>

Follow build-team/SKILL.md exactly. Do not write code yet.

1. Restate the goal and non-goals. Read _agent_ops/SESSION_BRIEF.md for
   constraints and _agent_ops/CURRENT_TASK.md for work already in flight.
   Check git state; warn if dirty or behind the base branch.
2. Business rules gate: read `Business Rules & Acceptance Criteria` in
   _agent_ops/PROJECT_CONTEXT_CARD.md. If it does not cover this feature, STOP
   and ask me for the acceptance criteria. Do not invent them.
3. Placement: use _agent_ops/REPO_MAP.md to say which module owns this concern
   and whether the change lands in a hot file. Do not create a new module when
   an existing one owns the concern.
4. Reuse scan: run
   python _agent_ops/tools/scan_deps.py --root . --seed "<concept>" --hops 2
   and tell me what you will reuse versus what is genuinely new.
5. Fill build-team/FEATURE_CONTRACT_TEMPLATE.md: interface, inputs, outputs,
   error cases, side effects and their single owner.
6. Give me files to create/modify, blast radius, cross-boundary warnings,
   rollback, and the token/risk level.
7. If the change spans more than one module, split it using
   build-team/SLICE_PLAN_TEMPLATE.md and propose slice 1 only.
8. Ask for confirmation. Only then write code.

While implementing:
- One responsibility per change; one serialized writer lane.
- Verify every function, API, import, and config key exists before referencing
  it. Never invent a symbol.
- Run the narrowest meaningful test. Do not claim a pass that did not run.
- Keep _agent_ops/CURRENT_TASK.md current: files touched, dead ends, next step.
- Classify actual work against the Session Protocol at closure. The prompt's
  file list never waives the implementation log, project context card, or
  decision log when their trigger occurred; write them before the receipt.
- For an authorized source commit: stage source explicitly after tests, run
  _agent_ops/tools/refresh_repo_map.py with --stage, inspect the generated map,
  then commit. Do not use --no-verify.
- Report the slice, then ask before starting the next one.
- Print the Closure Receipt from _agent_ops/SESSION_PROTOCOL.md.

Never use git add . Do not add or upgrade dependencies without naming the
package, the reason, and the lockfile impact, and getting my confirmation.
Do not commit or push unless I allow it.
```

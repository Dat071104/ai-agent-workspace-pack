---
name: build-team
description: Use this when the user wants to implement a new feature, endpoint, module, or behavior change in an existing codebase. Plans the change, confirms placement and business rules, then writes code in one serialized lane with tests. Not for bug fixes or cleanup.
---

# Skill: Build Team

## Purpose

Implement new behavior in an existing codebase. Every other team either advises,
audits, fixes, or cleans; this is the one that writes new code. It exists so a
request like "add feature X" has a destination instead of detouring through
`analyze-team` and `prompting-team`.

## When to Use

- Add a feature, endpoint, screen, command, or module.
- Extend existing behavior in a planned, additive way.
- Implement a phase from `_agent_ops/PHASE_ROADMAP.md`.

## When Not to Use

- Something is broken -> `bug-fix-team/`.
- Restructuring without new behavior -> `clean-code-team/`.
- Deciding *whether* or *which approach* -> `analyze-team/` first.
- Producing a prompt for a different agent -> `prompting-team/`.
- Auditing what exists -> `tester-team/`.

## Workflow

1. Re-anchor: restate the goal in one line. Check `_agent_ops/SESSION_BRIEF.md`
   for constraints and non-goals, and `_agent_ops/CURRENT_TASK.md` for work
   already in flight. Check git state; warn if the tree is dirty or behind the
   base branch.
2. **Business rules gate.** Read `Business Rules & Acceptance Criteria` in
   `_agent_ops/PROJECT_CONTEXT_CARD.md`. If it is empty or does not cover this
   feature, STOP and ask for the acceptance criteria. Do not invent them. Code
   that compiles but encodes a guessed rule is the most expensive failure this
   team can produce, because it passes review and fails in production.
3. **Placement.** Decide where the code goes using `_agent_ops/REPO_MAP.md`:
   which module owns this concern, its routes and entry points, and whether the
   change lands in a hot file or a most-called symbol. Do not invent a new
   module when an existing one owns the concern.
   `python _agent_ops/tools/explore.py --root . --entrypoints` lists the routes already
   wired up, which is the fastest way to see where a new endpoint belongs.
4. **Reuse scan.** Before writing a function, look for an existing one:

   ```bash
   python _agent_ops/tools/explore.py --root . --symbol <concept>
   python _agent_ops/tools/explore.py --root . --file <the module that owns this>
   ```

   `--symbol` finds definitions that already carry the name or concept;
   `--file` lists everything the owning module already exposes. State explicitly
   what you are reusing and what is genuinely new. Duplicating logic that
   already exists is the seed of the next "fixing one bug created another".
5. **Contract first.** Write down the interface before the implementation:
   function/endpoint signature, inputs, outputs, error cases, and the observable
   acceptance criterion for each business rule.
6. **Impact statement.** Name the files to be created and modified, the blast
   radius, and any cross-boundary effect. When the change modifies an existing
   symbol rather than only adding one, get the radius from the graph:
   `python _agent_ops/tools/explore.py --root . --impact <symbol>`. If the change must
   cross a module boundary, say so before editing, not after.
7. **Plan and confirm.** Present steps 3-6 as a short plan with a token/risk
   level. Get confirmation before writing code. Offer to split into slices when
   the change spans more than one module.
8. Implement ONE slice. One responsibility per change. One serialized writer
   lane -- never two agents writing the same files.
9. **Verify before claiming.** Before referencing any function, API, import, or
   config key, confirm it exists in the codebase or a real dependency. Never
   invent a symbol. Run the narrowest meaningful test; use `tester-team/` or the
   `tester` subagent for a wider check. Do not report a test as passing unless
   it ran.
10. Update `_agent_ops/CURRENT_TASK.md` as you go: files touched, approaches
    ruled out, next step. If you added or moved files, rebuild the index and map
    so the next session is not reasoning on a stale graph:
    `python _agent_ops/tools/build_code_index.py --root .` and
    `python _agent_ops/tools/generate_repo_map.py --root . --output _agent_ops/REPO_MAP.md --force`.
11. Report the slice: files changed, tests run with real output, what is still
    unimplemented. Ask before starting the next slice.
12. Print the Closure Receipt from `_agent_ops/SESSION_PROTOCOL.md`. Commit only
    if the user allowed it.

## Expected Output Contract

- Goal restatement and non-goals.
- Business rules and acceptance criteria used (or the question blocking them).
- Placement decision with the `REPO_MAP.md` evidence behind it.
- What is reused vs newly written.
- Interface contract before implementation.
- Files to create/modify, blast radius, cross-boundary warnings.
- Token/risk level and a confirmation question before writing code.
- After each slice: files changed, tests run, real results, remaining work.
- Closure Receipt per `_agent_ops/SESSION_PROTOCOL.md`.

## Safety Rules

- Never use `git add .`; stage explicit files only.
- Do not write code before the plan is confirmed, unless autonomous mode was
  explicitly approved for this task.
- Do not add, upgrade, or remove a dependency without naming the package,
  version change, reason, and expected lockfile change, and confirming first.
- Do not commit or push unless the user allowed it.
- Do not silently widen scope. A feature request is not permission to refactor
  the surrounding module.

## Correctness Guards

- Anti-guessing: missing business rules are a question, never an assumption.
- Anti-hallucination: only reference symbols verified to exist.
- Anti-duplication: reuse before writing; duplicated logic is the seed of the
  next "fixing one bug created another" report.
- No overlapping side effects: two code paths must not write the same state
  without one clear owner.
- Anti-drift: re-read the goal before each slice. If the work has drifted, stop
  and flag it.
- Honesty: unfinished is reported as unfinished. Untested is reported as
  untested.

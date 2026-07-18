# Team Router

Use this file before loading any long team folder. Route first, then load only the recommended team if the user confirms.

| User intent | Recommended team | Token/risk | Writes files by default? | Subagent | Confirmation needed? |
| --- | --- | --- | --- | --- | --- |
| Overview: what to improve next, priorities, ROI | `advisor-team/` | Medium | No | — | Yes, before routing follow-up work |
| Idea, architecture, options, roadmap | `analyze-team/` | Medium | No | — | Yes, before creating files or context cards |
| Create prompt, harness, phase prompt | `prompting-team/` | Medium to Very Heavy | No | — | Yes, before writing prompt files or autonomous prompts |
| Test, audit, QA, production readiness | `tester-team/` | Medium to Very Heavy | No | `tester` (read-only) | Yes, before running expensive checks |
| Bug report or suspected broken behavior | `bug-fix-team/` | Medium | No | `bug_hunter` (read-only), `bug_fixer` (write) | Yes, before fixing |
| Cleanup, refactor, repo is messy | `clean-code-team/` | Very Heavy | No | — | Yes, before every cleanup batch |
| Git safety, public repo, release check | `repo-hygiene-team/` | Light to Medium | No | `repo_hygiene_reviewer` (read-only) | Yes, before deleting/staging/committing |
| Handoff, report, continue later | `handoff-team/` | Light to Medium | No | — | Yes, before writing handoff files |

`@start-here` starts a managed session and initializes/refreshes only
`_agent_ops/` context. Subagents run only when the task has at least two truly
independent workstreams, native spawning is available, and you confirm after a
token-cost warning. Otherwise the root recommends solo or sequential roles.
Not sure which team? Type `@start-here <one line>`.

## Router-First Rule

When a user starts with a broad request:

1. Do not read every team folder.
2. Use this table or the README routing table.
3. Recommend the best team.
4. Explain why in one or two sentences.
5. Identify missing context.
6. Show expected output.
7. Ask whether to proceed.

## Work-Mode Recommendation

After routing, recommend one mode without assuming the user wants parallelism:

- `solo`: a small contained task;
- `auto`: root decides after minimal inspection (default);
- `parallel`: independent read-only workstreams; capability-detect first;
- `sequential`: dependent work or no real native spawning.

Explain the benefit, token cost, and risk of the recommendation. The root agent
keeps advisor behavior: it must state what it understood, context missing, and
the one confirmation needed before material scope or cost changes.

## Token/Risk Short Guide

- Light: quick routing, small report, simple hygiene check.
- Medium: analysis, scoped prompt, bug triage, scoped audit.
- Heavy: multi-phase prompt, broad audit, production review.
- Very Heavy: clean-code, full codebase audit, multi-phase autonomous execution prompt.

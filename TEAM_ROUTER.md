# Team Router

Use this file before loading any long team folder. Route first, then load only the recommended team if the user confirms.

| User intent | Recommended team | Token/risk | Writes files by default? | Confirmation needed? |
| --- | --- | --- | --- | --- |
| Idea, architecture, options, roadmap | `analyze-team/` | Medium | No | Yes, before creating files or context cards |
| Create prompt, harness, phase prompt | `prompting-team/` | Medium to Very Heavy | No | Yes, before writing prompt files or autonomous prompts |
| Test, audit, QA, production readiness | `tester-team/` | Medium to Very Heavy | No | Yes, before running expensive checks |
| Bug report or suspected broken behavior | `bug-fix-team/` | Medium | No | Yes, before fixing |
| Cleanup, refactor, repo is messy | `clean-code-team/` | Very Heavy | No | Yes, before every cleanup batch |
| Git safety, public repo, release check | `repo-hygiene-team/` | Light to Medium | No | Yes, before deleting/staging/committing |
| Handoff, report, continue later | `handoff-team/` | Light to Medium | No | Yes, before writing handoff files |

## Router-First Rule

When a user starts with a broad request:

1. Do not read every team folder.
2. Use this table or the README routing table.
3. Recommend the best team.
4. Explain why in one or two sentences.
5. Identify missing context.
6. Show expected output.
7. Ask whether to proceed.

## Token/Risk Short Guide

- Light: quick routing, small report, simple hygiene check.
- Medium: analysis, scoped prompt, bug triage, scoped audit.
- Heavy: multi-phase prompt, broad audit, production review.
- Very Heavy: clean-code, full codebase audit, multi-phase autonomous execution prompt.


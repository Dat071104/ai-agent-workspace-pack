---
name: bug-fix-team
description: Use this when the user reports a bug or failed behavior. Verify first with a failing test, reason across multiple root-cause hypotheses and fix directions for non-obvious bugs, then recommend one minimal fix before editing. Fast path for obvious bugs. Can run parallel bug_hunter subagents for hard bugs.
---

# Bug-Fix Team (adapter)

This is a Claude Code adapter. The source of truth is `bug-fix-team/SKILL.md` at
the repo root. Read that file and follow it exactly. Open a reference below only
when the step you are on names it; do not preload them.

References: `bug-fix-team/ROOT_CAUSE_HYPOTHESES_TEMPLATE.md`,
`bug-fix-team/FIX_DIRECTIONS_TEMPLATE.md`, `bug-fix-team/ZONE_BRAIN_FIX_PROMPT.md`,
`bug-fix-team/BUG_TRIAGE_PROMPT.md`, `build-team/PONYTAIL_RULES.md`,
`build-team/SELF_REVIEW_CHECKLIST.md`. For hard/ambiguous bugs, offer parallel
`bug_hunter` subagents (warn about token cost first), then a single `bug_fixer`.

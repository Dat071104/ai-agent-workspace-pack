---
name: bug-fix-team
description: Use this when the user reports a bug or failed behavior. Verify first, reason across multiple root-cause hypotheses and fix directions, then recommend one minimal fix before editing. Can run parallel bug_hunter subagents for hard bugs.
---

# Bug-Fix Team (adapter)

This is a Claude Code adapter. The source of truth is `bug-fix-team/SKILL.md` at
the repo root. Read that file and its references, then follow it exactly.

References: `bug-fix-team/ROOT_CAUSE_HYPOTHESES_TEMPLATE.md`,
`bug-fix-team/FIX_DIRECTIONS_TEMPLATE.md`, `bug-fix-team/ZONE_BRAIN_FIX_PROMPT.md`,
`bug-fix-team/BUG_TRIAGE_PROMPT.md`. For hard/ambiguous bugs, offer parallel
`bug_hunter` subagents (warn about token cost first), then a single `bug_fixer`.

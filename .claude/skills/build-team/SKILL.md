---
name: build-team
description: Use this when the user wants to implement a new feature, endpoint, module, or behavior change in an existing codebase. Plans the change, confirms placement and business rules, then writes the smallest complete change (ponytail rules) in one serialized lane with tests and a self-review. Not for bug fixes or cleanup.
---

# Build Team (adapter)

This is a Claude Code adapter. The source of truth is `build-team/SKILL.md` at
the repo root. Read that file and its references, then follow it exactly.

References: `build-team/FEATURE_CONTRACT_TEMPLATE.md`,
`build-team/SLICE_PLAN_TEMPLATE.md`, `build-team/PONYTAIL_RULES.md`,
`build-team/SELF_REVIEW_CHECKLIST.md`. Use `_agent_ops/REPO_MAP.md` for placement
and blast radius, and the `tester` subagent (read-only) for verification. There
is no dedicated write subagent: the root agent is the single writer lane.

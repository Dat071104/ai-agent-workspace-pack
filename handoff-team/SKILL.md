---
name: handoff-team
description: Use this for session handoffs, final reports, continuity summaries, next-session prompts, and milestone delivery notes. Do not use for code changes or bug fixing.
---

# Skill: Handoff Team

## Name

Handoff Team

## Description

Creates complete or compact handoff artifacts for continuity across sessions, agents, milestones, or final delivery.

## When to Use

- End of session.
- Before changing agents.
- Before release.
- After major phase completion.
- For portfolio/demo final reports.

## When Not to Use

- Direct code implementation.
- Bug fixing.
- Cleanup or refactoring.
- Audit-only work without a handoff need.

## Workflow

1. Read project context and logs.
2. Check git state and recent commit if available.
3. Summarize architecture and current status.
4. List what was built and files touched.
5. Record run/test commands.
6. Capture known issues and risks.
7. Provide next steps and next-session prompt.

## Output Format

- Executive summary.
- Repo state.
- Architecture.
- Work completed.
- How to run/test.
- Known issues.
- Next steps.
- Suggested next prompt.

## Safety Rules

- Never use `git add .`.
- Do not modify code unless asked.
- Do not commit or push unless user allowed it.
- Do not include secrets or private data.

---
name: repo-hygiene-team
description: Use this for git safety, public repo cleanliness, forbidden tracked files, generated artifacts, release readiness, and safe staging. Do not use for feature work or broad code cleanup.
---

# Skill: Repo Hygiene Team

## Name

Repo Hygiene Team

## Description

Checks git safety, public repo cleanliness, ignored files, generated artifacts, release readiness, and safe staging.

## When to Use

- Before commit.
- Before push.
- Before release.
- Before making a public repo.
- When generated/private files may be tracked.

## When Not to Use

- Feature implementation.
- Bug fixing.
- Broad cleanup or refactoring.
- Writing private project logs.

## Workflow

1. Check git status.
2. Inspect `.gitignore`.
3. Run hygiene script if available.
4. Check tracked files for forbidden patterns.
5. Check `_agent_ops/` against the hybrid tracking policy: durable memory
   (`INDEX.md`, `PROJECT_CONTEXT_CARD.md`, `REPO_MAP.md`, `HANDOFF.md`,
   `IMPLEMENTATION_LOG.md`, `archive/`, `DECISION_LOG.md`, `RISK_REGISTER.md`,
   `PHASE_ROADMAP.md`, `OPERATING_RULES.md`, `SESSION_PROTOCOL.md`,
   `phase_context_cards/`) is tracked on purpose so it survives a clone;
   only machine-local scratch (`SESSION_BRIEF.md`, `CURRENT_TASK.md`) and the
   derived `LOG_SUMMARY.md` stay untracked. Flag either direction. Tracked ops
   files are public on a public repo, so also check the log, archive, and
   handoff for secrets, credentials, customer names, and internal URLs.
6. Check docs and release readiness.
7. Report pass/fail and exact remediation.

## Output Format

- Git state.
- Hygiene findings.
- Forbidden tracked files.
- `_agent_ops/` tracking policy compliance.
- Release readiness.
- Recommended exact commands.

## Safety Rules

- Never use `git add .`.
- Do not remove files without user confirmation.
- Do not commit or push unless user allowed it.
- Do not expose secrets in reports.

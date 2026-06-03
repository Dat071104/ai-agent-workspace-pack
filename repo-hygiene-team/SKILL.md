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
5. Check docs and release readiness.
6. Report pass/fail and exact remediation.

## Output Format

- Git state.
- Hygiene findings.
- Forbidden tracked files.
- Release readiness.
- Recommended exact commands.

## Safety Rules

- Never use `git add .`.
- Do not remove files without user confirmation.
- Do not commit or push unless user allowed it.
- Do not expose secrets in reports.

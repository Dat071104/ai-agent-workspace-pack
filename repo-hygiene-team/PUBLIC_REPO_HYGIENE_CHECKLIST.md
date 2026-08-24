# Public Repo Hygiene Checklist

- [ ] README explains what the repo is.
- [ ] Setup and usage are clear.
- [ ] License exists.
- [ ] `.gitignore` blocks common generated/private files.
- [ ] No secrets are tracked.
- [ ] No local logs are tracked.
- [ ] No generated build outputs are tracked.
- [ ] No datasets, model files, or database files are tracked.
- [ ] Examples are generic and public-safe.
- [ ] Implementation logs do not expose private details.
- [ ] Commit history is acceptable for public release.

## `_agent_ops/` Hybrid Tracking Policy

Durable memory is tracked so it survives a clone; session scratch stays local.
`scripts/check_repo_hygiene.py` fails the build on a violation.

- [ ] `_agent_ops/.gitignore` exists.
- [ ] Session-scoped files are NOT tracked: `SESSION_BRIEF.md`,
      `CURRENT_TASK.md`, `LOG_SUMMARY.md`.
- [ ] Durable memory IS tracked so a fresh clone keeps it: `INDEX.md`,
      `OPERATING_RULES.md`, `SESSION_PROTOCOL.md`, `PROJECT_CONTEXT_CARD.md`,
      `REPO_MAP.md`, `HANDOFF.md`, `IMPLEMENTATION_LOG.md`, `archive/`,
      `DECISION_LOG.md`, `RISK_REGISTER.md`, `PHASE_ROADMAP.md`,
      `phase_context_cards/`.
- [ ] On a PUBLIC repo, review `IMPLEMENTATION_LOG.md`, `archive/`, and
      `HANDOFF.md` before release: they are tracked and therefore public. Keep
      customer names, internal URLs, and incident detail out of them.
- [ ] Tracked ops files contain no secrets, credentials, customer data, internal
      URLs, or unverified claims. On a public repo they are public.
- [ ] `REPO_MAP.md` exposes only paths that are already public in the repo.


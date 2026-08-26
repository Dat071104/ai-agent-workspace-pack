# Git Safety Rules

- Never use `git add .`.
- Stage explicit files only.
- Run `git status --short` before changes.
- Run `git status --short` after changes.
- Do not commit secrets.
- Do not commit private data.
- Do not commit model files, datasets, databases, or generated artifacts.
- Do not commit local ops logs by default.
- Commit only after validation passes.
- For a commit containing staged project code, run
  _agent_ops/tools/refresh_repo_map.py with --stage after validation and before
  git commit. It stages only the generated REPO_MAP.md; never bypass the managed
  hook with --no-verify.
- Push only when the user requested it.

`_agent_ops/` follows a hybrid policy rather than a blanket rule. Session-scoped
files stay local; durable project memory is tracked on purpose so it survives a
clone. `_agent_ops/.gitignore` enforces it, and `scripts/check_repo_hygiene.py`
exits 1 when a session-scoped file is tracked.

Never track:

- `_agent_ops/SESSION_BRIEF.md`
- `_agent_ops/CURRENT_TASK.md`
- `_agent_ops/LOG_SUMMARY.md`

Do track (a fresh clone must keep these):

- `_agent_ops/IMPLEMENTATION_LOG.md` and `_agent_ops/archive/`
- `_agent_ops/HANDOFF.md`
- `_agent_ops/PROJECT_CONTEXT_CARD.md`, `REPO_MAP.md`, `DECISION_LOG.md`,
  `RISK_REGISTER.md`, `PHASE_ROADMAP.md`, `phase_context_cards/`

Forbidden examples:

- `.env`
- `data/`
- `models/`
- `mlruns/`
- `artifacts/`
- `node_modules/`
- `dist/`
- `build/`
- `__pycache__/`
- `.pytest_cache/`
- `target/`
- `logs/`
- `*.sqlite`
- `*.sqlite3`
- `*.db`


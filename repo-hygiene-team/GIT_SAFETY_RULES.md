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
- Push only when the user requested it.

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


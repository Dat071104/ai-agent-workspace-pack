# Scripts

Lightweight Python helpers for initializing project memory, scanning simple dependencies, checking repo hygiene, generating starter context cards, and summarizing implementation logs.

All scripts use the Python standard library only.

## Commands

```bash
python scripts/init_project_ops.py --target "D:\MyProject"
python scripts/scan_deps.py --root . --seed "auth,login,session" --hops 2 --output markdown
python scripts/check_repo_hygiene.py --root .
python scripts/generate_context_card.py --root . --name "Project Alpha"
python scripts/summarize_implementation_log.py --log "_agent_ops/IMPLEMENTATION_LOG.md"
```

Safety:

- Scripts are cross-platform.
- Scripts print clear output.
- Scripts do not modify code unexpectedly.
- `init_project_ops.py` will not overwrite existing files unless `--force` is passed.


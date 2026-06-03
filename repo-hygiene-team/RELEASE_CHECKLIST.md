# Release Checklist

- [ ] Tests pass.
- [ ] Documentation is usable.
- [ ] Git status is clean.
- [ ] Hygiene script passes.
- [ ] No private/generated files are tracked.
- [ ] Version or release notes are prepared.
- [ ] Tag name is selected.
- [ ] Push target is confirmed.

Suggested release flow:

Do not copy this blindly. Run tag or push commands only after explicit user confirmation and only after the branch, remote, and tag name are confirmed.

```bash
git status --short
python scripts/check_repo_hygiene.py --root .
git tag v0.1.0
git push origin v0.1.0
```

Use explicit staging only. Never use `git add .`.

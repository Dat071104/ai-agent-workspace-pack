# Safe Refactor Checklist

- [ ] User confirmed cleanup risk.
- [ ] Git state is clean.
- [ ] Recovery branch or tag exists.
- [ ] Current tests pass or baseline failures are documented.
- [ ] Batch scope is small.
- [ ] Public behavior is unchanged unless explicitly requested.
- [ ] API and file format contracts are preserved.
- [ ] Tests cover touched behavior.
- [ ] Implementation log is updated.
- [ ] No generated/private files are staged.
- [ ] `git add .` is not used.


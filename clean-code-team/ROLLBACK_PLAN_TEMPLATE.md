# Rollback Plan Template

## Recovery Point

- Branch:
- Tag:
- Commit:

## Files Changed in Batch

- `<file>`

## Symptoms That Require Rollback

- `<symptom>`

## Rollback Steps

```bash
git status --short
git restore --staged <explicit-file>
git restore <explicit-file>
```

Use exact file paths. Do not use `git add .`.

## Post-Rollback Check

```bash
<test command>
```


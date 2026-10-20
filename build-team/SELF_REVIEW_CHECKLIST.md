# Self-Review Checklist

Adapted from ponytail-review (MIT, (c) 2026 DietrichGebert), upstream commit
9b58c1f. See `THIRD_PARTY_NOTICES.md`.

For M/L builds and Medium/Hard bugs (bug-fix: Bug / Risk / Scale / Missing
test only); S and Obvious use the Quick Self-Check in `PONYTAIL_RULES.md`.
Changes no code. Fix every Must fix first.

Review like the senior developer who will be paged when it breaks. Order of
importance: correct, safe, holds under load, tested, fast, lean. Every extra
line must be read, tested, and fixed later.

## 1. Understand First

- Input: the task's files, from `git status --short` (staged, unstaged,
  untracked), limited to what this task touched. Review tracked files with
  `git diff HEAD -- <file>`; read new files in full; never stage just to review.
  Then run `python _agent_ops/tools/explore.py --root . --impact <symbol>` (qualname
  if ambiguous) for
  each changed symbol and read those callers, the functions the change calls,
  and the tests.
- Trace the real flow: where data comes in, what is stored, what goes out.
- A change can break code it does not touch. When a signature, return value, or
  behavior changes, check every caller.
- Find the expected load (README, deploy config): one person running a script,
  or many users and processes. Judge scale against it and state the load you
  assumed.

## 2. Look For

1. **Bug:** wrong result, crash, missed edge case (empty, zero, last item,
   rounding, time zones), a broken caller, a fix applied in one caller while the
   shared function stays broken.
2. **Risk:** security holes (injection, weak randomness, secrets, unchecked user
   input), data loss (swallowed errors, wrong write order, no transaction).
3. **Scale:** fine for one user, wrong for many: check-then-write races, the
   same work in every process, unbounded growth, a query per item, O(n^2) on big
   input, per-process state that must be shared.
4. **Missing test:** risky new logic (branch, parser, money, security, data
   write, bug fix) with no test that fails when it breaks. One good test, not
   coverage.
5. **Speed:** big slowdowns are problems; small wins are suggestions.
6. **Lean:** delete (dead code, unused options, speculative features), reuse
   (name the existing helper's path), stdlib/native, yagni (one-implementation
   abstraction, config nobody sets), merge (near-copies), split (one function,
   several jobs; split by job, never by line count).

## 3. Check Before You Report

- No concrete case, no finding: name the input or situation and the wrong result.
- Re-read the lines: the caller exists, the value can really be empty, the code
  really is unused.
- A `shortcut:` marker naming its limit and trigger is a decision, not a
  finding, unless the expected load already crosses it.
- Propose the smallest fix that works; prefer fixes that delete code. No style
  taste, no "consider", no vague worries.

## 4. Output

Short sentences, everyday words; explain a technical term once. Findings and
verdict only; for M/L add a leading `What this change does:` (two or three
sentences). Skip empty groups:

- **Must fix:** bug, security, data loss, breaks at expected load.
- **Should fix:** risky code without a test, real slowness, duplication, mixed
  jobs, code that should not exist.
- **Nice to have:** small speed-ups, shorter forms.

Number findings across all groups ("fix 2 and 5"). Each has four parts:

```text
2. **<title>** (`path:Lstart-end`)
   - **What this is:** <what the code does>
   - **Problem:** <concrete case and wrong result>
   - **Fix:** <smallest change>
   - **If we skip it:** <consequence>
```

End with `Verdict: Ship.` or `Verdict: fix 1 and 3 first.`, then
`Lean: -N lines possible.` when lean findings exist, and `Not checked:` if
something mattered and could not be checked. Nothing found: `Looks good. Ship.`
plus one line on what was checked.

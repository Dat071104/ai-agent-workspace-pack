# Build Team

Use `build-team/` to implement new behavior in an existing codebase: a feature,
endpoint, module, or planned extension.

It is the only team that writes new code by default. `bug-fix-team/` repairs
broken behavior, `clean-code-team/` restructures without adding behavior, and
`prompting-team/` produces prompts for a different agent to execute.

Vietnamese note: Team nay dung de viet tinh nang moi. Phai co acceptance
criteria truoc khi code; neu thieu thi hoi, khong doan.

The workflow front-loads the three things that make new code go wrong:

1. missing business rules (guessed instead of asked),
2. wrong placement (new module invented when one already owns the concern),
3. duplicated logic (written again instead of reused).

Files:

- `SKILL.md`
- `FEATURE_CONTRACT_TEMPLATE.md`
- `SLICE_PLAN_TEMPLATE.md`

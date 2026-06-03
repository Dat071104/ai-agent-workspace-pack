# Operating Rules / Quy tac van hanh

## Agent Behavior

- Read project context before acting.
- Ask clarifying questions when scope is unclear.
- Explain assumptions.
- Do not claim tests passed unless they were run.
- Prefer Vietnamese when the user writes Vietnamese.

## Repo Hygiene

- Keep public repos free of secrets, private data, generated artifacts, databases, and local logs.
- Check git status before and after changes.
- Never use `git add .`.
- Stage explicit files only.

## Testing

- Run the smallest meaningful test first.
- Add broader tests when touching shared behavior.
- Record commands and results in the implementation log.

## Commit Rules

- Commit only when the user allowed it.
- Commit after validation passes.
- Use clear commit messages.
- Push only when requested.

## Safety Rules

- Ask before destructive actions.
- Ask before major structure creation unless the user explicitly requested autonomous execution.
- For high-risk cleanup, use `clean-code-team/`.


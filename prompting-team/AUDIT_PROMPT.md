# Audit Prompt

```text
You are using prompting-team to run an audit prompt.

Goal:
Audit the project or selected scope without fixing.

Repo path:
<absolute repo path>

Scope:
<full project, feature, folder, or phase>

Steps:
1. Check git status.
2. Read README.md, AGENTS.md, project context cards, implementation logs, decision logs, and risk register if present.
3. Inspect relevant code, tests, configuration, and docs.
4. Run safe read-only commands and tests when appropriate.
5. Report issues by severity with file/line references where possible.

Audit areas:
- functionality,
- integration,
- UX,
- accessibility basics,
- performance,
- security and safety,
- repo hygiene,
- documentation,
- test coverage.

Rules:
- Do not fix issues.
- Never use git add .
- Do not modify files.
- Do not commit or push.
- Be explicit about commands run and tests not run.

Final report:
- Findings ordered by severity.
- Evidence and reproduction notes.
- Open questions.
- Recommended next actions.
```


# Audit Prompt

```text
You are using prompting-team to run an audit prompt.

Goal:
Audit the project or selected scope without fixing.

Repo path:
<absolute repo path>

Scope:
<full project, feature, folder, or phase>

Target agent profile:
- Target agent/harness: <Codex / Claude Code / DeepSeek / Gemini / Cursor / other>.
- If native spawning is unavailable, or the target is weaker/less suited to the
  task: audit a smaller slice first, use explicit read lists, and avoid broad
  conclusions without evidence.
- If several teams would help, run them as ordered sequential roles unless the
  harness has real subagents.

Steps:
1. Check git status.
2. Read the target project's own AGENTS.md or always-on rules.
3. Read `_agent_ops/SESSION_BRIEF.md` and `_agent_ops/OPERATING_RULES.md` first.
4. Read only context cards, log entries, decisions, and risks relevant to this
   audit; state any missing evidence.
5. Read only the selected team SKILL.md files needed for this audit.
6. Inspect relevant code, tests, configuration, and docs.
7. Run safe read-only commands and tests when appropriate.
8. Report issues by severity with file/line references where possible.

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

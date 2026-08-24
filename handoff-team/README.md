# Handoff Team

Use `handoff-team/` to create continuity between sessions, agents, or project phases.

Handoff reports include:

- executive summary,
- repo state,
- branch/commit,
- architecture,
- what was built,
- how to run,
- how to test,
- known issues,
- next steps,
- files intentionally ignored,
- suggested prompt for next session.

Vietnamese note: Team nay tao bao cao ban giao de phien sau tiep tuc dung cho.

Output location:

- Chat report for the user, and
- `_agent_ops/HANDOFF.md` (tracked) so the next session -- possibly on another
  machine -- finds it without being told. `scripts/session_start.py` reports
  `CONTINUATION` when its `Status` is `open`.

Files:

- `SKILL.md`
- `HANDOFF_REPORT_TEMPLATE.md`
- `NEXT_SESSION_CONTEXT_TEMPLATE.md`
- `FINAL_PROJECT_REPORT_TEMPLATE.md`


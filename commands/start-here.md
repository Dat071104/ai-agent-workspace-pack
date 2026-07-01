# Start-Here Command (Advanced Auto-Router)

Use this when you do not know which team to use. Type `@start-here` plus a
one-line description of what you want. The agent routes automatically, warns
about token/risk, and asks at most one clarifying question before doing work.

```text
@start-here <one-line description of your goal>

You are the auto-router for this workspace pack.

Read only AGENTS.md, TEAM_ROUTER.md, and START_HERE.md first. Do not load every
team folder.

Do this:
1. Classify the intent and pick the best team from TEAM_ROUTER.md.
2. State the recommended team in one line and why in one line.
3. Tell me the exact way to invoke that team on MY harness (detect it; if unsure,
   ask once):
   - Codex: reference the team, e.g. "@bug-fix-team/SKILL.md", or invoke the
     matching .codex subagent for parallel work.
   - Claude Code: the team is a discoverable skill; you may also spawn the
     matching .claude subagent.
   - DeepSeek (deepcode) / Gemini (Antigravity) / Cursor / other: these are
     prompt-based with no native parallel subagents. Suggest the exact
     @reference to paste, e.g. "@tester-team/SKILL.md", and note that any "roles"
     run sequentially in one session, not in parallel.
4. Classify token/risk (Light / Medium / Heavy / Very Heavy) and warn if the
   work is Heavy or Very Heavy, per harness/TOKEN_RISK_MATRIX.md.
5. Note whether a real subagent applies (tester, bug_hunter, bug_fixer,
   repo_hygiene_reviewer) and whether parallel work would help. On prompt-based
   harnesses, say parallel is unavailable and offer sequential role-play instead.
6. Ask the SINGLE most important clarifying question, only if one is needed.
7. Show the expected output before starting.
8. Wait for my confirmation before writing or modifying files.

Rules:
- Chat first, files later.
- One clarifying question maximum, not five.
- Never use git add .
- Do not install dependencies.
- Do not run Heavy or E2E commands without approval.
- Do not claim a subagent was spawned on a harness that has no native subagents.
- Keep it concise and honest. Lead with the routing decision.
```

## Behavior Summary

- One-line in, routed answer out.
- Always shows token/risk before heavy work.
- At most one clarifying question.
- Never writes files or runs heavy commands without confirmation.

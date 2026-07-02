# Start Here

Use this file when you want a simple entry point for an AI coding session.

You do not need to read every folder in this pack. Start with this file and `AGENTS.md`. (`README.md` is a fuller guide for humans; the agent does not need to load it to route a task.) Describe your goal in plain language. The agent should route your request to the right team, explain why, ask clarifying questions if needed, and ask before writing or modifying files.
If the user attaches or pastes a long prompt/document, treat it as the task specification unless the user explicitly says it is only reference material.
If the task is still ambiguous, ask one concise clarification question.

## Fastest Entry: `@start-here`

If you do not know which team to use, type `@start-here` plus one line about your
goal. The agent auto-routes, warns about token/risk, and asks at most one
clarifying question before doing anything. See `commands/start-here.md`.

```text
@start-here I want to <goal in one line>.
```

## Context Intake Tiers (load in order, only as needed)

To keep context light on every agent, load files tier by tier and stop as soon
as you can act:

- Tier 0: `AGENTS.md`, `TEAM_ROUTER.md` (route the task).
- Tier 1: the ONE selected team's `SKILL.md` -- not the whole team folder.
- Tier 2: only the specific templates/prompts that `SKILL.md` references.
- Tier 3: only the target project files needed for the task.

Do not read every team folder, and do not pull in `README.md` to route.

## How This Should Work

1. You describe what you want.
2. The agent reads only the short entry docs first.
3. The agent uses `TEAM_ROUTER.md` to recommend a team.
4. The agent tells you the token/risk level.
5. The agent shows the expected output.
6. The agent asks for confirmation before writing files.

## If You Are Non-Technical

You can write what you want in normal language. You do not need to know the right framework, architecture, test command, or git command. The agent should give simple A/B/C choices, recommend one, explain expected results, and warn before expensive or risky work.

Vietnamese note: Ban co the mo ta y tuong bang ngon ngu binh thuong. Agent phai hoi lai, dua lua chon, va xin xac nhan truoc khi sua file.

## Examples

### Example 1: New Idea

```text
@start-here I want to build a budget tracker app. Analyze the idea first. Do not create files yet.
```

### Example 2: Phase Prompt

```text
@start-here I already have a project. Help me create a strong Codex prompt for Phase 1.
```

### Example 3: Bug Report

```text
@start-here I found a bug. Verify if it is real before fixing.
```

### Example 4: Messy Repo

```text
@start-here My repo is messy. Audit cleanup opportunities only. Do not modify files.
```

## Recommended First Prompt

```text
@start-here I want to [describe goal].
Route me to the right team, ask clarifying questions, and do not write files until I confirm.
```


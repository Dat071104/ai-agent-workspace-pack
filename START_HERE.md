# Start Here

Use this file when you want a simple entry point for an AI coding session.

You do not need to read every folder in this pack. Start with this file, `README.md`, or `AGENTS.md`. Describe your goal in plain language. The agent should route your request to the right team, explain why, ask clarifying questions if needed, and ask before writing or modifying files.
If the user attaches or pastes a long prompt/document, treat it as the task specification unless the user explicitly says it is only reference material.
If the task is still ambiguous, ask one concise clarification question.

## Fastest Entry: `@start-here`

If you do not know which team to use, type `@start-here` plus one line about your
goal. The agent auto-routes, warns about token/risk, and asks at most one
clarifying question before doing anything. See `commands/start-here.md`.

```text
@start-here I want to <goal in one line>.
```

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
@START_HERE.md
I want to build a budget tracker app. Analyze the idea first. Do not create files yet.
```

### Example 2: Phase Prompt

```text
@START_HERE.md
I already have a project. Help me create a strong Codex prompt for Phase 1.
```

### Example 3: Bug Report

```text
@START_HERE.md
I found a bug. Verify if it is real before fixing.
```

### Example 4: Messy Repo

```text
@START_HERE.md
My repo is messy. Audit cleanup opportunities only. Do not modify files.
```

## Recommended First Prompt

```text
@START_HERE.md
I want to [describe goal].
Please route me to the right team, ask clarifying questions, and do not write files until I confirm.
```


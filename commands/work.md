# Managed Work Command

Use this after `@start-here` has initialized the session. Normal natural-language
requests also use `auto`; this command is only for an explicit mode override.

```text
@work <auto | solo | parallel | sequential> [--prefer-subagents] <task>

Continue the managed session defined by AGENTS.md and
_agent_ops/SESSION_PROTOCOL.md.

1. Re-read only _agent_ops/SESSION_BRIEF.md and the active task's minimal
   context; do not reload every log or team folder.
2. Restate the goal, non-goals, constraints, and the relevant missing context.
3. Recommend the smallest useful mode. Treat `parallel`, or a clear natural-
   language request to spawn/use subagents, as a request to assess eligibility,
   not permission to spawn blindly. The latter enters `auto --prefer-subagents`
   without requiring the user to type this command again.
4. For real parallel work, require at least two independent workstreams,
   capability-detect native child-agent support, state token cost, give each
   child a bounded read-only context capsule, and keep all writes serialized.
5. If spawning is unavailable or not worthwhile, use sequential role checks and
   say so plainly.
6. Keep the advisor behavior: ask one focused clarification/confirmation when
   it materially changes the decision; do not infer broad scope.
7. Before a meaningful completion report, let the root update the smallest
   required _agent_ops records under SESSION_PROTOCOL.md. Do not stage, commit,
   or push them automatically.

Never use git add . Do not claim agents were spawned unless real child agents
were created by the current harness.
```

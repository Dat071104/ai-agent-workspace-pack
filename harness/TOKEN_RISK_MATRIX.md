# Token and Risk Matrix

Use this matrix before starting work. It helps the agent warn users about cost, complexity, and confirmation level.

| Level | Examples | Warning | Recommended model strength | Confirmation level | Full audit? |
| --- | --- | --- | --- | --- | --- |
| Light | Route task, answer question, small hygiene check, short handoff | Low time and token use | Standard capable model | Confirm before files only | No |
| Medium | Analyze idea, create scoped prompt, bug triage, scoped audit | Some context reading needed | Strong general model | Confirm before edits or long scans | Usually no |
| Heavy | Multi-phase prompt, broad audit, production-readiness review, large handoff | Can take time and many tokens | Strong model recommended | Confirm scope and expensive checks | Maybe |
| Very Heavy | Clean-code, full codebase audit, multi-phase autonomous execution prompt | High token/time/risk; can break working code if edits are allowed | Strongest available model | Confirm before start and before each risky step | Use only if needed |

## Practical Rules

- Full codebase audits are usually Heavy or Very Heavy.
- Clean-code is always Very Heavy.
- Production-readiness audit is usually Heavy.
- Bug triage is Medium until a fix is confirmed.
- If the user seems non-technical, explain the level in plain language and give A/B/C choices.


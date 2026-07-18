# Prompt Review Checklist

Before using a generated prompt, verify:

- [ ] Goal is explicit.
- [ ] Scope and non-goals are defined.
- [ ] Repo path placeholder is present.
- [ ] Initial inspection is included.
- [ ] Context/log reading is included.
- [ ] Managed-session hot context and the root-owned closure gate are included.
- [ ] Target agent/harness is identified.
- [ ] Native child-agent capability is detected; weaker or non-native targets use tighter scope.
- [ ] The prompt says exactly which context files to read and in what order.
- [ ] Extra teams, if useful, are ordered with explicit stop/confirm gates.
- [ ] Non-native harness roles are sequential, not claimed as parallel subagents.
- [ ] Subagents have bounded context capsules; root owns git, synthesis, and `_agent_ops/`.
- [ ] Phase gates or acceptance checks are included.
- [ ] Test requirements are included.
- [ ] Audit or review step is included when needed.
- [ ] Implementation log update is required.
- [ ] Git safety says never use `git add .`.
- [ ] Commit and push rules are explicit.
- [ ] Public repo hygiene is included.
- [ ] Final report format is included.
- [ ] Honesty rule is included.

# Risk Register / Danh sach rui ro

| Risk ID | Severity | Likelihood | Area | Description | Mitigation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| RISK-0001 | Medium | Low | Embedded layout | Legacy flat-copy embeds can still collide with host paths such as scripts/, .codex/, and .claude/. | Use `--embedded-folder ai-agent-workspace-pack` for new installs; retain flat mode only for compatibility. | Mitigated |
| RISK-0002 | Low | Medium | Harness discovery | Codex/Claude/Gemini may require lightweight root entry files even when all pack content is namespaced. | Keep root `AGENTS.md` as a first-line bridge; create `CLAUDE.md` and `GEMINI.md` only if absent, never overwrite host files. | Accepted |
| RISK-0003 | High | High | Harness discovery | A namespaced install buries `.codex/agents/`, `.claude/agents/`, and `.claude/skills/` one level down, where no harness auto-discovers them; the four subagents and nine team skills silently disappear while AGENTS.md still promises them. | Installer generates marked root pointers whose paths resolve into the pack folder; verified by golden test and a scratch install. Codex discovery confirmed by file placement, not by a Codex run. | Mitigated |
| RISK-0005 | Medium | Medium | Bootstrap | An install can stop at the missing-bridge warning: ops and adapters exist but no root `AGENTS.md` line, so no harness reads the pack. | The warning prints the exact one-line command; prepending a host file stays opt-in by design. | Accepted |
| RISK-0004 | Low | Medium | Code graph | A legacy flat embedded root still indexes its own pack scripts, because a flat host and a pack source checkout share the same markers. | New installs use the namespaced layout, where the exclusion is unambiguous. | Accepted |

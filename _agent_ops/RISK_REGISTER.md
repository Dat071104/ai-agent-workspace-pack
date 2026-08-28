# Risk Register / Danh sach rui ro

| Risk ID | Severity | Likelihood | Area | Description | Mitigation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| RISK-0001 | Medium | Low | Embedded layout | Legacy flat-copy embeds can still collide with host paths such as scripts/, .codex/, and .claude/. | Use `--embedded-folder ai-agent-workspace-pack` for new installs; retain flat mode only for compatibility. | Mitigated |
| RISK-0002 | Low | Medium | Harness discovery | Codex/Claude/Gemini may require lightweight root entry files even when all pack content is namespaced. | Keep root `AGENTS.md` as a first-line bridge; create `CLAUDE.md` and `GEMINI.md` only if absent, never overwrite host files. | Accepted |

# Risk Register / Danh sach rui ro

| Risk ID | Severity | Likelihood | Area | Description | Mitigation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| RISK-0001 | Medium | Medium | Embedded layout | Flat-copy embeds can still collide with host paths such as scripts/, .codex/, and .claude/. | Keep v1.1 compatibility-only; design namespaced .ai-agent-workspace-pack/ migration with adapter installation tests before changing the default. | Open |

# Advisor Team

Use `advisor-team/` for a senior advisor/mentor overview of a whole project. It
reads the context card and idea, assesses the current state, then ranks
improvement opportunities by business value and estimates how hard each one is.
It reports and routes; it does not change code.

When to use this vs `analyze-team/`:

- `advisor-team/` answers "what is most worth doing next, and why" across the
  whole project (overview, ROI, priorities).
- `analyze-team/` answers "how should I do THIS one thing" for a single decision
  (2-4 options, architecture, effort).

Vietnamese note: Dung team nay khi muon goc nhin sep/mentor tong quan: nen cai
thien gi truoc, kho de the nao, va viec nao chua nen lam. Chi bao cao, khong sua code.

Files:

- `SKILL.md`: workflow instructions.
- `ADVISORY_PROMPT.md`: copy-paste advisory prompt.
- `OPPORTUNITY_REGISTER_TEMPLATE.md`: ranked improvement register.
- `EFFORT_COMPLEXITY_RUBRIC.md`: difficulty scoring (S/M/L/XL).

Git safety:

- Read-only team. Never use `git add .`. Do not commit or change code.

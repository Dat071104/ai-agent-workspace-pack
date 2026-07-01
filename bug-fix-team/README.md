# Bug-Fix Team

Use `bug-fix-team/` when a reported issue may be a bug. This team verifies before fixing.

It distinguishes:

- real bug,
- misunderstanding,
- expected behavior,
- feature request,
- flaky environment.

Vietnamese note: Team nay khong sua ngay. Dau tien phai xac minh bug, phan tich vung anh huong, de xuat fix nho nhat, roi cho xac nhan.

It reasons across multiple root-cause hypotheses and multiple fix directions
before recommending one minimal fix. For hard or ambiguous bugs it can offer a
parallel-subagent mode (`bug_hunter`), but only after a token-cost warning.

Vietnamese note: Bug kho thi co the chay nhieu bug_hunter song song de dieu tra
tung huong fix, nhung phai canh bao token truoc va cho xac nhan.

Files:

- `SKILL.md`
- `BUG_TRIAGE_PROMPT.md`
- `ROOT_CAUSE_HYPOTHESES_TEMPLATE.md`
- `FIX_DIRECTIONS_TEMPLATE.md`
- `ZONE_BRAIN_FIX_PROMPT.md`
- `IMPACT_ANALYSIS_TEMPLATE.md`
- `FIX_CONFIRMATION_TEMPLATE.md`


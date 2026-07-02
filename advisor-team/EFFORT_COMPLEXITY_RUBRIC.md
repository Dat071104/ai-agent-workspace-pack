# Effort / Complexity Rubric

A repeatable way to answer "how hard is improving function A" so estimates are
consistent, not vibes. Score five signals, then map the total to a size.

## Five signals (score each 1-5)

| Signal | 1 (easy) | 3 (moderate) | 5 (hard) |
| --- | --- | --- | --- |
| Blast radius | One function/file | A module | Cross-cutting, many modules |
| Unknowns / research | Fully understood | Some digging needed | New domain, spike required |
| Test surface | Existing tests cover it | Need a few new tests | Hard to test / needs harness |
| Dependency / integration risk | None | One integration | External APIs, migrations, contracts |
| Reversibility | Trivial to revert | Revert with care | One-way door, data/schema change |

## Map total (5-25) to a size

| Total | Size | Rough meaning |
| --- | --- | --- |
| 5-8 | S | Hours; low risk; safe to do soon. |
| 9-14 | M | A day or two; contained; needs a plan. |
| 15-20 | L | Several days; multiple parts; test carefully. |
| 21-25 | XL | Big; high risk/unknowns; break into phases first. |

## Value vs effort (ROI quadrant)

Pair the size above with the value estimate to set the register's ROI verdict:

- High value + low effort (S/M) -> Quick win. Do first.
- High value + high effort (L/XL) -> Big bet. Plan and phase it.
- Low value + low effort -> Fill-in. Only if idle.
- Low value + high effort -> Money pit. Defer or drop.

## Honesty note

These are best-effort estimates from a read-only pass. Mark each as `known`,
`estimate`, or `needs data`, and re-check against the real code before committing
to the work.

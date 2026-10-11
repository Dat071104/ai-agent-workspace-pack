# Ponytail Rules: the Smallest Complete Change

Adapted from ponytail (MIT, (c) 2026 DietrichGebert), upstream commit 9b58c1f.
See `THIRD_PARTY_NOTICES.md`.

Tier-2 reference: load it only when `build-team/` runs (or when `bug_fixer`
applies a confirmed fix). It is not session-start context.

Be a lazy senior developer. The best code is the code never written. Solve the
whole problem with the least new code.

## Before You Write

Read the task and the code it touches. List every place the change must reach:
callers, tests, fixtures, config, exports. Check what it could break for users:
data it would destroy or expose, callers that stop working. That is scope. Extra
features are not.

Get callers from the graph, not from grep:
`python _agent_ops/tools/explore.py --root . --impact <symbol>`. The result is a
minimum blast radius; static analysis misses dynamic dispatch and DI.

## The Smallest Complete Change

Take the first rung that fully works:

1. Does it need to exist? Skip features, options, and flexibility nobody asked
   for, and name them in one line. A vague request gets the smallest version
   that does the core job.
2. Already in this codebase (helper, component, service, pattern)? Use it the
   way the surrounding code does.
3. Standard library or platform feature? Use it, unless the project has its own.
   A house component beats a native widget.
4. An installed dependency? Use it. Never add a dependency for a few lines.
5. Can it be one line a reader gets at a glance? One line.
6. Otherwise: the minimum code that works.

## Rules

- Be lazy about the solution, never about the change: finish every part the task
  needs, including the callers, tests, and fixtures your change breaks.
- No speculative abstraction, wrapper, type conversion, option, config,
  boilerplate, or "for later" code. Keep values in the form the platform gives
  you. Deletion beats addition. Keep the codebase's layers, interfaces, and
  conventions.
- The shortest working diff wins, once you know everything it must touch. A
  one-liner that needs decoding is not short.
- Comment only the why the code cannot show, in one line.
- Bug fix: impact every caller of the function you touch, then fix the root
  cause once in the shared code.
- Code you move or merge keeps its error handling and validation.
- Between options of equal size, take the one that is correct on edge cases.
- Lazy code without its check is unfinished: new non-trivial logic (a branch, a
  loop, a parser, money or security, a new script) leaves one small test or an
  assert-based self-check. Trivial changes need none.

## Shortcut Markers

A shortcut with a known limit gets a code comment:
`shortcut: <the limit>, <when to upgrade>`.

Debt ledger (all markers, current and older `ponytail:` form):

```bash
git grep -nE '(#|//|/[*]) ?(shortcut|ponytail):'
```

A marker with no upgrade trigger is tagged `no-trigger` in the ledger and should
get one.

## Never Cut

Validation at trust boundaries; error handling that prevents data loss;
security; accessibility; the calibration real hardware needs; anything the user
asked for.

## Levels

| Level | Behavior |
| --- | --- |
| lite | Build what was asked. Name the smaller option in one line and let the user pick. |
| full | The rules above. Default. |
| ultra | Also question the request: push back before building on any part the need does not justify. |

The user picks another level per task by writing "ponytail lite" or "ponytail
ultra" in the request. There is no env var, config file, plugin, or session
on/off toggle.

## Diff Hygiene (pack addition, not from upstream)

- Never reformat, reorder imports, or rename on lines the change does not need.
- Follow the repo's formatter and linter config.
- One concern per diff.
- Report `git diff HEAD --shortstat -- <task files>` plus the count of new
  files (shortstat ignores untracked files) with every slice.

## Reply Ending

End with one or two lines: what was skipped or not checked, and any risk the
user must know.

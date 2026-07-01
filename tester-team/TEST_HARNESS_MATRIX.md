# Test Harness Matrix

Map for detecting a project's real test tooling and proposing scoped run
commands. Detect first, propose commands, and run only after the user approves.
Never install anything.

## How to Detect

| Signal file | What it tells you |
| --- | --- |
| `package.json` (`scripts`, `devDependencies`) | JS/TS test + build tooling |
| `playwright.config.*` | Playwright E2E is set up |
| `jest.config.*` / `vitest.config.*` | Jest / Vitest unit tests |
| `cypress.config.*` | Cypress E2E |
| `pyproject.toml` / `pytest.ini` / `tox.ini` | Python + pytest |
| `go.mod` | Go test |
| Lockfile (`package-lock.json`, `pnpm-lock.yaml`, `poetry.lock`, `uv.lock`) | Confirms installed deps without running install |

## Framework -> Command Map

| Framework | Detect | Scoped run (narrow first) | Full run | Token/risk |
| --- | --- | --- | --- | --- |
| Playwright | `playwright.config.*` + dep | `npx playwright test <spec> --project=<name>` | `npx playwright test` | Heavy (E2E) |
| Playwright (single test) | as above | `npx playwright test -g "<test title>"` | — | Medium-Heavy |
| Jest | `jest` in deps | `npx jest <path> -t "<name>"` | `npx jest` | Medium |
| Vitest | `vitest` in deps | `npx vitest run <path> -t "<name>"` | `npx vitest run` | Medium |
| Cypress | `cypress.config.*` | `npx cypress run --spec <spec>` | `npx cypress run` | Heavy (E2E) |
| pytest | `pytest` available | `pytest <path>::<test> -k "<expr>"` | `pytest` | Medium |
| Go | `go.mod` | `go test ./<pkg> -run <Name>` | `go test ./...` | Medium |
| Build check | build script present | `npm run build` / `tsc --noEmit` / `python -m build` | — | Medium |

## Rules

- Narrow before broad: one spec, one project, or one test id first.
- E2E suites (Playwright, Cypress) are Heavy. Warn about token/time before
  running the full suite.
- If the tool is missing, report it as a gap and suggest (do not run) how the
  user could add it. Do not install.
- Report the exact command run and the exact result. Do not claim a pass that
  did not happen.

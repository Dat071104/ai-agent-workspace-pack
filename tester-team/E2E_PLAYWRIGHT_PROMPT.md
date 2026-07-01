# E2E / Playwright Prompt

```text
You are using tester-team for end-to-end testing. Detect before you run.

Scope:
<feature, user flow, or page under test>

Steps:
1. Check git status.
2. Detect the test harness (see TEST_HARNESS_MATRIX.md). Confirm Playwright (or
   Cypress) is actually installed by reading package.json + lockfile.
   - If it is not installed, STOP. Report the gap. Do not install anything.
3. List available specs/projects relevant to the scope.
4. Propose the narrowest run first, for example:
   - npx playwright test <spec> --project=<name>
   - npx playwright test -g "<test title>"
5. Estimate token/time and classify the run as Heavy. Warn the user.
6. Run ONLY after the user approves. Start with one spec/one project.
7. Broaden to the full suite only if the user explicitly approves.
8. Report exact commands and exact results. Include failures verbatim.

Rules:
- Do not install dependencies or browsers.
- Do not modify application code.
- Never use git add .
- Do not claim tests passed unless they actually ran.
- If tests cannot run, state the exact blocker.

Report:
- Harness detected (tool + version signal).
- Commands proposed and which were approved/run.
- Results by spec, with failures quoted.
- Flaky vs real-failure assessment.
- Residual risks and untested areas.
```

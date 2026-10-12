"""What session_start concludes about a task, from the records alone.

The defect: any real text under "Next Concrete Step" or "Files Touched" printed
TASK IN PROGRESS -- true of a finished task too -- and a line such as "None.
Commit/push still needs explicit authorization" under Open Questions was
counted as a question the task is blocked on.

Fixtures live under the OS temp directory.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PACK_ROOT = HERE.parent
SCRIPTS = PACK_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(HERE))

import session_start  # noqa: E402
from session_state import continuity_block, open_questions, task_has_live_state, task_status  # noqa: E402
from test_ops_ownership import init_args, make_repo, run, write  # noqa: E402


LIVE_BODY = (
    "## Original Goal\n\nShip the billing export\n\n"
    "## Files Touched So Far\n\n| File | What changed | Reverted? |\n| --- | --- | --- |\n"
    "| `src/billing.py` | added export | no |\n\n"
    "## Next Concrete Step\n\nRun the export against staging\n\n"
)
BRIEF = "## Original Goal\n\nShip billing\n\n## Active Task\n\nBilling export\n"


def task(status: str | None, questions: str = "- None.\n", notes: str = "") -> str:
    head = "# Current Task\n\n## Task ID / Started\n\n`TASK-0007` / `2026-01-01`\n\n"
    if status is not None:
        head += f"## Status\n\n`{status}`\n\n"
    tail = f"## Open Questions Awaiting User\n\n{questions}\n"
    if notes:
        tail += f"## Standing Permissions / Notes\n\n{notes}\n"
    return head + LIVE_BODY + tail


class TaskStatusTests(unittest.TestCase):
    def test_declared_states_and_their_spellings(self) -> None:
        for text, expected in (
            ("complete", "complete"),
            ("**Complete** -- shipped", "complete"),
            ("Complete -- shipped, records written", "complete"),
            ("done", "complete"),
            ("in-progress", "in-progress"),
            ("In Progress", "in-progress"),
            ("blocked: waiting on the API key", "blocked"),
            ("idle", "idle"),
        ):
            self.assertEqual(expected, task_status(f"## Status\n\n`{text}`\n"), text)

    def test_an_absent_or_unfilled_status_is_unknown_never_in_progress(self) -> None:
        for body in (
            "# Task\n\n## Next Concrete Step\n\nsomething\n",
            "## Status\n\n`in-progress | blocked | complete | idle`\n",
            "## Status\n\n`<state>`\n",
            "## Status\n\nsomething else entirely\n",
            "",
        ):
            self.assertIsNone(task_status(body), body)

    def test_the_shipped_template_is_idle_with_no_live_state_and_no_questions(self) -> None:
        template = (PACK_ROOT / "core-context" / "CURRENT_TASK.template.md").read_text(encoding="utf-8")
        self.assertEqual("idle", task_status(template))
        self.assertFalse(task_has_live_state(template))
        self.assertEqual([], open_questions(template))
        self.assertIn("**FRESH.**", "\n".join(continuity_block("", template, "")))


class OpenQuestionTests(unittest.TestCase):
    def test_none_and_permission_notes_are_not_questions(self) -> None:
        for questions in (
            "None. Commit/push still needs explicit authorization per slice set.\n",
            "- None. Commit/push still needs explicit authorization per slice set.\n",
            "- none\n",
            "- N/A\n",
            "- `<question the task is blocked on -- do not guess an answer>`\n",
            "",
        ):
            self.assertEqual([], open_questions(task("in-progress", questions)), questions)

    def test_a_standing_permission_note_is_not_a_question(self) -> None:
        text = task("in-progress", "- None\n", notes="- Commit/push needs explicit authorization per slice set.\n")
        self.assertEqual([], open_questions(text))

    def test_a_real_question_is_counted_beside_a_none_line(self) -> None:
        text = task("blocked", "- None of the options fit\n- Which payment provider do we use?\n")
        found = open_questions(text)
        self.assertEqual(["- Which payment provider do we use?"], found)


class ContinuityTests(unittest.TestCase):
    def lines(self, task_text: str, brief: str = BRIEF, handoff: str = "") -> str:
        return "\n".join(continuity_block(brief, task_text, handoff))

    def test_a_completed_task_is_not_in_progress(self) -> None:
        out = self.lines(task("complete"))
        self.assertNotIn("TASK IN PROGRESS", out)
        self.assertIn("SESSION ESTABLISHED", out)
        self.assertIn("marks the last task `complete`", out)

    def test_an_in_progress_task_resumes(self) -> None:
        self.assertIn("**TASK IN PROGRESS.**", self.lines(task("in-progress")))

    def test_a_blocked_task_waits_on_its_questions(self) -> None:
        out = self.lines(task("blocked", "- Which payment provider do we use?\n"))
        self.assertIn("**TASK BLOCKED.**", out)
        self.assertIn("Waiting on 1 user question(s)", out)
        self.assertNotIn("TASK IN PROGRESS", out)

    def test_an_idle_task_with_leftover_text_is_not_live(self) -> None:
        out = self.lines(task("idle"), brief="")
        self.assertIn("**FRESH.**", out)

    def test_a_legacy_file_without_status_is_unverified_not_asserted(self) -> None:
        out = self.lines(task(None, "None. Commit/push still needs explicit authorization per slice set.\n"))
        self.assertIn("**TASK STATE UNVERIFIED.**", out)
        self.assertNotIn("TASK IN PROGRESS", out)
        self.assertNotIn("BLOCKED", out)

    def test_an_open_handoff_outranks_the_task(self) -> None:
        out = self.lines(task("in-progress"), handoff="## Status\n\nopen\n## Date\n\n2026-01-01\n")
        self.assertIn("**CONTINUATION.**", out)
        self.assertNotIn("TASK IN PROGRESS", out)

    def test_closure_check_can_still_import_its_helpers_from_session_start(self) -> None:
        self.assertTrue(callable(session_start.first_value))
        self.assertTrue(callable(session_start.read_text))


class SessionStartOutputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="session-state-")
        self.base = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def project(self, task_text: str | None, name: str = "proj") -> Path:
        root = self.base / name
        make_repo(root, name)
        initialized = run(SCRIPTS / "init_project_ops.py", *init_args(root), cwd=PACK_ROOT)
        assert initialized.returncode == 0, initialized.stderr
        write(root / "_agent_ops" / "SESSION_BRIEF.md", BRIEF)
        if task_text is not None:
            write(root / "_agent_ops" / "CURRENT_TASK.md", task_text)
        return root

    def session(self, root: Path) -> str:
        result = run(root / "_agent_ops" / "tools" / "session_start.py", "--root", ".", cwd=root)
        self.assertEqual(0, result.returncode, result.stderr)
        return result.stdout

    def test_completed_task_prints_history_not_instructions(self) -> None:
        out = self.session(self.project(task("complete")))
        self.assertIn("- Status: complete", out)
        self.assertIn("history, not instructions", out)
        self.assertNotIn("TASK IN PROGRESS", out)
        self.assertNotIn("BLOCKED on", out)
        self.assertNotIn("Next Concrete Step: Run the export", out)

    def test_a_real_question_blocks_and_is_listed(self) -> None:
        out = self.session(self.project(task("blocked", "- Which payment provider do we use?\n")))
        self.assertIn("**TASK BLOCKED.**", out)
        self.assertIn("BLOCKED on 1 unanswered question(s):", out)
        self.assertIn("Which payment provider do we use?", out)

    def test_none_and_standing_notes_do_not_block(self) -> None:
        legacy_line = "None. Commit/push still needs explicit authorization per slice set.\n"
        for number, text in enumerate(
            (
                task("in-progress", legacy_line),
                task("in-progress", "- None\n", notes="- Commit/push needs explicit authorization.\n"),
            )
        ):
            out = self.session(self.project(text, name=f"proj{number}"))
            self.assertIn("**TASK IN PROGRESS.**", out)
            self.assertNotIn("BLOCKED on", out)

    def test_a_task_file_without_status_is_reported_as_unverified(self) -> None:
        out = self.session(self.project(task(None, "None. Commit/push still needs explicit authorization.\n")))
        self.assertIn("**TASK STATE UNVERIFIED.**", out)
        self.assertIn("Status: not recorded", out)
        self.assertNotIn("TASK IN PROGRESS", out)
        self.assertNotIn("BLOCKED on", out)

    def test_foreign_memory_never_reads_as_a_task_in_progress(self) -> None:
        root = self.project(task("in-progress"))
        stamp = root / "_agent_ops" / "OPS_OWNER.json"
        data = json.loads(stamp.read_text(encoding="utf-8"))
        data["root_commits"] = ["d" * 40]
        stamp.write_text(json.dumps(data), encoding="utf-8")

        out = self.session(root)
        self.assertIn("FOREIGN PROJECT MEMORY", out)
        for forbidden in ("TASK IN PROGRESS", "SESSION ESTABLISHED", "Run the export against staging", "## Current Task"):
            self.assertNotIn(forbidden, out)


if __name__ == "__main__":
    unittest.main()

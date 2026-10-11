import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "closure_check.py"


class ClosureCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.com")
        self.write("app.py", "print('v1')\n")
        for name in ("IMPLEMENTATION_LOG", "REPO_MAP", "CURRENT_TASK", "DECISION_LOG"):
            self.write(f"_agent_ops/{name}.md", f"# {name}\n")
        self.write("_agent_ops/SESSION_BRIEF.md", "# Brief\n\n## Last Verified Commit\n\n`none`\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "base")
        self.base = self.git("rev-parse", "HEAD")
        self.write("_agent_ops/SESSION_BRIEF.md", f"# Brief\n\n## Last Verified Commit\n\n`{self.base}`\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "brief")
        self.head = self.git("rev-parse", "HEAD")

    def git(self, *args: str) -> str:
        result = subprocess.run(["git", *args], cwd=self.root, text=True, capture_output=True, check=True)
        return result.stdout.strip()

    def write(self, rel: str, text: str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def run_check(self, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--root", str(self.root), *extra],
            text=True,
            capture_output=True,
        )

    def row(self, out: str, name: str) -> str:
        return next(line for line in out.splitlines() if line.startswith(f"- {name}"))

    def test_code_changed_with_untouched_log_is_missing(self) -> None:
        self.write("app.py", "print('v2')\n")
        result = self.run_check("--since", self.head)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("MISSING", self.row(result.stdout, "IMPLEMENTATION_LOG.md"))
        self.assertIn("MISSING", self.row(result.stdout, "SESSION_BRIEF.md"))
        self.assertIn("decide:", self.row(result.stdout, "DECISION_LOG.md"))

    def test_touched_log_is_reported_updated(self) -> None:
        self.write("app.py", "print('v2')\n")
        self.write("_agent_ops/IMPLEMENTATION_LOG.md", "# IMPLEMENTATION_LOG\n\nentry\n")
        result = self.run_check("--since", self.head)
        self.assertIn("updated (detected)", self.row(result.stdout, "IMPLEMENTATION_LOG.md"))

    def test_default_since_comes_from_session_brief(self) -> None:
        result = self.run_check()
        self.assertIn(f"since {self.base[:12]}", result.stdout)
        self.assertIn("updated (detected)", self.row(result.stdout, "SESSION_BRIEF.md"))

    def test_strict_exit_codes(self) -> None:
        self.write("app.py", "print('v2')\n")
        self.assertEqual(2, self.run_check("--since", self.head, "--strict").returncode)
        self.write("_agent_ops/IMPLEMENTATION_LOG.md", "# IMPLEMENTATION_LOG\n\nentry\n")
        self.write("_agent_ops/SESSION_BRIEF.md", "# Brief\n\nchanged\n")
        self.assertEqual(0, self.run_check("--since", self.head, "--strict").returncode)

    def test_no_code_change_has_no_missing_rows(self) -> None:
        result = self.run_check("--since", self.head, "--strict")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("MISSING", result.stdout)

    def test_committed_code_with_unchanged_repo_map_is_missing(self) -> None:
        self.write("app.py", "print('v2')\n")
        self.git("add", "app.py")
        self.git("commit", "-q", "-m", "code")
        result = self.run_check("--since", self.head)
        self.assertIn("MISSING", self.row(result.stdout, "REPO_MAP.md"))

    def test_untracked_ops_files_are_not_reported_updated(self) -> None:
        # A fresh bootstrap: every ops file is untracked, so none proves this task's record.
        self.git("rm", "-r", "-q", "--cached", "_agent_ops")
        self.git("commit", "-q", "-m", "untrack ops")
        head = self.git("rev-parse", "HEAD")
        self.write("app.py", "print('v2')\n")
        result = self.run_check("--since", head, "--strict")
        self.assertEqual(2, result.returncode, result.stdout)
        log = self.row(result.stdout, "IMPLEMENTATION_LOG.md")
        self.assertNotIn("updated (detected)", log)
        self.assertIn("MISSING", log)
        self.assertIn("log untracked", log)
        self.assertIn("ops file is untracked/new", self.row(result.stdout, "DECISION_LOG.md"))

    def test_gitignored_ops_file_uses_mtime(self) -> None:
        self.write(".gitignore", "_agent_ops/CURRENT_TASK.md\n")
        self.git("rm", "-q", "--cached", "_agent_ops/CURRENT_TASK.md")
        self.git("add", ".gitignore")
        self.git("commit", "-q", "-m", "ignore")
        head = self.git("rev-parse", "HEAD")
        path = self.root / "_agent_ops" / "CURRENT_TASK.md"
        stamp = int(self.git("show", "-s", "--format=%ct", head)) + 100
        os.utime(path, (stamp, stamp))
        result = self.run_check("--since", head)
        row = self.row(result.stdout, "CURRENT_TASK.md")
        self.assertIn("unverified: modified after", row)
        self.assertIn("mtime only, gitignored", row)
        self.assertNotIn("updated", row)

    def test_mtime_only_session_brief_is_unverified_not_missing(self) -> None:
        self.write(".gitignore", "_agent_ops/SESSION_BRIEF.md\n")
        self.git("rm", "-q", "--cached", "_agent_ops/SESSION_BRIEF.md")
        self.git("add", ".gitignore")
        self.git("commit", "-q", "-m", "ignore")
        head = self.git("rev-parse", "HEAD")
        self.write("app.py", "print('v2')\n")
        stamp = int(self.git("show", "-s", "--format=%ct", head)) + 100
        os.utime(self.root / "_agent_ops" / "SESSION_BRIEF.md", (stamp, stamp))
        row = self.row(self.run_check("--since", head).stdout, "SESSION_BRIEF.md")
        self.assertIn("unverified", row)
        self.assertNotIn("MISSING", row)
        self.assertNotIn("updated", row)

    def test_code_changed_with_absent_log_is_missing_under_strict(self) -> None:
        self.git("rm", "-q", "_agent_ops/IMPLEMENTATION_LOG.md")
        self.git("commit", "-q", "-m", "drop log")
        head = self.git("rev-parse", "HEAD")
        self.write("app.py", "print('v2')\n")
        result = self.run_check("--since", head, "--strict")
        self.assertEqual(2, result.returncode, result.stdout)
        log = self.row(result.stdout, "IMPLEMENTATION_LOG.md")
        self.assertIn("MISSING", log)
        self.assertIn("absent", log)


if __name__ == "__main__":
    unittest.main()

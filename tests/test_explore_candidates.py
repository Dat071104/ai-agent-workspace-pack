import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
HEADING = "Candidate tests (text match, unverified"


class ExploreCandidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.write("lib.py", "def compute():\n    return 1\n\n\ndef lonely():\n    return 2\n")

    def write(self, rel: str, text: str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def impact(self, symbol: str) -> str:
        index = self.root / "idx.json"
        build = subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / "build_code_index.py"), "--root", str(self.root), "--output", str(index)],
            text=True, capture_output=True,
        )
        self.assertEqual(0, build.returncode, build.stderr)
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / "explore.py"), "--root", str(self.root), "--index", str(index), "--impact", symbol],
            text=True, capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return result.stdout

    def test_subprocess_test_is_listed_as_candidate(self) -> None:
        self.write("tests/test_cli.py", "import subprocess\nsubprocess.run(['python', 'lib.py'])\n")
        out = self.impact("compute")
        self.assertIn("No test file in the affected set", out)
        section = out.split(HEADING, 1)[1]
        self.assertIn("- tests/test_cli.py", section)
        self.assertIn("not call edges", out)
        self.assertNotIn("tests/test_cli.py", out.split(HEADING, 1)[0])  # never mixed into the graph part

    def test_symbol_name_match_is_a_candidate(self) -> None:
        self.write("tests/test_names.py", "NAMES = ['compute']\n\n\ndef test_names():\n    pass\n")
        self.assertIn("- tests/test_names.py", self.impact("compute").split(HEADING, 1)[1])

    def test_graph_found_test_has_no_candidate_section(self) -> None:
        self.write("tests/test_lib.py", "from lib import compute\n\n\ndef test_it():\n    assert compute() == 1\n")
        out = self.impact("compute")
        self.assertIn("- tests/test_lib.py", out)
        self.assertNotIn(HEADING, out)

    def test_unmentioned_symbol_keeps_current_message(self) -> None:
        self.write("tests/test_other.py", "def test_nothing():\n    pass\n")
        out = self.impact("lonely")
        self.assertIn("No test file in the affected set", out)
        self.assertNotIn(HEADING, out)


if __name__ == "__main__":
    unittest.main()

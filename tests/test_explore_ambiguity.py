import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
AFFECTED = "Transitively affected"


def sym(file: str, qualname: str, **extra) -> dict:
    return {"file": file, "line": 1, "kind": "method", "qualname": qualname, **extra}


def call(frm: str, to: str) -> dict:
    return {"from": frm, "to": to, "kind": "CALLS", "conf": "exact"}


# `save` is defined three times; `Cache.save` exists in two files; `Store.fetch`
# is unique and called by `app.py::run`.
SYMBOLS = {
    "pkg/a.py::Cache.save": sym("pkg/a.py", "Cache.save"),
    "pkg/b.py::Cache.save": sym("pkg/b.py", "Cache.save"),
    "pkg/c.py::Repo.save": sym("pkg/c.py", "Repo.save"),
    "pkg/c.py::Store.fetch": sym("pkg/c.py", "Store.fetch"),
    "pkg/c.py::Store.push": sym("pkg/c.py", "Store.push", overloads=3),
    "app.py::run": sym("app.py", "run", kind="function"),
}
EDGES = [
    call("app.py::run", "pkg/a.py::Cache.save"),
    call("app.py::run", "pkg/c.py::Store.fetch"),
    call("app.py::run", "pkg/c.py::Store.push"),
]


class ExploreAmbiguityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        index = {
            "symbols": SYMBOLS,
            "edges": EDGES,
            "files": sorted({s["file"] for s in SYMBOLS.values()}),
            "commit": "test",
            "generated": "now",
        }
        (self.root / "idx.json").write_text(json.dumps(index), encoding="utf-8")

    def impact(self, query: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / "explore.py"), "--root", str(self.root),
             "--index", str(self.root / "idx.json"), "--impact", query],
            text=True, capture_output=True,
        )

    def test_ambiguous_short_name_is_refused(self) -> None:
        result = self.impact("save")
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn("ambiguous", result.stdout)
        for ident in ("pkg/a.py::Cache.save", "pkg/b.py::Cache.save", "pkg/c.py::Repo.save"):
            self.assertIn(ident, result.stdout)
        self.assertNotIn(AFFECTED, result.stdout)
        self.assertNotIn("showing the first", result.stdout)

    def test_unknown_symbol_is_an_error_not_no_impact(self) -> None:
        result = self.impact("does_not_exist")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("No symbol matches", result.stdout)
        self.assertNotIn(AFFECTED, result.stdout)

    def test_unique_qualname_runs_impact(self) -> None:
        result = self.impact("Repo.save")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("# Impact: Repo.save", result.stdout)

    def test_unique_full_id_runs_impact(self) -> None:
        result = self.impact("pkg/a.py::Cache.save")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(AFFECTED, result.stdout)
        self.assertIn("run", result.stdout)

    def test_shared_qualname_refused_then_full_id_works(self) -> None:
        refused = self.impact("Cache.save")
        self.assertEqual(2, refused.returncode, refused.stdout + refused.stderr)
        self.assertIn("pkg/a.py::Cache.save", refused.stdout)
        self.assertIn("pkg/b.py::Cache.save", refused.stdout)
        self.assertNotIn(AFFECTED, refused.stdout)
        self.assertEqual(0, self.impact("pkg/b.py::Cache.save").returncode)

    def test_single_substring_match_proceeds(self) -> None:
        result = self.impact("etch")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("# Impact: Store.fetch", result.stdout)

    def test_overload_label_and_note(self) -> None:
        result = self.impact("Store.push")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("[3 overloads merged]", self.symbol_output("Store.push"))
        self.assertIn("all 3 overloads", result.stdout)

    def test_plain_symbol_has_no_overload_text(self) -> None:
        result = self.impact("Store.fetch")
        self.assertNotIn("overloads", result.stdout)

    def symbol_output(self, query: str) -> str:
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / "explore.py"), "--root", str(self.root),
             "--index", str(self.root / "idx.json"), "--symbol", query],
            text=True, capture_output=True,
        ).stdout


if __name__ == "__main__":
    unittest.main()

"""Java/C# overloads merge into one `Type.method` node and are marked, never split.

Fixtures live under the OS temporary directory, never inside this repository.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from extract_java_csharp import extract_csharp, extract_java  # noqa: E402

JAVA_REPO = """\
public class Repo {
    public Repo() { }
    public Repo(int size) { }

    public void save(int id) { }
    public void save(String name) { }
    public void only() { }
}
"""

CS_REPO = """\
public class Repo
{
    public void Save(int id) { }
    public void Save(string name) { }
    public void Save(Order order) => Touch();
    public void Touch() { }
}
"""

JAVA_IFACE = """\
public interface Store {
    void put(int id);
    default void put(String name) { }
    void get();
}
"""

JAVA_CALLER = """\
public class Caller {
    private final Repo repo = new Repo();
    public void run() { repo.save(1); }
}
"""


class OverloadMarkingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="java-csharp-overloads-")
        self.root = Path(self.temp_dir.name) / "project"
        self.root.mkdir()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write(self, relative: str, content: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def build_index(self) -> dict:
        index_path = self.root / "code_index.json"
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        done = subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / "build_code_index.py"), "--root", str(self.root),
             "--output", str(index_path), "--quiet"],
            cwd=str(self.root), env=env, text=True, capture_output=True, check=False,
        )
        self.assertEqual(0, done.returncode, done.stderr)
        return json.loads(index_path.read_text(encoding="utf-8"))

    def test_java_overloads_are_one_marked_symbol(self) -> None:
        symbols = extract_java(self.write("Repo.java", JAVA_REPO), "Repo.java")["symbols"]
        self.assertEqual(2, symbols["Repo.save"]["overloads"])
        self.assertEqual(5, symbols["Repo.save"]["line"])  # first declaration wins

    def test_csharp_three_overloads_including_expression_body(self) -> None:
        symbols = extract_csharp(self.write("Repo.cs", CS_REPO), "Repo.cs")["symbols"]
        self.assertEqual(3, symbols["Repo.Save"]["overloads"])
        self.assertEqual(3, symbols["Repo.Save"]["line"])

    def test_constructors_are_marked_on_init(self) -> None:
        symbols = extract_java(self.write("Repo.java", JAVA_REPO), "Repo.java")["symbols"]
        self.assertEqual(2, symbols["Repo.<init>"]["overloads"])

    def test_single_method_has_no_overloads_key(self) -> None:
        symbols = extract_java(self.write("Repo.java", JAVA_REPO), "Repo.java")["symbols"]
        self.assertNotIn("overloads", symbols["Repo.only"])
        cs = extract_csharp(self.write("Repo.cs", CS_REPO), "Repo.cs")["symbols"]
        self.assertNotIn("overloads", cs["Repo.Touch"])
        self.assertNotIn("overloads", cs["Repo"])  # types are never marked

    def test_bodiless_and_default_interface_members_count_once_each(self) -> None:
        symbols = extract_java(self.write("Store.java", JAVA_IFACE), "Store.java")["symbols"]
        self.assertEqual(2, symbols["Store.put"]["overloads"])
        self.assertNotIn("overloads", symbols["Store.get"])

    def test_overload_field_survives_into_the_index(self) -> None:
        self.write("Repo.java", JAVA_REPO)
        self.write("Repo.cs", CS_REPO.replace("class Repo", "class CsRepo"))
        symbols = self.build_index()["symbols"]
        self.assertEqual(2, symbols["Repo.java::Repo.save"]["overloads"])
        self.assertEqual(2, symbols["Repo.java::Repo.<init>"]["overloads"])
        self.assertEqual(3, symbols["Repo.cs::CsRepo.Save"]["overloads"])
        self.assertNotIn("overloads", symbols["Repo.java::Repo.only"])

    def test_calls_to_an_overloaded_method_still_resolve_weakly(self) -> None:
        self.write("Repo.java", JAVA_REPO)
        self.write("Caller.java", JAVA_CALLER)
        index = self.build_index()
        calls = [
            e for e in index["edges"]
            if e["kind"] == "CALLS" and e["from"] == "Caller.java::Caller.run"
            and e["to"] == "Repo.java::Repo.save"
        ]
        self.assertEqual(["weak"], [e["conf"] for e in calls])


if __name__ == "__main__":
    unittest.main()

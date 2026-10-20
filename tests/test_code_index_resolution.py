"""CALLS resolution in the lite codegraph: what may be `exact`, what is dropped.

Fixtures live under the OS temporary directory, never inside this repository.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_code_index import build_index  # noqa: E402


class CodeIndexResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def write(self, rel: str, text: str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def calls(self, source: str) -> list[tuple[str, str]]:
        """(target, conf) for CALLS edges leaving `source` (a symbol id)."""
        index = build_index(self.root)
        return sorted(
            (e["to"], e["conf"])
            for e in index["edges"]
            if e["kind"] == "CALLS" and e["from"] == source
        )

    # -- F1: Python bare-name resolution -------------------------------------

    def test_external_import_is_not_shadowed_by_same_named_method(self) -> None:
        self.write(
            "app.py",
            "from external_package import save\n\n\n"
            "class Cache:\n    def save(self):\n        pass\n\n\n"
            "def run():\n    save()\n",
        )
        self.assertEqual([], self.calls("app.py::run"))

    def test_bare_call_never_targets_a_method(self) -> None:
        self.write(
            "app.py",
            "class Cache:\n    def save(self):\n        pass\n\n\n"
            "def run():\n    save()\n",
        )
        self.assertEqual([], self.calls("app.py::run"))

    def test_aliased_project_import_resolves_to_original_name(self) -> None:
        self.write("store.py", "def save():\n    pass\n\n\ndef persist():\n    pass\n")
        self.write(
            "app.py",
            "from store import save as persist\n\n\ndef run():\n    persist()\n",
        )
        edges = self.calls("app.py::run")
        self.assertEqual(["store.py::save"], [t for t, _ in edges])
        self.assertNotEqual("exact", edges[0][1])  # absolute import: heuristic

    def test_relative_aliased_import_is_exact(self) -> None:
        self.write("pkg/__init__.py", "")
        self.write("pkg/store.py", "def save():\n    pass\n")
        self.write(
            "pkg/app.py",
            "from .store import save as persist\n\n\ndef run():\n    persist()\n",
        )
        self.assertEqual([("pkg/store.py::save", "exact")], self.calls("pkg/app.py::run"))

    def test_two_same_file_defs_are_ambiguous_not_exact(self) -> None:
        # Same-qualname defs collapse in the symbol table; nested owners keep both.
        self.write(
            "dup.py",
            "def a():\n    def helper():\n        pass\n\n\n"
            "def b():\n    def helper():\n        pass\n\n\n"
            "def run():\n    helper()\n",
        )
        edges = self.calls("dup.py::run")
        self.assertEqual(2, len(edges))
        self.assertEqual({"ambiguous"}, {conf for _, conf in edges})

    def test_unique_same_file_function_is_exact(self) -> None:
        self.write("app.py", "def helper():\n    pass\n\n\ndef run():\n    helper()\n")
        self.assertEqual([("app.py::helper", "exact")], self.calls("app.py::run"))

    def test_nested_function_call_still_resolves(self) -> None:
        self.write(
            "app.py",
            "def run():\n    def inner():\n        pass\n    inner()\n",
        )
        self.assertEqual([("app.py::run.inner", "exact")], self.calls("app.py::run"))

    def test_attribute_call_is_never_exact(self) -> None:
        self.write(
            "app.py",
            "class Cache:\n    def save(self):\n        pass\n\n\n"
            "def run(cache):\n    cache.save()\n",
        )
        self.assertEqual([("app.py::Cache.save", "heuristic")], self.calls("app.py::run"))

    # -- F5: CALL_NOISE applies to attribute calls only ----------------------

    def test_bare_noise_named_calls_reach_project_defs(self) -> None:
        self.write(
            "app.py",
            "def update():\n    pass\n\n\ndef get():\n    pass\n\n\ndef add():\n    pass\n\n\n"
            "def run():\n    update()\n    get()\n    add()\n",
        )
        targets = {t for t, _ in self.calls("app.py::run")}
        self.assertEqual({"app.py::update", "app.py::get", "app.py::add"}, targets)

    def test_noise_named_attribute_call_is_still_filtered(self) -> None:
        self.write(
            "app.py",
            "class Store:\n    def get(self):\n        pass\n\n\n"
            "def run(d):\n    d.get('x')\n",
        )
        self.assertEqual([], self.calls("app.py::run"))

    def test_builtin_bare_call_creates_no_edge(self) -> None:
        self.write("app.py", "def run(x):\n    print(len(x))\n")
        self.assertEqual([], self.calls("app.py::run"))

    def test_builtin_name_does_not_match_a_definition_elsewhere(self) -> None:
        self.write("cli.py", "def list():\n    pass\n")
        self.write("app.py", "def run(x):\n    return list(x)\n")
        self.assertEqual([], self.calls("app.py::run"))

    def test_builtin_name_defined_in_the_same_file_resolves(self) -> None:
        self.write("cli.py", "def list():\n    pass\n\n\ndef run():\n    list()\n")
        self.assertEqual([("cli.py::list", "exact")], self.calls("cli.py::run"))

    def test_sys_path_import_keeps_a_heuristic_edge(self) -> None:
        # `sys.path.insert(0, "scripts")` then `from tool import work`: the
        # resolver cannot place `tool`, but scripts/tool.py is the only file
        # named after it, so the edge is a lead rather than dropped as external.
        self.write("scripts/tool.py", "def work():\n    pass\n")
        self.write("tests/test_tool.py", "from tool import work\n\n\ndef test_it():\n    work()\n")
        self.assertEqual(
            [("scripts/tool.py::work", "heuristic")], self.calls("tests/test_tool.py::test_it")
        )

    def test_package_reexport_keeps_a_heuristic_edge(self) -> None:
        # `pkg/__init__.py` re-exports `helper`: the binding names the package,
        # not the defining file, so the edge survives as a lead, never exact.
        self.write("pkg/__init__.py", "from .helpers import helper\n")
        self.write("pkg/helpers.py", "def helper():\n    pass\n")
        self.write("app.py", "from pkg import helper\n\n\ndef run():\n    helper()\n")
        self.assertEqual([("pkg/helpers.py::helper", "heuristic")], self.calls("app.py::run"))

    # -- JS ------------------------------------------------------------------

    def test_js_bare_noise_call_resolved_and_attribute_call_filtered(self) -> None:
        self.write(
            "app.js",
            "function update() {\n  return 1;\n}\n\n"
            "function push() {\n  return 2;\n}\n\n"
            "const run = () => {\n  update();\n  arr.push(1);\n};\n",
        )
        targets = {t for t, _ in self.calls("app.js")}
        self.assertIn("app.js::update", targets)
        self.assertNotIn("app.js::push", targets)

    def test_js_symbol_lines_are_unchanged(self) -> None:
        # No blank line before a definition: the regexes' leading `\s*` would
        # otherwise swallow it, a separate pre-existing quirk this test avoids.
        self.write(
            "app.js",
            "// header\nfunction first() {\n  return 1;\n}\n"
            "class Box {\n  open() {\n    return 2;\n  }\n}\n"
            "const third = () => 3;\n"
            "app.get('/x', handler);\n",
        )
        symbols = build_index(self.root)["symbols"]
        self.assertEqual(2, symbols["app.js::first"]["line"])
        self.assertEqual(5, symbols["app.js::Box"]["line"])
        self.assertEqual(6, symbols["app.js::open"]["line"])
        self.assertEqual(10, symbols["app.js::third"]["line"])
        self.assertEqual(11, symbols["app.js::<route GET /x>"]["line"])


if __name__ == "__main__":
    unittest.main()

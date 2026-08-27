"""Golden regression checks for the portable workspace-tool runtime.

Every fixture is created under the OS temporary directory, never inside this
repository. That keeps the pack's own code graph and hygiene result independent
of its tests.
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
PACK_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PACK_ROOT / "scripts"


class WorkspaceToolsGoldenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="workspace-tools-golden-")
        self.root = Path(self.temp_dir.name) / "project"
        self.root.mkdir()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write(self, relative: str, content: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def run_tool(self, script: Path, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [sys.executable, "-B", str(script), *args],
            cwd=str(cwd or self.root),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def init_project(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return self.run_tool(SCRIPTS / "init_project_ops.py", "--target", str(self.root), *extra, cwd=PACK_ROOT)

    def make_source_fixture(self) -> None:
        self.write("src/app/models/user.py", "class User:\n    pass\n")
        self.write(
            "src/app/services/relative_auth.py",
            "from ..models.user import User\n\n\ndef login_relative() -> User:\n    return User()\n",
        )
        self.write(
            "src/app/services/absolute_auth.py",
            "from app.models.user import User\n\n\ndef login_absolute() -> User:\n    return User()\n",
        )
        self.write(
            "tests/test_auth.py",
            "from app.services.relative_auth import login_relative\n\n\ndef test_login() -> None:\n    assert login_relative().__class__.__name__ == 'User'\n",
        )
        self.write("src/components/Button.tsx", "export function Button() { return 'button'; }\n")
        self.write(
            "src/ui/Page.tsx",
            "import Button from 'components/Button';\nimport React from 'react';\n\nexport function renderPage() { return Button(); }\n",
        )
        self.write("src/oversized.py", "# fixture line\n" * 401)

    def assert_import(self, index: dict, source: str, target: str, confidence: str) -> None:
        matches = [
            edge
            for edge in index["edges"]
            if edge["kind"] == "IMPORTS"
            and edge["from"].startswith(source)
            and edge["to"].startswith(target)
            and edge["conf"] == confidence
        ]
        self.assertTrue(matches, f"missing {confidence} import {source} -> {target}")

    def test_init_builds_graph_in_order_and_is_idempotent(self) -> None:
        self.make_source_fixture()
        first = self.init_project()
        self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual(10, len(list((self.root / "_agent_ops" / "tools").glob("*.py"))))
        self.assertTrue((self.root / "AGENTS.md").is_file())
        self.assertIn("## Pack Mode: Runtime-only", (self.root / "AGENTS.md").read_text(encoding="utf-8"))

        repo_map = (self.root / "_agent_ops" / "REPO_MAP.md").read_text(encoding="utf-8")
        self.assertIn("## Symbol Graph", repo_map)
        self.assertNotIn("Not built", repo_map)
        self.assertIn("## Oversized Files", repo_map)
        self.assertIn("src/oversized.py", repo_map)

        index = json.loads((self.root / "_agent_ops" / "code_index.json").read_text(encoding="utf-8"))
        self.assert_import(index, "src/app/services/relative_auth.py", "src/app/models/user.py", "exact")
        self.assert_import(index, "src/app/services/absolute_auth.py", "src/app/models/user.py", "heuristic")
        self.assert_import(index, "src/ui/Page.tsx", "src/components/Button.tsx", "heuristic")
        self.assertFalse(any("react" in edge["to"].lower() for edge in index["edges"]))

        impact = self.run_tool(self.root / "_agent_ops" / "tools" / "explore.py", "--impact", "login_relative")
        self.assertEqual(0, impact.returncode, impact.stderr)
        self.assertIn("tests/test_auth.py", impact.stdout)
        self.assertFalse(list(self.root.rglob("__pycache__")))

        second = self.init_project()
        self.assertEqual(0, second.returncode, second.stderr)
        self.assertEqual(10, second.stdout.count("UPDATE: "))
        self.assertIn("SKIP existing: " + str(self.root / "AGENTS.md"), second.stdout)

    def test_init_propagates_prompt_independent_closure_gate(self) -> None:
        self.assertEqual(0, self.init_project().returncode)

        agents = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        protocol = (self.root / "_agent_ops" / "SESSION_PROTOCOL.md").read_text(encoding="utf-8")
        rules = (self.root / "_agent_ops" / "OPERATING_RULES.md").read_text(encoding="utf-8")
        index = (self.root / "_agent_ops" / "INDEX.md").read_text(encoding="utf-8")
        task = (self.root / "_agent_ops" / "CURRENT_TASK.md").read_text(encoding="utf-8")
        log = (self.root / "_agent_ops" / "IMPLEMENTATION_LOG.md").read_text(encoding="utf-8")
        card = (self.root / "_agent_ops" / "PROJECT_CONTEXT_CARD.md").read_text(encoding="utf-8")

        self.assertIn("A task prompt defines deliverable scope, not durable recordkeeping.", agents)
        self.assertIn("## Prompt-Independence Invariant", protocol)
        self.assertIn("A task prompt controls the requested work, not durable recordkeeping.", rules)
        self.assertIn("A prompt omission never waives a triggered record.", index)
        self.assertIn("Prompt omission is never a reason to skip a triggered", task)
        self.assertIn("A prompt need not name this file", log)
        self.assertIn("even when the task prompt only names task-level files", card)

        session = self.run_tool(self.root / "_agent_ops" / "tools" / "session_start.py", "--root", ".")
        self.assertEqual(0, session.returncode, session.stderr)
        self.assertIn("## Durable Recordkeeping Gate", session.stdout)
        self.assertIn("not the task prompt's file list", session.stdout)
        self.assertIn("repo-map refresh helper", session.stdout)

    def test_hygiene_distinguishes_nested_models_from_root_artifacts(self) -> None:
        self.make_source_fixture()
        self.assertEqual(0, self.init_project().returncode)
        hygiene = self.run_tool(self.root / "_agent_ops" / "tools" / "check_repo_hygiene.py", "--root", ".")
        self.assertEqual(0, hygiene.returncode, hygiene.stdout + hygiene.stderr)

        self.write("data/generated.json", "{}\n")
        hygiene = self.run_tool(self.root / "_agent_ops" / "tools" / "check_repo_hygiene.py", "--root", ".")
        self.assertEqual(1, hygiene.returncode)
        self.assertIn("data/ matches directory data/", hygiene.stdout)

    def test_working_tree_code_makes_index_stale(self) -> None:
        self.make_source_fixture()
        self.assertEqual(0, self.init_project().returncode)
        for args in (
            ("init", "-q"),
            ("config", "user.email", "golden@example.invalid"),
            ("config", "user.name", "Golden Test"),
        ):
            self.assertEqual(0, subprocess.run(["git", *args], cwd=self.root, check=False).returncode)
        tracked = [str(path.relative_to(self.root)) for path in self.root.glob("src/**/*") if path.is_file()]
        tracked += [str(path.relative_to(self.root)) for path in self.root.glob("tests/**/*") if path.is_file()]
        self.assertEqual(0, subprocess.run(["git", "add", "--", *tracked], cwd=self.root, check=False).returncode)
        baseline = subprocess.run(["git", "commit", "-qm", "baseline"], cwd=self.root, text=True, capture_output=True)
        self.assertEqual(0, baseline.returncode, baseline.stdout + baseline.stderr)

        self.assertEqual(0, self.run_tool(self.root / "_agent_ops" / "tools" / "build_code_index.py", "--root", ".", "--quiet").returncode)
        self.assertEqual(
            0,
            self.run_tool(
                self.root / "_agent_ops" / "tools" / "generate_repo_map.py",
                "--root",
                ".",
                "--output",
                "_agent_ops/REPO_MAP.md",
                "--force",
            ).returncode,
        )
        self.write(
            "src/app/services/relative_auth.py",
            "from ..models.user import User\n\n\ndef login_relative() -> User:\n    # uncommitted\n    return User()\n",
        )
        session = self.run_tool(self.root / "_agent_ops" / "tools" / "session_start.py", "--root", ".")
        self.assertEqual(0, session.returncode, session.stderr)
        self.assertGreaterEqual(
            session.stdout.count("STALE: 1 code file(s) changed outside the Git index."),
            2,
        )
        self.assertNotIn("9 code file(s) changed outside the Git index.", session.stdout)

    def test_pre_commit_hook_refreshes_repo_map_for_staged_code(self) -> None:
        self.make_source_fixture()
        for args in (
            ("init", "-q"),
            ("config", "user.email", "golden@example.invalid"),
            ("config", "user.name", "Golden Test"),
        ):
            self.assertEqual(0, subprocess.run(["git", *args], cwd=self.root, check=False).returncode)

        initialized = self.init_project("--install-repo-map-hook")
        self.assertEqual(0, initialized.returncode, initialized.stderr)
        hook = self.root / ".git" / "hooks" / "pre-commit"
        self.assertIn("AI_AGENT_OPS_REPO_MAP_PRE_COMMIT", hook.read_text(encoding="utf-8"))

        tracked = [str(path.relative_to(self.root)) for path in self.root.glob("src/**/*") if path.is_file()]
        tracked += [str(path.relative_to(self.root)) for path in self.root.glob("tests/**/*") if path.is_file()]
        self.assertEqual(0, subprocess.run(["git", "add", "--", *tracked], cwd=self.root, check=False).returncode)
        baseline = subprocess.run(["git", "commit", "-qm", "baseline"], cwd=self.root, text=True, capture_output=True)
        self.assertEqual(0, baseline.returncode, baseline.stdout + baseline.stderr)
        committed = subprocess.run(
            ["git", "show", "--format=", "--name-only", "HEAD"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertIn("_agent_ops/REPO_MAP.md", committed.stdout.splitlines())

        self.write(
            "src/app/services/relative_auth.py",
            "from ..models.user import User\n\n\ndef login_relative() -> User:\n    # staged only\n    return User()\n",
        )
        self.assertEqual(
            0,
            subprocess.run(
                ["git", "add", "--", "src/app/services/relative_auth.py"],
                cwd=self.root,
                check=False,
            ).returncode,
        )
        commit = subprocess.run(["git", "commit", "-qm", "source change"], cwd=self.root, text=True, capture_output=True)
        self.assertEqual(0, commit.returncode, commit.stdout + commit.stderr)
        committed = subprocess.run(
            ["git", "show", "--format=", "--name-only", "HEAD"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertIn("src/app/services/relative_auth.py", committed.stdout.splitlines())
        self.assertIn("_agent_ops/REPO_MAP.md", committed.stdout.splitlines())

        session = self.run_tool(self.root / "_agent_ops" / "tools" / "session_start.py", "--root", ".")
        self.assertEqual(0, session.returncode, session.stderr)
        self.assertIn("Current with indexed source state", session.stdout)

    def test_pre_commit_hook_blocks_code_outside_the_index(self) -> None:
        self.make_source_fixture()
        for args in (
            ("init", "-q"),
            ("config", "user.email", "golden@example.invalid"),
            ("config", "user.name", "Golden Test"),
        ):
            self.assertEqual(0, subprocess.run(["git", *args], cwd=self.root, check=False).returncode)
        self.assertEqual(0, self.init_project("--install-repo-map-hook").returncode)

        tracked = [str(path.relative_to(self.root)) for path in self.root.glob("src/**/*") if path.is_file()]
        tracked += [str(path.relative_to(self.root)) for path in self.root.glob("tests/**/*") if path.is_file()]
        self.assertEqual(0, subprocess.run(["git", "add", "--", *tracked], cwd=self.root, check=False).returncode)
        baseline = subprocess.run(["git", "commit", "-qm", "baseline"], cwd=self.root, text=True, capture_output=True)
        self.assertEqual(0, baseline.returncode, baseline.stdout + baseline.stderr)

        self.write(
            "src/app/services/relative_auth.py",
            "from ..models.user import User\n\n\ndef login_relative() -> User:\n    # staged only\n    return User()\n",
        )
        self.assertEqual(
            0,
            subprocess.run(
                ["git", "add", "--", "src/app/services/relative_auth.py"],
                cwd=self.root,
                check=False,
            ).returncode,
        )
        self.write(
            "src/app/services/absolute_auth.py",
            "from app.models.user import User\n\n\ndef login_absolute() -> User:\n    # left unstaged\n    return User()\n",
        )
        blocked = subprocess.run(["git", "commit", "-qm", "unsafe source state"], cwd=self.root, text=True, capture_output=True)
        self.assertNotEqual(0, blocked.returncode)
        self.assertIn("outside the Git index", blocked.stdout + blocked.stderr)

    def test_repo_map_hook_preserves_an_existing_pre_commit_hook(self) -> None:
        self.assertEqual(0, subprocess.run(["git", "init", "-q"], cwd=self.root, check=False).returncode)
        existing_hook = self.write(".git/hooks/pre-commit", "#!/bin/sh\necho user hook\n")

        result = self.init_project("--install-repo-map-hook")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("WARN existing pre-commit hook preserved", result.stdout)
        self.assertEqual("#!/bin/sh\necho user hook\n", existing_hook.read_text(encoding="utf-8"))

    def test_embedded_pack_skips_only_detected_pack_directories(self) -> None:
        embedded = self.root / "embedded"
        ordinary = self.root / "ordinary"
        for directory in (embedded / "core-context", embedded / "scripts", embedded / "src", ordinary / "scripts"):
            directory.mkdir(parents=True, exist_ok=True)
        (embedded / "TEAM_ROUTER.md").write_text("# marker\n", encoding="utf-8")
        (embedded / "scripts" / "init_project_ops.py").write_text("def pack_tool(): pass\n", encoding="utf-8")
        (embedded / "src" / "app.py").write_text("def project_code(): pass\n", encoding="utf-8")
        (ordinary / "scripts" / "app.py").write_text("def user_script(): pass\n", encoding="utf-8")

        embedded_scan = self.run_tool(SCRIPTS / "scan_deps.py", "--root", str(embedded), "--output", "json", cwd=PACK_ROOT)
        ordinary_scan = self.run_tool(SCRIPTS / "scan_deps.py", "--root", str(ordinary), "--output", "json", cwd=PACK_ROOT)
        self.assertEqual(["src/app.py"], sorted(json.loads(embedded_scan.stdout)["graph"]))
        self.assertEqual(["scripts/app.py"], sorted(json.loads(ordinary_scan.stdout)["graph"]))

        embedded_init = self.run_tool(SCRIPTS / "init_project_ops.py", "--target", str(embedded), cwd=PACK_ROOT)
        self.assertEqual(0, embedded_init.returncode, embedded_init.stderr)
        agents = (embedded / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("## Pack Mode: Embedded", agents)
        self.assertIn("START_HERE.md", agents)
        self.assertIn("AI_AGENT_WORKSPACE_PACK:BEGIN v1", agents)
        embedded_check = self.run_tool(
            SCRIPTS / "init_project_ops.py",
            "--target",
            str(embedded),
            "--check-agents-bridge",
            cwd=PACK_ROOT,
        )
        self.assertEqual(0, embedded_check.returncode, embedded_check.stderr)
        self.assertIn("AGENTS BRIDGE: INSTALLED", embedded_check.stdout)

    def test_existing_agents_bridge_requires_explicit_install_and_is_idempotent(self) -> None:
        self.write("TEAM_ROUTER.md", "# marker\n")
        self.write("AGENTS.md", "# Existing project rules\nKeep this marker.\n")

        default = self.init_project()
        self.assertEqual(0, default.returncode, default.stderr)
        self.assertIn("WARN embedded pack detected but AGENTS bridge is missing", default.stdout)
        self.assertEqual(
            "# Existing project rules\nKeep this marker.\n",
            (self.root / "AGENTS.md").read_text(encoding="utf-8"),
        )

        installed = self.init_project("--install-agents-bridge")
        self.assertEqual(0, installed.returncode, installed.stderr)
        self.assertIn("AGENTS BRIDGE: INSTALLED", installed.stdout)
        agents = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Keep this marker.", agents)
        self.assertEqual(1, agents.count("AI_AGENT_WORKSPACE_PACK:BEGIN v1"))

        second = self.init_project("--install-agents-bridge")
        self.assertEqual(0, second.returncode, second.stderr)
        self.assertEqual(agents, (self.root / "AGENTS.md").read_text(encoding="utf-8"))

        checked = self.init_project("--check-agents-bridge")
        self.assertEqual(0, checked.returncode, checked.stderr)
        self.assertIn("AGENTS BRIDGE: INSTALLED", checked.stdout)

    def test_agents_bridge_check_is_read_only_and_detects_corruption(self) -> None:
        self.write("TEAM_ROUTER.md", "# marker\n")
        self.write("AGENTS.md", "# Existing rules\n<!-- AI_AGENT_WORKSPACE_PACK:BEGIN v1 -->\n")

        checked = self.init_project("--check-agents-bridge")
        self.assertNotEqual(0, checked.returncode)
        self.assertIn("AGENTS BRIDGE: CORRUPT", checked.stdout)
        self.assertFalse((self.root / "_agent_ops").exists())

        installed = self.init_project("--install-agents-bridge")
        self.assertEqual(0, installed.returncode, installed.stderr)
        self.assertIn("AGENTS BRIDGE: CORRUPT", installed.stdout)
        self.assertIn("not modified", installed.stdout)

    def test_agents_bridge_updates_only_its_outdated_managed_block(self) -> None:
        self.write("TEAM_ROUTER.md", "# marker\n")
        self.write(
            "AGENTS.md",
            "# Host rules\n"
            "<!-- AI_AGENT_WORKSPACE_PACK:BEGIN v1 -->\nold bridge\n"
            "<!-- AI_AGENT_WORKSPACE_PACK:END v1 -->\n"
            "# Host footer\n",
        )

        before = self.init_project("--check-agents-bridge")
        self.assertNotEqual(0, before.returncode)
        self.assertIn("AGENTS BRIDGE: OUTDATED", before.stdout)

        installed = self.init_project("--install-agents-bridge")
        self.assertEqual(0, installed.returncode, installed.stderr)
        self.assertIn("managed bridge v1 updated", installed.stdout)
        agents = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertTrue(agents.startswith("# Host rules\n"))
        self.assertTrue(agents.endswith("# Host footer\n"))
        self.assertNotIn("old bridge", agents)
        self.assertEqual(1, agents.count("AI_AGENT_WORKSPACE_PACK:BEGIN v1"))

    def test_nested_function_calls_are_not_attributed_to_outer_owner(self) -> None:
        self.write(
            "src/nested.py",
            "def target():\n"
            "    pass\n"
            "\n\n"
            "def other():\n"
            "    pass\n"
            "\n\n"
            "def outer():\n"
            "    def inner():\n"
            "        target()\n"
            "\n"
            "    other()\n",
        )
        self.assertEqual(0, self.init_project().returncode)
        index = json.loads((self.root / "_agent_ops" / "code_index.json").read_text(encoding="utf-8"))
        calls = {(edge["from"], edge["to"]) for edge in index["edges"] if edge["kind"] == "CALLS"}
        self.assertIn(("src/nested.py::outer", "src/nested.py::other"), calls)
        self.assertIn(("src/nested.py::outer.inner", "src/nested.py::target"), calls)
        self.assertNotIn(("src/nested.py::outer", "src/nested.py::target"), calls)

    def test_attribute_calls_never_resolve_as_exact(self) -> None:
        self.write(
            "src/billing.py",
            "class BillingService:\n    def save(self):\n        pass\n",
        )
        self.write(
            "src/cache.py",
            "from billing import BillingService\n\n\ndef flush(cache):\n    cache.save()\n",
        )
        self.assertEqual(0, self.init_project().returncode)
        index = json.loads((self.root / "_agent_ops" / "code_index.json").read_text(encoding="utf-8"))
        save_edges = [
            edge
            for edge in index["edges"]
            if edge["kind"] == "CALLS"
            and edge["from"] == "src/cache.py::flush"
            and edge["to"].endswith("::BillingService.save")
        ]
        self.assertTrue(save_edges, "expected an attribute-call edge to BillingService.save")
        self.assertNotEqual("exact", save_edges[0]["conf"])
        self.assertFalse(
            any(edge["kind"] == "CALLS" and edge["conf"] == "exact" and edge["to"].endswith(".save") for edge in index["edges"]),
            "attribute calls (obj.save()) must never resolve as exact",
        )

    def test_force_never_replaces_existing_agents_file(self) -> None:
        self.write("AGENTS.md", "# Existing project rules\nKeep this marker.\n")
        result = self.init_project("--force")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("SKIP existing: " + str(self.root / "AGENTS.md"), result.stdout)
        self.assertIn("Keep this marker.", (self.root / "AGENTS.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

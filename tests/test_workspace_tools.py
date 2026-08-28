"""Golden regression checks for the portable workspace-tool runtime.

Every fixture is created under the OS temporary directory, never inside this
repository. That keeps the pack's own code graph and hygiene result independent
of its tests.
"""

from __future__ import annotations

import json
import os
import shutil
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

    def test_a_pack_at_the_scanned_root_is_the_project(self) -> None:
        """A pack unpacked at the root and the pack's own source checkout are
        indistinguishable, so nothing at the root is treated as infrastructure.
        Excluding it made the pack's own repo map report a single file."""
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
        self.assertEqual(
            ["scripts/init_project_ops.py", "src/app.py"],
            sorted(json.loads(embedded_scan.stdout)["graph"]),
        )
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

    def test_namespaced_embed_keeps_pack_and_ops_in_one_folder(self) -> None:
        pack = self.root / "ai-agent-workspace-pack"
        self.write("ai-agent-workspace-pack/TEAM_ROUTER.md", "# copied pack marker\n")
        self.write("ai-agent-workspace-pack/core-context/.keep", "")
        self.write("ai-agent-workspace-pack/scripts/init_project_ops.py", "def pack_tool():\n    pass\n")
        self.write("AGENTS.md", "# Host rules\nKeep this text exactly.\n")
        self.write("src/app.py", "def project_entry():\n    return 'project'\n")

        installed = self.init_project(
            "--embedded-folder",
            "ai-agent-workspace-pack",
            "--install-agents-bridge",
        )
        self.assertEqual(0, installed.returncode, installed.stderr)
        self.assertFalse((self.root / "_agent_ops").exists())
        ops = pack / "_agent_ops"
        self.assertTrue((ops / "tools" / "session_start.py").is_file())
        self.assertTrue((ops / "REPO_MAP.md").is_file())
        self.assertIn("1 code files indexed", installed.stdout)

        bridge = "@ai-agent-workspace-pack/AGENTS.md\n"
        agents = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(bridge + "# Host rules\nKeep this text exactly.\n", agents)
        self.assertIn("@ai-agent-workspace-pack/AGENTS.md", (self.root / "CLAUDE.md").read_text(encoding="utf-8"))
        self.assertIn("@./ai-agent-workspace-pack/AGENTS.md", (self.root / "GEMINI.md").read_text(encoding="utf-8"))

        check = self.init_project("--embedded-folder", "ai-agent-workspace-pack", "--check-agents-bridge")
        self.assertEqual(0, check.returncode, check.stderr)
        self.assertIn("AGENTS BRIDGE: INSTALLED", check.stdout)

        second = self.init_project(
            "--embedded-folder",
            "ai-agent-workspace-pack",
            "--install-agents-bridge",
        )
        self.assertEqual(0, second.returncode, second.stderr)
        self.assertEqual(agents, (self.root / "AGENTS.md").read_text(encoding="utf-8"))

        session = self.run_tool(ops / "tools" / "session_start.py", "--root", ".", cwd=self.root)
        self.assertEqual(0, session.returncode, session.stderr)
        self.assertNotIn("does not exist. Initialize it", session.stdout)
        self.assertIn("src/app.py", (ops / "REPO_MAP.md").read_text(encoding="utf-8"))
        repo_map = (ops / "REPO_MAP.md").read_text(encoding="utf-8")
        self.assertNotIn("ai-agent-workspace-pack/scripts", repo_map)
        self.assertIn("--output ai-agent-workspace-pack/_agent_ops/REPO_MAP.md", repo_map)
        index = (ops / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("ai-agent-workspace-pack/_agent_ops/tools/session_start.py", index)

    def test_namespaced_embed_hook_stages_its_nested_repo_map(self) -> None:
        self.assertEqual(0, subprocess.run(["git", "init", "-q"], cwd=self.root, check=False).returncode)
        self.write("ai-agent-workspace-pack/TEAM_ROUTER.md", "# copied pack marker\n")
        self.write("ai-agent-workspace-pack/core-context/.keep", "")
        self.write("ai-agent-workspace-pack/scripts/init_project_ops.py", "def pack_tool():\n    pass\n")
        self.write("src/app.py", "def project_entry():\n    return 'first'\n")

        installed = self.init_project(
            "--embedded-folder",
            "ai-agent-workspace-pack",
            "--install-agents-bridge",
            "--install-repo-map-hook",
        )
        self.assertEqual(0, installed.returncode, installed.stderr)
        self.assertIn("managed repo-map pre-commit hook", installed.stdout)

        self.assertEqual(0, subprocess.run(["git", "add", "src/app.py"], cwd=self.root, check=False).returncode)
        committed = subprocess.run(
            ["git", "commit", "-qm", "namespaced map refresh"],
            cwd=self.root,
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, committed.returncode, committed.stdout + committed.stderr)
        staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=self.root, text=True, capture_output=True)
        self.assertEqual("", staged.stdout)
        ops = self.root / "ai-agent-workspace-pack" / "_agent_ops"
        self.assertTrue((ops / "REPO_MAP.md").is_file())
        hygiene = self.run_tool(ops / "tools" / "check_repo_hygiene.py", "--root", ".", cwd=self.root)
        self.assertEqual(0, hygiene.returncode, hygiene.stderr)
        self.assertIn("PASS: No session-scoped ai-agent-workspace-pack/_agent_ops/ files are tracked.", hygiene.stdout)

    def test_namespaced_embed_creates_only_the_bridge_when_host_agents_is_absent(self) -> None:
        self.write("ai-agent-workspace-pack/TEAM_ROUTER.md", "# copied pack marker\n")
        self.write("ai-agent-workspace-pack/core-context/.keep", "")
        self.write("ai-agent-workspace-pack/scripts/init_project_ops.py", "def pack_tool():\n    pass\n")

        installed = self.init_project(
            "--embedded-folder",
            "ai-agent-workspace-pack",
            "--install-agents-bridge",
        )
        self.assertEqual(0, installed.returncode, installed.stderr)
        self.assertEqual(
            "@ai-agent-workspace-pack/AGENTS.md\n",
            (self.root / "AGENTS.md").read_text(encoding="utf-8"),
        )

    def test_embed_pack_copies_clean_source_and_initializes_fresh_nested_ops(self) -> None:
        self.write("AGENTS.md", "# Host rules\n")
        self.write("src/app.py", "def project_entry():\n    return 'project'\n")

        embedded = self.run_tool(SCRIPTS / "embed_pack.py", "--target", str(self.root), cwd=PACK_ROOT)
        self.assertEqual(0, embedded.returncode, embedded.stderr)
        pack = self.root / "ai-agent-workspace-pack"
        self.assertTrue((pack / "TEAM_ROUTER.md").is_file())
        self.assertFalse((pack / ".git").exists())
        self.assertTrue((pack / "_agent_ops" / "tools" / "session_start.py").is_file())
        self.assertNotIn(
            "ai-agent-workspace-pack\n",
            (pack / "_agent_ops" / "PROJECT_CONTEXT_CARD.md").read_text(encoding="utf-8"),
        )
        self.assertEqual(
            "@ai-agent-workspace-pack/AGENTS.md\n# Host rules\n",
            (self.root / "AGENTS.md").read_text(encoding="utf-8"),
        )

    def test_named_directory_without_pack_signature_remains_project_code(self) -> None:
        self.write("ai-agent-workspace-pack/src/host_feature.py", "def host_feature():\n    return True\n")

        scan = self.run_tool(SCRIPTS / "scan_deps.py", "--root", str(self.root), "--output", "json", cwd=PACK_ROOT)
        self.assertEqual(0, scan.returncode, scan.stderr)
        self.assertIn("ai-agent-workspace-pack/src/host_feature.py", json.loads(scan.stdout)["graph"])

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

    def test_impact_groups_hops_by_worst_edge_confidence(self) -> None:
        # a --exact--> b --weak--> c --exact--> d
        # Impact of d must not let a weak hop (b->c) hide behind an exact hop
        # (c->d): only c belongs in "Confirmed impact"; a and b are tainted by
        # the weak edge on their only path back to d.
        index = {
            "version": 1,
            "generated": "2026-08-27",
            "commit": "test",
            "root": ".",
            "files": {},
            "symbols": {
                "a.py::a": {"file": "a.py", "qualname": "a", "lang": "python", "kind": "function", "line": 1},
                "b.py::b": {"file": "b.py", "qualname": "b", "lang": "python", "kind": "function", "line": 1},
                "c.py::c": {"file": "c.py", "qualname": "c", "lang": "python", "kind": "function", "line": 1},
                "d.py::d": {"file": "d.py", "qualname": "d", "lang": "python", "kind": "function", "line": 1},
            },
            "edges": [
                {"from": "a.py::a", "to": "b.py::b", "kind": "CALLS", "conf": "exact", "line": 1},
                {"from": "b.py::b", "to": "c.py::c", "kind": "CALLS", "conf": "weak", "line": 1},
                {"from": "c.py::c", "to": "d.py::d", "kind": "CALLS", "conf": "exact", "line": 1},
            ],
        }
        self.write("index.json", json.dumps(index))
        result = self.run_tool(
            SCRIPTS / "explore.py", "--root", str(self.root), "--index", "index.json", "--impact", "d", "--depth", "4",
        )
        self.assertEqual(0, result.returncode, result.stderr)

        def section(title: str) -> str:
            start = result.stdout.index(title)
            rest = result.stdout[start:]
            next_marker = rest.find("\n### ", 1)
            end_marker = rest.find("\n## ", 1)
            cut = min(m for m in (next_marker, end_marker) if m != -1)
            return rest[:cut]

        confirmed = section("### Confirmed impact")
        uncertain = section("### Uncertain leads")
        self.assertIn("c.py", confirmed)
        self.assertNotIn("a.py", confirmed)
        self.assertNotIn("b.py", confirmed)
        self.assertIn("a.py", uncertain)
        self.assertIn("b.py", uncertain)
        self.assertNotIn("### Probable impact", result.stdout)

    def test_tsconfig_paths_resolve_at_alias_imports(self) -> None:
        self.write(
            "tsconfig.json",
            "{\n"
            '  // repo tsconfig\n'
            '  "compilerOptions": {\n'
            '    "baseUrl": ".",\n'
            '    "paths": {\n'
            '      "@/*": ["./src/*"],\n'
            '    },\n'
            "  },\n"
            "}\n",
        )
        self.write("src/components/Button.tsx", "export function Button() { return 'button'; }\n")
        self.write(
            "src/ui/Page.tsx",
            "import Button from '@/components/Button';\n\nexport function renderPage() { return Button(); }\n",
        )
        self.assertEqual(0, self.init_project().returncode)
        index = json.loads((self.root / "_agent_ops" / "code_index.json").read_text(encoding="utf-8"))
        self.assert_import(index, "src/ui/Page.tsx", "src/components/Button.tsx", "heuristic")

    def test_claude_and_gemini_get_thin_agents_md_import_adapters(self) -> None:
        result = self.init_project()
        self.assertEqual(0, result.returncode, result.stderr)

        claude_md = (self.root / "CLAUDE.md").read_text(encoding="utf-8")
        gemini_md = (self.root / "GEMINI.md").read_text(encoding="utf-8")
        self.assertTrue(claude_md.startswith("@AGENTS.md"))
        self.assertTrue(gemini_md.startswith("@./AGENTS.md"))

        # Never overwritten: an existing CLAUDE.md/GEMINI.md is left untouched.
        self.write("CLAUDE.md", "# Existing Claude rules\nKeep this.\n")
        second = self.init_project("--force")
        self.assertEqual(0, second.returncode, second.stderr)
        self.assertEqual(
            "# Existing Claude rules\nKeep this.\n",
            (self.root / "CLAUDE.md").read_text(encoding="utf-8"),
        )

    def test_existing_harness_files_without_the_import_are_warned_about(self) -> None:
        self.write("CLAUDE.md", "# Existing Claude rules\nKeep this.\n")
        self.write("GEMINI.md", "# Existing Gemini rules\n@./other.md\n")

        result = self.init_project()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("WARN existing CLAUDE.md does not import AGENTS.md", result.stdout)
        self.assertIn("@AGENTS.md", result.stdout)
        self.assertIn("WARN existing GEMINI.md does not import AGENTS.md", result.stdout)
        self.assertIn("@./AGENTS.md", result.stdout)
        self.assertEqual(
            "# Existing Claude rules\nKeep this.\n",
            (self.root / "CLAUDE.md").read_text(encoding="utf-8"),
        )

        # No false positive once the import is actually present.
        self.write("CLAUDE.md", "@AGENTS.md\n\n## Claude Code\nExtra rule.\n")
        self.write("GEMINI.md", "@./AGENTS.md\n")
        clean = self.init_project()
        self.assertEqual(0, clean.returncode, clean.stderr)
        self.assertNotIn("WARN existing CLAUDE.md", clean.stdout)
        self.assertNotIn("WARN existing GEMINI.md", clean.stdout)

    def test_force_never_replaces_existing_agents_file(self) -> None:
        self.write("AGENTS.md", "# Existing project rules\nKeep this marker.\n")
        result = self.init_project("--force")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("SKIP existing: " + str(self.root / "AGENTS.md"), result.stdout)
        self.assertIn("Keep this marker.", (self.root / "AGENTS.md").read_text(encoding="utf-8"))


    def test_namespaced_embed_installs_root_harness_adapters(self) -> None:
        """Codex reads `.codex/agents/` and Claude Code reads `.claude/agents/`
        and `.claude/skills/` at the REPOSITORY ROOT only. A namespaced install
        buries both one level down, so without these pointers the four subagents
        and the nine team skills silently disappear."""
        self.write("ai-agent-workspace-pack/TEAM_ROUTER.md", "# copied pack marker\n")
        self.write("ai-agent-workspace-pack/core-context/.keep", "")
        self.write("ai-agent-workspace-pack/scripts/init_project_ops.py", "def pack_tool():\n    pass\n")
        self.write(
            "ai-agent-workspace-pack/.codex/agents/tester.toml",
            'name = "tester"\ndeveloper_instructions = """\nFollow tester-team/SKILL.md.\n"""\n',
        )
        self.write(
            "ai-agent-workspace-pack/.claude/agents/tester.md",
            "---\nname: tester\n---\n\nFollow `tester-team/SKILL.md` and `_agent_ops/REPO_MAP.md`.\n",
        )
        self.write(
            "ai-agent-workspace-pack/.claude/skills/tester-team/SKILL.md",
            "---\nname: tester-team\n---\n\nSource of truth: `tester-team/SKILL.md`.\n",
        )
        self.write("src/app.py", "def project_entry():\n    return 'project'\n")

        installed = self.init_project("--embedded-folder", "ai-agent-workspace-pack")
        self.assertEqual(0, installed.returncode, installed.stderr)
        self.assertIn("ROOT ADAPTERS: 3 written", installed.stdout)

        codex = (self.root / ".codex" / "agents" / "tester.toml").read_text(encoding="utf-8")
        self.assertTrue(codex.startswith("# AI_AGENT_WORKSPACE_PACK:ADAPTER v1"))
        self.assertIn("Follow ai-agent-workspace-pack/tester-team/SKILL.md.", codex)

        agent_path = self.root / ".claude" / "agents" / "tester.md"
        agent = agent_path.read_text(encoding="utf-8")
        # The marker must never displace YAML frontmatter, or discovery breaks.
        self.assertTrue(agent.startswith("---\nname: tester\n---\n"), agent)
        self.assertIn("AI_AGENT_WORKSPACE_PACK:ADAPTER v1", agent)
        self.assertIn("`ai-agent-workspace-pack/tester-team/SKILL.md`", agent)
        self.assertIn("`ai-agent-workspace-pack/_agent_ops/REPO_MAP.md`", agent)
        skill = (self.root / ".claude" / "skills" / "tester-team" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`ai-agent-workspace-pack/tester-team/SKILL.md`", skill)

        second = self.init_project("--embedded-folder", "ai-agent-workspace-pack")
        self.assertEqual(0, second.returncode, second.stderr)
        self.assertIn("ROOT ADAPTERS: 0 written, 3 unchanged", second.stdout)
        self.assertNotIn(
            "ai-agent-workspace-pack/ai-agent-workspace-pack",
            agent_path.read_text(encoding="utf-8"),
        )

        host = "---\nname: tester\n---\n\nHost owned.\n"
        agent_path.write_text(host, encoding="utf-8")
        third = self.init_project("--embedded-folder", "ai-agent-workspace-pack")
        self.assertEqual(0, third.returncode, third.stderr)
        self.assertIn("SKIP host-owned adapter", third.stdout)
        self.assertEqual(host, agent_path.read_text(encoding="utf-8"))

        opted_out = self.init_project(
            "--embedded-folder", "ai-agent-workspace-pack", "--no-root-adapters"
        )
        self.assertEqual(0, opted_out.returncode, opted_out.stderr)
        self.assertIn("SKIP root harness adapters", opted_out.stdout)

    def test_nested_workspace_pack_is_excluded_from_map_and_index(self) -> None:
        """The symbol graph must answer about the project, not about the pack
        copied into it -- and it must agree with the dependency scan that feeds
        REPO_MAP.md. They disagreed once, so both are asserted together."""
        self.write("ai-agent-workspace-pack/TEAM_ROUTER.md", "# copied pack marker\n")
        self.write("ai-agent-workspace-pack/core-context/.keep", "")
        self.write("ai-agent-workspace-pack/scripts/init_project_ops.py", "def pack_tool():\n    pass\n")
        self.write(
            "ai-agent-workspace-pack/scripts/explore.py",
            "from init_project_ops import pack_tool\n\n\ndef pack_helper():\n    return pack_tool()\n",
        )
        self.write("src/app.py", "def project_entry():\n    return 'project'\n")

        output = self.root / "index.json"
        built = self.run_tool(
            SCRIPTS / "build_code_index.py",
            "--root",
            str(self.root),
            "--output",
            str(output),
            cwd=PACK_ROOT,
        )
        self.assertEqual(0, built.returncode, built.stderr)
        index = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(["src/app.py"], sorted(index["files"]))
        self.assertNotIn("pack_tool", json.dumps(index["symbols"]))
        self.assertNotIn("pack_helper", json.dumps(index["symbols"]))

        scanned = self.run_tool(
            SCRIPTS / "scan_deps.py", "--root", str(self.root), "--output", "json", cwd=PACK_ROOT
        )
        self.assertEqual(0, scanned.returncode, scanned.stderr)
        self.assertEqual(sorted(index["files"]), sorted(json.loads(scanned.stdout)["graph"]))

    def test_pack_copied_into_a_project_installs_itself_namespaced(self) -> None:
        """The documented bootstrap is `init_project_ops.py --target .`, reached
        through the copied folder. Before auto-detection that exact command put
        `_agent_ops/` at the application root and installed no root adapters --
        the flat layout, reproduced by the pack's own instructions."""
        pack = self.root / "ai-agent-workspace-pack"
        pack.mkdir(parents=True)
        for entry in ("scripts", "core-context", ".claude", ".codex"):
            shutil.copytree(PACK_ROOT / entry, pack / entry)
        shutil.copy2(PACK_ROOT / "TEAM_ROUTER.md", pack / "TEAM_ROUTER.md")
        self.write("AGENTS.md", "# Host rules\nKeep this text exactly.\n")
        self.write("src/app.py", "def project_entry():\n    return 'project'\n")

        installed = self.run_tool(
            pack / "scripts" / "init_project_ops.py",
            "--target",
            str(self.root),
            "--no-index",
            "--no-repo-map",
        )
        self.assertEqual(0, installed.returncode, installed.stderr)
        self.assertIn("EMBEDDED FOLDER: auto-detected ai-agent-workspace-pack", installed.stdout)
        self.assertFalse((self.root / "_agent_ops").exists())
        self.assertTrue((pack / "_agent_ops" / "tools" / "session_start.py").is_file())
        self.assertTrue((self.root / ".codex" / "agents").is_dir())
        self.assertTrue((self.root / ".claude" / "skills" / "tester-team" / "SKILL.md").is_file())

        # A host AGENTS.md is never edited implicitly; the warning must name the
        # command that fixes it, because without the bridge no harness reads the pack.
        self.assertEqual(
            "# Host rules\nKeep this text exactly.\n",
            (self.root / "AGENTS.md").read_text(encoding="utf-8"),
        )
        self.assertIn("no harness will read the pack", installed.stdout)
        self.assertIn(
            "python ai-agent-workspace-pack/scripts/init_project_ops.py --target . --install-agents-bridge",
            installed.stdout,
        )

        bridged = self.run_tool(
            pack / "scripts" / "init_project_ops.py",
            "--target",
            str(self.root),
            "--no-index",
            "--no-repo-map",
            "--install-agents-bridge",
        )
        self.assertEqual(0, bridged.returncode, bridged.stderr)
        self.assertEqual(
            "@ai-agent-workspace-pack/AGENTS.md\n# Host rules\nKeep this text exactly.\n",
            (self.root / "AGENTS.md").read_text(encoding="utf-8"),
        )

        # An explicit ops folder still wins over detection.
        flat = self.run_tool(
            pack / "scripts" / "init_project_ops.py",
            "--target",
            str(self.root),
            "--ops-folder",
            "_agent_ops",
            "--no-index",
            "--no-repo-map",
        )
        self.assertEqual(0, flat.returncode, flat.stderr)
        self.assertNotIn("EMBEDDED FOLDER: auto-detected", flat.stdout)
        self.assertTrue((self.root / "_agent_ops").is_dir())

    def test_repository_without_commits_is_still_a_repository(self) -> None:
        """`rev-parse HEAD` fails before the first commit. Deriving "is this a
        git repo" from it reported a brand-new project as "not a git
        repository", which skipped the file listing, the source fingerprint and
        every staleness check on the one session that first builds the map."""
        self.assertEqual(0, subprocess.run(["git", "init", "-q"], cwd=self.root, check=False).returncode)
        self.write("src/app.py", "def project_entry():\n    return 'project'\n")
        installed = self.init_project()
        self.assertEqual(0, installed.returncode, installed.stderr)
        self.assertEqual(
            0,
            subprocess.run(["git", "add", "src/app.py"], cwd=self.root, check=False).returncode,
        )

        tools = self.root / "_agent_ops" / "tools"
        session = self.run_tool(tools / "session_start.py", "--root", ".")
        self.assertEqual(0, session.returncode, session.stderr)
        self.assertNotIn("not a git repository", session.stdout)
        self.assertIn("HEAD: none yet (no commits in this repository)", session.stdout)
        self.assertIn("A  src/app.py", session.stdout)
        self.assertIn("no commits yet, so there is nothing to verify memory against", session.stdout)
        # No branch may fall through to a `HEAD (not available)` label.
        self.assertNotIn("not available", session.stdout)

        # The fingerprint path works without any commit, so a rebuild against the
        # staged index must report current rather than unknown.
        for tool, output in (
            ("build_code_index.py", "_agent_ops/code_index.json"),
            ("generate_repo_map.py", "_agent_ops/REPO_MAP.md"),
        ):
            args = ["--root", ".", "--output", output]
            if tool == "generate_repo_map.py":
                args.append("--force")
            rebuilt = self.run_tool(tools / tool, *args)
            self.assertEqual(0, rebuilt.returncode, rebuilt.stderr)

        refreshed = self.run_tool(tools / "session_start.py", "--root", ".")
        self.assertEqual(0, refreshed.returncode, refreshed.stderr)
        self.assertIn("Current with the staged source index", refreshed.stdout)

    def test_first_commit_in_a_fresh_repository_passes_the_repo_map_hook(self) -> None:
        """The managed pre-commit hook runs for the first commit too, when there
        is no HEAD to diff against."""
        self.assertEqual(0, subprocess.run(["git", "init", "-q"], cwd=self.root, check=False).returncode)
        self.write("src/app.py", "def project_entry():\n    return 'project'\n")
        installed = self.init_project("--install-repo-map-hook")
        self.assertEqual(0, installed.returncode, installed.stderr)

        staged = self.run_tool(
            self.root / "_agent_ops" / "tools" / "refresh_repo_map.py", "--root", ".", "--stage"
        )
        self.assertEqual(0, staged.returncode, staged.stderr)
        self.assertNotIn("Traceback", staged.stderr)

if __name__ == "__main__":
    unittest.main()

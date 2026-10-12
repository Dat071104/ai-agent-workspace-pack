"""What a pack install ships, and who owns what afterwards.

Every fixture lives under the OS temp directory. The "source pack" is a copy of
this repository (so the scripts under test are the real ones), optionally made
into its own Git repository; hosts are bare temp directories. Secrets are fake.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


sys.dont_write_bytecode = True
PACK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACK_ROOT / "scripts"))

from init_project_ops import AGENTS_BRIDGE_BEGIN  # noqa: E402
from pack_manifest import MANIFEST_FILE, NOT_SHIPPED_TOP_LEVEL, is_allowlisted, is_denied  # noqa: E402
from pack_manifest import local_tree_files, repo_files, sha256_file, strip_managed_blocks  # noqa: E402
from pack_ownership import content_ids  # noqa: E402

PACK = "ai-agent-workspace-pack"
FAKE_SECRET = "FAKE_TOKEN_do_not_ship_0123456789"
SELF_BRIDGE = (
    "<!-- AI_AGENT_WORKSPACE_PACK:BEGIN v2 -->\n## AI Agent Workspace Pack\n\n"
    "This repository is the workspace pack itself.\n<!-- AI_AGENT_WORKSPACE_PACK:END v2 -->\n"
)
HOST_RULES = "# Host rules\nKeep this text exactly.\n"


class ShippingBase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="pack-shipping-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.host = self.base / "host"
        self.host.mkdir()

    def write(self, root: Path, rel: str, content: str) -> Path:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="")
        return path

    def git(self, root: Path, *args: str) -> str:
        # Never let a fixture mistake drive Git inside the real checkout.
        self.assertTrue(root.resolve().is_relative_to(self.base.resolve()), root)
        self.assertFalse((root / ".git").is_file(), "a .git FILE aliases another repository")
        result = subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "core.autocrlf=false", *args],
            cwd=str(root), text=True, capture_output=True, check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return result.stdout.strip()

    def make_source(self, name: str = "source", git: bool = True, block: bool = False) -> Path:
        """A copy of this pack, with local junk next to it, optionally a Git repo."""

        source = self.base / name
        for rel in local_tree_files(PACK_ROOT):
            destination = source / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(PACK_ROOT / rel, destination)
        if block:
            agents = source / "AGENTS.md"
            agents.write_bytes(agents.read_bytes() + b"\n" + SELF_BRIDGE.encode("utf-8"))
        if git:
            self.write(source, ".gitignore", (source / ".gitignore").read_text(encoding="utf-8") + "\nscratch_notes.txt\n")
            self.git(source, "init", "-q")
            self.git(source, "add", "-A")
            self.git(source, "commit", "-q", "-m", "pack")
        self.write(source, ".env", f"TOKEN={FAKE_SECRET}\n")
        self.write(source, ".env.local", f"TOKEN={FAKE_SECRET}\n")
        self.write(source, ".venv/pyvenv.cfg", "home = nowhere\n")
        self.write(source, "node_modules/leftpad/index.js", "module.exports = 1\n")
        self.write(source, "scripts/__pycache__/junk.cpython-312.pyc", "bytecode")
        self.write(source, ".DS_Store", "junk")
        return source

    def run_script(self, source: Path, script: str, *args: str, cwd: Path | None = None):
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        return subprocess.run(
            [sys.executable, "-B", str(source / "scripts" / script), *args],
            cwd=str(cwd or self.host), env=env, text=True, capture_output=True, check=False,
        )

    def embed(self, source: Path, *args: str):
        return self.run_script(source, "embed_pack.py", "--target", str(self.host), *args)

    def files_under(self, root: Path) -> set[str]:
        return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


class FreshEmbedTests(ShippingBase):
    def assert_clean_ship(self, source: Path) -> Path:
        result = self.embed(source)
        self.assertEqual(0, result.returncode, result.stderr)
        pack = self.host / PACK
        shipped = self.files_under(pack)
        for local in (".env", ".env.local", ".venv/pyvenv.cfg", "node_modules/leftpad/index.js", ".DS_Store"):
            self.assertNotIn(local, shipped)
        self.assertFalse([rel for rel in shipped if "__pycache__" in rel and not rel.startswith("_agent_ops/")])
        self.assertFalse([rel for rel in shipped if rel.startswith(("tests/", "examples/"))])
        for rel in shipped:
            self.assertNotIn(FAKE_SECRET, (pack / rel).read_text(encoding="utf-8", errors="ignore"), rel)
        for needed in ("TEAM_ROUTER.md", "AGENTS.md", "scripts/init_project_ops.py",
                       "core-context/README.md", ".claude/skills/tester-team/SKILL.md",
                       ".codex/agents/tester.toml", "PACK_VERSION", MANIFEST_FILE):
            self.assertIn(needed, shipped)
        return pack

    def test_git_source_ships_tracked_allowlisted_files_only(self) -> None:
        source = self.make_source(git=True)
        self.write(source, "scratch_notes.txt", "ignored by .gitignore, inside no allowlist rule")
        self.write(source, "scripts/scratch_notes.txt", "ignored by .gitignore inside scripts/")
        self.write(source, "commands/untracked-idea.md", "forgot to git add")
        pack = self.assert_clean_ship(source)
        self.assertFalse((pack / "scripts" / "scratch_notes.txt").exists())
        self.assertFalse((pack / "commands" / "untracked-idea.md").exists())
        self.assertIn("commands/untracked-idea.md", self.embed_warnings(source))

    def embed_warnings(self, source: Path) -> str:
        # Re-running into a fresh host shows the same warning.
        other = self.base / "host2"
        other.mkdir()
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        return subprocess.run(
            [sys.executable, "-B", str(source / "scripts" / "embed_pack.py"), "--target", str(other)],
            cwd=str(other), env=env, text=True, capture_output=True, check=False,
        ).stdout

    def test_non_git_source_uses_allowlist_plus_denylist(self) -> None:
        self.assert_clean_ship(self.make_source(git=False))

    def test_manifest_records_exactly_what_was_written(self) -> None:
        pack = self.assert_clean_ship(self.make_source())
        manifest = json.loads((pack / MANIFEST_FILE).read_text(encoding="utf-8"))
        written = self.files_under(pack)
        for rel, digest in manifest["files"].items():
            self.assertEqual(digest, sha256_file(pack / rel), rel)
        owned = set(manifest["files"])
        self.assertTrue(owned <= written)
        self.assertFalse([rel for rel in written - owned if not rel.startswith("_agent_ops/")
                          and rel not in {"PACK_VERSION", MANIFEST_FILE}])

    def test_chain_from_host_claude_md_never_says_the_host_is_the_pack(self) -> None:
        """CLAUDE.md -> root AGENTS.md -> pack AGENTS.md -> root adapters."""
        source = self.make_source(block=True)  # an old source still carrying the self-bridge
        self.write(self.host, "AGENTS.md", HOST_RULES)
        result = self.embed(source)
        self.assertEqual(0, result.returncode, result.stderr)

        chain = [self.host / "CLAUDE.md", self.host / "AGENTS.md", self.host / PACK / "AGENTS.md"]
        for root in (".claude/skills", ".claude/agents", ".codex/agents"):
            chain += [p for p in (self.host / root).rglob("*") if p.is_file()]
        imports = [line[1:] for line in chain[0].read_text(encoding="utf-8").splitlines() if line.startswith("@")]
        self.assertEqual(["AGENTS.md", f"{PACK}/AGENTS.md"], imports)
        for imported in imports:
            self.assertTrue((self.host / imported).is_file(), imported)

        root_agents = (self.host / "AGENTS.md").read_text(encoding="utf-8")
        self.assertTrue(root_agents.startswith(AGENTS_BRIDGE_BEGIN))
        self.assertTrue(root_agents.endswith(HOST_RULES), root_agents[-120:])

        self.assertNotIn("<!-- AI_AGENT_WORKSPACE_PACK", (self.host / PACK / "AGENTS.md").read_text(encoding="utf-8"))
        reference = re.compile(re.escape(PACK) + r"/([A-Za-z0-9_./-]+)")
        self.assertGreaterEqual(len(chain), 20)
        for path in chain:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("workspace pack itself", text, path)
            for match in reference.finditer(text):
                target = match.group(1).rstrip(".,;:)`'\"")
                self.assertTrue((self.host / PACK / target).exists(), f"{path.name} points at missing {target}")


class InPlaceAndOverlapTests(ShippingBase):
    def test_in_place_install_copies_nothing_and_is_repeatable(self) -> None:
        source = self.make_source("seed", git=False, block=True)
        pack = self.host / PACK
        shutil.copytree(source, pack)
        before = self.files_under(pack)
        first = self.run_script(pack, "embed_pack.py", "--target", str(self.host))
        self.assertEqual(0, first.returncode, first.stdout + first.stderr)
        self.assertIn("in place", first.stdout)
        self.assertFalse((pack / PACK).exists())
        self.assertTrue((pack / "_agent_ops" / "tools" / "session_start.py").is_file())
        self.assertTrue((pack / "tests").is_dir(), "files outside the shipping set are left alone")
        self.assertNotIn("workspace pack itself", (pack / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertIn(AGENTS_BRIDGE_BEGIN, (self.host / "AGENTS.md").read_text(encoding="utf-8"))
        manifest = json.loads((pack / MANIFEST_FILE).read_text(encoding="utf-8"))["files"]
        self.assertFalse([rel for rel in manifest if rel.startswith(("tests/", "examples/"))])
        self.assertIn("scripts/init_project_ops.py", manifest)
        self.assertTrue(before <= self.files_under(pack), "an in-place install deletes nothing")

        digest = sha256_file(pack / MANIFEST_FILE)
        second = self.run_script(pack, "embed_pack.py", "--target", str(self.host))
        self.assertEqual(0, second.returncode, second.stderr)
        self.assertEqual(digest, sha256_file(pack / MANIFEST_FILE))

    def test_destination_inside_source_is_refused_before_any_copy(self) -> None:
        source = self.make_source("seed", git=False)
        inner = source / "sub"
        inner.mkdir()
        result = self.run_script(source, "embed_pack.py", "--target", str(inner))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("lies inside the source pack", result.stderr)
        self.assertFalse((inner / PACK).exists())
        itself = self.run_script(source, "embed_pack.py", "--target", str(source))
        self.assertNotEqual(0, itself.returncode)
        self.assertFalse((source / PACK).exists())

    def test_source_inside_destination_is_refused_before_any_copy(self) -> None:
        source = self.make_source("seed", git=False)
        nested = self.host / PACK / "vendor" / "pack"
        shutil.copytree(source, nested)
        before = self.files_under(self.host)
        result = self.run_script(nested, "embed_pack.py", "--target", str(self.host))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("lies inside the destination", result.stderr)
        self.assertEqual(before, self.files_under(self.host))


class UpdateOwnershipTests(ShippingBase):
    def legacy_install(self, source: Path, version: str) -> Path:
        """What the pre-manifest installer left: a full copy plus a stamp, memory included."""
        pack = self.host / PACK
        shutil.copytree(source, pack, ignore=shutil.ignore_patterns(".git", ".env*", ".venv", "node_modules", "__pycache__"))
        self.write(pack, "PACK_VERSION", f"version: {version}\ninstalled: 2000-01-01\n")
        self.write(pack, "_agent_ops/PROJECT_CONTEXT_CARD.md", "# Card\nPROJECT MEMORY MARKER\n")
        return pack

    def update(self, source: Path, *extra: str):
        return self.embed(source, "--update", "--allow-dirty", *extra)

    def test_legacy_install_loses_unmodified_unshipped_files_and_keeps_modified(self) -> None:
        source = self.make_source()
        revision = self.git(source, "rev-parse", "--short", "HEAD")
        pack = self.legacy_install(source, revision)
        self.write(pack, "examples/README.md", "# my own edit of an example\n")
        self.write(pack, "notes/mine.txt", "host file that no record mentions\n")

        # A pre-stamp install holds real memory, so the one-time ownership choice is required.
        result = self.update(source, "--claim-memory")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertFalse((pack / "tests").exists(), "unmodified tests/ is provably the pack's")
        self.assertFalse((pack / "examples" / "generic-project-example").exists())
        self.assertEqual("# my own edit of an example\n", (pack / "examples" / "README.md").read_text(encoding="utf-8"))
        self.assertIn("examples/README.md", result.stdout)
        self.assertIn("no longer shipped but modified", result.stdout)
        self.assertTrue((pack / "notes" / "mine.txt").is_file())
        self.assertIn("PROJECT MEMORY MARKER", (pack / "_agent_ops" / "PROJECT_CONTEXT_CARD.md").read_text(encoding="utf-8"))
        self.assertFalse((pack / ".update-backup").exists(), "nothing shipped was host-modified")
        self.assertIn(MANIFEST_FILE, self.files_under(pack))

    def test_legacy_install_without_a_provable_revision_removes_nothing(self) -> None:
        source = self.make_source(git=False)
        pack = self.legacy_install(source, "deadbee")
        result = self.update(source, "--claim-memory")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue((pack / "tests" / "test_shipping.py").is_file())
        self.assertIn("cannot prove pack-owned", result.stdout)

    def test_update_with_manifest_removes_only_proven_files_and_backs_up_edits(self) -> None:
        source = self.make_source()
        self.assertEqual(0, self.embed(source).returncode)
        pack = self.host / PACK
        manifest_path = pack / MANIFEST_FILE
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        # An earlier revision shipped these; one has since been edited by the host.
        self.write(pack, "tests/old_test.py", "def test_old():\n    pass\n")
        self.write(pack, "examples/kept.md", "original\n")
        manifest["files"]["tests/old_test.py"] = sha256_file(pack / "tests/old_test.py")
        manifest["files"]["examples/kept.md"] = sha256_file(pack / "examples/kept.md")
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.write(pack, "examples/kept.md", "edited by the host\n")
        self.write(pack, "commands/host-added.md", "never in any manifest\n")
        shipped = (pack / "commands" / "work.md").read_bytes()
        self.write(pack, "commands/work.md", "host customised work.md\n")

        result = self.update(source)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertFalse((pack / "tests").exists())
        self.assertEqual("edited by the host\n", (pack / "examples" / "kept.md").read_text(encoding="utf-8"))
        self.assertTrue((pack / "commands" / "host-added.md").is_file())
        self.assertEqual(shipped, (pack / "commands" / "work.md").read_bytes())
        saved = list((pack / ".update-backup").glob("*/commands/work.md"))
        self.assertEqual(1, len(saved))
        self.assertEqual("host customised work.md\n", saved[0].read_text(encoding="utf-8"))
        self.assertIn("examples/kept.md", result.stdout)
        refreshed = json.loads(manifest_path.read_text(encoding="utf-8"))["files"]
        self.assertNotIn("examples/kept.md", refreshed, "a reported conflict becomes the host's file")
        self.assertNotIn("tests/old_test.py", refreshed)

    def test_update_is_idempotent(self) -> None:
        source = self.make_source()
        self.assertEqual(0, self.embed(source).returncode)
        pack = self.host / PACK
        self.assertEqual(0, self.update(source).returncode)
        digest = sha256_file(pack / MANIFEST_FILE)
        before = self.files_under(pack)
        again = self.update(source)
        self.assertEqual(0, again.returncode, again.stderr)
        self.assertIn("files written: 0", again.stdout)
        self.assertEqual(before, self.files_under(pack))
        self.assertEqual(digest, sha256_file(pack / MANIFEST_FILE))
        self.assertFalse((pack / ".update-backup").exists())


class MigrateProofTests(ShippingBase):
    def flat_host(self, source: Path) -> None:
        for rel in repo_files(source):
            if rel.split("/")[0] in {"_agent_ops"}:
                continue
            destination = self.host / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / rel, destination)
        self.write(self.host, "scripts/my_app_deploy.py", "def deploy():\n    return 'app'\n")
        self.write(self.host, "AGENTS.md", HOST_RULES)

    def migrate(self, source: Path, *args: str):
        return self.run_script(source, "migrate_pack.py", "--target", str(self.host), "--allow-dirty", *args)

    def test_same_name_different_content_is_a_conflict_and_nothing_moves(self) -> None:
        source = self.make_source()
        self.flat_host(source)
        self.write(self.host, "scripts/scan_deps.py", "# the application's own script that shares a name\n")
        before = self.files_under(self.host)
        for args in ((), ("--apply",)):
            result = self.migrate(source, *args)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("CONFLICTS (1)", result.stdout)
            self.assertIn("scripts/scan_deps.py", result.stdout)
            self.assertIn("nothing was moved", result.stderr)
            self.assertFalse((self.host / PACK).exists())
            self.assertEqual(before, self.files_under(self.host))

    def test_proven_pack_files_migrate_including_older_revisions(self) -> None:
        source = self.make_source()
        self.write(source, "harness/README.md", "OLD VERSION\n")
        self.git(source, "add", "harness/README.md")
        self.git(source, "commit", "-q", "-m", "older")
        self.write(source, "harness/README.md", "NEW VERSION\n")
        self.git(source, "add", "harness/README.md")
        self.git(source, "commit", "-q", "-m", "newer")
        self.flat_host(source)
        self.write(self.host, "harness/README.md", "OLD VERSION\n")

        result = self.migrate(source, "--apply")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        pack = self.host / PACK
        self.assertEqual("OLD VERSION\n", (pack / "harness" / "README.md").read_text(encoding="utf-8"))
        self.assertTrue((self.host / "scripts" / "my_app_deploy.py").is_file())
        self.assertTrue((pack / "tests").is_dir(), "legacy tests/ moved out of the host root")
        self.assertFalse((self.host / "tests").exists())
        self.assertTrue((pack / MANIFEST_FILE).is_file())

        # The recorded proof is what lets a later update retire what no longer ships.
        updated = self.embed(source, "--update", "--allow-dirty")
        self.assertEqual(0, updated.returncode, updated.stdout + updated.stderr)
        self.assertFalse((pack / "tests").exists())
        self.assertFalse((pack / "examples").exists())
        self.assertEqual("NEW VERSION\n", (pack / "harness" / "README.md").read_text(encoding="utf-8"))
        self.assertTrue((self.host / "scripts" / "my_app_deploy.py").is_file())


class ShippingSetUnitTests(unittest.TestCase):
    def test_every_pack_entry_is_either_shipped_or_deliberately_not(self) -> None:
        """A new top-level entry must be decided on, not silently dropped or leaked."""
        for rel in sorted(repo_files(PACK_ROOT)):
            top = rel.split("/")[0]
            self.assertTrue(
                is_allowlisted(rel) or top in NOT_SHIPPED_TOP_LEVEL,
                f"{rel}: add it to SHIPPED_* or NOT_SHIPPED_TOP_LEVEL in scripts/pack_manifest.py",
            )

    def test_local_state_is_denied_but_dotenv_examples_are_not(self) -> None:
        for denied in (".env", ".env.production", "a/.venv/x.py", "node_modules/x.js", "a/b.pyc",
                       "keys/server.pem", ".DS_Store", ".git", ".claude/settings.local.json", "_agent_ops/x.md"):
            self.assertTrue(is_denied(denied), denied)
        for kept in (".env.example", "scripts/embed_pack.py", ".claude/agents/tester.md", ".gitignore"):
            self.assertFalse(is_denied(kept), kept)

    def test_strip_managed_blocks_keeps_every_other_byte(self) -> None:
        self.assertEqual("a\n\nb\n", strip_managed_blocks("a\n\n" + SELF_BRIDGE + "\nb\n"))
        self.assertEqual("a\r\n", strip_managed_blocks("a\r\n\r\n" + SELF_BRIDGE.replace("\n", "\r\n")))
        self.assertEqual("host\n", strip_managed_blocks(SELF_BRIDGE + "\nhost\n"))
        untouched = "no block here\n<!-- AI_AGENT_WORKSPACE_PACK:BEGIN v2 -->\nunterminated\n"
        self.assertEqual(untouched, strip_managed_blocks(untouched))

    def test_content_proof_accepts_a_crlf_checkout_of_a_blob(self) -> None:
        self.assertTrue(content_ids(b"a\nb\n") & content_ids(b"a\r\nb\r\n"))
        self.assertFalse(content_ids(b"a\nb\n") & content_ids(b"a\nc\n"))


if __name__ == "__main__":
    unittest.main()

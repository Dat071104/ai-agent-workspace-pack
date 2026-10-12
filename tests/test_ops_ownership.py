"""Ownership of `_agent_ops/` memory, generated-policy upgrades, and the guards
around `--force`.

The defect these pin: copy a project that has its own memory into another
repository and init reported success, kept the foreign records, and
session_start told the next agent a task from the OTHER project was in progress.

Every fixture lives under the OS temp directory; nothing here writes into this
repository, and the real pack's own `_agent_ops/` is never read.
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
sys.path.insert(0, str(SCRIPTS))

import ops_identity  # noqa: E402
import ops_policy  # noqa: E402

GIT_ID = ("-c", "user.email=owner@example.invalid", "-c", "user.name=Owner Test")


def run(script: Path, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(
        [sys.executable, "-B", str(script), *args],
        cwd=str(cwd), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *GIT_ID, *args], cwd=str(root), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )


def write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def valid_stamp(**changes: object) -> dict:
    """A stamp exactly as init writes it (the schema is strict), with `changes` applied."""

    stamp = {
        "schema": 1,
        "project_id": "ab" * 16,
        "root_commits": ["a" * 40],
        "origin": "project",
        "established": "2026-01-01",
        "established_by": "init",
    }
    stamp.update(changes)
    return stamp


def make_repo(root: Path, marker: str) -> str:
    """A repository with one root commit whose hash depends on `marker`."""

    root.mkdir(parents=True, exist_ok=True)
    write(root / "src" / "app.py", f"def entry():\n    return {marker!r}\n")
    git(root, "init", "-q")
    git(root, "add", "--", "src/app.py")
    committed = git(root, "commit", "-qm", f"root of {marker}")
    assert committed.returncode == 0, committed.stderr
    return git(root, "rev-list", "--max-parents=0", "HEAD").stdout.split()[0]


def init_args(root: Path, *flags: str) -> tuple[str, ...]:
    """Arguments for a fast init: the index and map are not what these tests are about."""

    return ("--target", str(root), "--no-index", "--no-repo-map", *flags)


def snapshot(root: Path, skip: tuple[str, ...] = (".git",)) -> dict[str, bytes]:
    found: dict[str, bytes] = {}
    for current, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in skip]
        for name in files:
            path = Path(current) / name
            found[path.relative_to(root).as_posix()] = path.read_bytes()
    return found


class OpsCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="ops-ownership-")
        self.base = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def init(self, target: Path, *flags: str, script: Path | None = None) -> subprocess.CompletedProcess[str]:
        return run(script or SCRIPTS / "init_project_ops.py", *init_args(target, *flags), cwd=PACK_ROOT)

    def session(self, root: Path) -> subprocess.CompletedProcess[str]:
        tools = root / "_agent_ops" / "tools" / "session_start.py"
        script = tools if tools.is_file() else SCRIPTS / "session_start.py"
        return run(script, "--root", ".", cwd=root)

    def stamp(self, root: Path) -> dict:
        return json.loads((root / "_agent_ops" / "OPS_OWNER.json").read_text(encoding="utf-8"))

    def project_with_memory(self, name: str) -> tuple[Path, str]:
        """A repo that initialized itself and then did real work, as a project does."""

        root = self.base / name
        sha = make_repo(root, name)
        initialized = self.init(root)
        self.assertEqual(0, initialized.returncode, initialized.stderr)
        ops = root / "_agent_ops"
        write(ops / "PROJECT_CONTEXT_CARD.md", f"# Card\nMEMORY OF {name}\n")
        write(ops / "CURRENT_TASK.md", f"## Status\n\n`in-progress`\n\n## Next Concrete Step\n\nFinish {name} feature\n")
        write(ops / "SESSION_BRIEF.md", f"## Original Goal\n\nShip {name}\n\n## Active Task\n\n{name} work\n")
        write(ops / "HANDOFF.md", "## Status\n\nopen\n\n## Date\n\n2026-01-01\n")
        write(ops / "archive" / "IMPLEMENTATION_LOG_2026-01.md", f"# archived {name}\n")
        write(ops / "phase_context_cards" / "PHASE_001_core.md", f"# phase of {name}\n")
        write(ops / "PLAN_BIG_REFACTOR.md", f"# plan of {name}\n")
        write(ops / "LOG_SUMMARY.md", "scratch\n")
        write(ops / "code_index.json", "{}\n")
        return root, sha

    def pack_checkout(self) -> Path:
        """A stand-in for the pack's own repository: it runs ITS init on itself."""

        pack = self.base / "pack-source"
        make_repo(pack, "pack")
        shutil.copytree(SCRIPTS, pack / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(PACK_ROOT / "core-context", pack / "core-context")
        write(pack / "TEAM_ROUTER.md", "# router\n")
        write(pack / "AGENTS.md", "# The pack's own instructions\n")
        return pack

    def foreign_host(self, source: Path) -> Path:
        """The reproduction: copy a project's memory into a different repository."""

        host = self.base / "host"
        make_repo(host, "host-project")
        shutil.copytree(source / "_agent_ops", host / "_agent_ops")
        return host


class ForeignMemoryTests(OpsCase):
    def test_raw_copied_memory_is_refused_by_init_and_flagged_by_session_start(self) -> None:
        source, _ = self.project_with_memory("alpha")
        host = self.foreign_host(source)
        before = snapshot(host)

        refused = self.init(host)
        self.assertEqual(3, refused.returncode, refused.stdout + refused.stderr)
        self.assertIn("BLOCKED", refused.stderr)
        self.assertIn("--reset-memory", refused.stderr)
        self.assertIn("--claim-memory", refused.stderr)
        self.assertNotIn("Done.", refused.stdout)
        self.assertEqual(before, snapshot(host), "a refusal must not write anything")

        session = self.session(host)
        self.assertEqual(0, session.returncode, session.stderr)
        self.assertIn("FOREIGN PROJECT MEMORY", session.stdout)
        self.assertIn("--reset-memory", session.stdout)
        for forbidden in ("TASK IN PROGRESS", "SESSION ESTABLISHED", "CONTINUATION", "Finish alpha feature"):
            self.assertNotIn(forbidden, session.stdout)
        self.assertEqual(before, snapshot(host), "session_start must stay read-only")

    def test_reset_backs_up_every_file_then_starts_fresh_and_is_idempotent(self) -> None:
        source, _ = self.project_with_memory("alpha")
        host = self.foreign_host(source)
        ops = host / "_agent_ops"
        original = snapshot(ops)
        self.assertIn("HANDOFF.md", original)

        reset = self.init(host, "--reset-memory")
        self.assertEqual(0, reset.returncode, reset.stdout + reset.stderr)
        self.assertIn("RESET MEMORY: backed up", reset.stdout)

        backups = [path for path in (ops / "backups").iterdir()]
        self.assertEqual(1, len(backups))
        saved = snapshot(backups[0], skip=())
        self.assertEqual(original, saved, "the backup must hold every original file, byte for byte")
        for name in ("HANDOFF.md", "archive/IMPLEMENTATION_LOG_2026-01.md", "PLAN_BIG_REFACTOR.md",
                     "phase_context_cards/PHASE_001_core.md", "SESSION_BRIEF.md", "CURRENT_TASK.md",
                     "LOG_SUMMARY.md", "code_index.json", "OPS_OWNER.json"):
            self.assertIn(name, saved)

        self.assertFalse((ops / "HANDOFF.md").exists())
        self.assertFalse((ops / "PLAN_BIG_REFACTOR.md").exists())
        self.assertNotIn("MEMORY OF alpha", (ops / "PROJECT_CONTEXT_CARD.md").read_text(encoding="utf-8"))
        host_root = git(host, "rev-list", "--max-parents=0", "HEAD").stdout.split()
        self.assertEqual(host_root, self.stamp(host)["root_commits"])
        self.assertNotEqual(json.loads(saved["OPS_OWNER.json"])["project_id"], self.stamp(host)["project_id"])

        # The backup is neither indexed as code nor committable by accident.
        built = run(SCRIPTS / "init_project_ops.py", "--target", str(host), "--force", cwd=PACK_ROOT)
        self.assertEqual(0, built.returncode, built.stderr)
        index = json.loads((ops / "code_index.json").read_text(encoding="utf-8"))
        self.assertEqual(["src/app.py"], sorted(index["files"]))
        tracked = git(host, "status", "--porcelain", "--untracked-files=all").stdout
        self.assertNotIn("backups", tracked)
        ignored = git(host, "check-ignore", "-q", f"_agent_ops/backups/{backups[0].name}/tools/session_start.py")
        self.assertEqual(0, ignored.returncode)
        self.assertNotEqual(0, git(host, "check-ignore", "-q", "_agent_ops/OPS_OWNER.json").returncode)
        scan = run(SCRIPTS / "scan_deps.py", "--root", str(host), "--output", "json", cwd=PACK_ROOT)
        self.assertEqual(["src/app.py"], sorted(json.loads(scan.stdout)["graph"]))

        # Re-running the same command, or a plain init, changes nothing further.
        after_reset = snapshot(host)
        again = self.init(host, "--reset-memory")
        self.assertEqual(0, again.returncode, again.stderr)
        self.assertIn("nothing done", again.stdout)
        self.assertEqual(1, len(list((ops / "backups").iterdir())))
        plain = self.init(host)
        self.assertEqual(0, plain.returncode, plain.stderr)
        self.assertEqual(
            {k: v for k, v in after_reset.items() if not k.startswith("_agent_ops/tools/")},
            {k: v for k, v in snapshot(host).items() if not k.startswith("_agent_ops/tools/")},
        )
        self.assertIn("Owned by this project", self.session(host).stdout)

    def test_claim_memory_adopts_the_records_as_this_projects(self) -> None:
        source, _ = self.project_with_memory("alpha")
        host = self.foreign_host(source)
        old_id = self.stamp(host)["project_id"]

        claimed = self.init(host, "--claim-memory")
        self.assertEqual(0, claimed.returncode, claimed.stdout + claimed.stderr)
        self.assertIn("CLAIMED existing memory", claimed.stdout)
        ops = host / "_agent_ops"
        self.assertIn("MEMORY OF alpha", (ops / "PROJECT_CONTEXT_CARD.md").read_text(encoding="utf-8"))
        self.assertTrue((ops / "HANDOFF.md").is_file())
        self.assertFalse((ops / "backups").exists())
        stamp = self.stamp(host)
        self.assertEqual(git(host, "rev-list", "--max-parents=0", "HEAD").stdout.split(), stamp["root_commits"])
        self.assertEqual(old_id, stamp["previous_project_id"])
        self.assertIn("Owned by this project", self.session(host).stdout)

    def test_a_bound_stamp_from_the_pack_source_is_foreign_even_without_git(self) -> None:
        host = self.base / "plain-dir"
        write(host / "src" / "app.py", "def entry():\n    return 1\n")
        ops = host / "_agent_ops"
        write(ops / "PROJECT_CONTEXT_CARD.md", "# the pack's own card\n")
        write(ops / "OPS_OWNER.json", json.dumps(valid_stamp(origin="pack-source")))

        self.assertIn("FOREIGN PROJECT MEMORY", self.session(host).stdout)
        refused = self.init(host)
        self.assertEqual(3, refused.returncode, refused.stdout)

    def test_unreadable_history_is_unverifiable_not_foreign(self) -> None:
        host = self.base / "zip-download"
        write(host / "src" / "app.py", "def entry():\n    return 1\n")
        ops = host / "_agent_ops"
        write(ops / "PROJECT_CONTEXT_CARD.md", "# a real project's card\n")
        write(ops / "OPS_OWNER.json", json.dumps(valid_stamp(project_id="cd" * 16, root_commits=["b" * 40])))

        session = self.session(host)
        self.assertIn("UNVERIFIED", session.stdout)
        self.assertNotIn("FOREIGN PROJECT MEMORY", session.stdout)
        refused = self.init(host)
        self.assertEqual(3, refused.returncode)
        self.assertIn("cannot be verified", refused.stderr)
        self.assertEqual(0, self.init(host, "--claim-memory").returncode)
        self.assertEqual([], self.stamp(host)["root_commits"])

        write(ops / "OPS_OWNER.json", "{not json")
        self.assertEqual(3, self.init(host).returncode)

    def test_a_shallow_clone_cannot_prove_ownership_either_way(self) -> None:
        source, _ = self.project_with_memory("alpha")
        git(source, "add", "--", "_agent_ops")
        git(source, "commit", "-qm", "track memory")
        write(source / "src" / "more.py", "def more():\n    return 2\n")
        git(source, "add", "--", "src/more.py")
        git(source, "commit", "-qm", "second")
        shallow = self.base / "shallow"
        cloned = subprocess.run(
            ["git", "clone", "-q", "--depth", "1", source.as_uri(), str(shallow)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
        )
        self.assertEqual(0, cloned.returncode, cloned.stderr)

        verdict = ops_identity.assess(shallow, shallow / "_agent_ops")
        self.assertEqual(ops_identity.UNVERIFIABLE, verdict.state, verdict.detail)
        self.assertIn("shallow", verdict.detail)


class OwnedMemoryTests(OpsCase):
    def test_a_valid_clone_keeps_its_memory(self) -> None:
        source, root_sha = self.project_with_memory("alpha")
        git(source, "add", "--", "_agent_ops")
        self.assertEqual(0, git(source, "commit", "-qm", "track memory").returncode)
        clone = self.base / "clone-elsewhere"
        cloned = subprocess.run(
            ["git", "clone", "-q", str(source), str(clone)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
        )
        self.assertEqual(0, cloned.returncode, cloned.stderr)
        write(clone / "src" / "new.py", "def new():\n    return 3\n")
        git(clone, "add", "--", "src/new.py")
        self.assertEqual(0, git(clone, "commit", "-qm", "diverge: different HEAD").returncode)
        self.assertNotEqual(git(source, "rev-parse", "HEAD").stdout, git(clone, "rev-parse", "HEAD").stdout)
        self.assertEqual([root_sha], self.stamp(clone)["root_commits"])

        session = self.session(clone)
        self.assertIn("Owned by this project", session.stdout)
        self.assertNotIn("FOREIGN", session.stdout)
        kept = self.init(clone)
        self.assertEqual(0, kept.returncode, kept.stdout + kept.stderr)
        self.assertIn("OWNERSHIP: OWNED", kept.stdout)
        self.assertIn("MEMORY OF alpha", (clone / "_agent_ops" / "PROJECT_CONTEXT_CARD.md").read_text(encoding="utf-8"))
        self.assertFalse((clone / "_agent_ops" / "backups").exists())

    def test_a_repository_without_commits_is_unbound_until_its_first_commit(self) -> None:
        root = self.base / "fresh"
        write(root / "src" / "app.py", "def entry():\n    return 1\n")
        git(root, "init", "-q")

        first = self.init(root)
        self.assertEqual(0, first.returncode, first.stderr)
        stamp = self.stamp(root)
        self.assertEqual([], stamp["root_commits"])
        self.assertIn("names no root commit", self.session(root).stdout)

        git(root, "add", "--", "src/app.py")
        self.assertEqual(0, git(root, "commit", "-qm", "first commit").returncode)
        self.assertIn("names no root commit", self.session(root).stdout)

        bound = self.init(root)
        self.assertEqual(0, bound.returncode, bound.stderr)
        self.assertIn("BOUND to this repository's history", bound.stdout)
        rebound = self.stamp(root)
        self.assertEqual(stamp["project_id"], rebound["project_id"])
        self.assertEqual(git(root, "rev-list", "--max-parents=0", "HEAD").stdout.split(), rebound["root_commits"])
        self.assertIn("Owned by this project", self.session(root).stdout)

    def test_a_directory_without_git_stays_unbound_and_reinitializes_cleanly(self) -> None:
        root = self.base / "no-git"
        write(root / "src" / "app.py", "def entry():\n    return 1\n")
        self.assertEqual(0, self.init(root).returncode)
        write(root / "_agent_ops" / "PROJECT_CONTEXT_CARD.md", "# kept\n")
        again = self.init(root)
        self.assertEqual(0, again.returncode, again.stderr)
        self.assertEqual([], self.stamp(root)["root_commits"])
        self.assertEqual("# kept\n", (root / "_agent_ops" / "PROJECT_CONTEXT_CARD.md").read_text(encoding="utf-8"))


class LegacyMemoryTests(OpsCase):
    def legacy_host(self, records: dict[str, str], extra: dict[str, str] | None = None) -> Path:
        host = self.base / "legacy-host"
        make_repo(host, "legacy")
        for name, text in records.items():
            write(host / "_agent_ops" / name, text)
        for name, text in (extra or {}).items():
            write(host / name, text)
        return host

    PACK_RECORDS = {
        "PROJECT_CONTEXT_CARD.md": "# Card\nRUNTIME_TOOLS in scripts/init_project_ops.py lists tools.\n",
        "IMPLEMENTATION_LOG.md": "Fixed embed_pack.py and migrate_pack.py; tests in test_workspace_tools.\n",
        "HANDOFF.md": "## Status\n\nopen\n",
    }

    def test_unstamped_memory_that_describes_the_pack_is_refused(self) -> None:
        host = self.legacy_host(self.PACK_RECORDS)
        before = snapshot(host)

        refused = self.init(host)
        self.assertEqual(3, refused.returncode, refused.stdout + refused.stderr)
        self.assertIn("workspace pack's own memory", refused.stderr)
        self.assertIn("embed_pack.py", refused.stderr)
        self.assertIn("--claim-memory", refused.stderr)
        self.assertEqual(before, snapshot(host))
        self.assertIn("FOREIGN PROJECT MEMORY", self.session(host).stdout)

        self.assertEqual(0, self.init(host, "--reset-memory").returncode)
        self.assertEqual(1, len(list((host / "_agent_ops" / "backups").iterdir())))
        self.assertFalse((host / "_agent_ops" / "HANDOFF.md").exists())

    def test_unstamped_pack_memory_can_be_claimed_explicitly(self) -> None:
        host = self.legacy_host(self.PACK_RECORDS)
        self.assertEqual(0, self.init(host, "--claim-memory").returncode)
        self.assertEqual("claim-memory", self.stamp(host)["established_by"])
        self.assertTrue((host / "_agent_ops" / "HANDOFF.md").is_file())

    def test_an_ordinary_legacy_project_is_refused_until_the_user_chooses(self) -> None:
        """Round 1 auto-claimed it because it did not mention the pack. Absence of
        that signature is not proof of ownership, so a person must choose."""
        host = self.legacy_host(
            {
                "PROJECT_CONTEXT_CARD.md": "# Card\nBilling service MEMORY MARKER\n",
                "IMPLEMENTATION_LOG.md": "Ran embed_pack.py once to install the pack.\n",
            }
        )
        before = snapshot(host)
        session = self.session(host)
        self.assertIn("UNSTAMPED (legacy)", session.stdout)
        self.assertIn("embed_pack.py (in IMPLEMENTATION_LOG.md)", session.stdout)  # the evidence is shown
        self.assertNotIn("FOREIGN", session.stdout)

        refused = self.init(host)
        self.assertEqual(3, refused.returncode, refused.stdout + refused.stderr)
        self.assertIn("nothing proves it is this project's", refused.stderr)
        self.assertNotIn("workspace pack's own memory", refused.stderr)
        self.assertIn("--claim-memory", refused.stderr)
        self.assertIn("--reset-memory", refused.stderr)
        self.assertEqual(before, snapshot(host), "a refusal must not write anything")

        claimed = self.init(host, "--claim-memory")
        self.assertEqual(0, claimed.returncode, claimed.stdout + claimed.stderr)
        self.assertIn("CLAIMED existing memory (claim-memory)", claimed.stdout)
        self.assertIn("MEMORY MARKER", (host / "_agent_ops" / "PROJECT_CONTEXT_CARD.md").read_text(encoding="utf-8"))
        self.assertEqual("claim-memory", self.stamp(host)["established_by"])
        self.assertFalse((host / "_agent_ops" / "backups").exists())

    def test_a_project_that_merely_uses_the_pack_is_not_mistaken_for_it(self) -> None:
        """Naming the pack folder, `@start-here`, a team, `init_project_ops.py`
        and `TEAM_ROUTER.md` is what every embedded install's log does."""
        host = self.legacy_host(
            {
                "IMPLEMENTATION_LOG.md": (
                    "Bootstrapped with ai-agent-workspace-pack/scripts/init_project_ops.py after @start-here.\n"
                    "Routed to build-team via TEAM_ROUTER.md and START_HERE.md; PACK_VERSION recorded.\n"
                ),
                "PROJECT_CONTEXT_CARD.md": "# Card\nPayments API MEMORY MARKER\n",
            }
        )
        verdict = ops_identity.assess(host, host / "_agent_ops")
        self.assertEqual(ops_identity.LEGACY, verdict.state)
        self.assertFalse(verdict.suspect, verdict.evidence)
        # Not mistaken for the pack's memory -- but not proven to be this project's either.
        refused = self.init(host)
        self.assertEqual(3, refused.returncode, refused.stdout + refused.stderr)
        self.assertNotIn("workspace pack's own memory", refused.stderr)

    def test_pack_signatures_are_expected_where_the_root_is_itself_a_pack(self) -> None:
        host = self.legacy_host(
            self.PACK_RECORDS,
            extra={"TEAM_ROUTER.md": "# router\n", "core-context/.keep": "", "scripts/init_project_ops.py": "x = 1\n"},
        )
        verdict = ops_identity.assess(host, host / "_agent_ops")
        self.assertGreaterEqual(len(verdict.evidence), ops_identity.PACK_EVIDENCE_THRESHOLD)
        self.assertFalse(verdict.suspect)
        # Pack names are expected here, so the message is the generic one; an
        # unstamped memory still needs an explicit choice.
        refused = self.init(host)
        self.assertEqual(3, refused.returncode, refused.stdout + refused.stderr)
        self.assertNotIn("workspace pack's own memory", refused.stderr)
        self.assertEqual(0, self.init(host, "--claim-memory").returncode)

    def test_legacy_generated_policy_is_not_scanned_as_evidence(self) -> None:
        """SESSION_PROTOCOL.md of every project names tools and scripts."""
        host = self.legacy_host(
            {
                "PROJECT_CONTEXT_CARD.md": "# Card\n",
                "SESSION_PROTOCOL.md": "embed_pack.py migrate_pack.py RUNTIME_TOOLS test_workspace_tools\n",
            }
        )
        self.assertEqual((), ops_identity.legacy_pack_evidence(host / "_agent_ops"))


class PackSourceTests(OpsCase):
    def test_the_pack_source_stamps_its_own_memory_and_writes_no_self_bridge(self) -> None:
        pack = self.pack_checkout()
        write(pack / "_agent_ops" / "PROJECT_CONTEXT_CARD.md", "# the pack's own card\n")
        write(pack / "_agent_ops" / "OPS_OWNER.json", json.dumps(valid_stamp(project_id="ef" * 16, root_commits=["c" * 40])))
        agents = (pack / "AGENTS.md").read_bytes()
        script = pack / "scripts" / "init_project_ops.py"

        initialized = run(script, "--target", str(pack), "--no-index", "--no-repo-map", cwd=pack)
        self.assertEqual(0, initialized.returncode, initialized.stdout + initialized.stderr)
        self.assertIn("CLAIMED existing memory (pack-source)", initialized.stdout)
        self.assertEqual("pack-source", self.stamp(pack)["origin"])
        self.assertIn("NOT APPLICABLE", initialized.stdout)
        self.assertEqual(agents, (pack / "AGENTS.md").read_bytes())
        self.assertNotIn("workspace pack itself", (pack / "AGENTS.md").read_text(encoding="utf-8"))

        for flag in ("--check-agents-bridge", "--install-agents-bridge"):
            result = run(script, "--target", str(pack), "--no-index", "--no-repo-map", flag, cwd=pack)
            self.assertEqual(0, result.returncode, flag + result.stdout + result.stderr)
            self.assertIn("NOT APPLICABLE", result.stdout)
            self.assertNotIn("missing", result.stdout.lower())
            self.assertEqual(agents, (pack / "AGENTS.md").read_bytes())

    def test_a_copy_of_the_pack_inside_a_host_does_not_get_pack_source_treatment(self) -> None:
        """Its memory is the pack's, so the host must not inherit it."""
        pack = self.pack_checkout()
        self.assertEqual(0, run(pack / "scripts" / "init_project_ops.py", "--target", str(pack), "--no-index", "--no-repo-map", cwd=pack).returncode)
        host = self.base / "host-with-pack"
        make_repo(host, "host")
        copied = host / "ai-agent-workspace-pack"
        shutil.copytree(pack, copied, ignore=shutil.ignore_patterns(".git"))
        refused = run(copied / "scripts" / "init_project_ops.py", "--target", str(host), "--no-index", "--no-repo-map", cwd=host)
        self.assertEqual(3, refused.returncode, refused.stdout + refused.stderr)
        self.assertIn("BLOCKED", refused.stderr)
        self.assertIn("--reset-memory", refused.stderr)


class ForceGuardTests(OpsCase):
    def embedded_host(self) -> Path:
        host = self.base / "adapter-host"
        write(host / "src" / "app.py", "def entry():\n    return 1\n")
        pack = host / "ai-agent-workspace-pack"
        write(pack / "TEAM_ROUTER.md", "# marker\n")
        write(pack / "core-context" / ".keep", "")
        write(pack / "scripts" / "init_project_ops.py", "def pack_tool():\n    pass\n")
        write(pack / ".claude" / "agents" / "tester.md", "---\nname: tester\n---\n\nFollow `tester-team/SKILL.md`.\n")
        return host

    def test_force_never_overwrites_a_host_owned_adapter(self) -> None:
        host = self.embedded_host()
        args = ("--embedded-folder", "ai-agent-workspace-pack")
        self.assertEqual(0, self.init(host, *args).returncode)
        adapter = host / ".claude" / "agents" / "tester.md"
        generated = adapter.read_text(encoding="utf-8")
        self.assertIn("AI_AGENT_WORKSPACE_PACK:ADAPTER", generated)

        owned = "---\nname: tester\n---\n\nHost-written tester. Do not touch.\n"
        adapter.write_text(owned, encoding="utf-8")
        forced = self.init(host, *args, "--force")
        self.assertEqual(0, forced.returncode, forced.stderr)
        self.assertIn("SKIP host-owned adapter", forced.stdout)
        self.assertEqual(owned, adapter.read_text(encoding="utf-8"))

        # A marked (pack-generated) adapter is the pack's to refresh.
        adapter.write_text(generated.replace("Follow", "Edited"), encoding="utf-8")
        refreshed = self.init(host, *args)
        self.assertEqual(0, refreshed.returncode, refreshed.stderr)
        self.assertEqual(generated, adapter.read_text(encoding="utf-8"))

    def test_force_never_overwrites_project_memory(self) -> None:
        root = self.base / "force-project"
        make_repo(root, "force")
        self.assertEqual(0, self.init(root).returncode)
        ops = root / "_agent_ops"
        for name in ("PROJECT_CONTEXT_CARD.md", "SESSION_BRIEF.md", "CURRENT_TASK.md", "DECISION_LOG.md",
                     "IMPLEMENTATION_LOG.md", "RISK_REGISTER.md", "PHASE_ROADMAP.md"):
            write(ops / name, f"# {name}\nHARD-WON MEMORY\n")

        forced = self.init(root, "--force")
        self.assertEqual(0, forced.returncode, forced.stderr)
        self.assertIn("--force regenerated derived files only", forced.stdout)
        for name in ("PROJECT_CONTEXT_CARD.md", "SESSION_BRIEF.md", "CURRENT_TASK.md", "DECISION_LOG.md",
                     "IMPLEMENTATION_LOG.md", "RISK_REGISTER.md", "PHASE_ROADMAP.md"):
            self.assertIn("HARD-WON MEMORY", (ops / name).read_text(encoding="utf-8"), name)

    def test_force_still_regenerates_the_derived_map_and_index(self) -> None:
        root = self.base / "derived"
        make_repo(root, "derived")
        self.assertEqual(0, run(SCRIPTS / "init_project_ops.py", "--target", str(root), cwd=PACK_ROOT).returncode)
        ops = root / "_agent_ops"
        (ops / "REPO_MAP.md").write_text("STALE\n", encoding="utf-8")
        (ops / "code_index.json").write_text("{}\n", encoding="utf-8")
        forced = run(SCRIPTS / "init_project_ops.py", "--target", str(root), "--force", cwd=PACK_ROOT)
        self.assertEqual(0, forced.returncode, forced.stderr)
        self.assertNotEqual("STALE\n", (ops / "REPO_MAP.md").read_text(encoding="utf-8"))
        self.assertIn("src/app.py", (ops / "code_index.json").read_text(encoding="utf-8"))


class PolicyUpgradeTests(OpsCase):
    def make_templates(self, version: str) -> Path:
        templates = self.base / f"templates-{version}"
        for template in ops_policy.POLICY_TEMPLATES:
            write(templates / template, f"# {template} {version}\nPath: `_agent_ops/tools`\n")
        return templates

    def refresh(self, ops: Path, templates: Path, **kwargs) -> dict[str, ops_policy.PolicyResult]:
        results = ops_policy.refresh_generated_policy(ops, templates, "_agent_ops", **kwargs)
        return {result.name: result for result in results}

    def test_an_untouched_generated_file_follows_the_pack_and_a_customized_one_does_not(self) -> None:
        ops = self.base / "p" / "_agent_ops"
        ops.mkdir(parents=True)
        first = self.refresh(ops, self.make_templates("v1"))
        self.assertEqual({"WRITE"}, {r.action for r in first.values()})

        second = self.refresh(ops, self.make_templates("v2"))
        self.assertEqual({"REFRESH"}, {r.action for r in second.values()})
        self.assertIn("SESSION_PROTOCOL.template.md v2", (ops / "SESSION_PROTOCOL.md").read_text(encoding="utf-8"))

        (ops / "OPERATING_RULES.md").write_text("# our own rules\n", encoding="utf-8")
        third = self.refresh(ops, self.make_templates("v3"))
        self.assertEqual("KEEP-CUSTOMIZED", third["OPERATING_RULES.md"].action)
        self.assertIn("customized, not refreshed", third["OPERATING_RULES.md"].message)
        self.assertEqual("# our own rules\n", (ops / "OPERATING_RULES.md").read_text(encoding="utf-8"))
        self.assertEqual("REFRESH", third["SESSION_PROTOCOL.md"].action)

        # Line endings must not make an unedited file look edited.
        raw = (ops / "INDEX.md").read_bytes()
        (ops / "INDEX.md").write_bytes(raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        fourth = self.refresh(ops, self.make_templates("v4"))
        self.assertEqual("REFRESH", fourth["INDEX.md"].action)

    def test_unrecorded_legacy_files_are_refreshed_only_when_provably_the_packs(self) -> None:
        ops = self.base / "legacy" / "_agent_ops"
        templates = self.make_templates("v2")
        write(ops / "SESSION_PROTOCOL.md", "# SESSION_PROTOCOL.template.md v2\nPath: `_agent_ops/tools`\n")
        write(ops / "OPERATING_RULES.md", "# something nobody can account for\n")
        write(ops / "INDEX.md", "# INDEX.template.md v1\nPath: `_agent_ops/tools`\n")

        results = self.refresh(ops, templates)
        self.assertEqual("RECORD", results["SESSION_PROTOCOL.md"].action)
        self.assertEqual("KEEP-UNPROVEN", results["OPERATING_RULES.md"].action)
        self.assertEqual("KEEP-UNPROVEN", results["INDEX.md"].action)
        self.assertEqual("# something nobody can account for\n", (ops / "OPERATING_RULES.md").read_text(encoding="utf-8"))
        self.assertEqual(ops_policy.digest((templates / "SESSION_PROTOCOL.template.md").read_text(encoding="utf-8")),
                         ops_policy.read_manifest(ops)["SESSION_PROTOCOL.md"])
        self.assertNotIn("OPERATING_RULES.md", ops_policy.read_manifest(ops))

        # Unrecorded files stay unproven on every later run, never silently adopted.
        again = self.refresh(ops, templates)
        self.assertEqual("KEEP-UNPROVEN", again["OPERATING_RULES.md"].action)

    def test_an_unrecorded_file_matching_pack_history_is_refreshed(self) -> None:
        history = self.base / "pack-history"
        history.mkdir()
        git(history, "init", "-q")
        for version in ("v1", "v2"):
            for template, text in ((t, f"# {t} {version}\nPath: `_agent_ops/tools`\n") for t in ops_policy.POLICY_TEMPLATES):
                write(history / "core-context" / template, text)
            git(history, "add", "--", "core-context")
            self.assertEqual(0, git(history, "commit", "-qm", version).returncode)
        ops = self.base / "old-install" / "_agent_ops"
        write(ops / "SESSION_PROTOCOL.md", "# SESSION_PROTOCOL.template.md v1\nPath: `_agent_ops/tools`\n")
        write(ops / "OPERATING_RULES.md", "# OPERATING_RULES.template.md v1\nPath: `_agent_ops/tools`\n# hand edit\n")
        templates = history / "core-context"

        without_history = self.refresh(ops, templates)
        self.assertEqual("KEEP-UNPROVEN", without_history["SESSION_PROTOCOL.md"].action)
        shutil.rmtree(ops)
        write(ops / "SESSION_PROTOCOL.md", "# SESSION_PROTOCOL.template.md v1\nPath: `_agent_ops/tools`\n")
        write(ops / "OPERATING_RULES.md", "# OPERATING_RULES.template.md v1\nPath: `_agent_ops/tools`\n# hand edit\n")

        with_history = self.refresh(ops, templates, history_root=history)
        self.assertEqual("REFRESH", with_history["SESSION_PROTOCOL.md"].action)
        self.assertEqual("KEEP-UNPROVEN", with_history["OPERATING_RULES.md"].action)
        self.assertIn("v2", (ops / "SESSION_PROTOCOL.md").read_text(encoding="utf-8"))
        self.assertIn("# hand edit", (ops / "OPERATING_RULES.md").read_text(encoding="utf-8"))

    def test_a_later_pack_revision_reaches_an_installed_project_through_init(self) -> None:
        project = self.base / "installed"
        make_repo(project, "installed")
        self.assertEqual(0, self.init(project).returncode)
        ops = project / "_agent_ops"
        self.assertEqual(
            {"INDEX.md", "OPERATING_RULES.md", "SESSION_PROTOCOL.md"}, set(ops_policy.read_manifest(ops))
        )

        later = self.base / "pack-v2"
        shutil.copytree(SCRIPTS, later / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(PACK_ROOT / "core-context", later / "core-context")
        for name in ("SESSION_PROTOCOL.template.md", "OPERATING_RULES.template.md"):
            path = later / "core-context" / name
            path.write_text(path.read_text(encoding="utf-8") + "\nA rule added by pack v2.\n", encoding="utf-8")
        (ops / "OPERATING_RULES.md").write_text("# our customized rules\n", encoding="utf-8")

        update = self.init(project, script=later / "scripts" / "init_project_ops.py")
        self.assertEqual(0, update.returncode, update.stdout + update.stderr)
        self.assertIn("REFRESH policy", update.stdout)
        self.assertIn("A rule added by pack v2.", (ops / "SESSION_PROTOCOL.md").read_text(encoding="utf-8"))
        self.assertIn("KEEP customized, not refreshed", update.stdout)
        self.assertEqual("# our customized rules\n", (ops / "OPERATING_RULES.md").read_text(encoding="utf-8"))

    def test_init_in_a_git_pack_recognizes_unrecorded_policy_from_an_older_revision(self) -> None:
        """The path a project installed before the manifest existed takes: no
        record of what init wrote, so history is the only proof."""
        pack = self.base / "pack-with-history"
        shutil.copytree(SCRIPTS, pack / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(PACK_ROOT / "core-context", pack / "core-context")
        git(pack, "init", "-q")
        git(pack, "add", "--", "scripts", "core-context")
        self.assertEqual(0, git(pack, "commit", "-qm", "revision one").returncode)
        script = pack / "scripts" / "init_project_ops.py"

        project = self.base / "legacy-install"
        make_repo(project, "legacy-install")
        self.assertEqual(0, self.init(project, script=script).returncode)
        ops = project / "_agent_ops"
        (ops / "OPS_POLICY.json").unlink()  # an install from before the manifest existed
        (ops / "OPERATING_RULES.md").write_text(
            (ops / "OPERATING_RULES.md").read_text(encoding="utf-8") + "\nOur own house rule.\n", encoding="utf-8"
        )

        for name in ("SESSION_PROTOCOL.template.md", "OPERATING_RULES.template.md", "INDEX.template.md"):
            path = pack / "core-context" / name
            path.write_text(path.read_text(encoding="utf-8") + "\nAdded by revision two.\n", encoding="utf-8")
        git(pack, "add", "--", "core-context")
        self.assertEqual(0, git(pack, "commit", "-qm", "revision two").returncode)

        update = self.init(project, script=script)
        self.assertEqual(0, update.returncode, update.stdout + update.stderr)
        self.assertIn("matched an earlier pack rendering", update.stdout)
        self.assertIn("Added by revision two.", (ops / "SESSION_PROTOCOL.md").read_text(encoding="utf-8"))
        self.assertIn("Added by revision two.", (ops / "INDEX.md").read_text(encoding="utf-8"))
        self.assertIn("KEEP unproven, not refreshed", update.stdout)
        kept = (ops / "OPERATING_RULES.md").read_text(encoding="utf-8")
        self.assertIn("Our own house rule.", kept)
        self.assertNotIn("Added by revision two.", kept)

    def test_the_init_command_a_runtime_tool_prints_matches_the_install_layout(self) -> None:
        embedded = self.base / "embedded-host"
        for name in ("TEAM_ROUTER.md", "core-context/.keep", "scripts/init_project_ops.py"):
            write(embedded / "ai-agent-workspace-pack" / name, "x\n")
        hint = ops_identity.init_command_hint
        self.assertEqual(
            "python ai-agent-workspace-pack/scripts/init_project_ops.py --target . --reset-memory",
            hint(embedded, embedded / "ai-agent-workspace-pack" / "_agent_ops", "--reset-memory"),
        )
        plain = self.base / "plain-host"
        plain.mkdir()
        self.assertEqual(
            "python <pack>/scripts/init_project_ops.py --target . --claim-memory",
            hint(plain, plain / "_agent_ops", "--claim-memory"),
        )
        self.assertIn("--ops-folder tools/_agent_ops", hint(plain, plain / "tools" / "_agent_ops", "--claim-memory"))
        for name in ("TEAM_ROUTER.md", "core-context/.keep", "scripts/init_project_ops.py"):
            write(plain / name, "x\n")
        self.assertEqual(
            "python scripts/init_project_ops.py --target . --reset-memory",
            hint(plain, plain / "_agent_ops", "--reset-memory"),
        )

    def test_an_existing_ops_gitignore_learns_the_backup_folder(self) -> None:
        project = self.base / "old-gitignore"
        make_repo(project, "old")
        self.assertEqual(0, self.init(project).returncode)
        ignore = project / "_agent_ops" / ".gitignore"
        ignore.write_text(ignore.read_text(encoding="utf-8").replace("backups/\n", ""), encoding="utf-8")
        self.assertNotIn("backups/", ignore.read_text(encoding="utf-8").splitlines())

        updated = self.init(project)
        self.assertIn("backups/", ignore.read_text(encoding="utf-8").splitlines())
        self.assertIn("UPDATE:", updated.stdout)
        self.init(project)
        self.assertEqual(1, ignore.read_text(encoding="utf-8").splitlines().count("backups/"))


if __name__ == "__main__":
    unittest.main()

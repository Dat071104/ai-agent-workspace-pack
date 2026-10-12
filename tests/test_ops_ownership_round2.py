"""Memory ownership, round 2: ownership must be PROVEN, never presumed.

Four defects, each pinned by a test that fails when its fix is removed:

1. session_start stopped early only for provably foreign memory, so unverifiable,
   unstamped or damaged-stamp memory still printed "TASK IN PROGRESS" and
   "Resume from its Next Concrete Step" under an UNVERIFIED banner.
2. `OPS_OWNER.json` containing `{}` read as "made before the first commit", so it
   was reported as owned and init would bind it. The stamp schema is now strict.
3. Unstamped memory that did not mention the pack was auto-claimed by init.
   Absence of a pack signature is not proof of ownership.
4. `--reset-memory` verified its backup by file name and size before deleting the
   originals, so a same-size content difference passed.

Fixtures live under the OS temp directory.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "scripts"))

import ops_gate  # noqa: E402
import ops_identity  # noqa: E402
from test_ops_ownership import SCRIPTS, OpsCase, git, make_repo, run, snapshot, valid_stamp, write  # noqa: E402

# Text that only the memory of project "alpha" (see OpsCase.project_with_memory) contains.
ALPHA_ONLY = (
    "TASK IN PROGRESS", "Resume from", "CONTINUATION", "SESSION ESTABLISHED", "TASK BLOCKED",
    "Finish alpha feature", "Ship alpha", "alpha work", "MEMORY OF alpha",
    "## Session Continuity", "## Current Task", "## Session Brief", "## Memory Freshness", "## Repo Map",
)
RULES = "# Card\n## Business Rules\n- Rule: refunds within 14 days -> Accept when the order is under 14 days old\nMEMORY OF alpha\n"


def flip_one_byte(path: Path) -> None:
    """Same length, different content: what a size-only comparison cannot see.

    Computed from the bytes on disk rather than typed as a literal, because a
    text file's size depends on the platform's line endings.
    """

    data = path.read_bytes()
    path.write_bytes(bytes([data[0] ^ 1]) + data[1:])


def can_symlink(directory: Path) -> bool:
    target = directory / "link-probe-target"
    target.write_text("x", encoding="utf-8")
    try:
        os.symlink(target, directory / "link-probe")
    except (OSError, NotImplementedError):
        return False
    return True


class UnprovenMemoryIsWithheldTests(OpsCase):
    """session_start prints the ownership block and the init commands -- and nothing from the records."""

    def withheld(self, root: Path, heading: str) -> str:
        before = snapshot(root)
        result = self.session(root)
        self.assertEqual(0, result.returncode, result.stderr)
        out = result.stdout
        self.assertEqual(before, snapshot(root), "session_start must stay read-only")
        self.assertIn(heading, out)
        for flag in ("--claim-memory", "--reset-memory"):
            self.assertIn(f"init_project_ops.py --target . {flag}", out)
        for text in ALPHA_ONLY:
            self.assertNotIn(text, out)
        return out

    def copy_of_alpha(self, name: str) -> Path:
        source, _ = self.project_with_memory("alpha")
        copy = self.base / name
        shutil.copytree(source, copy, ignore=shutil.ignore_patterns(".git"))
        return copy

    def test_a_copy_without_git_cannot_prove_ownership(self) -> None:
        out = self.withheld(self.copy_of_alpha("zip-download"), "UNVERIFIED PROJECT MEMORY -- DO NOT RESUME")
        self.assertIn("not a git repository", out)

    def test_a_repository_without_commits_cannot_prove_ownership(self) -> None:
        host = self.copy_of_alpha("no-commits-yet")
        git(host, "init", "-q")
        out = self.withheld(host, "UNVERIFIED PROJECT MEMORY -- DO NOT RESUME")
        self.assertIn("no commits yet", out)

    def test_a_shallow_clone_cannot_prove_ownership(self) -> None:
        source, _ = self.project_with_memory("alpha")
        git(source, "add", "--", "_agent_ops")
        git(source, "commit", "-qm", "track memory")
        write(source / "src" / "more.py", "def more():\n    return 2\n")
        git(source, "add", "--", "src/more.py")
        git(source, "commit", "-qm", "second")
        shallow = self.base / "shallow"
        cloned = git(self.base, "clone", "-q", "--depth", "1", source.as_uri(), str(shallow))
        self.assertEqual(0, cloned.returncode, cloned.stderr)
        for name in ("CURRENT_TASK.md", "SESSION_BRIEF.md"):  # session-scoped, so never cloned
            write(shallow / "_agent_ops" / name, (source / "_agent_ops" / name).read_text(encoding="utf-8"))
        out = self.withheld(shallow, "UNVERIFIED PROJECT MEMORY -- DO NOT RESUME")
        self.assertIn("shallow clone", out)

    def test_unstamped_memory_cannot_prove_ownership(self) -> None:
        source, _ = self.project_with_memory("alpha")
        (source / "_agent_ops" / "OPS_OWNER.json").unlink()
        out = self.withheld(source, "UNVERIFIED PROJECT MEMORY -- DO NOT RESUME")
        self.assertIn("UNSTAMPED (legacy)", out)
        self.assertNotIn("FOREIGN", out)

    def test_a_damaged_stamp_cannot_prove_ownership(self) -> None:
        source, _ = self.project_with_memory("alpha")
        write(source / "_agent_ops" / "OPS_OWNER.json", "{}")
        out = self.withheld(source, "UNVERIFIED PROJECT MEMORY -- DO NOT RESUME")
        self.assertIn("OPS_OWNER.json is unusable: missing", out)
        self.assertNotIn("Owned by this project", out)

    def test_owned_memory_still_resumes(self) -> None:
        source, _ = self.project_with_memory("alpha")
        out = self.session(source).stdout
        self.assertIn("Owned by this project", out)
        for text in ("CONTINUATION", "Finish alpha feature", "## Session Continuity", "## Current Task"):
            self.assertIn(text, out)

    def test_a_valid_unbound_stamp_and_a_folder_with_no_memory_behave_as_before(self) -> None:
        fresh = self.base / "fresh"
        write(fresh / "src" / "app.py", "def entry():\n    return 1\n")
        git(fresh, "init", "-q")
        self.assertEqual(0, self.init(fresh).returncode)
        unbound = self.session(fresh).stdout
        self.assertIn("names no root commit", unbound)
        self.assertIn("## Session Continuity", unbound)

        empty = self.base / "empty-ops"
        (empty / "_agent_ops").mkdir(parents=True)
        new = self.session(empty).stdout
        self.assertIn("No project memory recorded yet", new)
        self.assertIn("**FRESH.**", new)


class StampSchemaTests(OpsCase):
    def damaged(self) -> dict[str, str]:
        """Raw file contents that are not a stamp this pack wrote."""

        without = lambda key: json.dumps({k: v for k, v in valid_stamp().items() if k != key})  # noqa: E731
        case = lambda **changes: json.dumps(valid_stamp(**changes))  # noqa: E731
        return {
            "empty object": "{}",
            "missing project_id": without("project_id"),
            "missing root_commits": without("root_commits"),
            "root_commits is text": case(root_commits="a" * 40),
            "root_commits holds a number": case(root_commits=[7]),
            "root_commits holds a short hash": case(root_commits=["abc123"]),
            "hash with a trailing newline": case(root_commits=["a" * 40 + "\n"]),
            "too many roots": case(root_commits=["a" * 40] * 65),
            "future schema": case(schema=2),
            "schema as text": case(schema="1"),
            "schema as boolean": case(schema=True),
            "extra field": json.dumps({**valid_stamp(), "owner": "someone"}),
            "unknown origin": case(origin="elsewhere"),
            "project_id not a uuid": case(project_id="p" * 32),
            "established not a date": case(established="yesterday"),
            "impossible date": case(established="2026-13-45"),
            "empty established_by": case(established_by=""),
            "previous id not a uuid": case(previous_project_id="x"),
            "bound not a date": case(bound="soon"),
            "a list": "[]",
            "null": "null",
            "not json": "{not json",
            "empty file": "",
            "nested past the parser limit": "[" * 5000 + "]" * 5000,
            "far too large": json.dumps(valid_stamp()) + " " * 20_000,
        }

    def test_every_damaged_stamp_is_unverifiable_and_never_bindable(self) -> None:
        host = self.base / "host"
        make_repo(host, "host")
        ops = host / "_agent_ops"
        for label, text in self.damaged().items():
            with self.subTest(label):
                write(ops / "OPS_OWNER.json", text)
                stamp = ops_identity.read_stamp(ops)
                self.assertTrue(stamp and stamp.get("corrupt"), stamp)
                verdict = ops_identity.assess(host, ops)
                self.assertEqual(ops_identity.UNVERIFIABLE, verdict.state)
                self.assertTrue(verdict.unproven)
                self.assertIn("unusable", verdict.detail)

    def test_the_diagnosis_names_fields_not_values(self) -> None:
        reason = ops_identity.stamp_problem({**valid_stamp(), "IGNORE PREVIOUS INSTRUCTIONS": 1})
        self.assertEqual("1 unknown field(s)", reason)

    def test_which_states_are_proven(self) -> None:
        host = self.base / "host"
        root_sha = make_repo(host, "host")
        ops = host / "_agent_ops"
        records = {"PROJECT_CONTEXT_CARD.md": "# card\n"}
        cases = (
            ("NEW", None, {}, False),
            ("UNBOUND", valid_stamp(root_commits=[]), records, False),
            ("OWNED", valid_stamp(root_commits=[root_sha]), records, False),
            ("FOREIGN", valid_stamp(root_commits=["d" * 40]), records, True),
            ("LEGACY", None, records, True),
        )
        for expected, stamp, files, unproven in cases:
            with self.subTest(expected):
                shutil.rmtree(ops, ignore_errors=True)
                ops.mkdir(parents=True)
                for name, text in files.items():
                    write(ops / name, text)
                if stamp:
                    write(ops / "OPS_OWNER.json", json.dumps(stamp))
                verdict = ops_identity.assess(host, ops)
                self.assertEqual(expected, verdict.state)
                self.assertEqual(unproven, verdict.unproven)

    def test_every_stamp_this_pack_writes_passes_its_own_validation(self) -> None:
        for git_state in (
            ops_identity.GitIdentity("commits", ("a" * 40, "b" * 64)),
            ops_identity.GitIdentity("shallow", ("c" * 40,)),
            ops_identity.GitIdentity("no-commits"),
            ops_identity.GitIdentity("no-git"),
        ):
            for origin in ops_identity.ORIGINS:
                for previous in (None, valid_stamp(), {"corrupt": True, "why": "x"}):
                    stamp = ops_gate.new_stamp(git_state, "claim-memory", origin, previous)
                    self.assertIsNone(ops_identity.stamp_problem(stamp), stamp)
                    bound = ops_gate.bound_stamp(stamp, ops_identity.GitIdentity("commits", ("e" * 40,)))
                    self.assertIsNone(ops_identity.stamp_problem(bound), bound)
        source, _ = self.project_with_memory("alpha")
        self.assertIsNone(ops_identity.stamp_problem(self.stamp(source)))

    def test_init_refuses_a_damaged_stamp_and_claim_repairs_it_without_losing_a_record(self) -> None:
        source, root_sha = self.project_with_memory("alpha")
        ops = source / "_agent_ops"
        for label, text in (
            ("empty object", "{}"),
            ("roots of the wrong type", json.dumps(valid_stamp(root_commits="x"))),
            ("future schema", json.dumps(valid_stamp(schema=2))),
        ):
            with self.subTest(label):
                write(ops / "OPS_OWNER.json", text)
                before = snapshot(source)
                refused = self.init(source)
                self.assertEqual(3, refused.returncode, refused.stdout + refused.stderr)
                self.assertIn("OPS_OWNER.json is unusable", refused.stderr)
                for flag in ("--claim-memory", "--reset-memory"):
                    self.assertIn(flag, refused.stderr)
                self.assertEqual(before, snapshot(source), "a refusal must not write anything")
                blocked = self.session(source).stdout
                self.assertIn("UNVERIFIED PROJECT MEMORY", blocked)
                self.assertNotIn("Owned by this project", blocked)

                claimed = self.init(source, "--claim-memory")
                self.assertEqual(0, claimed.returncode, claimed.stdout + claimed.stderr)
                stamp = self.stamp(source)
                self.assertIsNone(ops_identity.stamp_problem(stamp))
                self.assertEqual([root_sha], stamp["root_commits"])
                self.assertIn("MEMORY OF alpha", (ops / "PROJECT_CONTEXT_CARD.md").read_text(encoding="utf-8"))
                self.assertIn("Owned by this project", self.session(source).stdout)

    def test_reset_backs_up_a_damaged_stamp_and_starts_fresh(self) -> None:
        source, _ = self.project_with_memory("alpha")
        ops = source / "_agent_ops"
        write(ops / "OPS_OWNER.json", "{}")
        original = snapshot(ops)
        reset = self.init(source, "--reset-memory")
        self.assertEqual(0, reset.returncode, reset.stdout + reset.stderr)
        (backup,) = list((ops / "backups").iterdir())
        self.assertEqual(original, snapshot(backup, skip=()), "the damaged stamp is backed up too")
        self.assertIsNone(ops_identity.stamp_problem(self.stamp(source)))
        self.assertNotIn("MEMORY OF alpha", (ops / "PROJECT_CONTEXT_CARD.md").read_text(encoding="utf-8"))

    def test_a_stamp_that_is_not_a_regular_file_is_damage(self) -> None:
        host = self.base / "host"
        make_repo(host, "host")
        ops = host / "_agent_ops"
        (ops / "OPS_OWNER.json").mkdir(parents=True)
        self.assertEqual(ops_identity.UNVERIFIABLE, ops_identity.assess(host, ops).state)
        if can_symlink(self.base):
            shutil.rmtree(ops / "OPS_OWNER.json")
            elsewhere = write(self.base / "elsewhere.json", json.dumps(valid_stamp()))
            os.symlink(elsewhere, ops / "OPS_OWNER.json")
            self.assertEqual(ops_identity.UNVERIFIABLE, ops_identity.assess(host, ops).state)
            ops_gate.write_stamp(ops, valid_stamp(project_id="cd" * 16))
            self.assertFalse((ops / "OPS_OWNER.json").is_symlink())
            self.assertEqual(json.dumps(valid_stamp()), elsewhere.read_text(encoding="utf-8"), "the link target is untouched")
        self.assertEqual([], [p.name for p in ops.glob("*.tmp")])


class UnstampedMemoryNeedsAChoiceTests(OpsCase):
    def alpha_without_stamp(self) -> Path:
        """Another project's memory, business rules included, copied in with no stamp."""

        source, _ = self.project_with_memory("alpha")
        write(source / "_agent_ops" / "PROJECT_CONTEXT_CARD.md", RULES)
        host = self.foreign_host(source)
        (host / "_agent_ops" / "OPS_OWNER.json").unlink()
        return host

    def test_init_refuses_unstamped_memory_and_writes_nothing(self) -> None:
        host = self.alpha_without_stamp()
        before = snapshot(host)
        refused = self.init(host)
        self.assertEqual(3, refused.returncode, refused.stdout + refused.stderr)
        self.assertIn("nothing proves it is this project's", refused.stderr)
        self.assertIn("one-time step", refused.stderr)
        for flag in ("--claim-memory", "--reset-memory"):
            self.assertIn(flag, refused.stderr)
        self.assertEqual(before, snapshot(host))
        self.assertFalse((host / "_agent_ops" / "OPS_OWNER.json").exists())

    def test_claim_memory_adopts_the_records(self) -> None:
        host = self.alpha_without_stamp()
        claimed = self.init(host, "--claim-memory")
        self.assertEqual(0, claimed.returncode, claimed.stdout + claimed.stderr)
        ops = host / "_agent_ops"
        self.assertIn("refunds within 14 days", (ops / "PROJECT_CONTEXT_CARD.md").read_text(encoding="utf-8"))
        stamp = self.stamp(host)
        self.assertEqual("claim-memory", stamp["established_by"])
        self.assertEqual(git(host, "rev-list", "--max-parents=0", "HEAD").stdout.split(), stamp["root_commits"])
        self.assertFalse((ops / "backups").exists())
        self.assertIn("Owned by this project", self.session(host).stdout)
        self.assertEqual(0, self.init(host).returncode, "after the one-time step no flag is needed")

    def test_reset_memory_backs_up_then_starts_fresh(self) -> None:
        host = self.alpha_without_stamp()
        ops = host / "_agent_ops"
        original = snapshot(ops)
        reset = self.init(host, "--reset-memory")
        self.assertEqual(0, reset.returncode, reset.stdout + reset.stderr)
        (backup,) = list((ops / "backups").iterdir())
        self.assertEqual(original, snapshot(backup, skip=()))
        self.assertNotIn("refunds within 14 days", (ops / "PROJECT_CONTEXT_CARD.md").read_text(encoding="utf-8"))
        self.assertEqual("reset-memory", self.stamp(host)["established_by"])

    def test_an_embedded_install_is_told_the_exact_command_to_re_run(self) -> None:
        """What `embed_pack.py --update` shows when it re-initializes a legacy install."""
        host = self.base / "embedded-legacy"
        write(host / "src" / "app.py", "def entry():\n    return 1\n")
        pack = host / "ai-agent-workspace-pack"
        for name, text in (("TEAM_ROUTER.md", "# marker\n"), ("core-context/.keep", ""), ("scripts/init_project_ops.py", "x = 1\n")):
            write(pack / name, text)
        write(pack / "_agent_ops" / "PROJECT_CONTEXT_CARD.md", RULES)
        refused = self.init(host, "--embedded-folder", "ai-agent-workspace-pack")
        self.assertEqual(3, refused.returncode, refused.stdout + refused.stderr)
        self.assertIn("--embedded-folder ai-agent-workspace-pack --claim-memory", refused.stderr)
        self.assertIn("--embedded-folder ai-agent-workspace-pack --reset-memory", refused.stderr)

    def test_the_pack_source_needs_no_flag(self) -> None:
        pack = self.pack_checkout()
        write(pack / "_agent_ops" / "PROJECT_CONTEXT_CARD.md", "# the pack's own card\n")
        script = pack / "scripts" / "init_project_ops.py"
        result = run(script, "--target", str(pack), "--no-index", "--no-repo-map", cwd=pack)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("CLAIMED existing memory (pack-source)", result.stdout)
        self.assertEqual("pack-source", self.stamp(pack)["origin"])

    def test_authored_files_outside_the_named_records_still_count_as_memory(self) -> None:
        ops = self.base / "ops"
        ops.mkdir()
        for name in ("REPO_MAP.md", "INDEX.md", "SESSION_PROTOCOL.md", "archive/README.md", "phase_context_cards/README.md"):
            write(ops / name, "generated\n")
        self.assertFalse(ops_identity.has_memory(ops), "generated files are not memory")
        for name in ("archive/IMPLEMENTATION_LOG_2026-01.md", "phase_context_cards/PHASE_001_core.md", "PLAN_X.md", "HANDOFF.md"):
            with self.subTest(name):
                write(ops / name, "authored\n")
                self.assertTrue(ops_identity.has_memory(ops))
                (ops / name).unlink()


class UntouchedTemplatesTests(OpsCase):
    """The one unstamped folder init adopts without a flag: nothing in it was written by a person."""

    def templates_only(self) -> Path:
        root = self.base / "fresh"
        make_repo(root, "fresh")
        built = run(SCRIPTS / "init_project_ops.py", "--target", str(root), cwd=root)  # full init: map, index, tools
        self.assertEqual(0, built.returncode, built.stderr)
        (root / "_agent_ops" / "OPS_OWNER.json").unlink()
        return root

    def test_a_folder_of_untouched_templates_is_stamped_without_a_flag(self) -> None:
        root = self.templates_only()
        ops = root / "_agent_ops"
        self.assertTrue((ops / "REPO_MAP.md").is_file() and (ops / "tools").is_dir())
        self.assertEqual(ops_identity.LEGACY, ops_identity.assess(root, ops).state)
        stamped = self.init(root)
        self.assertEqual(0, stamped.returncode, stamped.stdout + stamped.stderr)
        self.assertIn("untouched templates", stamped.stdout)
        self.assertIsNone(ops_identity.stamp_problem(self.stamp(root)))
        self.assertFalse((ops / "backups").exists())

    def test_line_endings_do_not_make_a_template_look_edited(self) -> None:
        root = self.templates_only()
        ops, templates = root / "_agent_ops", SCRIPTS.parent / "core-context"
        for ending in (b"\n", b"\r\n"):
            for name in ops_identity.MEMORY_RECORDS:
                if (ops / name).is_file():
                    (ops / name).write_bytes((ops / name).read_bytes().replace(b"\r\n", b"\n").replace(b"\n", ending))
            with self.subTest(ending):
                self.assertTrue(ops_gate.holds_only_templates(ops, templates, "_agent_ops"))
        self.assertEqual(0, self.init(root).returncode)

    def test_one_authored_file_is_enough_to_ask(self) -> None:
        root = self.templates_only()
        ops = root / "_agent_ops"
        card = ops / "DECISION_LOG.md"
        pristine = card.read_bytes()
        additions = {
            "an edited record": lambda: card.write_bytes(pristine + b"\nDEC-0002 our own decision\n"),
            "a record from an older template": lambda: card.write_bytes(pristine.replace(b"Decision Log", b"Old Log", 1)),
            "a handoff": lambda: write(ops / "HANDOFF.md", "## Status\n\nopen\n"),
            "an archived log": lambda: write(ops / "archive" / "IMPLEMENTATION_LOG_2026-01.md", "old\n"),
            "a phase card": lambda: write(ops / "phase_context_cards" / "PHASE_001_core.md", "phase\n"),
            "a plan": lambda: write(ops / "PLAN_BIG_REFACTOR.md", "plan\n"),
        }
        for label, change in additions.items():
            with self.subTest(label):
                change()
                before = snapshot(root)
                refused = self.init(root)
                self.assertEqual(3, refused.returncode, refused.stdout + refused.stderr)
                self.assertEqual(before, snapshot(root))
                card.write_bytes(pristine)
                for extra in ("HANDOFF.md", "archive/IMPLEMENTATION_LOG_2026-01.md",
                              "phase_context_cards/PHASE_001_core.md", "PLAN_BIG_REFACTOR.md"):
                    (ops / extra).unlink(missing_ok=True)
        self.assertEqual(0, self.init(root).returncode, "restored, it is untouched again")

    def test_without_the_templates_nothing_can_be_shown_untouched(self) -> None:
        root = self.templates_only()
        gate = ops_gate.apply_ownership(
            root, root / "_agent_ops", claim=False, reset=False, pack_source=False, command=lambda flag: flag
        )
        self.assertFalse(gate.ok)


class BackupVerificationTests(OpsCase):
    def ops_folder(self) -> Path:
        ops = self.base / "ops"
        write(ops / "A.md", "alpha\n")
        write(ops / "deep" / "B.md", "bravo\n")
        (ops / "empty").mkdir()
        (ops / "bin.dat").write_bytes(bytes(range(256)))
        write(ops / "backups" / "older" / "keep.txt", "an earlier backup")
        return ops

    def live(self, ops: Path) -> dict[str, bytes]:
        return {name: data for name, data in snapshot(ops).items() if not name.startswith("backups/")}

    def after_copy(self, mutate):
        """Patch the copy step so `mutate(destination)` runs between copy and verify."""

        real = ops_gate._copy_ops

        def copy_then_corrupt(ops: Path, destination: Path) -> None:
            real(ops, destination)
            mutate(destination)

        return mock.patch.object(ops_gate, "_copy_ops", copy_then_corrupt)

    def test_a_same_size_change_between_copy_and_verify_is_refused(self) -> None:
        ops = self.ops_folder()
        before = self.live(ops)
        with self.after_copy(lambda d: flip_one_byte(d / "A.md")):
            with self.assertRaises(OSError) as caught:
                ops_gate.backup_ops(ops)
        self.assertIn("A.md", str(caught.exception))
        self.assertEqual(before, self.live(ops))
        names = sorted(path.name for path in (ops / "backups").iterdir())
        self.assertEqual(["older"], [n for n in names if not n.endswith(".INCOMPLETE")], "no unverified folder looks like a backup")
        self.assertEqual(1, len([n for n in names if n.endswith(".INCOMPLETE")]))

    def test_a_missing_or_extra_entry_is_refused(self) -> None:
        damages = {
            "missing file": lambda d: (d / "deep" / "B.md").unlink(),
            "extra file": lambda d: write(d / "extra.md", "x"),
            "missing empty directory": lambda d: (d / "empty").rmdir(),
            "extra directory": lambda d: (d / "extra-dir").mkdir(),
        }
        for label, damage in damages.items():
            with self.subTest(label):
                ops = self.ops_folder()
                with self.after_copy(damage), self.assertRaises(OSError):
                    ops_gate.backup_ops(ops)
                shutil.rmtree(ops)

    def test_a_reset_whose_backup_is_wrong_removes_nothing_and_stamps_nothing(self) -> None:
        host = self.base / "host"
        make_repo(host, "host")
        ops = host / "_agent_ops"
        write(ops / "PROJECT_CONTEXT_CARD.md", "# a card\n")
        write(ops / "HANDOFF.md", "## Status\n\nopen\n")
        before = self.live(ops)
        with self.after_copy(lambda d: flip_one_byte(d / "PROJECT_CONTEXT_CARD.md")):
            gate = ops_gate.apply_ownership(
                host, ops, claim=False, reset=True, pack_source=False, command=lambda flag: flag
            )
        self.assertFalse(gate.ok)
        self.assertIn("could not back up", gate.errors[0])
        self.assertIn("Nothing was removed", "\n".join(gate.errors))
        self.assertEqual(before, self.live(ops))

    def test_a_link_is_compared_by_its_target_and_never_followed(self) -> None:
        if not can_symlink(self.base):
            self.skipTest("this account cannot create symlinks")
        ops = self.ops_folder()
        outside = write(self.base / "outside.txt", "not part of the memory\n")
        os.symlink(outside, ops / "outside-link")
        os.symlink("A.md", ops / "relative-link")
        os.symlink(ops / "deep", ops / "dir-link", target_is_directory=True)
        destination, count = ops_gate.backup_ops(ops)
        for name in ("outside-link", "relative-link", "dir-link"):
            self.assertTrue((destination / name).is_symlink(), name)
            self.assertEqual(os.readlink(ops / name), os.readlink(destination / name))
        self.assertEqual(count, sum(1 for tag in ops_gate._entry_tags(destination, False).values() if tag != "dir"))

        def retarget(d: Path) -> None:
            (d / "relative-link").unlink()
            os.symlink("deep", d / "relative-link")

        with self.after_copy(retarget), self.assertRaises(OSError) as caught:
            ops_gate.backup_ops(ops)
        self.assertIn("relative-link", str(caught.exception))

    def test_a_link_is_read_with_readlink_not_opened(self) -> None:
        """The platform-independent half of the symlink rule: no privilege needed."""
        ops = self.ops_folder()
        write(ops / "pretend-link", "content that must not be hashed")
        with mock.patch.object(Path, "is_symlink", lambda self: self.name == "pretend-link"), \
                mock.patch.object(ops_gate.os, "readlink", lambda path: "where/it/points"):
            self.assertEqual("link:where/it/points", ops_gate._tag(ops / "pretend-link"))
        self.assertTrue(ops_gate._tag(ops / "A.md").startswith("sha256:"))

    def test_two_resets_in_one_second_get_two_folders(self) -> None:
        class Frozen:
            @staticmethod
            def now(tz=None):
                return datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)

        ops = self.ops_folder()
        with mock.patch.object(ops_gate, "datetime", Frozen):
            first, _ = ops_gate.backup_ops(ops)
            second, _ = ops_gate.backup_ops(ops)
        self.assertEqual(["20260102T030405Z", "20260102T030405Z-2"], [first.name, second.name])
        self.assertTrue((first / "A.md").is_file() and (second / "A.md").is_file())

    def test_a_folder_a_competing_reset_creates_first_is_never_shared(self) -> None:
        ops = self.ops_folder()
        real_mkdir, raced = Path.mkdir, []

        def racing(self, *args, **kwargs):
            if not raced and self.parent.name == "backups" and self.name == "20260102T030405Z":
                raced.append(self)
                real_mkdir(self)  # the other reset wins the folder between our check and our claim
                write(self / "competitor.txt", "theirs")
            return real_mkdir(self, *args, **kwargs)

        class Frozen:
            @staticmethod
            def now(tz=None):
                return datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)

        with mock.patch.object(ops_gate, "datetime", Frozen), mock.patch.object(Path, "mkdir", racing):
            mine, _ = ops_gate.backup_ops(ops)
        self.assertEqual("20260102T030405Z-2", mine.name)
        theirs = mine.parent / "20260102T030405Z"
        self.assertEqual(["competitor.txt"], sorted(p.name for p in theirs.iterdir()))


if __name__ == "__main__":
    unittest.main()

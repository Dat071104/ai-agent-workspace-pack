"""Install/update must never write or read through a link that leaves the pack folder.

A link (symlink or Windows junction) can sit at a shipped path, at any directory
above it, or at `.update-backup`. Following it would write outside the folder
the user chose, or overwrite another file inside it. The sync refuses instead,
before the first file is written, and never removes the link.

Every fixture lives under the OS temp directory. Creating links can need
privileges (Windows without Developer Mode): the test is then skipped with the
reason, and directory links fall back to a junction, which needs no privilege.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_shipping import PACK_ROOT, ShippingBase  # noqa: E402

sys.path.insert(0, str(PACK_ROOT / "scripts"))

from pack_sync import install_pack, update_pack  # noqa: E402

try:
    from pack_sync import UnsafePathError  # noqa: E402
except ImportError:  # before the fix: the tests must still run, and fail on the assertions
    UnsafePathError = OSError  # type: ignore[assignment,misc]

VERSION = "9.9.9"
SENTINEL = b"OUTSIDE: must never change\n"


class LinkTestBase(ShippingBase):
    def setUp(self) -> None:
        super().setUp()
        self.source = self.make_source(git=False)
        self.destination = self.base / "host" / "pack"
        self.outside = self.base / "outside"
        self.outside.mkdir()

    def link(self, path: Path, target: Path) -> None:
        """Replace `path` with a link to `target`; skip when the OS refuses links."""

        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.symlink(target, path, target_is_directory=target.is_dir())
            return
        except (OSError, NotImplementedError) as error:
            symlink_error = error
        if target.is_dir() and sys.platform == "win32":
            import _winapi  # noqa: PLC0415 -- Windows-only

            try:
                _winapi.CreateJunction(str(target), str(path))
                return
            except OSError as error:
                symlink_error = error
        self.skipTest(f"cannot create a link on this machine: {symlink_error}")

    def replace_with_dir_link(self, rel: str, target: Path) -> None:
        import shutil  # noqa: PLC0415

        path = self.destination / rel
        if path.exists() and not path.is_symlink():
            shutil.rmtree(path)
        self.link(path, target)

    def replace_with_file_link(self, rel: str, target: Path) -> None:
        path = self.destination / rel
        path.unlink()
        self.link(path, target)

    def outside_snapshot(self) -> dict[str, bytes]:
        return {p.relative_to(self.outside).as_posix(): p.read_bytes()
                for p in self.outside.rglob("*") if p.is_file()}

    def tree_snapshot(self) -> dict[str, bytes]:
        found: dict[str, bytes] = {}
        for current, dirs, files in os.walk(self.destination):
            dirs[:] = [name for name in dirs if not (Path(current) / name).is_symlink()]
            for name in files:
                path = Path(current) / name
                if not path.is_symlink():
                    found[path.relative_to(self.destination).as_posix()] = path.read_bytes()
        return found

    def installed(self) -> None:
        install_pack(self.source, self.destination, VERSION)


class SafeInstallTests(LinkTestBase):
    def test_normal_install_then_update_still_works(self) -> None:
        self.installed()
        self.assertTrue((self.destination / "AGENTS.md").is_file())
        report = update_pack(self.source, self.destination, VERSION, VERSION)
        self.assertGreater(report.unchanged, 0)
        self.assertEqual([], report.backed_up)

    def test_root_may_itself_be_a_link(self) -> None:
        real = self.base / "real_pack"
        real.mkdir()
        self.destination.parent.mkdir(parents=True, exist_ok=True)
        self.link(self.destination, real)
        self.installed()
        self.assertTrue((real / "AGENTS.md").is_file())
        update_pack(self.source, self.destination, VERSION, VERSION)


class LinkedFileTests(LinkTestBase):
    def test_update_refuses_shipped_file_linked_outside(self) -> None:
        self.installed()
        victim = self.outside / "victim.txt"
        victim.write_bytes(SENTINEL)
        self.replace_with_file_link("AGENTS.md", victim)
        before = self.tree_snapshot()

        with self.assertRaises(UnsafePathError) as caught:
            update_pack(self.source, self.destination, VERSION, VERSION)

        self.assertIn("AGENTS.md", str(caught.exception))
        self.assertEqual(SENTINEL, victim.read_bytes())
        self.assertEqual({"victim.txt": SENTINEL}, self.outside_snapshot())
        self.assertTrue((self.destination / "AGENTS.md").is_symlink(), "the link must be left in place")
        self.assertEqual(before, self.tree_snapshot(), "nothing may be written before the refusal")
        self.assertFalse((self.destination / ".update-backup").exists())

    def test_update_refuses_shipped_file_linked_to_another_file_inside(self) -> None:
        self.installed()
        notes = self.destination / "host_notes.txt"
        notes.write_bytes(SENTINEL)
        self.replace_with_file_link("TEAM_ROUTER.md", notes)

        with self.assertRaises(UnsafePathError):
            update_pack(self.source, self.destination, VERSION, VERSION)

        self.assertEqual(SENTINEL, notes.read_bytes())

    def test_stale_linked_file_is_never_read_or_removed(self) -> None:
        self.installed()
        # A later revision stops shipping this file; the host has linked it elsewhere.
        stale = "README.md"
        self.assertTrue((self.destination / stale).is_file(), "fixture needs a shipped README.md")
        (self.source / stale).unlink()
        victim = self.outside / "victim.txt"
        victim.write_bytes(SENTINEL)
        self.replace_with_file_link(stale, victim)

        report = update_pack(self.source, self.destination, VERSION, VERSION)

        self.assertEqual(SENTINEL, victim.read_bytes())
        self.assertIn(stale, report.conflicts)
        self.assertNotIn(stale, report.removed)
        self.assertTrue((self.destination / stale).is_symlink())


class LinkedDirectoryTests(LinkTestBase):
    def outside_with_shipped_lookalike(self) -> None:
        (self.outside / "pack_sync.py").write_bytes(SENTINEL)
        (self.outside / "sentinel.txt").write_bytes(SENTINEL)

    def test_update_refuses_parent_directory_linked_outside(self) -> None:
        self.installed()
        self.outside_with_shipped_lookalike()
        self.replace_with_dir_link("scripts", self.outside)
        before = self.outside_snapshot()

        with self.assertRaises(UnsafePathError) as caught:
            update_pack(self.source, self.destination, VERSION, VERSION)

        self.assertIn("scripts", str(caught.exception))
        self.assertEqual(before, self.outside_snapshot(), "no file may change or appear outside")
        linked = self.destination / "scripts"
        self.assertTrue(os.path.islink(linked) or getattr(os.path, "isjunction", lambda _: False)(linked),
                        "the link must be left in place")

    def test_install_refuses_parent_directory_linked_outside(self) -> None:
        self.destination.mkdir(parents=True)
        self.link(self.destination / "scripts", self.outside)

        with self.assertRaises(UnsafePathError):
            install_pack(self.source, self.destination, VERSION)

        self.assertEqual({}, self.outside_snapshot(), "nothing may be created outside the folder")
        self.assertEqual(["scripts"], sorted(p.name for p in self.destination.iterdir()),
                         "nothing may be written into the folder before the refusal")

    def test_update_refuses_backup_folder_linked_outside(self) -> None:
        self.installed()
        agents = self.destination / "AGENTS.md"
        agents.write_bytes(agents.read_bytes() + b"\nhost edit\n")  # forces a backup
        edited = agents.read_bytes()
        self.link(self.destination / ".update-backup", self.outside)

        with self.assertRaises(UnsafePathError) as caught:
            update_pack(self.source, self.destination, VERSION, VERSION)

        self.assertIn(".update-backup", str(caught.exception))
        self.assertEqual({}, self.outside_snapshot(), "the host's edit must not be copied outside")
        self.assertEqual(edited, agents.read_bytes(), "the host's edit must not be overwritten")


if __name__ == "__main__":
    unittest.main()

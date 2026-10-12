"""Shipping gaps found in review: backups, empty-index sources, install preflight.

Same fixture style as test_shipping.py (temp directories only; the "source pack"
is a copy of this repository's pack, optionally its own Git repository).
"""

from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path
from unittest import mock


sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_shipping import PACK, PACK_ROOT, ShippingBase  # noqa: E402  (also puts scripts/ on sys.path)
import pack_manifest  # noqa: E402
import pack_sync  # noqa: E402

FROZEN = "20260101-000000"
EXISTING_SCRIPT = "scripts/ops_policy.py"  # imported by init_project_ops.py


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


class BackupTests(ShippingBase):
    def installed(self) -> tuple[Path, Path]:
        source = self.make_source()
        result = self.embed(source)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return source, self.host / PACK

    def test_same_second_updates_keep_every_backup(self) -> None:
        source, pack = self.installed()
        work = pack / "commands" / "work.md"
        with mock.patch.object(pack_sync, "_timestamp", return_value=FROZEN):
            for edit in ("host edit A\n", "host edit B\n"):
                work.write_text(edit, encoding="utf-8", newline="")
                pack_sync.update_pack(source, pack, "v", "")
        folders = sorted((pack / ".update-backup").iterdir())
        self.assertEqual([FROZEN, f"{FROZEN}-1"], [folder.name for folder in folders])
        saved = [(folder / "commands" / "work.md").read_text(encoding="utf-8") for folder in folders]
        self.assertEqual(["host edit A\n", "host edit B\n"], saved)

    def test_update_that_backs_up_nothing_creates_no_backup_folder(self) -> None:
        source, pack = self.installed()
        pack_sync.update_pack(source, pack, "v", "")
        self.assertFalse((pack / ".update-backup").exists())

    def test_host_git_status_does_not_list_the_backup_folder(self) -> None:
        source, pack = self.installed()
        self.git(self.host, "init", "-q")
        self.git(self.host, "add", "-A")
        self.git(self.host, "commit", "-q", "-m", "host with pack")
        (pack / "commands" / "work.md").write_text("host edit\n", encoding="utf-8", newline="")
        result = self.embed(source, "--update", "--allow-dirty")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(1, len(list((pack / ".update-backup").glob("*/commands/work.md"))))
        status = self.git(self.host, "status", "--porcelain", "--untracked-files=all")
        self.assertNotIn(".update-backup", status)

    def test_shipped_gitignore_is_what_ignores_the_backup(self) -> None:
        self.assertIn(".update-backup/", (PACK_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines())
        self.assertTrue(pack_manifest.is_allowlisted(".gitignore"))


class EmptyIndexTests(ShippingBase):
    def empty_index_source(self) -> Path:
        source = self.make_source(git=False)
        self.git(source, "init", "-q")  # a repository of its own, nothing staged
        self.write(source, "commands/x.md", "never staged")
        return source

    def test_git_tracked_tells_empty_from_unusable(self) -> None:
        source = self.empty_index_source()
        self.assertEqual(set(), pack_manifest.git_tracked(source))
        self.assertEqual(set(), pack_manifest.shipping_set(source))
        with mock.patch.object(pack_manifest, "is_git_root", return_value=True), \
                mock.patch.object(pack_manifest, "_git", return_value=None):
            self.assertIsNone(pack_manifest.git_tracked(source), "a git failure is not an empty index")
        self.assertIsNone(pack_manifest.git_tracked(self.make_source("plain", git=False)))

    def test_empty_index_ships_nothing_and_the_installer_refuses(self) -> None:
        source = self.empty_index_source()
        result = self.embed(source)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("nothing staged", result.stderr)
        self.assertIn("git add", result.stderr)
        self.assertFalse((self.host / PACK).exists())
        self.assertEqual(set(), self.files_under(self.host))


class PreflightTests(ShippingBase):
    def unstage(self, source: Path, rel: str) -> None:
        self.git(source, "rm", "-q", "--cached", rel)  # file stays on disk, now untracked

    def test_untracked_required_script_is_refused_before_any_write(self) -> None:
        source = self.make_source()
        self.unstage(source, EXISTING_SCRIPT)
        result = self.embed(source)
        self.assertNotEqual(0, result.returncode)
        self.assertIn(EXISTING_SCRIPT, result.stderr)
        self.assertIn(f"git add {EXISTING_SCRIPT}", result.stderr)
        self.assertIn("staging is enough", result.stderr)
        self.assertNotIn("ModuleNotFoundError", result.stderr)
        self.assertEqual(set(), self.files_under(self.host), "nothing written")

        self.git(source, "add", EXISTING_SCRIPT)  # staged, still uncommitted
        fixed = self.embed(source)
        self.assertEqual(0, fixed.returncode, fixed.stdout + fixed.stderr)
        self.assertTrue((self.host / PACK / EXISTING_SCRIPT).is_file())

    def test_new_module_reachable_only_through_an_import_chain_is_required(self) -> None:
        source = self.make_source()
        init = source / "scripts" / "init_project_ops.py"
        init.write_text(init.read_text(encoding="utf-8") + "\nimport brand_new_helper  # noqa: E402\n",
                        encoding="utf-8", newline="")
        self.write(source, "scripts/brand_new_helper.py", "VALUE = 1\n")
        result = self.embed(source)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("scripts/brand_new_helper.py", result.stderr)
        self.assertIn("git add scripts/brand_new_helper.py", result.stderr)
        self.assertFalse((self.host / PACK).exists())

        self.git(source, "add", "scripts/brand_new_helper.py")
        self.assertEqual(0, self.embed(source).returncode)

    def test_untracked_warning_is_shown_before_initialization(self) -> None:
        source = self.make_source()
        self.write(source, "commands/x.md", "untracked, optional")
        result = self.embed(source)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("staging is enough", result.stdout)
        self.assertLess(result.stdout.index("WARN"), result.stdout.index("EMBEDDED PACK"))

    def test_non_git_source_still_installs_through_the_denylist(self) -> None:
        source = self.make_source("plain", git=False)
        result = self.embed(source)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertTrue((self.host / PACK / "scripts" / "init_project_ops.py").is_file())
        self.assertFalse((self.host / PACK / ".env").exists())

    def test_failed_update_preflight_leaves_the_installed_pack_byte_identical(self) -> None:
        source = self.make_source()
        self.assertEqual(0, self.embed(source).returncode)
        pack = self.host / PACK
        (pack / "commands" / "work.md").write_text("host edit\n", encoding="utf-8", newline="")
        self.write(source, "commands/work.md", "a newer tracked revision\n")  # an update would rewrite it
        self.unstage(source, EXISTING_SCRIPT)
        before = snapshot(self.host)
        result = self.embed(source, "--update", "--allow-dirty")
        self.assertNotEqual(0, result.returncode)
        self.assertIn(EXISTING_SCRIPT, result.stderr)
        self.assertEqual(before, snapshot(self.host))

    def test_in_place_preflight_failure_writes_nothing(self) -> None:
        seed = self.make_source("seed", git=False)
        # scan_deps is imported by init; check_repo_hygiene is only in init's tool list.
        for index, script in enumerate(("scan_deps.py", "check_repo_hygiene.py")):
            host = self.base / f"inplace{index}"
            pack = host / PACK
            shutil.copytree(seed, pack)
            (pack / "scripts" / script).unlink()
            before = snapshot(host)
            result = self.run_script(pack, "embed_pack.py", "--target", str(host), cwd=host)
            self.assertNotEqual(0, result.returncode, script)
            self.assertIn(f"scripts/{script}: absent from the source checkout", result.stderr)
            self.assertEqual(before, snapshot(host), script)

    def test_required_set_is_derived_from_imports_and_named_templates(self) -> None:
        required = pack_sync.required_files(self.make_source("plain", git=False))
        for rel in ("scripts/init_project_ops.py",
                    "scripts/build_code_index.py",   # lazy import inside init
                    "scripts/pack_sync.py",          # reached through embed_pack
                    "scripts/summarize_implementation_log.py",  # named in RUNTIME_TOOLS only
                    "core-context/SESSION_BRIEF.template.md",   # named in TEMPLATE_MAP
                    "TEAM_ROUTER.md"):
            self.assertIn(rel, required)


if __name__ == "__main__":
    unittest.main()

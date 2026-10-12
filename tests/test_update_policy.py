#!/usr/bin/env python3
"""`embed_pack.py --update` must carry policy fixes into projects installed earlier.

The embedded copy has no Git history, so only the source pack can prove that an
unrecorded (pre-OPS_POLICY.json) policy file is an unedited earlier rendering.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_shipping import PACK, ShippingBase  # noqa: E402


NEW_RULE = "- Policy line added by a later pack revision.\n"


class UpdatePolicyTests(ShippingBase):
    def test_update_refreshes_unedited_legacy_policy_and_keeps_edited_one(self) -> None:
        source = self.make_source()
        self.assertEqual(0, self.embed(source).returncode)
        ops = self.host / PACK / "_agent_ops"
        # A project initialized before policy hashes were recorded.
        (ops / "OPS_POLICY.json").unlink()
        rules = ops / "OPERATING_RULES.md"
        self.write(ops, "OPERATING_RULES.md", rules.read_text(encoding="utf-8") + "- Our own team rule.\n")

        for template in ("SESSION_PROTOCOL.template.md", "OPERATING_RULES.template.md"):
            path = source / "core-context" / template
            self.write(source, f"core-context/{template}", path.read_text(encoding="utf-8") + NEW_RULE)
        self.git(source, "commit", "-q", "-am", "policy fix")

        result = self.embed(source, "--update", "--allow-dirty")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn(NEW_RULE.strip(), (ops / "SESSION_PROTOCOL.md").read_text(encoding="utf-8"))
        edited = rules.read_text(encoding="utf-8")
        self.assertIn("- Our own team rule.", edited)
        self.assertNotIn(NEW_RULE.strip(), edited)
        self.assertIn("OPERATING_RULES.md", result.stdout)


class UpdateOwnershipPreflightTests(ShippingBase):
    """embed_pack asks init's ownership question before it writes, and forwards the answer."""

    def snapshot(self, root: Path) -> dict[str, bytes]:
        return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}

    def embedded_without_stamp(self, real_memory: bool) -> Path:
        source = self.make_source()
        self.assertEqual(0, self.embed(source).returncode)
        ops = self.host / PACK / "_agent_ops"
        (ops / "OPS_OWNER.json").unlink()  # as installed before ownership stamps existed
        if real_memory:
            self.write(ops, "PROJECT_CONTEXT_CARD.md", "# Card\nRULE: refunds within 30 days\n")
        return source

    def test_unproven_memory_stops_update_before_any_write(self) -> None:
        source = self.embedded_without_stamp(real_memory=True)
        before = self.snapshot(self.host / PACK)
        result = self.embed(source, "--update", "--allow-dirty")
        self.assertEqual(3, result.returncode, result.stdout + result.stderr)
        self.assertIn("embed_pack.py", result.stderr)
        self.assertIn("--update --allow-dirty --claim-memory", result.stderr)
        self.assertNotIn("UPDATED PACK", result.stdout)
        self.assertEqual(before, self.snapshot(self.host / PACK))

    def test_claim_flag_is_forwarded_to_init(self) -> None:
        source = self.embedded_without_stamp(real_memory=True)
        result = self.embed(source, "--update", "--allow-dirty", "--claim-memory")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        ops = self.host / PACK / "_agent_ops"
        self.assertTrue((ops / "OPS_OWNER.json").is_file())
        self.assertIn("refunds within 30 days", (ops / "PROJECT_CONTEXT_CARD.md").read_text(encoding="utf-8"))

    def test_untouched_templates_need_no_flag(self) -> None:
        # Same rendering path as init: a skeleton of untouched templates is not memory.
        source = self.embedded_without_stamp(real_memory=False)
        result = self.embed(source, "--update", "--allow-dirty")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertTrue((self.host / PACK / "_agent_ops" / "OPS_OWNER.json").is_file())


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Phase E1 tests — identity inventory mechanism.

Pins the metamorphosis inventory (docs/identity-inventory.json):
  - the inventory exists and is FRESH (matches the current tree)
  - every occurrence carries a policy class from docs/BRAND.md
  - protected classes (upstream-attribution, historical-doc) are non-empty
    and are the largest single protected block — S1 is measurable

stdlib-only; runs in CI unchanged.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INVENTORY = REPO_ROOT / "docs" / "identity-inventory.json"
TOOL = REPO_ROOT / "scripts" / "identity_map.py"

KNOWN_CLASSES = {
    "upstream-attribution", "historical-doc", "package-name", "workflow-name",
    "url", "path-reference", "user-facing", "doc-prose", "identifier",
}
PROTECTED_CLASSES = {"upstream-attribution", "historical-doc"}


def load() -> dict:
    return json.loads(INVENTORY.read_text(encoding="utf-8"))


class TestInventoryMechanism(unittest.TestCase):
    def test_tool_and_inventory_exist(self):
        self.assertTrue(TOOL.is_file(), "scripts/identity_map.py must exist (E1 deliverable)")
        self.assertTrue(INVENTORY.is_file(), "docs/identity-inventory.json must exist (E1 deliverable)")

    def test_inventory_is_fresh(self):
        """--check exits 0 only when the inventory matches the current tree.
        This forces every identity-affecting change to regenerate the
        inventory in the same commit — the audit trail can never drift."""
        result = subprocess.run(
            [sys.executable, str(TOOL), "--check"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(result.returncode, 0, f"stale inventory: {result.stderr.strip()}")

    def test_every_occurrence_has_policy_class(self):
        inv = load()
        bad = []
        for f in inv["files"]:
            for occ in f["occurrences"]:
                if occ["class"] not in KNOWN_CLASSES:
                    bad.append((f["path"], occ["line"], occ["class"]))
        self.assertEqual(bad, [], f"occurrences with unknown class: {bad}")

    def test_protected_block_is_present_and_measurable(self):
        inv = load()
        protected = inv["totals"]["by_class"].get("upstream-attribution", 0) + \
            inv["totals"]["by_class"].get("historical-doc", 0)
        self.assertGreater(protected, 0, "S1 protected block must be measurable")
        self.assertEqual(
            inv["totals"]["protected_occurrences"], protected,
            "protected_occurrences total must equal the sum of protected classes",
        )

    def test_rules_block_records_m4_and_s1(self):
        rules = load()["rules"]
        self.assertIn("m4", rules)
        self.assertIn("s1", rules)


if __name__ == "__main__":
    unittest.main()

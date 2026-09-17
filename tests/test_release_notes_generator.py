#!/usr/bin/env python3
"""test_release_notes_generator.py — Unit tests for Release Notes Generator (Epic RO1, Task RO1.3)."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys_path = REPO_ROOT / "scripts"
if str(sys_path) not in sys.path:
    sys.path.insert(0, str(sys_path))

import generate_release_notes as grn  # noqa: E402


class TestReleaseNotesGenerator(unittest.TestCase):
    def setUp(self):
        self.registry = grn.load_registry()
        self.version_data = json.loads((REPO_ROOT / "deployment" / "version.json").read_text(encoding="utf-8"))

    def test_standard_edition_release_notes_contains_all_mandated_sections(self):
        target = next(r for r in self.registry["releases"] if r["release_id"] == "wsa-2311-standard")
        notes = grn.build_release_notes(target, self.version_data)

        self.assertIn("Standard Edition", notes.user_notes)
        self.assertTrue(len(notes.technical_changes) >= 4)
        self.assertTrue(len(notes.compatibility_notes) >= 3)
        self.assertTrue(len(notes.upgrade_notes) >= 3)

        md = grn.format_markdown_release_notes(notes)
        self.assertIn("## 1. User Notes", md)
        self.assertIn("## 2. Technical Changes", md)
        self.assertIn("## 3. Compatibility Notes", md)
        self.assertIn("## 4. Upgrade Notes", md)
        self.assertIn("Cryptographic Checksums", md)

    def test_banking_edition_specifies_clean_unrooted_ramdisk(self):
        target = next(r for r in self.registry["releases"] if r["release_id"] == "wsa-2311-banking")
        notes = grn.build_release_notes(target, self.version_data)

        self.assertIn("Banking & Enterprise", notes.user_notes)
        self.assertTrue(any("clean vanilla ramdisk" in c for c in notes.technical_changes))

    def test_manager_release_notes_specifies_desktop_orchestration(self):
        target = next(r for r in self.registry["releases"] if r["release_id"] == "manager-0.2.2")
        notes = grn.build_release_notes(target, self.version_data)

        self.assertIn("Emberbird Manager", notes.user_notes)
        self.assertTrue(any("Tauri" in c for c in notes.technical_changes))
        self.assertTrue(any("Doctor" in c for c in notes.technical_changes))

    def test_notes_dict_schema(self):
        target = next(r for r in self.registry["releases"] if r["release_id"] == "wsa-2311-standard")
        notes = grn.build_release_notes(target, self.version_data)
        d = notes.to_dict()

        for key in ("release_id", "tag", "kind", "channel", "edition", "published_at", "user_notes", "technical_changes", "compatibility_notes", "upgrade_notes", "assets"):
            self.assertIn(key, d)

    def test_cli_execution_json(self):
        cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "generate_release_notes.py"),
            "--release-id", "wsa-2311-standard",
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI error: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertEqual(data["release_id"], "wsa-2311-standard")
        self.assertIn("Standard Edition", data["user_notes"])


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Contract and Validation Tests for Project Genesis (Phase R1 — Android 14 Research).

Verifies research documentation completeness, Treble diagnostic harness execution,
Zero-PII compliance, and Truth Hierarchy L1 non-fabrication guarantees.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
FEASIBILITY_DOC = DOCS_DIR / "research" / "ANDROID14_FEASIBILITY.md"
HARNESS_PATH = REPO_ROOT / "tools" / "research" / "test_gsi_boot.py"
REGISTRY_PATH = REPO_ROOT / "data" / "releases" / "releases.json"


class TestGenesisFeasibilityDocument(unittest.TestCase):
    """Verify Android 14 feasibility documentation integrity and contract compliance."""

    def test_document_exists(self):
        self.assertTrue(FEASIBILITY_DOC.is_file(), "ANDROID14_FEASIBILITY.md must exist")

    def test_mandated_sections_present(self):
        content = FEASIBILITY_DOC.read_text(encoding="utf-8")
        mandated_sections = [
            "Executive Summary",
            "Microsoft Proprietary HAL Boundary Map",
            "Treble GSI Compatibility",
            "Magisk Root",
            "Formal Go/No-Go Verdict",
        ]
        for section in mandated_sections:
            self.assertIn(section, content, f"Missing section: {section}")

    def test_formal_verdict_explicit(self):
        content = FEASIBILITY_DOC.read_text(encoding="utf-8")
        self.assertIn("NO-GO", content)
        self.assertIn("LTS", content)
        self.assertIn("2407.40000.4.0", content)

    def test_zero_pii_in_research(self):
        content = FEASIBILITY_DOC.read_text(encoding="utf-8").lower()
        pii_terms = ["c:\\users\\", "/home/", "@gmail.com", "password", "token="]
        for term in pii_terms:
            self.assertNotIn(term, content, f"Potential PII detected: {term}")


class TestGenesisDiagnosticHarness(unittest.TestCase):
    """Verify test_gsi_boot.py execution and image inspection capabilities."""

    def test_harness_exists(self):
        self.assertTrue(HARNESS_PATH.is_file(), "test_gsi_boot.py must exist")

    def test_harness_cli_json_audit(self):
        cmd = [sys.executable, str(HARNESS_PATH), "--audit-hal-symbols", "--json"]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(proc.stdout)
        self.assertIn("hal_audit", data)
        self.assertEqual(data["hal_audit"]["target_api"], 34)
        self.assertEqual(data["hal_audit"]["verdict"], "NO-GO (LTS Ratified)")
        self.assertTrue(len(data["hal_audit"]["components"]) >= 4)

    def test_sparse_header_detection(self):
        import struct

        with tempfile.NamedTemporaryFile(suffix=".img", delete=False) as f:
            temp_img = Path(f.name)
            # Write Android sparse magic and header (28 bytes total)
            header = struct.pack("<IHHHHIIII", 0xED26FF3A, 1, 0, 28, 12, 4096, 100, 1, 0)
            f.write(header)

        try:
            cmd = [sys.executable, str(HARNESS_PATH), "--inspect-image", str(temp_img), "--json"]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(proc.stdout)
            self.assertTrue(data["image_inspection"]["is_sparse"])
            self.assertEqual(data["image_inspection"]["format"], "android_sparse_image")
            self.assertEqual(data["image_inspection"]["sparse_meta"]["block_size"], 4096)
        finally:
            if temp_img.exists():
                temp_img.unlink()


class TestTruthHierarchyNonFabrication(unittest.TestCase):
    """Ensure no synthetic or unverified Android 14 releases exist in releases.json."""

    def test_no_synthetic_android_14_releases(self):
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        for release in registry.get("releases", []):
            if release.get("kind") == "subsystem":
                # Official WSA versions start with 2xxx
                ver = release.get("wsa_version", "")
                self.assertFalse(ver.startswith("14."), f"Fabricated Android 14 version found: {ver}")
                # Android API for published WSA releases must be 32 or 33
                tag = release.get("tag", "")
                self.assertNotIn("android-14", tag.lower())


if __name__ == "__main__":
    unittest.main()

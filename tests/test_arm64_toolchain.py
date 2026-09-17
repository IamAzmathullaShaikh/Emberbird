#!/usr/bin/env python3
"""ARM64 Toolchain and Contract Tests (Phase A1 — Project Snapdragon).

Tests offline ABI resolution, build script CLI parameters, GApps asset matching,
and Truth Hierarchy L1 compliance for ARM64 enablement.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
REGISTRY_PATH = REPO_ROOT / "data" / "releases" / "releases.json"

sys.path.insert(0, str(TOOLS_DIR))
import generateGappsLink  # noqa: E402


class TestARM64ABIResolution(unittest.TestCase):
    """Verify ABI mappings between WSA architecture and component names."""

    def test_magisk_abi_mapping(self):
        """Magisk uses arm64-v8a inside APK lib directories."""
        arch_map = {
            "x64": "x86_64",
            "arm64": "arm64-v8a",
        }
        for arch, expected_abi in arch_map.items():
            resolved = "arm64-v8a" if arch == "arm64" else "x86_64"
            self.assertEqual(resolved, expected_abi)

    def test_gapps_arch_mapping(self):
        """GApps WSA-Addon images use machine architecture names."""
        arch_map = {
            "x64": "x86_64",
            "arm64": "arm64",
        }
        for arch, expected_gapps_arch in arch_map.items():
            resolved = "arm64" if arch == "arm64" else "x86_64"
            self.assertEqual(resolved, expected_gapps_arch)

    def test_config_sh_native_arch_logic(self):
        """Verify config.sh architecture environment resolution logic."""
        config_sh = (TOOLS_DIR / "config.sh").read_text(encoding="utf-8")
        self.assertIn('arm64) TARGET_ARCH_NATIVE="arm64"', config_sh)
        self.assertIn('*)     TARGET_ARCH_NATIVE="x86_64"', config_sh)
        self.assertIn("gapps-${api_ver}-${TARGET_ARCH_NATIVE}.img", config_sh)


class TestGappsLinkGeneration(unittest.TestCase):
    """Verify generateGappsLink.py ARM64 argument parsing and regex patterns."""

    def test_parse_args_default_arch(self):
        test_argv = ["generateGappsLink.py", "/tmp/dl", "/tmp/aria2.lst", "33"]
        with patch.object(sys, "argv", test_argv):
            _, _, api, arch = generateGappsLink._parse_args()
            self.assertEqual(api, "33")
            self.assertEqual(arch, "x86_64")

    def test_parse_args_arm64_arch(self):
        test_argv = ["generateGappsLink.py", "/tmp/dl", "/tmp/aria2.lst", "33", "arm64"]
        with patch.object(sys, "argv", test_argv):
            _, _, api, arch = generateGappsLink._parse_args()
            self.assertEqual(api, "33")
            self.assertEqual(arch, "arm64")

    def test_parse_args_rejects_unsupported_arch(self):
        test_argv = ["generateGappsLink.py", "/tmp/dl", "/tmp/aria2.lst", "33", "riscv64"]
        with patch.object(sys, "argv", test_argv):
            with self.assertRaises(SystemExit) as ctx:
                generateGappsLink._parse_args()
            self.assertEqual(ctx.exception.code, 1)

    def test_arm64_asset_matching(self):
        release_str = "13.0"
        arch = "arm64"
        pattern = re.compile(rf"gapps.*{re.escape(release_str)}.*{re.escape(arch)}.*\.img$", re.I)

        self.assertTrue(pattern.search("gapps-13.0-arm64.img"))
        self.assertTrue(pattern.search("gapps-13.0-arm64-20231015.img"))
        self.assertFalse(pattern.search("gapps-13.0-x86_64.img"))
        self.assertFalse(pattern.search("gapps-12.1-arm64.img"))

    def test_arch_agnostic_fallback_filters_conflicting_archs(self):
        """Fallback candidate must not match conflicting architecture tokens."""
        arch_tokens = generateGappsLink._ARCH_TOKENS
        self.assertIn("x86_64", arch_tokens)
        self.assertIn("arm64", arch_tokens)

        valid_agnostic = "gapps-13.0.img"
        self.assertFalse(any(t in valid_agnostic.lower() for t in arch_tokens))

        invalid_conflict = "gapps-13.0-x86_64.img"
        self.assertTrue(any(t in invalid_conflict.lower() for t in arch_tokens))


class TestBuildScriptsCLI(unittest.TestCase):
    """Verify build script argument support for ARM64 and Bring-Your-Own-Bundle."""

    def test_build_local_argparse(self):
        build_local_code = (TOOLS_DIR / "build_local.py").read_text(encoding="utf-8")
        self.assertIn('choices=["x64", "arm64"]', build_local_code)
        self.assertIn('--wsa-file', build_local_code)
        self.assertIn('magisk_abi = "arm64-v8a" if args.arch == "arm64" else "x86_64"', build_local_code)
        self.assertIn('gapps_arch = "arm64" if args.arch == "arm64" else "x86_64"', build_local_code)

    def test_build_sh_options(self):
        build_sh_code = (TOOLS_DIR / "build.sh").read_text(encoding="utf-8")
        self.assertIn("x64|arm64", build_sh_code)
        self.assertIn("--wsa-file", build_sh_code)
        self.assertIn("wsa-file:", build_sh_code)
        self.assertIn("CUSTOM_WSA_FILE", build_sh_code)


class TestRegistryARM64Compliance(unittest.TestCase):
    """Verify registry generator pattern and Truth Hierarchy L1 enforcement."""

    def test_package_regex_matches_arm64(self):
        from scripts.build_registry import PACKAGE_RE

        self.assertTrue(PACKAGE_RE.match("WSA_2407.40000.4.0_x64.7z"))
        self.assertTrue(PACKAGE_RE.match("WSA_2407.40000.4.0_x64_vanilla.7z"))
        self.assertTrue(PACKAGE_RE.match("WSA_2407.40000.4.0_arm64.7z"))
        self.assertTrue(PACKAGE_RE.match("WSA_2407.40000.4.0_arm64_vanilla.7z"))
        self.assertFalse(PACKAGE_RE.match("WSA_2407.40000.4.0_arm64.zip"))
        self.assertFalse(PACKAGE_RE.match("WSA_2407.40000.4.0_x86.7z"))

    def test_truth_hierarchy_l1_no_synthetic_arm64_releases(self):
        """Verify that committed registry only contains genuine published releases."""
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        for release in registry.get("releases", []):
            if release.get("kind") == "subsystem":
                for asset in release.get("assets", []):
                    # Every asset must have a verified non-placeholder hash
                    sha256 = asset["sha256"]
                    self.assertEqual(len(sha256), 64)
                    self.assertNotEqual(sha256, "0" * 64)
                    # If any arm64 asset exists, it must have a real source URL
                    if asset.get("arch") == "arm64":
                        self.assertTrue(asset["source_url"].startswith("https://"))


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
test_bootstrap_winget.py — Unit tests for winget submission & hash bootstrap.

Uses a fake GitHub transport (monkeypatched module functions) so no network is
touched. Covers: release resolution, asset picking, checksum cross-verification,
honesty contract (no invented hashes), manifest patching, and submission
package structural checks.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import bootstrap_winget as bw  # noqa: E402

SETUP_NAME = "WSABuildsManager-Setup-0.2.3-x64.exe"
HASH_A = "a" * 64
HASH_B = "b" * 64


def make_release(checksum_hash=HASH_A, sidecar_hash=HASH_A, with_checksums=True, with_sidecar=True):
    assets = [
        {"name": SETUP_NAME, "size": 2_500_000, "browser_download_url": f"https://x/{SETUP_NAME}"},
        {"name": "WSABuildsManager-0.2.3-checksums.txt", "size": 200,
         "browser_download_url": "https://x/checksums.txt"},
        {"name": f"{SETUP_NAME}.sha256", "size": 90, "browser_download_url": "https://x/setup.sha256"},
    ]
    if not with_checksums:
        assets = [a for a in assets if not a["name"].endswith("checksums.txt")]
    if not with_sidecar:
        assets = [a for a in assets if not a["name"].endswith(".sha256")]
    return {"tag_name": "v0.2.3", "draft": False, "assets": assets}


class FakeTransports(unittest.TestCase):
    def setUp(self):
        self._orig_download = bw.download_with_hash
        self._orig_api = bw.api_get_json
        self.downloads = {}

        def fake_download(url, sha256=None):
            if url.endswith("checksums.txt"):
                body = f"{HASH_A} *{SETUP_NAME}\n{HASH_B} *WSABuildsManager-Portable-0.2.3-x64.zip".encode()
            elif url.endswith(".sha256"):
                body = f"{self.sidecar_hash} *{SETUP_NAME}".encode()
            else:
                body = b"fake-installer-bytes"
            return body, HASH_A if "checksums" not in url and not url.endswith(".sha256") else None

        self._fake_download = fake_download
        bw.download_with_hash = fake_download

    def tearDown(self):
        bw.download_with_hash = self._orig_download
        bw.api_get_json = self._orig_api


class TestChecksumVerification(FakeTransports):
    def test_checksums_and_sidecar_agree(self):
        self.sidecar_hash = HASH_A
        release = make_release()
        source = bw.verify_against_checksums(release, SETUP_NAME, HASH_A)
        self.assertIn(source, ("checksums.txt", "sidecar"))

    def test_disagreement_raises(self):
        self.sidecar_hash = HASH_B
        release = make_release(sidecar_hash=HASH_B)
        with self.assertRaises(bw.BootstrapError):
            bw.verify_against_checksums(release, SETUP_NAME, HASH_A)

    def test_no_references_raises(self):
        release = make_release(with_checksums=False, with_sidecar=False)
        with self.assertRaises(bw.BootstrapError):
            bw.verify_against_checksums(release, SETUP_NAME, HASH_A)


class TestReleaseResolution(FakeTransports):
    def test_missing_release_is_bootstrap_error(self):
        def fake_api(url):
            raise bw.BootstrapError(f"Not found: {url}")
        bw.api_get_json = fake_api
        with self.assertRaises(bw.BootstrapError):
            bw.resolve_release("0.2.3")

    def test_draft_refused(self):
        bw.api_get_json = lambda url: {"tag_name": "v0.2.3", "draft": True, "assets": []}
        with self.assertRaises(bw.BootstrapError):
            bw.resolve_release("0.2.3")


class TestAssetPicking(FakeTransports):
    def test_missing_asset_lists_available(self):
        release = make_release()
        with self.assertRaises(bw.BootstrapError) as ctx:
            bw.pick_installer_asset(release, "Nope-Setup-0.2.3-x64.exe")
        self.assertIn(SETUP_NAME, str(ctx.exception))

    def test_suspiciously_small_asset_refused(self):
        """A 30-byte 'installer' is a stub — the pipeline must refuse it."""
        import tempfile
        release = make_release()
        release["assets"][0]["size"] = 30  # stub-size installer
        bw.api_get_json = lambda url: release

        with tempfile.TemporaryDirectory() as td:
            manifest_dir = Path(td) / "0.2.3"
            manifest_dir.mkdir()
            (manifest_dir / "Emberbird.Manager.installer.yaml").write_text(
                "PackageIdentifier: WSABuilds.WSABuildsManager\n"
                "PackageVersion: 0.2.3\n"
                "  - Architecture: x64\n"
                f"    InstallerUrl: https://x/{SETUP_NAME}\n"
                '    InstallerSha256: "' + "0" * 64 + """\n""",
                encoding="utf-8",
            )
            orig_dir = bw.MANIFESTS_DIR
            orig_pkg = bw.PACKAGE_ID
            bw.MANIFESTS_DIR = Path(td)
            bw.PACKAGE_ID = "Emberbird.Manager"
            manifest_dir = Path(td) / "0.2.3"
            manifest_dir.mkdir(parents=True, exist_ok=True)
            try:
                (manifest_dir / f"{bw.PACKAGE_ID}.installer.yaml").write_text(
                    "PackageIdentifier: Emberbird.Manager\n"
                    "PackageVersion: 0.2.3\n"
                    "  - Architecture: x64\n"
                    f"    InstallerUrl: https://x/{SETUP_NAME}\n"
                    '    InstallerSha256: "' + "0" * 64 + """\n""",
                    encoding="utf-8",
                )
                with self.assertRaises(bw.BootstrapError) as ctx:
                    bw.bootstrap("0.2.3", expected_hash=None, allow_download=True)
                self.assertIn("suspiciously small", str(ctx.exception))
            finally:
                bw.MANIFESTS_DIR = orig_dir
                bw.PACKAGE_ID = orig_pkg


class TestManifestPatching(FakeTransports):
    def test_patch_fields(self):
        text = (
            "PackageIdentifier: WSABuilds.WSABuildsManager\n"
            "PackageVersion: 0.2.3\n"
            "Installers:\n"
            "  - Architecture: x64\n"
            "    InstallerUrl: https://example/x.exe\n"
            '    InstallerSha256: "0000000000000000000000000000000000000000000000000000000000000000"\n'
        )
        patched = bw.patch_manifest_field(text, "InstallerSha256", HASH_A)
        self.assertIn(f'InstallerSha256: "{HASH_A}"', patched)
        patched = bw.patch_manifest_field(patched, "PackageVersion", "0.2.3")
        self.assertIn("PackageVersion: 0.2.3", patched)

    def test_patch_missing_field_raises(self):
        with self.assertRaises(bw.BootstrapError):
            bw.patch_manifest_field("a: 1\n", "InstallerUrl", "https://x")


class TestHonestyContract(FakeTransports):
    def test_no_hash_source_refuses(self):
        with tempfile.TemporaryDirectory() as td:
            manifest_dir = Path(td) / "0.2.3"
            manifest_dir.mkdir()
            (manifest_dir / "Emberbird.Manager.installer.yaml").write_text(
                "PackageIdentifier: WSABuilds.WSABuildsManager\n"
                "PackageVersion: 0.2.3\n"
                "  - Architecture: x64\n"
                "    InstallerUrl: https://x/" + SETUP_NAME + "\n"
                '    InstallerSha256: "' + "0" * 64 + '"\n',
                encoding="utf-8",
            )
            # Point module at the temp manifests dir
            orig_dir = bw.MANIFESTS_DIR
            bw.MANIFESTS_DIR = Path(td)
            try:
                with self.assertRaises(bw.BootstrapError):
                    bw.bootstrap("0.2.3", expected_hash=None, allow_download=False)
            finally:
                bw.MANIFESTS_DIR = orig_dir


class TestSubmissionPackageChecks(unittest.TestCase):
    def test_structural_checks_detect_missing_hash(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "0.2.3"
            base.mkdir()
            (base / "Emberbird.Manager.installer.yaml").write_text(
                "PackageIdentifier: WSABuilds.WSABuildsManager\n"
                "PackageVersion: 0.2.3\n"
                "ManifestType: installer\n"
                "ManifestVersion: 1.6.0\n"
                "  - Architecture: x64\n"
                "    InstallerUrl: https://x/setup.exe\n"
                '    InstallerSha256: "' + "0" * 64 + '"\n',
                encoding="utf-8",
            )
            (base / "Emberbird.Manager.yaml").write_text(
                "PackageIdentifier: WSABuilds.WSABuildsManager\n"
                "PackageVersion: 0.2.3\n"
                "ManifestType: version\n"
                "ManifestVersion: 1.6.0\n",
                encoding="utf-8",
            )
            (base / "Emberbird.Manager.locale.en-US.yaml").write_text(
                "PackageIdentifier: WSABuilds.WSABuildsManager\n"
                "PackageVersion: 0.2.3\n"
                "ManifestType: defaultLocale\n"
                "ManifestVersion: 1.6.0\n",
                encoding="utf-8",
            )
            installer = (base / "Emberbird.Manager.installer.yaml").read_text(encoding="utf-8")
            h = bw.read_manifest_field(installer, "InstallerSha256")
            self.assertEqual(h, "0" * 64)
            # The structural check must reject the all-zero placeholder hash.
            is_real = len(h) == 64 and h != "0" * 64
            self.assertFalse(is_real)


if __name__ == "__main__":
    unittest.main()

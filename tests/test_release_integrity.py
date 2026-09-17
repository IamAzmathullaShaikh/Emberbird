#!/usr/bin/env python3
"""Publication Integrity Gate tests (Release Integrity epic).

The Releases section is a public download surface: whatever lands there is run
by real users. These tests pin the rule that fabricated or unverifiable bytes
can never be published, and that the staging scaffold is detected as such.

stdlib-only; runs in CI unchanged.
"""

import io
import json
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import release_integrity as ri  # noqa: E402


def make_pe(path: Path, size: int = 1 << 20) -> Path:
    """A minimal, structurally valid PE image padded to `size` bytes."""
    payload = bytearray(b"\x00" * size)
    payload[0:2] = b"MZ"
    e_lfanew = 0x80
    struct.pack_into("<I", payload, 0x3C, e_lfanew)
    payload[e_lfanew : e_lfanew + 4] = b"PE\x00\x00"
    path.write_bytes(bytes(payload))
    return path


def make_zip(path: Path, payload_bytes: int = 0) -> Path:
    """A real ZIP container. Subsystem archives must clear a 100 MiB floor, so
    callers pad with STORED (incompressible) content when the floor applies."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("AppxManifest.xml", "<Package/>")
        if payload_bytes:
            zf.writestr("payload.bin", b"\x00" * payload_bytes)
    return path


class TestScaffoldDetection(unittest.TestCase):
    """Scaffold bytes written by build_release_candidates.py are never REAL."""

    def test_manager_setup_scaffold_is_placeholder(self):
        with tempfile.TemporaryDirectory() as tmp:
            stub = Path(tmp) / "EmberbirdManager-Setup-0.2.2-x64.exe"
            stub.write_bytes(b"MZ_EMBERBIRD_MANAGER_DESKTOP_SETUP_BINARY_PAYLOAD_V0.2.2")
            verdict = ri.classify_artifact(stub)
            self.assertEqual(verdict.verdict, ri.PLACEHOLDER)
            self.assertFalse(verdict.publishable)

    def test_manager_portable_scaffold_is_placeholder(self):
        with tempfile.TemporaryDirectory() as tmp:
            stub = Path(tmp) / "EmberbirdManager-Portable-0.2.2-x64.zip"
            stub.write_bytes(b"PK_EMBERBIRD_MANAGER_DESKTOP_PORTABLE_ZIP_PAYLOAD_V0.2.2")
            self.assertEqual(ri.classify_artifact(stub).verdict, ri.PLACEHOLDER)

    def test_mock_wsa_initrd_marker_is_placeholder(self):
        with tempfile.TemporaryDirectory() as tmp:
            stub = Path(tmp) / "WSA_2407.40000.4.0_x64.7z"
            stub.write_bytes(b"MAGISK_BOOT_IMG_HEADER\nROOT_STAGE=2\n")
            self.assertEqual(ri.classify_artifact(stub).verdict, ri.PLACEHOLDER)


class TestUnverifiable(unittest.TestCase):
    """Bytes that claim a container they are not must be refused."""

    def test_tiny_installer_is_unverifiable(self):
        with tempfile.TemporaryDirectory() as tmp:
            tiny = Path(tmp) / "EmberbirdManager-Setup-0.2.2-x64.exe"
            tiny.write_bytes(b"MZ" + b"\x00" * 54)
            verdict = ri.classify_artifact(tiny)
            self.assertEqual(verdict.verdict, ri.UNVERIFIABLE)
            self.assertTrue(any("floor" in r for r in verdict.reasons))

    def test_text_bytes_named_exe_are_unverifiable(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "EmberbirdManager-Setup-0.2.2-x64.exe"
            fake.write_bytes(b"this is not an executable" * 60000)
            self.assertEqual(ri.classify_artifact(fake).verdict, ri.UNVERIFIABLE)

    def test_zip_without_zip_signature_is_unverifiable(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "EmberbirdManager-Portable-0.2.2-x64.zip"
            fake.write_bytes(b"NOTAZIP" + b"\x00" * (1 << 20))
            self.assertEqual(ri.classify_artifact(fake).verdict, ri.UNVERIFIABLE)

    def test_seven_zip_without_signature_is_unverifiable(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "WSA_2407.40000.4.0_x64.7z"
            fake.write_bytes(b"\x00" * (128 << 20))
            self.assertEqual(ri.classify_artifact(fake).verdict, ri.UNVERIFIABLE)

    def test_placeholder_checksum_manifest_is_unverifiable(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "checksums.sha256"
            manifest.write_text(
                "REQUIRES REPOSITORY VERIFICATION *EmberbirdManager-Setup.exe\n",
                encoding="utf-8",
            )
            self.assertEqual(ri.classify_artifact(manifest).verdict, ri.UNVERIFIABLE)

    def test_zero_byte_artifact_is_unverifiable(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "EmberbirdManager-Setup-0.2.2-x64.exe"
            empty.write_bytes(b"")
            self.assertEqual(ri.classify_artifact(empty).verdict, ri.UNVERIFIABLE)


class TestRealArtifacts(unittest.TestCase):
    """Genuine build outputs pass."""

    def test_valid_pe_installer_is_real(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = make_pe(Path(tmp) / "EmberbirdManager-Setup-0.2.2-x64.exe")
            verdict = ri.classify_artifact(exe)
            self.assertEqual(verdict.verdict, ri.REAL)
            self.assertTrue(verdict.publishable)

    def test_real_zip_archive_is_real(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = make_zip(
                Path(tmp) / "EmberbirdManager-Portable-0.2.2-x64.zip",
                payload_bytes=(ri.MIN_BYTES["portable"] + 4096),
            )
            self.assertEqual(ri.classify_artifact(archive).verdict, ri.REAL)

    def test_real_subsystem_archive_is_real(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = make_zip(Path(tmp) / "WSA_2407.40000.4.0_x64.zip")
            with mock.patch.dict(ri.MIN_BYTES, {"subsystem-archive": 64}):
                self.assertEqual(ri.classify_artifact(archive).verdict, ri.REAL)

    def test_subsystem_floor_matches_a_plausible_distribution(self):
        # Regression pin: the floor exists so manifest-only stubs (1-2 KB) can
        # never masquerade as a real Windows Subsystem for Android distribution.
        self.assertEqual(ri.MIN_BYTES["subsystem-archive"], 100 << 20)
        self.assertGreaterEqual(ri.MIN_BYTES["installer"], 1 << 20)

    def test_real_subsystem_archive_fails_floor_when_tiny(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = make_zip(Path(tmp) / "WSA_2407.40000.4.0_x64.zip")
            self.assertEqual(ri.classify_artifact(archive).verdict, ri.UNVERIFIABLE)

    def test_real_sha256_and_sha512_manifests_are_real(self):
        with tempfile.TemporaryDirectory() as tmp:
            sha256 = Path(tmp) / "checksums.sha256"
            sha256.write_text(f"{'a' * 64} *artifact.zip\n", encoding="utf-8")
            sha512 = Path(tmp) / "checksums.sha512"
            sha512.write_text(f"{'b' * 128} *artifact.zip\n", encoding="utf-8")
            self.assertEqual(ri.classify_artifact(sha256).verdict, ri.REAL)
            self.assertEqual(ri.classify_artifact(sha512).verdict, ri.REAL)


class TestGateReport(unittest.TestCase):
    def test_gate_fails_when_any_artifact_is_not_real(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = make_pe(Path(tmp) / "EmberbirdManager-Setup-0.2.2-x64.exe")
            bad = Path(tmp) / "EmberbirdManager-Portable-0.2.2-x64.zip"
            bad.write_bytes(b"PK_EMBERBIRD_MANAGER_DESKTOP_PORTABLE_ZIP_PAYLOAD_V0.2.2")

            report = ri.gate_report(ri.audit_artifacts([good, bad]))
            self.assertFalse(report["passed"])
            self.assertEqual(report["blocking"], 1)
            self.assertEqual(report["publishable"], 1)

    def test_gate_passes_when_all_artifacts_are_real(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = make_pe(Path(tmp) / "EmberbirdManager-Setup-0.2.2-x64.exe")
            archive = make_zip(
                Path(tmp) / "EmberbirdManager-Portable-0.2.2-x64.zip",
                payload_bytes=(ri.MIN_BYTES["portable"] + 4096),
            )
            report = ri.gate_report(ri.audit_artifacts([exe, archive]))
            self.assertTrue(report["passed"])
            self.assertEqual(report["blocking"], 0)

    def test_directory_collection_skips_internal_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            make_pe(d / "EmberbirdManager-Setup-0.2.2-x64.exe")
            (d / "github-release.json").write_text("{}", encoding="utf-8")
            (d / "RELEASE_NOTES.md").write_text("# notes", encoding="utf-8")
            names = [p.name for p in ri.collect_directory_artifacts(d)]
            self.assertEqual(names, ["EmberbirdManager-Setup-0.2.2-x64.exe"])


class TestUploadRefusesPlaceholders(unittest.TestCase):
    """The uploader is the last line of defence for the public Releases section."""

    def _run_uploader(self, args: list):
        import contextlib

        import upload_github_release_assets as up

        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = up.main(args)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_gate_only_refuses_scaffold_artifact_without_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            stub = Path(tmp) / "EmberbirdManager-Setup-0.2.2-x64.exe"
            stub.write_bytes(b"MZ_EMBERBIRD_MANAGER_DESKTOP_SETUP_BINARY_PAYLOAD_V0.2.2")

            code, out, err = self._run_uploader(
                ["--files", str(stub), "--gate-only", "--tag", "v0.2.3"]
            )

            self.assertEqual(code, 1)
            self.assertIn("PLACEHOLDER", out)
            self.assertIn("REFUSING TO PUBLISH", err)
            # The refusal happens before authentication, so no credential call.
            self.assertNotIn("Authenticated as GitHub user", out)

    def test_gate_only_accepts_genuine_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = make_pe(Path(tmp) / "EmberbirdManager-Setup-0.2.2-x64.exe")
            code, out, _ = self._run_uploader(
                ["--files", str(exe), "--gate-only", "--tag", "v0.2.3"]
            )
            self.assertEqual(code, 0)
            self.assertIn("Gate PASSED", out)
            self.assertIn("nothing uploaded", out)

    def test_dist_dir_mode_gates_directory_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "EmberbirdManager-Setup-0.2.2-x64.exe").write_bytes(
                b"MZ_EMBERBIRD_MANAGER_DESKTOP_SETUP_BINARY_PAYLOAD_V0.2.2"
            )
            code, out, _ = self._run_uploader(["--dist-dir", str(d), "--gate-only"])
            self.assertEqual(code, 1)
            self.assertIn("PLACEHOLDER", out)


class TestPublishRefusesPlaceholders(unittest.TestCase):
    """A fabricated artifact can never be registered as a release."""

    def test_build_release_entry_raises_on_scaffold_artifact(self):
        import publish_release as pub

        with tempfile.TemporaryDirectory() as tmp:
            dist_dir = Path(tmp)
            (dist_dir / "WSA_2407.40000.4.0_x64.7z").write_bytes(
                b"DUMMY_ARCHIVE_DATA"
            )
            with self.assertRaises(ValueError) as ctx:
                pub.build_release_entry(dist_dir=dist_dir)
            self.assertIn("Publication Integrity Gate FAILED", str(ctx.exception))

    def test_build_release_entry_rejects_scaffold_manager_binaries(self):
        import publish_release as pub

        with tempfile.TemporaryDirectory() as tmp:
            dist_dir = Path(tmp)
            (dist_dir / "EmberbirdManager-Setup-0.2.3-x64.exe").write_bytes(
                b"MZ_EMBERBIRD_MANAGER_DESKTOP_SETUP_BINARY_PAYLOAD_V0.2.3"
            )
            (dist_dir / "EmberbirdManager-Portable-0.2.3-x64.zip").write_bytes(
                b"PK_EMBERBIRD_MANAGER_DESKTOP_PORTABLE_ZIP_PAYLOAD_V0.2.3"
            )
            with self.assertRaises(ValueError):
                pub.build_release_entry(dist_dir=dist_dir)

    def test_publication_defaults_to_the_canonical_repo_slug(self):
        import publish_release as pub

        self.assertEqual(pub.DEFAULT_REPO_SLUG, "IamAzmathullaShaikh/Emberbird")


class TestCandidateBuilderHonesty(unittest.TestCase):
    """Local candidate staging must never claim to be publishable."""

    def test_manager_candidates_are_named_from_the_identity_seam(self):
        import build_release_candidates as brc

        version_data = json.loads(
            (REPO_ROOT / "deployment" / "version.json").read_text(encoding="utf-8")
        )
        product_name = version_data["manager"]["product_name"]
        expected_prefix = "".join(part for part in product_name.split() if part)

        self.assertEqual(brc.artifact_prefix(), expected_prefix)
        self.assertEqual(expected_prefix, "EmberbirdManager")

    def test_staged_manager_candidate_is_marked_placeholder(self):
        import build_release_candidates as brc

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            entry = brc.build_manager_candidate(out, "0.2.3")
            self.assertTrue(entry.is_mock)
            self.assertEqual(entry.status, "PLACEHOLDER")
            names = [p.name for p in (out / entry.directory).iterdir()]
            self.assertTrue(all(n.startswith("EmberbirdManager-") for n in names))

    def test_packaged_scaffold_reports_placeholder_status(self):
        import package_release as pkg

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "release"
            input_dir = Path(tmp) / "staging"
            (input_dir / "WSA_2407.40000.4.0_x64").mkdir(parents=True)
            (input_dir / "WSA_2407.40000.4.0_x64" / "AppxManifest.xml").write_text(
                "<Package/>", encoding="utf-8"
            )

            _, meta = pkg.package_release_candidates(
                input_dir=input_dir, output_dir=output_dir, format_choice="zip"
            )

            self.assertNotEqual(meta["validation_status"], "VERIFIED")
            self.assertEqual(meta["validation_status"], "UNVERIFIABLE")
            self.assertIn("publication_integrity", meta)


class TestReleaseWorkflowPublishGuard(unittest.TestCase):
    """Publishing a build must be possible without risking published history."""

    @classmethod
    def setUpClass(cls):
        import yaml

        cls.workflow_path = REPO_ROOT / ".github" / "workflows" / "release.yml"
        cls.workflow = yaml.safe_load(cls.workflow_path.read_text(encoding="utf-8"))
        cls.text = cls.workflow_path.read_text(encoding="utf-8")

    def test_dispatch_exposes_an_explicit_new_tag_input(self):
        inputs = self.workflow[True]["workflow_dispatch"]["inputs"]
        self.assertIn("tag_name", inputs)
        self.assertIn("release_title", inputs)

    def test_history_overwrite_is_denied_by_default(self):
        inputs = self.workflow[True]["workflow_dispatch"]["inputs"]
        self.assertFalse(inputs["allow_history_overwrite"]["default"])
        call_inputs = self.workflow[True]["workflow_call"]["inputs"]
        self.assertFalse(call_inputs["allow_history_overwrite"]["default"])

    def test_publish_guard_runs_before_the_release_step(self):
        jobs = self.workflow["jobs"]["validate-and-publish"]["steps"]
        names = [s.get("name", "") for s in jobs]
        guard_idx = next(i for i, n in enumerate(names) if "Publish Guard" in n)
        publish_idx = next(i for i, n in enumerate(names) if n.startswith("Publish GitHub Release"))
        self.assertLess(guard_idx, publish_idx)

    def test_publish_guard_refuses_to_overwrite_published_assets(self):
        steps = self.workflow["jobs"]["validate-and-publish"]["steps"]
        guard = next(s for s in steps if "Publish Guard" in s.get("name", ""))
        body = guard["run"]
        self.assertIn("gh release view", body)
        self.assertIn("REALITY GATE REFUSAL", body)
        self.assertIn("exit 1", body)
        self.assertIn("allow_history_overwrite", guard["env"]["ALLOW_OVERWRITE"])

    def test_release_step_uses_the_resolved_tag(self):
        self.assertIn("tag_name: ${{ steps.release-info.outputs.tag }}", self.text)


if __name__ == "__main__":
    unittest.main()

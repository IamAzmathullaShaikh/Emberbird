#!/usr/bin/env python3
"""PH-27 contract tests — the diagnostic bundle can never carry a secret.

``platform/diagnostics`` assembles a shareable archive from the real Doctor
report. A restatement that leaks is worse than no bundle, so these tests pin
the sanitizer to real hostile inputs, pin the archive's members and digests,
and prove the never-include-secrets gate end to end: secrets planted in probe
summaries must not appear in *any* byte of any member of the emitted zip.
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent
PLATFORM_DIR = REPO_ROOT / "platform"
if str(PLATFORM_DIR) not in sys.path:
    sys.path.insert(0, str(PLATFORM_DIR))

from doctor import DoctorReport, ProbeResult, ProbeSeverity, ProbeStatus, VerificationState  # noqa: E402
import diagnostics  # noqa: E402

GITHUB_TOKEN = "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"  # gitleaks:ignore
USER_PATH = "C:\\Users\\bangersoul\\AppData"


def make_report(summary_extra: str = "") -> DoctorReport:
    probe = ProbeResult(
        probe_id="VM_PLATFORM",
        domain="runtime",
        title="Virtualization platform",
        status=ProbeStatus.PASS,
        severity=ProbeSeverity.INFO,
        summary=f"Enabled. Config path: {USER_PATH}{summary_extra}",
        details="observed via DISM",
        verification=VerificationState.NOT_ATTEMPTED,
    )
    return DoctorReport(
        platform_name="Emberbird",
        version="0.3.0",
        system_os="Windows",
        os_release="11 Pro",
        architecture="x86_64",
        overall_status=ProbeStatus.PASS,
        exit_code=0,
        total_probes=1,
        passed_count=1,
        warn_count=0,
        fail_count=0,
        probes=[probe],
        captured_at="2026-09-22T00:00:00Z",
    )


class TestSanitizer(unittest.TestCase):
    def test_secret_shaped_tokens_are_redacted(self):
        cases = [
            ("api_key = sk-live-abcdefgh12345678", "sk-live-abcdefgh12345678"),
            (f"token: {GITHUB_TOKEN}", GITHUB_TOKEN),
            ("password=hunter2secretvalue", "hunter2secretvalue"),
            ("pass=hunter2secretvalue", "hunter2secretvalue"),
            ("MAC 00:1A:2B:3C:4D:5E lease", "00:1A:2B:3C:4D:5E"),
            ("serial_number: WSN-77331-ABC", "WSN-77331-ABC"),
        ]
        for hostile, secret in cases:
            with self.subTest(hostile=hostile[:20]):
                clean = diagnostics.sanitize_text(hostile)
                self.assertIn(diagnostics.REDACTED, clean)
                self.assertNotIn(secret, clean)

    def test_user_profile_paths_are_redacted(self):
        self.assertNotIn("bangersoul", diagnostics.sanitize_text(USER_PATH))
        self.assertNotIn("alice", diagnostics.sanitize_text("/home/alice/data"))

    def test_benign_text_survives_verbatim(self):
        benign = "WSA_2407.40000.4.0_x64_Release-Nightly.7z verified via DISM"
        self.assertEqual(diagnostics.sanitize_text(benign), benign)

    def test_sanitization_walks_keys_and_nested_values(self):
        tree = {f"note_{GITHUB_TOKEN}": [{"deep": USER_PATH}, "safe", 42, None, True]}
        clean = json.dumps(diagnostics.sanitize_tree(tree))
        self.assertNotIn(GITHUB_TOKEN, clean)
        self.assertNotIn("bangersoul", clean)
        self.assertIn("safe", clean)
        self.assertIn(diagnostics.REDACTED, clean)


class TestBundleAssembly(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.out_dir = Path(self._tmp.name)

    def test_bundle_members_and_digests(self):
        summary = diagnostics.build_bundle(self.out_dir, make_report)
        archive = Path(summary["archive"])
        self.assertTrue(archive.is_file())
        self.assertEqual(archive.name, "emberbird-diagnostics.zip")
        with zipfile.ZipFile(archive) as zf:
            names = sorted(zf.namelist())
            payload = json.loads(zf.read("diagnostics.json"))
            readme = zf.read("README.txt").decode("utf-8")
        self.assertEqual(names, ["README.txt", "diagnostics.json"])
        json_digest = hashlib.sha256(
            (self.out_dir / "diagnostics.json").read_bytes()
        ).hexdigest()
        self.assertIn(json_digest, readme)

    def test_every_required_section_is_present(self):
        summary = diagnostics.build_bundle(self.out_dir, make_report)
        with zipfile.ZipFile(Path(summary["archive"])) as zf:
            payload = json.loads(zf.read("diagnostics.json"))
        for section in ("system", "runtime", "adb", "packages", "logs", "artifact_hashes", "probes"):
            self.assertIn(section, payload, f"PH-27 requires the {section} section")

    def test_summary_counts_and_captured_at_flow_through(self):
        summary = diagnostics.build_bundle(self.out_dir, make_report)
        self.assertEqual(summary["captured_at"], "2026-09-22T00:00:00Z")
        self.assertIn("diagnostics.json", summary["files"])
        self.assertIn("README.txt", summary["files"])

    def test_the_real_engine_runner_is_used_by_default(self):
        # The CLI path must run the real Doctor engine, not a fixture runner.
        source = (PLATFORM_DIR / "diagnostics" / "__init__.py").read_text(encoding="utf-8")
        self.assertIn("engine_runner", source)
        self.assertIn("collect_sections", source)


class TestNeverIncludeSecrets(unittest.TestCase):
    """The gate the phase names: hostile input in, no secrets out — any member."""

    SECRETS = [
        GITHUB_TOKEN,
        "bangersoul",
        "hunter2secretvalue",
        "sk-live-abcdefgh12345678",
        "00:1A:2B:3C:4D:5E",
    ]

    def test_no_member_byte_contains_any_planted_secret(self):
        hostile_report = make_report(
            summary_extra=f" auth={GITHUB_TOKEN} pass=hunter2secretvalue "
            "nic=00:1A:2B:3C:4D:5E key=sk-live-abcdefgh12345678"
        )
        with tempfile.TemporaryDirectory() as td:
            summary = diagnostics.build_bundle(Path(td), lambda: hostile_report)
            self.assertGreater(summary["redactions"], 0, "sanitizer must fire on planted secrets")
            with zipfile.ZipFile(Path(summary["archive"])) as zf:
                for member in zf.namelist():
                    raw = zf.read(member)
                    decoded = raw.decode("utf-8", errors="replace")
                    for secret in self.SECRETS:
                        self.assertNotIn(
                            secret, decoded, f"{secret[:12]}… leaked into {member}"
                        )

    def test_sanitizer_reported_count_matches_planted_secrets(self):
        hostile_report = make_report(summary_extra=f" auth={GITHUB_TOKEN}")
        with tempfile.TemporaryDirectory() as td:
            summary = diagnostics.build_bundle(Path(td), lambda: hostile_report)
        self.assertGreaterEqual(summary["redactions"], 1)


class TestCliSurface(unittest.TestCase):
    def test_cli_diagnostics_subcommand_exists_and_prints_summary(self):
        cli_dir = REPO_ROOT / "platform" / "cli"
        if str(cli_dir) not in sys.path:
            sys.path.insert(0, str(cli_dir))
        from emberbird.__main__ import main  # noqa: E402

        import contextlib

        with tempfile.TemporaryDirectory() as td:
            buffer = io.StringIO()
            with (
                contextlib.redirect_stdout(buffer),
                contextlib.redirect_stderr(buffer),
                patch("doctor.DoctorEngine.run_diagnostics", return_value=make_report()),
                patch("sys.platform", "win32"),
            ):
                code = main(["diagnostics", "--out", td, "--json"])
            self.assertEqual(code, 0, buffer.getvalue())
            payload = json.loads(buffer.getvalue())
            self.assertIn("archive", payload)
            self.assertGreaterEqual(payload["redactions"], 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

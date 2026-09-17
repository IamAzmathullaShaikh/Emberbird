#!/usr/bin/env python3
"""test_doctor.py — Comprehensive Unit & Contract Tests for Project Doctor (Phase D1).

Tests probe evaluations, mock dispatching, schema adherence, exit codes,
elevation security, data preservation, and Zero-PII compliance.
"""

from __future__ import annotations

import json
import socket
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
PLATFORM_DIR = REPO_ROOT / "platform"
if str(PLATFORM_DIR) not in sys.path:
    sys.path.insert(0, str(PLATFORM_DIR))

from doctor import (
    DoctorEngine,
    DoctorReport,
    ProbeResult,
    ProbeSeverity,
    ProbeStatus,
    probe_adb_loopback,
    probe_appx_service,
    probe_developer_mode,
    probe_google_signin,
    probe_hardware_virtualization,
    probe_hypervisor_platform,
    probe_network_connectivity,
    probe_play_services,
    probe_storage_health,
    probe_vhdx_lock,
    probe_vm_platform,
    probe_wsl_subsystem,
)


class TestDoctorProbes(unittest.TestCase):
    """Verifies individual probe logic under mock responses."""

    def test_probe_hardware_virtualization_enabled(self):
        mock_exec = MagicMock(return_value=(0, "True\n", ""))
        with patch("doctor.is_windows", return_value=True):
            res = probe_hardware_virtualization(executor=mock_exec)
            self.assertEqual(res.probe_id, "PRB-01")
            self.assertEqual(res.status, ProbeStatus.PASS)
            self.assertEqual(res.severity, ProbeSeverity.CRITICAL)

    def test_probe_hardware_virtualization_disabled(self):
        mock_exec = MagicMock(return_value=(0, "False\n", ""))
        with patch("doctor.is_windows", return_value=True):
            res = probe_hardware_virtualization(executor=mock_exec)
            self.assertEqual(res.probe_id, "PRB-01")
            self.assertEqual(res.status, ProbeStatus.FAIL)
            self.assertIn("DISABLED", res.summary)
            self.assertFalse(res.can_autofix)

    def test_probe_vm_platform_enabled(self):
        mock_exec = MagicMock(return_value=(0, "State : Enabled\n", ""))
        with patch("doctor.is_windows", return_value=True):
            res = probe_vm_platform(executor=mock_exec)
            self.assertEqual(res.probe_id, "PRB-02")
            self.assertEqual(res.status, ProbeStatus.PASS)

    def test_probe_vm_platform_disabled(self):
        mock_exec = MagicMock(return_value=(0, "State : Disabled\n", ""))
        with patch("doctor.is_windows", return_value=True):
            res = probe_vm_platform(executor=mock_exec)
            self.assertEqual(res.probe_id, "PRB-02")
            self.assertEqual(res.status, ProbeStatus.FAIL)
            self.assertTrue(res.can_autofix)
            self.assertIn("dism.exe", res.remediation_cmd)

    def test_probe_hypervisor_platform_disabled(self):
        mock_exec = MagicMock(return_value=(0, "State : Disabled\n", ""))
        with patch("doctor.is_windows", return_value=True):
            res = probe_hypervisor_platform(executor=mock_exec)
            self.assertEqual(res.probe_id, "PRB-03")
            self.assertEqual(res.status, ProbeStatus.FAIL)
            self.assertTrue(res.can_autofix)

    def test_probe_developer_mode_enabled(self):
        mock_exec = MagicMock(return_value=(0, "    AllowDevelopmentWithoutDevLicense    REG_DWORD    0x1\n", ""))
        with patch("doctor.is_windows", return_value=True):
            res = probe_developer_mode(executor=mock_exec)
            self.assertEqual(res.probe_id, "PRB-04")
            self.assertEqual(res.status, ProbeStatus.PASS)

    def test_probe_developer_mode_disabled(self):
        mock_exec = MagicMock(return_value=(1, "", "ERROR: The system was unable to find the specified registry key."))
        with patch("doctor.is_windows", return_value=True):
            res = probe_developer_mode(executor=mock_exec)
            self.assertEqual(res.probe_id, "PRB-04")
            self.assertEqual(res.status, ProbeStatus.FAIL)
            self.assertTrue(res.can_autofix)
            self.assertIn("reg add", res.remediation_cmd)

    def test_probe_appx_service_stopped(self):
        mock_exec = MagicMock(return_value=(0, "STATE              : 1  STOPPED\n", ""))
        with patch("doctor.is_windows", return_value=True):
            res = probe_appx_service(executor=mock_exec)
            self.assertEqual(res.probe_id, "PRB-05")
            self.assertEqual(res.status, ProbeStatus.WARN)
            self.assertTrue(res.can_autofix)

    def test_probe_adb_loopback_offline(self):
        # Port closed returns WARN
        with patch("socket.socket.connect", side_effect=socket.error("Connection refused")):
            res = probe_adb_loopback(port=59999, timeout=0.1)
            self.assertEqual(res.probe_id, "PRB-06")
            self.assertEqual(res.status, ProbeStatus.WARN)
            self.assertFalse(res.can_autofix)

    def test_probe_vhdx_lock_clean(self):
        mock_exec = MagicMock(return_value=(0, '"notepad.exe","1234","Console","1","10,000 K"\n', ""))
        with patch("doctor.is_windows", return_value=True):
            res = probe_vhdx_lock(executor=mock_exec)
            self.assertEqual(res.probe_id, "PRB-07")
            self.assertEqual(res.status, ProbeStatus.PASS)

    def test_probe_wsl_subsystem_running(self):
        mock_exec = MagicMock(return_value=(0, "STATE              : 4  RUNNING\n", ""))
        with patch("doctor.is_windows", return_value=True):
            res = probe_wsl_subsystem(executor=mock_exec)
            self.assertEqual(res.probe_id, "PRB-08")
            self.assertEqual(res.status, ProbeStatus.PASS)

    def test_probe_wsl_subsystem_stopped(self):
        mock_exec = MagicMock(return_value=(0, "STATE              : 1  STOPPED\n", ""))
        with patch("doctor.is_windows", return_value=True):
            res = probe_wsl_subsystem(executor=mock_exec)
            self.assertEqual(res.probe_id, "PRB-08")
            self.assertEqual(res.status, ProbeStatus.WARN)
            self.assertTrue(res.can_autofix)

    def test_probe_play_services_registered(self):
        mock_exec = MagicMock(return_value=(0, "MicrosoftCorporationII.WindowsSubsystemForAndroid\n", ""))
        with patch("doctor.is_windows", return_value=True):
            res = probe_play_services(executor=mock_exec)
            self.assertEqual(res.probe_id, "PRB-09")
            self.assertEqual(res.status, ProbeStatus.PASS)

    def test_probe_play_services_missing(self):
        mock_exec = MagicMock(return_value=(1, "", "No package found"))
        with patch("doctor.is_windows", return_value=True):
            res = probe_play_services(executor=mock_exec)
            self.assertEqual(res.probe_id, "PRB-09")
            self.assertEqual(res.status, ProbeStatus.WARN)

    def test_probe_google_signin_enabled(self):
        mock_exec = MagicMock(return_value=(0, "    PlayStoreEnabled    REG_DWORD    0x1\n", ""))
        with patch("doctor.is_windows", return_value=True):
            res = probe_google_signin(executor=mock_exec)
            self.assertEqual(res.probe_id, "PRB-10")
            self.assertEqual(res.status, ProbeStatus.PASS)

    def test_probe_network_connectivity_up(self):
        mock_exec = MagicMock(return_value=(0, "Up\n", ""))
        with patch("doctor.is_windows", return_value=True):
            res = probe_network_connectivity(executor=mock_exec)
            self.assertEqual(res.probe_id, "PRB-11")
            self.assertEqual(res.status, ProbeStatus.PASS)

    def test_probe_storage_health_sufficient(self):
        mock_exec = MagicMock(return_value=(0, "65\n", ""))
        with patch("doctor.is_windows", return_value=True):
            res = probe_storage_health(executor=mock_exec)
            self.assertEqual(res.probe_id, "PRB-12")
            self.assertEqual(res.status, ProbeStatus.PASS)

    def test_probe_storage_health_critical(self):
        mock_exec = MagicMock(return_value=(0, "5\n", ""))
        with patch("doctor.is_windows", return_value=True):
            res = probe_storage_health(executor=mock_exec)
            self.assertEqual(res.probe_id, "PRB-12")
            self.assertEqual(res.status, ProbeStatus.FAIL)
            self.assertIn("Critically low", res.summary)


class TestDoctorEngine(unittest.TestCase):
    """Verifies overall status roll-ups, exit codes, and serialization."""

    def test_all_pass_yields_exit_code_zero(self):
        engine = DoctorEngine()
        pass_probe = lambda: ProbeResult("P", "D", "T", ProbeStatus.PASS, ProbeSeverity.INFO, "S", "D")
        engine.probes = [pass_probe, pass_probe]

        report = engine.run_diagnostics()
        self.assertEqual(report.overall_status, ProbeStatus.PASS)
        self.assertEqual(report.exit_code, 0)
        self.assertEqual(report.passed_count, 2)
        self.assertEqual(report.fail_count, 0)

    def test_warning_yields_exit_code_one(self):
        engine = DoctorEngine()
        pass_probe = lambda: ProbeResult("P1", "D", "T", ProbeStatus.PASS, ProbeSeverity.INFO, "S", "D")
        warn_probe = lambda: ProbeResult("P2", "D", "T", ProbeStatus.WARN, ProbeSeverity.WARNING, "S", "D")
        engine.probes = [pass_probe, warn_probe]

        report = engine.run_diagnostics()
        self.assertEqual(report.overall_status, ProbeStatus.WARN)
        self.assertEqual(report.exit_code, 1)
        self.assertEqual(report.warn_count, 1)

    def test_critical_failure_yields_exit_code_two(self):
        engine = DoctorEngine()
        pass_probe = lambda: ProbeResult("P1", "D", "T", ProbeStatus.PASS, ProbeSeverity.INFO, "S", "D")
        fail_probe = lambda: ProbeResult("P2", "D", "T", ProbeStatus.FAIL, ProbeSeverity.CRITICAL, "S", "D")
        engine.probes = [pass_probe, fail_probe]

        report = engine.run_diagnostics()
        self.assertEqual(report.overall_status, ProbeStatus.FAIL)
        self.assertEqual(report.exit_code, 2)
        self.assertEqual(report.fail_count, 1)

    def test_schema_compliance(self):
        engine = DoctorEngine()
        report = engine.run_diagnostics()
        d = report.to_dict()

        schema_path = REPO_ROOT / "platform" / "doctor" / "doctor.schema.json"
        self.assertTrue(schema_path.is_file())
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        for req in schema["required"]:
            self.assertIn(req, d, f"Missing required field in report: {req}")

        for p in d["probes"]:
            for req in schema["properties"]["probes"]["items"]["required"]:
                self.assertIn(req, p, f"Missing required probe field: {req}")

    def test_zero_pii_doctrine(self):
        """Doctor reports must never leak personal user paths, usernames, or IP addresses."""
        engine = DoctorEngine()
        report = engine.run_diagnostics()
        dump = json.dumps(report.to_dict())

        forbidden_patterns = [
            r"[A-Za-z]:\\[Uu]sers\\[A-Za-z0-9_-]+\\",
            r"/home/[A-Za-z0-9_-]+/",
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        ]
        import re
        for pat in forbidden_patterns:
            self.assertFalse(re.search(pat, dump), f"PII pattern matched in doctor report: {pat}")

    def test_data_preservation_doctrine_in_remediation(self):
        """Remediation commands must NEVER delete or truncate virtual disk files."""
        engine = DoctorEngine()
        report = engine.run_diagnostics()
        import re
        destructive_pattern = re.compile(r"\b(del|rm|rmdir|format|diskpart|truncate|drop)\b", re.IGNORECASE)

        for probe in report.probes:
            if probe.remediation_cmd:
                match = destructive_pattern.search(probe.remediation_cmd)
                self.assertIsNone(match, f"Destructive command keyword '{match.group(0) if match else ''}' found in probe {probe.probe_id}")

    def test_elevation_guard_when_non_admin(self):
        """Non-admin user invoking remediation gets clean exit code 2 and warning."""
        engine = DoctorEngine()
        with patch("doctor.is_windows", return_value=True), patch("doctor.is_admin", return_value=False):
            code, logs = engine.apply_remediation()
            self.assertEqual(code, 2)
            self.assertTrue(any("ELEVATION REQUIRED" in log for log in logs))


if __name__ == "__main__":
    unittest.main()

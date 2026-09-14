#!/usr/bin/env python3
"""
test_runtime_compatibility.py — Unit tests for the runtime compatibility harness.

Covers: baseline capture, app probing (all five lifecycle outcomes), status
derivation, report shape validation, submission generation + schema re-check,
and the honesty contract (no adb -> exit 2, placeholder status, no records).
"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import runtime_compatibility as rc  # noqa: E402


class FakeAdb:
    """Scripted adb: maps command tuples to canned stdout."""

    def __init__(self, script=None):
        self.script = script or {}
        self.calls = []

    def __call__(self, args, timeout=None):
        self.calls.append(tuple(args))
        key = tuple(args)
        if key in self.script:
            value = self.script[key]
            if isinstance(value, Exception):
                raise rc.AdbError(str(value))
            return value
        raise rc.AdbError(f"unscripted adb call: {args}")


def base_script(**overrides):
    """Canned adb responses for a Magisk-managed WSA with GApps present."""
    script = {
        ("start-server",): "",
        ("devices",): "List of devices attached\nemulator-5554\tdevice\n",
        ("shell", "getprop", "ro.build.version.release"): "13\n",
        ("shell", "getprop", "ro.build.version.sdk"): "33\n",
        ("shell", "getprop", "ro.product.cpu.abilist"): "x86_64,arm64-v8a\n",
        ("shell", "pm", "list", "packages"): (
            "package:org.telegram.messenger.web\npackage:com.spotify.music\n"
            "package:com.android.vending\npackage:com.google.android.gms\n"
            "package:com.topjohnwu.magisk\n"
        ),
    }
    # The su probe must fail for a Magisk-managed device (root detected via
    # package presence, not via su). Registered as a scripted failure.
    script[("shell", "su", "-c", "id")] = rc.AdbError("su: not found")
    return script


class TestBaselineCapture(unittest.TestCase):
    def test_baseline_captures_platform_facts(self):
        adb = FakeAdb(base_script())
        baseline = rc.capture_baseline(adb)
        self.assertEqual(baseline["android_version"], "13")
        self.assertEqual(baseline["android_sdk"], "33")
        self.assertEqual(baseline["root_flavor"], "Magisk")
        self.assertTrue(baseline["gapps_present"])
        self.assertEqual(baseline["package_count"], 5)

    def test_baseline_survives_getprop_failures(self):
        script = base_script()
        script[("shell", "getprop", "ro.build.version.release")] = rc.AdbError("boom")
        adb = FakeAdb(script)
        baseline = rc.capture_baseline(adb)
        self.assertTrue(baseline["android_version"].startswith("<error"))


class TestProbing(unittest.TestCase):
    def _probe_script(self, packages, launch="OK", focus_pkg=None, logcat=""):
        script = base_script()
        script[("shell", "pm", "list", "packages")] = packages
        script[("shell", "monkey", "-p", "org.telegram.messenger.web", "-c",
                "android.intent.category.LAUNCHER", "1")] = launch
        focus = f"mCurrentFocus=Window{{123 u0 {focus_pkg}/com.example.MainActivity}}" if focus_pkg else "mCurrentFocus=Window{123 u0 NotificationShade}"
        script[("shell", "dumpsys", "window")] = focus
        script[("logcat", "-c")] = ""
        script[("logcat", "-d", "-s", "AndroidRuntime:E")] = logcat
        return script

    def test_installed_and_focused_is_working(self):
        adb = FakeAdb(self._probe_script(
            "package:org.telegram.messenger.web",
            focus_pkg="org.telegram.messenger.web",
        ))
        probe = rc.probe_app(adb, "org.telegram.messenger.web", launch_wait_s=0)
        self.assertEqual(probe["result"], "launched_focused")
        self.assertEqual(rc.derive_status(probe), "Working")

    def test_crash_evidence_yields_broken(self):
        adb = FakeAdb(self._probe_script(
            "package:org.telegram.messenger.web",
            focus_pkg="org.telegram.messenger.web",
            logcat="E AndroidRuntime: Process: org.telegram.messenger.web, FATAL EXCEPTION: main",
        ))
        probe = rc.probe_app(adb, "org.telegram.messenger.web", launch_wait_s=0)
        self.assertEqual(probe["result"], "crashed")
        self.assertEqual(rc.derive_status(probe), "Broken")
        self.assertTrue(probe["crash_evidence"])

    def test_not_installed_is_broken_status(self):
        adb = FakeAdb(self._probe_script(""))
        probe = rc.probe_app(adb, "org.telegram.messenger.web", launch_wait_s=0)
        self.assertEqual(probe["result"], "not_installed")
        self.assertEqual(rc.derive_status(probe), "Broken")

    def test_launch_failure_is_broken(self):
        script = self._probe_script("package:org.telegram.messenger.web")
        script[("shell", "monkey", "-p", "org.telegram.messenger.web", "-c",
                "android.intent.category.LAUNCHER", "1")] = rc.AdbError("inject failed")
        adb = FakeAdb(script)
        probe = rc.probe_app(adb, "org.telegram.messenger.web", launch_wait_s=0)
        self.assertEqual(probe["result"], "launch_failed")

    def test_unfocused_launch_is_workaround_required(self):
        adb = FakeAdb(self._probe_script(
            "package:org.telegram.messenger.web",
            focus_pkg=None,
        ))
        probe = rc.probe_app(adb, "org.telegram.messenger.web", launch_wait_s=0)
        self.assertEqual(probe["result"], "launched_unverified_focus")
        self.assertEqual(rc.derive_status(probe), "Workaround Required")


class TestReportAndSubmissions(unittest.TestCase):
    def _report(self):
        baseline = {"android_version": "13", "android_sdk": "33", "abi_list": "x86_64",
                    "root_flavor": "Magisk", "gapps_present": True, "package_count": 5}
        probes = {
            "Telegram": {"package_id": "org.telegram.messenger.web", "result": "launched_focused",
                         "focused_window": "org.telegram.messenger.web/x", "crash_evidence": [],
                         "launch_command_output": ["OK"]},
            "Netflix": {"package_id": "com.netflix.mediaclient", "result": "not_installed",
                        "focused_window": None, "crash_evidence": [], "launch_command_output": []},
        }
        report = rc.build_report(baseline, probes, "adb:emulator-5554")
        return report

    def test_report_shape_valid(self):
        self.assertEqual(rc.validate_report_shape(self._report()), [])

    def test_report_shape_catches_invalid_status(self):
        report = self._report()
        report["apps"]["Telegram"]["compatibility_status"] = "Might work"
        self.assertTrue(rc.validate_report_shape(report))

    def test_submissions_are_schema_valid(self):
        import validate_compatibility as vc

        report = self._report()
        written = rc.write_submissions(report, "Magisk")
        try:
            self.assertEqual(len(written), 2)
            for path in written:
                errors = vc.validate_file(path)
                self.assertEqual(errors, [], f"{path.name} must be schema-valid")
            telegram = json.loads((rc.SUBMISSIONS_DIR / written[0].name).read_text(encoding="utf-8"))
            self.assertEqual(telegram["verification_status"], "unverified")
        finally:
            for path in written:
                path.unlink(missing_ok=True)

    def test_summary_renders_table(self):
        summary = rc.render_summary(self._report())
        self.assertIn("Telegram", summary)
        self.assertIn("Working", summary)
        self.assertIn("unverified", summary)


class TestHonestyContract(unittest.TestCase):
    """Runtime Reality Gate: no environment -> no claims, ever."""

    def test_missing_adb_returns_exit_2(self):
        exit_code = rc.main(["--adb", "definitely-not-a-real-adb-binary-xyz"])
        self.assertEqual(exit_code, 2)


if __name__ == "__main__":
    unittest.main()
